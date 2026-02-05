"""Shared Modbus transport logic for TCP and Serial transports.

This module provides the BaseModbusTransport class containing all register
reading/writing logic, retry handling, and device data methods shared between
ModbusTransport (TCP) and ModbusSerialTransport (RTU serial).

Subclasses must implement:
- connect() / disconnect() — protocol-specific connection management
- _reconnect() — protocol-specific reconnection with logging
- capabilities property — transport capability flags
- _create_client() — optional, for client initialization
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from pymodbus.exceptions import ModbusIOException

from ._register_readers import (
    is_midbox_device,
    read_device_type_async,
    read_firmware_version_async,
    read_parallel_config_async,
    read_serial_number_async,
)
from .data import (
    BatteryBankData,
    InverterEnergyData,
    InverterRuntimeData,
    MidboxRuntimeData,
)
from .exceptions import (
    TransportConnectionError,
    TransportReadError,
    TransportTimeoutError,
    TransportWriteError,
)
from .protocol import BaseTransport

if TYPE_CHECKING:
    from pylxpweb.devices.inverters._features import InverterFamily
    from pylxpweb.transports.register_maps import (
        EnergyRegisterMap,
        RuntimeRegisterMap,
    )

_LOGGER = logging.getLogger(__name__)

# Register group definitions for efficient reading
# Based on Modbus 40-register per call limit
# Source: EG4-18KPV-12LV Modbus Protocol + eg4-modbus-monitor + Yippy's BMS docs
INPUT_REGISTER_GROUPS = {
    "power_energy": (0, 32),  # Registers 0-31: Power, voltage, SOC/SOH, current
    "status_energy": (32, 32),  # Registers 32-63: Status, energy, fault/warning codes
    "temperatures": (64, 16),  # Registers 64-79: Temperatures, currents, fault history
    "bms_data": (80, 33),  # Registers 80-112: BMS passthrough data (Yippy's docs)
    "extended_data": (113, 18),  # Registers 113-130: Parallel config, generator, EPS L1N/L2N
    # Note: Registers 140-143 are AFCI current per 18kPV docs, not EPS voltage
    "output_power": (170, 2),  # Registers 170-171: Output power
}

# GridBOSS register groups for read_midbox_runtime
_MIDBOX_REGISTER_GROUPS: list[tuple[int, int]] = [
    (0, 40),  # Voltages, currents, power, smart loads 1-3
    (40, 28),  # Smart load 4 power + energy today
    (68, 40),  # Energy totals
    (108, 12),  # Smart port 4 status + AC couple totals
    (128, 4),  # Frequencies
]


class BaseModbusTransport(BaseTransport):
    """Base class for Modbus-based transports (TCP and Serial).

    Provides shared register read/write logic with retry handling,
    adaptive inter-group delays, and device data conversion methods.

    Subclasses must set ``self._client`` to a pymodbus async client
    and implement ``connect()``, ``disconnect()``, and ``_reconnect()``.
    """

    def __init__(
        self,
        serial: str,
        *,
        unit_id: int = 1,
        timeout: float = 10.0,
        inverter_family: InverterFamily | None = None,
        retries: int = 2,
        retry_delay: float = 0.5,
        inter_register_delay: float = 0.05,
        pymodbus_retries: int = 3,
    ) -> None:
        """Initialize base Modbus transport.

        Args:
            serial: Inverter serial number (for identification)
            unit_id: Modbus unit/slave ID (default 1)
            timeout: Connection and operation timeout in seconds
            inverter_family: Inverter model family for correct register mapping
            retries: Application-level retries per register read (default 2)
            retry_delay: Initial delay between retries in seconds, doubles each
                attempt (default 0.5)
            inter_register_delay: Delay between register group reads in seconds
                (default 0.05)
            pymodbus_retries: Number of retries passed to pymodbus client
                (default 3)
        """
        super().__init__(serial)
        self._unit_id = unit_id
        self._timeout = timeout
        self._inverter_family = inverter_family
        self._retries = retries
        self._retry_delay = retry_delay
        self._inter_register_delay = inter_register_delay
        self._pymodbus_retries = pymodbus_retries
        self._client: Any = None
        self._lock = asyncio.Lock()
        self._consecutive_errors: int = 0
        self._max_consecutive_errors: int = 3
        self._last_read_retried: bool = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def unit_id(self) -> int:
        """Get the Modbus unit/slave ID."""
        return self._unit_id

    @property
    def inverter_family(self) -> InverterFamily | None:
        """Get the inverter family for register mapping."""
        return self._inverter_family

    @inverter_family.setter
    def inverter_family(self, value: InverterFamily | None) -> None:
        """Set the inverter family for register mapping."""
        if value != self._inverter_family:
            _LOGGER.debug(
                "Updating inverter family from %s to %s for %s",
                self._inverter_family,
                value,
                self._serial,
            )
        self._inverter_family = value

    @property
    def runtime_register_map(self) -> RuntimeRegisterMap:
        """Get the runtime register map for this inverter family."""
        from pylxpweb.transports.register_maps import get_runtime_map

        return get_runtime_map(self._inverter_family)

    @property
    def energy_register_map(self) -> EnergyRegisterMap:
        """Get the energy register map for this inverter family."""
        from pylxpweb.transports.register_maps import get_energy_map

        return get_energy_map(self._inverter_family)

    # ------------------------------------------------------------------
    # Register Read/Write (with retry and error tracking)
    # ------------------------------------------------------------------

    async def _read_registers(
        self,
        address: int,
        count: int,
        *,
        input_registers: bool,
    ) -> list[int]:
        """Read Modbus registers with retry and error tracking.

        Args:
            address: Starting register address
            count: Number of registers to read (max 40)
            input_registers: True for input registers (FC4), False for holding (FC3)

        Returns:
            List of register values

        Raises:
            TransportReadError: If read fails after all retries
            TransportTimeoutError: If operation times out
        """
        self._ensure_connected()

        if self._client is None:
            raise TransportConnectionError("Modbus client not initialized")

        reg_type = "input" if input_registers else "holding"
        last_err: Exception | None = None
        self._last_read_retried = False

        for attempt in range(self._retries + 1):
            async with self._lock:
                try:
                    read_fn = (
                        self._client.read_input_registers
                        if input_registers
                        else self._client.read_holding_registers
                    )
                    result = await read_fn(
                        address=address,
                        count=min(count, 40),
                        device_id=self._unit_id,
                    )

                    if result.isError():
                        raise TransportReadError(
                            f"Modbus read error at address {address}: {result}"
                        )

                    if not hasattr(result, "registers") or result.registers is None:
                        raise TransportReadError(
                            f"Invalid Modbus response at address {address}: "
                            "no registers in response"
                        )

                    self._consecutive_errors = 0
                    return list(result.registers)

                except ModbusIOException as err:
                    self._consecutive_errors += 1
                    if "timeout" in str(err).lower():
                        last_err = TransportTimeoutError(
                            f"Timeout reading {reg_type} registers at {address}"
                        )
                    else:
                        last_err = TransportReadError(
                            f"Failed to read {reg_type} registers at {address}: {err}"
                        )
                    last_err.__cause__ = err
                except TimeoutError as err:
                    self._consecutive_errors += 1
                    last_err = TransportTimeoutError(
                        f"Timeout reading {reg_type} registers at {address}"
                    )
                    last_err.__cause__ = err
                except (TransportReadError, TransportTimeoutError) as err:
                    self._consecutive_errors += 1
                    last_err = err
                except OSError as err:
                    self._consecutive_errors += 1
                    last_err = TransportReadError(
                        f"Failed to read {reg_type} registers at {address}: {err}"
                    )
                    last_err.__cause__ = err

            # Retry with exponential backoff (skip on last attempt)
            if attempt < self._retries:
                self._last_read_retried = True
                delay = self._retry_delay * (2**attempt)
                _LOGGER.debug(
                    "Retry %d/%d reading %s registers at %d after %.1fs",
                    attempt + 1,
                    self._retries,
                    reg_type,
                    address,
                    delay,
                )
                await asyncio.sleep(delay)

        _LOGGER.error(
            "Failed to read %s registers at %d after %d attempts: %s",
            reg_type,
            address,
            self._retries + 1,
            last_err,
        )
        raise last_err  # type: ignore[misc]

    async def _read_input_registers(
        self,
        address: int,
        count: int,
    ) -> list[int]:
        """Read input registers (read-only runtime data)."""
        return await self._read_registers(address, count, input_registers=True)

    async def _read_holding_registers(
        self,
        address: int,
        count: int,
    ) -> list[int]:
        """Read holding registers (configuration parameters)."""
        return await self._read_registers(address, count, input_registers=False)

    async def _write_holding_registers(
        self,
        address: int,
        values: list[int],
    ) -> bool:
        """Write holding registers.

        Args:
            address: Starting register address
            values: List of values to write

        Returns:
            True if write succeeded

        Raises:
            TransportWriteError: If write fails
            TransportTimeoutError: If operation times out
        """
        self._ensure_connected()

        if self._client is None:
            raise TransportConnectionError("Modbus client not initialized")

        async with self._lock:
            try:
                if len(values) == 1:
                    result = await self._client.write_register(
                        address=address,
                        value=values[0],
                        device_id=self._unit_id,
                    )
                else:
                    result = await self._client.write_registers(
                        address=address,
                        values=values,
                        device_id=self._unit_id,
                    )

                if result.isError():
                    _LOGGER.error(
                        "Modbus error writing registers at %d: %s",
                        address,
                        result,
                    )
                    raise TransportWriteError(f"Modbus write error at address {address}: {result}")

                return True

            except ModbusIOException as err:
                if "timeout" in str(err).lower():
                    _LOGGER.error("Timeout writing registers at %d", address)
                    raise TransportTimeoutError(f"Timeout writing registers at {address}") from err
                _LOGGER.error("Failed to write registers at %d: %s", address, err)
                raise TransportWriteError(f"Failed to write registers at {address}: {err}") from err
            except TimeoutError as err:
                _LOGGER.error("Timeout writing registers at %d", address)
                raise TransportTimeoutError(f"Timeout writing registers at {address}") from err
            except OSError as err:
                _LOGGER.error("Failed to write registers at %d: %s", address, err)
                raise TransportWriteError(f"Failed to write registers at {address}: {err}") from err

    # ------------------------------------------------------------------
    # Register Group Reading (with adaptive inter-group delay)
    # ------------------------------------------------------------------

    async def _read_register_groups(
        self,
        group_names: list[str] | None = None,
    ) -> dict[int, int]:
        """Read multiple register groups sequentially with inter-group delays.

        Args:
            group_names: Specific group names to read from INPUT_REGISTER_GROUPS.
                If None, reads all groups.

        Returns:
            Dict mapping register address to value

        Raises:
            TransportReadError: If any group read fails
        """
        if group_names is None:
            groups = list(INPUT_REGISTER_GROUPS.items())
        else:
            groups = [
                (name, INPUT_REGISTER_GROUPS[name])
                for name in group_names
                if name in INPUT_REGISTER_GROUPS
            ]

        if self._consecutive_errors >= self._max_consecutive_errors:
            await self._reconnect()

        registers: dict[int, int] = {}
        current_delay = self._inter_register_delay

        for i, (group_name, (start, count)) in enumerate(groups):
            try:
                values = await self._read_input_registers(start, count)
                for offset, value in enumerate(values):
                    registers[start + offset] = value
            except Exception as e:
                _LOGGER.error(
                    "Failed to read register group '%s': %s",
                    group_name,
                    e,
                )
                raise TransportReadError(
                    f"Failed to read register group '{group_name}': {e}"
                ) from e

            # Increase delay when retries occurred to give the device breathing room
            if self._last_read_retried:
                current_delay = min(current_delay * 2, 1.0)
                _LOGGER.debug(
                    "Increasing inter-group delay to %.3fs after retries",
                    current_delay,
                )

            if i < len(groups) - 1:
                await asyncio.sleep(current_delay)

        return registers

    def _registers_from_values(
        self,
        start: int,
        values: list[int],
    ) -> dict[int, int]:
        """Build address-to-value dict from a contiguous register read.

        Args:
            start: Starting register address
            values: List of register values

        Returns:
            Dict mapping register address to value
        """
        return {start + offset: value for offset, value in enumerate(values)}

    # ------------------------------------------------------------------
    # Device Data Methods
    # ------------------------------------------------------------------

    async def read_runtime(self) -> InverterRuntimeData:
        """Read runtime data via Modbus input registers.

        Returns:
            Runtime data with all values properly scaled

        Raises:
            TransportReadError: If read operation fails
        """
        input_registers = await self._read_register_groups()
        return InverterRuntimeData.from_modbus_registers(input_registers, self.runtime_register_map)

    async def read_energy(self) -> InverterEnergyData:
        """Read energy statistics via Modbus input registers.

        Returns:
            Energy data with all values in kWh

        Raises:
            TransportReadError: If read operation fails
        """
        input_registers = await self._read_register_groups(["power_energy", "status_energy"])

        # bms_data is supplementary -- don't fail the entire energy read
        # if these registers time out
        try:
            bms_registers = await self._read_register_groups(["bms_data"])
            input_registers.update(bms_registers)
        except (TransportReadError, TransportTimeoutError):
            _LOGGER.debug(
                "bms_data registers unavailable for %s, continuing without them",
                self._serial,
            )

        return InverterEnergyData.from_modbus_registers(input_registers, self.energy_register_map)

    async def read_battery(
        self,
        include_individual: bool = True,
    ) -> BatteryBankData | None:
        """Read battery information via Modbus.

        Args:
            include_individual: If True, also reads extended registers (5000+)
                for individual battery module data.

        Returns:
            Battery bank data with available information, None if no battery

        Raises:
            TransportReadError: If read operation fails
        """
        from pylxpweb.transports.register_maps import (
            INDIVIDUAL_BATTERY_BASE_ADDRESS,
            INDIVIDUAL_BATTERY_MAX_COUNT,
            INDIVIDUAL_BATTERY_REGISTER_COUNT,
        )

        if self._consecutive_errors >= self._max_consecutive_errors:
            await self._reconnect()

        all_registers: dict[int, int] = {}

        # Read all runtime registers (0-127) including:
        # - Power/voltage registers (0-31)
        # - Extended registers including battery_current at reg 75 (32-79)
        # - BMS passthrough registers (80-112)
        # Local Modbus reads are cheap, so read the full range
        try:
            # Read in two chunks due to Modbus protocol limits (max ~125 registers per read)
            runtime_regs_1 = await self._read_input_registers(0, 64)
            all_registers.update(self._registers_from_values(0, runtime_regs_1))

            runtime_regs_2 = await self._read_input_registers(64, 64)
            all_registers.update(self._registers_from_values(64, runtime_regs_2))
        except Exception as e:
            _LOGGER.warning("Failed to read runtime registers 0-127: %s", e)

        # Read individual battery registers (5000+) if requested
        battery_count = all_registers.get(96, 0)
        individual_registers: dict[int, int] | None = None

        if include_individual and battery_count > 0:
            individual_registers = {}
            batteries_to_read = min(battery_count, INDIVIDUAL_BATTERY_MAX_COUNT)
            total_registers = batteries_to_read * INDIVIDUAL_BATTERY_REGISTER_COUNT

            try:
                current_addr = INDIVIDUAL_BATTERY_BASE_ADDRESS
                remaining = total_registers

                while remaining > 0:
                    chunk_size = min(remaining, 40)
                    values = await self._read_input_registers(current_addr, chunk_size)
                    individual_registers.update(self._registers_from_values(current_addr, values))
                    current_addr += chunk_size
                    remaining -= chunk_size

                _LOGGER.debug(
                    "Read individual battery data for %d batteries from registers %d-%d",
                    batteries_to_read,
                    INDIVIDUAL_BATTERY_BASE_ADDRESS,
                    current_addr - 1,
                )
            except Exception as e:
                _LOGGER.warning(
                    "Failed to read individual battery registers (5000+): %s",
                    e,
                )
                individual_registers = None

        result = BatteryBankData.from_modbus_registers(
            all_registers,
            self.runtime_register_map,
            individual_registers,
        )

        if result is None:
            _LOGGER.debug("Battery voltage below threshold, assuming no battery present")
        elif result.batteries:
            _LOGGER.debug(
                "Loaded %d individual batteries via Modbus",
                len(result.batteries),
            )

        return result

    async def read_parameters(
        self,
        start_address: int,
        count: int,
    ) -> dict[int, int]:
        """Read configuration parameters via Modbus holding registers.

        Args:
            start_address: Starting register address
            count: Number of registers to read (max 40 per call)

        Returns:
            Dict mapping register address to raw integer value

        Raises:
            TransportReadError: If read operation fails
        """
        result: dict[int, int] = {}
        remaining = count
        current_address = start_address

        while remaining > 0:
            chunk_size = min(remaining, 40)
            values = await self._read_holding_registers(current_address, chunk_size)
            result.update(self._registers_from_values(current_address, values))
            current_address += chunk_size
            remaining -= chunk_size

        return result

    async def write_parameters(
        self,
        parameters: dict[int, int],
    ) -> bool:
        """Write configuration parameters via Modbus holding registers.

        Args:
            parameters: Dict mapping register address to value to write

        Returns:
            True if all writes succeeded

        Raises:
            TransportWriteError: If any write operation fails
        """
        sorted_params = sorted(parameters.items())

        # Group consecutive addresses for batch writing
        groups: list[tuple[int, list[int]]] = []
        current_start: int | None = None
        current_values: list[int] = []

        for address, value in sorted_params:
            if current_start is None:
                current_start = address
                current_values = [value]
            elif address == current_start + len(current_values):
                current_values.append(value)
            else:
                groups.append((current_start, current_values))
                current_start = address
                current_values = [value]

        if current_start is not None and current_values:
            groups.append((current_start, current_values))

        for start_address, values in groups:
            await self._write_holding_registers(start_address, values)

        return True

    # ------------------------------------------------------------------
    # Device Info / Discovery
    # ------------------------------------------------------------------

    async def read_serial_number(self) -> str:
        """Read inverter serial number from input registers 115-119.

        Returns:
            10-character serial number string

        Raises:
            TransportReadError: If read operation fails
        """
        return await read_serial_number_async(self._read_input_registers, self._serial)

    async def read_firmware_version(self) -> str:
        """Read full firmware version code from holding registers 7-10.

        Returns:
            Full firmware code string (e.g., "FAAB-2525") or empty string
        """
        return await read_firmware_version_async(self._read_holding_registers)

    async def validate_serial(self, expected_serial: str) -> bool:
        """Validate that the connected inverter matches the expected serial.

        Args:
            expected_serial: The serial number the user expects to connect to

        Returns:
            True if serials match, False otherwise

        Raises:
            TransportReadError: If read operation fails
        """
        actual_serial = await self.read_serial_number()
        matches = actual_serial == expected_serial

        if not matches:
            _LOGGER.warning(
                "Serial mismatch: expected %s, got %s",
                expected_serial,
                actual_serial,
            )

        return matches

    async def read_device_type(self) -> int:
        """Read device type code from register 19.

        Returns:
            Device type code integer

        Raises:
            TransportReadError: If read operation fails
        """
        return await read_device_type_async(self._read_holding_registers)

    def is_midbox_device(self, device_type_code: int) -> bool:
        """Check if device type code indicates a MID/GridBOSS device."""
        return is_midbox_device(device_type_code)

    async def read_parallel_config(self) -> int:
        """Read parallel configuration from input register 113.

        Returns:
            Raw 16-bit value with packed parallel config, or 0 if read fails.

        Raises:
            TransportReadError: If read operation fails
        """
        return await read_parallel_config_async(self._read_input_registers, self._serial)

    async def read_midbox_runtime(self) -> MidboxRuntimeData:
        """Read runtime data from a MID/GridBOSS device.

        Returns:
            MidboxRuntimeData with all values properly scaled

        Raises:
            TransportReadError: If read operation fails
        """
        from pylxpweb.transports.register_maps import (
            GRIDBOSS_ENERGY_MAP,
            GRIDBOSS_RUNTIME_MAP,
        )

        input_registers: dict[int, int] = {}

        try:
            for i, (start, count) in enumerate(_MIDBOX_REGISTER_GROUPS):
                values = await self._read_input_registers(start, count)
                input_registers.update(self._registers_from_values(start, values))

                # Inter-group delay between reads (skip after last group)
                if i < len(_MIDBOX_REGISTER_GROUPS) - 1:
                    await asyncio.sleep(self._inter_register_delay)

        except Exception as e:
            _LOGGER.error("Failed to read MID input registers: %s", e)
            raise TransportReadError(f"Failed to read MID registers: {e}") from e

        return MidboxRuntimeData.from_modbus_registers(
            input_registers, GRIDBOSS_RUNTIME_MAP, GRIDBOSS_ENERGY_MAP
        )

    # ------------------------------------------------------------------
    # Reconnect (subclasses may override for custom logging)
    # ------------------------------------------------------------------

    async def _reconnect(self) -> None:
        """Reconnect Modbus client to reset state after consecutive errors.

        Uses lock with double-check to prevent concurrent reconnection.
        """
        async with self._lock:
            if self._consecutive_errors < self._max_consecutive_errors:
                return

            _LOGGER.warning(
                "Reconnecting Modbus client for %s after %d consecutive errors",
                self._serial,
                self._consecutive_errors,
            )
            await self.disconnect()
            await self.connect()
            self._consecutive_errors = 0

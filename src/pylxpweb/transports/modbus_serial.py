"""Modbus RTU serial transport implementation.

This module provides the ModbusSerialTransport class for direct local
communication with inverters via Modbus RTU over USB-to-RS485 serial adapters.

IMPORTANT: Single-Client Limitation
------------------------------------
Serial ports support only ONE concurrent connection.
Running multiple clients causes communication errors and data corruption.

Ensure only ONE integration/script connects to each serial port at a time.

Example:
    transport = ModbusSerialTransport(
        port="/dev/ttyUSB0",
        baudrate=19200,
        serial="CE12345678",
    )
    await transport.connect()

    runtime = await transport.read_runtime()
    print(f"PV Power: {runtime.pv_total_power}W")
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from pymodbus.exceptions import ModbusIOException

from ._register_readers import (
    is_midbox_device,
    read_device_type_async,
    read_firmware_version_async,
    read_parallel_config_async,
    read_serial_number_async,
)
from .capabilities import MODBUS_CAPABILITIES, TransportCapabilities
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
    from pymodbus.client import AsyncModbusSerialClient

    from pylxpweb.devices.inverters._features import InverterFamily
    from pylxpweb.transports.register_maps import (
        EnergyRegisterMap,
        RuntimeRegisterMap,
    )

_LOGGER = logging.getLogger(__name__)

# Register group definitions (same as Modbus TCP)
INPUT_REGISTER_GROUPS = {
    "power_energy": (0, 32),
    "status_energy": (32, 32),
    "temperatures": (64, 16),
    "bms_data": (80, 33),
    "extended_data": (113, 18),
    "eps_split_phase": (140, 3),
    "output_power": (170, 2),
}


class ModbusSerialTransport(BaseTransport):
    """Modbus RTU serial transport for local inverter communication.

    This transport connects directly to the inverter via a USB-to-RS485
    serial adapter using Modbus RTU protocol.

    IMPORTANT: Single-Client Limitation
    ------------------------------------
    Serial ports support only ONE concurrent connection.
    Running multiple clients causes communication errors and data corruption.

    Ensure only ONE integration/script connects to each serial port at a time.

    Example:
        transport = ModbusSerialTransport(
            port="/dev/ttyUSB0",
            baudrate=19200,
            serial="CE12345678",
        )
        await transport.connect()

        runtime = await transport.read_runtime()
        print(f"PV Power: {runtime.pv_total_power}W")

    Note:
        Requires the `pymodbus` and `pyserial` packages to be installed:
        uv add pymodbus pyserial
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 19200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        unit_id: int = 1,
        serial: str = "",
        timeout: float = 10.0,
        inverter_family: InverterFamily | None = None,
    ) -> None:
        """Initialize Modbus serial transport.

        Args:
            port: Serial port path (e.g., /dev/ttyUSB0, COM3, /dev/tty.usbserial)
            baudrate: Serial baud rate (default 19200 for EG4 inverters)
            bytesize: Data bits per byte (default 8)
            parity: Parity setting - 'N' (none), 'E' (even), 'O' (odd)
            stopbits: Number of stop bits (default 1)
            unit_id: Modbus unit/slave ID (default 1)
            serial: Inverter serial number (for identification)
            timeout: Connection and operation timeout in seconds
            inverter_family: Inverter model family for correct register mapping.
                If None, defaults to PV_SERIES (EG4-18KPV) for backward
                compatibility.
        """
        super().__init__(serial)
        self._port = port
        self._baudrate = baudrate
        self._bytesize = bytesize
        self._parity = parity
        self._stopbits = stopbits
        self._unit_id = unit_id
        self._timeout = timeout
        self._inverter_family = inverter_family
        self._client: AsyncModbusSerialClient | None = None
        self._lock = asyncio.Lock()
        self._consecutive_errors: int = 0
        self._max_consecutive_errors: int = 3

    @property
    def capabilities(self) -> TransportCapabilities:
        """Get Modbus transport capabilities."""
        return MODBUS_CAPABILITIES

    @property
    def port(self) -> str:
        """Get the serial port path."""
        return self._port

    @property
    def baudrate(self) -> int:
        """Get the serial baud rate."""
        return self._baudrate

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

    async def connect(self) -> None:
        """Establish Modbus RTU serial connection.

        Raises:
            TransportConnectionError: If connection fails
        """
        try:
            from pymodbus.client import AsyncModbusSerialClient

            self._client = AsyncModbusSerialClient(
                port=self._port,
                baudrate=self._baudrate,
                bytesize=self._bytesize,
                parity=self._parity,
                stopbits=self._stopbits,
                timeout=self._timeout,
            )

            connected = await self._client.connect()
            if not connected:
                raise TransportConnectionError(f"Failed to connect to serial port {self._port}")

            self._connected = True
            self._consecutive_errors = 0
            _LOGGER.info(
                "Modbus serial transport connected to %s @ %d baud (unit %s) for %s",
                self._port,
                self._baudrate,
                self._unit_id,
                self._serial,
            )

            # Brief delay to allow serial port to stabilize
            await asyncio.sleep(0.2)

        except ImportError as err:
            raise TransportConnectionError(
                "pymodbus or pyserial package not installed. Install with: uv add pymodbus pyserial"
            ) from err
        except PermissionError as err:
            _LOGGER.error(
                "Permission denied opening serial port %s: %s",
                self._port,
                err,
            )
            raise TransportConnectionError(
                f"Permission denied for {self._port}. "
                "On Linux, add user to 'dialout' group: sudo usermod -a -G dialout $USER"
            ) from err
        except (TimeoutError, OSError) as err:
            _LOGGER.error(
                "Failed to connect to serial port %s: %s",
                self._port,
                err,
            )
            raise TransportConnectionError(
                f"Failed to connect to {self._port}: {err}. "
                "Verify: (1) serial port exists, (2) device is connected, "
                "(3) correct permissions, (4) port is not in use by another application."
            ) from err

    async def disconnect(self) -> None:
        """Close Modbus serial connection."""
        if self._client:
            self._client.close()
            self._client = None

        self._connected = False
        _LOGGER.debug("Modbus serial transport disconnected for %s", self._serial)

    async def _reconnect(self) -> None:
        """Reconnect Modbus client to reset state."""
        async with self._lock:
            if self._consecutive_errors < self._max_consecutive_errors:
                return

            _LOGGER.warning(
                "Reconnecting Modbus serial client for %s after %d consecutive errors",
                self._serial,
                self._consecutive_errors,
            )
            await self.disconnect()
            await self.connect()
            self._consecutive_errors = 0

    async def _read_registers(
        self,
        address: int,
        count: int,
        *,
        input_registers: bool,
    ) -> list[int]:
        """Read Modbus registers with error tracking and reconnect support.

        Args:
            address: Starting register address
            count: Number of registers to read (max 40)
            input_registers: True for input registers (FC4), False for holding (FC3)

        Returns:
            List of register values

        Raises:
            TransportReadError: If read fails
            TransportTimeoutError: If operation times out
        """
        self._ensure_connected()

        if self._client is None:
            raise TransportConnectionError("Modbus client not initialized")

        reg_type = "input" if input_registers else "holding"

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
                    _LOGGER.error(
                        "Modbus error reading %s registers at %d: %s",
                        reg_type,
                        address,
                        result,
                    )
                    raise TransportReadError(f"Modbus read error at address {address}: {result}")

                if not hasattr(result, "registers") or result.registers is None:
                    _LOGGER.error(
                        "Invalid Modbus response at address %d: no registers",
                        address,
                    )
                    raise TransportReadError(
                        f"Invalid Modbus response at address {address}: no registers"
                    )

                self._consecutive_errors = 0
                return list(result.registers)

            except ModbusIOException as err:
                self._consecutive_errors += 1
                if "timeout" in str(err).lower():
                    _LOGGER.error("Timeout reading %s registers at %d", reg_type, address)
                    raise TransportTimeoutError(
                        f"Timeout reading {reg_type} registers at {address}"
                    ) from err
                _LOGGER.error("Failed to read %s registers at %d: %s", reg_type, address, err)
                raise TransportReadError(
                    f"Failed to read {reg_type} registers at {address}: {err}"
                ) from err
            except TimeoutError as err:
                self._consecutive_errors += 1
                _LOGGER.error("Timeout reading %s registers at %d", reg_type, address)
                raise TransportTimeoutError(
                    f"Timeout reading {reg_type} registers at {address}"
                ) from err
            except OSError as err:
                self._consecutive_errors += 1
                _LOGGER.error("Failed to read %s registers at %d: %s", reg_type, address, err)
                raise TransportReadError(
                    f"Failed to read {reg_type} registers at {address}: {err}"
                ) from err

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
                error_msg = str(err)
                if "timeout" in error_msg.lower():
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

    async def _read_register_groups(
        self,
        group_names: list[str] | None = None,
    ) -> dict[int, int]:
        """Read multiple register groups sequentially with inter-group delays."""
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

            # Brief delay between groups for serial stability
            if i < len(groups) - 1:
                await asyncio.sleep(0.05)

        return registers

    async def read_runtime(self) -> InverterRuntimeData:
        """Read runtime data via Modbus input registers."""
        input_registers = await self._read_register_groups()
        return InverterRuntimeData.from_modbus_registers(input_registers, self.runtime_register_map)

    async def read_energy(self) -> InverterEnergyData:
        """Read energy statistics via Modbus input registers."""
        input_registers = await self._read_register_groups(["power_energy", "status_energy"])

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
        """Read battery information via Modbus."""
        from pylxpweb.transports.register_maps import (
            INDIVIDUAL_BATTERY_BASE_ADDRESS,
            INDIVIDUAL_BATTERY_MAX_COUNT,
            INDIVIDUAL_BATTERY_REGISTER_COUNT,
        )

        if self._consecutive_errors >= self._max_consecutive_errors:
            await self._reconnect()

        all_registers: dict[int, int] = {}

        power_regs = await self._read_input_registers(0, 32)
        for i, value in enumerate(power_regs):
            all_registers[i] = value

        try:
            bms_values = await self._read_input_registers(80, 33)
            for offset, value in enumerate(bms_values):
                all_registers[80 + offset] = value
        except Exception as e:
            _LOGGER.warning("Failed to read BMS registers 80-112: %s", e)

        battery_count = all_registers.get(96, 0)

        individual_registers: dict[int, int] | None = None
        if include_individual and battery_count > 0:
            individual_registers = {}
            batteries_to_read = min(battery_count, INDIVIDUAL_BATTERY_MAX_COUNT)
            total_registers = batteries_to_read * INDIVIDUAL_BATTERY_REGISTER_COUNT

            try:
                start_addr = INDIVIDUAL_BATTERY_BASE_ADDRESS
                remaining = total_registers
                current_addr = start_addr

                while remaining > 0:
                    chunk_size = min(remaining, 40)
                    values = await self._read_input_registers(current_addr, chunk_size)
                    for offset, value in enumerate(values):
                        individual_registers[current_addr + offset] = value
                    current_addr += chunk_size
                    remaining -= chunk_size

                _LOGGER.debug(
                    "Read individual battery data for %d batteries",
                    batteries_to_read,
                )
            except Exception as e:
                _LOGGER.warning(
                    "Failed to read individual battery registers: %s",
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
                "Loaded %d individual batteries via Modbus serial",
                len(result.batteries),
            )

        return result

    async def read_parameters(
        self,
        start_address: int,
        count: int,
    ) -> dict[int, int]:
        """Read configuration parameters via Modbus holding registers."""
        result: dict[int, int] = {}

        remaining = count
        current_address = start_address

        while remaining > 0:
            chunk_size = min(remaining, 40)
            values = await self._read_holding_registers(current_address, chunk_size)

            for offset, value in enumerate(values):
                result[current_address + offset] = value

            current_address += chunk_size
            remaining -= chunk_size

        return result

    async def write_parameters(
        self,
        parameters: dict[int, int],
    ) -> bool:
        """Write configuration parameters via Modbus holding registers."""
        sorted_params = sorted(parameters.items())

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

    async def read_serial_number(self) -> str:
        """Read inverter serial number from input registers 115-119."""
        return await read_serial_number_async(self._read_input_registers, self._serial)

    async def read_firmware_version(self) -> str:
        """Read full firmware version code from holding registers 7-10."""
        return await read_firmware_version_async(self._read_holding_registers)

    async def validate_serial(self, expected_serial: str) -> bool:
        """Validate that the connected inverter matches the expected serial."""
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
        """Read device type code from register 19."""
        return await read_device_type_async(self._read_holding_registers)

    def is_midbox_device(self, device_type_code: int) -> bool:
        """Check if device type code indicates a MID/GridBOSS device."""
        return is_midbox_device(device_type_code)

    async def read_parallel_config(self) -> int:
        """Read parallel configuration from input register 113."""
        return await read_parallel_config_async(self._read_input_registers, self._serial)

    async def read_midbox_runtime(self) -> MidboxRuntimeData:
        """Read runtime data from a MID/GridBOSS device."""
        from pylxpweb.transports.register_maps import (
            GRIDBOSS_ENERGY_MAP,
            GRIDBOSS_RUNTIME_MAP,
        )

        input_registers: dict[int, int] = {}

        try:
            # All reads capped at 40 registers (hardware limit)
            # Registers 0-39 (voltages, currents, power, smart loads 1-3)
            values = await self._read_input_registers(0, 40)
            for offset, value in enumerate(values):
                input_registers[offset] = value
            await asyncio.sleep(0.05)

            # Registers 40-67 (smart load 4 power + energy today)
            values = await self._read_input_registers(40, 28)
            for offset, value in enumerate(values):
                input_registers[40 + offset] = value
            await asyncio.sleep(0.05)

            # Registers 68-107 (energy totals)
            values = await self._read_input_registers(68, 40)
            for offset, value in enumerate(values):
                input_registers[68 + offset] = value
            await asyncio.sleep(0.05)

            # Registers 108-119 (smart port 4 status + AC couple totals)
            values = await self._read_input_registers(108, 12)
            for offset, value in enumerate(values):
                input_registers[108 + offset] = value
            await asyncio.sleep(0.05)

            # Registers 128-131 (frequencies)
            freq_values = await self._read_input_registers(128, 4)
            for offset, value in enumerate(freq_values):
                input_registers[128 + offset] = value

        except Exception as e:
            _LOGGER.error("Failed to read MID input registers: %s", e)
            raise TransportReadError(f"Failed to read MID registers: {e}") from e

        return MidboxRuntimeData.from_modbus_registers(
            input_registers, GRIDBOSS_RUNTIME_MAP, GRIDBOSS_ENERGY_MAP
        )

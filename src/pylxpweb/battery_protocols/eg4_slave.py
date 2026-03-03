"""EG4 slave battery protocol (standard EG4-LL register map).

Used by batteries with unit ID 2+ on the RS485 daisy chain.
Register map sourced from ricardocello's eg4_waveshare.py.

Register layout:
  - Regs 0-38: Runtime state (voltage, current, cells, temps, SOC, etc.)
  - Regs 105-127: Device info (model, firmware, serial)
"""

from __future__ import annotations

import struct

from pylxpweb.constants.scaling import ScaleFactor
from pylxpweb.transports.data import BatteryData

from .base import BatteryProtocol, BatteryRegister, BatteryRegisterBlock

# Runtime registers (0-38)
_RUNTIME_REGISTERS = (
    BatteryRegister(0, "voltage", ScaleFactor.SCALE_100, unit="V"),
    BatteryRegister(1, "current", ScaleFactor.SCALE_100, signed=True, unit="A"),
    # Cell voltages 2-17 handled dynamically based on num_cells (reg 36)
    BatteryRegister(18, "pcb_temp", ScaleFactor.SCALE_NONE, signed=True, unit="\u00b0C"),
    BatteryRegister(19, "avg_temp", ScaleFactor.SCALE_NONE, signed=True, unit="\u00b0C"),
    BatteryRegister(20, "max_temp", ScaleFactor.SCALE_NONE, signed=True, unit="\u00b0C"),
    BatteryRegister(21, "remaining_capacity", ScaleFactor.SCALE_NONE, unit="Ah"),
    BatteryRegister(22, "max_charge_current", ScaleFactor.SCALE_NONE, unit="A"),
    BatteryRegister(23, "soh", ScaleFactor.SCALE_NONE, unit="%"),
    BatteryRegister(24, "soc", ScaleFactor.SCALE_NONE, unit="%"),
    BatteryRegister(25, "status", ScaleFactor.SCALE_NONE),
    BatteryRegister(26, "warning", ScaleFactor.SCALE_NONE),
    BatteryRegister(27, "protection", ScaleFactor.SCALE_NONE),
    BatteryRegister(28, "error", ScaleFactor.SCALE_NONE),
    # Regs 29-30: cycle count (32-bit BE), handled in decode()
    # Regs 31-32: full capacity (32-bit), not used in basic decode
    BatteryRegister(36, "num_cells", ScaleFactor.SCALE_NONE),
    BatteryRegister(37, "designed_capacity", ScaleFactor.SCALE_10, unit="Ah"),
    BatteryRegister(38, "balance_bitmap", ScaleFactor.SCALE_NONE),
)

_RUNTIME_BLOCK = BatteryRegisterBlock(start=0, count=39, registers=_RUNTIME_REGISTERS)
_INFO_BLOCK = BatteryRegisterBlock(start=105, count=23, registers=())


def _decode_ascii(registers: dict[int, int], start: int, count: int) -> str:
    """Decode register values as ASCII (high byte, low byte per register).

    Args:
        registers: Dict mapping register address to raw 16-bit value.
        start: First register address to decode.
        count: Number of registers to decode.

    Returns:
        Decoded ASCII string with null bytes and whitespace stripped.
    """
    raw_bytes = bytearray()
    for i in range(count):
        val = registers.get(start + i, 0)
        raw_bytes.append((val >> 8) & 0xFF)
        raw_bytes.append(val & 0xFF)
    return raw_bytes.decode("ascii", errors="replace").replace("\x00", "").strip()


def _signed_int16(raw: int) -> int:
    """Interpret a raw unsigned 16-bit value as signed int16.

    Args:
        raw: Unsigned 16-bit register value.

    Returns:
        Signed integer in range [-32768, 32767].
    """
    return struct.unpack("h", struct.pack("H", raw & 0xFFFF))[0]


class EG4SlaveProtocol(BatteryProtocol):
    """Standard EG4-LL register map for slave batteries (unit ID 2+).

    Decodes runtime registers (0-38) and device info registers (105-127)
    into a BatteryData object with all values properly scaled.
    """

    name = "eg4_slave"
    register_blocks = [_RUNTIME_BLOCK, _INFO_BLOCK]

    def decode(self, raw_regs: dict[int, int], battery_index: int = 0) -> BatteryData:
        """Decode slave battery registers into BatteryData.

        Args:
            raw_regs: Dict mapping register address to raw 16-bit value.
            battery_index: 0-based index of the battery in the bank.

        Returns:
            BatteryData with all values properly scaled.
        """
        # Voltage (reg 0): /100
        voltage = self.decode_register(
            BatteryRegister(0, "voltage", ScaleFactor.SCALE_100, unit="V"),
            raw_regs.get(0, 0),
        )

        # Current (reg 1): /100, signed
        current = self.decode_register(
            BatteryRegister(1, "current", ScaleFactor.SCALE_100, signed=True, unit="A"),
            raw_regs.get(1, 0),
        )

        # Number of cells (reg 36)
        num_cells = raw_regs.get(36, 0)

        # Cell voltages (regs 2-17): /1000
        cell_voltages = [raw_regs.get(2 + i, 0) / 1000.0 for i in range(num_cells)]
        non_zero_cells = [v for v in cell_voltages if v > 0]

        # Temperatures (signed): PCB=reg18, avg=reg19, max=reg20
        pcb_temp = _signed_int16(raw_regs.get(18, 0))
        max_temp = _signed_int16(raw_regs.get(20, 0))

        # SOC (reg 24) and SOH (reg 23): direct, no scaling
        soc = raw_regs.get(24, 0)
        soh = raw_regs.get(23, 100)

        # Remaining capacity (reg 21): direct Ah
        remaining_capacity = float(raw_regs.get(21, 0))

        # Max charge current (reg 22): direct A
        max_charge_current = float(raw_regs.get(22, 0))

        # Designed capacity (reg 37): /10
        max_capacity = raw_regs.get(37, 0) / 10.0

        # Cycle count (regs 29-30): 32-bit big-endian
        cycle_count = (raw_regs.get(29, 0) << 16) | raw_regs.get(30, 0)

        # Status/warning/protection bitfields
        status = raw_regs.get(25, 0)
        warning = raw_regs.get(26, 0)
        fault = raw_regs.get(27, 0)

        # Device info (if available in register map)
        model = _decode_ascii(raw_regs, 105, 12)
        firmware = _decode_ascii(raw_regs, 117, 3)
        serial = _decode_ascii(raw_regs, 120, 8)

        return BatteryData(
            battery_index=battery_index,
            serial_number=serial,
            voltage=voltage,
            current=current,
            soc=soc,
            soh=soh,
            temperature=float(max_temp),
            max_capacity=max_capacity,
            current_capacity=remaining_capacity if remaining_capacity > 0 else None,
            cycle_count=cycle_count,
            cell_count=num_cells,
            cell_voltages=cell_voltages,
            min_cell_voltage=min(non_zero_cells) if non_zero_cells else 0.0,
            max_cell_voltage=max(non_zero_cells) if non_zero_cells else 0.0,
            min_cell_temperature=float(pcb_temp),
            max_cell_temperature=float(max_temp),
            charge_current_limit=max_charge_current,
            model=model,
            firmware_version=firmware,
            status=status,
            warning_code=warning,
            fault_code=fault,
        )

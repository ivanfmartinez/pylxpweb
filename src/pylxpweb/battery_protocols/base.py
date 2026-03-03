"""Base classes for battery protocol definitions."""

from __future__ import annotations

import struct
from dataclasses import dataclass

from pylxpweb.constants.scaling import ScaleFactor, apply_scale
from pylxpweb.transports.data import BatteryData


@dataclass(frozen=True)
class BatteryRegister:
    """Single register field definition.

    Attributes:
        address: Modbus register address.
        name: Canonical field name (e.g. "voltage", "current").
        scale: How to convert raw 16-bit value to real units.
        signed: If True, interpret raw value as signed int16.
        unit: Display unit string ("V", "A", "°C", "%").
    """

    address: int
    name: str
    scale: ScaleFactor
    signed: bool = False
    unit: str = ""


@dataclass(frozen=True)
class BatteryRegisterBlock:
    """Contiguous block of registers to read in one Modbus call.

    Attributes:
        start: First register address in the block.
        count: Number of contiguous registers to read.
        registers: Field definitions for registers within this block.
    """

    start: int
    count: int
    registers: tuple[BatteryRegister, ...]


class BatteryProtocol:
    """Base class for battery protocol definitions.

    Subclasses define register_blocks and override decode() to produce
    BatteryData from raw register values.
    """

    name: str = "base"
    register_blocks: list[BatteryRegisterBlock] = []

    @staticmethod
    def decode_register(reg: BatteryRegister, raw_value: int) -> float:
        """Decode a single raw register value using the register definition.

        Args:
            reg: Register definition with scaling and sign info.
            raw_value: Raw unsigned 16-bit value from Modbus.

        Returns:
            Scaled float value in proper units.
        """
        if reg.signed:
            raw_value = struct.unpack("h", struct.pack("H", raw_value & 0xFFFF))[0]
        return apply_scale(raw_value, reg.scale)

    def decode(self, raw_regs: dict[int, int], battery_index: int = 0) -> BatteryData:
        """Decode raw registers into a BatteryData object.

        Subclasses must override this method.

        Args:
            raw_regs: Dict mapping register address to raw 16-bit value.
            battery_index: 0-based index of the battery in the bank.

        Returns:
            BatteryData with all values properly scaled.
        """
        raise NotImplementedError

"""Tests for battery protocol base classes."""

from __future__ import annotations

import struct

import pytest

from pylxpweb.battery_protocols.base import (
    BatteryProtocol,
    BatteryRegister,
    BatteryRegisterBlock,
)
from pylxpweb.constants.scaling import ScaleFactor


class TestBatteryRegister:
    """Tests for BatteryRegister dataclass."""

    def test_basic_register(self) -> None:
        reg = BatteryRegister(address=22, name="voltage", scale=ScaleFactor.SCALE_100, unit="V")
        assert reg.address == 22
        assert reg.name == "voltage"
        assert reg.scale == ScaleFactor.SCALE_100
        assert reg.signed is False
        assert reg.unit == "V"

    def test_signed_register(self) -> None:
        reg = BatteryRegister(
            address=23,
            name="current",
            scale=ScaleFactor.SCALE_100,
            signed=True,
            unit="A",
        )
        assert reg.signed is True

    def test_frozen(self) -> None:
        reg = BatteryRegister(address=0, name="x", scale=ScaleFactor.SCALE_NONE)
        with pytest.raises(AttributeError):
            reg.address = 5  # type: ignore[misc]


class TestBatteryRegisterBlock:
    """Tests for BatteryRegisterBlock."""

    def test_block_creation(self) -> None:
        regs = (
            BatteryRegister(address=22, name="voltage", scale=ScaleFactor.SCALE_100, unit="V"),
            BatteryRegister(
                address=23,
                name="current",
                scale=ScaleFactor.SCALE_100,
                signed=True,
                unit="A",
            ),
        )
        block = BatteryRegisterBlock(start=19, count=23, registers=regs)
        assert block.start == 19
        assert block.count == 23
        assert len(block.registers) == 2


class TestBatteryProtocol:
    """Tests for BatteryProtocol base class."""

    def test_decode_unsigned(self) -> None:
        """Protocol.decode_register handles unsigned values."""
        reg = BatteryRegister(address=22, name="voltage", scale=ScaleFactor.SCALE_100, unit="V")
        result = BatteryProtocol.decode_register(reg, 5294)
        assert result == pytest.approx(52.94)

    def test_decode_signed_negative(self) -> None:
        """Protocol.decode_register handles signed negative values."""
        reg = BatteryRegister(
            address=23,
            name="current",
            scale=ScaleFactor.SCALE_100,
            signed=True,
            unit="A",
        )
        # -3080 as unsigned 16-bit = 62456
        raw = struct.unpack("H", struct.pack("h", -3080))[0]
        result = BatteryProtocol.decode_register(reg, raw)
        assert result == pytest.approx(-30.80)

    def test_decode_no_scale(self) -> None:
        """Protocol.decode_register with SCALE_NONE returns float."""
        reg = BatteryRegister(address=41, name="num_cells", scale=ScaleFactor.SCALE_NONE)
        result = BatteryProtocol.decode_register(reg, 16)
        assert result == 16.0

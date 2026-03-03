"""Tests for battery protocol base classes."""

from __future__ import annotations

import struct

import pytest

from pylxpweb.battery_protocols.base import (
    BatteryProtocol,
    BatteryRegister,
    BatteryRegisterBlock,
    decode_ascii,
    signed_int16,
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


class TestSignedInt16:
    """Tests for the signed_int16 utility function."""

    def test_positive_value(self) -> None:
        assert signed_int16(100) == 100

    def test_negative_value(self) -> None:
        raw = struct.unpack("H", struct.pack("h", -5))[0]
        assert signed_int16(raw) == -5

    def test_zero(self) -> None:
        assert signed_int16(0) == 0

    def test_max_positive(self) -> None:
        assert signed_int16(32767) == 32767

    def test_min_negative(self) -> None:
        assert signed_int16(32768) == -32768


class TestDecodeAscii:
    """Tests for the decode_ascii utility function."""

    def test_basic_string(self) -> None:
        regs = {0: 0x4142, 1: 0x4344}  # "ABCD"
        assert decode_ascii(regs, 0, 2) == "ABCD"

    def test_with_null_bytes(self) -> None:
        regs = {0: 0x4142, 1: 0x0000}  # "AB\x00\x00"
        assert decode_ascii(regs, 0, 2) == "AB"

    def test_missing_registers(self) -> None:
        regs: dict[int, int] = {}
        assert decode_ascii(regs, 0, 2) == ""

    def test_offset_start(self) -> None:
        regs = {105: 0x4547, 106: 0x342D}  # "EG4-"
        assert decode_ascii(regs, 105, 2) == "EG4-"


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


class TestDecodeCellVoltages:
    """Tests for BatteryProtocol.decode_cell_voltages."""

    def test_basic_cells(self) -> None:
        raw = {2: 3310, 3: 3320, 4: 3330, 5: 3340}
        cells, min_v, max_v = BatteryProtocol.decode_cell_voltages(
            raw, start_address=2, num_cells=4
        )
        assert len(cells) == 4
        assert cells[0] == pytest.approx(3.310)
        assert cells[3] == pytest.approx(3.340)
        assert min_v == pytest.approx(3.310)
        assert max_v == pytest.approx(3.340)

    def test_zero_cells(self) -> None:
        raw: dict[int, int] = {}
        cells, min_v, max_v = BatteryProtocol.decode_cell_voltages(
            raw, start_address=2, num_cells=0
        )
        assert cells == []
        assert min_v == 0.0
        assert max_v == 0.0

    def test_all_zero_values(self) -> None:
        raw = {2: 0, 3: 0, 4: 0}
        cells, min_v, max_v = BatteryProtocol.decode_cell_voltages(
            raw, start_address=2, num_cells=3
        )
        assert len(cells) == 3
        assert min_v == 0.0
        assert max_v == 0.0

    def test_offset_start_address(self) -> None:
        raw = {113: 3308, 114: 3310}
        cells, min_v, max_v = BatteryProtocol.decode_cell_voltages(
            raw, start_address=113, num_cells=2
        )
        assert cells[0] == pytest.approx(3.308)
        assert cells[1] == pytest.approx(3.310)


class TestRegLookup:
    """Tests for BatteryProtocol._reg name-based lookup."""

    def test_lookup_existing(self) -> None:
        from pylxpweb.battery_protocols.eg4_slave import EG4SlaveProtocol

        proto = EG4SlaveProtocol()
        reg = proto._reg("voltage")
        assert reg.address == 0
        assert reg.scale == ScaleFactor.SCALE_100

    def test_lookup_missing_raises(self) -> None:
        from pylxpweb.battery_protocols.eg4_slave import EG4SlaveProtocol

        proto = EG4SlaveProtocol()
        with pytest.raises(KeyError, match="nonexistent"):
            proto._reg("nonexistent")

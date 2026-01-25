"""Tests for binary formatter."""

from datetime import datetime

import pytest

from pylxpweb.cli.collectors.base import CollectionResult
from pylxpweb.cli.formatters.base import DiagnosticData
from pylxpweb.cli.formatters.binary import BinaryFormatter, BinaryReader


class TestBinaryFormatter:
    """Tests for BinaryFormatter."""

    def test_format_basic(self) -> None:
        """Test basic binary formatting."""
        data = DiagnosticData(
            collections=[
                CollectionResult(
                    source="modbus",
                    timestamp=datetime(2026, 1, 25, 12, 0, 0),
                    serial_number="CE12345678",
                    input_registers={0: 100, 1: 200},
                    holding_registers={0: 50},
                )
            ],
            timestamp=datetime(2026, 1, 25, 12, 0, 0),
        )

        formatter = BinaryFormatter(sanitize=False)
        output = formatter.format(data)

        # Check magic header
        assert output[:4] == b"LXPD"
        # Check version
        assert output[4] == 1
        # Check it's binary
        assert formatter.is_binary is True
        assert formatter.file_extension == "bin"

    def test_format_with_sanitization(self) -> None:
        """Test binary formatting with sanitization."""
        data = DiagnosticData(
            collections=[
                CollectionResult(
                    source="modbus",
                    timestamp=datetime(2026, 1, 25, 12, 0, 0),
                    serial_number="CE12345678",
                    input_registers={0: 100},
                    holding_registers={},
                )
            ],
            timestamp=datetime(2026, 1, 25, 12, 0, 0),
        )

        formatter = BinaryFormatter(sanitize=True)
        output = formatter.format(data)

        # Check sanitization flag is set
        flags = output[5]
        assert flags & BinaryFormatter.FLAG_SANITIZED

    def test_format_multiple_sources(self) -> None:
        """Test binary formatting with multiple collections."""
        data = DiagnosticData(
            collections=[
                CollectionResult(
                    source="modbus",
                    timestamp=datetime(2026, 1, 25, 12, 0, 0),
                    serial_number="CE12345678",
                    input_registers={0: 100},
                    holding_registers={},
                ),
                CollectionResult(
                    source="dongle",
                    timestamp=datetime(2026, 1, 25, 12, 0, 0),
                    serial_number="CE12345678",
                    input_registers={0: 100},
                    holding_registers={},
                ),
            ],
            timestamp=datetime(2026, 1, 25, 12, 0, 0),
        )

        formatter = BinaryFormatter(sanitize=False, include_all_sources=True)
        output = formatter.format(data)

        # Check multi-source flag is set
        flags = output[5]
        assert flags & BinaryFormatter.FLAG_MULTI_SOURCE


class TestBinaryReader:
    """Tests for BinaryReader."""

    def test_roundtrip(self) -> None:
        """Test formatting and parsing roundtrip."""
        data = DiagnosticData(
            collections=[
                CollectionResult(
                    source="modbus",
                    timestamp=datetime(2026, 1, 25, 12, 0, 0),
                    serial_number="CE12345678",
                    input_registers={0: 100, 10: 65535, 20: 0},
                    holding_registers={0: 50, 5: 1234},
                )
            ],
            timestamp=datetime(2026, 1, 25, 12, 0, 0),
        )

        formatter = BinaryFormatter(sanitize=False)
        binary_data = formatter.format(data)

        reader = BinaryReader()
        parsed = reader.parse(binary_data)

        assert parsed["serial_number"] == "CE12345678"
        assert len(parsed["collections"]) == 1

        collection = parsed["collections"][0]
        assert collection["source"] == "modbus"
        assert collection["input_registers"][0] == 100
        assert collection["input_registers"][10] == 65535
        assert collection["input_registers"][20] == 0
        assert collection["holding_registers"][0] == 50
        assert collection["holding_registers"][5] == 1234

    def test_invalid_magic(self) -> None:
        """Test parsing with invalid magic header."""
        reader = BinaryReader()

        with pytest.raises(ValueError, match="Invalid magic header"):
            reader.parse(b"XXXX" + bytes(100))

    def test_data_too_short(self) -> None:
        """Test parsing with data too short."""
        reader = BinaryReader()

        with pytest.raises(ValueError, match="Data too short"):
            reader.parse(b"LXPD")

    def test_unsupported_version(self) -> None:
        """Test parsing with unsupported version."""
        reader = BinaryReader()

        # Magic + version 99 + rest
        data = b"LXPD" + bytes([99]) + bytes(20)

        with pytest.raises(ValueError, match="Unsupported version"):
            reader.parse(data)

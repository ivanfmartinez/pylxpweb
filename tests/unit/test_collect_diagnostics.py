"""Unit tests for diagnostic data collection script."""

from __future__ import annotations

# Import sanitization functions from the utils script
import sys
from pathlib import Path

import pytest

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))

from collect_diagnostics import sanitize_diagnostics, sanitize_value


class TestSanitizeValue:
    """Tests for sanitize_value function."""

    def test_sanitize_serial_number_long(self) -> None:
        """Test sanitization of long serial number."""
        result = sanitize_value("serialNum", "4512670118")
        assert result == "45******18"
        assert len(result) == len("4512670118")

    def test_sanitize_serial_number_short(self) -> None:
        """Test sanitization of short serial number."""
        result = sanitize_value("serial", "1234")
        assert result == "****"
        assert len(result) == 4

    def test_sanitize_serial_number_empty(self) -> None:
        """Test sanitization of empty serial number."""
        result = sanitize_value("serialNum", "")
        assert result == ""

    def test_sanitize_serial_number_various_keys(self) -> None:
        """Test sanitization works with various serial number key names."""
        serial = "1234567890"
        expected = "12******90"

        assert sanitize_value("serial", serial) == expected
        assert sanitize_value("serialNum", serial) == expected
        assert sanitize_value("serial_number", serial) == expected
        assert sanitize_value("device_sn", serial) == expected
        assert sanitize_value("inverter_sn", serial) == expected
        assert sanitize_value("SERIAL_NUM", serial) == expected  # case insensitive

    def test_sanitize_address(self) -> None:
        """Test sanitization of street address."""
        result = sanitize_value("address", "6245 N WILLARD AVE")
        assert result == "123 Example Street, City, State"

    def test_sanitize_various_address_keys(self) -> None:
        """Test sanitization works with various address key names."""
        address = "123 Main St"
        expected = "123 Example Street, City, State"

        assert sanitize_value("address", address) == expected
        assert sanitize_value("street", address) == expected
        assert sanitize_value("location", address) == expected
        assert sanitize_value("addr", address) == expected
        assert sanitize_value("ADDRESS", address) == expected  # case insensitive

    def test_sanitize_gps_coordinates(self) -> None:
        """Test sanitization of GPS coordinates."""
        assert sanitize_value("latitude", 37.7749) == 0.0
        assert sanitize_value("longitude", -122.4194) == 0.0
        assert sanitize_value("lat", 37.7749) == 0.0
        assert sanitize_value("lon", -122.4194) == 0.0
        assert sanitize_value("lng", -122.4194) == 0.0

    def test_sanitize_plant_name_with_address(self) -> None:
        """Test sanitization of plant name containing address."""
        result = sanitize_value("name", "6245 N WILLARD AVE")
        assert result == "Example Station"

        result = sanitize_value("plant_name", "123 Main Street Unit 5")
        assert result == "Example Station"

    def test_sanitize_plant_name_safe(self) -> None:
        """Test that ALL station/plant names are sanitized (privacy requirement)."""
        # Station names are ALWAYS sanitized, even if they don't look like addresses
        result = sanitize_value("name", "My Home Solar")
        assert result == "Example Station"

        result = sanitize_value("station_name", "East Wing")
        assert result == "Example Station"

    def test_sanitize_nested_dict(self) -> None:
        """Test sanitization of nested dictionary."""
        data = {
            "serialNum": "1234567890",
            "address": "123 Main St",
            "nested": {
                "serial": "9876543210",
                "location": "456 Oak Ave",
            },
        }

        result = sanitize_value("data", data)

        assert result["serialNum"] == "12******90"
        assert result["address"] == "123 Example Street, City, State"
        assert result["nested"]["serial"] == "98******10"
        assert result["nested"]["location"] == "123 Example Street, City, State"

    def test_sanitize_list(self) -> None:
        """Test sanitization of list."""
        data = [
            {"serialNum": "1234567890"},
            {"serialNum": "9876543210"},
        ]

        result = sanitize_value("inverters", data)

        assert result[0]["serialNum"] == "12******90"
        assert result[1]["serialNum"] == "98******10"

    def test_sanitize_preserves_safe_values(self) -> None:
        """Test that non-sensitive values are preserved."""
        assert sanitize_value("model", "EG4-18KPV") == "EG4-18KPV"
        assert sanitize_value("status", "Online") == "Online"
        assert sanitize_value("soc", 85) == 85
        assert sanitize_value("voltage", 53.9) == 53.9
        assert sanitize_value("enabled", True) is True


class TestSanitizeDiagnostics:
    """Tests for sanitize_diagnostics function."""

    def test_sanitize_complete_diagnostics(self) -> None:
        """Test sanitization of complete diagnostic structure."""
        diagnostics = {
            "collection_timestamp": "2025-11-20T14:30:00",
            "pylxpweb_version": "0.2.2",
            "base_url": "https://monitor.eg4electronics.com",
            "stations": [
                {
                    "id": 12345,
                    "name": "6245 N WILLARD AVE",
                    "location": "6245 N WILLARD AVE, Chicago, IL",
                    "parallel_groups": [
                        {
                            "mid_device": {
                                "serial_number": "4524850115",
                                "model": "MID-GridBOSS",
                            },
                            "inverters": [
                                {
                                    "serial_number": "4512670118",
                                    "model": "EG4-18KPV",
                                    "battery_bank": {
                                        "batteries": [
                                            {
                                                "battery_index": 0,
                                                "voltage": 53.94,
                                                "soc": 85,
                                            }
                                        ]
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        result = sanitize_diagnostics(diagnostics)

        # Check sanitization
        station = result["stations"][0]
        assert station["id"] == "00000"  # Station IDs are sanitized (privacy)
        assert station["name"] == "Example Station"
        assert station["location"] == "123 Example Street, City, State"
        mid_device = station["parallel_groups"][0]["mid_device"]
        assert mid_device["serial_number"] == "45******15"
        inverter = station["parallel_groups"][0]["inverters"][0]
        assert inverter["serial_number"] == "45******18"

        # Check preservation of safe data
        assert result["collection_timestamp"] == "2025-11-20T14:30:00"
        assert result["pylxpweb_version"] == "0.2.2"
        assert result["base_url"] == "https://monitor.eg4electronics.com"
        assert mid_device["model"] == "MID-GridBOSS"
        assert inverter["model"] == "EG4-18KPV"
        battery = inverter["battery_bank"]["batteries"][0]
        assert battery["voltage"] == 53.94
        assert battery["soc"] == 85

    def test_sanitize_empty_diagnostics(self) -> None:
        """Test sanitization of empty diagnostic structure."""
        diagnostics = {
            "collection_timestamp": "2025-11-20T14:30:00",
            "stations": [],
        }

        result = sanitize_diagnostics(diagnostics)

        assert result["collection_timestamp"] == "2025-11-20T14:30:00"
        assert result["stations"] == []


class TestAddressDetection:
    """Tests for address detection in plant names."""

    def test_detect_address_with_number_and_street(self) -> None:
        """Test detection of address with number and street keyword."""
        addresses = [
            "6245 N WILLARD AVE",
            "123 Main Street",
            "456 Oak Avenue",
            "789 Pine Road",
            "321 Elm Drive",
            "654 Maple Way",
            "987 Cedar Lane",
            "147 Birch Boulevard",
            "258 Willow Court",
        ]

        for addr in addresses:
            result = sanitize_value("name", addr)
            assert result == "Example Station", f"Failed to detect address: {addr}"

    def test_preserve_safe_plant_names(self) -> None:
        """Test that ALL station/plant names are sanitized (privacy requirement)."""
        # Per user requirement: ALL station names should be redacted for privacy
        names_to_sanitize = [
            "My Home Solar",
            "East Wing",
            "Solar Array 1",
            "Main Building",
            "Garage System",
            "Rooftop Installation",
        ]

        for name in names_to_sanitize:
            result = sanitize_value("name", name)
            assert result == "Example Station", f"Failed to sanitize name: {name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

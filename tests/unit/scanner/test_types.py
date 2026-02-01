"""Unit tests for scanner.types module."""

from __future__ import annotations

import pytest

from pylxpweb.scanner.types import DeviceType, ScanConfig, ScanProgress, ScanResult


class TestDeviceType:
    """Tests for DeviceType enum."""

    def test_modbus_verified_value(self) -> None:
        """Test MODBUS_VERIFIED enum value."""
        assert DeviceType.MODBUS_VERIFIED.value == "modbus_verified"

    def test_modbus_unverified_value(self) -> None:
        """Test MODBUS_UNVERIFIED enum value."""
        assert DeviceType.MODBUS_UNVERIFIED.value == "modbus_unverified"

    def test_dongle_candidate_value(self) -> None:
        """Test DONGLE_CANDIDATE enum value."""
        assert DeviceType.DONGLE_CANDIDATE.value == "dongle_candidate"

    def test_enum_members(self) -> None:
        """Test all enum members are present."""
        expected = {"MODBUS_VERIFIED", "MODBUS_UNVERIFIED", "DONGLE_CANDIDATE"}
        actual = {member.name for member in DeviceType}
        assert actual == expected


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_basic_result(self) -> None:
        """Test creating a basic scan result."""
        result = ScanResult(
            ip="192.168.1.50",
            port=502,
            device_type=DeviceType.MODBUS_UNVERIFIED,
        )
        assert result.ip == "192.168.1.50"
        assert result.port == 502
        assert result.device_type == DeviceType.MODBUS_UNVERIFIED
        assert result.serial is None
        assert result.model_family is None

    def test_verified_result(self) -> None:
        """Test creating a verified Modbus result."""
        result = ScanResult(
            ip="192.168.1.100",
            port=502,
            device_type=DeviceType.MODBUS_VERIFIED,
            serial="4512345678",
            model_family="PV_SERIES",
            device_type_code=2092,
            firmware_version="1.0.5",
            response_time_ms=45.3,
        )
        assert result.ip == "192.168.1.100"
        assert result.serial == "4512345678"
        assert result.model_family == "PV_SERIES"
        assert result.device_type_code == 2092
        assert result.firmware_version == "1.0.5"
        assert result.response_time_ms == 45.3

    def test_dongle_result(self) -> None:
        """Test creating a dongle candidate result."""
        result = ScanResult(
            ip="192.168.1.200",
            port=8000,
            device_type=DeviceType.DONGLE_CANDIDATE,
            mac_address="A4:CF:12:34:56:78",
            mac_vendor="Espressif",
            response_time_ms=12.5,
        )
        assert result.ip == "192.168.1.200"
        assert result.port == 8000
        assert result.device_type == DeviceType.DONGLE_CANDIDATE
        assert result.mac_address == "A4:CF:12:34:56:78"
        assert result.mac_vendor == "Espressif"

    def test_is_verified_property(self) -> None:
        """Test is_verified property."""
        verified = ScanResult(
            ip="192.168.1.1",
            port=502,
            device_type=DeviceType.MODBUS_VERIFIED,
            serial="1234567890",
        )
        unverified = ScanResult(
            ip="192.168.1.2",
            port=502,
            device_type=DeviceType.MODBUS_UNVERIFIED,
        )
        dongle = ScanResult(
            ip="192.168.1.3",
            port=8000,
            device_type=DeviceType.DONGLE_CANDIDATE,
        )

        assert verified.is_verified is True
        assert unverified.is_verified is False
        assert dongle.is_verified is False

    def test_is_dongle_candidate_property(self) -> None:
        """Test is_dongle_candidate property."""
        verified = ScanResult(
            ip="192.168.1.1",
            port=502,
            device_type=DeviceType.MODBUS_VERIFIED,
        )
        unverified = ScanResult(
            ip="192.168.1.2",
            port=502,
            device_type=DeviceType.MODBUS_UNVERIFIED,
        )
        dongle = ScanResult(
            ip="192.168.1.3",
            port=8000,
            device_type=DeviceType.DONGLE_CANDIDATE,
        )

        assert verified.is_dongle_candidate is False
        assert unverified.is_dongle_candidate is False
        assert dongle.is_dongle_candidate is True

    def test_display_label_verified(self) -> None:
        """Test display_label for verified device."""
        result = ScanResult(
            ip="192.168.1.100",
            port=502,
            device_type=DeviceType.MODBUS_VERIFIED,
            serial="4512345678",
            model_family="PV_SERIES",
        )
        expected = "PV_SERIES (4512345678) @ 192.168.1.100:502"
        assert result.display_label == expected

    def test_display_label_verified_no_model_family(self) -> None:
        """Test display_label for verified device without model family."""
        result = ScanResult(
            ip="192.168.1.100",
            port=502,
            device_type=DeviceType.MODBUS_VERIFIED,
            serial="4512345678",
            model_family=None,
        )
        expected = "EG4 (4512345678) @ 192.168.1.100:502"
        assert result.display_label == expected

    def test_display_label_dongle_with_vendor(self) -> None:
        """Test display_label for dongle with MAC vendor."""
        result = ScanResult(
            ip="192.168.1.200",
            port=8000,
            device_type=DeviceType.DONGLE_CANDIDATE,
            mac_address="A4:CF:12:34:56:78",
            mac_vendor="Espressif",
        )
        expected = "Dongle candidate @ 192.168.1.200:8000 (MAC: Espressif)"
        assert result.display_label == expected

    def test_display_label_dongle_no_vendor(self) -> None:
        """Test display_label for dongle without MAC vendor."""
        result = ScanResult(
            ip="192.168.1.200",
            port=8000,
            device_type=DeviceType.DONGLE_CANDIDATE,
            mac_address="AA:BB:CC:DD:EE:FF",
            mac_vendor=None,
        )
        expected = "Dongle candidate @ 192.168.1.200:8000 (MAC: Unknown vendor)"
        assert result.display_label == expected

    def test_display_label_unverified(self) -> None:
        """Test display_label for unverified Modbus device."""
        result = ScanResult(
            ip="192.168.1.50",
            port=502,
            device_type=DeviceType.MODBUS_UNVERIFIED,
        )
        expected = "Modbus device @ 192.168.1.50:502 (unverified)"
        assert result.display_label == expected

    def test_result_with_error(self) -> None:
        """Test result with error message."""
        result = ScanResult(
            ip="192.168.1.50",
            port=502,
            device_type=DeviceType.MODBUS_UNVERIFIED,
            error="Connection timeout",
        )
        assert result.error == "Connection timeout"

    def test_default_response_time(self) -> None:
        """Test default response time is 0.0."""
        result = ScanResult(
            ip="192.168.1.1",
            port=502,
            device_type=DeviceType.MODBUS_UNVERIFIED,
        )
        assert result.response_time_ms == 0.0


class TestScanProgress:
    """Tests for ScanProgress dataclass."""

    def test_basic_progress(self) -> None:
        """Test creating a basic scan progress."""
        progress = ScanProgress(total_hosts=100, scanned=50, found=5)
        assert progress.total_hosts == 100
        assert progress.scanned == 50
        assert progress.found == 5

    def test_percent_property(self) -> None:
        """Test percent property calculation."""
        progress = ScanProgress(total_hosts=100, scanned=50, found=5)
        assert progress.percent == 50.0

    def test_percent_zero_total(self) -> None:
        """Test percent property when total_hosts is 0."""
        progress = ScanProgress(total_hosts=0, scanned=0, found=0)
        assert progress.percent == 100.0

    def test_percent_partial(self) -> None:
        """Test percent property with partial completion."""
        progress = ScanProgress(total_hosts=254, scanned=127, found=3)
        expected = (127 / 254) * 100.0
        assert progress.percent == pytest.approx(expected)

    def test_percent_complete(self) -> None:
        """Test percent property at 100%."""
        progress = ScanProgress(total_hosts=254, scanned=254, found=10)
        assert progress.percent == 100.0

    def test_percent_start(self) -> None:
        """Test percent property at start (0%)."""
        progress = ScanProgress(total_hosts=254, scanned=0, found=0)
        assert progress.percent == 0.0


class TestScanConfig:
    """Tests for ScanConfig dataclass."""

    def test_default_config(self) -> None:
        """Test creating config with default values."""
        config = ScanConfig(ip_range="192.168.1.0/24")
        assert config.ip_range == "192.168.1.0/24"
        assert config.ports == [502, 8000]
        assert config.timeout == 0.5
        assert config.concurrency == 50
        assert config.verify_modbus is True
        assert config.lookup_mac is False

    def test_custom_config(self) -> None:
        """Test creating config with custom values."""
        config = ScanConfig(
            ip_range="192.168.1.1-192.168.1.254",
            ports=[502],
            timeout=1.0,
            concurrency=100,
            verify_modbus=False,
            lookup_mac=True,
        )
        assert config.ip_range == "192.168.1.1-192.168.1.254"
        assert config.ports == [502]
        assert config.timeout == 1.0
        assert config.concurrency == 100
        assert config.verify_modbus is False
        assert config.lookup_mac is True

    def test_single_port_config(self) -> None:
        """Test config with single port."""
        config = ScanConfig(ip_range="192.168.1.100", ports=[502])
        assert config.ports == [502]

    def test_multiple_ports_config(self) -> None:
        """Test config with multiple ports."""
        config = ScanConfig(
            ip_range="192.168.1.0/24",
            ports=[502, 8000, 503],
        )
        assert config.ports == [502, 8000, 503]

    def test_short_timeout_config(self) -> None:
        """Test config with short timeout."""
        config = ScanConfig(ip_range="192.168.1.0/24", timeout=0.1)
        assert config.timeout == 0.1

    def test_high_concurrency_config(self) -> None:
        """Test config with high concurrency."""
        config = ScanConfig(ip_range="192.168.1.0/24", concurrency=200)
        assert config.concurrency == 200

"""Tests for scanner data types."""

from pylxpweb.scanner.types import DeviceType, ScanConfig, ScanProgress, ScanResult


class TestScanResult:
    """Tests for ScanResult."""

    def test_verified_modbus(self):
        result = ScanResult(
            ip="192.168.1.50",
            port=502,
            device_type=DeviceType.MODBUS_VERIFIED,
            serial="4512345678",
            model_family="PV_SERIES",
        )
        assert result.is_verified
        assert not result.is_dongle_candidate
        assert "PV_SERIES" in result.display_label
        assert "4512345678" in result.display_label

    def test_dongle_candidate(self):
        result = ScanResult(
            ip="192.168.1.100",
            port=8000,
            device_type=DeviceType.DONGLE_CANDIDATE,
            mac_vendor="Espressif",
        )
        assert not result.is_verified
        assert result.is_dongle_candidate
        assert "Espressif" in result.display_label

    def test_dongle_candidate_no_mac(self):
        result = ScanResult(
            ip="192.168.1.100",
            port=8000,
            device_type=DeviceType.DONGLE_CANDIDATE,
        )
        assert "Unknown vendor" in result.display_label

    def test_unverified_modbus(self):
        result = ScanResult(
            ip="192.168.1.50",
            port=502,
            device_type=DeviceType.MODBUS_UNVERIFIED,
        )
        assert not result.is_verified
        assert "unverified" in result.display_label


class TestScanProgress:
    """Tests for ScanProgress."""

    def test_percent(self):
        p = ScanProgress(total_hosts=100, scanned=50, found=3)
        assert p.percent == 50.0

    def test_percent_zero(self):
        p = ScanProgress(total_hosts=0, scanned=0, found=0)
        assert p.percent == 100.0

    def test_percent_complete(self):
        p = ScanProgress(total_hosts=254, scanned=254, found=2)
        assert p.percent == 100.0


class TestScanConfig:
    """Tests for ScanConfig defaults."""

    def test_defaults(self):
        config = ScanConfig(ip_range="192.168.1.0/24")
        assert config.ports == [502, 8000]
        assert config.timeout == 0.5
        assert config.concurrency == 50
        assert config.verify_modbus is True
        assert config.lookup_mac is False

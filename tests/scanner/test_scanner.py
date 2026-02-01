"""Tests for NetworkScanner with mocked network I/O."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pylxpweb.scanner.scanner import NetworkScanner
from pylxpweb.scanner.types import DeviceType, ScanConfig, ScanProgress


def _mock_writer() -> MagicMock:
    """Create a mock asyncio StreamWriter."""
    writer = MagicMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    return writer


@pytest.fixture
def scan_config():
    """Config scanning a tiny range for fast tests."""
    return ScanConfig(
        ip_range="192.168.1.1-192.168.1.3",
        ports=[502],
        timeout=0.1,
        concurrency=10,
        verify_modbus=False,
        lookup_mac=False,
    )


class TestNetworkScanner:
    """Tests for NetworkScanner."""

    async def test_scan_no_open_ports(self, scan_config):
        """All connections refused → no results."""
        with patch("pylxpweb.scanner.scanner.asyncio.open_connection", side_effect=OSError):
            scanner = NetworkScanner(scan_config)
            results = [r async for r in scanner.scan()]
            assert results == []

    async def test_scan_finds_open_port(self, scan_config):
        """One host has port 502 open → one result."""
        call_count = 0

        async def mock_open_connection(host, port):
            nonlocal call_count
            call_count += 1
            if host == "192.168.1.2":
                return MagicMock(), _mock_writer()
            raise ConnectionRefusedError()

        target = "pylxpweb.scanner.scanner.asyncio.open_connection"
        with patch(target, side_effect=mock_open_connection):
            scanner = NetworkScanner(scan_config)
            results = [r async for r in scanner.scan()]

        assert len(results) == 1
        assert results[0].ip == "192.168.1.2"
        assert results[0].port == 502
        assert results[0].device_type == DeviceType.MODBUS_UNVERIFIED

    async def test_scan_dongle_port(self):
        """Port 8000 open → dongle candidate."""
        config = ScanConfig(
            ip_range="192.168.1.5",
            ports=[8000],
            timeout=0.1,
            verify_modbus=False,
            lookup_mac=False,
        )

        async def mock_open(host, port):
            return MagicMock(), _mock_writer()

        with patch("pylxpweb.scanner.scanner.asyncio.open_connection", side_effect=mock_open):
            scanner = NetworkScanner(config)
            results = [r async for r in scanner.scan()]

        assert len(results) == 1
        assert results[0].device_type == DeviceType.DONGLE_CANDIDATE

    async def test_scan_progress_callback(self, scan_config):
        """Progress callback invoked during scan."""
        progress_updates: list[ScanProgress] = []

        with patch("pylxpweb.scanner.scanner.asyncio.open_connection", side_effect=OSError):
            scanner = NetworkScanner(scan_config, progress_callback=progress_updates.append)
            _ = [r async for r in scanner.scan()]

        # Final update should show all hosts scanned
        assert any(p.total_hosts == 3 for p in progress_updates)

    async def test_scan_with_modbus_verification(self):
        """Modbus verification succeeds → MODBUS_VERIFIED result."""
        config = ScanConfig(
            ip_range="192.168.1.50",
            ports=[502],
            timeout=0.1,
            verify_modbus=True,
            lookup_mac=False,
        )

        async def mock_open(host, port):
            return MagicMock(), _mock_writer()

        mock_info = MagicMock()
        mock_info.serial = "4512345678"
        mock_info.device_type_code = 2092  # PV_SERIES
        mock_info.firmware_version = "1.0.5"

        mock_transport = MagicMock()
        mock_transport.connect = AsyncMock()
        mock_transport.disconnect = AsyncMock()

        with (
            patch("pylxpweb.scanner.scanner.asyncio.open_connection", side_effect=mock_open),
            patch(
                "pylxpweb.transports.factory.create_modbus_transport",
                return_value=mock_transport,
            ),
            patch(
                "pylxpweb.transports.discovery.discover_device_info",
                return_value=mock_info,
            ),
        ):
            scanner = NetworkScanner(config)
            results = [r async for r in scanner.scan()]

        assert len(results) == 1
        assert results[0].device_type == DeviceType.MODBUS_VERIFIED
        assert results[0].serial == "4512345678"
        assert results[0].model_family == "PV_SERIES"

    async def test_scan_modbus_verification_unknown_code(self):
        """Unknown device type code → MODBUS_UNVERIFIED."""
        config = ScanConfig(
            ip_range="192.168.1.50",
            ports=[502],
            timeout=0.1,
            verify_modbus=True,
            lookup_mac=False,
        )

        async def mock_open(host, port):
            return MagicMock(), _mock_writer()

        mock_info = MagicMock()
        mock_info.serial = "9999999999"
        mock_info.device_type_code = 9999  # Unknown
        mock_info.firmware_version = None

        mock_transport = MagicMock()
        mock_transport.connect = AsyncMock()
        mock_transport.disconnect = AsyncMock()

        with (
            patch("pylxpweb.scanner.scanner.asyncio.open_connection", side_effect=mock_open),
            patch(
                "pylxpweb.transports.factory.create_modbus_transport",
                return_value=mock_transport,
            ),
            patch(
                "pylxpweb.transports.discovery.discover_device_info",
                return_value=mock_info,
            ),
        ):
            scanner = NetworkScanner(config)
            results = [r async for r in scanner.scan()]

        assert len(results) == 1
        assert results[0].device_type == DeviceType.MODBUS_UNVERIFIED
        assert results[0].error is not None

    async def test_scan_modbus_verification_failure(self):
        """Modbus connect succeeds but verification raises → MODBUS_UNVERIFIED."""
        config = ScanConfig(
            ip_range="192.168.1.50",
            ports=[502],
            timeout=0.1,
            verify_modbus=True,
            lookup_mac=False,
        )

        async def mock_open(host, port):
            return MagicMock(), _mock_writer()

        mock_transport = MagicMock()
        mock_transport.connect = AsyncMock(side_effect=OSError("Connection reset"))

        with (
            patch("pylxpweb.scanner.scanner.asyncio.open_connection", side_effect=mock_open),
            patch(
                "pylxpweb.transports.factory.create_modbus_transport",
                return_value=mock_transport,
            ),
        ):
            scanner = NetworkScanner(config)
            results = [r async for r in scanner.scan()]

        assert len(results) == 1
        assert results[0].device_type == DeviceType.MODBUS_UNVERIFIED
        assert "Connection reset" in (results[0].error or "")

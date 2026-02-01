"""Unit tests for scanner.mac_lookup module."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pylxpweb.scanner.mac_lookup import (
    KNOWN_DONGLE_OUIS,
    get_oui_vendor,
    is_known_dongle_oui,
    lookup_mac_address,
)


class TestGetOuiVendor:
    """Tests for get_oui_vendor function."""

    def test_known_espressif_oui(self) -> None:
        """Test known Espressif OUI."""
        mac = "A4:CF:12:34:56:78"
        vendor = get_oui_vendor(mac)
        assert vendor == "Espressif"

    def test_known_waveshare_oui(self) -> None:
        """Test known Waveshare OUI."""
        mac = "00:1A:FE:11:22:33"
        vendor = get_oui_vendor(mac)
        assert vendor == "Waveshare"

    def test_unknown_oui(self) -> None:
        """Test unknown OUI returns None."""
        mac = "AA:BB:CC:DD:EE:FF"
        vendor = get_oui_vendor(mac)
        assert vendor is None

    def test_lowercase_mac(self) -> None:
        """Test lowercase MAC address is handled."""
        mac = "a4:cf:12:34:56:78"
        vendor = get_oui_vendor(mac)
        assert vendor == "Espressif"

    def test_mixed_case_mac(self) -> None:
        """Test mixed case MAC address is handled."""
        mac = "a4:Cf:12:34:56:78"
        vendor = get_oui_vendor(mac)
        assert vendor == "Espressif"

    def test_empty_mac(self) -> None:
        """Test empty MAC returns None."""
        vendor = get_oui_vendor("")
        assert vendor is None

    def test_short_mac(self) -> None:
        """Test MAC shorter than OUI returns None."""
        vendor = get_oui_vendor("A4:CF")
        assert vendor is None

    def test_exact_oui_length(self) -> None:
        """Test MAC with exactly OUI length (8 chars)."""
        mac = "24:0A:C4"
        vendor = get_oui_vendor(mac)
        assert vendor == "Espressif"

    def test_all_espressif_ouis_present(self) -> None:
        """Test multiple Espressif OUIs are in the database."""
        espressif_ouis = [
            "24:0A:C4",
            "3C:61:05",
            "A4:CF:12",
            "FC:F5:C4",
        ]
        for oui in espressif_ouis:
            vendor = get_oui_vendor(oui + ":00:00:00")
            assert vendor == "Espressif", f"OUI {oui} should be Espressif"

    def test_oui_database_not_empty(self) -> None:
        """Test KNOWN_DONGLE_OUIS has entries."""
        assert len(KNOWN_DONGLE_OUIS) > 0
        assert "Espressif" in KNOWN_DONGLE_OUIS.values()
        assert "Waveshare" in KNOWN_DONGLE_OUIS.values()


class TestIsKnownDongleOui:
    """Tests for is_known_dongle_oui function."""

    def test_known_oui_returns_true(self) -> None:
        """Test known OUI returns True."""
        assert is_known_dongle_oui("A4:CF:12:34:56:78") is True

    def test_unknown_oui_returns_false(self) -> None:
        """Test unknown OUI returns False."""
        assert is_known_dongle_oui("AA:BB:CC:DD:EE:FF") is False

    def test_empty_mac_returns_false(self) -> None:
        """Test empty MAC returns False."""
        assert is_known_dongle_oui("") is False

    def test_short_mac_returns_false(self) -> None:
        """Test short MAC returns False."""
        assert is_known_dongle_oui("A4:CF") is False

    def test_case_insensitive(self) -> None:
        """Test function is case-insensitive."""
        assert is_known_dongle_oui("a4:cf:12:34:56:78") is True
        assert is_known_dongle_oui("A4:CF:12:34:56:78") is True


class TestLookupMacAddress:
    """Tests for lookup_mac_address function."""

    @pytest.fixture
    def mock_subprocess(self) -> MagicMock:
        """Create a mock subprocess for testing."""
        proc = MagicMock()
        proc.wait = AsyncMock(return_value=0)
        proc.communicate = AsyncMock()
        return proc

    async def test_successful_lookup_darwin(self, mock_subprocess: MagicMock) -> None:
        """Test successful MAC lookup on macOS."""
        arp_output = b"? (192.168.1.100) at a4:cf:12:34:56:78 on en0 ifscope [ethernet]"
        mock_subprocess.communicate.return_value = (arp_output, b"")

        with (
            patch("sys.platform", "darwin"),
            patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_subprocess,
            ) as mock_exec,
        ):
            result = await lookup_mac_address("192.168.1.100")

        assert result == "A4:CF:12:34:56:78"
        assert mock_exec.call_count == 2  # ping + arp

    async def test_successful_lookup_linux(self, mock_subprocess: MagicMock) -> None:
        """Test successful MAC lookup on Linux."""
        arp_output = b"192.168.1.100 ether a4:cf:12:34:56:78 C eth0"
        mock_subprocess.communicate.return_value = (arp_output, b"")

        with (
            patch("sys.platform", "linux"),
            patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_subprocess,
            ) as mock_exec,
        ):
            result = await lookup_mac_address("192.168.1.100")

        assert result == "A4:CF:12:34:56:78"
        assert mock_exec.call_count == 2  # ping + arp

    async def test_mac_with_dashes(self, mock_subprocess: MagicMock) -> None:
        """Test MAC address with dashes is converted to colons."""
        arp_output = b"192.168.1.100 at a4-cf-12-34-56-78"
        mock_subprocess.communicate.return_value = (arp_output, b"")

        with (
            patch("sys.platform", "linux"),
            patch("asyncio.create_subprocess_exec", return_value=mock_subprocess),
        ):
            result = await lookup_mac_address("192.168.1.100")

        assert result == "A4:CF:12:34:56:78"

    async def test_mac_with_single_digit_bytes(self, mock_subprocess: MagicMock) -> None:
        """Test MAC address with single digit bytes is zero-padded."""
        arp_output = b"192.168.1.100 at a:b:c:d:e:f"
        mock_subprocess.communicate.return_value = (arp_output, b"")

        with (
            patch("sys.platform", "linux"),
            patch("asyncio.create_subprocess_exec", return_value=mock_subprocess),
        ):
            result = await lookup_mac_address("192.168.1.100")

        assert result == "0A:0B:0C:0D:0E:0F"

    async def test_no_mac_in_arp_table(self, mock_subprocess: MagicMock) -> None:
        """Test when MAC not found in ARP table."""
        arp_output = b"192.168.1.100 (incomplete)"
        mock_subprocess.communicate.return_value = (arp_output, b"")

        with (
            patch("sys.platform", "linux"),
            patch("asyncio.create_subprocess_exec", return_value=mock_subprocess),
        ):
            result = await lookup_mac_address("192.168.1.100")

        assert result is None

    async def test_ping_timeout(self, mock_subprocess: MagicMock) -> None:
        """Test when ping times out."""
        arp_output = b"192.168.1.100 at a4:cf:12:34:56:78"
        ping_proc = MagicMock()
        ping_proc.wait = AsyncMock(side_effect=asyncio.TimeoutError)
        arp_proc = MagicMock()
        arp_proc.communicate = AsyncMock(return_value=(arp_output, b""))

        with (
            patch("sys.platform", "linux"),
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=[ping_proc, arp_proc],
            ),
        ):
            result = await lookup_mac_address("192.168.1.100")

        # Should still succeed if ARP table has entry
        assert result == "A4:CF:12:34:56:78"

    async def test_ping_oserror(self, mock_subprocess: MagicMock) -> None:
        """Test when ping fails with OSError."""
        arp_output = b"192.168.1.100 at a4:cf:12:34:56:78"
        ping_proc = MagicMock()
        ping_proc.wait = AsyncMock(side_effect=OSError("Network unreachable"))
        arp_proc = MagicMock()
        arp_proc.communicate = AsyncMock(return_value=(arp_output, b""))

        with (
            patch("sys.platform", "linux"),
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=[ping_proc, arp_proc],
            ),
        ):
            result = await lookup_mac_address("192.168.1.100")

        # Should still succeed if ARP table has entry
        assert result == "A4:CF:12:34:56:78"

    async def test_arp_timeout(self, mock_subprocess: MagicMock) -> None:
        """Test when ARP command times out."""
        ping_proc = MagicMock()
        ping_proc.wait = AsyncMock(return_value=0)
        arp_proc = MagicMock()
        arp_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError)

        with (
            patch("sys.platform", "linux"),
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=[ping_proc, arp_proc],
            ),
        ):
            result = await lookup_mac_address("192.168.1.100")

        assert result is None

    async def test_arp_oserror(self, mock_subprocess: MagicMock) -> None:
        """Test when ARP command fails with OSError."""
        ping_proc = MagicMock()
        ping_proc.wait = AsyncMock(return_value=0)
        arp_proc = MagicMock()
        arp_proc.communicate = AsyncMock(side_effect=OSError("Command not found"))

        with (
            patch("sys.platform", "linux"),
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=[ping_proc, arp_proc],
            ),
        ):
            result = await lookup_mac_address("192.168.1.100")

        assert result is None

    async def test_darwin_ping_args(self, mock_subprocess: MagicMock) -> None:
        """Test ping arguments are correct on macOS."""
        arp_output = b"? (192.168.1.100) at a4:cf:12:34:56:78"
        mock_subprocess.communicate.return_value = (arp_output, b"")

        with (
            patch("sys.platform", "darwin"),
            patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_subprocess,
            ) as mock_exec,
        ):
            await lookup_mac_address("192.168.1.100")

        # Check first call (ping) has correct args
        ping_call = mock_exec.call_args_list[0]
        ping_args = ping_call[0]
        assert ping_args == ("ping", "-c", "1", "-W", "500", "192.168.1.100")

    async def test_linux_ping_args(self, mock_subprocess: MagicMock) -> None:
        """Test ping arguments are correct on Linux."""
        arp_output = b"192.168.1.100 at a4:cf:12:34:56:78"
        mock_subprocess.communicate.return_value = (arp_output, b"")

        with (
            patch("sys.platform", "linux"),
            patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_subprocess,
            ) as mock_exec,
        ):
            await lookup_mac_address("192.168.1.100")

        # Check first call (ping) has correct args
        ping_call = mock_exec.call_args_list[0]
        ping_args = ping_call[0]
        assert ping_args == ("ping", "-c", "1", "-W", "1", "192.168.1.100")

    async def test_arp_args(self, mock_subprocess: MagicMock) -> None:
        """Test ARP command arguments are correct."""
        arp_output = b"192.168.1.100 at a4:cf:12:34:56:78"
        mock_subprocess.communicate.return_value = (arp_output, b"")

        with (
            patch("sys.platform", "linux"),
            patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_subprocess,
            ) as mock_exec,
        ):
            await lookup_mac_address("192.168.1.100")

        # Check second call (arp) has correct args
        arp_call = mock_exec.call_args_list[1]
        arp_args = arp_call[0]
        assert arp_args == ("arp", "-n", "192.168.1.100")

    async def test_empty_arp_output(self, mock_subprocess: MagicMock) -> None:
        """Test when ARP returns empty output."""
        mock_subprocess.communicate.return_value = (b"", b"")

        with (
            patch("sys.platform", "linux"),
            patch("asyncio.create_subprocess_exec", return_value=mock_subprocess),
        ):
            result = await lookup_mac_address("192.168.1.100")

        assert result is None

    async def test_malformed_arp_output(self, mock_subprocess: MagicMock) -> None:
        """Test when ARP output doesn't contain a MAC."""
        arp_output = b"No such device"
        mock_subprocess.communicate.return_value = (arp_output, b"")

        with (
            patch("sys.platform", "linux"),
            patch("asyncio.create_subprocess_exec", return_value=mock_subprocess),
        ):
            result = await lookup_mac_address("192.168.1.100")

        assert result is None

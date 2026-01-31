"""Tests for MAC OUI lookup utilities."""

from pylxpweb.scanner.mac_lookup import get_oui_vendor, is_known_dongle_oui


class TestGetOuiVendor:
    """Tests for get_oui_vendor."""

    def test_espressif_oui(self):
        assert get_oui_vendor("A4:CF:12:34:56:78") == "Espressif"

    def test_waveshare_oui(self):
        assert get_oui_vendor("00:1A:FE:AA:BB:CC") == "Waveshare"

    def test_unknown_oui(self):
        assert get_oui_vendor("FF:FF:FF:00:00:00") is None

    def test_empty_mac(self):
        assert get_oui_vendor("") is None

    def test_short_mac(self):
        assert get_oui_vendor("AA:BB") is None

    def test_case_insensitive(self):
        assert get_oui_vendor("a4:cf:12:34:56:78") == "Espressif"


class TestIsKnownDongleOui:
    """Tests for is_known_dongle_oui."""

    def test_known(self):
        assert is_known_dongle_oui("A4:CF:12:34:56:78") is True

    def test_unknown(self):
        assert is_known_dongle_oui("FF:FF:FF:00:00:00") is False

"""Network device scanner for discovering EG4 devices on a local network.

This module provides async network scanning capabilities to find EG4 inverters,
GridBOSS devices, and WiFi dongles on a local network without requiring the user
to know device IP addresses.

Usage::

    from pylxpweb.scanner import NetworkScanner, ScanConfig

    config = ScanConfig(ip_range="192.168.1.0/24")
    scanner = NetworkScanner(config)

    async for result in scanner.scan():
        if result.is_verified:
            print(f"Found EG4 {result.model_family} at {result.ip}")
        elif result.is_dongle_candidate:
            print(f"Possible dongle at {result.ip} (MAC: {result.mac_vendor})")
"""

from __future__ import annotations

from .mac_lookup import KNOWN_DONGLE_OUIS, get_oui_vendor, is_known_dongle_oui, lookup_mac_address
from .scanner import NetworkScanner
from .types import DeviceType, ScanConfig, ScanProgress, ScanResult
from .utils import estimate_scan_duration, parse_ip_range

__all__ = [
    "DeviceType",
    "KNOWN_DONGLE_OUIS",
    "NetworkScanner",
    "ScanConfig",
    "ScanProgress",
    "ScanResult",
    "estimate_scan_duration",
    "get_oui_vendor",
    "is_known_dongle_oui",
    "lookup_mac_address",
    "parse_ip_range",
]

"""MAC address resolution and OUI vendor lookup.

Uses the system ARP table to find MAC addresses for discovered IPs,
then matches the OUI prefix against known EG4 dongle manufacturers.
"""

from __future__ import annotations

import asyncio
import logging
import re
import sys

_LOGGER = logging.getLogger(__name__)

# Known OUI prefixes for EG4 WiFi dongles (Espressif ESP32 modules)
# Format: first 3 bytes of MAC in uppercase with colons
KNOWN_DONGLE_OUIS: dict[str, str] = {
    "24:0A:C4": "Espressif",
    "24:6F:28": "Espressif",
    "24:62:AB": "Espressif",
    "30:AE:A4": "Espressif",
    "3C:61:05": "Espressif",
    "3C:71:BF": "Espressif",
    "40:22:D8": "Espressif",
    "40:F5:20": "Espressif",
    "4C:11:AE": "Espressif",
    "54:32:04": "Espressif",
    "58:CF:79": "Espressif",
    "5C:CF:7F": "Espressif",
    "68:C6:3A": "Espressif",
    "70:04:1D": "Espressif",
    "78:21:84": "Espressif",
    "78:E3:6D": "Espressif",
    "7C:9E:BD": "Espressif",
    "7C:DF:A1": "Espressif",
    "80:7D:3A": "Espressif",
    "84:0D:8E": "Espressif",
    "84:CC:A8": "Espressif",
    "84:F3:EB": "Espressif",
    "8C:AA:B5": "Espressif",
    "8C:CE:4E": "Espressif",
    "90:97:D5": "Espressif",
    "94:3C:C6": "Espressif",
    "94:B5:55": "Espressif",
    "94:B9:7E": "Espressif",
    "98:CD:AC": "Espressif",
    "A0:20:A6": "Espressif",
    "A4:CF:12": "Espressif",
    "AC:67:B2": "Espressif",
    "B4:E6:2D": "Espressif",
    "BC:DD:C2": "Espressif",
    "C4:4F:33": "Espressif",
    "C4:5B:BE": "Espressif",
    "C4:DD:57": "Espressif",
    "C8:2B:96": "Espressif",
    "C8:C9:A3": "Espressif",
    "CC:50:E3": "Espressif",
    "CC:DB:A7": "Espressif",
    "D8:A0:1D": "Espressif",
    "D8:BF:C0": "Espressif",
    "DC:4F:22": "Espressif",
    "E0:98:06": "Espressif",
    "E8:68:E7": "Espressif",
    "EC:94:CB": "Espressif",
    "F0:08:D1": "Espressif",
    "F4:CF:A2": "Espressif",
    "FC:F5:C4": "Espressif",
    # Waveshare RS485-to-Ethernet adapters
    "00:1A:FE": "Waveshare",
}

# Regex to extract MAC from ARP output (works on Linux and macOS)
_MAC_RE = re.compile(r"([\da-fA-F]{1,2}[:\-]){5}[\da-fA-F]{1,2}")


async def lookup_mac_address(ip: str) -> str | None:
    """Look up a MAC address from the system ARP table.

    Sends a single ARP probe (ping) to populate the cache, then reads ARP.

    Args:
        ip: IP address to look up.

    Returns:
        MAC address string (e.g., "A4:CF:12:34:56:78") or None.
    """
    # Ping to populate ARP cache (1 packet, short timeout)
    try:
        if sys.platform == "darwin":
            ping_args = ["ping", "-c", "1", "-W", "500", ip]
        else:
            ping_args = ["ping", "-c", "1", "-W", "1", ip]

        proc = await asyncio.create_subprocess_exec(
            *ping_args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=2.0)
    except (TimeoutError, OSError):
        pass  # Ping may fail; ARP entry might still exist

    # Read ARP table
    try:
        arp_args = ["arp", "-n", ip]
        proc = await asyncio.create_subprocess_exec(
            *arp_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=2.0)
        output = stdout.decode("utf-8", errors="replace")

        match = _MAC_RE.search(output)
        if match:
            mac = match.group(0).upper().replace("-", ":")
            parts = mac.split(":")
            mac = ":".join(p.zfill(2) for p in parts)
            return mac
    except (TimeoutError, OSError) as err:
        _LOGGER.debug("ARP lookup failed for %s: %s", ip, err)

    return None


def get_oui_vendor(mac: str) -> str | None:
    """Look up the OUI vendor name for a MAC address.

    Args:
        mac: MAC address in "XX:XX:XX:XX:XX:XX" format.

    Returns:
        Vendor name if the OUI is in our known list, or None.
    """
    if not mac or len(mac) < 8:
        return None
    oui = mac[:8].upper()
    return KNOWN_DONGLE_OUIS.get(oui)


def is_known_dongle_oui(mac: str) -> bool:
    """Check if a MAC address matches a known EG4 dongle OUI."""
    return get_oui_vendor(mac) is not None

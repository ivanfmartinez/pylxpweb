"""Data types for network device scanning results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DeviceType(Enum):
    """Classification of a discovered network device."""

    MODBUS_VERIFIED = "modbus_verified"
    MODBUS_UNVERIFIED = "modbus_unverified"
    DONGLE_CANDIDATE = "dongle_candidate"


@dataclass
class ScanResult:
    """A single device found during a network scan.

    Attributes:
        ip: IP address where the device was found.
        port: TCP port that responded.
        device_type: Classification of the device.
        serial: Device serial number (Modbus verified only).
        model_family: Model family name (Modbus verified only).
        device_type_code: Raw register 19 value (Modbus verified only).
        firmware_version: Firmware string (Modbus verified only).
        mac_address: MAC address from ARP table (if available).
        mac_vendor: OUI vendor name (if MAC lookup enabled).
        response_time_ms: TCP connection response time in milliseconds.
        error: Error message if verification failed.
    """

    ip: str
    port: int
    device_type: DeviceType
    serial: str | None = None
    model_family: str | None = None
    device_type_code: int | None = None
    firmware_version: str | None = None
    mac_address: str | None = None
    mac_vendor: str | None = None
    response_time_ms: float = 0.0
    error: str | None = None

    @property
    def is_verified(self) -> bool:
        """True if this is a verified EG4 device."""
        return self.device_type == DeviceType.MODBUS_VERIFIED

    @property
    def is_dongle_candidate(self) -> bool:
        """True if this might be a WiFi dongle."""
        return self.device_type == DeviceType.DONGLE_CANDIDATE

    @property
    def display_label(self) -> str:
        """Human-readable label for UI display."""
        if self.device_type == DeviceType.MODBUS_VERIFIED:
            return f"{self.model_family or 'EG4'} ({self.serial}) @ {self.ip}:{self.port}"
        if self.device_type == DeviceType.DONGLE_CANDIDATE:
            vendor = self.mac_vendor or "Unknown vendor"
            return f"Dongle candidate @ {self.ip}:{self.port} (MAC: {vendor})"
        return f"Modbus device @ {self.ip}:{self.port} (unverified)"


@dataclass
class ScanProgress:
    """Progress update emitted during a network scan.

    Attributes:
        total_hosts: Total number of IPs to scan.
        scanned: Number of IPs scanned so far.
        found: Number of devices found so far.
    """

    total_hosts: int
    scanned: int
    found: int

    @property
    def percent(self) -> float:
        """Percentage of scan completed (0-100)."""
        if self.total_hosts == 0:
            return 100.0
        return (self.scanned / self.total_hosts) * 100.0


@dataclass
class ScanConfig:
    """Configuration for a network scan.

    Attributes:
        ip_range: CIDR notation or IP range string.
        ports: TCP ports to scan (default: Modbus 502 + Dongle 8000).
        timeout: Per-connection timeout in seconds.
        concurrency: Maximum concurrent TCP connections.
        verify_modbus: If True, probe Modbus devices for EG4 identification.
        lookup_mac: If True, check ARP table and resolve OUI vendor.
    """

    ip_range: str
    ports: list[int] = field(default_factory=lambda: [502, 8000])
    timeout: float = 0.5
    concurrency: int = 50
    verify_modbus: bool = True
    lookup_mac: bool = False

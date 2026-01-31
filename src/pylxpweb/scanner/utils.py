"""IP range parsing and validation utilities for network scanning."""

from __future__ import annotations

import ipaddress

# Private IP networks per RFC 1918 + RFC 6598
_PRIVATE_NETWORKS: list[ipaddress.IPv4Network] = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
    ipaddress.IPv4Network("100.64.0.0/10"),  # CGN / Tailscale
]

# Maximum hosts before we warn (subnet larger than /20)
MAX_SAFE_HOSTS = 4094


def parse_ip_range(ip_range: str) -> list[str]:
    """Parse an IP range string into a list of host IP addresses.

    Supports:
        - CIDR notation: "192.168.1.0/24"
        - Single IP: "192.168.1.50"
        - Dash range: "192.168.1.1-192.168.1.254"

    Args:
        ip_range: IP range string in any supported format.

    Returns:
        List of individual IP address strings.

    Raises:
        ValueError: If the input is not a valid IP range or contains
            non-private addresses.
    """
    ip_range = ip_range.strip()

    # Dash range: "192.168.1.1-192.168.1.254"
    if "-" in ip_range and "/" not in ip_range:
        return _parse_dash_range(ip_range)

    # Single IP or CIDR
    try:
        network = ipaddress.ip_network(ip_range, strict=False)
    except ValueError as err:
        raise ValueError(f"Invalid IP range: {ip_range!r}") from err

    _validate_private(network)

    if network.prefixlen == 32:
        return [str(network.network_address)]

    return [str(ip) for ip in network.hosts()]


def _parse_dash_range(ip_range: str) -> list[str]:
    """Parse a dash-separated IP range like '192.168.1.1-192.168.1.254'."""
    parts = ip_range.split("-", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid dash range: {ip_range!r}")

    try:
        start = ipaddress.IPv4Address(parts[0].strip())
        end = ipaddress.IPv4Address(parts[1].strip())
    except (ValueError, ipaddress.AddressValueError) as err:
        raise ValueError(f"Invalid IP in range: {ip_range!r}") from err

    if start > end:
        raise ValueError(f"Start IP must be <= end IP: {ip_range!r}")

    count = int(end) - int(start) + 1
    if count > MAX_SAFE_HOSTS:
        raise ValueError(
            f"Range contains {count} hosts (max {MAX_SAFE_HOSTS}). Use a smaller range."
        )

    # Validate both endpoints are private
    for addr in (start, end):
        if not addr.is_private:
            raise ValueError(f"Only private IP ranges are allowed, got {addr}")

    # Validate both endpoints are on the same /24 subnet
    start_net = ipaddress.IPv4Network(f"{start}/24", strict=False)
    end_net = ipaddress.IPv4Network(f"{end}/24", strict=False)
    if start_net != end_net and count > 254:
        raise ValueError(
            f"Dash range spans multiple subnets ({start_net} to {end_net}). "
            "Use CIDR notation for cross-subnet scans."
        )

    return [str(ipaddress.IPv4Address(int(start) + i)) for i in range(count)]


def _validate_private(network: ipaddress.IPv4Network | ipaddress.IPv6Network) -> None:
    """Validate that a network is within private address space."""
    if isinstance(network, ipaddress.IPv6Network):
        raise ValueError("IPv6 scanning is not supported")

    if not isinstance(network, ipaddress.IPv4Network):
        raise TypeError(f"Expected IPv4Network, got {type(network).__name__}")

    if not any(network.subnet_of(priv) for priv in _PRIVATE_NETWORKS):
        raise ValueError(
            f"Only private IP ranges are allowed (10.x, 172.16-31.x, 192.168.x), got {network}"
        )

    host_count = network.num_addresses - 2  # Subtract network + broadcast
    if host_count > MAX_SAFE_HOSTS:
        raise ValueError(
            f"Subnet {network} contains {host_count} hosts (max {MAX_SAFE_HOSTS}). "
            "Use a smaller subnet (e.g., /24)."
        )


def estimate_scan_duration(
    host_count: int,
    ports_per_host: int,
    timeout: float,
    concurrency: int,
) -> float:
    """Estimate scan duration in seconds.

    This is a rough upper-bound estimate assuming worst case (all timeouts).

    Args:
        host_count: Number of hosts to scan.
        ports_per_host: Number of ports per host.
        timeout: Per-connection timeout in seconds.
        concurrency: Maximum concurrent connections.

    Returns:
        Estimated duration in seconds.
    """
    total_probes = host_count * ports_per_host
    batches = (total_probes + concurrency - 1) // concurrency
    return batches * timeout

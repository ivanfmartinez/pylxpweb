"""Unit tests for scanner.utils module."""

from __future__ import annotations

import pytest

from pylxpweb.scanner.utils import (
    MAX_SAFE_HOSTS,
    estimate_scan_duration,
    parse_ip_range,
)


class TestParseIpRange:
    """Tests for parse_ip_range function."""

    def test_single_ip(self) -> None:
        """Test parsing a single IP address."""
        result = parse_ip_range("192.168.1.50")
        assert result == ["192.168.1.50"]

    def test_cidr_notation_slash24(self) -> None:
        """Test parsing a /24 CIDR range."""
        result = parse_ip_range("192.168.1.0/24")
        assert len(result) == 254
        assert "192.168.1.1" in result
        assert "192.168.1.254" in result
        assert "192.168.1.0" not in result  # Network address excluded
        assert "192.168.1.255" not in result  # Broadcast excluded

    def test_cidr_notation_slash30(self) -> None:
        """Test parsing a /30 CIDR range."""
        result = parse_ip_range("192.168.1.0/30")
        assert len(result) == 2
        assert "192.168.1.1" in result
        assert "192.168.1.2" in result

    def test_cidr_notation_slash32(self) -> None:
        """Test parsing a /32 CIDR (single IP)."""
        result = parse_ip_range("192.168.1.50/32")
        assert result == ["192.168.1.50"]

    def test_dash_range_simple(self) -> None:
        """Test parsing a simple dash range."""
        result = parse_ip_range("192.168.1.1-192.168.1.5")
        assert result == [
            "192.168.1.1",
            "192.168.1.2",
            "192.168.1.3",
            "192.168.1.4",
            "192.168.1.5",
        ]

    def test_dash_range_single_ip(self) -> None:
        """Test parsing a dash range with same start/end."""
        result = parse_ip_range("192.168.1.100-192.168.1.100")
        assert result == ["192.168.1.100"]

    def test_dash_range_large(self) -> None:
        """Test parsing a large dash range."""
        result = parse_ip_range("192.168.1.1-192.168.1.254")
        assert len(result) == 254
        assert result[0] == "192.168.1.1"
        assert result[-1] == "192.168.1.254"

    def test_whitespace_stripped(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        result = parse_ip_range("  192.168.1.50  ")
        assert result == ["192.168.1.50"]

    def test_whitespace_in_dash_range(self) -> None:
        """Test whitespace handling in dash ranges."""
        result = parse_ip_range("192.168.1.1 - 192.168.1.3")
        assert result == ["192.168.1.1", "192.168.1.2", "192.168.1.3"]

    def test_private_networks_192_168(self) -> None:
        """Test 192.168.x.x private network."""
        result = parse_ip_range("192.168.1.0/28")
        assert len(result) == 14  # /28 has 14 hosts

    def test_private_networks_10(self) -> None:
        """Test 10.x.x.x private network."""
        result = parse_ip_range("10.0.0.0/29")
        assert len(result) == 6  # /29 has 6 hosts

    def test_private_networks_172_16(self) -> None:
        """Test 172.16.x.x private network."""
        result = parse_ip_range("172.16.0.0/28")
        assert len(result) == 14

    def test_private_networks_cgn(self) -> None:
        """Test 100.64.x.x CGN/Tailscale network."""
        result = parse_ip_range("100.64.0.0/28")
        assert len(result) == 14

    def test_invalid_ip_format(self) -> None:
        """Test error on invalid IP format."""
        with pytest.raises(ValueError, match="Invalid IP range"):
            parse_ip_range("not.an.ip.address")

    def test_invalid_cidr_prefix(self) -> None:
        """Test error on invalid CIDR prefix."""
        with pytest.raises(ValueError, match="Invalid IP range"):
            parse_ip_range("192.168.1.0/99")

    def test_public_ip_rejected(self) -> None:
        """Test error when public IP is used."""
        with pytest.raises(ValueError, match="Only private IP ranges are allowed"):
            parse_ip_range("8.8.8.8/24")

    def test_public_ip_in_dash_range(self) -> None:
        """Test error when public IP in dash range."""
        with pytest.raises(ValueError, match="Only private IP ranges are allowed"):
            parse_ip_range("8.8.8.1-8.8.8.10")

    def test_subnet_too_large(self) -> None:
        """Test error when subnet is too large."""
        with pytest.raises(ValueError, match="contains .* hosts"):
            parse_ip_range("192.168.0.0/16")

    def test_dash_range_too_large(self) -> None:
        """Test error when dash range is too large."""
        with pytest.raises(ValueError, match="Range contains .* hosts"):
            parse_ip_range("192.168.1.1-192.168.255.254")

    def test_dash_range_reversed(self) -> None:
        """Test error when start > end in dash range."""
        with pytest.raises(ValueError, match="Start IP must be <= end IP"):
            parse_ip_range("192.168.1.100-192.168.1.50")

    def test_dash_range_invalid_format(self) -> None:
        """Test error on invalid dash range format."""
        with pytest.raises(ValueError, match="Invalid IP in range"):
            parse_ip_range("192.168.1.1-not.an.ip")

    def test_dash_range_cross_subnet_small(self) -> None:
        """Test dash range spanning subnets (small range)."""
        result = parse_ip_range("192.168.1.250-192.168.2.5")
        assert len(result) == 12
        assert result[0] == "192.168.1.250"
        assert result[-1] == "192.168.2.5"

    def test_dash_range_cross_subnet_large(self) -> None:
        """Test error for large cross-subnet dash range."""
        with pytest.raises(ValueError, match="Dash range spans multiple subnets"):
            parse_ip_range("192.168.1.1-192.168.10.254")

    def test_ipv6_rejected(self) -> None:
        """Test error when IPv6 is used."""
        with pytest.raises(ValueError, match="IPv6 scanning is not supported"):
            parse_ip_range("fe80::1/64")

    def test_empty_string(self) -> None:
        """Test error on empty string."""
        with pytest.raises(ValueError, match="Invalid IP range"):
            parse_ip_range("")

    def test_max_safe_hosts_boundary(self) -> None:
        """Test MAX_SAFE_HOSTS constant value."""
        assert MAX_SAFE_HOSTS == 4094

    def test_cidr_at_max_safe_hosts(self) -> None:
        """Test CIDR at MAX_SAFE_HOSTS boundary (/20)."""
        result = parse_ip_range("192.168.0.0/20")
        expected = 4094  # /20 has 4094 hosts
        assert len(result) == expected

    def test_cidr_exceeds_max_safe_hosts(self) -> None:
        """Test error when CIDR exceeds MAX_SAFE_HOSTS."""
        with pytest.raises(ValueError, match="contains .* hosts"):
            parse_ip_range("192.168.0.0/19")


class TestEstimateScanDuration:
    """Tests for estimate_scan_duration function."""

    def test_single_host_single_port(self) -> None:
        """Test estimate for 1 host, 1 port."""
        duration = estimate_scan_duration(
            host_count=1,
            ports_per_host=1,
            timeout=1.0,
            concurrency=10,
        )
        assert duration == 1.0

    def test_multiple_hosts_sequential(self) -> None:
        """Test estimate for multiple hosts with low concurrency."""
        duration = estimate_scan_duration(
            host_count=10,
            ports_per_host=2,
            timeout=0.5,
            concurrency=5,
        )
        # 10 hosts * 2 ports = 20 probes
        # 20 probes / 5 concurrency = 4 batches
        # 4 batches * 0.5s = 2.0s
        assert duration == 2.0

    def test_high_concurrency(self) -> None:
        """Test estimate with high concurrency (single batch)."""
        duration = estimate_scan_duration(
            host_count=100,
            ports_per_host=2,
            timeout=1.0,
            concurrency=500,
        )
        # 100 hosts * 2 ports = 200 probes
        # 200 probes / 500 concurrency = 1 batch
        # 1 batch * 1.0s = 1.0s
        assert duration == 1.0

    def test_exact_batch_division(self) -> None:
        """Test estimate when probes divide evenly by concurrency."""
        duration = estimate_scan_duration(
            host_count=50,
            ports_per_host=2,
            timeout=0.5,
            concurrency=10,
        )
        # 50 hosts * 2 ports = 100 probes
        # 100 probes / 10 concurrency = 10 batches
        # 10 batches * 0.5s = 5.0s
        assert duration == 5.0

    def test_partial_batch(self) -> None:
        """Test estimate with partial final batch."""
        duration = estimate_scan_duration(
            host_count=25,
            ports_per_host=2,
            timeout=1.0,
            concurrency=10,
        )
        # 25 hosts * 2 ports = 50 probes
        # 50 probes / 10 concurrency = 5 batches
        # 5 batches * 1.0s = 5.0s
        assert duration == 5.0

    def test_large_network_scan(self) -> None:
        """Test estimate for large network scan (/24)."""
        duration = estimate_scan_duration(
            host_count=254,
            ports_per_host=2,
            timeout=0.5,
            concurrency=50,
        )
        # 254 hosts * 2 ports = 508 probes
        # 508 probes / 50 concurrency = 11 batches (rounded up)
        # 11 batches * 0.5s = 5.5s
        assert duration == 5.5

    def test_zero_hosts(self) -> None:
        """Test estimate with zero hosts."""
        duration = estimate_scan_duration(
            host_count=0,
            ports_per_host=2,
            timeout=1.0,
            concurrency=10,
        )
        assert duration == 0.0

    def test_zero_ports(self) -> None:
        """Test estimate with zero ports."""
        duration = estimate_scan_duration(
            host_count=100,
            ports_per_host=0,
            timeout=1.0,
            concurrency=10,
        )
        assert duration == 0.0

    def test_one_probe_per_batch(self) -> None:
        """Test estimate with concurrency of 1."""
        duration = estimate_scan_duration(
            host_count=5,
            ports_per_host=2,
            timeout=1.0,
            concurrency=1,
        )
        # 5 hosts * 2 ports = 10 probes
        # 10 probes / 1 concurrency = 10 batches
        # 10 batches * 1.0s = 10.0s
        assert duration == 10.0

    def test_fractional_timeout(self) -> None:
        """Test estimate with fractional timeout."""
        duration = estimate_scan_duration(
            host_count=10,
            ports_per_host=1,
            timeout=0.25,
            concurrency=5,
        )
        # 10 hosts * 1 port = 10 probes
        # 10 probes / 5 concurrency = 2 batches
        # 2 batches * 0.25s = 0.5s
        assert duration == 0.5

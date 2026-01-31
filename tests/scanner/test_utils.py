"""Tests for scanner IP range parsing utilities."""

import pytest

from pylxpweb.scanner.utils import estimate_scan_duration, parse_ip_range


class TestParseIpRange:
    """Tests for parse_ip_range."""

    def test_cidr_24(self):
        hosts = parse_ip_range("192.168.1.0/24")
        assert len(hosts) == 254
        assert hosts[0] == "192.168.1.1"
        assert hosts[-1] == "192.168.1.254"

    def test_cidr_28(self):
        hosts = parse_ip_range("10.0.0.0/28")
        assert len(hosts) == 14

    def test_single_ip(self):
        hosts = parse_ip_range("192.168.1.50")
        assert hosts == ["192.168.1.50"]

    def test_dash_range(self):
        hosts = parse_ip_range("192.168.1.10-192.168.1.20")
        assert len(hosts) == 11
        assert hosts[0] == "192.168.1.10"
        assert hosts[-1] == "192.168.1.20"

    def test_dash_range_single(self):
        hosts = parse_ip_range("192.168.1.10-192.168.1.10")
        assert hosts == ["192.168.1.10"]

    def test_whitespace_stripped(self):
        hosts = parse_ip_range("  192.168.1.0/24  ")
        assert len(hosts) == 254

    def test_reject_public_ip(self):
        with pytest.raises(ValueError, match="private"):
            parse_ip_range("8.8.8.0/24")

    def test_reject_ipv6(self):
        with pytest.raises(ValueError, match="IPv6"):
            parse_ip_range("fe80::/64")

    def test_reject_large_subnet(self):
        with pytest.raises(ValueError, match="max"):
            parse_ip_range("10.0.0.0/16")

    def test_reject_invalid_format(self):
        with pytest.raises(ValueError):
            parse_ip_range("not-an-ip")

    def test_reject_reversed_range(self):
        with pytest.raises(ValueError, match="<="):
            parse_ip_range("192.168.1.20-192.168.1.10")

    def test_tailscale_cgn_allowed(self):
        hosts = parse_ip_range("100.64.0.0/24")
        assert len(hosts) == 254


class TestEstimateScanDuration:
    """Tests for estimate_scan_duration."""

    def test_basic_estimate(self):
        duration = estimate_scan_duration(
            host_count=254, ports_per_host=2, timeout=0.5, concurrency=50
        )
        # 508 probes / 50 concurrency = 11 batches * 0.5s = 5.5s
        assert 5.0 <= duration <= 6.0

    def test_single_host(self):
        duration = estimate_scan_duration(
            host_count=1, ports_per_host=1, timeout=1.0, concurrency=50
        )
        assert duration == 1.0

    def test_high_concurrency(self):
        duration = estimate_scan_duration(
            host_count=100, ports_per_host=2, timeout=0.5, concurrency=200
        )
        assert duration == 0.5  # All fit in one batch

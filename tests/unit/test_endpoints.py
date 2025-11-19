"""Unit tests for endpoint modules."""

from __future__ import annotations

import pytest
from aiohttp.test_utils import TestServer

from pylxpweb import LuxpowerClient


class TestAnalyticsEndpoints:
    """Test analytics endpoint methods."""

    @pytest.mark.asyncio
    async def test_get_chart_data(self, mock_api_server: TestServer) -> None:
        """Test getting chart data."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.analytics.get_chart_data("1234567890", "ppv", "2024-01-01")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_energy_day_breakdown(self, mock_api_server: TestServer) -> None:
        """Test getting energy day breakdown."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.analytics.get_energy_day_breakdown("1234567890", "2024-01-01")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_energy_month_breakdown(self, mock_api_server: TestServer) -> None:
        """Test getting energy month breakdown."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.analytics.get_energy_month_breakdown("1234567890", 2024, 1)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_energy_year_breakdown(self, mock_api_server: TestServer) -> None:
        """Test getting energy year breakdown."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.analytics.get_energy_year_breakdown("1234567890", 2024)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_energy_total_breakdown(self, mock_api_server: TestServer) -> None:
        """Test getting energy total breakdown."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.analytics.get_energy_total_breakdown("1234567890")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_event_list(self, mock_api_server: TestServer) -> None:
        """Test getting event list."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.analytics.get_event_list("1234567890", "2024-01-01", "2024-01-31")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_battery_list(self, mock_api_server: TestServer) -> None:
        """Test getting battery list."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.analytics.get_battery_list("1234567890")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_inverter_info(self, mock_api_server: TestServer) -> None:
        """Test getting inverter info."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.analytics.get_inverter_info("1234567890")
            assert isinstance(result, dict)


class TestExportEndpoints:
    """Test export endpoint methods."""

    @pytest.mark.asyncio
    async def test_export_data(self, mock_api_server: TestServer) -> None:
        """Test exporting data."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.export.export_data(
                "1234567890", "2024-01-01", "2024-01-31", "energy"
            )
            assert isinstance(result, bytes)


class TestForecastingEndpoints:
    """Test forecasting endpoint methods."""

    @pytest.mark.asyncio
    async def test_get_solar_forecast(self, mock_api_server: TestServer) -> None:
        """Test getting solar forecast."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.forecasting.get_solar_forecast("1234567890")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_weather_forecast(self, mock_api_server: TestServer) -> None:
        """Test getting weather forecast."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.forecasting.get_weather_forecast("1234567890")
            assert isinstance(result, dict)

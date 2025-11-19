"""Unit tests for LuxpowerClient using aiohttp.test."""

from __future__ import annotations

import pytest
from aiohttp.test_utils import TestServer

from pylxpweb import LuxpowerClient
from pylxpweb.exceptions import LuxpowerAuthError


class TestAuthentication:
    """Test authentication functionality."""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_api_server: TestServer) -> None:
        """Test successful login."""
        client = LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        )

        try:
            response = await client.login()
            assert response.success is True
            assert response.username == "testuser"
            assert response.userId == 99999
            assert len(response.plants) > 0
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_login_failure(self, mock_api_server: TestServer) -> None:
        """Test login with invalid credentials."""
        client = LuxpowerClient(
            "wronguser",
            "wrongpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        )

        try:
            with pytest.raises(LuxpowerAuthError):
                await client.login()
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_api_server: TestServer) -> None:
        """Test client as async context manager."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            assert client._session_expires is not None


class TestPlantDiscovery:
    """Test plant/station discovery."""

    @pytest.mark.asyncio
    async def test_get_plants(self, mock_api_server: TestServer) -> None:
        """Test getting list of plants."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.plants.get_plants()
            assert response.total == 1
            assert len(response.rows) == 1
            plant = response.rows[0]
            assert plant.plantId == 99999
            assert plant.name == "My Solar Station"


class TestDeviceDiscovery:
    """Test device discovery."""

    @pytest.mark.asyncio
    async def test_get_devices(self, mock_api_server: TestServer) -> None:
        """Test getting device list."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.devices.get_devices(99999)
            assert response.success is True
            assert len(response.rows) == 3  # 2 inverters + 1 GridBOSS

    @pytest.mark.asyncio
    async def test_get_parallel_groups(self, mock_api_server: TestServer) -> None:
        """Test getting parallel group details."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.devices.get_parallel_group_details(99999)
            assert response.success is True
            assert len(response.parallelGroups) == 1
            group = response.parallelGroups[0]
            assert group.parallelGroup == "A"


class TestRuntimeData:
    """Test runtime data retrieval."""

    @pytest.mark.asyncio
    async def test_get_inverter_runtime(self, mock_api_server: TestServer) -> None:
        """Test getting inverter runtime data."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.devices.get_inverter_runtime("1234567890")
            assert response.success is True
            assert response.serialNum == "1234567890"
            assert response.soc == 71
            assert response.ppv == 0  # PV power
            assert response.pToUser == 1030  # Power to user

    @pytest.mark.asyncio
    async def test_get_inverter_energy(self, mock_api_server: TestServer) -> None:
        """Test getting inverter energy statistics."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.devices.get_inverter_energy("1234567890")
            assert response.success is True
            assert response.serialNum == "1234567890"
            assert response.soc == 71

    @pytest.mark.asyncio
    async def test_get_parallel_energy(self, mock_api_server: TestServer) -> None:
        """Test getting parallel group energy statistics."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.devices.get_parallel_energy("1234567890")
            assert response.success is True

    @pytest.mark.asyncio
    async def test_get_battery_info(self, mock_api_server: TestServer) -> None:
        """Test getting battery information."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.devices.get_battery_info("1234567890")
            assert response.success is True
            assert response.serialNum == "1234567890"
            assert response.soc == 71
            assert len(response.batteryArray) > 0

    @pytest.mark.asyncio
    async def test_get_midbox_runtime(self, mock_api_server: TestServer) -> None:
        """Test getting GridBOSS/MID runtime data."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.devices.get_midbox_runtime("0987654321")
            assert response.success is True
            assert response.serialNum == "0987654321"


class TestDeviceControl:
    """Test device control operations."""

    @pytest.mark.asyncio
    async def test_read_parameters(self, mock_api_server: TestServer) -> None:
        """Test reading device parameters."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.control.read_parameters("1234567890")
            assert response.success is True
            assert response.serialNum == "1234567890"
            assert "HOLD_SYSTEM_CHARGE_SOC_LIMIT" in response.parameters

    @pytest.mark.asyncio
    async def test_write_parameter(self, mock_api_server: TestServer) -> None:
        """Test writing a device parameter."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.control.write_parameter(
                "1234567890", "HOLD_SYSTEM_CHARGE_SOC_LIMIT", "100"
            )
            assert response.success is True

    @pytest.mark.asyncio
    async def test_control_function(self, mock_api_server: TestServer) -> None:
        """Test controlling a device function."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.control.control_function("1234567890", "FUNC_EPS_EN", True)
            assert response.success is True

    @pytest.mark.asyncio
    async def test_start_quick_charge(self, mock_api_server: TestServer) -> None:
        """Test starting quick charge."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.control.start_quick_charge("1234567890")
            assert response.success is True

    @pytest.mark.asyncio
    async def test_stop_quick_charge(self, mock_api_server: TestServer) -> None:
        """Test stopping quick charge."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.control.stop_quick_charge("1234567890")
            assert response.success is True

    @pytest.mark.asyncio
    async def test_get_quick_charge_status(self, mock_api_server: TestServer) -> None:
        """Test getting quick charge status."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            response = await client.control.get_quick_charge_status("1234567890")
            assert response.success is True
            assert response.hasUnclosedQuickChargeTask is False


class TestCaching:
    """Test response caching functionality."""

    @pytest.mark.asyncio
    async def test_runtime_data_caching(self, mock_api_server: TestServer) -> None:
        """Test that runtime data is cached appropriately."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            # First call
            response1 = await client.devices.get_inverter_runtime("1234567890")

            # Second call should use cache
            response2 = await client.devices.get_inverter_runtime("1234567890")

            assert response1.soc == response2.soc
            assert response1.serverTime == response2.serverTime


class TestErrorHandling:
    """Test error handling and retry logic."""

    @pytest.mark.asyncio
    async def test_backoff_on_error(self, mock_api_server: TestServer) -> None:
        """Test that backoff is applied on errors."""
        client = LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        )

        try:
            # Initial state
            assert client._consecutive_errors == 0
            assert client._current_backoff_delay == 0.0

            # Try to login with wrong credentials (will fail)
            try:
                client.username = "wrong"
                client.password = "wrong"
                await client.login()
            except LuxpowerAuthError:
                pass

            # Verify backoff was increased
            assert client._consecutive_errors == 1
            assert client._current_backoff_delay > 0

        finally:
            await client.close()


class TestSessionManagement:
    """Test session management."""

    @pytest.mark.asyncio
    async def test_session_creation(self, mock_api_server: TestServer) -> None:
        """Test that client creates its own session."""
        client = LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        )

        try:
            assert client._session is None
            assert client._owns_session is True

            await client.login()

            assert client._session is not None
            assert client._owns_session is True
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_session_injection(self, mock_api_server: TestServer) -> None:
        """Test that client can use injected session."""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            client = LuxpowerClient(
                "testuser",
                "testpass",
                base_url=str(mock_api_server.make_url("")),
                verify_ssl=False,
                session=session,
            )

            try:
                assert client._session is session
                assert client._owns_session is False

                await client.login()

                # Session should still be the injected one
                assert client._session is session
            finally:
                await client.close()

            # Injected session should not be closed
            assert not session.closed


class TestPlantConfiguration:
    """Test plant configuration methods."""

    @pytest.mark.asyncio
    async def test_get_plant_overview(self, mock_api_server: TestServer) -> None:
        """Test getting plant overview with metrics."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            overview = await client.plants.get_plant_overview()
            assert isinstance(overview, dict)

    @pytest.mark.asyncio
    async def test_get_plant_overview_with_search(self, mock_api_server: TestServer) -> None:
        """Test getting plant overview with search filter."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            overview = await client.plants.get_plant_overview(search_text="Solar")
            assert isinstance(overview, dict)

    @pytest.mark.asyncio
    async def test_get_inverter_overview(self, mock_api_server: TestServer) -> None:
        """Test getting inverter overview."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            overview = await client.plants.get_inverter_overview()
            assert isinstance(overview, dict)

    @pytest.mark.asyncio
    async def test_get_inverter_overview_with_filters(self, mock_api_server: TestServer) -> None:
        """Test getting inverter overview with filters."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            overview = await client.plants.get_inverter_overview(
                page=1,
                rows=10,
                plant_id=99999,
                search_text="1234567890",
                status_filter="normal",
            )
            assert isinstance(overview, dict)

    @pytest.mark.asyncio
    async def test_set_daylight_saving_time(self, mock_api_server: TestServer) -> None:
        """Test setting daylight saving time."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.plants.set_daylight_saving_time(99999, True)
            assert isinstance(result, dict)

            result = await client.plants.set_daylight_saving_time(99999, False)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_plant_details(self, mock_api_server: TestServer) -> None:
        """Test getting plant details."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            details = await client.plants.get_plant_details(99999)
            assert isinstance(details, dict)
            assert details["plantId"] == 12345
            assert details["name"] == "My Solar Station"
            assert details["country"] == "United States of America"
            assert details["timezone"] == "GMT -8"

    @pytest.mark.asyncio
    async def test_prepare_plant_update_data(self, mock_api_server: TestServer) -> None:
        """Test preparing plant update data with static country mapping."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            # Get plant details first
            details = await client.plants.get_plant_details(99999)

            # Prepare update data
            data = await client._prepare_plant_update_data(details, daylightSavingTime=True)

            assert data["plantId"] == "99999"
            assert data["name"] == "My Solar Station"
            assert data["country"] == "UNITED_STATES_OF_AMERICA"
            assert data["timezone"] == "WEST8"
            assert data["daylightSavingTime"] is True
            assert data["continent"] == "NORTH_AMERICA"
            assert data["region"] == "NORTH_AMERICA"

    @pytest.mark.asyncio
    async def test_fetch_country_location_from_api(self, mock_api_server: TestServer) -> None:
        """Test fetching country location from locale API."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            # Test fetching a country from the API
            # The mock returns the country in all continents/regions
            # so it finds the first match
            continent, region = await client._fetch_country_location_from_api(
                "United States of America"
            )
            # Should find a valid continent and region (first match in iteration order)
            assert isinstance(continent, str)
            assert isinstance(region, str)
            assert len(continent) > 0
            assert len(region) > 0

    @pytest.mark.asyncio
    async def test_update_plant_config(self, mock_api_server: TestServer) -> None:
        """Test updating plant configuration."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.plants.update_plant_config(99999, daylightSavingTime=True)
            assert isinstance(result, dict)
            assert result["success"] is True

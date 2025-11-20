"""Unit tests for LuxpowerClient using aioresponses for HTTP mocking.

This approach is faster and more reliable than using TestServer.
"""

from __future__ import annotations

from typing import Any

import pytest
from aioresponses import aioresponses

from pylxpweb import LuxpowerClient
from pylxpweb.exceptions import LuxpowerAuthError

# Import fixtures
from tests.conftest_aioresponses import (
    battery_response,
    energy_response,
    login_response,
    mocked_api,
    plants_response,
    runtime_response,
)

# Base URL for all tests
BASE_URL = "https://monitor.eg4electronics.com"


class TestAuthentication:
    """Test authentication functionality."""

    @pytest.mark.asyncio
    async def test_login_success(
        self, mocked_api: aioresponses, login_response: dict[str, Any]
    ) -> None:
        """Test successful login."""
        # Mock the API endpoint
        mocked_api.post(
            f"{BASE_URL}/WManage/api/login",
            payload=login_response,
        )

        # Test the client
        client = LuxpowerClient("testuser", "testpass")
        response = await client.login()

        assert response.success is True
        assert response.username == "testuser"
        assert response.userId == 99999
        assert len(response.plants) > 0

        await client.close()

    @pytest.mark.asyncio
    async def test_login_failure(self, mocked_api: aioresponses) -> None:
        """Test login with invalid credentials."""
        # Mock failed login
        mocked_api.post(
            f"{BASE_URL}/WManage/api/login",
            payload={"success": False, "message": "Invalid credentials"},
            status=401,
        )

        client = LuxpowerClient("wronguser", "wrongpass")

        with pytest.raises(LuxpowerAuthError):
            await client.login()

        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(
        self, mocked_api: aioresponses, login_response: dict[str, Any]
    ) -> None:
        """Test client as async context manager."""
        mocked_api.post(
            f"{BASE_URL}/WManage/api/login",
            payload=login_response,
        )

        async with LuxpowerClient("testuser", "testpass") as client:
            assert client._session_expires is not None


class TestPlantDiscovery:
    """Test plant/station discovery."""

    @pytest.mark.asyncio
    async def test_get_plants(
        self,
        mocked_api: aioresponses,
        login_response: dict[str, Any],
        plants_response: dict[str, Any],
    ) -> None:
        """Test getting list of plants."""
        # Mock login
        mocked_api.post(
            f"{BASE_URL}/WManage/api/login",
            payload=login_response,
        )

        # Mock plants list
        mocked_api.post(
            f"{BASE_URL}/WManage/web/config/plant/list/viewer",
            payload=plants_response,
        )

        async with LuxpowerClient("testuser", "testpass") as client:
            response = await client.plants.get_plants()
            assert response.total == 1
            assert len(response.rows) == 1
            plant = response.rows[0]
            assert plant.plantId == 99999
            assert plant.name == "Example Solar Station"


class TestDeviceDiscovery:
    """Test device discovery."""

    @pytest.mark.asyncio
    async def test_get_devices(
        self,
        mocked_api: aioresponses,
        login_response: dict[str, Any],
    ) -> None:
        """Test getting device list."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock devices list
        devices_response = {
            "success": True,
            "rows": login_response["plants"][0]["inverters"],
        }
        mocked_api.post(
            f"{BASE_URL}/WManage/api/inverterOverview/list",
            payload=devices_response,
        )

        async with LuxpowerClient("testuser", "testpass") as client:
            response = await client.devices.get_devices(99999)
            assert response.success is True
            assert len(response.rows) == 3  # 2 inverters + 1 GridBOSS


class TestRuntimeData:
    """Test runtime data retrieval."""

    @pytest.mark.asyncio
    async def test_get_inverter_runtime(
        self,
        mocked_api: aioresponses,
        login_response: dict[str, Any],
        runtime_response: dict[str, Any],
    ) -> None:
        """Test getting inverter runtime data."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock runtime data
        mocked_api.post(
            f"{BASE_URL}/WManage/api/inverter/getInverterRuntime",
            payload=runtime_response,
        )

        async with LuxpowerClient("testuser", "testpass") as client:
            response = await client.devices.get_inverter_runtime("1234567890")
            assert response.success is True
            assert response.serialNum == "1234567890"
            assert response.soc == 71
            assert response.ppv == 0  # PV power
            assert response.pToUser == 1030  # Power to user

    @pytest.mark.asyncio
    async def test_get_inverter_energy(
        self,
        mocked_api: aioresponses,
        login_response: dict[str, Any],
        energy_response: dict[str, Any],
    ) -> None:
        """Test getting inverter energy statistics."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock energy data
        mocked_api.post(
            f"{BASE_URL}/WManage/api/inverter/getInverterEnergyInfo",
            payload=energy_response,
        )

        async with LuxpowerClient("testuser", "testpass") as client:
            response = await client.devices.get_inverter_energy("1234567890")
            assert response.success is True
            assert response.serialNum == "1234567890"
            assert response.soc == 71

    @pytest.mark.asyncio
    async def test_get_battery_info(
        self,
        mocked_api: aioresponses,
        login_response: dict[str, Any],
        battery_response: dict[str, Any],
    ) -> None:
        """Test getting battery information."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock battery info
        mocked_api.post(
            f"{BASE_URL}/WManage/api/battery/getBatteryInfo",
            payload=battery_response,
        )

        async with LuxpowerClient("testuser", "testpass") as client:
            response = await client.devices.get_battery_info("1234567890")
            assert response.success is True
            assert response.serialNum == "1234567890"
            assert response.soc == 71
            assert len(response.batteryArray) > 0


class TestCaching:
    """Test response caching functionality."""

    @pytest.mark.asyncio
    async def test_runtime_data_caching(
        self,
        mocked_api: aioresponses,
        login_response: dict[str, Any],
        runtime_response: dict[str, Any],
    ) -> None:
        """Test that runtime data is cached appropriately."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock runtime data (only once - cache will be used for second call)
        mocked_api.post(
            f"{BASE_URL}/WManage/api/inverter/getInverterRuntime",
            payload=runtime_response,
        )

        async with LuxpowerClient("testuser", "testpass") as client:
            # First call
            response1 = await client.devices.get_inverter_runtime("1234567890")

            # Second call should use cache
            response2 = await client.devices.get_inverter_runtime("1234567890")

            assert response1.soc == response2.soc
            assert response1.serverTime == response2.serverTime


class TestErrorHandling:
    """Test error handling and retry logic."""

    @pytest.mark.asyncio
    async def test_backoff_on_error(
        self,
        mocked_api: aioresponses,
    ) -> None:
        """Test that backoff is applied on errors."""
        # Mock failed login (mock it twice since client will retry)
        mocked_api.post(
            f"{BASE_URL}/WManage/api/login",
            payload={"success": False, "message": "Invalid credentials"},
            status=401,
        )
        mocked_api.post(
            f"{BASE_URL}/WManage/api/login",
            payload={"success": False, "message": "Invalid credentials"},
            status=401,
        )

        client = LuxpowerClient("wrong", "wrong")

        try:
            # Initial state
            assert client._consecutive_errors == 0
            assert client._current_backoff_delay == 0.0

            # Try to login with wrong credentials (will fail)
            try:
                await client.login()
            except LuxpowerAuthError:
                pass

            # Verify backoff was increased (client retries, so 2 errors)
            assert client._consecutive_errors >= 1
            assert client._current_backoff_delay > 0

        finally:
            await client.close()


class TestSessionManagement:
    """Test session management."""

    @pytest.mark.asyncio
    async def test_session_creation(
        self,
        mocked_api: aioresponses,
        login_response: dict[str, Any],
    ) -> None:
        """Test that client creates its own session."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        client = LuxpowerClient("testuser", "testpass")

        try:
            assert client._session is None
            assert client._owns_session is True

            await client.login()

            assert client._session is not None
            assert client._owns_session is True
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_session_injection(
        self,
        mocked_api: aioresponses,
        login_response: dict[str, Any],
    ) -> None:
        """Test that client can use injected session."""
        import aiohttp

        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        async with aiohttp.ClientSession() as session:
            client = LuxpowerClient("testuser", "testpass", session=session)

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

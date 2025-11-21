"""Unit tests for quick charge/discharge endpoints."""

from __future__ import annotations

from typing import Any

import pytest
from aioresponses import aioresponses

from pylxpweb import LuxpowerClient
from pylxpweb.models import QuickChargeStatus, SuccessResponse

# Base URL for all tests
BASE_URL = "https://monitor.eg4electronics.com"


class TestQuickChargeEndpoints:
    """Test quick charge control endpoints."""

    @pytest.mark.asyncio
    async def test_start_quick_charge(
        self, mocked_api: aioresponses, login_response: dict[str, Any]
    ):
        """Test starting quick charge operation."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock start quick charge
        mocked_api.post(
            f"{BASE_URL}/WManage/web/config/quickCharge/start",
            payload={"success": True, "msg": ""},
        )

        client = LuxpowerClient("testuser", "testpass")
        async with client:
            result = await client.api.control.start_quick_charge("1234567890")

            assert isinstance(result, SuccessResponse)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_stop_quick_charge(
        self, mocked_api: aioresponses, login_response: dict[str, Any]
    ):
        """Test stopping quick charge operation."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock stop quick charge - success case
        mocked_api.post(
            f"{BASE_URL}/WManage/web/config/quickCharge/stop",
            payload={"success": True, "msg": ""},
        )

        client = LuxpowerClient("testuser", "testpass")
        async with client:
            result = await client.api.control.stop_quick_charge("1234567890")

            assert isinstance(result, SuccessResponse)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_get_quick_charge_status(
        self, mocked_api: aioresponses, login_response: dict[str, Any]
    ):
        """Test getting quick charge status."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock get status
        mocked_api.post(
            f"{BASE_URL}/WManage/web/config/quickCharge/getStatusInfo",
            payload={
                "success": True,
                "hasUnclosedQuickChargeTask": False,
                "hasUnclosedQuickDischargeTask": False,
            },
        )

        client = LuxpowerClient("testuser", "testpass")
        async with client:
            result = await client.api.control.get_quick_charge_status("1234567890")

            assert isinstance(result, QuickChargeStatus)
            assert result.success is True
            assert result.hasUnclosedQuickChargeTask is False
            assert result.hasUnclosedQuickDischargeTask is False

    @pytest.mark.asyncio
    async def test_get_quick_charge_status_active(
        self, mocked_api: aioresponses, login_response: dict[str, Any]
    ):
        """Test getting quick charge status when active."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock get status - charge active
        mocked_api.post(
            f"{BASE_URL}/WManage/web/config/quickCharge/getStatusInfo",
            payload={
                "success": True,
                "hasUnclosedQuickChargeTask": True,
                "hasUnclosedQuickDischargeTask": False,
            },
        )

        client = LuxpowerClient("testuser", "testpass")
        async with client:
            result = await client.api.control.get_quick_charge_status("1234567890")

            assert result.hasUnclosedQuickChargeTask is True
            assert result.hasUnclosedQuickDischargeTask is False


class TestQuickDischargeEndpoints:
    """Test quick discharge control endpoints."""

    @pytest.mark.asyncio
    async def test_start_quick_discharge(
        self, mocked_api: aioresponses, login_response: dict[str, Any]
    ):
        """Test starting quick discharge operation."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock start quick discharge
        mocked_api.post(
            f"{BASE_URL}/WManage/web/config/quickDischarge/start",
            payload={"success": True, "msg": ""},
        )

        client = LuxpowerClient("testuser", "testpass")
        async with client:
            result = await client.api.control.start_quick_discharge("1234567890")

            assert isinstance(result, SuccessResponse)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_stop_quick_discharge(
        self, mocked_api: aioresponses, login_response: dict[str, Any]
    ):
        """Test stopping quick discharge operation."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock stop quick discharge
        mocked_api.post(
            f"{BASE_URL}/WManage/web/config/quickDischarge/stop",
            payload={"success": True, "msg": ""},
        )

        client = LuxpowerClient("testuser", "testpass")
        async with client:
            result = await client.api.control.stop_quick_discharge("1234567890")

            assert isinstance(result, SuccessResponse)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_get_quick_discharge_status_via_charge_endpoint(
        self, mocked_api: aioresponses, login_response: dict[str, Any]
    ):
        """Test getting quick discharge status via quickCharge/getStatusInfo endpoint."""
        # Mock login
        mocked_api.post(f"{BASE_URL}/WManage/api/login", payload=login_response)

        # Mock get status - discharge active
        mocked_api.post(
            f"{BASE_URL}/WManage/web/config/quickCharge/getStatusInfo",
            payload={
                "success": True,
                "hasUnclosedQuickChargeTask": False,
                "hasUnclosedQuickDischargeTask": True,
            },
        )

        client = LuxpowerClient("testuser", "testpass")
        async with client:
            result = await client.api.control.get_quick_charge_status("1234567890")

            # Verify the shared endpoint returns discharge status
            assert result.hasUnclosedQuickChargeTask is False
            assert result.hasUnclosedQuickDischargeTask is True


class TestQuickChargeStatusModel:
    """Test QuickChargeStatus model with both charge and discharge fields."""

    def test_model_with_both_fields(self):
        """Test model with both charge and discharge status."""
        status = QuickChargeStatus(
            success=True,
            hasUnclosedQuickChargeTask=True,
            hasUnclosedQuickDischargeTask=False,
        )

        assert status.success is True
        assert status.hasUnclosedQuickChargeTask is True
        assert status.hasUnclosedQuickDischargeTask is False

    def test_model_with_default_discharge_field(self):
        """Test model with discharge field defaulting to False."""
        status = QuickChargeStatus(
            success=True,
            hasUnclosedQuickChargeTask=False,
        )

        # Should default to False if not provided (for older API versions)
        assert status.hasUnclosedQuickDischargeTask is False

    def test_model_both_active(self):
        """Test model with both charge and discharge active (unlikely but valid)."""
        status = QuickChargeStatus(
            success=True,
            hasUnclosedQuickChargeTask=True,
            hasUnclosedQuickDischargeTask=True,
        )

        assert status.hasUnclosedQuickChargeTask is True
        assert status.hasUnclosedQuickDischargeTask is True

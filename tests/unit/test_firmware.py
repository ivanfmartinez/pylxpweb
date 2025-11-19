"""Unit tests for firmware update functionality."""

from __future__ import annotations

import pytest
from aiohttp.test_utils import TestServer

from pylxpweb.client import LuxpowerClient
from pylxpweb.models import (
    FirmwareUpdateCheck,
    FirmwareUpdateStatus,
    UpdateEligibilityStatus,
    UpdateStatus,
)


class TestFirmwareUpdateCheck:
    """Test firmware update check functionality."""

    @pytest.mark.asyncio
    async def test_check_firmware_updates_available(self, mock_api_server: TestServer) -> None:
        """Test checking for firmware updates when updates are available."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.firmware.check_firmware_updates("1234567890")

            assert isinstance(result, FirmwareUpdateCheck)
            assert result.success is True
            assert result.details.serialNum == "1234567890"
            assert result.details.v1 == 33
            assert result.details.lastV1 == 37
            assert result.details.has_update() is True
            assert result.details.has_app_update() is True
            assert result.details.has_parameter_update() is True
            assert result.infoForwardUrl is not None


class TestFirmwareUpdateStatus:
    """Test firmware update status functionality."""

    @pytest.mark.asyncio
    async def test_get_firmware_status_complete(self, mock_api_server: TestServer) -> None:
        """Test getting firmware update status - completed update."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.firmware.get_firmware_update_status()

            assert isinstance(result, FirmwareUpdateStatus)
            assert result.progressing is False
            assert len(result.deviceInfos) == 1

            device = result.deviceInfos[0]
            assert device.inverterSn == "1234567890"
            assert device.updateStatus == UpdateStatus.SUCCESS
            assert device.is_complete() is True
            assert device.is_in_progress() is False
            assert device.is_failed() is False
            assert device.updateRate == "100% - 561 / 561"


class TestUpdateEligibility:
    """Test firmware update eligibility checks."""

    @pytest.mark.asyncio
    async def test_check_eligibility_allowed(self, mock_api_server: TestServer) -> None:
        """Test eligibility check - device allowed to update."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            result = await client.firmware.check_update_eligibility("1234567890")

            assert isinstance(result, UpdateEligibilityStatus)
            assert result.success is True
            assert result.msg == "allowToUpdate"
            assert result.is_allowed() is True


class TestStartFirmwareUpdate:
    """Test starting firmware updates."""

    @pytest.mark.asyncio
    async def test_start_firmware_update_success(self, mock_api_server: TestServer) -> None:
        """Test starting firmware update successfully."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            # Start update (this is a mock, won't actually update)
            result = await client.firmware.start_firmware_update("1234567890")

            assert result is True

    @pytest.mark.asyncio
    async def test_start_firmware_update_with_fast_mode(self, mock_api_server: TestServer) -> None:
        """Test starting firmware update with fast mode enabled."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            # Start update with fast mode
            result = await client.firmware.start_firmware_update("1234567890", try_fast_mode=True)

            assert result is True

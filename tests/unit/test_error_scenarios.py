"""Unit tests for error handling and edge cases."""

from __future__ import annotations

from typing import Any

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from pylxpweb.client import LuxpowerClient
from pylxpweb.exceptions import (
    LuxpowerAPIError,
    LuxpowerAuthError,
    LuxpowerConnectionError,
)


class TestAuthenticationErrors:
    """Test authentication error scenarios."""

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, mock_api_server: TestServer) -> None:
        """Test login with invalid credentials raises AuthError."""
        # Invalid credentials should fail (testuser/testpass are valid)
        client = LuxpowerClient(
            "invalid_user",
            "invalid_pass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        )

        try:
            with pytest.raises(LuxpowerAuthError):
                await client.login()
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_api_call_without_explicit_login(self, mock_api_server: TestServer) -> None:
        """Test that API calls without explicit login still work."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            # Context manager calls login automatically
            # Make API call - should work
            result = await client.get_plants()
            assert result.total >= 0


class TestAPIErrors:
    """Test API error responses."""

    @pytest.mark.asyncio
    async def test_auth_required_for_api_calls(self, mock_api_server: TestServer) -> None:
        """Test that making API calls requires authentication."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            # Context manager already logged in
            # API calls should work
            result = await client.get_plants()
            assert result is not None


class TestConnectionErrors:
    """Test connection error scenarios."""

    @pytest.mark.asyncio
    async def test_connection_timeout(self) -> None:
        """Test handling of connection timeouts."""
        # Use an invalid URL that will fail to connect
        client = LuxpowerClient(
            "test",
            "test",
            base_url="http://localhost:9999",  # Non-existent server
            verify_ssl=False,
        )

        try:
            with pytest.raises(LuxpowerConnectionError):
                await client.login()
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_invalid_base_url(self) -> None:
        """Test handling of malformed base URL."""
        client = LuxpowerClient(
            "test",
            "test",
            base_url="not-a-valid-url",
            verify_ssl=False,
        )

        try:
            with pytest.raises((LuxpowerConnectionError, ValueError)):
                await client.login()
        finally:
            await client.close()


class TestBackoffRetry:
    """Test exponential backoff and retry logic."""

    @pytest.mark.asyncio
    async def test_backoff_on_repeated_errors(self) -> None:
        """Test that backoff increases with repeated errors."""
        call_count = 0

        async def handle_failing_login(request: web.Request) -> web.Response:
            nonlocal call_count
            call_count += 1
            # Always fail
            return web.json_response({"success": False}, status=500)

        app = web.Application()
        app.router.add_post("/WManage/api/login", handle_failing_login)

        server = TestServer(app)
        await server.start_server()

        try:
            client = LuxpowerClient(
                "test",
                "test",
                base_url=str(server.make_url("")),
                verify_ssl=False,
            )

            try:
                # First attempt should fail quickly
                with pytest.raises(LuxpowerAPIError):
                    await client.login()

                # Backoff should be active now, indicated by _consecutive_errors
                assert client._consecutive_errors > 0
            finally:
                await client.close()
        finally:
            await server.close()


class TestCacheBehavior:
    """Test caching behavior and edge cases."""

    @pytest.mark.asyncio
    async def test_cache_is_used(self, mock_api_server: TestServer) -> None:
        """Test that caching works correctly."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            # First call - should cache
            runtime1 = await client.get_inverter_runtime("1234567890")
            assert runtime1.serialNum == "1234567890"

            # Cache should now have the runtime data
            assert len(client._response_cache) > 0


class TestSessionManagement:
    """Test session management and lifecycle."""

    @pytest.mark.asyncio
    async def test_session_reuse(self, mock_api_server: TestServer) -> None:
        """Test that session is reused across requests."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            # Make multiple requests
            await client.get_plants()
            await client.get_plants()

            # Session should be reused
            assert client._session is not None
            assert not client._session.closed

    @pytest.mark.asyncio
    async def test_session_injection(self, mock_api_server: TestServer) -> None:
        """Test injecting an external session."""
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
                await client.login()
                assert client._session is session
            finally:
                # Closing client should NOT close injected session
                await client.close()
                assert not session.closed

    @pytest.mark.asyncio
    async def test_session_cleanup_on_close(self, mock_api_server: TestServer) -> None:
        """Test that session is properly closed on client close."""
        client = LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        )

        await client.login()
        session = client._session
        assert session is not None
        assert not session.closed

        await client.close()
        assert session.closed


class TestContextManager:
    """Test context manager behavior."""

    @pytest.mark.asyncio
    async def test_context_manager_login_and_close(self, mock_api_server: TestServer) -> None:
        """Test that context manager handles login and close properly."""
        async with LuxpowerClient(
            "testuser",
            "testpass",
            base_url=str(mock_api_server.make_url("")),
            verify_ssl=False,
        ) as client:
            # Should be logged in
            assert client._session_expires is not None
            # Session should be active
            assert client._session is not None
            assert not client._session.closed

        # After exiting context, session should be closed
        # (we can't test this easily without keeping reference)


class TestPlantDetailsErrors:
    """Test plant details error scenarios."""

    @pytest.mark.asyncio
    async def test_get_plant_details_not_found(self, login_response: dict[str, Any]) -> None:
        """Test error when plant details are not found."""

        async def handle_empty_plant_details(request: web.Request) -> web.Response:
            return web.json_response({"success": True, "total": 0, "rows": []})

        async def handle_login(request: web.Request) -> web.Response:
            return web.json_response(login_response)

        app = web.Application()
        app.router.add_post("/WManage/api/login", handle_login)
        app.router.add_post("/WManage/web/config/plant/list/viewer", handle_empty_plant_details)

        server = TestServer(app)
        await server.start_server()

        try:
            async with LuxpowerClient(
                "test",
                "test",
                base_url=str(server.make_url("")),
                verify_ssl=False,
            ) as client:
                from pylxpweb.exceptions import LuxpowerAPIError

                with pytest.raises(LuxpowerAPIError, match="Plant .* not found"):
                    await client.get_plant_details(99999)
        finally:
            await server.close()


class TestLocaleAPIErrors:
    """Test locale API error scenarios."""

    @pytest.mark.asyncio
    async def test_fetch_country_not_in_any_region(self, login_response: dict[str, Any]) -> None:
        """Test error when country is not found in any region."""

        async def handle_empty_regions(request: web.Request) -> web.Response:
            return web.json_response([])

        async def handle_empty_countries(request: web.Request) -> web.Response:
            return web.json_response([])

        async def handle_login(request: web.Request) -> web.Response:
            return web.json_response(login_response)

        app = web.Application()
        app.router.add_post("/WManage/api/login", handle_login)
        app.router.add_post("/WManage/locale/region", handle_empty_regions)
        app.router.add_post("/WManage/locale/country", handle_empty_countries)

        server = TestServer(app)
        await server.start_server()

        try:
            async with LuxpowerClient(
                "test",
                "test",
                base_url=str(server.make_url("")),
                verify_ssl=False,
            ) as client:
                from pylxpweb.exceptions import LuxpowerAPIError

                with pytest.raises(LuxpowerAPIError, match="Country .* not found in locale API"):
                    await client._fetch_country_location_from_api("NonexistentCountry")
        finally:
            await server.close()

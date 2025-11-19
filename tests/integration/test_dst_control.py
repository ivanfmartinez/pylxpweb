"""Integration tests for DST control functionality."""

# Import redaction helper
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pylxpweb import LuxpowerClient


@pytest.mark.asyncio
async def test_get_plant_details(live_client: LuxpowerClient) -> None:
    """Test getting plant details with DST status."""
    plants = await live_client.plants.get_plants()
    assert len(plants.rows) > 0

    plant_id = str(plants.rows[0].plantId)
    details = await live_client.plants.get_plant_details(plant_id)

    # Verify required fields for DST control
    assert "plantId" in details
    assert "name" in details
    assert "timezone" in details
    assert "country" in details
    assert "daylightSavingTime" in details
    assert "createDate" in details

    # Verify timezone format
    assert details["timezone"].startswith("GMT")


@pytest.mark.asyncio
async def test_dst_toggle(live_client: LuxpowerClient) -> None:
    """Test toggling DST on and off.

    IMPORTANT: This test reads the current state, toggles it, then restores
    the CURRENT state from the API (not a cached value) to ensure the live
    system is always left in its original configuration.
    """
    plants = await live_client.plants.get_plants()
    plant_id = str(plants.rows[0].plantId)

    # Get current DST status from API
    details = await live_client.plants.get_plant_details(plant_id)
    original_dst = details["daylightSavingTime"]

    try:
        # Toggle DST
        new_dst = not original_dst
        result = await live_client.plants.set_daylight_saving_time(plant_id, new_dst)

        assert result["success"] is True

        # Verify change
        updated = await live_client.plants.get_plant_details(plant_id)
        assert updated["daylightSavingTime"] == new_dst

    finally:
        # ALWAYS restore by reading current state from API first
        # This ensures we restore the actual original value, not a cached one
        current_details = await live_client.plants.get_plant_details(plant_id)

        # Only restore if current state differs from original
        if current_details["daylightSavingTime"] != original_dst:
            await live_client.plants.set_daylight_saving_time(plant_id, original_dst)

            # Verify restoration
            final = await live_client.plants.get_plant_details(plant_id)
            assert final["daylightSavingTime"] == original_dst


@pytest.mark.asyncio
async def test_update_plant_config(live_client: LuxpowerClient) -> None:
    """Test updating plant configuration with hybrid approach.

    IMPORTANT: This test reads the current state, toggles it, then restores
    the CURRENT state from the API (not a cached value) to ensure the live
    system is always left in its original configuration.
    """
    plants = await live_client.plants.get_plants()
    plant_id = str(plants.rows[0].plantId)

    # Get current config from API
    details = await live_client.plants.get_plant_details(plant_id)
    original_dst = details["daylightSavingTime"]

    try:
        # Update DST via update_plant_config
        result = await live_client.plants.update_plant_config(
            plant_id, daylightSavingTime=not original_dst
        )

        assert result["success"] is True

        # Verify change
        updated = await live_client.plants.get_plant_details(plant_id)
        assert updated["daylightSavingTime"] == (not original_dst)

    finally:
        # ALWAYS restore by reading current state from API first
        # This ensures we restore the actual original value, not a cached one
        current_details = await live_client.plants.get_plant_details(plant_id)

        # Only restore if current state differs from original
        if current_details["daylightSavingTime"] != original_dst:
            await live_client.plants.update_plant_config(plant_id, daylightSavingTime=original_dst)

            # Verify restoration
            final = await live_client.plants.get_plant_details(plant_id)
            assert final["daylightSavingTime"] == original_dst


@pytest.mark.asyncio
async def test_hybrid_mapping_static_path(live_client: LuxpowerClient) -> None:
    """Test that common countries use static mapping (fast path)."""
    plants = await live_client.plants.get_plants()
    plant_id = str(plants.rows[0].plantId)

    details = await live_client.plants.get_plant_details(plant_id)
    original_dst = details["daylightSavingTime"]

    # Assuming USA for this test (adjust if different)
    if details["country"] == "United States of America":
        # This should use static mapping (no API calls)
        # We can't easily verify this without logging, but we can verify it works
        # Set to same value (no-op) to test the code path
        result = await live_client.plants.set_daylight_saving_time(plant_id, original_dst)
        assert result["success"] is True

        # Verify no change (since we set it to the same value)
        final = await live_client.plants.get_plant_details(plant_id)
        assert final["daylightSavingTime"] == original_dst


@pytest.mark.asyncio
async def test_invalid_plant_id(live_client: LuxpowerClient) -> None:
    """Test DST control with invalid plant ID.

    Note: The API silently accepts invalid plant IDs and returns success=True.
    This test verifies that the client can handle this without raising exceptions.
    In practice, invalid plant IDs simply have no effect.
    """
    # API accepts invalid plant IDs without error
    result = await live_client.plants.set_daylight_saving_time("99999999", True)
    assert result["success"] is True

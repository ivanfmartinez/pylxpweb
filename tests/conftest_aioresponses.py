"""Simplified conftest using aioresponses for fast, reliable HTTP mocking."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from aioresponses import aioresponses

# Load sample API responses
SAMPLES_DIR = Path(__file__).parent / "samples"


def load_sample(filename: str) -> dict[str, Any]:
    """Load a sample JSON response file."""
    file_path = SAMPLES_DIR / filename
    with open(file_path) as f:
        return json.load(f)


@pytest.fixture
def mocked_api() -> Generator[aioresponses, None, None]:
    """Provide aioresponses mock for HTTP requests.

    This fixture mocks all HTTP requests made by aiohttp.ClientSession.
    Configure mocked responses within your test using:

        mocked_api.post(url, payload=data, status=200)
    """
    with aioresponses() as m:
        yield m


@pytest.fixture
def login_response() -> dict[str, Any]:
    """Sample login response."""
    return load_sample("login.json")


@pytest.fixture
def plants_response() -> dict[str, Any]:
    """Sample plants list response."""
    data = load_sample("plants.json")
    return {"total": len(data), "rows": data}


@pytest.fixture
def runtime_response() -> dict[str, Any]:
    """Sample inverter runtime response."""
    return load_sample("runtime_1234567890.json")


@pytest.fixture
def energy_response() -> dict[str, Any]:
    """Sample energy info response."""
    return load_sample("energy_1234567890.json")


@pytest.fixture
def battery_response() -> dict[str, Any]:
    """Sample battery info response."""
    return load_sample("battery_1234567890.json")


@pytest.fixture
def parallel_energy_response() -> dict[str, Any]:
    """Sample parallel energy response."""
    # Return a minimal valid response
    return {"success": True}


@pytest.fixture
def parallel_groups_response() -> dict[str, Any]:
    """Sample parallel groups response."""
    return {
        "success": True,
        "parallelGroups": [
            {
                "parallelGroup": "A",
                "inverters": [],
            }
        ],
    }

"""Unit tests for constants module."""

from __future__ import annotations

import pytest

from pylxpweb.constants import (
    CONTINENT_MAP,
    CONTINENT_REVERSE_MAP,
    COUNTRY_MAP,
    COUNTRY_REVERSE_MAP,
    COUNTRY_TO_LOCATION_STATIC,
    REGION_MAP,
    REGION_REVERSE_MAP,
    TIMEZONE_MAP,
    TIMEZONE_REVERSE_MAP,
    get_continent_enum,
    get_continent_region_from_country,
    get_country_enum,
    get_region_enum,
    get_timezone_enum,
)


class TestTimezoneMappings:
    """Test timezone mapping constants and functions."""

    def test_timezone_map_exists(self) -> None:
        """Test that timezone map exists and has entries."""
        assert isinstance(TIMEZONE_MAP, dict)
        assert len(TIMEZONE_MAP) > 0

    def test_timezone_reverse_map_exists(self) -> None:
        """Test that reverse timezone map exists."""
        assert isinstance(TIMEZONE_REVERSE_MAP, dict)
        assert len(TIMEZONE_REVERSE_MAP) > 0

    def test_timezone_maps_are_inverse(self) -> None:
        """Test that forward and reverse maps are inverses."""
        # Every forward mapping should have a reverse
        for human, enum in TIMEZONE_MAP.items():
            assert enum in TIMEZONE_REVERSE_MAP
            assert TIMEZONE_REVERSE_MAP[enum] == human

    def test_timezone_map_has_expected_entries(self) -> None:
        """Test that timezone map has specific expected entries."""
        assert TIMEZONE_MAP["GMT -8"] == "WEST8"
        assert TIMEZONE_MAP["GMT 0"] == "ZERO"
        assert TIMEZONE_MAP["GMT +8"] == "EAST8"
        assert TIMEZONE_MAP["GMT +5:30"] == "EAST5_30"

    def test_get_timezone_enum_valid(self) -> None:
        """Test getting timezone enum for valid input."""
        assert get_timezone_enum("GMT -8") == "WEST8"
        assert get_timezone_enum("GMT 0") == "ZERO"
        assert get_timezone_enum("GMT +1") == "EAST1"

    def test_get_timezone_enum_invalid(self) -> None:
        """Test that invalid timezone raises ValueError."""
        with pytest.raises(ValueError, match="Unknown timezone"):
            get_timezone_enum("GMT +99")


class TestCountryMappings:
    """Test country mapping constants and functions."""

    def test_country_map_exists(self) -> None:
        """Test that country map exists and has entries."""
        assert isinstance(COUNTRY_MAP, dict)
        assert len(COUNTRY_MAP) > 0

    def test_country_reverse_map_exists(self) -> None:
        """Test that reverse country map exists."""
        assert isinstance(COUNTRY_REVERSE_MAP, dict)
        assert len(COUNTRY_REVERSE_MAP) > 0

    def test_country_maps_are_inverse(self) -> None:
        """Test that forward and reverse maps are inverses."""
        for human, enum in COUNTRY_MAP.items():
            assert enum in COUNTRY_REVERSE_MAP
            assert COUNTRY_REVERSE_MAP[enum] == human

    def test_country_map_has_expected_entries(self) -> None:
        """Test that country map has North American countries."""
        assert COUNTRY_MAP["United States of America"] == "UNITED_STATES_OF_AMERICA"
        assert COUNTRY_MAP["Canada"] == "CANADA"
        assert COUNTRY_MAP["Mexico"] == "MEXICO"

    def test_get_country_enum_valid(self) -> None:
        """Test getting country enum for valid input."""
        assert get_country_enum("United States of America") == "UNITED_STATES_OF_AMERICA"
        assert get_country_enum("Canada") == "CANADA"

    def test_get_country_enum_invalid(self) -> None:
        """Test that invalid country raises ValueError."""
        with pytest.raises(ValueError, match="Unknown country"):
            get_country_enum("Atlantis")


class TestContinentMappings:
    """Test continent mapping constants and functions."""

    def test_continent_map_exists(self) -> None:
        """Test that continent map exists and has entries."""
        assert isinstance(CONTINENT_MAP, dict)
        assert len(CONTINENT_MAP) == 6  # All 6 continents

    def test_continent_reverse_map_exists(self) -> None:
        """Test that reverse continent map exists."""
        assert isinstance(CONTINENT_REVERSE_MAP, dict)
        assert len(CONTINENT_REVERSE_MAP) == 6

    def test_continent_maps_are_inverse(self) -> None:
        """Test that forward and reverse maps are inverses."""
        for human, enum in CONTINENT_MAP.items():
            assert enum in CONTINENT_REVERSE_MAP
            assert CONTINENT_REVERSE_MAP[enum] == human

    def test_continent_map_has_all_continents(self) -> None:
        """Test that all 6 continents are present."""
        expected_continents = {
            "Africa",
            "Asia",
            "Europe",
            "North America",
            "Oceania",
            "South America",
        }
        assert set(CONTINENT_MAP.keys()) == expected_continents

    def test_get_continent_enum_valid(self) -> None:
        """Test getting continent enum for valid input."""
        assert get_continent_enum("North America") == "NORTH_AMERICA"
        assert get_continent_enum("Europe") == "EUROPE"
        assert get_continent_enum("Asia") == "ASIA"

    def test_get_continent_enum_invalid(self) -> None:
        """Test that invalid continent raises ValueError."""
        with pytest.raises(ValueError, match="Unknown continent"):
            get_continent_enum("Pangaea")


class TestRegionMappings:
    """Test region mapping constants and functions."""

    def test_region_map_exists(self) -> None:
        """Test that region map exists and has entries."""
        assert isinstance(REGION_MAP, dict)
        assert len(REGION_MAP) > 0

    def test_region_reverse_map_exists(self) -> None:
        """Test that reverse region map exists."""
        assert isinstance(REGION_REVERSE_MAP, dict)
        assert len(REGION_REVERSE_MAP) > 0

    def test_region_maps_are_inverse(self) -> None:
        """Test that forward and reverse maps are inverses."""
        for human, enum in REGION_MAP.items():
            assert enum in REGION_REVERSE_MAP
            assert REGION_REVERSE_MAP[enum] == human

    def test_region_map_has_north_america_regions(self) -> None:
        """Test that region map has North American regions."""
        # Note: REGION_MAP is context-dependent, showing North America regions
        assert "North America" in REGION_MAP or "NORTH_AMERICA" in REGION_REVERSE_MAP

    def test_get_region_enum_valid(self) -> None:
        """Test getting region enum for valid input."""
        # Test with known regions from the map
        for human_readable in REGION_MAP:
            enum_value = get_region_enum(human_readable)
            assert enum_value == REGION_MAP[human_readable]

    def test_get_region_enum_invalid(self) -> None:
        """Test that invalid region raises ValueError."""
        with pytest.raises(ValueError, match="Unknown region"):
            get_region_enum("Unknown Region")


class TestCountryLocationMapping:
    """Test country to location (continent/region) mapping."""

    def test_static_mapping_exists(self) -> None:
        """Test that static country-to-location mapping exists."""
        assert isinstance(COUNTRY_TO_LOCATION_STATIC, dict)
        assert len(COUNTRY_TO_LOCATION_STATIC) > 0

    def test_static_mapping_structure(self) -> None:
        """Test that static mapping has correct structure."""
        for country, (continent, region) in COUNTRY_TO_LOCATION_STATIC.items():
            assert isinstance(country, str)
            assert isinstance(continent, str)
            assert isinstance(region, str)
            # Verify continents are valid enum values
            assert continent in CONTINENT_REVERSE_MAP or continent in CONTINENT_MAP.values()

    def test_static_mapping_has_common_countries(self) -> None:
        """Test that static mapping includes common countries."""
        assert "United States of America" in COUNTRY_TO_LOCATION_STATIC
        assert "Canada" in COUNTRY_TO_LOCATION_STATIC
        assert "United Kingdom" in COUNTRY_TO_LOCATION_STATIC
        assert "Australia" in COUNTRY_TO_LOCATION_STATIC

    def test_get_continent_region_from_country_valid(self) -> None:
        """Test getting continent/region for known countries."""
        continent, region = get_continent_region_from_country("United States of America")
        assert continent == "NORTH_AMERICA"
        assert region == "NORTH_AMERICA"

        continent, region = get_continent_region_from_country("United Kingdom")
        assert continent == "EUROPE"
        assert region == "WESTERN_EUROPE"

    def test_get_continent_region_from_country_invalid(self) -> None:
        """Test that unknown country raises ValueError."""
        with pytest.raises(ValueError, match="not in static mapping"):
            get_continent_region_from_country("Unknown Country")

    def test_all_static_countries_covered(self) -> None:
        """Test that all static mapped countries work with the function."""
        for country in COUNTRY_TO_LOCATION_STATIC:
            # Should not raise
            continent, region = get_continent_region_from_country(country)
            assert isinstance(continent, str)
            assert isinstance(region, str)


class TestConstantsIntegrity:
    """Test overall integrity and consistency of constants."""

    def test_no_duplicate_enum_values_timezone(self) -> None:
        """Test that timezone enum values are unique."""
        enum_values = list(TIMEZONE_MAP.values())
        assert len(enum_values) == len(set(enum_values))

    def test_no_duplicate_enum_values_country(self) -> None:
        """Test that country enum values are unique."""
        enum_values = list(COUNTRY_MAP.values())
        assert len(enum_values) == len(set(enum_values))

    def test_no_duplicate_enum_values_continent(self) -> None:
        """Test that continent enum values are unique."""
        enum_values = list(CONTINENT_MAP.values())
        assert len(enum_values) == len(set(enum_values))

    def test_no_duplicate_enum_values_region(self) -> None:
        """Test that region enum values are unique."""
        enum_values = list(REGION_MAP.values())
        assert len(enum_values) == len(set(enum_values))

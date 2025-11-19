# Locale API Endpoints

**Discovery Date**: 2025-11-18
**Purpose**: Hierarchical locale data (continents → regions → countries)

---

## Overview

The Luxpower/EG4 API provides locale endpoints that return hierarchical geographic data used for plant configuration. These endpoints are essential for discovering the complete mapping of countries to their continent and region enum values.

## Endpoints

### 1. Get Regions for Continent

**POST** `/WManage/locale/region`

Retrieves all regions for a given continent.

**Request**:
- **Method**: POST
- **Content-Type**: `application/x-www-form-urlencoded; charset=UTF-8`
- **Body**: `continent={CONTINENT_ENUM}`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `continent` | string | Yes | Continent enum value (e.g., "NORTH_AMERICA", "EUROPE", "ASIA") |

**Valid Continent Values**:
- `AFRICA`
- `ASIA`
- `EUROPE`
- `NORTH_AMERICA`
- `OCEANIA`
- `SOUTH_AMERICA`

**Response**:
- **Status**: 200
- **Content-Type**: `text/html;charset=UTF-8` (actually JSON)
- **Body**: Array of region objects

```json
[
  {
    "value": "NORTH_AMERICA",
    "text": "North America"
  },
  {
    "value": "CENTRAL_AMERICA",
    "text": "Central America"
  },
  {
    "value": "CARIBBEAN",
    "text": "Caribbean"
  }
]
```

**Example curl**:
```bash
curl 'https://monitor.eg4electronics.com/WManage/locale/region' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'Cookie: JSESSIONID=...' \
  --data-raw 'continent=NORTH_AMERICA'
```

---

### 2. Get Countries for Region

**POST** `/WManage/locale/country`

Retrieves all countries for a given region.

**Request**:
- **Method**: POST
- **Content-Type**: `application/x-www-form-urlencoded; charset=UTF-8`
- **Body**: `region={REGION_ENUM}`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `region` | string | Yes | Region enum value (e.g., "NORTH_AMERICA", "CARIBBEAN") |

**Response**:
- **Status**: 200
- **Content-Type**: `text/html;charset=UTF-8` (actually JSON)
- **Body**: Array of country objects

```json
[
  {
    "value": "CANADA",
    "text": "Canada"
  },
  {
    "value": "UNITED_STATES_OF_AMERICA",
    "text": "United States of America"
  },
  {
    "value": "MEXICO",
    "text": "Mexico"
  },
  {
    "value": "GREENLAND",
    "text": "Greenland"
  }
]
```

**Example curl**:
```bash
curl 'https://monitor.eg4electronics.com/WManage/locale/country' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'Cookie: JSESSIONID=...' \
  --data-raw 'region=NORTH_AMERICA'
```

---

## Usage in Plant Configuration

These endpoints are used to:

1. **Discover available regions for a continent**
2. **Discover available countries for a region**
3. **Build reverse mapping**: country name → (continent, region)

The POST endpoint `/WManage/web/config/plant/edit` requires:
- `continent` (enum)
- `region` (enum)
- `country` (enum)

But the GET endpoint `/WManage/web/config/plant/list/viewer` only returns:
- `country` (human-readable text)

Therefore, we must use the locale endpoints to derive continent and region from the country name.

---

## Complete Hierarchy

### Coverage

- **6 Continents**
- **23 Regions**
- **226 Countries**

### Continent → Regions Mapping

| Continent | Regions |
|-----------|---------|
| `AFRICA` | `NORTH_AFRICA`, `EAST_AFRICA`, `CENTRAL_AFRICA`, `WEST_AFRICA`, `SOUTH_AFRICA` |
| `ASIA` | `EAST_ASIA`, `SOUTHEAST_ASIA`, `SOUTH_ASIA`, `CENTRAL_ASIA`, `WEST_ASIA` |
| `EUROPE` | `NORDIC_EUROPE`, `EASTERN_EUROPE`, `CENTRAL_EUROPE`, `WESTERN_EUROPE`, `SOUTHERN_EUROPE` |
| `NORTH_AMERICA` | `NORTH_AMERICA`, `CENTRAL_AMERICA`, `CARIBBEAN` |
| `OCEANIA` | `OCEANIA` |
| `SOUTH_AMERICA` | `SA_NORTHERN_PART`, `SA_MIDWEST`, `SA_EAST`, `SA_SOUTHERN_PART` |

---

## Implementation Strategy

### Static Mapping (Fast Path)

For common countries (e.g., USA, Canada, UK, Germany), use static mapping to avoid API calls:

```python
COUNTRY_TO_LOCATION_STATIC = {
    "United States of America": ("NORTH_AMERICA", "NORTH_AMERICA"),
    "Canada": ("NORTH_AMERICA", "NORTH_AMERICA"),
    "United Kingdom": ("EUROPE", "WESTERN_EUROPE"),
    # ... ~35 common countries
}
```

### Dynamic Fetching (Comprehensive)

For unknown countries, query the locale API:

```python
async def fetch_country_location(country_name):
    for continent in ALL_CONTINENTS:
        regions = await get_regions(continent)
        for region in regions:
            countries = await get_countries(region)
            if country_name in [c["text"] for c in countries]:
                return (continent, region)
```

### Hybrid Approach (Recommended)

1. Try static mapping first (O(1) lookup)
2. If not found, fetch from locale API (O(n) search)
3. Cache the result for future use

---

## Notes

- **Content-Type Header**: The API returns `text/html;charset=UTF-8` but the body is valid JSON
- **Authentication**: Requires valid `JSESSIONID` cookie from `/WManage/api/login`
- **Method**: Only POST is supported (GET returns 405)
- **Caching**: Results should be cached as locale data rarely changes
- **Complete Data**: See `research/locale_data_complete.json` for full hierarchy

---

## Related Endpoints

- **Plant Configuration**: `/WManage/web/config/plant/edit` (POST) - requires continent/region enums
- **Plant Details**: `/WManage/web/config/plant/list/viewer` (POST) - returns human-readable country
- **Timezone Mapping**: See `constants.py` for timezone enum conversions

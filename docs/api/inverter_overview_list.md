# Inverter Overview List Endpoint

**Endpoint**: `POST /WManage/api/inverterOverview/list`
**Discovery Date**: 2025-11-18
**Purpose**: Get paginated list of all inverters with real-time metrics

---

## Overview

This endpoint provides a **device-centric view** of all inverters across all plants (or filtered by plant). Unlike `/WManage/api/plantOverview/list/viewer` which provides plant-level aggregated data, this endpoint shows individual inverter metrics.

**Key Features**:
- Per-inverter real-time power metrics
- Battery state (SOC, voltage)
- Energy totals per inverter
- Parallel group information
- Pagination support
- Status filtering

---

## Request

**Method**: POST
**Content-Type**: `application/x-www-form-urlencoded; charset=UTF-8`
**Authentication**: Required (JSESSIONID cookie)

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | int | Yes | Page number (1-indexed) |
| `rows` | int | Yes | Number of rows per page |
| `plantId` | int | Yes | Plant ID (-1 for all plants, or specific plant ID) |
| `searchText` | string | No | Search filter for serial number or device name |
| `statusText` | string | Yes | Status filter ("all", "normal", "fault", etc.) |

### Example Request

```bash
# All inverters across all plants
curl 'https://monitor.eg4electronics.com/WManage/api/inverterOverview/list' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'Cookie: JSESSIONID=...' \
  --data-raw 'page=1&rows=30&plantId=-1&searchText=&statusText=all'

# Inverters for specific plant
curl 'https://monitor.eg4electronics.com/WManage/api/inverterOverview/list' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'Cookie: JSESSIONID=...' \
  --data-raw 'page=1&rows=30&plantId=19147&searchText=&statusText=all'
```

---

## Response

**Status**: 200
**Content-Type**: `application/json`

### Response Structure

```json
{
  "success": true,
  "total": 2,
  "rows": [
    {
      "serialNum": "1234567890",
      "statusText": "normal",
      "deviceType": 6,
      "deviceTypeText": "18KPV",
      "phase": 1,
      "plantId": 19147,
      "plantName": "123 Main St",

      // Real-time Power Metrics
      "ppv": 2609,                    // PV power (W)
      "ppvText": "2 kW",
      "pCharge": 2039,                // Battery charging power (W)
      "pChargeText": "2 kW",
      "pDisCharge": 0,                // Battery discharging power (W)
      "pDisChargeText": "0 W",
      "pConsumption": 0,              // Consumption power (W)
      "pConsumptionText": "0 W",

      // Battery State
      "soc": "82 %",                  // State of charge
      "vBat": 537,                    // Battery voltage (×0.1 V)
      "vBatText": "53.7 V",

      // Energy Totals
      "totalYielding": 14297,         // Lifetime PV production (×0.1 kWh)
      "totalYieldingText": "1429.7 kWh",
      "totalDischarging": 27718,      // Lifetime battery discharge (×0.1 kWh)
      "totalDischargingText": "2771.8 kWh",
      "totalExport": 61276,           // Lifetime grid export (×0.1 kWh)
      "totalExportText": "6127.6 kWh",
      "totalUsage": 36363,            // Lifetime consumption (×0.1 kWh)
      "totalUsageText": "3636.3 kWh",

      // Parallel Configuration
      "parallelGroup": "A",
      "parallelIndex": "2",
      "parallelInfo": "A2, Parallel",
      "parallelModel": "PARALLEL"
    },
    {
      "serialNum": "0987654321",
      "statusText": "normal",
      "deviceType": 9,
      "deviceTypeText": "Grid Boss",
      "phase": 1,
      "plantId": 19147,
      "plantName": "123 Main St",

      // Grid Boss devices have empty metrics
      "ppv": 0,
      "ppvText": "",
      "pCharge": 0,
      "pChargeText": "",
      "pDisCharge": 0,
      "pDisChargeText": "",
      "pConsumption": 0,
      "pConsumptionText": "",
      "soc": "",
      "vBat": 0,
      "vBatText": "",
      "totalYielding": 0,
      "totalYieldingText": "0 kWh",
      "totalDischarging": 0,
      "totalDischargingText": "0 kWh",
      "totalExport": 0,
      "totalExportText": "0 kWh",
      "totalUsage": 0,
      "totalUsageText": "0 kWh",

      // Grid Boss has parallel info but no metrics
      "parallelGroup": "A",
      "parallelIndex": "3",
      "parallelInfo": "A3, Parallel",
      "parallelModel": "PARALLEL"
    }
  ]
}
```

---

## Field Descriptions

### Inverter Identification

| Field | Type | Description |
|-------|------|-------------|
| `serialNum` | string | Inverter serial number (10 digits) |
| `deviceType` | int | Device type code (6=18KPV, 9=Grid Boss, etc.) |
| `deviceTypeText` | string | Human-readable device type |
| `phase` | int | Phase number (1, 2, or 3) |
| `plantId` | int | Parent plant ID |
| `plantName` | string | Parent plant name |
| `statusText` | string | Device status ("normal", "fault", "offline") |

### Real-Time Power Metrics

| Field | Type | Unit | Scaling | Description |
|-------|------|------|---------|-------------|
| `ppv` | int | W | 1:1 | Current PV production power |
| `pCharge` | int | W | 1:1 | Current battery charging power |
| `pDisCharge` | int | W | 1:1 | Current battery discharging power |
| `pConsumption` | int | W | 1:1 | Current consumption |

### Battery State

| Field | Type | Unit | Scaling | Description |
|-------|------|------|---------|-------------|
| `soc` | string | % | - | State of charge percentage (formatted) |
| `vBat` | int | V | ÷10 | Battery voltage |

### Energy Totals

| Field | Type | Unit | Scaling | Description |
|-------|------|------|---------|-------------|
| `totalYielding` | int | kWh | ÷10 | Lifetime PV production |
| `totalDischarging` | int | kWh | ÷10 | Lifetime battery discharge |
| `totalExport` | int | kWh | ÷10 | Lifetime grid export |
| `totalUsage` | int | kWh | ÷10 | Lifetime consumption |

### Parallel Configuration

| Field | Type | Description |
|-------|------|-------------|
| `parallelGroup` | string | Parallel group identifier (A, B, C, etc.) |
| `parallelIndex` | string | Position within parallel group |
| `parallelInfo` | string | Formatted parallel info ("A2, Parallel") |
| `parallelModel` | string | Parallel model ("PARALLEL", "STANDALONE") |

---

## Device Types

Common device type codes:

| Code | Device Type |
|------|-------------|
| 6 | 18KPV |
| 9 | Grid Boss (MID device) |
| 4 | 12KPV |
| 5 | FlexBOSS |
| 7 | XP (other models) |

---

## Pagination

The endpoint supports pagination for large installations:

**Request**:
```json
{
  "page": 2,      // Page 2
  "rows": 30,     // 30 inverters per page
  "plantId": -1,
  "searchText": "",
  "statusText": "all"
}
```

**Response**:
```json
{
  "success": true,
  "total": 75,          // Total inverters across all pages
  "rows": [ /* ... */ ] // 30 inverters for page 2
}
```

**Pagination Calculation**:
- Total pages = `ceil(total / rows)`
- Has next page = `page * rows < total`

---

## Filtering

### By Plant

**All Plants**:
```json
{"plantId": -1}
```

**Specific Plant**:
```json
{"plantId": 19147}
```

### By Status

| Value | Description |
|-------|-------------|
| `"all"` | All inverters |
| `"normal"` | Normal operation |
| `"fault"` | Fault condition |
| `"offline"` | Communication lost |

### By Search Text

Search by serial number or device name:
```json
{"searchText": "4512670"}  // Partial serial number match
```

---

## Use Cases

### 1. Multi-Site Dashboard

```python
async def get_all_inverters_dashboard(client):
    """Get all inverters across all sites."""
    response = await client._request(
        "POST",
        "/WManage/api/inverterOverview/list",
        data={
            "page": 1,
            "rows": 100,
            "plantId": -1,  # All plants
            "searchText": "",
            "statusText": "all"
        }
    )

    for inverter in response["rows"]:
        print(f"{inverter['plantName']} - {inverter['serialNum']}")
        print(f"  Type: {inverter['deviceTypeText']}")
        print(f"  PV: {inverter['ppvText']}")
        print(f"  SOC: {inverter['soc']}")
        print(f"  Status: {inverter['statusText']}")
```

### 2. Fault Detection

```python
async def check_faults(client):
    """Find all inverters with faults."""
    response = await client._request(
        "POST",
        "/WManage/api/inverterOverview/list",
        data={
            "page": 1,
            "rows": 100,
            "plantId": -1,
            "searchText": "",
            "statusText": "fault"  # Only faulted devices
        }
    )

    if response["total"] > 0:
        print(f"⚠️  {response['total']} devices with faults:")
        for inverter in response["rows"]:
            print(f"  - {inverter['serialNum']} at {inverter['plantName']}")
```

### 3. Performance Comparison

```python
async def compare_inverter_performance(client, plant_id):
    """Compare performance of inverters in same plant."""
    response = await client._request(
        "POST",
        "/WManage/api/inverterOverview/list",
        data={
            "page": 1,
            "rows": 30,
            "plantId": plant_id,
            "searchText": "",
            "statusText": "all"
        }
    )

    for inverter in response["rows"]:
        if inverter["deviceType"] != 9:  # Skip Grid Boss
            yield_kwh = inverter["totalYielding"] / 10
            print(f"{inverter['serialNum']}: {yield_kwh:.1f} kWh lifetime")
```

### 4. Parallel Group Analysis

```python
async def analyze_parallel_groups(client, plant_id):
    """Analyze parallel group configuration."""
    response = await client._request(
        "POST",
        "/WManage/api/inverterOverview/list",
        data={
            "page": 1,
            "rows": 30,
            "plantId": plant_id,
            "searchText": "",
            "statusText": "all"
        }
    )

    groups = {}
    for inv in response["rows"]:
        group = inv["parallelGroup"]
        if group not in groups:
            groups[group] = []
        groups[group].append(inv)

    for group_name, inverters in groups.items():
        print(f"\nParallel Group {group_name}:")
        for inv in sorted(inverters, key=lambda x: x["parallelIndex"]):
            print(f"  {inv['parallelInfo']}: {inv['serialNum']}")
```

---

## Comparison with Related Endpoints

| Feature | `/api/inverterOverview/list` | `/api/plantOverview/list/viewer` |
|---------|------------------------------|----------------------------------|
| **Scope** | Per-inverter | Per-plant (aggregated) |
| **Pagination** | ✅ Yes | ❌ No |
| **Filtering** | ✅ Status, search | ❌ Limited (search only) |
| **Plant Filter** | ✅ All or specific | ❌ All only |
| **Battery SOC** | ✅ Per inverter | ❌ Not shown |
| **Parallel Info** | ✅ Detailed | ✅ Summary |
| **Best For** | Device inventory, diagnostics | Plant monitoring |

---

## Notes

- **Empty Metrics**: Grid Boss (deviceType=9) devices return empty/zero power metrics
- **Scaling**: Battery voltage scaled by 10 (537 → 53.7V), energy by 10 (14297 → 1429.7 kWh)
- **Pagination**: Required for large installations (>30 inverters)
- **Status Filter**: Use "fault" to quickly identify problematic devices
- **Cross-Plant**: Use `plantId=-1` to see all inverters across all plants user has access to

---

## Related Documentation

- Plant Overview: `/WManage/api/plantOverview/list/viewer`
- Inverter Runtime: `/WManage/api/inverter/getInverterRuntime`
- Parallel Groups: `/WManage/api/inverterOverview/getParallelGroupDetails`

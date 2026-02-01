"""Extended tests for MIDRuntimePropertiesMixin - Energy properties and edge cases.

This module provides comprehensive coverage for:
- Energy properties (UPS, Grid, Load, AC Couple, Smart Load)
- Aggregate energy properties (_sum_energy helper)
- is_off_grid property with transport runtime
- AC Couple power edge cases (LOCAL mode)
- None handling for all energy fields
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pylxpweb.devices.mid_device import MIDDevice
from pylxpweb.models import MidboxData, MidboxRuntime


@pytest.fixture
def mid_device_with_energy_data() -> MIDDevice:
    """Create MID device with comprehensive energy data."""
    mock_client = MagicMock()

    mid_device = MIDDevice(
        client=mock_client,
        serial_number="4524850115",
        model="GridBOSS",
    )

    # Create runtime data with energy fields populated
    midbox_data = MidboxData.model_construct(
        # Required base fields
        status=1,
        serverTime="2025-11-22 10:30:00",
        deviceTime="2025-11-22 10:30:05",
        gridRmsVolt=2420,
        upsRmsVolt=2400,
        genRmsVolt=0,
        gridL1RmsVolt=1210,
        gridL2RmsVolt=1210,
        upsL1RmsVolt=1200,
        upsL2RmsVolt=1200,
        genL1RmsVolt=0,
        genL2RmsVolt=0,
        gridL1RmsCurr=0,
        gridL2RmsCurr=0,
        loadL1RmsCurr=0,
        loadL2RmsCurr=0,
        genL1RmsCurr=0,
        genL2RmsCurr=0,
        upsL1RmsCurr=0,
        upsL2RmsCurr=0,
        gridL1ActivePower=0,
        gridL2ActivePower=0,
        loadL1ActivePower=0,
        loadL2ActivePower=0,
        genL1ActivePower=0,
        genL2ActivePower=0,
        upsL1ActivePower=0,
        upsL2ActivePower=0,
        hybridPower=0,
        gridFreq=6000,
        smartPort1Status=0,
        smartPort2Status=0,
        smartPort3Status=0,
        smartPort4Status=0,
        # UPS Energy (÷10 for kWh)
        eUpsTodayL1=184,  # 18.4 kWh
        eUpsTodayL2=156,  # 15.6 kWh
        eUpsTotalL1=52400,  # 5240.0 kWh
        eUpsTotalL2=48200,  # 4820.0 kWh
        # Grid Export Energy
        eToGridTodayL1=52,  # 5.2 kWh
        eToGridTodayL2=48,  # 4.8 kWh
        eToGridTotalL1=12000,  # 1200.0 kWh
        eToGridTotalL2=11500,  # 1150.0 kWh
        # Grid Import Energy
        eToUserTodayL1=120,  # 12.0 kWh
        eToUserTodayL2=110,  # 11.0 kWh
        eToUserTotalL1=28000,  # 2800.0 kWh
        eToUserTotalL2=26500,  # 2650.0 kWh
        # Load Energy
        eLoadTodayL1=240,  # 24.0 kWh
        eLoadTodayL2=220,  # 22.0 kWh
        eLoadTotalL1=68000,  # 6800.0 kWh
        eLoadTotalL2=64000,  # 6400.0 kWh
        # AC Couple 1 Energy
        eACcouple1TodayL1=35,  # 3.5 kWh
        eACcouple1TodayL2=32,  # 3.2 kWh
        eACcouple1TotalL1=8500,  # 850.0 kWh
        eACcouple1TotalL2=8200,  # 820.0 kWh
        # AC Couple 2 Energy
        eACcouple2TodayL1=28,  # 2.8 kWh
        eACcouple2TodayL2=25,  # 2.5 kWh
        eACcouple2TotalL1=6800,  # 680.0 kWh
        eACcouple2TotalL2=6500,  # 650.0 kWh
        # AC Couple 3 Energy
        eACcouple3TodayL1=42,  # 4.2 kWh
        eACcouple3TodayL2=38,  # 3.8 kWh
        eACcouple3TotalL1=10200,  # 1020.0 kWh
        eACcouple3TotalL2=9800,  # 980.0 kWh
        # AC Couple 4 Energy
        eACcouple4TodayL1=15,  # 1.5 kWh
        eACcouple4TodayL2=12,  # 1.2 kWh
        eACcouple4TotalL1=3800,  # 380.0 kWh
        eACcouple4TotalL2=3500,  # 350.0 kWh
        # Smart Load 1 Energy
        eSmartLoad1TodayL1=62,  # 6.2 kWh
        eSmartLoad1TodayL2=58,  # 5.8 kWh
        eSmartLoad1TotalL1=15000,  # 1500.0 kWh
        eSmartLoad1TotalL2=14500,  # 1450.0 kWh
        # Smart Load 2 Energy
        eSmartLoad2TodayL1=48,  # 4.8 kWh
        eSmartLoad2TodayL2=44,  # 4.4 kWh
        eSmartLoad2TotalL1=11800,  # 1180.0 kWh
        eSmartLoad2TotalL2=11200,  # 1120.0 kWh
        # Smart Load 3 Energy
        eSmartLoad3TodayL1=75,  # 7.5 kWh
        eSmartLoad3TodayL2=70,  # 7.0 kWh
        eSmartLoad3TotalL1=18200,  # 1820.0 kWh
        eSmartLoad3TotalL2=17500,  # 1750.0 kWh
        # Smart Load 4 Energy
        eSmartLoad4TodayL1=32,  # 3.2 kWh
        eSmartLoad4TodayL2=28,  # 2.8 kWh
        eSmartLoad4TotalL1=7800,  # 780.0 kWh
        eSmartLoad4TotalL2=7200,  # 720.0 kWh
    )

    runtime = MidboxRuntime.model_construct(
        midboxData=midbox_data,
        fwCode="v1.0.0",
    )

    mid_device._runtime = runtime
    return mid_device


@pytest.fixture
def mid_device_without_runtime() -> MIDDevice:
    """Create MID device with no runtime data."""
    mock_client = MagicMock()

    mid_device = MIDDevice(
        client=mock_client,
        serial_number="4524850115",
        model="GridBOSS",
    )
    mid_device._runtime = None
    return mid_device


class TestEnergyPropertiesUPS:
    """Test UPS energy properties."""

    def test_e_ups_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify UPS L1 today energy uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ups_today_l1 == 18.4

    def test_e_ups_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify UPS L2 today energy uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ups_today_l2 == 15.6

    def test_e_ups_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify UPS L1 lifetime energy uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ups_total_l1 == 5240.0

    def test_e_ups_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify UPS L2 lifetime energy uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ups_total_l2 == 4820.0

    def test_e_ups_today_aggregate(self, mid_device_with_energy_data):
        """Verify UPS today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_ups_today == 34.0  # 18.4 + 15.6

    def test_e_ups_total_aggregate(self, mid_device_with_energy_data):
        """Verify UPS lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_ups_total == 10060.0  # 5240.0 + 4820.0

    def test_ups_energy_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify UPS energy returns None when runtime is None."""
        assert mid_device_without_runtime.e_ups_today_l1 is None
        assert mid_device_without_runtime.e_ups_today_l2 is None
        assert mid_device_without_runtime.e_ups_total_l1 is None
        assert mid_device_without_runtime.e_ups_total_l2 is None
        assert mid_device_without_runtime.e_ups_today is None
        assert mid_device_without_runtime.e_ups_total is None


class TestEnergyPropertiesGridExport:
    """Test grid export energy properties."""

    def test_e_to_grid_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify grid export L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_to_grid_today_l1 == 5.2

    def test_e_to_grid_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify grid export L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_to_grid_today_l2 == 4.8

    def test_e_to_grid_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify grid export L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_to_grid_total_l1 == 1200.0

    def test_e_to_grid_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify grid export L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_to_grid_total_l2 == 1150.0

    def test_e_to_grid_today_aggregate(self, mid_device_with_energy_data):
        """Verify grid export today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_to_grid_today == 10.0  # 5.2 + 4.8

    def test_e_to_grid_total_aggregate(self, mid_device_with_energy_data):
        """Verify grid export lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_to_grid_total == 2350.0  # 1200.0 + 1150.0

    def test_grid_export_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify grid export returns None when runtime is None."""
        assert mid_device_without_runtime.e_to_grid_today_l1 is None
        assert mid_device_without_runtime.e_to_grid_today_l2 is None
        assert mid_device_without_runtime.e_to_grid_total_l1 is None
        assert mid_device_without_runtime.e_to_grid_total_l2 is None
        assert mid_device_without_runtime.e_to_grid_today is None
        assert mid_device_without_runtime.e_to_grid_total is None


class TestEnergyPropertiesGridImport:
    """Test grid import energy properties."""

    def test_e_to_user_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify grid import L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_to_user_today_l1 == 12.0

    def test_e_to_user_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify grid import L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_to_user_today_l2 == 11.0

    def test_e_to_user_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify grid import L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_to_user_total_l1 == 2800.0

    def test_e_to_user_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify grid import L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_to_user_total_l2 == 2650.0

    def test_e_to_user_today_aggregate(self, mid_device_with_energy_data):
        """Verify grid import today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_to_user_today == 23.0  # 12.0 + 11.0

    def test_e_to_user_total_aggregate(self, mid_device_with_energy_data):
        """Verify grid import lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_to_user_total == 5450.0  # 2800.0 + 2650.0

    def test_grid_import_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify grid import returns None when runtime is None."""
        assert mid_device_without_runtime.e_to_user_today_l1 is None
        assert mid_device_without_runtime.e_to_user_today_l2 is None
        assert mid_device_without_runtime.e_to_user_total_l1 is None
        assert mid_device_without_runtime.e_to_user_total_l2 is None
        assert mid_device_without_runtime.e_to_user_today is None
        assert mid_device_without_runtime.e_to_user_total is None


class TestEnergyPropertiesLoad:
    """Test load energy properties."""

    def test_e_load_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify load L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_load_today_l1 == 24.0

    def test_e_load_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify load L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_load_today_l2 == 22.0

    def test_e_load_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify load L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_load_total_l1 == 6800.0

    def test_e_load_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify load L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_load_total_l2 == 6400.0

    def test_e_load_today_aggregate(self, mid_device_with_energy_data):
        """Verify load today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_load_today == 46.0  # 24.0 + 22.0

    def test_e_load_total_aggregate(self, mid_device_with_energy_data):
        """Verify load lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_load_total == 13200.0  # 6800.0 + 6400.0

    def test_load_energy_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify load energy returns None when runtime is None."""
        assert mid_device_without_runtime.e_load_today_l1 is None
        assert mid_device_without_runtime.e_load_today_l2 is None
        assert mid_device_without_runtime.e_load_total_l1 is None
        assert mid_device_without_runtime.e_load_total_l2 is None
        assert mid_device_without_runtime.e_load_today is None
        assert mid_device_without_runtime.e_load_total is None


class TestEnergyPropertiesACCouple1:
    """Test AC Couple 1 energy properties."""

    def test_e_ac_couple1_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 1 L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple1_today_l1 == 3.5

    def test_e_ac_couple1_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 1 L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple1_today_l2 == 3.2

    def test_e_ac_couple1_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 1 L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple1_total_l1 == 850.0

    def test_e_ac_couple1_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 1 L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple1_total_l2 == 820.0

    def test_e_ac_couple1_today_aggregate(self, mid_device_with_energy_data):
        """Verify AC Couple 1 today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_ac_couple1_today == 6.7  # 3.5 + 3.2

    def test_e_ac_couple1_total_aggregate(self, mid_device_with_energy_data):
        """Verify AC Couple 1 lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_ac_couple1_total == 1670.0  # 850.0 + 820.0

    def test_ac_couple1_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify AC Couple 1 returns None when runtime is None."""
        assert mid_device_without_runtime.e_ac_couple1_today_l1 is None
        assert mid_device_without_runtime.e_ac_couple1_today_l2 is None
        assert mid_device_without_runtime.e_ac_couple1_total_l1 is None
        assert mid_device_without_runtime.e_ac_couple1_total_l2 is None
        assert mid_device_without_runtime.e_ac_couple1_today is None
        assert mid_device_without_runtime.e_ac_couple1_total is None


class TestEnergyPropertiesACCouple2:
    """Test AC Couple 2 energy properties."""

    def test_e_ac_couple2_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 2 L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple2_today_l1 == 2.8

    def test_e_ac_couple2_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 2 L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple2_today_l2 == 2.5

    def test_e_ac_couple2_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 2 L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple2_total_l1 == 680.0

    def test_e_ac_couple2_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 2 L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple2_total_l2 == 650.0

    def test_e_ac_couple2_today_aggregate(self, mid_device_with_energy_data):
        """Verify AC Couple 2 today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_ac_couple2_today == 5.3  # 2.8 + 2.5

    def test_e_ac_couple2_total_aggregate(self, mid_device_with_energy_data):
        """Verify AC Couple 2 lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_ac_couple2_total == 1330.0  # 680.0 + 650.0

    def test_ac_couple2_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify AC Couple 2 returns None when runtime is None."""
        assert mid_device_without_runtime.e_ac_couple2_today_l1 is None
        assert mid_device_without_runtime.e_ac_couple2_today_l2 is None
        assert mid_device_without_runtime.e_ac_couple2_total_l1 is None
        assert mid_device_without_runtime.e_ac_couple2_total_l2 is None
        assert mid_device_without_runtime.e_ac_couple2_today is None
        assert mid_device_without_runtime.e_ac_couple2_total is None


class TestEnergyPropertiesACCouple3:
    """Test AC Couple 3 energy properties."""

    def test_e_ac_couple3_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 3 L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple3_today_l1 == 4.2

    def test_e_ac_couple3_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 3 L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple3_today_l2 == 3.8

    def test_e_ac_couple3_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 3 L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple3_total_l1 == 1020.0

    def test_e_ac_couple3_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 3 L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple3_total_l2 == 980.0

    def test_e_ac_couple3_today_aggregate(self, mid_device_with_energy_data):
        """Verify AC Couple 3 today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_ac_couple3_today == 8.0  # 4.2 + 3.8

    def test_e_ac_couple3_total_aggregate(self, mid_device_with_energy_data):
        """Verify AC Couple 3 lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_ac_couple3_total == 2000.0  # 1020.0 + 980.0

    def test_ac_couple3_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify AC Couple 3 returns None when runtime is None."""
        assert mid_device_without_runtime.e_ac_couple3_today_l1 is None
        assert mid_device_without_runtime.e_ac_couple3_today_l2 is None
        assert mid_device_without_runtime.e_ac_couple3_total_l1 is None
        assert mid_device_without_runtime.e_ac_couple3_total_l2 is None
        assert mid_device_without_runtime.e_ac_couple3_today is None
        assert mid_device_without_runtime.e_ac_couple3_total is None


class TestEnergyPropertiesACCouple4:
    """Test AC Couple 4 energy properties."""

    def test_e_ac_couple4_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 4 L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple4_today_l1 == 1.5

    def test_e_ac_couple4_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 4 L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple4_today_l2 == 1.2

    def test_e_ac_couple4_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 4 L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple4_total_l1 == 380.0

    def test_e_ac_couple4_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify AC Couple 4 L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_ac_couple4_total_l2 == 350.0

    def test_e_ac_couple4_today_aggregate(self, mid_device_with_energy_data):
        """Verify AC Couple 4 today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_ac_couple4_today == 2.7  # 1.5 + 1.2

    def test_e_ac_couple4_total_aggregate(self, mid_device_with_energy_data):
        """Verify AC Couple 4 lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_ac_couple4_total == 730.0  # 380.0 + 350.0

    def test_ac_couple4_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify AC Couple 4 returns None when runtime is None."""
        assert mid_device_without_runtime.e_ac_couple4_today_l1 is None
        assert mid_device_without_runtime.e_ac_couple4_today_l2 is None
        assert mid_device_without_runtime.e_ac_couple4_total_l1 is None
        assert mid_device_without_runtime.e_ac_couple4_total_l2 is None
        assert mid_device_without_runtime.e_ac_couple4_today is None
        assert mid_device_without_runtime.e_ac_couple4_total is None


class TestEnergyPropertiesSmartLoad1:
    """Test Smart Load 1 energy properties."""

    def test_e_smart_load1_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 1 L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load1_today_l1 == 6.2

    def test_e_smart_load1_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 1 L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load1_today_l2 == 5.8

    def test_e_smart_load1_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 1 L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load1_total_l1 == 1500.0

    def test_e_smart_load1_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 1 L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load1_total_l2 == 1450.0

    def test_e_smart_load1_today_aggregate(self, mid_device_with_energy_data):
        """Verify Smart Load 1 today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_smart_load1_today == 12.0  # 6.2 + 5.8

    def test_e_smart_load1_total_aggregate(self, mid_device_with_energy_data):
        """Verify Smart Load 1 lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_smart_load1_total == 2950.0  # 1500.0 + 1450.0

    def test_smart_load1_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify Smart Load 1 returns None when runtime is None."""
        assert mid_device_without_runtime.e_smart_load1_today_l1 is None
        assert mid_device_without_runtime.e_smart_load1_today_l2 is None
        assert mid_device_without_runtime.e_smart_load1_total_l1 is None
        assert mid_device_without_runtime.e_smart_load1_total_l2 is None
        assert mid_device_without_runtime.e_smart_load1_today is None
        assert mid_device_without_runtime.e_smart_load1_total is None


class TestEnergyPropertiesSmartLoad2:
    """Test Smart Load 2 energy properties."""

    def test_e_smart_load2_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 2 L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load2_today_l1 == 4.8

    def test_e_smart_load2_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 2 L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load2_today_l2 == 4.4

    def test_e_smart_load2_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 2 L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load2_total_l1 == 1180.0

    def test_e_smart_load2_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 2 L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load2_total_l2 == 1120.0

    def test_e_smart_load2_today_aggregate(self, mid_device_with_energy_data):
        """Verify Smart Load 2 today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_smart_load2_today == 9.2  # 4.8 + 4.4

    def test_e_smart_load2_total_aggregate(self, mid_device_with_energy_data):
        """Verify Smart Load 2 lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_smart_load2_total == 2300.0  # 1180.0 + 1120.0

    def test_smart_load2_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify Smart Load 2 returns None when runtime is None."""
        assert mid_device_without_runtime.e_smart_load2_today_l1 is None
        assert mid_device_without_runtime.e_smart_load2_today_l2 is None
        assert mid_device_without_runtime.e_smart_load2_total_l1 is None
        assert mid_device_without_runtime.e_smart_load2_total_l2 is None
        assert mid_device_without_runtime.e_smart_load2_today is None
        assert mid_device_without_runtime.e_smart_load2_total is None


class TestEnergyPropertiesSmartLoad3:
    """Test Smart Load 3 energy properties."""

    def test_e_smart_load3_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 3 L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load3_today_l1 == 7.5

    def test_e_smart_load3_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 3 L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load3_today_l2 == 7.0

    def test_e_smart_load3_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 3 L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load3_total_l1 == 1820.0

    def test_e_smart_load3_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 3 L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load3_total_l2 == 1750.0

    def test_e_smart_load3_today_aggregate(self, mid_device_with_energy_data):
        """Verify Smart Load 3 today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_smart_load3_today == 14.5  # 7.5 + 7.0

    def test_e_smart_load3_total_aggregate(self, mid_device_with_energy_data):
        """Verify Smart Load 3 lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_smart_load3_total == 3570.0  # 1820.0 + 1750.0

    def test_smart_load3_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify Smart Load 3 returns None when runtime is None."""
        assert mid_device_without_runtime.e_smart_load3_today_l1 is None
        assert mid_device_without_runtime.e_smart_load3_today_l2 is None
        assert mid_device_without_runtime.e_smart_load3_total_l1 is None
        assert mid_device_without_runtime.e_smart_load3_total_l2 is None
        assert mid_device_without_runtime.e_smart_load3_today is None
        assert mid_device_without_runtime.e_smart_load3_total is None


class TestEnergyPropertiesSmartLoad4:
    """Test Smart Load 4 energy properties."""

    def test_e_smart_load4_today_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 4 L1 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load4_today_l1 == 3.2

    def test_e_smart_load4_today_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 4 L2 today uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load4_today_l2 == 2.8

    def test_e_smart_load4_total_l1_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 4 L1 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load4_total_l1 == 780.0

    def test_e_smart_load4_total_l2_scaled_correctly(self, mid_device_with_energy_data):
        """Verify Smart Load 4 L2 lifetime uses ÷10 scaling."""
        assert mid_device_with_energy_data.e_smart_load4_total_l2 == 720.0

    def test_e_smart_load4_today_aggregate(self, mid_device_with_energy_data):
        """Verify Smart Load 4 today aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_smart_load4_today == 6.0  # 3.2 + 2.8

    def test_e_smart_load4_total_aggregate(self, mid_device_with_energy_data):
        """Verify Smart Load 4 lifetime aggregate sums L1 + L2."""
        assert mid_device_with_energy_data.e_smart_load4_total == 1500.0  # 780.0 + 720.0

    def test_smart_load4_returns_none_when_runtime_none(self, mid_device_without_runtime):
        """Verify Smart Load 4 returns None when runtime is None."""
        assert mid_device_without_runtime.e_smart_load4_today_l1 is None
        assert mid_device_without_runtime.e_smart_load4_today_l2 is None
        assert mid_device_without_runtime.e_smart_load4_total_l1 is None
        assert mid_device_without_runtime.e_smart_load4_total_l2 is None
        assert mid_device_without_runtime.e_smart_load4_today is None
        assert mid_device_without_runtime.e_smart_load4_total is None


class TestSumEnergyHelper:
    """Test _sum_energy helper method for aggregate calculations."""

    @pytest.fixture
    def mid_device_partial_energy(self) -> MIDDevice:
        """Create MID device with partial energy data (some None values)."""
        mock_client = MagicMock()

        mid_device = MIDDevice(
            client=mock_client,
            serial_number="4524850115",
            model="GridBOSS",
        )

        # Create runtime data with some energy fields None
        midbox_data = MidboxData.model_construct(
            # Required base fields
            status=1,
            serverTime="2025-11-22 10:30:00",
            deviceTime="2025-11-22 10:30:05",
            gridRmsVolt=2420,
            upsRmsVolt=2400,
            genRmsVolt=0,
            gridL1RmsVolt=1210,
            gridL2RmsVolt=1210,
            upsL1RmsVolt=1200,
            upsL2RmsVolt=1200,
            genL1RmsVolt=0,
            genL2RmsVolt=0,
            gridL1RmsCurr=0,
            gridL2RmsCurr=0,
            loadL1RmsCurr=0,
            loadL2RmsCurr=0,
            genL1RmsCurr=0,
            genL2RmsCurr=0,
            upsL1RmsCurr=0,
            upsL2RmsCurr=0,
            gridL1ActivePower=0,
            gridL2ActivePower=0,
            loadL1ActivePower=0,
            loadL2ActivePower=0,
            genL1ActivePower=0,
            genL2ActivePower=0,
            upsL1ActivePower=0,
            upsL2ActivePower=0,
            hybridPower=0,
            gridFreq=6000,
            smartPort1Status=0,
            smartPort2Status=0,
            smartPort3Status=0,
            smartPort4Status=0,
            # Partial energy data - only L1 values populated
            eUpsTodayL1=100,  # 10.0 kWh
            eUpsTodayL2=None,  # Not available
            eToGridTodayL1=None,  # Not available
            eToGridTodayL2=50,  # 5.0 kWh
        )

        runtime = MidboxRuntime.model_construct(
            midboxData=midbox_data,
            fwCode="v1.0.0",
        )

        mid_device._runtime = runtime
        return mid_device

    def test_sum_energy_both_values_present(self, mid_device_partial_energy):
        """Test _sum_energy with L1 present and L2 None treats None as 0."""
        # e_ups_today_l1 = 10.0, e_ups_today_l2 = None
        # Should sum as 10.0 + 0.0 = 10.0
        assert mid_device_partial_energy.e_ups_today == 10.0

    def test_sum_energy_l2_present_l1_none(self, mid_device_partial_energy):
        """Test _sum_energy with L2 present and L1 None treats None as 0."""
        # e_to_grid_today_l1 = None, e_to_grid_today_l2 = 5.0
        # Should sum as 0.0 + 5.0 = 5.0
        assert mid_device_partial_energy.e_to_grid_today == 5.0

    def test_sum_energy_both_none_returns_none(self, mid_device_partial_energy):
        """Test _sum_energy returns None when both L1 and L2 are None."""
        # e_to_user_today_l1 = None, e_to_user_today_l2 = None
        # Should return None (not 0.0)
        assert mid_device_partial_energy.e_to_user_today is None


class TestIsOffGridProperty:
    """Test is_off_grid property with transport runtime."""

    @pytest.fixture
    def mid_device_off_grid(self) -> MIDDevice:
        """Create MID device with isOffGrid=True in transport runtime."""
        mock_client = MagicMock()

        mid_device = MIDDevice(
            client=mock_client,
            serial_number="4524850115",
            model="GridBOSS",
        )

        # Use MagicMock to allow arbitrary attribute access (isOffGrid)
        runtime = MagicMock()
        runtime.isOffGrid = True

        mid_device._runtime = runtime
        return mid_device

    @pytest.fixture
    def mid_device_on_grid(self) -> MIDDevice:
        """Create MID device with isOffGrid=False in transport runtime."""
        mock_client = MagicMock()

        mid_device = MIDDevice(
            client=mock_client,
            serial_number="4524850115",
            model="GridBOSS",
        )

        runtime = MagicMock()
        runtime.isOffGrid = False

        mid_device._runtime = runtime
        return mid_device

    def test_is_off_grid_true_when_transport_runtime_true(self, mid_device_off_grid):
        """Verify is_off_grid returns True when transport runtime has isOffGrid=True."""
        assert mid_device_off_grid.is_off_grid is True

    def test_is_off_grid_false_when_transport_runtime_false(self, mid_device_on_grid):
        """Verify is_off_grid returns False when transport runtime has isOffGrid=False."""
        assert mid_device_on_grid.is_off_grid is False

    def test_is_off_grid_false_when_runtime_none(self, mid_device_without_runtime):
        """Verify is_off_grid returns False when runtime is None."""
        assert mid_device_without_runtime.is_off_grid is False

    def test_is_off_grid_false_when_attribute_missing(self):
        """Verify is_off_grid returns False when isOffGrid attribute doesn't exist."""
        mock_client = MagicMock()

        mid_device = MIDDevice(
            client=mock_client,
            serial_number="4524850115",
            model="GridBOSS",
        )

        midbox_data = MidboxData.model_construct(
            status=1,
            serverTime="2025-11-22 10:30:00",
            deviceTime="2025-11-22 10:30:05",
            gridRmsVolt=2420,
            upsRmsVolt=2400,
            genRmsVolt=0,
            gridL1RmsVolt=1210,
            gridL2RmsVolt=1210,
            upsL1RmsVolt=1200,
            upsL2RmsVolt=1200,
            genL1RmsVolt=0,
            genL2RmsVolt=0,
            gridL1RmsCurr=0,
            gridL2RmsCurr=0,
            loadL1RmsCurr=0,
            loadL2RmsCurr=0,
            genL1RmsCurr=0,
            genL2RmsCurr=0,
            upsL1RmsCurr=0,
            upsL2RmsCurr=0,
            gridL1ActivePower=0,
            gridL2ActivePower=0,
            loadL1ActivePower=0,
            loadL2ActivePower=0,
            genL1ActivePower=0,
            genL2ActivePower=0,
            upsL1ActivePower=0,
            upsL2ActivePower=0,
            hybridPower=0,
            gridFreq=6000,
            smartPort1Status=0,
            smartPort2Status=0,
            smartPort3Status=0,
            smartPort4Status=0,
        )

        runtime = MidboxRuntime.model_construct(
            midboxData=midbox_data,
            fwCode="v1.0.0",
        )
        # Don't add isOffGrid attribute - simulating missing field

        mid_device._runtime = runtime

        # Should gracefully return False with getattr default
        assert mid_device.is_off_grid is False


class TestACCouplePowerLocalMode:
    """Test AC Couple power helper method for LOCAL mode edge cases."""

    @pytest.fixture
    def mid_device_local_mode(self) -> MIDDevice:
        """Create MID device simulating LOCAL mode (Modbus/Dongle).

        In LOCAL mode:
        - Smart Port status registers are not available (default to 0)
        - Smart Load power fields contain AC Couple power data
        - AC Couple power fields are 0 (not populated by API)
        """
        mock_client = MagicMock()

        mid_device = MIDDevice(
            client=mock_client,
            serial_number="4524850115",
            model="GridBOSS",
        )

        midbox_data = MidboxData.model_construct(
            # Required fields
            status=1,
            serverTime="2025-11-22 10:30:00",
            deviceTime="2025-11-22 10:30:05",
            gridRmsVolt=2420,
            upsRmsVolt=2400,
            genRmsVolt=0,
            gridL1RmsVolt=1210,
            gridL2RmsVolt=1210,
            upsL1RmsVolt=1200,
            upsL2RmsVolt=1200,
            genL1RmsVolt=0,
            genL2RmsVolt=0,
            gridL1RmsCurr=0,
            gridL2RmsCurr=0,
            loadL1RmsCurr=0,
            loadL2RmsCurr=0,
            genL1RmsCurr=0,
            genL2RmsCurr=0,
            upsL1RmsCurr=0,
            upsL2RmsCurr=0,
            gridL1ActivePower=0,
            gridL2ActivePower=0,
            loadL1ActivePower=0,
            loadL2ActivePower=0,
            genL1ActivePower=0,
            genL2ActivePower=0,
            upsL1ActivePower=0,
            upsL2ActivePower=0,
            hybridPower=0,
            gridFreq=6000,
            # LOCAL mode: Port status not available (defaults to 0)
            smartPort1Status=0,
            smartPort2Status=0,
            smartPort3Status=0,
            smartPort4Status=0,
            # Smart Load power has non-zero data (AC Couple power in LOCAL mode)
            smartLoad1L1ActivePower=1200,
            smartLoad1L2ActivePower=1300,
            smartLoad2L1ActivePower=0,
            smartLoad2L2ActivePower=0,
            smartLoad3L1ActivePower=850,
            smartLoad3L2ActivePower=900,
            smartLoad4L1ActivePower=0,
            smartLoad4L2ActivePower=0,
            # AC Couple power fields remain 0 (API doesn't populate)
            acCouple1L1ActivePower=0,
            acCouple1L2ActivePower=0,
            acCouple2L1ActivePower=0,
            acCouple2L2ActivePower=0,
            acCouple3L1ActivePower=0,
            acCouple3L2ActivePower=0,
            acCouple4L1ActivePower=0,
            acCouple4L2ActivePower=0,
        )

        runtime = MidboxRuntime.model_construct(
            midboxData=midbox_data,
            fwCode="v1.0.0",
        )

        mid_device._runtime = runtime
        return mid_device

    def test_ac_couple_power_reads_smart_load_when_local_mode_and_nonzero(
        self, mid_device_local_mode
    ):
        """Verify AC Couple reads Smart Load power in LOCAL mode when non-zero."""
        device = mid_device_local_mode

        # Port 1: status=0 (no HTTP API status), Smart Load power non-zero
        # Should read from Smart Load fields
        assert device.ac_couple1_l1_power == 1200
        assert device.ac_couple1_l2_power == 1300
        assert device.ac_couple1_power == 2500  # 1200 + 1300

        # Port 3: status=0, Smart Load power non-zero
        assert device.ac_couple3_l1_power == 850
        assert device.ac_couple3_l2_power == 900
        assert device.ac_couple3_power == 1750  # 850 + 900

    def test_ac_couple_power_returns_zero_when_local_mode_and_zero_smart_load(
        self, mid_device_local_mode
    ):
        """Verify AC Couple returns 0 in LOCAL mode when Smart Load power is 0."""
        device = mid_device_local_mode

        # Port 2: status=0, Smart Load power is 0
        # Should return 0 from acCouple2L*ActivePower fields
        assert device.ac_couple2_l1_power == 0
        assert device.ac_couple2_l2_power == 0
        assert device.ac_couple2_power == 0

        # Port 4: status=0, Smart Load power is 0
        assert device.ac_couple4_l1_power == 0
        assert device.ac_couple4_l2_power == 0
        assert device.ac_couple4_power == 0

    def test_ac_couple_power_helper_returns_zero_when_runtime_none(
        self, mid_device_without_runtime
    ):
        """Verify _get_ac_couple_power returns 0 when runtime is None."""
        # All AC Couple power properties should return 0
        assert mid_device_without_runtime.ac_couple1_l1_power == 0
        assert mid_device_without_runtime.ac_couple1_l2_power == 0
        assert mid_device_without_runtime.ac_couple2_l1_power == 0
        assert mid_device_without_runtime.ac_couple2_l2_power == 0
        assert mid_device_without_runtime.ac_couple3_l1_power == 0
        assert mid_device_without_runtime.ac_couple3_l2_power == 0
        assert mid_device_without_runtime.ac_couple4_l1_power == 0
        assert mid_device_without_runtime.ac_couple4_l2_power == 0


class TestFrequencyPropertiesExtended:
    """Test additional frequency properties not covered in basic tests."""

    def test_phase_lock_frequency_scaled_correctly(self, mid_device_with_energy_data):
        """Verify phase lock frequency uses ÷100 scaling."""
        # Create device with phase lock frequency
        mock_client = MagicMock()
        mid_device = MIDDevice(
            client=mock_client,
            serial_number="4524850115",
            model="GridBOSS",
        )

        midbox_data = MidboxData.model_construct(
            status=1,
            serverTime="2025-11-22 10:30:00",
            deviceTime="2025-11-22 10:30:05",
            gridRmsVolt=2420,
            upsRmsVolt=2400,
            genRmsVolt=0,
            gridL1RmsVolt=1210,
            gridL2RmsVolt=1210,
            upsL1RmsVolt=1200,
            upsL2RmsVolt=1200,
            genL1RmsVolt=0,
            genL2RmsVolt=0,
            gridL1RmsCurr=0,
            gridL2RmsCurr=0,
            loadL1RmsCurr=0,
            loadL2RmsCurr=0,
            genL1RmsCurr=0,
            genL2RmsCurr=0,
            upsL1RmsCurr=0,
            upsL2RmsCurr=0,
            gridL1ActivePower=0,
            gridL2ActivePower=0,
            loadL1ActivePower=0,
            loadL2ActivePower=0,
            genL1ActivePower=0,
            genL2ActivePower=0,
            upsL1ActivePower=0,
            upsL2ActivePower=0,
            hybridPower=0,
            phaseLockFreq=6005,  # Should be 60.05 Hz
            gridFreq=6000,  # 60.00 Hz
            genFreq=5995,  # Should be 59.95 Hz
            smartPort1Status=0,
            smartPort2Status=0,
            smartPort3Status=0,
            smartPort4Status=0,
        )

        runtime = MidboxRuntime.model_construct(
            midboxData=midbox_data,
            fwCode="v1.0.0",
        )

        mid_device._runtime = runtime

        assert mid_device.phase_lock_frequency == 60.05
        assert mid_device.generator_frequency == 59.95

    def test_phase_lock_frequency_returns_default_when_none(self, mid_device_without_runtime):
        """Verify phase lock frequency returns default when runtime is None."""
        assert mid_device_without_runtime.phase_lock_frequency == 0.0

    def test_generator_frequency_returns_default_when_none(self, mid_device_without_runtime):
        """Verify generator frequency returns default when runtime is None."""
        assert mid_device_without_runtime.generator_frequency == 0.0

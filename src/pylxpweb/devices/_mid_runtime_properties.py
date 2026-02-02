"""Runtime properties mixin for MIDDevice (GridBOSS).

This mixin provides properly-scaled property accessors for all GridBOSS
sensor data from the MID device runtime API. All properties return typed,
scaled values with graceful None handling.

Properties are organized by category:
- Voltage Properties (Grid, UPS, Generator - aggregate and per-phase)
- Current Properties (Grid, Load, Generator, UPS - per-phase)
- Power Properties (Grid, Load, Generator, UPS - per-phase and totals)
- Frequency Properties
- Smart Port Status
- System Status & Info
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pylxpweb.constants import scale_mid_current, scale_mid_frequency, scale_mid_voltage

if TYPE_CHECKING:
    from pylxpweb.models import MidboxRuntime


def _safe_sum(*values: int | None) -> int | None:
    """Sum values, returning None if all are None, treating individual Nones as 0."""
    if all(v is None for v in values):
        return None
    return sum(v for v in values if v is not None)


class MIDRuntimePropertiesMixin:
    """Mixin providing runtime property accessors for MID devices."""

    _runtime: MidboxRuntime | None

    # ===========================================
    # Smart Port Power Helper Methods
    # ===========================================

    def _get_ac_couple_power(self, port: int, phase: str) -> int | None:
        """Get AC Couple power for a port, using Smart Load data when in AC Couple mode.

        The EG4 API only provides power data in smartLoad*L*ActivePower fields.
        The acCouple*L*ActivePower fields don't exist in the API response and
        default to 0. When a port is configured for AC Couple mode (status=2),
        we read from the Smart Load fields to get the actual power values.

        For LOCAL mode (Modbus/Dongle), port status registers are not available,
        so status defaults to 0. In this case, we check if Smart Load power is
        non-zero and return it directly, allowing LOCAL mode users to see
        AC Couple power without needing port status.

        Args:
            port: Port number (1-4)
            phase: Phase identifier ("l1" or "l2")

        Returns:
            Power in watts, or None if no data.
        """
        if self._runtime is None:
            return None

        midbox = self._runtime.midboxData

        port_status: int | None = getattr(midbox, f"smartPort{port}Status", None)
        smart_load_power: int | None = getattr(
            midbox, f"smartLoad{port}{phase.upper()}ActivePower", None
        )

        if port_status == 2:
            # AC Couple mode confirmed via HTTP API
            return smart_load_power

        if port_status in (None, 0) and smart_load_power is not None and smart_load_power != 0:
            # LOCAL mode: port status unavailable, but Smart Load has data
            return smart_load_power

        # Not in AC Couple mode - return the AC Couple field
        return getattr(midbox, f"acCouple{port}{phase.upper()}ActivePower", None)

    # ===========================================
    # Voltage Properties - Aggregate
    # ===========================================

    @property
    def grid_voltage(self) -> float | None:
        """Get aggregate grid voltage in volts."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.gridRmsVolt
        return scale_mid_voltage(val) if val is not None else None

    @property
    def ups_voltage(self) -> float | None:
        """Get aggregate UPS voltage in volts."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.upsRmsVolt
        return scale_mid_voltage(val) if val is not None else None

    @property
    def generator_voltage(self) -> float | None:
        """Get aggregate generator voltage in volts."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.genRmsVolt
        return scale_mid_voltage(val) if val is not None else None

    # ===========================================
    # Voltage Properties - Grid Per-Phase
    # ===========================================

    @property
    def grid_l1_voltage(self) -> float | None:
        """Get grid L1 voltage in volts."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.gridL1RmsVolt
        return scale_mid_voltage(val) if val is not None else None

    @property
    def grid_l2_voltage(self) -> float | None:
        """Get grid L2 voltage in volts."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.gridL2RmsVolt
        return scale_mid_voltage(val) if val is not None else None

    # ===========================================
    # Voltage Properties - UPS Per-Phase
    # ===========================================

    @property
    def ups_l1_voltage(self) -> float | None:
        """Get UPS L1 voltage in volts."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.upsL1RmsVolt
        return scale_mid_voltage(val) if val is not None else None

    @property
    def ups_l2_voltage(self) -> float | None:
        """Get UPS L2 voltage in volts."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.upsL2RmsVolt
        return scale_mid_voltage(val) if val is not None else None

    # ===========================================
    # Voltage Properties - Generator Per-Phase
    # ===========================================

    @property
    def generator_l1_voltage(self) -> float | None:
        """Get generator L1 voltage in volts."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.genL1RmsVolt
        return scale_mid_voltage(val) if val is not None else None

    @property
    def generator_l2_voltage(self) -> float | None:
        """Get generator L2 voltage in volts."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.genL2RmsVolt
        return scale_mid_voltage(val) if val is not None else None

    # ===========================================
    # Current Properties - Grid
    # ===========================================

    @property
    def grid_l1_current(self) -> float | None:
        """Get grid L1 current in amps."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.gridL1RmsCurr
        return scale_mid_current(val) if val is not None else None

    @property
    def grid_l2_current(self) -> float | None:
        """Get grid L2 current in amps."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.gridL2RmsCurr
        return scale_mid_current(val) if val is not None else None

    # ===========================================
    # Current Properties - Load
    # ===========================================

    @property
    def load_l1_current(self) -> float | None:
        """Get load L1 current in amps."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.loadL1RmsCurr
        return scale_mid_current(val) if val is not None else None

    @property
    def load_l2_current(self) -> float | None:
        """Get load L2 current in amps."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.loadL2RmsCurr
        return scale_mid_current(val) if val is not None else None

    # ===========================================
    # Current Properties - Generator
    # ===========================================

    @property
    def generator_l1_current(self) -> float | None:
        """Get generator L1 current in amps."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.genL1RmsCurr
        return scale_mid_current(val) if val is not None else None

    @property
    def generator_l2_current(self) -> float | None:
        """Get generator L2 current in amps."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.genL2RmsCurr
        return scale_mid_current(val) if val is not None else None

    # ===========================================
    # Current Properties - UPS
    # ===========================================

    @property
    def ups_l1_current(self) -> float | None:
        """Get UPS L1 current in amps."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.upsL1RmsCurr
        return scale_mid_current(val) if val is not None else None

    @property
    def ups_l2_current(self) -> float | None:
        """Get UPS L2 current in amps."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.upsL2RmsCurr
        return scale_mid_current(val) if val is not None else None

    # ===========================================
    # Power Properties - Grid
    # ===========================================

    @property
    def grid_l1_power(self) -> int | None:
        """Get grid L1 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.gridL1ActivePower

    @property
    def grid_l2_power(self) -> int | None:
        """Get grid L2 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.gridL2ActivePower

    @property
    def grid_power(self) -> int | None:
        """Get total grid power in watts (L1 + L2)."""
        if self._runtime is None:
            return None
        return _safe_sum(
            self._runtime.midboxData.gridL1ActivePower,
            self._runtime.midboxData.gridL2ActivePower,
        )

    # ===========================================
    # Power Properties - Load
    # ===========================================

    @property
    def load_l1_power(self) -> int | None:
        """Get load L1 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.loadL1ActivePower

    @property
    def load_l2_power(self) -> int | None:
        """Get load L2 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.loadL2ActivePower

    @property
    def load_power(self) -> int | None:
        """Get total load power in watts (L1 + L2)."""
        if self._runtime is None:
            return None
        return _safe_sum(
            self._runtime.midboxData.loadL1ActivePower,
            self._runtime.midboxData.loadL2ActivePower,
        )

    # ===========================================
    # Power Properties - Generator
    # ===========================================

    @property
    def generator_l1_power(self) -> int | None:
        """Get generator L1 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.genL1ActivePower

    @property
    def generator_l2_power(self) -> int | None:
        """Get generator L2 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.genL2ActivePower

    @property
    def generator_power(self) -> int | None:
        """Get total generator power in watts (L1 + L2)."""
        if self._runtime is None:
            return None
        return _safe_sum(
            self._runtime.midboxData.genL1ActivePower,
            self._runtime.midboxData.genL2ActivePower,
        )

    # ===========================================
    # Power Properties - UPS
    # ===========================================

    @property
    def ups_l1_power(self) -> int | None:
        """Get UPS L1 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.upsL1ActivePower

    @property
    def ups_l2_power(self) -> int | None:
        """Get UPS L2 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.upsL2ActivePower

    @property
    def ups_power(self) -> int | None:
        """Get total UPS power in watts (L1 + L2)."""
        if self._runtime is None:
            return None
        return _safe_sum(
            self._runtime.midboxData.upsL1ActivePower,
            self._runtime.midboxData.upsL2ActivePower,
        )

    # ===========================================
    # Power Properties - Hybrid System
    # ===========================================

    @property
    def hybrid_power(self) -> int | None:
        """Get hybrid system power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.hybridPower

    # ===========================================
    # Frequency Properties
    # ===========================================

    @property
    def phase_lock_frequency(self) -> float | None:
        """Get PLL (phase-lock loop) frequency in Hz."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.phaseLockFreq
        return scale_mid_frequency(val) if val is not None else None

    @property
    def grid_frequency(self) -> float | None:
        """Get grid frequency in Hz."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.gridFreq
        return scale_mid_frequency(val) if val is not None else None

    @property
    def generator_frequency(self) -> float | None:
        """Get generator frequency in Hz."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.genFreq
        return scale_mid_frequency(val) if val is not None else None

    # ===========================================
    # Smart Port Status
    # ===========================================

    @property
    def smart_port1_status(self) -> int | None:
        """Get smart port 1 status."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartPort1Status

    @property
    def smart_port2_status(self) -> int | None:
        """Get smart port 2 status."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartPort2Status

    @property
    def smart_port3_status(self) -> int | None:
        """Get smart port 3 status."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartPort3Status

    @property
    def smart_port4_status(self) -> int | None:
        """Get smart port 4 status."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartPort4Status

    # ===========================================
    # Power Properties - Smart Load 1
    # ===========================================

    @property
    def smart_load1_l1_power(self) -> int | None:
        """Get Smart Load 1 L1 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartLoad1L1ActivePower

    @property
    def smart_load1_l2_power(self) -> int | None:
        """Get Smart Load 1 L2 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartLoad1L2ActivePower

    @property
    def smart_load1_power(self) -> int | None:
        """Get Smart Load 1 total power in watts (L1 + L2)."""
        if self._runtime is None:
            return None
        return _safe_sum(
            self._runtime.midboxData.smartLoad1L1ActivePower,
            self._runtime.midboxData.smartLoad1L2ActivePower,
        )

    # ===========================================
    # Power Properties - Smart Load 2
    # ===========================================

    @property
    def smart_load2_l1_power(self) -> int | None:
        """Get Smart Load 2 L1 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartLoad2L1ActivePower

    @property
    def smart_load2_l2_power(self) -> int | None:
        """Get Smart Load 2 L2 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartLoad2L2ActivePower

    @property
    def smart_load2_power(self) -> int | None:
        """Get Smart Load 2 total power in watts (L1 + L2)."""
        if self._runtime is None:
            return None
        return _safe_sum(
            self._runtime.midboxData.smartLoad2L1ActivePower,
            self._runtime.midboxData.smartLoad2L2ActivePower,
        )

    # ===========================================
    # Power Properties - Smart Load 3
    # ===========================================

    @property
    def smart_load3_l1_power(self) -> int | None:
        """Get Smart Load 3 L1 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartLoad3L1ActivePower

    @property
    def smart_load3_l2_power(self) -> int | None:
        """Get Smart Load 3 L2 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartLoad3L2ActivePower

    @property
    def smart_load3_power(self) -> int | None:
        """Get Smart Load 3 total power in watts (L1 + L2)."""
        if self._runtime is None:
            return None
        return _safe_sum(
            self._runtime.midboxData.smartLoad3L1ActivePower,
            self._runtime.midboxData.smartLoad3L2ActivePower,
        )

    # ===========================================
    # Power Properties - Smart Load 4
    # ===========================================

    @property
    def smart_load4_l1_power(self) -> int | None:
        """Get Smart Load 4 L1 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartLoad4L1ActivePower

    @property
    def smart_load4_l2_power(self) -> int | None:
        """Get Smart Load 4 L2 active power in watts."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.smartLoad4L2ActivePower

    @property
    def smart_load4_power(self) -> int | None:
        """Get Smart Load 4 total power in watts (L1 + L2)."""
        if self._runtime is None:
            return None
        return _safe_sum(
            self._runtime.midboxData.smartLoad4L1ActivePower,
            self._runtime.midboxData.smartLoad4L2ActivePower,
        )

    # ===========================================
    # Power Properties - AC Couple 1
    # ===========================================

    @property
    def ac_couple1_l1_power(self) -> int | None:
        """Get AC Couple 1 L1 active power in watts."""
        return self._get_ac_couple_power(1, "l1")

    @property
    def ac_couple1_l2_power(self) -> int | None:
        """Get AC Couple 1 L2 active power in watts."""
        return self._get_ac_couple_power(1, "l2")

    @property
    def ac_couple1_power(self) -> int | None:
        """Get AC Couple 1 total power in watts (L1 + L2)."""
        return _safe_sum(
            self._get_ac_couple_power(1, "l1"),
            self._get_ac_couple_power(1, "l2"),
        )

    # ===========================================
    # Power Properties - AC Couple 2
    # ===========================================

    @property
    def ac_couple2_l1_power(self) -> int | None:
        """Get AC Couple 2 L1 active power in watts."""
        return self._get_ac_couple_power(2, "l1")

    @property
    def ac_couple2_l2_power(self) -> int | None:
        """Get AC Couple 2 L2 active power in watts."""
        return self._get_ac_couple_power(2, "l2")

    @property
    def ac_couple2_power(self) -> int | None:
        """Get AC Couple 2 total power in watts (L1 + L2)."""
        return _safe_sum(
            self._get_ac_couple_power(2, "l1"),
            self._get_ac_couple_power(2, "l2"),
        )

    # ===========================================
    # Power Properties - AC Couple 3
    # ===========================================

    @property
    def ac_couple3_l1_power(self) -> int | None:
        """Get AC Couple 3 L1 active power in watts."""
        return self._get_ac_couple_power(3, "l1")

    @property
    def ac_couple3_l2_power(self) -> int | None:
        """Get AC Couple 3 L2 active power in watts."""
        return self._get_ac_couple_power(3, "l2")

    @property
    def ac_couple3_power(self) -> int | None:
        """Get AC Couple 3 total power in watts (L1 + L2)."""
        return _safe_sum(
            self._get_ac_couple_power(3, "l1"),
            self._get_ac_couple_power(3, "l2"),
        )

    # ===========================================
    # Power Properties - AC Couple 4
    # ===========================================

    @property
    def ac_couple4_l1_power(self) -> int | None:
        """Get AC Couple 4 L1 active power in watts."""
        return self._get_ac_couple_power(4, "l1")

    @property
    def ac_couple4_l2_power(self) -> int | None:
        """Get AC Couple 4 L2 active power in watts."""
        return self._get_ac_couple_power(4, "l2")

    @property
    def ac_couple4_power(self) -> int | None:
        """Get AC Couple 4 total power in watts (L1 + L2)."""
        return _safe_sum(
            self._get_ac_couple_power(4, "l1"),
            self._get_ac_couple_power(4, "l2"),
        )

    # ===========================================
    # System Status & Info
    # ===========================================

    @property
    def status(self) -> int | None:
        """Get device status code."""
        if self._runtime is None:
            return None
        return self._runtime.midboxData.status

    @property
    def server_time(self) -> str:
        """Get server timestamp."""
        if self._runtime is None:
            return ""
        return self._runtime.midboxData.serverTime

    @property
    def device_time(self) -> str:
        """Get device timestamp."""
        if self._runtime is None:
            return ""
        return self._runtime.midboxData.deviceTime

    @property
    def firmware_version(self) -> str:
        """Get firmware version."""
        if self._runtime is None:
            return ""
        return self._runtime.fwCode

    @property
    def has_data(self) -> bool:
        """Check if device has runtime data."""
        return self._runtime is not None

    @property
    def is_off_grid(self) -> bool:
        """Check if the system is operating in off-grid/EPS mode."""
        if self._runtime is None:
            return False
        return bool(getattr(self._runtime, "isOffGrid", False))

    # ===========================================
    # Energy Properties - UPS
    # ===========================================

    @property
    def e_ups_today_l1(self) -> float | None:
        """Get UPS L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eUpsTodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_ups_today_l2(self) -> float | None:
        """Get UPS L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eUpsTodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_ups_total_l1(self) -> float | None:
        """Get UPS L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eUpsTotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_ups_total_l2(self) -> float | None:
        """Get UPS L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eUpsTotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - Grid Export
    # ===========================================

    @property
    def e_to_grid_today_l1(self) -> float | None:
        """Get grid export L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eToGridTodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_to_grid_today_l2(self) -> float | None:
        """Get grid export L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eToGridTodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_to_grid_total_l1(self) -> float | None:
        """Get grid export L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eToGridTotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_to_grid_total_l2(self) -> float | None:
        """Get grid export L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eToGridTotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - Grid Import
    # ===========================================

    @property
    def e_to_user_today_l1(self) -> float | None:
        """Get grid import L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eToUserTodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_to_user_today_l2(self) -> float | None:
        """Get grid import L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eToUserTodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_to_user_total_l1(self) -> float | None:
        """Get grid import L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eToUserTotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_to_user_total_l2(self) -> float | None:
        """Get grid import L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eToUserTotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - Load
    # ===========================================

    @property
    def e_load_today_l1(self) -> float | None:
        """Get load L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eLoadTodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_load_today_l2(self) -> float | None:
        """Get load L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eLoadTodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_load_total_l1(self) -> float | None:
        """Get load L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eLoadTotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_load_total_l2(self) -> float | None:
        """Get load L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eLoadTotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - AC Couple 1
    # ===========================================

    @property
    def e_ac_couple1_today_l1(self) -> float | None:
        """Get AC Couple 1 L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple1TodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple1_today_l2(self) -> float | None:
        """Get AC Couple 1 L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple1TodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple1_total_l1(self) -> float | None:
        """Get AC Couple 1 L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple1TotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple1_total_l2(self) -> float | None:
        """Get AC Couple 1 L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple1TotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - AC Couple 2
    # ===========================================

    @property
    def e_ac_couple2_today_l1(self) -> float | None:
        """Get AC Couple 2 L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple2TodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple2_today_l2(self) -> float | None:
        """Get AC Couple 2 L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple2TodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple2_total_l1(self) -> float | None:
        """Get AC Couple 2 L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple2TotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple2_total_l2(self) -> float | None:
        """Get AC Couple 2 L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple2TotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - AC Couple 3
    # ===========================================

    @property
    def e_ac_couple3_today_l1(self) -> float | None:
        """Get AC Couple 3 L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple3TodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple3_today_l2(self) -> float | None:
        """Get AC Couple 3 L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple3TodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple3_total_l1(self) -> float | None:
        """Get AC Couple 3 L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple3TotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple3_total_l2(self) -> float | None:
        """Get AC Couple 3 L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple3TotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - AC Couple 4
    # ===========================================

    @property
    def e_ac_couple4_today_l1(self) -> float | None:
        """Get AC Couple 4 L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple4TodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple4_today_l2(self) -> float | None:
        """Get AC Couple 4 L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple4TodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple4_total_l1(self) -> float | None:
        """Get AC Couple 4 L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple4TotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_ac_couple4_total_l2(self) -> float | None:
        """Get AC Couple 4 L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eACcouple4TotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - Smart Load 1
    # ===========================================

    @property
    def e_smart_load1_today_l1(self) -> float | None:
        """Get Smart Load 1 L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad1TodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load1_today_l2(self) -> float | None:
        """Get Smart Load 1 L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad1TodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load1_total_l1(self) -> float | None:
        """Get Smart Load 1 L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad1TotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load1_total_l2(self) -> float | None:
        """Get Smart Load 1 L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad1TotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - Smart Load 2
    # ===========================================

    @property
    def e_smart_load2_today_l1(self) -> float | None:
        """Get Smart Load 2 L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad2TodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load2_today_l2(self) -> float | None:
        """Get Smart Load 2 L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad2TodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load2_total_l1(self) -> float | None:
        """Get Smart Load 2 L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad2TotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load2_total_l2(self) -> float | None:
        """Get Smart Load 2 L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad2TotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - Smart Load 3
    # ===========================================

    @property
    def e_smart_load3_today_l1(self) -> float | None:
        """Get Smart Load 3 L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad3TodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load3_today_l2(self) -> float | None:
        """Get Smart Load 3 L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad3TodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load3_total_l1(self) -> float | None:
        """Get Smart Load 3 L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad3TotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load3_total_l2(self) -> float | None:
        """Get Smart Load 3 L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad3TotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Energy Properties - Smart Load 4
    # ===========================================

    @property
    def e_smart_load4_today_l1(self) -> float | None:
        """Get Smart Load 4 L1 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad4TodayL1
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load4_today_l2(self) -> float | None:
        """Get Smart Load 4 L2 energy today in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad4TodayL2
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load4_total_l1(self) -> float | None:
        """Get Smart Load 4 L1 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad4TotalL1
        return val / 10.0 if val is not None else None

    @property
    def e_smart_load4_total_l2(self) -> float | None:
        """Get Smart Load 4 L2 lifetime energy in kWh."""
        if self._runtime is None:
            return None
        val = self._runtime.midboxData.eSmartLoad4TotalL2
        return val / 10.0 if val is not None else None

    # ===========================================
    # Aggregate Energy Properties (L1 + L2)
    # ===========================================

    def _sum_energy(self, l1: float | None, l2: float | None) -> float | None:
        """Sum L1 and L2 energy values, returning None if both are None."""
        if l1 is None and l2 is None:
            return None
        return (l1 or 0.0) + (l2 or 0.0)

    # UPS Energy Aggregates

    @property
    def e_ups_today(self) -> float | None:
        """Get total UPS energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_ups_today_l1, self.e_ups_today_l2)

    @property
    def e_ups_total(self) -> float | None:
        """Get total UPS lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_ups_total_l1, self.e_ups_total_l2)

    # Grid Export Energy Aggregates

    @property
    def e_to_grid_today(self) -> float | None:
        """Get total grid export energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_to_grid_today_l1, self.e_to_grid_today_l2)

    @property
    def e_to_grid_total(self) -> float | None:
        """Get total grid export lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_to_grid_total_l1, self.e_to_grid_total_l2)

    # Grid Import Energy Aggregates

    @property
    def e_to_user_today(self) -> float | None:
        """Get total grid import energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_to_user_today_l1, self.e_to_user_today_l2)

    @property
    def e_to_user_total(self) -> float | None:
        """Get total grid import lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_to_user_total_l1, self.e_to_user_total_l2)

    # Load Energy Aggregates

    @property
    def e_load_today(self) -> float | None:
        """Get total load energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_load_today_l1, self.e_load_today_l2)

    @property
    def e_load_total(self) -> float | None:
        """Get total load lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_load_total_l1, self.e_load_total_l2)

    # AC Couple 1 Energy Aggregates

    @property
    def e_ac_couple1_today(self) -> float | None:
        """Get total AC Couple 1 energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_ac_couple1_today_l1, self.e_ac_couple1_today_l2)

    @property
    def e_ac_couple1_total(self) -> float | None:
        """Get total AC Couple 1 lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_ac_couple1_total_l1, self.e_ac_couple1_total_l2)

    # AC Couple 2 Energy Aggregates

    @property
    def e_ac_couple2_today(self) -> float | None:
        """Get total AC Couple 2 energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_ac_couple2_today_l1, self.e_ac_couple2_today_l2)

    @property
    def e_ac_couple2_total(self) -> float | None:
        """Get total AC Couple 2 lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_ac_couple2_total_l1, self.e_ac_couple2_total_l2)

    # AC Couple 3 Energy Aggregates

    @property
    def e_ac_couple3_today(self) -> float | None:
        """Get total AC Couple 3 energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_ac_couple3_today_l1, self.e_ac_couple3_today_l2)

    @property
    def e_ac_couple3_total(self) -> float | None:
        """Get total AC Couple 3 lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_ac_couple3_total_l1, self.e_ac_couple3_total_l2)

    # AC Couple 4 Energy Aggregates

    @property
    def e_ac_couple4_today(self) -> float | None:
        """Get total AC Couple 4 energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_ac_couple4_today_l1, self.e_ac_couple4_today_l2)

    @property
    def e_ac_couple4_total(self) -> float | None:
        """Get total AC Couple 4 lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_ac_couple4_total_l1, self.e_ac_couple4_total_l2)

    # Smart Load 1 Energy Aggregates

    @property
    def e_smart_load1_today(self) -> float | None:
        """Get total Smart Load 1 energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_smart_load1_today_l1, self.e_smart_load1_today_l2)

    @property
    def e_smart_load1_total(self) -> float | None:
        """Get total Smart Load 1 lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_smart_load1_total_l1, self.e_smart_load1_total_l2)

    # Smart Load 2 Energy Aggregates

    @property
    def e_smart_load2_today(self) -> float | None:
        """Get total Smart Load 2 energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_smart_load2_today_l1, self.e_smart_load2_today_l2)

    @property
    def e_smart_load2_total(self) -> float | None:
        """Get total Smart Load 2 lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_smart_load2_total_l1, self.e_smart_load2_total_l2)

    # Smart Load 3 Energy Aggregates

    @property
    def e_smart_load3_today(self) -> float | None:
        """Get total Smart Load 3 energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_smart_load3_today_l1, self.e_smart_load3_today_l2)

    @property
    def e_smart_load3_total(self) -> float | None:
        """Get total Smart Load 3 lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_smart_load3_total_l1, self.e_smart_load3_total_l2)

    # Smart Load 4 Energy Aggregates

    @property
    def e_smart_load4_today(self) -> float | None:
        """Get total Smart Load 4 energy today in kWh (L1 + L2)."""
        return self._sum_energy(self.e_smart_load4_today_l1, self.e_smart_load4_today_l2)

    @property
    def e_smart_load4_total(self) -> float | None:
        """Get total Smart Load 4 lifetime energy in kWh (L1 + L2)."""
        return self._sum_energy(self.e_smart_load4_total_l1, self.e_smart_load4_total_l2)

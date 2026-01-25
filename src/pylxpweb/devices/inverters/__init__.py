"""Inverter implementations for different EG4/Luxpower models."""

from ._features import (
    DEVICE_TYPE_CODE_TO_FAMILY,
    FAMILY_DEFAULT_FEATURES,
    GridType,
    InverterFamily,
    InverterFeatures,
    InverterModelInfo,
    get_family_features,
    get_inverter_family,
)
from .base import (
    FUNC_EN_BIT_AC_CHARGE,
    FUNC_EN_BIT_EPS,
    FUNC_EN_BIT_FORCED_CHARGE,
    FUNC_EN_BIT_FORCED_DISCHARGE,
    FUNC_EN_BIT_PV_PRIORITY,
    FUNC_EN_BIT_STANDBY,
    HOLD_AC_CHARGE_POWER,
    HOLD_AC_CHARGE_SOC_LIMIT,
    HOLD_CHARGE_CURRENT,
    HOLD_DISCHARGE_CURRENT,
    HOLD_DISCHARGE_POWER,
    HOLD_FUNC_EN,
    HOLD_OFF_GRID_SOC_CUTOFF,
    HOLD_ON_GRID_SOC_CUTOFF,
    HOLD_PV_CHARGE_POWER,
    HOLD_SYS_FUNC,
    SYS_FUNC_BIT_GREEN_MODE,
    BaseInverter,
)
from .generic import GenericInverter
from .hybrid import HybridInverter

__all__ = [
    # Inverter classes
    "BaseInverter",
    "GenericInverter",
    "HybridInverter",
    # Feature detection
    "InverterFamily",
    "InverterFeatures",
    "InverterModelInfo",
    "GridType",
    # Feature utilities
    "get_inverter_family",
    "get_family_features",
    "DEVICE_TYPE_CODE_TO_FAMILY",
    "FAMILY_DEFAULT_FEATURES",
    # Register constants for transport control
    "HOLD_FUNC_EN",
    "FUNC_EN_BIT_EPS",
    "FUNC_EN_BIT_AC_CHARGE",
    "FUNC_EN_BIT_STANDBY",
    "FUNC_EN_BIT_FORCED_DISCHARGE",
    "FUNC_EN_BIT_FORCED_CHARGE",
    "FUNC_EN_BIT_PV_PRIORITY",
    "HOLD_SYS_FUNC",
    "SYS_FUNC_BIT_GREEN_MODE",
    "HOLD_AC_CHARGE_POWER",
    "HOLD_AC_CHARGE_SOC_LIMIT",
    "HOLD_ON_GRID_SOC_CUTOFF",
    "HOLD_OFF_GRID_SOC_CUTOFF",
    "HOLD_CHARGE_CURRENT",
    "HOLD_DISCHARGE_CURRENT",
    "HOLD_PV_CHARGE_POWER",
    "HOLD_DISCHARGE_POWER",
]

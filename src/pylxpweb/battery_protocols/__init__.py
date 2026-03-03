"""Battery RS485 protocol definitions.

Each protocol defines register maps as pure data structures.
No I/O code --- decoding only.
"""

from __future__ import annotations

from .base import BatteryProtocol, BatteryRegister, BatteryRegisterBlock

__all__ = [
    "BatteryProtocol",
    "BatteryRegister",
    "BatteryRegisterBlock",
]

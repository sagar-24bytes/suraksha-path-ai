"""
SurakshaPath AI — MicroPython / CPython Compatibility Wrapper.

Provides portable, lightweight abstractions for time, ticks, sleeping, JSON,
randomness, and logging that run identically under both CPython 3.10+ and MicroPython.

MicroPython Design Rules:
  - Zero heavy desktop library dependencies.
  - Low memory footprint and zero dynamic imports.
  - Safe fallback for time.ticks_ms() / time.ticks_diff() under CPython.
"""

from __future__ import annotations

import sys
import time
import json
import random

# Detect runtime environment
IS_MICROPYTHON = (sys.implementation.name == "micropython")


# =============================================================
# MicroPython Ticks & Time Compatibility
# =============================================================

def get_ticks_ms() -> int:
    """Get monotonic time in milliseconds.

    Returns:
        Milliseconds tick count as integer.
    """
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    # CPython fallback
    return int(time.time() * 1000) & 0x3FFFFFFF


def ticks_diff(ticks1: int, ticks2: int) -> int:
    """Calculate time difference (ticks1 - ticks2) handling wrap-around.

    Args:
        ticks1: Newer tick count.
        ticks2: Older tick count.

    Returns:
        Difference in milliseconds.
    """
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(ticks1, ticks2)
    return ticks1 - ticks2


def sleep_ms(ms: int) -> None:
    """Pause execution for specified milliseconds.

    Args:
        ms: Milliseconds to sleep.
    """
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000.0)


# =============================================================
# Lightweight Portable Logging
# =============================================================

def log_info(msg: str) -> None:
    """Log an informational message."""
    print(f"[FW INFO] {msg}")


def log_warn(msg: str) -> None:
    """Log a warning message."""
    print(f"[FW WARN] {msg}")


def log_err(msg: str) -> None:
    """Log an error message."""
    print(f"[FW ERR]  {msg}")

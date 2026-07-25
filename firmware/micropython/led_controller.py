"""
SurakshaPath AI — Logical LED Animation State Machine.

Tracks visual indicator status for local node LED/Neopixel displays.

Supported Logical States:
  - SAFE_SOLID:     Steady green light (Zone is safe).
  - WARN_PULSE:     Pulsing yellow light (Zone advisory/warning).
  - DANGER_FLASH:   Flashing red light (Evacuate zone immediately).
  - BLOCKED_CROSS:  Alternating orange/black pattern (Exit/path impassable).
  - OFFLINE:        Dim white/off (Node offline or unpowered).

Design Rule:
  - Pure logical state machine — zero GPIO or physical driver dependencies.
"""

from __future__ import annotations

from typing import Dict, Any
from communication.packet_schema import (
    LED_STATE_SAFE_SOLID,
    LED_STATE_WARN_PULSE,
    LED_STATE_DANGER_FLASH,
    LED_STATE_BLOCKED_CROSS,
)


class LogicalLEDController:
    """Logical LED animation state machine."""

    def __init__(self) -> None:
        self._current_state: str = LED_STATE_SAFE_SOLID
        self._is_blocked: bool = False

    @property
    def current_state(self) -> str:
        """Get current active logical LED state string."""
        return self._current_state

    def set_blocked(self, is_blocked: bool) -> None:
        """Mark node/exit as blocked."""
        self._is_blocked = is_blocked
        if is_blocked:
            self._current_state = LED_STATE_BLOCKED_CROSS

    def update_from_hazard(self, hazard_score: float, evacuation_state: str, node_health: str = "HEALTHY") -> str:
        """Determine next LED animation pattern based on hazard level and health.

        Args:
            hazard_score: Current fused hazard score (0.0–1.0).
            evacuation_state: "NORMAL", "WARNING", "EVACUATE", "SHELTER".
            node_health: "HEALTHY", "WARNING", "OFFLINE", "FAULT".

        Returns:
            Updated LED state string.
        """
        if node_health in ("OFFLINE", "FAULT") and hazard_score < 0.7:
            # Degraded/failed health defaults to danger flash or warn pulse
            self._current_state = LED_STATE_WARN_PULSE
            return self._current_state

        if self._is_blocked or hazard_score >= 0.85:
            self._current_state = LED_STATE_BLOCKED_CROSS
        elif hazard_score >= 0.60 or evacuation_state == "EVACUATE":
            self._current_state = LED_STATE_DANGER_FLASH
        elif hazard_score >= 0.20 or evacuation_state == "WARNING":
            self._current_state = LED_STATE_WARN_PULSE
        else:
            self._current_state = LED_STATE_SAFE_SOLID

        return self._current_state

    def get_rgb_color_hint(self) -> Tuple[int, int, int]:
        """Return RGB color hint tuple (R, G, B) for visual preview tools."""
        if self._current_state == LED_STATE_SAFE_SOLID:
            return (46, 204, 113)    # Emerald Green
        elif self._current_state == LED_STATE_WARN_PULSE:
            return (241, 196, 15)   # Sunflower Yellow
        elif self._current_state == LED_STATE_DANGER_FLASH:
            return (231, 76, 60)    # Alizarin Red
        elif self._current_state == LED_STATE_BLOCKED_CROSS:
            return (230, 126, 34)   # Carrot Orange
        return (100, 100, 100)      # Gray/Offline

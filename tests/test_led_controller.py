"""
SurakshaPath AI — Logical LED Controller Unit Tests.

Tests:
  - Initial animation state
  - State transitions based on hazard scores and evacuation states
  - Manual block overrides (BLOCKED_CROSS)
  - RGB color preview hints
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import unittest
from firmware.micropython.led_controller import LogicalLEDController
from communication.packet_schema import (
    LED_STATE_SAFE_SOLID,
    LED_STATE_WARN_PULSE,
    LED_STATE_DANGER_FLASH,
    LED_STATE_BLOCKED_CROSS,
)


class TestLogicalLEDController(unittest.TestCase):
    """Unit test suite for LogicalLEDController."""

    def setUp(self) -> None:
        """Initialize LED controller before each test."""
        self.led = LogicalLEDController()

    def test_initial_state(self) -> None:
        """Test initial default state is SAFE_SOLID."""
        self.assertEqual(self.led.current_state, LED_STATE_SAFE_SOLID)
        self.assertEqual(self.led.get_rgb_color_hint(), (46, 204, 113))

    def test_warn_state_transition(self) -> None:
        """Test transition to WARN_PULSE."""
        state = self.led.update_from_hazard(0.35, "WARNING")
        self.assertEqual(state, LED_STATE_WARN_PULSE)

    def test_danger_state_transition(self) -> None:
        """Test transition to DANGER_FLASH."""
        state = self.led.update_from_hazard(0.75, "EVACUATE")
        self.assertEqual(state, LED_STATE_DANGER_FLASH)

    def test_blocked_state_override(self) -> None:
        """Test setting blocked state forces BLOCKED_CROSS pattern."""
        self.led.set_blocked(True)
        self.assertEqual(self.led.current_state, LED_STATE_BLOCKED_CROSS)
        self.assertEqual(self.led.get_rgb_color_hint(), (230, 126, 34))


if __name__ == "__main__":
    unittest.main()

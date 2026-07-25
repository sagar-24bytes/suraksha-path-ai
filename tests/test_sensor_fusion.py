"""
SurakshaPath AI — On-Device Sensor Fusion Unit Tests.

Tests:
  - Input normalization (temperature, smoke, flame)
  - Weighted evidence combination formula
  - Evacuation state mapping (NORMAL, WARNING, EVACUATE)
  - Zero-confidence fail-safe default behavior
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
from firmware.micropython.sensor_fusion import EmbeddedSensorFusion
from communication.packet_schema import (
    EVAC_STATE_NORMAL,
    EVAC_STATE_WARNING,
    EVAC_STATE_EVACUATE,
)


class TestEmbeddedSensorFusion(unittest.TestCase):
    """Unit test suite for EmbeddedSensorFusion."""

    def setUp(self) -> None:
        """Initialize fusion engine before each test."""
        self.fusion = EmbeddedSensorFusion()

    def test_temperature_normalization(self) -> None:
        """Test temperature normalization bounds."""
        self.assertEqual(self.fusion.normalize_temperature(25.0), 0.0)
        self.assertEqual(self.fusion.normalize_temperature(200.0), 1.0)
        self.assertGreater(self.fusion.normalize_temperature(100.0), 0.3)

    def test_safe_baseline_fusion(self) -> None:
        """Test fusion under safe ambient conditions."""
        hazard_score, state = self.fusion.compute_hazard(
            temperature=25.0,
            smoke_level=0.0,
            flame_detected=False,
        )
        self.assertEqual(hazard_score, 0.0)
        self.assertEqual(state, EVAC_STATE_NORMAL)

    def test_high_hazard_fusion(self) -> None:
        """Test fusion under severe fire conditions."""
        hazard_score, state = self.fusion.compute_hazard(
            temperature=180.0,
            smoke_level=0.9,
            flame_detected=True,
        )
        self.assertGreaterEqual(hazard_score, 0.80)
        self.assertEqual(state, EVAC_STATE_EVACUATE)

    def test_failsafe_zero_confidence(self) -> None:
        """Test fail-safe score when all sensor confidence is zero."""
        hazard_score, state = self.fusion.compute_hazard(
            temperature=25.0,
            smoke_level=0.0,
            flame_detected=False,
            temp_confidence=0.0,
            smoke_confidence=0.0,
            flame_confidence=0.0,
        )
        self.assertEqual(hazard_score, 0.70)
        self.assertEqual(state, EVAC_STATE_WARNING)


if __name__ == "__main__":
    unittest.main()

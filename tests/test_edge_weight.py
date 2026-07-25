"""
SurakshaPath AI — Dynamic Edge Weight Engine Unit Tests.

Tests:
  - Baseline edge traversal weight calculation
  - Fire door penalty multiplier
  - Exponential hazard score penalty exp(k * H_v)
  - Explicitly blocked edges returning float("inf")
  - Hazard threshold blockage (hazard >= 0.80)
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
import math
from routing.graph import Edge
from routing.edge_weight import DynamicEdgeWeightCalculator, INFINITY_WEIGHT
from routing.hazard_model import HazardSnapshot, ZoneRisk


class TestDynamicEdgeWeightCalculator(unittest.TestCase):
    """Unit test suite for DynamicEdgeWeightCalculator."""

    def setUp(self) -> None:
        """Initialize calculator before each test."""
        self.calculator = DynamicEdgeWeightCalculator(
            k_hazard_sensitivity=4.0,
            fire_door_multiplier=1.25,
            blocked_threshold=0.80,
        )

    def test_baseline_weight(self) -> None:
        """Test base weight with 0.0 hazard score."""
        edge = Edge("R-101", "C-01", base_weight=5.0, has_fire_door=False)
        weight = self.calculator.calculate_weight(edge, hazard_score=0.0)
        self.assertEqual(weight, 5.0)

    def test_fire_door_penalty(self) -> None:
        """Test fire door multiplier."""
        edge = Edge("R-101", "C-01", base_weight=4.0, has_fire_door=True)
        weight = self.calculator.calculate_weight(edge, hazard_score=0.0)
        self.assertEqual(weight, 5.0)  # 4.0 * 1.25

    def test_exponential_hazard_penalty(self) -> None:
        """Test exponential hazard penalty exp(k * H_v)."""
        edge = Edge("R-101", "C-01", base_weight=10.0)
        # H_v = 0.5 -> exp(4 * 0.5) = exp(2.0) = ~7.389
        weight = self.calculator.calculate_weight(edge, hazard_score=0.5)
        expected = round(10.0 * math.exp(2.0), 4)
        self.assertEqual(weight, expected)

    def test_blocked_threshold(self) -> None:
        """Test edge blockage when hazard exceeds 0.80 threshold."""
        edge = Edge("R-101", "C-01", base_weight=5.0)
        weight = self.calculator.calculate_weight(edge, hazard_score=0.85)
        self.assertEqual(weight, INFINITY_WEIGHT)

    def test_explicit_blocked_edge_in_snapshot(self) -> None:
        """Test explicit blocked edge in HazardSnapshot."""
        edge = Edge("R-101", "C-01", base_weight=5.0)
        snapshot = HazardSnapshot(blocked_edges=[("R-101", "C-01")])
        weight = self.calculator.calculate_weight_with_snapshot(edge, snapshot)
        self.assertEqual(weight, INFINITY_WEIGHT)


if __name__ == "__main__":
    unittest.main()

"""
SurakshaPath AI — Fire Physics Model Unit Tests.

Tests:
  - Initialization of zone fire states
  - Ignition and temperature rise
  - Deterministic fire growth across simulation ticks
  - Extinguishing fire and cooling down
  - Thermal conduction across connected edges
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
from simulation.fire_physics import FirePhysicsModel, ZoneFireState


class TestFirePhysicsModel(unittest.TestCase):
    """Unit test suite for FirePhysicsModel."""

    def setUp(self) -> None:
        """Initialize fire physics model before each test."""
        self.model = FirePhysicsModel(ambient_temp_c=25.0, max_temp_c=800.0)
        self.zones = ["R-101", "R-102", "C-01"]
        self.edges = [("R-101", "C-01"), ("R-102", "C-01")]
        self.model.initialize_zones(self.zones)

    def test_zone_initialization(self) -> None:
        """Verify baseline ambient state for all zones."""
        states = self.model.get_all_states()
        self.assertEqual(len(states), 3)
        for zone_id in self.zones:
            state = states[zone_id]
            self.assertEqual(state.temperature, 25.0)
            self.assertEqual(state.intensity, 0.0)
            self.assertFalse(state.is_ignited)

    def test_ignition(self) -> None:
        """Test igniting a target zone."""
        success = self.model.ignite("R-101", initial_intensity=0.2)
        self.assertTrue(success)
        
        state = self.model.get_state("R-101")
        self.assertIsNotNone(state)
        self.assertTrue(state.is_ignited)
        self.assertEqual(state.intensity, 0.2)
        self.assertGreater(state.temperature, 25.0)

    def test_fire_growth_over_ticks(self) -> None:
        """Test fire intensity and temperature progression over multiple ticks."""
        self.model.ignite("R-101", initial_intensity=0.1)
        initial_temp = self.model.get_state("R-101").temperature

        for _ in range(5):
            self.model.update()

        state = self.model.get_state("R-101")
        self.assertGreater(state.intensity, 0.1)
        self.assertGreater(state.temperature, initial_temp)

    def test_extinguish_and_cooling(self) -> None:
        """Test extinguishing a fire and subsequent cooling towards ambient."""
        self.model.ignite("R-101", initial_intensity=0.5)
        self.model.update()
        high_temp = self.model.get_state("R-101").temperature

        self.model.extinguish("R-101")
        state = self.model.get_state("R-101")
        self.assertFalse(state.is_ignited)
        self.assertEqual(state.intensity, 0.0)

        # Update several ticks to cool down
        for _ in range(10):
            self.model.update()

        cooled_temp = self.model.get_state("R-101").temperature
        self.assertLess(cooled_temp, high_temp)

    def test_thermal_conduction_across_edges(self) -> None:
        """Test heat flow between connected adjacent zones."""
        self.model.ignite("R-101", initial_intensity=0.8)
        
        # Advance physics with connected edges
        for _ in range(5):
            self.model.update(adjacency_edges=self.edges)

        c01_temp = self.model.get_state("C-01").temperature
        self.assertGreater(c01_temp, 25.0)


if __name__ == "__main__":
    unittest.main()

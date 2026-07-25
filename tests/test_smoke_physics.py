"""
SurakshaPath AI — Smoke Physics Model Unit Tests.

Tests:
  - Smoke generation in burning zones
  - Inter-room smoke diffusion across connected edges
  - Smoke dissipation when fire subsides
  - Manual smoke level overrides
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
from simulation.fire_physics import ZoneFireState
from simulation.smoke_physics import SmokePhysicsModel


class TestSmokePhysicsModel(unittest.TestCase):
    """Unit test suite for SmokePhysicsModel."""

    def setUp(self) -> None:
        """Initialize smoke physics model before each test."""
        self.model = SmokePhysicsModel(base_diffusion_rate=0.2, smoke_generation_coeff=0.3)
        self.zones = ["R-101", "C-01", "R-102"]
        self.edges = [("R-101", "C-01"), ("C-01", "R-102")]
        self.model.initialize_zones(self.zones)

    def test_initial_smoke_level(self) -> None:
        """Verify baseline smoke level is 0.0 for all zones."""
        for z in self.zones:
            self.assertEqual(self.model.get_smoke_level(z), 0.0)

    def test_smoke_generation(self) -> None:
        """Test smoke generation in a burning zone."""
        fire_states = {
            "R-101": ZoneFireState(zone_id="R-101", intensity=0.5, is_ignited=True),
            "C-01": ZoneFireState(zone_id="C-01", intensity=0.0, is_ignited=False),
            "R-102": ZoneFireState(zone_id="R-102", intensity=0.0, is_ignited=False),
        }

        self.model.update(fire_states=fire_states)
        self.assertGreater(self.model.get_smoke_level("R-101"), 0.0)

    def test_smoke_diffusion(self) -> None:
        """Test smoke diffusing from R-101 into corridor C-01."""
        fire_states = {
            "R-101": ZoneFireState(zone_id="R-101", intensity=0.8, is_ignited=True),
            "C-01": ZoneFireState(zone_id="C-01", intensity=0.0, is_ignited=False),
            "R-102": ZoneFireState(zone_id="R-102", intensity=0.0, is_ignited=False),
        }

        for _ in range(3):
            self.model.update(fire_states=fire_states, adjacency_edges=self.edges)

        self.assertGreater(self.model.get_smoke_level("C-01"), 0.0)

    def test_smoke_dissipation(self) -> None:
        """Test smoke clearing when no fire is present."""
        self.model.set_smoke_level("R-101", 0.5)
        self.assertEqual(self.model.get_smoke_level("R-101"), 0.5)

        safe_fire_states = {
            z: ZoneFireState(zone_id=z, intensity=0.0, is_ignited=False)
            for z in self.zones
        }

        for _ in range(10):
            self.model.update(fire_states=safe_fire_states)

        self.assertLess(self.model.get_smoke_level("R-101"), 0.5)


if __name__ == "__main__":
    unittest.main()

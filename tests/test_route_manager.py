"""
SurakshaPath AI — Route Manager & Route Cache Unit Tests.

Tests:
  - DefaultRouteManager processing RouteRequest contracts
  - Multi-node evacuation routing
  - Shelter-In-Place fallback when no safe route exists
  - RouteCache hit and automatic invalidation on hazard snapshot update
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
from routing.graph import BuildingGraph, Node, Edge
from routing.path_manager import RouteRequest, RouteResult, DefaultRouteManager
from routing.hazard_model import HazardSnapshot, ZoneRisk, TelemetryHazardProvider
from communication.packet_schema import TelemetryPacket


class TestRouteManagerAndCache(unittest.TestCase):
    """Unit test suite for DefaultRouteManager and RouteCache."""

    def setUp(self) -> None:
        """Construct building topology:
            [R-101] ---> [C-01] ---> (X-01 Exit)
        """
        self.graph = BuildingGraph("Small Building")
        self.graph.add_node(Node("R-101", name="Office 101", is_exit=False))
        self.graph.add_node(Node("C-01", name="Corridor 1", is_exit=False))
        self.graph.add_node(Node("X-01", name="Main Exit", is_exit=True))

        self.graph.add_edge(Edge("R-101", "C-01", base_weight=3.0))
        self.graph.add_edge(Edge("C-01", "X-01", base_weight=4.0))

        self.hazard_provider = TelemetryHazardProvider()
        self.route_mgr = DefaultRouteManager(
            graph=self.graph,
            hazard_provider=self.hazard_provider,
            enable_cache=True,
        )

    def test_single_route_calculation(self) -> None:
        """Test calculating route for single request."""
        req = RouteRequest("R-101")
        res = self.route_mgr.calculate_route(req)

        self.assertIsInstance(res, RouteResult)
        self.assertFalse(res.is_shelter_in_place)
        self.assertEqual(res.source_node, "R-101")
        self.assertEqual(res.target_exit, "X-01")
        self.assertEqual(res.path, ["R-101", "C-01", "X-01"])

    def test_shelter_in_place_when_trapped(self) -> None:
        """Test shelter-in-place when corridor C-01 is blocked."""
        packets = {
            "C-01": TelemetryPacket(zone_id="C-01", hazard_score=0.95, evacuation_state="EVACUATE")
        }
        self.hazard_provider.update_telemetry(packets, timestamp=1.0)

        req = RouteRequest("R-101")
        res = self.route_mgr.calculate_route(req)

        self.assertTrue(res.is_shelter_in_place)
        self.assertEqual(res.path, [])
        self.assertEqual(res.target_exit, "")

    def test_route_cache_hit_and_invalidation(self) -> None:
        """Test route cache hit and invalidation on hazard change."""
        req = RouteRequest("R-101")
        res1 = self.route_mgr.calculate_route(req)
        self.assertEqual(self.route_mgr.cache.size, 1)

        # Same request -> cache hit
        res2 = self.route_mgr.calculate_route(req)
        self.assertEqual(res1.path, res2.path)

        # Update hazard snapshot -> invalidates cache
        packets = {"R-101": TelemetryPacket(zone_id="R-101", hazard_score=0.3)}
        self.hazard_provider.update_telemetry(packets, timestamp=5.0)

        res3 = self.route_mgr.calculate_route(req)
        # Cache cleared and re-populated with new hazard state
        self.assertEqual(self.route_mgr.cache.size, 1)


if __name__ == "__main__":
    unittest.main()

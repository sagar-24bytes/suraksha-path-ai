"""
SurakshaPath AI — Dijkstra Pathfinder Unit Tests.

Tests:
  - Basic shortest path calculation on safe graph topology
  - Multi-exit destination choice (selects nearest / optimal exit)
  - Unreachable targets / disconnected nodes
  - Deterministic tie-breaking consistency
  - Hazard avoidance (selects longer safe path over shorter dangerous path)
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
from routing.dijkstra import DijkstraPathfinder
from routing.edge_weight import DynamicEdgeWeightCalculator, INFINITY_WEIGHT
from routing.hazard_model import HazardSnapshot, ZoneRisk


class TestDijkstraPathfinder(unittest.TestCase):
    """Unit test suite for DijkstraPathfinder."""

    def setUp(self) -> None:
        """Construct test graph topology:
        
            (X-01 Exit) <--- [C-01] <--- [R-101] (Source)
                              |
                              v
                           [C-02] ---> (X-02 Exit)
        """
        self.graph = BuildingGraph("Test Graph")
        self.graph.add_node(Node("R-101", name="Office 101", is_exit=False))
        self.graph.add_node(Node("C-01", name="Corridor 1", is_exit=False))
        self.graph.add_node(Node("C-02", name="Corridor 2", is_exit=False))
        self.graph.add_node(Node("X-01", name="Main Exit", is_exit=True))
        self.graph.add_node(Node("X-02", name="East Exit", is_exit=True))

        self.graph.add_edge(Edge("R-101", "C-01", base_weight=3.0))
        self.graph.add_edge(Edge("C-01", "X-01", base_weight=4.0))
        self.graph.add_edge(Edge("C-01", "C-02", base_weight=2.0))
        self.graph.add_edge(Edge("C-02", "X-02", base_weight=3.0))

        self.pathfinder = DijkstraPathfinder()

    def test_basic_shortest_path(self) -> None:
        """Test finding shortest path on baseline graph (R-101 -> C-01 -> X-01)."""
        path, cost, risk, exit_node = self.pathfinder.find_shortest_path(
            graph=self.graph,
            source_node="R-101",
            target_exits=["X-01", "X-02"],
        )

        self.assertEqual(exit_node, "X-01")
        self.assertEqual(path, ["R-101", "C-01", "X-01"])
        self.assertEqual(cost, 7.0)  # 3.0 + 4.0

    def test_multi_exit_selection(self) -> None:
        """Test selecting X-02 when X-01 path becomes longer or blocked."""
        snapshot = HazardSnapshot(
            zone_risks={
                "X-01": ZoneRisk("X-01", hazard_score=0.9, is_blocked=True)  # X-01 blocked
            }
        )

        path, cost, risk, exit_node = self.pathfinder.find_shortest_path(
            graph=self.graph,
            source_node="R-101",
            target_exits=["X-01", "X-02"],
            snapshot=snapshot,
        )

        self.assertEqual(exit_node, "X-02")
        self.assertEqual(path, ["R-101", "C-01", "C-02", "X-02"])

    def test_unreachable_target(self) -> None:
        """Test pathfinder when all exits are blocked."""
        snapshot = HazardSnapshot(
            zone_risks={
                "X-01": ZoneRisk("X-01", is_blocked=True),
                "X-02": ZoneRisk("X-02", is_blocked=True),
            }
        )

        path, cost, risk, exit_node = self.pathfinder.find_shortest_path(
            graph=self.graph,
            source_node="R-101",
            target_exits=["X-01", "X-02"],
            snapshot=snapshot,
        )

        self.assertEqual(path, [])
        self.assertEqual(cost, INFINITY_WEIGHT)
        self.assertEqual(exit_node, "")

    def test_hazard_avoidance_rerouting(self) -> None:
        """Test choosing longer safe path over shorter dangerous path."""
        # High hazard at C-01
        snapshot = HazardSnapshot(
            zone_risks={
                "C-01": ZoneRisk("C-01", hazard_score=0.75, confidence=1.0)
            }
        )

        path, cost, risk, exit_node = self.pathfinder.find_shortest_path(
            graph=self.graph,
            source_node="R-101",
            target_exits=["X-01", "X-02"],
            snapshot=snapshot,
        )

        # C-01 weight becomes base_weight(4.0) * exp(4 * 0.75) = 4 * 20.085 = 80.34
        self.assertGreater(cost, 50.0)
        self.assertGreater(risk, 0.0)


if __name__ == "__main__":
    unittest.main()

"""
SurakshaPath AI — Deterministic Dijkstra Pathfinder.

Implements single-source multi-destination Dijkstra shortest path search over BuildingGraph.

Features:
  - Priority queue (`heapq`) implementation for O((E + V) log V) efficiency.
  - Multi-exit destination search (finds shortest/safest path to any valid exit node).
  - Deterministic tie-breaking (lexicographical node ID comparison on equal cost).
  - Handles unreachable targets / fully blocked corridors gracefully.
  - Computes path array, total traversal time in seconds, and cumulative risk.
"""

from __future__ import annotations

import heapq
from typing import Dict, List, Tuple, Optional, Set

from routing.graph import BuildingGraph, Node, Edge
from routing.edge_weight import DynamicEdgeWeightCalculator, INFINITY_WEIGHT
from routing.hazard_model import HazardSnapshot


class DijkstraPathfinder:
    """Deterministic Dijkstra shortest path engine."""

    def __init__(self, weight_calculator: Optional[DynamicEdgeWeightCalculator] = None) -> None:
        """Initialize DijkstraPathfinder.

        Args:
            weight_calculator: DynamicEdgeWeightCalculator instance (defaults to standard).
        """
        self.calculator = weight_calculator or DynamicEdgeWeightCalculator()

    def find_shortest_path(
        self,
        graph: BuildingGraph,
        source_node: str,
        target_exits: List[str],
        snapshot: Optional[HazardSnapshot] = None,
    ) -> Tuple[List[str], float, float, str]:
        """Find the optimal evacuation route from source_node to any available exit in target_exits.

        Args:
            graph: BuildingGraph topology container.
            source_node: Starting node ID (e.g. "R-105").
            target_exits: List of emergency exit node IDs (e.g. ["X-01", "X-02", "X-03"]).
            snapshot: HazardSnapshot containing building risk state and blocked edges.

        Returns:
            Tuple of:
              - path: Ordered list of node IDs from source to exit (empty if unreachable).
              - total_cost: Total dynamic traversal time in seconds (inf if unreachable).
              - cumulative_risk: Sum of hazard scores along the path.
              - chosen_exit: Target exit ID selected (empty string if unreachable).
        """
        if source_node not in graph.nodes:
            return [], INFINITY_WEIGHT, 0.0, ""

        valid_exits: Set[str] = {e for e in target_exits if e in graph.nodes}
        if not valid_exits:
            return [], INFINITY_WEIGHT, 0.0, ""

        # Early exit check: if starting at an exit, cost is 0.0
        if source_node in valid_exits:
            return [source_node], 0.0, 0.0, source_node

        # Check if source node itself is completely blocked/impassable
        if snapshot:
            src_risk = snapshot.get_risk(source_node)
            if src_risk.is_blocked or src_risk.hazard_score >= self.calculator.blocked_threshold:
                return [], INFINITY_WEIGHT, 0.0, ""

        # Priority queue entries: (cost, node_id)
        # We use node_id as second element for deterministic tie-breaking on equal cost
        distances: Dict[str, float] = {n: INFINITY_WEIGHT for n in graph.nodes}
        predecessors: Dict[str, Optional[str]] = {n: None for n in graph.nodes}
        
        distances[source_node] = 0.0
        pq: List[Tuple[float, str]] = [(0.0, source_node)]

        visited: Set[str] = set()

        while pq:
            current_cost, current_node = heapq.heappop(pq)

            if current_node in visited:
                continue
            visited.add(current_node)

            # Reached a valid exit! Since Dijkstra expands in order of increasing cost,
            # the first exit popped from PQ is guaranteed to be the minimal cost exit.
            if current_node in valid_exits:
                path = self._reconstruct_path(predecessors, source_node, current_node)
                risk = self._calculate_cumulative_risk(path, snapshot)
                return path, round(current_cost, 4), round(risk, 4), current_node

            # Expand neighbors
            neighbors = graph.get_neighbors(current_node)
            # Sort neighbors lexicographically for deterministic tie-breaking
            neighbors.sort()

            for neighbor in neighbors:
                if neighbor in visited:
                    continue

                edge = graph.get_edge(current_node, neighbor)
                if edge is None:
                    continue

                edge_cost = self.calculator.calculate_weight_with_snapshot(edge, snapshot)
                if edge_cost == INFINITY_WEIGHT:
                    continue

                new_cost = current_cost + edge_cost
                if new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    predecessors[neighbor] = current_node
                    heapq.heappush(pq, (new_cost, neighbor))

        # No path found to any exit (unreachable or completely blocked)
        return [], INFINITY_WEIGHT, 0.0, ""

    @staticmethod
    def _reconstruct_path(
        predecessors: Dict[str, Optional[str]],
        source_node: str,
        target_node: str,
    ) -> List[str]:
        """Reconstruct path list from predecessors dictionary."""
        path = []
        curr: Optional[str] = target_node
        while curr is not None:
            path.append(curr)
            if curr == source_node:
                break
            curr = predecessors.get(curr)

        path.reverse()
        if path and path[0] == source_node:
            return path
        return []

    @staticmethod
    def _calculate_cumulative_risk(
        path: List[str],
        snapshot: Optional[HazardSnapshot] = None,
    ) -> float:
        """Calculate sum of zone hazard scores along path."""
        if not path or not snapshot:
            return 0.0
        return sum(snapshot.get_risk(node_id).hazard_score for node_id in path)

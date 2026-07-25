"""
SurakshaPath AI — Shared Routing Graph Topology Data Structures.

Defines structural graph representation (Node, Edge, BuildingGraph) used across
Simulation, MicroPython Firmware, Routing, and the Fire Commander Dashboard.

Design Principles:
  - Structural graph data structures only.
  - Zero pathfinding or routing algorithm implementation.
  - Simple, memory-efficient Python classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set


@dataclass
class Node:
    """Structural node representation in the building graph topology.

    Attributes:
        id:          Unique node identifier (e.g., "R-105", "X-01").
        name:        Human-readable node name (e.g., "Kitchen", "Main Entrance").
        floor:       Floor number (e.g., 1, 2).
        x:           X-coordinate on floor plan (0.0–15.0).
        y:           Y-coordinate on floor plan (0.0–10.0).
        is_exit:     True if this node is an emergency exit point.
        capacity:    Maximum occupant capacity of the zone.
    """
    id: str
    name: str = ""
    floor: int = 1
    x: float = 0.0
    y: float = 0.0
    is_exit: bool = False
    capacity: int = 0


@dataclass
class Edge:
    """Physical walkable connection between two nodes in the building.

    Attributes:
        from_node:     Source node ID.
        to_node:       Target node ID.
        distance_m:    Physical traversal distance in meters.
        base_weight:   Normal traversal time in seconds under safe baseline conditions.
        has_fire_door: True if connection is separated by a fire-rated door.
    """
    from_node: str
    to_node: str
    distance_m: float = 5.0
    base_weight: float = 5.0
    has_fire_door: bool = False


class BuildingGraph:
    """Structural graph container representing the building topology."""

    def __init__(self, name: str = "Building Graph") -> None:
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[Tuple[str, str], Edge] = {}
        self.adjacency: Dict[str, Set[str]] = {}

    def add_node(self, node: Node) -> None:
        """Add a structural node to the building graph."""
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = set()

    def add_edge(self, edge: Edge, bidirectional: bool = True) -> None:
        """Add a physical edge to the graph.

        Args:
            edge: Edge instance to add.
            bidirectional: If True, adds both (from_node -> to_node) and (to_node -> from_node).
        """
        if edge.from_node not in self.nodes or edge.to_node not in self.nodes:
            raise ValueError(f"Cannot add edge between unknown nodes: {edge.from_node} -> {edge.to_node}")

        self.edges[(edge.from_node, edge.to_node)] = edge
        self.adjacency[edge.from_node].add(edge.to_node)

        if bidirectional:
            rev_edge = Edge(
                from_node=edge.to_node,
                to_node=edge.from_node,
                distance_m=edge.distance_m,
                base_weight=edge.base_weight,
                has_fire_door=edge.has_fire_door,
            )
            self.edges[(edge.to_node, edge.from_node)] = rev_edge
            self.adjacency[edge.to_node].add(edge.from_node)

    def get_node(self, node_id: str) -> Optional[Node]:
        """Look up a node by ID. Returns None if not found."""
        return self.nodes.get(node_id)

    def get_exit_nodes(self) -> List[Node]:
        """Return list of all exit nodes in the building graph."""
        return [n for n in self.nodes.values() if n.is_exit]

    def get_neighbors(self, node_id: str) -> List[str]:
        """Return list of neighbor node IDs connected to node_id."""
        return list(self.adjacency.get(node_id, set()))

    def get_edge(self, from_node: str, to_node: str) -> Optional[Edge]:
        """Look up an edge between two nodes. Returns None if not found."""
        return self.edges.get((from_node, to_node))

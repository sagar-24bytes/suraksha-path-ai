"""
SurakshaPath AI — Shared Evacuation Routing Subsystem Package.

Provides structural topology graphs, dynamic edge weight calculation, hazard model snapshot
contracts, Dijkstra shortest-path pathfinder, self-invalidating route cache, and high-level
route manager orchestrator.

Exports:
  - Node, Edge, BuildingGraph: Structural graph topology data structures
  - BaseWeightProvider, EdgeWeightCalculator, DynamicEdgeWeightCalculator, INFINITY_WEIGHT
  - ZoneRisk, HazardSnapshot, HazardProvider, TelemetryHazardProvider
  - RouteRequest, RouteResult, RouteManager, DefaultRouteManager
  - DijkstraPathfinder: Deterministic Dijkstra shortest path engine
  - RouteCache: Self-invalidating route cache
"""

from routing.graph import Node, Edge, BuildingGraph
from routing.edge_weight import BaseWeightProvider, EdgeWeightCalculator, DynamicEdgeWeightCalculator, INFINITY_WEIGHT
from routing.hazard_model import ZoneRisk, HazardSnapshot, HazardProvider, TelemetryHazardProvider
from routing.path_manager import RouteRequest, RouteResult, RouteManager, DefaultRouteManager
from routing.dijkstra import DijkstraPathfinder
from routing.route_cache import RouteCache

__all__ = [
    "Node",
    "Edge",
    "BuildingGraph",
    "BaseWeightProvider",
    "EdgeWeightCalculator",
    "DynamicEdgeWeightCalculator",
    "INFINITY_WEIGHT",
    "ZoneRisk",
    "HazardSnapshot",
    "HazardProvider",
    "TelemetryHazardProvider",
    "RouteRequest",
    "RouteResult",
    "RouteManager",
    "DefaultRouteManager",
    "DijkstraPathfinder",
    "RouteCache",
]

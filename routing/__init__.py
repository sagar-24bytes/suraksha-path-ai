"""
SurakshaPath AI — Shared Evacuation Routing Subsystem Package.

Provides structural topology graphs, dynamic edge weight interfaces, hazard model snapshot
contracts, and high-level route manager abstractions.

Exports:
  - Node, Edge, BuildingGraph: Structural graph topology data structures
  - BaseWeightProvider, EdgeWeightCalculator: Edge weight interface contracts
  - ZoneRisk, HazardSnapshot, HazardProvider: Hazard model contracts & provider interface
  - RouteRequest, RouteResult, RouteManager: Evacuation routing interface contracts
"""

from routing.graph import Node, Edge, BuildingGraph
from routing.edge_weight import BaseWeightProvider, EdgeWeightCalculator
from routing.hazard_model import ZoneRisk, HazardSnapshot, HazardProvider
from routing.path_manager import RouteRequest, RouteResult, RouteManager

__all__ = [
    "Node",
    "Edge",
    "BuildingGraph",
    "BaseWeightProvider",
    "EdgeWeightCalculator",
    "ZoneRisk",
    "HazardSnapshot",
    "HazardProvider",
    "RouteRequest",
    "RouteResult",
    "RouteManager",
]

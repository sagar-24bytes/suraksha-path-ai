"""
SurakshaPath AI — Shared Route Manager Implementation.

Implements RouteRequest, RouteResult, RouteManager ABC, and DefaultRouteManager which
orchestrates evacuation path requests by querying BuildingGraph, HazardSnapshot,
RouteCache, and DijkstraPathfinder.

Responsibilities:
  - Process RouteRequest contracts.
  - Query current HazardSnapshot via HazardProvider.
  - Consult RouteCache to bypass redundant path searches.
  - Run DijkstraPathfinder to compute optimal hazard-aware route.
  - Return RouteResult contract (path, total_cost, target_exit, shelter_in_place status).
  - Single authority for routing logic in the entire system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from routing.graph import BuildingGraph, Node
from routing.edge_weight import DynamicEdgeWeightCalculator, INFINITY_WEIGHT
from routing.hazard_model import HazardSnapshot, HazardProvider, ZoneRisk
from routing.dijkstra import DijkstraPathfinder
from routing.route_cache import RouteCache


@dataclass
class RouteRequest:
    """Evacuation path calculation request parameters.

    Attributes:
        source_node:    Starting zone/node ID.
        target_exits:   List of allowed emergency exit node IDs (None = all available exits).
        avoid_hazards:  True to apply dynamic hazard penalties.
    """
    source_node: str
    target_exits: Optional[List[str]] = None
    avoid_hazards: bool = True


@dataclass
class RouteResult:
    """Computed evacuation route output contract.

    Attributes:
        source_node:         Starting zone ID.
        target_exit:         Selected target emergency exit node ID.
        path:                Ordered list of node IDs from source to target exit.
        estimated_time_s:    Total estimated traversal cost in seconds.
        cumulative_risk:     Sum of hazard risks along the path.
        is_shelter_in_place: True if no valid, safe evacuation path exists.
    """
    source_node: str
    target_exit: str = ""
    path: List[str] = field(default_factory=list)
    estimated_time_s: float = 0.0
    cumulative_risk: float = 0.0
    is_shelter_in_place: bool = False


class RouteManager(ABC):
    """Abstract interface for evacuation routing engines."""

    @abstractmethod
    def calculate_route(self, request: RouteRequest) -> RouteResult:
        """Calculate optimal evacuation route for a single route request."""
        pass

    @abstractmethod
    def calculate_all_routes(self, source_nodes: List[str]) -> Dict[str, RouteResult]:
        """Calculate optimal evacuation routes for multiple source nodes."""
        pass


class DefaultRouteManager(RouteManager):
    """Default implementation of RouteManager interface."""

    def __init__(
        self,
        graph: BuildingGraph,
        hazard_provider: Optional[HazardProvider] = None,
        weight_calculator: Optional[DynamicEdgeWeightCalculator] = None,
        enable_cache: bool = True,
    ) -> None:
        """Initialize DefaultRouteManager.

        Args:
            graph: Structural BuildingGraph topology container.
            hazard_provider: Optional HazardProvider instance.
            weight_calculator: Optional DynamicEdgeWeightCalculator instance.
            enable_cache: True to enable route caching.
        """
        self.graph = graph
        self.hazard_provider = hazard_provider
        self.calculator = weight_calculator or DynamicEdgeWeightCalculator()
        self.pathfinder = DijkstraPathfinder(self.calculator)
        
        self.enable_cache = enable_cache
        self.cache = RouteCache() if enable_cache else None

    def calculate_route(self, request: RouteRequest) -> RouteResult:
        """Calculate optimal evacuation route for a single RouteRequest.

        Args:
            request: RouteRequest specifying source_node, allowed exits, etc.

        Returns:
            RouteResult contract containing path, cost, target exit, shelter_in_place flag.
        """
        if request.source_node not in self.graph.nodes:
            return RouteResult(source_node=request.source_node, is_shelter_in_place=True)

        # Retrieve hazard snapshot if available and requested
        snapshot: Optional[HazardSnapshot] = None
        if request.avoid_hazards and self.hazard_provider is not None:
            snapshot = self.hazard_provider.get_hazard_snapshot()

        # Target exits: request specified or all exit nodes in building graph
        if request.target_exits:
            target_exits = [e for e in request.target_exits if e in self.graph.nodes]
        else:
            target_exits = [n.id for n in self.graph.get_exit_nodes()]

        if not target_exits:
            return RouteResult(source_node=request.source_node, is_shelter_in_place=True)

        # Consult route cache
        if self.enable_cache and self.cache:
            cached_result = self.cache.get(request.source_node, target_exits, snapshot)
            if cached_result is not None:
                return cached_result

        # Run Dijkstra algorithm
        path, cost, risk, exit_node = self.pathfinder.find_shortest_path(
            graph=self.graph,
            source_node=request.source_node,
            target_exits=target_exits,
            snapshot=snapshot,
        )

        # Determine if Shelter-In-Place is required (no valid path or infinite cost)
        is_shelter = (len(path) == 0 or cost >= INFINITY_WEIGHT)

        result = RouteResult(
            source_node=request.source_node,
            target_exit=exit_node if not is_shelter else "",
            path=path if not is_shelter else [],
            estimated_time_s=cost if not is_shelter else INFINITY_WEIGHT,
            cumulative_risk=risk if not is_shelter else 1.0,
            is_shelter_in_place=is_shelter,
        )

        # Store in cache
        if self.enable_cache and self.cache:
            self.cache.put(request.source_node, target_exits, result, snapshot)

        return result

    def calculate_all_routes(self, source_nodes: Optional[List[str]] = None) -> Dict[str, RouteResult]:
        """Calculate optimal evacuation routes for multiple source nodes.

        Args:
            source_nodes: Optional list of zone IDs (defaults to all non-exit nodes).

        Returns:
            Dict mapping source_node -> RouteResult.
        """
        if source_nodes is None:
            source_nodes = [n_id for n_id, node in self.graph.nodes.items() if not node.is_exit]

        results: Dict[str, RouteResult] = {}
        for src in source_nodes:
            req = RouteRequest(source_node=src)
            results[src] = self.calculate_route(req)

        return results

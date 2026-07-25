"""
SurakshaPath AI — Shared Route Manager Interfaces.

Defines the high-level request, result, and manager contracts for evacuation routing.

Design Principles:
  - Data contracts and abstract manager interface only.
  - Zero Dijkstra, A*, or pathfinding algorithm implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
        """Calculate optimal evacuation route for a single route request.

        Args:
            request: RouteRequest parameters.

        Returns:
            RouteResult contract containing path and costs.
        """
        pass

    @abstractmethod
    def calculate_all_routes(self, source_nodes: List[str]) -> Dict[str, RouteResult]:
        """Calculate optimal evacuation routes for multiple source nodes.

        Args:
            source_nodes: List of starting zone IDs.

        Returns:
            Dict mapping source_node -> RouteResult.
        """
        pass

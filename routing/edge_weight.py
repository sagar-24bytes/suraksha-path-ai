"""
SurakshaPath AI — Dynamic Edge Weight Calculation Engine.

Calculates dynamic traversal costs for building edges based on physical hazard scores,
temperature, smoke obscuration, closed fire doors, and corridor blockages.

Edge Weight Formula:
  W = W_base · exp(k · H_v) · (1 + β · S_v) · M_door

  If H_v >= blocked_threshold or (from_node, to_node) in blocked_edges:
      W = infinity (Impassable)

  Where:
    W_base: Baseline safe traversal time in seconds.
    H_v: Composite hazard score (0.0–1.0) of destination/corridor zone.
    k: Exponential hazard sensitivity multiplier (default 4.0).
    S_v: Smoke density obscuration (0.0–1.0).
    β: Smoke penalty factor (default 1.5).
    M_door: Fire-rated door traversal penalty multiplier (default 1.25 if closed).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from routing.graph import Edge
from routing.hazard_model import HazardSnapshot


# Constants for infinite weight (impassable/blocked edge)
INFINITY_WEIGHT: float = float("inf")


class BaseWeightProvider(ABC):
    """Abstract provider for static baseline traversal weights."""

    @abstractmethod
    def get_base_weight(self, from_node: str, to_node: str) -> float:
        """Get baseline traversal weight in seconds under safe conditions."""
        pass


class EdgeWeightCalculator(ABC):
    """Abstract interface for dynamic edge weight calculations based on hazard levels."""

    @abstractmethod
    def calculate_weight(
        self,
        edge: Edge,
        hazard_score: float = 0.0,
        confidence: float = 1.0,
    ) -> float:
        """Calculate dynamic traversal cost for an edge."""
        pass


class DynamicEdgeWeightCalculator(EdgeWeightCalculator):
    """Dynamic dynamic edge cost calculator incorporating physical hazard penalties."""

    def __init__(
        self,
        k_hazard_sensitivity: float = 4.0,
        beta_smoke_penalty: float = 1.5,
        fire_door_multiplier: float = 1.25,
        blocked_threshold: float = 0.80,
    ) -> None:
        """Initialize DynamicEdgeWeightCalculator.

        Args:
            k_hazard_sensitivity: Exponential multiplier for hazard score penalty.
            beta_smoke_penalty: Linear multiplier for smoke obscuration penalty.
            fire_door_multiplier: Penalty multiplier when traversing a fire door.
            blocked_threshold: Hazard score at or above which an edge becomes impassable.
        """
        self.k = k_hazard_sensitivity
        self.beta = beta_smoke_penalty
        self.fire_door_multiplier = fire_door_multiplier
        self.blocked_threshold = blocked_threshold

    def calculate_weight(
        self,
        edge: Edge,
        hazard_score: float = 0.0,
        confidence: float = 1.0,
    ) -> float:
        """Calculate dynamic traversal cost for an edge without snapshot context.

        Args:
            edge: Physical Edge instance.
            hazard_score: Hazard score of destination/corridor zone (0.0–1.0).
            confidence: Sensor confidence in hazard score (0.0–1.0).

        Returns:
            Calculated dynamic edge weight in seconds, or float("inf") if blocked.
        """
        # Blocked if hazard exceeds safety threshold
        if hazard_score >= self.blocked_threshold:
            return INFINITY_WEIGHT

        base_weight = edge.base_weight

        # Exponential hazard penalty factor: exp(k * H_v)
        effective_hazard = hazard_score * confidence
        hazard_penalty = math.exp(self.k * effective_hazard)

        # Fire door penalty
        door_penalty = self.fire_door_multiplier if edge.has_fire_door else 1.0

        weight = base_weight * hazard_penalty * door_penalty
        return round(weight, 4)

    def calculate_weight_with_snapshot(
        self,
        edge: Edge,
        snapshot: Optional[HazardSnapshot] = None,
    ) -> float:
        """Calculate dynamic traversal cost using a complete HazardSnapshot.

        Args:
            edge: Physical Edge instance.
            snapshot: HazardSnapshot containing building-wide risks & blocked edges.

        Returns:
            Calculated dynamic edge cost in seconds, or float("inf") if impassable.
        """
        if snapshot is None:
            return self.calculate_weight(edge)

        # 1. Check explicit edge blockages
        if (edge.from_node, edge.to_node) in snapshot.blocked_edges:
            return INFINITY_WEIGHT
        if (edge.to_node, edge.from_node) in snapshot.blocked_edges:
            return INFINITY_WEIGHT

        # 2. Retrieve destination node hazard risk
        risk = snapshot.get_risk(edge.to_node)
        if risk.is_blocked or risk.hazard_score >= self.blocked_threshold:
            return INFINITY_WEIGHT

        # Base traversal time
        base = edge.base_weight

        # Hazard score penalty: exp(k * H_v)
        hazard_mult = math.exp(self.k * risk.hazard_score * risk.confidence)

        # Fire door penalty
        door_mult = self.fire_door_multiplier if edge.has_fire_door else 1.0

        cost = base * hazard_mult * door_mult
        return round(cost, 4)

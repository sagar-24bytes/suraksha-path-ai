"""
SurakshaPath AI — Shared Edge Weight Abstraction Interfaces.

Defines the abstract base classes and contracts for dynamic edge cost calculation.

Design Principles:
  - Abstract interfaces and baseline definitions only.
  - Zero calculation formulas or pathfinding code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from routing.graph import Edge


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
        """Calculate dynamic traversal cost for an edge.

        Args:
            edge: Physical Edge instance.
            hazard_score: Hazard score of target/corridor zone (0.0–1.0).
            confidence: Sensor confidence in hazard score (0.0–1.0).

        Returns:
            Computed dynamic edge weight cost in seconds.
        """
        pass

"""
SurakshaPath AI — Shared Hazard Data Interfaces for Routing.

Defines structural hazard snapshots and provider abstractions consumed by the routing subsystem.

Design Principles:
  - Data contracts and abstract provider interfaces only.
  - Zero sensor fusion or physics calculations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ZoneRisk:
    """Hazard and risk snapshot for a single zone.

    Attributes:
        zone_id:      Target zone identifier.
        hazard_score: Composite hazard score (0.0–1.0).
        hazard_level: Discrete classification ("SAFE", "ADVISORY", "WARNING", "DANGER", "CRITICAL").
        confidence:   Assessment confidence (0.0–1.0).
        is_blocked:   True if zone or exit is completely impassable.
    """
    zone_id: str
    hazard_score: float = 0.0
    hazard_level: str = "SAFE"
    confidence: float = 1.0
    is_blocked: bool = False


@dataclass
class HazardSnapshot:
    """Complete building-wide hazard state snapshot at a given tick.

    Attributes:
        timestamp:     Simulation/clock timestamp in seconds.
        zone_risks:    Dict of zone_id -> ZoneRisk.
        blocked_edges: List of (from_node, to_node) pairs that are impassable.
    """
    timestamp: float = 0.0
    zone_risks: Dict[str, ZoneRisk] = field(default_factory=dict)
    blocked_edges: List[tuple[str, str]] = field(default_factory=list)

    def get_risk(self, zone_id: str) -> ZoneRisk:
        """Retrieve ZoneRisk for a zone, defaulting to safe if unlisted."""
        return self.zone_risks.get(zone_id, ZoneRisk(zone_id=zone_id))


class HazardProvider(ABC):
    """Abstract interface for components that supply building hazard snapshots."""

    @abstractmethod
    def get_hazard_snapshot(self) -> HazardSnapshot:
        """Retrieve current building hazard snapshot."""
        pass

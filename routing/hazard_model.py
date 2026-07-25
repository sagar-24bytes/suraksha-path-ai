"""
SurakshaPath AI — Shared Hazard Data Models & Providers.

Defines structural hazard snapshots and provider abstractions consumed by the routing subsystem.

Providers:
  - SimulationHazardProvider: Extracts HazardSnapshot directly from SimulationEngine.
  - TelemetryHazardProvider: Extracts HazardSnapshot from a stream of TelemetryPackets.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from communication.packet_schema import TelemetryPacket


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
    blocked_edges: List[Tuple[str, str]] = field(default_factory=list)

    def get_risk(self, zone_id: str) -> ZoneRisk:
        """Retrieve ZoneRisk for a zone, defaulting to safe if unlisted."""
        return self.zone_risks.get(zone_id, ZoneRisk(zone_id=zone_id))

    def compute_hash(self) -> str:
        """Compute lightweight state signature hash for route cache invalidation."""
        risk_tuples = sorted([(k, v.hazard_score, v.is_blocked) for k, v in self.zone_risks.items()])
        blocked_tuples = sorted(self.blocked_edges)
        return str(hash((self.timestamp, tuple(risk_tuples), tuple(blocked_tuples))))


class HazardProvider(ABC):
    """Abstract interface for components that supply building hazard snapshots."""

    @abstractmethod
    def get_hazard_snapshot(self) -> HazardSnapshot:
        """Retrieve current building hazard snapshot."""
        pass


class TelemetryHazardProvider(HazardProvider):
    """HazardProvider implementation assembling HazardSnapshot from TelemetryPackets."""

    def __init__(self) -> None:
        self._current_packets: Dict[str, TelemetryPacket] = {}
        self._blocked_edges: List[Tuple[str, str]] = []
        self._timestamp: float = 0.0

    def update_telemetry(
        self,
        packets: Dict[str, TelemetryPacket],
        blocked_edges: Optional[List[Tuple[str, str]]] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Update provider telemetry data."""
        self._current_packets = dict(packets)
        if blocked_edges is not None:
            self._blocked_edges = list(blocked_edges)
        if timestamp is not None:
            self._timestamp = timestamp

    def get_hazard_snapshot(self) -> HazardSnapshot:
        """Construct and return current HazardSnapshot."""
        zone_risks: Dict[str, ZoneRisk] = {}

        for zone_id, pkt in self._current_packets.items():
            is_blocked = (pkt.evacuation_state == "SHELTER" or pkt.hazard_score >= 0.85)
            zone_risks[zone_id] = ZoneRisk(
                zone_id=zone_id,
                hazard_score=pkt.hazard_score,
                hazard_level=pkt.evacuation_state,
                confidence=1.0,
                is_blocked=is_blocked,
            )

        return HazardSnapshot(
            timestamp=self._timestamp,
            zone_risks=zone_risks,
            blocked_edges=self._blocked_edges,
        )

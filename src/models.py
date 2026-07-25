"""
SurakshaPath AI — Data Models.

All dataclasses and enums shared across the system.
This module contains ONLY data definitions — no business logic.

Naming conventions:
    Enums:       PascalCase with UPPER_SNAKE values
    Dataclasses: PascalCase
    Fields:      snake_case with type hints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# =============================================================
# Enums
# =============================================================

class HazardLevel(Enum):
    """Discrete hazard classification for a zone.

    Mapped from continuous hazard score (0.0–1.0)
    using thresholds defined in thresholds.yaml.
    """
    SAFE = "SAFE"
    ADVISORY = "ADVISORY"
    WARNING = "WARNING"
    DANGER = "DANGER"
    CRITICAL = "CRITICAL"


class SensorType(Enum):
    """Types of sensors deployed in the building."""
    TEMPERATURE = "TEMPERATURE"
    SMOKE = "SMOKE"
    FLAME = "FLAME"


class ZoneType(Enum):
    """Classification of building zones."""
    ROOM = "ROOM"
    CORRIDOR = "CORRIDOR"
    STAIRWELL = "STAIRWELL"
    LOBBY = "LOBBY"
    EXIT = "EXIT"


class SensorStatus(Enum):
    """Operational state of an individual sensor."""
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    OFFLINE = "OFFLINE"


class SimulationEventType(Enum):
    """Types of scripted events in a simulation scenario."""
    IGNITE = "IGNITE"
    SENSOR_FAIL = "SENSOR_FAIL"
    SENSOR_RECOVER = "SENSOR_RECOVER"
    COMM_FAIL = "COMM_FAIL"
    COMM_RESTORE = "COMM_RESTORE"
    BLOCK_EXIT = "BLOCK_EXIT"
    UNBLOCK_EXIT = "UNBLOCK_EXIT"


class SystemStatus(Enum):
    """Overall system operational status displayed in the header."""
    NORMAL = "NORMAL"
    ADVISORY = "ADVISORY"
    ALERT = "ALERT"
    FAILSAFE = "FAILSAFE"


# =============================================================
# Sensor Data Models
# =============================================================

@dataclass
class SensorReading:
    """A single reading from one sensor at one point in time.

    Attributes:
        sensor_id:        Unique identifier (e.g., "T-R-105").
        sensor_type:      Type of sensor.
        zone_id:          Zone where the sensor is installed.
        raw_value:        Unprocessed sensor value (type-specific units).
        normalized_value: Threat level mapped to 0.0–1.0.
        confidence:       Trustworthiness of this reading (0.0–1.0).
        timestamp:        Simulation tick when this reading was produced.
        status:           Operational state of the sensor.
    """
    sensor_id: str
    sensor_type: SensorType
    zone_id: str
    raw_value: float
    normalized_value: float
    confidence: float
    timestamp: float
    status: SensorStatus = SensorStatus.NORMAL


# =============================================================
# Hazard Assessment Models
# =============================================================

@dataclass
class ZoneHazardState:
    """Fused hazard assessment for a single zone.

    Produced by the sensor fusion engine each tick.

    Attributes:
        zone_id:              Zone identifier.
        hazard_score:         Composite score (0.0–1.0).
        hazard_level:         Discrete classification.
        confidence:           Overall confidence in the assessment.
        contributing_factors: Per-sensor-type contribution breakdown.
        reasoning:            Human-readable explanation strings.
    """
    zone_id: str
    hazard_score: float
    hazard_level: HazardLevel
    confidence: float
    contributing_factors: Dict[str, float] = field(default_factory=dict)
    reasoning: List[str] = field(default_factory=list)


@dataclass
class FusionExplanation:
    """Detailed breakdown of how a hazard score was computed.

    Displayed in the Explainability Panel so judges can see
    the exact formula computation.

    Attributes:
        zone_id:               Zone identifier.
        sensor_contributions:  Per-sensor detail: type, value, weight,
                               confidence, and individual contribution.
        numerator:             Sum of (weight × confidence × value).
        denominator:           Sum of (weight × confidence).
        hazard_score:          Final computed score.
        hazard_level:          Classified level.
        reasoning:             List of human-readable reason strings.
    """
    zone_id: str
    sensor_contributions: List[Dict[str, float]]
    numerator: float
    denominator: float
    hazard_score: float
    hazard_level: HazardLevel
    reasoning: List[str]


# =============================================================
# Routing Models
# =============================================================

@dataclass
class RouteResult:
    """Computed evacuation route for a single zone.

    Produced by the pathfinder each tick.

    Attributes:
        source_zone:          Starting zone of the route.
        exit_id:              Target exit zone.
        path:                 Ordered list of zone IDs from source to exit.
        estimated_time_s:     Total estimated traversal time.
        route_risk:           Cumulative risk score along the path.
        is_shelter_in_place:  True if no valid route exists.
    """
    source_zone: str
    exit_id: str
    path: List[str]
    estimated_time_s: float
    route_risk: float
    is_shelter_in_place: bool = False


# =============================================================
# Simulation Event Model
# =============================================================

@dataclass
class SimulationEvent:
    """A scripted event that fires at a specific simulation tick.

    Loaded from scenarios.yaml by the scenario manager.

    Attributes:
        tick:        Tick number when this event fires.
        event_type:  Category of the event.
        zone_id:     Affected zone (if applicable).
        sensor_id:   Affected sensor (if applicable).
        parameters:  Event-specific key-value parameters.
    """
    tick: int
    event_type: SimulationEventType
    zone_id: Optional[str] = None
    sensor_id: Optional[str] = None
    parameters: Dict = field(default_factory=dict)


# =============================================================
# System Snapshot
# =============================================================

@dataclass
class EvacuationSnapshot:
    """Complete system state at a single simulation tick.

    This is the primary data structure passed from the engine
    to the dashboard. It contains everything needed to render
    the entire UI.

    Attributes:
        tick:                 Current simulation tick number.
        timestamp:            Wall-clock timestamp of this snapshot.
        zone_hazard_states:   Per-zone hazard assessments.
        sensor_readings:      All sensor readings for this tick.
        routes:               Per-zone evacuation routes.
        alerts:               Alert messages generated this tick.
        blocked_edges:        List of (from, to) zone ID pairs.
        evacuation_progress:  Summary counters (total, evacuated, remaining).
        fire_intensities:     Per-zone fire intensity (0.0–1.0).
        smoke_levels:         Per-zone smoke density (0.0–1.0).
        system_status:        Overall system status.
    """
    tick: int
    timestamp: float
    zone_hazard_states: Dict[str, ZoneHazardState] = field(default_factory=dict)
    sensor_readings: List[SensorReading] = field(default_factory=list)
    routes: Dict[str, RouteResult] = field(default_factory=dict)
    alerts: List[Dict[str, str]] = field(default_factory=list)
    blocked_edges: List[Tuple[str, str]] = field(default_factory=list)
    evacuation_progress: Dict[str, int] = field(default_factory=lambda: {
        "total": 0,
        "evacuated": 0,
        "remaining": 0,
    })
    fire_intensities: Dict[str, float] = field(default_factory=dict)
    smoke_levels: Dict[str, float] = field(default_factory=dict)
    system_status: SystemStatus = SystemStatus.NORMAL

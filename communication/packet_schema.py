"""
SurakshaPath AI — Canonical Shared Telemetry Packet Schema.

Defines the immutable TelemetryPacket schema used across Simulation, MicroPython
Firmware, Transport Abstraction, and the Fire Commander Dashboard.

Features:
  - Strongly typed dataclass with standard defaults
  - Schema versioning (schema_version = "1.0")
  - Lightweight module-level status constants (MicroPython / CPython compatible)
  - JSON and dictionary serialization/deserialization helpers
  - Extended field and status validation
  - Zero external enum dependency for minimal memory usage
"""

from __future__ import annotations

import json
import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any

# =============================================================
# Lightweight Status Constants (MicroPython & CPython Compatible)
# =============================================================

# --- Evacuation States ---
EVAC_STATE_NORMAL = "NORMAL"
EVAC_STATE_WARNING = "WARNING"
EVAC_STATE_EVACUATE = "EVACUATE"
EVAC_STATE_SHELTER = "SHELTER"

ALLOWED_EVACUATION_STATES = {
    EVAC_STATE_NORMAL,
    EVAC_STATE_WARNING,
    EVAC_STATE_EVACUATE,
    EVAC_STATE_SHELTER,
}

# --- Health States ---
HEALTH_HEALTHY = "HEALTHY"
HEALTH_WARNING = "WARNING"
HEALTH_OFFLINE = "OFFLINE"
HEALTH_ERROR = "ERROR"
HEALTH_FAULT = "FAULT"
HEALTH_DEGRADED = "DEGRADED"
HEALTH_TIMEDOUT = "TIMEDOUT"
HEALTH_DISCONNECTED = "DISCONNECTED"
HEALTH_WATCHDOG_RESET = "WATCHDOG_RESET"

ALLOWED_NODE_HEALTH_STATES = {
    HEALTH_HEALTHY,
    HEALTH_WARNING,
    HEALTH_OFFLINE,
    HEALTH_ERROR,
    HEALTH_FAULT,
}

ALLOWED_COMM_HEALTH_STATES = {
    HEALTH_HEALTHY,
    HEALTH_DEGRADED,
    HEALTH_TIMEDOUT,
    HEALTH_DISCONNECTED,
}

ALLOWED_FIRMWARE_HEALTH_STATES = {
    HEALTH_HEALTHY,
    HEALTH_WATCHDOG_RESET,
    HEALTH_FAULT,
}

# --- LED States ---
LED_STATE_SAFE_SOLID = "SAFE_SOLID"
LED_STATE_WARN_PULSE = "WARN_PULSE"
LED_STATE_DANGER_FLASH = "DANGER_FLASH"
LED_STATE_BLOCKED_CROSS = "BLOCKED_CROSS"

ALLOWED_LED_STATES = {
    LED_STATE_SAFE_SOLID,
    LED_STATE_WARN_PULSE,
    LED_STATE_DANGER_FLASH,
    LED_STATE_BLOCKED_CROSS,
}


# =============================================================
# Canonical Shared Telemetry Packet
# =============================================================

@dataclass
class TelemetryPacket:
    """Canonical Telemetry Packet exchanged across all subsystems.

    Attributes:
        schema_version:       Schema protocol version string (default "1.0").
        packet_id:            Unique packet identifier (UUID4 string).
        timestamp:            Unix/simulation timestamp in seconds.
        node_id:              Unique node ID (e.g., "NODE-R105").
        zone_id:              Zone identifier (e.g., "R-105").
        temperature:          Temperature in °C (default 25.0).
        smoke_level:          Smoke density obscuration 0.0–1.0 (default 0.0).
        flame_detected:       Optical flame sensor state (default False).
        occupancy_count:      Current occupant count in zone (default 0).
        hazard_score:         Fused hazard score 0.0–1.0 (default 0.0).
        evacuation_state:     Evacuation status ("NORMAL", "WARNING", "EVACUATE", "SHELTER").
        recommended_exit:     Assigned exit node (e.g., "X-01").
        route_cost:           Estimated evacuation route traversal cost in seconds.
        node_health:          Health status ("HEALTHY", "WARNING", "OFFLINE", "ERROR", "FAULT").
        communication_health: Comm link status ("HEALTHY", "DEGRADED", "TIMEDOUT", "DISCONNECTED").
        firmware_health:      MicroPython firmware runtime status ("HEALTHY", "WATCHDOG_RESET", "FAULT").
        led_state:            Neopixel/RGB indicator state ("SAFE_SOLID", "WARN_PULSE", "DANGER_FLASH", "BLOCKED_CROSS").
        battery_level:        Power supply percentage 0.0–100.0 (default 100.0).
        metadata:             Optional dictionary for extra telemetry annotations.
    """
    schema_version: str = "1.0"
    packet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    node_id: str = ""
    zone_id: str = ""

    # Physical / Sensor Readings
    temperature: float = 25.0
    smoke_level: float = 0.0
    flame_detected: bool = False
    occupancy_count: int = 0

    # Computed Algorithmic Outputs
    hazard_score: float = 0.0
    evacuation_state: str = EVAC_STATE_NORMAL
    recommended_exit: str = "X-01"
    route_cost: float = 0.0

    # System & Subsystem Health Diagnostics
    node_health: str = HEALTH_HEALTHY
    communication_health: str = HEALTH_HEALTHY
    firmware_health: str = HEALTH_HEALTHY

    # Actuation & Power State
    led_state: str = LED_STATE_SAFE_SOLID
    battery_level: float = 100.0

    # Extended Payload Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize TelemetryPacket to a clean dictionary representation.

        Returns:
            Dictionary containing all packet fields.
        """
        return asdict(self)

    def to_json(self) -> str:
        """Serialize TelemetryPacket to a JSON string.

        Returns:
            Compact JSON string representation.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TelemetryPacket:
        """Deserialize a TelemetryPacket from a dictionary.

        Args:
            data: Dictionary containing packet fields.

        Returns:
            Constructed TelemetryPacket instance.
        """
        valid_fields = {f for f in cls.__dataclass_fields__}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    @classmethod
    def from_json(cls, json_str: str) -> TelemetryPacket:
        """Deserialize a TelemetryPacket from a JSON string.

        Args:
            json_str: JSON formatted string.

        Returns:
            Constructed TelemetryPacket instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> bool:
        """Validate packet field bounds, types, and status values.

        Returns:
            True if all fields are valid, False otherwise.
        """
        try:
            if not isinstance(self.schema_version, str) or not self.schema_version:
                return False
            if not isinstance(self.packet_id, str) or not self.packet_id:
                return False
            if not isinstance(self.timestamp, (int, float)) or self.timestamp < 0:
                return False
            if not isinstance(self.temperature, (int, float)):
                return False
            if not (0.0 <= float(self.smoke_level) <= 1.0):
                return False
            if not isinstance(self.flame_detected, bool):
                return False
            if not isinstance(self.occupancy_count, int) or self.occupancy_count < 0:
                return False
            if not (0.0 <= float(self.hazard_score) <= 1.0):
                return False
            if not (0.0 <= float(self.battery_level) <= 100.0):
                return False
            
            # Status Value Validations
            if self.evacuation_state not in ALLOWED_EVACUATION_STATES:
                return False
            if self.node_health not in ALLOWED_NODE_HEALTH_STATES:
                return False
            if self.communication_health not in ALLOWED_COMM_HEALTH_STATES:
                return False
            if self.firmware_health not in ALLOWED_FIRMWARE_HEALTH_STATES:
                return False
            if self.led_state not in ALLOWED_LED_STATES:
                return False

            return True
        except Exception:
            return False

"""
SurakshaPath AI — Synthetic Sensor Generator.

Converts physical ground-truth states (fire physics, smoke dynamics, occupancy)
into realistic TelemetryPacket telemetry with configurable sensor noise.

Features:
  - Deterministic noise injection when initialized with a fixed seed.
  - Gaussian noise on temperature and smoke sensors.
  - Generates canonical TelemetryPacket instances — no ad-hoc formats.
  - Populates physical readings, health indicators, battery levels, and initial states.
"""

from __future__ import annotations

import random
import time
from typing import Dict, List, Optional

from communication.packet_schema import (
    TelemetryPacket,
    EVAC_STATE_NORMAL,
    HEALTH_HEALTHY,
    LED_STATE_SAFE_SOLID,
)
from simulation.fire_physics import ZoneFireState


class SensorGenerator:
    """Generates synthetic TelemetryPacket telemetry from zone physical state."""

    def __init__(
        self,
        seed: Optional[int] = 42,
        temp_noise_std: float = 0.5,
        smoke_noise_std: float = 0.01,
        flame_detection_threshold: float = 0.15,
    ) -> None:
        """Initialize SensorGenerator.

        Args:
            seed: Random seed for deterministic simulation output (None for non-deterministic).
            temp_noise_std: Standard deviation of Gaussian noise added to temperature (°C).
            smoke_noise_std: Standard deviation of Gaussian noise added to smoke level (0.0–1.0).
            flame_detection_threshold: Fire intensity threshold at which optical flame sensor trips.
        """
        self.seed = seed
        self.temp_noise_std = temp_noise_std
        self.smoke_noise_std = smoke_noise_std
        self.flame_detection_threshold = flame_detection_threshold

        self._rng = random.Random(seed)

    def reseed(self, seed: Optional[int]) -> None:
        """Reset the random number generator with a new seed."""
        self.seed = seed
        self._rng = random.Random(seed)

    def generate_packet(
        self,
        zone_id: str,
        fire_state: ZoneFireState,
        smoke_level: float,
        occupancy_count: int = 0,
        current_tick: float = 0.0,
    ) -> TelemetryPacket:
        """Generate a single TelemetryPacket for a zone based on physical state.

        Args:
            zone_id: Zone/Node identifier.
            fire_state: Physical ZoneFireState from FirePhysicsModel.
            smoke_level: Smoke obscuration level (0.0–1.0) from SmokePhysicsModel.
            occupancy_count: Current occupant count in the zone.
            current_tick: Simulation tick / timestamp.

        Returns:
            Canonical TelemetryPacket instance.
        """
        # Apply Gaussian noise to physical readings
        noisy_temp = fire_state.temperature + self._rng.gauss(0.0, self.temp_noise_std)
        noisy_temp = max(10.0, noisy_temp)  # Floor at 10°C ambient

        noisy_smoke = smoke_level + self._rng.gauss(0.0, self.smoke_noise_std)
        noisy_smoke = max(0.0, min(1.0, noisy_smoke))

        # Optical flame sensor trip
        flame_detected = fire_state.is_ignited and (fire_state.intensity >= self.flame_detection_threshold)

        node_id = f"NODE-{zone_id}"

        return TelemetryPacket(
            schema_version="1.0",
            timestamp=float(current_tick),
            node_id=node_id,
            zone_id=zone_id,
            temperature=round(noisy_temp, 2),
            smoke_level=round(noisy_smoke, 4),
            flame_detected=flame_detected,
            occupancy_count=max(0, occupancy_count),
            hazard_score=0.0,  # Computed on-device / by fusion in later phases
            evacuation_state=EVAC_STATE_NORMAL,
            recommended_exit="X-01",
            route_cost=0.0,
            node_health=HEALTH_HEALTHY,
            communication_health=HEALTH_HEALTHY,
            firmware_health=HEALTH_HEALTHY,
            led_state=LED_STATE_SAFE_SOLID,
            battery_level=100.0,
            metadata={"simulated": True},
        )

    def generate_all_packets(
        self,
        fire_states: Dict[str, ZoneFireState],
        smoke_levels: Dict[str, float],
        occupancy_map: Optional[Dict[str, int]] = None,
        current_tick: float = 0.0,
    ) -> Dict[str, TelemetryPacket]:
        """Generate TelemetryPacket instances for all zones in the building.

        Args:
            fire_states: Dict of zone_id -> ZoneFireState.
            smoke_levels: Dict of zone_id -> smoke_level.
            occupancy_map: Dict of zone_id -> occupant count.
            current_tick: Simulation tick / timestamp.

        Returns:
            Dict of zone_id -> TelemetryPacket.
        """
        occupancy_map = occupancy_map or {}
        packets: Dict[str, TelemetryPacket] = {}

        for zone_id, fire_state in fire_states.items():
            smoke = smoke_levels.get(zone_id, 0.0)
            occ = occupancy_map.get(zone_id, 0)
            pkt = self.generate_packet(
                zone_id=zone_id,
                fire_state=fire_state,
                smoke_level=smoke,
                occupancy_count=occ,
                current_tick=current_tick,
            )
            packets[zone_id] = pkt

        return packets

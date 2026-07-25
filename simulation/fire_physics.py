"""
SurakshaPath AI — Fire Physics Simulation Model.

Implements a deterministic, zone-based fire growth and heat transfer model.
Tracks fire intensity (0.0–1.0), temperature (°C), ignition status, and thermal decay.

Key Design Principles:
  - Deterministic calculations when supplied with a fixed seed or parameters.
  - Independent per-zone state management.
  - Radiative and conductive heat transfer between connected adjacent zones.
  - Fully configurable physics parameters (growth rate, max temp, cooling rate).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class ZoneFireState:
    """Physical fire state for a single zone.

    Attributes:
        zone_id:             Identifier of the zone.
        intensity:           Normalized fire intensity 0.0 (no fire) to 1.0 (flashover).
        temperature:         Temperature in degrees Celsius.
        is_ignited:          True if an active flame/fire is burning in this zone.
        burn_duration_ticks: Number of ticks the fire has been active.
    """
    zone_id: str
    intensity: float = 0.0
    temperature: float = 25.0
    is_ignited: bool = False
    burn_duration_ticks: int = 0


class FirePhysicsModel:
    """Deterministic fire growth and thermal dynamics simulator."""

    def __init__(
        self,
        ambient_temp_c: float = 25.0,
        max_temp_c: float = 800.0,
        base_growth_rate: float = 0.03,
        cooling_rate: float = 0.01,
        heat_transfer_coeff: float = 0.05,
    ) -> None:
        """Initialize FirePhysicsModel.

        Args:
            ambient_temp_c: Base room temperature when safe (°C).
            max_temp_c: Maximum flashover fire temperature (°C).
            base_growth_rate: Per-tick growth rate of fire intensity.
            cooling_rate: Thermal dissipation rate per tick when fire dies out.
            heat_transfer_coeff: Thermal transfer rate between connected zones.
        """
        self.ambient_temp_c = ambient_temp_c
        self.max_temp_c = max_temp_c
        self.base_growth_rate = base_growth_rate
        self.cooling_rate = cooling_rate
        self.heat_transfer_coeff = heat_transfer_coeff

        self._states: Dict[str, ZoneFireState] = {}

    def initialize_zones(self, zone_ids: List[str]) -> None:
        """Initialize or reset all zones to safe ambient baseline state.

        Args:
            zone_ids: List of all zone identifiers in the building topology.
        """
        self._states = {
            z_id: ZoneFireState(zone_id=z_id, temperature=self.ambient_temp_c)
            for z_id in zone_ids
        }

    def ignite(self, zone_id: str, initial_intensity: float = 0.15) -> bool:
        """Ignite a fire in a target zone.

        Args:
            zone_id: Zone to ignite.
            initial_intensity: Starting fire intensity (0.01–1.0).

        Returns:
            True if zone exists and was ignited, False otherwise.
        """
        if zone_id not in self._states:
            return False

        state = self._states[zone_id]
        state.is_ignited = True
        state.intensity = max(state.intensity, min(1.0, initial_intensity))
        state.temperature = max(
            state.temperature,
            self.ambient_temp_c + (self.max_temp_c - self.ambient_temp_c) * state.intensity * 0.5
        )
        return True

    def extinguish(self, zone_id: str) -> bool:
        """Extinguish fire in a target zone.

        Args:
            zone_id: Zone to extinguish.

        Returns:
            True if zone exists and fire was put out.
        """
        if zone_id not in self._states:
            return False

        state = self._states[zone_id]
        state.is_ignited = False
        state.intensity = 0.0
        return True

    def get_state(self, zone_id: str) -> Optional[ZoneFireState]:
        """Retrieve current physical fire state for a zone."""
        return self._states.get(zone_id)

    def get_all_states(self) -> Dict[str, ZoneFireState]:
        """Retrieve physical fire state dictionary for all zones."""
        return self._states

    def update(
        self,
        adjacency_edges: Optional[List[Tuple[str, str]]] = None,
        growth_multiplier: float = 1.0,
    ) -> Dict[str, ZoneFireState]:
        """Advance the fire physics simulation by one tick.

        Args:
            adjacency_edges: List of bidirectional (zone_a, zone_b) connected edges.
            growth_multiplier: Scenario growth rate modifier.

        Returns:
            Dictionary of updated ZoneFireState objects for all zones.
        """
        effective_growth = self.base_growth_rate * growth_multiplier
        next_temperatures: Dict[str, float] = {z: s.temperature for z, s in self._states.items()}

        # 1. Update active fires (intensity & internal temperature)
        for zone_id, state in self._states.items():
            if state.is_ignited:
                state.burn_duration_ticks += 1
                # Exponential-logistic intensity growth
                state.intensity = min(1.0, state.intensity + effective_growth * (1.0 - state.intensity * 0.2))
                
                # Temperature target proportional to fire intensity
                target_temp = self.ambient_temp_c + (self.max_temp_c - self.ambient_temp_c) * state.intensity
                state.temperature += (target_temp - state.temperature) * 0.25
                next_temperatures[zone_id] = state.temperature
            else:
                # Cooling down towards ambient
                if state.temperature > self.ambient_temp_c:
                    state.temperature -= (state.temperature - self.ambient_temp_c) * self.cooling_rate
                    next_temperatures[zone_id] = state.temperature

        # 2. Inter-zone thermal conduction across adjacent connected edges
        if adjacency_edges:
            for zone_a, zone_b in adjacency_edges:
                if zone_a in self._states and zone_b in self._states:
                    temp_a = self._states[zone_a].temperature
                    temp_b = self._states[zone_b].temperature
                    temp_diff = temp_a - temp_b

                    heat_flow = temp_diff * self.heat_transfer_coeff
                    next_temperatures[zone_a] -= heat_flow * 0.5
                    next_temperatures[zone_b] += heat_flow * 0.5

                    # Spontaneous secondary ignition if adjacent temperature exceeds 150°C
                    if temp_a > 150.0 and not self._states[zone_b].is_ignited:
                        if self._states[zone_a].intensity > 0.4:
                            self.ignite(zone_b, initial_intensity=0.1)

                    if temp_b > 150.0 and not self._states[zone_a].is_ignited:
                        if self._states[zone_b].intensity > 0.4:
                            self.ignite(zone_a, initial_intensity=0.1)

        # Apply next temperatures
        for zone_id, new_temp in next_temperatures.items():
            self._states[zone_id].temperature = max(self.ambient_temp_c, new_temp)

        return self._states

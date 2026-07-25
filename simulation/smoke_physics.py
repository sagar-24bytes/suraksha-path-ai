"""
SurakshaPath AI — Smoke Diffusion Simulation Model.

Implements realistic smoke generation and inter-zone corridor diffusion.
Smoke leads fire — it propagates faster through open doors and connected corridors.

Key Design Principles:
  - Smoke generation is proportional to fire intensity and burn duration.
  - Inter-zone diffusion occurs across adjacent structural edges.
  - Smoke levels decay when fire is extinguished and ventilation occurs.
  - Deterministic step execution given fixed inputs.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Optional
from simulation.fire_physics import ZoneFireState


class SmokePhysicsModel:
    """Smoke generation and inter-room diffusion simulator."""

    def __init__(
        self,
        base_diffusion_rate: float = 0.15,
        smoke_generation_coeff: float = 0.25,
        dissipation_rate: float = 0.02,
    ) -> None:
        """Initialize SmokePhysicsModel.

        Args:
            base_diffusion_rate: Rate at which smoke diffuses to adjacent zones per tick.
            smoke_generation_coeff: Rate at which burning fire generates smoke.
            dissipation_rate: Rate at which smoke clears when fire subsides.
        """
        self.base_diffusion_rate = base_diffusion_rate
        self.smoke_generation_coeff = smoke_generation_coeff
        self.dissipation_rate = dissipation_rate

        self._smoke_levels: Dict[str, float] = {}

    def initialize_zones(self, zone_ids: List[str]) -> None:
        """Initialize or reset smoke levels to 0.0 for all zones."""
        self._smoke_levels = {z_id: 0.0 for z_id in zone_ids}

    def get_smoke_level(self, zone_id: str) -> float:
        """Retrieve current smoke obscuration level (0.0–1.0) for a zone."""
        return self._smoke_levels.get(zone_id, 0.0)

    def get_all_smoke_levels(self) -> Dict[str, float]:
        """Retrieve smoke level dictionary for all zones."""
        return self._smoke_levels

    def set_smoke_level(self, zone_id: str, level: float) -> None:
        """Manually override smoke level for a zone (e.g., scenario event)."""
        if zone_id in self._smoke_levels:
            self._smoke_levels[zone_id] = max(0.0, min(1.0, level))

    def update(
        self,
        fire_states: Dict[str, ZoneFireState],
        adjacency_edges: Optional[List[Tuple[str, str]]] = None,
        diffusion_multiplier: float = 1.0,
    ) -> Dict[str, float]:
        """Advance smoke generation and diffusion by one tick.

        Args:
            fire_states: Dict of ZoneFireState from the FirePhysicsModel.
            adjacency_edges: List of (zone_a, zone_b) physical connections.
            diffusion_multiplier: Scenario modifier for smoke spread speed.

        Returns:
            Dictionary of updated smoke levels (0.0–1.0) per zone.
        """
        effective_diffusion = self.base_diffusion_rate * diffusion_multiplier
        next_smoke = dict(self._smoke_levels)

        # 1. Smoke generation in burning zones
        for zone_id, fire_state in fire_states.items():
            if zone_id not in next_smoke:
                next_smoke[zone_id] = 0.0

            if fire_state.is_ignited and fire_state.intensity > 0.0:
                gen_amount = fire_state.intensity * self.smoke_generation_coeff
                next_smoke[zone_id] = min(1.0, next_smoke[zone_id] + gen_amount)
            else:
                # Gradual smoke dissipation
                if next_smoke[zone_id] > 0.0:
                    next_smoke[zone_id] = max(0.0, next_smoke[zone_id] - self.dissipation_rate)

        # 2. Smoke diffusion across connected edges (high smoke -> low smoke)
        if adjacency_edges:
            delta_smoke: Dict[str, float] = {z: 0.0 for z in next_smoke}
            for zone_a, zone_b in adjacency_edges:
                if zone_a in next_smoke and zone_b in next_smoke:
                    smoke_a = next_smoke[zone_a]
                    smoke_b = next_smoke[zone_b]
                    diff = smoke_a - smoke_b

                    transfer = diff * effective_diffusion * 0.5
                    delta_smoke[zone_a] -= transfer
                    delta_smoke[zone_b] += transfer

            for zone_id, delta in delta_smoke.items():
                next_smoke[zone_id] = max(0.0, min(1.0, next_smoke[zone_id] + delta))

        self._smoke_levels = next_smoke
        return self._smoke_levels

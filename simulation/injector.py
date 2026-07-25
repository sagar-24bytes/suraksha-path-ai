"""
SurakshaPath AI — Simulation Orchestrator & Telemetry Injector.

Orchestrates the Digital Twin simulation pipeline per tick:
  ScenarioEngine → FirePhysicsModel → SmokePhysicsModel → SensorGenerator → FaultInjector → TelemetryPackets

Responsibilities:
  - Advance simulation tick and execute scenario timelines.
  - Advance fire growth and smoke diffusion physics models.
  - Sample physical states and generate canonical TelemetryPacket telemetry.
  - Apply active fault injections (stuck sensors, dead nodes, comm degradation).
  - Return updated TelemetryPacket instances for all building zones.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Optional, Any

from communication.packet_schema import TelemetryPacket
from simulation.fire_physics import FirePhysicsModel, ZoneFireState
from simulation.smoke_physics import SmokePhysicsModel
from simulation.sensor_generator import SensorGenerator
from simulation.fault_injector import FaultInjector, ActiveFault
from simulation.scenario_engine import ScenarioEngine, ScenarioDefinition


class SimulationEngine:
    """Master orchestrator for the Digital Twin physics simulation."""

    def __init__(
        self,
        building_zones: Optional[List[str]] = None,
        adjacency_edges: Optional[List[Tuple[str, str]]] = None,
        scenario_key: str = "kitchen_fire",
        seed: Optional[int] = 42,
    ) -> None:
        """Initialize SimulationEngine.

        Args:
            building_zones: List of zone IDs (e.g. ["R-101", "C-01", "X-01"]).
            adjacency_edges: List of bidirectional (zone_a, zone_b) connection edges.
            scenario_key: Starting scenario identifier.
            seed: Random seed for deterministic simulation output.
        """
        self.building_zones = building_zones or []
        self.adjacency_edges = adjacency_edges or []
        self.seed = seed

        # Sub-components
        self.scenario_engine = ScenarioEngine(scenario_key)
        self.fire_physics = FirePhysicsModel()
        self.smoke_physics = SmokePhysicsModel()
        self.sensor_generator = SensorGenerator(seed=seed)
        self.fault_injector = FaultInjector()

        self._current_tick: int = 0
        self.reset_simulation()

    def reset_simulation(self, scenario_key: Optional[str] = None) -> None:
        """Reset physics models and scenario timeline to tick 0.

        Args:
            scenario_key: Optional new scenario key to load.
        """
        if scenario_key:
            self.scenario_engine.load_scenario(scenario_key)
        else:
            self.scenario_engine.reset()

        self._current_tick = 0
        self.fire_physics.initialize_zones(self.building_zones)
        self.smoke_physics.initialize_zones(self.building_zones)
        self.fault_injector.clear_faults()
        self.sensor_generator.reseed(self.seed)

        # Ignite initial scenario zone
        scenario = self.scenario_engine.current_scenario
        if scenario.ignition_zone in self.building_zones:
            self.fire_physics.ignite(
                scenario.ignition_zone,
                initial_intensity=scenario.initial_intensity,
            )

        # Load scripted faults from scenario
        for event in scenario.events:
            evt_type = event.get("type")
            t_tick = int(event.get("tick", 0))
            z_id = event.get("zone_id", "")
            s_id = event.get("sensor_id", "")

            if evt_type == "COMM_FAIL" and z_id:
                self.fault_injector.add_fault("DEAD_NODE", zone_id=z_id, start_tick=t_tick)
            elif evt_type == "SENSOR_FAIL" and s_id:
                # Extract zone ID from sensor_id (e.g. SM-R-105 -> R-105)
                zone_target = z_id or s_id.split("-", 1)[-1] if "-" in s_id else s_id
                self.fault_injector.add_fault("STUCK_TEMPERATURE", zone_id=zone_target, start_tick=t_tick)

    def load_building_topology(
        self,
        zones: List[str],
        edges: List[Tuple[str, str]],
    ) -> None:
        """Update building layout topology and reset physics models.

        Args:
            zones: List of zone IDs.
            edges: List of bidirectional connection edges.
        """
        self.building_zones = zones
        self.adjacency_edges = edges
        self.reset_simulation()

    def step(self) -> Dict[str, TelemetryPacket]:
        """Advance Digital Twin simulation by one tick.

        Returns:
            Dictionary mapping zone_id to canonical TelemetryPacket.
        """
        # 1. Advance scenario timeline
        tick, firing_events = self.scenario_engine.step()
        self._current_tick = tick
        scenario = self.scenario_engine.current_scenario

        # Process timeline events firing at this tick
        for evt in firing_events:
            evt_type = evt.get("type")
            z_id = evt.get("zone_id", "")

            if evt_type == "IGNITE" and z_id in self.building_zones:
                intensity = float(evt.get("parameters", {}).get("intensity", 0.15))
                self.fire_physics.ignite(z_id, initial_intensity=intensity)

        # 2. Advance Fire and Smoke Physics
        fire_states = self.fire_physics.update(
            adjacency_edges=self.adjacency_edges,
            growth_multiplier=scenario.growth_multiplier,
        )

        smoke_levels = self.smoke_physics.update(
            fire_states=fire_states,
            adjacency_edges=self.adjacency_edges,
            diffusion_multiplier=scenario.diffusion_multiplier,
        )

        # 3. Generate Synthetic Sensor Telemetry Packets
        packets = self.sensor_generator.generate_all_packets(
            fire_states=fire_states,
            smoke_levels=smoke_levels,
            occupancy_map=scenario.initial_occupancy,
            current_tick=float(self._current_tick),
        )

        # 4. Apply Active Fault Injections
        packets = self.fault_injector.apply_faults(packets, current_tick=self._current_tick)

        return packets

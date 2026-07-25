"""
SurakshaPath AI — Digital Twin Simulation Package.

Subsystem 1: Environment modeling, fire & smoke physics, synthetic sensor sampling,
fault injection, and telemetry packet generation.

Exports:
  - FirePhysicsModel, ZoneFireState: Fire growth and thermal transfer physics
  - SmokePhysicsModel: Smoke generation and corridor diffusion physics
  - SensorGenerator: Synthetic telemetry packet generator with configurable noise
  - FaultInjector, ActiveFault: Fault injection framework
  - ScenarioEngine, ScenarioDefinition: Pre-defined fire scenario engine
  - SimulationEngine: Master simulation coordinator / orchestrator
"""

from simulation.fire_physics import FirePhysicsModel, ZoneFireState
from simulation.smoke_physics import SmokePhysicsModel
from simulation.sensor_generator import SensorGenerator
from simulation.fault_injector import FaultInjector, ActiveFault
from simulation.scenario_engine import ScenarioEngine, ScenarioDefinition
from simulation.injector import SimulationEngine

__all__ = [
    "FirePhysicsModel",
    "ZoneFireState",
    "SmokePhysicsModel",
    "SensorGenerator",
    "FaultInjector",
    "ActiveFault",
    "ScenarioEngine",
    "ScenarioDefinition",
    "SimulationEngine",
]

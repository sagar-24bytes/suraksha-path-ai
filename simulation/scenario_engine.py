"""
SurakshaPath AI — Fire Scenario Engine.

Defines and executes reusable fire scenarios (Kitchen Fire, Electrical Fire, Flashover,
Slow Smoldering, Blocked Exit, Server Room Fire, Laboratory Fire).

Responsibilities:
  - Load scenario parameters and timeline events.
  - Expose ignition locations, growth rate modifiers, and initial occupancy profiles.
  - Synchronize scenario events with the simulation timeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ScenarioDefinition:
    """Pre-defined or custom scenario definition.

    Attributes:
        key:                 Unique scenario identifier string.
        name:                Human-readable scenario display name.
        description:         Detailed explanation of what the scenario tests.
        duration_s:          Total scenario duration in seconds.
        ignition_zone:       Zone where fire ignites.
        initial_intensity:   Starting fire intensity (0.01–1.0).
        growth_multiplier:   Fire growth rate multiplier.
        diffusion_multiplier: Smoke spread rate multiplier.
        initial_occupancy:   Dict of zone_id -> occupant count.
        events:              Timed event list [{tick, type, zone_id, ...}].
    """
    key: str
    name: str
    description: str
    duration_s: int = 180
    ignition_zone: str = "R-105"
    initial_intensity: float = 0.15
    growth_multiplier: float = 1.0
    diffusion_multiplier: float = 1.0
    initial_occupancy: Dict[str, int] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)


# Built-in scenarios catalog
BUILTIN_SCENARIOS: Dict[str, ScenarioDefinition] = {
    "kitchen_fire": ScenarioDefinition(
        key="kitchen_fire",
        name="Kitchen Fire",
        description="Cooking fire ignites in Kitchen (R-105). Smoke spreads rapidly through East Corridor (C-02).",
        duration_s=180,
        ignition_zone="R-105",
        initial_intensity=0.15,
        growth_multiplier=1.0,
        diffusion_multiplier=1.2,
        initial_occupancy={"R-101": 4, "R-103": 10, "R-105": 3, "R-201": 2, "L-01": 5},
    ),
    "electrical_room": ScenarioDefinition(
        key="electrical_room",
        name="Electrical Room Fire",
        description="Fast-spreading cable fire in Electrical Room (R-106). High heat threatens Exit X-02.",
        duration_s=150,
        ignition_zone="R-106",
        initial_intensity=0.25,
        growth_multiplier=2.0,
        diffusion_multiplier=1.5,
        initial_occupancy={"R-104": 6, "R-105": 2, "R-106": 1, "R-203": 5},
    ),
    "flashover": ScenarioDefinition(
        key="flashover",
        name="Flashover Event",
        description="Slow smoldering in Server Room (R-201) followed by flashover at t=60s.",
        duration_s=180,
        ignition_zone="R-201",
        initial_intensity=0.05,
        growth_multiplier=0.5,
        diffusion_multiplier=0.8,
        initial_occupancy={"R-201": 2, "R-202": 5, "R-203": 4, "C-03": 0},
    ),
    "slow_smoldering": ScenarioDefinition(
        key="slow_smoldering",
        name="Slow Smoldering Fire",
        description="Smoldering in Conference Room (R-103). High smoke generation with delayed temperature rise.",
        duration_s=180,
        ignition_zone="R-103",
        initial_intensity=0.03,
        growth_multiplier=0.3,
        diffusion_multiplier=1.4,
        initial_occupancy={"R-103": 12, "R-101": 5, "L-01": 6},
    ),
    "blocked_exit": ScenarioDefinition(
        key="blocked_exit",
        name="Blocked Exit & Comm Failure",
        description="Fire in R-104 blocks Main Entrance X-01 at t=30s; comm failure at C-02 at t=60s.",
        duration_s=180,
        ignition_zone="R-104",
        initial_intensity=0.20,
        growth_multiplier=1.2,
        diffusion_multiplier=1.0,
        initial_occupancy={"R-104": 7, "R-101": 5, "L-01": 8},
        events=[
            {"tick": 30, "type": "BLOCK_EXIT", "zone_id": "X-01"},
            {"tick": 60, "type": "COMM_FAIL", "zone_id": "C-02"},
        ],
    ),
    "server_room": ScenarioDefinition(
        key="server_room",
        name="Server Room Fire",
        description="Electrical fire in Floor 2 Server Room (R-201) spreading to Upper Corridor C-03.",
        duration_s=150,
        ignition_zone="R-201",
        initial_intensity=0.20,
        growth_multiplier=1.5,
        diffusion_multiplier=1.0,
        initial_occupancy={"R-201": 2, "R-202": 4, "R-203": 3, "R-204": 4},
    ),
    "laboratory_fire": ScenarioDefinition(
        key="laboratory_fire",
        name="Laboratory Chemical Fire",
        description="High-intensity chemical ignition in R-106 with toxic smoke diffusion.",
        duration_s=120,
        ignition_zone="R-106",
        initial_intensity=0.35,
        growth_multiplier=2.5,
        diffusion_multiplier=2.0,
        initial_occupancy={"R-106": 2, "R-105": 3, "R-104": 4},
    ),
}


class ScenarioEngine:
    """Manages scenario loading and execution timeline."""

    def __init__(self, scenario_key: str = "kitchen_fire") -> None:
        """Initialize ScenarioEngine with a scenario key."""
        self._current_scenario: ScenarioDefinition = self.get_scenario(scenario_key)
        self._current_tick: int = 0

    @classmethod
    def get_scenario(cls, key: str) -> ScenarioDefinition:
        """Retrieve a scenario definition by key, falling back to kitchen_fire."""
        return BUILTIN_SCENARIOS.get(key, BUILTIN_SCENARIOS["kitchen_fire"])

    @classmethod
    def list_scenarios(cls) -> List[Dict[str, str]]:
        """Return list of available scenario metadata ({key, name, description})."""
        return [
            {"key": s.key, "name": s.name, "description": s.description}
            for s in BUILTIN_SCENARIOS.values()
        ]

    @property
    def current_scenario(self) -> ScenarioDefinition:
        """Return active ScenarioDefinition."""
        return self._current_scenario

    def load_scenario(self, scenario_key: str) -> ScenarioDefinition:
        """Load a new active scenario and reset the scenario tick counter."""
        self._current_scenario = self.get_scenario(scenario_key)
        self._current_tick = 0
        return self._current_scenario

    def reset(self) -> None:
        """Reset scenario tick counter."""
        self._current_tick = 0

    def step(self) -> Tuple[int, List[Dict[str, Any]]]:
        """Advance scenario timeline by one tick.

        Returns:
            Tuple of (current_tick, list of events firing at this tick).
        """
        self._current_tick += 1
        firing_events = [
            e for e in self._current_scenario.events
            if e.get("tick") == self._current_tick
        ]
        return self._current_tick, firing_events

"""
SurakshaPath AI — Configuration Loader.

Loads and validates all YAML configuration files.
Returns strongly-typed dataclass instances.

Usage:
    config = load_all_configs()
    building = config.building
    scenarios = config.scenarios
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml

from models import SensorType, ZoneType, SimulationEventType


# =============================================================
# Configuration Dataclasses
# =============================================================

@dataclass
class ZoneConfig:
    """Parsed configuration for a single building zone."""
    id: str
    name: str
    zone_type: ZoneType
    floor: int
    x: float
    y: float
    capacity: int
    is_exit: bool
    sensors: List[SensorType]


@dataclass
class EdgeConfig:
    """Parsed configuration for a connection between two zones."""
    from_zone: str
    to_zone: str
    distance_m: float
    base_weight: float
    has_fire_door: bool


@dataclass
class BuildingConfig:
    """Complete building layout configuration."""
    name: str
    floors: int
    zones: List[ZoneConfig]
    edges: List[EdgeConfig]

    def get_zone(self, zone_id: str) -> Optional[ZoneConfig]:
        """Look up a zone by ID. Returns None if not found."""
        for zone in self.zones:
            if zone.id == zone_id:
                return zone
        return None

    def get_exit_ids(self) -> List[str]:
        """Return IDs of all exit zones."""
        return [z.id for z in self.zones if z.is_exit]

    def get_zones_on_floor(self, floor: int) -> List[ZoneConfig]:
        """Return all zones on a given floor."""
        return [z for z in self.zones if z.floor == floor]

    def get_zone_ids(self) -> List[str]:
        """Return all zone IDs."""
        return [z.id for z in self.zones]


@dataclass
class ScenarioEventConfig:
    """A single timed event within a scenario."""
    tick: int
    event_type: SimulationEventType
    zone_id: Optional[str]
    sensor_id: Optional[str]
    parameters: Dict[str, Any]


@dataclass
class ScenarioConfig:
    """Configuration for a single simulation scenario."""
    key: str
    name: str
    description: str
    duration_s: int
    initial_occupancy: Dict[str, int]
    events: List[ScenarioEventConfig]
    overrides: Dict[str, float]


@dataclass
class ThresholdsConfig:
    """All tunable algorithm parameters."""
    sensor_weights: Dict[str, float]
    hazard_levels: Dict[str, List[float]]
    risk_engine: Dict[str, float]
    failsafe: Dict[str, float]
    sensor_normalization: Dict[str, Any]
    cross_validation: Dict[str, float]
    fire_defaults: Dict[str, Any]


@dataclass
class AppConfig:
    """Application and dashboard settings."""
    title: str
    subtitle: str
    version: str
    tick_interval_s: float
    default_speed: int
    default_scenario: str
    max_history_ticks: int
    max_alerts_display: int
    floor_plan_x_range: List[float]
    floor_plan_y_range: List[float]


@dataclass
class AllConfig:
    """Container holding all loaded configuration."""
    building: BuildingConfig
    scenarios: Dict[str, ScenarioConfig]
    thresholds: ThresholdsConfig
    app: AppConfig


# =============================================================
# Path Resolution
# =============================================================

def _find_config_dir() -> str:
    """Locate the config directory relative to the source tree.

    Handles both:
      - `streamlit run src/dashboard.py` (cwd = project root)
      - Direct execution from src/

    Returns:
        Absolute path to the config directory.

    Raises:
        FileNotFoundError: If the config directory cannot be found.
    """
    # src/ directory is where this file lives
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)
    config_dir = os.path.join(project_root, "config")

    if os.path.isdir(config_dir):
        return config_dir

    # Fallback: maybe cwd is the project root
    cwd_config = os.path.join(os.getcwd(), "config")
    if os.path.isdir(cwd_config):
        return cwd_config

    raise FileNotFoundError(
        f"Configuration directory not found. "
        f"Searched: {config_dir}, {cwd_config}. "
        f"Run from the project root: streamlit run src/dashboard.py"
    )


def _load_yaml(filepath: str) -> Dict:
    """Load a single YAML file with error handling.

    Args:
        filepath: Absolute path to the YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file contains invalid YAML.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Configuration file not found: {filepath}")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {filepath}: {e}") from e

    if data is None:
        raise ValueError(f"Configuration file is empty: {filepath}")

    return data


# =============================================================
# Individual Config Loaders
# =============================================================

def _parse_zone(raw: Dict) -> ZoneConfig:
    """Parse a single zone entry from building.yaml."""
    sensor_types = []
    for s in raw.get("sensors", []):
        try:
            sensor_types.append(SensorType(s))
        except ValueError:
            print(f"  [WARN] Unknown sensor type '{s}' in zone {raw['id']}, skipping.")

    try:
        zone_type = ZoneType(raw["type"])
    except ValueError:
        print(f"  [WARN] Unknown zone type '{raw['type']}' for zone {raw['id']}, defaulting to ROOM.")
        zone_type = ZoneType.ROOM

    return ZoneConfig(
        id=raw["id"],
        name=raw.get("name", raw["id"]),
        zone_type=zone_type,
        floor=int(raw["floor"]),
        x=float(raw["x"]),
        y=float(raw["y"]),
        capacity=int(raw.get("capacity", 0)),
        is_exit=bool(raw.get("is_exit", False)),
        sensors=sensor_types,
    )


def _parse_edge(raw: Dict) -> EdgeConfig:
    """Parse a single edge entry from building.yaml."""
    return EdgeConfig(
        from_zone=raw["from"],
        to_zone=raw["to"],
        distance_m=float(raw.get("distance_m", 5.0)),
        base_weight=float(raw.get("base_weight", 5.0)),
        has_fire_door=bool(raw.get("has_fire_door", False)),
    )


def load_building_config(config_dir: str) -> BuildingConfig:
    """Load and parse building.yaml.

    Args:
        config_dir: Path to the config directory.

    Returns:
        Parsed BuildingConfig instance.
    """
    filepath = os.path.join(config_dir, "building.yaml")
    data = _load_yaml(filepath)

    building_meta = data.get("building", {})
    raw_zones = data.get("zones", [])
    raw_edges = data.get("edges", [])

    zones = [_parse_zone(z) for z in raw_zones]
    edges = [_parse_edge(e) for e in raw_edges]

    # Validation: check that all edge endpoints reference valid zones
    zone_ids = {z.id for z in zones}
    for edge in edges:
        if edge.from_zone not in zone_ids:
            print(f"  [WARN] Edge references unknown zone: {edge.from_zone}")
        if edge.to_zone not in zone_ids:
            print(f"  [WARN] Edge references unknown zone: {edge.to_zone}")

    config = BuildingConfig(
        name=building_meta.get("name", "Unnamed Building"),
        floors=int(building_meta.get("floors", 1)),
        zones=zones,
        edges=edges,
    )

    print(f"  [OK] Building loaded: {config.name}")
    print(f"    {len(zones)} zones, {len(edges)} edges, {config.floors} floors")
    print(f"    Exits: {config.get_exit_ids()}")

    return config


def load_scenarios_config(config_dir: str) -> Dict[str, ScenarioConfig]:
    """Load and parse scenarios.yaml.

    Args:
        config_dir: Path to the config directory.

    Returns:
        Dictionary mapping scenario key to ScenarioConfig.
    """
    filepath = os.path.join(config_dir, "scenarios.yaml")
    data = _load_yaml(filepath)

    raw_scenarios = data.get("scenarios", {})
    scenarios: Dict[str, ScenarioConfig] = {}

    for key, raw in raw_scenarios.items():
        events = []
        for evt in raw.get("events", []):
            try:
                event_type = SimulationEventType(evt["type"])
            except (ValueError, KeyError):
                print(f"  [WARN] Unknown event type in scenario '{key}': {evt.get('type')}")
                continue

            events.append(ScenarioEventConfig(
                tick=int(evt["tick"]),
                event_type=event_type,
                zone_id=evt.get("zone_id"),
                sensor_id=evt.get("sensor_id"),
                parameters=evt.get("parameters", {}),
            ))

        # Sort events by tick to ensure correct execution order
        events.sort(key=lambda e: e.tick)

        scenarios[key] = ScenarioConfig(
            key=key,
            name=raw.get("name", key),
            description=raw.get("description", "").strip(),
            duration_s=int(raw.get("duration_s", 180)),
            initial_occupancy=raw.get("initial_occupancy", {}),
            events=events,
            overrides=raw.get("overrides", {}),
        )

    print(f"  [OK] Scenarios loaded: {list(scenarios.keys())}")
    return scenarios


def load_thresholds_config(config_dir: str) -> ThresholdsConfig:
    """Load and parse thresholds.yaml.

    Args:
        config_dir: Path to the config directory.

    Returns:
        Parsed ThresholdsConfig instance.
    """
    filepath = os.path.join(config_dir, "thresholds.yaml")
    data = _load_yaml(filepath)

    config = ThresholdsConfig(
        sensor_weights=data.get("sensor_weights", {}),
        hazard_levels=data.get("hazard_levels", {}),
        risk_engine=data.get("risk_engine", {}),
        failsafe=data.get("failsafe", {}),
        sensor_normalization=data.get("sensor_normalization", {}),
        cross_validation=data.get("cross_validation", {}),
        fire_defaults=data.get("fire_defaults", {}),
    )

    print(f"  [OK] Thresholds loaded: {len(data)} parameter groups")
    return config


def load_app_config(config_dir: str) -> AppConfig:
    """Load and parse app_config.yaml.

    Args:
        config_dir: Path to the config directory.

    Returns:
        Parsed AppConfig instance.
    """
    filepath = os.path.join(config_dir, "app_config.yaml")
    data = _load_yaml(filepath)

    app_data = data.get("app", {})
    sim_data = data.get("simulation", {})
    dash_data = data.get("dashboard", {})

    config = AppConfig(
        title=app_data.get("title", "SurakshaPath AI"),
        subtitle=app_data.get("subtitle", ""),
        version=app_data.get("version", "0.0.0"),
        tick_interval_s=float(sim_data.get("tick_interval_s", 1.0)),
        default_speed=int(sim_data.get("default_speed", 1)),
        default_scenario=sim_data.get("default_scenario", "kitchen_fire"),
        max_history_ticks=int(dash_data.get("max_history_ticks", 120)),
        max_alerts_display=int(dash_data.get("max_alerts_display", 50)),
        floor_plan_x_range=dash_data.get("floor_plan_x_range", [0, 15]),
        floor_plan_y_range=dash_data.get("floor_plan_y_range", [0, 10]),
    )

    print(f"  [OK] App config loaded: {config.title} v{config.version}")
    return config


# =============================================================
# Master Loader
# =============================================================

def load_all_configs(config_dir: Optional[str] = None) -> AllConfig:
    """Load all configuration files and return a unified config object.

    Args:
        config_dir: Optional explicit path to the config directory.
                    If None, auto-detects from the project structure.

    Returns:
        AllConfig instance with all parsed configuration.

    Raises:
        FileNotFoundError: If config directory or files are missing.
        ValueError: If any YAML file is malformed.
    """
    if config_dir is None:
        config_dir = _find_config_dir()

    print(f"\n[LOAD] Loading configuration from: {config_dir}")

    building = load_building_config(config_dir)
    scenarios = load_scenarios_config(config_dir)
    thresholds = load_thresholds_config(config_dir)
    app = load_app_config(config_dir)

    print(f"[OK] All configuration loaded successfully.\n")

    return AllConfig(
        building=building,
        scenarios=scenarios,
        thresholds=thresholds,
        app=app,
    )

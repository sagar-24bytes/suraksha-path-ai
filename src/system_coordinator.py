"""
SurakshaPath AI — System Coordinator & Integration Bridge.

Orchestrates live runtime interaction between all 5 subsystems:
  1. Digital Twin Simulation (simulation/injector.py)
  2. Transport Abstraction (communication/mock_transport.py)
  3. Shared Routing Subsystem (routing/path_manager.py)
  4. MicroPython Firmware Nodes (firmware/micropython/main.py)
  5. Fire Commander Dashboard (src/dashboard.py)

Flow per tick:
  SimulationEngine.step() → MockTransport.publish() → TelemetryHazardProvider.update()
  → DefaultRouteManager.calculate_all_routes() → FirmwareNode.update_mock_environment() & step()
  → Fused Telemetry Published → Dashboard UI State
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Any

from config_loader import load_all_configs, AllConfig
from communication.packet_schema import TelemetryPacket, HEALTH_HEALTHY
from communication.mock_transport import MockTransport
from simulation.injector import SimulationEngine
from routing.graph import BuildingGraph, Node, Edge
from routing.hazard_model import TelemetryHazardProvider, HazardSnapshot
from routing.edge_weight import DynamicEdgeWeightCalculator
from routing.path_manager import DefaultRouteManager, RouteRequest, RouteResult
from firmware.micropython.main import FirmwareNode

logger = logging.getLogger(__name__)


class SystemCoordinator:
    """Master system coordinator integrating all 5 subsystems."""

    def __init__(self, scenario_key: str = "kitchen_fire", config_dir: Optional[str] = None) -> None:
        """Initialize SystemCoordinator and load all configurations.

        Args:
            scenario_key: Initial scenario identifier.
            config_dir: Optional path to config directory.
        """
        self.config: AllConfig = load_all_configs(config_dir)
        self.scenario_key = scenario_key
        
        # 1. Initialize Communication Layer
        self.transport = MockTransport(name="CommanderTransport")
        self.transport.connect()

        # 2. Build BuildingGraph topology from YAML config
        self.graph = BuildingGraph(name=self.config.building.name)
        self._build_graph_topology()

        # 3. Initialize Simulation Subsystem
        zones = [z.id for z in self.config.building.zones]
        edges = [(e.from_zone, e.to_zone) for e in self.config.building.edges]
        self.simulation = SimulationEngine(
            building_zones=zones,
            adjacency_edges=edges,
            scenario_key=scenario_key,
            seed=42,
        )

        # 4. Initialize Shared Routing Subsystem
        self.hazard_provider = TelemetryHazardProvider()
        self.weight_calculator = DynamicEdgeWeightCalculator()
        self.route_manager = DefaultRouteManager(
            graph=self.graph,
            hazard_provider=self.hazard_provider,
            weight_calculator=self.weight_calculator,
            enable_cache=True,
        )

        # 5. Initialize MicroPython Firmware Nodes (one per zone)
        self.firmware_nodes: Dict[str, FirmwareNode] = {
            z.id: FirmwareNode(zone_id=z.id, transport=self.transport)
            for z in self.config.building.zones
        }

        # Runtime State Cache
        self.current_tick: int = 0
        self.latest_telemetry: Dict[str, TelemetryPacket] = {}
        self.latest_routes: Dict[str, RouteResult] = {}
        self.alerts_history: List[Dict[str, Any]] = []
        self._alerted_zones: Dict[str, set] = {}  # category -> set of zone_ids already alerted

        # Run initial tick 0 setup
        self._initial_setup()

    def _build_graph_topology(self) -> None:
        """Populate BuildingGraph from building.yaml configuration."""
        for z in self.config.building.zones:
            node = Node(
                id=z.id,
                name=z.name,
                floor=z.floor,
                x=z.x,
                y=z.y,
                is_exit=z.is_exit,
                capacity=z.capacity,
            )
            self.graph.add_node(node)

        for e in self.config.building.edges:
            edge = Edge(
                from_node=e.from_zone,
                to_node=e.to_zone,
                distance_m=e.distance_m,
                base_weight=e.base_weight,
                has_fire_door=e.has_fire_door,
            )
            self.graph.add_edge(edge, bidirectional=True)

    def _initial_setup(self) -> None:
        """Perform initial telemetry sampling and route calculation."""
        self.latest_telemetry = self.simulation.step()
        self.hazard_provider.update_telemetry(self.latest_telemetry, timestamp=0.0)
        self.latest_routes = self.route_manager.calculate_all_routes()
        self._add_alert("SYSTEM", "SurakshaPath AI Platform Initialized cleanly.", "INFO")

    def load_scenario(self, scenario_key: str) -> None:
        """Switch scenario and reset system tick counter."""
        self.scenario_key = scenario_key
        self.simulation.reset_simulation(scenario_key)
        self.current_tick = 0
        self.latest_telemetry = self.simulation.step()
        self.hazard_provider.update_telemetry(self.latest_telemetry, timestamp=0.0)
        self.latest_routes = self.route_manager.calculate_all_routes()
        self._alerted_zones = {}
        self._add_alert("SCENARIO", f"Loaded Scenario: {scenario_key.upper().replace('_', ' ')}", "WARNING")

    def reset(self) -> None:
        """Reset current scenario to tick 0."""
        self.load_scenario(self.scenario_key)

    def step(self) -> Dict[str, Any]:
        """Advance the entire system pipeline by 1 tick (1.0s).

        Pipeline Flow:
          Simulation Engine -> Raw Telemetry -> Hazard Provider -> Dynamic Routing
          -> MicroPython Firmware Nodes -> Fused Telemetry Packets -> Dashboard State

        Returns:
            Dict containing tick, telemetry, routes, alerts, and system_health.
        """
        self.current_tick += 1

        # 1. Advance Simulation Physics & sample raw noisy telemetry
        raw_packets = self.simulation.step()

        # 2. Publish raw packets to Communication Layer
        for zone_id, pkt in raw_packets.items():
            self.transport.publish(f"suraksha/telemetry/{zone_id}", pkt)

        # 3. Update Routing Subsystem Hazard Provider
        self.hazard_provider.update_telemetry(raw_packets, timestamp=float(self.current_tick))

        # 4. Calculate Dynamic Evacuation Routes for all non-exit zones
        self.latest_routes = self.route_manager.calculate_all_routes()

        # 5. Execute MicroPython Firmware Nodes (poll, fusion, LEDs, diagnostics)
        fused_packets: Dict[str, TelemetryPacket] = {}
        for zone_id, fw_node in self.firmware_nodes.items():
            raw_pkt = raw_packets.get(zone_id)
            if raw_pkt:
                fw_node.update_mock_environment(
                    temperature=raw_pkt.temperature,
                    smoke_level=raw_pkt.smoke_level,
                    flame_detected=raw_pkt.flame_detected,
                    occupancy_count=raw_pkt.occupancy_count,
                )
                
                # Check for exit assignment from routing
                assigned_route = self.latest_routes.get(zone_id)
                if assigned_route and assigned_route.is_shelter_in_place:
                    fw_node.led_ctrl.set_blocked(True)
                else:
                    fw_node.led_ctrl.set_blocked(False)

                # Step firmware clock by 500ms
                fused_pkt = fw_node.step(500)
                if fused_pkt:
                    fused_packets[zone_id] = fused_pkt

        # Fallback to raw if firmware not stepped
        self.latest_telemetry = fused_packets if fused_packets else raw_packets

        # 6. Generate Alerts based on telemetry & route changes
        self._check_alerts()

        return {
            "tick": self.current_tick,
            "telemetry": self.latest_telemetry,
            "routes": self.latest_routes,
            "alerts": self.alerts_history,
            "health": self.get_system_health(),
        }

    def _check_alerts(self) -> None:
        """Scan telemetry & routes for meaningful state-change alerts.
        
        Only generates alerts when conditions genuinely change.
        Avoids repetitive per-tick spam for the same zone/category.
        """
        for zone_id, pkt in self.latest_telemetry.items():
            # Fire detection — alert once per zone
            if pkt.flame_detected and pkt.hazard_score >= 0.6:
                if not self._zone_already_alerted("FIRE_ACTIVE", zone_id):
                    self._mark_zone_alerted("FIRE_ACTIVE", zone_id)
                    self._add_alert("FIRE", f"Fire detected in Zone {zone_id} (Temp: {pkt.temperature:.0f}\u00b0C)", "DANGER")

            # Smoke threshold crossing — alert once per zone
            if pkt.smoke_level >= 0.25 and not self._zone_already_alerted("SMOKE_WARN", zone_id):
                self._mark_zone_alerted("SMOKE_WARN", zone_id)
                self._add_alert("SMOKE", f"Smoke detected in Zone {zone_id} ({pkt.smoke_level * 100:.0f}% obscuration)", "WARNING")

            # Heavy smoke — alert once per zone
            if pkt.smoke_level >= 0.7 and not self._zone_already_alerted("SMOKE_HEAVY", zone_id):
                self._mark_zone_alerted("SMOKE_HEAVY", zone_id)
                self._add_alert("SMOKE", f"Heavy smoke obscuration in Zone {zone_id} ({pkt.smoke_level * 100:.0f}%)", "DANGER")

            # Hazard elevation — alert once per zone
            if pkt.hazard_score >= 0.40 and not self._zone_already_alerted("HAZARD_ELEVATED", zone_id):
                self._mark_zone_alerted("HAZARD_ELEVATED", zone_id)
                self._add_alert("HAZARD", f"Hazard elevated in Zone {zone_id} (score: {pkt.hazard_score:.2f}, state: {pkt.evacuation_state})", "WARNING")

            # Node health — alert once per zone
            if pkt.node_health != HEALTH_HEALTHY and not self._zone_already_alerted("NODE_HEALTH", zone_id):
                self._mark_zone_alerted("NODE_HEALTH", zone_id)
                self._add_alert("HEALTH", f"Node {pkt.node_id} reported {pkt.node_health} status", "WARNING")

        # Shelter-In-Place — alert once per combination
        sheltered_zones = [z_id for z_id, r in self.latest_routes.items() if r.is_shelter_in_place]
        if sheltered_zones:
            shelter_key = ",".join(sorted(sheltered_zones))
            if not self._zone_already_alerted("SHELTER", shelter_key):
                self._mark_zone_alerted("SHELTER", shelter_key)
                self._add_alert("EVACUATION", f"\U0001f6a8 SHELTER IN PLACE for zones: {', '.join(sheltered_zones)}", "CRITICAL")

    def _zone_already_alerted(self, category: str, zone_id: str) -> bool:
        """Check if a zone has already fired a specific alert category."""
        return zone_id in self._alerted_zones.get(category, set())

    def _mark_zone_alerted(self, category: str, zone_id: str) -> None:
        """Mark a zone as having fired a specific alert category."""
        if category not in self._alerted_zones:
            self._alerted_zones[category] = set()
        self._alerted_zones[category].add(zone_id)

    def _add_alert(self, category: str, message: str, level: str) -> None:
        """Add an alert entry to the chronological log.
        
        Deduplicates by checking the most recent alert (position 0).
        """
        # Avoid exact duplicate of the most recent alert
        if self.alerts_history and self.alerts_history[0]["message"] == message:
            return
        
        self.alerts_history.insert(0, {
            "tick": self.current_tick,
            "category": category,
            "message": message,
            "level": level,
        })
        # Keep last 50 alerts
        if len(self.alerts_history) > 50:
            self.alerts_history.pop()

    def get_system_health(self) -> Dict[str, str]:
        """Compute overall 5-aspect system health matrix."""
        return {
            "Simulation": "Healthy" if self.simulation else "Critical",
            "Communication": "Healthy" if self.transport.is_connected else "Critical",
            "Routing": "Healthy" if self.route_manager else "Critical",
            "Firmware": "Healthy" if all(n.diag_mgr.node_health == HEALTH_HEALTHY for n in self.firmware_nodes.values()) else "Warning",
            "Dashboard": "Healthy",
        }

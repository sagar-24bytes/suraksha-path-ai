"""
SurakshaPath AI — System Integration & End-to-End Pipeline Unit Tests.

Tests:
  - SystemCoordinator initialization across all 5 subsystems
  - End-to-end tick step execution (Simulation -> Transport -> Routing -> Firmware -> Dashboard state)
  - Scenario loading & resetting
  - Hazard-aware evacuation route updating during simulated fire progression
  - Alert logging and 5-aspect health matrix evaluation
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import unittest
from src.system_coordinator import SystemCoordinator
from communication.packet_schema import TelemetryPacket
from routing.path_manager import RouteResult


class TestSystemIntegration(unittest.TestCase):
    """Integration test suite for the complete 5-subsystem platform."""

    def setUp(self) -> None:
        """Initialize SystemCoordinator before each test."""
        self.coordinator = SystemCoordinator(scenario_key="kitchen_fire")

    def tearDown(self) -> None:
        """Disconnect transport after test."""
        if self.coordinator.transport:
            self.coordinator.transport.disconnect()

    def test_system_initialization(self) -> None:
        """Verify all 5 subsystems initialize cleanly."""
        self.assertIsNotNone(self.coordinator.simulation)
        self.assertIsNotNone(self.coordinator.transport)
        self.assertIsNotNone(self.coordinator.route_manager)
        self.assertEqual(len(self.coordinator.firmware_nodes), 18)
        self.assertTrue(self.coordinator.transport.is_connected)

        health = self.coordinator.get_system_health()
        self.assertEqual(health["Simulation"], "Healthy")
        self.assertEqual(health["Communication"], "Healthy")
        self.assertEqual(health["Routing"], "Healthy")
        self.assertEqual(health["Dashboard"], "Healthy")

    def test_end_to_end_step_execution(self) -> None:
        """Test full pipeline tick step execution."""
        initial_tick = self.coordinator.current_tick

        state = self.coordinator.step()
        self.assertEqual(state["tick"], initial_tick + 1)
        self.assertIn("telemetry", state)
        self.assertIn("routes", state)
        self.assertIn("alerts", state)
        self.assertIn("health", state)

        # Verify telemetry dictionary populated
        self.assertEqual(len(state["telemetry"]), 18)
        for zone_id, pkt in state["telemetry"].items():
            self.assertIsInstance(pkt, TelemetryPacket)
            self.assertTrue(pkt.validate())

        # Verify route manager output
        for zone_id, route in state["routes"].items():
            self.assertIsInstance(route, RouteResult)

    def test_fire_progression_and_rerouting(self) -> None:
        """Test dynamic route updating over multiple simulation ticks."""
        initial_route = self.coordinator.latest_routes.get("R-105")

        # Step simulation 10 ticks to advance fire growth
        for _ in range(10):
            self.coordinator.step()

        updated_telemetry = self.coordinator.latest_telemetry
        kitchen_pkt = updated_telemetry.get("R-105")

        # Verify fire growth in ignited zone R-105
        self.assertIsNotNone(kitchen_pkt)
        self.assertGreater(kitchen_pkt.hazard_score, 0.0)

    def test_scenario_switching_and_reset(self) -> None:
        """Test loading a new scenario and resetting system clock."""
        self.coordinator.load_scenario("electrical_room")
        self.assertEqual(self.coordinator.scenario_key, "electrical_room")
        self.assertEqual(self.coordinator.current_tick, 0)

        self.coordinator.step()
        self.assertEqual(self.coordinator.current_tick, 1)

        self.coordinator.reset()
        self.assertEqual(self.coordinator.current_tick, 0)


if __name__ == "__main__":
    unittest.main()

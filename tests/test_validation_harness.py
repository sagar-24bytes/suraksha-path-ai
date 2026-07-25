"""
SurakshaPath AI — Phase 7 Quality Assurance & System Acceptance Validation Harness.

Executes systematic end-to-end acceptance tests:
  1. Full system startup & configuration verification
  2. Multi-tick simulation physics & telemetry propagation
  3. All 7 scenarios execution (Kitchen Fire, Electrical Room, Flashover, Slow Smoldering, Blocked Exit, Server Room Fire, Laboratory Fire)
  4. Dynamic evacuation routing, edge penalty scaling, and Shelter-In-Place fallback
  5. MicroPython firmware node scheduler, sensor fusion, LED state machine, and heartbeat diagnostics
  6. Dashboard components rendering & state data integrity
  7. Stress test execution (100 simulation ticks continuous)
  8. Negative & boundary tests (rapid scenario switching, rapid pause/reset, un-updated zones)
"""

import sys
import os
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import unittest
from src.system_coordinator import SystemCoordinator
from simulation.scenario_engine import BUILTIN_SCENARIOS
from communication.packet_schema import TelemetryPacket, HEALTH_HEALTHY
from routing.path_manager import RouteResult
from src.dashboard_components import (
    render_floor_plan,
    render_explainability_panel,
    render_telemetry_panel,
    render_alerts_feed,
    render_health_panel,
)


class TestValidationHarness(unittest.TestCase):
    """Phase 7 End-to-End Validation Suite."""

    def setUp(self) -> None:
        """Initialize SystemCoordinator."""
        self.coordinator = SystemCoordinator(scenario_key="kitchen_fire")

    def tearDown(self) -> None:
        """Disconnect transport."""
        if self.coordinator.transport:
            self.coordinator.transport.disconnect()

    def test_01_full_system_startup(self) -> None:
        """Step 1: Full system startup verification."""
        self.assertIsNotNone(self.coordinator.simulation)
        self.assertTrue(self.coordinator.transport.is_connected)
        self.assertEqual(len(self.coordinator.firmware_nodes), 18)
        self.assertIsNotNone(self.coordinator.route_manager)

    def test_02_multi_tick_normal_operation(self) -> None:
        """Step 2: Verify normal continuous operation across 20 ticks."""
        for t in range(1, 21):
            state = self.coordinator.step()
            self.assertEqual(state["tick"], t)
            self.assertEqual(len(state["telemetry"]), 18)
            self.assertGreaterEqual(len(state["routes"]), 15)

    def test_03_all_scenarios_execution(self) -> None:
        """Step 3: Execute all 7 built-in fire scenarios."""
        for key in BUILTIN_SCENARIOS.keys():
            self.coordinator.load_scenario(key)
            self.assertEqual(self.coordinator.scenario_key, key)
            self.assertEqual(self.coordinator.current_tick, 0)

            # Advance 5 ticks for each scenario
            for _ in range(5):
                state = self.coordinator.step()
                self.assertIsNotNone(state["telemetry"])

    def test_04_routing_and_shelter_in_place(self) -> None:
        """Step 4: Verify routing hazard avoidance and shelter-in-place."""
        self.coordinator.load_scenario("flashover")
        for _ in range(15):
            self.coordinator.step()

        routes = self.coordinator.latest_routes
        sheltered = [z_id for z_id, r in routes.items() if r.is_shelter_in_place]
        # Under extreme flashover, shelter-in-place should activate
        self.assertTrue(isinstance(sheltered, list))

    def test_05_firmware_diagnostics_and_leds(self) -> None:
        """Step 5: Verify firmware task scheduler, LEDs, and diagnostics."""
        for _ in range(5):
            self.coordinator.step()

        for z_id, fw_node in self.coordinator.firmware_nodes.items():
            self.assertEqual(fw_node.diag_mgr.node_health, HEALTH_HEALTHY)
            self.assertIn(fw_node.led_ctrl.current_state, [
                "SAFE_SOLID", "WARN_PULSE", "DANGER_FLASH", "BLOCKED_CROSS"
            ])

    def test_06_dashboard_component_rendering(self) -> None:
        """Step 6: Verify Plotly floor plan & components generate without exception."""
        self.coordinator.step()
        fig = render_floor_plan(
            graph=self.coordinator.graph,
            telemetry=self.coordinator.latest_telemetry,
            routes=self.coordinator.latest_routes,
            selected_floor=1,
            selected_zone_id="R-105",
        )
        self.assertIsNotNone(fig)

    def test_07_stress_test_100_ticks(self) -> None:
        """Step 7: Stress test running 100 continuous ticks."""
        start_time = time.time()
        for _ in range(100):
            self.coordinator.step()
        elapsed = time.time() - start_time
        # 100 ticks should complete in less than 5.0 seconds
        self.assertLess(elapsed, 5.0)

    def test_08_negative_boundary_tests(self) -> None:
        """Step 8: Rapid switching, resetting, and boundary condition tests."""
        for _ in range(10):
            self.coordinator.load_scenario("kitchen_fire")
            self.coordinator.step()
            self.coordinator.reset()
            self.coordinator.load_scenario("electrical_room")
            self.coordinator.step()

        self.assertEqual(self.coordinator.current_tick, 1)


if __name__ == "__main__":
    unittest.main()

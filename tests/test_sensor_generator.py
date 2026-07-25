"""
SurakshaPath AI — Sensor Generator & Fault Injector Unit Tests.

Tests:
  - Synthetic TelemetryPacket generation from physical states
  - Seeded random generator determinism
  - Optical flame sensor trip threshold
  - FaultInjector active rule matching & packet mutation
  - Full SimulationEngine step execution
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
from communication.packet_schema import TelemetryPacket, HEALTH_OFFLINE, HEALTH_TIMEDOUT
from simulation.fire_physics import ZoneFireState
from simulation.sensor_generator import SensorGenerator
from simulation.fault_injector import FaultInjector
from simulation.injector import SimulationEngine


class TestSensorGeneratorAndFaultInjector(unittest.TestCase):
    """Unit test suite for SensorGenerator, FaultInjector, and SimulationEngine."""

    def setUp(self) -> None:
        """Initialize components before each test."""
        self.generator = SensorGenerator(seed=12345)
        self.fault_injector = FaultInjector()

    def test_sensor_packet_generation(self) -> None:
        """Test canonical TelemetryPacket generation."""
        fire_state = ZoneFireState(zone_id="R-105", intensity=0.5, temperature=120.0, is_ignited=True)
        pkt = self.generator.generate_packet(
            zone_id="R-105",
            fire_state=fire_state,
            smoke_level=0.4,
            occupancy_count=3,
            current_tick=10.0,
        )

        self.assertIsInstance(pkt, TelemetryPacket)
        self.assertEqual(pkt.zone_id, "R-105")
        self.assertEqual(pkt.node_id, "NODE-R-105")
        self.assertEqual(pkt.occupancy_count, 3)
        self.assertEqual(pkt.timestamp, 10.0)
        self.assertTrue(pkt.flame_detected)
        self.assertTrue(pkt.validate())

    def test_deterministic_seed_behavior(self) -> None:
        """Test that same seed produces identical noisy output."""
        gen1 = SensorGenerator(seed=999)
        gen2 = SensorGenerator(seed=999)

        fire = ZoneFireState(zone_id="R-101", intensity=0.2, temperature=40.0)
        pkt1 = gen1.generate_packet("R-101", fire, smoke_level=0.1)
        pkt2 = gen2.generate_packet("R-101", fire, smoke_level=0.1)

        self.assertEqual(pkt1.temperature, pkt2.temperature)
        self.assertEqual(pkt1.smoke_level, pkt2.smoke_level)

    def test_fault_injection_stuck_temperature(self) -> None:
        """Test STUCK_TEMPERATURE fault injection."""
        self.fault_injector.add_fault("STUCK_TEMPERATURE", zone_id="R-101", start_tick=5, value=99.9)

        fire = ZoneFireState(zone_id="R-101", temperature=25.0)
        pkt = self.generator.generate_packet("R-101", fire, smoke_level=0.0)
        packets = {"R-101": pkt}

        # Before start tick (tick 2) -> fault inactive
        packets_tick2 = self.fault_injector.apply_faults(dict(packets), current_tick=2)
        self.assertNotEqual(packets_tick2["R-101"].temperature, 99.9)

        # On or after start tick (tick 5) -> fault active
        packets_tick5 = self.fault_injector.apply_faults(dict(packets), current_tick=5)
        self.assertEqual(packets_tick5["R-101"].temperature, 99.9)
        self.assertEqual(packets_tick5["R-101"].metadata.get("injected_fault"), "STUCK_TEMPERATURE")

    def test_fault_injection_dead_node(self) -> None:
        """Test DEAD_NODE fault injection."""
        self.fault_injector.add_fault("DEAD_NODE", zone_id="R-102", start_tick=1)

        fire = ZoneFireState(zone_id="R-102", temperature=25.0)
        pkt = self.generator.generate_packet("R-102", fire, smoke_level=0.0)
        packets = {"R-102": pkt}

        mutated = self.fault_injector.apply_faults(packets, current_tick=1)
        self.assertEqual(mutated["R-102"].node_health, HEALTH_OFFLINE)
        self.assertEqual(mutated["R-102"].communication_health, HEALTH_TIMEDOUT)

    def test_simulation_engine_integration_step(self) -> None:
        """Test full SimulationEngine pipeline step."""
        zones = ["R-101", "C-01", "X-01"]
        edges = [("R-101", "C-01"), ("C-01", "X-01")]
        
        sim = SimulationEngine(
            building_zones=zones,
            adjacency_edges=edges,
            scenario_key="kitchen_fire",
            seed=42,
        )

        packets = sim.step()
        self.assertIsInstance(packets, dict)
        self.assertEqual(len(packets), 3)

        for z_id in zones:
            self.assertIn(z_id, packets)
            self.assertIsInstance(packets[z_id], TelemetryPacket)
            self.assertTrue(packets[z_id].validate())


if __name__ == "__main__":
    unittest.main()

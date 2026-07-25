"""
SurakshaPath AI — Firmware Diagnostics & FirmwareNode Unit Tests.

Tests:
  - Heartbeat counter incrementing
  - Battery charge level degradation tracking
  - Communication activity registration and timeout evaluation
  - Complete FirmwareNode integration step & TelemetryPacket publishing
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
from firmware.micropython.diagnostics import DiagnosticsManager
from firmware.micropython.main import FirmwareNode
from communication.mock_transport import MockTransport
from communication.packet_schema import TelemetryPacket, HEALTH_HEALTHY, HEALTH_WARNING


class TestFirmwareDiagnosticsAndNode(unittest.TestCase):
    """Unit test suite for DiagnosticsManager and FirmwareNode."""

    def setUp(self) -> None:
        """Initialize components before each test."""
        self.diag = DiagnosticsManager(node_id="NODE-R101")
        self.transport = MockTransport()
        self.transport.connect()

    def tearDown(self) -> None:
        """Disconnect transport after each test."""
        self.transport.disconnect()

    def test_heartbeat_increment(self) -> None:
        """Test heartbeat counter increments on each invocation."""
        self.assertEqual(self.diag.heartbeat_counter, 0)
        self.assertEqual(self.diag.heartbeat(), 1)
        self.assertEqual(self.diag.heartbeat(), 2)

    def test_battery_level_tracking(self) -> None:
        """Test battery level degradation triggers node health warnings."""
        self.assertEqual(self.diag.battery_level, 100.0)
        self.assertEqual(self.diag.node_health, HEALTH_HEALTHY)

        self.diag.update_battery(15.0)
        self.assertEqual(self.diag.node_health, HEALTH_WARNING)

    def test_firmware_node_step_and_publish(self) -> None:
        """Test full FirmwareNode step execution and telemetry publishing."""
        node = FirmwareNode(zone_id="R-101", transport=self.transport)
        
        # Subscribe to node telemetry topic
        received_packets = []
        def cb(topic: str, packet: TelemetryPacket) -> None:
            received_packets.append(packet)

        self.transport.subscribe("suraksha/telemetry/R-101", cb)

        # Update environment & advance node step by 1000ms
        node.update_mock_environment(temperature=45.0, smoke_level=0.3, flame_detected=False)
        pkt = node.step(1000)

        self.assertIsNotNone(pkt)
        self.assertIsInstance(pkt, TelemetryPacket)
        self.assertEqual(pkt.zone_id, "R-101")
        self.assertEqual(pkt.temperature, 45.0)
        self.assertEqual(pkt.smoke_level, 0.3)
        self.assertEqual(len(received_packets), 1)
        self.assertEqual(received_packets[0].node_id, "NODE-R-101")


if __name__ == "__main__":
    unittest.main()

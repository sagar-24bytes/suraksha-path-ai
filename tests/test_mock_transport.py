"""
SurakshaPath AI — MockTransport Unit Tests.

Tests:
  - Connect and disconnect lifecycle
  - Single publisher and subscriber packet delivery
  - Multiple subscribers receiving same publication
  - Topic pattern matching (exact topics vs wildcard '#')
  - Unsubscribe functionality
  - Interface compliance checks
"""

import sys
import os

# Add project root and src/ to sys.path for test imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import unittest
from communication.interface import CommunicationInterface
from communication.packet_schema import TelemetryPacket
from communication.mock_transport import MockTransport


class TestMockTransport(unittest.TestCase):
    """Unit test suite for MockTransport and CommunicationInterface compliance."""

    def setUp(self) -> None:
        """Initialize a connected MockTransport before each test."""
        self.transport = MockTransport(name="TestMockTransport")
        self.transport.connect()

    def tearDown(self) -> None:
        """Disconnect transport after each test."""
        self.transport.disconnect()

    def test_interface_compliance(self) -> None:
        """Verify MockTransport inherits from CommunicationInterface."""
        self.assertIsInstance(self.transport, CommunicationInterface)

    def test_connect_disconnect_lifecycle(self) -> None:
        """Test connection status toggles."""
        t = MockTransport()
        self.assertFalse(t.is_connected)
        self.assertTrue(t.connect())
        self.assertTrue(t.is_connected)
        self.assertTrue(t.disconnect())
        self.assertFalse(t.is_connected)

    def test_single_publish_subscribe(self) -> None:
        """Test publishing a packet to a subscribed topic."""
        received_packets = []

        def callback(topic: str, packet: TelemetryPacket) -> None:
            received_packets.append((topic, packet))

        topic = "suraksha/telemetry/R-101"
        self.transport.subscribe(topic, callback)

        pkt = TelemetryPacket(node_id="NODE-101", zone_id="R-101", temperature=35.0)
        published = self.transport.publish(topic, pkt)

        self.assertTrue(published)
        self.assertEqual(len(received_packets), 1)
        self.assertEqual(received_packets[0][0], topic)
        self.assertEqual(received_packets[0][1].node_id, "NODE-101")
        self.assertEqual(received_packets[0][1].temperature, 35.0)

    def test_multiple_subscribers(self) -> None:
        """Test multiple subscribers receiving the same published packet."""
        sub1_hits = []
        sub2_hits = []

        def cb1(t: str, p: TelemetryPacket) -> None:
            sub1_hits.append(p)

        def cb2(t: str, p: TelemetryPacket) -> None:
            sub2_hits.append(p)

        topic = "suraksha/telemetry/R-105"
        self.transport.subscribe(topic, cb1)
        self.transport.subscribe(topic, cb2)

        pkt = TelemetryPacket(node_id="NODE-105", zone_id="R-105", hazard_score=0.75)
        self.transport.publish(topic, pkt)

        self.assertEqual(len(sub1_hits), 1)
        self.assertEqual(len(sub2_hits), 1)
        self.assertEqual(sub1_hits[0].hazard_score, 0.75)
        self.assertEqual(sub2_hits[0].hazard_score, 0.75)

    def test_wildcard_topic_matching(self) -> None:
        """Test wildcard '#' topic subscription."""
        wildcard_hits = []

        def wildcard_cb(t: str, p: TelemetryPacket) -> None:
            wildcard_hits.append((t, p))

        self.transport.subscribe("suraksha/telemetry/#", wildcard_cb)

        pkt1 = TelemetryPacket(node_id="NODE-101", zone_id="R-101")
        pkt2 = TelemetryPacket(node_id="NODE-102", zone_id="R-102")

        self.transport.publish("suraksha/telemetry/R-101", pkt1)
        self.transport.publish("suraksha/telemetry/R-102", pkt2)

        self.assertEqual(len(wildcard_hits), 2)
        self.assertEqual(wildcard_hits[0][0], "suraksha/telemetry/R-101")
        self.assertEqual(wildcard_hits[1][0], "suraksha/telemetry/R-102")

    def test_unsubscribe(self) -> None:
        """Test unsubscribing a callback."""
        received = []

        def cb(t: str, p: TelemetryPacket) -> None:
            received.append(p)

        topic = "suraksha/telemetry/S-01"
        self.transport.subscribe(topic, cb)
        self.transport.publish(topic, TelemetryPacket(node_id="S-01"))
        self.assertEqual(len(received), 1)

        # Unsubscribe
        self.transport.unsubscribe(topic, cb)
        self.transport.publish(topic, TelemetryPacket(node_id="S-01"))
        self.assertEqual(len(received), 1)  # No new messages received

    def test_publish_when_disconnected(self) -> None:
        """Test that publish fails when transport is disconnected."""
        self.transport.disconnect()
        pkt = TelemetryPacket()
        result = self.transport.publish("test/topic", pkt)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()

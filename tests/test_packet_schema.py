"""
SurakshaPath AI — TelemetryPacket Schema Unit Tests.

Tests:
  - Default initialization & custom fields
  - Schema versioning (schema_version = "1.0")
  - Dictionary serialization / deserialization roundtrip
  - JSON serialization / deserialization roundtrip
  - Packet validation logic, status constants, & edge cases
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
from communication.packet_schema import (
    TelemetryPacket,
    EVAC_STATE_NORMAL,
    EVAC_STATE_EVACUATE,
    HEALTH_HEALTHY,
    HEALTH_FAULT,
    LED_STATE_SAFE_SOLID,
    LED_STATE_DANGER_FLASH,
)


class TestTelemetryPacketSchema(unittest.TestCase):
    """Unit test suite for TelemetryPacket schema."""

    def test_default_packet_creation(self) -> None:
        """Test default values on packet creation."""
        pkt = TelemetryPacket()
        self.assertEqual(pkt.schema_version, "1.0")
        self.assertTrue(len(pkt.packet_id) > 0)
        self.assertGreater(pkt.timestamp, 0)
        self.assertEqual(pkt.temperature, 25.0)
        self.assertEqual(pkt.smoke_level, 0.0)
        self.assertFalse(pkt.flame_detected)
        self.assertEqual(pkt.hazard_score, 0.0)
        self.assertEqual(pkt.evacuation_state, EVAC_STATE_NORMAL)
        self.assertEqual(pkt.node_health, HEALTH_HEALTHY)
        self.assertEqual(pkt.led_state, LED_STATE_SAFE_SOLID)
        self.assertTrue(pkt.validate())

    def test_custom_packet_creation(self) -> None:
        """Test setting custom values."""
        pkt = TelemetryPacket(
            schema_version="1.0",
            node_id="NODE-R105",
            zone_id="R-105",
            temperature=88.5,
            smoke_level=0.75,
            flame_detected=True,
            occupancy_count=4,
            hazard_score=0.82,
            evacuation_state=EVAC_STATE_EVACUATE,
            recommended_exit="X-01",
            led_state=LED_STATE_DANGER_FLASH,
        )
        self.assertEqual(pkt.schema_version, "1.0")
        self.assertEqual(pkt.node_id, "NODE-R105")
        self.assertEqual(pkt.zone_id, "R-105")
        self.assertEqual(pkt.temperature, 88.5)
        self.assertEqual(pkt.smoke_level, 0.75)
        self.assertTrue(pkt.flame_detected)
        self.assertEqual(pkt.occupancy_count, 4)
        self.assertEqual(pkt.hazard_score, 0.82)
        self.assertEqual(pkt.evacuation_state, "EVACUATE")
        self.assertTrue(pkt.validate())

    def test_dict_serialization_roundtrip(self) -> None:
        """Test to_dict() and from_dict() roundtrip."""
        original = TelemetryPacket(
            node_id="NODE-101",
            temperature=65.2,
            smoke_level=0.45,
            flame_detected=True,
            hazard_score=0.61,
            metadata={"sensor_model": "DS18B20", "calibrated": True},
        )
        data_dict = original.to_dict()
        self.assertIsInstance(data_dict, dict)
        self.assertEqual(data_dict["schema_version"], "1.0")
        self.assertEqual(data_dict["node_id"], "NODE-101")
        self.assertEqual(data_dict["temperature"], 65.2)

        reconstructed = TelemetryPacket.from_dict(data_dict)
        self.assertEqual(reconstructed.schema_version, original.schema_version)
        self.assertEqual(reconstructed.node_id, original.node_id)
        self.assertEqual(reconstructed.temperature, original.temperature)
        self.assertEqual(reconstructed.smoke_level, original.smoke_level)
        self.assertEqual(reconstructed.flame_detected, original.flame_detected)
        self.assertEqual(reconstructed.metadata, original.metadata)
        self.assertTrue(reconstructed.validate())

    def test_json_serialization_roundtrip(self) -> None:
        """Test to_json() and from_json() roundtrip."""
        original = TelemetryPacket(
            node_id="NODE-C01",
            zone_id="C-01",
            temperature=42.0,
            smoke_level=0.30,
            hazard_score=0.35,
        )
        json_str = original.to_json()
        self.assertIsInstance(json_str, str)
        self.assertIn('"schema_version": "1.0"', json_str)
        self.assertIn('"node_id": "NODE-C01"', json_str)

        reconstructed = TelemetryPacket.from_json(json_str)
        self.assertEqual(reconstructed.schema_version, original.schema_version)
        self.assertEqual(reconstructed.node_id, original.node_id)
        self.assertEqual(reconstructed.zone_id, original.zone_id)
        self.assertEqual(reconstructed.temperature, original.temperature)
        self.assertEqual(reconstructed.smoke_level, original.smoke_level)
        self.assertTrue(reconstructed.validate())

    def test_validation_bounds(self) -> None:
        """Test packet validation bounds and error detection."""
        # Valid packet
        valid_pkt = TelemetryPacket(smoke_level=0.5, hazard_score=0.5, battery_level=50.0)
        self.assertTrue(valid_pkt.validate())

        # Invalid smoke_level (> 1.0)
        invalid_smoke = TelemetryPacket(smoke_level=1.5)
        self.assertFalse(invalid_smoke.validate())

        # Invalid hazard_score (< 0.0)
        invalid_hazard = TelemetryPacket(hazard_score=-0.1)
        self.assertFalse(invalid_hazard.validate())

        # Invalid battery_level (> 100.0)
        invalid_battery = TelemetryPacket(battery_level=105.0)
        self.assertFalse(invalid_battery.validate())

        # Empty packet_id
        invalid_id = TelemetryPacket(packet_id="")
        self.assertFalse(invalid_id.validate())

    def test_status_constants_validation(self) -> None:
        """Test extended status validation rules."""
        # Invalid evacuation_state
        invalid_evac = TelemetryPacket(evacuation_state="INVALID_STATE")
        self.assertFalse(invalid_evac.validate())

        # Invalid node_health
        invalid_node = TelemetryPacket(node_health="BAD_HEALTH")
        self.assertFalse(invalid_node.validate())

        # Invalid comm_health
        invalid_comm = TelemetryPacket(communication_health="NO_LINK")
        self.assertFalse(invalid_comm.validate())

        # Invalid firmware_health
        invalid_fw = TelemetryPacket(firmware_health="DEAD")
        self.assertFalse(invalid_fw.validate())

        # Invalid led_state
        invalid_led = TelemetryPacket(led_state="PURPLE_RAIN")
        self.assertFalse(invalid_led.validate())


if __name__ == "__main__":
    unittest.main()

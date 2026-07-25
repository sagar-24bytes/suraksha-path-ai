"""
SurakshaPath AI — Firmware Communication Helper.

Constructs canonical TelemetryPacket telemetry from local sensor manager, fusion engine,
led controller, and diagnostics manager, and transmits over CommunicationInterface.

Design Rules:
  - Reuses canonical TelemetryPacket schema and CommunicationInterface.
  - Zero duplicated packet definitions or MQTT code.
"""

from __future__ import annotations

from typing import Optional
from communication.packet_schema import TelemetryPacket
from communication.interface import CommunicationInterface
from firmware.micropython.sensors import SensorManager
from firmware.micropython.sensor_fusion import EmbeddedSensorFusion
from firmware.micropython.led_controller import LogicalLEDController
from firmware.micropython.diagnostics import DiagnosticsManager
from firmware.micropython.compat import get_ticks_ms


class FirmwareCommunicationHelper:
    """Helper class assembling and transmitting telemetry packets for a firmware node."""

    def __init__(
        self,
        node_id: str,
        zone_id: str,
        transport: Optional[CommunicationInterface] = None,
    ) -> None:
        self.node_id = node_id
        self.zone_id = zone_id
        self.transport = transport
        self.sequence_num = 0

    def build_packet(
        self,
        sensor_mgr: SensorManager,
        fusion_engine: EmbeddedSensorFusion,
        led_ctrl: LogicalLEDController,
        diag_mgr: DiagnosticsManager,
        recommended_exit: str = "X-01",
        route_cost: float = 0.0,
    ) -> TelemetryPacket:
        """Assemble a complete canonical TelemetryPacket from node components.

        Returns:
            Canonical TelemetryPacket instance.
        """
        self.sequence_num += 1
        readings = sensor_mgr.read_all()
        
        hazard_score, evac_state = fusion_engine.compute_hazard(
            temperature=readings["temperature"],
            smoke_level=readings["smoke_level"],
            flame_detected=readings["flame_detected"],
        )

        health_info = diag_mgr.check_diagnostics()
        uptime_s = round(diag_mgr.get_uptime_ms() / 1000.0, 2)

        return TelemetryPacket(
            schema_version="1.0",
            timestamp=uptime_s,
            node_id=self.node_id,
            zone_id=self.zone_id,
            temperature=readings["temperature"],
            smoke_level=readings["smoke_level"],
            flame_detected=readings["flame_detected"],
            occupancy_count=readings["occupancy_count"],
            hazard_score=hazard_score,
            evacuation_state=evac_state,
            recommended_exit=recommended_exit,
            route_cost=route_cost,
            node_health=health_info["node_health"],
            communication_health=health_info["communication_health"],
            firmware_health=health_info["firmware_health"],
            led_state=led_ctrl.current_state,
            battery_level=diag_mgr.battery_level,
            metadata={"heartbeat": diag_mgr.heartbeat_counter, "seq": self.sequence_num},
        )

    def publish_telemetry(
        self,
        packet: TelemetryPacket,
        topic_prefix: str = "suraksha/telemetry",
    ) -> bool:
        """Transmit packet using transport abstraction if available.

        Args:
            packet: TelemetryPacket to publish.
            topic_prefix: Base topic.

        Returns:
            True if published successfully, False otherwise.
        """
        if self.transport is None or not self.transport.is_connected:
            return False

        topic = f"{topic_prefix}/{self.zone_id}"
        return self.transport.publish(topic, packet)

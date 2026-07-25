"""
SurakshaPath AI — Firmware MicroPython Coordinator Entry Point.

Orchestrates local node embedded execution loop:
  CooperativeScheduler → SensorManager → EmbeddedSensorFusion → DiagnosticsManager → LogicalLEDController → FirmwareCommunicationHelper

Responsibilities:
  - Initialize embedded components.
  - Register periodic tasks with CooperativeScheduler.
  - Run cooperative tasks on every tick/step.
  - Structure closely matches future physical ESP32 main.py.
"""

from __future__ import annotations

from typing import Optional
from firmware.micropython import config
from firmware.micropython.scheduler import CooperativeScheduler
from firmware.micropython.sensors import SensorManager
from firmware.micropython.sensor_fusion import EmbeddedSensorFusion
from firmware.micropython.led_controller import LogicalLEDController
from firmware.micropython.diagnostics import DiagnosticsManager
from firmware.micropython.communication import FirmwareCommunicationHelper
from communication.interface import CommunicationInterface
from communication.packet_schema import TelemetryPacket


class FirmwareNode:
    """Embedded firmware node coordinator."""

    def __init__(
        self,
        zone_id: str = "R-101",
        transport: Optional[CommunicationInterface] = None,
    ) -> None:
        self.zone_id = zone_id
        self.node_id = f"NODE-{zone_id}"
        
        # Sub-components
        self.scheduler = CooperativeScheduler()
        self.sensor_mgr = SensorManager(zone_id)
        self.fusion_engine = EmbeddedSensorFusion()
        self.led_ctrl = LogicalLEDController()
        self.diag_mgr = DiagnosticsManager(self.node_id)
        self.comm_helper = FirmwareCommunicationHelper(self.node_id, self.zone_id, transport)

        self.last_packet: Optional[TelemetryPacket] = None
        self._register_tasks()

    def _register_tasks(self) -> None:
        """Register periodic cooperative tasks with scheduler."""
        self.scheduler.add_task("poll_sensors", config.SENSOR_POLL_INTERVAL_MS, self._task_poll_sensors)
        self.scheduler.add_task("sensor_fusion", config.FUSION_INTERVAL_MS, self._task_sensor_fusion)
        self.scheduler.add_task("update_leds", config.LED_REFRESH_INTERVAL_MS, self._task_update_leds)
        self.scheduler.add_task("update_diagnostics", config.HEARTBEAT_INTERVAL_MS, self._task_update_diagnostics)
        self.scheduler.add_task("publish_telemetry", config.COMM_INTERVAL_MS, self._task_publish_telemetry)

    def _task_poll_sensors(self) -> None:
        """Task 1: Poll sensor drivers."""
        self.sensor_mgr.read_all()

    def _task_sensor_fusion(self) -> None:
        """Task 2: Compute hazard score & evacuation state."""
        readings = self.sensor_mgr.read_all()
        hazard_score, evac_state = self.fusion_engine.compute_hazard(
            temperature=readings["temperature"],
            smoke_level=readings["smoke_level"],
            flame_detected=readings["flame_detected"],
        )
        self.led_ctrl.update_from_hazard(hazard_score, evac_state, self.diag_mgr.node_health)

    def _task_update_leds(self) -> None:
        """Task 3: Refresh LED state machine."""
        pass  # State machine updated during fusion step

    def _task_update_diagnostics(self) -> None:
        """Task 4: Diagnostics heartbeat update."""
        self.diag_mgr.heartbeat()

    def _task_publish_telemetry(self) -> None:
        """Task 5: Construct and publish TelemetryPacket."""
        pkt = self.comm_helper.build_packet(
            sensor_mgr=self.sensor_mgr,
            fusion_engine=self.fusion_engine,
            led_ctrl=self.led_ctrl,
            diag_mgr=self.diag_mgr,
        )
        self.last_packet = pkt
        if self.comm_helper.transport and self.comm_helper.transport.is_connected:
            if self.comm_helper.publish_telemetry(pkt):
                self.diag_mgr.update_comm_activity()

    def update_mock_environment(
        self,
        temperature: float,
        smoke_level: float,
        flame_detected: bool,
        occupancy_count: int = 0,
    ) -> None:
        """Update mock sensor inputs from simulation / test harness."""
        self.sensor_mgr.update_mock_readings(
            temperature=temperature,
            smoke_level=smoke_level,
            flame_detected=flame_detected,
            occupancy_count=occupancy_count,
        )

    def step(self, elapsed_ms: int = 500) -> Optional[TelemetryPacket]:
        """Advance firmware clock by `elapsed_ms` and run cooperative tasks.

        Args:
            elapsed_ms: Milliseconds elapsed since last step.

        Returns:
            Latest TelemetryPacket produced during step.
        """
        self.scheduler.step(elapsed_ms)
        return self.last_packet


def main() -> None:
    """MicroPython entry point placeholder."""
    node = FirmwareNode("R-101")
    print(f"SurakshaPath AI Firmware Node '{node.node_id}' initialized.")
    node.step(1000)
    if node.last_packet:
        print(f"Generated Packet: hazard_score={node.last_packet.hazard_score}, state={node.last_packet.evacuation_state}")


if __name__ == "__main__":
    main()

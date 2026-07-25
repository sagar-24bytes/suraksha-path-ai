"""
SurakshaPath AI — Dedicated MicroPython Firmware Package.

Subsystem 2: Embedded firmware running task scheduler, on-device sensor fusion,
sensor hardware abstraction, LED state animation, and diagnostics manager.

Exports:
  - CooperativeScheduler, Task: Single-threaded cooperative task scheduler
  - SensorManager, BaseSensor, TemperatureSensor, SmokeSensor, FlameSensor, OccupancySensor
  - EmbeddedSensorFusion: On-device evidence fusion engine
  - LogicalLEDController: Visual indicator animation state machine
  - DiagnosticsManager: Node runtime health monitor
  - FirmwareCommunicationHelper: Telemetry packet constructor & transport bridge
  - FirmwareNode: Master firmware node coordinator
"""

from firmware.micropython.compat import get_ticks_ms, ticks_diff, sleep_ms
from firmware.micropython.scheduler import CooperativeScheduler, Task
from firmware.micropython.sensors import (
    SensorManager,
    BaseSensor,
    TemperatureSensor,
    SmokeSensor,
    FlameSensor,
    OccupancySensor,
)
from firmware.micropython.sensor_fusion import EmbeddedSensorFusion
from firmware.micropython.led_controller import LogicalLEDController
from firmware.micropython.diagnostics import DiagnosticsManager
from firmware.micropython.communication import FirmwareCommunicationHelper
from firmware.micropython.main import FirmwareNode

__all__ = [
    "get_ticks_ms",
    "ticks_diff",
    "sleep_ms",
    "CooperativeScheduler",
    "Task",
    "SensorManager",
    "BaseSensor",
    "TemperatureSensor",
    "SmokeSensor",
    "FlameSensor",
    "OccupancySensor",
    "EmbeddedSensorFusion",
    "LogicalLEDController",
    "DiagnosticsManager",
    "FirmwareCommunicationHelper",
    "FirmwareNode",
]

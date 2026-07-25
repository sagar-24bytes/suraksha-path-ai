"""
SurakshaPath AI — Firmware Health & Diagnostics Manager.

Tracks runtime health metrics for embedded node operation.

Monitored Diagnostic Parameters:
  - Node heartbeat sequence counter
  - Uptime in milliseconds
  - Battery charge level (0.0–100.0%)
  - Last communication timestamp & timeout detection
  - Sensor fault counters & watchdog reset indicators
  - Health statuses: node_health, communication_health, firmware_health
"""

from __future__ import annotations

from typing import Dict, Any
from firmware.micropython import config
from firmware.micropython.compat import get_ticks_ms, ticks_diff
from communication.packet_schema import (
    HEALTH_HEALTHY,
    HEALTH_WARNING,
    HEALTH_OFFLINE,
    HEALTH_FAULT,
    HEALTH_DEGRADED,
    HEALTH_TIMEDOUT,
    HEALTH_WATCHDOG_RESET,
)


class DiagnosticsManager:
    """Embedded runtime health monitor."""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self.start_ticks_ms: int = get_ticks_ms()
        self.heartbeat_counter: int = 0
        self.battery_level: float = config.BATTERY_FULL_PCT
        self.last_comm_ticks_ms: int = get_ticks_ms()
        
        self.sensor_faults_count: int = 0
        self.watchdog_resets: int = 0
        
        self.node_health: str = HEALTH_HEALTHY
        self.communication_health: str = HEALTH_HEALTHY
        self.firmware_health: str = HEALTH_HEALTHY

    def heartbeat(self) -> int:
        """Increment heartbeat counter and return value."""
        self.heartbeat_counter += 1
        return self.heartbeat_counter

    def update_comm_activity(self) -> None:
        """Register successful communication activity."""
        self.last_comm_ticks_ms = get_ticks_ms()
        self.communication_health = HEALTH_HEALTHY

    def update_battery(self, level: float) -> float:
        """Update battery charge percentage."""
        self.battery_level = max(0.0, min(100.0, float(level)))
        if self.battery_level <= config.BATTERY_CRIT_PCT:
            self.node_health = HEALTH_FAULT
        elif self.battery_level <= config.BATTERY_WARN_PCT:
            self.node_health = HEALTH_WARNING
        return self.battery_level

    def record_sensor_fault(self) -> None:
        """Record a detected sensor fault."""
        self.sensor_faults_count += 1
        if self.node_health == HEALTH_HEALTHY:
            self.node_health = HEALTH_WARNING

    def record_watchdog_event(self) -> None:
        """Record a watchdog reset event."""
        self.watchdog_resets += 1
        self.firmware_health = HEALTH_WATCHDOG_RESET

    def check_diagnostics(self) -> Dict[str, str]:
        """Perform diagnostic evaluation of health parameters.

        Returns:
            Dict containing node_health, communication_health, firmware_health.
        """
        now = get_ticks_ms()
        time_since_comm = ticks_diff(now, self.last_comm_ticks_ms)

        # Check for communication timeout
        if time_since_comm > config.COMM_TIMEOUT_MS:
            self.communication_health = HEALTH_TIMEDOUT
        elif time_since_comm > config.COMM_TIMEOUT_MS // 2:
            self.communication_health = HEALTH_DEGRADED

        return {
            "node_health": self.node_health,
            "communication_health": self.communication_health,
            "firmware_health": self.firmware_health,
        }

    def get_uptime_ms(self) -> int:
        """Return node uptime in milliseconds."""
        return ticks_diff(get_ticks_ms(), self.start_ticks_ms)

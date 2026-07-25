"""
SurakshaPath AI — Sensor Hardware Abstraction Framework.

Provides sensor driver abstractions for Temperature, Smoke, Flame, and Occupancy.
Includes mock drivers for simulation/testing so physical hardware drivers (ADC/I2C/GPIO)
can replace them later with zero changes to firmware business logic.

Design Rules:
  - Simple, predictable classes for low RAM footprint.
  - Uniform read() contract returning normalized floats or raw values.
"""

from __future__ import annotations

from typing import Dict, Any, Optional


class BaseSensor:
    """Abstract Base Class for all sensor drivers."""

    def __init__(self, sensor_id: str, zone_id: str) -> None:
        self.sensor_id = sensor_id
        self.zone_id = zone_id
        self.is_faulty = False

    def read(self) -> Any:
        """Read latest sensor value."""
        raise NotImplementedError


class TemperatureSensor(BaseSensor):
    """Temperature sensor driver (°C)."""

    def __init__(self, sensor_id: str, zone_id: str, initial_temp: float = 25.0) -> None:
        super().__init__(sensor_id, zone_id)
        self._value: float = initial_temp

    def set_mock_value(self, temp_c: float) -> None:
        """Set mock temperature for simulation/test."""
        self._value = max(-40.0, min(1000.0, temp_c))

    def read(self) -> float:
        """Read temperature in °C."""
        return self._value


class SmokeSensor(BaseSensor):
    """Smoke obscuration sensor driver (0.0–1.0)."""

    def __init__(self, sensor_id: str, zone_id: str, initial_smoke: float = 0.0) -> None:
        super().__init__(sensor_id, zone_id)
        self._value: float = initial_smoke

    def set_mock_value(self, smoke_level: float) -> None:
        """Set mock smoke level for simulation/test."""
        self._value = max(0.0, min(1.0, smoke_level))

    def read(self) -> float:
        """Read smoke level (0.0–1.0)."""
        return self._value


class FlameSensor(BaseSensor):
    """Optical flame detector driver (True/False)."""

    def __init__(self, sensor_id: str, zone_id: str, initial_flame: bool = False) -> None:
        super().__init__(sensor_id, zone_id)
        self._value: bool = initial_flame

    def set_mock_value(self, flame_detected: bool) -> None:
        """Set mock flame state for simulation/test."""
        self._value = bool(flame_detected)

    def read(self) -> bool:
        """Read flame status."""
        return self._value


class OccupancySensor(BaseSensor):
    """Occupancy count sensor driver (int)."""

    def __init__(self, sensor_id: str, zone_id: str, initial_occ: int = 0) -> None:
        super().__init__(sensor_id, zone_id)
        self._value: int = initial_occ

    def set_mock_value(self, count: int) -> None:
        """Set mock occupancy count."""
        self._value = max(0, int(count))

    def read(self) -> int:
        """Read occupant count."""
        return self._value


class SensorManager:
    """Manages all local sensors installed on a firmware node."""

    def __init__(self, zone_id: str) -> None:
        self.zone_id = zone_id
        self.temp_sensor = TemperatureSensor(f"T-{zone_id}", zone_id)
        self.smoke_sensor = SmokeSensor(f"SM-{zone_id}", zone_id)
        self.flame_sensor = FlameSensor(f"FL-{zone_id}", zone_id)
        self.occ_sensor = OccupancySensor(f"OC-{zone_id}", zone_id)

    def update_mock_readings(
        self,
        temperature: float,
        smoke_level: float,
        flame_detected: bool,
        occupancy_count: int = 0,
    ) -> None:
        """Update mock values for all local sensors simultaneously."""
        self.temp_sensor.set_mock_value(temperature)
        self.smoke_sensor.set_mock_value(smoke_level)
        self.flame_sensor.set_mock_value(flame_detected)
        self.occ_sensor.set_mock_value(occupancy_count)

    def read_all(self) -> Dict[str, Any]:
        """Poll all sensors and return current readings dictionary.

        Returns:
            Dict containing temperature, smoke_level, flame_detected, occupancy_count.
        """
        return {
            "temperature": self.temp_sensor.read(),
            "smoke_level": self.smoke_sensor.read(),
            "flame_detected": self.flame_sensor.read(),
            "occupancy_count": self.occ_sensor.read(),
        }

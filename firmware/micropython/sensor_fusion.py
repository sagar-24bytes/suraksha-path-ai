"""
SurakshaPath AI — On-Device Sensor Fusion Engine.

Implements lightweight evidence fusion on MicroPython using a weighted linear combination:
  H_z = Σ(w_i · c_i · t_i) / Σ(w_i · c_i)

Key Features:
  - Deterministic and transparent math (zero Machine Learning).
  - Uses weights and thresholds from firmware config.py.
  - Normalizes raw inputs (temperature, smoke, flame) to 0.0–1.0 threat levels.
  - Computes hazard score and maps to evacuation state ("NORMAL", "WARNING", "EVACUATE", "SHELTER").
"""

from __future__ import annotations

from typing import Dict, Any, Tuple
from firmware.micropython import config
from communication.packet_schema import (
    EVAC_STATE_NORMAL,
    EVAC_STATE_WARNING,
    EVAC_STATE_EVACUATE,
    EVAC_STATE_SHELTER,
)


class EmbeddedSensorFusion:
    """On-device evidence fusion engine for embedded microcontrollers."""

    def __init__(self) -> None:
        # Load weights from firmware config
        self.w_temp = config.SENSOR_WEIGHT_TEMP
        self.w_smoke = config.SENSOR_WEIGHT_SMOKE
        self.w_flame = config.SENSOR_WEIGHT_FLAME

    @staticmethod
    def normalize_temperature(temp_c: float) -> float:
        """Normalize temperature (°C) to 0.0–1.0 threat level using linear piecewise.

        Args:
            temp_c: Raw temperature in °C.

        Returns:
            Normalized threat score 0.0 (ambient) to 1.0 (flashover).
        """
        if temp_c <= config.TEMP_AMBIENT_C:
            return 0.0
        if temp_c >= 200.0:
            return 1.0
        # Piecewise mapping: 25°C = 0.0, 80°C = 0.4, 200°C = 1.0
        return min(1.0, max(0.0, (temp_c - config.TEMP_AMBIENT_C) / (200.0 - config.TEMP_AMBIENT_C)))

    @staticmethod
    def normalize_smoke(smoke_level: float) -> float:
        """Normalize smoke obscuration (0.0–1.0).

        Args:
            smoke_level: Raw obscuration value.

        Returns:
            Clamped threat score 0.0–1.0.
        """
        return max(0.0, min(1.0, float(smoke_level)))

    @staticmethod
    def normalize_flame(flame_detected: bool) -> float:
        """Normalize flame sensor reading (True/False).

        Args:
            flame_detected: Flame sensor digital status.

        Returns:
            1.0 if flame detected, 0.0 otherwise.
        """
        return 1.0 if flame_detected else 0.0

    def compute_hazard(
        self,
        temperature: float,
        smoke_level: float,
        flame_detected: bool,
        temp_confidence: float = 1.0,
        smoke_confidence: float = 1.0,
        flame_confidence: float = 1.0,
    ) -> Tuple[float, str]:
        """Compute composite hazard score and evacuation state.

        Formula:
          H_z = Σ(w_i · c_i · t_i) / Σ(w_i · c_i)

        Args:
            temperature: Temperature in °C.
            smoke_level: Smoke level 0.0–1.0.
            flame_detected: Flame status bool.
            temp_confidence: Confidence score for temp sensor (0.0–1.0).
            smoke_confidence: Confidence score for smoke sensor (0.0–1.0).
            flame_confidence: Confidence score for flame sensor (0.0–1.0).

        Returns:
            Tuple of (hazard_score 0.0–1.0, evacuation_state string).
        """
        t_temp = self.normalize_temperature(temperature)
        t_smoke = self.normalize_smoke(smoke_level)
        t_flame = self.normalize_flame(flame_detected)

        num = (
            (self.w_temp * temp_confidence * t_temp) +
            (self.w_smoke * smoke_confidence * t_smoke) +
            (self.w_flame * flame_confidence * t_flame)
        )
        den = (
            (self.w_temp * temp_confidence) +
            (self.w_smoke * smoke_confidence) +
            (self.w_flame * flame_confidence)
        )

        if den <= 0.001:
            # Fail-safe default if all sensor confidence is zero
            hazard_score = 0.70
        else:
            hazard_score = max(0.0, min(1.0, num / den))

        # Map continuous score to evacuation state
        if hazard_score >= config.THRESHOLD_DANGER:
            evac_state = EVAC_STATE_EVACUATE
        elif hazard_score >= config.THRESHOLD_WARNING:
            evac_state = EVAC_STATE_WARNING
        elif hazard_score >= config.THRESHOLD_ADVISORY:
            evac_state = EVAC_STATE_WARNING
        else:
            evac_state = EVAC_STATE_NORMAL

        return round(hazard_score, 4), evac_state

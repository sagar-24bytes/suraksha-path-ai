"""
SurakshaPath AI — MicroPython Firmware Configuration.

Centralizes all embedded timing intervals, fusion weights, threshold parameters,
and battery bounds. Reuses standard threshold values from thresholds.yaml.

Design Rule:
  - Primitive data types only (ints, floats, dicts) for low RAM footprint.
  - Zero hardcoded magic numbers in business logic.
"""

from __future__ import annotations

# =============================================================
# Embedded Task Timing Intervals (Milliseconds)
# =============================================================
SENSOR_POLL_INTERVAL_MS = 500       # Sensor acquisition frequency
FUSION_INTERVAL_MS      = 500       # Sensor fusion & hazard calculation frequency
COMM_INTERVAL_MS        = 1000      # Telemetry packet publish frequency
LED_REFRESH_INTERVAL_MS = 100       # LED state machine animation refresh
HEARTBEAT_INTERVAL_MS   = 1000      # Health diagnostic heartbeat update

# =============================================================
# Sensor Fusion Base Weights & Parameters
# =============================================================
# Aligned with config/thresholds.yaml
SENSOR_WEIGHT_TEMP  = 0.30
SENSOR_WEIGHT_SMOKE = 0.25
SENSOR_WEIGHT_FLAME = 0.40

# Temperature Normalization Parameters (Sigmoid/Linear approximation)
TEMP_AMBIENT_C  = 25.0
TEMP_MIDPOINT_C = 80.0
TEMP_MAX_C      = 800.0

# Smoke Normalization Parameters
SMOKE_MAX_OBSCURATION = 1.0

# =============================================================
# Hazard Score Thresholds
# =============================================================
THRESHOLD_SAFE     = 0.20
THRESHOLD_ADVISORY = 0.40
THRESHOLD_WARNING  = 0.60
THRESHOLD_DANGER   = 0.80

# =============================================================
# Health & Battery Bounds
# =============================================================
BATTERY_FULL_PCT = 100.0
BATTERY_WARN_PCT = 20.0
BATTERY_CRIT_PCT = 5.0

COMM_TIMEOUT_MS = 5000              # Time without comm before DEGRADED state

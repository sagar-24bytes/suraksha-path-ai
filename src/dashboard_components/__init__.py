"""
SurakshaPath AI — Fire Commander Dashboard Components Package.

Contains modular UI rendering components for:
  - Floor Plan & Route Overlays (visualizations.py)
  - Mandatory Explainability Panel (explainability.py)
  - Live Telemetry Table (telemetry_panel.py)
  - Real-Time Alerts Feed (alerts.py)
  - 5-Aspect Subsystem Health Matrix (health_panel.py)
  - Interactive Sidebar Controls (controls.py)
"""

from src.dashboard_components.visualizations import render_floor_plan
from src.dashboard_components.explainability import render_explainability_panel
from src.dashboard_components.telemetry_panel import render_telemetry_panel
from src.dashboard_components.alerts import render_alerts_feed
from src.dashboard_components.health_panel import render_health_panel
from src.dashboard_components.controls import render_sidebar_controls

__all__ = [
    "render_floor_plan",
    "render_explainability_panel",
    "render_telemetry_panel",
    "render_alerts_feed",
    "render_health_panel",
    "render_sidebar_controls",
]

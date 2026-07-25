"""
SurakshaPath AI — Fire Commander Dashboard Components Package.

Contains modular UI rendering components for:
  - Architectural Floor Plan & Visualizations (visualizations.py)
  - Building Architecture Mapping Layer (building_mapper.py)
  - Mandatory Explainability Panel (explainability.py)
  - Live Telemetry Table (telemetry_panel.py)
  - Real-Time Alerts Feed (alerts.py)
  - Top SCADA KPI Cards & 5-Aspect Health Matrix (health_panel.py)
  - Interactive Sidebar Controls (controls.py)
"""

from src.dashboard_components.visualizations import render_commercial_floor_plan, render_floor_plan
from src.dashboard_components.building_mapper import get_room_display_name, NODE_TO_ROOM_MAP
from src.dashboard_components.timeline import render_event_timeline
from src.dashboard_components.explainability import render_explainability_panel
from src.dashboard_components.telemetry_panel import render_telemetry_panel
from src.dashboard_components.alerts import render_alerts_feed
from src.dashboard_components.health_panel import render_top_kpi_cards, render_health_panel
from src.dashboard_components.controls import render_sidebar_controls

__all__ = [
    "render_commercial_floor_plan",
    "render_floor_plan",
    "get_room_display_name",
    "NODE_TO_ROOM_MAP",
    "render_event_timeline",
    "render_explainability_panel",
    "render_telemetry_panel",
    "render_alerts_feed",
    "render_top_kpi_cards",
    "render_health_panel",
    "render_sidebar_controls",
]

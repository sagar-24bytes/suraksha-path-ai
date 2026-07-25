"""
SurakshaPath AI — Fire Commander Dashboard Entry Point.

Primary operator command-center interface coordinating all 5 subsystems:
  Digital Twin Simulation → Transport Layer → Dynamic Routing → MicroPython Firmware → Fire Commander UI

Features:
  - One-click application startup (streamlit run src/dashboard.py)
  - Custom dark theme styling (#0f0f1a)
  - Plotly interactive floor plan with smooth HSL hazard gradients & dynamic route arrows
  - Mandatory Explainability Panel (w_i · c_i · t_i formula breakdown & reroute reasoning)
  - Real-time emergency alerts feed
  - 5-aspect subsystem health matrix (Simulation, Comm, Firmware, Routing, Dashboard)
  - Live telemetry table detailing all 18 building zones
  - Interactive scenario controls (Kitchen Fire, Electrical Room, Flashover, Blocked Exit, etc.)
"""

import sys
import os
import time

# Ensure project root and src/ are in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import streamlit as st
from system_coordinator import SystemCoordinator
from simulation.scenario_engine import BUILTIN_SCENARIOS
from src.dashboard_components import (
    render_floor_plan,
    render_explainability_panel,
    render_telemetry_panel,
    render_alerts_feed,
    render_health_panel,
    render_sidebar_controls,
)

# -------------------------------------------------------------
# Streamlit Page Setup & Custom CSS Styling
# -------------------------------------------------------------
st.set_page_config(
    page_title="SurakshaPath AI — Fire Commander Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Dark Command Center CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0f0f1a;
        color: #e0e0e0;
    }
    .stSidebar {
        background-color: #161625 !important;
    }
    .metric-card {
        background-color: #1a1a2e;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #2a2a40;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# Session State Initialization (SystemCoordinator Singleton)
# -------------------------------------------------------------
if "coordinator" not in st.session_state:
    st.session_state.coordinator = SystemCoordinator(scenario_key="kitchen_fire")
    st.session_state.is_playing = False
    st.session_state.last_scenario = "kitchen_fire"

coordinator: SystemCoordinator = st.session_state.coordinator
all_zone_ids = [z.id for z in coordinator.config.building.zones]

# -------------------------------------------------------------
# Render Sidebar Controls
# -------------------------------------------------------------
scenarios_meta = [
    {"key": s.key, "name": s.name, "description": s.description}
    for s in BUILTIN_SCENARIOS.values()
]

user_controls = render_sidebar_controls(
    available_scenarios=scenarios_meta,
    current_scenario_key=coordinator.scenario_key,
    all_zone_ids=all_zone_ids,
)

# Handle Sidebar Actions
if user_controls["scenario_key"] != st.session_state.last_scenario:
    st.session_state.last_scenario = user_controls["scenario_key"]
    coordinator.load_scenario(user_controls["scenario_key"])
    st.session_state.is_playing = False

if user_controls["reset_clicked"]:
    coordinator.reset()
    st.session_state.is_playing = False

if user_controls["play_pause_clicked"]:
    st.session_state.is_playing = not st.session_state.is_playing

if user_controls["step_clicked"]:
    coordinator.step()

# -------------------------------------------------------------
# Header Bar & Clock
# -------------------------------------------------------------
head_col1, head_col2, head_col3 = st.columns([3, 1, 1])

with head_col1:
    st.title("🔥 SurakshaPath AI — Fire Commander Dashboard")
    st.caption(f"Building: **{coordinator.config.building.name}** | Scenario: **{coordinator.scenario_key.upper().replace('_', ' ')}**")

with head_col2:
    st.metric(label="Simulation Clock", value=f"T + {coordinator.current_tick:02d}:00s")

with head_col3:
    status_str = "🟢 RUNNING" if st.session_state.is_playing else "⏸️ PAUSED"
    st.metric(label="System Status", value=status_str)

st.divider()

# -------------------------------------------------------------
# 5-Aspect Subsystem Health Matrix Panel
# -------------------------------------------------------------
render_health_panel(coordinator.get_system_health())
st.divider()

# -------------------------------------------------------------
# Main Visualization & Emergency Alerts Feed (2 Columns)
# -------------------------------------------------------------
vis_col, alert_col = st.columns([3, 2])

with vis_col:
    st.subheader(f"🗺️ Floor Plan — Floor {user_controls['selected_floor']} (Dynamic Route Overlays)")
    fig = render_floor_plan(
        graph=coordinator.graph,
        telemetry=coordinator.latest_telemetry,
        routes=coordinator.latest_routes,
        selected_floor=user_controls["selected_floor"],
        selected_zone_id=user_controls["selected_zone"],
    )
    st.plotly_chart(fig, use_container_width=True)

with alert_col:
    render_alerts_feed(coordinator.alerts_history)

st.divider()

# -------------------------------------------------------------
# Mandatory Explainability Panel (XAI Evidence Breakdown)
# -------------------------------------------------------------
render_explainability_panel(
    selected_zone_id=user_controls["selected_zone"],
    telemetry=coordinator.latest_telemetry,
    routes=coordinator.latest_routes,
)

st.divider()

# -------------------------------------------------------------
# Live Telemetry Panel Table
# -------------------------------------------------------------
render_telemetry_panel(
    telemetry=coordinator.latest_telemetry,
    routes=coordinator.latest_routes,
)

# -------------------------------------------------------------
# Real-Time Play Execution Loop
# -------------------------------------------------------------
if st.session_state.is_playing:
    time.sleep(1.0)
    coordinator.step()
    st.rerun()

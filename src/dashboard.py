"""
SurakshaPath AI — Fire Commander Dashboard Entry Point.

Primary operator command-center interface coordinating all 5 subsystems:
  Digital Twin Simulation → Transport Layer → Dynamic Routing → MicroPython Firmware → Fire Commander UI

Modern Emergency Command Center UI (Light Theme & Hero Building Focus):
  - SCADA industrial building management aesthetic (#f8f9fa background, white cards #ffffff)
  - Architectural commercial building floor plan occupying 85-90% of center panel width via native st.image()
  - Top SCADA KPI Cards (Fire zones, Smoke zones, Active occupants, Safe exits, Online nodes, Sim clock)
  - Chronological Event Timeline & Alerts Feed
  - Two-tier Decision Explainability Panel (Operator summary + Expandable evidence fusion math)
  - 5-aspect subsystem health matrix & Live 18-zone telemetry table
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
    render_commercial_floor_plan,
    render_event_timeline,
    render_explainability_panel,
    render_telemetry_panel,
    render_alerts_feed,
    render_top_kpi_cards,
    render_health_panel,
    render_sidebar_controls,
)

# -------------------------------------------------------------
# Streamlit Page Setup & Custom SCADA Styling
# -------------------------------------------------------------
st.set_page_config(
    page_title="SurakshaPath AI — Fire Commander Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injected SCADA Styling & Layout Cleaners
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f8f9fa;
        color: #2c3e50;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stSidebar {
        background-color: #ffffff !important;
        border-right: 1px solid #e9ecef;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        color: #2c3e50;
    }
    div[data-testid="stMetricLabel"] {
        color: #7f8c8d !important;
        font-weight: 600;
    }
    /* Hide standalone floating code blocks in the main layout to prevent stray code artifacts */
    div[data-testid="stCodeBlock"] {
        display: none !important;
    }
    /* Preserve code blocks inside expander panels for mathematical explainability formulas */
    div[data-testid="stExpander"] div[data-testid="stCodeBlock"] {
        display: block !important;
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
# Top Header & SCADA KPI Cards Row
# -------------------------------------------------------------
head_col1, head_col2 = st.columns([3, 1])
with head_col1:
    st.title("🏢 SurakshaPath AI — Fire Commander Operations Dashboard")
    st.caption(f"Commercial Building: **{coordinator.config.building.name}** &nbsp;|&nbsp; Scenario Story: **{coordinator.scenario_key.upper().replace('_', ' ')}**")

with head_col2:
    if st.session_state.is_playing:
        st.success("🟢 LIVE RUNNING")
    else:
        st.info("⏸️ SIMULATION PAUSED")

# Render Top KPI Cards Row
render_top_kpi_cards(
    telemetry=coordinator.latest_telemetry,
    routes=coordinator.latest_routes,
    current_tick=coordinator.current_tick,
)

st.divider()

# -------------------------------------------------------------
# Main Operations Center Layout (Center Hero Building vs Right Timeline)
# 85-90% Width Split for Commercial Building Floor Plan
# -------------------------------------------------------------
center_col, right_col = st.columns([3.8, 1.0])

with center_col:
    # Render SVG architectural commercial floor plan via native st.image() (Phase 8.4 SCADA Mode)
    render_commercial_floor_plan(
        graph=coordinator.graph,
        telemetry=coordinator.latest_telemetry,
        routes=coordinator.latest_routes,
        selected_floor=user_controls["selected_floor"],
        selected_zone_id=user_controls["selected_zone"],
        current_tick=coordinator.current_tick,
    )

with right_col:
    render_event_timeline(coordinator.alerts_history)
    st.divider()
    render_alerts_feed(coordinator.alerts_history)

st.divider()

# -------------------------------------------------------------
# Operator Explainability Panel & Subsystem Health
# -------------------------------------------------------------
render_explainability_panel(
    selected_zone_id=user_controls["selected_zone"],
    telemetry=coordinator.latest_telemetry,
    routes=coordinator.latest_routes,
)

st.divider()

# -------------------------------------------------------------
# 5-Aspect Subsystem Health Matrix & Live Telemetry Table
# -------------------------------------------------------------
render_health_panel(coordinator.get_system_health())
st.divider()

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

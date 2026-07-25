"""
SurakshaPath AI — Fire Commander Dashboard Entry Point (Phase 8.4.2).

Primary operator command-center interface coordinating all 5 subsystems:
  Digital Twin Simulation -> Transport Layer -> Dynamic Routing -> MicroPython Firmware -> Fire Commander UI

Professional Honeywell-style Emergency Command Center:
  - SCADA industrial building management aesthetic (#f8f9fa background, white cards #ffffff)
  - Architectural commercial building floor plan with LED corridor guidance & animated evacuation
  - Top SCADA KPI Cards (Fire zones, Smoke zones, Active occupants, Safe exits, Online nodes, Sim clock)
  - Fixed-height intelligent event timeline merging backend alerts + genuine AI rerouting decisions
  - Two-tier Decision Explainability Panel (Operator summary + Expandable evidence fusion math)
  - 5-aspect subsystem health matrix & Live 18-zone telemetry table

Phase 8.4.2 Additions:
  - Genuine AI route change detection by comparing consecutive RouteResult snapshots
  - AI decision events generated ONLY when the routing engine actually changes target exits or paths
  - Fixed-height timeline and alerts preventing page height overflow
  - All values 100% backend-driven — no fabricated events or artificial modifications
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
# Genuine AI Route Change Detection (Phase 8.4.2)
# Compares consecutive RouteResult snapshots — no fabrication
# -------------------------------------------------------------

def _detect_genuine_route_changes(prev_routes, curr_routes, current_tick):
    """Detect genuine AI routing decisions by comparing actual RouteResult snapshots.

    Only generates events when the backend routing engine truly changes:
      - The target_exit for a zone (rerouting to a different exit)
      - A zone entering shelter-in-place (all routes blocked)

    Args:
        prev_routes: Dict of zone_id -> {target_exit, path, is_shelter} from previous tick.
        curr_routes: Dict of zone_id -> RouteResult from current tick.
        current_tick: Current simulation tick integer.

    Returns:
        List of genuine AI decision event dicts (may be empty if no changes detected).
    """
    if not prev_routes or not curr_routes:
        return []

    events = []
    reroute_count = 0

    for zone_id, curr_route in curr_routes.items():
        prev_data = prev_routes.get(zone_id)
        if not prev_data:
            continue

        prev_exit = prev_data.get("target_exit", "")
        curr_exit = curr_route.target_exit or ""
        prev_shelter = prev_data.get("is_shelter", False)
        curr_shelter = curr_route.is_shelter_in_place

        # Genuine target exit change — routing engine selected a different exit
        if prev_exit and curr_exit and prev_exit != curr_exit:
            events.append({
                "tick": current_tick,
                "category": "AI_REROUTE",
                "message": f"AI recalculated route for {zone_id}: Exit {prev_exit} \u2192 Exit {curr_exit}",
                "level": "WARNING",
            })
            reroute_count += 1

        # Genuine shelter-in-place activation — all routes became blocked
        if not prev_shelter and curr_shelter:
            events.append({
                "tick": current_tick,
                "category": "EVACUATION",
                "message": f"SHELTER IN PLACE activated for Zone {zone_id} \u2014 all routes blocked",
                "level": "CRITICAL",
            })

        # Genuine shelter-in-place deactivation — routes became available again
        if prev_shelter and not curr_shelter and curr_exit:
            events.append({
                "tick": current_tick,
                "category": "AI_REROUTE",
                "message": f"Route restored for Zone {zone_id} \u2192 Exit {curr_exit}",
                "level": "INFO",
            })
            reroute_count += 1

    # If genuine rerouting occurred, add LED update event
    if reroute_count > 0:
        events.append({
            "tick": current_tick,
            "category": "LED_UPDATE",
            "message": f"LED corridor guidance updated \u2014 {reroute_count} zone(s) rerouted",
            "level": "INFO",
        })

    return events


# -------------------------------------------------------------
# Streamlit Page Setup & Custom SCADA Styling
# -------------------------------------------------------------
st.set_page_config(
    page_title="SurakshaPath AI \u2014 Fire Commander Dashboard",
    page_icon="\U0001f3e2",
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
    st.session_state.previous_routes = {}
    st.session_state.ai_decision_events = []

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
    st.session_state.previous_routes = {}
    st.session_state.ai_decision_events = []

if user_controls["reset_clicked"]:
    coordinator.reset()
    st.session_state.is_playing = False
    st.session_state.previous_routes = {}
    st.session_state.ai_decision_events = []

if user_controls["play_pause_clicked"]:
    st.session_state.is_playing = not st.session_state.is_playing

if user_controls["step_clicked"]:
    coordinator.step()

# -------------------------------------------------------------
# Phase 8.4.2: Genuine Route Change Detection
# Compare actual RouteResult snapshots — no fabrication
# -------------------------------------------------------------
_prev_routes = st.session_state.previous_routes
_curr_routes = coordinator.latest_routes

_new_ai_events = _detect_genuine_route_changes(_prev_routes, _curr_routes, coordinator.current_tick)

if _new_ai_events:
    st.session_state.ai_decision_events = _new_ai_events + st.session_state.ai_decision_events
    # Keep only latest 30 genuine events
    st.session_state.ai_decision_events = st.session_state.ai_decision_events[:30]

# Store current routes snapshot for next comparison
st.session_state.previous_routes = {
    z: {
        "target_exit": r.target_exit,
        "path": list(r.path) if r.path else [],
        "is_shelter": r.is_shelter_in_place,
    }
    for z, r in _curr_routes.items()
}

# -------------------------------------------------------------
# Top Header & SCADA KPI Cards Row
# -------------------------------------------------------------
head_col1, head_col2 = st.columns([3, 1])
with head_col1:
    st.title("\U0001f3e2 SurakshaPath AI \u2014 Fire Commander Operations Dashboard")
    st.caption(f"Commercial Building: **{coordinator.config.building.name}** &nbsp;|&nbsp; Scenario Story: **{coordinator.scenario_key.upper().replace('_', ' ')}**")

with head_col2:
    if st.session_state.is_playing:
        st.success("\U0001f7e2 LIVE RUNNING")
    else:
        st.info("\u23f8\ufe0f SIMULATION PAUSED")

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
    # Render SVG architectural floor plan with Phase 8.4.2 SCADA overlays
    render_commercial_floor_plan(
        graph=coordinator.graph,
        telemetry=coordinator.latest_telemetry,
        routes=coordinator.latest_routes,
        selected_floor=user_controls["selected_floor"],
        selected_zone_id=user_controls["selected_zone"],
        current_tick=coordinator.current_tick,
    )

with right_col:
    # Pass genuine AI decision events to the timeline
    render_event_timeline(
        coordinator.alerts_history,
        ai_events=st.session_state.ai_decision_events,
    )
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

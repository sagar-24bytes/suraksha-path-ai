"""
SurakshaPath AI — Sidebar Interactive Controls Component.

Renders interactive sidebar controls for scenario selection, simulation tick controls
(Play, Pause, Step, Reset), speed slider, floor filter, and inspect zone dropdown.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Any
import streamlit as st


def render_sidebar_controls(
    available_scenarios: List[Dict[str, str]],
    current_scenario_key: str,
    all_zone_ids: List[str],
) -> Dict[str, Any]:
    """Render Streamlit sidebar controls and return user interaction state.

    Args:
        available_scenarios: List of metadata dicts [{key, name, description}].
        current_scenario_key: Active scenario key string.
        all_zone_ids: List of all building zone IDs for inspection dropdown.

    Returns:
        Dict containing user control selections (scenario_key, is_running, selected_floor, inspected_zone, etc.).
    """
    st.sidebar.title("🔥 SurakshaPath AI")
    st.sidebar.caption("Honeywell Campus Connect 2026")
    st.sidebar.divider()

    # 1. Scenario Selector
    st.sidebar.subheader("🎯 Scenario Selector")
    scenario_names = [s["name"] for s in available_scenarios]
    scenario_keys = [s["key"] for s in available_scenarios]
    
    default_idx = scenario_keys.index(current_scenario_key) if current_scenario_key in scenario_keys else 0
    selected_name = st.sidebar.selectbox("Select Fire Scenario:", scenario_names, index=default_idx)
    selected_key = scenario_keys[scenario_names.index(selected_name)]

    # Scenario description text
    desc = next((s["description"] for s in available_scenarios if s["key"] == selected_key), "")
    st.sidebar.info(f"**Scenario Description**:\n{desc}")

    st.sidebar.divider()

    # 2. Simulation Execution Controls
    st.sidebar.subheader("🕹️ Simulation Controls")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        play_pause = st.button("▶️ Play / ⏸️ Pause", use_container_width=True)
    with col2:
        step_btn = st.button("⏭️ Step (1s)", use_container_width=True)

    reset_btn = st.sidebar.button("🔄 Reset Simulation", use_container_width=True)

    speed = st.sidebar.select_slider(
        "Simulation Speed:",
        options=["1x", "2x", "5x", "10x"],
        value="1x",
    )

    st.sidebar.divider()

    # 3. View Filter & Inspection Selection
    st.sidebar.subheader("🗺️ View Filters")
    selected_floor = st.sidebar.radio("Select Building Floor:", options=[1, 2], index=0, horizontal=True)

    selected_zone = st.sidebar.selectbox("Inspect Zone (Explainability):", options=all_zone_ids, index=0)

    st.sidebar.divider()
    st.sidebar.caption("🟢 **System Ready** | MicroPython Nodes Active")

    return {
        "scenario_key": selected_key,
        "play_pause_clicked": play_pause,
        "step_clicked": step_btn,
        "reset_clicked": reset_btn,
        "speed": speed,
        "selected_floor": selected_floor,
        "selected_zone": selected_zone,
    }

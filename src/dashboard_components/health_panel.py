"""
SurakshaPath AI — Top KPI Cards & System Health Panel Components.

Renders modern SCADA light-theme top KPI metrics cards and 5-aspect subsystem health badges.
"""

from __future__ import annotations

from typing import Dict, List, Any
import streamlit as st
from communication.packet_schema import TelemetryPacket
from routing.path_manager import RouteResult


def render_top_kpi_cards(
    telemetry: Dict[str, TelemetryPacket],
    routes: Dict[str, RouteResult],
    current_tick: int,
) -> None:
    """Render top SCADA KPI metrics row in Streamlit.

    Args:
        telemetry: Dict of zone_id -> TelemetryPacket.
        routes: Dict of zone_id -> RouteResult.
        current_tick: Current simulation tick integer.
    """
    fire_count = sum(1 for p in telemetry.values() if p.flame_detected or p.temperature > 50.0)
    smoke_count = sum(1 for p in telemetry.values() if p.smoke_level > 0.25)
    total_occupants = sum(p.occupancy_count for p in telemetry.values())
    safe_exits = sum(1 for r in routes.values() if not r.is_shelter_in_place and r.target_exit)
    online_nodes = sum(1 for p in telemetry.values() if p.node_health == "HEALTHY")

    cols = st.columns(6)

    with cols[0]:
        st.metric(label="🔥 Fire Zones", value=f"{fire_count}", delta=f"{fire_count} active" if fire_count else "0", delta_color="inverse")
    with cols[1]:
        st.metric(label="💨 Smoke Zones", value=f"{smoke_count}", delta=f"{smoke_count} active" if smoke_count else "0", delta_color="inverse")
    with cols[2]:
        st.metric(label="👥 Occupants", value=f"{total_occupants}", delta="In Building")
    with cols[3]:
        st.metric(label="🚪 Safe Exits", value=f"{safe_exits}", delta="Paths Open")
    with cols[4]:
        st.metric(label="🟢 Online Nodes", value=f"{online_nodes}/18", delta="Active Nodes")
    with cols[5]:
        st.metric(label="⏱️ Sim Clock", value=f"T + {current_tick:02d}s", delta="Running")


def render_health_panel(health_matrix: Dict[str, str]) -> None:
    """Render 5-aspect subsystem health status in Streamlit.

    Args:
        health_matrix: Dict of subsystem_name -> status_string ("Healthy", "Warning", "Critical").
    """
    st.subheader("🛡️ 5-Aspect Subsystem Health Matrix")

    cols = st.columns(5)
    subsystems = ["Simulation", "Communication", "Firmware", "Routing", "Dashboard"]

    for i, sys_name in enumerate(subsystems):
        status = health_matrix.get(sys_name, "Healthy")
        with cols[i]:
            if status == "Healthy":
                st.metric(label=sys_name, value="🟢 HEALTHY")
            elif status == "Warning":
                st.metric(label=sys_name, value="⚠️ WARNING")
            else:
                st.metric(label=sys_name, value="🔴 CRITICAL")

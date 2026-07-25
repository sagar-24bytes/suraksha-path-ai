"""
SurakshaPath AI — Live Telemetry Panel Component.

Renders real-time telemetry table detailing all building zones, sensor values,
fused hazard scores, evacuation states, health metrics, and LED animation states.
"""

from __future__ import annotations

from typing import Dict, List, Any
import pandas as pd
import streamlit as st
from communication.packet_schema import TelemetryPacket
from routing.path_manager import RouteResult


def render_telemetry_panel(
    telemetry: Dict[str, TelemetryPacket],
    routes: Dict[str, RouteResult],
) -> None:
    """Render pandas dataframe live telemetry table in Streamlit.

    Args:
        telemetry: Dict of zone_id -> TelemetryPacket.
        routes: Dict of zone_id -> RouteResult.
    """
    st.subheader("📊 Live Sensor Telemetry & Node Status")

    table_data: List[Dict[str, Any]] = []
    for zone_id, pkt in sorted(telemetry.items()):
        route = routes.get(zone_id)
        assigned_exit = route.target_exit if (route and not route.is_shelter_in_place) else ("SHELTER" if route and route.is_shelter_in_place else "X-01")
        path_cost = f"{route.estimated_time_s:.1f}s" if (route and not route.is_shelter_in_place) else "∞"

        table_data.append({
            "Zone": zone_id,
            "Node ID": pkt.node_id,
            "Temp (°C)": f"{pkt.temperature:.1f}",
            "Smoke Obsc.": f"{pkt.smoke_level * 100:.0f}%",
            "Flame": "🔥 YES" if pkt.flame_detected else "NO",
            "Hazard Score": f"{pkt.hazard_score:.3f}",
            "Evac State": pkt.evacuation_state,
            "Assigned Exit": assigned_exit,
            "Route Cost": path_cost,
            "LED Pattern": pkt.led_state,
            "Node Health": pkt.node_health,
            "Comm Link": pkt.communication_health,
            "Battery": f"{pkt.battery_level:.0f}%",
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

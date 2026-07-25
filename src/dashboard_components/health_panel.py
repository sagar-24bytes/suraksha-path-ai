"""
SurakshaPath AI — System Health Matrix Component.

Renders 5-aspect health status indicators for emergency operators:
  1. Digital Twin Simulation
  2. Transport Communication
  3. MicroPython Firmware
  4. Evacuation Routing Engine
  5. Commander Dashboard
"""

from __future__ import annotations

from typing import Dict
import streamlit as st


def render_health_panel(health_matrix: Dict[str, str]) -> None:
    """Render 5-aspect system health metrics in Streamlit.

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

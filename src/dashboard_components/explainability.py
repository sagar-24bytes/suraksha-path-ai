"""
SurakshaPath AI — Explainability Panel Component.

Renders mandatory Explainable AI (XAI) breakdown cards and reasoning text for judges
and emergency operators.

Explains:
  - Live formula mathematical breakdown (w_i · c_i · t_i)
  - Assigned emergency exit and total evacuation time
  - Specific reasons why routes changed (smoke, flame, blocked exit)
"""

from __future__ import annotations

from typing import Dict, Optional, Any
import streamlit as st
from communication.packet_schema import TelemetryPacket
from routing.path_manager import RouteResult


def render_explainability_panel(
    selected_zone_id: str,
    telemetry: Dict[str, TelemetryPacket],
    routes: Dict[str, RouteResult],
) -> None:
    """Render operator-friendly Explainability Panel for a selected zone.

    Args:
        selected_zone_id: Currently inspected zone ID.
        telemetry: Dict of zone_id -> TelemetryPacket.
        routes: Dict of zone_id -> RouteResult.
    """
    st.subheader(f"🔍 Explainability Panel — Zone {selected_zone_id}")

    pkt = telemetry.get(selected_zone_id, TelemetryPacket(zone_id=selected_zone_id))
    route = routes.get(selected_zone_id, RouteResult(source_node=selected_zone_id))

    # Column 1: Live Mathematical Evidence Fusion Breakdown Card
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Mathematical Evidence Fusion Breakdown**")
        w_t, w_s, w_f = 0.30, 0.25, 0.40
        t_norm = min(1.0, max(0.0, (pkt.temperature - 25.0) / 175.0))
        s_norm = pkt.smoke_level
        f_norm = 1.0 if pkt.flame_detected else 0.0

        st.code(
            f"Sensor Fusion Formula:\n"
            f"H_z = (w_T · T_norm + w_S · S_norm + w_F · F_norm) / Σw_i\n\n"
            f"  Temp ({pkt.temperature:.1f}°C)  : {w_t:.2f} × {t_norm:.2f} = {w_t * t_norm:.3f}\n"
            f"  Smoke ({pkt.smoke_level * 100:.0f}%)  : {w_s:.2f} × {s_norm:.2f} = {w_s * s_norm:.3f}\n"
            f"  Flame ({'YES' if pkt.flame_detected else 'NO'})   : {w_f:.2f} × {f_norm:.2f} = {w_f * f_norm:.3f}\n"
            f"  -----------------------------------------\n"
            f"  Composite Hazard Score = {pkt.hazard_score:.4f} ({pkt.evacuation_state})",
            language="markdown",
        )

    # Column 2: Operator Evacuation Routing Explanation
    with col2:
        st.markdown("**Evacuation Path Reasoning**")

        if route.is_shelter_in_place:
            st.error(
                f"🚨 **SHELTER IN PLACE REQUIRED**\n\n"
                f"**Reason**: All surrounding corridors or exits exceed hazardous thresholds (H_v ≥ 0.80). "
                f"No safe evacuation route exists from Zone {selected_zone_id}. "
                f"Occupants must seal doors and await fire response."
            )
        else:
            path_str = " → ".join(route.path) if route.path else "Direct Exit"
            reason_text = (
                f"Selected Exit **{route.target_exit}** via path `[{path_str}]`.\n\n"
                f"• **Estimated Evacuation Time**: `{route.estimated_time_s:.1f} seconds`\n"
                f"• **Cumulative Path Risk**: `{route.cumulative_risk:.2f}`\n"
            )

            if pkt.hazard_score >= 0.40:
                reason_text += f"• **Reroute Rationale**: Zone {selected_zone_id} elevated to {pkt.evacuation_state}. Dynamic edge costs increased penalty by {pkt.hazard_score * 100:.0f}%, routing occupants to safest exit {route.target_exit}."
            else:
                reason_text += f"• **Reroute Rationale**: Primary route is clear. Minimal hazard along corridor path."

            st.success(reason_text)

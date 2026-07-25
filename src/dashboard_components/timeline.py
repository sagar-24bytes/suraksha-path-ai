"""
SurakshaPath AI — Event Timeline Component.

Displays a chronological timeline of significant building emergency events:
  - 🔥 Fire Ignition Events
  - 💨 Smoke Obscuration Spread
  - 🚪 Exit Blockages
  - 🟢 Evacuation Reroutes
  - 👥 Occupant Guidance Updates
"""

from __future__ import annotations

from typing import Dict, List, Any
import streamlit as st


def render_event_timeline(alerts: List[Dict[str, Any]]) -> None:
    """Render chronological event timeline cards using native Streamlit components.

    Args:
        alerts: List of alert dicts [{tick, category, message, level}].
    """
    st.subheader("⏱️ Emergency Event Timeline")

    if not alerts:
        st.info("🟢 No emergency events recorded yet. System operating normally.")
        return

    # Render top timeline alerts using native Streamlit notification blocks
    for alert in alerts[:6]:
        tick = alert.get("tick", 0)
        cat = alert.get("category", "SYSTEM")
        msg = alert.get("message", "")
        level = alert.get("level", "INFO")

        if cat == "FIRE":
            icon = "🔥"
        elif cat == "SMOKE":
            icon = "💨"
        elif cat == "EVACUATION":
            icon = "🚪"
        elif cat == "HEALTH":
            icon = "⚠️"
        else:
            icon = "ℹ️"

        card_text = f"T + {tick:02d}s  |  {icon} [{cat}]  {msg}"

        if level in ["CRITICAL", "DANGER"]:
            st.error(card_text)
        elif level == "WARNING":
            st.warning(card_text)
        else:
            st.info(card_text)

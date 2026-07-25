"""
SurakshaPath AI — Alert Feed Component.

Displays chronological, prioritized alert logs for emergency operators.
"""

from __future__ import annotations

from typing import Dict, List, Any
import streamlit as st


def render_alerts_feed(alerts: List[Dict[str, Any]]) -> None:
    """Render chronological emergency alerts feed in Streamlit.

    Args:
        alerts: List of alert dictionaries [{tick, category, message, level}].
    """
    st.subheader("🚨 Real-Time Emergency Alerts Feed")

    if not alerts:
        st.info("🟢 System Normal. No active emergency alerts.")
        return

    # Render top 8 most recent alerts
    for alert in alerts[:8]:
        tick = alert.get("tick", 0)
        cat = alert.get("category", "SYSTEM")
        msg = alert.get("message", "")
        level = alert.get("level", "INFO")

        prefix = f"**[T + {tick:02d}s] [{cat}]**"

        if level == "CRITICAL":
            st.error(f"🚨 {prefix} {msg}")
        elif level == "DANGER":
            st.error(f"🔥 {prefix} {msg}")
        elif level == "WARNING":
            st.warning(f"⚠️ {prefix} {msg}")
        else:
            st.info(f"ℹ️ {prefix} {msg}")

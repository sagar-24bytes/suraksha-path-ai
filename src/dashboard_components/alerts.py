"""
SurakshaPath AI — Phase 8.4.2 Fixed-Height Alert Feed Component.

Displays chronological, prioritized alert logs in a fixed-height scrollable container
to prevent page height from growing indefinitely during long simulations.
"""

from __future__ import annotations

from typing import Dict, List, Any
import streamlit as st


_ALERTS_CSS = """
<style>
.alerts-container {
    max-height: 300px;
    overflow-y: auto;
    padding-right: 4px;
    scrollbar-width: thin;
    scrollbar-color: #cbd5e1 #f1f5f9;
}
.alerts-container::-webkit-scrollbar {
    width: 5px;
}
.alerts-container::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 3px;
}
.alert-card {
    padding: 6px 10px;
    margin-bottom: 5px;
    border-radius: 4px;
    font-size: 0.82rem;
    line-height: 1.3;
}
.alert-critical {
    background-color: #fef2f2;
    border-left: 3px solid #dc2626;
    color: #991b1b;
}
.alert-warning {
    background-color: #fffbeb;
    border-left: 3px solid #f59e0b;
    color: #92400e;
}
.alert-info {
    background-color: #f0f9ff;
    border-left: 3px solid #3b82f6;
    color: #1e40af;
}
</style>
"""


def render_alerts_feed(alerts: List[Dict[str, Any]]) -> None:
    """Render chronological emergency alerts feed in a fixed-height scrollable container.

    Args:
        alerts: List of alert dictionaries [{tick, category, message, level}].
    """
    st.subheader("\U0001f6a8 Emergency Alerts")

    if not alerts:
        st.info("\U0001f7e2 No active emergency alerts.")
        return

    st.markdown(_ALERTS_CSS, unsafe_allow_html=True)

    html_lines = ['<div class="alerts-container">']

    for alert in alerts[:10]:
        tick = alert.get("tick", 0)
        cat = alert.get("category", "SYSTEM")
        msg = alert.get("message", "")
        level = alert.get("level", "INFO")

        if level in ("CRITICAL", "DANGER"):
            css = "alert-critical"
            icon = "\U0001f6a8" if level == "CRITICAL" else "\U0001f525"
        elif level == "WARNING":
            css = "alert-warning"
            icon = "\u26a0\ufe0f"
        else:
            css = "alert-info"
            icon = "\u2139\ufe0f"

        line = (
            f'<div class="alert-card {css}">'
            f'{icon} <b>[T+{tick:02d}s] [{cat}]</b> {msg}'
            f'</div>'
        )
        html_lines.append(line)

    html_lines.append("</div>")
    st.markdown("".join(html_lines), unsafe_allow_html=True)

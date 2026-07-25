"""
SurakshaPath AI — Phase 8.4.2 Fixed-Height Intelligent Event Console.

Renders a fixed-height, internally scrollable emergency event console:
  - Fixed 420px scrollable container preventing page overflow.
  - Merges backend alerts with genuine AI decision events (detected from actual RouteResult changes).
  - Displays latest 15 operational story events chronologically.
  - High-contrast SCADA alert cards with category-specific styling.
  - No fabricated events — only displays what the backend actually produces.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
import streamlit as st


# ─── Timeline CSS (injected once) ───────────────────────────────────
_TIMELINE_CSS = """
<style>
.timeline-console {
    max-height: 420px;
    overflow-y: auto;
    padding-right: 6px;
    margin-bottom: 10px;
    scrollbar-width: thin;
    scrollbar-color: #cbd5e1 #f1f5f9;
}
.timeline-console::-webkit-scrollbar {
    width: 6px;
}
.timeline-console::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 3px;
}
.tl-card {
    padding: 8px 12px;
    margin-bottom: 6px;
    border-radius: 4px;
    font-size: 0.85rem;
    line-height: 1.35;
}
.tl-fire {
    background-color: #fef2f2;
    border-left: 4px solid #ef4444;
    color: #991b1b;
}
.tl-smoke {
    background-color: #fffbeb;
    border-left: 4px solid #f59e0b;
    color: #92400e;
}
.tl-ai {
    background-color: #ecfdf5;
    border-left: 4px solid #10b981;
    color: #065f46;
}
.tl-evac {
    background-color: #fef2f2;
    border-left: 4px solid #dc2626;
    color: #991b1b;
}
.tl-led {
    background-color: #f0fdf4;
    border-left: 4px solid #22c55e;
    color: #166534;
}
.tl-system {
    background-color: #f8fafc;
    border-left: 4px solid #64748b;
    color: #334155;
}
.tl-health {
    background-color: #fffbeb;
    border-left: 4px solid #eab308;
    color: #854d0e;
}
</style>
"""

# Category -> (CSS class, icon)
_CATEGORY_STYLE = {
    "FIRE": ("tl-fire", "\U0001f525"),
    "SMOKE": ("tl-smoke", "\U0001f4a8"),
    "AI_REROUTE": ("tl-ai", "\U0001f9e0"),
    "EVACUATION": ("tl-evac", "\U0001f6a8"),
    "LED_UPDATE": ("tl-led", "\U0001f4a1"),
    "HEALTH": ("tl-health", "\u26a0\ufe0f"),
    "SCENARIO": ("tl-system", "\U0001f3af"),
    "SYSTEM": ("tl-system", "\U0001f4a1"),
}


def render_event_timeline(
    alerts: List[Dict[str, Any]],
    ai_events: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Render fixed-height, internally scrollable SCADA event timeline console.

    Merges backend alerts with genuine AI decision events and displays them
    as a chronological emergency response story.

    Args:
        alerts: List of alert dicts from SystemCoordinator.alerts_history.
        ai_events: Optional list of genuine AI decision event dicts detected
                   from actual RouteResult changes between ticks.
    """
    st.subheader("\u23f1\ufe0f Emergency Event Timeline")

    if ai_events is None:
        ai_events = []

    # Merge all events and sort by tick descending (most recent first)
    all_events = list(alerts) + list(ai_events)

    if not all_events:
        st.info("\U0001f7e2 System Operating Normally \u2014 SCADA Telemetry Nominal")
        return

    all_events.sort(key=lambda e: e.get("tick", 0), reverse=True)

    # Take latest 15 events only — discard older entries
    recent_events = all_events[:15]

    # Inject CSS once
    st.markdown(_TIMELINE_CSS, unsafe_allow_html=True)

    # Build HTML timeline cards
    html_lines = ['<div class="timeline-console">']

    for event in recent_events:
        tick = event.get("tick", 0)
        cat = event.get("category", "SYSTEM")
        msg = event.get("message", "")
        level = event.get("level", "INFO")

        css_class, icon = _CATEGORY_STYLE.get(cat, ("tl-system", "\U0001f4a1"))

        # Override class for critical/danger level regardless of category
        if level in ("CRITICAL", "DANGER") and cat not in ("AI_REROUTE", "LED_UPDATE"):
            css_class = "tl-fire"

        line = (
            f'<div class="tl-card {css_class}">'
            f'<b>T+{tick:02d}s</b> &nbsp;|&nbsp; {icon} <b>[{cat}]</b>'
            f' &nbsp; {msg}</div>'
        )
        html_lines.append(line)

    html_lines.append("</div>")
    st.markdown("".join(html_lines), unsafe_allow_html=True)

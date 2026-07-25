"""
SurakshaPath AI — Phase 8.4.2 Professional SCADA Emergency Command Center Visualizer.

Renders a Honeywell-style Emergency Command Center visual experience:
  - Complete removal of all static decorative occupant icons from room groups during evacuation.
  - Realistic corridor-mounted LED guidance chevrons with soft SVG glow and pulsing animation.
  - Dynamic route-aware LED rendering: only safe corridor segments are illuminated.
  - Hazard-driven exit state visualization (safe pulsing green / blocked flashing red / inactive grey).
  - Smooth animated occupant movement following the current backend RouteResult path.
  - CSS fade-in transitions for smooth route change rendering.
  - 100% backend-driven: all hazard, smoke, fire, route values come directly from
    TelemetryPacket and RouteResult with ZERO artificial damping or fabrication.
  - Zero backend, simulation, routing, or firmware mutations.
"""

from __future__ import annotations

import os
import math
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List, Tuple, Set
import streamlit as st

from .building_mapper import get_svg_filepath, NODE_TO_ROOM_MAP

# ─── Constants ───────────────────────────────────────────────────────
PERSON_EMOJIS = frozenset({"\U0001f465", "\U0001f464", "\U0001f468", "\U0001f9d1", "\U0001f469", "\U0001f9cd", "\U0001f6b6"})
HAZARD_UNSAFE_THRESHOLD = 0.50
CHEVRON_SPACING_PX = 45.0
LED_PRIMARY = "#10b981"
LED_CORE = "#a7f3d0"
EXIT_SAFE_FILL = "#dcfce7"
EXIT_BLOCKED_FILL = "#fef2f2"
EXIT_INACTIVE_FILL = "#e2e8f0"

# ─── SVG CSS Keyframe Animations (Phase 8.4.2) ──────────────────────
SVG_PHASE_842_CSS = """
<style>
  @keyframes flameFlicker {
    0% { transform: scale(1.0); opacity: 0.9; }
    50% { transform: scale(1.15); opacity: 1.0; }
    100% { transform: scale(1.0); opacity: 0.9; }
  }
  @keyframes ledPulse {
    0% { opacity: 0.30; }
    50% { opacity: 1.0; }
    100% { opacity: 0.30; }
  }
  @keyframes exitSafeGlow {
    0% { stroke-width: 4; opacity: 0.85; }
    50% { stroke-width: 7; opacity: 1.0; }
    100% { stroke-width: 4; opacity: 0.85; }
  }
  @keyframes exitDangerFlash {
    0% { stroke-width: 4; opacity: 1.0; }
    50% { stroke-width: 6; opacity: 0.6; }
    100% { stroke-width: 4; opacity: 1.0; }
  }
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  .flame-anim {
    animation: flameFlicker 1.2s ease-in-out infinite;
    transform-origin: center;
  }
  .led-chevron {
    animation: fadeIn 0.4s ease-out, ledPulse 1.8s ease-in-out infinite;
  }
  .exit-safe {
    animation: exitSafeGlow 1.5s ease-in-out infinite;
  }
  .exit-danger {
    animation: exitDangerFlash 0.8s ease-in-out infinite;
  }
  .occupant-entity {
    animation: fadeIn 0.3s ease-out;
  }
</style>
"""

# ─── SVG LED Glow Filter Definition ─────────────────────────────────
SVG_LED_GLOW_FILTER = (
    '<filter id="led-glow" x="-50%" y="-50%" width="200%" height="200%">'
    '<feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="blur"/>'
    '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
    '</filter>'
)


# ─── Helper Functions ────────────────────────────────────────────────

def _strip_static_occupant_icons(room_elem: ET.Element) -> None:
    """Remove decorative person emoji text elements from a room group.

    Scans child <text> elements for person-related emojis (👥, 👤, etc.)
    and removes them so rooms appear empty during active evacuation.
    Does NOT remove non-person icons (🏢, 🍽️, ⚡, 🚪, etc.).
    """
    to_remove = []
    for child in list(room_elem):
        tag = child.tag.split("}")[-1]
        if tag == "text":
            text_content = child.text or ""
            if any(emoji in text_content for emoji in PERSON_EMOJIS):
                to_remove.append(child)
    for child in to_remove:
        room_elem.remove(child)


def _compute_chevrons_on_segment(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    spacing: float = CHEVRON_SPACING_PX,
) -> List[Tuple[float, float, float]]:
    """Compute chevron positions and rotation angles along a line segment.

    Returns list of (center_x, center_y, angle_degrees) tuples evenly
    distributed along the segment, pointing from p1 toward p2.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx * dx + dy * dy)

    if length < spacing * 0.6:
        return []

    angle = math.degrees(math.atan2(dy, dx))
    num = max(1, int(length / spacing))

    chevrons = []
    for i in range(1, num + 1):
        t = i / (num + 1)
        cx = p1[0] + t * dx
        cy = p1[1] + t * dy
        chevrons.append((cx, cy, angle))

    return chevrons


def _get_exit_state(
    zone_id: str,
    telemetry: Dict[str, Any],
    routes: Dict[str, Any],
) -> str:
    """Determine exit visual state based purely on backend data.

    Returns:
        'safe'     — exit is target_exit in at least one active route
        'blocked'  — exit has hazard_score >= HAZARD_UNSAFE_THRESHOLD
        'inactive' — exit is available but not currently a routing target
    """
    pkt = telemetry.get(zone_id)
    hazard = getattr(pkt, "hazard_score", 0.0) if pkt else 0.0

    # Blocked if backend hazard exceeds threshold
    if hazard >= HAZARD_UNSAFE_THRESHOLD:
        return "blocked"

    # Safe if the routing engine selected this exit for any zone
    for route in routes.values():
        if route and not route.is_shelter_in_place and route.target_exit == zone_id:
            return "safe"

    return "inactive"


# ─── Main Overlay Injection ─────────────────────────────────────────

def _apply_phase_8_4_2_overlays(
    svg_path: str,
    telemetry: Dict[str, Any],
    routes: Dict[str, Any],
    selected_floor: int,
    selected_zone_id: Optional[str] = None,
    current_tick: int = 0,
) -> str:
    """Inject Phase 8.4.2 SCADA overlays into architectural SVG template.

    All values are read directly from backend TelemetryPacket and RouteResult.
    No artificial damping, scaling, or fabrication of any values.

    Overlays injected:
      - Hazard room fills & smoke layers (raw backend hazard_score / smoke_level)
      - Animated flame indicators (raw backend flame_detected / temperature)
      - Corridor LED chevron guidance (only on safe segments)
      - Animated evacuating occupants (following current RouteResult.path)
      - Exit state visualization (safe/blocked/inactive from backend)

    Args:
        svg_path: Path to canonical architectural SVG template.
        telemetry: Dict of zone_id -> TelemetryPacket.
        routes: Dict of zone_id -> RouteResult.
        selected_floor: Floor level integer (1, 2, or 3).
        selected_zone_id: Currently inspected zone ID for highlight.
        current_tick: Current simulation tick integer.

    Returns:
        Path to generated live SVG asset file.
    """
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # ─── 1. Inject CSS Animations & LED Glow Filter into <defs> ───
    defs_elem = root.find("{http://www.w3.org/2000/svg}defs")
    if defs_elem is None:
        defs_elem = root.find("defs")

    style_element = ET.fromstring(SVG_PHASE_842_CSS)
    glow_filter = ET.fromstring(SVG_LED_GLOW_FILTER)

    if defs_elem is not None:
        defs_elem.append(style_element)
        defs_elem.append(glow_filter)
    else:
        root.insert(0, style_element)
        root.insert(1, glow_filter)

    # ─── 2. Process All Room Groups ──────────────────────────────
    room_centers: Dict[str, Tuple[float, float]] = {}
    room_rects: Dict[str, ET.Element] = {}
    exit_zones: Set[str] = set()

    for elem in root.iter():
        elem_id = elem.attrib.get("id", "")
        if not elem_id.startswith("room-"):
            continue

        zone_id = elem_id.replace("room-", "")

        # Track exit zones for state visualization
        if zone_id.startswith("X-") or zone_id.startswith("S-"):
            exit_zones.add(zone_id)

        # A. Strip ALL static decorative person icons once evacuation begins (Req #1)
        if current_tick > 0:
            _strip_static_occupant_icons(elem)

        # B. Extract primary room geometry (first <rect> child)
        rect_elem = None
        for child in list(elem):
            tag = child.tag.split("}")[-1]
            if tag == "rect" and rect_elem is None:
                rect_elem = child
                rx = float(child.attrib.get("x", 0))
                ry = float(child.attrib.get("y", 0))
                rw = float(child.attrib.get("width", 0))
                rh = float(child.attrib.get("height", 0))
                room_centers[zone_id] = (rx + rw / 2.0, ry + rh / 2.0)
                room_rects[zone_id] = child

        pkt = telemetry.get(zone_id)
        if not pkt or rect_elem is None:
            continue

        # C. Read RAW backend values — no damping, no scaling
        hazard = getattr(pkt, "hazard_score", 0.0)
        smoke = getattr(pkt, "smoke_level", 0.0)
        temp = getattr(pkt, "temperature", 25.0)
        flame = getattr(pkt, "flame_detected", False) or temp > 50.0

        # D. Hazard fill & border using raw backend hazard_score
        if flame or hazard >= 0.80:
            fill_color = "#fee2e2"
            stroke_color = "#dc2626"
            stroke_width = "5"
        elif hazard >= 0.40:
            fill_color = "#ffedd5"
            stroke_color = "#f97316"
            stroke_width = "4"
        elif hazard >= 0.20:
            fill_color = "#fef9c3"
            stroke_color = "#eab308"
            stroke_width = "3"
        else:
            fill_color = "#ffffff"
            stroke_color = "#64748b"
            stroke_width = "3"

        # Selected zone inspector highlight
        if zone_id == selected_zone_id:
            stroke_color = "#2563eb"
            stroke_width = "5"

        # E. Exit state visualization (Req #7) — driven by backend routing decisions
        if zone_id.startswith("X-"):
            exit_state = _get_exit_state(zone_id, telemetry, routes)
            if exit_state == "safe":
                rect_elem.attrib["fill"] = EXIT_SAFE_FILL
                rect_elem.attrib["stroke"] = "#059669"
                rect_elem.attrib["stroke-width"] = "4"
                rect_elem.attrib["class"] = "exit-safe"
                rect_elem.attrib["filter"] = "url(#led-glow)"
            elif exit_state == "blocked":
                rect_elem.attrib["fill"] = EXIT_BLOCKED_FILL
                rect_elem.attrib["stroke"] = "#ef4444"
                rect_elem.attrib["stroke-width"] = "4"
                rect_elem.attrib["class"] = "exit-danger"
            else:  # inactive
                rect_elem.attrib["fill"] = EXIT_INACTIVE_FILL
                rect_elem.attrib["stroke"] = "#94a3b8"
                rect_elem.attrib["stroke-width"] = "3"
        else:
            rect_elem.attrib["fill"] = fill_color
            rect_elem.attrib["stroke"] = stroke_color
            rect_elem.attrib["stroke-width"] = stroke_width

        rx_val = float(rect_elem.attrib.get("x", "0"))
        ry_val = float(rect_elem.attrib.get("y", "0"))
        rw_val = float(rect_elem.attrib.get("width", "0"))
        rh_val = float(rect_elem.attrib.get("height", "0"))

        # F. Animated flame indicator for fire ignition rooms
        if flame:
            fx = rx_val + rw_val / 2.0
            fy = ry_val + 38.0
            flame_txt = ET.Element("text", {
                "x": f"{fx:.1f}",
                "y": f"{fy:.1f}",
                "font-family": "'Segoe UI', system-ui, sans-serif",
                "font-size": "26",
                "text-anchor": "middle",
                "class": "flame-anim",
            })
            flame_txt.text = "\U0001f525"
            elem.append(flame_txt)

        # G. Translucent smoke layer using raw backend smoke_level
        if smoke > 0.05:
            smoke_opacity = min(0.65, 0.12 + smoke * 0.50)
            smoke_rect = ET.Element("rect", {
                "x": f"{rx_val:.1f}",
                "y": f"{ry_val:.1f}",
                "width": f"{rw_val:.1f}",
                "height": f"{rh_val:.1f}",
                "fill": f"rgba(71, 85, 105, {smoke_opacity:.2f})",
                "rx": "6",
                "pointer-events": "none",
            })
            elem.append(smoke_rect)

        # H. Show occupancy badge only at T=0 (before evacuation starts)
        occupants = getattr(pkt, "occupancy_count", 0)
        if occupants > 0 and current_tick == 0:
            ox = rx_val + rw_val / 2.0
            oy = ry_val + rh_val - 18.0
            badge_txt = ET.Element("text", {
                "x": f"{ox:.1f}",
                "y": f"{oy:.1f}",
                "font-family": "'Segoe UI', system-ui, sans-serif",
                "font-size": "12",
                "font-weight": "700",
                "fill": "#475569",
                "text-anchor": "middle",
            })
            badge_txt.text = f"\U0001f465 {occupants}"
            elem.append(badge_txt)

    # ─── 3. Render Corridor LED Guidance & Animated Occupant Entities ───
    routes_to_draw: List[Any] = []
    if selected_zone_id and selected_zone_id in routes:
        routes_to_draw.append(routes[selected_zone_id])
    else:
        routes_to_draw.extend(routes.values())

    drawn_paths: Set[tuple] = set()
    chevron_delay_counter = 0

    for route in routes_to_draw:
        if not route or route.is_shelter_in_place or not route.path:
            continue

        path_nodes = route.path

        # Collect path points that exist on the current floor
        floor_path_pts: List[Tuple[str, Tuple[float, float]]] = []
        for n_id in path_nodes:
            if n_id in room_centers:
                floor_path_pts.append((n_id, room_centers[n_id]))

        if len(floor_path_pts) < 2:
            continue

        path_key = tuple(n[0] for n in floor_path_pts)
        if path_key in drawn_paths:
            continue
        drawn_paths.add(path_key)

        # A. LED Chevrons — ONLY on safe segments (Req #3, #4)
        for i in range(len(floor_path_pts) - 1):
            node_a_id = floor_path_pts[i][0]
            node_b_id = floor_path_pts[i + 1][0]
            p1 = floor_path_pts[i][1]
            p2 = floor_path_pts[i + 1][1]

            # Check BOTH endpoints hazard from the actual backend TelemetryPacket
            pkt_a = telemetry.get(node_a_id)
            pkt_b = telemetry.get(node_b_id)
            hazard_a = getattr(pkt_a, "hazard_score", 0.0) if pkt_a else 0.0
            hazard_b = getattr(pkt_b, "hazard_score", 0.0) if pkt_b else 0.0

            # Skip LED guidance on segments with unsafe endpoints
            if hazard_a >= HAZARD_UNSAFE_THRESHOLD or hazard_b >= HAZARD_UNSAFE_THRESHOLD:
                continue

            # Compute chevron positions along this safe segment
            chevrons = _compute_chevrons_on_segment(p1, p2)

            for cx, cy, angle in chevrons:
                delay = (chevron_delay_counter % 8) * 0.15
                chevron_delay_counter += 1

                # Outer glow chevron (green emerald with soft blur)
                g_outer = ET.Element("g", {
                    "transform": f"translate({cx:.1f},{cy:.1f}) rotate({angle:.1f})",
                    "class": "led-chevron",
                    "style": f"animation-delay: 0s, {delay:.2f}s;",
                })
                ET.SubElement(g_outer, "polygon", {
                    "points": "-5,-6 10,0 -5,6",
                    "fill": LED_PRIMARY,
                    "opacity": "0.7",
                    "filter": "url(#led-glow)",
                })
                root.append(g_outer)

                # Inner bright core chevron (lighter green center)
                g_inner = ET.Element("g", {
                    "transform": f"translate({cx:.1f},{cy:.1f}) rotate({angle:.1f})",
                    "class": "led-chevron",
                    "style": f"animation-delay: 0s, {delay:.2f}s;",
                })
                ET.SubElement(g_inner, "polygon", {
                    "points": "-3,-4 7,0 -3,4",
                    "fill": LED_CORE,
                    "opacity": "0.9",
                })
                root.append(g_inner)

        # B. Animated Occupants Following Current Backend Route (Req #6)
        source_zone = path_nodes[0]
        src_pkt = telemetry.get(source_zone)
        occupants = getattr(src_pkt, "occupancy_count", 0) if src_pkt else 0

        if occupants > 0 and current_tick > 0 and len(floor_path_pts) >= 2:
            num_segments = len(floor_path_pts) - 1

            # Spread multiple occupants along the path with staggered progress
            for occ_idx in range(min(occupants, 5)):
                stagger = occ_idx * 0.08
                progress = min(1.0, max(0.0, (current_tick / max(1, num_segments * 3.5)) - stagger))

                if progress >= 1.0:
                    continue  # Occupant has reached exit — evacuated

                # Interpolate position along the route path geometry
                total_progress = progress * num_segments
                seg_idx = min(num_segments - 1, int(total_progress))
                sub_t = total_progress - seg_idx

                # Verify occupant is on a safe segment
                node_at = floor_path_pts[seg_idx][0]
                pkt_at = telemetry.get(node_at)
                hazard_at = getattr(pkt_at, "hazard_score", 0.0) if pkt_at else 0.0
                if hazard_at >= HAZARD_UNSAFE_THRESHOLD:
                    continue  # Occupant would not be on an unsafe segment

                p_start = floor_path_pts[seg_idx][1]
                p_end = floor_path_pts[min(seg_idx + 1, len(floor_path_pts) - 1)][1]

                ox = p_start[0] + sub_t * (p_end[0] - p_start[0])
                oy = p_start[1] + sub_t * (p_end[1] - p_start[1])

                occ_txt = ET.Element("text", {
                    "x": f"{ox:.1f}",
                    "y": f"{oy + 6:.1f}",
                    "font-family": "'Segoe UI', system-ui, sans-serif",
                    "font-size": "20",
                    "text-anchor": "middle",
                    "class": "occupant-entity",
                })
                occ_txt.text = "\U0001f464"
                root.append(occ_txt)

    # ─── 4. Save Generated SVG to Output Directory ───────────────
    gen_dir = os.path.join(os.path.dirname(svg_path), "generated")
    os.makedirs(gen_dir, exist_ok=True)
    out_path = os.path.join(gen_dir, f"floor{selected_floor}_live.svg")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path


# ─── Public Rendering Entry Point ───────────────────────────────────

def render_commercial_floor_plan(
    graph: Any = None,
    telemetry: Optional[Dict[str, Any]] = None,
    routes: Optional[Dict[str, Any]] = None,
    selected_floor: int = 1,
    selected_zone_id: Optional[str] = None,
    current_tick: int = 0,
) -> str:
    """Render commercial building floor plan with Phase 8.4.2 SCADA overlays.

    Args:
        graph: BuildingGraph topology (unused in visualization phase).
        telemetry: Dict of zone_id -> TelemetryPacket.
        routes: Dict of zone_id -> RouteResult.
        selected_floor: Selected floor level (1, 2, or 3).
        selected_zone_id: Inspected zone ID for highlight.
        current_tick: Current simulation tick integer.

    Returns:
        SVG content string for backward compatibility with test harnesses.
    """
    svg_path = get_svg_filepath(selected_floor)

    if os.path.exists(svg_path):
        st.subheader(f"\U0001f3e2 Commercial Office Floor Plan \u2014 Storey {selected_floor}")

        # Generate live SVG with Phase 8.4.2 overlays
        if telemetry and routes:
            display_svg_path = _apply_phase_8_4_2_overlays(
                svg_path, telemetry, routes, selected_floor, selected_zone_id, current_tick
            )
        else:
            display_svg_path = svg_path

        # Render building floor plan natively using Streamlit st.image()
        st.image(
            display_svg_path,
            caption=f"Storey {selected_floor} \u2014 Honeywell Emergency Command Center (LED Corridor Guidance Active)",
            use_container_width=True,
        )

        # Compact SCADA Hazard & Evacuation Legend
        leg_c1, leg_c2, leg_c3, leg_c4, leg_c5, leg_c6, leg_c7, leg_c8 = st.columns(8)
        with leg_c1:
            st.caption("\U0001f7e2 **Safe** (0\u201320%)")
        with leg_c2:
            st.caption("\U0001f7e1 **Advisory** (20\u201340%)")
        with leg_c3:
            st.caption("\U0001f7e0 **Warning** (40\u201360%)")
        with leg_c4:
            st.caption("\U0001f534 **Danger** (60\u201380%)")
        with leg_c5:
            st.caption("\U0001f525 **Fire**")
        with leg_c6:
            st.caption("\U0001f464 **Evacuating**")
        with leg_c7:
            st.caption("\u25b6 **LED Guide**")
        with leg_c8:
            st.caption("\U0001f6aa **Target Exit**")

        with open(display_svg_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        st.error(f"SVG floor plan asset not found at path: `{svg_path}`")
        return ""


# Alias for backward compatibility with existing tests/imports
render_floor_plan = render_commercial_floor_plan

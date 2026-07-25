"""
SurakshaPath AI — SCADA Animated Visualizer & AI Evacuation Guidance (Phase 8.4).

Pure SVG-animated emergency evacuation experience:
  - Localized Fire & Smoke Hazard Falloff (Deep Red ignition, Warm Orange adjacent, White safe).
  - Pure SVG CSS Animations (flameFlicker, ledFlow, routeGlow, exitPulse).
  - Corridor Flowing LED Directional Strips (>>>>>>>>>>>>) animating toward assigned safe exit.
  - Animated Occupant Evacuation Interpolation along concourse corridors toward target exits.
  - Recommended Exit Glow Accent (⭐ RECOMMENDED EXIT).
  - 100% driven passively by existing TelemetryPacket and RouteResult data.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List, Tuple
import streamlit as st

from .building_mapper import get_svg_filepath, NODE_TO_ROOM_MAP

# Embedded CSS Animations for Pure SVG Rendering
SVG_ANIMATION_CSS = """
<style>
  @keyframes flameFlicker {
    0% { transform: scale(1.0); opacity: 0.9; }
    50% { transform: scale(1.18); opacity: 1.0; }
    100% { transform: scale(1.0); opacity: 0.9; }
  }
  @keyframes ledFlow {
    from { stroke-dashoffset: 28; }
    to { stroke-dashoffset: 0; }
  }
  @keyframes routeGlow {
    0% { stroke-opacity: 0.75; stroke-width: 6.5px; }
    50% { stroke-opacity: 1.0; stroke-width: 8.5px; }
    100% { stroke-opacity: 0.75; stroke-width: 6.5px; }
  }
  @keyframes exitPulse {
    0% { stroke: #10b981; stroke-width: 5px; }
    50% { stroke: #059669; stroke-width: 8px; }
    100% { stroke: #10b981; stroke-width: 5px; }
  }
  .flame-anim {
    animation: flameFlicker 1.2s ease-in-out infinite;
    transform-origin: center;
  }
  .led-strip-anim {
    stroke-dasharray: 8 6;
    animation: ledFlow 0.7s linear infinite;
  }
  .route-line-anim {
    animation: routeGlow 1.8s ease-in-out infinite;
  }
  .target-exit-anim {
    animation: exitPulse 1.4s ease-in-out infinite;
  }
</style>
"""


def _apply_phase_8_4_overlays(
    svg_path: str,
    telemetry: Dict[str, Any],
    routes: Dict[str, Any],
    selected_floor: int,
    selected_zone_id: Optional[str] = None,
    current_tick: int = 0,
) -> str:
    """Inject Phase 8.4 SCADA hazard falloff, LED corridor strips, and animated occupant interpolation.

    Args:
        svg_path: Path to canonical architectural SVG template.
        telemetry: Dict of zone_id -> TelemetryPacket.
        routes: Dict of zone_id -> RouteResult.
        selected_floor: Floor level integer (1, 2, or 3).
        selected_zone_id: Currently inspected zone ID for route emphasis.
        current_tick: Current simulation tick integer.

    Returns:
        Path to generated live SVG asset file.
    """
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Inject SVG Animation CSS Block into <defs> or <svg> root
    defs_elem = root.find("{http://www.w3.org/2000/svg}defs")
    if defs_elem is None:
        defs_elem = root.find("defs")
    
    style_element = ET.fromstring(SVG_ANIMATION_CSS)
    if defs_elem is not None:
        defs_elem.append(style_element)
    else:
        root.insert(0, style_element)

    room_centers: Dict[str, Tuple[float, float]] = {}
    room_rects: Dict[str, ET.Element] = {}

    # 1. Process all room groups matching id="room-ZONE_ID"
    for elem in root.iter():
        elem_id = elem.attrib.get("id", "")
        if elem_id.startswith("room-"):
            zone_id = elem_id.replace("room-", "")
            pkt = telemetry.get(zone_id)

            rect_elem = None
            for child in elem:
                tag = child.tag.split("}")[-1]
                if tag == "rect":
                    rect_elem = child
                    rx = float(child.attrib.get("x", 0))
                    ry = float(child.attrib.get("y", 0))
                    rw = float(child.attrib.get("width", 0))
                    rh = float(child.attrib.get("height", 0))
                    room_centers[zone_id] = (rx + rw / 2.0, ry + rh / 2.0)
                    room_rects[zone_id] = child
                    break

            if not pkt or rect_elem is None:
                continue

            hazard = getattr(pkt, "hazard_score", 0.0)
            smoke = getattr(pkt, "smoke_level", 0.0)
            temp = getattr(pkt, "temperature", 25.0)
            flame = getattr(pkt, "flame_detected", False) or temp > 50.0

            # Localized Hazard Falloff Fill & Border
            if flame or hazard >= 0.80:
                fill_color = "#fee2e2"  # Deep red ignition fill
                stroke_color = "#dc2626"  # Alarm red border
                stroke_width = "5"
            elif hazard >= 0.40:
                fill_color = "#ffedd5"  # Warm orange adjacent fill
                stroke_color = "#f97316"  # Orange border
                stroke_width = "4"
            elif hazard >= 0.20:
                fill_color = "#fef9c3"  # Light yellow fill
                stroke_color = "#eab308"  # Amber border
                stroke_width = "3"
            else:
                fill_color = "#ffffff"  # Clean white safe room fill
                stroke_color = "#64748b"  # Slate grey border
                stroke_width = "3"

            if zone_id == selected_zone_id:
                stroke_color = "#2563eb"
                stroke_width = "5"

            if not (zone_id.startswith("X-") and hazard < 0.20):
                rect_elem.attrib["fill"] = fill_color
            rect_elem.attrib["stroke"] = stroke_color
            rect_elem.attrib["stroke-width"] = stroke_width

            rx = float(rect_elem.attrib.get("x", "0"))
            ry = float(rect_elem.attrib.get("y", "0"))
            rw = float(rect_elem.attrib.get("width", "0"))
            rh = float(rect_elem.attrib.get("height", "0"))

            # Animated Flame Indicator for Fire Ignition Rooms
            if flame:
                fx = rx + rw / 2.0
                fy = ry + 38.0
                flame_txt = ET.Element("text", {
                    "x": f"{fx:.1f}",
                    "y": f"{fy:.1f}",
                    "font-family": "'Segoe UI', system-ui, sans-serif",
                    "font-size": "26",
                    "text-anchor": "middle",
                    "class": "flame-anim",
                })
                flame_txt.text = "🔥"
                elem.append(flame_txt)

            # Translucent Smoke Layer
            if smoke > 0.05:
                smoke_opacity = min(0.65, 0.12 + smoke * 0.50)
                smoke_rect = ET.Element("rect", {
                    "x": f"{rx:.1f}",
                    "y": f"{ry:.1f}",
                    "width": f"{rw:.1f}",
                    "height": f"{rh:.1f}",
                    "fill": f"rgba(71, 85, 105, {smoke_opacity:.2f})",
                    "rx": "6",
                    "pointer-events": "none",
                })
                elem.append(smoke_rect)

    # 2. Render Animated Evacuation Routes, Flowing LED Strips, & Occupants
    routes_to_draw = []
    if selected_zone_id and selected_zone_id in routes:
        routes_to_draw.append(routes[selected_zone_id])
    else:
        routes_to_draw.extend(routes.values())

    drawn_paths = set()
    for route in routes_to_draw:
        if not route or route.is_shelter_in_place or not route.path:
            continue

        path_nodes = route.path
        floor_path_pts = []
        for n_id in path_nodes:
            if n_id in room_centers:
                floor_path_pts.append((n_id, room_centers[n_id]))

        if len(floor_path_pts) >= 2:
            path_key = tuple(n[0] for n in floor_path_pts)
            if path_key in drawn_paths:
                continue
            drawn_paths.add(path_key)

            path_d = "M " + " L ".join(f"{p[1][0]:.1f} {p[1][1]:.1f}" for p in floor_path_pts)
            
            # A. Glowing Emerald Green Route Vector Line
            route_path_elem = ET.Element("path", {
                "d": path_d,
                "stroke": "#10b981",
                "stroke-width": "7",
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
                "fill": "none",
                "class": "route-line-anim",
            })
            root.append(route_path_elem)

            # B. Flowing LED Corridor Guidance Strip (>>>>>>>>>>>>)
            led_strip_elem = ET.Element("path", {
                "d": path_d,
                "stroke": "#059669",
                "stroke-width": "3",
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
                "fill": "none",
                "class": "led-strip-anim",
            })
            root.append(led_strip_elem)

            # C. Route Direction Markers (➔)
            for i in range(len(floor_path_pts) - 1):
                p1 = floor_path_pts[i][1]
                p2 = floor_path_pts[i + 1][1]
                mx = (p1[0] + p2[0]) / 2.0
                my = (p1[1] + p2[1]) / 2.0

                arrow_txt = ET.Element("text", {
                    "x": f"{mx:.1f}",
                    "y": f"{my + 6:.1f}",
                    "font-family": "'Segoe UI', system-ui, sans-serif",
                    "font-size": "20",
                    "font-weight": "800",
                    "fill": "#047857",
                    "text-anchor": "middle",
                })
                arrow_txt.text = "➔"
                root.append(arrow_txt)

            # D. Animated Occupant Evacuation Position Interpolation (👤)
            source_zone = path_nodes[0]
            src_pkt = telemetry.get(source_zone)
            occupants = getattr(src_pkt, "occupancy_count", 0) if src_pkt else 0

            if occupants > 0 and len(floor_path_pts) >= 2:
                # Interpolate occupant along path based on current simulation tick T
                num_segments = len(floor_path_pts) - 1
                prog = (current_tick % 10) / 10.0
                seg_idx = min(num_segments - 1, int(prog * num_segments))
                sub_t = (prog * num_segments) - seg_idx

                p_start = floor_path_pts[seg_idx][1]
                p_end = floor_path_pts[seg_idx + 1][1]

                ox = p_start[0] + sub_t * (p_end[0] - p_start[0])
                oy = p_start[1] + sub_t * (p_end[1] - p_start[1])

                occ_anim_txt = ET.Element("text", {
                    "x": f"{ox:.1f}",
                    "y": f"{oy + 5:.1f}",
                    "font-family": "'Segoe UI', system-ui, sans-serif",
                    "font-size": "22",
                    "text-anchor": "middle",
                })
                occ_anim_txt.text = "👤"
                root.append(occ_anim_txt)

            # E. Recommended Exit Glow Accent
            target_exit = route.target_exit
            if target_exit in room_rects:
                ex_rect = room_rects[target_exit]
                ex_rect.attrib["class"] = "target-exit-anim"

    # Save to generated directory
    gen_dir = os.path.join(os.path.dirname(svg_path), "generated")
    os.makedirs(gen_dir, exist_ok=True)
    out_path = os.path.join(gen_dir, f"floor{selected_floor}_live.svg")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path


def render_commercial_floor_plan(
    graph: Any = None,
    telemetry: Optional[Dict[str, Any]] = None,
    routes: Optional[Dict[str, Any]] = None,
    selected_floor: int = 1,
    selected_zone_id: Optional[str] = None,
    current_tick: int = 0,
) -> str:
    """Render clean architectural commercial building floor plan with Phase 8.4 SCADA animations.

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
        st.subheader(f"🏢 Commercial Office Floor Plan — Storey {selected_floor} (SCADA Evacuation Mode)")

        # Generate live SVG asset with Phase 8.4 SCADA animations
        if telemetry and routes:
            display_svg_path = _apply_phase_8_4_overlays(
                svg_path, telemetry, routes, selected_floor, selected_zone_id, current_tick
            )
        else:
            display_svg_path = svg_path

        # Render building floor plan natively using Streamlit's st.image component
        st.image(
            display_svg_path,
            caption=f"Storey {selected_floor} Emergency Command Center (Phase 8.4 LED & Animated Evacuation Active)",
            use_container_width=True,
        )

        # Render compact SCADA Hazard & Evacuation Legend
        leg_c1, leg_c2, leg_c3, leg_c4, leg_c5, leg_c6, leg_c7, leg_c8 = st.columns(8)
        with leg_c1:
            st.caption("🟢 **Safe** (0–20%)")
        with leg_c2:
            st.caption("🟡 **Advisory** (20–40%)")
        with leg_c3:
            st.caption("🟠 **Warning** (40–60%)")
        with leg_c4:
            st.caption("🔴 **Danger** (60–80%)")
        with leg_c5:
            st.caption("🔥 **Fire Ignition**")
        with leg_c6:
            st.caption("👤 **Evacuating**")
        with leg_c7:
            st.caption("➔ **AI Route**")
        with leg_c8:
            st.caption("🟢 **LED Guidance**")

        with open(display_svg_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        st.error(f"SVG floor plan asset not found at path: `{svg_path}`")
        return ""


# Alias for backward compatibility with existing tests/imports
render_floor_plan = render_commercial_floor_plan

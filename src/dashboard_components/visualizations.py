"""
SurakshaPath AI — Plotly Floor Plan & Route Overlay Component.

Renders interactive Plotly 2D floor plan layout with smooth HSL hazard color transitions
and animated dynamic evacuation route arrows.

Color Gradient Mapping:
  - SAFE (Hazard < 0.20): Emerald Green (#2ecc71)
  - ADVISORY (0.20–0.40): Sunflower Yellow (#f1c40f)
  - WARNING (0.40–0.60): Carrot Orange (#e67e22)
  - DANGER (0.60–0.80): Alizarin Red (#e74c3c)
  - CRITICAL (>= 0.80): Midnight Black (#1a1a1a)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import plotly.graph_objects as go
from communication.packet_schema import TelemetryPacket
from routing.graph import BuildingGraph
from routing.path_manager import RouteResult


def get_hazard_color(hazard_score: float, is_blocked: bool = False) -> str:
    """Map hazard score to smooth hex color string."""
    if is_blocked or hazard_score >= 0.80:
        return "#1a1a1a"  # Midnight Black / Blocked
    elif hazard_score >= 0.60:
        return "#e74c3c"  # Alizarin Red / Danger
    elif hazard_score >= 0.40:
        return "#e67e22"  # Carrot Orange / Warning
    elif hazard_score >= 0.20:
        return "#f1c40f"  # Sunflower Yellow / Advisory
    return "#2ecc71"      # Emerald Green / Safe


def render_floor_plan(
    graph: BuildingGraph,
    telemetry: Dict[str, TelemetryPacket],
    routes: Dict[str, RouteResult],
    selected_floor: int = 1,
    selected_zone_id: Optional[str] = None,
) -> go.Figure:
    """Render Plotly 2D Floor Plan with node status, edges, and route arrows.

    Args:
        graph: BuildingGraph topology.
        telemetry: Dict of zone_id -> TelemetryPacket.
        routes: Dict of zone_id -> RouteResult.
        selected_floor: Floor level to filter (1 or 2).
        selected_zone_id: Highlighted zone for explainability focus.

    Returns:
        Plotly Figure instance.
    """
    fig = go.Figure()

    # Filter nodes for selected floor
    floor_nodes = {n_id: node for n_id, node in graph.nodes.items() if node.floor == selected_floor}
    floor_node_ids = set(floor_nodes.keys())

    # 1. Draw Physical Connecting Edges (corridors/doors)
    drawn_edges = set()
    for (u, v), edge in graph.edges.items():
        if u in floor_node_ids and v in floor_node_ids:
            edge_pair = tuple(sorted([u, v]))
            if edge_pair in drawn_edges:
                continue
            drawn_edges.add(edge_pair)

            node_u, node_v = floor_nodes[u], floor_nodes[v]
            line_color = "#34495e"
            line_width = 2
            dash_style = "dot" if edge.has_fire_door else "solid"

            fig.add_trace(go.Scatter(
                x=[node_u.x, node_v.x],
                y=[node_u.y, node_v.y],
                mode="lines",
                line=dict(color=line_color, width=line_width, dash=dash_style),
                hoverinfo="none",
                showlegend=False,
            ))

    # 2. Draw Dynamic Evacuation Route Arrows
    drawn_route_edges = set()
    for src_id, route in routes.items():
        if route.is_shelter_in_place or not route.path:
            continue
        
        path = route.path
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if u in floor_node_ids and v in floor_node_ids:
                route_pair = (u, v)
                if route_pair in drawn_route_edges:
                    continue
                drawn_route_edges.add(route_pair)

                node_u, node_v = floor_nodes[u], floor_nodes[v]
                fig.add_trace(go.Scatter(
                    x=[node_u.x, node_v.x],
                    y=[node_u.y, node_v.y],
                    mode="lines+markers",
                    line=dict(color="#3498db", width=4),  # Electric Blue Route Line
                    marker=dict(symbol="arrow", size=12, angleref="previous", color="#3498db"),
                    hoverinfo="text",
                    hovertext=f"Evacuation Route Segment: {u} → {v}",
                    showlegend=False,
                ))

    # 3. Draw Nodes (Rooms, Corridors, Exits)
    node_x, node_y = [], []
    node_colors, node_sizes, node_symbols, hover_texts, node_labels = [], [], [], [], []

    for n_id, node in floor_nodes.items():
        pkt = telemetry.get(n_id, TelemetryPacket(zone_id=n_id))
        hazard = pkt.hazard_score
        is_blocked = (pkt.evacuation_state == "SHELTER" or hazard >= 0.80)

        node_x.append(node.x)
        node_y.append(node.y)
        node_colors.append(get_hazard_color(hazard, is_blocked))
        node_labels.append(n_id)

        # Highlight selection
        if n_id == selected_zone_id:
            node_sizes.append(42)
            node_symbols.append("hexagon")
        elif node.is_exit:
            node_sizes.append(36)
            node_symbols.append("square")
        else:
            node_sizes.append(30)
            node_symbols.append("circle")

        hover_info = (
            f"<b>Zone {node.id}</b> ({node.name})<br/>"
            f"Hazard Score: <b>{hazard:.2f}</b><br/>"
            f"Temp: {pkt.temperature}°C | Smoke: {pkt.smoke_level * 100:.0f}%<br/>"
            f"Flame: {'🔥 YES' if pkt.flame_detected else 'NO'}<br/>"
            f"State: {pkt.evacuation_state} | LED: {pkt.led_state}<br/>"
            f"Assigned Exit: {pkt.recommended_exit}"
        )
        hover_texts.append(hover_info)

    # Scatter trace for nodes
    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            symbol=node_symbols,
            line=dict(color="#ffffff", width=2),
        ),
        text=node_labels,
        textposition="middle center",
        textfont=dict(color="#ffffff", size=10, family="monospace"),
        hoverinfo="text",
        hovertext=hover_texts,
        showlegend=False,
    ))

    # Layout styling (Dark Theme Command Center)
    fig.update_layout(
        paper_bgcolor="#0f0f1a",
        plot_bgcolor="#161625",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 16]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 11]),
        margin=dict(l=10, r=10, t=10, b=10),
        height=480,
    )

    return fig

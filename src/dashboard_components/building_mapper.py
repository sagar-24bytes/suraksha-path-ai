"""
SurakshaPath AI — Building Architecture Mapping Layer.

Maps internal backend graph node IDs (R-101, R-105, C-01, X-01, etc.) to:
  - Human-readable room names (Server Room, Reception, Kitchen, etc.)
  - Storey floor assignments (Floor 1, Floor 2, Floor 3)
  - SVG floor plan asset file paths (assets/building/floor1.svg, etc.)
"""

from __future__ import annotations

import os
from typing import Dict, Any

# Map backend node ID to human-readable visual room metadata
NODE_TO_ROOM_MAP: Dict[str, Dict[str, Any]] = {
    # Floor 1 Nodes
    "L-01": {"name": "Main Reception & Lobby", "floor": 1, "type": "lobby"},
    "R-101": {"name": "Receptionist Office", "floor": 1, "type": "office"},
    "R-102": {"name": "Meeting Room Alpha", "floor": 1, "type": "meeting"},
    "R-103": {"name": "Security & Visitor Office", "floor": 1, "type": "security"},
    "R-104": {"name": "Ground Washrooms", "floor": 1, "type": "washroom"},
    "R-105": {"name": "Cafeteria & Kitchen", "floor": 1, "type": "kitchen"},
    "R-106": {"name": "Electrical & HVAC Room", "floor": 1, "type": "electrical"},
    "C-01": {"name": "Central Main Corridor (C-01)", "floor": 1, "type": "corridor"},
    "S-01": {"name": "Stairwell & Lift Shaft S1", "floor": 1, "type": "stairwell"},
    "X-01": {"name": "Main Entrance Exit X-01", "floor": 1, "type": "exit"},
    "X-02": {"name": "East Emergency Exit X-02", "floor": 1, "type": "exit"},

    # Floor 2 Nodes
    "R-201": {"name": "Executive Office 201 (HR)", "floor": 2, "type": "office"},
    "R-202": {"name": "Server Hall & Data Center", "floor": 2, "type": "server"},
    "R-203": {"name": "Open Workspace 203", "floor": 2, "type": "workspace"},
    "R-204": {"name": "Research Laboratory 204", "floor": 2, "type": "lab"},
    "C-02": {"name": "West Operations Corridor (C-02)", "floor": 2, "type": "corridor"},
    "C-03": {"name": "East Corridor (C-03)", "floor": 2, "type": "corridor"},
    "X-03": {"name": "Fire Escape Stair Exit X-03", "floor": 2, "type": "exit"},

    # Floor 3 Nodes (Roof / Management)
    "R-301": {"name": "HVAC & Solar Power Room", "floor": 3, "type": "utility"},
    "R-302": {"name": "Executive Lounge & Archive", "floor": 3, "type": "lounge"},
    "R-303": {"name": "Executive Conference Hall", "floor": 3, "type": "conference"},
}


def get_room_display_name(node_id: str) -> str:
    """Retrieve human-readable room name for a given node ID."""
    info = NODE_TO_ROOM_MAP.get(node_id)
    if info:
        return info["name"]
    return f"Room {node_id}"


def get_svg_filepath(floor_num: int) -> str:
    """Retrieve absolute path to SVG floor plan asset for a given floor number."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    floor_file = f"floor{min(3, max(1, floor_num))}.svg"
    return os.path.join(project_root, "assets", "building", floor_file)

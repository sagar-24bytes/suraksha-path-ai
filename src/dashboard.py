"""
SurakshaPath AI — Dashboard Entry Point.

Main Streamlit application. This is the single entry point:
    streamlit run src/dashboard.py

Phase 1: Dark-themed shell with layout placeholders and
          session state initialization. No simulation,
          no graphs, no Plotly yet.
"""

from __future__ import annotations

import streamlit as st

from config_loader import load_all_configs
from models import HazardLevel, SystemStatus


# =============================================================
# Constants
# =============================================================

# --- Color Palette (Dark Command Center Theme) ---
COLOR_BG_PRIMARY = "#0f0f1a"
COLOR_BG_CARD = "#16213e"
COLOR_BG_SIDEBAR = "#1a1a2e"
COLOR_TEXT_PRIMARY = "#eaeaea"
COLOR_TEXT_SECONDARY = "#8892b0"
COLOR_ACCENT = "#e94560"
COLOR_SAFE = "#2ecc71"
COLOR_ADVISORY = "#f1c40f"
COLOR_WARNING = "#e67e22"
COLOR_DANGER = "#e74c3c"
COLOR_CRITICAL = "#2c3e50"
COLOR_ROUTE = "#3498db"
COLOR_EXIT = "#27ae60"
COLOR_BLOCKED = "#95a5a6"

# --- System Status Display ---
STATUS_CONFIG = {
    SystemStatus.NORMAL:   {"emoji": "🟢", "label": "SYSTEM READY",   "color": COLOR_SAFE},
    SystemStatus.ADVISORY: {"emoji": "🟡", "label": "ADVISORY",       "color": COLOR_ADVISORY},
    SystemStatus.ALERT:    {"emoji": "🔴", "label": "ALERT",          "color": COLOR_DANGER},
    SystemStatus.FAILSAFE: {"emoji": "⚫", "label": "FAILSAFE ACTIVE","color": COLOR_CRITICAL},
}


# =============================================================
# Dark Theme CSS
# =============================================================

DARK_THEME_CSS = """
<style>
    /* ---- Global Background ---- */
    .stApp {
        background-color: #0f0f1a;
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background-color: #1a1a2e;
        border-right: 1px solid #2a2a4a;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: #c0c0d0;
    }

    /* ---- Headers ---- */
    .stApp h1 { color: #eaeaea; }
    .stApp h2 { color: #d0d0e0; }
    .stApp h3 { color: #b0b0c0; }

    /* ---- Main text ---- */
    .stApp p, .stApp li, .stApp label, .stApp span {
        color: #c0c0d0;
    }

    /* ---- Metric cards ---- */
    div[data-testid="stMetric"] {
        background-color: #16213e;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #2a2a4a;
    }
    div[data-testid="stMetric"] label {
        color: #8892b0 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #eaeaea !important;
    }

    /* ---- Cards / Containers ---- */
    div[data-testid="stExpander"] {
        background-color: #16213e;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
    }

    /* ---- Buttons ---- */
    .stButton > button {
        background-color: #16213e;
        color: #eaeaea;
        border: 1px solid #3a3a5a;
        border-radius: 6px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #1f2b47;
        border-color: #e94560;
        color: #ffffff;
    }

    /* ---- Select boxes ---- */
    div[data-testid="stSelectbox"] > div > div {
        background-color: #16213e;
        color: #eaeaea;
        border: 1px solid #3a3a5a;
    }

    /* ---- Horizontal rule ---- */
    hr {
        border-color: #2a2a4a;
    }

    /* ---- Custom: placeholder panel ---- */
    .placeholder-panel {
        background-color: #16213e;
        border: 1px dashed #3a3a5a;
        border-radius: 10px;
        padding: 30px 20px;
        text-align: center;
        color: #5a5a7a;
        margin: 8px 0;
    }
    .placeholder-panel .icon {
        font-size: 2em;
        margin-bottom: 8px;
    }
    .placeholder-panel .label {
        font-size: 0.9em;
        font-weight: 500;
    }

    /* ---- Custom: header bar ---- */
    .header-bar {
        background: linear-gradient(135deg, #16213e 0%, #1a1a3e 100%);
        border-radius: 10px;
        padding: 16px 24px;
        margin-bottom: 16px;
        border: 1px solid #2a2a4a;
    }
    .header-title {
        color: #eaeaea;
        font-size: 1.6em;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        color: #8892b0;
        font-size: 0.9em;
        margin: 0;
    }

    /* ---- Custom: status badge ---- */
    .status-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* ---- Scrollable container ---- */
    .scrollable-feed {
        max-height: 250px;
        overflow-y: auto;
        padding: 8px;
        background-color: #16213e;
        border-radius: 8px;
        border: 1px solid #2a2a4a;
    }

    /* ---- Hide Streamlit branding ---- */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background-color: #0f0f1a; }
</style>
"""


# =============================================================
# Session State Initialization
# =============================================================

def _init_session_state(config) -> None:
    """Initialize all session state variables needed across phases.

    Only sets values that are NOT already present, so this is
    safe to call on every rerun.

    Args:
        config: Loaded AllConfig instance.
    """
    defaults = {
        # --- Simulation control ---
        "simulation_running": False,
        "current_tick": 0,
        "speed_multiplier": config.app.default_speed,
        "selected_scenario": config.app.default_scenario,
        "selected_zone": None,
        "selected_floor": 1,

        # --- Configuration references ---
        "config": config,

        # --- Simulation state (populated by future phases) ---
        "zone_hazard_states": {},
        "sensor_readings": [],
        "routes": {},
        "alerts": [],
        "blocked_edges": [],
        "fire_intensities": {},
        "smoke_levels": {},
        "evacuation_progress": {
            "total": 0,
            "evacuated": 0,
            "remaining": 0,
        },
        "system_status": SystemStatus.NORMAL,

        # --- History buffer for trend charts ---
        "snapshot_history": [],

        # --- Sensor health tracking ---
        "sensor_statuses": {},

        # --- Occupancy tracking ---
        "occupancy": {},
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# =============================================================
# Placeholder Panel Helper
# =============================================================

def _placeholder_panel(icon: str, label: str, sublabel: str = "") -> None:
    """Render a styled placeholder panel for a future feature.

    Args:
        icon:     Emoji icon displayed large.
        label:    Primary label text.
        sublabel: Optional secondary description.
    """
    sub_html = f'<div style="color:#4a4a6a;font-size:0.75em;margin-top:4px;">{sublabel}</div>' if sublabel else ""
    st.markdown(
        f"""
        <div class="placeholder-panel">
            <div class="icon">{icon}</div>
            <div class="label">{label}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================
# Header Bar
# =============================================================

def _render_header() -> None:
    """Render the top header bar with title, clock, and status."""
    config = st.session_state.config
    status = st.session_state.system_status
    status_info = STATUS_CONFIG[status]
    tick = st.session_state.current_tick

    minutes = tick // 60
    seconds = tick % 60
    clock_str = f"T + {minutes:02d}:{seconds:02d}"

    col_title, col_clock, col_status = st.columns([5, 2, 2])

    with col_title:
        st.markdown(
            f"""
            <div class="header-bar">
                <div class="header-title">🔥 {config.app.title}</div>
                <div class="header-subtitle">{config.app.subtitle}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_clock:
        st.markdown(
            f"""
            <div class="header-bar" style="text-align:center;">
                <div style="color:#8892b0;font-size:0.8em;">SIMULATION CLOCK</div>
                <div style="color:#eaeaea;font-size:1.4em;font-weight:700;font-family:monospace;">
                    {clock_str}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_status:
        st.markdown(
            f"""
            <div class="header-bar" style="text-align:center;">
                <div style="color:#8892b0;font-size:0.8em;">SYSTEM STATUS</div>
                <div style="margin-top:4px;">
                    <span class="status-badge"
                          style="background-color:{status_info['color']}20;
                                 color:{status_info['color']};
                                 border:1px solid {status_info['color']};">
                        {status_info['emoji']} {status_info['label']}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================================================
# Sidebar
# =============================================================

def _render_sidebar() -> None:
    """Render the sidebar with scenario selection and controls."""
    config = st.session_state.config

    with st.sidebar:
        st.markdown("### 🎛️ Control Panel")
        st.markdown("---")

        # --- Scenario Selection ---
        st.markdown("**📋 Scenario**")
        scenario_keys = list(config.scenarios.keys())
        scenario_names = [config.scenarios[k].name for k in scenario_keys]

        current_idx = 0
        if st.session_state.selected_scenario in scenario_keys:
            current_idx = scenario_keys.index(st.session_state.selected_scenario)

        selected_name = st.selectbox(
            "Select scenario",
            scenario_names,
            index=current_idx,
            label_visibility="collapsed",
        )
        selected_key = scenario_keys[scenario_names.index(selected_name)]
        st.session_state.selected_scenario = selected_key

        # Scenario description
        scenario = config.scenarios[selected_key]
        with st.expander("ℹ️ Scenario Details", expanded=False):
            st.markdown(f"**{scenario.name}**")
            st.markdown(
                f"<div style='color:#8892b0;font-size:0.85em;'>{scenario.description}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"⏱ Duration: **{scenario.duration_s}s**")

        st.markdown("---")

        # --- Simulation Controls ---
        st.markdown("**🕹️ Simulation**")
        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)

        with ctrl_col1:
            if st.session_state.simulation_running:
                st.button("⏸", key="btn_pause", help="Pause simulation", use_container_width=True)
            else:
                st.button("▶", key="btn_play", help="Start simulation", use_container_width=True)

        with ctrl_col2:
            st.button("⏭", key="btn_step", help="Advance one tick", use_container_width=True)

        with ctrl_col3:
            st.button("⏹", key="btn_reset", help="Reset simulation", use_container_width=True)

        with ctrl_col4:
            pass  # Reserved for future use

        st.markdown("")

        # --- Speed Control ---
        st.session_state.speed_multiplier = st.select_slider(
            "⚡ Speed",
            options=[1, 2, 5, 10],
            value=st.session_state.speed_multiplier,
        )

        st.markdown("---")

        # --- Building Info ---
        st.markdown("**🏢 Building**")
        st.markdown(f"_{config.building.name}_")

        bld_col1, bld_col2 = st.columns(2)
        with bld_col1:
            st.metric("Floors", config.building.floors)
        with bld_col2:
            st.metric("Zones", len(config.building.zones))

        exits = config.building.get_exit_ids()
        st.markdown(f"🚪 Exits: `{'`, `'.join(exits)}`")

        total_capacity = sum(z.capacity for z in config.building.zones)
        st.metric("Total Capacity", total_capacity)

        st.markdown("---")

        # --- Floor Selection ---
        st.markdown("**🏗️ Floor View**")
        st.session_state.selected_floor = st.radio(
            "Select floor",
            options=list(range(1, config.building.floors + 1)),
            format_func=lambda x: f"Floor {x}",
            horizontal=True,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # --- Footer ---
        st.markdown(
            f"""
            <div style="text-align:center;color:#5a5a7a;font-size:0.75em;margin-top:16px;">
                SurakshaPath AI v{config.app.version}<br/>
                Honeywell Campus Connect 2026
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================================================
# Main Content Area
# =============================================================

def _render_main_content() -> None:
    """Render the main two-column dashboard layout with placeholders."""
    main_col, side_col = st.columns([65, 35], gap="medium")

    with main_col:
        # --- Floor Plan (Phase 2) ---
        st.markdown("#### 🗺️ Building Floor Plan")
        _placeholder_panel(
            "🏢",
            "Interactive Floor Plan",
            "Phase 2: Zone visualization with hazard coloring and route overlays",
        )

        # --- Hazard Heatmap (Phase 4) ---
        st.markdown("#### 🌡️ Hazard Heatmap")
        _placeholder_panel(
            "🔥",
            "Hazard Heatmap Overlay",
            "Phase 4: Continuous color gradient showing hazard intensity",
        )

        # --- Sensor Trends (Phase 6) ---
        st.markdown("#### 📈 Sensor Trend Charts")
        _placeholder_panel(
            "📊",
            "Time-Series Sensor Data",
            "Phase 6: Temperature, smoke, and hazard score over time",
        )

    with side_col:
        # --- Zone Status (Phase 5) ---
        st.markdown("#### 📋 Zone Status")
        _placeholder_panel(
            "🗂️",
            "Zone Status Table",
            "Phase 5: Sortable table with hazard levels and assigned exits",
        )

        # --- Sensor Health (Phase 4) ---
        st.markdown("#### 🔬 Sensor Health")
        _placeholder_panel(
            "📡",
            "Sensor Health Monitor",
            "Phase 4: Per-sensor status, readings, and confidence",
        )

        # --- Alerts Feed (Phase 6) ---
        st.markdown("#### 🚨 Live Alerts")
        _placeholder_panel(
            "⚠️",
            "Alert Feed",
            "Phase 6: Real-time event log with severity coloring",
        )

        # --- Explainability Panel (Phase 4) ---
        st.markdown("#### 🧠 Explainability Panel")
        _placeholder_panel(
            "🔍",
            "AI Decision Explanation",
            "Phase 4: Per-zone formula breakdown and reasoning",
        )

        # --- Evacuation Progress (Phase 5) ---
        st.markdown("#### 🚶 Evacuation Progress")
        evac = st.session_state.evacuation_progress
        evac_col1, evac_col2, evac_col3 = st.columns(3)
        with evac_col1:
            st.metric("Total", evac["total"])
        with evac_col2:
            st.metric("Evacuated", evac["evacuated"])
        with evac_col3:
            st.metric("Remaining", evac["remaining"])


# =============================================================
# Main Entry Point
# =============================================================

def main() -> None:
    """Dashboard entry point. Called on every Streamlit rerun."""
    # --- Page Configuration (must be first Streamlit call) ---
    st.set_page_config(
        page_title="SurakshaPath AI — Fire Evacuation System",
        page_icon="🔥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # --- Inject Dark Theme CSS ---
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

    # --- Load Configuration (cached across reruns) ---
    if "config" not in st.session_state:
        try:
            config = load_all_configs()
            st.session_state.config = config
        except (FileNotFoundError, ValueError) as e:
            st.error(f"❌ Configuration Error: {e}")
            st.stop()
    
    config = st.session_state.config

    # --- Initialize Session State ---
    _init_session_state(config)

    # --- Render Dashboard ---
    _render_header()
    _render_sidebar()
    _render_main_content()


if __name__ == "__main__":
    main()

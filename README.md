# 🔥 SurakshaPath AI

**AI-Assisted Dynamic Fire Evacuation System for Commercial Buildings**

*Honeywell Campus Connect Hackathon 2026*

---

## Overview

SurakshaPath AI is a real-time fire evacuation system that continuously:

1. **Simulates** multi-sensor fire detection (temperature, smoke, flame)
2. **Fuses** sensor data using a confidence-weighted mathematical formula
3. **Calculates** dynamic edge weights based on hazard severity
4. **Recalculates** evacuation routes using A\* pathfinding
5. **Visualizes** building hazards on a live command-center dashboard

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the dashboard
streamlit run src/dashboard.py
```

## Architecture

```
Sensor Simulation → Sensor Fusion → Risk Engine → A* Pathfinding → Dashboard
```

| Layer | Module | Responsibility |
|---|---|---|
| Simulation | `simulation.py` | Fire spread, smoke diffusion, sensor generation |
| Fusion | `sensor_fusion.py` | Weighted multi-modal hazard scoring |
| Risk | `risk_engine.py` | Dynamic graph edge weight computation |
| Pathfinding | `pathfinder.py` | A\* evacuation route calculation |
| Orchestration | `engine.py` | Per-tick pipeline execution |
| State | `state.py` | In-memory snapshot management |
| Visualization | `visualizations.py` | Plotly floor plan, heatmap, charts |
| Dashboard | `dashboard.py` | Streamlit command-center UI |

## Tech Stack

- **Python 3.10+**
- **Streamlit** — Dashboard framework
- **NetworkX** — Graph data structure and A\* algorithm
- **Plotly** — Interactive visualization
- **NumPy** — Numerical computation
- **Pandas** — Data aggregation
- **PyYAML** — Configuration management

## Project Structure

```
suraksha_path_ai/
├── config/              # YAML configuration files
│   ├── building.yaml    # Building layout: zones, edges, exits
│   ├── scenarios.yaml   # Fire simulation scenarios
│   ├── thresholds.yaml  # Hazard weights and thresholds
│   └── app_config.yaml  # Application settings
├── src/                 # Source code (11 modules)
│   ├── models.py        # Data models and enums
│   ├── config_loader.py # Configuration loading
│   ├── building_graph.py# NetworkX graph construction
│   ├── simulation.py    # Fire and sensor simulation
│   ├── sensor_fusion.py # Multi-modal sensor fusion
│   ├── risk_engine.py   # Edge weight calculation
│   ├── pathfinder.py    # A* pathfinding
│   ├── engine.py        # Pipeline orchestrator
│   ├── state.py         # State management
│   ├── visualizations.py# Plotly rendering
│   └── dashboard.py     # Streamlit entry point
├── docs/                # Documentation
└── assets/              # Static assets
```

## License

MIT

---

*SurakshaPath AI — Honeywell Campus Connect 2026*

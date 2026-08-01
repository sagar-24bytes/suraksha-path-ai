# 🔥 SurakshaPath AI

**AI-Assisted Dynamic Fire Evacuation System for Commercial Buildings**



---

## Overview

SurakshaPath AI is a real-time, 5-subsystem fire evacuation platform that continuously:

1. **Simulates** multi-sensor fire physics, smoke diffusion, and scenario injection via a **Python Digital Twin** (`simulation/`).
2. **Executes** on-device multi-modal sensor fusion, dynamic edge weighting, logical LED indicators, and diagnostics via an **Embedded MicroPython Firmware Layer** (`firmware/micropython/`).
3. **Decouples** network transports (Mock/MQTT) via a unified **Transport Abstraction Layer** (`communication/`).
4. **Calculates** dynamic hazard-aware evacuation paths via a single-authority **Shared Evacuation Routing Subsystem** (`routing/`).
5. **Visualizes** building hazards, evacuation routes, Explainability formulas, and 5-aspect system health via a Streamlit **Fire Commander Dashboard** (`src/dashboard.py`).

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run system verification test suite (65 tests)
python -m unittest discover -s tests -p "test_*.py"

# Launch the Fire Commander Dashboard
streamlit run src/dashboard.py
```

## Documentation

- 📄 **System Architecture Specification** → [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- 🔄 **System Integration Specification** → [`docs/SYSTEM_SEQUENCE.md`](docs/SYSTEM_SEQUENCE.md)
- 🔌 **API Contracts & Schemas** → [`docs/API_CONTRACTS.md`](docs/API_CONTRACTS.md)
- 🚀 **Deployment & Setup Guide** → [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- 🎯 **Interactive Scenario Demo Guide** → [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md)
- 💡 **Key Design Decisions (ADRs)** → [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md)
- ✅ **System Validation & Acceptance Report** → [`docs/VALIDATION_REPORT.md`](docs/VALIDATION_REPORT.md)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FIRE COMMANDER DASHBOARD                              │
│                    (Streamlit Operator Dashboard)                           │
│  · Live Floor Visualization   · Node & Comm Health Monitor  · Scenario Ctrl │
│  · Explainability Panel       · Real-time Alerts Feed       · Audit Reports │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ (Unified Telemetry & Route Packets)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    TRANSPORT ABSTRACTION LAYER                              │
│  · CommunicationInterface  · MockTransport (Dev)  · MQTTTransport (Live)    │
└──────────────────▲───────────────────────────────────────▲──────────────────┘
                   │                                       │
┌──────────────────▼───────────────────┐ ┌─────────────────▼──────────────────┐
│  PYTHON DIGITAL TWIN SIMULATION      │ │  MICROPYTHON EMBEDDED FIRMWARE     │
│  · Fire & Smoke Physics Models       │ │  · Single-threaded Task Scheduler  │
│  · Synthetic Sensor Generator        │ │  · Sensor Data Acquisition & Prep  │
│  · Fault & Drop Injector             │ │  · On-Device Evidence Sensor Fusion│
│  · Scripted Scenario Timeline        │ │  · Logical LED Indicator Controller│
└──────────────────┬───────────────────┘ └─────────────────┬──────────────────┘
                   │                                       │
┌──────────────────▼───────────────────────────────────────▼──────────────────┐
│                   SHARED EVACUATION ROUTING SUBSYSTEM                       │
│  · Single Routing Authority          · Deterministic Dijkstra Pathfinder    │
│  · DynamicEdgeWeightCalculator       · Self-Invalidating RouteCache         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Subsystem Breakdown

| Subsystem | Folder | Responsibilities |
|---|---|---|
| **Digital Twin Simulation** | `simulation/` | Fire & smoke physics, noisy sensor generation, fault injection, scenario timelines, packet injection |
| **MicroPython Firmware** | `firmware/micropython/` | Single-threaded scheduler, CPython compat layer, sensor drivers, on-device fusion, LED state machine, diagnostics |
| **Transport Abstraction** | `communication/` | Abstract transport interface, canonical `TelemetryPacket` schema, Mock/MQTT transports |
| **Shared Routing Subsystem** | `routing/` | Single routing authority, Dijkstra pathfinder, dynamic edge weight formula, self-invalidating route cache |
| **Fire Commander Dashboard** | `src/` | Operator Streamlit dashboard, Plotly floor plan, Explainability card, 5-aspect health monitor |
| **Engineering Docs** | `docs/` | Complete documentation suite (Architecture, Sequence, APIs, Deployment, Demo, ADRs, Validation) |

## Tech Stack

- **Python 3.10+** (Dashboard, Simulation, Routing, Transport)
- **MicroPython** (Firmware Layer)
- **Streamlit** (Fire Commander Dashboard)
- **NetworkX** & **Plotly** (Graph data structure & visualization)
- **NumPy** & **Pandas** (Numerical computation & data logging)
- **PyYAML** (Configuration management)

## Project Structure

```
suraksha_path_ai/
├── config/                             # Central System Configuration (YAML)
│   ├── building.yaml                   # 2-floor office topology (18 nodes, 23 edges)
│   ├── scenarios.yaml                  # Scenario definitions & event timelines
│   ├── thresholds.yaml                 # Algorithmic weights & fail-safe bounds
│   └── app_config.yaml                 # Dashboard & transport settings
├── communication/                      # Transport Abstraction Layer
│   ├── interface.py                    # CommunicationInterface ABC
│   ├── packet_schema.py                # TelemetryPacket versioned dataclass
│   ├── mock_transport.py               # In-memory pub/sub queue transport
│   └── mqtt_transport.py               # Local/Cloud MQTT transport
├── simulation/                         # Subsystem 1: Digital Twin Simulation
│   ├── fire_physics.py                 # Thermal growth & inter-zone spread
│   ├── smoke_physics.py                # Obscuration generation & diffusion
│   ├── sensor_generator.py            # Synthetic readings + noise generator
│   ├── fault_injector.py              # Sensor faults & packet drop injector
│   ├── scenario_engine.py             # Scenario loader & timeline executor
│   └── injector.py                     # Simulation orchestrator & tick executor
├── routing/                            # Shared Evacuation Routing Subsystem
│   ├── graph.py                        # Node, Edge, BuildingGraph data structures
│   ├── edge_weight.py                  # DynamicEdgeWeightCalculator engine
│   ├── hazard_model.py                 # ZoneRisk, HazardSnapshot & TelemetryHazardProvider
│   ├── dijkstra.py                     # Deterministic Dijkstra Pathfinder
│   ├── route_cache.py                  # Self-invalidating RouteCache
│   └── path_manager.py                 # DefaultRouteManager orchestrator
├── firmware/                           # Subsystem 2: Dedicated MicroPython Firmware
│   └── micropython/
│       ├── main.py                     # MicroPython entry point
│       ├── scheduler.py                # Single-threaded cooperative task runner
│       ├── compat.py                   # CPython / MicroPython abstraction wrapper
│       ├── communication.py            # MicroPython transport wrapper
│       ├── sensors.py                  # Sensor hardware abstraction drivers
│       ├── sensor_fusion.py            # On-device weighted fusion engine
│       ├── led_controller.py           # Logical LED animation state machine
│       ├── diagnostics.py              # Node heartbeat & health manager
│       └── config.py                   # MicroPython constants
├── src/                                # Subsystem 3: Fire Commander Dashboard
│   ├── models.py                       # Shared Python data models & enums
│   ├── config_loader.py                # YAML configuration loader
│   ├── system_coordinator.py           # Master 5-subsystem bridge
│   ├── dashboard_components/           # Modular UI rendering components
│   └── dashboard.py                    # Streamlit Fire Commander UI shell
├── docs/                               # Engineering Documentation Suite
│   ├── ARCHITECTURE.md                 # System Architecture Specification
│   ├── SYSTEM_SEQUENCE.md              # System Integration Specification
│   ├── API_CONTRACTS.md                # API Contracts & Data Schemas
│   ├── DEPLOYMENT.md                   # Deployment & Setup Guide
│   ├── DEMO_GUIDE.md                   # Interactive Scenario Demo Guide
│   ├── DESIGN_DECISIONS.md             # Key Architectural Rationale
│   └── VALIDATION_REPORT.md            # System Validation & Acceptance Report
└── tests/                              # Comprehensive Unit & Integration Test Suite
```

---

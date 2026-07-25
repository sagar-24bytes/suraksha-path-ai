# System Architecture Specification

**SurakshaPath AI — AI-Assisted Dynamic Fire Evacuation System**
*Honeywell Campus Connect Hackathon 2026*

---

## 1. Project Overview

SurakshaPath AI is an industrial-grade, 3-subsystem fire evacuation platform designed for commercial buildings. The platform continuously monitors environmental parameters (temperature, smoke obscuration, optical flame, occupancy), computes on-device multi-sensor evidence fusion, calculates dynamic hazard-aware evacuation routes, and renders an operator dashboard for emergency commanders.

The platform is designed around **5 primary decoupled subsystems**:
1. **Digital Twin Simulation** (`simulation/`)
2. **Transport Abstraction Layer** (`communication/`)
3. **Shared Evacuation Routing Subsystem** (`routing/`)
4. **Dedicated MicroPython Firmware** (`firmware/micropython/`)
5. **Fire Commander Dashboard** (`src/dashboard.py`)

---

## 2. System Architecture Overview

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

---

## 3. High-Level Subsystem Responsibilities

### 3.1 Digital Twin Simulation (`simulation/`)
- **Physics Models**: Simulates thermal growth ($I_z$), heat conduction, and smoke obscuration diffusion ($S_v$) across structural edges.
- **Sensor Generation**: Samples physical states into canonical `TelemetryPacket` instances with Gaussian noise.
- **Fault Injection**: Injects stuck sensors, dead nodes, comm degradation, and battery drain without mutating base physics.
- **Scenario Management**: Executes 7 built-in fire scenarios (Kitchen Fire, Electrical Room, Flashover, Slow Smoldering, Blocked Exit, Server Room Fire, Laboratory Fire).

### 3.2 Transport Abstraction Layer (`communication/`)
- **Contract Interface**: `CommunicationInterface` abstract base class defining `publish()`, `subscribe()`, and `unsubscribe()`.
- **Mock Transport**: Thread-safe in-memory pub/sub broker (`MockTransport`) with wildcard topic matching (`suraksha/telemetry/#`).
- **MQTT Transport**: Architecture-ready MQTT driver (`MQTTTransport`) with graceful standby fallback.

### 3.3 Shared Evacuation Routing Subsystem (`routing/`)
- **Single Routing Authority**: Sole component responsible for shortest-path pathfinding and edge cost calculations.
- **Dijkstra Pathfinder**: Deterministic multi-destination Dijkstra search with lexicographical tie-breaking.
- **Dynamic Edge Cost**: Exponential hazard penalty formula $W = W_{\text{base}} \cdot e^{k H_v} \cdot M_{\text{door}}$.
- **Route Cache**: Self-invalidating lookup cache keyed by hazard snapshot signature hash.

### 3.4 MicroPython Embedded Firmware (`firmware/micropython/`)
- **Cooperative Scheduler**: Single-threaded periodic task runner operating without `threading` or `asyncio`.
- **On-Device Sensor Fusion**: Weighted evidence fusion formula $H_z = \frac{\sum w_i c_i t_i}{\sum w_i c_i}$ (zero Machine Learning).
- **Logical LED Controller**: Animation state machine managing `SAFE_SOLID`, `WARN_PULSE`, `DANGER_FLASH`, `BLOCKED_CROSS`.
- **Diagnostics Manager**: Tracks heartbeats, uptime, battery charge levels, and communication link timeouts.

### 3.5 Fire Commander Dashboard (`src/dashboard.py`)
- **Operator Command Center**: Streamlit dark-themed UI (`#0f0f1a`).
- **Floor Plan**: Plotly interactive visualization with HSL hazard gradients and dynamic route overlay arrows.
- **Explainability Panel**: Live mathematical formula breakdown card ($\sum w_i c_i t_i$) and reasoning generator.
- **Multi-Aspect Health**: Independent indicators for Simulation, Firmware, Comm, Node, and Sensor health.

---

## 4. Directory Structure

```
suraksha_path_ai/
├── config/                             # System Configuration (YAML)
│   ├── building.yaml                   # 2-floor office topology (18 nodes, 23 edges)
│   ├── scenarios.yaml                  # Scenario definitions & event timelines
│   ├── thresholds.yaml                 # Algorithmic weights & fail-safe bounds
│   └── app_config.yaml                 # Dashboard & transport settings
├── communication/                      # Transport Abstraction Layer
│   ├── interface.py                    # CommunicationInterface ABC
│   ├── packet_schema.py                # TelemetryPacket schema & status constants
│   ├── mock_transport.py               # In-memory pub/sub queue transport
│   └── mqtt_transport.py               # Local/Cloud MQTT transport
├── simulation/                         # Subsystem 1: Digital Twin Simulation
│   ├── fire_physics.py                 # Thermal growth & conduction physics
│   ├── smoke_physics.py                # Obscuration & corridor diffusion physics
│   ├── sensor_generator.py            # Synthetic telemetry generator with noise
│   ├── fault_injector.py              # Sensor fault & drop injector
│   ├── scenario_engine.py             # Scenario loader & timeline executor
│   └── injector.py                     # Simulation orchestrator & tick executor
├── routing/                            # Shared Evacuation Routing Subsystem
│   ├── graph.py                        # Node, Edge, BuildingGraph data structures
│   ├── edge_weight.py                  # DynamicEdgeWeightCalculator engine
│   ├── hazard_model.py                 # ZoneRisk, HazardSnapshot & TelemetryHazardProvider
│   ├── dijkstra.py                     # Deterministic Dijkstra Pathfinder
│   ├── route_cache.py                  # Self-invalidating RouteCache
│   └── path_manager.py                 # DefaultRouteManager orchestrator
├── firmware/                           # Subsystem 2: MicroPython Firmware
│   └── micropython/
│       ├── main.py                     # MicroPython node coordinator entry point
│       ├── compat.py                   # CPython / MicroPython abstraction wrapper
│       ├── scheduler.py                # Single-threaded cooperative task runner
│       ├── sensors.py                  # Sensor hardware abstraction drivers
│       ├── sensor_fusion.py            # On-device weighted fusion engine
│       ├── led_controller.py           # Logical LED animation state machine
│       ├── diagnostics.py              # Node health & heartbeat manager
│       ├── communication.py            # Telemetry constructor & transport helper
│       └── config.py                   # MicroPython timing & threshold constants
├── src/                                # Subsystem 3: Fire Commander Dashboard
│   ├── models.py                       # Shared Python data models & enums
│   ├── config_loader.py                # YAML configuration loader
│   └── dashboard.py                    # Streamlit Fire Commander UI shell
├── docs/                               # Engineering Documentation
│   ├── ARCHITECTURE.md                 # System Architecture Specification
│   ├── SYSTEM_SEQUENCE.md              # End-to-End System Sequence Blueprint
│   ├── API_CONTRACTS.md                # Data Contracts & Schema Summaries
│   ├── DEPLOYMENT.md                   # Deployment & Setup Guide
│   ├── DEMO_GUIDE.md                   # Interactive Scenario Demo Guide
│   └── DESIGN_DECISIONS.md             # Key Architectural Rationale
└── tests/                              # Comprehensive Unit Test Suite
```

---

## 5. Data Flow Summary

$$\text{Scenario Engine} \longrightarrow \text{Physics Simulation} \longrightarrow \text{Sensor Generator} \longrightarrow \text{Communication Layer}$$

$$\text{Communication Layer} \longrightarrow \text{Hazard Provider} \longrightarrow \text{Dynamic Edge Weighting} \longrightarrow \text{Dijkstra Pathfinder}$$

$$\text{Routing Result} \longrightarrow \text{MicroPython Firmware} \longrightarrow \text{On-Device Fusion / LEDs} \longrightarrow \text{Fire Commander Dashboard}$$

---

## 6. Primary Design Principles

1. **Single Routing Authority**: `routing/path_manager.py::DefaultRouteManager` is the single source of truth for path planning. Neither Simulation, Firmware, nor Dashboard duplicates pathfinding logic.
2. **Canonical Telemetry Contract**: All telemetry exchanges use `communication/packet_schema.py::TelemetryPacket`.
3. **Transport Abstraction**: Network protocols are isolated behind `CommunicationInterface`. Swapping `MockTransport` for `MQTTTransport` requires zero application code changes.
4. **Modular Subsystem Componentization**: Each subsystem maintains explicit, clean boundaries with zero circular dependencies.
5. **Separation of Concerns**: Physical physics tracking, embedded sensor processing, routing calculation, and UI rendering operate completely independently.

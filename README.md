# 🔥 SurakshaPath AI

**AI-Assisted Dynamic Fire Evacuation System for Commercial Buildings**

*Honeywell Campus Connect Hackathon 2026*

---

## Overview

SurakshaPath AI is a real-time, 3-subsystem fire evacuation architecture that continuously:

1. **Simulates** multi-sensor fire physics, smoke diffusion, and scenario injection via a **Python Digital Twin** (`simulation/`).
2. **Executes** on-device multi-modal sensor fusion, dynamic edge weighting, lightweight routing, and Neopixel LED status animation via an **Embedded MicroPython Firmware Layer** (`firmware/micropython/`).
3. **Decouples** network transports (Mock/MQTT) via a unified **Transport Abstraction Layer** (`communication/`).
4. **Visualizes** building hazards, evacuation routes, Explainability formulas, and 5-aspect system health via a Streamlit **Fire Commander Dashboard** (`src/dashboard.py`).

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the Fire Commander Dashboard
streamlit run src/dashboard.py
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FIRE COMMANDER DASHBOARD                              │
│                    (Streamlit Operator Dashboard)                           │
│  · Live Floor Visualization   · Node & Comm Health Monitor  · Scenario Ctrl │
│  · Explainability Panel       · Real-time Alerts Feed       · Audit Reports │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ (Unified Telemetry & Control Packets)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    TRANSPORT ABSTRACTION LAYER                              │
│  · CommunicationInterface  · MockTransport (Dev)  · MQTTTransport (Live)    │
└──────────────────▲───────────────────────────────────────▲──────────────────┘
                   │                                       │
┌──────────────────▼───────────────────┐ ┌─────────────────▼──────────────────┐
│  PYTHON DIGITAL TWIN SIMULATION      │ │  MICROPYTHON EMBEDDED FIRMWARE     │
│  · Physics Engine (Fire/Smoke)       │ │  · Non-blocking Scheduler (asyncio)│
│  · Synthetic Sensor Generation       │ │  · Sensor Data Acquisition & Prep  │
│  · Fault & Drop Injector             │ │  · Weighted Sensor Fusion Engine   │
│  · Scenario Manager & Timeline       │ │  · Embedded Dynamic Edge Weighting │
│  · Packet Converter / Injector       │ │  · Embedded Routing Engine (Dijkstra)│
└──────────────────────────────────────┘ │  · Concurrent LED Indicator Ctrl   │
                                         │  · Health & Fail-Safe Controller   │
                                         └────────────────────────────────────┘
```

## Subsystem Breakdown

| Subsystem | Folder | Responsibilities |
|---|---|---|
| **Digital Twin Simulation** | `simulation/` | Fire & smoke physics, noisy sensor generation, fault injection, scenario timelines, packet injection |
| **MicroPython Firmware** | `firmware/micropython/` | Non-blocking scheduler (`uasyncio`), CPython compat layer, sensor acquisition, fusion engine, dynamic edge cost, embedded routing, LED controller, health monitor |
| **Transport Abstraction** | `communication/` | Abstract transport interface, canonical `TelemetryPacket` schema, Mock/MQTT transports |
| **Fire Commander Dashboard** | `src/` | Operator Streamlit dashboard, Plotly floor plan, Explainability card, 5-aspect health monitor |
| **Hardware Documentation** | `hardware/` | Board specs (ESP32), pinouts, flashing guides, simulation vs hardware mapping |
| **Engineering Docs** | `docs/` | System architecture, communication schema, fusion math, routing specs, flowcharts |

## Tech Stack

- **Python 3.10+** (Dashboard, Simulation, Transport)
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
│   ├── scenarios.yaml                  # 5 official simulation scenarios
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
│   └── injector.py                     # Packet converter & transport injector
├── firmware/                           # Subsystem 2: Dedicated MicroPython Firmware
│   └── micropython/
│       ├── main.py                     # MicroPython entry point
│       ├── scheduler.py                # uasyncio non-blocking task runner
│       ├── compat.py                   # CPython / MicroPython abstraction wrapper
│       ├── communication.py            # MicroPython transport wrapper
│       ├── packet.py                   # Lightweight packet serializer
│       ├── sensors.py                  # Sensor buffer & acquisition logic
│       ├── sensor_fusion.py            # On-device weighted fusion engine
│       ├── edge_weight.py              # On-device dynamic edge cost calculator
│       ├── routing.py                  # Embedded routing engine
│       ├── led_controller.py           # Non-blocking LED animation state machine
│       ├── health.py                   # Node heartbeat & fail-safe controller
│       └── config.py                   # MicroPython constants
├── src/                                # Subsystem 3: Fire Commander Dashboard
│   ├── models.py                       # Shared Python data models & enums
│   ├── config_loader.py                # YAML configuration loader
│   └── dashboard.py                    # Streamlit Fire Commander UI shell
├── hardware/                           # Hardware Specification & Deployment Specs
│   ├── supported_boards.md             # ESP32 specs & pinouts
│   └── deployment_notes.md             # Flashing & hardware integration guides
├── docs/                               # Engineering Documentation
│   ├── architecture.md                 # System Architecture Specification
│   └── flowcharts.md                   # System Execution Flowcharts
└── tests/                              # Integration & Verification Tests
```

---

*SurakshaPath AI — Honeywell Campus Connect 2026*

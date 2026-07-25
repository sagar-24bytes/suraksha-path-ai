# API Contracts & Data Schemas

**SurakshaPath AI — Data Interface Specification**
*Honeywell Campus Connect Hackathon 2026*

---

## Overview

This document specifies the primary data contracts exchanged across the 5 subsystems of SurakshaPath AI. All contracts use strongly-typed dataclasses and serialization primitives compatible with both Python 3.10+ and MicroPython.

---

## 1. `TelemetryPacket`

* **File**: `communication/packet_schema.py`
* **Purpose**: The canonical, immutable telemetry contract exchanged across Simulation, Communication, MicroPython Firmware, Routing, and Dashboard.
* **Producer**: `simulation/sensor_generator.py` (raw data), `firmware/micropython/communication.py` (fused telemetry).
* **Consumer**: `communication/mock_transport.py`, `routing/hazard_model.py`, `firmware/micropython/main.py`, `src/dashboard.py`.

### Key Fields:

| Field Name | Type | Description |
|---|---|---|
| `schema_version` | `str` | Schema version string (default `"1.0"`). |
| `packet_id` | `str` | Unique packet UUID4 identifier. |
| `timestamp` | `float` | Simulation/clock timestamp in seconds. |
| `node_id` | `str` | Node identifier (e.g. `"NODE-R105"`). |
| `zone_id` | `str` | Structural zone identifier (e.g. `"R-105"`). |
| `temperature` | `float` | Temperature in °C. |
| `smoke_level` | `float` | Smoke obscuration density (0.0–1.0). |
| `flame_detected` | `bool` | Optical flame sensor binary state. |
| `occupancy_count` | `int` | Zone occupant count. |
| `hazard_score` | `float` | Fused hazard score (0.0–1.0). |
| `evacuation_state` | `str` | Status string (`"NORMAL"`, `"WARNING"`, `"EVACUATE"`, `"SHELTER"`). |
| `recommended_exit` | `str` | Assigned exit node ID (e.g. `"X-01"`). |
| `route_cost` | `float` | Estimated evacuation traversal time in seconds. |
| `node_health` | `str` | Node status (`"HEALTHY"`, `"WARNING"`, `"OFFLINE"`, `"FAULT"`). |
| `communication_health`| `str` | Comm link status (`"HEALTHY"`, `"DEGRADED"`, `"TIMEDOUT"`). |
| `firmware_health` | `str` | Firmware runtime status (`"HEALTHY"`, `"WATCHDOG_RESET"`). |
| `led_state` | `str` | Logical LED state (`"SAFE_SOLID"`, `"WARN_PULSE"`, `"DANGER_FLASH"`, `"BLOCKED_CROSS"`). |
| `battery_level` | `float` | Power supply charge percentage (0.0–100.0%). |

---

## 2. `RouteRequest`

* **File**: `routing/path_manager.py`
* **Purpose**: Input request contract specifying evacuation path parameters.
* **Producer**: `src/dashboard.py`, `firmware/micropython/main.py`, testing harnesses.
* **Consumer**: `routing/path_manager.py::DefaultRouteManager`.

### Key Fields:

| Field Name | Type | Description |
|---|---|---|
| `source_node` | `str` | Starting zone/node ID (e.g. `"R-105"`). |
| `target_exits` | `Optional[List[str]]` | Allowed exit node IDs (or `None` for all building exits). |
| `avoid_hazards` | `bool` | `True` to enable dynamic hazard penalty calculations. |

---

## 3. `RouteResult`

* **File**: `routing/path_manager.py`
* **Purpose**: Output contract containing calculated optimal evacuation paths and hazard risks.
* **Producer**: `routing/path_manager.py::DefaultRouteManager`, `routing/dijkstra.py::DijkstraPathfinder`.
* **Consumer**: `src/dashboard.py` (visualization overlay), `firmware/micropython/main.py` (exit assignment).

### Key Fields:

| Field Name | Type | Description |
|---|---|---|
| `source_node` | `str` | Starting zone ID. |
| `target_exit` | `str` | Selected optimal emergency exit node ID (e.g. `"X-02"`). |
| `path` | `List[str]` | Ordered list of node IDs (`["R-105", "C-02", "X-02"]`). |
| `estimated_time_s` | `float` | Total dynamic traversal cost in seconds (`infinity` if trapped). |
| `cumulative_risk` | `float` | Sum of hazard scores along path nodes. |
| `is_shelter_in_place` | `bool` | `True` if no valid safe path exists to any exit. |

---

## 4. `HazardSnapshot`

* **File**: `routing/hazard_model.py`
* **Purpose**: Building-wide physical risk state contract consumed by dynamic edge weighting engines.
* **Producer**: `routing/hazard_model.py::TelemetryHazardProvider`, `simulation/injector.py`.
* **Consumer**: `routing/edge_weight.py::DynamicEdgeWeightCalculator`, `routing/dijkstra.py`.

### Key Fields:

| Field Name | Type | Description |
|---|---|---|
| `timestamp` | `float` | Simulation/clock timestamp in seconds. |
| `zone_risks` | `Dict[str, ZoneRisk]` | Dict mapping `zone_id` to individual `ZoneRisk` dataclasses. |
| `blocked_edges` | `List[Tuple[str, str]]` | List of `(from_node, to_node)` pairs that are impassable. |

---

## 5. `DiagnosticState`

* **File**: `firmware/micropython/diagnostics.py`
* **Purpose**: Embedded runtime health snapshot populated into `TelemetryPacket` health fields.
* **Producer**: `firmware/micropython/diagnostics.py::DiagnosticsManager`.
* **Consumer**: `firmware/micropython/communication.py`, `src/dashboard.py`.

### Key Fields:

| Field Name | Type | Description |
|---|---|---|
| `heartbeat_counter` | `int` | Monotonic heartbeat sequence counter. |
| `uptime_ms` | `int` | Firmware node uptime in milliseconds. |
| `battery_level` | `float` | Battery charge percentage (0.0–100.0%). |
| `node_health` | `str` | Node status string (`"HEALTHY"`, `"WARNING"`, `"FAULT"`). |
| `communication_health` | `str` | Comm link status string (`"HEALTHY"`, `"DEGRADED"`, `"TIMEDOUT"`). |
| `firmware_health` | `str` | Firmware runtime status (`"HEALTHY"`, `"WATCHDOG_RESET"`). |

# Architectural Design Decisions (ADRs)

**SurakshaPath AI — Key Engineering Rationale**
*Honeywell Campus Connect Hackathon 2026*

---

## 1. Why Dijkstra Instead of A* Algorithm?

* **Context**: We needed a shortest-path algorithm for multi-exit commercial building graphs (~18–500 nodes).
* **Decision**: Selected **Dijkstra's Algorithm** with priority queue (`heapq`) over A*.
* **Rationale**:
  1. Commercial building evacuation requires multi-destination search (finding the shortest/safest path to *any* exit). Standard A* requires a single target destination heuristic.
  2. For graphs of scale $V \le 500$, Dijkstra computes in $<0.1\text{ms}$, making A* heuristic overhead unnecessary.
  3. Dijkstra provides 100% deterministic, explainable path outputs with zero risk of admissible heuristic misconfigurations.

---

## 2. Why Does `TelemetryPacket` Exist as a Single Canonical Contract?

* **Context**: Multiple subsystems (Simulation, Firmware, Transport, Dashboard) need to exchange telemetry.
* **Decision**: Created one versioned `TelemetryPacket` schema (`communication/packet_schema.py`).
* **Rationale**:
  1. Eliminates ad-hoc dictionaries and data transformation bugs between Python and MicroPython.
  2. Ensures strict validation bounds across physical readings and system health fields.
  3. Enables lossless serialization between JSON string payloads and in-memory dataclass instances.

---

## 3. Why is Routing a Shared Subsystem (`routing/`)?

* **Context**: Initially routing was located inside firmware/simulation.
* **Decision**: Extracted routing into a standalone shared package (`routing/`).
* **Rationale**:
  1. Routing is consumed by Simulation (throughput evaluation), Firmware (exit assignment), Dashboard (visual path overlay), and analytics.
  2. Enforces the **Single Routing Authority** principle: exactly one module computes shortest paths, preventing duplicate pathfinding logic.

---

## 4. Why Does MicroPython Firmware Perform No Pathfinding?

* **Context**: Consideration of running Dijkstra on-device inside ESP32 microcontrollers.
* **Decision**: Firmware receives `RouteResult` contracts and focuses on sensor acquisition, fusion, LEDs, and diagnostics.
* **Rationale**:
  1. ESP32 nodes have constrained RAM ($320\text{ KB}$) and single-threaded execution loops.
  2. Offloading pathfinding to the shared routing engine preserves embedded CPU cycles for $100\text{ms}$ LED refresh animations and sensor polling.

---

## 5. Why Abstract Communication (`CommunicationInterface`)?

* **Context**: Need to support local simulation testing without requiring a live MQTT broker.
* **Decision**: Created `CommunicationInterface` abstract base class.
* **Rationale**:
  1. Decouples business logic from network transport implementations.
  2. Allows seamless switching between `MockTransport` (in-memory queues) and `MQTTTransport` (Paho MQTT pub/sub) without changing a single line of application code.

---

## 6. Why Does `MockTransport` Exist?

* **Context**: Needed rapid testing and local simulation before physical ESP32 hardware is connected.
* **Decision**: Built thread-safe in-memory pub/sub broker (`MockTransport`).
* **Rationale**:
  1. Allows 100% of unit tests (53 tests) to run in $0.003\text{s}$ without external process dependencies.
  2. Supports MQTT-style wildcard topic matching (`suraksha/telemetry/#`) for realistic message routing.

---

## 7. Why Was Deterministic Simulation Chosen?

* **Context**: Need reproducible simulation runs for judging presentations and unit testing.
* **Decision**: Used seedable random generators (`random.Random(seed)`).
* **Rationale**:
  1. Guarantees that running scenario "Kitchen Fire" with seed `42` produces identical thermal curves and telemetry packets every time.
  2. Prevents judge demonstration surprises caused by non-deterministic random drift.

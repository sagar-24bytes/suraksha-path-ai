# Interactive Scenario Demonstration Guide

**SurakshaPath AI — Honeywell Judging Demo Guide**
*Honeywell Campus Connect Hackathon 2026*

---

## Overview

This guide provides step-by-step instructions for demonstrating SurakshaPath AI to judges during the Honeywell Campus Connect Hackathon presentation.

---

## Demo Scenario 1: Kitchen Fire & Dynamic Rerouting

* **Objective**: Demonstrate dynamic sensor fusion and automatic route calculation during a fast-growing fire.
* **Selection**: Select **"Kitchen Fire"** from the sidebar dropdown.
* **Timeline**:
  - $T + 00:00$: Kitchen (`R-105`) ignites ($I_z = 0.15$). Building state is green (`SAFE_SOLID`).
  - $T + 00:30$: Temperature in `R-105` exceeds $80^\circ\text{C}$; smoke obscuration reaches $0.65$.
  - $T + 00:45$: Sensor Fusion updates hazard score to $H_z = 0.78$. `R-105` changes to red (`DANGER_FLASH`).
  - $T + 01:00$: Routing Engine recalculates edge costs. Corridor `C-01` receives high penalty. Route shifts from Exit `X-01` to East Exit `X-02`.
* **What Audience Should Observe**:
  - Plotly floor plan color transitions cleanly from green $\rightarrow$ yellow $\rightarrow$ red.
  - Animated blue path arrows dynamically reroute occupants away from Kitchen `R-105` towards Exit `X-02`.
  - Explainability Card renders live formula breakdown: $\sum w_i c_i t_i / \sum w_i c_i$.

---

## Demo Scenario 2: Blocked Corridor (Exit Impassable)

* **Objective**: Demonstrate structural exit blockage handling.
* **Selection**: Select **"Blocked Exit & Comm Failure"** from sidebar.
* **Timeline**:
  - $T + 00:30$: Main Entrance `X-01` becomes completely blocked ($W = \infty$).
  - $T + 00:35$: Dijkstra Pathfinder detects blocked threshold and evaluates alternative exit `X-02`.
* **What Audience Should Observe**:
  - Main Entrance `X-01` flashes orange/black (`BLOCKED_CROSS`).
  - All occupant evacuation paths automatically swing towards secondary Exit `X-02`.

---

## Demo Scenario 3: Communication Link Loss

* **Objective**: Demonstrate fail-safe operation during hardware network drops.
* **Selection**: Inject **"COMM_FAIL"** on corridor `C-02` at $T + 00:60$.
* **Timeline**:
  - $T + 01:00$: Node `C-02` stops publishing heartbeats.
  - $T + 01:05$: `DiagnosticsManager` exceeds `COMM_TIMEOUT_MS` ($5000\text{ms}$) and sets `communication_health="TIMEDOUT"`.
* **What Audience Should Observe**:
  - Node `C-02` status badge switches to gray/black **TIMEDOUT** alert.
  - System applies conservative hazard penalty to `C-02` ($H_z \ge 0.70$), routing occupants through alternative corridors.

---

## Demo Scenario 4: Shelter-In-Place Emergency Fallback

* **Objective**: Demonstrate safe fallback when all evacuation exits are impassable.
* **Selection**: Select **"Flashover Event"** with full building blockage.
* **Timeline**:
  - All surrounding corridors and exits exceed $H_v \ge 0.80$.
  - Dijkstra Pathfinder finds zero valid paths to any exit and returns `is_shelter_in_place = True`.
* **What Audience Should Observe**:
  - Prominent emergency banner renders on dashboard: **🚨 SHELTER IN PLACE — ALL EXITS IMPASSABLE**.
  - Node LED controllers switch to `BLOCKED_CROSS` indicator pattern.

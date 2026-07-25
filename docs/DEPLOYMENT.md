# Deployment & Setup Guide

**SurakshaPath AI — Platform Setup & Verification**
*Honeywell Campus Connect Hackathon 2026*

---

## 1. System Requirements

- **Operating System**: Windows 10/11, macOS 12+, or Ubuntu 20.04+
- **Python**: Python 3.10, 3.11, or 3.12
- **Memory**: Minimum 4 GB RAM
- **Disk Space**: 200 MB free space

---

## 2. Installation & Virtual Environment

1. Clone or navigate to the repository directory:
   ```bash
   cd "C:\Users\LENOVO\.gemini\antigravity\scratch\suraksha_path_ai\SurakshaPath AI"
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install pinned dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 3. Running Unit Tests

Verify platform integrity across all 5 subsystems by running the unit test suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Expected Output:
```
........................[TestMockTransport] Publish failed: Transport not connected.
.............................
----------------------------------------------------------------------
Ran 53 tests in 0.003s

OK
```

---

## 4. Launching the Fire Commander Dashboard

Start the Streamlit Fire Commander Dashboard:

```bash
streamlit run src/dashboard.py
```

- Local Web URL: `http://localhost:8501`
- Network URL: Shown in console log

---

## 5. Startup Execution Order

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Config Loader parses building.yaml & scenarios.yaml │
├─────────────────────────────────────────────────────────────┤
│ Step 2: Communication Layer initializes MockTransport       │
├─────────────────────────────────────────────────────────────┤
│ Step 3: Digital Twin Simulation initializes physics models  │
├─────────────────────────────────────────────────────────────┤
│ Step 4: Routing Engine loads building graph topology        │
├─────────────────────────────────────────────────────────────┤
│ Step 5: MicroPython Firmware nodes start cooperative loops  │
├─────────────────────────────────────────────────────────────┤
│ Step 6: Streamlit Dashboard renders Fire Commander UI       │
└─────────────────────────────────────────────────────────────┘
```

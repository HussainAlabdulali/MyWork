# Industry 4.0 IoT Dashboard

An industrial IoT proof of concept that connects NI myRIO sensor acquisition to a Flask-based monitoring dashboard. The system ingests live sensor readings, derives event signals, stores logs, and displays real-time module views for common smart-manufacturing scenarios.

## Overview

The project combines a LabVIEW/myRIO acquisition layer with a Python Flask web application. Sensor readings are collected from the myRIO and Arduino-compatible sensors, sent to the backend, processed into derived values, and displayed in dashboard pages with charts, thresholds, status indicators, notifications, and CSV exports.

The dashboard covers five monitoring scenarios:

- Smart tool-drop detection
- Machine vibration monitoring
- AGV tipping/collision detection
- Package drop logging
- Worker fatigue/fall monitoring

## Features

- NI myRIO and LabVIEW acquisition prototypes for accelerometer and auxiliary sensor readings
- HTTP-oriented Flask API workflow, with earlier UDP/TCP/Node-RED communication prototypes kept for reference
- Sensor-derived metrics such as acceleration magnitude, fall state, pitch, and roll
- SQLite database managed through SQLAlchemy ORM
- CSV logs for validation, inspection, and dashboard export workflows
- Live browser polling with JavaScript and Chart.js
- Adjustable thresholds, update toggles, status indicators, and browser notifications
- Multi-page dashboard for industrial monitoring use cases

## Tech Stack

- **Hardware/acquisition:** NI myRIO, LabVIEW, Arduino-compatible sensors
- **Backend:** Python, Flask, SQLAlchemy, pandas
- **Storage:** SQLite and CSV logs
- **Frontend:** HTML, CSS, Bootstrap, JavaScript, Chart.js
- **Protocols explored:** HTTP, TCP, UDP, Node-RED-assisted testing

## Repository Layout

```text
.
├── main.py                 # Flask application and API routes
├── models.py               # SQLAlchemy data models
├── csv_utils.py            # CSV logging and sensor-derived helpers
├── templates/              # Dashboard pages
├── static/                 # CSS, JS, images, and visual assets
├── labview-myrio/          # LabVIEW/myRIO acquisition and protocol prototypes
├── sample-data/            # Representative validation CSVs
├── docs/                   # Trimmed technical report
├── archive/                # Older prototype code kept for reference
└── requirements.txt
```

## Data Flow

```text
myRIO / sensors
    -> LabVIEW acquisition
    -> Flask API
    -> SQLAlchemy + SQLite / CSV logs
    -> browser dashboard
```

## Documentation

- `docs/Industry4_IoT_Dashboard_Trimmed_Report.docx` summarizes the architecture, implementation, dashboard modules, and validation approach.
- `labview-myrio/README.md` explains the LabVIEW project files and protocol prototypes.

This portfolio copy excludes local virtual environments, generated deployment builds, raw runtime extracts, SQLite databases, and private working archives.

## Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Then open:

```text
http://localhost:5000
```

## Notes

The current implementation prioritizes end-to-end hardware integration, real-time dashboard behavior, event logging, and exportable validation data. Future improvements would include cleaner app packaging and a user database.

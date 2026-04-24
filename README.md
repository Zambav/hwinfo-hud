# HWiNFO HUD

A live hardware dashboard built on top of **HWiNFO64 shared memory**, a **Python reader**, a **FastAPI + WebSocket server**, and a browser UI tuned for readable real-time telemetry.

## What this repo is

This project reads sensor data from HWiNFO64 and streams it into a custom dashboard.

Pipeline:

```text
HWiNFO64 Shared Memory
  -> Python ctypes reader
  -> FastAPI server
  -> WebSocket stream
  -> Browser HUD
```

## Current app structure

```text
hwinfo-monitor/
├── .gitignore
├── CHANGELOG.md
├── README.md
├── reader.py
├── requirements.txt
├── server.py
└── static/
    └── index.html
```

## Requirements

- Windows
- HWiNFO64 running
- HWiNFO Sensor window open
- **Shared Memory Support** enabled in HWiNFO
- Python 3.10+

## Setup

### 1. Enable HWiNFO shared memory

In HWiNFO64:

- Open **Settings**
- Go to **Sensors**
- Scroll down
- Enable **Shared Memory Support**

### 2. Install dependencies

```bash
cd projects/hwinfo-monitor
pip install -r requirements.txt
```

### 3. Run the server

```bash
python server.py
```

Then open:

```text
http://127.0.0.1:8080
```

## API

- `GET /` -> dashboard
- `GET /api/sensors` -> full HWiNFO data snapshot
- `GET /api/readings` -> current flat readings list
- `GET /api/debug` -> shared memory diagnostics
- `WS /ws` -> live telemetry stream

## How we made it work

The main technical problem was not the UI. It was the shared memory bridge.

### Final working setup

- Shared memory mapping name: `Global\HWiNFO_SENS_SM2`
- Mutex name: `Global\HWiNFO_SM2_MUTEX`
- Signature constant: `0x53695748` (`HWiS`)
- Reader implementation: `ctypes` structs matching the HWiNFO SDK layout
- Transport: polling shared memory on the server side, then broadcasting through WebSocket

### Important lessons

1. **The struct layout had to match exactly**
   - Wrong offsets or field sizes break everything.
   - The reader now uses packed `ctypes.LittleEndianStructure` definitions.

2. **The signature check mattered**
   - Earlier attempts used the wrong signature expectation.
   - The live mapping signature that worked here is `0x53695748`.

3. **Privilege level must match**
   - If HWiNFO runs elevated and Python does not, or vice versa, shared memory access can fail.

4. **The sensor window must be open**
   - HWiNFO needs to be actively exposing the sensor shared memory.

5. **A browser HUD needs selective data, not raw dumps**
   - HWiNFO exposes a lot of duplicate, low-value, or zero-value readings.
   - The frontend now filters and deduplicates where helpful.

## Design methodology

This dashboard is being shaped around a few rules.

### 1. Real-time readability over raw completeness

Not every sensor belongs on screen.

We prefer:
- the most useful temperatures
- meaningful power and load values
- deduplicated storage entries
- layouts that stay readable while values update live

We avoid:
- repeated copies of the same drive
- zero-only metrics
- noisy panels that make the dashboard harder to scan

### 2. Motion-friendly visualizations

For fast-changing telemetry, a graph should:
- stay within the layout
- be readable at a glance
- update smoothly
- preserve trend, not just current value

That is why the HUD moved away from overstuffed static cards and oversized graphs toward simpler live views.

### 3. Futuristic look, practical information

The visual style is intentionally sci-fi:
- deep-space dark background
- cyan glow accents
- glass panels
- bracket corners
- mono + geometric heading fonts

But the goal is still utility first. If something looks cool but hurts readability, it should be removed.

## Current UI direction

The interface currently focuses on:
- a simplified **live temperature graph**
- cleaner GPU detail panels
- filtered storage cards
- a more readable futuristic HUD styling language

## Notes for future work

Likely next improvements:
- rolling history buffers with smarter graph scaling
- better grouping of high-value GPU metrics
- more explicit sensor selection rules in the frontend
- optional compact and expanded dashboard modes

## Repo cleanup policy

This repo intentionally keeps only the files needed to run and maintain the app.

One-off diagnostic scripts were removed after the shared memory bridge was stabilized. Their findings are documented here and in `CHANGELOG.md` instead of being left as repo clutter.

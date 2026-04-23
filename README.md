# HWiNFO Monitor

Live hardware sensor dashboard powered by HWiNFO64 shared memory + FastAPI + WebSocket.

## How it works

```
HWiNFO64 (Shared Memory) → Python reader → FastAPI server → WebSocket → Browser dashboard
```

HWiNFO64 exposes real-time sensor data via a shared memory segment (`Global\HWiNFO_SENS_SM2`). The Python reader parses the binary blob and the FastAPI server streams it to any connected browser.

## Setup

**1. Enable HWiNFO shared memory**

Open HWiNFO64 → Settings → Sensors → scroll to the bottom → check **Shared Memory Support**. That's the only HWiNFO config needed.

**2. Install and run**

```bash
cd projects/hwinfo-monitor
pip install -r requirements.txt
python server.py
```

Then open `http://localhost:8080` in your browser.

## Project layout

```
hwinfo-monitor/
├── reader.py          # Shared memory parser (ctypes structs)
├── server.py          # FastAPI + WebSocket server
├── requirements.txt
├── static/
│   └── index.html     # Dashboard UI
└── README.md
```

## Requirements

- HWiNFO64 running with Shared Memory Support enabled
- Python 3.10+
- `fastapi`, `uvicorn[standard]`

## API

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Dashboard |
| `/api/sensors` | GET | One-shot full sensor + reading dump |
| `/api/readings` | GET | Flat list of current readings |
| `/ws` | WS | Live sensor stream (~1 update/sec) |

## Customization

Edit `static/index.html` to:
- Change temperature thresholds (`TEMP_THRESHOLDS`)
- Reorder sensor types (`TYPE_ORDER`)
- Adjust color scheme via CSS variables in `:root`
- Add new card types or gauges
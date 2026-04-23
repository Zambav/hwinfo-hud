"""
HWiNFO Monitor — FastAPI server with WebSocket sensor stream.
"""
import asyncio
import json
import logging
import struct
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from reader import read_hwinfo, get_debug_info

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HWiNFO Monitor")
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


@app.get("/")
def index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "Dashboard not found"}


@app.get("/api/sensors")
def sensors():
    data = read_hwinfo()
    if data is None:
        return {"error": "HWiNFO shared memory not accessible. Check /api/debug."}
    return data


@app.get("/api/readings")
def readings():
    data = read_hwinfo()
    if data is None:
        return {"error": "HWiNFO shared memory not accessible. Check /api/debug."}
    return {"readings": data["readings"], "meta": data.get("meta", {})}


@app.get("/api/debug")
def debug():
    return get_debug_info()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket client connected")
    try:
        while True:
            data = read_hwinfo()
            if data is not None:
                await ws.send_text(json.dumps(data))
            else:
                await ws.send_text(json.dumps({
                    "error": "HWiNFO not available",
                    "debug": get_debug_info(),
                }))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")

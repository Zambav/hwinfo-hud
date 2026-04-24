# Changelog

## 2026-04-23

### Repo cleanup

- Removed obsolete diagnostic and one-off debug scripts:
  - `debug_sm.py`
  - `dump_header.py`
  - `hwinfo_diag.py`
  - `list_sensors.py`
  - `verify.py`
  - local untracked debug helpers used during UI iteration
- Kept the repo focused on the actual product surface:
  - `reader.py`
  - `server.py`
  - `static/index.html`
  - `README.md`
  - `CHANGELOG.md`
  - `requirements.txt`

### Shared memory integration findings

After debugging the HWiNFO bridge, the final working approach was:

- Use the shared memory mapping: `Global\HWiNFO_SENS_SM2`
- Use the mutex: `Global\HWiNFO_SM2_MUTEX`
- Validate the active signature as: `0x53695748` (`HWiS`)
- Read data with packed `ctypes` structures matching the HWiNFO SDK layout
- Stream browser updates through FastAPI + WebSocket

#### Key fixes that made it work

- Corrected the expected shared memory signature
- Corrected struct interpretation and offsets
- Stopped using the wrong assumptions about the buffer layout
- Confirmed privilege level mismatches can block access
- Confirmed HWiNFO needs the sensor window open with Shared Memory Support enabled

### UI redesign work

The dashboard moved away from a plain diagnostic layout toward a more futuristic HUD style.

#### Visual direction

- Deep-space dark background
- Cyan glow highlights
- Glass panels
- Bracket corner accents
- Space Grotesk + JetBrains Mono typography
- Scanline overlay for subtle sci-fi motion

#### Data design direction

We learned that a hardware dashboard gets worse when it tries to show everything.

The current design methodology is:

1. **Prefer signal over completeness**
   - Show the most useful temperatures, power numbers, and loads
   - Remove duplicate and low-value readings

2. **Prefer motion-readable graphs**
   - Live data should fit the page and remain legible while changing
   - Visualizations should emphasize trend and scanability

3. **Filter aggressively**
   - Remove values that are always `0`
   - Remove `N/A`-style clutter
   - Deduplicate storage views when HWiNFO exposes the same hardware multiple ways

### Storage cleanup logic

- Deduplicated repeated drive views that represented the same physical device
- Reduced redundant SSD cards that were effectively copies of each other

### GPU dashboard direction

The GPU section was expanded and refined to focus on useful live telemetry such as:

- GPU core temperature
- hotspot or memory-junction proxy temperature
- board power
- clocks
- VRAM allocation and usage
- performance limit state

Then simplified again where necessary when added detail hurt readability.

### CPU graph direction

The CPU temperature section went through multiple iterations:

1. Static bar-style view
2. Denser per-core tile or heatmap direction
3. Simplified live graph direction for better fit and readability

Main lesson:

- The graph must stay on-screen, update cleanly, and avoid overloading the layout
- Good live telemetry design is not just about showing more data, it is about showing the right moving data in the right format

### Documentation

- Rewrote `README.md` to document:
  - how the bridge works
  - how the app is run
  - what technical fixes made it work
  - the design methodology behind the dashboard
- Added this `CHANGELOG.md` to preserve technical and design learnings instead of leaving them trapped in temporary scripts or chat history

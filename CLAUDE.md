# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Cross-platform (macOS/Windows) desktop GUI app that records heart rate from Polar BLE devices (Verity Sense, H10 chest strap), plots it live, and persists samples to JSON. Built with DearPyGUI + asyncio + Bleak/`polar-python`.

## Commands

```bash
pip install -r requirements.txt   # install deps (polar-python is a git dependency)
python main.py                    # run the app from source

python debug_bleak.py             # troubleshoot raw BLE connectivity via Bleak
python debug_connect.py           # troubleshoot Polar connection via polar-python

pyinstaller hrrecorder.spec       # build a frozen binary (.app on macOS, .exe on Windows)
./create_dmg.sh                   # package the macOS .app into a DMG (run after PyInstaller)
```

There is no test suite, linter, or formatter configured. The `debug_*.py` scripts are the manual verification tools for BLE issues.

## Releasing

CI (`.github/workflows/build.yml`) builds Windows exe + installer and macOS DMG on every push to `main`, and creates a GitHub Release when a `v*` tag is pushed. The release convention (see recent git history) is: bump `__version__` in `version.py`, commit, then tag `vX.Y.Z` and push the tag. The version string flows from `version.py` into the app UI (bottom-right label) and into `hrrecorder.spec`'s macOS bundle metadata — keep them in sync via `version.py` only.

## Architecture

Three modules, one thread. The app runs a **single asyncio event loop on the main thread** (see `HRRecorderApp.run` and `main_loop` in [main.py](main.py)). `main_loop` is an async loop that renders one DearPyGUI frame, then `await asyncio.sleep(0.01)` to yield so BLE (Bleak) coroutines can run. There is deliberately **no separate loop thread** (the old threaded approach is commented out). Consequences:

- Any async work is scheduled with `self.loop.create_task(...)` from synchronous DearPyGUI callbacks. Do not block the main thread — a blocking call freezes both the UI and BLE.
- BLE reads that could hang (battery, disconnect) are wrapped in `asyncio.wait_for(..., timeout=...)` in [recorder.py](recorder.py). Preserve those timeouts.

**BLE → UI data path is decoupled by a `queue.Queue`.** `PolarRecorder`'s HR callback pushes `(timestamp, hr)` onto `self.data_queue` from within BLE callback context; `update_plot` (called every frame) drains the queue, applies the sampling-interval filter, buffers via `DataManager`, and updates the plot. This is what keeps BLE callbacks off the UI-mutation path.

**[main.py](main.py) — `HRRecorderApp`**: owns all UI, state, and orchestration. Note two distinct time cadences: HR arrives continuously but is only *recorded* when `ts - last_sample_time >= sampling_interval`; the buffer is flushed to disk every 30s during recording and again on stop. The plot shows only the last 300 points.

**[recorder.py](recorder.py) — `PolarRecorder`**: wraps `polar_python.PolarDevice` + Bleak. Devices are connected **by exact MAC address** (`connect_to_address`), not by name, to avoid cross-pairing when multiple identical Polar devices are nearby. Connection retries 3×. Battery is read via the standard GATT Battery characteristic (`2A19`).

**[data_manager.py](data_manager.py) — `DataManager`**: buffers points and writes one JSON file per session named `sub-{id}_date-{YYYYMMDD}_time-{HHMMSS}.json`. `save_buffer` re-reads the existing file and appends, so it's safe to call repeatedly during a session.

**Reconnection resilience**: a watchdog (`check_watchdog`, `watchdog_interval = 20s`) fires during recording if no data arrives, and auto disconnect→reconnect→resume-stream. `on_ble_disconnect` (Bleak callback) flips `is_connected`, and `update_plot` reconciles the Connect/Reconnect button visibility each frame.

## Data & log locations

Both live in `~/Documents/HRRecorder/` (see `get_app_data_path` in [main.py](main.py)) — chosen for user visibility and to avoid macOS sandbox permission issues. Recordings are `.json`; the app log is `hrrecorder.log`.

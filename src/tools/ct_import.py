"""Import circuits from FluidSim 4.2 .ct files (best effort).

The original FluidSim .ct files store the circuit as a compressed stream of
vector/pixel drawing primitives. Extracting a clean object model from them is
not reliable, but this module provides several useful capabilities:

* Auto-detection of whether a file is our JSON format or a binary .ct.
* Decoding the binary .ct via the CTDecoder.
* A "symbol map" that recognises common symbol file names from the real
  FluidSim 4.2 library and places editable components on the canvas.
"""

import json
import os
import re
from pathlib import Path

# Default locations of the real FluidSim 4.2 installation if present.
DEFAULT_FLUIDSIM_ROOT = [
    Path.home() / "Downloads" / "FluidSim 4.2",
]

# Map real .ct symbol filenames (without extension) to our catalog ids.
SYMBOL_NAME_MAP = {
    # hydraulic supply
    "hsup1": "pump", "hsup3": "pump_vane", "hsup4": "piston_pump",
    "hsup5": "variable_pump", "s1": "tank", "s3": "tank", "pg1": "pressure_gauge",
    "acc1": "accumulator", "acc2": "accumulator", "amp1": "filter",
    # pneumatic supply
    "psup1": "compressor", "psup3": "air_supply", "pacc1": "accumulator",
    # actuators
    "a1": "cylinder_single", "a2": "cylinder_double", "a3": "cylinder_double",
    "a4": "cylinder_single", "a5": "cylinder_double", "a6": "motor",
    "a7": "cylinder_telescopic", "a8": "motor_bi", "a001": "cylinder_single",
    "a002": "cylinder_double", "a003": "cylinder_telescopic",
    "a004": "cylinder_telescopic", "a005": "cylinder_double",
    "mi2": "motor", "fuact/a1": "cylinder_single", "fuact/a2": "cylinder_double",
    # valves
    "cv2": "check_valve", "cv3": "check_valve", "cv4": "check_valve",
    "cv8": "check_valve", "pco": "pilot_check_valve",
    "prv1": "relief_valve", "prv2": "relief_valve",
    "prvp": "pressure_reducer", "ppo2": "relief_valve", "ppc": "flow_control",
    "ppc2": "flow_control", "throttle": "throttle",
    "sf1": "valve_4_3", "sf2a": "valve_4_3", "sf3": "valve_4_3",
    "sf6": "valve_4_2", "sf7": "valve_4_3", "sf8": "valve_4_2",
    "sf10": "valve_3_2", "sf11": "valve_3_2", "sf12": "valve_2_2",
    "sf13": "valve_2_2", "of2": "one_way_flow_control",
    "t1p": "throttle", "t2p": "throttle",
    "psf8": "valve_5_2", "psf8b": "valve_5_2", "pth1": "throttle",
    # sensors
    "mea1": "pressure_gauge", "mea1b": "pressure_gauge", "mea2": "pressure_gauge",
    "mea3": "flow_meter", "mea4": "temperature_gauge", "mea5": "pressure_switch",
    "ps1": "pressure_switch", "ps2": "pressure_switch",
}


def _resolve_fluidsim_root():
    for p in DEFAULT_FLUIDSIM_ROOT:
        if p.is_dir():
            return p
    return None


def detect_fluidsim_root():
    """Return the path to the FluidSim 4.2 installation if present."""
    return _resolve_fluidsim_root()


def is_binary_ct(data: bytes) -> bool:
    """Return True if the file looks like FluidSim's compressed binary .ct."""
    if not data:
        return False
    if data[:1] == b"{":
        return False
    printable = sum(32 <= b <= 126 for b in data[:64])
    return printable / max(1, len(data[:64])) < 0.5


def load_file(path):
    """Load a .ct file into a component list.

    Returns a dict ``{"status", "message", "circuit"}`` where ``circuit`` is
    compatible with :meth:`CircuitCanvas.load_circuit`.
    """
    path = str(path)
    with open(path, "rb") as f:
        data = f.read()

    # Our own JSON format saved with a .ct extension
    if data[:1] == b"{":
        try:
            return {"status": "ok", "message": "Loaded JSON circuit",
                    "circuit": json.loads(data.decode("utf-8"))}
        except Exception as e:
            return {"status": "error", "message": f"Invalid JSON .ct: {e}",
                    "circuit": None}

    # Try binary decoding and symbol-name extraction
    try:
        from src.tools.ct_browser import CTDecoder
        dec = CTDecoder()
        fmt = dec.detect_format(data)
        decoded = dec.decode_format(data, fmt)
    except Exception as e:
        decoded = data
        fmt = "unknown"

    text = decoded.decode("latin1", errors="replace")
    symbols = []
    seen = set()
    known = sorted(SYMBOL_NAME_MAP.keys(), key=len, reverse=True)
    for name in known:
        pat = re.compile(r"[\"']?" + re.escape(name) + r"(?:\.ct)?[\"']")
        if pat.search(text):
            if name not in seen:
                seen.add(name)
                symbols.append(SYMBOL_NAME_MAP[name])

    if not symbols:
        return {
            "status": "preview_only",
            "message": f"Decoded {fmt} file but could not extract editable components "
                       f"({len(decoded)} bytes). Use the .ct Browser to inspect it.",
            "circuit": None,
        }

    components = []
    for i, sym in enumerate(symbols):
        components.append({
            "id": f"ct_{i}",
            "type": sym,
            "x": 100 + i * 120,
            "y": 150,
            "width": 80,
            "height": 60,
            "rotation": 0,
            "properties": {},
            "name": f"{sym} {i + 1}",
        })
    return {
        "status": "ok",
        "message": f"Imported {len(symbols)} recognised component(s) from .ct file.",
        "circuit": {"components": components, "connections": []},
    }
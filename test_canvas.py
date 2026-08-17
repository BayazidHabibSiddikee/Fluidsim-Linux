#!/usr/bin/env python3
"""Headless Qt tests for the canvas port-switch (toggle) integration.

Run with:  QT_QPA_PLATFORM=offscreen python3 test_canvas.py
"""
import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# A QGuiApplication must exist before `src.ui` builds its QIcon cache.
from PySide6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication([])

from src.ui.canvas import CircuitCanvas
from src.simulation.engine import SimulationEngine, DIRECTIONAL_VALVES


class Results:
    failures = 0
    count = 0


def check(cond, message):
    Results.count += 1
    if not cond:
        Results.failures += 1
        print(f"  FAIL: {message}")


def _make_comp(ctype, cid="c1"):
    return {"id": cid, "type": ctype, "x": 0.0, "y": 0.0,
            "width": 80.0, "height": 60.0, "rotation": 0.0,
            "properties": {}}


def test_set_tool_accepts_all_tools():
    canvas = CircuitCanvas()
    for tool in ("select", "wire", "place", "delete", "pan", "toggle"):
        canvas.set_tool(tool)
        check(canvas._tool == tool, f"set_tool({tool!r}) accepted")


def test_is_directional_valve():
    canvas = CircuitCanvas()
    check(DIRECTIONAL_VALVES, "non-empty valve set")
    for ctype in DIRECTIONAL_VALVES:
        check(canvas.is_directional_valve(ctype), f"{ctype} is directional")
    check(not canvas.is_directional_valve("pump"), "pump is not a valve")


def test_toggle_component_actuation():
    canvas = CircuitCanvas()
    comp = _make_comp("valve_4_3")
    # Pre-seed live sim state like _sim_tick does.
    canvas.set_sim_states({comp["id"]: {"position": 0, "actuated": False}})

    emitted = []
    canvas.actuation_changed.connect(lambda c: emitted.append(c["id"]))

    result = canvas.toggle_component_actuation(comp)
    check(result is True, "toggle returns True on first flip")
    check(comp["properties"].get("actuated") is True, "properties flipped to True")
    st = canvas._sim_states[comp["id"]]
    check(st["actuated"] is True and st["position"] == 1,
          f"live state updated {st}")
    check(emitted == [comp["id"]], f"actuation_changed emitted {emitted}")

    result2 = canvas.toggle_component_actuation(comp)
    check(result2 is False and comp["properties"]["actuated"] is False,
          "second toggle flips back to False")


def test_toggle_ignores_non_valves():
    canvas = CircuitCanvas()
    comp = _make_comp("pump")
    canvas.set_sim_states({})
    result = canvas.toggle_component_actuation(comp)
    check(result is False, "non-valve not toggled")
    check(not comp["properties"], "pump properties untouched")


def main():
    test_set_tool_accepts_all_tools()
    test_is_directional_valve()
    test_toggle_component_actuation()
    test_toggle_ignores_non_valves()
    print(f"test_canvas: {Results.count - Results.failures}/{Results.count} passed")
    if Results.failures:
        print(f"{Results.failures} failure(s)")
        return 1
    return 0


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    sys.exit(main())
#!/usr/bin/env python3
"""Pure-logic tests for the simulation engine's port-switch actuation.

No Qt is imported here (engine.py only depends on the stdlib), so these run
with plain `python3 test_engine.py` even where PySide6 is unavailable.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.simulation.engine import (SimulationEngine, DIRECTIONAL_VALVES)


def _make_comp(ctype, cid="c1"):
    return {"id": cid, "type": ctype, "properties": {}}


class Results:
    failures = 0
    count = 0


def check(cond, message):
    Results.count += 1
    if not cond:
        Results.failures += 1
        print(f"  FAIL: {message}")


def test_directional_valves_cover_5_2_and_5_3():
    for ctype in ("valve_5_2", "valve_5_3"):
        check(ctype in DIRECTIONAL_VALVES, f"{ctype} registered as directional")
        eng = SimulationEngine()
        state = eng._init_state(ctype)
        check(state == {"position": 0, "actuated": False},
              f"{ctype} initial state {state}")


def test_set_actuated():
    eng = SimulationEngine()
    comp = _make_comp("valve_4_3")
    result = eng.set_actuated(comp, True)
    check(result is True, "set_actuated returns True")
    check(comp["properties"]["actuated"] is True, "property written")
    st = eng.get_state("c1")
    check(st.get("actuated") is True and st.get("position") == 1,
          f"state reflects actuation {st}")


def test_set_actuated_ignores_non_valves():
    eng = SimulationEngine()
    comp = _make_comp("pump")
    check(eng.set_actuated(comp, True) is False, "pump not treated as valve")


def test_toggle_flips_back_and_forth():
    eng = SimulationEngine()
    comp = _make_comp("valve_2_2")
    first = eng.toggle_actuation(comp)
    second = eng.toggle_actuation(comp)
    check(first is True and second is False,
          f"toggle cycles True->False ({first}, {second})")
    check(eng.get_state("c1").get("position") == 0,
          "position returns to 0 after two toggles")


def test_all_valve_types_toggle():
    for ctype in DIRECTIONAL_VALVES:
        eng = SimulationEngine()
        comp = _make_comp(ctype)
        eng.toggle_actuation(comp)
        st = eng.get_state("c1")
        check(st.get("actuated") is True and st.get("position") == 1,
              f"{ctype} toggles to actuated/position 1")
        comp["properties"]["actuated"] = False
        eng.set_actuated(comp, False)
        check(eng.get_state("c1").get("position") == 0,
              f"{ctype} releases to position 0")


def main():
    test_directional_valves_cover_5_2_and_5_3()
    test_set_actuated()
    test_set_actuated_ignores_non_valves()
    test_toggle_flips_back_and_forth()
    test_all_valve_types_toggle()

    print(f"test_engine: {Results.count - Results.failures}/{Results.count} passed")
    if Results.failures:
        print(f"{Results.failures} failure(s)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
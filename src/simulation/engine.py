"""Simulation engine for hydraulic and pneumatic circuits."""
import math
from enum import Enum


class PortType(Enum):
    HYDRAULIC_IN = "hydraulic_in"
    HYDRAULIC_OUT = "hydraulic_out"
    PNEUMATIC_IN = "pneumatic_in"
    PNEUMATIC_OUT = "pneumatic_out"
    MECHANICAL = "mechanical"
    PILOT = "pilot"
    DRAIN = "drain"


# All directional (port-switch) valve types share the same actuation model.
DIRECTIONAL_VALVES = ("valve_2_2", "valve_3_2", "valve_4_2", "valve_4_3",
                      "valve_5_2", "valve_5_3")

# Component families (must match the symbol catalog keys in src/symbols/library.py).
PUMP_TYPES = ("gear_pump", "pump", "pump_vane", "piston_pump", "variable_pump",
              "internally_gear_pump", "hydraulic_power_unit")
COMPRESSOR_TYPES = ("compressor", "air_supply", "vacuum_generator")
CYLINDER_TYPES = ("cylinder_single", "cylinder_double", "cylinder_telescopic",
                  "plunger_cylinder", "cylinder_cushioned")
GAUGE_TYPES = ("pressure_gauge", "piston_gauge", "bourdon_gauge", "pressure_switch")
MOTOR_TYPES = ("motor", "motor_bi", "air_motor", "electric_motor")


def _is_pressure_source(ctype):
    return ctype in PUMP_TYPES or ctype in COMPRESSOR_TYPES


def _apply_actuation(state, props):
    """Set ``actuated``/``position`` state from a component's properties."""
    actuated = bool(props.get("actuated", False))
    state["actuated"] = actuated
    state["position"] = 1 if actuated else 0


class SimulationEngine:
    def __init__(self):
        self.mode = "hydraulic"
        self.time = 0.0
        self.dt = 0.001
        self.pressure = 101325.0
        self.gravity = 9.81
        self.fluid_density = 870.0
        self.air_density = 1.225
        self.component_states = {}

    def set_mode(self, mode):
        self.mode = mode
        if mode == "pneumatic":
            self.pressure = 600000.0
        else:
            self.pressure = 101325.0

    def reset(self):
        self.time = 0.0
        self.component_states.clear()

    def step(self, components, connections):
        self.time += self.dt
        for comp in components:
            cid = comp["id"]
            ctype = comp["type"]
            state = self.component_states.get(cid, self._init_state(ctype))
            self._update_component(state, ctype, comp, components, connections)
            self.component_states[cid] = state
        self._propagate_fluid(components, connections)

    def _init_state(self, ctype):
        if ctype in CYLINDER_TYPES:
            return {"position": 0.0, "velocity": 0.0, "pressure_a": 0.0, "pressure_b": 0.0}
        elif ctype in DIRECTIONAL_VALVES:
            return {"position": 0, "actuated": False}
        elif ctype in PUMP_TYPES:
            return {"flow_rate": 0.02, "speed": 1500, "on": True}
        elif ctype in COMPRESSOR_TYPES:
            return {"flow_rate": 0.5, "on": True}
        elif ctype == "tank":
            return {"level": 0.8, "pressure": 0.0}
        elif ctype == "pressure_gauge":
            return {"reading": 0.0}
        elif ctype == "flow_meter":
            return {"reading": 0.0}
        elif ctype == "relief_valve":
            return {"set_pressure": 10e6, "open": False}
        elif ctype == "check_valve":
            return {"open": False}
        elif ctype == "throttle":
            return {"opening": 1.0}
        elif ctype == "filter":
            return {"blocked": False, "delta_p": 0}
        elif ctype in MOTOR_TYPES:
            return {"speed": 0.0, "torque": 0.0}
        elif ctype == "spring_return":
            return {"force": 0.0}
        else:
            return {}

    def _update_component(self, state, ctype, comp, components, connections):
        props = comp.get("properties", {})
        if ctype in PUMP_TYPES:
            if props.get("running", True):
                state["flow_rate"] = props.get("flow_rate", 0.02)
            else:
                state["flow_rate"] = 0.0
        elif ctype in COMPRESSOR_TYPES:
            if props.get("running", True):
                state["flow_rate"] = props.get("flow_rate", 0.5)
            else:
                state["flow_rate"] = 0.0
        elif ctype in DIRECTIONAL_VALVES:
            _apply_actuation(state, props)
        elif ctype == "cylinder_single":
            sp = state["position"]
            if sp < 1.0 and state["pressure_a"] > 1e5:
                force = (state["pressure_a"] - self.pressure) * props.get("bore_area", 0.00126)
                mass = props.get("mass", 2.0)
                state["velocity"] += (force / mass) * self.dt
                state["velocity"] *= 0.95
                state["position"] = min(1.0, sp + state["velocity"] * self.dt)
            elif state["pressure_a"] < 1e5 and state["position"] > 0:
                state["position"] = max(0.0, sp - 0.5 * self.dt)
                state["velocity"] = 0.0
        elif ctype in ("cylinder_double", "cylinder_telescopic",
                       "plunger_cylinder", "cylinder_cushioned"):
            sp = state["position"]
            f_a = (state["pressure_a"] - self.pressure) * props.get("bore_area", 0.00126)
            f_b = (state["pressure_b"] - self.pressure) * props.get("rod_area", 0.0006)
            net = f_a - f_b
            mass = props.get("mass", 2.0)
            state["velocity"] += (net / mass) * self.dt
            state["velocity"] *= 0.95
            state["position"] = max(0.0, min(1.0, sp + state["velocity"] * self.dt))
        elif ctype in GAUGE_TYPES:
            state["reading"] = state.get("pressure_a", 0.0)
        elif ctype == "relief_valve":
            state["open"] = state.get("pressure_a", 0) > props.get("set_pressure", 10e6)
        elif ctype == "check_valve":
            state["open"] = state.get("pressure_a", 0) > state.get("pressure_b", 0)
        elif ctype in MOTOR_TYPES:
            if props.get("running", True):
                state["speed"] = props.get("speed", 500)
                state["torque"] = props.get("torque", 10)
            else:
                state["speed"] = 0
                state["torque"] = 0

    def _propagate_fluid(self, components, connections):
        """Flood-fill pressure through the connection graph.

        Pumps/compressors are pressure sources. Directional valves only
        pass pressure when actuated. Tanks are drains (ground).
        """
        comp_map = {c["id"]: c for c in components}
        adj = {cid: [] for cid in comp_map}
        for conn in connections:
            a = conn.get("from_component")
            b = conn.get("to_component")
            if a in adj and b in adj:
                adj[a].append(b)
                adj[b].append(a)

        pressure = (self.pressure + 5e5 if self.mode == "hydraulic"
                    else self.pressure + 6e5)

        # Neutral networks: every connected node not reached by a source
        # or a tank gets drained towards the tank/atmosphere pressure.
        pressurized = set()
        for comp in components:
            cid = comp["id"]
            state = self.component_states.get(cid, {})
            ctype = comp.get("type", "")
            if _is_pressure_source(ctype) and state.get("flow_rate", 0) > 0:
                pressurized.add(cid)
            elif ctype == "tank":
                # Tank is a drain: neutral networks connected to it lose
                # pressure; the tank itself holds system pressure.
                state["pressure"] = self.pressure
                state["level"] = min(1.0, state.get("level", 0.8) + 0.0001)

        # Flood-fill from each source through open valves.
        stack = list(pressurized)
        while stack:
            cid = stack.pop()
            state = self.component_states.get(cid, {})
            for key in ("pressure_a", "pressure_b", "reading"):
                if key in state:
                    state[key] = pressure
            for nxt in adj.get(cid, []):
                if nxt in pressurized:
                    continue
                ntype = comp_map[nxt].get("type", "")
                if ntype in DIRECTIONAL_VALVES:
                    nstate = self.component_states.get(nxt, {})
                    if not nstate.get("actuated"):
                        continue
                pressurized.add(nxt)
                stack.append(nxt)

        # Drain every node that ended up in a neutral (unpressurized)
        # network: it is not reachable from a source through open valves.
        for comp in components:
            cid = comp["id"]
            state = self.component_states.get(cid, {})
            if cid in pressurized:
                continue
            ctype = comp.get("type", "")
            if ctype == "tank":
                continue
            for key in ("pressure_a", "pressure_b", "reading"):
                if key in state:
                    state[key] = max(0.0, state[key] - 5e5 * self.dt)

    def get_state(self, component_id):
        return self.component_states.get(component_id, {})

    # ------------------------------------------------------------------
    # Port-switch actuation (interactive valve toggling)
    # ------------------------------------------------------------------

    def set_actuated(self, component, value):
        """Set a directional valve's ``properties['actuated']`` and refresh
        its live state so the canvas can animate the switch immediately."""
        ctype = component.get("type", "")
        if ctype not in DIRECTIONAL_VALVES:
            return False
        props = component.setdefault("properties", {})
        props["actuated"] = bool(value)
        self._ensure_state(component, ctype, props)
        return bool(value)

    def toggle_actuation(self, component):
        """Flip a directional valve's actuation. Returns the new value."""
        ctype = component.get("type", "")
        props = component.setdefault("properties", {})
        new_value = not bool(props.get("actuated", False))
        return self.set_actuated(component, new_value)

    def _ensure_state(self, component, ctype, props):
        cid = component["id"]
        state = self.component_states.setdefault(cid, self._init_state(ctype))
        if ctype in DIRECTIONAL_VALVES:
            _apply_actuation(state, props)

    def get_pressure(self, component_id):
        state = self.component_states.get(component_id, {})
        return state.get("pressure_a", 0.0)

    def get_flow(self, component_id):
        state = self.component_states.get(component_id, {})
        return state.get("flow_rate", state.get("reading", 0.0))

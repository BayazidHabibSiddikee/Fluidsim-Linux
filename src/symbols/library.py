"""Symbol library for FluidSim Linux hydraulic/pneumatic circuit simulator."""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit
)
from PySide6.QtCore import Signal, Qt, QRectF, QMimeData
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPainterPath
)


class _SymbolTreeWidget(QTreeWidget):
    """QTreeWidget that carries the symbol id in drag mime data."""
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return
        sym_id = item.data(0, Qt.UserRole)
        if not sym_id:
            return
        from PySide6.QtGui import QDrag
        mime = QMimeData()
        mime.setText(str(sym_id))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(supportedActions)

# ---------------------------------------------------------------------------
# Symbol Catalog
# ---------------------------------------------------------------------------

SYMBOL_CATALOG = {
    "Hydraulic": {
        "Sources": ["gear_pump", "pump", "pump_vane", "piston_pump", "variable_pump",
                     "internally_gear_pump", "hydraulic_power_unit"],
        "Actuators": [
            "cylinder_single", "cylinder_double", "cylinder_telescopic",
            "plunger_cylinder", "cylinder_cushioned",
            "motor", "motor_bi",
        ],
        "Directional Valves": [
            "valve_2_2", "valve_3_2", "valve_4_2", "valve_4_3",
            "valve_5_2", "valve_5_3",
        ],
        "Pressure & Flow Valves": [
            "check_valve", "check_valve_delockable", "check_valve_double_delockable",
            "pilot_check_valve", "relief_valve", "pressure_reducer",
            "sequence_valve",
            "throttle", "needle_valve", "needle_restrictor", "gap_restrictor",
            "one_way_flow_control", "flow_control",
        ],
        "Sensors": [
            "pressure_gauge", "piston_gauge", "bourdon_gauge",
            "pressure_switch", "flow_meter", "temperature_gauge",
        ],
        "Accessories": [
            "tank", "filter", "accumulator", "heat_exchanger",
            "water_cooler", "air_cooler", "heating_element",
        ],
        "Power Unit": [
            "hydraulic_power_unit", "reservoir_elevated",
        ],
    },
    "Pneumatic": {
        "Sources": ["compressor", "air_supply", "vacuum_generator"],
        "Actuators": [
            "cylinder_single", "cylinder_double", "cylinder_telescopic",
            "air_motor", "motor_bi",
        ],
        "Directional Valves": [
            "valve_2_2", "valve_3_2", "valve_3_2_unloaded",
            "valve_4_2", "valve_4_3",
            "valve_5_2", "valve_5_3",
        ],
        "Pressure & Flow Valves": [
            "check_valve", "relief_valve", "shuttle_valve",
            "two_pressure_valve", "throttle", "one_way_flow_control",
            "quick_exhaust",
        ],
        "Sensors": [
            "pressure_switch", "limit_switch", "proximity_sensor", "flow_meter",
        ],
        "Accessories": [
            "air_service_unit", "regulator", "lubricator", "silencer",
        ],
    },
    "Electrical": {
        "Power Supply": ["battery", "dc_supply", "ac_mains", "ground"],
        "Actuators": ["electric_motor", "solenoid", "lamp", "speaker"],
        "Relays & Coils": ["relay", "relay_nc", "current_limiter", "relay_timer"],
        "Switches": [
            "switch_push", "switch_push_nc", "switch_toggle",
            "switch_limit", "switch_proximity",
        ],
        "Protection": ["fuse", "buzzer"],
        "Semiconductors": ["diode", "transistor", "op_amp"],
    },
    "Digital & Control": {
        "Logic Gates": ["and_gate", "or_gate", "not_gate", "nand_gate", "nor_gate", "xor_gate"],
        "Sequential": ["timer", "d_flip_flop", "jk_flip_flop", "sr_latch",
                        "counter", "pulse_generator", "shift_register"],
        "Controllers": ["plc", "comparator", "pid_controller"],
        "Display": ["display_7seg"],
    },
}

# ---------------------------------------------------------------------------
# Per-component port definitions
# Each entry is a list of (side, label) pairs that exactly match the real
# FluidSim 4.2 port count and names.  The canvas uses get_component_ports()
# instead of the old generic 4-port system.
# ---------------------------------------------------------------------------

COMPONENT_PORTS = {
    # Hydraulic sources — suction (bottom/tank) + pressure (top)
    "pump":            [("top", "P"), ("bottom", "T")],
    "gear_pump":       [("top", "P"), ("bottom", "T")],
    "pump_vane":       [("top", "P"), ("bottom", "T")],
    "piston_pump":     [("top", "P"), ("bottom", "T")],
    "variable_pump":   [("top", "P"), ("bottom", "T")],
    # Pneumatic sources
    "compressor":      [("top", "P"), ("bottom", "T")],
    "air_supply":      [("bottom", "P")],
    "vacuum_generator":[("top", "V"), ("bottom", "P")],
    # Actuators
    "cylinder_single": [("top", "A"), ("bottom", "T")],
    "cylinder_double": [("top", "A"), ("bottom", "B")],
    "cylinder_telescopic": [("top", "A"), ("bottom", "B")],
    "motor":           [("top", "P"), ("bottom", "T")],
    "air_motor":       [("top", "P"), ("bottom", "T")],
    "motor_bi":        [("top", "P"), ("bottom", "T"), ("left", "A"), ("right", "B")],
    # Directional valves
    "valve_2_2":       [("top", "P"), ("bottom", "A")],
    "valve_3_2":       [("top", "P"), ("bottom", "T"), ("right", "A")],
    "valve_4_2":       [("top", "P"), ("bottom", "T"), ("left", "A"), ("right", "B")],
    "valve_4_3":       [("top", "P"), ("bottom", "T"), ("left", "A"), ("right", "B")],
    "valve_5_2":       [("top", "P"), ("bottom", "R"), ("left", "A"), ("right", "B")],
    "valve_5_3":       [("top", "P"), ("bottom", "R"), ("left", "A"), ("right", "B")],
    # Pressure / flow valves
    "check_valve":     [("left", "A"), ("right", "B")],
    "pilot_check_valve": [("left", "A"), ("right", "B"), ("top", "X")],
    "relief_valve":    [("top", "P"), ("bottom", "T")],
    "pressure_reducer":[("top", "P"), ("bottom", "A")],
    "throttle":        [("left", "A"), ("right", "B")],
    "needle_valve":    [("left", "A"), ("right", "B")],
    "one_way_flow_control": [("left", "A"), ("right", "B")],
    "flow_control":    [("left", "A"), ("right", "B")],
    "shuttle_valve":   [("left", "A"), ("right", "B"), ("bottom", "C")],
    "two_pressure_valve": [("left", "A"), ("right", "B"), ("bottom", "C")],
    "quick_exhaust":   [("top", "P"), ("left", "A"), ("right", "R")],
    # Sensors
    "pressure_gauge":  [("bottom", "P")],
    "pressure_switch": [("bottom", "P"), ("top", "S")],
    "flow_meter":      [("left", "A"), ("right", "B")],
    "temperature_gauge": [("bottom", "T")],
    "limit_switch":    [("bottom", "S")],
    "proximity_sensor":[("bottom", "S")],
    # Accessories
    "tank":            [("top", "T")],
    "filter":          [("top", "A"), ("bottom", "B")],
    "accumulator":     [("bottom", "P")],
    "heat_exchanger":  [("top", "A"), ("bottom", "B")],
    "regulator":       [("top", "P"), ("bottom", "A")],
    "lubricator":      [("top", "A"), ("bottom", "B")],
    "silencer":        [("top", "A")],
    "air_service_unit":[("top", "P"), ("bottom", "A")],
    # Electrical
    "battery":         [("top", "+"), ("bottom", "-")],
    "dc_supply":       [("top", "+"), ("bottom", "-")],
    "ac_mains":        [("top", "L"), ("bottom", "N")],
    "ground":          [("top", "G")],
    "electric_motor":  [("left", "+"), ("right", "-")],
    "solenoid":        [("top", "A"), ("bottom", "K")],
    "lamp":            [("top", "A"), ("bottom", "K")],
    "relay":           [("top", "A1"), ("bottom", "A2"), ("left", "NC"), ("right", "NO")],
    "relay_nc":        [("top", "A1"), ("bottom", "A2"), ("left", "NC"), ("right", "NO")],
    "current_limiter": [("left", "A"), ("right", "B")],
    "switch_push":     [("left", "1"), ("right", "2")],
    "switch_push_nc":  [("left", "1"), ("right", "2")],
    "switch_toggle":   [("left", "1"), ("right", "2")],
    "switch_limit":    [("left", "1"), ("right", "2")],
    "switch_proximity":[("left", "1"), ("right", "2")],
    "fuse":            [("left", "1"), ("right", "2")],
    "buzzer":          [("top", "+"), ("bottom", "-")],
    # Digital & Logic
    "and_gate":        [("left", "A"), ("top", "B"), ("right", "Y")],
    "or_gate":         [("left", "A"), ("top", "B"), ("right", "Y")],
    "not_gate":        [("left", "A"), ("right", "Y")],
    "nand_gate":       [("left", "A"), ("top", "B"), ("right", "Y")],
    "nor_gate":        [("left", "A"), ("top", "B"), ("right", "Y")],
    "xor_gate":        [("left", "A"), ("top", "B"), ("right", "Y")],
    "timer":           [("left", "IN"), ("right", "OUT"), ("top", "EN")],
    "d_flip_flop":     [("left", "D"), ("top", "CLK"), ("right", "Q"), ("bottom", "Q̄")],
    "counter":         [("left", "IN"), ("top", "RST"), ("right", "OUT")],
    "pulse_generator": [("top", "EN"), ("right", "OUT")],
    "plc":             [("left", "I"), ("right", "O"), ("top", "P"), ("bottom", "G")],
    "comparator":      [("left", "A"), ("top", "B"), ("right", "Y")],
    "pid_controller":  [("left", "SP"), ("top", "PV"), ("right", "OUT")],
    # New components from FluidSim 4.2 catalog
    "internally_gear_pump": [("top", "P"), ("bottom", "T")],
    "hydraulic_power_unit": [("top", "P"), ("bottom", "T")],
    "reservoir_elevated":   [("top", "T")],
    "plunger_cylinder":     [("top", "A"), ("bottom", "T")],
    "cylinder_cushioned":   [("top", "A"), ("bottom", "B")],
    "check_valve_delockable": [("left", "A"), ("right", "B")],
    "check_valve_double_delockable": [("left", "A"), ("right", "B")],
    "sequence_valve":      [("top", "P"), ("bottom", "A")],
    "needle_restrictor":   [("left", "A"), ("right", "B")],
    "gap_restrictor":      [("left", "A"), ("right", "B")],
    "piston_gauge":        [("bottom", "P")],
    "bourdon_gauge":       [("bottom", "P")],
    "water_cooler":        [("top", "A"), ("bottom", "B")],
    "air_cooler":          [("top", "A"), ("bottom", "B")],
    "heating_element":     [("top", "A"), ("bottom", "B")],
    "valve_3_2_unloaded":  [("top", "P"), ("bottom", "T"), ("right", "A")],
    "speaker":             [("left", "+"), ("right", "-")],
    "relay_timer":         [("top", "A1"), ("bottom", "A2"), ("left", "NC"), ("right", "NO")],
    "diode":               [("left", "A"), ("right", "B")],
    "transistor":          [("left", "B"), ("top", "E"), ("right", "C")],
    "op_amp":              [("left", "A"), ("top", "B"), ("right", "Y")],
    "jk_flip_flop":        [("left", "J"), ("top", "CLK"), ("right", "Q"), ("bottom", "Q̄")],
    "sr_latch":            [("left", "S"), ("top", "R"), ("right", "Q"), ("bottom", "Q̄")],
    "shift_register":      [("left", "IN"), ("top", "CLK"), ("right", "OUT")],
    "display_7seg":        [("left", "A"), ("right", "B")],
}


def get_component_ports(comp):
    """Return a list of port descriptors for *comp*.

    Each descriptor is a dict with keys ``side`` (str), ``label`` (str) and
    ``pos`` (QPointF in scene coordinates).  The positions are computed from
    the component bounding rect and rotation.
    """
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QTransform

    ctype = comp.get("type", "")
    port_defs = COMPONENT_PORTS.get(ctype)

    x, y, w, h = comp["x"], comp["y"], comp["width"], comp["height"]
    rot = comp.get("rotation", 0)

    if port_defs is None:
        # Unknown component: show minimal 2 ports (top + bottom) to avoid clutter
        port_defs = [("top", "A"), ("bottom", "B")]

    side_to_pos = {
        "top":    QPointF(x + w / 2, y),
        "right":  QPointF(x + w,     y + h / 2),
        "bottom": QPointF(x + w / 2, y + h),
        "left":   QPointF(x,         y + h / 2),
    }

    ports = []
    for side, label in port_defs:
        pos = side_to_pos.get(side, QPointF(x + w / 2, y + h / 2))
        if rot != 0:
            cx, cy = x + w / 2, y + h / 2
            t = QTransform()
            t.translate(cx, cy)
            t.rotate(rot)
            t.translate(-cx, -cy)
            pos = t.map(pos)
        ports.append({"side": side, "label": label, "comp_id": comp["id"], "pos": pos})
    return ports


# Keep PORT_LABELS for backward compat (now unused in canvas, kept for tests).
PORT_LABELS = {k: {s: l for s, l in v} for k, v in COMPONENT_PORTS.items()}




DISPLAY_NAMES = {
    "pump": "Fixed Displacement Pump",
    "gear_pump": "Gear Pump",
    "pump_vane": "Vane Pump",
    "piston_pump": "Piston Pump",
    "variable_pump": "Variable Displacement Pump",
    "cylinder_single": "Single-Acting Cylinder",
    "cylinder_double": "Double-Acting Cylinder",
    "cylinder_telescopic": "Telescopic Cylinder",
    "motor": "Hydraulic Motor",
    "air_motor": "Air Motor",
    "motor_bi": "Reversible Motor",
    "valve_2_2": "2/2 Way Valve",
    "valve_3_2": "3/2 Way Valve",
    "valve_4_2": "4/2 Way Valve",
    "valve_4_3": "4/3 Way Valve",
    "valve_5_2": "5/2 Way Valve",
    "valve_5_3": "5/3 Way Valve",
    "check_valve": "Check Valve",
    "pilot_check_valve": "Pilot-Operated Check Valve",
    "relief_valve": "Relief Valve",
    "pressure_reducer": "Pressure Reducing Valve",
    "throttle": "Throttle Valve",
    "needle_valve": "Needle Valve",
    "one_way_flow_control": "One-Way Flow Control Valve",
    "flow_control": "Flow Control Valve",
    "shuttle_valve": "Shuttle Valve",
    "two_pressure_valve": "Two-Pressure (AND) Valve",
    "tank": "Tank / Reservoir",
    "pressure_gauge": "Pressure Gauge",
    "pressure_switch": "Pressure Switch",
    "temperature_gauge": "Temperature Gauge",
    "flow_meter": "Flow Meter",
    "filter": "Filter",
    "accumulator": "Accumulator",
    "heat_exchanger": "Heat Exchanger",
    "compressor": "Compressor",
    "air_supply": "Air Supply",
    "vacuum_generator": "Vacuum Generator",
    "regulator": "Pressure Regulator",
    "lubricator": "Lubricator",
    "silencer": "Silencer",
    "air_service_unit": "Air Service Unit (FRL)",
    "quick_exhaust": "Quick Exhaust Valve",
    "limit_switch": "Limit Switch",
    "proximity_sensor": "Proximity Sensor",
    # Electrical
    "battery": "Battery / DC Source",
    "dc_supply": "DC Power Supply",
    "ac_mains": "AC Mains Supply",
    "ground": "Ground",
    "electric_motor": "Electric Motor",
    "solenoid": "Solenoid",
    "lamp": "Indicator Lamp",
    "relay": "Relay (NO)",
    "relay_nc": "Relay (NC)",
    "current_limiter": "Current Limiter",
    "switch_push": "Push Button (NO)",
    "switch_push_nc": "Push Button (NC)",
    "switch_toggle": "Toggle Switch",
    "switch_limit": "Limit Switch (Elec.)",
    "switch_proximity": "Proximity Switch",
    "fuse": "Fuse",
    "buzzer": "Buzzer / Alarm",
    # Digital & Control
    "and_gate": "AND Gate",
    "or_gate": "OR Gate",
    "not_gate": "NOT Gate",
    "nand_gate": "NAND Gate",
    "nor_gate": "NOR Gate",
    "xor_gate": "XOR Gate",
    "timer": "Timer / Delay",
    "d_flip_flop": "D Flip-Flop",
    "counter": "Counter",
    "pulse_generator": "Pulse Generator",
    "plc": "PLC / Controller",
    "comparator": "Comparator",
    "pid_controller": "PID Controller",
    # New components from FluidSim 4.2 catalog
    "internally_gear_pump": "Internally Toothed Gear Pump",
    "hydraulic_power_unit": "Hydraulic Power Unit",
    "reservoir_elevated": "Elevated Reservoir",
    "plunger_cylinder": "Plunger Cylinder",
    "cylinder_cushioned": "Double-Acting Cylinder (Cushioned)",
    "check_valve_delockable": "Delockable Check Valve",
    "check_valve_double_delockable": "Delockable Double Check Valve",
    "sequence_valve": "Sequence Valve",
    "needle_restrictor": "Needle Restrictor",
    "gap_restrictor": "Gap Restrictor with Helix",
    "piston_gauge": "Piston Pressure Gauge",
    "bourdon_gauge": "Bourdon-Tube Pressure Gauge",
    "water_cooler": "Water Cooler",
    "air_cooler": "Air Cooler",
    "heating_element": "Heating Element",
    "valve_3_2_unloaded": "3/2 Way Valve (Unloaded)",
    "speaker": "Speaker",
    "relay_timer": "Timer Relay",
    "diode": "Diode",
    "transistor": "Transistor",
    "op_amp": "Op-Amp",
    "jk_flip_flop": "JK Flip-Flop",
    "sr_latch": "SR Latch",
    "shift_register": "Shift Register",
    "display_7seg": "7-Segment Display",
}

# ---------------------------------------------------------------------------
# Component Defaults
# ---------------------------------------------------------------------------

COMPONENT_DEFAULTS = {
    "pump": {"flow_rate": 20.0, "pressure_max": 250.0, "rpm": 1500},
    "gear_pump": {"flow_rate": 30.0, "pressure_max": 210.0, "rpm": 1500},
    "pump_vane": {"flow_rate": 15.0, "pressure_max": 175.0, "rpm": 1500},
    "piston_pump": {"flow_rate": 40.0, "pressure_max": 400.0, "rpm": 1500},
    "variable_pump": {"flow_rate": 60.0, "pressure_max": 350.0, "rpm": 1500},
    "cylinder_single": {"bore": 50.0, "stroke": 200.0, "rod_diameter": 20.0},
    "cylinder_double": {"bore": 50.0, "stroke": 200.0, "rod_diameter": 20.0},
    "cylinder_telescopic": {"bore": 80.0, "stroke": 400.0, "stages": 3},
    "motor": {"displacement": 25.0, "pressure_max": 250.0, "rpm_max": 3000},
    "air_motor": {"displacement": 50.0, "rpm_max": 8000},
    "motor_bi": {"displacement": 25.0, "pressure_max": 250.0, "rpm_max": 3000},
    "valve_2_2": {"position": "normally_closed", "actuation": "solenoid"},
    "valve_3_2": {"position": "normally_closed", "actuation": "solenoid"},
    "valve_4_2": {"position": "center_closed", "actuation": "solenoid"},
    "valve_4_3": {"position": "center_closed", "actuation": "solenoid"},
    "valve_5_2": {"position": "center_closed", "actuation": "solenoid"},
    "valve_5_3": {"position": "center_closed", "actuation": "solenoid"},
    "check_valve": {"cracking_pressure": 0.5},
    "pilot_check_valve": {"cracking_pressure": 0.5, "pilot_pressure": 30.0},
    "relief_valve": {"set_pressure": 200.0, "flow_max": 50.0},
    "pressure_reducer": {"set_pressure": 100.0, "flow_max": 40.0},
    "throttle": {"opening": 50.0, "flow_max": 30.0},
    "needle_valve": {"opening": 50.0, "flow_max": 25.0},
    "one_way_flow_control": {"opening": 50.0, "flow_max": 30.0},
    "flow_control": {"set_flow": 20.0, "flow_max": 40.0},
    "shuttle_valve": {"cracking_pressure": 0.3},
    "two_pressure_valve": {"cracking_pressure": 0.3},
    "tank": {"volume": 50.0, "fluid": "hydraulic_oil"},
    "pressure_gauge": {"range_max": 400.0, "unit": "bar"},
    "pressure_switch": {"set_pressure": 100.0, "hysteresis": 10.0},
    "temperature_gauge": {"range_max": 150.0, "unit": "degC"},
    "flow_meter": {"range_max": 100.0, "unit": "l/min"},
    "filter": {"rating": 10.0, "type": "return_line"},
    "accumulator": {"volume": 1.0, "pre_charge": 100.0, "type": "bladder"},
    "heat_exchanger": {"cooling_power": 50.0, "flow_max": 100.0},
    "compressor": {"flow_rate": 500.0, "pressure_max": 10.0, "type": "rotary"},
    "air_supply": {"pressure": 6.0, "flow_rate": 1000.0},
    "vacuum_generator": {"vacuum_level": -0.85, "flow_rate": 200.0},
    "regulator": {"inlet_pressure": 10.0, "outlet_pressure": 4.0},
    "lubricator": {"capacity": 0.5},
    "silencer": {"insertion_loss": 35.0},
    "air_service_unit": {"filter_rating": 5.0, "outlet_pressure": 6.0},
    "quick_exhaust": {"bore": 20.0},
    "limit_switch": {"roller": "roller_lever"},
    "proximity_sensor": {"sensing_range": 5.0},
    # Electrical
    "battery": {"voltage": 24.0},
    "dc_supply": {"voltage": 24.0, "current_max": 10.0},
    "ac_mains": {"voltage": 230.0, "frequency": 50.0},
    "ground": {}, "electric_motor": {"voltage": 24.0, "power": 500.0},
    "solenoid": {"voltage": 24.0, "nominal_current": 0.5},
    "lamp": {"voltage": 24.0, "color": "green"},
    "relay": {"voltage": 24.0, "contacts": 2, "type": "normally_open"},
    "relay_nc": {"voltage": 24.0, "contacts": 2, "type": "normally_closed"},
    "current_limiter": {"set_current": 5.0},
    "switch_push": {"contact": "normally_open"},
    "switch_push_nc": {"contact": "normally_closed"},
    "switch_toggle": {"positions": 2},
    "switch_limit": {"contact": "normally_open"},
    "switch_proximity": {"sensing_range": 5.0, "type": "inductive"},
    "fuse": {"rating": 10.0},
    "buzzer": {"voltage": 24.0, "db": 85.0},
    # Digital & Control
    "and_gate": {"inputs": 2}, "or_gate": {"inputs": 2},
    "not_gate": {}, "nand_gate": {"inputs": 2}, "nor_gate": {"inputs": 2},
    "xor_gate": {"inputs": 2}, "timer": {"delay": 1.0, "mode": "on_delay"},
    "d_flip_flop": {}, "counter": {"count_max": 9999}, "pulse_generator": {"period": 1.0},
    "plc": {"inputs": 8, "outputs": 8}, "comparator": {"threshold": 5.0},
    "pid_controller": {"kp": 1.0, "ki": 0.1, "kd": 0.01},
    # New components
    "internally_gear_pump": {"flow_rate": 30.0, "pressure_max": 210.0, "rpm": 1500},
    "hydraulic_power_unit": {"flow_rate": 50.0, "pressure_max": 250.0, "rpm": 1500},
    "reservoir_elevated":   {"volume": 100.0, "fluid": "hydraulic_oil"},
    "plunger_cylinder":     {"bore": 40.0, "stroke": 200.0},
    "cylinder_cushioned":   {"bore": 50.0, "stroke": 200.0, "rod_diameter": 20.0},
    "check_valve_delockable": {"cracking_pressure": 0.3},
    "check_valve_double_delockable": {"cracking_pressure": 0.3},
    "sequence_valve":       {"set_pressure": 50.0, "flow_max": 30.0},
    "needle_restrictor":    {"opening": 50.0, "flow_max": 25.0},
    "gap_restrictor":       {"opening": 50.0, "flow_max": 30.0},
    "piston_gauge":         {"range_max": 400.0, "unit": "bar"},
    "bourdon_gauge":        {"range_max": 400.0, "unit": "bar"},
    "water_cooler":         {"cooling_power": 50.0, "flow_max": 100.0},
    "air_cooler":           {"cooling_power": 30.0, "flow_max": 80.0},
    "heating_element":      {"heating_power": 2.0, "max_flow": 50.0},
    "valve_3_2_unloaded":   {"position": "normally_open", "actuation": "solenoid"},
    "speaker":              {"voltage": 24.0, "impedance": 8.0},
    "relay_timer":          {"voltage": 24.0, "delay": 5.0, "contacts": 1},
    "diode":                {},
    "transistor":           {"voltage": 24.0, "current_max": 0.5},
    "op_amp":               {"gain": 100000.0},
    "jk_flip_flop":         {},
    "sr_latch":             {},
    "shift_register":       {"stages": 8},
    "display_7seg":         {},
}

# ---------------------------------------------------------------------------
# Component Properties (editable in the properties panel)
# ---------------------------------------------------------------------------

COMPONENT_PROPERTIES = {
    "pump": [
        {"key": "flow_rate", "label": "Flow Rate (L/min)", "type": "float",
         "default": 20.0, "min": 0.1, "max": 500.0},
        {"key": "pressure_max", "label": "Max Pressure (bar)", "type": "float",
         "default": 250.0, "min": 1.0, "max": 1000.0},
        {"key": "rpm", "label": "Speed (RPM)", "type": "int",
         "default": 1500, "min": 100, "max": 6000},
    ],
    "pump_vane": [
        {"key": "flow_rate", "label": "Flow Rate (L/min)", "type": "float",
         "default": 15.0, "min": 0.1, "max": 200.0},
        {"key": "pressure_max", "label": "Max Pressure (bar)", "type": "float",
         "default": 175.0, "min": 1.0, "max": 500.0},
        {"key": "rpm", "label": "Speed (RPM)", "type": "int",
         "default": 1500, "min": 100, "max": 6000},
    ],
    "piston_pump": [
        {"key": "flow_rate", "label": "Flow Rate (L/min)", "type": "float",
         "default": 40.0, "min": 0.1, "max": 1000.0},
        {"key": "pressure_max", "label": "Max Pressure (bar)", "type": "float",
         "default": 400.0, "min": 1.0, "max": 1500.0},
        {"key": "rpm", "label": "Speed (RPM)", "type": "int",
         "default": 1500, "min": 100, "max": 6000},
    ],
    "cylinder_single": [
        {"key": "bore", "label": "Bore (mm)", "type": "float",
         "default": 50.0, "min": 5.0, "max": 500.0},
        {"key": "stroke", "label": "Stroke (mm)", "type": "float",
         "default": 200.0, "min": 10.0, "max": 3000.0},
        {"key": "rod_diameter", "label": "Rod Diameter (mm)", "type": "float",
         "default": 20.0, "min": 5.0, "max": 200.0},
    ],
    "cylinder_double": [
        {"key": "bore", "label": "Bore (mm)", "type": "float",
         "default": 50.0, "min": 5.0, "max": 500.0},
        {"key": "stroke", "label": "Stroke (mm)", "type": "float",
         "default": 200.0, "min": 10.0, "max": 3000.0},
        {"key": "rod_diameter", "label": "Rod Diameter (mm)", "type": "float",
         "default": 20.0, "min": 5.0, "max": 200.0},
    ],
    "motor": [
        {"key": "displacement", "label": "Displacement (cc/rev)", "type": "float",
         "default": 25.0, "min": 1.0, "max": 500.0},
        {"key": "pressure_max", "label": "Max Pressure (bar)", "type": "float",
         "default": 250.0, "min": 1.0, "max": 1000.0},
        {"key": "rpm_max", "label": "Max Speed (RPM)", "type": "int",
         "default": 3000, "min": 100, "max": 10000},
    ],
    "valve_2_2": [
        {"key": "position", "label": "Default Position", "type": "combo",
         "default": "normally_closed",
         "options": ["normally_closed", "normally_open"]},
        {"key": "actuation", "label": "Actuation", "type": "combo",
         "default": "solenoid",
         "options": ["solenoid", "manual", "pilot", "spring"]},
    ],
    "valve_3_2": [
        {"key": "position", "label": "Default Position", "type": "combo",
         "default": "normally_closed",
         "options": ["normally_closed", "normally_open"]},
        {"key": "actuation", "label": "Actuation", "type": "combo",
         "default": "solenoid",
         "options": ["solenoid", "manual", "pilot", "spring"]},
    ],
    "valve_4_2": [
        {"key": "position", "label": "Spool Position", "type": "combo",
         "default": "center_closed",
         "options": ["center_closed", "center_open", "float"]},
        {"key": "actuation", "label": "Actuation", "type": "combo",
         "default": "solenoid",
         "options": ["solenoid", "manual", "pilot"]},
    ],
    "valve_4_3": [
        {"key": "position", "label": "Spool Position", "type": "combo",
         "default": "center_closed",
         "options": ["center_closed", "center_open", "float", "tandem"]},
        {"key": "actuation", "label": "Actuation", "type": "combo",
         "default": "solenoid",
         "options": ["solenoid", "manual", "pilot"]},
    ],
    "check_valve": [
        {"key": "cracking_pressure", "label": "Cracking Pressure (bar)",
         "type": "float", "default": 0.5, "min": 0.0, "max": 10.0},
    ],
    "relief_valve": [
        {"key": "set_pressure", "label": "Set Pressure (bar)", "type": "float",
         "default": 200.0, "min": 1.0, "max": 500.0},
        {"key": "flow_max", "label": "Max Flow (L/min)", "type": "float",
         "default": 50.0, "min": 1.0, "max": 500.0},
    ],
    "throttle": [
        {"key": "opening", "label": "Opening (%)", "type": "float",
         "default": 50.0, "min": 0.0, "max": 100.0},
        {"key": "flow_max", "label": "Max Flow (L/min)", "type": "float",
         "default": 30.0, "min": 0.1, "max": 500.0},
    ],
    "tank": [
        {"key": "volume", "label": "Volume (L)", "type": "float",
         "default": 50.0, "min": 0.5, "max": 10000.0},
        {"key": "fluid", "label": "Fluid", "type": "combo",
         "default": "hydraulic_oil",
         "options": ["hydraulic_oil", "water_glycol", "synthetic"]},
    ],
    "pressure_gauge": [
        {"key": "range_max", "label": "Range (bar)", "type": "float",
         "default": 400.0, "min": 1.0, "max": 1500.0},
        {"key": "unit", "label": "Unit", "type": "combo",
         "default": "bar", "options": ["bar", "psi", "MPa"]},
    ],
    "flow_meter": [
        {"key": "range_max", "label": "Range (L/min)", "type": "float",
         "default": 100.0, "min": 0.1, "max": 2000.0},
        {"key": "unit", "label": "Unit", "type": "combo",
         "default": "l/min", "options": ["l/min", "gpm", "m\u00b3/h"]},
    ],
    "filter": [
        {"key": "rating", "label": "Filtration (\u00b5m)", "type": "float",
         "default": 10.0, "min": 1.0, "max": 250.0},
        {"key": "type", "label": "Type", "type": "combo",
         "default": "return_line",
         "options": ["return_line", "pressure_line", "suction", "offline"]},
    ],
    "accumulator": [
        {"key": "volume", "label": "Volume (L)", "type": "float",
         "default": 1.0, "min": 0.1, "max": 500.0},
        {"key": "pre_charge", "label": "Pre-charge (bar)", "type": "float",
         "default": 100.0, "min": 1.0, "max": 400.0},
        {"key": "type", "label": "Type", "type": "combo",
         "default": "bladder",
         "options": ["bladder", "piston", "diaphragm"]},
    ],
    "compressor": [
        {"key": "flow_rate", "label": "Flow Rate (L/min)", "type": "float",
         "default": 500.0, "min": 1.0, "max": 5000.0},
        {"key": "pressure_max", "label": "Max Pressure (bar)", "type": "float",
         "default": 10.0, "min": 0.5, "max": 40.0},
        {"key": "type", "label": "Type", "type": "combo",
         "default": "rotary",
         "options": ["rotary", "reciprocating", "scroll", "screw"]},
    ],
    "air_supply": [
        {"key": "pressure", "label": "Pressure (bar)", "type": "float",
         "default": 6.0, "min": 0.1, "max": 20.0},
        {"key": "flow_rate", "label": "Flow Rate (L/min)", "type": "float",
         "default": 1000.0, "min": 1.0, "max": 50000.0},
    ],
    "regulator": [
        {"key": "inlet_pressure", "label": "Inlet Pressure (bar)", "type": "float",
         "default": 10.0, "min": 0.5, "max": 40.0},
        {"key": "outlet_pressure", "label": "Outlet Pressure (bar)", "type": "float",
         "default": 4.0, "min": 0.1, "max": 20.0},
    ],
    "lubricator": [
        {"key": "capacity", "label": "Capacity (L)", "type": "float",
         "default": 0.5, "min": 0.05, "max": 5.0},
    ],
    "silencer": [
        {"key": "insertion_loss", "label": "Insertion Loss (dB)", "type": "float",
         "default": 35.0, "min": 5.0, "max": 70.0},
    ],
    "quick_exhaust": [
        {"key": "bore", "label": "Port Bore (mm)", "type": "float",
         "default": 20.0, "min": 2.0, "max": 100.0},
    ],
}


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _draw_arrow(painter, x1, y1, x2, y2, size=6):
    """Draw an arrowhead at (x2, y2) pointing in the direction of the line."""
    angle = math.atan2(y2 - y1, x2 - x1)
    a1 = angle + math.pi * 0.8
    a2 = angle - math.pi * 0.8
    path = QPainterPath()
    path.moveTo(x2, y2)
    path.lineTo(x2 + size * math.cos(a1), y2 + size * math.sin(a1))
    path.lineTo(x2 + size * math.cos(a2), y2 + size * math.sin(a2))
    path.closeSubpath()
    painter.drawPath(path)


def _draw_dashed_line(painter, x1, y1, x2, y2):
    """Draw a dashed line."""
    old = painter.pen()
    pen = QPen(old.color(), old.widthF(), Qt.DashLine)
    painter.setPen(pen)
    painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    painter.setPen(old)


def _draw_spring(painter, cx, y1, y2, width=10):
    """Draw a zigzag spring symbol along a vertical line at cx."""
    h = y2 - y1
    coils = 6
    seg = h / (coils * 2)
    half = width / 2
    path = QPainterPath()
    path.moveTo(cx, y1)
    for i in range(coils * 2):
        yy = y1 + seg * (i + 1)
        x_off = half if i % 2 == 0 else -half
        path.lineTo(cx + x_off, yy)
    path.lineTo(cx, y2)
    painter.drawPath(path)


def _draw_solenoid(painter, cx, y1, y2, width=14):
    """Draw a solenoid coil symbol (rectangle with X) at cx between y1 and y2."""
    x1 = cx - width / 2
    h = y2 - y1
    painter.drawRect(int(x1), int(y1), int(width), int(h))
    painter.drawLine(int(x1), int(y1), int(x1 + width), int(y2))
    painter.drawLine(int(x1 + width), int(y1), int(x1), int(y2))


def _draw_dot(painter, cx, cy, r=3):
    """Draw a filled dot."""
    painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))


# ---------------------------------------------------------------------------
# Symbol Drawing Dispatch
# ---------------------------------------------------------------------------

def draw_symbol(painter, symbol_id, rect, color=None, active=False, sim_state=None):
    """Draw an ISO schematic symbol inside *rect*.

    Parameters
    ----------
    painter : QPainter
        Active painter, already begin()-ed on the target device.
    symbol_id : str
        Key from SYMBOL_CATALOG (e.g. ``"pump"``).
    rect : QRectF
        Target rectangle to draw within.
    color : QColor, optional
        Foreground colour. Defaults to black.
    active : bool
        If True the symbol is drawn highlighted.
    sim_state : dict, optional
        Simulation state for animated drawing (position, pressure, etc.)
    """
    if color is None:
        color = QColor(Qt.black)

    pen = QPen(color, 1.5)
    if active:
        pen = QPen(QColor("#0066ff"), 2.5)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    dispatch = {
        "pump": _draw_pump,
        "gear_pump": _draw_gear_pump,
        "pump_vane": _draw_pump_vane,
        "piston_pump": _draw_piston_pump,
        "variable_pump": _draw_variable_pump,
        "cylinder_single": _draw_cylinder_single,
        "cylinder_double": _draw_cylinder_double,
        "cylinder_telescopic": _draw_cylinder_telescopic,
        "motor": _draw_motor,
        "air_motor": _draw_motor,
        "motor_bi": _draw_motor_bi,
        "valve_2_2": _draw_valve_2_2,
        "valve_3_2": _draw_valve_3_2,
        "valve_4_2": _draw_valve_4_2,
        "valve_4_3": _draw_valve_4_3,
        "valve_5_2": _draw_valve_5_2,
        "valve_5_3": _draw_valve_5_3,
        "check_valve": _draw_check_valve,
        "pilot_check_valve": _draw_pilot_check_valve,
        "relief_valve": _draw_relief_valve,
        "pressure_reducer": _draw_pressure_reducer,
        "throttle": _draw_throttle,
        "needle_valve": _draw_needle_valve,
        "one_way_flow_control": _draw_one_way_flow_control,
        "flow_control": _draw_flow_control,
        "shuttle_valve": _draw_shuttle_valve,
        "two_pressure_valve": _draw_two_pressure_valve,
        "tank": _draw_tank,
        "pressure_gauge": _draw_pressure_gauge,
        "pressure_switch": _draw_pressure_switch,
        "temperature_gauge": _draw_temperature_gauge,
        "flow_meter": _draw_flow_meter,
        "filter": _draw_filter,
        "accumulator": _draw_accumulator,
        "heat_exchanger": _draw_heat_exchanger,
        "compressor": _draw_compressor,
        "air_supply": _draw_air_supply,
        "vacuum_generator": _draw_vacuum_generator,
        "regulator": _draw_regulator,
        "lubricator": _draw_lubricator,
        "silencer": _draw_silencer,
        "air_service_unit": _draw_air_service_unit,
        "quick_exhaust": _draw_quick_exhaust,
        "limit_switch": _draw_limit_switch,
        "proximity_sensor": _draw_proximity_sensor,
        # Electrical
        "battery": _draw_battery,
        "dc_supply": _draw_battery,
        "ac_mains": _draw_ac_mains,
        "ground": _draw_ground,
        "electric_motor": _draw_electric_motor,
        "solenoid": _draw_electric_solenoid,
        "lamp": _draw_lamp,
        "relay": _draw_relay,
        "relay_nc": _draw_relay_nc,
        "current_limiter": _draw_current_limiter,
        "switch_push": _draw_switch_push,
        "switch_push_nc": _draw_switch_push_nc,
        "switch_toggle": _draw_switch_toggle,
        "switch_limit": _draw_switch_limit,
        "switch_proximity": _draw_switch_proximity,
        "fuse": _draw_fuse,
        "buzzer": _draw_buzzer,
        # Digital & Control
        "and_gate": _draw_and_gate,
        "or_gate": _draw_or_gate,
        "not_gate": _draw_not_gate,
        "nand_gate": _draw_nand_gate,
        "nor_gate": _draw_nor_gate,
        "xor_gate": _draw_xor_gate,
        "timer": _draw_timer,
        "d_flip_flop": _draw_d_flip_flop,
        "counter": _draw_counter,
        "pulse_generator": _draw_pulse_generator,
        "plc": _draw_plc,
        "comparator": _draw_comparator,
        "pid_controller": _draw_pid_controller,
        # New components
        "internally_gear_pump": _draw_internally_gear_pump,
        "hydraulic_power_unit": _draw_hydraulic_power_unit,
        "reservoir_elevated": _draw_reservoir_elevated,
        "plunger_cylinder": _draw_plunger_cylinder,
        "cylinder_cushioned": _draw_cylinder_cushioned,
        "check_valve_delockable": _draw_check_valve_delockable,
        "check_valve_double_delockable": _draw_check_valve_double_delockable,
        "sequence_valve": _draw_sequence_valve,
        "needle_restrictor": _draw_needle_restrictor,
        "gap_restrictor": _draw_gap_restrictor,
        "piston_gauge": _draw_piston_gauge,
        "bourdon_gauge": _draw_bourdon_gauge,
        "water_cooler": _draw_water_cooler,
        "air_cooler": _draw_air_cooler,
        "heating_element": _draw_heating_element,
        "valve_3_2_unloaded": _draw_valve_3_2_unloaded,
        "speaker": _draw_speaker,
        "relay_timer": _draw_relay_timer,
        "diode": _draw_diode,
        "transistor": _draw_transistor,
        "op_amp": _draw_op_amp,
        "jk_flip_flop": _draw_jk_flip_flop,
        "sr_latch": _draw_sr_latch,
        "shift_register": _draw_shift_register,
        "display_7seg": _draw_display_7seg,
    }

    fn = dispatch.get(symbol_id)
    if fn:
        painter.save()
        fn(painter, rect, sim_state=sim_state)
        painter.restore()


# ---------------------------------------------------------------------------
# Individual symbol painters
# ---------------------------------------------------------------------------

def _draw_pump(painter, r, sim_state=None):
    """ISO pump: square with filled triangle indicating flow direction."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.5
    
    # Animate if running
    running = sim_state and sim_state.get("on", True)
    if not running:
        painter.setPen(QPen(QColor(128, 128, 128), 1.5))
    
    painter.drawRect(int(cx - s / 2), int(cy - s / 2), int(s), int(s))
    # filled triangle (flow arrow)
    tri = QPainterPath()
    half = s * 0.3
    tri.moveTo(cx - half, cy - half * 0.8)
    tri.lineTo(cx + half, cy)
    tri.lineTo(cx - half, cy + half * 0.8)
    tri.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)


def _draw_pump_vane(painter, r, sim_state=None):
    """ISO vane pump: circle with inner vane lines."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.35
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    # inner circle for rotor
    inner = rad * 0.4
    painter.drawEllipse(int(cx - inner), int(cy - inner), int(inner * 2), int(inner * 2))
    # vane lines
    for ang in [0, math.pi / 3, -math.pi / 3]:
        x1 = cx + inner * math.cos(ang)
        y1 = cy + inner * math.sin(ang)
        x2 = cx + rad * 0.95 * math.cos(ang)
        y2 = cy + rad * 0.95 * math.sin(ang)
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    # flow direction triangle
    _draw_pump(painter, QRectF(r.left(), cy - rad * 0.4, r.width() * 0.3, rad * 0.8))


def _draw_piston_pump(painter, r, sim_state=None):
    """ISO piston pump: circle with diagonal line through it."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.35
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    # diagonal line indicating variable displacement
    painter.drawLine(
        int(cx - rad * 0.7), int(cy + rad * 0.7),
        int(cx + rad * 0.7), int(cy - rad * 0.7),
    )
    # arrow head on the diagonal
    _draw_arrow(painter, cx - rad * 0.7, cy + rad * 0.7,
                cx + rad * 0.7, cy - rad * 0.7, size=int(rad * 0.2))


def _draw_cylinder_single(painter, r, sim_state=None):
    """ISO single-acting cylinder: rectangle body with one port."""
    w = r.width() * 0.5
    h = r.height() * 0.7
    x = r.center().x() - w / 2
    y = r.top() + r.height() * 0.1
    
    # Draw cylinder body
    painter.drawRect(int(x), int(y), int(w), int(h))
    
    # Animate piston position if simulation state is available
    if sim_state and "position" in sim_state:
        pos = sim_state["position"]  # 0.0 to 1.0
        py = y + h * (0.5 + 0.4 * pos)  # Move piston line based on position
    else:
        py = y + h * 0.5  # Default center position
    
    # piston line
    painter.drawLine(int(x), int(py), int(x + w), int(py))
    
    # port line at bottom
    painter.drawLine(int(r.center().x()), int(y + h),
                     int(r.center().x()), int(y + h + r.height() * 0.15))


def _draw_cylinder_double(painter, r, sim_state=None):
    """ISO double-acting cylinder: rectangle body with two ports."""
    w = r.width() * 0.5
    h = r.height() * 0.65
    x = r.center().x() - w / 2
    y = r.top() + r.height() * 0.1
    
    # Draw cylinder body
    painter.drawRect(int(x), int(y), int(w), int(h))
    
    # Animate piston position if simulation state is available
    if sim_state and "position" in sim_state:
        pos = sim_state["position"]  # 0.0 to 1.0
        py = y + h * (0.1 + 0.8 * pos)  # Move piston line based on position
    else:
        py = y + h * 0.5  # Default center position
    
    # piston line
    painter.drawLine(int(x), int(py), int(x + w), int(py))
    # piston rod (thin rectangle extending to the right)
    rod_w = w * 0.4
    rod_h = h * 0.15
    painter.drawRect(int(x + w), int(py - rod_h / 2), int(rod_w), int(rod_h))
    
    # two port lines
    painter.drawLine(int(x), int(y + h * 0.25),
                     int(x - r.width() * 0.15), int(y + h * 0.25))
    painter.drawLine(int(x), int(y + h * 0.75),
                     int(x - r.width() * 0.15), int(y + h * 0.75))


def _draw_motor(painter, r, sim_state=None):
    """ISO hydraulic motor: circle with two filled triangles."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.35
    
    # Animate rotation if motor is running
    running = sim_state and sim_state.get("running", True)
    if not running:
        painter.setPen(QPen(QColor(128, 128, 128), 1.5))
    
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    
    # two filled triangles pointing outward (motor output)
    painter.setBrush(QBrush(painter.pen().color()))
    for direction in [1, -1]:
        tri = QPainterPath()
        tip_x = cx + direction * rad * 0.5
        tri.moveTo(tip_x, cy - rad * 0.25)
        tri.lineTo(tip_x + direction * rad * 0.35, cy)
        tri.lineTo(tip_x, cy + rad * 0.25)
        tri.closeSubpath()
        painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)


def _draw_directional_valve(painter, r, ports_in, ports_out, sim_state=None):
    """Draw a directional control valve box with port labels.

    ports_in: list of label strings for top ports (P, T, A, B etc.)
    ports_out: list of label strings for bottom ports.
    sim_state: dict, optional
        Simulation state for animated drawing (position, etc.)
    """
    w = r.width() * 0.55
    h = r.height() * 0.35
    x = r.center().x() - w / 2
    y = r.center().y() - h / 2

    # valve box
    painter.drawRect(int(x), int(y), int(w), int(h))

    # draw port lines going outward
    n_in = len(ports_in)
    n_out = len(ports_out)
    if n_in > 0:
        spacing_in = w / (n_in + 1)
        for i, label in enumerate(ports_in):
            px = x + spacing_in * (i + 1)
            painter.drawLine(int(px), int(y), int(px), int(y - r.height() * 0.15))
    if n_out > 0:
        spacing_out = w / (n_out + 1)
        for i, label in enumerate(ports_out):
            px = x + spacing_out * (i + 1)
            painter.drawLine(int(px), int(y + h), int(px), int(y + h + r.height() * 0.15))

    # actuation symbol on left (small rectangle) - highlight if actuated
    act_w = w * 0.12
    actuated = sim_state and sim_state.get("actuated", False)
    position = sim_state and sim_state.get("position", 0)
    
    if actuated:
        painter.setPen(QPen(QColor(0, 180, 0), 2))
        painter.setBrush(QBrush(QColor(200, 255, 200)))
    else:
        painter.setPen(QPen(painter.pen().color(), 1.5))
        painter.setBrush(Qt.NoBrush)
    
    painter.drawRect(int(x - act_w - 2), int(y + h * 0.2),
                     int(act_w), int(h * 0.6))
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(painter.pen().color(), 1.5))

    # return spring on right
    _draw_spring(painter, x + w + 8, y + h * 0.15, y + h * 0.85, width=w * 0.1)
    
    # Show position indicator (small rectangle inside valve box)
    if position is not None:
        pos_x = x + w * 0.2 + (w * 0.6) * position
        painter.setBrush(QBrush(QColor(200, 100, 100)))
        painter.drawRect(int(pos_x - 3), int(y + h * 0.4), 6, int(h * 0.2))
        painter.setBrush(Qt.NoBrush)


def _draw_valve_2_2(painter, r, sim_state=None):
    """2/2 directional valve: 2 ports, 2 positions."""
    # Animate valve position
    position = sim_state and sim_state.get("position", 0)
    
    _draw_directional_valve(painter, r, ["P"], ["A"], sim_state=sim_state)
    # draw internal arrow in box
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.55
    bh = r.height() * 0.35
    bx = cx - bw / 2
    by = cy - bh / 2
    
    # Animate arrow based on valve position
    if position:
        # Arrow points differently based on position
        _draw_arrow(painter, bx + bw * 0.3, by + bh * 0.5,
                    bx + bw * 0.7, by + bh * 0.5, size=int(bh * 0.15))
    else:
        _draw_arrow(painter, bx + bw * 0.5, by + bh * 0.7,
                    bx + bw * 0.5, by + bh * 0.3, size=int(bh * 0.15))


def _draw_valve_3_2(painter, r, sim_state=None):
    """3/2 directional valve: 3 ports, 2 positions."""
    _draw_directional_valve(painter, r, ["P"], ["A", "T"], sim_state=sim_state)
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.55
    bh = r.height() * 0.35
    bx = cx - bw / 2
    by = cy - bh / 2
    _draw_arrow(painter, bx + bw * 0.5, by + bh * 0.7,
                bx + bw * 0.5, by + bh * 0.3, size=int(bh * 0.15))


def _draw_valve_4_2(painter, r, sim_state=None):
    """4/2 directional valve: 4 ports, 2 positions."""
    _draw_directional_valve(painter, r, ["P", "T"], ["A", "B"], sim_state=sim_state)
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.55
    bh = r.height() * 0.35
    bx = cx - bw / 2
    by = cy - bh / 2
    # parallel arrows in center
    for offset in [-bw * 0.15, bw * 0.15]:
        _draw_arrow(painter, bx + bw / 2 + offset, by + bh * 0.75,
                    bx + bw / 2 + offset, by + bh * 0.25, size=int(bh * 0.12))


def _draw_valve_4_3(painter, r, sim_state=None):
    """4/3 directional valve: 4 ports, 3 positions."""
    _draw_directional_valve(painter, r, ["P", "T"], ["A", "B"], sim_state=sim_state)
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.55
    bh = r.height() * 0.35
    bx = cx - bw / 2
    by = cy - bh / 2
    # divider line for 3rd position
    third = bw / 3
    painter.drawLine(int(bx + third), int(by), int(bx + third), int(by + bh))
    # arrows in left section (parallel)
    for offset in [-bw * 0.08, bw * 0.08]:
        _draw_arrow(painter, bx + third / 2 + offset, by + bh * 0.75,
                    bx + third / 2 + offset, by + bh * 0.25, size=int(bh * 0.1))
    # crossed arrows in right section
    mid_r = bx + third + third / 2
    _draw_arrow(painter, mid_r - third * 0.2, by + bh * 0.75,
                mid_r + third * 0.2, by + bh * 0.25, size=int(bh * 0.1))
    _draw_arrow(painter, mid_r + third * 0.2, by + bh * 0.75,
                mid_r - third * 0.2, by + bh * 0.25, size=int(bh * 0.1))


def _draw_check_valve(painter, r, sim_state=None):
    """ISO check valve: triangle pointing to ball stop."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    # triangle (flow allowed direction)
    tri = QPainterPath()
    tri.moveTo(cx - s, cy - s)
    tri.lineTo(cx + s, cy)
    tri.lineTo(cx - s, cy + s)
    tri.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)
    # ball / stop line
    painter.drawLine(int(cx + s), int(cy - s), int(cx + s), int(cy + s))
    # port lines
    painter.drawLine(int(cx - s - r.width() * 0.15), int(cy),
                     int(cx - s), int(cy))
    painter.drawLine(int(cx + s), int(cy),
                     int(cx + s + r.width() * 0.15), int(cy))


def _draw_relief_valve(painter, r, sim_state=None):
    """ISO relief valve: box with arrow and spring."""
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.35
    bh = r.height() * 0.35
    bx = cx - bw / 2
    by = cy - bh / 2
    painter.drawRect(int(bx), int(by), int(bw), int(bh))
    # arrow inside
    _draw_arrow(painter, bx + bw * 0.5, by + bh * 0.8,
                bx + bw * 0.5, by + bh * 0.2, size=int(bh * 0.15))
    # spring on right
    _draw_spring(painter, bx + bw + 8, by + bh * 0.1, by + bh * 0.9, width=bw * 0.15)
    # pilot line (dashed) from bottom to side
    _draw_dashed_line(painter, bx, by + bh, bx - r.width() * 0.12, by + bh)
    _draw_dashed_line(painter, bx - r.width() * 0.12, by + bh,
                      bx - r.width() * 0.12, cy - bh * 0.5)
    # port lines
    painter.drawLine(int(bx), int(by + bh), int(bx), int(by + bh + r.height() * 0.1))
    painter.drawLine(int(bx + bw), int(by + bh),
                     int(bx + bw), int(by + bh + r.height() * 0.1))


def _draw_throttle(painter, r, sim_state=None):
    """ISO throttle / restrictor: two arcs forming an orifice."""
    cx, cy = r.center().x(), r.center().y()
    arc_r = min(r.width(), r.height()) * 0.25
    # top arc
    path = QPainterPath()
    path.arcTo(cx - arc_r, cy - arc_r * 0.8, arc_r * 2, arc_r * 1.6, 0, 180)
    painter.drawPath(path)
    # bottom arc (mirrored)
    path2 = QPainterPath()
    path2.arcTo(cx - arc_r, cy - arc_r * 0.8, arc_r * 2, arc_r * 1.6, 0, -180)
    painter.drawPath(path2)
    # port lines
    painter.drawLine(int(cx - arc_r - r.width() * 0.15), int(cy),
                     int(cx - arc_r), int(cy))
    painter.drawLine(int(cx + arc_r), int(cy),
                     int(cx + arc_r + r.width() * 0.15), int(cy))


def _draw_tank(painter, r, sim_state=None):
    """ISO tank / reservoir: open-top rectangle (triangle pointing down)."""
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.55
    h = r.height() * 0.45
    x = cx - w / 2
    y = cy - h / 3
    # tank body (rectangle)
    painter.drawRect(int(x), int(y), int(w), int(h))
    
    # fluid level line inside - ANIMATED based on simulation state
    if sim_state and "level" in sim_state:
        fluid_y = y + h * (1.0 - sim_state["level"])
    else:
        fluid_y = y + h * 0.6
    
    # Draw fluid as filled rectangle
    painter.setBrush(QBrush(QColor(100, 180, 255)))
    painter.drawRect(int(x + 2), int(y + 2), int(w - 4), int(fluid_y - y - 2))
    painter.setBrush(Qt.NoBrush)
    
    # fluid level line
    painter.drawLine(int(x + w * 0.1), int(fluid_y), int(x + w * 0.9), int(fluid_y))
    # return line from top center
    painter.drawLine(int(cx), int(y), int(cx), int(y - r.height() * 0.12))
    # suction line from top
    painter.drawLine(int(cx), int(y), int(cx), int(y - r.height() * 0.12))


def _draw_pressure_gauge(painter, r, sim_state=None):
    """ISO pressure gauge: circle with arrow and \"P\" label."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.35
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    # needle arrow - ANIMATED based on pressure reading
    if sim_state and "reading" in sim_state:
        # Normalize reading to 0-1 range, cap at max
        reading = min(1.0, max(0.0, sim_state["reading"] / 1e7))
        # Rotate needle: 0 reading = 135 deg (left), 1 reading = 45 deg (right)
        angle = 135 - reading * 90
        rad_angle = math.radians(angle)
        # Calculate needle tip position
        needle_len = rad * 0.65
        tip_x = cx + needle_len * math.cos(rad_angle)
        tip_y = cy + needle_len * math.sin(rad_angle)
        _draw_arrow(painter, cx, cy, tip_x, tip_y, size=int(rad * 0.15))
    else:
        # Default position
        _draw_arrow(painter, cx, cy, cx + rad * 0.65, cy - rad * 0.5, size=int(rad * 0.15))
    _draw_arrow(painter, cx, cy, cx + rad * 0.65, cy - rad * 0.5, size=int(rad * 0.15))
    # small label "P"
    font = painter.font()
    font.setPixelSize(int(rad * 0.7))
    painter.setFont(font)
    painter.drawText(int(cx - rad * 0.2), int(cy + rad * 0.6), "P")
    # port line from bottom
    painter.drawLine(int(cx), int(cy + rad), int(cx), int(cy + rad + r.height() * 0.08))


def _draw_flow_meter(painter, r, sim_state=None):
    """ISO flow meter: circle with \"F\" and arrow."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.35
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    # arrow
    _draw_arrow(painter, cx - rad * 0.4, cy + rad * 0.1,
                cx + rad * 0.4, cy + rad * 0.1, size=int(rad * 0.15))
    # label
    font = painter.font()
    font.setPixelSize(int(rad * 0.7))
    painter.setFont(font)
    painter.drawText(int(cx - rad * 0.2), int(cy - rad * 0.1), "F")


def _draw_filter(painter, r, sim_state=None):
    """ISO filter: diamond shape."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.35
    diamond = QPainterPath()
    diamond.moveTo(cx, cy - s)
    diamond.lineTo(cx + s, cy)
    diamond.lineTo(cx, cy + s)
    diamond.lineTo(cx - s, cy)
    diamond.closeSubpath()
    painter.drawPath(diamond)
    # port lines
    painter.drawLine(int(cx), int(cy - s - r.height() * 0.08), int(cx), int(cy - s))
    painter.drawLine(int(cx), int(cy + s), int(cx), int(cy + s + r.height() * 0.08))
    # dashed drain line from bottom-right
    _draw_dashed_line(painter, cx + s * 0.7, cy + s * 0.7,
                      cx + s * 0.7 + r.width() * 0.1, cy + s * 0.7)


def _draw_accumulator(painter, r, sim_state=None):
    """ISO accumulator: capsule / elongated oval with gas charge."""
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.35
    h = r.height() * 0.55
    # capsule body
    path = QPainterPath()
    path.moveTo(cx - w, cy - h * 0.5)
    path.arcTo(cx - w, cy - h, w * 2, h, 180, 180)
    path.lineTo(cx + w, cy + h * 0.5)
    path.arcTo(cx - w, cy - h * 0, w * 2, h, 0, 180)
    path.closeSubpath()
    painter.drawPath(path)
    # separator line (gas/fluid)
    painter.drawLine(int(cx - w * 0.8), int(cy), int(cx + w * 0.8), int(cy))
    # gas label
    font = painter.font()
    font.setPixelSize(int(w * 0.45))
    painter.setFont(font)
    painter.drawText(int(cx - w * 0.3), int(cy - h * 0.2), "N")
    # port line
    painter.drawLine(int(cx), int(cy + h * 0.5), int(cx), int(cy + h * 0.5 + r.height() * 0.06))


def _draw_compressor(painter, r, sim_state=None):
    """ISO compressor: same as pump but with air context."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.35
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    # filled triangle indicating compression
    painter.setBrush(QBrush(painter.pen().color()))
    tri = QPainterPath()
    tri.moveTo(cx - rad * 0.3, cy - rad * 0.4)
    tri.lineTo(cx + rad * 0.3, cy)
    tri.lineTo(cx - rad * 0.3, cy + rad * 0.4)
    tri.closeSubpath()
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)


def _draw_air_supply(painter, r, sim_state=None):
    """ISO air supply: triangle pointing down (diamond with line)."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    # diamond
    diamond = QPainterPath()
    diamond.moveTo(cx, cy - s)
    diamond.lineTo(cx + s, cy)
    diamond.lineTo(cx, cy + s)
    diamond.lineTo(cx - s, cy)
    diamond.closeSubpath()
    painter.drawPath(diamond)
    # horizontal line through center
    painter.drawLine(int(cx - s * 0.6), int(cy), int(cx + s * 0.6), int(cy))


def _draw_regulator(painter, r, sim_state=None):
    """ISO pressure regulator: circle with diagonal arrow and line through it."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.35
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    # diagonal arrow
    _draw_arrow(painter, cx + rad * 0.4, cy + rad * 0.4,
                cx - rad * 0.4, cy - rad * 0.4, size=int(rad * 0.15))
    # line through
    painter.drawLine(int(cx - rad * 0.5), int(cy + rad * 0.5),
                     int(cx + rad * 0.5), int(cy - rad * 0.5))


def _draw_lubricator(painter, r, sim_state=None):
    """ISO lubricator: vertical line with drip symbol."""
    cx, cy = r.center().x(), r.center().y()
    # vertical body
    h = r.height() * 0.45
    painter.drawLine(int(cx), int(cy - h / 2), int(cx), int(cy + h / 2))
    # drip / drop shape
    drop_r = h * 0.12
    path = QPainterPath()
    path.moveTo(cx, cy - drop_r)
    path.arcTo(cx - drop_r, cy, drop_r * 2, drop_r * 2, 0, 180)
    path.arcTo(cx - drop_r, cy, drop_r * 2, drop_r * 2, 180, 180)
    path.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(path)
    painter.setBrush(Qt.NoBrush)


def _draw_silencer(painter, r, sim_state=None):
    """ISO silencer / muffler: triangle inside a rectangle."""
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.35
    h = r.height() * 0.35
    bx = cx - w / 2
    by = cy - h / 2
    painter.drawRect(int(bx), int(by), int(w), int(h))
    # triangle
    tri = QPainterPath()
    tri.moveTo(bx + w * 0.2, by + h * 0.8)
    tri.lineTo(bx + w * 0.8, by + h * 0.8)
    tri.lineTo(bx + w * 0.5, by + h * 0.2)
    tri.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)


def _draw_quick_exhaust(painter, r, sim_state=None):
    """ISO quick exhaust valve: diamond with arrow."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    diamond = QPainterPath()
    diamond.moveTo(cx, cy - s)
    diamond.lineTo(cx + s, cy)
    diamond.lineTo(cx, cy + s)
    diamond.lineTo(cx - s, cy)
    diamond.closeSubpath()
    painter.drawPath(diamond)
    # arrow through diamond
    _draw_arrow(painter, cx - s * 0.4, cy + s * 0.3,
                cx + s * 0.4, cy - s * 0.3, size=int(s * 0.2))
    # exhaust port line to the right
    painter.drawLine(int(cx + s), int(cy), int(cx + s + r.width() * 0.12), int(cy))


# ---------------------------------------------------------------------------
# Additional symbol painters (expanded catalog)
# ---------------------------------------------------------------------------

def _draw_gear_pump(painter, r, sim_state=None):
    """ISO gear pump: circle with two meshing gears."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.32
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    g = rad * 0.3
    painter.drawEllipse(int(cx - g * 0.9), int(cy - g * 0.6), int(g * 2), int(g * 2))
    painter.drawEllipse(int(cx + g * 0.2), int(cy + g * 0.6), int(g * 2), int(g * 2))
    _draw_arrow(painter, cx - rad * 0.7, cy + rad * 0.5, cx + rad * 0.7, cy - rad * 0.5, size=int(rad * 0.2))


def _draw_variable_pump(painter, r, sim_state=None):
    """ISO variable displacement pump: circle with diagonal arrow."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.35
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    painter.drawLine(
        int(cx - rad * 0.7), int(cy + rad * 0.7),
        int(cx + rad * 0.7), int(cy - rad * 0.7),
    )
    _draw_arrow(painter, cx - rad * 0.7, cy + rad * 0.7,
                cx + rad * 0.7, cy - rad * 0.7, size=int(rad * 0.2))
    painter.setBrush(QBrush(painter.pen().color()))
    tri = QPainterPath()
    half = rad * 0.3
    tri.moveTo(cx - half, cy - half * 0.8)
    tri.lineTo(cx + half, cy)
    tri.lineTo(cx - half, cy + half * 0.8)
    tri.closeSubpath()
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)


def _draw_cylinder_telescopic(painter, r, sim_state=None):
    """ISO telescopic cylinder: stacked rectangles with two ports."""
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.4
    h = r.height() * 0.6
    y = r.top() + r.height() * 0.12
    painter.drawRect(int(cx - w / 2), int(y), int(w), int(h))
    painter.drawRect(int(cx - w / 2), int(y + h * 0.25), int(w * 0.7), int(h * 0.5))
    py = y + h * 0.5
    painter.drawLine(int(cx - w / 2), int(py), int(cx - w / 2 + w * 0.7), int(py))
    painter.drawLine(int(cx), int(y + h), int(cx), int(y + h + r.height() * 0.1))
    painter.drawLine(int(cx - w / 2), int(y + h * 0.75),
                     int(cx - w / 2 - r.width() * 0.12), int(y + h * 0.75))


def _draw_motor_bi(painter, r, sim_state=None):
    """ISO reversible motor: circle with double arrows."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.35
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    painter.setBrush(QBrush(painter.pen().color()))
    for direction in [1, -1]:
        tri = QPainterPath()
        tip_x = cx + direction * rad * 0.5
        tri.moveTo(tip_x, cy - rad * 0.25)
        tri.lineTo(tip_x + direction * rad * 0.35, cy)
        tri.lineTo(tip_x, cy + rad * 0.25)
        tri.closeSubpath()
        painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)
    _draw_arrow(painter, cx - rad * 0.2, cy + rad * 0.5, cx + rad * 0.2, cy - rad * 0.5, size=int(rad * 0.16))
    _draw_arrow(painter, cx + rad * 0.2, cy - rad * 0.5, cx - rad * 0.2, cy + rad * 0.5, size=int(rad * 0.16))


def _draw_valve_5_2(painter, r, sim_state=None):
    _draw_directional_valve(painter, r, ["P", "A", "B"], ["T", "R"], sim_state=sim_state)
    cx, cy = r.center().x(), r.center().y()
    r_len = r.width() * 0.20
    cy2 = cy + r.height() * 0.30
    _draw_arrow(painter, cx - r_len, cy2, cx + r_len, cy2, size=int(r.height() * 0.05))
    _draw_arrow(painter, cx - r_len, cy - r.height() * 0.30, cx + r_len, cy - r.height() * 0.30, size=int(r.height() * 0.05))


def _draw_valve_5_3(painter, r, sim_state=None):
    _draw_directional_valve(painter, r, ["P", "A", "B"], ["T", "R"], sim_state=sim_state)
    cx, cy = r.center().x(), r.center().y()
    r_len = r.width() * 0.20
    _draw_arrow(painter, cx - r_len, cy + r.height() * 0.30, cx + r_len, cy + r.height() * 0.30, size=int(r.height() * 0.05))


def _draw_pilot_check_valve(painter, r, sim_state=None):
    """ISO pilot-operated check valve: check valve with dashed pilot line."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.28
    tri = QPainterPath()
    tri.moveTo(cx - s, cy - s)
    tri.lineTo(cx + s, cy)
    tri.lineTo(cx - s, cy + s)
    tri.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)
    painter.drawLine(int(cx + s), int(cy - s), int(cx + s), int(cy + s))
    _draw_dashed_line(painter, cx - s, cy + s, cx - s - r.width() * 0.15, cy + s)
    painter.drawLine(int(cx - s - r.width() * 0.15), int(cy), int(cx - s), int(cy))
    painter.drawLine(int(cx + s), int(cy), int(cx + s + r.width() * 0.15), int(cy))


def _draw_pressure_reducer(painter, r, sim_state=None):
    """ISO pressure reducing valve: box with arrow and pilot line."""
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.35
    bh = r.height() * 0.35
    bx = cx - bw / 2
    by = cy - bh / 2
    painter.drawRect(int(bx), int(by), int(bw), int(bh))
    _draw_arrow(painter, bx + bw * 0.8, by + bh * 0.8, bx + bw * 0.2, by + bh * 0.2, size=int(bh * 0.12))
    _draw_dashed_line(painter, bx + bw, by + bh, bx + bw + r.width() * 0.12, by + bh)
    _draw_dashed_line(painter, bx + bw + r.width() * 0.12, by + bh, bx + bw + r.width() * 0.12, cy)
    _draw_spring(painter, bw * 0.5 + bx, by - r.height() * 0.12, by, width=bw * 0.12)
    painter.drawLine(int(bx), int(by + bh), int(bx), int(by + bh + r.height() * 0.1))
    painter.drawLine(int(bx + bw), int(by + bh), int(bx + bw), int(by + bh + r.height() * 0.1))


def _draw_needle_valve(painter, r, sim_state=None):
    """ISO needle valve: throttle plus adjustable needle."""
    _draw_throttle(painter, r)
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    painter.drawLine(int(cx), int(cy - s),
                     int(cx - s * 1.2), int(cy + s * 1.2))


def _draw_one_way_flow_control(painter, r, sim_state=None):
    """ISO one-way flow control: throttle in parallel with check valve."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.2
    tri = QPainterPath()
    tri.moveTo(cx - s, cy - s)
    tri.lineTo(cx + s * 0.5, cy)
    tri.lineTo(cx - s, cy + s)
    tri.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)
    painter.drawLine(int(cx + s * 0.5), int(cy - s), int(cx + s * 0.5), int(cy + s))
    arc_r = min(r.width(), r.height()) * 0.28
    path = QPainterPath()
    path.arcTo(cx + s * 0.2, cy - arc_r * 0.8, arc_r * 2, arc_r * 1.6, 0, 180)
    painter.drawPath(path)
    painter.drawLine(int(cx - r.width() * 0.18), int(cy), int(cx - s), int(cy))
    painter.drawLine(int(cx + s * 0.5), int(cy), int(cx + r.width() * 0.18), int(cy))


def _draw_flow_control(painter, r, sim_state=None):
    """ISO flow control valve: box with arrow and spring."""
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.35
    bh = r.height() * 0.4
    bx = cx - bw / 2
    by = cy - bh / 2
    painter.drawRect(int(bx), int(by), int(bw), int(bh))
    _draw_arrow(painter, bx + bw * 0.8, by + bh * 0.85, bx + bw * 0.2, by + bh * 0.15, size=int(bh * 0.15))
    _draw_spring(painter, bx + bw + 8, by + bh * 0.1, by + bh * 0.9, width=bw * 0.1)
    painter.drawLine(int(bx), int(cy), int(bx - r.width() * 0.12), int(cy))
    painter.drawLine(int(bx + bw), int(cy), int(bx + bw + r.width() * 0.12), int(cy))


def _draw_shuttle_valve(painter, r, sim_state=None):
    """ISO shuttle valve (OR): one outlet, two inlets."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.28
    painter.setBrush(QBrush(painter.pen().color()))
    tri = QPainterPath()
    tri.moveTo(cx, cy - s)
    tri.lineTo(cx - s * 0.8, cy)
    tri.lineTo(cx, cy + s)
    tri.closeSubpath()
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)
    painter.drawLine(int(cx + s * 0.8), int(cy), int(cx + s * 0.8 + r.width() * 0.12), int(cy))
    painter.drawLine(int(cx - s * 0.8 - r.width() * 0.12), int(cy), int(cx - s * 0.8), int(cy))


def _draw_two_pressure_valve(painter, r, sim_state=None):
    """ISO two-pressure (AND) valve: two inlets both needed."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.25
    painter.setBrush(QBrush(painter.pen().color()))
    tri = QPainterPath()
    tri.moveTo(cx - s, cy + s)
    tri.lineTo(cx, cy)
    tri.lineTo(cx + s, cy + s)
    tri.closeSubpath()
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)
    painter.drawLine(int(cx), int(cy - s), int(cx), int(cy - s - r.height() * 0.1))
    painter.drawLine(int(cx - s - r.width() * 0.1), int(cy + s), int(cx - s), int(cy + s))
    painter.drawLine(int(cx + s), int(cy + s), int(cx + s + r.width() * 0.1), int(cy + s))


def _draw_pressure_switch(painter, r, sim_state=None):
    """ISO pressure switch: box with set-pressure lever."""
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.4
    bh = r.height() * 0.3
    bx = cx - bw / 2
    by = cy - bh / 2
    painter.drawRect(int(bx), int(by), int(bw), int(bh))
    painter.drawLine(int(bx + bw * 0.2), int(by + bh * 0.7),
                     int(bx + bw * 0.7), int(by + bh * 0.3))
    _draw_arrow(painter, bx + bw * 0.2, by + bh * 0.7,
                bx + bw * 0.7, by + bh * 0.3, size=int(bh * 0.15))
    _draw_spring(painter, bx + bw, by + bh * 0.2, by + bh * 0.8, width=bw * 0.08)
    painter.drawLine(int(cx), int(by + bh), int(cx), int(by + bh + r.height() * 0.1))


def _draw_temperature_gauge(painter, r, sim_state=None):
    """ISO temperature gauge: circle with thermometer."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.32
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    painter.drawEllipse(int(cx - rad * 0.15), int(cy), int(rad * 0.4), int(rad * 0.4))
    painter.drawLine(int(cx), int(cy + rad * 0.4), int(cx), int(cy + rad * 0.9))
    painter.drawLine(int(cx - rad * 0.5), int(cy - rad * 0.5),
                     int(cx + rad * 0.5), int(cy - rad * 0.5))
    painter.drawLine(int(cx), int(cy + rad), int(cx), int(cy + rad + r.height() * 0.1))


def _draw_heat_exchanger(painter, r, sim_state=None):
    """ISO heat exchanger: rectangle with cooling diagonals."""
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.4
    bh = r.height() * 0.4
    bx = cx - bw / 2
    by = cy - bh / 2
    painter.drawRect(int(bx), int(by), int(bw), int(bh))
    for i in range(3):
        yy = by + bh * 0.3 + i * bh * 0.2
        painter.drawLine(int(bx + bh * 0.3), int(yy), int(bx + bw), int(yy - bh * 0.3))
    painter.drawLine(int(bx), int(cy), int(bx - r.width() * 0.12), int(cy))
    painter.drawLine(int(bx + bw), int(cy), int(bx + bw + r.width() * 0.12), int(cy))


def _draw_vacuum_generator(painter, r, sim_state=None):
    """ISO vacuum generator (ejector)."""
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.25
    bh = r.height() * 0.4
    bx = cx - bw / 2
    by = cy - bh / 2
    painter.drawRect(int(bx), int(by), int(bw), int(bh))
    painter.drawLine(int(cx), int(by - r.height() * 0.12), int(cx), int(by))
    painter.drawLine(int(cx), int(by + bh), int(cx), int(by + bh + r.height() * 0.12))
    painter.drawLine(int(bx + bw), int(cy), int(bx + bw + r.width() * 0.14), int(cy))
    _draw_arrow(painter, cx - bw * 0.2, cy + bh * 0.2, cx + bw * 0.4, cy - bh * 0.2, size=int(bh * 0.1))


def _draw_air_service_unit(painter, r, sim_state=None):
    """ISO air service unit (FRL): filter + regulator + lubricator in series."""
    w = r.width() * 0.5
    h = r.height() * 0.4
    x = r.center().x() - w / 2
    y = r.center().y() - h / 2
    seg = w / 3
    painter.drawRect(int(x), int(y), int(w), int(h))
    painter.drawLine(int(x + seg), int(y), int(x + seg), int(y + h))
    painter.drawLine(int(x + seg * 2), int(y), int(x + seg * 2), int(y + h))
    painter.drawRect(int(x + seg * 0.2), int(y + h * 0.4), int(seg * 0.6), int(h * 0.4))
    painter.drawRect(int(x + seg * 1.3), int(y + h * 0.1), int(seg * 0.5), int(h * 0.2))
    painter.drawRect(int(x + seg * 2.2), int(y + h * 0.4), int(seg * 0.6), int(h * 0.4))
    cy = r.center().y()
    painter.drawLine(int(x), int(cy), int(x - r.width() * 0.1), int(cy))
    painter.drawLine(int(x + w), int(cy), int(x + w + r.width() * 0.1), int(cy))


def _draw_limit_switch(painter, r, sim_state=None):
    """ISO limit switch: circle with roller lever."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.3
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    painter.drawLine(int(cx), int(cy - rad), int(cx + rad * 0.5), int(cy - rad * 1.5))
    painter.drawEllipse(int(cx + rad * 0.1), int(cy - rad * 1.6), int(rad * 0.4), int(rad * 0.4))
    painter.drawLine(int(cx), int(cy + rad), int(cx), int(cy + rad + r.height() * 0.1))


def _draw_proximity_sensor(painter, r, sim_state=None):
    """ISO proximity sensor: diamond with wave lines."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    diamond = QPainterPath()
    diamond.moveTo(cx, cy - s)
    diamond.lineTo(cx + s * 0.7, cy)
    diamond.lineTo(cx, cy + s)
    diamond.lineTo(cx - s * 0.7, cy)
    diamond.closeSubpath()
    painter.drawPath(diamond)
    for i in range(2):
        yy = cy - s + (i + 1) * s * 0.4
        painter.drawArc(int(cx - s * 0.5), int(yy - s * 0.15), int(s), int(s * 0.3), 0, -180)
    painter.drawLine(int(cx), int(cy + s), int(cx), int(cy + s + r.height() * 0.1))


# ---------------------------------------------------------------------------
# Electrical & Digital symbol painters
# ---------------------------------------------------------------------------

def _draw_battery(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.35
    painter.drawLine(int(cx - s), int(cy - s * 0.5), int(cx - s), int(cy + s * 0.5))
    painter.drawLine(int(cx + s * 0.5), int(cy - s), int(cx + s * 0.5), int(cy + s))
    painter.drawLine(int(cx - s - r.width() * 0.12), int(cy), int(cx - s), int(cy))
    painter.drawLine(int(cx + s * 0.5), int(cy), int(cx + s * 0.5 + r.width() * 0.12), int(cy))
    painter.drawText(int(cx - s - 8), int(cy - s * 0.8), "+")
    painter.drawText(int(cx + s * 0.5 + 2), int(cy + s), "-")


def _draw_ac_mains(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.32
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    w = rad * 0.8
    h = rad * 0.3
    path = QPainterPath()
    path.moveTo(cx - w / 2, cy)
    path.arcTo(cx - w / 2, cy - h, w / 2, h * 2, 180, -180)
    path.arcTo(cx, cy - h, w / 2, h * 2, 180, -180)
    painter.drawPath(path)


def _draw_ground(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.35
    painter.drawLine(int(cx), int(cy - s), int(cx), int(cy))
    painter.drawLine(int(cx - s), int(cy), int(cx + s), int(cy))
    for i in range(1, 3):
        yy = cy + i * s * 0.25
        hw = s * (1 - i * 0.3)
        painter.drawLine(int(cx - hw), int(yy), int(cx + hw), int(yy))


def _draw_electric_motor(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.32
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    painter.drawText(int(cx - 6), int(cy + 5), "M")


def _draw_electric_solenoid(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    w = min(r.width(), r.height()) * 0.4
    x1 = cx - w / 2
    painter.drawRect(int(x1), int(cy - 6), int(w), int(12))
    painter.drawLine(int(x1), int(cy - 6), int(x1 + w), int(cy + 6))
    painter.drawLine(int(x1 + w), int(cy - 6), int(x1), int(cy + 6))


def _draw_lamp(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.3
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    painter.drawLine(int(cx - rad * 0.6), int(cy - rad * 0.6),
                     int(cx + rad * 0.6), int(cy + rad * 0.6))
    painter.drawLine(int(cx + rad * 0.6), int(cy - rad * 0.6),
                     int(cx - rad * 0.6), int(cy + rad * 0.6))


def _draw_relay(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    w = min(r.width(), r.height()) * 0.3
    x = cx - w / 2
    painter.drawRect(int(x), int(cy - w), int(w), int(w * 2))
    painter.drawLine(int(cx), int(cy + w), int(cx + w * 0.6), int(cy + w + w * 0.5))


def _draw_relay_nc(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    w = min(r.width(), r.height()) * 0.3
    x = cx - w / 2
    painter.drawRect(int(x), int(cy - w), int(w), int(w * 2))
    painter.drawLine(int(cx), int(cy + w), int(cx + w * 0.6), int(cy + w))


def _draw_current_limiter(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    w = min(r.width(), r.height()) * 0.6
    seg = w / 6
    x0 = cx - w / 2
    path = QPainterPath()
    path.moveTo(x0, cy)
    for i in range(6):
        path.lineTo(x0 + seg * (i + 1), cy + (seg * 0.6 if i % 2 == 0 else -seg * 0.6))
    path.lineTo(x0 + w, cy)
    painter.drawPath(path)


def _draw_switch_push(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    painter.drawLine(int(cx - s), int(cy + s * 0.2), int(cx + s), int(cy - s * 0.4))
    painter.drawLine(int(cx - s), int(cy + s), int(cx - s), int(cy - s * 0.4))
    painter.drawLine(int(cx + s), int(cy - s * 0.4), int(cx + s), int(cy - s))
    painter.drawLine(int(cx), int(cy - s), int(cx), int(cy))


def _draw_switch_push_nc(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.28
    painter.drawLine(int(cx - s), int(cy - s * 0.3), int(cx + s), int(cy))
    painter.drawLine(int(cx - s), int(cy + s), int(cx - s), int(cy - s * 0.4))
    painter.drawLine(int(cx + s), int(cy), int(cx + s), int(cy + s))
    painter.drawLine(int(cx), int(cy - s), int(cx), int(cy))


def _draw_switch_toggle(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    painter.drawLine(int(cx), int(cy + s), int(cx), int(cy - s * 0.3))
    painter.drawLine(int(cx), int(cy - s * 0.3), int(cx + s * 0.6), int(cy - s))
    painter.drawLine(int(cx - s * 0.5), int(cy - s * 0.8), int(cx + s * 0.5), int(cy - s * 0.8))


def _draw_switch_limit(painter, r, sim_state=None):
    _draw_switch_push(painter, r)
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.28
    painter.drawLine(int(cx), int(cy - s), int(cx + s * 0.4), int(cy - s * 1.6))
    painter.drawEllipse(int(cx + s * 0.2), int(cy - s * 1.7), int(s * 0.4), int(s * 0.4))


def _draw_switch_proximity(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    diamond = QPainterPath()
    diamond.moveTo(cx, cy - s)
    diamond.lineTo(cx + s * 0.6, cy)
    diamond.lineTo(cx, cy + s)
    diamond.lineTo(cx - s * 0.6, cy)
    diamond.closeSubpath()
    painter.drawPath(diamond)
    _draw_arrow(painter, cx - s * 0.4, cy + s * 0.3, cx + s * 0.4, cy - s * 0.3, size=int(s * 0.15))


def _draw_fuse(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    w = min(r.width(), r.height()) * 0.4
    x1 = cx - w
    painter.drawLine(int(x1 - r.width() * 0.12), int(cy), int(x1), int(cy))
    painter.drawRect(int(x1), int(cy - w * 0.3), int(w), int(w * 0.6))
    painter.drawLine(int(x1 + w), int(cy), int(x1 + w + r.width() * 0.12), int(cy))


def _draw_buzzer(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.3
    painter.drawArc(int(cx - rad), int(cy - rad * 0.6), int(rad * 2), int(rad * 1.2), 0, -180)
    _draw_arrow(painter, cx - rad * 0.6, cy + rad * 0.4, cx + rad * 0.6, cy - rad * 0.4, size=int(rad * 0.2))
    painter.drawText(int(cx - 4), int(cy + 10), "!")


# -- Logic gates ---------------------------------------------------------

def _draw_logic_body(painter, r, label):
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.55
    h = r.height() * 0.5
    x = cx - w / 2
    y = cy - h / 2
    rect = QPainterPath()
    rect.addRoundedRect(QRectF(x, y, w, h), 3, 3)
    painter.drawPath(rect)
    painter.drawText(int(cx - 5), int(cy + 5), label)


def _draw_and_gate(painter, r, sim_state=None):
    _draw_logic_body(painter, r, "&")


def _draw_or_gate(painter, r, sim_state=None):
    _draw_logic_body(painter, r, "\u22651")


def _draw_not_gate(painter, r, sim_state=None):
    _draw_logic_body(painter, r, "1")
    cx, cy = r.center().x(), r.center().y()
    painter.drawEllipse(int(cx + r.width() * 0.28), int(cy - 2), 4, 4)


def _draw_nand_gate(painter, r, sim_state=None):
    _draw_and_gate(painter, r)
    cx, cy = r.center().x(), r.center().y()
    painter.drawEllipse(int(cx + r.width() * 0.28), int(cy - 2), 4, 4)


def _draw_nor_gate(painter, r, sim_state=None):
    _draw_or_gate(painter, r)
    cx, cy = r.center().x(), r.center().y()
    painter.drawEllipse(int(cx + r.width() * 0.28), int(cy - 2), 4, 4)


def _draw_xor_gate(painter, r, sim_state=None):
    _draw_logic_body(painter, r, "=1")


# -- Sequential & control -------------------------------------------------

def _draw_timer(painter, r, sim_state=None):
    _draw_logic_body(painter, r, "T")


def _draw_d_flip_flop(painter, r, sim_state=None):
    _draw_logic_body(painter, r, "D")


def _draw_counter(painter, r, sim_state=None):
    _draw_logic_body(painter, r, "C")


def _draw_pulse_generator(painter, r, sim_state=None):
    _draw_logic_body(painter, r, "P")


def _draw_plc(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.6
    h = r.height() * 0.5
    x = cx - w / 2
    y = cy - h / 2
    painter.drawRect(int(x), int(y), int(w), int(h))
    painter.drawText(int(cx - 6), int(cy + 5), "PLC")


def _draw_comparator(painter, r, sim_state=None):
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.35
    tri = QPainterPath()
    tri.moveTo(cx - s, cy - s)
    tri.lineTo(cx + s, cy)
    tri.lineTo(cx - s, cy + s)
    tri.closeSubpath()
    painter.drawPath(tri)


def _draw_pid_controller(painter, r, sim_state=None):
    _draw_plc(painter, r)
    painter.drawText(int(r.center().x() - 12), int(r.center().y() + 5), "PID")


# ---------------------------------------------------------------------------
# NEW SYMBOL DRAWING FUNCTIONS (from FluidSim 4.2 catalog expansion)
# ---------------------------------------------------------------------------

def _draw_internally_gear_pump(painter, r, sim_state=None):
    """ISO internally toothed gear pump: circle with offset inner circle."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.32
    # Outer circle
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    # Offset inner circle (gerotor style)
    off = rad * 0.25
    inner_r = rad * 0.55
    painter.drawEllipse(int(cx - off - inner_r), int(cy - off - inner_r),
                        int(inner_r * 2), int(inner_r * 2))
    # Flow arrow
    _draw_arrow(painter, cx - rad * 0.6, cy + rad * 0.4,
                cx + rad * 0.6, cy - rad * 0.4, size=int(rad * 0.15))


def _draw_hydraulic_power_unit(painter, r, sim_state=None):
    """Hydraulic power unit: pump + motor + tank combination."""
    cx, cy = r.center().x(), r.center().y()
    w, h = r.width() * 0.45, r.height() * 0.35
    # Pump symbol (left half)
    pump_r = QRectF(cx - w, cy - h, w, h * 2)
    _draw_gear_pump(painter, pump_r, sim_state=sim_state)
    # Tank symbol (right half)
    tank_rect = QRectF(cx, cy - h * 0.7, w, h * 1.4)
    painter.drawRect(int(tank_rect.left()), int(tank_rect.top()),
                     int(tank_rect.width()), int(tank_rect.height()))
    # Fluid level
    painter.drawLine(int(tank_rect.left() + w * 0.1), int(cy + h * 0.2),
                     int(tank_rect.right() - w * 0.1), int(cy + h * 0.2))


def _draw_reservoir_elevated(painter, r, sim_state=None):
    """Elevated reservoir: tank symbol raised on legs."""
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.5
    h = r.height() * 0.3
    # Tank body
    painter.drawRect(int(cx - w / 2), int(cy - h), int(w), int(h))
    # Support legs
    painter.drawLine(int(cx - w / 2), int(cy - h), int(cx - w / 2), int(cy - h - r.height() * 0.15))
    painter.drawLine(int(cx + w / 2), int(cy - h), int(cx + w / 2), int(cy - h - r.height() * 0.15))
    # Return line from top
    painter.drawLine(int(cx), int(cy - h), int(cx), int(cy - h - r.height() * 0.12))


def _draw_plunger_cylinder(painter, r, sim_state=None):
    """Plunger cylinder: single-acting with thick plunger."""
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.35
    h = r.height() * 0.6
    x = cx - w / 2
    y = cy - h / 2
    # Cylinder body
    painter.drawRect(int(x), int(y), int(w), int(h))
    # Plunger (thick rod)
    rod_w = w * 0.6
    painter.drawLine(int(cx - rod_w / 2), int(cy), int(cx - rod_w / 2), int(y))
    painter.drawLine(int(cx + rod_w / 2), int(cy), int(cx + rod_w / 2), int(y))
    # Port at bottom
    painter.drawLine(int(cx), int(y + h), int(cx), int(y + h + r.height() * 0.12))


def _draw_cylinder_cushioned(painter, r, sim_state=None):
    """Double-acting cylinder with end position cushioning."""
    w = r.width() * 0.5
    h = r.height() * 0.65
    x = r.center().x() - w / 2
    y = r.top() + r.height() * 0.1
    # Draw basic double-acting cylinder
    painter.drawRect(int(x), int(y), int(w), int(h))
    # Piston
    py = y + h * 0.5
    painter.drawLine(int(x), int(py), int(x + w), int(py))
    # Rod
    rod_w = w * 0.4
    rod_h = h * 0.15
    painter.drawRect(int(x + w), int(py - rod_h / 2), int(rod_w), int(rod_h))
    # Cushioning symbols (small circles at ends)
    painter.drawEllipse(int(x + w * 0.1), int(y + h * 0.15), int(w * 0.15), int(h * 0.15))
    painter.drawEllipse(int(x + w * 0.75), int(y + h * 0.15), int(w * 0.15), int(h * 0.15))
    # Ports
    painter.drawLine(int(x), int(y + h * 0.25), int(x - r.width() * 0.15), int(y + h * 0.25))
    painter.drawLine(int(x), int(y + h * 0.75), int(x - r.width() * 0.15), int(y + h * 0.75))


def _draw_check_valve_delockable(painter, r, sim_state=None):
    """Delockable check valve: check valve with lock mechanism."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.28
    # Standard check valve
    tri = QPainterPath()
    tri.moveTo(cx - s, cy - s)
    tri.lineTo(cx + s, cy)
    tri.lineTo(cx - s, cy + s)
    tri.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)
    painter.drawLine(int(cx + s), int(cy - s), int(cx + s), int(cy + s))
    # Lock mechanism (small rectangle on side)
    lock_w = s * 0.4
    lock_h = s * 0.8
    painter.drawRect(int(cx + s + 2), int(cy - lock_h / 2), int(lock_w), int(lock_h))
    # Port lines
    painter.drawLine(int(cx - s - r.width() * 0.15), int(cy), int(cx - s), int(cy))
    painter.drawLine(int(cx + s + lock_w + 2), int(cy), int(cx + s + lock_w + r.width() * 0.1), int(cy))


def _draw_check_valve_double_delockable(painter, r, sim_state=None):
    """Double delockable check valve: two check valves in parallel."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.25
    # Two triangles side by side
    for offset in [-s * 0.6, s * 0.6]:
        tx, ty = cx + offset, cy
        tri = QPainterPath()
        tri.moveTo(tx - s * 0.6, ty - s * 0.6)
        tri.lineTo(tx + s * 0.6, ty)
        tri.lineTo(tx - s * 0.6, ty + s * 0.6)
        tri.closeSubpath()
        painter.setBrush(QBrush(painter.pen().color()))
        painter.drawPath(tri)
        painter.setBrush(Qt.NoBrush)
    # Common port lines
    painter.drawLine(int(cx - s * 1.5), int(cy), int(cx - s * 0.6), int(cy))
    painter.drawLine(int(cx + s * 0.6), int(cy), int(cx + s * 1.5), int(cy))


def _draw_sequence_valve(painter, r, sim_state=None):
    """Sequence valve: relief valve with external pilot line."""
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.35
    bh = r.height() * 0.35
    bx = cx - bw / 2
    by = cy - bh / 2
    painter.drawRect(int(bx), int(by), int(bw), int(bh))
    # Arrow pointing up (opens when pressure reached)
    _draw_arrow(painter, bx + bw * 0.5, by + bh * 0.8,
                bx + bw * 0.5, by + bh * 0.2, size=int(bh * 0.15))
    # Spring on right
    _draw_spring(painter, bx + bw + 8, by + bh * 0.1, by + bh * 0.9, width=bw * 0.15)
    # Pilot line (dashed) from bottom to top
    _draw_dashed_line(painter, bx, by + bh, bx, by - r.height() * 0.15)
    # Port lines
    painter.drawLine(int(bx), int(by + bh), int(bx), int(by + bh + r.height() * 0.1))
    painter.drawLine(int(bx + bw), int(by + bh), int(bx + bw), int(by + bh + r.height() * 0.1))


def _draw_needle_restrictor(painter, r, sim_state=None):
    """Needle restrictor: variable orifice with needle adjustment."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.25
    # Arc-orifice symbol
    path = QPainterPath()
    path.arcTo(cx - s, cy - s * 0.8, s * 2, s * 1.6, 0, 180)
    painter.drawPath(path)
    path2 = QPainterPath()
    path2.arcTo(cx - s, cy - s * 0.8, s * 2, s * 1.6, 0, -180)
    painter.drawPath(path2)
    # Needle line through center
    painter.drawLine(int(cx), int(cy - s), int(cx - s * 1.2), int(cy + s * 1.2))
    # Port lines
    painter.drawLine(int(cx - s - r.width() * 0.15), int(cy), int(cx - s), int(cy))
    painter.drawLine(int(cx + s), int(cy), int(cx + s + r.width() * 0.15), int(cy))


def _draw_gap_restrictor(painter, r, sim_state=None):
    """Gap restrictor with helix: variable flow control."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    # Variable orifice (adjustable restriction)
    painter.drawLine(int(cx - s), int(cy), int(cx - s * 0.3), int(cy))
    painter.drawLine(int(cx + s * 0.3), int(cy), int(cx + s), int(cy))
    # Adjustable gap (angled line)
    painter.drawLine(int(cx - s * 0.3), int(cy - s * 0.5), int(cx + s * 0.3), int(cy + s * 0.5))
    # Helix symbol (coil) on the adjustable part
    for i in range(3):
        yy = cy - s * 0.3 + i * s * 0.3
        painter.drawArc(int(cx - s * 0.15), int(yy - s * 0.1), int(s * 0.3), int(s * 0.2), 0, -180)


def _draw_piston_gauge(painter, r, sim_state=None):
    """Piston pressure gauge: circular gauge with piston indicator."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.35
    painter.drawEllipse(int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2))
    # Piston inside
    painter.drawLine(int(cx - rad * 0.5), int(cy), int(cx + rad * 0.5), int(cy))
    painter.drawLine(int(cx), int(cy - rad * 0.5), int(cx), int(cy + rad * 0.5))
    # Label
    font = painter.font()
    font.setPixelSize(int(rad * 0.5))
    painter.setFont(font)
    painter.drawText(int(cx - rad * 0.15), int(cy + rad * 0.3), "P")
    # Port
    painter.drawLine(int(cx), int(cy + rad), int(cx), int(cy + rad + r.height() * 0.08))


def _draw_bourdon_gauge(painter, r, sim_state=None):
    """Bourdon-tube pressure gauge: C-shaped tube with pointer."""
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) * 0.3
    # C-shaped tube
    path = QPainterPath()
    path.arcTo(cx - rad, cy - rad, rad * 2, rad * 2, 225, 270)
    painter.drawPath(path)
    # Pointer from center
    angle = -math.pi * 0.3
    px = cx + rad * 0.6 * math.cos(angle)
    py = cy + rad * 0.6 * math.sin(angle)
    painter.drawLine(int(cx), int(cy), int(px), int(py))
    # Center dot
    painter.drawEllipse(int(cx - 2), int(cy - 2), 4, 4)
    # Port
    painter.drawLine(int(cx), int(cy + rad), int(cx), int(cy + rad + r.height() * 0.08))


def _draw_water_cooler(painter, r, sim_state=None):
    """Water cooler: heat exchanger with water flow indication."""
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.4
    bh = r.height() * 0.4
    bx = cx - bw / 2
    by = cy - bh / 2
    painter.drawRect(int(bx), int(by), int(bw), int(bh))
    # Water flow arrows (bottom path)
    for i in range(2):
        yy = by + bh * 0.3 + i * bh * 0.4
        painter.drawLine(int(bx + bh * 0.2), int(yy), int(bx + bw), int(yy - bh * 0.2))
    # Main flow line
    painter.drawLine(int(bx), int(cy), int(bx - r.width() * 0.12), int(cy))
    painter.drawLine(int(bx + bw), int(cy), int(bx + bw + r.width() * 0.12), int(cy))


def _draw_air_cooler(painter, r, sim_state=None):
    """Air cooler: heat exchanger with fan symbol."""
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.4
    bh = r.height() * 0.4
    bx = cx - bw / 2
    by = cy - bh / 2
    painter.drawRect(int(bx), int(by), int(bw), int(bh))
    # Fan blades (circle with lines)
    fan_r = bw * 0.3
    painter.drawEllipse(int(cx - fan_r), int(cy - fan_r), int(fan_r * 2), int(fan_r * 2))
    for ang in [0, math.pi / 2, math.pi, math.pi * 1.5]:
        ex = cx + fan_r * 0.8 * math.cos(ang)
        ey = cy + fan_r * 0.8 * math.sin(ang)
        painter.drawLine(int(cx), int(cy), int(ex), int(ey))
    # Flow lines
    painter.drawLine(int(bx), int(cy), int(bx - r.width() * 0.12), int(cy))
    painter.drawLine(int(bx + bw), int(cy), int(bx + bw + r.width() * 0.12), int(cy))


def _draw_heating_element(painter, r, sim_state=None):
    """Heating element: resistor symbol in flow path."""
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.5
    # Zigzag resistor
    seg = w / 6
    x0 = cx - w / 2
    path = QPainterPath()
    path.moveTo(x0, cy)
    for i in range(6):
        path.lineTo(x0 + seg * (i + 0.5), cy + (seg * 0.4 if i % 2 == 0 else -seg * 0.4))
        path.lineTo(x0 + seg * (i + 1), cy)
    painter.drawPath(path)
    # Flow continuation
    painter.drawLine(int(x0 - r.width() * 0.12), int(cy), int(x0), int(cy))
    painter.drawLine(int(x0 + w), int(cy), int(x0 + w + r.width() * 0.12), int(cy))


def _draw_valve_3_2_unloaded(painter, r, sim_state=None):
    """3/2 way valve with unloaded position."""
    _draw_directional_valve(painter, r, ["P"], ["A", "T"], sim_state=sim_state)
    cx, cy = r.center().x(), r.center().y()
    bw = r.width() * 0.55
    bh = r.height() * 0.35
    bx = cx - bw / 2
    by = cy - bh / 2
    # Divider for 2 positions
    painter.drawLine(int(bx + bw / 2), int(by), int(bx + bw / 2), int(by + bh))
    # Position 1: P to A (arrow up)
    _draw_arrow(painter, bx + bw * 0.25, by + bh * 0.75,
                bx + bw * 0.25, by + bh * 0.25, size=int(bh * 0.12))
    # Position 2: P closed, A to T (crossed)
    _draw_arrow(painter, bx + bw * 0.75, by + bh * 0.75,
                bx + bw * 0.75, by + bh * 0.25, size=int(bh * 0.12))


def _draw_speaker(painter, r, sim_state=None):
    """Speaker/electroacoustic transducer."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.35
    # Triangle (speaker cone)
    tri = QPainterPath()
    tri.moveTo(cx - s * 0.5, cy - s)
    tri.lineTo(cx + s * 0.5, cy - s)
    tri.lineTo(cx, cy + s * 0.5)
    tri.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)
    # Lines
    painter.drawLine(int(cx - s * 0.5), int(cy - s), int(cx - s * 0.5), int(cy + s * 0.2))
    painter.drawLine(int(cx + s * 0.5), int(cy - s), int(cx + s * 0.5), int(cy + s * 0.2))
    # Terminals
    painter.drawLine(int(cx - s), int(cy + s * 0.5), int(cx - s * 0.5), int(cy + s * 0.5))
    painter.drawLine(int(cx + s * 0.5), int(cy + s * 0.5), int(cx + s), int(cy + s * 0.5))


def _draw_relay_timer(painter, r, sim_state=None):
    """Timer relay: relay coil with timer symbol."""
    cx, cy = r.center().x(), r.center().y()
    w = min(r.width(), r.height()) * 0.3
    # Coil rectangle
    painter.drawRect(int(cx - w / 2), int(cy - w), int(w), int(w * 2))
    # Timer arc
    painter.drawArc(int(cx - w * 0.6), int(cy - w * 0.6), int(w * 1.2), int(w * 1.2), 0, -180)
    # Contacts
    painter.drawLine(int(cx), int(cy + w), int(cx + w * 0.5), int(cy + w + w * 0.3))
    # Labels
    font = painter.font()
    font.setPixelSize(int(w * 0.4))
    painter.setFont(font)
    painter.drawText(int(cx - w * 0.15), int(cy - w * 0.2), "T")


def _draw_diode(painter, r, sim_state=None):
    """Diode: triangle with bar."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    # Triangle
    tri = QPainterPath()
    tri.moveTo(cx - s * 0.5, cy - s * 0.6)
    tri.lineTo(cx + s * 0.5, cy)
    tri.lineTo(cx - s * 0.5, cy + s * 0.6)
    tri.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)
    # Bar
    painter.drawLine(int(cx + s * 0.5), int(cy - s * 0.6), int(cx + s * 0.5), int(cy + s * 0.6))
    # Terminals
    painter.drawLine(int(cx - s), int(cy), int(cx - s * 0.5), int(cy))
    painter.drawLine(int(cx + s * 0.5), int(cy), int(cx + s), int(cy))


def _draw_transistor(painter, r, sim_state=None):
    """NPN transistor symbol."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.3
    # Circle
    painter.drawEllipse(int(cx - s), int(cy - s), int(s * 2), int(s * 2))
    # Base line
    painter.drawLine(int(cx - s), int(cy), int(cx - s * 0.2), int(cy))
    # Collector and emitter
    painter.drawLine(int(cx - s * 0.2), int(cy - s * 0.5), int(cx + s * 0.5), int(cy - s * 0.5))
    painter.drawLine(int(cx - s * 0.2), int(cy + s * 0.5), int(cx + s * 0.5), int(cy + s * 0.5))
    # Emitter arrow
    _draw_arrow(painter, cx, int(cy + s * 0.35), cx + s * 0.3, int(cy + s * 0.65), size=4)
    # Terminals
    painter.drawLine(int(cx - s), int(cy), int(cx - s - r.width() * 0.12), int(cy))
    painter.drawLine(int(cx + s * 0.5), int(cy - s * 0.5), int(cx + s * 0.5 + r.width() * 0.1), int(cy - s * 0.5))
    painter.drawLine(int(cx + s * 0.5), int(cy + s * 0.5), int(cx + s * 0.5 + r.width() * 0.1), int(cy + s * 0.5))


def _draw_op_amp(painter, r, sim_state=None):
    """Operational amplifier: triangle with + - inputs."""
    cx, cy = r.center().x(), r.center().y()
    s = min(r.width(), r.height()) * 0.35
    # Triangle
    tri = QPainterPath()
    tri.moveTo(cx - s, cy - s * 0.7)
    tri.lineTo(cx - s, cy + s * 0.7)
    tri.lineTo(cx + s * 0.8, cy)
    tri.closeSubpath()
    painter.setBrush(QBrush(painter.pen().color()))
    painter.drawPath(tri)
    painter.setBrush(Qt.NoBrush)
    # + and - labels
    font = painter.font()
    font.setPixelSize(int(s * 0.4))
    painter.setFont(font)
    painter.drawText(int(cx - s * 0.7), int(cy - s * 0.3), "+")
    painter.drawText(int(cx - s * 0.7), int(cy + s * 0.4), "-")
    # Terminals
    painter.drawLine(int(cx - s), int(cy - s * 0.5), int(cx - s - r.width() * 0.12), int(cy - s * 0.5))
    painter.drawLine(int(cx - s), int(cy + s * 0.5), int(cx - s - r.width() * 0.12), int(cy + s * 0.5))
    painter.drawLine(int(cx + s * 0.8), int(cy), int(cx + s * 0.8 + r.width() * 0.1), int(cy))


def _draw_jk_flip_flop(painter, r, sim_state=None):
    """JK Flip-Flop: rectangle with J, K, CLK, Q, Q̄."""
    _draw_logic_body(painter, r, "JK")
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.55
    h = r.height() * 0.5
    x = cx - w / 2
    y = cy - h / 2
    # Redraw box
    painter.drawRect(int(x), int(y), int(w), int(h))
    # Labels
    font = painter.font()
    font.setPixelSize(int(h * 0.35))
    painter.setFont(font)
    painter.drawText(int(x + 2), int(cy - h * 0.2), "J")
    painter.drawText(int(x + 2), int(cy + h * 0.15), "K")
    painter.drawText(int(x + w * 0.3), int(cy + h * 0.35), "CLK")
    painter.drawText(int(x + w * 0.5), int(cy - h * 0.2), "Q")
    painter.drawText(int(x + w * 0.5), int(cy + h * 0.35), "Q̄")


def _draw_sr_latch(painter, r, sim_state=None):
    """SR Latch: rectangle with S, R, Q, Q̄."""
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.55
    h = r.height() * 0.5
    x = cx - w / 2
    y = cy - h / 2
    painter.drawRect(int(x), int(y), int(w), int(h))
    font = painter.font()
    font.setPixelSize(int(h * 0.35))
    painter.setFont(font)
    painter.drawText(int(x + 2), int(cy - h * 0.2), "S")
    painter.drawText(int(x + 2), int(cy + h * 0.15), "R")
    painter.drawText(int(x + w * 0.5), int(cy - h * 0.2), "Q")
    painter.drawText(int(x + w * 0.5), int(cy + h * 0.35), "Q̄")


def _draw_shift_register(painter, r, sim_state=None):
    """Shift Register: rectangle with IN, CLK, OUT."""
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.55
    h = r.height() * 0.5
    x = cx - w / 2
    y = cy - h / 2
    painter.drawRect(int(x), int(y), int(w), int(h))
    font = painter.font()
    font.setPixelSize(int(h * 0.3))
    painter.setFont(font)
    painter.drawText(int(x + 2), int(cy), "IN")
    painter.drawText(int(cx), int(cy - h * 0.25), "CLK")
    painter.drawText(int(x + w - 10), int(cy), "OUT")


def _draw_display_7seg(painter, r, sim_state=None):
    """7-Segment Display: rectangular display outline."""
    cx, cy = r.center().x(), r.center().y()
    w = r.width() * 0.5
    h = r.height() * 0.5
    x = cx - w / 2
    y = cy - h / 2
    # Outer rectangle
    painter.drawRect(int(x), int(y), int(w), int(h))
    # Segment lines (simplified)
    painter.drawLine(int(x + w * 0.1), int(y + h * 0.5), int(x + w * 0.4), int(y + h * 0.5))
    painter.drawLine(int(x + w * 0.6), int(y + h * 0.5), int(x + w * 0.9), int(y + h * 0.5))
    painter.drawLine(int(cx), int(y + h * 0.1), int(cx), int(y + h * 0.9))
    # Label
    font = painter.font()
    font.setPixelSize(int(h * 0.25))
    painter.setFont(font)
    painter.drawText(int(cx - 5), int(cy + h * 0.35), "8")


# ---------------------------------------------------------------------------
# Symbol Library Widget
# ---------------------------------------------------------------------------

class SymbolLibrary(QWidget):
    """Panel showing all available symbols in a tree, with search filter.

    Signals
    -------
    symbol_selected(str)
        Emitted when the user clicks a symbol item.  The argument is the
        symbol id (e.g. ``"pump"``).
    """

    symbol_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._populate_tree()

    # -- layout -------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search symbols...")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        self._tree = _SymbolTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(16)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.setDragEnabled(True)
        self._tree.setDragDropMode(QTreeWidget.DragOnly)
        layout.addWidget(self._tree)

    # -- population ---------------------------------------------------------

    def _populate_tree(self):
        for mode, categories in sorted(SYMBOL_CATALOG.items()):
            mode_item = QTreeWidgetItem(self._tree, [mode])
            mode_item.setFlags(mode_item.flags() & ~Qt.ItemIsSelectable)
            font = mode_item.font(0)
            font.setBold(True)
            mode_item.setFont(0, font)

            for cat, symbols in sorted(categories.items()):
                cat_item = QTreeWidgetItem(mode_item, [cat])
                cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
                cat_item.setExpanded(True)

                for sym_id in symbols:
                    name = DISPLAY_NAMES.get(sym_id, sym_id)
                    sym_item = QTreeWidgetItem(cat_item, [name])
                    sym_item.setData(0, Qt.UserRole, sym_id)
                    sym_item.setFlags(sym_item.flags() | Qt.ItemIsDragEnabled)

            mode_item.setExpanded(True)

    # -- slots --------------------------------------------------------------

    def _on_item_clicked(self, item, column):
        sym_id = item.data(0, Qt.UserRole)
        if sym_id is not None:
            self.symbol_selected.emit(sym_id)

    def _on_search(self, text):
        text = text.lower().strip()
        for i in range(self._tree.topLevelItemCount()):
            mode_item = self._tree.topLevelItem(i)
            any_visible = False
            for j in range(mode_item.childCount()):
                cat_item = mode_item.child(j)
                cat_visible = False
                for k in range(cat_item.childCount()):
                    sym_item = cat_item.child(k)
                    if text in sym_item.text(0).lower() or text in (sym_item.data(0, Qt.UserRole) or "").lower():
                        sym_item.setHidden(False)
                        cat_visible = True
                    else:
                        sym_item.setHidden(True)
                cat_item.setHidden(not cat_visible)
                if cat_visible:
                    any_visible = True
            mode_item.setHidden(not any_visible)

    # -- public helpers -----------------------------------------------------

    def symbol_ids(self):
        """Return a flat list of all symbol ids in catalog order."""
        result = []
        for categories in SYMBOL_CATALOG.values():
            for symbols in categories.values():
                result.extend(symbols)
        return result

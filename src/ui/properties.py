"""Properties panel with live simulation values, categories, and improved styling."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFormLayout, QLabel,
    QCheckBox, QDoubleSpinBox, QSpinBox, QLineEdit, QGroupBox,
    QComboBox, QFrame,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from src.ui import ICONS


TYPE_LABELS = {
    "pump": "Fixed Displacement Pump", "gear_pump": "Gear Pump",
    "pump_vane": "Vane Pump", "piston_pump": "Piston Pump",
    "variable_pump": "Variable Displacement Pump",
    "compressor": "Compressor", "air_supply": "Air Supply",
    "vacuum_generator": "Vacuum Generator",
    "cylinder_single": "Single-Acting Cylinder", "cylinder_double": "Double-Acting Cylinder",
    "cylinder_telescopic": "Telescopic Cylinder",
    "motor": "Hydraulic Motor", "air_motor": "Air Motor", "motor_bi": "Reversible Motor",
    "valve_2_2": "2/2 Way Valve", "valve_3_2": "3/2 Way Valve",
    "valve_4_2": "4/2 Way Valve", "valve_4_3": "4/3 Way Valve",
    "valve_5_2": "5/2 Way Valve", "valve_5_3": "5/3 Way Valve",
    "check_valve": "Check Valve", "pilot_check_valve": "Pilot-Operated Check Valve",
    "relief_valve": "Relief Valve", "pressure_reducer": "Pressure Reducing Valve",
    "throttle": "Throttle Valve", "needle_valve": "Needle Valve",
    "one_way_flow_control": "One-Way Flow Control Valve", "flow_control": "Flow Control Valve",
    "shuttle_valve": "Shuttle Valve", "two_pressure_valve": "Two-Pressure (AND) Valve",
    "quick_exhaust": "Quick Exhaust Valve",
    "tank": "Tank / Reservoir", "pressure_gauge": "Pressure Gauge",
    "pressure_switch": "Pressure Switch", "temperature_gauge": "Temperature Gauge",
    "flow_meter": "Flow Meter", "filter": "Filter",
    "accumulator": "Accumulator", "heat_exchanger": "Heat Exchanger",
    "regulator": "Pressure Regulator",
    "lubricator": "Lubricator", "silencer": "Silencer",
    "air_service_unit": "Air Service Unit (FRL)",
    "limit_switch": "Limit Switch", "proximity_sensor": "Proximity Sensor",
    # Electrical
    "battery": "Battery / DC Source", "dc_supply": "DC Power Supply",
    "ac_mains": "AC Mains Supply", "ground": "Ground",
    "electric_motor": "Electric Motor", "solenoid": "Solenoid", "lamp": "Indicator Lamp",
    "relay": "Relay (NO)", "relay_nc": "Relay (NC)", "current_limiter": "Current Limiter",
    "switch_push": "Push Button (NO)", "switch_push_nc": "Push Button (NC)",
    "switch_toggle": "Toggle Switch", "switch_limit": "Limit Switch (Elec.)",
    "switch_proximity": "Proximity Switch",
    "fuse": "Fuse", "buzzer": "Buzzer / Alarm",
    # Digital & Control
    "and_gate": "AND Gate", "or_gate": "OR Gate", "not_gate": "NOT Gate",
    "nand_gate": "NAND Gate", "nor_gate": "NOR Gate", "xor_gate": "XOR Gate",
    "timer": "Timer / Delay", "d_flip_flop": "D Flip-Flop", "counter": "Counter",
    "pulse_generator": "Pulse Generator", "plc": "PLC / Controller",
    "comparator": "Comparator", "pid_controller": "PID Controller",
    "spring_return": "Spring Return",
}


class PropertiesPanel(QWidget):
    """Enhanced properties panel with categories and live simulation values."""

    property_changed = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._component = None
        self._building = False
        self._widgets = {}
        self._sim_states = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # --- Header with component name ---
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        self.title_label = QLabel("No component selected")
        self.title_label.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #eee; padding: 4px;")
        h_layout.addWidget(self.title_label)
        h_layout.addStretch()

        self.sim_status_label = QLabel("")
        self.sim_status_label.setStyleSheet(
            "font-size: 10px; color: #888; padding: 4px;")
        h_layout.addWidget(self.sim_status_label)

        main_layout.addWidget(header)

        # --- Scrollable form ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        self.form_layout = QFormLayout(scroll_content)
        self.form_layout.setSpacing(6)
        self.form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.form_layout.setFormAlignment(Qt.AlignTop)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def set_component(self, comp):
        self._component = comp
        self._widgets.clear()
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)

        if not comp:
            self.title_label.setText("No component selected")
            self.sim_status_label.setText("")
            return

        ctype = comp.get("type", "unknown")
        label = TYPE_LABELS.get(ctype, ctype)
        if len(label) > 30:
            label = label[:27] + "..."
        self.title_label.setText(label)
        self.sim_status_label.setText(f"[{ctype}]")

        props = comp.get("properties", {})

        # --- Position group ---
        self._add_group("Position", [
            ("Name", self._make_editable(props.get("name", ""), "name")),
            ("X", self._make_spin(comp.get("x", 0), -10000, 10000, "x")),
            ("Y", self._make_spin(comp.get("y", 0), -10000, 10000, "y")),
            ("Rotation", self._make_spin(comp.get("rotation", 0), 0, 270, "rotation", step=90)),
        ])

        # --- Dynamic groups based on type ---
        dynamic_groups = self._build_dynamic_groups(ctype, props)
        for group_name, items in dynamic_groups.items():
            self._add_group(group_name, items)

        # --- Live simulation values (read-only, always at bottom) ---
        self._add_readonly_live_values(comp)

    def set_sim_states(self, states):
        """Update simulation states for live value display."""
        self._sim_states = states
        if self._component:
            self.set_component(self._component)

    def _add_group(self, title, widgets_items):
        """Add a styled group box with form items."""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; font-size: 11px; color: #aaa;
                border: 1px solid #3d3d3d; border-radius: 4px;
                margin-top: 6px; padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 8px; padding: 0 4px;
                color: #6aafcf;
            }
        """)
        glayout = QFormLayout(group)
        glayout.setSpacing(5)
        glayout.setContentsMargins(8, 25, 8, 8)

        for label_text, widget in widgets_items:
            widget.setObjectName(f"group_{title}_{label_text}")
            glayout.addRow(label_text, widget)
            self._widgets[label_text.lower()] = widget

        self.form_layout.addRow(group)

    def _build_dynamic_groups(self, ctype, props):
        """Build property groups based on component type."""
        groups = {}

        if ctype in ("pump", "gear_pump", "pump_vane", "piston_pump", "variable_pump"):
            groups["Operation"] = [
                ("Running", self._make_check(props.get("running", True), "running")),
                ("Flow Rate (L/min)", self._make_dspin(props.get("flow_rate", 20.0), 0, 500, "flow_rate")),
                ("Speed (RPM)", self._make_spin(props.get("rpm", 1500), 0, 10000, "rpm")),
                ("Max Pressure (bar)", self._make_dspin(props.get("pressure_max", 250), 0, 1000, "pressure_max")),
            ]
        elif ctype == "compressor":
            groups["Operation"] = [
                ("Running", self._make_check(props.get("running", True), "running")),
                ("Flow Rate (L/min)", self._make_dspin(props.get("flow_rate", 500), 0, 5000, "flow_rate")),
                ("Max Pressure (bar)", self._make_dspin(props.get("pressure_max", 10), 0, 30, "pressure_max")),
            ]
        elif ctype == "air_supply":
            groups["Settings"] = [
                ("Pressure (bar)", self._make_dspin(props.get("pressure", 6.0), 0, 30, "pressure")),
                ("Flow Rate (L/min)", self._make_dspin(props.get("flow_rate", 1000), 0, 10000, "flow_rate")),
            ]
        elif ctype in ("cylinder_single", "cylinder_double"):
            groups["Dimensions"] = [
                ("Bore (mm)", self._make_spin(props.get("bore", 50), 5, 500, "bore")),
                ("Stroke (mm)", self._make_spin(props.get("stroke", 200), 10, 2000, "stroke")),
                ("Rod Diameter (mm)", self._make_spin(props.get("rod_diameter", 20), 2, 200, "rod_diameter")),
            ]
        elif ctype == "cylinder_telescopic":
            groups["Dimensions"] = [
                ("Bore (mm)", self._make_spin(props.get("bore", 80), 5, 500, "bore")),
                ("Stroke (mm)", self._make_spin(props.get("stroke", 400), 10, 4000, "stroke")),
                ("Stages", self._make_spin(props.get("stages", 3), 2, 6, "stages")),
            ]
        elif ctype in ("motor", "air_motor", "motor_bi"):
            groups["Operation"] = [
                ("Running", self._make_check(props.get("running", True), "running")),
                ("Displacement (cm3/rev)", self._make_dspin(props.get("displacement", 25), 0, 500, "displacement")),
                ("Max Speed (RPM)", self._make_spin(props.get("rpm_max", 3000), 0, 10000, "rpm_max")),
            ]
        elif ctype in ("valve_2_2", "valve_3_2", "valve_4_2", "valve_4_3", "valve_5_2", "valve_5_3"):
            groups["State"] = [
                ("Actuated", self._make_check(props.get("actuated", False), "actuated")),
                ("Position", QLabel(props.get("position", "normally_closed"))),
            ]
        elif ctype in ("relief_valve", "pressure_reducer"):
            groups["Settings"] = [
                ("Set Pressure (bar)", self._make_dspin(props.get("set_pressure", 200), 0, 1000, "set_pressure")),
                ("Max Flow (L/min)", self._make_dspin(props.get("flow_max", 50), 0, 1000, "flow_max")),
            ]
        elif ctype in ("throttle", "needle_valve", "one_way_flow_control"):
            groups["Settings"] = [
                ("Opening (%)", self._make_dspin(props.get("opening", 50), 0, 100, "opening")),
                ("Max Flow (L/min)", self._make_dspin(props.get("flow_max", 30), 0, 1000, "flow_max")),
            ]
        elif ctype == "pressure_gauge":
            val = props.get("value", 0.0)
            groups["Reading"] = [
                ("Current Value", QLabel(f"{val:.2f} bar")),
            ]
        elif ctype == "pressure_switch":
            groups["Settings"] = [
                ("Set Pressure (bar)", self._make_dspin(props.get("set_pressure", 100), 0, 1000, "set_pressure")),
                ("Hysteresis (bar)", self._make_dspin(props.get("hysteresis", 10), 0, 100, "hysteresis")),
            ]
        elif ctype == "accumulator":
            groups["Specs"] = [
                ("Volume (L)", self._make_dspin(props.get("volume", 1.0), 0.1, 100, "volume")),
                ("Pre-charge (bar)", self._make_dspin(props.get("pre_charge", 100), 0, 500, "pre_charge")),
            ]

        return groups

    def _make_editable(self, value, key):
        w = QLineEdit(str(value))
        w.setObjectName(key)
        w.setStyleSheet("""
            QLineEdit {
                background: #1e1e1e; color: #ddd; border: 1px solid #444;
                border-radius: 3px; padding: 2px 6px;
            }
            QLineEdit:focus { border-color: #2e86c1; }
        """)
        w.textChanged.connect(lambda t: self._emit(key, t))
        return w

    def _make_check(self, value, key):
        w = QCheckBox()
        w.setChecked(bool(value))
        w.setObjectName(key)
        w.setStyleSheet("""
            QCheckBox { color: #ddd; spacing: 6px; }
            QCheckBox::indicator { width: 16px; height: 16px;
                border: 1px solid #555; border-radius: 3px; background: #1e1e1e; }
            QCheckBox::indicator:checked { background: #2e86c1; border-color: #2e86c1; }
        """)
        w.toggled.connect(lambda v: self._emit(key, v))
        return w

    def _make_spin(self, value, lo, hi, key, step=1):
        is_float = step < 1 or isinstance(value, float)
        if is_float:
            w = QDoubleSpinBox()
            w.setRange(lo, hi)
            w.setValue(float(value))
            w.setDecimals(2)
            w.setSingleStep(step)
        else:
            w = QSpinBox()
            w.setRange(int(lo), int(hi))
            w.setValue(int(value))
            w.setSingleStep(step)
        w.setObjectName(key)
        w.setStyleSheet("""
            QSpinBox, QDoubleSpinBox {
                background: #1e1e1e; color: #ddd; border: 1px solid #444;
                border-radius: 3px; padding: 2px 4px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus { border-color: #2e86c1; }
        """)
        w.valueChanged.connect(lambda v: self._emit(key, v))
        return w

    def _make_dspin(self, value, lo, hi, key):
        w = QDoubleSpinBox()
        w.setRange(lo, hi)
        w.setValue(float(value))
        w.setDecimals(2)
        w.setSingleStep(0.01)
        w.setObjectName(key)
        w.setStyleSheet("""
            QDoubleSpinBox {
                background: #1e1e1e; color: #ddd; border: 1px solid #444;
                border-radius: 3px; padding: 2px 4px;
            }
            QDoubleSpinBox:focus { border-color: #2e86c1; }
        """)
        w.valueChanged.connect(lambda v: self._emit(key, v))
        return w

    def _add_readonly_live_values(self, comp):
        """Add read-only live simulation values at the bottom of the panel."""
        if not self._sim_states:
            return

        ctype = comp.get("type", "")
        cid = comp.get("id", "")
        state = self._sim_states.get(cid, {})

        if not state:
            return

        live_items = []

        if ctype in ("cylinder_single", "cylinder_double"):
            pos = state.get("position", 0) * 100
            press_a = state.get("pressure_a", 0) / 1e5
            live_items.extend([
                ("Position", QLabel(f"{pos:.1f}%")),
                ("Pressure A", QLabel(f"{press_a:.2f} bar")),
            ])
        elif ctype == "pressure_gauge":
            reading = state.get("reading", 0) / 1e5
            live_items.append(("Reading", QLabel(f"{reading:.2f} bar")))
        elif ctype in ("pump", "compressor"):
            fr = state.get("flow_rate", 0)
            live_items.append(("Flow Rate", QLabel(f"{fr:.2f} L/min")))
        elif ctype in ("valve_2_2", "valve_3_2", "valve_4_2", "valve_4_3"):
            act = state.get("actuated", False)
            live_items.append(("State", QLabel("ACTIVATED" if act else "NORMAL")))
        elif ctype == "tank":
            level = state.get("level", 0) * 100
            live_items.append(("Level", QLabel(f"{level:.1f}%")))

        if live_items:
            self._add_group("Live Values", live_items)

    def _emit(self, key, value):
        if self._building:
            return
        if key == "name" and self._component:
            self._component["name"] = value
        elif key in ("x", "y", "rotation") and self._component:
            self._component[key] = value
        elif self._component:
            if "properties" not in self._component:
                self._component["properties"] = {}
            self._component["properties"][key] = value
        self.property_changed.emit(key, value)

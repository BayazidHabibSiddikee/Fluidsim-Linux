# FluidSim Linux — UI/UX Design: Tool Palette, Port Switches & Animations

**Role:** UI/UX Designer
**Domain:** PySide6 (Qt 6) desktop application
**Scope:** Three design areas — (1) restructured tool palette ("tool parts"),
(2) interactive port switches for directional valves, (3) sim_state-driven
per-frame animations.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Restructured Tool Palette](#2-restructured-tool-palette--tool-parts-architecture)
3. [Interactive Port Switches](#3-interactive-port-switches--actuation-rectangle-click)
4. [Animation Pipeline](#4-animation--sim_state-drives-per-frame-repaints)
5. [Code Changes Summary](#5-summary-of-required-code-changes)

---

## 1. Overview

### 1.1 Current Architecture

| Layer | File | Class | Role |
|-------|------|-------|------|
| App shell | `src/app.py` | `MainWindow(QMainWindow)` | Owns canvas, palettes, sim engine, timer |
| Tool palette | `src/ui/tools.py` | `ToolPalette(QWidget)`, `ToolButton(QToolButton)` | 5 tool buttons (no QButtonGroup) |
| Canvas | `src/ui/canvas.py` | `CircuitCanvas(QWidget)` | Rendering + mouse interaction; `self._tool` is a bare string |
| Properties | `src/ui/properties.py` | `PropertiesPanel(QWidget)` | Editable + live sim values |
| Library | `src/ui/library.py` | `SymbolLibrary(QWidget)` | Drag-and-drop symbol browser |
| Symbols | `src/symbols/library.py` | `draw_symbol()`, per-type `_draw_*` | QPainter-based ISO schematic drawers |
| Simulation | `src/simulation/engine.py` | `SimulationEngine` | Time-stepped physics; `component_states` dict |
| Icons | `src/ui/icons.py` | `make_all_icons()` | Programmatic QIcon factory |

### 1.2 Key Findings

- `CircuitCanvas.set_tool()` **only accepts** `"select"`, `"wire"`, `"place"`.
  The `"delete"` tool exists in the palette but is actually routed to a
  `QAction(shortcut=Delete)` → `canvas.delete_selected`. The `"pan"` tool
  exists in the palette but is actually handled via **middle-mouse drag**
  in `mousePressEvent` / `mouseMoveEvent`.
- `ToolPalette` (ui variant) does **not** use `QButtonGroup` — it stores
  buttons in a plain list and checks `.isChecked()` manually.
- Keyboard shortcuts (V/W/P/X) are dispatched via a fragile
  `tool_palette_parent()` walk-up that reaches into `parent.buttons[N].click()`.
- Directional valve actuation rectangles are drawn by
  `_draw_directional_valve()` — they respond to `sim_state["actuated"]`
  but **have no hit detection** for mouse clicks.
- Three visual states for actuation (green / neutral / red) are not fully
  implemented; only green (actuated) and gray (neutral) exist.
- Animation is purely **frame-based QPainter** driven by `QTimer.timeout`
  → `sim_engine.step()` → `canvas.set_sim_states()` → `canvas.update()` →
  `paintEvent()` → `draw_symbol(sim_state=...)`.

---

## 3. Interactive Port Switches — Actuation Rectangle Click

### 3.1 Current State in Codebase

In `src/symbols/library.py`, `_draw_directional_valve()` draws:

```
  ← act_w →
  ┌┄┄┄┄┄┄┄┐   ┌──────────┐   ╱╲     ┌──────────┐
  │ act   │   │ valve    │  ╱  ╲   │ spring  │
  │ rect  │   │ box      │ ╱    ╲  │ (zigzag)│
  └┄┄┄┄┄┄┄┘   └──────────┘╲      ╱ └──────────┘
  y+h*0.2              y                y+h*0.85

  Actuation rect bounds:
    w      = rect.width() * 0.55
    act_w  = w * 0.12
    act_x  = x - act_w - 2
    act_y  = y + h * 0.2
    act_h  = h * 0.6

  Position indicator (red dot) moves inside valve box:
    pos_x = x + w*0.2 + (w*0.6) * position  (0=left, 1=right)
```

- **Actuation rectangle bounds:** `(x - act_w - 2, y + h*0.2, act_w, h*0.6)`
  where `w = rect.width() * 0.55`, `act_w = w * 0.12`
- When `sim_state["actuated"]` is `True`: green pen `(0,180,0)` + light-green
  brush `(200,255,200)`.
- When `False`: default pen, `NoBrush`.
- **No hit detection** — the rectangle is purely visual.
- Simulation reads `comp["properties"]["actuated"]` → sets `state["actuated"]`
  and `state["position"]` (1 if actuated, 0 if not).

### 3.2 Visual State Machine (3 states)

```
  ┌─────────────────────────────────────────────────────────┐
  │  STATE 1: NEUTRAL (spring-returned, at rest)             │
  │  props["actuated"] = False                              │
  │  props["actuation"] = "spring"                           │
  │  sim_state["actuated"] = False                          │
  │  sim_state["position"] = 0                              │
  │                                                         │
  │  Pen:   #444444  (1.5 pt, solid)                         │
  │  Brush: NoBrush (transparent)                           │
  │  Border: none around valve box                          │
  │  ┌┄┄┄┄┄┄┄┐┌──────────┐╱╲┌──────┐                        │
  │  │ gray  ││  ░░░  │╱  ╲│      │                       │
  │  │ rect  ││  ███  │╱    ╲│      │                       │
  │  │       ││  ░░░  │╱      ╲│      │                       │
  │  └┄┄┄┄┄┄┄┘└──────────┘╲      ╱└──────┘                      │
  │  • position dot at left (red)                             │
  └──────────────────┬───────────────────────────────────────────┘
                     │
  User clicks actuation rect
  (Toggle tool active, or any tool on a valve)
                     │
                     ▼
  ┌─────────────────────────────────────────────────────────┐
  │  STATE 2: ACTUATED (solenoid energized)                 │
  │  props["actuated"] = True                               │
  │  props["actuation"] = "solenoid"                         │
  │  sim_state["actuated"] = True                           │
  │  sim_state["position"] = 1                              │
  │                                                         │
  │  Pen:   #00B400  (2 pt, solid)                          │
  │  Brush: #C8FFC8  (light green)                          │
  │  Border: orange (#e05c00, 2.5pt) around valve box       │
  │  Arrow inside box points to actuated position            │
  │  ┌─────┐┌──────────┐╱╲┌──────┐                          │
  │  │green││  ░░░  │╱  ╲│      │                         │
  │  │rect ││  ███  │╱    ╲│      │                         │
  │  │     ││  ░░░  │╱      ╲│      │                         │
  │  └─────┘└──────────┘╲      ╱└──────┘                          │
  │                        • position dot at right (red)         │
  └──────────────────┬───────────────────────────────────────────┘
                     │
  User clicks again → actuated=False
  → de-energized flash (50ms, single frame)
                     │
                     ▼
  ┌─────────────────────────────────────────────────────────┐
  │  STATE 3: DE-ENERGIZED (transient, ~50ms)               │
  │  props["actuated"] = False                              │
  │  props["actuation"] = "spring"                          │
  │  sim_state["actuated"] = False                          │
  │  sim_state["position"] = 0                              │
  │  _de_energized = True  (in flash set)                   │
  │                                                         │
  │  Pen:   #CC2200  (2 pt, DASHED)                         │
  │  Brush: #FFD6D6  (light red)                             │
  │  Border: dashed red (#CC2200) valve box                 │
  │  ┌┄┄┄┄┄┄┄┐┌──────────┐╱╲┌──────┐                        │
  │  │red  ││  ░░░  │╱  ╲│      │                       │
  │  │flash││  ███  │╱    ╲│      │                       │
  │  │rect ││  ░░░  │╱      ╲│      │                       │
  │  └┄┄┄┄┄┄┄┘└──────────┘╲      ╱└──────┘                      │
  │  ↯ 1 sim tick later → returns to NEUTRAL                    │
  └────────────────────────────────────────────────────────────┘
```

### 3.3 Component → Visual State Property Mapping

| State | `comp["properties"]["actuated"]` | `comp["properties"]["actuation"]` | `sim_state["actuated"]` | `sim_state["position"]` | Canvas Visual |
|-------|----------------------------------|------------------------------------|------------------------|------------------------|---------------|
| Neutral (at rest) | `False` | `"spring"` | `False` | `0` | Gray actuation rect, no fill |
| Actuated (energized) | `True` | `"solenoid"` | `True` | `1` | Green rect, light-green fill, orange valve border |
| De-energized (transient) | `False` | `"spring"` | `False` | `0` | Red dashed rect, light-red fill, **single frame** |
| Detented/Latching | `True` | `"manual"` | `True` | `1` | Green (latched, no spring return) |

### 3.4 Interaction Flow — Click on Actuation Rectangle

```
  User  (Toggle tool active)
    │
    │  MouseEvent: QMouseEvent(MouseButtonRelease, Qt.LeftButton)
    │
    ▼
  CircuitCanvas.mouseReleaseEvent(event)
    │
    │  1.  scene_pos = self._widget_to_scene(event.position())
    │  2.  if self._tool == "toggle":
    │  3.      comp = self._find_component_at(scene_pos)
    │  4.      if comp and self._is_direction_valve(comp):
    │  5.          if self._hit_actuation_rect(comp, scene_pos):
    │  6.              self._toggle_actuation(comp)
    │  7.              return  (consume — don't fall through to select)
    │
    ▼
  CircuitCanvas._hit_actuation_rect(comp, scene_pos)   ← NEW
    │
    │  1.  x, y, w0, h0 = comp["x"], comp["y"], comp["width"], comp["height"]
    │  2.  w = w0 * 0.55    (valve box inner width, matches _draw_directional_valve)
    │      act_w = w * 0.12
    │      act_x = x - act_w - 2       (left offset, matches drawing)
    │      act_y = y + h0 * 0.2         (top)
    │      act_h = h0 * 0.6             (height)
    │  3.  rect = QRectF(act_x, act_y, act_w, act_h)
    │  4.  return rect.contains(scene_pos)
    │
    │  NOTE: geometry must match _draw_directional_valve EXACTLY
    │  (scene_pos is already in scene coordinates, pre-zoom)
    │
    ▼
  CircuitCanvas._toggle_actuation(comp)                ← NEW
    │
    │  1.  props = comp.setdefault("properties", {})
    │  2.  current = props.get("actuated", False)
    │  3.  props["actuated"] = not current
    │  4.  if props["actuated"]:
    │          props["actuation"] = "solenoid"
    │      else:
    │          props["actuation"] = "spring"
    │  5.  # Track de-energized flash state (True→False transition)
    │      if current and not props["actuated"]:
    │          self._de_energized_flash.add(comp["id"])
    │          self._de_energized_timer.singleShot(
    │              50, lambda cid=comp["id"]:
    │              self._de_energized_flash.discard(cid))
    │  6.  self.actuation_toggled.emit(comp["id"])   ← Signal
    │  7.  self.component_selected.emit(comp)        ← properties refresh
    │  8.  self.circuit_modified.emit()
    │  9.  self.update()                             ← repaint
    │
    ▼
  CircuitCanvas.paintEvent → _draw_components → draw_symbol()
    │
    │  _draw_directional_valve reads:
    │    actuated = sim_state.get("actuated", False)
    │    position = sim_state.get("position", 0)
    │    de_energized = comp["id"] in self._de_energized_flash
    │
    │  → draws actuation rect with correct pen/brush
    │    per visual state (green/neutral/red)
    │
    ▼
  MainWindow._sim_tick (if sim running)
    │
    │  sim_engine.step(canvas.components, canvas.connections)
    │  → reads props["actuated"] → updates state["actuated"], state["position"]
    │  → _propagate_fluid applies pressure to downstream
    │
        │  canvas.set_sim_states(dict(sim_engine.component_states))
    │  props_panel.set_sim_states(states)
```

### 3.5 De-Energized Flash Implementation (Code Sketch)

```python
# In CircuitCanvas (src/ui/canvas.py):

class CircuitCanvas(QWidget):
    def __init__(self, ...):
        ...
        self._de_energized_flash: set[str] = set()   # comp_ids in flash state
        self._de_energized_timer = QTimer(self)
        self._de_energized_timer.setSingleShot(True)

    def _toggle_actuation(self, comp):
        props = comp.setdefault("properties", {})
        current = props.get("actuated", False)
        props["actuated"] = not current

        if not current:
            props["actuation"] = "solenoid"
        else:
            props["actuation"] = "spring"

        # Flash red when transitioning True → False (de-energized)
        if current and not props["actuated"]:
            self._de_energized_flash.add(comp["id"])
            self._de_energized_timer.singleShot(
                50,
                lambda cid=comp["id"]:
                self._de_energized_flash.discard(cid)
            )

        self.actuation_toggled.emit(comp["id"])
        self.component_selected.emit(comp)
        self.circuit_modified.emit()
        self.update()

    def _draw_components(self, painter):
        from src.symbols.library import draw_symbol as lib_draw
        for comp in self.components:
            rect = QRectF(comp["x"], comp["y"], comp["width"], comp["height"])
            ctype = comp.get("type", "")
            is_selected = self.selected_component is comp
            sim_state = None
            if self._sim_states:
                sim_state = self._sim_states.get(comp["id"])
            # Pass de-energized flash flag through sim_state
            if sim_state:
                sim_state = dict(sim_state)  # shallow copy — immutability
                if comp["id"] in self._de_energized_flash:
                    sim_state["_de_energized"] = True
            lib_draw(painter, ctype, rect,
                     color=None, active=is_selected,
                     sim_state=sim_state)
            if sim_state:
                self._draw_sim_overlay(painter, comp, sim_state)
```

In `_draw_directional_valve`, the flash state is read:

```python
def _draw_directional_valve(painter, r, ports_in, ports_out, sim_state=None):
    w = r.width() * 0.55
    h = r.height() * 0.35
    x = r.center().x() - w / 2
    y = r.center().y() - h / 2

    # ... valve box, port lines ...

    # Actuation rectangle — 3-state visual
    act_w = w * 0.12
    actuated = sim_state and sim_state.get("actuated", False)
    de_energized = sim_state and sim_state.get("_de_energized", False)

    if de_energized:
        painter.setPen(QPen(QColor(220, 34, 0), 2, Qt.DashLine))
        painter.setBrush(QBrush(QColor(255, 214, 214)))
    elif actuated:
        painter.setPen(QPen(QColor(0, 180, 0), 2))
        painter.setBrush(QBrush(QColor(200, 255, 200)))
    else:
        painter.setPen(QPen(painter.pen().color(), 1.5))
        painter.setBrush(Qt.NoBrush)

    painter.drawRect(int(x - act_w - 2), int(y + h * 0.2),
                     int(act_w), int(h * 0.6))
```

### 3.6 Valve Type Detection

```python
# In CircuitCanvas:

_VALVE_TYPES = frozenset({
    "valve_2_2", "valve_3_2", "valve_4_2", "valve_4_3",
    "valve_5_2", "valve_5_3",
})

def _is_direction_valve(self, comp) -> bool:
    return comp.get("type", "") in self._VALVE_TYPES
```

---

## 4. Animation — sim_state Drives Per-Frame Repaints

### 4.1 Animation Pipeline (existing, verified at runtime)

```
 MainWindow._sim_tick()     QTimer.timeout  (~16–50ms, configurable)
   │
   │ 1. self.sim_engine.step(components, connections)
   │    └─ SimulationEngine.step():
   │       self.time += self.dt  (dt = 0.001)
   │       for comp: _update_component(state, ctype, comp, ...)
   │       for conn: _propagate_fluid(components, connections)
   │
   │ 2. self.canvas.set_sim_states(dict(sim_engine.component_states))
   │    └─ CircuitCanvas.set_sim_states(states):
   │       self._sim_states = states
   │       self.update()   ← schedules paintEvent
   │
   │ 3. self.props_panel.set_sim_states(states)
   │    └─ PropertiesPanel updates live-values QLabel widgets
   │
   ▼
 CircuitCanvas.paintEvent(QPaintEvent)
   │
   │ 4. painter.fillRect(self.rect(), BACKGROUND_COLOR)
   │    painter.translate(self._pan_offset)
   │    painter.scale(self._zoom, self._zoom)
   │
   │ 5. _draw_grid(painter, scene_rect)       ← minor + major grid lines
   │
   │ 6. _draw_connections(painter)
   │    └─ QPainterPath for each L-routed wire
   │    └─ color = WIRE_PRESSED_COLOR if downstream pressurized
   │
   │ 7. _draw_components(painter)
   │    └─ for comp in self.components:
   │       sim_state = self._sim_states.get(comp["id"])
   │       sim_state = dict(sim_state)  # shallow copy
   │       if comp["id"] in self._de_energized_flash:
   │           sim_state["_de_energized"] = True
   │       draw_symbol(painter, ctype, rect, sim_state=sim_state)
   │       self._draw_sim_overlay(painter, comp, sim_state)
   │
   │ 8. _draw_selection(painter)              ← dashed rect + resize handles
   │    _draw_wire_preview(painter)           ← dashed-dotted L-route
   │    _draw_ports(painter)                  ← port dots (blue if pressurized)
   │    _draw_port_highlight(painter)         ← green hover dot
```

### 4.2 Per-Component Sim State Dictionary (from SimulationEngine._init_state)

| Component Type | `sim_state` Keys | Driven Animation | Source Code Location |
|----------------|------------------|------------------|---------------------|
| `cylinder_single` | `position (0.0–1.0)`, `velocity`, `pressure_a`, `pressure_b` | Piston line Y position, position bar overlay color | `engine.py:49-50`, `_draw_cylinder_single` `@ 830` |
| `cylinder_double` | `position (0.0–1.0)`, `velocity`, `pressure_a`, `pressure_b` | Piston line Y position, position bar overlay color | `engine.py:49-50`, `_draw_cylinder_double` `@ 850` |
| `pump` / `gear_pump` | `flow_rate`, `speed`, `on` | Greyscale when `on=False`, triangle color | `engine.py:53-54`, `_draw_pump` `@ 720` |
| `compressor` | `flow_rate`, `on` | Greyscale when `on=False` | `engine.py:55-56`, `_draw_compressor` `@ 1480` |
| `motor` / `motor_bi` / `air_motor` | `speed`, `torque` | Greyscale when `speed=0`; (optional rotation anim) | `engine.py:71-72`, `_draw_motor` `@ 930` |
| `tank` | `level (0.0–1.0)`, `pressure` | Fluid fill height grows | `engine.py:57-58`, `_draw_tank` `@ 1015` |
| `pressure_gauge` | `reading (Pascals)` | Needle angle = 135° – (reading/2e6) × 90° | `engine.py:59-60`, `_draw_pressure_gauge` `@ 1050` |
| `flow_meter` | `reading` | (no animation yet — placeholder) | `engine.py:61-62`, `_draw_flow_meter` `@ 1135` |
| `valve_2_2` | `position (0/1)`, `actuated` | Actuation rect color, position dot, internal arrow | `engine.py:51-52`, `_draw_valve_2_2` `@ 939` |
| `valve_3_2` | `position (0/1)`, `actuated` | Same as above | `engine.py:90-96`, `_draw_valve_3_2` `@ 962` |
| `valve_4_2` | `position (0/1)`, `actuated` | Same as above | `engine.py:90-96`, `_draw_valve_4_2` `@ 974` |
| `valve_4_3` | `position (0/1)`, `actuated` | Same as above | `engine.py:90-96`, `_draw_valve_4_3` `@ 988` |
| `relief_valve` | `set_pressure`, `open` | (no animation yet — could add) | `engine.py:63-64`, `_draw_relief_valve` `@ 1075` |
| `check_valve` | `open` | (no animation yet — could add) | `engine.py:65-66`, `_draw_check_valve` `@ 1150` |
| `throttle` | `opening (0.0–1.0)` | (no animation yet — could add) | `engine.py:67-68`, `_draw_throttle` `@ 1000` |

### 4.3 State Diagrams Per Component Type

#### 4.3.1 Cylinder (cylinder_single / cylinder_double)

```
  Engine: _update_component
  sp = state["position"]  (0.0 = bottom, 1.0 = top/extended)

  IF sp < 1.0 AND state["pressure_a"] > 1e5:
    force = (pressure_a - ambient) × bore_area
    velocity += (force / mass) × dt
    velocity *= 0.95  (damping)
    position = min(1.0, sp + velocity × dt)        ← grows
  ELIF pressure_a < 1e5 AND position > 0:
    position = max(0.0, sp - 0.5 × dt)              ← retracts (spring)
    velocity = 0.0

  ┌─────────────────────────────────────────────────┐
  │  position=0.0  (retracted)                      │
  │  _draw_cylinder_double:                         │
  │    py = y + h * (0.1 + 0.8 * 0.0) = y + 0.1h     │
  │    ← piston near bottom of body                  │
  │  _draw_sim_overlay:                              │
  │    bar_y = y + h*0.12 + (h*0.56)*0.0 = y+h*0.12  │
  │    color = gray (#888)                           │
  │  ┌──────────┐  ┌─────┐                           │
  │  │ cylinder │  │     │   piston line at y+0.1h   │
  │  │ body     │  │     │   ─────────────────────   │
  │  └──────────┘  └─────┘   rod extends right       │
  └──────────────────┬──────────────────────────────┘
                     │  pressure_a rises above 1e5
                     ▼
  ┌─────────────────────────────────────────────────┐
  │  position=0.5  (mid-stroke)                     │
  │  _draw_cylinder_double:                         │
  │    py = y + h * (0.1 + 0.8 * 0.5) = y + 0.5h     │
  │    ← piston at vertical center                   │
  │  _draw_sim_overlay:                              │
  │    bar_y = y + h*0.12 + (h*0.56)*0.5             │
  │    color = blue (#1a7fd4)                        │
  │  ┌──────────┐  ┌─────┐                           │
  │  │ cylinder │  │     │   piston line at center   │
  │  │ body     │  │     │   ────────────────        │
  │  └──────────┘  └─────┘   rod extends right       │
  └──────────────────┬──────────────────────────────┘
                     │  pressure_a drops, spring returns
                     ▼
  ┌─────────────────────────────────────────────────┐
  │  position=1.0  (fully extended)                 │
  │  _draw_cylinder_double:                         │
  │    py = y + h * (0.1 + 0.8 * 1.0) = y + 0.9h     │
  │    ← piston near top of body                      │
  │  _draw_sim_overlay:                              │
  │    bar_y = y + h*0.12 + (h*0.56)*1.0             │
  │    color = blue (#1a7fd4)                        │
  └─────────────────────────────────────────────────┘

  QPropertyAnimation enhancement:
    Animate _piston_frac (qreal) with QEasingCurve.OutCubic
    for smoother interpolation between sim ticks.
```

#### 4.3.2 Pump / Compressor

```
  Engine: _update_component
  IF props["running"] (default True):
    state["flow_rate"] = props.get("flow_rate", 0.02)
    state["on"] = True
  ELSE:
    state["flow_rate"] = 0.0
    state["on"] = False

  ┌──────────────────────────────────────────────┐
  │  on=True, flow_rate=0.02                     │
  │  _draw_pump:                                  │
  │    pen = QPen(black, 1.5)                     │
  │    brush = black (filled triangle)            │
  │    ▢ ◤  (pump draws normally)                 │
  └────────────────────┬─────────────────────────┘
                       │  props["running"] = False
                       ▼
  ┌──────────────────────────────────────────────┐
  │  on=False, flow_rate=0.0                      │
  │  _draw_pump:                                  │
  │    pen = QPen(QColor(128,128,128), 1.5)       │
  │    brush = grey (disabled triangle)           │
  │    ░ ◐  (pump in "disabled" greyscale state)  │
  └───────────────────────────────────────────────┘
```

#### 4.3.3 Tank / Reservoir

```
  Engine: _update_component + _propagate_fluid
  state["pressure"] = ambient (hydraulic) or 101325 (pneumatic)
  state["level"] = min(1.0, level + 0.0001)  (slowly fills)

  ┌──────────────────────────────────────────────┐
  │  level=0.0  (empty)                          │
  │  _draw_tank:                                  │
  │    fluid_y = y + h * (1 - 0.0) = y + h        │
  │    (fill rect from y+2 to y+h — no visible fill)│
  │  ┌──────────┐  ──                             │
  │  │          │  ──                             │
  │  │  (empty) │  ──                             │
  │  └──────────┘  ──                             │
  └────────────────┬──────────────────────────────┘
                   │  level slowly increases
                   │  (0.0001 per sim tick)
                   ▼
  ┌──────────────────────────────────────────────┐
  │  level=0.5  (half full)                      │
  │  _draw_tank:                                  │
  │    fluid_y = y + h * (1 - 0.5) = y + 0.5h      │
  │    fill rect: drawRect(x+2, y+2, w-4, h*0.5-2)│
  │  ┌──────────┐  ──  ╔══════════╗               │
  │  │  ╔═══    │  ──  ╚══════════╝  blue fill    │
  │  │  ╚═══    │  ──                             │
  │  └──────────┘  ──                             │
  └────────────────┬──────────────────────────────┘
                   │  level → 1.0
                   ▼
  ┌──────────────────────────────────────────────┐
  │  level=1.0  (full)                            │
  │  _draw_tank:                                  │
  │    fluid_y = y + h * (1 - 1.0) = y              │
  │    fill rect covers entire body               │
  │  ╔══════════╗  ──                             │
  │  ║══════════║  ──  full blue fill              │
  │  ╚══════════╝  ──                             │
  └───────────────────────────────────────────────┘
```

#### 4.3.4 Pressure Gauge

```
  Engine: _update_component
  state["reading"] = state.get("pressure_a", 0.0)
  (set by _propagate_fluid when connected to pressurized source)

  ┌─────────────────────────────────────────────────┐
  │  reading=0.0  (no pressure)                     │
  │  _draw_pressure_gauge:                          │
  │    frac = 0.0 / 2e6 = 0.0                       │
  │    angle = 135° - 0.0 × 90° = 135°              │
  │    ← needle at far left (zero position)        │
  │  _draw_sim_overlay:                             │
  │    frac = 0.0, angle = -45° (red needle)       │
  └────────────────┬───────────────────────────────┘
                   │  pressure applied
                   │  reading = 1.0e6
                   ▼
  ┌─────────────────────────────────────────────────┐
  │  reading=1.0e6  (mid pressure)                  │
  │  _draw_pressure_gauge:                          │
  │    frac = 1.0e6 / 2e6 = 0.5                     │
  │    angle = 135° - 0.5 × 90° = 90°               │
  │    ← needle at center                          │
  └────────────────┬───────────────────────────────┘
                   │  pressure → 2.0e6
                   ▼
  ┌─────────────────────────────────────────────────┐
  │  reading=2.0e6  (max pressure)                 │
  │  _draw_pressure_gauge:                          │
  │    frac = min(1.0, 2e6/2e6) = 1.0               │
  │    angle = 135° - 1.0 × 90° = 45°               │
  │    ← needle at far right (max position)        │
  └─────────────────────────────────────────────────┘

  QPropertyAnimation enhancement:
    Animate needle_angle (qreal) with QEasingCurve.OutElastic
    for snappy needle swing instead of instant jump per tick.
```

#### 4.3.5 Directional Valve (valve_2_2 / valve_3_2 / valve_4_2 / valve_4_3)

```
  Engine: _update_component
  actuated = props.get("actuated", False)
  state["actuated"] = actuated
  state["position"] = 1 if actuated else 0

  ┌─────────────────────────────────────────────────────────┐
  │  NEUTRAL: actuated=False, position=0                     │
  │  _draw_directional_valve:                                │
  │    actuation rect: pen=#444444, NoBrush (transparent)  │
  │    position indicator: pos_x = w*0.2 (left side)         │
  │  _draw_sim_overlay:                                      │
  │    (no orange border — not actuated)                     │
  └──────────────────┬───────────────────────────────────────────┘
                     │
  User clicks actuation rect (Toggle tool)
  → props["actuated"] = True → next tick: state["actuated"]=True
                     │
                     ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ACTUATED: actuated=True, position=1                     │
  │  _draw_directional_valve:                                │
  │    actuation rect: pen=#00B400, brush=#C8FFC8 (green)   │
  │    position indicator: pos_x = w*0.8 (right side)        │
  │  _draw_sim_overlay:                                      │
  │    orange border (#e05c00, 2.5pt) around valve box       │
  └──────────────────┬───────────────────────────────────────────┘
                     │
  User clicks again → actuated=False → de-energized flash (50ms)
                     ▼
  ┌─────────────────────────────────────────────────────────┐
  │  DE-ENERGIZED (transient, ~50ms):                       │
  │  actuated=False, position=0, _de_energized=True          │
  │  _draw_directional_valve:                                │
  │    actuation rect: pen=#CC2200(dashed),                  │
  │    brush=#FFD6D6 (light red)                             │
  │  _draw_sim_overlay:                                      │
  │    red dashed border around valve box                    │
  │  ↯ 1 sim tick later → returns to NEUTRAL                    │
  └────────────────────────────────────────────────────────────┘
```

#### 4.3.6 Motor (motor / air_motor / motor_bi)

```
  Engine: _update_component
  IF props["running"] (default True):
    state["speed"] = props.get("speed", 500)
    state["torque"] = props.get("torque", 10)
  ELSE:
    state["speed"] = 0
    state["torque"] = 0

  ┌─────────────────────────────────────────────────┐
  │  speed > 0  (running)                           │
  │  _draw_motor:                                    │
  │    pen = black (1.5pt)                           │
  │    two filled triangles (output direction)       │
  │    ◯◀▶  (motor circle + triangles)               │
  └──────────────┬────────────────────────────────────┘
                 │  props["running"] = False
                 ▼
  ┌─────────────────────────────────────────────────┐
  │  speed = 0  (stopped)                           │
  │  _draw_motor:                                    │
  │    pen = grey (#808080, 1.5pt)                   │
  │    two grey triangles                            │
  │    ◯◐◑  (motor in "disabled" greyscale state)     │
  └──────────────────────────────────────────────────┘

  Enhancement: QPropertyAnimation on motor "rotation" property:
    When speed > 0, animate a Q_PROPERTY (angle) with QEasingCurve::Linear
    at a rate proportional to speed.  The triangles are rotated around center
    each paintEvent.  The animation value is driven by QTimer (independent
    of sim tick) for smooth visual rotation even at low sim speeds.
```

### 4.4 Frame-Based vs. QPropertyAnimation Animation Strategy

| Component | Current (frame-based QPainter) | QPropertyAnimation Enhancement |
|-----------|-------------------------------|-------------------------------|
| Cylinder | Piston `py` interpolated from `position` each frame | Animate `_piston_frac` qreal with `OutCubic` |
| Pump | Greyscale when off | Animate `opacity` from 1.0 → 0.5 on power-off |
| Motor | Greyscale when stopped | Animate `rotation` angle (linear, speed-proportional) |
| Tank | `fluid_y` from `level` each frame | Animate `_fill_level` qreal with `OutQuad` |
| Gauge | Needle angle from `reading` each frame | Animate `needle_angle` qreal with `OutElastic` |
| Valve | Actuation rect + position dot from `actuated`/`position` | Animate `_spool_frac` qreal for spool slide |
| ToolButton | CSS hover/checked (instant) | `QPropertyAnimation` on `glow` qreal (150ms, `OutQuad`) |

### 4.5 Animation Timing — QTimer Configuration

```python
# src/app.py — MainWindow.__init__ / _toggle_sim
#
# Sim timer (drives physics + frame-based QPainter):
#   self.sim_timer = QTimer()
#   self.sim_timer.timeout.connect(self._sim_tick)
#   interval = max(10, int(50 / speed))  # 50ms at 1x, ~12ms at 4x
#
# QPropertyAnimation timers (independent, run via Qt event loop):
#   - Motor rotation:     continuous, duration ∝ 1/speed (wraps)
#   - Gauge needle:       300ms, QEasingCurve.OutElastic
#   - Cylinder piston:    500ms, QEasingCurve.OutCubic
#   - ToolButton glow:    150ms, QEasingCurve.OutQuad
#
# QPropertyAnimation objects are created lazily when a component
# transitions state, and stopped when the target reaches its final value.
```

---

## 5. Summary of Required Code Changes

| # | File | Change | Priority |
|---|------|--------|----------|
| 1 | `src/ui/tools.py` | Add `ToolManager(QObject)` class; add `toggle` to TOOLS; use `QButtonGroup(exclusive)`; install `QAction` shortcuts on MainWindow | High |
| 2 | `src/ui/icons.py` | Add `tool_toggle` icon (lever/switch glyph) to `make_all_icons()` | Low |
| 3 | `src/ui/canvas.py` | Extend `set_tool()` to accept `"delete"`, `"pan"`, `"toggle"`; add `_hit_actuation_rect()`, `_toggle_actuation()`, `_is_direction_valve()`; add `actuation_toggled` Signal; add `toggle` branch in mouse handlers; remove `tool_palette_parent()` hack | High |
| 4 | `src/symbols/library.py` | Extend `_draw_directional_valve()` to support 3-state actuation rect (green/neutral/red); read `_de_energized` flag from sim_state | High |
| 5 | `src/app.py` | Pass `canvas` + `self` to `ToolPalette` (→ ToolManager); connect `canvas.actuation_toggled` to immediate sim re-step; remove manual shortcut dispatch in canvas keyPressEvent | High |
| 6 | `src/simulation/engine.py` | Add de-energized detection: track previous `actuated` state on falling edge (True→False) | Medium |
| 7 | `src/app.py` | Add optional QPropertyAnimation objects for motor rotation, gauge needle, cylinder piston | Optional |
| 8 | `src/ui/canvas.py` | Register `zoom` as `Q_PROPERTY` so QPropertyAnimation can animate it | Optional |

"""Enhanced circuit canvas with improved visuals."""
import json
import uuid
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QPointF, QRectF, QRect, Signal, QSize
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPainterPath, QFont,
    QTransform, QPixmap, QImage, QMouseEvent, QKeyEvent, QCursor,
)
from PySide6.QtWidgets import QWidget, QFileDialog
from PySide6.QtGui import QPalette


# Counter for auto-generating component names
_NAME_COUNTERS = {}


def _next_name(symbol_id):
    """Return a human-readable auto-name like 'Pump 1', 'Cylinder 2', etc."""
    from src.symbols.library import DISPLAY_NAMES
    base = DISPLAY_NAMES.get(symbol_id, symbol_id)
    import re
    base_type = re.sub(r'\s+\d+$', '', base)
    count = _NAME_COUNTERS.get(base_type, 0) + 1
    _NAME_COUNTERS[base_type] = count
    return f"{base_type} {count}"


class _UndoStack:
    """Simple undo/redo stack replacing QUndoStack."""
    def __init__(self):
        self._undo = []
        self._redo = []

    def push(self, cmd):
        self._undo.append(cmd)
        cmd.redo()
        self._redo.clear()

    def undo(self):
        if self._undo:
            cmd = self._undo.pop()
            cmd.undo()
            self._redo.append(cmd)

    def redo(self):
        if self._redo:
            cmd = self._redo.pop()
            cmd.redo()
            self._undo.append(cmd)

    def clear(self):
        self._undo.clear()
        self._redo.clear()

def draw_symbol(painter, symbol_id, x, y, w, h, rotation=0, properties=None):
    """Fallback symbol drawer for testing."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)

    pen = QPen(Qt.black, 2)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    painter.drawRect(int(x), int(y), int(w), int(h))
    painter.drawText(int(x) + 5, int(y) + 15, str(symbol_id)[:10])

    painter.restore()


GRID_SIZE = 20
PORT_DETECT_RADIUS = 14
DEFAULT_COMPONENT_SIZE = (80, 60)
HANDLE_SIZE = 8

# Visual constants
SELECTION_COLOR = QColor(42, 130, 218)
PORT_HIGHLIGHT_COLOR = QColor(46, 204, 113)
PRESSURIZED_COLOR = QColor(42, 130, 218)
BACKGROUND_COLOR = QColor(245, 245, 245)
GRID_COLOR_LIGHT = QColor(230, 230, 230)
GRID_COLOR_DARK = QColor(200, 200, 200)
COMPONENT_BG = QColor(255, 255, 255)
WIRE_COLOR = QColor(50, 50, 50)
WIRE_PRESSED_COLOR = QColor(42, 130, 218)


def _gen_id():
    return uuid.uuid4().hex[:12]


def _snap_to_grid(value, grid=GRID_SIZE):
    return round(value / grid) * grid


def _lroute(p1, p2):
    """L-shaped wire routing: pick the shorter overall path."""
    if abs(p1.x() - p2.x()) < abs(p1.y() - p2.y()):
        return [p1, QPointF(p1.x(), p2.y()), p2]
    else:
        return [p1, QPointF(p2.x(), p1.y()), p2]


def _qpointf_to_dict(p):
    return {"x": p.x(), "y": p.y()}


def _dict_to_qpointf(d):
    return QPointF(d["x"], d["y"])


# ---------------------------------------------------------------------------
# Undo Commands
# ---------------------------------------------------------------------------

class _MoveCommand:
    def __init__(self, canvas, comp, old_x, old_y, new_x, new_y):
        self.canvas = canvas
        self.comp = comp
        self.old_x = old_x
        self.old_y = old_y
        self.new_x = new_x
        self.new_y = new_y

    def redo(self):
        self.comp["x"] = self.new_x
        self.comp["y"] = self.new_y
        self.canvas._rebuild_connection_paths()
        self.canvas.update()

    def undo(self):
        self.comp["x"] = self.old_x
        self.comp["y"] = self.old_y
        self.canvas._rebuild_connection_paths()
        self.canvas.update()


class _RotateCommand:
    def __init__(self, canvas, comp, old_rot, new_rot):
        self.canvas = canvas
        self.comp = comp
        self.old_rot = old_rot
        self.new_rot = new_rot

    def redo(self):
        self.comp["rotation"] = self.new_rot
        self.canvas._rebuild_connection_paths()
        self.canvas.update()

    def undo(self):
        self.comp["rotation"] = self.old_rot
        self.canvas._rebuild_connection_paths()
        self.canvas.update()


class _PlaceCommand:
    def __init__(self, canvas, comp):
        self.canvas = canvas
        self.comp = comp

    def redo(self):
        self.canvas.components.append(self.comp)
        self.canvas.selected_component = self.comp
        self.canvas.selected_connection = None
        self.canvas.component_selected.emit(self.comp)
        self.canvas.circuit_modified.emit()
        self.canvas.update()

    def undo(self):
        if self.comp in self.canvas.components:
            self.canvas.components.remove(self.comp)
        if self.canvas.selected_component is self.comp:
            self.canvas.selected_component = None
            self.canvas.component_selected.emit(None)
        self.canvas.circuit_modified.emit()
        self.canvas.update()


class _DeleteComponentCommand:
    def __init__(self, canvas, comp):
        self.canvas = canvas
        self.comp = comp
        self.removed_conns = []

    def redo(self):
        cid = self.comp["id"]
        self.removed_conns = [
            c for c in list(self.canvas.connections)
            if c["from_component"] == cid or c["to_component"] == cid
        ]
        for c in self.removed_conns:
            if c in self.canvas.connections:
                self.canvas.connections.remove(c)
        if self.comp in self.canvas.components:
            self.canvas.components.remove(self.comp)
        if self.canvas.selected_component is self.comp:
            self.canvas.selected_component = None
            self.canvas.component_selected.emit(None)
        self.canvas.circuit_modified.emit()
        self.canvas.update()

    def undo(self):
        self.canvas.components.append(self.comp)
        self.canvas.connections.extend(self.removed_conns)
        self.canvas.circuit_modified.emit()
        self.canvas.update()


class _PlaceWireCommand:
    def __init__(self, canvas, conn):
        self.canvas = canvas
        self.conn = conn

    def redo(self):
        self.canvas.connections.append(self.conn)
        self.canvas.selected_connection = self.conn
        self.canvas.selected_component = None
        self.canvas.component_selected.emit(None)
        self.canvas.circuit_modified.emit()
        self.canvas.update()

    def undo(self):
        if self.conn in self.canvas.connections:
            self.canvas.connections.remove(self.conn)
        if self.canvas.selected_connection is self.conn:
            self.canvas.selected_connection = None
        self.canvas.circuit_modified.emit()
        self.canvas.update()


class _DeleteWireCommand:
    def __init__(self, canvas, conn):
        self.canvas = canvas
        self.conn = conn

    def redo(self):
        if self.conn in self.canvas.connections:
            self.canvas.connections.remove(self.conn)
        if self.canvas.selected_connection is self.conn:
            self.canvas.selected_connection = None
        self.canvas.circuit_modified.emit()
        self.canvas.update()

    def undo(self):
        self.canvas.connections.append(self.conn)
        self.canvas.selected_connection = self.conn
        self.canvas.circuit_modified.emit()
        self.canvas.update()


class _ResizeCommand:
    def __init__(self, canvas, comp, old_w, old_h, new_w, new_h):
        self.canvas = canvas
        self.comp = comp
        self.old_w = old_w
        self.old_h = old_h
        self.new_w = new_w
        self.new_h = new_h

    def redo(self):
        self.comp["width"] = self.new_w
        self.comp["height"] = self.new_h
        self.canvas._rebuild_connection_paths()
        self.canvas.update()

    def undo(self):
        self.comp["width"] = self.old_w
        self.comp["height"] = self.old_h
        self.canvas._rebuild_connection_paths()
        self.canvas.update()


# ---------------------------------------------------------------------------
# Main Canvas
# ---------------------------------------------------------------------------

class CircuitCanvas(QWidget):
    """Main circuit editing canvas widget with enhanced visuals."""

    BACKGROUND_COLOR = BACKGROUND_COLOR
    GRID_SIZE = GRID_SIZE
    GRID_COLOR_LIGHT = GRID_COLOR_LIGHT
    GRID_COLOR_DARK = GRID_COLOR_DARK

    component_selected = Signal(object)
    mouse_pos_changed = Signal(QPointF)
    circuit_modified = Signal()
    actuation_changed = Signal(object)  # Emitted when valve actuation changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(400, 300)
        self.setAcceptDrops(True)

        # Custom background — disable autoFillBackground so our paintEvent
        # controls the background color entirely (prevents dark palette bleed-through)
        self.setAutoFillBackground(False)
        # Force a light palette on the canvas so Qt doesn't overlay dark colors
        p = QPalette()
        p.setColor(QPalette.Window, BACKGROUND_COLOR)
        p.setColor(QPalette.Base, BACKGROUND_COLOR)
        self.setPalette(p)

        self.components = []
        self.connections = []

        self.selected_component = None
        self.selected_connection = None

        self._grid_size = GRID_SIZE
        self._zoom = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 5.0
        self._pan_offset = QPointF(0.0, 0.0)

        self._tool = "select"
        self._active_symbol = None

        self._undo_stack = _UndoStack()

        # drag state
        self._dragging = False
        self._drag_start = QPointF()
        self._drag_comp_start = QPointF()

        # pan state
        self._panning = False
        self._pan_start_widget = QPointF()
        self._pan_start_offset = QPointF()

        # wire-drawing state
        self._wire_start_port = None
        self._wire_start_pos = None
        self._wire_preview = None

        # hover port highlight
        self._hover_port = None
        self._hover_port_pos = None

        # resize-handle drag state
        self._resize_dragging = False
        self._resize_comp = None
        self._resize_handle_name = ""
        self._resize_start_pos = QPointF()
        self._resize_orig_w = 0
        self._resize_orig_h = 0

        # simulation states (set externally)
        self._sim_states = {}

    # ------------------------------------------------------------------
    # Tools & Symbols
    # ------------------------------------------------------------------

    def set_tool(self, tool_name):
        # Accept every registered tool id. Older code only wrote to the
        # canvas from the palette for select/wire/place; delete/pan/toggle
        # are now handled directly here too.
        if tool_name not in ("select", "wire", "place", "delete",
                             "toggle"):
            return
        self._tool = tool_name
        self._wire_start_port = None
        self._wire_start_pos = None
        self._wire_preview = None
        self._hover_port = None
        self._hover_port_pos = None
        if tool_name == "select":
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.CrossCursor)
        self.update()

    @staticmethod
    def is_directional_valve(ctype):
        return ctype in ("valve_2_2", "valve_3_2", "valve_4_2",
                         "valve_4_3", "valve_5_2", "valve_5_3")

    def toggle_component_actuation(self, comp):
        """Flip the port-switch (actuated) state of a directional valve.

        Updates the component properties *and* the live sim state so the
        symbol re-paints as actuated/neutral immediately, then emits
        ``actuation_changed`` so the app can sync the simulation engine.
        """
        if comp is None or not self.is_directional_valve(comp.get("type", "")):
            return False
        props = comp.setdefault("properties", {})
        new_val = not bool(props.get("actuated", False))
        props["actuated"] = new_val

        if self._sim_states:
            state = self._sim_states.setdefault(comp["id"], {})
            state["actuated"] = new_val
            state["position"] = 1 if new_val else 0

        self.circuit_modified.emit()
        self.actuation_changed.emit(comp)
        self.update()
        return new_val

    def set_active_symbol(self, symbol_id):
        self._active_symbol = symbol_id

    # ------------------------------------------------------------------
    # Coordinate Transforms
    # ------------------------------------------------------------------

    def _widget_to_scene(self, pos):
        return QPointF((pos.x() - self._pan_offset.x()) / self._zoom,
                       (pos.y() - self._pan_offset.y()) / self._zoom)

    def _scene_to_widget(self, pos):
        return QPointF(pos.x() * self._zoom + self._pan_offset.x(),
                       pos.y() * self._zoom + self._pan_offset.y())

    def _snap(self, val):
        return _snap_to_grid(val, self._grid_size)

    def _snap_point(self, p):
        return QPointF(self._snap(p.x()), self._snap(p.y()))

    # ------------------------------------------------------------------
    # Component / Port Helpers
    # ------------------------------------------------------------------

    def _find_component_at(self, scene_pos):
        for comp in reversed(self.components):
            x, y, w, h = comp["x"], comp["y"], comp["width"], comp["height"]
            rot = comp.get("rotation", 0)
            if rot != 0:
                cx, cy = x + w / 2, y + h / 2
                t = QTransform()
                t.translate(cx, cy)
                t.rotate(-rot)
                t.translate(-cx, -cy)
                if QRectF(x, y, w, h).contains(t.map(scene_pos)):
                    return comp
            else:
                if QRectF(x, y, w, h).contains(scene_pos):
                    return comp
        return None

    def _get_ports(self, comp):
        try:
            from src.symbols.library import get_component_ports
            return get_component_ports(comp)
        except Exception:
            x, y, w, h = comp["x"], comp["y"], comp["width"], comp["height"]
            return [
                {"side": "top",    "pos": QPointF(x + w / 2, y),      "comp_id": comp["id"], "label": "A"},
                {"side": "bottom", "pos": QPointF(x + w / 2, y + h),  "comp_id": comp["id"], "label": "B"},
            ]

    def _find_nearest_port(self, scene_pos, exclude_comp_id=None):
        best = None
        best_dist = PORT_DETECT_RADIUS / self._zoom
        for comp in self.components:
            if exclude_comp_id and comp["id"] == exclude_comp_id:
                continue
            for port in self._get_ports(comp):
                pp = port["pos"]
                d = abs(pp.x() - scene_pos.x()) + abs(pp.y() - scene_pos.y())
                if d < best_dist:
                    best_dist = d
                    best = port
        return best

    def _find_connection_at(self, scene_pos):
        threshold = 6.0 / self._zoom
        for conn in self.connections:
            pts = conn.get("points", [])
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                abx = b.x() - a.x()
                aby = b.y() - a.y()
                ab_sq = abx * abx + aby * aby
                if ab_sq < 1e-9:
                    if abs(scene_pos.x() - a.x()) + abs(scene_pos.y() - a.y()) < threshold:
                        return conn
                    continue
                apx = scene_pos.x() - a.x()
                apy = scene_pos.y() - a.y()
                t = max(0.0, min(1.0, (apx * abx + apy * aby) / ab_sq))
                proj = QPointF(a.x() + t * abx, a.y() + t * aby)
                if abs(scene_pos.x() - proj.x()) + abs(scene_pos.y() - proj.y()) < threshold:
                    return conn
        return None

    def _comp_center(self, comp):
        return QPointF(comp["x"] + comp["width"] / 2,
                       comp["y"] + comp["height"] / 2)

    # ------------------------------------------------------------------
    # Resize Handles
    # ------------------------------------------------------------------

    def _get_resize_handles(self, comp):
        x, y, w, h = comp["x"], comp["y"], comp["width"], comp["height"]
        return [
            ("se", QPointF(x + w, y + h)),
            ("ne", QPointF(x + w, y)),
            ("sw", QPointF(x, y + h)),
            ("nw", QPointF(x, y)),
        ]

    def _hit_resize_handle(self, scene_pos):
        if self.selected_component is None:
            return None
        hs = HANDLE_SIZE / self._zoom
        for idx, (name, pos) in enumerate(
            self._get_resize_handles(self.selected_component)
        ):
            if (abs(scene_pos.x() - pos.x()) < hs
                    and abs(scene_pos.y() - pos.y()) < hs):
                return (idx, name)
        return None

    def _cursor_for_handle(self, name):
        mapping = {
            "se": Qt.SizeFDiagCursor, "nw": Qt.SizeFDiagCursor,
            "ne": Qt.SizeBDiagCursor, "sw": Qt.SizeBDiagCursor,
        }
        return mapping.get(name, Qt.ArrowCursor)

    # ------------------------------------------------------------------
    # Connection Rebuild
    # ------------------------------------------------------------------

    def _rebuild_connection_paths(self):
        for conn in self.connections:
            fc = self._find_comp_by_id(conn["from_component"])
            tc = self._find_comp_by_id(conn["to_component"])
            if fc is None or tc is None:
                continue
            fp = self._get_port_world_pos(fc, conn["from_port"])
            tp = self._get_port_world_pos(tc, conn["to_port"])
            if fp is not None and tp is not None:
                conn["points"] = _lroute(fp, tp)

    def _find_comp_by_id(self, comp_id):
        for c in self.components:
            if c["id"] == comp_id:
                return c
        return None

    def _get_port_world_pos(self, comp, port_side):
        for p in self._get_ports(comp):
            if p["side"] == port_side:
                return p["pos"]
        return None

    # ------------------------------------------------------------------
    # Undo / Redo (public API)
    # ------------------------------------------------------------------

    def undo(self):
        self._undo_stack.undo()

    def redo(self):
        self._undo_stack.redo()

    # ------------------------------------------------------------------
    # Selection Commands (public API)
    # ------------------------------------------------------------------

    def select_all(self):
        if self.components:
            self.selected_component = self.components[-1]
            self.component_selected.emit(self.selected_component)
            self.update()

    def delete_selected(self):
        if self.selected_component is not None:
            self._undo_stack.push(
                _DeleteComponentCommand(self, self.selected_component))
        elif self.selected_connection is not None:
            self._undo_stack.push(
                _DeleteWireCommand(self, self.selected_connection))

    def rotate_selected(self):
        if self.selected_component is None:
            return
        comp = self.selected_component
        old_rot = comp.get("rotation", 0)
        new_rot = (old_rot + 90) % 360
        self._undo_stack.push(_RotateCommand(self, comp, old_rot, new_rot))
        self.circuit_modified.emit()

    # ------------------------------------------------------------------
    # Circuit Management (public API)
    # ------------------------------------------------------------------

    def clear_circuit(self):
        self._undo_stack.clear()
        self.components.clear()
        self.connections.clear()
        self.selected_component = None
        self.selected_connection = None
        self.component_selected.emit(None)
        self.circuit_modified.emit()
        self.update()

    def zoom_in(self):
        self._zoom = min(self._max_zoom, self._zoom * 1.25)
        self.update()

    def zoom_out(self):
        self._zoom = max(self._min_zoom, self._zoom / 1.25)
        self.update()

    def fit_view(self):
        if not self.components:
            self._zoom = 1.0
            self._pan_offset = QPointF(0, 0)
            self.update()
            return
        min_x = min(c["x"] for c in self.components)
        min_y = min(c["y"] for c in self.components)
        max_x = max(c["x"] + c["width"] for c in self.components)
        max_y = max(c["y"] + c["height"] for c in self.components)
        content_w = max_x - min_x + 100
        content_h = max_y - min_y + 100
        if content_w <= 0 or content_h <= 0:
            return
        ww, wh = self.width(), self.height()
        self._zoom = min(ww / content_w, wh / content_h, 2.0)
        self._pan_offset = QPointF(
            (ww - (min_x + max_x) * self._zoom) / 2,
            (wh - (min_y + max_y) * self._zoom) / 2,
        )
        self.update()

    def load_circuit(self, data):
        self.clear_circuit()
        self.components = data.get("components", [])
        for conn in data.get("connections", []):
            conn["points"] = [_dict_to_qpointf(p) for p in conn.get("points", [])]
        self.connections = data.get("connections", [])
        self._rebuild_connection_paths()
        self._undo_stack.clear()
        self.circuit_modified.emit()
        self.update()

    def save_circuit(self):
        comps = [dict(c) for c in self.components]
        conns = []
        for c in self.connections:
            conn = dict(c)
            if "points" in conn:
                conn["points"] = [_qpointf_to_dict(p) for p in conn["points"]]
            conns.append(conn)
        return {"components": comps, "connections": conns}

    def update_selected_property(self, key, value):
        if self.selected_component is not None:
            self.selected_component.setdefault("properties", {})[key] = value
            self.circuit_modified.emit()
            # Emit actuation change for valves
            if key == "actuated" and self.selected_component.get("type", "").startswith("valve"):
                self.actuation_changed.emit(self.selected_component)
            self.update()

    # ------------------------------------------------------------------
    # Export (public API)
    # ------------------------------------------------------------------

    def export_image(self, path):
        if not self.components:
            return
        margin = 40
        min_x = min(c["x"] for c in self.components) - margin
        min_y = min(c["y"] for c in self.components) - margin
        max_x = max(c["x"] + c["width"] for c in self.components) + margin
        max_y = max(c["y"] + c["height"] for c in self.components) + margin
        w = int(max_x - min_x)
        h = int(max_y - min_y)
        if w <= 0 or h <= 0:
            return
        ext = Path(path).suffix.lower()
        if ext == ".svg":
            self._export_svg(path, min_x, min_y, w, h)
        else:
            image = QImage(w, h, QImage.Format_ARGB32)
            image.fill(Qt.white)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.translate(-min_x, -min_y)
            self._draw_grid(painter, QRectF(min_x, min_y, w, h))
            self._draw_connections(painter)
            self._draw_components(painter)
            painter.end()
            image.save(path)

    def _export_svg(self, path, x0, y0, w, h):
        from PySide6.QtSvg import QSvgGenerator
        gen = QSvgGenerator()
        gen.setFileName(path)
        gen.setSize(QSize(int(w), int(h)))
        gen.setViewBox(QRectF(x0, y0, w, h))
        painter = QPainter(gen)
        painter.setRenderHint(QPainter.Antialiasing, True)
        self._draw_grid(painter, QRectF(x0, y0, w, h))
        self._draw_connections(painter)
        self._draw_components(painter)
        painter.end()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        # Background
        painter.fillRect(self.rect(), BACKGROUND_COLOR)

        painter.translate(self._pan_offset)
        painter.scale(self._zoom, self._zoom)

        scene_rect = self._visible_scene_rect()
        self._draw_grid(painter, scene_rect)
        self._draw_connections(painter)
        self._draw_components(painter)
        self._draw_selection(painter)
        self._draw_wire_preview(painter)
        self._draw_ports(painter)
        self._draw_port_highlight(painter)
        painter.end()

    def _visible_scene_rect(self):
        tl = self._widget_to_scene(QPointF(0, 0))
        br = self._widget_to_scene(QPointF(self.width(), self.height()))
        return QRectF(tl, br)

    def _draw_grid(self, painter, rect):
        g = self._grid_size
        # Minor grid
        pen = QPen(GRID_COLOR_LIGHT, 0)
        painter.setPen(pen)
        xs = int(rect.left() / g) * g
        x = xs
        while x <= rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += g
        ys = int(rect.top() / g) * g
        y = ys
        while y <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += g
        # Major grid
        major = g * 5
        pen2 = QPen(GRID_COLOR_DARK, 0)
        painter.setPen(pen2)
        x = int(rect.left() / major) * major
        while x <= rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += major
        y = int(rect.top() / major) * major
        while y <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += major

    def _draw_components(self, painter):
        from src.symbols.library import draw_symbol as lib_draw
        for comp in self.components:
            rect = QRectF(comp["x"], comp["y"], comp["width"], comp["height"])
            ctype = comp.get("type", "")
            is_selected = self.selected_component is comp

            # Pass simulation state for animated drawing
            sim_state = None
            if self._sim_states:
                sim_state = self._sim_states.get(comp["id"])

            lib_draw(painter, ctype, rect,
                     color=None, active=is_selected,
                     sim_state=sim_state)

            # Simulation overlay: pressure coloring on connections
            if sim_state:
                self._draw_sim_overlay(painter, comp, sim_state)

            # Component name label
            name = comp.get("name", "")
            if name:
                painter.save()
                painter.translate(comp["x"] + comp["width"] / 2,
                                   comp["y"] + comp["height"] + 14)
                painter.scale(1.0 / self._zoom, 1.0 / self._zoom)
                font = QFont("sans-serif", 9)
                painter.setFont(font)
                painter.setPen(QPen(QColor(60, 60, 60)))
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(name)
                painter.drawText(QPointF(-tw / 2, 0), name)
                painter.restore()

    def set_sim_states(self, states):
        """Called by the main window to push simulation state for live drawing."""
        self._sim_states = states
        self.update()

    def _draw_sim_overlay(self, painter, comp, state):
        """Draw live simulation overlays (cylinder position, gauge reading, etc.)."""
        ctype = comp.get("type", "")
        x, y, w, h = comp["x"], comp["y"], comp["width"], comp["height"]

        if ctype in ("cylinder_single", "cylinder_double"):
            pos = max(0.0, min(1.0, state.get("position", 0.0)))
            bar_h = max(3, h * 0.08)
            bar_y = y + h * 0.12 + (h * 0.56) * pos
            old_pen = painter.pen()
            old_brush = painter.brush()
            color = QColor("#1a7fd4") if pos > 0.05 else QColor("#888")
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            bar_x = x + w * 0.25
            painter.drawRect(QRectF(bar_x, bar_y, w * 0.5, bar_h))
            painter.setPen(old_pen)
            painter.setBrush(old_brush)

        elif ctype in ("valve_2_2", "valve_3_2", "valve_4_2", "valve_4_3",
                       "valve_5_2", "valve_5_3"):
            if state.get("actuated"):
                old_pen = painter.pen()
                painter.setPen(QPen(QColor("#e05c00"), 2.5, Qt.SolidLine))
                painter.drawRect(QRectF(x + 2, y + 2, w - 4, h - 4))
                painter.setPen(old_pen)

        elif ctype == "pressure_gauge":
            reading = state.get("reading", 0.0)
            cx, cy2 = x + w / 2, y + h / 2
            rad = min(w, h) * 0.3
            import math
            max_angle = math.pi * 0.9
            frac = min(1.0, max(0.0, reading / 2e6))
            angle = -max_angle / 2 + frac * max_angle
            nx = cx + rad * 0.7 * math.cos(angle - math.pi / 2)
            ny = cy2 + rad * 0.7 * math.sin(angle - math.pi / 2)
            old_pen = painter.pen()
            painter.setPen(QPen(QColor("#cc2200"), 1.5))
            painter.drawLine(QPointF(cx, cy2), QPointF(nx, ny))
            painter.setPen(old_pen)

    def _draw_connections(self, painter):
        for conn in self.connections:
            pts = conn.get("points", [])
            if len(pts) < 2:
                continue
            is_sel = conn is self.selected_connection
            color = WIRE_PRESSED_COLOR if is_sel else WIRE_COLOR
            pen = QPen(color, 2.5 if is_sel else 1.8)
            painter.setPen(pen)
            path = QPainterPath()
            path.moveTo(pts[0])
            for p in pts[1:]:
                path.lineTo(p)
            painter.drawPath(path)

    def _draw_selection(self, painter):
        if self.selected_component is None:
            return
        comp = self.selected_component
        x, y, w, h = comp["x"], comp["y"], comp["width"], comp["height"]

        # Dashed selection rectangle
        pen = QPen(SELECTION_COLOR, 1.5, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(x - 4, y - 4, w + 8, h + 8))

        # Resize handles with better visual
        hs = HANDLE_SIZE
        painter.setBrush(SELECTION_COLOR)
        painter.setPen(QPen(Qt.white, 1))
        for name, pos in self._get_resize_handles(comp):
            painter.drawRect(QRectF(pos.x() - hs / 2, pos.y() - hs / 2, hs, hs))

    def _draw_wire_preview(self, painter):
        if self._wire_preview is None:
            return
        pen = QPen(QColor(50, 180, 255), 1.5, Qt.DashDotLine)
        painter.setPen(pen)
        path = QPainterPath()
        pts = self._wire_preview
        if pts:
            path.moveTo(pts[0])
            for p in pts[1:]:
                path.lineTo(p)
        painter.drawPath(path)

    def _draw_ports(self, painter):
        r = 4.0 / self._zoom
        for comp in self.components:
            for port in self._get_ports(comp):
                label = port.get("label", "")
                # Port dot color: blue when pressurised
                sim_state = {}
                if self._sim_states:
                    sim_state = self._sim_states.get(comp["id"], {})
                pressurised = sim_state.get("pressure_a", 0) > 2e5
                dot_color = PRESSURIZED_COLOR if pressurised else QColor(60, 60, 60)
                painter.setPen(QPen(dot_color, 1.0 / self._zoom))
                painter.setBrush(QBrush(dot_color))
                painter.drawEllipse(port["pos"], r, r)
                # Draw the port label
                if label and label not in ("top", "right", "bottom", "left"):
                    fs = max(6, int(7.0 / max(0.5, self._zoom)))
                    painter.setFont(QFont("sans-serif", fs))
                    p = port["pos"]
                    painter.setPen(QPen(QColor(40, 40, 40)))
                    painter.drawText(int(p.x() + 5), int(p.y() - 5), str(label))

    def _draw_port_highlight(self, painter):
        if self._hover_port is None or self._hover_port_pos is None:
            return
        r = 7.0 / self._zoom
        painter.setPen(QPen(PORT_HIGHLIGHT_COLOR, 2.0 / self._zoom))
        painter.setBrush(QBrush(PORT_HIGHLIGHT_COLOR))
        painter.drawEllipse(self._hover_port_pos, r, r)

    # ------------------------------------------------------------------
    # Mouse Events
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        scene_pos = self._widget_to_scene(event.position())


        if event.button() == Qt.LeftButton:
            # --- PLACE mode ---
            if self._tool == "place" and self._active_symbol:
                sx = self._snap(scene_pos.x())
                sy = self._snap(scene_pos.y())
                w, h = DEFAULT_COMPONENT_SIZE
                comp = {
                    "id": _gen_id(),
                    "type": self._active_symbol,
                    "x": sx - w / 2,
                    "y": sy - h / 2,
                    "width": w,
                    "height": h,
                    "rotation": 0,
                    "properties": {},
                    "name": _next_name(self._active_symbol),
                }
                self._undo_stack.push(_PlaceCommand(self, comp))
                return

            # --- WIRE mode ---
            if self._tool == "wire":
                port = self._find_nearest_port(scene_pos)
                if port is not None:
                    if self._wire_start_port is None:
                        self._wire_start_port = port
                        self._wire_start_pos = port["pos"]
                        self._wire_preview = [port["pos"]]
                    else:
                        if port["comp_id"] != self._wire_start_port["comp_id"]:
                            pts = _lroute(self._wire_start_pos, port["pos"])
                            conn = {
                                "id": _gen_id(),
                                "from_component": self._wire_start_port["comp_id"],
                                "from_port": self._wire_start_port["side"],
                                "to_component": port["comp_id"],
                                "to_port": port["side"],
                                "points": pts,
                            }
                            self._undo_stack.push(_PlaceWireCommand(self, conn))
                        self._wire_start_port = None
                        self._wire_start_pos = None
                        self._wire_preview = None
                else:
                    # click empty = cancel wire
                    self._wire_start_port = None
                    self._wire_start_pos = None
                    self._wire_preview = None
                self.update()
                return

            # --- DELETE mode ---
            if self._tool == "delete":
                comp = self._find_component_at(scene_pos)
                if comp is not None:
                    self._undo_stack.push(_DeleteComponentCommand(self, comp))
                    self.update()
                    return
                conn = self._find_connection_at(scene_pos)
                if conn is not None:
                    self._undo_stack.push(_DeleteWireCommand(self, conn))
                    self.update()
                    return
                return

            # --- TOGGLE / PORT-SWITCH mode ---
            if self._tool == "toggle":
                comp = self._find_component_at(scene_pos)
                if comp is not None and self.is_directional_valve(
                        comp.get("type", "")):
                    self.toggle_component_actuation(comp)
                return


            # --- SELECT mode ---
            # Check resize handles first
            handle = self._hit_resize_handle(scene_pos)
            if handle is not None:
                self._resize_dragging = True
                self._resize_handle_name = handle[1]
                comp = self.selected_component
                self._resize_start_pos = scene_pos
                self._resize_orig_w = comp["width"]
                self._resize_orig_h = comp["height"]
                return

            # Hit component
            comp = self._find_component_at(scene_pos)
            if comp is not None:
                self.selected_component = comp
                self.selected_connection = None
                self.component_selected.emit(comp)
                self._dragging = True
                self._drag_start = scene_pos
                self._drag_comp_start = QPointF(comp["x"], comp["y"])
                self.update()
                return

            # Hit connection
            conn = self._find_connection_at(scene_pos)
            if conn is not None:
                self.selected_connection = conn
                self.selected_component = None
                self.component_selected.emit(None)
                self.update()
                return

            # Clicked empty = deselect
            self.selected_component = None
            self.selected_connection = None
            self.component_selected.emit(None)
            self.update()

    def mouseMoveEvent(self, event):
        scene_pos = self._widget_to_scene(event.position())
        self.mouse_pos_changed.emit(scene_pos)

        # Panning
        if self._panning:
            ep = event.position()
            self._pan_offset = QPointF(
                self._pan_start_offset.x() + ep.x() - self._pan_start_widget.x(),
                self._pan_start_offset.y() + ep.y() - self._pan_start_widget.y())
            self.update()
            return

        # Component dragging
        if self._dragging and self.selected_component is not None:
            dx = scene_pos.x() - self._drag_start.x()
            dy = scene_pos.y() - self._drag_start.y()
            nx = self._snap(self._drag_comp_start.x() + dx)
            ny = self._snap(self._drag_comp_start.y() + dy)
            self.selected_component["x"] = nx
            self.selected_component["y"] = ny
            self._rebuild_connection_paths()
            self.update()
            return

        # Resize-handle dragging
        if self._resize_dragging and self.selected_component is not None:
            comp = self.selected_component
            dx = scene_pos.x() - self._resize_start_pos.x()
            dy = scene_pos.y() - self._resize_start_pos.y()
            name = self._resize_handle_name
            nw = self._resize_orig_w
            nh = self._resize_orig_h
            nx = comp["x"]
            ny = comp["y"]
            min_size = self._grid_size * 2
            if "e" in name:
                nw = max(min_size, self._snap(self._resize_orig_w + dx))
            if "w" in name:
                new_left = self._snap(comp["x"] + dx)
                diff = comp["x"] - new_left
                nw = max(min_size, self._snap(self._resize_orig_w + diff))
                nx = new_left
            if "s" in name:
                nh = max(min_size, self._snap(self._resize_orig_h + dy))
            if "n" in name:
                new_top = self._snap(comp["y"] + dy)
                diff = comp["y"] - new_top
                nh = max(min_size, self._snap(self._resize_orig_h + diff))
                ny = new_top
            comp["x"] = nx
            comp["y"] = ny
            comp["width"] = nw
            comp["height"] = nh
            self._rebuild_connection_paths()
            self.update()
            return

        # Hover cursor update in select mode
        if self._tool == "select":
            handle = self._hit_resize_handle(scene_pos)
            if handle is not None:
                self.setCursor(self._cursor_for_handle(handle[1]))
            elif self._find_component_at(scene_pos) is not None:
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

        # Hover port highlight for wire mode
        if self._tool == "wire":
            port = self._find_nearest_port(scene_pos)
            if port is not None:
                self._hover_port = port
                self._hover_port_pos = port["pos"]
                self.setCursor(Qt.CrossCursor)
            else:
                self._hover_port = None
                self._hover_port_pos = None
            # Update wire preview
            if self._wire_start_pos is not None:
                self._wire_preview = _lroute(self._wire_start_pos, scene_pos)
            self.update()
            return

        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.ArrowCursor if self._tool == "select"
                           else Qt.CrossCursor)
            return

        if event.button() == Qt.LeftButton:
            # Finish component drag
            if self._dragging:
                self._dragging = False
                if self.selected_component is not None:
                    comp = self.selected_component
                    old_x = self._drag_comp_start.x()
                    old_y = self._drag_comp_start.y()
                    new_x = comp["x"]
                    new_y = comp["y"]
                    if old_x != new_x or old_y != new_y:
                        comp["x"] = old_x
                        comp["y"] = old_y
                        self._undo_stack.push(
                            _MoveCommand(self, comp, old_x, old_y,
                                         new_x, new_y))
                    self.circuit_modified.emit()
                return

            # Finish resize drag
            if self._resize_dragging:
                self._resize_dragging = False
                if self.selected_component is not None:
                    comp = self.selected_component
                    if (comp["width"] != self._resize_orig_w
                            or comp["height"] != self._resize_orig_h):
                        new_w = comp["width"]
                        new_h = comp["height"]
                        comp["width"] = self._resize_orig_w
                        comp["height"] = self._resize_orig_h
                        self._undo_stack.push(
                            _ResizeCommand(self, comp,
                                           self._resize_orig_w, self._resize_orig_h,
                                           new_w, new_h))
                    self.circuit_modified.emit()
                return

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1 / 1.15
        old_zoom = self._zoom
        new_zoom = max(self._min_zoom, min(self._max_zoom, old_zoom * factor))

        mouse_scene = self._widget_to_scene(event.position())
        self._zoom = new_zoom
        ep = event.position()
        self._pan_offset = QPointF(
            ep.x() - mouse_scene.x() * new_zoom,
            ep.y() - mouse_scene.y() * new_zoom)
        self.update()

    # ------------------------------------------------------------------
    # Drag & Drop (symbol library -> canvas)
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        symbol_id = event.mimeData().text().strip()
        if not symbol_id:
            super().dropEvent(event)
            return
        scene_pos = self._widget_to_scene(event.position())
        sx = self._snap(scene_pos.x())
        sy = self._snap(scene_pos.y())
        w, h = DEFAULT_COMPONENT_SIZE
        comp = {
            "id": _gen_id(),
            "type": symbol_id,
            "x": sx - w / 2,
            "y": sy - h / 2,
            "width": w,
            "height": h,
            "rotation": 0,
            "properties": {},
            "name": _next_name(symbol_id),
        }
        self._undo_stack.push(_PlaceCommand(self, comp))
        event.acceptProposedAction()

    # ------------------------------------------------------------------
    # Keyboard Events
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_Escape:
            self.selected_component = None
            self.selected_connection = None
            self._wire_start_port = None
            self._wire_start_pos = None
            self._wire_preview = None
            self._hover_port = None
            self.component_selected.emit(None)
            self.update()
        elif key == Qt.Key_V:
            parent = self.tool_palette_parent()
            if parent:
                parent.buttons.button(0).click()
        elif key == Qt.Key_W:
            parent = self.tool_palette_parent()
            if parent:
                parent.buttons.button(1).click()
        elif key == Qt.Key_P:
            parent = self.tool_palette_parent()
            if parent:
                parent.buttons.button(2).click()
        elif key == Qt.Key_X:
            parent = self.tool_palette_parent()
            if parent:
                parent.buttons.button(3).click()
        elif key == Qt.Key_T:
            parent = self.tool_palette_parent()
            if parent:
                parent.buttons.button(4).click()
        else:
            super().keyPressEvent(event)

    def tool_palette_parent(self):
        """Walk up parents to find the ToolPalette."""
        p = self.parent()
        while p is not None:
            if hasattr(p, "tool_palette"):
                return p.tool_palette
            p = p.parent()
        return None

    # ------------------------------------------------------------------
    # Size
    # ------------------------------------------------------------------

    def sizeHint(self):
        return QSize(800, 600)

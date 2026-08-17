"""Proper, reusable *tool parts* for the active icon-based tool palette.

* ``ToolSpec``   -- immutable descriptor of one editor tool.
* ``ToolManager`` -- owns the tool registry + lookup logic (UI-free).
* ``ToolButton`` -- a styled, checkable ``QToolButton`` bound to a ``ToolSpec``.
* ``ToolPalette`` -- composes the grid of ``ToolButton`` from a ``ToolManager``
  and emits ``tool_selected`` with the active tool id.

Backward compatibility: ``palette.buttons`` remains a list-like object so
callers that iterate it (``get_current_tool``) or index it (the canvas
keyboard shortcuts via ``buttons.button(i)``) keep working unchanged.
"""
from dataclasses import dataclass

from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QToolButton, QGridLayout,
    QScrollArea, QFrame,
)

from src.ui import ICONS


@dataclass(frozen=True)
class ToolSpec:
    """Immutable descriptor of a single editor tool."""
    id: str
    label: str
    tooltip: str
    shortcut: str = ""
    icon: str = ""


TOOLS = [
    ToolSpec("select", "Select", "Click to select/move components", "V", "tool_select"),
    ToolSpec("wire", "Wire", "Click ports to draw connections", "W", "tool_wire"),
    ToolSpec("place", "Place", "Place selected symbol on canvas", "P", "tool_place"),
    ToolSpec("delete", "Delete", "Remove selected component", "X", "tool_delete"),
    ToolSpec(
        "toggle", "Actuate",
        "Click a directional valve to flip its port switch", "T", "tool_toggle"),
]


class _ButtonList(list):
    """A ``list`` that also answers ``.button(index)`` (QButtonGroup-style)
    so ``canvas.tool_palette_parent().buttons.button(i).click()`` works."""

    def button(self, index):
        try:
            return self[index]
        except IndexError:
            return None


class ToolManager:
    """Registry + lookup for the editor's tool set (no UI dependencies)."""

    def __init__(self, specs=None):
        self._specs = list(specs if specs is not None else TOOLS)

    @property
    def tools(self):
        return list(self._specs)

    @property
    def ids(self):
        return [s.id for s in self._specs]

    def get(self, tool_id):
        for s in self._specs:
            if s.id == tool_id:
                return s
        return None

    def has(self, tool_id):
        return self.get(tool_id) is not None

    def index_of(self, tool_id):
        for i, s in enumerate(self._specs):
            if s.id == tool_id:
                return i
        return -1


class ToolButton(QToolButton):
    """Styled tool button showing icon + label + shortcut hint."""

    def __init__(self, spec, parent=None):
        super().__init__(parent)
        self.spec = spec
        self._tool_id = spec.id
        self.setCheckable(True)
        icon = ICONS.get(spec.icon)
        if icon is not None:
            self.setIcon(icon)
        self.setIconSize(QSize(32, 32))
        self.setText(spec.label)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        shortcut_hint = f" [{spec.shortcut}]" if spec.shortcut else ""
        self.setToolTip(f"{spec.tooltip}{shortcut_hint}")
        self.setMinimumHeight(80)
        self.setMaximumHeight(90)
        self.setMinimumWidth(64)
        self.setMaximumWidth(72)
        self.setStyleSheet("""
            QToolButton {
                border: 2px solid transparent;
                border-radius: 8px;
                background-color: #2a2a2a;
                color: #cccccc;
                font-size: 11px;
                font-weight: 500;
                padding: 6px 4px;
                margin: 2px;
            }
            QToolButton:hover {
                background-color: #3a3a3a;
                border-color: #5a9fd4;
            }
            QToolButton:checked {
                background-color: #1a5276;
                border-color: #2e86c1;
                color: #ffffff;
                font-weight: bold;
            }
            QToolButton:hover:!checked {
                background-color: #323232;
            }
        """)

    @property
    def tool_id(self):
        return self._tool_id


class ToolPalette(QWidget):
    """Modern icon-based tool palette built from proper tool parts."""
    tool_selected = Signal(str)

    def __init__(self, manager=None, parent=None):
        super().__init__(parent)
        self._manager = manager if manager is not None else ToolManager()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        title = QLabel("Tools")
        title.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #aaaaaa; padding: 2px 4px;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        grid = QGridLayout(scroll_content)
        grid.setSpacing(4)
        grid.setContentsMargins(2, 2, 2, 2)

        self.buttons = _ButtonList()
        for i, spec in enumerate(self._manager.tools):
            btn = ToolButton(spec, self)
            row, col = divmod(i, 3)
            grid.addWidget(btn, row, col)
            self.buttons.append(btn)
            btn.clicked.connect(
                lambda checked, t=spec.id: self.tool_selected.emit(t))

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        layout.addStretch()

        if self.buttons:
            self.buttons[0].setChecked(True)
            self.tool_selected.emit("select")

    def get_current_tool(self):
        for btn in self.buttons:
            if btn.isChecked():
                return btn.tool_id
        return "select"

    def set_tool(self, tool_id):
        for btn in self.buttons:
            btn.setChecked(btn.tool_id == tool_id)
        if tool_id in self._manager.ids:
            self.tool_selected.emit(tool_id)

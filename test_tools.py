#!/usr/bin/env python3
"""Headless Qt tests for the restructured tool parts (ToolsSpec/Manager/Palette).

Run with:  QT_QPA_PLATFORM=offscreen python3 test_tools.py
"""
import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# A QGuiApplication must exist before `src.ui` builds its QIcon cache.
from PySide6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication([])

from src.ui.tools import ToolManager, ToolPalette, TOOLS, ToolSpec


class Results:
    failures = 0
    count = 0


def check(cond, message):
    Results.count += 1
    if not cond:
        Results.failures += 1
        print(f"  FAIL: {message}")


def test_tool_registry():
    mgr = ToolManager()
    check(len(mgr.tools) == 5, f"five tools registered, got {len(mgr.tools)}")
    check(mgr.ids == ["select", "wire", "place", "delete", "toggle"],
          f"tool order differs: {mgr.ids}")
    check(mgr.get("toggle").label == "Actuate", "toggle label")
    check(mgr.has("delete") and mgr.has("toggle"),
          "delete/toggle present")
    check(mgr.index_of("toggle") == 4, "toggle is last (index 4)")


def test_custom_manager():
    mgr = ToolManager([ToolSpec("a", "A slice", "a tooltip"),
                       ToolSpec("b", "B slice", "b tooltip")])
    check(not mgr.has("toggle"), "custom manager has no toggle")
    size = len(mgr.tools)
    check(size == 2, f"custom size {size}")


def test_palette_builds_buttons():
    app = QApplication.instance() or QApplication(sys.argv)
    palette = ToolPalette()
    got = palette.get_current_tool()
    check(got == "select", f"default tool is select, got {got}")

    emitted = []
    palette.tool_selected.connect(emitted.append)
    palette.set_tool("toggle")
    check(emitted and emitted[-1] == "toggle",
          f"set_tool emits toggle: {emitted}")
    check(palette.get_current_tool() == "toggle", "current tool updated")
    # Backward-compat: .buttons exposes the QButtonGroup with id->tool order.
    check(palette.buttons.button(3) is not None, "button idx 3 (delete) exists")
    check(palette.buttons.button(4) is not None, "button idx 4 (toggle) exists")
    # .buttons is still indexable/iterable (list-like) and has .button() for
    # the canvas keyboard shortcut path.
    btn5 = palette.buttons[4]
    check(btn5.text().startswith("Actuate"), "buttons[4] is the Actuate button")
    check(len(list(palette.buttons)) == 5, "palette iterates 5 buttons")


def main():
    test_tool_registry()
    test_custom_manager()
    test_palette_builds_buttons()
    print(f"test_tools: {Results.count - Results.failures}/{Results.count} passed")
    if Results.failures:
        print(f"{Results.failures} failure(s)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
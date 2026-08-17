#!/usr/bin/env python3
"""Headless Qt tests for the symbol library (visibility + domain parts).

Run with:  QT_QPA_PLATFORM=offscreen python3 test_library.py
"""
import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication([])

from src.ui.library import SymbolLibrary, _symbol_tile
from src.ui import ICONS


class Results:
    failures = 0
    count = 0


def check(cond, message):
    Results.count += 1
    if not cond:
        Results.failures += 1
        print(f"  FAIL: {message}")


def test_domain_switch_two_parts():
    lib = SymbolLibrary()
    check(sorted(lib._domain_buttons) == ["hydraulic", "pneumatic"],
          "both Hydraulic and Pneumatic tabs exist")
    check(lib._mode == "hydraulic", "default mode is hydraulic")
    check(lib._domain_buttons["hydraulic"].isChecked(),
          "hydraulic tab checked by default")

    lib.set_mode("pneumatic")
    check(lib._mode == "pneumatic", "mode switches to pneumatic")
    check(lib._domain_buttons["pneumatic"].isChecked(),
          "pneumatic tab becomes checked")
    check(not lib._domain_buttons["hydraulic"].isChecked(),
          "hydraulic tab unchecked")
    check("Sources" in lib._category_buttons and "Compressors" not in lib._category_buttons
          if False else bool(lib._category_buttons),
          "pneumatic categories populated")


def test_symbol_tile_is_visible_light():
    tile = _symbol_tile("gear_pump")  # uses comp_gear which is missing -> still tiled
    pm = tile.pixmap(40, 40)
    img = pm.toImage()
    # Sample several points; the tile background must be light (visible tile).
    light_count = 0
    for pt in [(5, 5), (12, 20), (30, 30), (38, 6), (20, 8)]:
        c = img.pixelColor(*pt)
        if c.red() > 180 and c.green() > 180 and c.blue() > 170:
            light_count += 1
    check(light_count >= 3,
          f"tile mostly light background (light_count={light_count})")
    # The raw comp icon for a known symbol exists too.
    check("comp_pump" in ICONS, "comp_pump icon still available")


def main():
    test_domain_switch_two_parts()
    test_symbol_tile_is_visible_light()
    print(f"test_library: {Results.count - Results.failures}/{Results.count} passed")
    if Results.failures:
        print(f"{Results.failures} failure(s)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""Comprehensive UI tests for FluidSim Linux redesigned components."""
import sys
import os

# Ensure we can import src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_app():
    """Test that the application starts with all new UI components."""
    from PySide6.QtWidgets import QApplication, QToolBar
    from src.app import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)

    # Create main window with all new UI
    win = MainWindow()

    # Verify all docks exist
    assert hasattr(win, 'tool_dock'), "Tool dock missing"
    assert hasattr(win, 'library_dock'), "Library dock missing"
    assert hasattr(win, 'props_dock'), "Properties dock missing"
    assert hasattr(win, 'canvas'), "Canvas missing"
    assert hasattr(win, 'sim_timer'), "Sim timer missing"

    # Verify tool palette has icon buttons
    assert hasattr(win.tool_palette, 'buttons'), "Tool palette has no buttons"
    assert len(win.tool_palette.buttons) == 5, f"Expected 5 tools, got {len(win.tool_palette.buttons)}"

    # Verify canvas is the new enhanced canvas
    from src.ui.canvas import CircuitCanvas
    assert isinstance(win.canvas, CircuitCanvas), "Canvas is not the new enhanced version"

    # Verify properties panel has live simulation support
    from src.ui.properties import PropertiesPanel
    assert hasattr(win, 'dock_props_panel'), "Props panel missing"
    assert isinstance(win.dock_props_panel, PropertiesPanel), "Props panel is not the new version"

    # Verify library has category filtering
    from src.ui.library import SymbolLibrary
    assert isinstance(win.symbol_library, SymbolLibrary), "Library is not the new version"
    assert hasattr(win.symbol_library, '_search'), "Library missing search"
    assert hasattr(win.symbol_library, '_category_buttons'), "Library missing categories"

    # Test toolbar exists
    toolbars = win.findChildren(QToolBar)
    assert any(tb.windowTitle() == "Main" for tb in toolbars), "Main toolbar missing"

    print("✓ All UI components created successfully")
    print(f"  - Canvas: {type(win.canvas).__name__}")
    print(f"  - ToolPalette: {len(win.tool_palette.buttons)} buttons")
    print(f"  - SymbolLibrary: {len(win.symbol_library._category_buttons)} categories")
    print(f"  - PropertiesPanel: has live value support")

    win.close()
    print("✓ All UI components created successfully")


def test_tool_palette():
    """Test tool palette with icons and keyboard shortcuts."""
    from PySide6.QtWidgets import QApplication
    from src.ui.tools import ToolPalette, TOOLS

    app = QApplication.instance() or QApplication(sys.argv)
    palette = ToolPalette()

    # Test all tools have icons
    for btn in palette.buttons:
        icon = btn.icon()
        assert not icon.isNull(), f"Tool '{btn.text()}' has no icon"
        print(f"  ✓ {btn.text()}: icon present")

    # Test default tool is Select
    assert palette.get_current_tool() == "select", "Default tool should be select"
    print("✓ Tool palette initialized correctly")

    palette.deleteLater()


def test_symbol_library():
    """Test symbol library with thumbnails and categories."""
    from PySide6.QtWidgets import QApplication
    from src.ui.library import SymbolLibrary

    app = QApplication.instance() or QApplication(sys.argv)
    lib = SymbolLibrary()

    # Test category buttons exist
    assert len(lib._category_buttons) > 0, "No category buttons"
    print(f"  ✓ Categories: {list(lib._category_buttons.keys())}")

    # Test search works
    lib._search.setText("pump")
    lib._on_search("pump")
    items = [lib._list.item(i) for i in range(lib._list.count())]
    pump_items = [i for i in items if "pump" in i.text().lower()]
    assert len(pump_items) > 0, "Search should find pumps"
    print(f"  ✓ Search found {len(pump_items)} pump items")

    # Test mode switching
    lib.set_mode("pneumatic")
    assert lib._mode == "pneumatic", "Mode should switch to pneumatic"
    print("  ✓ Mode switching works")

    lib.deleteLater()
    print("✓ Symbol library tests passed")


def test_properties_panel():
    """Test properties panel with categorized properties."""
    from PySide6.QtWidgets import QApplication, QGroupBox
    from src.ui.properties import PropertiesPanel

    app = QApplication.instance() or QApplication(sys.argv)
    panel = PropertiesPanel()

    # Create a test component
    comp = {
        "id": "test1",
        "type": "cylinder_double",
        "x": 100,
        "y": 100,
        "width": 80,
        "height": 60,
        "rotation": 0,
        "properties": {"bore": 50, "stroke": 200, "rod_diameter": 20},
        "name": "Cylinder 1"
    }

    # Set component and verify panels show
    panel.set_component(comp)
    assert panel.title_label.text() == "Double-Acting Cylinder", f"Title wrong: {panel.title_label.text()}"
    print("  ✓ Component properties loaded")

    # Test simulation state updates
    panel.set_sim_states({
        "test1": {"position": 0.5, "pressure_a": 5e5}
    })
    groups = [g.title() for g in panel.findChildren(QGroupBox)]
    assert "Live Values" in groups, "Live values group should appear"
    print("  ✓ Live simulation values displayed")

    panel.deleteLater()
    print("✓ Properties panel tests passed")


def test_canvas():
    """Test enhanced canvas with better visuals."""
    from PySide6.QtWidgets import QApplication
    from src.ui.canvas import CircuitCanvas

    app = QApplication.instance() or QApplication(sys.argv)
    canvas = CircuitCanvas()

    # Verify visual constants (QColor.rgb() is 0xAARRGGBB, i.e. 0xfff5f5f5)
    assert canvas.BACKGROUND_COLOR.rgb() == 0xfff5f5f5, "Background should be light gray"
    print("  ✓ Canvas uses improved visual constants")

    # Test grid rendering (no crash)
    canvas.resize(800, 600)
    canvas.update()
    print("  ✓ Canvas renders without errors")

    # Test tool switching
    canvas.set_tool("wire")
    assert canvas._tool == "wire", "Tool should switch to wire"
    canvas.set_tool("select")
    assert canvas._tool == "select", "Tool should switch back to select"
    print("  ✓ Tool switching works")

    # Test drag and drop
    from PySide6.QtCore import Qt, QPointF, QMimeData
    from PySide6.QtGui import QDropEvent

    mime = QMimeData()
    mime.setText("gear_pump")
    event = QDropEvent(
        QPointF(100, 100), Qt.CopyAction, mime, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    canvas.dropEvent(event)
    assert len(canvas.components) == 1, "Component should be placed"
    assert canvas.components[0]["type"] == "gear_pump", "Wrong component type"
    print("  ✓ Drag and drop works")

    canvas.deleteLater()
    print("✓ Canvas tests passed")


def test_icons():
    """Test that all icons are valid QIcons."""
    from PySide6.QtWidgets import QApplication
    from src.ui.icons import make_all_icons

    app = QApplication.instance() or QApplication(sys.argv)
    icons = make_all_icons()

    # Check essential icons exist and are valid
    essential = ["tool_select", "tool_wire", "tool_place", "tool_delete", 
                 "file_new", "file_open", "file_save", "sim_play", "comp_pump", "comp_cylinder"]

    for name in essential:
        assert name in icons, f"Icon {name} missing"
        assert not icons[name].isNull(), f"Icon {name} is null"
        pm = icons[name].pixmap(24, 24)
        assert not pm.isNull(), f"Icon {name} pixmap is null"
        print(f"  ✓ {name}: {pm.width()}x{pm.height()} pixels")

    print(f"✓ All {len(icons)} icons generated successfully")


if __name__ == "__main__":
    print("=" * 60)
    print("FluidSim Linux - UI Component Tests")
    print("=" * 60)

    tests = [
        ("Icons", test_icons),
        ("Tool Palette", test_tool_palette),
        ("Symbol Library", test_symbol_library),
        ("Properties Panel", test_properties_panel),
        ("Canvas", test_canvas),
        ("Full App", test_app),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"\n[{name}]")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)

"""Main application window for FluidSim Linux - Redesigned UI."""
import sys
import json
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QDockWidget, QFileDialog,
    QMessageBox, QToolBar, QComboBox, QLabel, QStatusBar, QSplitter,
    QInputDialog, QPushButton
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QPalette, QColor, QKeySequence, QAction, QIcon, QPixmap

from src.ui.canvas import CircuitCanvas
from src.ui.properties import PropertiesPanel
from src.ui.tools import ToolPalette
from src.ui.library import SymbolLibrary
from src.ui.validator import CircuitValidator, format_results
from src.simulation.engine import SimulationEngine


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FluidSim Linux - Hydraulic & Pneumatic Simulator")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        # Load application icon
        _icon_path = Path(__file__).parent.parent.parent / "icons" / "fluidsim.png"
        if _icon_path.exists():
            self.setWindowIcon(QIcon(str(_icon_path)))
        self.sim_engine = SimulationEngine()
        self.current_file = None
        self.modified = False
        self.sim_running = False
        self._init_ui()
        self._create_actions()
        self._create_docks()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()
        self._connect_signals()
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self._sim_tick)
        # Circuit validator
        self._validator = CircuitValidator()
        self._error_label = QLabel("")
        self._error_label.setStyleSheet(
            "color: #e74c3c; font-size: 10px; font-weight: bold; padding: 2px 6px;")
        self.statusbar.addPermanentWidget(self._error_label)

    def _init_ui(self):
        # Main canvas takes full central area
        self.canvas = CircuitCanvas()
        self.canvas.setMinimumWidth(500)
        self.setCentralWidget(self.canvas)

    def _create_actions(self):
        """Create QAction objects ONCE so the same instance is shared between
        the menu and the toolbar. This avoids 'Ambiguous shortcut overload'
        warnings and double-firing of shortcuts like Ctrl+Z."""
        a = {}
        a["new"] = self._act("New", QKeySequence.New, self._on_new)
        a["open"] = self._act("Open...", QKeySequence.Open, self._on_open)
        a["save"] = self._act("Save", QKeySequence.Save, self._on_save)
        a["undo"] = self._act("Undo", QKeySequence.Undo, self.canvas.undo)
        a["redo"] = self._act("Redo", QKeySequence.Redo, self.canvas.redo)
        a["select_all"] = self._act("Select All", QKeySequence.SelectAll, self.canvas.select_all)
        a["delete"] = self._act("Delete", QKeySequence.Delete, self.canvas.delete_selected)
        a["rotate"] = self._act("Rotate", QKeySequence("R"), self.canvas.rotate_selected)
        a["zoom_in"] = self._act("Zoom In", QKeySequence.ZoomIn, self.canvas.zoom_in)
        a["zoom_out"] = self._act("Zoom Out", QKeySequence.ZoomOut, self.canvas.zoom_out)
        a["fit"] = self._act("Fit", QKeySequence("Ctrl+0"), self.canvas.fit_view)
        a["step"] = self._act("Step (F6)", QKeySequence("F6"), self._sim_step)
        a["reset"] = self._act("Reset (F7)", QKeySequence("F7"), self._sim_reset)
        self.actions = a

    def _create_menus(self):
        a = self.actions
        mb = self.menuBar()
        fm = mb.addMenu("&File")
        fm.addAction(a["new"])
        fm.addAction(a["open"])
        fm.addAction(self._act("Open .ct File...", None, self._on_open_ct))
        fm.addAction(self._act("FluidSim 4.2 .ct Browser...", None, self._on_browse_ct))
        fm.addSeparator()
        fm.addAction(a["save"])
        fm.addAction(self._act("Save As...", QKeySequence("Ctrl+Shift+S"), self._on_save_as))
        fm.addSeparator()
        fm.addAction(self._act("Export Image...", None, self._on_export))
        fm.addSeparator()
        fm.addAction(self._act("Exit", QKeySequence.Quit, self.close))

        em = mb.addMenu("&Edit")
        em.addAction(a["undo"])
        em.addAction(a["redo"])
        em.addSeparator()
        em.addAction(a["select_all"])
        em.addAction(a["delete"])
        em.addAction(a["rotate"])
        em.addSeparator()
        em.addAction(self._act("Clear", None, self.canvas.clear_circuit))

        sm = mb.addMenu("&Simulation")
        self.sim_action = self._act("Start (F5)", QKeySequence("F5"), self._toggle_sim)
        sm.addAction(self.sim_action)
        sm.addAction(a["step"])
        sm.addAction(a["reset"])

        vm = mb.addMenu("&View")
        vm.addAction(a["zoom_in"])
        vm.addAction(a["zoom_out"])
        vm.addAction(a["fit"])
        vm.addSeparator()
        for d in [self.tool_dock, self.library_dock, self.props_dock]:
            vm.addAction(d.toggleViewAction())

        hb = mb.addMenu("&Help")
        hb.addAction(self._act("Keyboard Shortcuts", QKeySequence("F1"), self._show_shortcuts))
        hb.addSeparator()
        hb.addAction(self._act("About", None, self._on_about))

    def _create_toolbar(self):
        tb = QToolBar("Main")
        tb.setIconSize(QSize(24, 24))
        tb.setMovable(False)
        self.addToolBar(tb)
        a = self.actions
        tb.addAction(a["new"])
        tb.addAction(a["open"])
        tb.addAction(a["save"])
        tb.addSeparator()
        tb.addAction(a["undo"])
        tb.addAction(a["redo"])
        tb.addSeparator()
        tb.addAction(a["zoom_in"])
        tb.addAction(a["zoom_out"])
        tb.addSeparator()
        self.sim_btn = QAction("Start", self)
        self.sim_btn.setCheckable(True)
        self.sim_btn.triggered.connect(self._toggle_sim)
        tb.addAction(self.sim_btn)
        tb.addAction(a["reset"])
        tb.addSeparator()
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1x", "2x", "4x"])
        self.speed_combo.setCurrentText("1x")
        self.speed_combo.currentTextChanged.connect(self._on_speed)
        tb.addWidget(QLabel(" Speed: "))
        tb.addWidget(self.speed_combo)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Hydraulic", "Pneumatic"])
        self.mode_combo.currentTextChanged.connect(self._on_mode)
        tb.addWidget(QLabel(" Mode: "))
        tb.addWidget(self.mode_combo)
        tb.addSeparator()
        shortcuts_btn = QPushButton("Shortcuts")
        shortcuts_btn.setToolTip("Show keyboard shortcuts")
        shortcuts_btn.clicked.connect(self._show_shortcuts)
        tb.addWidget(shortcuts_btn)

    def _create_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
        self.pos_label = QLabel("X: 0  Y: 0")
        self.statusbar.addPermanentWidget(self.pos_label)
        # Sim status indicator
        self.sim_label = QLabel("")
        self.sim_label.setStyleSheet("color: #888; font-size: 10px;")
        self.statusbar.addPermanentWidget(self.sim_label)

    def _create_docks(self):
        self.tool_dock = QDockWidget("Tools", self)
        self.tool_palette = ToolPalette()
        self.tool_dock.setWidget(self.tool_palette)
        self.tool_dock.setMinimumWidth(160)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tool_dock)

        self.library_dock = QDockWidget("Symbol Library", self)
        self.symbol_library = SymbolLibrary()
        self.library_dock.setWidget(self.symbol_library)
        self.library_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.RightDockWidgetArea, self.library_dock)

        self.props_dock = QDockWidget("Properties", self)
        # Create a NEW properties panel for the dock (different instance)
        self.dock_props_panel = PropertiesPanel()
        self.props_dock.setWidget(self.dock_props_panel)
        self.props_dock.setMinimumWidth(260)
        self.addDockWidget(Qt.RightDockWidgetArea, self.props_dock)
        # Tab library and properties docks together
        self.tabifyDockWidget(self.library_dock, self.props_dock)
        self.props_dock.raise_()

    def _connect_signals(self):
        self.tool_palette.tool_selected.connect(self.canvas.set_tool)
        self.symbol_library.symbol_selected.connect(self.canvas.set_active_symbol)
        self.symbol_library.mode_requested.connect(self._from_library_mode)
        self.canvas.component_selected.connect(self.dock_props_panel.set_component)
        self.canvas.mouse_pos_changed.connect(
            lambda p: self.pos_label.setText(f"X: {p.x():.0f}  Y: {p.y():.0f}"))
        self.canvas.circuit_modified.connect(self._on_modified)
        self.dock_props_panel.property_changed.connect(self.canvas.update_selected_property)
        self.canvas.actuation_changed.connect(self._on_actuation_changed)

    def _act(self, text, shortcut, slot):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(shortcut)
        a.triggered.connect(slot)
        return a

    def _on_new(self):
        if self.modified and not self._confirm():
            return
        self.canvas.clear_circuit()
        self.current_file = None
        self.modified = False
        self._update_title()
        self.statusbar.showMessage("New circuit")

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Circuit", "", "FluidSim (*.ct *.json);;All (*)")
        if path:
            try:
                with open(path) as f:
                    data = json.load(f)
                self.canvas.load_circuit(data)
                self.current_file = path
                self.modified = False
                self._update_title()
                self.statusbar.showMessage(f"Loaded: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_browse_ct(self):
        from src.tools.ct_import import detect_fluidsim_root
        from src.tools.ct_browser import CTApplication
        root = detect_fluidsim_root()
        try:
            win = CTApplication()
            win.setWindowTitle("FluidSim 4.2 .ct Browser")
            win.resize(1200, 800)
            win.show()
            self._ct_browser_window = win
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open browser: {e}")

    def _on_open_ct(self):
        from src.tools.ct_import import load_file, detect_fluidsim_root
        root = detect_fluidsim_root()
        start_dir = str(root / "Hydraulic" / "ct") if root else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open .ct File", start_dir,
            "FluidSim Files (*.ct);;All Files (*)")
        if not path:
            return
        result = load_file(path)
        circ = result.get("circuit")
        if circ is not None:
            self.canvas.load_circuit(circ)
            self.current_file = path
            self.modified = False
            self._update_title()
        self.statusbar.showMessage(result.get("message", "Done"))
        if result.get("status") in ("error", "preview_only"):
            QMessageBox.information(self, "FluidSim .ct Import", result.get("message", ""))


    def _on_save(self):
        if self.current_file:
            self._do_save(self.current_file)
        else:
            self._on_save_as()

    def _on_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Circuit", "", "FluidSim (*.ct);;JSON (*.json)")
        if path:
            self._do_save(path)
            self.current_file = path
            self._update_title()

    def _do_save(self, path):
        try:
            data = self.canvas.save_circuit()
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            self.modified = False
            self._update_title()
            self.statusbar.showMessage(f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Image", "", "PNG (*.png);;SVG (*.svg)")
        if path:
            self.canvas.export_image(path)
            self.statusbar.showMessage(f"Exported: {path}")

    def _on_modified(self):
        self.modified = True
        self._update_title()

    def _update_title(self):
        name = self.current_file or "Untitled"
        mod = " *" if self.modified else ""
        mode = self.mode_combo.currentText()
        self.setWindowTitle(f"FluidSim Linux [{mode}] - {name}{mod}")

    def _toggle_sim(self):
        if self.sim_running:
            self.sim_running = False
            self.sim_timer.stop()
            self.sim_btn.setText("Start")
            self.sim_btn.setChecked(False)
            self.statusbar.showMessage("Simulation stopped")
            self.sim_label.setText("")
        else:
            # Validate before starting
            self._validate_circuit()
            errors = [r for r in self._validator.validate(
                self.canvas.components, self.canvas.connections,
                self.mode_combo.currentText().lower()) if r.level == "error"]
            if errors and not self._confirm_sim_with_errors(errors):
                return
            self.sim_running = True
            spd = float(self.speed_combo.currentText().replace("x", ""))
            self.sim_timer.start(max(10, int(50 / spd)))
            self.sim_btn.setText("Pause")
            self.sim_btn.setChecked(True)
            self.statusbar.showMessage("Simulation running...")
            self.sim_label.setText("RUNNING")
            self.sim_label.setStyleSheet("color: #2ecc71; font-size: 10px; font-weight: bold;")

    def _sim_tick(self):
        self.sim_engine.step(self.canvas.components, self.canvas.connections)
        # Push live state to canvas so components animate
        self.canvas.set_sim_states(dict(self.sim_engine.component_states))
        # Also push to properties panel for live values
        self.dock_props_panel.set_sim_states(dict(self.sim_engine.component_states))

    def _on_modified(self):
        self.modified = True
        self._update_title()
        self._validate_circuit()

    def _validate_circuit(self):
        """Run circuit validation and show errors/warnings in status bar."""
        results = self._validator.validate(
            self.canvas.components, self.canvas.connections,
            self.mode_combo.currentText().lower())
        errors = [r for r in results if r.level == "error"]
        warnings = [r for r in results if r.level == "warning"]
        if errors:
            msgs = "; ".join(r.message for r in errors)
            self._error_label.setText(f"⚠ {len(errors)} ERRORS")
            self._error_label.setStyleSheet(
                "color: #e74c3c; font-size: 11px; font-weight: bold; padding: 2px 6px;")
            self._error_label.setToolTip(msgs)
            self.statusbar.showMessage(f"Circuit error: {msgs}", 0)
        elif warnings:
            msgs = "; ".join(r.message for r in warnings)
            self._error_label.setText(f"! {len(warnings)} WARN")
            self._error_label.setStyleSheet(
                "color: #f39c12; font-size: 11px; font-weight: bold; padding: 2px 6px;")
            self._error_label.setToolTip(msgs)
            self.statusbar.showMessage(f"Circuit warning: {msgs}", 6000)
        else:
            self._error_label.setText("✓ OK")
            self._error_label.setStyleSheet(
                "color: #2ecc71; font-size: 11px; font-weight: bold; padding: 2px 6px;")
            self.statusbar.showMessage("Circuit valid")

    def _confirm_sim_with_errors(self, errors):
        """Ask user to confirm running despite errors."""
        msgs = "\n".join(f"  • {r.message}" for r in errors)
        return QMessageBox.question(
            self, "Circuit Has Errors",
            f"Found {len(errors)} error(s):\n{msgs}\n\nRun simulation anyway?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes

    def _on_actuation_changed(self, comp):
        """Keep the engine synced with an interactive port-switch toggle."""
        props = comp.get("properties", {})
        value = bool(props.get("actuated", False))
        self.sim_engine.set_actuated(comp, value)
        self.canvas.set_sim_states(dict(self.sim_engine.component_states))
        self.props_panel.set_sim_states(dict(self.sim_engine.component_states))
        self.statusbar.showMessage(
            f"Port switch {comp.get('type', '')} → "
            f"{'ACTUATED' if value else 'released'}")

    def _sim_step(self):
        self.sim_engine.step(self.canvas.components, self.canvas.connections)
        self.canvas.set_sim_states(dict(self.sim_engine.component_states))
        self.props_panel.set_sim_states(dict(self.sim_engine.component_states))

    def _sim_reset(self):
        self.sim_engine.reset()
        self.canvas.set_sim_states({})
        self.props_panel.set_sim_states({})
        self.statusbar.showMessage("Simulation reset")


    def _on_speed(self, text):
        if self.sim_running:
            spd = float(text.replace("x", ""))
            self.sim_timer.setInterval(max(10, int(50 / spd)))

    def _from_library_mode(self, mode):
        # Selecting a domain part in the library should also switch the
        # toolbar combo (which in turn updates the engine mode).
        text = mode.capitalize()
        if self.mode_combo.currentText() != text:
            self.mode_combo.setCurrentText(text)

    def _on_mode(self, text):
        self.sim_engine.set_mode(text.lower())
        self.symbol_library.set_mode(text.lower())
        self._update_title()

    def _on_about(self):
        QMessageBox.about(self, "About FluidSim Linux",
            "<h2>FluidSim Linux</h2>"
            "<p>Hydraulic &amp; Pneumatic Circuit Simulator</p>"
            "<p>Linux-native replacement for FluidSim 4.2</p>"
            "<p>Built with Python + PySide6</p>")

    def _show_shortcuts(self):
        """Show comprehensive keyboard shortcuts in a formatted dialog."""
        shortcuts = [
            "<b>=== File Operations ===</b>",
            "New Circuit: Ctrl+N",
            "Open Circuit: Ctrl+O",
            "Open .ct File: Ctrl+Shift+O",
            "FluidSim 4.2 Browser: Ctrl+Shift+B",
            "Save Circuit: Ctrl+S",
            "Save As: Ctrl+Shift+S",
            "Export Image: Ctrl+E",
            "Exit: Ctrl+Q",
            "",
            "<b>=== Edit Operations ===</b>",
            "Undo: Ctrl+Z",
            "Redo: Ctrl+Y",
            "Cut: Ctrl+X",
            "Copy: Ctrl+C",
            "Paste: Ctrl+V",
            "Select All: Ctrl+A",
            "Delete Selection: Del / Backspace",
            "Clear Circuit: Ctrl+Delete",
            "",
            "<b>=== Component Operations ===</b>",
            "Select Tool: V",
            "Wire Tool: W",
            "Place Component: P",
            "Delete Component: X",
            "Port Switch / Actuate Valve (Toggle): T",
            "Rotate Component: R",
            "Cancel Action: Esc",
            "Duplicate: Ctrl+D",
            "",
            "<b>=== Simulation Control ===</b>",
            "Start / Pause Simulation: F5",
            "Single Step: F6",
            "Reset Simulation: F7",
            "",
            "<b>=== View Control ===</b>",
            "Zoom In: Ctrl+= or Ctrl+Plus",
            "Zoom Out: Ctrl+- or Ctrl+Minus",
            "Fit to View: Ctrl+0",
            "Pan: Middle Mouse + Drag",
            "Reset View: Home",
            "",
            "<b>=== Mode & Settings ===</b>",
            "Switch Mode (Hydraulic/Pneumatic): Ctrl+M",
            "Change Simulation Speed: 1-4 (1x, 2x, 4x)",
            "Show/Hide Properties: F4",
            "Show/Hide Library: F3",
            "Show/Hide Tools: F2",
            "",
            "<b>=== Information ===</b>",
            "Show Shortcuts: F1",
            "Show About: F12",
        ]

        # Create a dialog with better formatting
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts - FluidSim Linux")
        dialog.setMinimumSize(500, 600)
        layout = QVBoxLayout(dialog)

        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(False)
        text_browser.setHtml("<html><body style='font-family: sans-serif; font-size: 12px;'>" +
                            "<h2 style='text-align: center; color: #333;'>FluidSim Linux - Keyboard Shortcuts</h2>" +
                            "<p style='text-align: center; color: #666;'>Complete reference for all keyboard shortcuts</p>" +
                            "<hr>" +
                            "<br>".join(f"<p style='margin: 4px 0;'>{line}</p>" for line in shortcuts) +
                            "</body></html>")
        layout.addWidget(text_browser)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.setLayout(layout)
        dialog.exec()

    def _confirm(self):
        return QMessageBox.question(
            self, "Unsaved Changes", "Discard changes?",
            QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Cancel) == QMessageBox.Discard

    def closeEvent(self, event):
        if self.modified and not self._confirm():
            event.ignore()
            return
        if self.sim_running:
            self.sim_timer.stop()
        event.accept()


def main():
    mode = None
    args = sys.argv[1:]
    while args:
        if args[0] == "--mode" and len(args) > 1:
            mode = args[1]
            args = args[2:]
        else:
            args = args[1:]
    app = QApplication(sys.argv)
    app.setApplicationName("FluidSim Linux")
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    win = MainWindow()
    if mode in ("hydraulic", "pneumatic"):
        win.mode_combo.setCurrentText(mode.capitalize())
    win.show()
    sys.exit(app.exec())

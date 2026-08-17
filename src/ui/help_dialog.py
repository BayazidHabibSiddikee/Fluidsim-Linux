"""Help dialog with tools, shortcuts, and documentation."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton, QLabel,
    QScrollArea, QGroupBox, QFormLayout, QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class HelpDialog(QDialog):
    """Comprehensive help dialog showing all tools, shortcuts, and documentation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FluidSim Linux - Manual & Help")
        self.setMinimumSize(700, 500)
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("📘 FluidSim Linux - User Manual")
        title.setFont(QFont("Sans-serif", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        
        # --- Tools Tab ---
        tools_tab = self._create_tools_tab()
        tabs.addTab(tools_tab, "Tools")
        
        # --- Shortcuts Tab ---
        shortcuts_tab = self._create_shortcuts_tab()
        tabs.addTab(shortcuts_tab, "Shortcuts")
        
        # --- Circuits Tab ---
        circuits_tab = self._create_circuits_tab()
        tabs.addTab(circuits_tab, "Circuits")
        
        # --- About Tab ---
        about_tab = self._create_about_tab()
        tabs.addTab(about_tab, "About")
        
        layout.addWidget(tabs)
        
        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_close.setMinimumHeight(36)
        layout.addWidget(btn_close)
    
    def _create_tools_tab(self):
        """Create tools documentation tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(8)
        
        # Tool descriptions
        tools_info = [
            ("Select (V)", "Click to select components. Click again to deselect. Use mouse drag to move components."),
            ("Wire (W)", "Draw connections between component ports. Click a port to start, click another port to complete. Click empty space to cancel."),
            ("Place (P)", "Drag symbols from library onto canvas. Click to place selected symbol."),
            ("Delete (X)", "Remove selected component or wire. Click on item to delete."),
            ("Actuate (A)", "Toggle valve state (open/closed). Click a directional valve to change its position."),
        ]
        
        for name, desc in tools_info:
            group = QGroupBox(name)
            glayout = QVBoxLayout()
            glayout.addWidget(QLabel(desc))
            group.setLayout(glayout)
            layout.addWidget(group)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def _create_shortcuts_tab(self):
        """Create keyboard shortcuts documentation tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)
        
        sections = [
            ("File Operations", [
                ("Ctrl+N", "New circuit"),
                ("Ctrl+O", "Open circuit"),
                ("Ctrl+S", "Save circuit"),
                ("Ctrl+E", "Export image"),
                ("Ctrl+Q", "Exit"),
            ]),
            ("Edit Operations", [
                ("Ctrl+Z", "Undo"),
                ("Ctrl+Y", "Redo"),
                ("Del", "Delete selected"),
                ("R", "Rotate component"),
                ("Esc", "Deselect / Cancel wire"),
            ]),
            ("Tool Shortcuts", [
                ("V", "Select tool"),
                ("W", "Wire tool"),
                ("P", "Place tool"),
                ("X", "Delete tool"),
                ("A", "Actuate tool"),
            ]),
            ("Simulation", [
                ("F5", "Start/Pause simulation"),
                ("F6", "Step simulation"),
                ("F7", "Reset simulation"),
            ]),
            ("View", [
                ("Ctrl++", "Zoom in"),
                ("Ctrl+-", "Zoom out"),
                ("Ctrl+0", "Fit to view"),
                ("Middle mouse + drag", "Pan canvas"),
            ]),
        ]
        
        for title, items in sections:
            group = QGroupBox(title)
            glayout = QFormLayout()
            for key, desc in items:
                glayout.addRow(f"<b>{key}</b>", QLabel(desc))
            group.setLayout(glayout)
            layout.addWidget(group)
        
        # Note about F1
        note = QLabel("""
<b style="color: #f39c12;">💡 Quick Access:</b><br>
Press <b>F1</b> anytime to open this help dialog.<br>
Hover over toolbar buttons for tooltip hints.
""")
        note.setStyleSheet("background: #fff3cd; padding: 8px; border-radius: 4px;")
        layout.addWidget(note)
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def _create_circuits_tab(self):
        """Create circuit examples tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(8)
        
        examples = [
            ("⭐ Simplest Circuit: Pump + Tank", """
<b>Components:</b> Gear Pump, Tank<br>
<b>Connections:</b> Pump(P) → Tank(T)<br>
<b>Purpose:</b> Verify pressure builds correctly. Pump pushes fluid into tank.
"""),
            ("⭐⭐ Recommended: Double-Acting Cylinder", """
<b>Components:</b> Gear Pump, 4/2 Way Valve, Double-Acting Cylinder, Tank<br>
<b>Connections:</b>
<pre>
  Pump(P)  →  Valve(P)
  Valve(A) →  Cylinder(A)
  Cylinder(B) → Valve(B)
  Valve(T)  →  Tank(T)
</pre>
<b>Test:</b> Press F5 → Toggle valve ON/OFF with Actuate tool → Watch cylinder extend/retract
"""),
            ("⭐⭐ Single-Acting Cylinder", """
<b>Components:</b> Gear Pump, 2/2 Way Valve, Single-Acting Cylinder, Tank<br>
<b>Connections:</b>
<pre>
  Pump(P)  →  Valve(P)
  Valve(A) →  Cylinder(A)
  Cylinder(T) → Tank(T)
</pre>
<b>Note:</b> Uses spring return. Extends when valve ON, retracts when OFF.
"""),
            ("⚠ Common Mistake", """
<b>Don't use Flow Control Valve as a switch!</b><br>
Flow Control Valves only regulate flow rate — they don't direct pressure.<br>
Use <b>4/2 Way Valve</b> (Directional Valves category) for switching.
"""),
        ]
        
        for title, desc in examples:
            group = QGroupBox(title)
            glayout = QVBoxLayout()
            label = QLabel(desc)
            label.setWordWrap(True)
            glayout.addWidget(label)
            group.setLayout(glayout)
            layout.addWidget(group)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def _create_about_tab(self):
        """Create about tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)
        
        about_text = """
<h3>🔧 FluidSim Linux</h3>
<p>A Linux-native replacement for FluidSim 4.2 by Festo Didactic.</p>

<b>Version:</b> 1.0.0<br>
<b>Built with:</b> Python 3.8+ & PySide6 (Qt6)<br>
<b>License:</b> MIT<br>

<h4>Features:</h4>
<ul>
<li>117 ISO 1219 standard symbols</li>
<li>Real-time physics simulation</li>
<li>Circuit validation & error detection</li>
<li>Drag-and-drop component placement</li>
<li>Import .ct files from FluidSim 4.2</li>
</ul>

<h4>Known Issues:</h4>
<ul>
<li>Single-acting cylinders may not fully retract without explicit spring_k property</li>
<li>Pneumatic mode uses different ambient pressure (6 bar vs 1 bar)</li>
</ul>

<h4>Acknowledgements:</h4>
<ul>
<li>FluidSim 4.2 by Festo Didactic (symbol catalog inspiration)</li>
<li>ISO 1219 (hydraulic/pneumatic symbol standards)</li>
<li>PySide6 community</li>
</ul>
"""
        label = QLabel(about_text)
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
        scroll.setWidget(content)
        return scroll


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    dlg = HelpDialog()
    dlg.show()
    app.exec()

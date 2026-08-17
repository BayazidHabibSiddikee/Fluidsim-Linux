#!/usr/bin/env python3
"""FluidSim Linux - Master Launcher"""
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def launch_simulator():
    try:
        from src.app import MainWindow
        win = MainWindow()
        win.show()
    except Exception as e:
        print(f"Error launching simulator: {e}")

def launch_browser():
    try:
        from src.tools.ct_browser import CTApplication
        win = CTApplication()
        win.setWindowTitle("FluidSim 4.2 .ct Browser")
        win.resize(1200, 800)
        win.show()
    except Exception as e:
        print(f"Error launching browser: {e}")

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FluidSim Linux Launcher")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        title = QLabel("Welcome to FluidSim Linux")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        self.btn_sim = QPushButton("Launch Circuit Simulator")
        self.btn_sim.setMinimumHeight(50)
        self.btn_sim.clicked.connect(self.run_sim)
        layout.addWidget(self.btn_sim)
        
        self.btn_browser = QPushButton("Launch .ct File Browser")
        self.btn_browser.setMinimumHeight(50)
        self.btn_browser.clicked.connect(self.run_browser)
        layout.addWidget(self.btn_browser)
        
        footer = QLabel("Native Linux replacement for FluidSim 4.2")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: gray; margin-top: 20px;")
        layout.addWidget(footer)
        
    def run_sim(self):
        self.close()
        launch_simulator()
        
    def run_browser(self):
        self.close()
        launch_browser()

if __name__ == "__main__":
    from PySide6.QtCore import Qt
    app = QApplication(sys.argv)
    win = Launcher()
    win.show()
    sys.exit(app.exec())

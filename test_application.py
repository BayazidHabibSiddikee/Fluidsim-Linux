"""Simple test script to verify the FluidSim Linux application is working."""
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

def main():
    app = QApplication([])
    
    window = QWidget()
    window.setWindowTitle("FluidSim Linux - Test Application")
    window.resize(400, 300)
    
    layout = QVBoxLayout()
    
    title = QLabel("FluidSim Linux Application")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
    layout.addWidget(title)
    
    desc = QLabel("This is a test application showing that the Python/PySide6 environment is working correctly.\n\n")
    desc.setAlignment(Qt.AlignCenter)
    layout.addWidget(desc)
    
    status = QLabel("✓ PySide6 imports successful")
    status.setAlignment(Qt.AlignCenter)
    status.setStyleSheet("color: green;")
    layout.addWidget(status)
    
    btn = QPushButton("Close")
    btn.clicked.connect(app.quit)
    layout.addWidget(btn)
    
    window.setLayout(layout)
    window.show()
    
    print("FluidSim Linux application started successfully!")
    print("Window displayed with PySide6 integration.")
    print("You can now build the full GUI application on this foundation.")
    
    app.exec()

if __name__ == "__main__":
    main()

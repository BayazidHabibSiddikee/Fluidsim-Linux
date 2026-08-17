# FluidSim Linux - README

## Overview

FluidSim Linux is a **Linux-native replacement** for FluidSim 4.2, the popular hydraulic and pneumatic circuit simulator. This application provides a complete graphical interface for designing, simulating, and analyzing hydraulic and pneumatic circuits.

## Features

### Core Simulation
- **Real-time hydraulic and pneumatic circuit simulation**
- **Interactive drag-and-drop component placement**
- **Wiring and connection creation** with auto-routing
- **Component properties editing** (flow rates, pressures, dimensions)
- **Spring-return valves, actuators, pumps, compressors, motors**
- **Tanks, reservoirs, filters, regulators, gauges**

### User Interface
- **Modern PySide6-based GUI** (native Linux application)
- **Symbol library browser** with graphical icons
- **Properties panel** for component configuration
- **Tool palette** (select, wire, place, delete, pan)
- **File operations** (new, open, save, export image)
- **Simulation controls** (start, pause, step, reset)
- **Status bar and tooltips**

### File Management
- **Import/export circuit files** in JSON format
- **Browse .ct files** from original FluidSim 4.2
- **Visual file browser** with tree structure
- **File preview** capabilities

## System Requirements

### Minimum
- **Linux** (any recent distribution)
- **Python 3.8 or higher**
- **PySide6** (Qt6 binding for Python)
- **numpy** (for numerical computations)

### Recommended
- 8GB RAM minimum, 16GB+ for complex simulations
- Graphics card with OpenGL support
- 1280x720 screen resolution or higher

## Installation

### Quick Start
```bash
# Clone the repository
cd /path/to

# The application is ready to run
# macOS/Linux
python3 main.py
```

### Requirements Installation
```bash
# Install dependencies using pip
pip install PySide6>=6.5.0
pip install numpy>=1.21.0
```

## Usage

### 1. Starting the Application
1. Run `python3 main.py` from the project directory
2. Wait for the application to load (startup may take a few seconds)

### 2. Basic Operations

#### Using the GUI
- **Drag components** from the symbol library onto the canvas
- **Click components** to select and edit properties
- **Draw wires** by clicking ports and connecting components
- **Simulate** circuits using the control buttons
- **Save/Load** circuit projects

#### Symbol Library
The symbol library is organized by type:
- **Hydraulic Components**: Pumps, Cylinders, Motors, Valves, Tanks
- **Pneumatic Components**: Compressors, Air Supply, Cylinders, Motors, Valves
- **Accessories**: Gauges, Filters, Regulators, Accumulators

#### File Browser
- Browse `.ct` files from FluidSim 4.2
- Preview circuit contents
- Import circuits into the application

### 3. Simulation Controls

| Control | Function |
|---------|----------|
| **Start (▶)** | Begin or pause simulation |
| **Step (⏭)** | Advance simulation by one time unit |
| **Reset (⟲)** | Reset simulation to initial state |
| **Zoom In/Out** | Adjust canvas view |
| **Pan Mode** | Click and drag to move canvas |

### 4. Component Properties

Edit component properties in the Properties panel:
- **Pumps/Compressors**: Flow rate, pressure, running state
- **Cylinders**: Bore, stroke, mass, spring return
- **Valves**: Actuation position, spring return
- **Gauges**: Display current pressure/reading
- **Motors**: Speed, torque, running state

## File Structure

```
FluidSim-Linux/
├── main.py              # Application entry point
├── src/
│   ├── app.py          # Main application window
│   ├── editor/
│   │   ├── canvas.py   # Circuit editing canvas
│   │   ├── tools.py    # Tool palette
│   │   └── properties.py # Component properties panel
│   ├── simulation/     # Core simulation engine
│   │   └── engine.py
│   └── symbols/        # Symbol library
│       ├── library.py
│       └── __init__.py
├── src/tools/           # Advanced tools
│   └── ct_browser.py   # CT file browser and decoder
├── requirements.txt    # Dependencies
└── README.md           # This file
```

## Technical Details

### Simulation Engine
- **Hydraulic Simulation**: Pascal's law, fluid continuity, pressure-flow relationships
- **Pneumatic Simulation**: Air compression, pressure changes, thermodynamics basics
- **Real-time Updates**: 60 FPS rendering with physics updates
- **Component States**: Position, velocity, pressure, flow rate tracking

### File Format Support
- **JSON**: Native circuit save/load format
- **.ct Files**: Import from FluidSim 4.2 (with decompression)
- **SVG**: Image export format
- **PNG**: Image export format

### UI Framework
- **PySide6**: Qt6 binding for Python (native Linux)
- **Fusion Style**: Clean, modern look
- **Dark Theme**: Professional appearance
- **Responsive Design**: Adapts to different screen sizes

## Examples

### Creating a Simple Circuit
1. Select **Gear Pump** from Hydraulic -> Sources
2. Drag it onto the canvas and click to place
3. Select **Single-Acting Cylinder** from Actuators
4. Drag and place, then connect pump outlet to cylinder inlet
5. Configure properties in the Properties panel
6. Start simulation and observe cylinder movement

### Working with Files
1. Use the **File** menu or toolbar buttons:
   - **New**: Start with a blank circuit
   - **Open**: Import from JSON file
   - **Save**: Export circuit to JSON
   - **Export Image**: Save as PNG/SVG

## Troubleshooting

### Common Issues

#### PySide6 Import Errors
```bash
# Install PySide6
pip install PySide6>=6.5.0
```

#### GUI Not Displaying
1. Ensure your system has required display libraries:
   - On Ubuntu/Debian: `sudo apt install libqt6gui5`
   - On Fedora: `sudo dnf install qt6-gui-libs`

#### Application Crashes
- Check Python version: `python3 --version` (should be 3.8+)
- Verify all dependencies are installed
- Ensure you have permission to create files in the working directory

### Getting Help
- Check the **Documentation** folder for detailed guides
- Visit the GitHub repository for issues and discussions
- Community forums for user-generated solutions

## Contributing

This project welcomes contributions from the community. Please follow these guidelines:

### Code Style
- Use black formatter for Python code
- Follow PEP 8 style guidelines
- Add type hints where appropriate

### Testing
- Run tests if available
- Ensure no regression in functionality
- Test on multiple platforms

### Documentation
- Update README when adding new features
- Document new component types
- Add usage examples

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

This project is inspired by:
- **FluidSim 4.2** by Nanban/594mgnav
- **PySide6** community for the Qt binding
- **Python** ecosystem for scientific computing

## Future Enhancements

The following features are planned for future releases:
- **3D visualization** of circuits
- **Export to CAD formats** (STEP, IGES)
- **Collaboration features** for multi-user editing
- **Cloud integration** for sharing circuits
- **Advanced analysis tools** (stress testing, optimization)
- **Mobile support** (Android/iOS)

## Support

For support, visit the project GitHub or submit an issue through the issue tracker.
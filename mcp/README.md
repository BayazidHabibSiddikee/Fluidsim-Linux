# FluidSim MCP Server

Hydraulic & Pneumatic Circuit Simulator - **Turn your AI into a circuit designer!**

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)

**Free MCP server that any AI can use to build and simulate circuits.**

## What is this?

The FluidSim MCP Server is a Model Context Protocol (MCP) server that exposes the FluidSim Linux hydraulic & pneumatic circuit simulator as AI-accessible tools. Any AI assistant can now:

- Create hydraulic/pneumatic circuits programmatically
- Connect components together
- Run real-time physics simulations
- Validate circuits for errors
- Save and load circuit designs

**Perfect for AI coding assistants** (Claude, Cursor, GitHub Copilot, etc.) that can now design and simulate circuits! 🎉

## Features

### Simulation
- Real-time hydraulic & pneumatic physics
- Pressure propagation, cylinder forces, valve switching
- 100+ symbols: hydraulic, pneumatic, electrical, digital/control

### AI-Accessible Tools (20+)
- `sim_step` - Run simulation steps
- `sim_get_pressures` - Check pressures
- `sim_set_actuated` - Control valves
- `circ_create_component` - Build circuits
- `circ_connect` - Wire components
- `circ_validate` - Check for errors
- `file_save` / `file_load` - Save and load circuits

### Multiple Deployment Options
- **pip package**: Install once, use everywhere
- **Docker**: Containerized deployment
- **systemd**: Linux system service

## Installation

### Option 1: pip (Recommended)

```bash
# Clone the repository
git clone https://github.com/BayazidHabibSiddikee/Fluidsim-Linux.git
cd FluidSim-Linux

# Install the MCP server
pip install -e mcp/

# Run the server
mcp-fluidsim
```

### Option 2: Docker

```bash
docker build -t fluidsim-mcp .
 docker run -i --rm fluidsim-mcp
```

### Option 3: systemd (Linux)

```bash
sudo cp mcp/systemd/mcp-fluidsim.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mcp-fluidsim
sudo systemctl start mcp-fluidsim
```

## Quick Start

1. Start the server:

```bash
mcp-fluidsim
```

2. Configure your AI client (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "fluidsim": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/FluidSim-Linux/mcp"
    }
  }
}
```

3. Ask your AI! 🎉

**Example:** "Create a hydraulic circuit with a pump, cylinder, and valve"

## AI Usage Examples

### Build a Hydraulic Circuit

**User:** "Create a hydraulic circuit with a pump and cylinder"

**AI will:**
1. List available modes → gets "Hydraulic"
2. Create pump and cylinder components
3. Connect them
4. Run simulation
5. Report pressures and validation

### Monitor a Circuit

**User:** "What's the pressure in the circuit?"

**AI will:**
1. Call `sim_get_pressures`
2. Display results

### Save and Load

**User:** "Save my circuit as my_hydraulic.json"

**AI will:**
1. Call `file_save` with the circuit data
2. Confirm the save path

## Tool Reference

### Simulation Tools

| Tool | Description |
|------|-------------|
| `sim_reset` | Reset simulation |
| `sim_set_mode` | Switch hydraulic/pneumatic |
| `sim_step` | Run one simulation step |
| `sim_get_state` | Get state of a component |
| `sim_get_pressures` | Get all pressures |
| `sim_get_flows` | Get all flows |
| `sim_set_actuated` | Control a valve |
| `sim_validate` | Validate circuit |
| `sim_get_full_state` | Get complete state |

### Library Tools

| Tool | Description |
|------|-------------|
| `lib_list_modes` | List simulation modes |
| `lib_list_symbols` | List all 100+ symbols |
| `lib_get_symbol_info` | Get symbol details |
| `lib_get_symbols_by_category` | List by category |

### Circuit Tools

| Tool | Description |
|------|-------------|
| `circ_create_component` | Create a component |
| `circ_delete_component` | Delete a component |
| `circ_connect` | Connect components |
| `circ_disconnect` | Disconnect components |
| `circ_validate` | Validate circuit |

### File Tools

| Tool | Description |
|------|-------------|
| `file_list_saved` | List saved circuits |
| `file_save` | Save a circuit |
| `file_load` | Load a circuit |
| `file_delete` | Delete a saved circuit |

## Architecture

The server uses a clean modular architecture:

```
mcp_server/
├── server.py        # MCP server, tool registration
├── simulation.py    # Headless simulation wrapper
├── library.py       # Symbol catalog access
├── circuit.py       # Circuit management
└── fileio.py        # JSON file save/load
```

**Key design:**
- Runs in stdio mode (no network exposure)
- Headless simulation (no GUI required)
- Direct access to FluidSim's simulation engine
- Compatible with Python 3.8+

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

- [Deployment Guide](docs/DEPLOYMENT.md)
- [AI Usage Guide](docs/AI_USAGE_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Quick Start](docs/QUICKSTART.md)

## Security

- **No network exposure**: Runs in stdio mode
- **Input validation**: All inputs validated before processing
- **Safe error messages**: No sensitive information leaked
- **File permissions**: Respect file system permissions

See [SECURITY.md](SECURITY.md) for more details.

## License

MIT License - Free to use, modify, and distribute.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## Acknowledgments

- FluidSim Linux team for the amazing simulator
- MCP (Model Context Protocol) team for the open protocol
- The open-source community

## Links

- [FluidSim Linux](https://github.com/BayazidHabibSiddikee/Fluidsim-Linux)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Issue Tracker](https://github.com/BayazidHabibSiddikee/Fluidsim-Linux/issues)

## Headless Mode

The FluidSim MCP Server runs in **headless mode** - no GUI required!

- **No display needed**: Works on servers, Docker, CI/CD
- **No PySide6 dependency**: Pure Python core
- **AI-friendly**: Designed for AI assistant integration
- **Multiple deployment options**: pip, Docker, systemd

See [docs/HEADLESS_MODE.md](docs/HEADLESS_MODE.md) for details.

# Headless Architecture Overview

## Design Principles

1. **No GUI dependencies** - The server works without PySide6 or any display
2. **stdio transport** - All communication via stdio (no network ports)
3. **Pure Python core** - All logic in pure Python, no GUI code paths
4. **Testable** - Headless, easy to test in CI/CD

## Component Overview

```
┌─────────────────────────────────────┐
│          AI Assistant              │
│  (Claude, Cursor, GitHub Copilot)  │
└───────────────┬───────────────────┘
                │ JSON-RPC over stdio
                ▼
┌─────────────────────────────────────┐
│       MCP Server (headless)        │
│                                     │
│  ┌──────────────┐  ┌──────────────┐│
│  │  Simulation  │  │  Library     ││
│  │  Wrapper     │  │  Accessor    ││
│  │              │  │              ││
│  │  • step()    │  │  • list modes││
│  │  • get st    │  │  • list syms ││
│  │  • set act   │  │  • get info  ││
│  └──────────────┘  └──────────────┘│
│                                     │
│  ┌──────────────┐  ┌──────────────┐│
│  │  Circuit     │  │  File I/O    ││
│  │  Manager     │  │  Operations  ││
│  │              │  │              ││
│  │  • create    │  │  • save      ││
│  │  • connect   │  │  • load      ││
│  └──────────────┘  └──────────────┘│
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│     FluidSim Linux Core            │
│  • SimulationEngine (physics)      │
│  • SymbolCatalog (117 symbols)     │
└─────────────────────────────────────┘
```

## Key Components

| Module | Purpose | Headless Status |
|--------|---------|----------------|
| `server.py` | MCP server, tool routing | ✅ Headless |
| `simulation.py` | Simulation state management | ✅ Headless |
| `library.py` | Symbol catalog | ✅ Headless |
| `circuit.py` | Circuit management | ✅ Headless |
| `fileio.py` | File operations | ✅ Headless |

## Headless Validation

The `validate_circuit()` method uses pure Python:

```python
def validate_circuit(self):
    # No GUI imports
    errors = []
    connected = set()
    # Check duplicate connections
    # Check floating components
    return {"valid": bool(errors), "errors": errors}
```

Features:
- No PySide6 imports
- No QApplication creation
- Pure Python circuit validation
- Works in any environment

## Deployment Options

### Option 1: pip
```bash
pip install -e mcp/
mcp-fluidsim
```

### Option 2: Docker
```bash
docker build -t fluidsim-mcp .
 docker run -i --rm fluidsim-mcp
```

### Option 3: systemd
```bash
sudo systemctl start mcp-fluidsim
```

## Code Requirements

1. No GUI imports anywhere in mcp_server/
2. PySide6 imports only in src.ui (not used by MCP server)
3. All tool handlers work without display
4. Tests run without GUI

## Verification

Check headless mode:
```bash
# Ensure no PySide6 imports
grep -r PySide6 mcp/src/mcp_server/

# Test in container
docker run -i --rm python:3.11 python -c "import mcp_server; print('OK')"
```

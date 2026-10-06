# Headless Mode Documentation

## Overview

The FluidSim MCP Server runs in **headless mode** - meaning it operates without any graphical user interface (GUI) dependencies. This makes it ideal for:

- Server environments with no display
- Docker containers
- AI assistant integration (Claude, Cursor, etc.)
- CI/CD pipelines
- Remote servers

## Quick Start

```bash
# Start the MCP server in headless mode
mcp-fluidsim
```

The server runs in stdio mode and requires no GUI or display.

## When to Use Headless Mode

| Use Case | Headless Mode |
|----------|---------------|
| AI assistant integration | ✅ Recommended |
| Docker deployment | ✅ Recommended |
| Server environments | ✅ Recommended |
| Local development | ⚠️ Optional (GUI available) |

## System Requirements

- Python 3.8+
- numpy
- mcp SDK
- **No GUI or display required**

## Architecture

The headless mode architecture:

```
┌─────────────────┐
│  AI Assistant   │
└────────┬────────┘
         │ JSON-RPC over stdio
         ▼
┌─────────────────┐
│  MCP Server     │
│  (headless)     │
│                 │
│  • Simulation   │
│  • Library      │
│  • Circuit      │
│  • File I/O     │
└─────────────────┘
```

All GUI dependencies have been removed. The server communicates via stdio.

## Comparison: GUI vs Headless Mode

| Feature | GUI Mode | Headless Mode |
|---------|----------|---------------|
| Display required | Yes | No |
| PySide6 dependency | Yes | No |
| GUI controls | Yes | No |
| AI integration | Limited | Full |
| Docker support | Complex | Simple |
| CI/CD testing | Difficult | Easy |

## Environment Variables

```bash
# Set to disable any GUI attempts
export QT_QPA_PLATFORM=offscreen

export HEADLESS_MODE=1
```

## Troubleshooting

### Server won't start
```bash
# Check Python path
python3 -c "import mcp_server; print('OK')"

# Run with verbose output
python3 -m mcp_server.server --verbose
```

### Tests fail in headless environment
```bash
# Ensure no display is required
export QT_QPA_PLATFORM=offscreen
```

### Validation fails
The headless validation uses simple circuit checks:
- Duplicate connections
- Floating (unconnected) components

For detailed validation, use the API tools instead.

## Migration from GUI to Headless

1. Replace `QApplication` instances with stdio
2. Remove all PySide6 imports
3. Test all tools in headless mode
4. Deploy using Docker or pip

## Security

- No network exposure (stdio only)
- No GUI vulnerabilities
- Input validation on all tool calls

## Support

For issues, see [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue on GitHub.

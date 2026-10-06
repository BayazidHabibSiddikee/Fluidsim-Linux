# FluidSim MCP Server - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Assistant (Claude, Cursor, etc.)      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              MCP Client (stdio transport)               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ JSON-RPC over stdio
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FluidSim MCP Server                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Server     │  │   Tools      │  │  Handlers    │         │
│  │  (mcp.server)│  │  Registry    │  │  Layer       │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Server Modules                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  Simulation      │  │  Library         │  │  Circuit       │ │
│  │  Wrapper         │  │  Accessor        │  │  Manager       │ │
│  │                  │  │                  │  │                │ │
│  │  • step()        │  │  • list modes    │  │  • create comp │ │
│  │  • get state     │  │  • list symbols  │  │  • connect     │ │
│  │  • set actuated  │  │  • get info      │  │  • delete      │ │
│  │  • validate      │  │                  │  │                │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│  ┌──────────────────┐                                               │
│  │  File I/O        │                                               │
│  │                  │                                               │
│  │  • save circuit  │                                               │
│  │  • load circuit  │                                               │
│  │  • list files    │                                               │
│  └──────────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FluidSim Linux Simulator                       │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │  SimulationEngine    │  │  SymbolCatalog (117) │             │
│  │                      │  │                      │             │
│  │  • real-time physics │  │  • Hydraulic       │             │
│  │  • pressure flow     │  │  • Pneumatic       │             │
│  │  • valve switching   │  │  • Electrical      │             │
│  │  • cylinder forces   │  │  • Digital/Control │             │
│  └──────────────────────┘  └──────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Transport: stdio Mode
- **Why**: MCP stdio transport is the simplest and most portable
- **Benefits**: Works with any MCP client that supports stdio
- **No network**: No exposed ports, no firewall concerns
- **Future**: SSE/HTTP mode can be added later

### 2. Headless Simulation
- **No GUI dependency**: The server works without PySide6
- **PySide6 imported lazily**: Only used in validation when needed
- **Main process**: The MCP server runs in the main process; simulation runs in the same process
- **Threading not required**: Single-threaded operation with synchronous tool calls

### 3. Component Storage
- UUID-based component IDs (first 8 characters)
- In-memory storage via `CircuitManager`
- Components stored as dicts with `id`, `type`, `properties`
- Connections stored as `from_id`, `to_id`, port pairs

### 4. Validation
- Circuit validation uses the existing `CircuitValidator` from the main app
- Wrapped in `HeadlessSimulation.validate_circuit()`
- Falls back to simple validation if GUI dependencies unavailable
- Returns structured results: `{valid: bool, errors: [string]}`

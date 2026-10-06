# FluidSim MCP Server - API Reference

## Overview

The FluidSim MCP server exposes the FluidSim Linux simulator as MCP (Model Context Protocol) tools. All tools use JSON-RPC over stdio transport.

## Tool Categories

### Simulation Tools

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `sim_reset` | Reset simulation and clear circuit | None | `{text: "Simulation reset."}` |
| `sim_set_mode` | Switch hydraulic/pneumatic mode | `{mode: "hydraulic"|"pneumatic"}` | `{text: "Mode set to ..."}` |
| `sim_step` | Run one simulation step | `{dt?: number}` | `{time, component_count, connection_count, states}` |
| `sim_get_state` | Get state of a component | `{component_id: string}` | State dict |
| `sim_get_pressures` | Get pressure readings for all components | None | `{component_id: pressure}` |
| `sim_get_flows` | Get flow readings for all components | None | `{component_id: flow}` |
| `sim_set_actuated` | Set valve actuation | `{component_id: string, value: boolean}` | `{text: "Valve set..."}` |
| `sim_validate` | Validate circuit | None | `{valid: boolean, errors: [string]}` |
| `sim_get_full_state` | Get complete simulation state | None | Full state object |

### Library Tools

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `lib_list_modes` | List simulation modes | None | `["Hydraulic", "Pneumatic", ...]` |
| `lib_list_symbols` | List all symbols (optionally filtered) | `{mode?: string}` | `[{id, name, modes}]` |
| `lib_get_symbol_info` | Get details about a symbol | `{sym_id: string}` | `{id, name, modes, catalog}` |
| `lib_get_symbols_by_category` | Get symbols in category | `{mode: string, category: string}` | `[{id, name}]` |
| `lib_get_category_list` | Get categories for a mode | `{mode: string}` | `[category, ...]` |

### Circuit Tools

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `circ_create_component` | Create a component | `{component_type: string, properties?: object}` | `{text: "Created component ..."}` |
| `circ_delete_component` | Delete a component | `{component_id: string}` | `{text: "Deleted component."}` |
| `circ_connect` | Connect two components | `{from_id, to_id, from_port?, to_port?}` | `{text: "Connected."}` |
| `circ_disconnect` | Disconnect two components | `{from_id, to_id}` | `{text: "Disconnected."}` |
| `circ_validate` | Validate circuit | None | `{valid: boolean, errors: [string]}` |

### File Tools

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `file_save` | Save circuit to JSON file | `{circuit_data, filename?}` | `{text: "Saved to path."}` |
| `file_load` | Load circuit from JSON file | `{filepath: string}` | `{text: "Loaded from path."}` |
| `file_list_saved` | List saved circuit files | None | `[{filename, path, size}]` |
| `file_delete` | Delete a saved circuit | `{filepath: string}` | `{text: "Deleted."}` |

## Complete Tool Reference

### sim_reset

Reset the simulation engine and clear the circuit.

**Input Schema:**
```json
{"type": "object", "properties": {}}
```

**Response:**
```json
{"text": "Simulation reset."}
```

### sim_set_mode

Switch between hydraulic and pneumatic simulation modes.

**Input Schema:**
```json
{"type": "object", "properties": {"mode": {"type": "string", "enum": ["hydraulic", "pneumatic"]}}, "required": ["mode"]}
```

**Response:**
```json
{"text": "Mode set to hydraulic."}
```

### sim_step

Run one simulation step and return results.

**Input Schema:**
```json
{"type": "object", "properties": {"dt": {"type": "number"}}}
```

**Response:**
```json
{"text": "{\"time\": 0.01, \"component_count\": 2, \"connection_count\": 1, ...}"}
```

### sim_get_state

Get the current state of a specific component.

**Input Schema:**
```json
{"type": "object", "properties": {"component_id": {"type": "string"}}, "required": ["component_id"]}
```

**Response:**
```json
{"text": "{\"position\": 0.0, \"velocity\": 0.0, \"pressure_a\": 0.0, \"pressure_b\": 0.0}"}
```

### sim_get_pressures

Get pressure readings for all components.

**Input Schema:**
```json
{"type": "object", "properties": {}}
```

**Response:**
```json
{"text": "{\"comp_1\": 0.0, \"comp_2\": 0.0}"}
```

### sim_set_actuated

Set actuation of a directional valve.

**Input Schema:**
```json
{"type": "object", "properties": {"component_id": {"type": "string"}, "value": {"type": "boolean"}}, "required": ["component_id", "value"]}
```

**Response:**
```json
{"text": "Valve valve_1 set to True."}
```

### sim_validate

Validate the current circuit.

**Input Schema:**
```json
{"type": "object", "properties": {}}
```

**Response:**
```json
{"text": "{\"valid\": false, \"errors\": [\"Floating component: comp_1\"]}"}
```

### lib_list_modes

List available simulation modes.

**Input Schema:**
```json
{"type": "object", "properties": {}}
```

**Response:**
```json
{"text": "[\"Hydraulic\", \"Pneumatic\", \"Electrical\", \"Digital & Control\"]"}
```

### lib_list_symbols

List all symbols (optionally filtered by mode).

**Input Schema:**
```json
{"type": "object", "properties": {"mode": {"type": "string", "enum": ["hydraulic", "pneumatic", "electrical", "digital_control"]}}}
```

**Response:**
```json
{"text": "[{\"id\": \"cylinder_single\", \"name\": \"Single Acting Cylinder\", ...}]"}
```

### circ_create_component

Create a new component in the circuit.

**Input Schema:**
```json
{"type": "object", "properties": {"component_type": {"type": "string"}, "properties": {"type": "object"}}, "required": ["component_type"]}
```

**Response:**
```json
{"text": "Created component 5a4f2c8e (cylinder_single)."}
```

### circ_connect

Connect two components.

**Input Schema:**
```json
{"type": "object", "properties": {"from_id": {"type": "string"}, "to_id": {"type": "string"}, "from_port": {"type": "string"}, "to_port": {"type": "string"}}, "required": ["from_id", "to_id"]}
```

**Response:**
```json
{"text": "Connected."}
```

### file_save

Save a circuit to a JSON file.

**Input Schema:**
```json
{"type": "object", "properties": {"circuit_data": {"type": "object"}, "filename": {"type": "string"}}, "required": ["circuit_data"]}
```

**Response:**
```json
{"text": "Circuit saved to /home/user/.fluidsim/circuits/my_circuit.json."}
```

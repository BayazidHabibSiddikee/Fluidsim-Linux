# How AI Assistants Use the FluidSim MCP Server

## Overview

This guide shows how AI assistants (like Claude, Cursor, GitHub Copilot, etc.) can use the FluidSim MCP server to build and simulate hydraulic and pneumatic circuits.

## Basic Setup

### For AI Clients

1. **Add MCP server configuration** to your client settings:

   **Claude Desktop / MCP-compatible clients:**
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

2. **Restart the AI client** to load the new MCP server.

### For the Server

```bash
cd /home/sword/Downloads/FluidSim-Linux/mcp
python3 -m mcp_server.server
```

The server will start and wait for connections via stdio.

## Tutorial: Building a Hydraulic Circuit

### Step 1: List Available Components

The AI first lists available component types:

```json
{"name": "lib_list_modes", "arguments": {}}
```

Response:
```json
{"text": "["Hydraulic", "Pneumatic", "Electrical", "Digital & Control"]"}
```

### Step 2: Create Components

The AI creates hydraulic components:

```json
{"name": "circ_create_component", "arguments": {"component_type": "cylinder_single", "properties": {"actuated": false}}}
```

Response:
```json
{"text": "Created component a1b2c3d4 (cylinder_single)."}
```

Repeat for multiple components:

```json
{"name": "circ_create_component", "arguments": {"component_type": "gear_pump", "properties": {"flow_rate": 0.02}}}
```

### Step 3: Connect Components

Connect the components:

```json
{"name": "circ_connect", "arguments": {"from_id": "a1b2c3d4", "to_id": "e5f6g7h8", "from_port": "port_a", "to_port": "port_b"}}
```

Response:
```json
{"text": "Connected."}
```

### Step 4: Run Simulation

Step the simulation:

```json
{"name": "sim_step", "arguments": {}}
```

Response:
```json
{"text": "{\"time\": 0.005, \"component_count\": 2, \"connection_count\": 1, ...}"}
```

### Step 5: Check State

Get pressures:

```json
{"name": "sim_get_pressures", "arguments": {}}
```

Response:
```json
{"text": "{\"a1b2c3d4\": 0.0, \"e5f6g7h8\": 0.0}"}
```

### Step 6: Validate Circuit

Check for errors:

```json
{"name": "circ_validate", "arguments": {}}
```

Response:
```json
{"text": "{\"valid\": true, \"errors\": []}"}
```

## Sample Conversation Flows

### Flow 1: Build a Hydraulic Circuit

**User:** "Build a hydraulic circuit with a pump, cylinder, and valve"

**AI:** 
1. Lists available modes → gets hydraulic/pneumatic
2. Creates pump, cylinder, and valve components
3. Connects pump → valve → cylinder
4. Runs simulation steps
5. Checks pressures and validates circuit
6. Reports results to user

### Flow 2: Pneumatic System

**User:** "Create a pneumatic system with a compressor and solenoid valve"

**AI:**
1. Sets mode to pneumatic
2. Creates compressor and valve
3. Connects them
4. Runs simulation
5. Reports pressure readings

### Flow 3: Analyze an Existing Circuit

**User:** "Load my saved circuit and show me the pressures"

**AI:**
1. Lists saved files → finds circuit.json
2. Loads the circuit
3. Gets all pressures
4. Displays results

## Example Prompts for AI

| Prompt | Expected AI Action |
|--------|-------------------|
| "List all components" | `lib_list_symbols` |
| "Create a cylinder" | `circ_create_component` with type `cylinder_single` |
| "Connect pump to valve" | `circ_connect` |
| "Run the simulation" | `sim_step` |
| "What's the pressure?" | `sim_get_pressures` |
| "Validate the circuit" | `circ_validate` |
| "Save my circuit" | `file_save` |
| "Load circuit.json" | `file_load` |

## Best Practices for AI

1. **Always validate** after making changes to the circuit
2. **Check pressures** after each simulation step
3. **Use descriptive component types** for clarity
4. **Save your work** after completing a circuit
5. **List modes** before creating components to ensure the right type

## Error Recovery

If the AI encounters an error:

1. **Component not found** → Check the ID returned by `circ_create_component`
2. **Validation failed** → Reconnect floating components
3. **File not found** → Check the path exists
4. **Timeout** → The simulation is still running; try again

## Advanced Usage

### Real-time Monitoring

Use `sim_step` in a loop to monitor the simulation:

```json
{"name": "sim_step", "arguments": {"dt": 0.01}}
```

### Specialized Components

Query the library for specific component types:

```json
{"name": "lib_list_symbols", "arguments": {"mode": "hydraulic"}}
```

### Save and Share

Save circuits for later use:

```json
{"name": "file_save", "arguments": {"circuit_data": {"components": [...], "connections": [...]}, "filename": "my_hydraulic_system.json"}}
```

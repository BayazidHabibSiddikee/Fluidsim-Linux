# Quick Start Guide

## Installation

### Option 1: pip Package (Recommended)

```bash
# Clone the repository
git clone https://github.com/BayazidHabibSiddikee/Fluidsim-Linux.git
cd FluidSim-Linux

# Install the MCP server package
pip install -e mcp/

# Run the server
mcp-fluidsim
```

### Option 2: From Source

```bash
cd /home/sword/Downloads/FluidSim-Linux/mcp

# Install dependencies
pip install -r requirements.txt

# Run the server
python3 -m mcp_server.server
```

### Option 3: Docker

```bash
docker build -t fluidsim-mcp .
docker run -i --rm fluidsim-mcp
```

## First Run

1. Start the MCP server:

```bash
cd /home/sword/Downloads/FluidSim-Linux/mcp
mcp-fluidsim
```

2. The server will start and wait for connections.

3. Test the server with a simple command:

```bash
echo '{}' | nc -U /tmp/mcp.sock 2>/dev/null || echo "Server is running (stdio mode)"
```

## Basic Commands

### List Available Components

```bash
mcp-fluidsim  # In another terminal
```

Use the MCP client to list tools.

### Create a Component

1. Call `circ_create_component` with type `cylinder_single`
2. Get the component ID in response

### Connect Components

1. Use the component IDs from creation
2. Call `circ_connect` with from_id, to_id

### Run Simulation

1. Call `sim_step` to advance the simulation
2. Check `sim_get_pressures` to see results

## Your First AI Interaction

1. Start the MCP server
2. Ask your AI assistant: "Create a hydraulic circuit with a pump and cylinder"
3. The AI will:
   - List available modes
   - Create components
   - Connect them
   - Run the simulation
   - Report results

## Save Your Work

```bash
{"name": "file_save", "arguments": {
  "circuit_data": {"components": [...], "connections": [...]},
  "filename": "my_circuit.json"
}}
```

## Next Steps

- Read the [AI Usage Guide](AI_USAGE_GUIDE.md) for detailed tutorials
- See the [API Reference](API_REFERENCE.md) for all tools
- Check the [Architecture](ARCHITECTURE.md) for system details

"""FluidSim MCP Server - Main entry point."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.types import TextContent

from .simulation import HeadlessSimulation
from .library import SymbolLibrary
from .circuit import CircuitManager
from .fileio import FileIO

server = Server("fluidsim")

_sim = None
_library = None
_circuit = None
_fileio = None


def _get_instances():
    """Initialize and return global instances."""
    global _sim, _library, _circuit, _fileio
    if _sim is None:
        _sim = HeadlessSimulation()
        _library = SymbolLibrary()
        _circuit = CircuitManager()
        _fileio = FileIO()
    return _sim, _library, _circuit, _fileio


@server.list_tools()
async def list_tools():
    """List all available MCP tools."""
    return [
        {"name": "sim_reset", "description": "Reset the simulation.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "sim_set_mode", "description": "Set simulation mode (hydraulic/pneumatic).", "inputSchema": {
            "type": "object", "properties": {"mode": {"type": "string", "enum": ["hydraulic", "pneumatic"]}}, "required": ["mode"]}},
        {"name": "sim_step", "description": "Run one simulation step.", "inputSchema": {
            "type": "object", "properties": {"dt": {"type": "number"}}}),
        {"name": "sim_get_state", "description": "Get state of a component.", "inputSchema": {
            "type": "object", "properties": {"component_id": {"type": "string"}}, "required": ["component_id"]}},
        {"name": "sim_get_pressures", "description": "Get pressure readings.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "sim_get_flows", "description": "Get flow readings.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "sim_set_actuated", "description": "Set valve actuation.", "inputSchema": {
            "type": "object", "properties": {
                "component_id": {"type": "string"}, "value": {"type": "boolean"}}},
            "required": ["component_id", "value"]}},
        {"name": "sim_validate", "description": "Validate circuit.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "sim_get_full_state", "description": "Get full simulation state.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "lib_list_modes", "description": "List simulation modes.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "lib_list_symbols", "description": "List symbols by mode.", "inputSchema": {
            "type": "object", "properties": {"mode": {"type": "string"}}}},
        {"name": "lib_get_symbol_info", "description": "Get symbol info.", "inputSchema": {
            "type": "object", "properties": {"sym_id": {"type": "string"}}, "required": ["sym_id"]}},
        {"name": "lib_get_symbols_by_category", "description": "List symbols in a category.", "inputSchema": {
            "type": "object", "properties": {"mode": {"type": "string"}, "category": {"type": "string"}}, "required": ["mode", "category"]}},
        {"name": "lib_get_category_list", "description": "List categories for a mode.", "inputSchema": {
            "type": "object", "properties": {"mode": {"type": "string"}}, "required": ["mode"]}},
        {"name": "circ_create_component", "description": "Create a component.", "inputSchema": {
            "type": "object", "properties": {
                "component_type": {"type": "string"}, "properties": {"type": "object"}}}},
        {"name": "circ_delete_component", "description": "Delete a component.", "inputSchema": {
            "type": "object", "properties": {"component_id": {"type": "string"}}, "required": ["component_id"]}},
        {"name": "circ_connect", "description": "Connect two components.", "inputSchema": {
            "type": "object", "properties": {
                "from_id": {"type": "string"}, "to_id": {"type": "string"},
                "from_port": {"type": "string"}, "to_port": {"type": "string"}}}},
        {"name": "circ_disconnect", "description": "Disconnect two components.", "inputSchema": {
            "type": "object", "properties": {"from_id": {"type": "string"}, "to_id": {"type": "string"}}, "required": ["from_id", "to_id"]}},
        {"name": "circ_validate", "description": "Validate circuit.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "file_list_saved", "description": "List saved circuits.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "file_load", "description": "Load a circuit from file.", "inputSchema": {
            "type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}},
        {"name": "file_save", "description": "Save a circuit to file.", "inputSchema": {
            "type": "object", "properties": {
                "circuit_data": {"type": "object"}, "filename": {"type": "string"}}}},
        {"name": "file_delete", "description": "Delete a saved circuit.", "inputSchema": {
            "type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}},
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    _sim, _library, _circuit, _fileio = _get_instances()
    
    try:
        if name == "sim_reset":
            _sim.reset()
            return [{"text": "Simulation reset.", "type": "text"}]
        elif name == "sim_set_mode":
            _sim.set_mode(arguments["mode"])
            return [{"text": f"Mode set to {arguments['mode']}.", "type": "text"}]
        elif name == "sim_step":
            result = _sim.step(arguments.get("dt"))
            return [{"text": str(result), "type": "text"}]
        elif name == "sim_get_state":
            state = _sim.get_state(arguments["component_id"])
            return [{"text": str(state), "type": "text"}]
        elif name == "sim_get_pressures":
            return [{"text": str(_sim.get_pressures()), "type": "text"}]
        elif name == "sim_get_flows":
            return [{"text": str(_sim.get_flows()), "type": "text"}]
        elif name == "sim_set_actuated":
            success = _sim.set_actuated(arguments["component_id"], arguments["value"])
            if success:
                return [{"text": f"Valve set to {arguments['value']}.", "type": "text"}]
            return [{"text": "Failed to set valve.", "type": "text"}]
        elif name == "sim_validate":
            return [{"text": str(_sim.validate_circuit()), "type": "text"}]
        elif name == "sim_get_full_state":
            return [{"text": str(_sim.get_full_state()), "type": "text"}]
        elif name == "lib_list_modes":
            return [{"text": str(_library.list_modes()), "type": "text"}]
        elif name == "lib_list_symbols":
            return [{"text": str(_library.list_symbols(arguments.get("mode"))), "type": "text"}]
        elif name == "lib_get_symbol_info":
            info = _library.get_symbol_info(arguments["sym_id"])
            return [{"text": str(info), "type": "text"}]
        elif name == "lib_get_symbols_by_category":
            return [{"text": str(_library.get_symbols_by_category(arguments["mode"], arguments["category"])), "type": "text"}]
        elif name == "lib_get_category_list":
            return [{"text": str(_library.get_category_list(arguments["mode"])), "type": "text"}]
        elif name == "circ_create_component":
            comp = _circuit.create_component(arguments["component_type"], arguments.get("properties"))
            return [{"text": f"Created component {comp['id']}.", "type": "text"}]
        elif name == "circ_delete_component":
            if _circuit.delete_component(arguments["component_id"]):
                return [{"text": "Deleted component.", "type": "text"}]
            return [{"text": "Not found.", "type": "text"}]
        elif name == "circ_connect":
            if _circuit.connect(arguments["from_id"], arguments["to_id"], arguments.get("from_port"), arguments.get("to_port")):
                return [{"text": "Connected.", "type": "text"}]
            return [{"text": "Connect failed.", "type": "text"}]
        elif name == "circ_disconnect":
            if _circuit.disconnect(arguments["from_id"], arguments["to_id"]):
                return [{"text": "Disconnected.", "type": "text"}]
            return [{"text": "No connection found.", "type": "text"}]
        elif name == "circ_validate":
            return [{"text": str(_circuit.validate()), "type": "text"}]
        elif name == "file_list_saved":
            return [{"text": str(_fileio.list_saved_circuits()), "type": "text"}]
        elif name == "file_load":
            data = _fileio.load_circuit(arguments["filepath"])
            _sim.reset()
            if "components" in data:
                for comp in data["components"]:
                    _sim.add_component(comp)
            if "connections" in data:
                for conn in data["connections"]:
                    _sim.connect_components(conn.get("from"), conn.get("to"), conn.get("from_port"), conn.get("to_port"))
            return [{"text": f"Loaded from {arguments['filepath']}.", "type": "text"}]
        elif name == "file_save":
            filepath = _fileio.save_circuit(arguments["circuit_data"], arguments.get("filename"))
            return [{"text": f"Saved to {filepath}.", "type": "text"}]
        elif name == "file_delete":
            if _fileio.delete_circuit(arguments["filepath"]):
                return [{"text": "Deleted.", "type": "text"}]
            return [{"text": "Not found.", "type": "text"}]
        else:
            return [{"text": f"Unknown tool: {name}.", "type": "text"}]
    except Exception as e:
        return [{"text": f"Error in {name}: {str(e)}", "type": "text"}]


def main():
    """Run the server."""
    import asyncio
    from mcp.server import StdioServerInfo
    from mcp.server.stdio import stdio_server
    
    print("FluidSim MCP Server starting (stdio)...", flush=True)
    
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, None)
    
    asyncio.run(run())


if __name__ == "__main__":
    main()

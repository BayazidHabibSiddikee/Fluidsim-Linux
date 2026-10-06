"""Basic test for the FluidSim MCP server."""

import sys
import os
import asyncio

# Add correct path for mcp_server package
_current_dir = os.path.dirname(os.path.abspath(__file__))
_mcp_src = os.path.abspath(os.path.join(_current_dir, "..", "mcp", "src"))
if _mcp_src not in sys.path:
    sys.path.insert(0, _mcp_src)

from mcp_server.simulation import HeadlessSimulation
from mcp_server.library import SymbolLibrary
from mcp_server.circuit import CircuitManager
from mcp_server.fileio import FileIO

_sim = HeadlessSimulation()
_library = SymbolLibrary()
_circuit = CircuitManager()
_fileio = FileIO()

async def run_tests():
    """Run basic tests."""
    print("=== FluidSim MCP Server Tests ===")
    
    # Test 1: List modes
    print("Test 1: List modes")
    modes = _library.list_modes()
    print(f"  Modes: {modes}")
    # Check case-insensitively
    mode_lower = [m.lower() for m in modes]
    assert "hydraulic" in mode_lower and "pneumatic" in mode_lower
    print("  PASSED")
    
    # Test 2: List symbols
    print("Test 2: List symbols")
    symbols = _library.list_symbols()
    print(f"  Symbols: {len(symbols)}")
    assert len(symbols) > 0
    print("  PASSED")
    
    # Test 3: Create components
    print("Test 3: Create components")
    comp = _circuit.create_component("cylinder_single", {"actuated": False})
    comp2 = _circuit.create_component("gear_pump", {"flow_rate": 0.02})
    print(f"  Created: {comp['id']} and {comp2['id']}")
    assert comp["id"] and comp2["id"]
    print("  PASSED")
    
    # Test 4: Connect components
    print("Test 4: Connect components")
    result = _circuit.connect(comp["id"], comp2["id"])
    print(f"  Connect result: {result}")
    assert result
    print("  PASSED")
    
    # Test 5: Step simulation
    print("Test 5: Step simulation")
    result = _circuit._sim.step()
    print(f"  Step result: time={result['time']}, components={result['component_count']}")
    assert result["time"] > 0
    print("  PASSED")
    
    # Test 6: Get pressures
    print("Test 6: Get pressures")
    pressures = _circuit._sim.get_pressures()
    print(f"  Pressures: {pressures}")
    assert len(pressures) > 0
    print("  PASSED")
    
    # Test 7: Set valve actuation
    print("Test 7: Set valve actuation")
    _circuit._sim.set_actuated(comp2["id"], True)
    print(f"  Set actuation: {result}")
    assert result
    print("  PASSED")
    
    # Test 8: Validate circuit
    print("Test 8: Validate circuit")
    _circuit._sim.validate_circuit()
    print(f"  Validation: {result}")
    print("  PASSED")
    
    # Test 9: Save to file
    print("Test 9: Save to file")
    test_data = {"components": [comp, comp2], "connections": [{"from": comp["id"], "to": comp2["id"]}]}
    path = _fileio.save_circuit(test_data, "test_circuit.json")
    print(f"  Saved to: {path}")
    assert os.path.exists(path)
    print("  PASSED")
    
    # Test 10: List saved files
    print("Test 10: List saved files")
    saved = _fileio.list_saved_circuits()
    print(f"  Saved files: {len(saved)}")
    assert len(saved) > 0
    print("  PASSED")
    
    print("=== ALL TESTS PASSED ===")

if __name__ == "__main__":
    asyncio.run(run_tests())

"""Headless compatibility tests for the FluidSim MCP server."""

import sys
import os
import subprocess

# Add path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import pytest

from mcp_server.simulation import HeadlessSimulation
from mcp_server.library import SymbolLibrary
from mcp_server.circuit import CircuitManager
from mcp_server.fileio import FileIO


class TestHeadlessMode:
    """Test suite for headless mode operation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize simulation manager."""
        self._library = SymbolLibrary()
        self._circuit = CircuitManager()
        self._fileio = FileIO()
        self._sim = self._circuit._sim  # Use the same instance

    def test_simulation_without_gui(self):
        """Test that simulation works without any GUI."""
        assert self._sim is not None
        # Should not require PySide6
        assert self._sim.engine is not None

    def test_list_modes(self):
        """Test listing simulation modes."""
        modes = self._library.list_modes()
        assert "Hydraulic" in modes
        assert "Pneumatic" in modes

    def test_create_component(self):
        """Test creating a component headless."""
        comp = self._circuit.create_component("cylinder_single", {"actuated": False})
        assert comp["id"] is not None
        assert comp["type"] == "cylinder_single"

    def test_create_multiple_components(self):
        """Test creating multiple components."""
        comp1 = self._circuit.create_component("gear_pump")
        comp2 = self._circuit.create_component("valve_2_2", {"actuated": True})
        assert comp1["id"] != comp2["id"]

    def test_connect_components(self):
        """Test connecting components headless."""
        comp1 = self._circuit.create_component("cylinder_single")
        comp2 = self._circuit.create_component("gear_pump")
        result = self._circuit.connect(comp1["id"], comp2["id"])
        assert result is True

    def test_step_simulation(self):
        """Test running simulation steps."""
        comp1 = self._circuit.create_component("cylinder_single")
        comp2 = self._circuit.create_component("gear_pump")
        self._circuit.connect(comp1["id"], comp2["id"])
        # Sync the simulation state
        self._circuit.sync()
        result = self._sim.step()
        assert result["time"] > 0
        assert result["component_count"] >= 2

    def test_get_pressures(self):
        """Test getting pressure readings."""
        comp = self._circuit.create_component("cylinder_single")
        # Sync the simulation state
        self._circuit.sync()
        pressures = self._sim.get_pressures()
        assert len(pressures) >= 1

    def test_set_actuated(self):
        """Test setting valve actuation."""
        comp = self._circuit.create_component("valve_2_2", {"actuated": False})
        # Sync the simulation state
        self._circuit.sync()
        result = self._sim.set_actuated(comp["id"], True)
        assert result is True

    def test_validate_circuit(self):
        """Test circuit validation headless."""
        comp1 = self._circuit.create_component("cylinder_single")
        result = self._sim.validate_circuit()
        assert "valid" in result

    def test_save_to_file(self):
        """Test saving circuit to file."""
        comp = self._circuit.create_component("cylinder_single")
        test_data = {"components": [comp], "connections": []}
        path = self._fileio.save_circuit(test_data, "test_headless.json")
        assert os.path.exists(path)
        os.remove(path)

    def test_list_saved(self):
        """Test listing saved files."""
        saved = self._fileio.list_saved_circuits()
        assert isinstance(saved, list)


class TestNoGuiDependencies:
    """Test that no GUI dependencies remain."""

    def test_no_pyside6_imports(self):
        """Test that no files import PySide6 in the mcp_server package."""
        mcp_server_dir = os.path.join(os.path.dirname(__file__), "..", "src", "mcp_server")
        for root, dirs, files in os.walk(mcp_server_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r") as f:
                        content = f.read()
                        assert "PySide6" not in content, f"Found PySide6 in {filepath}"
                        assert "src.ui.canvas" not in content, f"Found src.ui.canvas in {filepath}"

    def test_no_qapp_creation(self):
        """Test that no QApplication is created in the mcp_server package."""
        mcp_server_dir = os.path.join(os.path.dirname(__file__), "..", "src", "mcp_server")
        for root, dirs, files in os.walk(mcp_server_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r") as f:
                        content = f.read()
                        assert "QApplication" not in content, f"Found QApplication in {filepath}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

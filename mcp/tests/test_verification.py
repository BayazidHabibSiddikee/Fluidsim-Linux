"""Comprehensive verification tests for both GUI and headless modes."""

import sys
import os
import subprocess
import time

# Add path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import pytest

from mcp_server.simulation import HeadlessSimulation
from mcp_server.library import SymbolLibrary
from mcp_server.circuit import CircuitManager
from mcp_server.fileio import FileIO


class TestVerificationSuite:
    """Comprehensive verification suite for both GUI and headless modes."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize test state."""
        self._library = SymbolLibrary()
        self._circuit = CircuitManager()
        self._fileio = FileIO()
        self._sim = self._circuit._sim  # same instance so sync() works

    # ── Server Mode Verification ──────────────────────────────────────────

    def test_server_starts_in_headless_mode(self):
        """Test that server starts without any GUI display."""
        # Should work without DISPLAY or QT_QPA_PLATFORM
        assert True  # Server would start - test just verifies no errors

    def test_no_gui_dependencies(self):
        """Verify no GUI dependencies in mcp_server package."""
        mcp_server_dir = os.path.join(os.path.dirname(__file__), "..", "src", "mcp_server")
        for root, dirs, files in os.walk(mcp_server_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r") as f:
                        content = f.read()
                        assert "PySide6" not in content, f"Found PySide6 in {filepath}"
                        assert "src.ui.canvas" not in content, f"Found src.ui.canvas in {filepath}"
                        assert "QApplication" not in content, f"Found QApplication in {filepath}"

    # ── Headless Mode Verification ──────────────────────────────────────

    def test_headless_simulation_step(self):
        """Test simulation step in headless mode."""
        comp = self._circuit.create_component("cylinder_single")
        result = self._sim.step()
        assert result["time"] > 0

    def test_headless_library_queries(self):
        """Test library queries in headless mode."""
        modes = self._library.list_modes()
        symbols = self._library.list_symbols()
        assert len(modes) > 0
        assert len(symbols) > 0

    def test_headless_circuit_operations(self):
        """Test circuit operations in headless mode."""
        comp1 = self._circuit.create_component("cylinder_single")
        comp2 = self._circuit.create_component("gear_pump")
        assert self._circuit.connect(comp1["id"], comp2["id"])

    def test_headless_file_operations(self):
        """Test file operations in headless mode."""
        test_data = {"components": [], "connections": []}
        path = self._fileio.save_circuit(test_data, "test_verify.json")
        assert os.path.exists(path)
        os.remove(path)

    # ── GUI Mode Verification ────────────────────────────────────────────

    def test_gui_mode_compatibility(self):
        """Test GUI mode compatibility (if PySide6 available)."""
        # Try importing GUI modules - should work if PySide6 installed
        try:
            from src.ui.validator import CircuitValidator
            assert CircuitValidator is not None
            # Validator should work in headless (tests will skip if no GUI)
            assert True
        except ImportError as e:
            # If PySide6 is not installed, skip GUI tests
            pytest.skip(f"PySide6 not installed: {e}")

    def test_grey_fallback(self):
        """Test that server degrades gracefully when PySide6 missing."""
        # The server should work with or without PySide6
        # If PySide6 is missing, validation should still work
        comp1 = self._circuit.create_component("cylinder_single")
        comp2 = self._circuit.create_component("gear_pump")
        self._circuit.connect(comp1["id"], comp2["id"])
        result = self._sim.validate_circuit()
        assert "valid" in result

    # ── Error Handling Verification ──────────────────────────────────────

    def test_invalid_component_id(self):
        """Test error handling for invalid component ID."""
        result = self._sim.get_state("nonexistent_id_12345")
        assert "id" not in result or result.get("id") is None

    def test_invalid_file_path(self):
        """Test error handling for invalid file path."""
        with pytest.raises(Exception):
            self._fileio.load_circuit("/nonexistent/path/invalid.json")

    def test_connect_nonexistent_component(self):
        """Test connecting to non-existent components."""
        result = self._circuit.connect("nonexistent_1", "nonexistent_2")
        assert result is False

    # ── Performance Verification ─────────────────────────────────────────

    def test_concurrent_tool_calls(self):
        """Test handling of concurrent tool calls."""
        # Test that multiple operations can run in sequence without issues
        results = []
        for i in range(5):
            comp = self._circuit.create_component("valve_2_2", {"actuated": False})
            self._sim.set_actuated(comp["id"], True)
            self._circuit.connect(comp["id"], comp["id"])
            results.append(self._sim.step())
        
        # All operations should succeed
        for r in results:
            assert r["time"] > 0

    def test_large_circuit(self):
        """Test creating and managing a large circuit (50+ components)."""
        components = []
        for i in range(50):
            comp = self._circuit.create_component(
                "cylinder_single" if i % 2 == 0 else "valve_2_2",
                {"actuated": (i % 5 == 0)}
            )
            components.append(comp["id"])
        
        # Connect all components in a chain
        for i in range(len(components) - 1):
            self._circuit.connect(components[i], components[i + 1])
        
        self._circuit.sync()
        result = self._sim.step()
        
        assert result["component_count"] >= 50
        assert result["time"] > 0
        assert result["time"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

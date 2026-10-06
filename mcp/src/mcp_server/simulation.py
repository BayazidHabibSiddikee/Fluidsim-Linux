"""Simulation layer for FluidSim MCP server.

Provides headless access to the SimulationEngine without requiring a GUI.
"""

import sys
import os
from typing import Any, Dict, List, Optional

# Add parent to path so we can import the actual simulation engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.simulation.engine import SimulationEngine


class HeadlessSimulation:
    """Headless simulation wrapper that works without PySide6 GUI."""

    def __init__(self, mode: str = "hydraulic"):
        self.engine = SimulationEngine()
        self.engine.set_mode(mode)
        self._circuit_components: List[Dict[str, Any]] = []
        self._circuit_connections: List[Dict[str, Any]] = []

    def reset(self):
        """Reset the simulation engine."""
        self.engine.reset()
        self._circuit_components = []
        self._circuit_connections = []

    def set_mode(self, mode: str):
        """Switch between hydraulic and pneumatic modes."""
        self.engine.set_mode(mode)

    def add_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Add a component to the circuit.
        
        Args:
            component: Dict with keys 'id', 'type', 'properties' (optional)
        
        Returns:
            The component dict
        """
        self._circuit_components.append(component)
        self._ensure_engine_state(component)
        return component

    def remove_component(self, component_id: str) -> bool:
        """Remove a component from the circuit.
        
        Args:
            component_id: The ID of the component to remove
        
        Returns:
            True if removed, False if not found
        """
        initial_len = len(self._circuit_components)
        self._circuit_components = [
            c for c in self._circuit_components if c.get("id") != component_id
        ]
        if len(self._circuit_components) < initial_len:
            self.engine.reset()
            for comp in self._circuit_components:
                self._ensure_engine_state(comp)
        return len(self._circuit_components) < initial_len

    def connect_components(
        self, from_id: str, to_id: str, from_port: Optional[str] = None, to_port: Optional[str] = None
    ) -> bool:
        """Connect two components.
        
        Args:
            from_id: Source component ID
            to_id: Destination component ID
            from_port: Source port (if applicable)
            to_port: Destination port (if applicable)
        
        Returns:
            True if connection was added, False if components not found
        """
        from_comp = None
        to_comp = None
        for comp in self._circuit_components:
            if comp.get("id") == from_id:
                from_comp = comp
            if comp.get("id") == to_id:
                to_comp = comp
        
        if from_comp is None or to_comp is None:
            return False
        
        connection = {
            "from": from_id,
            "to": to_id,
            "from_port": from_port,
            "to_port": to_port,
        }
        self._circuit_connections.append(connection)
        
        # Ensure states are initialized
        for comp in self._circuit_components:
            self._ensure_engine_state(comp)
        return True

    def disconnect_components(self, from_id: str, to_id: str) -> bool:
        """Disconnect two components.
        
        Args:
            from_id: Source component ID
            to_id: Destination component ID
        
        Returns:
            True if disconnected, False if no connection found
        """
        initial_len = len(self._circuit_connections)
        self._circuit_connections = [
            c for c in self._circuit_connections
            if not (c.get("from") == from_id and c.get("to") == to_id)
        ]
        return len(self._circuit_connections) < initial_len

    def step(self, dt: Optional[float] = None) -> Dict[str, Any]:
        """Run one simulation step.
        
        Args:
            dt: Timestep override (defaults to engine default)
        
        Returns:
            Dict with step results including time, pressures, flows
        """
        if dt is not None:
            self.engine.dt = dt
        
        self.engine.step(self._circuit_components, self._circuit_connections)
        
        # Collect state from all components
        states = {comp["id"]: self.engine.get_state(comp["id"]) for comp in self._circuit_components}
        
        return {
            "time": self.engine.time,
            "component_count": len(self._circuit_components),
            "connection_count": len(self._circuit_connections),
            "states": states,
        }

    def get_state(self, component_id: str) -> Dict[str, Any]:
        """Get the current state of a specific component.
        
        Args:
            component_id: The ID of the component
        
        Returns:
            Dict of state values
        """
        return self.engine.get_state(component_id)

    def get_pressures(self) -> Dict[str, float]:
        """Get pressure readings for all components.
        
        Returns:
            Dict mapping component IDs to their pressure_a values
        """
        pressures = {}
        for comp in self._circuit_components:
            pressures[comp["id"]] = self.engine.get_pressure(comp["id"])
        return pressures

    def get_flows(self) -> Dict[str, float]:
        """Get flow readings for all components.
        
        Returns:
            Dict mapping component IDs to their flow rates
        """
        flows = {}
        for comp in self._circuit_components:
            flows[comp["id"]] = self.engine.get_flow(comp["id"])
        return flows

    def set_actuated(self, component_id: str, value: bool) -> bool:
        """Set actuation state of a directional valve.
        
        Args:
            component_id: The ID of the valve
            value: True to actuate, False to release
        
        Returns:
            True if set successfully, False if not a valve or not found
        """
        for comp in self._circuit_components:
            if comp.get("id") == component_id:
                return self.engine.set_actuated(comp, value)
        return False

    def validate_circuit(self) -> Dict[str, Any]:
        """Validate the current circuit.
        
        Returns:
            Dict with 'valid' boolean and list of 'errors'
        """
        # Import here to avoid circular dependency
        from src.ui.validator import CircuitValidator
        
        if not self._circuit_components:
            return {"valid": True, "errors": []}
        
        # Build a simplified diagram for validation
        from src.ui.canvas import CircuitCanvas
        from PySide6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        
        try:
            canvas = CircuitCanvas()
            # Temporarily set the components and connections
            original_components = canvas.components
            original_connections = canvas.connections
            
            canvas.components = self._circuit_components
            canvas.connections = self._circuit_connections
            
            # Run validation
            validator = CircuitValidator()
            results = validator.validate(canvas)
            
            canvas.components = original_components
            canvas.connections = original_connections
            
            return {
                "valid": results.get("valid", False),
                "errors": results.get("errors", []),
            }
        except Exception as e:
            return {"valid": False, "errors": [f"Validation failed: {str(e)}"]}

    def get_full_state(self) -> Dict[str, Any]:
        """Get the complete state of the simulation.
        
        Returns:
            Dict with all simulation data
        """
        return {
            "mode": self.engine.mode,
            "time": self.engine.time,
            "gravity": self.engine.gravity,
            "fluid_density": self.engine.fluid_density,
            "component_count": len(self._circuit_components),
            "connection_count": len(self._circuit_connections),
            "components": self._circuit_components,
            "connections": self._circuit_connections,
            "pressures": self.get_pressures(),
            "flows": self.get_flows(),
            "component_states": {
                comp["id"]: self.engine.get_state(comp["id"])
                for comp in self._circuit_components
            },
        }

    def _ensure_engine_state(self, component: Dict[str, Any]):
        """Ensure the engine has state initialized for a component."""
        cid = component.get("id")
        ctype = component.get("type")
        if cid and ctype:
            self.engine._ensure_state(component, ctype, component.get("properties", {}))

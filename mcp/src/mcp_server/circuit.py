"""Circuit management layer for FluidSim MCP server."""

from typing import Any, Dict, List, Optional

from .simulation import HeadlessSimulation


class CircuitManager:
    """Manages circuit state and operations."""

    def __init__(self, mode: str = "hydraulic"):
        self._sim = HeadlessSimulation(mode)

    # --- Component operations ---

    def create_component(self, component_type: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new component.
        
        Args:
            component_type: Type identifier (e.g., 'cylinder_single', 'valve_2_2', 'pump')
            properties: Optional properties dict
        
        Returns:
            The created component dict
        """
        import uuid
        component_id = str(uuid.uuid4())[:8]
        component = {
            "id": component_id,
            "type": component_type,
            "properties": properties or {},
        }
        self._sim.add_component(component)
        return component

    def delete_component(self, component_id: str) -> bool:
        """Delete a component from the circuit.
        
        Args:
            component_id: The ID of the component
        
        Returns:
            True if deleted, False if not found
        """
        return self._sim.remove_component(component_id)

    # --- Connection operations ---

    def connect(self, from_id: str, to_id: str, from_port: Optional[str] = None, to_port: Optional[str] = None) -> bool:
        """Connect two components.
        
        Args:
            from_id: Source component ID
            to_id: Destination component ID
            from_port: Source port name
            to_port: Destination port name
        
        Returns:
            True if connected, False if components not found
        """
        return self._sim.connect_components(from_id, to_id, from_port, to_port)

    def disconnect(self, from_id: str, to_id: str) -> bool:
        """Disconnect two components.
        
        Args:
            from_id: Source component ID
            to_id: Destination component ID
        
        Returns:
            True if disconnected, False if no connection found
        """
        return self._sim.disconnect_components(from_id, to_id)

    # --- Simulation operations ---

    def step(self, dt: Optional[float] = None) -> Dict[str, Any]:
        """Run one simulation step.
        
        Args:
            dt: Optional timestep override
        
        Returns:
            Dict with simulation results
        """
        return self._sim.step(dt)

    def get_state(self, component_id: str) -> Dict[str, Any]:
        """Get the state of a specific component.
        
        Args:
            component_id: The component ID
        
        Returns:
            Dict of state values
        """
        return self._sim.get_state(component_id)

    def get_pressures(self) -> Dict[str, float]:
        """Get pressure readings for all components.
        
        Returns:
            Dict mapping component IDs to pressure values
        """
        return self._sim.get_pressures()

    def get_flows(self) -> Dict[str, float]:
        """Get flow readings for all components.
        
        Returns:
            Dict mapping component IDs to flow values
        """
        return self._sim.get_flows()

    def set_actuated(self, component_id: str, value: bool) -> bool:
        """Set actuation of a directional valve.
        
        Args:
            component_id: The valve component ID
            value: True to actuate, False to release
        
        Returns:
            True if set, False if not a valve
        """
        return self._sim.set_actuated(component_id, value)

    # --- Validation ---

    def validate(self) -> Dict[str, Any]:
        """Validate the current circuit.
        
        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        return self._sim.validate_circuit()

    # --- Full state ---

    def get_full_state(self) -> Dict[str, Any]:
        """Get the complete simulation state.
        
        Returns:
            Dict with all simulation data
        """
        return self._sim.get_full_state()

    # --- Mode / reset ---

    def set_mode(self, mode: str):
        """Switch simulation mode.
        
        Args:
            mode: 'hydraulic' or 'pneumatic'
        """
        self._sim.set_mode(mode)

    def reset(self):
        """Reset the simulation."""
        self._sim.reset()

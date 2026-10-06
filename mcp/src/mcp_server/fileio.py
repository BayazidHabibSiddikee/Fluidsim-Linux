"""File I/O layer for FluidSim MCP server."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_SAVE_DIR = Path.home() / ".fluidsim" / "circuits"


class FileIO:
    """Handles JSON save/load of circuits."""

    def __init__(self, save_dir: Optional[Path] = None):
        self.save_dir = save_dir or DEFAULT_SAVE_DIR
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def save_circuit(self, circuit_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save a circuit to a JSON file.
        
        Args:
            circuit_data: Dict containing circuit data (components, connections, etc.)
            filename: Optional filename. If not provided, generates one.
        
        Returns:
            The path where the file was saved
        """
        if filename is None:
            import uuid
            filename = f"fluidsim_{uuid.uuid4().hex[:8]}.json"
        
        filepath = self.save_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(circuit_data, f, indent=2)
        
        return str(filepath)

    def load_circuit(self, filepath: str) -> Dict[str, Any]:
        """Load a circuit from a JSON file.
        
        Args:
            filepath: Path to the JSON file
        
        Returns:
            Dict containing circuit data
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Circuit file not found: {filepath}")
        
        with open(path, "r") as f:
            data = json.load(f)
        
        return data

    def list_saved_circuits(self) -> List[Dict[str, Any]]:
        """List all saved circuit files.
        
        Returns:
            List of dicts with 'filename' and 'path'
        """
        if not self.save_dir.exists():
            return []
        
        circuits = []
        for filepath in self.save_dir.glob("*.json"):
            circuits.append({
                "filename": filepath.name,
                "path": str(filepath),
                "size": filepath.stat().st_size,
            })
        return circuits

    def delete_circuit(self, filepath: str) -> bool:
        """Delete a saved circuit file.
        
        Args:
            filepath: Path to the file to delete
        
        Returns:
            True if deleted, False if not found
        """
        path = Path(filepath)
        if not path.exists():
            return False
        path.unlink()
        return True

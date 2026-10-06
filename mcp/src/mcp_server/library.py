"""Symbol library layer for FluidSim MCP server."""

from typing import Any, Dict, List, Optional

from src.symbols.library import SYMBOL_CATALOG, DISPLAY_NAMES


class SymbolLibrary:
    """Accessor for the symbol catalog."""

    def __init__(self):
        self._catalog = SYMBOL_CATALOG
        self._display_names = DISPLAY_NAMES

    def list_modes(self) -> List[str]:
        """List available simulation modes (hydraulic, pneumatic, etc.).
        
        Returns:
            List of mode strings
        """
        return list(self._catalog.keys())

    def list_symbols(self, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all symbols, optionally filtered by mode.
        
        Args:
            mode: Simulation mode to filter by (hydraulic, pneumatic, electrical, digital_control)
        
        Returns:
            List of symbol dicts with 'id' and 'name'
        """
        if mode:
            catalog_key = mode.lower()
            if catalog_key not in self._catalog:
                return []
            symbols = self._catalog[catalog_key]
        else:
            symbols = {}
            for mode, sym_list in self._catalog.items():
                for sym in sym_list:
                    symbols[sym] = symbols.get(sym, [])
                    symbols[sym].append(mode)
        
        result = []
        for sym_id, name in self._display_names.items():
            modes = symbols.get(sym_id, []) if isinstance(symbols, dict) else []
            result.append({
                "id": sym_id,
                "name": name,
                "modes": modes,
            })
        return result

    def get_symbol_info(self, sym_id: str) -> Optional[Dict[str, Any]]:
        """Get details about a specific symbol.
        
        Args:
            sym_id: The symbol ID
        
        Returns:
            Dict with symbol info, or None if not found
        """
        if sym_id not in self._display_names:
            return None
        modes = []
        for mode, sym_list in self._catalog.items():
            if sym_id in sym_list:
                modes.append(mode)
        return {
            "id": sym_id,
            "name": self._display_names[sym_id],
            "modes": modes,
            "catalog": sym_id in self._catalog.get("hydraulic", []) or \
                      sym_id in self._catalog.get("pneumatic", []) or \
                      sym_id in self._catalog.get("electrical", []) or \
                      sym_id in self._catalog.get("digital_control", []),
        }

    def get_symbols_by_category(self, mode: str, category: str) -> List[Dict[str, Any]]:
        """Get symbols in a specific category.
        
        Args:
            mode: Simulation mode (hydraulic, pneumatic, electrical, digital_control)
            category: Category name
        
        Returns:
            List of symbol dicts
        """
        if mode.lower() not in self._catalog:
            return []
        
        catalog_key = mode.lower()
        symbol_ids = self._catalog[catalog_key].get(category, [])
        
        return [
            {
                "id": sym_id,
                "name": self._display_names.get(sym_id, sym_id),
            }
            for sym_id in symbol_ids
        ]

    def get_category_list(self, mode: str) -> List[str]:
        """Get available categories for a mode.
        
        Args:
            mode: Simulation mode
        
        Returns:
            List of category names
        """
        if mode.lower() not in self._catalog:
            return []
        return list(self._catalog[mode.lower()].keys())

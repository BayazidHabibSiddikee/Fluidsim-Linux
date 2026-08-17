"""Circuit validator — detects common wiring errors and physics issues."""
from typing import Optional


class CircuitResult:
    """Holds validation findings for a single component or connection."""
    def __init__(self, level: str, message: str, comp_id: str = ""):
        self.level = level  # "error", "warning", "info"
        self.message = message
        self.comp_id = comp_id

    def __repr__(self):
        return f"CircuitResult({self.level!r}, {self.message!r})"


class CircuitValidator:
    """Validates hydraulic/pneumatic circuits for common errors."""

    DIRECTIONAL_VALVES = frozenset({
        "valve_2_2", "valve_3_2", "valve_4_2", "valve_4_3",
        "valve_5_2", "valve_5_3",
    })
    PRESSURE_SOURCES = frozenset({
        "gear_pump", "pump", "pump_vane", "piston_pump", "variable_pump",
        "internally_gear_pump", "hydraulic_power_unit",
        "compressor", "air_supply", "vacuum_generator",
    })
    ACTUATORS = frozenset({
        "cylinder_single", "cylinder_double", "cylinder_telescopic",
        "plunger_cylinder", "cylinder_cushioned",
        "motor", "motor_bi", "air_motor",
    })
    DRAINS = frozenset({"tank"})

    def validate(self, components: list, connections: list, mode: str) -> list[CircuitResult]:
        """Return list of findings for the given circuit."""
        results: list[CircuitResult] = []
        if not components:
            return results

        comp_map = {c["id"]: c for c in components}
        active_sources = self._active_sources(components)
        drain_ids = self._drain_components(comp_map)
        port_usage = self._port_usage(connections, comp_map)

        # --- Source checks ---
        for sid in active_sources:
            comp = comp_map[sid]
            ctype = comp.get("type", "")
            if ctype in self.PRESSURE_SOURCES:
                # Source must connect to at least one component
                src_ports = port_usage.get(sid, set())
                if not src_ports:
                    results.append(CircuitResult(
                        "error",
                        f"{ctype.replace('_', ' ').title()} has no outgoing connections — pressure cannot flow",
                        sid,
                    ))
                else:
                    # Check if source connects to a valve/actuator or direct drain
                    dst_types = {comp_map[c["to_component"]].get("type")
                                 for c in connections
                                 if c.get("from_component") == sid and c["to_component"] in comp_map}
                    if not dst_types.intersection(self.ACTUATORS | self.DRAINS | self.DIRECTIONAL_VALVES):
                        results.append(CircuitResult(
                            "warning",
                            f"Source connects to {', '.join(sorted(dst_types))} — check that pressure path is valid",
                            sid,
                        ))

        # --- Actuator checks ---
        for cid, comp in comp_map.items():
            ctype = comp.get("type", "")
            if ctype in self.ACTUATORS:
                ports_used = port_usage.get(cid, set())
                if not ports_used:
                    results.append(CircuitResult(
                        "error",
                        f"{ctype.replace('_', ' ').title()} is floating — no connections",
                        cid,
                    ))
                elif len(ports_used) == 1 and ctype in (
                    "cylinder_single", "cylinder_double", "cylinder_telescopic",
                    "plunger_cylinder", "cylinder_cushioned",
                ):
                    results.append(CircuitResult(
                        "warning",
                        f"Cylinder has only 1 connection — may not extend/retract properly",
                        cid,
                    ))

        # --- Valve checks ---
        for vid, comp in comp_map.items():
            ctype = comp.get("type", "")
            if ctype in self.DIRECTIONAL_VALVES:
                ports_used = port_usage.get(vid, set())
                if not ports_used:
                    results.append(CircuitResult(
                        "error",
                        f"{ctype.replace('_', ' ').title()} is not wired — will block all flow",
                        vid,
                    ))

        # --- Drain checks ---
        for tid, comp in comp_map.items():
            ctype = comp.get("type", "")
            if ctype in self.DRAINS:
                # Tanks should ideally have at least one connection
                pass  # Tanks can be unconnected (they're ground reference)

        # --- Connection sanity ---
        for conn in connections:
            src = conn.get("from_component")
            dst = conn.get("to_component")
            if src and src not in comp_map:
                results.append(CircuitResult(
                    "error",
                    f"Connection references unknown component '{src}'",
                    src or "",
                ))
            if dst and dst not in comp_map:
                results.append(CircuitResult(
                    "error",
                    f"Connection references unknown component '{dst}'",
                    dst or "",
                ))

        # --- Loop detection (simple) ---
        adj = self._build_adj(comp_map, connections)
        loops = self._find_simple_loops(adj, comp_map)
        for loop in loops[:3]:  # Show at most 3 loops
            ids = [comp_map[i]["id"] for i in loop if i in comp_map]
            names = [comp_map[i].get("name", comp_map[i].get("type", "?")) for i in loop if i in comp_map]
            results.append(CircuitResult(
                "info",
                f"Circuit loop detected: {' → '.join(names)}",
                ids[0] if ids else "",
            ))

        return results

    def _active_sources(self, components: list) -> list[str]:
        ids = []
        for c in components:
            ctype = c.get("type", "")
            props = c.get("properties", {})
            if ctype in self.PRESSURE_SOURCES:
                if props.get("running", True):
                    ids.append(c["id"])
        return ids

    def _drain_components(self, comp_map: dict) -> set[str]:
        return {cid for cid, c in comp_map.items()
                if c.get("type") in self.DRAINS}

    def _port_usage(self, connections: list, comp_map: dict) -> dict[str, set]:
        """Map component_id -> set of port labels used."""
        usage: dict[str, set] = {}
        for conn in connections:
            src = conn.get("from_component")
            dst = conn.get("to_component")
            from_port = conn.get("from_port", "")
            to_port = conn.get("to_port", "")
            if src:
                usage.setdefault(src, set()).add(from_port)
            if dst:
                usage.setdefault(dst, set()).add(to_port)
        return usage

    def _build_adj(self, comp_map: dict, connections: list) -> dict[str, list]:
        adj = {cid: [] for cid in comp_map}
        for conn in connections:
            a, b = conn.get("from_component"), conn.get("to_component")
            if a and b and a in adj and b in adj:
                adj[a].append(b)
                adj[b].append(a)
        return adj

    def _find_simple_loops(self, adj: dict, comp_map: dict) -> list[list]:
        """Find simple cycles in the undirected graph."""
        visited = set()
        loops = []

        def dfs(node, path, start):
            for nb in adj.get(node, []):
                if nb == start and len(path) > 2:
                    loops.append(list(path))
                elif nb not in visited:
                    visited.add(nb)
                    path.append(nb)
                    dfs(nb, path, start)
                    path.pop()
            visited.discard(node)

        for node in adj:
            visited.clear()
            visited.add(node)
            dfs(node, [node], node)
        return loops


# ─── Validation result icons/colors ───

RESULT_STYLE = {
    "error":   ("#e74c3c", "🔴"),
    "warning": ("#f39c12", "🟡"),
    "info":    ("#3498db", "ℹ️"),
}


def format_results(results: list[CircuitResult]) -> list[tuple[str, str, str]]:
    """Return (color, emoji, text) tuples for UI display."""
    out = []
    for r in results:
        color, emoji = RESULT_STYLE.get(r.level, ("#888", "•"))
        out.append((color, emoji, f"[{r.level.upper()}] {r.message}"))
    return out

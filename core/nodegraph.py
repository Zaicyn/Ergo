"""Ergo Node Graph — data model, validation, and compilation to Ergo source.

A node graph is a DAG of typed operations. Each node has input and output pins.
Edges connect output pins to input pins with type checking. The graph compiles
to flat Ergo source via topological sort.

Determinism guarantee: same graph -> same source -> same binary -> same output.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


# ── Types ────────────────────────────────────────────────────

class PinType(Enum):
    REAL = "REAL"
    INTEGER = "INTEGER"
    LOGICAL = "LOGICAL"
    CHARACTER = "CHARACTER"

    def promotes_to(self, other: PinType) -> bool:
        """Can this type be implicitly promoted to other?"""
        if self == other:
            return True
        if self == PinType.INTEGER and other == PinType.REAL:
            return True
        return False


class PinDir(Enum):
    IN = auto()
    OUT = auto()


# ── Pin ──────────────────────────────────────────────────────

@dataclass
class Pin:
    name: str
    type: PinType
    direction: PinDir
    shape: tuple | None = None  # None = scalar, (10,) = 1D, (8, 2) = 2D

    @property
    def is_scalar(self) -> bool:
        return self.shape is None

    @property
    def type_label(self) -> str:
        s = self.type.value
        if self.shape:
            s += f"({','.join(str(d) for d in self.shape)})"
        return s


# ── Node Kinds ───────────────────────────────────────────────

class NodeKind(Enum):
    INTRINSIC = "intrinsic"      # built-in Ergo op (SIN, +, CLAMP, etc.)
    CONSTANT = "constant"        # PARAMETER value
    INPUT = "input"              # graph boundary input
    OUTPUT = "output"            # graph boundary output
    SUBGRAPH = "subgraph"        # collapsed group -> Ergo FUNCTION


# ── Node Definitions (the catalog) ──────────────────────────

# Each entry: (input_pins, output_pins, ergo_template)
# Template uses {pin_name} substitution.

_R = PinType.REAL
_I = PinType.INTEGER
_L = PinType.LOGICAL
_C = PinType.CHARACTER

def _pins_in(*specs) -> list[Pin]:
    return [Pin(name=n, type=t, direction=PinDir.IN) for n, t in specs]

def _pins_out(*specs) -> list[Pin]:
    return [Pin(name=n, type=t, direction=PinDir.OUT) for n, t in specs]


@dataclass
class NodeDef:
    """Definition of a node type (from the catalog)."""
    name: str
    kind: NodeKind
    inputs: list[Pin]
    outputs: list[Pin]
    template: str  # Ergo expression template, e.g. "{a} + {b}"


# Built-in node catalog
NODE_CATALOG: dict[str, NodeDef] = {}

def _register(name: str, kind: NodeKind, inputs: list[Pin], outputs: list[Pin],
              template: str):
    NODE_CATALOG[name] = NodeDef(name, kind, inputs, outputs, template)

# Arithmetic
_register("Add",    NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _R)), "{a} + {b}")
_register("Sub",    NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _R)), "{a} - {b}")
_register("Mul",    NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _R)), "{a} * {b}")
_register("Div",    NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _R)), "{a} / {b}")
_register("Pow",    NodeKind.INTRINSIC, _pins_in(("base", _R), ("exp", _R)), _pins_out(("out", _R)), "{base} ** {exp}")
_register("Negate", NodeKind.INTRINSIC, _pins_in(("x", _R)),             _pins_out(("out", _R)), "-{x}")

# Integer arithmetic
_register("AddInt", NodeKind.INTRINSIC, _pins_in(("a", _I), ("b", _I)), _pins_out(("out", _I)), "{a} + {b}")
_register("SubInt", NodeKind.INTRINSIC, _pins_in(("a", _I), ("b", _I)), _pins_out(("out", _I)), "{a} - {b}")
_register("MulInt", NodeKind.INTRINSIC, _pins_in(("a", _I), ("b", _I)), _pins_out(("out", _I)), "{a} * {b}")
_register("DivInt", NodeKind.INTRINSIC, _pins_in(("a", _I), ("b", _I)), _pins_out(("out", _I)), "{a} / {b}")
_register("Mod",    NodeKind.INTRINSIC, _pins_in(("a", _I), ("b", _I)), _pins_out(("out", _I)), "MOD({a}, {b})")

# Math intrinsics
_register("Sin",   NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "SIN({x})")
_register("Cos",   NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "COS({x})")
_register("Tan",   NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "TAN({x})")
_register("Asin",  NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "ASIN({x})")
_register("Acos",  NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "ACOS({x})")
_register("Atan",  NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "ATAN({x})")
_register("Atan2", NodeKind.INTRINSIC, _pins_in(("y", _R), ("x", _R)), _pins_out(("out", _R)), "ATAN2({y}, {x})")
_register("Sqrt",  NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "SQRT({x})")
_register("Abs",   NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "ABS({x})")
_register("Exp",   NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "EXP({x})")
_register("Log",   NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "LOG({x})")
_register("Log10", NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "LOG10({x})")
_register("Sinh",  NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "SINH({x})")
_register("Cosh",  NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "COSH({x})")
_register("Tanh",  NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _R)), "TANH({x})")
_register("Clamp", NodeKind.INTRINSIC, _pins_in(("x", _R), ("lo", _R), ("hi", _R)), _pins_out(("out", _R)), "CLAMP({x}, {lo}, {hi})")
_register("Max",   NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _R)), "MAX({a}, {b})")
_register("Min",   NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _R)), "MIN({a}, {b})")

# Comparison
_register("Less",      NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _L)), "{a} < {b}")
_register("Greater",   NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _L)), "{a} > {b}")
_register("Equal",     NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _L)), "{a} = {b}")
_register("NotEqual",  NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _L)), "{a} \u2260 {b}")
_register("LessEq",    NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _L)), "{a} \u2264 {b}")
_register("GreaterEq", NodeKind.INTRINSIC, _pins_in(("a", _R), ("b", _R)), _pins_out(("out", _L)), "{a} \u2265 {b}")

# Logic
_register("And", NodeKind.INTRINSIC, _pins_in(("a", _L), ("b", _L)), _pins_out(("out", _L)), "{a} .AND. {b}")
_register("Or",  NodeKind.INTRINSIC, _pins_in(("a", _L), ("b", _L)), _pins_out(("out", _L)), "{a} .OR. {b}")
_register("Not", NodeKind.INTRINSIC, _pins_in(("a", _L)),             _pins_out(("out", _L)), ".NOT. {a}")

# Control flow
_register("Switch", NodeKind.INTRINSIC,
          _pins_in(("cond", _L), ("t", _R), ("f", _R)),
          _pins_out(("out", _R)),
          "SWITCH({cond}, {t}, {f})")  # special: emits IF/ELSE

# Conversion
_register("ToReal", NodeKind.INTRINSIC, _pins_in(("x", _I)), _pins_out(("out", _R)), "REAL({x})")
_register("ToInt",  NodeKind.INTRINSIC, _pins_in(("x", _R)), _pins_out(("out", _I)), "INT({x})")
_register("ToChar", NodeKind.INTRINSIC, _pins_in(("x", _I)), _pins_out(("out", _C)), "CHAR({x})")
_register("ToIChar",NodeKind.INTRINSIC, _pins_in(("x", _C)), _pins_out(("out", _I)), "ICHAR({x})")

# Bitwise
_register("ISHFT", NodeKind.INTRINSIC, _pins_in(("val", _I), ("shift", _I)), _pins_out(("out", _I)), "ISHFT({val}, {shift})")
_register("IEOR",  NodeKind.INTRINSIC, _pins_in(("a", _I), ("b", _I)), _pins_out(("out", _I)), "IEOR({a}, {b})")
_register("IAND",  NodeKind.INTRINSIC, _pins_in(("a", _I), ("b", _I)), _pins_out(("out", _I)), "IAND({a}, {b})")
_register("IOR",   NodeKind.INTRINSIC, _pins_in(("a", _I), ("b", _I)), _pins_out(("out", _I)), "IOR({a}, {b})")
_register("BitNot",NodeKind.INTRINSIC, _pins_in(("a", _I)),             _pins_out(("out", _I)), "NOT({a})")


# ── Node Instance ────────────────────────────────────────────

@dataclass
class Node:
    """A node instance in a graph."""
    id: str
    op: str                     # key into NODE_CATALOG, or "constant"/"input"/"output"
    position: tuple[float, float] = (0.0, 0.0)  # canvas position for Nuklear

    # For constant nodes
    const_type: PinType | None = None
    const_value: Any = None

    # For input/output boundary nodes
    pin_name: str | None = None
    pin_type: PinType | None = None

    @property
    def definition(self) -> NodeDef | None:
        return NODE_CATALOG.get(self.op)

    def input_pins(self) -> list[Pin]:
        if self.op == "constant":
            return []
        if self.op == "input":
            return []
        if self.op == "output":
            return [Pin(self.pin_name or "value", self.pin_type or PinType.REAL, PinDir.IN)]
        defn = self.definition
        return list(defn.inputs) if defn else []

    def output_pins(self) -> list[Pin]:
        if self.op == "constant":
            return [Pin("out", self.const_type or PinType.REAL, PinDir.OUT)]
        if self.op == "input":
            return [Pin(self.pin_name or "value", self.pin_type or PinType.REAL, PinDir.OUT)]
        if self.op == "output":
            return []
        defn = self.definition
        return list(defn.outputs) if defn else []

    def get_input_pin(self, name: str) -> Pin | None:
        for p in self.input_pins():
            if p.name == name:
                return p
        return None

    def get_output_pin(self, name: str) -> Pin | None:
        for p in self.output_pins():
            if p.name == name:
                return p
        return None


# ── Edge ─────────────────────────────────────────────────────

@dataclass
class Edge:
    src_node: str   # node id
    src_pin: str    # output pin name
    dst_node: str   # node id
    dst_pin: str    # input pin name


# ── Graph ────────────────────────────────────────────────────

@dataclass
class GraphParam:
    """A compile-time parameter visible to all nodes."""
    name: str
    type: PinType
    value: Any  # int or float


@dataclass
class Graph:
    """A complete node graph — validates and compiles to Ergo source."""
    name: str
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    parameters: list[GraphParam] = field(default_factory=list)

    # ── building ─────────────────────────────────────────

    def add_node(self, node: Node) -> str:
        self.nodes[node.id] = node
        return node.id

    def add_edge(self, src_node: str, src_pin: str,
                 dst_node: str, dst_pin: str) -> Edge:
        edge = Edge(src_node, src_pin, dst_node, dst_pin)
        self.edges.append(edge)
        return edge

    def add_constant(self, id: str, type: PinType, value: Any,
                     position: tuple = (0, 0)) -> str:
        node = Node(id=id, op="constant", const_type=type,
                    const_value=value, position=position)
        return self.add_node(node)

    def add_input(self, id: str, name: str, type: PinType,
                  position: tuple = (0, 0)) -> str:
        node = Node(id=id, op="input", pin_name=name,
                    pin_type=type, position=position)
        return self.add_node(node)

    def add_output(self, id: str, name: str, type: PinType,
                   position: tuple = (0, 0)) -> str:
        node = Node(id=id, op="output", pin_name=name,
                    pin_type=type, position=position)
        return self.add_node(node)

    def add_op(self, id: str, op: str,
               position: tuple = (0, 0)) -> str:
        node = Node(id=id, op=op, position=position)
        return self.add_node(node)

    # ── validation ───────────────────────────────────────

    def validate(self) -> list[str]:
        """Validate the graph. Returns list of error strings (empty = valid)."""
        errors = []

        # Check all nodes reference valid ops
        for nid, node in self.nodes.items():
            if node.op not in ("constant", "input", "output"):
                if node.op not in NODE_CATALOG:
                    errors.append(f"Node '{nid}': unknown operation '{node.op}'")

        # Check all edges reference valid nodes and pins
        for edge in self.edges:
            if edge.src_node not in self.nodes:
                errors.append(f"Edge: source node '{edge.src_node}' not found")
                continue
            if edge.dst_node not in self.nodes:
                errors.append(f"Edge: destination node '{edge.dst_node}' not found")
                continue

            src = self.nodes[edge.src_node]
            dst = self.nodes[edge.dst_node]

            src_pin = src.get_output_pin(edge.src_pin)
            if src_pin is None:
                errors.append(
                    f"Edge: node '{edge.src_node}' has no output pin '{edge.src_pin}'")
                continue

            dst_pin = dst.get_input_pin(edge.dst_pin)
            if dst_pin is None:
                errors.append(
                    f"Edge: node '{edge.dst_node}' has no input pin '{edge.dst_pin}'")
                continue

            # Type check
            if not src_pin.type.promotes_to(dst_pin.type):
                errors.append(
                    f"Edge {edge.src_node}.{edge.src_pin} -> "
                    f"{edge.dst_node}.{edge.dst_pin}: "
                    f"type mismatch {src_pin.type.value} -> {dst_pin.type.value}")

        # Check for multiple edges into the same input pin
        input_connections: dict[tuple[str, str], list[str]] = {}
        for edge in self.edges:
            key = (edge.dst_node, edge.dst_pin)
            input_connections.setdefault(key, []).append(edge.src_node)
        for (nid, pin), sources in input_connections.items():
            if len(sources) > 1:
                errors.append(
                    f"Node '{nid}' pin '{pin}': "
                    f"multiple inputs ({', '.join(sources)}) — fan-in not allowed")

        # Check for unconnected required input pins
        connected_inputs = {(e.dst_node, e.dst_pin) for e in self.edges}
        for nid, node in self.nodes.items():
            for pin in node.input_pins():
                if (nid, pin.name) not in connected_inputs:
                    errors.append(
                        f"Node '{nid}' pin '{pin.name}': unconnected input")

        # Check for cycles (topological sort)
        try:
            self._topo_sort()
        except ValueError as e:
            errors.append(str(e))

        return errors

    # ── topological sort ─────────────────────────────────

    def _topo_sort(self) -> list[str]:
        """Kahn's algorithm. Returns node IDs in execution order.
        Raises ValueError if a cycle exists."""
        # Build adjacency
        in_degree: dict[str, int] = {nid: 0 for nid in self.nodes}
        successors: dict[str, list[str]] = {nid: [] for nid in self.nodes}

        for edge in self.edges:
            in_degree[edge.dst_node] += 1
            successors[edge.src_node].append(edge.dst_node)

        # Start with zero in-degree nodes, sorted for determinism
        queue = sorted([nid for nid, d in in_degree.items() if d == 0])
        order = []

        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for succ in sorted(successors[nid]):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)
            queue.sort()  # deterministic order

        if len(order) != len(self.nodes):
            errors = set(self.nodes.keys()) - set(order)
            raise ValueError(f"Cycle detected involving nodes: {errors}")

        return order

    # ── compilation to Ergo source ───────────────────────

    def compile(self) -> str:
        """Compile the graph to Ergo source code."""
        errors = self.validate()
        if errors:
            raise ValueError(
                f"Graph validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors))

        order = self._topo_sort()
        lines = []

        lines.append(f"! Node graph: {self.name}")
        lines.append(f"! Generated by Ergo node graph compiler")
        lines.append("")
        lines.append("IMPLICIT NONE")
        lines.append("")

        # Emit parameters
        for param in self.parameters:
            ergo_type = param.type.value
            if isinstance(param.value, float):
                val = repr(param.value)
            else:
                val = str(param.value)
            lines.append(f"PARAMETER {ergo_type} :: {param.name} = {val}")

        if self.parameters:
            lines.append("")

        # Map node outputs to variable names
        var_names: dict[tuple[str, str], str] = {}  # (node_id, pin_name) -> var_name

        # Assign names to graph inputs
        for nid in order:
            node = self.nodes[nid]
            if node.op == "input":
                var_name = node.pin_name or f"_in_{nid}"
                for pin in node.output_pins():
                    var_names[(nid, pin.name)] = var_name

        # Assign names to constants
        for nid in order:
            node = self.nodes[nid]
            if node.op == "constant":
                var_names[(nid, "out")] = f"_c_{nid}"

        # Assign names to intermediate nodes
        for nid in order:
            node = self.nodes[nid]
            if node.op not in ("constant", "input", "output"):
                for pin in node.output_pins():
                    var_names[(nid, pin.name)] = f"_{nid}"

        # Collect variable declarations by type
        decls: dict[str, list[str]] = {}  # type -> [var names]

        # Declare graph input variables
        for nid in order:
            node = self.nodes[nid]
            if node.op == "input":
                ptype = (node.pin_type or PinType.REAL).value
                vname = var_names[(nid, node.pin_name or "value")]
                decls.setdefault(ptype, []).append(vname)

        # Declare constant variables
        for nid in order:
            node = self.nodes[nid]
            if node.op == "constant":
                ptype = (node.const_type or PinType.REAL).value
                vname = var_names[(nid, "out")]
                decls.setdefault(ptype, []).append(vname)

        # Declare intermediate variables
        for nid in order:
            node = self.nodes[nid]
            if node.op not in ("constant", "input", "output"):
                for pin in node.output_pins():
                    ptype = pin.type.value
                    vname = var_names[(nid, pin.name)]
                    decls.setdefault(ptype, []).append(vname)

        # Declare output variables
        for nid in order:
            node = self.nodes[nid]
            if node.op == "output":
                ptype = (node.pin_type or PinType.REAL).value
                vname = node.pin_name or f"_out_{nid}"
                decls.setdefault(ptype, []).append(vname)

        for type_name, names in sorted(decls.items()):
            lines.append(f"{type_name} :: {', '.join(names)}")

        lines.append("")

        # Build lookup: for each input pin, what variable feeds it?
        input_source: dict[tuple[str, str], str] = {}
        for edge in self.edges:
            src_var = var_names.get((edge.src_node, edge.src_pin))
            if src_var:
                input_source[(edge.dst_node, edge.dst_pin)] = src_var

        # Emit constants
        for nid in order:
            node = self.nodes[nid]
            if node.op == "constant":
                vname = var_names[(nid, "out")]
                val = node.const_value
                if isinstance(val, float):
                    val_str = repr(val)
                else:
                    val_str = str(val)
                lines.append(f"{vname} := {val_str}")

        # Emit operations in topological order
        for nid in order:
            node = self.nodes[nid]
            if node.op in ("constant", "input", "output"):
                continue

            defn = node.definition
            if defn is None:
                lines.append(f"! ERROR: unknown op {node.op}")
                continue

            # Build substitution dict: pin_name -> source variable
            subs = {}
            for pin in defn.inputs:
                src_var = input_source.get((nid, pin.name))
                if src_var:
                    subs[pin.name] = src_var
                else:
                    subs[pin.name] = f"/* UNCONNECTED:{pin.name} */"

            # Handle Switch specially
            if node.op == "Switch":
                out_var = var_names[(nid, "out")]
                lines.append(f"IF {subs['cond']} THEN")
                lines.append(f"  {out_var} := {subs['t']}")
                lines.append(f"ELSE")
                lines.append(f"  {out_var} := {subs['f']}")
                lines.append(f"ENDIF")
                continue

            # General case: template substitution
            expr = defn.template.format(**subs)
            out_var = var_names[(nid, defn.outputs[0].name)]
            lines.append(f"{out_var} := {expr}")

        lines.append("")

        # Emit outputs (PRINT for now, or assign to output vars)
        for nid in order:
            node = self.nodes[nid]
            if node.op == "output":
                out_name = node.pin_name or f"_out_{nid}"
                src_var = input_source.get((nid, out_name))
                if src_var is None:
                    src_var = input_source.get((nid, "value"))
                if src_var:
                    lines.append(f"PRINT {src_var}")

        lines.append("")
        lines.append("STOP")
        return "\n".join(lines) + "\n"

    # ── serialization ────────────────────────────────────

    def to_json(self) -> str:
        """Serialize to JSON."""
        data = {
            "name": self.name,
            "version": "0.1",
            "parameters": [
                {"name": p.name, "type": p.type.value, "value": p.value}
                for p in self.parameters
            ],
            "nodes": [
                self._node_to_dict(n) for n in self.nodes.values()
            ],
            "edges": [
                {
                    "src": f"{e.src_node}:{e.src_pin}",
                    "dst": f"{e.dst_node}:{e.dst_pin}",
                }
                for e in self.edges
            ],
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def from_json(text: str) -> Graph:
        """Deserialize from JSON."""
        data = json.loads(text)
        g = Graph(name=data["name"])

        for p in data.get("parameters", []):
            g.parameters.append(GraphParam(
                name=p["name"],
                type=PinType(p["type"]),
                value=p["value"],
            ))

        for nd in data["nodes"]:
            node = Node(
                id=nd["id"],
                op=nd["op"],
                position=tuple(nd.get("position", [0, 0])),
            )
            if "const_type" in nd:
                node.const_type = PinType(nd["const_type"])
            if "const_value" in nd:
                node.const_value = nd["const_value"]
            if "pin_name" in nd:
                node.pin_name = nd["pin_name"]
            if "pin_type" in nd:
                node.pin_type = PinType(nd["pin_type"])
            g.nodes[node.id] = node

        for ed in data["edges"]:
            src_parts = ed["src"].split(":")
            dst_parts = ed["dst"].split(":")
            g.edges.append(Edge(
                src_node=src_parts[0], src_pin=src_parts[1],
                dst_node=dst_parts[0], dst_pin=dst_parts[1],
            ))

        return g

    def _node_to_dict(self, n: Node) -> dict:
        d: dict[str, Any] = {
            "id": n.id,
            "op": n.op,
            "position": list(n.position),
        }
        if n.const_type is not None:
            d["const_type"] = n.const_type.value
        if n.const_value is not None:
            d["const_value"] = n.const_value
        if n.pin_name is not None:
            d["pin_name"] = n.pin_name
        if n.pin_type is not None:
            d["pin_type"] = n.pin_type.value
        return d

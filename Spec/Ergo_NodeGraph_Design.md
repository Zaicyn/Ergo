# Ergo Node Graph — Design Specification

*Draft v0.1 — 2026-04-18*

## Motivation

Ergo is deterministic. Every operation is a pure function of its inputs. There are
no hidden allocations, no evaluation reordering, no side effects through aliased state.

This makes Ergo ideal for visual node-graph programming:
- Every node is a typed function: inputs on the left, outputs on the right.
- Every edge is a typed value. Type mismatches are visually obvious and statically rejected.
- Execution order is unambiguous — determined by the DAG topology.
- The graph compiles to flat Ergo source, which compiles to C. No interpreter needed.

Target rendering: **Nuklear Immediate Mode** (C, already in use).

---

## Core Concepts

### 1. Node

A node is a typed operation with named input pins and named output pins.

```
+---------------------------+
|  NERNST_POTENTIAL         |
|                           |
|  [REAL] ion_out  ──►  [REAL] E  |
|  [REAL] ion_in   ──►         |
|  [REAL] RT_F     ──►         |
+---------------------------+
```

Every node maps to one of:
- **Intrinsic**: a built-in Ergo operation (SIN, CLAMP, ISHFT, +, -, *, /, etc.)
- **Expression**: a compound expression (e.g., `RT_F * LOG10(ion_out / ion_in)`)
- **Subgraph**: a collapsed group of nodes (compiles to an Ergo FUNCTION)
- **Constant**: a PARAMETER value (no inputs, one output)
- **Input/Output**: external interface pins for the graph boundary

### 2. Pin

A pin is a named, typed connection point on a node.

```
Pin {
    name:      str          -- "ion_out", "result", "x"
    type:      ErgoType     -- REAL, INTEGER, LOGICAL, REAL(N), INTEGER(N,M)
    direction: IN | OUT
    shape:     tuple | None -- None = scalar, (10,) = 1D array, (8, 2) = 2D
}
```

**Type rules on pins:**
- Scalar pins carry a single value.
- Array pins carry a shape. The shape must be compile-time known (PARAMETER or literal).
- PARAMETER pins are always scalar constants.

### 3. Edge

An edge connects one output pin to one input pin.

```
Edge {
    src_node:  NodeID
    src_pin:   str      -- output pin name
    dst_node:  NodeID
    dst_pin:   str      -- input pin name
}
```

**Validation rules:**
- Type must match: `src.type == dst.type` (or valid promotion: INTEGER -> REAL).
- Shape must match exactly (no implicit reshape).
- One-to-many is allowed (one output feeds multiple inputs — fan-out).
- Many-to-one is forbidden (no implicit merge).
- Cycles are forbidden (DAG only — deterministic execution order).

### 4. Graph

```
Graph {
    name:       str
    nodes:      dict[NodeID, Node]
    edges:      list[Edge]
    parameters: list[Parameter]   -- compile-time constants visible to all nodes
    inputs:     list[Pin]         -- graph-level input interface
    outputs:    list[Pin]         -- graph-level output interface
}
```

---

## Node Categories

### Arithmetic Nodes

Single operation, maps directly to one Ergo operator.

| Node       | Inputs          | Output     | Ergo        |
|------------|-----------------|------------|-------------|
| Add        | a:REAL, b:REAL  | out:REAL   | `a + b`     |
| Sub        | a:REAL, b:REAL  | out:REAL   | `a - b`     |
| Mul        | a:REAL, b:REAL  | out:REAL   | `a * b`     |
| Div        | a:REAL, b:REAL  | out:REAL   | `a / b`     |
| Pow        | base:REAL, exp:REAL | out:REAL | `base ** exp` |
| Negate     | x:REAL          | out:REAL   | `-x`        |

### Math Intrinsic Nodes

| Node     | Inputs        | Output    | Ergo         |
|----------|---------------|-----------|--------------|
| Sin      | x:REAL        | out:REAL  | `SIN(x)`     |
| Cos      | x:REAL        | out:REAL  | `COS(x)`     |
| Sqrt     | x:REAL        | out:REAL  | `SQRT(x)`    |
| Abs      | x:REAL        | out:REAL  | `ABS(x)`     |
| Log10    | x:REAL        | out:REAL  | `LOG10(x)`   |
| Exp      | x:REAL        | out:REAL  | `EXP(x)`     |
| Atan2    | y:REAL, x:REAL| out:REAL  | `ATAN2(y,x)` |
| Clamp    | x:REAL, lo:REAL, hi:REAL | out:REAL | `CLAMP(x,lo,hi)` |
| Max      | a:REAL, b:REAL | out:REAL | `MAX(a,b)`   |
| Min      | a:REAL, b:REAL | out:REAL | `MIN(a,b)`   |
| Mod      | a:INT, b:INT   | out:INT  | `MOD(a,b)`   |

### Comparison Nodes

| Node     | Inputs         | Output      | Ergo       |
|----------|----------------|-------------|------------|
| Less     | a:REAL, b:REAL | out:LOGICAL | `a < b`    |
| Greater  | a:REAL, b:REAL | out:LOGICAL | `a > b`    |
| Equal    | a:REAL, b:REAL | out:LOGICAL | `a = b`    |
| NotEqual | a:REAL, b:REAL | out:LOGICAL | `a != b`   |
| LessEq   | a:REAL, b:REAL | out:LOGICAL | `a <= b`  |
| GreaterEq| a:REAL, b:REAL | out:LOGICAL | `a >= b`  |

### Logic Nodes

| Node  | Inputs                    | Output      | Ergo         |
|-------|---------------------------|-------------|--------------|
| And   | a:LOGICAL, b:LOGICAL      | out:LOGICAL | `a .AND. b`  |
| Or    | a:LOGICAL, b:LOGICAL      | out:LOGICAL | `a .OR. b`   |
| Not   | a:LOGICAL                 | out:LOGICAL | `.NOT. a`    |

### Control Flow Nodes

These are structural — they change execution topology, not just data flow.

| Node       | Inputs                        | Outputs        | Ergo equivalent      |
|------------|-------------------------------|----------------|----------------------|
| Switch     | cond:LOGICAL, t:REAL, f:REAL  | out:REAL       | `IF cond THEN t ELSE f` |
| Select     | idx:INTEGER, vals:REAL[N]     | out:REAL       | `SELECT CASE (idx)`  |

### Conversion Nodes

| Node    | Inputs        | Output        | Ergo        |
|---------|---------------|---------------|-------------|
| ToReal  | x:INTEGER     | out:REAL      | `REAL(x)`   |
| ToInt   | x:REAL        | out:INTEGER   | `INT(x)`    |
| ToChar  | x:INTEGER     | out:CHARACTER | `CHAR(x)`   |
| ToIChar | x:CHARACTER   | out:INTEGER   | `ICHAR(x)`  |

### Bitwise Nodes

| Node   | Inputs              | Output     | Ergo            |
|--------|---------------------|------------|-----------------|
| ISHFT  | val:INT, shift:INT  | out:INT    | `ISHFT(val,s)`  |
| IEOR   | a:INT, b:INT        | out:INT    | `IEOR(a,b)`     |
| IAND   | a:INT, b:INT        | out:INT    | `IAND(a,b)`     |
| IOR    | a:INT, b:INT        | out:INT    | `IOR(a,b)`      |
| BitNot | a:INT               | out:INT    | `NOT(a)`        |

### Constant / Parameter Nodes

No inputs. Single output. Value is compile-time fixed.

```
+------------------+
|  CONST: 9.80665  |
|           [REAL] out ──►
+------------------+
```

Compiles to `PARAMETER REAL :: _node_42 = 9.80665`.

### Subgraph Node

A collapsed group of nodes. Exposes selected internal pins as external interface.
Compiles to an Ergo `FUNCTION` definition.

```
+-----------------------------+
|  NERNST  [subgraph]        |
|                             |
|  [REAL] ion_out  ──►  [REAL] E  |
|  [REAL] ion_in   ──►       |
|  [REAL] RT_F     ──►       |
+-----------------------------+
```

Compiles to:
```
REAL FUNCTION NERNST(ion_out, ion_in, RT_F)
  REAL :: ion_out, ion_in, RT_F
  NERNST := RT_F * LOG10(ion_out / ion_in)
  RETURN NERNST
END
```

---

## Execution Model

### Topological Sort → Sequential Ergo

The graph is a DAG. Compile to Ergo by topological sort:

1. Collect all nodes with no incoming edges (constants, inputs).
2. Compute each node's output as a named temporary.
3. Emit in dependency order.

Example graph:

```
  [CONST 5.0] ──► [a] Add ──► [x] Sin ──► [out]
  [CONST 3.0] ──► [b]
```

Compiles to:
```
PARAMETER REAL :: _c0 = 5.0
PARAMETER REAL :: _c1 = 3.0
REAL :: _add_0, _sin_0

_add_0 := _c0 + _c1
_sin_0 := SIN(_add_0)
PRINT _sin_0
```

### Naming Convention

Each node gets a deterministic name: `_<type>_<id>` where `id` is the topological
order index. This ensures:
- No name collisions.
- Reproducible output across compilations.
- Generated code is readable (you can trace `_clamp_7` back to node 7).

---

## Tick-Based Execution (Simulation Integration)

For simulation use cases (membrane model, colony sim), nodes execute per-tick
inside a DO loop. The graph represents **one tick's computation**.

```
Graph: membrane_tick
  Inputs:  PSI, HIN, KIN, ATP, MSHINT
  Outputs: PSI', HIN', KIN', ATP'

  [Internal nodes: Nernst, Leak, Pump, Harvest, Decay, Update]
```

Compiles to:
```
DO IT = 1, NTICK
  ! -- Unrolled graph nodes in dependency order --
  EK := NERNST * LOG10(KOUT / KIN)
  GK := GK0 * (1.0 - 0.95 * MSHINT)
  IK := GK * (PSI - EK)
  ...
  PSI := PSI + DPSIDT
ENDDO
```

The graph boundary (inputs/outputs) maps to the loop's state variables.
The graph interior maps to the loop body.

---

## Serialization Format

JSON, human-readable, diffable. One file per graph.

```json
{
  "name": "nernst_potential",
  "version": "0.1",
  "parameters": [
    {"name": "RT_F", "type": "REAL", "value": 61.5}
  ],
  "nodes": [
    {
      "id": "log10_0",
      "type": "intrinsic",
      "op": "LOG10",
      "position": [200, 150]
    },
    {
      "id": "div_0",
      "type": "intrinsic",
      "op": "Div",
      "position": [100, 150]
    },
    {
      "id": "mul_0",
      "type": "intrinsic",
      "op": "Mul",
      "position": [300, 150]
    }
  ],
  "edges": [
    {"src": "input:ion_out", "dst": "div_0:a"},
    {"src": "input:ion_in",  "dst": "div_0:b"},
    {"src": "div_0:out",     "dst": "log10_0:x"},
    {"src": "log10_0:out",   "dst": "mul_0:a"},
    {"src": "param:RT_F",    "dst": "mul_0:b"},
    {"src": "mul_0:out",     "dst": "output:E"}
  ],
  "inputs": [
    {"name": "ion_out", "type": "REAL"},
    {"name": "ion_in",  "type": "REAL"}
  ],
  "outputs": [
    {"name": "E", "type": "REAL"}
  ]
}
```

---

## Validation Pipeline

Graph validation mirrors the Ergo checker, operating on the graph structure:

### 1. Structural Validation
- No cycles (topological sort succeeds).
- Every input pin has exactly one incoming edge (or a default value).
- No dangling output pins on boundary nodes.

### 2. Type Validation
- Edge source type matches edge destination type (with INTEGER->REAL promotion).
- Shape compatibility on array edges.

### 3. Semantic Validation
- Constants are compile-time evaluable.
- Subgraph recursion is bounded (no graph calling itself).
- Array dimensions resolve to PARAMETER values.

### 4. Compilation
- Topological sort → flat Ergo source.
- Ergo checker validates the generated source (double-check).
- Codegen → C → gcc.

---

## Nuklear Integration Notes

Nuklear immediate mode maps cleanly to this model:

- **Node rendering**: `nk_begin()` per node, pins as `nk_layout_row_dynamic()` rows.
- **Edge rendering**: Bezier curves between pin positions (`nk_stroke_curve()`).
- **Pin interaction**: circle widgets at pin positions; drag from output to input to create edge.
- **Type coloring**:
  - REAL pins → blue
  - INTEGER pins → green
  - LOGICAL pins → orange
  - CHARACTER pins → pink
  - Array pins → same color with thickness proportional to rank

- **Node coloring by category**:
  - Arithmetic → gray
  - Intrinsic → teal
  - Control flow → yellow
  - Constant → white
  - Subgraph → purple border
  - Input/Output → red/green

- **Context menu**: right-click canvas → node palette, organized by category.
- **Subgraph collapse**: select nodes → right-click → "Collapse to Subgraph".
- **Live preview**: with determinism, can evaluate the graph in real-time as nodes are connected.

---

## Compilation Targets

A graph can compile to multiple targets:

| Target          | Output                        | Use case                |
|-----------------|-------------------------------|-------------------------|
| Ergo source     | `.ergo` file                   | Human-readable, editable|
| C executable    | Binary via gcc                | Standalone simulation   |
| C function      | `.c` + `.h` pair              | Embed in larger program |
| Tick function   | Function called per-timestep  | Simulation loop body    |
| Nuklear live    | Immediate evaluation in GUI   | Interactive prototyping |

---

## Future: Bidirectional Editing

Because Ergo source and node graphs are semantically equivalent:

- **Graph → Source**: topological sort, emit Ergo statements.
- **Source → Graph**: parse Ergo, reconstruct dependency DAG, infer node positions.

This means a user could:
1. Build a graph visually.
2. Export to `.ergo`.
3. Hand-edit the `.ergo` (add optimizations, restructure).
4. Re-import into the graph editor.

Round-trip fidelity is possible because Ergo has no hidden state — the graph
and the source contain exactly the same information.

---

## Implementation Phases

### Phase A: Data Model (Python)
- `Node`, `Pin`, `Edge`, `Graph` dataclasses.
- JSON serialization/deserialization.
- Graph validation (cycles, types, shapes).
- Graph → Ergo source compilation.
- Unit tests: validate → compile → run → check output.

### Phase B: Nuklear Renderer (C)
- Load graph JSON.
- Render nodes and edges with Nuklear.
- Pin drag-and-drop for edge creation.
- Node palette and context menu.
- Type-colored pins and edges.

### Phase C: Interactive Editing
- Add/remove nodes and edges in GUI.
- Undo/redo stack.
- Subgraph collapse/expand.
- Auto-layout (topological layers, minimize edge crossings).
- Live compilation preview.

### Phase D: Simulation Integration
- Tick-based graph execution.
- State variable binding (graph inputs/outputs ↔ simulation state).
- Real-time parameter adjustment (slide a PARAMETER, see output change).
- Integration with existing Ergo simulations (membrane, colony).

---

## Design Principles

1. **The graph IS the program.** Not a sketch, not a diagram. It compiles.
2. **No hidden evaluation.** Every operation is a visible node. Every data flow is a visible edge.
3. **Types are visual.** Pin colors encode types. Shape mismatches are impossible to connect.
4. **Deterministic layout.** Same graph → same source → same binary → same output. Always.
5. **Bidirectional.** Graph ↔ Source. Neither is "primary". Both are views of the same program.

---

## Implementation Status (2026-08, Phase A complete)

**Working and gated** (`tests/nodegraph/run_nodegraph.py`, 11/11,
wired into the golden gate):

- Data model, validation (cycles, types, fan-in, unconnected pins,
  unknown ops, undeclared parameters), deterministic topological
  compile to Ergo source — `core/nodegraph.py`.
- JSON serialization **in the schema of this document** (top-level
  `inputs`/`outputs`, `input:`/`output:`/`param:` edge refs);
  round-trip is text-stable. `input` pins accept a `"value"` default
  (standalone-target initializer; absent = 0/false).
- CLI route: `python -m core <graph>.json [-o bin]` compiles a graph
  straight to a binary; `--emit-ergo` prints the generated Ergo
  source (the readable/editable target from the Compilation Targets
  table), `--emit-c` the C.
- Examples: `tests/nodegraph/nernst.json` (the §Serialization graph,
  verified against the analytic Nernst potential),
  `tests/nodegraph/signal_condition.json` (constants, comparison,
  fan-out, Switch → IF/ELSE).

**Deferred (roadmap, honest gaps):**

- **Subgraph nodes** (collapse → Ergo FUNCTION): catalog/validation
  have no subgraph support yet. This is the next implementation
  tranche; the boundary machinery (input/output pins + defaults)
  already matches what a FUNCTION lowering needs.
- **Array/shape pins**: `Pin.shape` exists in the model but no
  catalog node consumes arrays and compile() emits scalars only.
- **Select node** (SELECT CASE): not implemented; Switch (IF/ELSE)
  is.
- **Tick-based execution** (Phase D): design-only. The graph boundary
  maps to loop state as specified here; no lowering exists.
- **Nuklear renderer / interactive editing** (Phases B–C): not
  started; `position` fields round-trip through JSON for it.
- **Source → graph** direction of bidirectional editing: not started.

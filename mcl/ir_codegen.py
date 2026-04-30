"""C99 code generator from Ergo IR.

Consumes an IRModule and produces C99 source code. This replaces the
direct AST-to-C codegen path — the pipeline is now:

    AST -> Checker -> IR -> C99

The existing AST codegen (codegen.py) is preserved as a reference and fallback.
"""

from __future__ import annotations

from .ir import (
    IRModule, IRFunc, IRVar, IRBlock, IRIf, IRLoop, IRSelect, IRWhileLoop,
    IRInst, IRConst, IRRef, IRType, StorageClass, Op, Operand,
)
from .ir_gpu import GPUPlan, KernelPlan
from . import ast_nodes as ast


def _c_type(t: IRType) -> str:
    """Map IR type to C type, respecting precision setting."""
    if t == IRType.REAL:
        return IRType.REAL.c_type  # "float" or "double" per global precision
    return {
        IRType.INTEGER: "int",
        IRType.LOGICAL: "int",
        IRType.CHARACTER: "char",
        IRType.STRING: "const char*",
        IRType.VOID: "void",
    }[t]

# Legacy dict — some code paths still use this directly
C_TYPE = {
    IRType.INTEGER: "int",
    IRType.LOGICAL: "int",
    IRType.CHARACTER: "char",
    IRType.STRING: "const char*",
    IRType.VOID: "void",
}

# Math intrinsics -> C function name
C_MATH = {
    Op.SIN: "sin", Op.COS: "cos", Op.TAN: "tan",
    Op.ASIN: "asin", Op.ACOS: "acos", Op.ATAN: "atan", Op.ATAN2: "atan2",
    Op.EXP: "exp", Op.LOG: "log", Op.LOG10: "log10",
    Op.SQRT: "sqrt", Op.SINH: "sinh", Op.COSH: "cosh", Op.TANH: "tanh",
}


class IRCodeGen:
    def __init__(self, module: IRModule, gpu_plan: GPUPlan | None = None,
                 backend=None, render: bool = False, jit_mode: bool = False):
        self.module = module
        self.gpu_plan = gpu_plan
        self.backend = backend
        self.render = render
        self.jit_mode = jit_mode
        self._in_frame_loop = False
        self._batched_frame = False  # True inside batched frame dispatch loop
        self._frame_ended_early = False  # True when frame_end emitted before CPU suffix
        self.lines: list[str] = []
        self.indent = 0
        self._last_line_directive = 0
        # Track var types for PRINT format inference
        self._var_types: dict[str, IRType] = {}
        # Track arrays for subscript codegen
        self._array_shapes: dict[str, tuple] = {}
        # Track function return types
        self._func_return_types: dict[str, IRType] = {}

        # Build kernel lookup: loop source line -> KernelPlan
        # Used by _emit_loop to decide whether to emit dispatch or for-loop
        self._kernel_by_line: dict[int, KernelPlan] = {}
        if gpu_plan:
            for k in gpu_plan.kernels:
                self._kernel_by_line[k.source_line] = k

        # Track arrays recently uploaded to GPU (cleared on CPU write).
        # Used to eliminate redundant uploads in the merged render+sync pass.
        self._gpu_current: set[str] = set()

        # Pre-analyze subroutine array access for GPU sync around CPU calls.
        # Maps func_name -> (arrays_read, arrays_written)
        self._sub_array_access: dict[str, tuple[set[str], set[str]]] = {}
        for func in module.functions:
            reads: set[str] = set()
            writes: set[str] = set()
            self._collect_array_reads(func.body, reads)
            self._collect_array_writes(func.body, writes)
            if reads or writes:
                self._sub_array_access[func.name] = (reads, writes)

    def _detect_particle_soa(self) -> dict | None:
        """Detect SoA particle simulation pattern.

        Returns dict with buffer names if POS_X, POS_Y, POS_Z arrays exist,
        plus best color array candidate. Returns None if not a particle sim.
        """
        arrays = self._array_shapes
        has_px = "POS_X" in arrays
        has_py = "POS_Y" in arrays
        has_pz = "POS_Z" in arrays
        if not (has_px and has_py and has_pz):
            return None

        # Find best color array: prefer OMEGA_NAT, then THETA, then POS_X
        color_arr = "POS_X"
        for candidate in ["OMEGA_NAT", "THETA", "PUMP_SCALE", "VEL_X"]:
            if candidate in arrays:
                t = self._var_types.get(candidate, IRType.REAL)
                if t == IRType.REAL:
                    color_arr = candidate
                    break

        # Find the particle count variable (usually NPART or N)
        count_var = None
        for name in ["NPART", "N_PART", "N", "NUM_PARTICLES"]:
            if name in self._var_types:
                count_var = name
                break

        # Infer world scale from DISK_OUTER_R or array size
        world_scale_expr = "1.0f / 1200.0f"  # default
        for name in ["DISK_OUTER_R", "DOMAIN_SIZE", "BOX_SIZE"]:
            if name in self._var_types:
                world_scale_expr = f"1.0f / (float){name}"
                break

        return {
            "pos_x": "POS_X", "pos_y": "POS_Y", "pos_z": "POS_Z",
            "color": color_arr,
            "count_var": count_var,
            "world_scale": world_scale_expr,
            "render_arrays": ["POS_X", "POS_Y", "POS_Z", color_arr],
        }

    def generate(self) -> str:
        mod = self.module
        has_gpu = self.gpu_plan and self.gpu_plan.kernels

        self._put_raw("#include <stdio.h>")
        self._put_raw("#include <math.h>")
        self._put_raw("#include <stdlib.h>")
        self._put_raw("#include <string.h>")
        if has_gpu or self.render:
            from .ir import get_real_precision
            if get_real_precision() == 32:
                self._put_raw("#define ERGO_F32_MODE")
            self._put_raw("#include \"ergo_vk.h\"")
        # NET clause: include UDP transport for oracle communication
        verify_meta = self._find_verify_meta(mod.main_body)
        has_net = verify_meta and verify_meta.get("net_host")
        self._has_net = has_net
        if has_net:
            self._put_raw("#include \"ergo_net.h\"")
        self._put_raw("")

        # Collect metadata
        self._collect_metadata()

        # Emit PARAMETER constants at file scope
        params = [g for g in mod.globals if g.storage == StorageClass.PARAMETER]
        for g in params:
            self._emit_line(g.line)
            ct = self._c_type(g.type)
            lit = self._const_lit(g.type, g.init_value)
            # Integer PARAMETERs must be #define so gcc accepts them as array dims
            if g.type == IRType.INTEGER:
                self._put(f"#define {g.name} {lit}")
            else:
                self._put(f"static const {ct} {g.name} = {lit};")
        if params:
            self._put_raw("")

        # Forward declarations for functions
        for fn in mod.functions:
            self._emit_forward_decl(fn)
        if mod.functions:
            self._put_raw("")

        # Emit STATIC variables at file scope
        statics = [g for g in mod.globals if g.storage == StorageClass.STATIC]
        for g in statics:
            self._emit_static_var(g, mod)
        if statics:
            self._put_raw("")

        # Embed SPIR-V binaries as byte arrays (if GPU)
        if has_gpu:
            self._emit_spirv_embeds()
            self._put_raw("")

        # Emit functions
        for fn in mod.functions:
            self._emit_function(fn)
            self._put_raw("")

        # JIT mode: no main(), just export functions + statics
        if self.jit_mode:
            return "\n".join(self.lines) + "\n"

        # Emit main
        self._put("int main(int argc, char *argv[]) {")
        self.indent += 1

        # Runtime CLI parsing
        self._emit_cli_parsing()

        # Declare main locals
        for v in mod.main_locals:
            self._emit_local_decl(v, mod)

        # Declare SSA temporaries
        self._emit_temps(mod.main_body)

        # Oracle shadow arrays (if any VERIFY statements exist)
        self._emit_oracle_decls(mod.main_body)

        # GPU init: Vulkan, buffers, pipelines
        if has_gpu:
            self._put_raw("")
            self._emit_gpu_init()
        elif self.render:
            # Render-only mode (no GPU kernels): init Vulkan + create
            # buffers for the arrays we need to visualize
            self._put_raw("")
            self._emit_render_only_init()

        # Emit main body
        self._emit_body(mod.main_body)

        # GPU shutdown
        if has_gpu or self.render:
            self._put("ergo_vk_shutdown();")

        # NET shutdown
        if has_net:
            self._put("if (_consensus_enabled) ergo_net_close(&_ergo_net);")

        self._put("return 0;")
        self.indent -= 1
        self._put("}")

        return "\n".join(self.lines) + "\n"

    # ── metadata ─────────────────────────────────────────────

    def _collect_metadata(self):
        mod = self.module
        for g in mod.globals:
            self._var_types[g.name] = g.type
            if g.shape:
                self._array_shapes[g.name] = g.shape
        for fn in mod.functions:
            self._func_return_types[fn.name] = fn.return_type
            for p in fn.params:
                self._var_types[p.name] = p.type
                if p.shape:
                    self._array_shapes[p.name] = p.shape
            for v in fn.locals:
                self._var_types[v.name] = v.type
                if v.shape:
                    self._array_shapes[v.name] = v.shape
        for v in mod.main_locals:
            self._var_types[v.name] = v.type
            if v.shape:
                self._array_shapes[v.name] = v.shape

    # ── helpers ──────────────────────────────────────────────

    def _put(self, line: str):
        self.lines.append("    " * self.indent + line)

    def _put_raw(self, line: str):
        self.lines.append(line)

    def _c_type(self, t: IRType) -> str:
        return _c_type(t)

    def _emit_line(self, line: int):
        if self.module.source_file and line > 0:
            if line != self._last_line_directive:
                self._put_raw(f'#line {line} "{self.module.source_file}"')
                self._last_line_directive = line

    def _const_lit(self, t: IRType, value) -> str:
        if t == IRType.REAL:
            s = repr(value) if isinstance(value, float) else str(value)
            if "." not in s and "e" not in s.lower():
                s += ".0"
            return s
        if t == IRType.INTEGER:
            return str(value)
        if t == IRType.LOGICAL:
            return "1" if value else "0"
        if t == IRType.STRING:
            return f'"{value}"'
        return str(value)

    def _operand(self, op: Operand) -> str:
        if isinstance(op, IRConst):
            return self._const_lit(op.type, op.value)
        if isinstance(op, IRRef):
            return op.name
        return "/* ? */"

    # ── static vars ──────────────────────────────────────────

    def _emit_static_var(self, g: IRVar, mod: IRModule):
        ct = self._c_type(g.type)
        if g.shape:
            dims = "".join(f"[{self._dim_expr(d)}]" for d in g.shape)
            init = self._data_init(g.name, mod)
            self._put(f"static {ct} {g.name}{dims}{init};")
        else:
            init = ""
            if g.init_value is not None:
                init = f" = {self._const_lit(g.type, g.init_value)}"
            elif g.name in mod.data_inits:
                vals = mod.data_inits[g.name]
                if vals:
                    init = f" = {self._const_lit(g.type, self._ast_lit_value(vals[0]))}"
            self._put(f"static {ct} {g.name}{init};")

    def _data_init(self, name: str, mod: IRModule) -> str:
        if name not in mod.data_inits:
            return ""
        vals = mod.data_inits[name]
        if not vals:
            return ""
        val_strs = [self._ast_lit_str(v) for v in vals]
        return " = {" + ", ".join(val_strs) + "}"

    def _ast_lit_str(self, node) -> str:
        """Convert an AST literal to a C literal string."""
        if isinstance(node, ast.Literal):
            if node.type == "REAL":
                s = repr(node.value)
                if "." not in s and "e" not in s.lower():
                    s += ".0"
                return s
            if node.type == "INTEGER":
                return str(node.value)
        return "0"

    def _ast_lit_value(self, node) -> any:
        if isinstance(node, ast.Literal):
            return node.value
        return 0

    def _dim_expr(self, d) -> str:
        """Convert an IR shape dimension (could be AST node or int) to C."""
        if isinstance(d, int):
            return str(d)
        if isinstance(d, ast.Literal):
            return str(d.value)
        if isinstance(d, str):
            return d
        return str(d)

    def _resolve_const(self, operand) -> int | None:
        """Try to resolve an IR operand to a compile-time integer.

        Handles IRConst directly and IRRef to PARAMETER globals.
        Returns None if the value cannot be resolved.
        """
        if isinstance(operand, IRConst):
            if operand.type == IRType.INTEGER:
                return operand.value
            return None
        if isinstance(operand, IRRef):
            # Check if it's a PARAMETER (compile-time constant)
            for g in self.module.globals:
                if g.name == operand.name and g.storage == StorageClass.PARAMETER:
                    if g.init_value is not None and g.type == IRType.INTEGER:
                        return g.init_value
            return None
        return None

    # ── forward declarations ─────────────────────────────────

    def _emit_forward_decl(self, fn: IRFunc):
        params = self._func_param_str(fn)
        if fn.is_subroutine:
            self._put(f"void {fn.name}({params});")
        else:
            ret = self._c_type(fn.return_type)
            self._put(f"{ret} {fn.name}({params});")

    def _func_param_str(self, fn: IRFunc) -> str:
        if not fn.params:
            return "void"
        parts = []
        for p in fn.params:
            ct = self._c_type(p.type)
            if p.shape:
                if len(p.shape) == 1:
                    parts.append(f"{ct} {p.name}[]")
                else:
                    dims = "".join(f"[{self._dim_expr(d)}]" for d in p.shape[1:])
                    parts.append(f"{ct} {p.name}[][{dims[1:-1]}]" if len(p.shape) > 1 else f"{ct} *{p.name}")
            else:
                parts.append(f"{ct} {p.name}")
        return ", ".join(parts)

    # ── functions ────────────────────────────────────────────

    def _emit_function(self, fn: IRFunc):
        params = self._func_param_str(fn)
        if fn.is_subroutine:
            self._put(f"void {fn.name}({params}) {{")
        else:
            ret = self._c_type(fn.return_type)
            self._put(f"{ret} {fn.name}({params}) {{")
        self.indent += 1

        # Register params in var_types
        param_set = set(p.name for p in fn.params)
        for p in fn.params:
            self._var_types[p.name] = p.type
            if p.shape:
                self._array_shapes[p.name] = p.shape

        # Declare locals
        for v in fn.locals:
            if v.name not in param_set:
                self._emit_local_decl_simple(v)

        # Declare SSA temporaries
        self._emit_temps(fn.body)

        # Emit body — disable GPU dispatch in subroutine functions.
        # GPU dispatches only happen in main() where the inlined code
        # and GPU buffer/pipeline variables live.
        saved_kernel_map = self._kernel_by_line
        self._kernel_by_line = {}
        self._emit_body(fn.body)
        self._kernel_by_line = saved_kernel_map

        self.indent -= 1
        self._put("}")

    # ── local declarations ───────────────────────────────────

    def _emit_local_decl(self, v: IRVar, mod: IRModule):
        self._emit_line(v.line)
        ct = self._c_type(v.type)
        if v.storage == StorageClass.PARAMETER:
            init = self._const_lit(v.type, v.init_value)
            self._put(f"const {ct} {v.name} = {init};")
        elif v.storage == StorageClass.ALLOCATABLE:
            self._put(f"{ct} *{v.name} = NULL;")
        elif v.shape:
            dims = "".join(f"[{self._dim_expr(d)}]" for d in v.shape)
            init = self._data_init(v.name, mod)
            self._put(f"{ct} {v.name}{dims}{init};")
        else:
            init = ""
            if v.init_value is not None:
                init = f" = {self._const_lit(v.type, v.init_value)}"
            self._put(f"{ct} {v.name}{init};")

    def _emit_local_decl_simple(self, v: IRVar):
        ct = self._c_type(v.type)
        if v.storage == StorageClass.PARAMETER:
            init = self._const_lit(v.type, v.init_value)
            self._put(f"const {ct} {v.name} = {init};")
        elif v.storage == StorageClass.ALLOCATABLE:
            self._put(f"{ct} *{v.name} = NULL;")
        elif v.shape:
            dims = "".join(f"[{self._dim_expr(d)}]" for d in v.shape)
            self._put(f"{ct} {v.name}{dims};")
        else:
            self._put(f"{ct} {v.name};")

    # ── structured body emission ─────────────────────────────

    def _emit_body(self, items: list, suppress_final_download: bool = False
                   ) -> set[str]:
        """Emit C code for a list of IR items.

        Returns the set of GPU arrays dirtied on CPU that haven't been
        uploaded yet (relevant for cross-iteration sync in loops).
        """
        # Track whether the previous item was a GPU dispatch,
        # so we know when to insert downloads for CPU access.
        last_dispatch_arrays: set[str] | None = None
        # Track arrays modified on CPU since last GPU dispatch,
        # so we can upload them before the next GPU dispatch.
        cpu_dirty_arrays: set[str] = set()
        gpu_array_set = set(self._gpu_arrays()) if self.gpu_plan else set()

        for i, item in enumerate(items):
            # If we just dispatched and this item is NOT another extracted
            # loop, the CPU is about to read — download GPU arrays first.
            # Only download arrays the CPU suffix actually reads.
            if last_dispatch_arrays is not None:
                is_gpu_loop = (isinstance(item, IRLoop) and
                               item.line in self._kernel_by_line)
                if not is_gpu_loop:
                    # In batched frame mode, defer mid-body downloads if
                    # there are more GPU dispatches ahead.  All dispatches
                    # must finish in one cmd_buf before any transfer.
                    more_dispatches = False
                    if self._batched_frame:
                        for future in items[i:]:
                            if isinstance(future, IRLoop):
                                if self._kernel_by_line.get(future.line):
                                    more_dispatches = True
                                    break
                    if more_dispatches:
                        # Keep accumulating dispatch arrays; don't download yet
                        pass
                    else:
                        # Scan remaining items to find which arrays CPU reads
                        remaining = items[i:]
                        cpu_reads: set[str] = set()
                        for ri in remaining:
                            if isinstance(ri, IRLoop):
                                k = self._kernel_by_line.get(ri.line)
                                if k:
                                    continue  # GPU kernel — skip
                            self._collect_array_reads([ri], cpu_reads)
                            self._collect_array_writes([ri], cpu_reads)
                        needed = last_dispatch_arrays & cpu_reads
                        if needed:
                            # In batched frame mode, end the GPU command buffer
                            # and wait for the fence BEFORE any host↔device
                            # transfer.  Adreno corrupts fence state if
                            # xfer_cmd_buf is submitted while the frame
                            # cmd_buf is still open.
                            if self._batched_frame and not self._frame_ended_early:
                                self._put("ergo_vk_frame_end();")
                                self._frame_ended_early = True
                            # Check if all remaining CPU reads are gated by
                            # VERIFY (every N) and conditional blocks.  If so,
                            # guard the download so pure-GPU frames skip it.
                            verify_meta = self._find_verify_meta(remaining)
                            verify_guard = (verify_meta and
                                            verify_meta.get("every", 1) > 1 and
                                            self._batched_frame)
                            if verify_guard:
                                every = verify_meta["every"]
                                self._put(f"if (!_oracle_init || "
                                          f"_oracle_frame % {every} == 0) {{")
                                self.indent += 1
                            self._put("ergo_vk_frame_wait();")
                            pp = getattr(self, '_pp_arrays', set())
                            self._put("/* Download GPU results for CPU access */")
                            for arr in sorted(needed):
                                shape = self._array_shapes.get(arr)
                                if shape:
                                    size_expr = " * ".join(
                                        self._dim_expr(d) for d in shape)
                                    sz = self._gpu_sizeof(arr)
                                    if arr in pp:
                                        self._put(
                                            f"ergo_vk_download_at(d_{arr}, {arr}, "
                                            f"(size_t)_pp_wr_offset * {sz}, "
                                            f"{size_expr} * {sz});")
                                    else:
                                        self._put(
                                            f"ergo_vk_download(d_{arr}, {arr}, "
                                            f"{size_expr} * {sz});")
                            if verify_guard:
                                self.indent -= 1
                                self._put("}")
                        last_dispatch_arrays = None

            if isinstance(item, IRBlock):
                self._emit_block(item)
                # Override starting N from JNI after SIM_INIT params are set
                if getattr(item, 'inlined_from', None) == "SIM_INIT":
                    self._put("{ extern int ergo_start_n "
                              "__attribute__((weak));")
                    self._put("  if (&ergo_start_n && ergo_start_n > 0)")
                    self._put("    _SIM_INIT_N = ergo_start_n; }")
                    # Runtime CLI: -N overrides starting particle count
                    self._put("if (_cli_n > 0) {")
                    self._put('    fprintf(stderr, "[CLI] -N %d: setting NPART\\n", _cli_n);')
                    self._put("    _SIM_INIT_N = _cli_n;")
                    self._put("}")
                    # Runtime CLI: -M caps the CAP parameter so SIM_INIT
                    # sets CAPACITY correctly downstream
                    self._put("if (_cli_m > 0) {")
                    self._put('    fprintf(stderr, "[CLI] -M %d: capping CAPACITY\\n", _cli_m);')
                    self._put("    _SIM_INIT_CAP = _cli_m;")
                    self._put("}")
                    # Runtime CLI: --no-spawn disables spawning
                    if "SPAWN_RATE" in self._var_types:
                        self._put("if (_cli_no_spawn) {")
                        self._put('    fprintf(stderr, "[CLI] --no-spawn: SPAWN_RATE = 0\\n");')
                        self._put("    SPAWN_RATE = 0.0;")
                        self._put("}")
                # Track CPU-dirty arrays from ZERO/STORE ops in blocks
                if gpu_array_set:
                    block_writes: set[str] = set()
                    self._collect_array_writes([item], block_writes)
                    block_writes &= gpu_array_set
                    # In batched mode, ZERO ops on GPU arrays emit frame_fill
                    # instead of memset — these are GPU-side ops, not CPU-dirty.
                    if self._batched_frame:
                        gpu_filled: set[str] = set()
                        for inst in item.insts:
                            if inst.op == Op.ZERO:
                                arr = inst.meta.get("array", "")
                                if arr in gpu_array_set:
                                    gpu_filled.add(arr)
                        block_writes -= gpu_filled
                    cpu_dirty_arrays |= block_writes
                    # CPU write invalidates GPU copies
                    self._gpu_current -= block_writes
            elif isinstance(item, IRIf):
                self._emit_if(item)
                # Track CPU-dirty arrays from IF body writes
                if gpu_array_set:
                    if_writes: set[str] = set()
                    self._collect_array_writes([item], if_writes)
                    if_writes &= gpu_array_set
                    cpu_dirty_arrays |= if_writes
                    self._gpu_current -= if_writes
            elif isinstance(item, IRLoop):
                # Check if this loop is a GPU dispatch
                kernel = self._kernel_by_line.get(item.line)
                if kernel and not self._is_gpu_kernel(kernel):
                    kernel = None  # init-only kernel, run on CPU
                if kernel:
                    # Upload any CPU-dirty arrays before GPU dispatch
                    if cpu_dirty_arrays:
                        # Only upload arrays this kernel actually reads
                        needed = (kernel.arrays_read | kernel.arrays_written) & cpu_dirty_arrays
                        if needed:
                            self._put("/* Upload CPU-modified arrays to GPU */")
                            for arr in sorted(needed):
                                shape = self._array_shapes.get(arr)
                                if shape:
                                    size_expr = " * ".join(
                                        self._dim_expr(d) for d in shape)
                                    sz = self._gpu_sizeof(arr)
                                    self._put(f"ergo_vk_upload(d_{arr}, {arr}, "
                                              f"{size_expr} * {sz});")
                        cpu_dirty_arrays -= (kernel.arrays_read | kernel.arrays_written)
                        self._gpu_current |= needed
                    # In batched mode, add barrier before each dispatch
                    # (covers fill→compute and compute→compute dependencies)
                    if self._batched_frame:
                        self._put("ergo_vk_frame_barrier();")
                    # Accumulate arrays written across consecutive dispatches
                    if last_dispatch_arrays is None:
                        last_dispatch_arrays = set()
                    last_dispatch_arrays |= kernel.arrays_written
                else:
                    # CPU loop — track which GPU arrays it may modify
                    cpu_writes: set[str] = set()
                    self._collect_array_writes([item], cpu_writes)
                    cpu_writes &= gpu_array_set
                    cpu_dirty_arrays |= cpu_writes
                    self._gpu_current -= cpu_writes
                self._emit_loop(item)
                # If a CPU loop contains GPU dispatches (e.g. frame loop),
                # propagate GPU-written arrays so post-loop CPU code can
                # trigger downloads.
                if not kernel and self.gpu_plan:
                    inner_gpu_written: set[str] = set()
                    def _scan_gpu_writes(body_items):
                        for bi in body_items:
                            if isinstance(bi, IRLoop):
                                ik = self._kernel_by_line.get(bi.line)
                                if ik:
                                    inner_gpu_written.update(ik.arrays_written)
                                else:
                                    _scan_gpu_writes(bi.body)
                            elif isinstance(bi, IRBlock):
                                pass  # blocks don't contain loops directly
                            elif isinstance(bi, IRIf):
                                _scan_gpu_writes(bi.then_body)
                                if bi.else_body:
                                    _scan_gpu_writes(bi.else_body)
                    _scan_gpu_writes(item.body)
                    if inner_gpu_written:
                        if last_dispatch_arrays is None:
                            last_dispatch_arrays = set()
                        last_dispatch_arrays |= inner_gpu_written
                # For SPLIT kernels, the suffix upload already synced
                # CPU-modified arrays to GPU. Clear them from dirty set.
                if kernel and kernel.is_partial:
                    suffix_writes: set[str] = set()
                    prefix_count = len(kernel.loop.body)
                    suffix_items = item.body[prefix_count:]
                    if suffix_items:
                        self._collect_array_writes(suffix_items, suffix_writes)
                        cpu_dirty_arrays -= (suffix_writes & gpu_array_set)
            elif isinstance(item, IRSelect):
                self._emit_select(item)

            elif isinstance(item, IRWhileLoop):
                self._emit_while_loop(item)

            # NET hook: detect end of inlined SIM_CENSUS_ADAPTIVE
            if (self._has_net and
                    getattr(item, 'inlined_end', None) == "SIM_CENSUS_ADAPTIVE"):
                self._put("if (_consensus_enabled) {")
                self._emit_census_net_send()
                self._put("}")

        # If the body ends after a dispatch, download for any
        # subsequent CPU code (e.g. PRINT after last loop).
        # Suppressed in frame loops where render reads GPU memory directly.
        if last_dispatch_arrays is not None and not suppress_final_download:
            if self._batched_frame and not self._frame_ended_early:
                self._put("ergo_vk_frame_end();")
                self._put("ergo_vk_frame_wait();")
                self._frame_ended_early = True
            pp = getattr(self, '_pp_arrays', set())
            self._put("/* Download GPU results for CPU access */")
            for arr in sorted(last_dispatch_arrays):
                shape = self._array_shapes.get(arr)
                if shape:
                    size_expr = " * ".join(self._dim_expr(d) for d in shape)
                    sz = self._gpu_sizeof(arr)
                    if arr in pp:
                        self._put(f"ergo_vk_download_at(d_{arr}, {arr}, "
                                  f"(size_t)_pp_wr_offset * {sz}, "
                                  f"{size_expr} * {sz});")
                    else:
                        self._put(f"ergo_vk_download(d_{arr}, {arr}, "
                                  f"{size_expr} * {sz});")
            last_dispatch_arrays = None

        return cpu_dirty_arrays

    def _emit_block(self, block: IRBlock):
        for inst in block.insts:
            self._emit_line(inst.line)
            self._emit_inst(inst)

    def _emit_if(self, node: IRIf):
        self._emit_line(node.line)
        cond = self._operand(node.condition)
        self._put(f"if ({cond}) {{")
        self.indent += 1
        self._emit_body(node.then_body)
        self.indent -= 1
        if node.else_body:
            # Check for ELSEIF chain
            if (len(node.else_body) == 1 and isinstance(node.else_body[0], IRIf)):
                inner = node.else_body[0]
                # But there might be a cond_block before it
                self._put(f"}} else {{")
                self.indent += 1
                self._emit_body(node.else_body)
                self.indent -= 1
                self._put("}")
            else:
                self._put("} else {")
                self.indent += 1
                self._emit_body(node.else_body)
                self.indent -= 1
                self._put("}")
        else:
            self._put("}")

    def _emit_loop(self, node: IRLoop):
        self._emit_line(node.line)

        # Check if this loop was extracted as a GPU kernel
        kernel = self._kernel_by_line.get(node.line)
        if kernel and not kernel.is_partial:
            if self._is_gpu_kernel(kernel):
                self._emit_gpu_dispatch(kernel)
                return
            else:
                # Kernel references arrays without GPU buffers — run on CPU
                kernel = None

        if kernel and kernel.is_partial:
            # Split kernel: dispatch the flow prefix in parallel (replaces
            # all loop iterations for those items), then a CPU loop for
            # the structural suffix that couldn't be parallelized.
            # Skip dispatch for read-only prefixes — they don't produce
            # useful GPU output and the CPU suffix runs the full loop anyway.
            if kernel.arrays_written:
                self._emit_gpu_dispatch(kernel)
            # The structural suffix is the remainder of the original
            # loop body, starting from the split point. The original
            # IRLoop still has the full body; the kernel's loop has
            # only the flow prefix. Emit the suffix items as a CPU loop.
            prefix_count = len(kernel.loop.body) if kernel.arrays_written else 0
            suffix_items = node.body[prefix_count:]
            if suffix_items:
                start = self._operand(node.start)
                end = self._operand(node.end)
                step = self._operand(node.step)
                self._emit_gpu_download_for_suffix(kernel)
                self._put(f"for (int {node.var} = {start}; {node.var} <= {end}; {node.var} += {step}) {{")
                self.indent += 1
                self._emit_body(suffix_items)
                self.indent -= 1
                self._put("}")
                self._emit_gpu_upload_after_suffix(kernel, suffix_items)
            return

        start = self._operand(node.start)
        end = self._operand(node.end)
        step = self._operand(node.step)

        # Detect frame loop: the outermost non-extracted loop that
        # contains GPU dispatches.  Used for both render and headless
        # batched dispatch.
        is_frame_loop = False
        if not self._in_frame_loop:
            if self._loop_contains_dispatch(node):
                is_frame_loop = True
            elif (self.render or self._has_net) and not kernel:
                start_val = self._resolve_const(node.start)
                end_val = self._resolve_const(node.end)
                if start_val is not None and end_val is not None:
                    iters = end_val - start_val + 1
                    if iters >= 100:
                        is_frame_loop = True

        if is_frame_loop:
            self._in_frame_loop = True
            has_gpu_dispatches = self._items_contain_dispatch(node.body)
            use_batched = has_gpu_dispatches and self.gpu_plan
            self._batched_frame = use_batched
            # Re-upload all GPU arrays before the frame loop starts,
            # in case CPU code between init and here modified them
            # (e.g. seeding initial population).
            gpu_arrays = self._gpu_arrays()
            if gpu_arrays:
                self._put("/* Sync CPU state to GPU before frame loop */")
                for arr in gpu_arrays:
                    shape = self._array_shapes.get(arr)
                    if shape:
                        size_expr = " * ".join(self._dim_expr(d) for d in shape)
                        sz = self._gpu_sizeof(arr)
                        self._put(f"ergo_vk_upload(d_{arr}, {arr}, "
                                  f"{size_expr} * {sz});")
            # Use runtime _max_frames if DEFAULT_FRAMES is the bound
            _loop_end = "_max_frames" if end == "DEFAULT_FRAMES" and "DEFAULT_FRAMES" in self._var_types else end
            self._put(f"for (int {node.var} = {start}; {node.var} <= {_loop_end}; {node.var} += {step}) {{")
            self.indent += 1
            if use_batched:
                self._put("ergo_vk_frame_begin();")
                if hasattr(self, '_pp_arrays') and self._pp_arrays:
                    self._put("/* Ping-pong: swap read/write offsets */")
                    self._put("{ int _tmp = _pp_rd_offset; _pp_rd_offset = _pp_wr_offset; _pp_wr_offset = _tmp; }")
            # NET: non-blocking drain of incoming global field from oracle.
            # If complete, replace local GRID_DENSITY before stencil.
            if self._has_net:
                self._put("if (_consensus_enabled) {")
                self._emit_field_recv()
                self._put("}")
                # Stop flag: allow graceful termination from JNI/signal
                self._put(f"{{ extern volatile int ergo_stop_requested "
                          f"__attribute__((weak));")
                self._put(f"  if (&ergo_stop_requested && "
                          f"ergo_stop_requested) break; }}")
            # Emit body; suppress final download if GPU dispatches handle it
            self._frame_ended_early = False
            frame_dirty = self._emit_body(node.body,
                            suppress_final_download=has_gpu_dispatches)

            # ── Combined upload: render + next-frame sync ──
            # Merge the render array upload and the next-frame GPU sync
            # into a single pass to eliminate redundant transfers.
            # Arrays dirtied by the CPU suffix need uploading once;
            # the render call then reads directly from GPU buffers.
            upload_set: set[str] = set()

            # Collect arrays ANY frame-loop GPU kernel reads/writes
            if frame_dirty and has_gpu_dispatches:
                all_kernel_arrays: set[str] = set()
                for bodyitem in node.body:
                    if isinstance(bodyitem, IRLoop):
                        k = self._kernel_by_line.get(bodyitem.line)
                        if k:
                            all_kernel_arrays |= k.arrays_read | k.arrays_written
                upload_set = frame_dirty & all_kernel_arrays

            # Rendering (only when --render is active)
            if self.render:
              particle = self._detect_particle_soa()
            else:
              particle = None
            if particle:
                # ── Particle cloud rendering ──
                count = particle["count_var"] or self._dim_expr(
                    self._array_shapes["POS_X"][0])
                color_arr = particle["color"]

                # Add render arrays to upload set ONLY if CPU dirtied them.
                # Arrays written by GPU kernels are already current on GPU —
                # do NOT overwrite them with stale CPU data.
                render_arrays = set(particle["render_arrays"])
                gpu_written: set[str] = set()
                for bodyitem in node.body:
                    if isinstance(bodyitem, IRLoop):
                        k = self._kernel_by_line.get(bodyitem.line)
                        if k:
                            gpu_written |= k.arrays_written
                if frame_dirty:
                    render_need_upload = render_arrays & frame_dirty - gpu_written
                else:
                    render_need_upload = set()  # GPU has current data, no upload
                upload_set |= render_need_upload

                # Single upload pass — skip arrays already on GPU
                upload_needed = upload_set - self._gpu_current - gpu_written
                if upload_needed:
                    self._put("/* Sync CPU state to GPU (render + next frame) */")
                    for arr in sorted(upload_needed):
                        shape = self._array_shapes.get(arr)
                        if shape:
                            size_expr = " * ".join(
                                self._dim_expr(d) for d in shape)
                            sz = self._gpu_sizeof(arr)
                            self._put(f"ergo_vk_upload(d_{arr}, {arr}, "
                                      f"{size_expr} * {sz});")
                    self._gpu_current |= upload_needed

                # CPU oracle scans color array for value range
                self._emit_minmax_scan(color_arr, count)

                ws = particle["world_scale"]
                # Ensure compute is submitted and complete before render reads
                if self._batched_frame and not self._frame_ended_early:
                    self._put("ergo_vk_frame_end();")
                    self._put("ergo_vk_frame_wait();")
                    self._frame_ended_early = True
                if hasattr(self, '_pp_arrays') and self._pp_arrays:
                    self._put(f"ergo_vk_set_render_offset("
                              f"(size_t)_pp_wr_offset * sizeof(float));")
                self._put(f"ergo_vk_render_points("
                          f"d_{particle['pos_x']}, d_{particle['pos_y']}, "
                          f"d_{particle['pos_z']}, d_{particle['color']}, "
                          f"{count}, 3.0f, _vmin, _vmax, {ws});")
            elif self.render:
                # ── Grid / heightfield rendering ──
                render_arr = None
                first_real = None
                for arr in (gpu_arrays or sorted(self._array_shapes.keys())):
                    t = self._var_types.get(arr, IRType.REAL)
                    if t == IRType.REAL:
                        if first_real is None:
                            first_real = arr
                        if "PSI" in arr.upper():
                            render_arr = arr
                            break
                if render_arr is None:
                    render_arr = first_real
                if render_arr:
                    if frame_dirty:
                        upload_set.add(render_arr)
                    # Single upload pass
                    if upload_set:
                        self._put("/* Sync CPU state to GPU (render + next frame) */")
                        for arr in sorted(upload_set):
                            shape = self._array_shapes.get(arr)
                            if shape:
                                size_expr = " * ".join(
                                    self._dim_expr(d) for d in shape)
                                sz = self._gpu_sizeof(arr)
                                self._put(f"ergo_vk_upload(d_{arr}, {arr}, "
                                          f"{size_expr} * {sz});")
                    shape = self._array_shapes.get(render_arr)
                    gw, gh = self._infer_grid(shape)
                    scan_count = " * ".join(
                        self._dim_expr(d) for d in shape) if shape else "1"
                    self._emit_minmax_scan(render_arr, scan_count)
                    self._put(f"ergo_vk_render_frame(d_{render_arr}, {gw}, "
                              f"{gh}, _vmin, _vmax, 0.3f);")
            else:
                pass  # uploads deferred to after frame_end
            # Stats update: expose frame/npart to JNI for UI polling
            if self._has_net:
                self._put(f"{{ extern volatile int ergo_stats_frame "
                          f"__attribute__((weak));")
                self._put(f"  extern volatile int ergo_stats_npart "
                          f"__attribute__((weak));")
                self._put(f"  if (&ergo_stats_frame) "
                          f"ergo_stats_frame = {node.var};")
                self._put(f"  if (&ergo_stats_npart) "
                          f"ergo_stats_npart = NPART; }}")
            if use_batched and not self._frame_ended_early:
                self._put("ergo_vk_frame_end();")
            # Upload CPU-dirtied arrays after frame_end so GPU work is
            # committed.  For ping-pong arrays, upload to PP_WR — which
            # becomes PP_RD next frame after the swap at frame_begin.
            if upload_set:
                pp = getattr(self, '_pp_arrays', set())
                # Guard uploads with the same condition as suffix downloads:
                # only upload when CPU code actually modified arrays.
                verify_meta = self._find_verify_meta(node.body)
                upload_guard = (verify_meta and
                                verify_meta.get("every", 1) > 1 and
                                use_batched)
                if upload_guard:
                    every = verify_meta["every"]
                    self._put(f"if (!_oracle_init || "
                              f"_oracle_frame % {every} == 0) {{")
                    self.indent += 1
                # Ensure GPU is idle before transfers (idempotent)
                if use_batched:
                    self._put("ergo_vk_frame_wait();")
                self._put("/* Upload CPU-modified arrays for next frame */")
                for arr in sorted(upload_set):
                    shape = self._array_shapes.get(arr)
                    if shape:
                        size_expr = " * ".join(
                            self._dim_expr(d) for d in shape)
                        sz = self._gpu_sizeof(arr)
                        if arr in pp:
                            self._put(f"ergo_vk_upload_at(d_{arr}, {arr}, "
                                      f"(size_t)_pp_wr_offset * {sz}, "
                                      f"{size_expr} * {sz});")
                        else:
                            self._put(f"ergo_vk_upload(d_{arr}, {arr}, "
                                      f"{size_expr} * {sz});")
                if upload_guard:
                    self.indent -= 1
                    self._put("}")
            if self.render:
                self._put(f"if (ergo_vk_should_close()) break;")
            self.indent -= 1
            self._put("}")
            if use_batched:
                self._put("/* Flush last frame */")
                self._put("ergo_vk_frame_begin(); ergo_vk_frame_end();")
            self._in_frame_loop = False
            self._batched_frame = False
            self._frame_ended_early = False
        else:
            self._put(f"for (int {node.var} = {start}; {node.var} <= {end}; {node.var} += {step}) {{")
            self.indent += 1
            dirty = self._emit_body(node.body)
            # If this loop body contains GPU dispatches and ends with
            # CPU-dirty arrays, upload them before the next iteration
            # so GPU kernels read current data.
            if dirty and self._items_contain_dispatch(node.body):
                # Figure out which arrays the first kernel in the body reads
                first_kernel_reads: set[str] = set()
                for bodyitem in node.body:
                    if isinstance(bodyitem, IRLoop):
                        k = self._kernel_by_line.get(bodyitem.line)
                        if k:
                            first_kernel_reads = k.arrays_read | k.arrays_written
                            break
                needed = dirty & first_kernel_reads
                if needed:
                    self._put("/* Upload CPU-modified arrays for next tick */")
                    for arr in sorted(needed):
                        shape = self._array_shapes.get(arr)
                        if shape:
                            size_expr = " * ".join(
                                self._dim_expr(d) for d in shape)
                            sz = self._gpu_sizeof(arr)
                            self._put(f"ergo_vk_upload(d_{arr}, {arr}, "
                                      f"{size_expr} * {sz});")
            # Inner loops (e.g. SIM_SPAWN) may inherit _batched_frame from
            # the outer frame loop. Only emit frame_end/flush if the inner
            # loop itself contains GPU dispatches AND the frame is still open.
            inner_has_dispatches = self._items_contain_dispatch(node.body)
            _saved_batched = self._batched_frame
            _saved_ended_early = self._frame_ended_early
            if self._batched_frame and inner_has_dispatches and not self._frame_ended_early:
                self._put("ergo_vk_frame_end();")
            self.indent -= 1
            self._put("}")
            if self._batched_frame and inner_has_dispatches and not self._frame_ended_early:
                self._put("/* Flush last frame */")
                self._put("ergo_vk_frame_begin(); ergo_vk_frame_end();")
            # Restore outer frame state
            self._batched_frame = _saved_batched
            self._frame_ended_early = _saved_ended_early

    def _emit_minmax_scan(self, arr: str, count_expr: str):
        """Emit fixed value range for render color mapping.

        The color array (typically OMEGA_NAT) has known bounds from the
        simulation constants. A CPU-side scan over millions of elements
        would stall the pipeline every frame. Use fixed range instead.
        """
        # Color range: ERGO_VMIN/ERGO_VMAX env vars override defaults.
        # Default 0.0-0.15 covers the OMEGA floor (~0.05) with full palette.
        # Set ERGO_VMAX=2.0 to see the full range (mostly blue).
        self._put(f"float _vmin = getenv(\"ERGO_VMIN\") ? "
                  f"atof(getenv(\"ERGO_VMIN\")) : 0.0f;")
        self._put(f"float _vmax = getenv(\"ERGO_VMAX\") ? "
                  f"atof(getenv(\"ERGO_VMAX\")) : 0.15f;")

    def _infer_grid(self, shape: tuple | None) -> tuple[str, str]:
        """Infer 2D grid dimensions from a 1D array shape.

        For a 1D array of size N, tries to find a factorization close
        to a 2:1 aspect ratio. Returns (width_expr, height_expr).
        """
        if not shape or len(shape) != 1:
            return ("64", "1")
        n = shape[0]
        if isinstance(n, int):
            # Try common simulation grid factorizations
            for w in [64, 128, 256, 32, 48, 96]:
                if n % w == 0:
                    return (str(w), str(n // w))
            # Fallback: square-ish
            import math
            sq = int(math.isqrt(n))
            while sq > 1 and n % sq != 0:
                sq -= 1
            return (str(n // sq), str(sq))
        # Dynamic size — use the dimension expression
        return (self._dim_expr(n), "1")

    def _gpu_sizeof(self, arr: str) -> str:
        """Return the C sizeof expression for a GPU array's element type."""
        t = self._var_types.get(arr, IRType.REAL)
        if t == IRType.INTEGER or t == IRType.LOGICAL:
            return "sizeof(int)"
        return f"sizeof({IRType.REAL.c_type})"

    def _emit_while_loop(self, node: IRWhileLoop):
        self._emit_line(node.line)

        # Detect frame loop: DO WHILE containing GPU dispatches
        is_frame_loop = False
        if not self._in_frame_loop and self._items_contain_dispatch(node.body):
            is_frame_loop = True

        if is_frame_loop:
            self._in_frame_loop = True
            self._batched_frame = bool(self.gpu_plan)
            # Sync CPU state to GPU before frame loop
            gpu_arrays = self._gpu_arrays()
            if gpu_arrays:
                self._put("/* Sync CPU state to GPU before frame loop */")
                for arr in gpu_arrays:
                    shape = self._array_shapes.get(arr)
                    if shape:
                        size_expr = " * ".join(self._dim_expr(d) for d in shape)
                        sz = self._gpu_sizeof(arr)
                        self._put(f"ergo_vk_upload(d_{arr}, {arr}, "
                                  f"{size_expr} * {sz});")

        # Emit condition block (computes the condition value)
        self._emit_block(node.cond_block)
        cond = self._operand(node.condition)
        self._put(f"while ({cond}) {{")
        self.indent += 1

        if is_frame_loop and self._batched_frame:
            self._put("ergo_vk_frame_begin();")

        self._emit_body(node.body)

        # Re-evaluate condition at end of loop body
        self._emit_block(node.cond_block)

        if is_frame_loop and self._batched_frame:
            self._put("ergo_vk_frame_end();")
            if self.render:
                self._put("ergo_vk_frame_present();")
                self._put("if (ergo_vk_should_close()) break;")

        self.indent -= 1
        self._put("}")

        if is_frame_loop:
            self._in_frame_loop = False
            self._batched_frame = False

    def _loop_contains_dispatch(self, node: IRLoop) -> bool:
        """Check if a loop body contains any extracted GPU kernel dispatches (recursive)."""
        return self._items_contain_dispatch(node.body)

    def _items_contain_dispatch(self, items: list) -> bool:
        """Recursively check if any items contain GPU kernel dispatches."""
        for item in items:
            if isinstance(item, IRLoop):
                if item.line in self._kernel_by_line:
                    return True
                if self._items_contain_dispatch(item.body):
                    return True
            elif isinstance(item, IRWhileLoop):
                if self._items_contain_dispatch(item.body):
                    return True
            elif isinstance(item, IRIf):
                if self._items_contain_dispatch(item.then_body):
                    return True
                if item.else_body and self._items_contain_dispatch(item.else_body):
                    return True
        return False

    def _emit_select(self, node: IRSelect):
        self._emit_line(node.line)
        expr = self._operand(node.expr)
        self._put(f"switch ({expr}) {{")
        self.indent += 1
        for case_val, case_body in node.cases:
            if case_val is None:
                self._put("default: {")
            else:
                self._put(f"case {self._operand(case_val)}: {{")
            self.indent += 1
            self._emit_body(case_body)
            self._put("break;")
            self.indent -= 1
            self._put("}")
        self.indent -= 1
        self._put("}")

    # ── instruction emission ─────────────────────────────────

    def _emit_inst(self, inst: IRInst):
        op = inst.op
        args = inst.args
        result = inst.result

        # Simple copy (assignment)
        if op == Op.COPY:
            if inst.meta.get("kind") == "cycle":
                self._put("continue;")
                return
            if result and args:
                self._put(f"{result} = {self._operand(args[0])};")
            return

        # Arithmetic binary ops
        if op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV):
            c_op = {Op.ADD: "+", Op.SUB: "-", Op.MUL: "*", Op.DIV: "/"}[op]
            self._put(f"{result} = ({self._operand(args[0])} {c_op} {self._operand(args[1])});")
            return

        if op == Op.POW:
            self._put(f"{result} = pow({self._operand(args[0])}, {self._operand(args[1])});")
            return

        if op == Op.MOD:
            a, b = self._operand(args[0]), self._operand(args[1])
            if self._is_int_operand(args[0]) and self._is_int_operand(args[1]):
                self._put(f"{result} = ({a} % {b});")
            else:
                self._put(f"{result} = fmod({a}, {b});")
            return

        if op == Op.NEG:
            self._put(f"{result} = (-{self._operand(args[0])});")
            return

        # Relational
        if op in (Op.LT, Op.GT, Op.EQ, Op.NE, Op.LE, Op.GE):
            c_op = {
                Op.LT: "<", Op.GT: ">", Op.EQ: "==",
                Op.NE: "!=", Op.LE: "<=", Op.GE: ">=",
            }[op]
            self._put(f"{result} = ({self._operand(args[0])} {c_op} {self._operand(args[1])});")
            return

        # Logical
        if op == Op.AND:
            self._put(f"{result} = ({self._operand(args[0])} && {self._operand(args[1])});")
            return
        if op == Op.OR:
            self._put(f"{result} = ({self._operand(args[0])} || {self._operand(args[1])});")
            return
        if op == Op.NOT:
            self._put(f"{result} = (!{self._operand(args[0])});")
            return

        # Bitwise
        if op == Op.ISHFT:
            val = self._operand(args[0])
            shift = args[1]
            if isinstance(shift, IRConst) and shift.type == IRType.INTEGER:
                sv = shift.value
                if sv >= 0:
                    self._put(f"{result} = (({val}) << {sv});")
                else:
                    self._put(f"{result} = ((unsigned)({val}) >> {-sv});")
            else:
                s = self._operand(shift)
                self._put(f"{result} = (({s}) >= 0 ? ({val}) << ({s}) : (unsigned)({val}) >> -({s}));")
            return
        if op == Op.IEOR:
            self._put(f"{result} = ({self._operand(args[0])} ^ {self._operand(args[1])});")
            return
        if op == Op.IAND:
            self._put(f"{result} = ({self._operand(args[0])} & {self._operand(args[1])});")
            return
        if op == Op.IOR:
            self._put(f"{result} = ({self._operand(args[0])} | {self._operand(args[1])});")
            return
        if op == Op.BITNOT:
            self._put(f"{result} = (~{self._operand(args[0])});")
            return

        # Type conversion
        if op == Op.TO_REAL:
            self._put(f"{result} = ({IRType.REAL.c_type})({self._operand(args[0])});")
            return
        if op == Op.TO_INT:
            self._put(f"{result} = (int)({self._operand(args[0])});")
            return
        if op == Op.TO_CHAR:
            self._put(f"{result} = (char)({self._operand(args[0])});")
            return

        # Math intrinsics
        if op in C_MATH:
            c_func = C_MATH[op]
            a = ", ".join(self._operand(a) for a in args)
            self._put(f"{result} = {c_func}({a});")
            return

        # ABS — type aware
        if op == Op.ABS:
            a = self._operand(args[0])
            if self._is_int_operand(args[0]):
                self._put(f"{result} = abs({a});")
            else:
                self._put(f"{result} = fabs({a});")
            return

        # MAX / MIN
        if op == Op.MAX:
            a, b = self._operand(args[0]), self._operand(args[1])
            if self._is_int_operand(args[0]):
                self._put(f"{result} = (({a}) > ({b}) ? ({a}) : ({b}));")
            else:
                self._put(f"{result} = fmax({a}, {b});")
            return
        if op == Op.MIN:
            a, b = self._operand(args[0]), self._operand(args[1])
            if self._is_int_operand(args[0]):
                self._put(f"{result} = (({a}) < ({b}) ? ({a}) : ({b}));")
            else:
                self._put(f"{result} = fmin({a}, {b});")
            return

        # CLAMP — branchless
        if op == Op.CLAMP:
            x, lo, hi = self._operand(args[0]), self._operand(args[1]), self._operand(args[2])
            if self._is_int_operand(args[0]):
                self._put(f"{result} = (({x}) < ({lo}) ? ({lo}) : (({x}) > ({hi}) ? ({hi}) : ({x})));")
            else:
                self._put(f"{result} = fmin(fmax({x}, {lo}), {hi});")
            return

        # Array LOAD
        if op == Op.LOAD:
            array_name = inst.meta.get("array", "?")
            indices = "][".join(self._operand(a) for a in args)
            self._put(f"{result} = {array_name}[{indices}];")
            return

        # Array STORE
        if op == Op.STORE:
            array_name = inst.meta.get("array", "?")
            val = self._operand(args[0])
            indices = "][".join(self._operand(a) for a in args[1:])
            self._put(f"{array_name}[{indices}] = {val};")
            return

        # ALLOC
        if op == Op.ALLOC:
            ct = self._c_type(inst.type)
            size = " * ".join(self._operand(a) for a in args)
            self._put(f"{result} = ({ct} *)malloc(({size}) * sizeof({ct}));")
            return

        # FREE
        if op == Op.FREE:
            name = self._operand(args[0])
            self._put(f"free({name}); {name} = NULL;")
            return

        # ZERO — zero entire array via memset (or GPU fill in batched frame)
        if op == Op.ZERO:
            array_name = inst.meta.get("array", "?")
            gpu_array_set = set(self._gpu_arrays()) if self.gpu_plan else set()
            if self._batched_frame and array_name in gpu_array_set:
                shape = self._array_shapes.get(array_name)
                if shape:
                    size_expr = " * ".join(
                        self._dim_expr(d) for d in shape)
                    sz = self._gpu_sizeof(array_name)
                    self._put(f"ergo_vk_frame_fill(d_{array_name}, "
                              f"{size_expr} * {sz});")
                    return
            self._put(f"memset({array_name}, 0, sizeof({array_name}));")
            return

        # Function call (with return value)
        if op == Op.CALL:
            func = inst.meta.get("func", "?")
            a = ", ".join(self._operand(a) for a in args)
            self._put(f"{result} = {func}({a});")
            return

        # Subroutine call (void)
        if op == Op.CALL_VOID:
            func = inst.meta.get("func", "?")
            a = ", ".join(self._operand(a) for a in args)
            # GPU sync: download arrays before CPU call, upload after
            has_gpu = self.gpu_plan and self.gpu_plan.kernels
            gpu_arrays = set(self._gpu_arrays()) if has_gpu else set()
            sub_access = self._sub_array_access.get(func)
            need_sync = has_gpu and sub_access and self._in_frame_loop
            dl_arrays = set()
            ul_arrays = set()
            if need_sync:
                reads, writes = sub_access
                pp = getattr(self, '_pp_arrays', set())
                # Download GPU arrays this sub reads
                dl_arrays = (reads | writes) & gpu_arrays
                if dl_arrays:
                    # Ensure GPU cmd buf is submitted and idle before transfer
                    if self._batched_frame and not self._frame_ended_early:
                        self._put("ergo_vk_frame_end();")
                        self._put("ergo_vk_frame_wait();")
                        self._frame_ended_early = True
                    self._put(f"/* GPU→CPU sync for {func} */")
                    for arr in sorted(dl_arrays):
                        shape = self._array_shapes.get(arr)
                        if shape:
                            size_expr = " * ".join(
                                self._dim_expr(d) for d in shape)
                            sz = self._gpu_sizeof(arr)
                            if arr in pp:
                                self._put(
                                    f"ergo_vk_download_at(d_{arr}, {arr}, "
                                    f"(size_t)_pp_wr_offset * {sz}, "
                                    f"{size_expr} * {sz});")
                            else:
                                self._put(
                                    f"ergo_vk_download(d_{arr}, {arr}, "
                                    f"{size_expr} * {sz});")
                # Track arrays to upload after the call
                ul_arrays = writes & gpu_arrays
            self._put(f"{func}({a});")
            # Upload modified arrays back to GPU
            if ul_arrays:
                self._put(f"/* CPU→GPU sync after {func} */")
                for arr in sorted(ul_arrays):
                    shape = self._array_shapes.get(arr)
                    if shape:
                        size_expr = " * ".join(
                            self._dim_expr(d) for d in shape)
                        sz = self._gpu_sizeof(arr)
                        pp = getattr(self, '_pp_arrays', set())
                        if arr in pp:
                            self._put(
                                f"ergo_vk_upload_at(d_{arr}, {arr}, "
                                f"(size_t)_pp_wr_offset * {sz}, "
                                f"{size_expr} * {sz});")
                        else:
                            self._put(
                                f"ergo_vk_upload(d_{arr}, {arr}, "
                                f"{size_expr} * {sz});")
            # NET hook: send census packet after adaptive census call
            if func == "SIM_CENSUS_ADAPTIVE" and self._has_net:
                self._put("if (_consensus_enabled) {")
                self._emit_census_net_send()
                self._put("}")
            return

        # PRINT
        if op == Op.PRINT:
            val = args[0]
            fmt = self._format_for_operand(val)
            self._put(f'printf("{fmt}\\n", {self._operand(val)});')
            return

        # WRITE
        if op == Op.WRITE:
            unit = inst.meta.get("unit", "*")
            fmt = inst.meta.get("fmt", "")
            advance = inst.meta.get("advance", True)
            stream = "stderr" if unit == "0" else "stdout"
            if advance:
                fmt = fmt + "\\n"
            if args:
                a = ", ".join(self._operand(a) for a in args)
                self._put(f'fprintf({stream}, "{fmt}", {a});')
            else:
                self._put(f'fprintf({stream}, "{fmt}");')
            return

        # FLUSH
        if op == Op.FLUSH:
            self._put("fflush(stdout);")
            return

        # RETURN (with value)
        if op == Op.RETURN:
            self._put(f"return {self._operand(args[0])};")
            return

        # RETURN_VOID
        if op == Op.RETURN_VOID:
            self._put("return;")
            return

        # STOP
        if op == Op.STOP:
            if self.gpu_plan and self.gpu_plan.kernels:
                self._put("ergo_vk_shutdown();")
            self._put("return 0;")
            return

        # VERIFY — CPU oracle checkpoint
        if op == Op.VERIFY:
            self._emit_verify(inst)
            return

        # SORT_BY_GEN — compiler-generated sort dispatch
        if op == Op.SORT_BY_GEN:
            self._emit_sort_by_gen(inst)
            return

        self._put(f"/* unhandled IR op: {op.value} */")

    def _emit_oracle_decls(self, items: list):
        """Scan for VERIFY ops and emit oracle shadow array declarations."""
        verify_meta = self._find_verify_meta(items)
        if not verify_meta:
            return
        arrays = verify_meta["arrays"]
        n = verify_meta["oracle_size"]
        self._put(f"/* Oracle shadow state ({n} particles) */")
        self._put(f"int _oracle_frame = 0;")
        self._put(f"int _oracle_init = 0;")
        self._put(f"double _oracle_prev_err = 0.0;")
        for arr in arrays:
            ct = self._c_type(self._var_types.get(arr, IRType.REAL))
            self._put(f"static {ct} _oracle_{arr}[{n}];")
            self._put(f"{ct} _oracle_gpu_{arr}[{n}];")
            self._put(f"{ct} _oracle_save_{arr}[{n}];")
        # NET: UDP transport state
        net_host = verify_meta.get("net_host")
        if net_host:
            self._put(f"/* NET: UDP transport to oracle */")
            self._put(f"ergo_net_t _ergo_net;")
            self._put(f"ergo_spawn_t _oracle_spawn = {{0}};")
            # Parse host:port from MCL source (compile-time defaults)
            if ":" in net_host:
                host, port = net_host.rsplit(":", 1)
            else:
                host, port = net_host, "4242"
            gpu_id = verify_meta.get("net_gpu_id", 0)
            # Use runtime globals if available (Android JNI sets these),
            # otherwise fall back to compiled-in defaults.
            self._put(f"/* Runtime-configurable oracle host/port "
                      f"(defaults: {host}:{port} gpu={gpu_id}) */")
            self._put(f"extern char ergo_oracle_host[256] "
                      f"__attribute__((weak));")
            self._put(f"extern int ergo_oracle_port "
                      f"__attribute__((weak));")
            self._put(f"extern int ergo_gpu_id "
                      f"__attribute__((weak));")
            self._put(f"const char *_net_host = "
                      f"(&ergo_oracle_host[0]) ? ergo_oracle_host "
                      f": \"{host}\";")
            self._put(f"int _net_port = "
                      f"(&ergo_oracle_port) ? ergo_oracle_port "
                      f": {port};")
            self._put(f"int _net_gpu = "
                      f"(&ergo_gpu_id) ? ergo_gpu_id "
                      f": {gpu_id};")
            self._put(f"int _consensus_enabled = "
                      f"(getenv(\"ERGO_CONSENSUS\") != NULL);")
            self._put(f"ergo_field_rx_t _field_rx;")
            self._put(f"memset(&_field_rx, 0, sizeof(_field_rx));")
            self._put(f"uint32_t _field_send_id = 0;")
            self._put(f"if (_consensus_enabled) {{")
            self.indent += 1
            self._put(f"if (ergo_net_init(&_ergo_net, _net_host, "
                      f"_net_port, 0, _net_gpu) < 0) {{")
            self.indent += 1
            self._put(f"fprintf(stderr, \"[NET] Failed to init "
                      f"transport to %s:%d\\n\", _net_host, _net_port);")
            self._put(f"return 1;")
            self.indent -= 1
            self._put(f"}}")
            # Init field exchange + join multicast (already declared above)
            self._put(f"ergo_net_mcast_init_recv(&_ergo_net);")
            self.indent -= 1
            self._put(f"}} else {{")
            self.indent += 1
            self._put(f"fprintf(stderr, \"[NET] Consensus disabled "
                      f"(set ERGO_CONSENSUS=1 to enable)\\n\");")
            self.indent -= 1
            self._put(f"}}")
        self._put("")

    def _find_verify_meta(self, items: list) -> dict | None:
        """Find the first VERIFY instruction's metadata in a body."""
        for item in items:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.op == Op.VERIFY:
                        return inst.meta
            elif isinstance(item, IRIf):
                r = self._find_verify_meta(item.then_body)
                if r:
                    return r
                if item.else_body:
                    r = self._find_verify_meta(item.else_body)
                    if r:
                        return r
            elif isinstance(item, IRLoop):
                r = self._find_verify_meta(item.body)
                if r:
                    return r
            elif isinstance(item, IRWhileLoop):
                r = self._find_verify_meta(item.body)
                if r:
                    return r
        return None

    def _emit_sort_by_gen(self, inst: IRInst):
        """Emit GPU sort-by-GEN dispatch: histogram → scan → scatter → swap."""
        arrays = inst.meta["arrays"]
        # Find the matching sort plan
        sp = None
        for s in self.gpu_plan.sort_plans:
            if s.arrays == arrays:
                sp = s
                break
        if not sp:
            self._put(f"/* SORT_BY_GEN: no matching sort plan */")
            return

        hk = sp.histogram_kernel_id
        sk = sp.scan_kernel_id
        sck = sp.scatter_kernel_id

        # Submit the frame's regular work first so the render pipeline
        # doesn't stall behind the sort. ergo_vk_frame_drain submits
        # without waiting and re-opens the command buffer.
        self._put(f"/* ── SORT_BY_GEN: submit frame, then sort in fresh cmd buf ── */")
        self._put(f"ergo_vk_frame_drain();")
        self._put(f"{{")
        self.indent += 1

        # Step 1: Zero the histogram buffer
        self._put(f"ergo_vk_frame_fill(d_sort_histogram, 32 * sizeof(int));")

        # Step 2: Dispatch histogram kernel
        self._put(f"/* COUNT_GEN: atomicAdd histogram[GEN] per particle */")
        self._put(f"ergo_vk_bind_buffer(pipe_{hk}, 0, d_FLAGS);")
        self._put(f"ergo_vk_bind_buffer(pipe_{hk}, 1, d_sort_histogram);")
        self._put(f"{{ struct {{ int _s_NPART; int _s_GEN_SHIFT; int _s_GEN_MASK; }} _pc = {{ NPART, GEN_SHIFT, GEN_MASK }};")
        self._put(f"  ergo_vk_push_constants(pipe_{hk}, &_pc, sizeof(_pc)); }}")
        self._put(f"ergo_vk_frame_dispatch(pipe_{hk}, (NPART + 255) / 256);")
        self._put(f"ergo_vk_frame_barrier();")

        # Step 3: Dispatch scan kernel (single workgroup of 32 threads)
        self._put(f"/* SCAN_GEN: exclusive prefix sum over histogram */")
        self._put(f"ergo_vk_bind_buffer(pipe_{sk}, 0, d_sort_histogram);")
        self._put(f"ergo_vk_bind_buffer(pipe_{sk}, 1, d_sort_offsets);")
        self._put(f"ergo_vk_frame_dispatch(pipe_{sk}, 1);")
        self._put(f"ergo_vk_frame_barrier();")

        # Step 4: Dispatch scatter kernel
        self._put(f"/* SCATTER_GEN: scatter particles to sorted positions */")
        self._put(f"ergo_vk_bind_buffer(pipe_{sck}, 0, d_FLAGS);")
        self._put(f"ergo_vk_bind_buffer(pipe_{sck}, 1, d_sort_offsets);")
        bind_idx = 2
        # Source arrays (read from current particle buffers)
        for arr in arrays:
            self._put(f"ergo_vk_bind_buffer(pipe_{sck}, {bind_idx}, d_{arr});")
            bind_idx += 1
        # Destination arrays (write to temp sorted buffers)
        for arr in arrays:
            self._put(f"ergo_vk_bind_buffer(pipe_{sck}, {bind_idx}, d_sort_{arr});")
            bind_idx += 1
        self._put(f"{{ struct {{ int _s_NPART; int _s_GEN_SHIFT; int _s_GEN_MASK; }} _pc = {{ NPART, GEN_SHIFT, GEN_MASK }};")
        self._put(f"  ergo_vk_push_constants(pipe_{sck}, &_pc, sizeof(_pc)); }}")
        self._put(f"ergo_vk_frame_dispatch(pipe_{sck}, (NPART + 255) / 256);")

        # Pointer swap: CPU-side only. Queue ordering guarantees the
        # scatter completes before any subsequent dispatches read the
        # swapped buffers. Next frame's bind_buffer picks up new handles.
        self._put(f"/* Pointer swap: sorted → active */")
        for arr in arrays:
            self._put(f"{{ ErgoVkBuf _tmp = d_{arr}; d_{arr} = d_sort_{arr}; d_sort_{arr} = _tmp; }}")
        # Force render descriptor set rebind — buffer handles changed
        self._put(f"{{ extern int pts_ds_bound; pts_ds_bound = 0; }}")

        self.indent -= 1
        self._put(f"}}")

    def _emit_verify(self, inst: IRInst):
        """Emit CPU oracle verification checkpoint.

        Downloads a sparse sample from GPU, compares against CPU shadow
        state, and reports divergence. The shadow arrays are evolved
        independently by the CPU each frame using the same physics.
        """
        arrays = inst.meta["arrays"]
        n = inst.meta["oracle_size"]
        every = inst.meta["every"]
        tol = inst.meta["tolerance"]

        self._put(f"/* === CPU Oracle: verify {n} particles, every {every} frames === */")

        # Lazy init: copy seed state into shadow arrays on first call
        self._put(f"if (!_oracle_init) {{")
        self.indent += 1
        for arr in arrays:
            self._put(f"memcpy(_oracle_{arr}, {arr}, "
                      f"{n} * sizeof({arr}[0]));")
        self._put(f"_oracle_init = 1;")
        self._put(f"fprintf(stderr, \"[ORACLE] Initialized shadow state "
                  f"({n} particles)\\n\");")
        self.indent -= 1
        self._put(f"}}")

        # Frame counter guard
        if every > 1:
            self._put(f"if (_oracle_frame % {every} == 0) {{")
            self.indent += 1

        # Sparse download: just the first N elements of each array
        # For ping-pong arrays, read from the current-state half (PP_RD offset)
        has_gpu = self.gpu_plan and self.gpu_plan.kernels
        if has_gpu:
            # Ensure GPU cmd buf is submitted and idle before transfer
            if self._batched_frame and not self._frame_ended_early:
                self._put("ergo_vk_frame_end();")
                self._put("ergo_vk_frame_wait();")
                self._frame_ended_early = True
            pp = getattr(self, '_pp_arrays', set())
            for arr in arrays:
                sz = self._gpu_sizeof(arr)
                if arr in pp:
                    self._put(f"ergo_vk_download_at(d_{arr}, _oracle_gpu_{arr}, "
                              f"(size_t)_pp_wr_offset * {sz}, {n} * {sz});")
                else:
                    self._put(f"ergo_vk_download(d_{arr}, _oracle_gpu_{arr}, "
                              f"{n} * {sz});")

        # Compare current state against CPU shadow
        # GPU mode: compare downloaded GPU sample vs shadow
        # CPU mode: compare global arrays directly vs shadow
        self._put(f"{{")
        self.indent += 1
        self._put(f"double _max_err = 0.0, _worst_gpu = 0.0, _worst_cpu = 0.0;")
        self._put(f"const char *_worst_arr = \"\";")
        self._put(f"int _worst_idx = 0;")
        for arr in arrays:
            self._put(f"for (int _vi = 0; _vi < {n}; _vi++) {{")
            self.indent += 1
            if has_gpu:
                self._put(f"double _gpu = _oracle_gpu_{arr}[_vi];")
            else:
                self._put(f"double _gpu = {arr}[_vi];")
            self._put(f"double _cpu = _oracle_{arr}[_vi];")
            self._put(f"double _denom = fabs(_cpu) > 1e-30 ? fabs(_cpu) : 1e-30;")
            self._put(f"double _rel = fabs(_gpu - _cpu) / _denom;")
            self._put(f"if (_rel > _max_err) {{ _max_err = _rel; "
                      f"_worst_gpu = _gpu; _worst_cpu = _cpu; "
                      f"_worst_arr = \"{arr}\"; _worst_idx = _vi; }}")
            self.indent -= 1
            self._put(f"}}")
        # Compute divergence rate and Lyapunov ratio
        # λ ≈ |rate/divergence| — exponential growth indicator
        self._put(f"double _d_err = _max_err - _oracle_prev_err;")
        self._put(f"double _lyap = (_max_err > 1e-30) ? "
                  f"fabs(_d_err) / _max_err : 0.0;")
        self._put(f"const char *_regime = "
                  f"(_lyap > 1.0) ? \"EXPONENTIAL\" : "
                  f"(_lyap < 0.1) ? \"PLATEAU\" : "
                  f"\"LINEAR\";")
        self._put(f"if (_max_err > {tol}) {{")
        self.indent += 1
        self._put(f"fprintf(stderr, \"[ORACLE] frame %d: %s d=%.2e "
                  f"rate=%+.2e %s[%d] (gpu=%.4e cpu=%.4e)\\n\",")
        self._put(f"    _oracle_frame, _regime, _max_err, _d_err,")
        self._put(f"    _worst_arr, _worst_idx, _worst_gpu, _worst_cpu);")
        self.indent -= 1
        self._put(f"}} else if (_oracle_frame % 1000 == 0) {{")
        self.indent += 1
        self._put(f"fprintf(stderr, \"[ORACLE] frame %d: OK (max_rel=%.2e)\\n\","
                  f" _oracle_frame, _max_err);")
        self.indent -= 1
        self._put(f"}}")
        self._put(f"_oracle_prev_err = _max_err;")

        # NET: send verify payload to oracle (672 bytes = 12 particles × 7 doubles)
        net_host = inst.meta.get("net_host")
        if net_host:
            self._put(f"if (_consensus_enabled) {{")
            self._put(f"/* NET: pack and send Lagrangian probe */")
            self._put(f"{{")
            self.indent += 1
            has_gpu = self.gpu_plan and self.gpu_plan.kernels
            self._put(f"{IRType.REAL.c_type} _vfy_buf[{n} * {len(arrays)}];")
            for i, arr in enumerate(arrays):
                src = f"_oracle_gpu_{arr}" if has_gpu else arr
                self._put(f"memcpy(_vfy_buf + {i * n}, "
                          f"{src}, {n} * sizeof({IRType.REAL.c_type}));")
            self._put(f"ergo_net_send_verify(&_ergo_net, _oracle_frame, "
                      f"_vfy_buf, sizeof(_vfy_buf));")
            self.indent -= 1
            self._put(f"}}")
            # Non-blocking receive: check for spawn commands from oracle
            self._put(f"if (ergo_net_recv_spawn(&_ergo_net, &_oracle_spawn)) {{")
            self.indent += 1
            self._put(f"NET_SPAWN_ACTIVE = 1;")
            self._put(f"NET_SPAWN_COUNT = (int)_oracle_spawn.spawn_count;")
            self._put(f"NET_SPAWN_PAUSE = (_oracle_spawn.flags & 1) ? 1 : 0;")
            self._put(f"NET_CENSUS_OVERRIDE = (int)_oracle_spawn.next_census;")
            self._put(f"{{ extern volatile int ergo_stats_connected "
                      f"__attribute__((weak));")
            self._put(f"  if (&ergo_stats_connected) "
                      f"ergo_stats_connected = 1; }}")
            self._put(f"fprintf(stderr, \"[NET] spawn cmd: count=%u "
                      f"id=%u next_census=%u flags=0x%x\\n\",")
            self._put(f"    _oracle_spawn.spawn_count, _oracle_spawn.spawn_id,")
            self._put(f"    _oracle_spawn.next_census, _oracle_spawn.flags);")
            self.indent -= 1
            self._put(f"}}")
            self._put(f"}} /* end consensus */")

        self.indent -= 1
        self._put(f"}}")

        # Evolve CPU shadow state using the same physics subroutine.
        # The subroutine SIM_PHYSICS_STEP operates on global arrays, so
        # we swap the first N elements in, run physics on N particles,
        # then swap back. This is the oracle's independent computation.
        self._put(f"/* Oracle: evolve shadow state */")
        # Save first N elements of global arrays
        for arr in arrays:
            self._put(f"memcpy(_oracle_save_{arr}, {arr}, "
                      f"{n} * sizeof({arr}[0]));")
        # Copy shadow into global arrays
        for arr in arrays:
            self._put(f"memcpy({arr}, _oracle_{arr}, "
                      f"{n} * sizeof({arr}[0]));")
        # Run CPU physics on first N particles
        # We call the un-inlined subroutine with the oracle particle count
        self._put(f"{{ int _save_NPART = NPART; NPART = {n};")
        self._put(f"  SIM_PHYSICS_STEP(DEFAULT_DT);")
        self._put(f"  NPART = _save_NPART; }}")
        # Copy result back to shadow
        for arr in arrays:
            self._put(f"memcpy(_oracle_{arr}, {arr}, "
                      f"{n} * sizeof({arr}[0]));")
        # Restore global arrays
        for arr in arrays:
            self._put(f"memcpy({arr}, _oracle_save_{arr}, "
                      f"{n} * sizeof({arr}[0]));")

        self._put(f"_oracle_frame++;")

        if every > 1:
            self.indent -= 1
            self._put(f"}} else {{ _oracle_frame++; }}")

    def _emit_census_net_send(self):
        """Emit census packet send after SIM_CENSUS_ADAPTIVE call.

        Packs the census globals (populated by the Ergo subroutine) into
        an ergo_census_t and sends to the oracle. The oracle responds with
        spawn commands which are received in the VERIFY path.
        """
        self._put(f"/* NET: send census reduction to oracle */")
        self._put(f"{{")
        self.indent += 1
        self._put(f"ergo_census_t _census;")
        self._put(f"memset(&_census, 0, sizeof(_census));")
        # Map Ergo census globals to packet fields.
        # The subroutine computed these; we read the globals it wrote.
        # Population counts come from the last census call's reduction.
        # We use the PREV_ state variables since the subroutine just
        # updated them with current values.
        self._put(f"_census.frame = (uint32_t)CENSUS_PREV_FRAME;")
        self._put(f"_census.omega_mean = CENSUS_PREV_OMEGA_MEAN;")
        self._put(f"_census.omega_max = CENSUS_PREV_OMEGA_MAX;")
        self._put(f"_census.crystal = (uint32_t)CENSUS_PREV_CRYSTAL;")
        self._put(f"_census.spread = CENSUS_PREV_SPREAD;")
        self._put(f"_census.alive = (uint32_t)NPART;")
        self._put(f"_census.sample_count = (uint32_t)NPART;")
        self._put(f"_census.capacity = (uint32_t)CAPACITY;")
        self._put(f"ergo_net_send_census(&_ergo_net, "
                  f"(uint32_t)CENSUS_PREV_FRAME, &_census);")
        # Send density field for multi-GPU reduction.
        # Field protocol is always f32. GRID_DENSITY may be int or real.
        grid_type = self._var_types.get("GRID_DENSITY", IRType.REAL)
        from .ir import get_real_precision
        if grid_type == IRType.REAL and get_real_precision() == 32:
            self._put(f"ergo_net_send_field(&_ergo_net, "
                      f"(uint32_t)CENSUS_PREV_FRAME, "
                      f"(const float*)GRID_DENSITY, ++_field_send_id);")
        else:
            # Convert int or f64 density to f32 for network
            src_type = "int" if grid_type == IRType.INTEGER else "double"
            self._put(f"{{ float _fld_buf[ERGO_FIELD_GRID_CELLS];")
            self._put(f"  for (int _fi = 0; _fi < ERGO_FIELD_GRID_CELLS; _fi++)")
            self._put(f"    _fld_buf[_fi] = (float)"
                      f"(({src_type}*)GRID_DENSITY)[_fi];")
            self._put(f"  ergo_net_send_field(&_ergo_net, "
                      f"(uint32_t)CENSUS_PREV_FRAME, "
                      f"_fld_buf, ++_field_send_id); }}")
        self._put(f"fprintf(stderr, \"[NET] field sent id=%u "
                  f"(%d chunks)\\n\", _field_send_id, ERGO_FIELD_NCHUNKS);")
        self.indent -= 1
        self._put(f"}}")

    def _emit_field_to_grid(self, grid_name: str):
        """Emit code to copy _field_rx.grid (f32) into a grid array.
        Handles f64 mode by converting element-wise."""
        from .ir import get_real_precision
        if get_real_precision() == 32:
            self._put(f"memcpy({grid_name}, _field_rx.grid, "
                      f"sizeof({grid_name}));")
        else:
            self._put(f"for (int _gi = 0; _gi < ERGO_FIELD_GRID_CELLS; _gi++)")
            self._put(f"  ((double*){grid_name})[_gi] = "
                      f"(double)_field_rx.grid[_gi];")

    def _emit_field_recv(self):
        """Emit non-blocking drain of incoming global density field.

        Called at the top of each frame iteration. Drains any pending
        FIELD packets from the oracle, reassembles into _field_rx.
        If complete, replaces GRID_DENSITY and uploads to GPU.
        Applied before scatter — the global field persists until the
        next local scatter overwrites it.
        """
        self._put(f"/* NET: drain multicast field + unicast spawn/field */")
        self._put(f"{{")
        self.indent += 1
        has_gpu = self.gpu_plan and self.gpu_plan.kernels
        # 1. Drain multicast socket for field broadcast (O(1) from oracle)
        self._put(f"for (int _fi = 0; _fi < 200; _fi++) {{")
        self.indent += 1
        self._put(f"int _fc = ergo_net_recv_field_mcast(&_ergo_net, "
                  f"&_field_rx);")
        self._put(f"if (_fc < 0) break;")  # no mcast socket
        self._put(f"if (_fc == 0) break;")  # no packet
        self._put(f"if (_fc == 1) {{")  # field complete
        self.indent += 1
        self._emit_field_to_grid("GRID_DENSITY_GLOBAL")
        if has_gpu:
            self._put(f"ergo_vk_upload(d_GRID_DENSITY_GLOBAL, "
                      f"GRID_DENSITY_GLOBAL, "
                      f"sizeof(GRID_DENSITY_GLOBAL));")
        self._put(f"fprintf(stderr, \"[NET] global field received "
                  f"(id=%u, mcast, blend=%.2f)\\n\", "
                  f"_field_rx.field_id, FIELD_BLEND);")
        self._put(f"ergo_field_rx_reset(&_field_rx);")
        self._put(f"break;")
        self.indent -= 1
        self._put(f"}}")
        self.indent -= 1
        self._put(f"}}")
        # 2. Drain unicast socket for spawn commands + fallback field
        self._put(f"ergo_hdr_t _fh;")
        self._put(f"uint8_t _fp[2048];")
        self._put(f"struct sockaddr_in _fs;")
        self._put(f"for (int _fi = 0; _fi < 200; _fi++) {{")
        self.indent += 1
        self._put(f"int _ft = ergo_net_recv(&_ergo_net, &_fh, _fp, "
                  f"sizeof(_fp), &_fs);")
        self._put(f"if (_ft == 0) break;")
        self._put(f"if (_ft == ERGO_FIELD) {{")
        self.indent += 1
        self._put(f"if (ergo_field_rx_chunk(&_field_rx, _fp, "
                  f"_fh.payload_len)) {{")
        self.indent += 1
        self._emit_field_to_grid("GRID_DENSITY_GLOBAL")
        if has_gpu:
            self._put(f"ergo_vk_upload(d_GRID_DENSITY_GLOBAL, "
                      f"GRID_DENSITY_GLOBAL, "
                      f"sizeof(GRID_DENSITY_GLOBAL));")
        self._put(f"fprintf(stderr, \"[NET] global field received "
                  f"(id=%u, unicast, blend=%.2f)\\n\", "
                  f"_field_rx.field_id, FIELD_BLEND);")
        self._put(f"ergo_field_rx_reset(&_field_rx);")
        self.indent -= 1
        self._put(f"}}")
        self.indent -= 1
        self._put(f"}} else if (_ft == ERGO_SPAWN) {{")
        self.indent += 1
        self._put(f"ergo_spawn_t _sp;")
        self._put(f"memcpy(&_sp, _fp, sizeof(_sp));")
        self._put(f"if (_sp.spawn_id > _ergo_net.last_spawn_id) {{")
        self.indent += 1
        self._put(f"_ergo_net.last_spawn_id = _sp.spawn_id;")
        self._put(f"NET_SPAWN_ACTIVE = 1;")
        self._put(f"NET_SPAWN_COUNT = (int)_sp.spawn_count;")
        self._put(f"NET_SPAWN_PAUSE = (_sp.flags & 1) ? 1 : 0;")
        self._put(f"NET_CENSUS_OVERRIDE = (int)_sp.next_census;")
        self._put(f"{{ extern volatile int ergo_stats_connected "
                  f"__attribute__((weak));")
        self._put(f"  if (&ergo_stats_connected) "
                  f"ergo_stats_connected = 1; }}")
        self.indent -= 1
        self._put(f"}}")
        self.indent -= 1
        self._put(f"}}")
        self.indent -= 1
        self._put(f"}}")
        self.indent -= 1
        self._put(f"}}")

    # ── GPU codegen helpers ──────────────────────────────────

    def _frame_kernel_ids(self) -> set[int]:
        """Kernel IDs dispatched inside the frame loop (not init-only)."""
        if not self.gpu_plan:
            return set()
        # Find the outermost loop in main_body that contains GPU dispatches
        frame_ids: set[int] = set()
        for item in self.module.main_body:
            if isinstance(item, IRLoop):
                if item.line not in self._kernel_by_line and self._items_contain_dispatch(item.body):
                    self._collect_kernel_ids(item.body, frame_ids)
            elif isinstance(item, IRWhileLoop):
                if self._items_contain_dispatch(item.body):
                    self._collect_kernel_ids(item.body, frame_ids)
        return frame_ids

    def _collect_kernel_ids(self, items: list, ids: set[int]):
        """Recursively collect kernel IDs from extracted loops in items."""
        for item in items:
            if isinstance(item, IRLoop):
                k = self._kernel_by_line.get(item.line)
                if k:
                    ids.add(k.kernel_id)
                self._collect_kernel_ids(item.body, ids)
            elif isinstance(item, IRWhileLoop):
                self._collect_kernel_ids(item.body, ids)
            elif isinstance(item, IRIf):
                self._collect_kernel_ids(item.then_body, ids)
                if item.else_body:
                    self._collect_kernel_ids(item.else_body, ids)

    def _gpu_arrays(self) -> list[str]:
        """Arrays that need GPU buffers — only those used by frame-loop kernels.
        Sorted largest-first to minimize VRAM fragmentation."""
        if not self.gpu_plan:
            return []
        if not hasattr(self, '_cached_gpu_arrays'):
            frame_ids = self._frame_kernel_ids()
            if not frame_ids:
                frame_ids = {k.kernel_id for k in self.gpu_plan.kernels}
            self._cached_frame_kernel_ids = frame_ids
            arrays: set[str] = set()
            for k in self.gpu_plan.kernels:
                if k.kernel_id in frame_ids:
                    arrays |= k.arrays_read | k.arrays_written
            self._cached_gpu_arrays = sorted(arrays)
            self._cached_gpu_array_set = set(self._cached_gpu_arrays)
        return self._cached_gpu_arrays

    def _is_gpu_kernel(self, kernel) -> bool:
        """Check if a kernel should be dispatched on GPU (all its arrays have buffers)."""
        if not hasattr(self, '_cached_gpu_array_set'):
            self._gpu_arrays()  # populate cache
        all_arrays = kernel.arrays_read | kernel.arrays_written
        return all_arrays.issubset(self._cached_gpu_array_set)

    def _emit_spirv_embeds(self):
        """Assemble SPIR-V text with spirv-as and embed binaries as C byte arrays."""
        import subprocess, tempfile, os
        if not self.backend:
            return
        device_code = self.backend.generate()
        parts = device_code.split("; SPIR-V")
        # Map sequential SPIR-V modules to kernel IDs from the plan
        # First: extracted kernels, then sort kernels (histogram, scan, scatter)
        kernel_ids = [k.kernel_id for k in self.gpu_plan.kernels]
        sort_kids = []
        for sp in self.gpu_plan.sort_plans:
            sort_kids.extend([sp.histogram_kernel_id, sp.scan_kernel_id,
                              sp.scatter_kernel_id])
        all_kids = kernel_ids + sort_kids
        part_idx = 0
        for part in parts:
            if not part.strip():
                continue
            if part_idx >= len(all_kids):
                break
            kid = all_kids[part_idx]
            # Skip SPIRV assembly for init-only kernels (no GPU buffers)
            if part_idx < len(kernel_ids):
                k_obj = self.gpu_plan.kernels[part_idx]
                if not self._is_gpu_kernel(k_obj):
                    part_idx += 1
                    continue
            spvasm = "; SPIR-V" + part

            # Write text assembly to temp file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".spvasm", delete=False, prefix="ergo_k"
            ) as f:
                f.write(spvasm)
                asm_path = f.name
            spv_path = asm_path.replace(".spvasm", ".spv")

            try:
                result = subprocess.run(
                    ["spirv-as", "--target-env", "spv1.3",
                     asm_path, "-o", spv_path],
                    capture_output=True, text=True,
                )
                if result.returncode != 0:
                    import sys
                    print(f"[spirv] spirv-as failed for kernel_{kid}:",
                          file=sys.stderr)
                    print(result.stderr, file=sys.stderr)
                    self._put_raw(f"/* ERROR: spirv-as failed for kernel_{kid} */")
                    part_idx += 1
                    continue

                with open(spv_path, "rb") as f:
                    spv_bytes = f.read()

                # Emit as static const unsigned char array
                self._put_raw(f"static const unsigned char kernel_{kid}_spv[] = {{")
                line = "    "
                for i, b in enumerate(spv_bytes):
                    line += f"0x{b:02x},"
                    if (i + 1) % 16 == 0:
                        self._put_raw(line)
                        line = "    "
                if line.strip():
                    self._put_raw(line)
                self._put_raw(f"}};")
                self._put_raw(f"static const size_t kernel_{kid}_spv_size = sizeof(kernel_{kid}_spv);")
            finally:
                os.unlink(asm_path)
                if os.path.exists(spv_path):
                    os.unlink(spv_path)

            part_idx += 1

    def _emit_cli_parsing(self):
        """Emit runtime CLI argument parsing for -N, -M, --frames, --no-spawn."""
        self._put("/* Runtime CLI overrides */")
        self._put("int _cli_n = 0, _cli_m = 0, _cli_frames = 0, _cli_no_spawn = 0;")
        self._put("for (int _i = 1; _i < argc; _i++) {")
        self.indent += 1
        self._put('if (strcmp(argv[_i], "-N") == 0 && _i + 1 < argc)')
        self._put("    _cli_n = atoi(argv[++_i]);")
        self._put('else if (strcmp(argv[_i], "-M") == 0 && _i + 1 < argc)')
        self._put("    _cli_m = atoi(argv[++_i]);")
        self._put('else if (strcmp(argv[_i], "--frames") == 0 && _i + 1 < argc)')
        self._put("    _cli_frames = atoi(argv[++_i]);")
        self._put('else if (strcmp(argv[_i], "--no-spawn") == 0)')
        self._put("    _cli_no_spawn = 1;")
        self.indent -= 1
        self._put("}")
        # Override DEFAULT_FRAMES via runtime variable
        if "DEFAULT_FRAMES" in self._var_types:
            self._put("int _max_frames = DEFAULT_FRAMES;")
            self._put("if (_cli_frames > 0) {")
            self._put('    fprintf(stderr, "[CLI] --frames %d\\n", _cli_frames);')
            self._put("    _max_frames = _cli_frames;")
            self._put("}")
        self._put("")

    def _emit_vram_capacity(self):
        """Emit runtime MAXPART/CAPACITY computation from VRAM.

        Queries DEVICE_LOCAL heap size, computes bytes-per-particle
        (including ping-pong 2x), and clamps MAXPART to 50% of available.
        """
        # Compute bytes per particle from GPU array shapes
        # Particle arrays have shape (MAXPART,), grid arrays have shape (32,32,32)
        particle_arrays = []
        pp = getattr(self, '_pp_arrays', set())
        for arr in self._gpu_arrays():
            shape = self._array_shapes.get(arr)
            if shape and len(shape) == 1:
                # 1D array sized by MAXPART — this is a particle array
                sz = self._gpu_sizeof(arr)
                multiplier = 2 if arr in pp else 1
                particle_arrays.append((arr, sz, multiplier))

        if not particle_arrays:
            return  # no particle arrays, nothing to scale

        # Only emit VRAM capacity code if program declares MAXPART
        if "MAXPART" not in self._var_types:
            return

        # Sum bytes per particle (resolve sizeof to actual byte count)
        from .ir import get_real_precision
        real_bytes = 4 if get_real_precision() == 32 else 8
        def _sizeof_bytes(sz_expr: str) -> int:
            if "int" in sz_expr:
                return 4
            return real_bytes
        bytes_per_particle = sum(
            _sizeof_bytes(sz) * mult for _, sz, mult in particle_arrays)

        self._put(f"/* VRAM-based particle capacity */")
        self._put(f"{{")
        self.indent += 1
        self._put(f"size_t _vram = ergo_vk_device_local_bytes();")
        self._put(f"size_t _budget = _vram / 2;  /* 50% of DEVICE_LOCAL */")
        self._put(f"int _vram_cap = (int)(_budget / {bytes_per_particle});")
        self._put(f"if (_vram_cap < 1024) _vram_cap = MAXPART;  "
                  f"/* floor: use MAXPART if VRAM query fails */")
        self._put(f"if (_vram_cap < MAXPART) {{")
        self.indent += 1
        self._put(f"fprintf(stderr, \"[VRAM] clamping MAXPART %d → %d "
                  f"(%.0f MB VRAM, %d bytes/particle)\\n\",")
        self._put(f"    MAXPART, _vram_cap, (double)_vram / (1024*1024), "
                  f"{bytes_per_particle});")
        self._put(f"CAPACITY = _vram_cap;")
        self.indent -= 1
        self._put(f"}} else {{")
        self.indent += 1
        self._put(f"fprintf(stderr, \"[VRAM] %.0f MB → %d particles "
                  f"available (MAXPART=%d)\\n\",")
        self._put(f"    (double)_vram / (1024*1024), _vram_cap, MAXPART);")
        self._put(f"CAPACITY = MAXPART;")
        self.indent -= 1
        self._put(f"}}")
        self._put(f"if (CAPACITY <= 0) CAPACITY = MAXPART;  "
                  f"/* absolute failsafe */")
        # Runtime overrides from JNI (Android) or host env
        self._put(f"{{ extern int ergo_max_cap __attribute__((weak));")
        self._put(f"  if (&ergo_max_cap && ergo_max_cap > 0 "
                  f"&& ergo_max_cap < CAPACITY)")
        self._put(f"    CAPACITY = ergo_max_cap; }}")
        # Runtime CLI -M is applied after SIM_INIT (see _emit_body)
        self.indent -= 1
        self._put(f"}}")

    def _emit_gpu_init(self):
        """Emit Vulkan init, buffer allocation, and pipeline creation."""
        self._put("/* === Vulkan init === */")
        if self.render:
            self._put("ergo_vk_init(0); /* windowed */")
        else:
            self._put("ergo_vk_init(1); /* headless */")
        # Compute VRAM-based particle capacity (50% of DEVICE_LOCAL heap)
        self._emit_vram_capacity()
        self._put("")

        # Ping-pong disabled until SPIRV offset injection bug is resolved
        pp_arrays: set[str] = set()
        self._pp_arrays = pp_arrays

        # Allocate device buffers (2x for ping-pong arrays).
        # Particle arrays (1D, sized by MAXPART) use CAPACITY for VRAM-aware sizing.
        self._put("/* Device buffers */")
        for arr in self._gpu_arrays():
            shape = self._array_shapes.get(arr)
            sz = self._gpu_sizeof(arr)
            if shape:
                # Replace MAXPART with CAPACITY for 1D particle arrays
                dims = []
                for d in shape:
                    expr = self._dim_expr(d)
                    if expr == "MAXPART":
                        dims.append("CAPACITY")
                    else:
                        dims.append(expr)
                size_expr = " * ".join(dims)
                if arr in pp_arrays:
                    self._put(f"ErgoVkBuf d_{arr} = ergo_vk_create_buffer("
                              f"2 * {size_expr} * {sz}); /* ping-pong 2x */")
                else:
                    self._put(f"ErgoVkBuf d_{arr} = ergo_vk_create_buffer("
                              f"{size_expr} * {sz});")
            else:
                self._put(f"ErgoVkBuf d_{arr} = ergo_vk_create_buffer("
                          f"{sz}); /* scalar fallback */")
        if pp_arrays:
            # Pre-swapped: first frame_begin swap will flip to rd=0, wr=CAPACITY
            # so frame 1 reads from offset 0 (where initial upload landed)
            # and writes to the second half [CAPACITY..2*CAPACITY)
            self._put(f"int _pp_rd_offset = CAPACITY;")
            self._put(f"int _pp_wr_offset = 0;")
        self._put("")

        # Load SPIR-V pipelines — for now, from external .spv files
        # Phase E will embed the binaries
        self._put("/* Load compute pipelines (from external .spv files) */")
        for k in self.gpu_plan.kernels:
            if not self._is_gpu_kernel(k):
                continue  # skip init-only kernels without GPU buffers
            n_bufs = len(k.arrays_written) + len(k.arrays_read - k.arrays_written)
            scalars = sorted(k.scalars_read,
                             key=lambda s: (0 if self._var_types.get(s, IRType.REAL) == IRType.REAL else 1, s))
            pc_size = 0
            from .ir import get_real_precision
            real_sz = 4 if get_real_precision() == 32 else 8
            has_real = False
            for s in scalars:
                t = self._var_types.get(s, IRType.REAL)
                if t == IRType.REAL:
                    has_real = True
                    if pc_size % real_sz != 0:
                        pc_size += (real_sz - pc_size % real_sz)
                    pc_size += real_sz
                else:
                    pc_size += 4
            # Match C struct trailing padding (align to largest member)
            if has_real and pc_size % real_sz != 0:
                pc_size += (real_sz - pc_size % real_sz)
            # Ping-pong offsets (2 × int) if this kernel has read-write arrays
            k_pp = k.arrays_read & k.arrays_written
            if k_pp and hasattr(self, '_pp_arrays') and k_pp & self._pp_arrays:
                pc_size += 4 * 2  # _pp_rd_offset + _pp_wr_offset
            self._put(f"ErgoVkPipe pipe_{k.kernel_id} = ergo_vk_load_shader("
                      f"kernel_{k.kernel_id}_spv, kernel_{k.kernel_id}_spv_size, "
                      f"{n_bufs}, {pc_size});")
        self._put("")

        # Sort-by-GEN buffers and pipelines
        for sp in self.gpu_plan.sort_plans:
            self._put("/* Sort-by-GEN: temporary buffers */")
            self._put(f"ErgoVkBuf d_sort_histogram = ergo_vk_create_buffer(32 * sizeof(int));")
            self._put(f"ErgoVkBuf d_sort_offsets = ergo_vk_create_buffer(32 * sizeof(int));")
            for arr in sp.arrays:
                sz = self._gpu_sizeof(arr)
                self._put(f"ErgoVkBuf d_sort_{arr} = ergo_vk_create_buffer("
                          f"MAXPART * {sz});")
            self._put("")
            # Histogram kernel: 2 buffers (FLAGS, histogram), 3 push constants (NPART, GEN_SHIFT, GEN_MASK)
            self._put("/* Sort-by-GEN: compute pipelines */")
            self._put(f"ErgoVkPipe pipe_{sp.histogram_kernel_id} = ergo_vk_load_shader("
                      f"kernel_{sp.histogram_kernel_id}_spv, kernel_{sp.histogram_kernel_id}_spv_size, "
                      f"2, 12);")
            # Scan kernel: 2 buffers (histogram, offsets), 0 push constants
            self._put(f"ErgoVkPipe pipe_{sp.scan_kernel_id} = ergo_vk_load_shader("
                      f"kernel_{sp.scan_kernel_id}_spv, kernel_{sp.scan_kernel_id}_spv_size, "
                      f"2, 0);")
            # Scatter kernel: 2 + 2*N buffers, 3 push constants
            n_arrays = len(sp.arrays)
            self._put(f"ErgoVkPipe pipe_{sp.scatter_kernel_id} = ergo_vk_load_shader("
                      f"kernel_{sp.scatter_kernel_id}_spv, kernel_{sp.scatter_kernel_id}_spv_size, "
                      f"{2 + 2 * n_arrays}, 12);")
            self._put("")

        # Initial upload of all GPU arrays
        self._put("/* Upload initial state */")
        for arr in self._gpu_arrays():
            shape = self._array_shapes.get(arr)
            if shape:
                size_expr = " * ".join(self._dim_expr(d) for d in shape)
                sz = self._gpu_sizeof(arr)
                self._put(f"ergo_vk_upload(d_{arr}, {arr}, "
                          f"{size_expr} * {sz});")
        self._put("")

    def _emit_render_only_init(self):
        """Emit Vulkan init and render buffer allocation for CPU-only rendering.

        Called when --render is used but no GPU kernels were extracted.
        Detects particle SoA pattern and creates buffers for visualization.
        """
        self._put("/* === Vulkan render-only init === */")
        self._put("ergo_vk_init(0); /* windowed */")
        self._put("")

        particle = self._detect_particle_soa()
        if particle:
            # Create GPU buffers for the render arrays
            self._put("/* Render buffers (particle SoA) */")
            for arr in particle["render_arrays"]:
                shape = self._array_shapes.get(arr)
                sz = self._gpu_sizeof(arr)
                if shape:
                    size_expr = " * ".join(self._dim_expr(d) for d in shape)
                    self._put(f"ErgoVkBuf d_{arr} = ergo_vk_create_buffer("
                              f"{size_expr} * {sz});")
            self._put("")
        else:
            # Grid-based: find best REAL array and create one buffer
            render_arr = None
            for name, shape in self._array_shapes.items():
                t = self._var_types.get(name, IRType.REAL)
                if t == IRType.REAL:
                    if "PSI" in name.upper():
                        render_arr = name
                        break
                    if render_arr is None:
                        render_arr = name
            if render_arr:
                shape = self._array_shapes.get(render_arr)
                sz = self._gpu_sizeof(render_arr)
                if shape:
                    size_expr = " * ".join(self._dim_expr(d) for d in shape)
                    self._put(f"/* Render buffer (grid) */")
                    self._put(f"ErgoVkBuf d_{render_arr} = ergo_vk_create_buffer("
                              f"{size_expr} * {sz});")
                    self._put("")

    def _emit_gpu_dispatch(self, kernel: KernelPlan):
        """Emit a GPU kernel dispatch in place of a CPU loop."""
        kid = kernel.kernel_id
        bound = self._operand(kernel.loop_bound)

        self._put(f"/* GPU dispatch: kernel_{kid} (source line {kernel.source_line}) */")

        # Bind buffers
        buf_idx = 0
        for arr in sorted(kernel.arrays_written):
            self._put(f"ergo_vk_bind_buffer(pipe_{kid}, {buf_idx}, d_{arr});")
            buf_idx += 1
        for arr in sorted(kernel.arrays_read - kernel.arrays_written):
            self._put(f"ergo_vk_bind_buffer(pipe_{kid}, {buf_idx}, d_{arr});")
            buf_idx += 1

        # Push constants — member names prefixed with _s_ to avoid
        # collision with #define'd PARAMETER macros (e.g. PFLAG_ACTIVE).
        # Sort by type (doubles first, then ints) to match SPIRV layout
        # and avoid mixed-type padding mismatches.
        scalars = sorted(kernel.scalars_read,
                         key=lambda s: (0 if self._var_types.get(s, IRType.REAL) == IRType.REAL else 1, s))
        # Check for ping-pong arrays (read AND written)
        # Uses self._pp_arrays which is disabled until PP bug is fixed
        pp_arrays = kernel.arrays_read & kernel.arrays_written & getattr(self, '_pp_arrays', set())
        has_pp = len(pp_arrays) > 0 and self._is_gpu_kernel(kernel)

        if scalars or has_pp:
            self._put(f"{{")
            self.indent += 1
            self._put(f"struct {{")
            self.indent += 1
            pc_vals = list(scalars)
            for s in scalars:
                t = self._var_types.get(s, IRType.REAL)
                c_type = IRType.REAL.c_type if t == IRType.REAL else "int"
                self._put(f"{c_type} _s_{s};")
            if has_pp:
                self._put(f"int _s__pp_rd_offset;")
                self._put(f"int _s__pp_wr_offset;")
                pc_vals.append("_pp_rd_offset")
                pc_vals.append("_pp_wr_offset")
            self.indent -= 1
            self._put(f"}} _pc = {{ {', '.join(pc_vals)} }};")
            self._put(f"ergo_vk_push_constants(pipe_{kid}, &_pc, sizeof(_pc));")
            self.indent -= 1
            self._put(f"}}")

        if self._batched_frame:
            self._put(f"ergo_vk_frame_dispatch(pipe_{kid}, ({bound} + 255) / 256);")
        else:
            self._put(f"ergo_vk_dispatch(pipe_{kid}, ({bound} + 255) / 256);")

    def _emit_gpu_download_for_suffix(self, kernel: KernelPlan):
        """Download arrays that the structural CPU suffix needs to read.
        In batched frame mode, GPU work hasn't executed yet — we download
        from PP_RD (previous frame's output, already committed).
        Uses ping-pong offset for read-write arrays."""
        pp = getattr(self, '_pp_arrays', set())
        self._put("/* Download GPU results for CPU access */")
        for arr in sorted(kernel.arrays_written):
            shape = self._array_shapes.get(arr)
            if shape:
                size_expr = " * ".join(self._dim_expr(d) for d in shape)
                sz = self._gpu_sizeof(arr)
                if arr in pp:
                    self._put(f"ergo_vk_download_at(d_{arr}, {arr}, "
                              f"(size_t)_pp_wr_offset * {sz}, "
                              f"{size_expr} * {sz});")
                else:
                    self._put(f"ergo_vk_download(d_{arr}, {arr}, "
                              f"{size_expr} * {sz});")

    def _emit_gpu_upload_after_suffix(self, kernel: KernelPlan, suffix_items: list):
        """Upload arrays that the structural CPU suffix may have modified.
        Uses ping-pong offset for read-write arrays."""
        gpu_array_set = set(self._gpu_arrays())
        suffix_writes: set[str] = set()
        self._collect_array_writes(suffix_items, suffix_writes)
        suffix_writes &= gpu_array_set
        pp = getattr(self, '_pp_arrays', set())
        for arr in sorted(suffix_writes):
            shape = self._array_shapes.get(arr)
            if shape:
                size_expr = " * ".join(self._dim_expr(d) for d in shape)
                sz = self._gpu_sizeof(arr)
                if arr in pp:
                    self._put(f"ergo_vk_upload_at(d_{arr}, {arr}, "
                              f"(size_t)_pp_wr_offset * {sz}, "
                              f"{size_expr} * {sz});")
                else:
                    self._put(f"ergo_vk_upload(d_{arr}, {arr}, "
                              f"{size_expr} * {sz});")
        # Mark these arrays as GPU-current
        self._gpu_current |= suffix_writes

    def _collect_array_writes(self, items: list, writes: set[str]):
        """Walk IR items and collect names of arrays written by STORE or ZERO ops."""
        for item in items:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.op in (Op.STORE, Op.ZERO):
                        arr = inst.meta.get("array", "")
                        if arr:
                            writes.add(arr)
            elif isinstance(item, IRIf):
                self._collect_array_writes(item.then_body, writes)
                if item.else_body:
                    self._collect_array_writes(item.else_body, writes)
            elif isinstance(item, IRLoop):
                self._collect_array_writes(item.body, writes)
            elif isinstance(item, IRWhileLoop):
                self._collect_array_writes(item.body, writes)

    def _collect_array_reads(self, items: list, reads: set[str]):
        """Walk IR items and collect names of arrays read by LOAD ops."""
        for item in items:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.op == Op.LOAD:
                        arr = inst.meta.get("array", "")
                        if arr:
                            reads.add(arr)
            elif isinstance(item, IRIf):
                self._collect_array_reads(item.then_body, reads)
                if item.else_body:
                    self._collect_array_reads(item.else_body, reads)
            elif isinstance(item, IRLoop):
                self._collect_array_reads(item.body, reads)

    # ── helpers ──────────────────────────────────────────────

    def _is_int_operand(self, op: Operand) -> bool:
        if isinstance(op, IRConst):
            return op.type == IRType.INTEGER
        if isinstance(op, IRRef):
            t = self._var_types.get(op.name, op.type)
            return t == IRType.INTEGER
        return False

    def _collect_temps(self, items: list) -> dict[str, IRType]:
        """Walk structured IR body and collect all temporary variable names and types."""
        temps: dict[str, IRType] = {}
        for item in items:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.result and inst.result.startswith("_"):
                        temps[inst.result] = inst.type
            elif isinstance(item, IRIf):
                temps.update(self._collect_temps(item.then_body))
                if item.else_body:
                    temps.update(self._collect_temps(item.else_body))
            elif isinstance(item, IRLoop):
                temps.update(self._collect_temps(item.body))
            elif isinstance(item, IRWhileLoop):
                temps.update(self._collect_temps([item.cond_block]))
                temps.update(self._collect_temps(item.body))
            elif isinstance(item, IRSelect):
                for _, case_body in item.cases:
                    temps.update(self._collect_temps(case_body))
        return temps

    def _emit_temps(self, items: list):
        """Declare all SSA temporaries used in the body."""
        temps = self._collect_temps(items)
        # Skip temps already declared as main_locals (e.g. from inlining)
        declared = {v.name for v in self.module.main_locals}
        temps = {k: v for k, v in temps.items() if k not in declared}
        # Register in var_types for type inference
        for name, t in temps.items():
            self._var_types[name] = t
        # Group by type
        by_type: dict[str, list[str]] = {}
        for name, t in sorted(temps.items()):
            ct = self._c_type(t)
            by_type.setdefault(ct, []).append(name)
        for ct, names in sorted(by_type.items()):
            for i in range(0, len(names), 10):
                batch = names[i:i+10]
                self._put(f"{ct} {', '.join(batch)};")

    def _format_for_operand(self, op: Operand) -> str:
        if isinstance(op, IRConst):
            return {
                IRType.INTEGER: "%d", IRType.REAL: "%f",
                IRType.LOGICAL: "%d",
            }.get(op.type, "%f")
        if isinstance(op, IRRef):
            t = self._var_types.get(op.name, op.type)
            return {
                IRType.INTEGER: "%d", IRType.REAL: "%f",
                IRType.LOGICAL: "%d",
            }.get(t, "%f")
        return "%f"

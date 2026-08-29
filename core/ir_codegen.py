"""C99 code generator from Ergo IR.

Consumes an IRModule and produces C99 source code. This replaces the
direct AST-to-C codegen path — the pipeline is now:

    AST -> Checker -> IR -> C99

The existing AST codegen (codegen.py) is preserved as a reference and fallback.

Tile clipmap: when --gpu-tile-size is active and the program declares a
STATIC INTEGER array named TILE_CLIP, the host tile loop of every tiled
non-reduction kernel skips tiles flagged 0 (skipped tile = its output
elements are not updated this dispatch; stale device values persist —
soundness is the program's responsibility). See --gpu-tile-size docs.

Frame-loop kernel scans (upload_set / kernel_reads for the end-of-frame
CPU->GPU sync) recurse into nested IF/loop bodies via
_collect_kernel_ids — kernels nested inside conditionals (e.g. the DBM
solver's IF-guarded sweep loops) still get their CPU-dirtied arrays
uploaded.

Dirty-range transfers (Inc-4): 1-D GPU-resident arrays get a runtime
dirty interval (_rg_lo_ARR/_rg_hi_ARR, 0-based, file-scope) merged at
every CPU store / ZERO — only executed writes count, so guarded writes
(e.g. CAP>0 branches) cost no upload when skipped, and point deposits
upload 4 bytes instead of the whole array. Uploads become a guarded
ergo_vk_upload_at over the interval; arrays without tracking (multi-dim,
ping-pong) keep whole-array uploads. Mid-body downloads of arrays whose
remaining CPU reads all sit under one MOD(G,k)==0 guard are emitted
inside that guard (e.g. every-250-step residual probes no longer force
per-step whole-array downloads). Never under-approximates: any
unanalyzable access falls back to whole-array.
"""

from __future__ import annotations

from .ir import (
    IRModule, IRFunc, IRVar, IRBlock, IRIf, IRLoop, IRSelect, IRWhileLoop,
    IRInst, IRConst, IRRef, IRType, StorageClass, Op, Operand,
    get_real_precision,
)
from .ir_gpu import GPUPlan, KernelPlan
from . import ast_nodes as ast
from .errors import MCLError


def _c_type(t: IRType) -> str:
    """Map IR type to C type, respecting precision setting."""
    if t == IRType.REAL:
        return IRType.REAL.c_type  # "float" or "double" per global precision
    return {
        IRType.INTEGER: "int",
        IRType.INT64: "long long",
        IRType.LOGICAL: "int",
        IRType.CHARACTER: "char",
        IRType.STRING: "const char*",
        IRType.VOID: "void",
    }[t]

# Legacy dict — some code paths still use this directly
C_TYPE = {
    IRType.INTEGER: "int",
    IRType.INT64: "long long",
    IRType.LOGICAL: "int",
    IRType.CHARACTER: "char",
    IRType.STRING: "const char*",
    IRType.VOID: "void",
}

# Math intrinsics -> C function name (f32 mode appends "f": sin -> sinf)
C_MATH = {
    Op.SIN: "sin", Op.COS: "cos", Op.TAN: "tan",
    Op.ASIN: "asin", Op.ACOS: "acos", Op.ATAN: "atan", Op.ATAN2: "atan2",
    Op.EXP: "exp", Op.LOG: "log", Op.LOG10: "log10",
    Op.SQRT: "sqrt", Op.SINH: "sinh", Op.COSH: "cosh", Op.TANH: "tanh",
}


def _real_math(base: str) -> str:
    """libm function name for the current REAL precision (sin vs sinf)."""
    return base + "f" if get_real_precision() == 32 else base


def _c_str_escape(s: str) -> str:
    """Escape a string's contents for a C string literal."""
    return (s.replace("\\", "\\\\")
             .replace('"', '\\"')
             .replace("\n", "\\n"))


def _c_str_lit(value) -> str:
    """Emit a string value as a quoted, escaped C string literal."""
    return f'"{_c_str_escape(str(value))}"'


def _real_lit(value) -> str:
    """Format a REAL literal respecting the precision setting.

    f32 mode keeps the repr digits and appends an 'f' suffix — C rounds the
    decimal to the nearest f32, matching how spirv-as rounds the same
    decimal on the GPU side. repr() of inf/nan is not valid C ('inf.0'
    was emitted before), so those map to GCC/Clang builtins (this
    compiler's driver is gcc-only).
    """
    f32 = get_real_precision() == 32
    s = repr(value) if isinstance(value, float) else str(value)
    if s in ("inf", "-inf", "nan"):
        if f32:
            return {"inf": "__builtin_inff()",
                    "-inf": "-__builtin_inff()",
                    "nan": '__builtin_nanf("")'}[s]
        return {"inf": "__builtin_inf()",
                "-inf": "-__builtin_inf()",
                "nan": '__builtin_nan("")'}[s]
    if "." not in s and "e" not in s.lower():
        s += ".0"
    if f32:
        s += "f"
    return s


class IRCodeGen:
    def __init__(self, module: IRModule, gpu_plan: GPUPlan | None = None,
                 backend=None, render: bool = False, jit_mode: bool = False,
                 no_verify: bool = False, gpu_tile_size: int = 0):
        self.module = module
        self.gpu_plan = gpu_plan
        self.backend = backend
        self.render = render
        self.jit_mode = jit_mode
        self.no_verify = no_verify
        # --gpu-tile-size: dispatch extracted kernels in contiguous tiles
        # over the same buffer (0 = whole-range dispatch, unchanged).
        # Quantized to a workgroup multiple so tiled reduction partials
        # partition the range exactly like the untiled dispatch.
        self.gpu_tile_size = gpu_tile_size
        self._qtile = max(256, (gpu_tile_size // 256) * 256)
        # Tile clipmap: size expression of the program-declared
        # TILE_CLIP array, or None when absent/inert. Set in
        # _emit_gpu_init (needs _array_shapes/_var_types populated).
        self._tile_clip_size: str | None = None
        self._clip_warned: set = set()  # reduction kids warned about
        self._in_frame_loop = False
        self._batched_frame = False  # True inside batched frame dispatch loop
        self._frame_gpu_dirty = set()  # GPU arrays written by a dispatch
        # A6: by-reference scalar dummies (Fortran argument semantics).
        # Subroutine signature table + the ref set active during the
        # subroutine body currently being emitted.
        self._ir_subs = {fn.name: fn for fn in module.functions
                         if fn.is_subroutine}
        self._ref_scalars: set[str] = set()
        self._carg_counter = 0  # deterministic temp naming for call args
                                       # in the current frame (D19)
        self._frame_ended_early = False  # True when frame_end emitted before CPU suffix
        # Coalesced reductions: reduction kernels dispatched into the
        # current batched frame whose host read-back is deferred to one
        # drain + one combined download (see _flush_pending_reductions).
        self._pending_reductions: list = []
        self.lines: list[str] = []
        self.indent = 0
        self._last_line_directive = 0
        # Per-loop counter for hoisted DO bound temporaries (_ergo_endN etc.)
        self._loop_tmp_counter = 0
        # Track var types for PRINT format inference
        self._var_types: dict[str, IRType] = {}
        # Track arrays for subscript codegen
        self._array_shapes: dict[str, tuple] = {}
        # Track function return types
        self._func_return_types: dict[str, IRType] = {}
        # ALLOCATABLE arrays declared with a size companion (_ergo_sz_*)
        self._allocatable: set[str] = set()

        # Build kernel lookup: loop source line -> KernelPlan
        # Used by _emit_loop to decide whether to emit dispatch or for-loop
        self._kernel_by_line: dict[int, KernelPlan] = {}
        self._kernel_by_id: dict[int, KernelPlan] = {}
        if gpu_plan:
            for k in gpu_plan.kernels:
                self._kernel_by_line[k.source_line] = k
                self._kernel_by_id[k.kernel_id] = k

        # Track arrays recently uploaded to GPU (cleared on CPU write).
        # Used to eliminate redundant uploads in the merged render+sync pass.
        self._gpu_current: set[str] = set()
        # CPU-dirty arrays: written on the host, not yet uploaded. Shared
        # across ALL body-nesting levels (an init loop in an outer body
        # must be visible to the upload-before-dispatch logic of kernels
        # nested in inner loops). Cleared per-array on upload and when a
        # GPU kernel rewrites the array.
        self._cpu_dirty: set[str] = set()
        # Arrays already downloaded in the current loop body — used by the
        # end-of-iteration refresh to avoid re-downloading data the
        # mid-body logic already fetched this iteration.
        self._body_downloaded: set[str] = set()

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

        # Find best color array: prefer OMEGA_NAT, then VEL_X, then POS_X
        # ERGO_COLOR env var overrides at runtime (e.g. ERGO_COLOR=VEL_X)
        color_arr = "POS_X"
        for candidate in ["OMEGA_NAT", "VEL_X", "THETA"]:
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
        # File I/O runtime (Spec Part 10): unit table + OPEN/CLOSE/raw
        # helpers — header-only, always included (static inline, no
        # cost when unused).
        self._put_raw("#include \"ergo_io.h\"")
        if self._uses_esf(mod):
            self._put_raw("#include \"ergo_stream.h\"")
        self._put_raw("")
        self._put_raw("#ifndef ERGO_BUILD_VERSION")
        self._put_raw('#define ERGO_BUILD_VERSION "unknown"')
        self._put_raw("#endif")
        self._put_raw("")

        # FNV-1a hash helper for ERGO_HASH_FINAL=1 state-hash diagnostic.
        # Only emitted when GPU state needs to be hashable on exit.
        if has_gpu:
            self._put_raw("/* FNV-1a 64-bit, byte-wise. Used by ERGO_HASH_FINAL=1. */")
            self._put_raw("static unsigned long long _ergo_fnv1a_update("
                          "unsigned long long h, const void *data, size_t n) {")
            self._put_raw("    const unsigned char *p = (const unsigned char*)data;")
            self._put_raw("    for (size_t i = 0; i < n; i++) {"
                          " h ^= p[i]; h *= 1099511628211ULL; }")
            self._put_raw("    return h;")
            self._put_raw("}")
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

        # Dirty-range transfer state (Inc-4): one runtime interval per
        # tracked (1-D, GPU-resident, non-pp) array. File scope so CPU
        # subroutines' stores can merge too. [lo,hi] 0-based inclusive;
        # hi < 0 = no tracked write since last upload.
        if self.gpu_plan:
            _rg_arrays = [a for a in self._gpu_arrays()
                          if self._rg_tracked(a)]
            if _rg_arrays:
                self._put_raw("/* runtime dirty intervals (Inc-4) */")
                for a in _rg_arrays:
                    kw = "" if self.jit_mode else "static "
                    self._put_raw(f"{kw}int _rg_lo_{a} = 2147483647, "
                                  f"_rg_hi_{a} = -1;")
                self._put_raw("")

        # Emit arena BSS if any ALLOC/FREE op is reachable from main or a
        # function body. BSS is zero-filled by the loader; no libc.
        if self._uses_allocate(mod):
            self._emit_arena_decl()

        # Emit the _ergo_dot helper once if DOT_PRODUCT/NORM2 is used.
        if self._uses_dot(mod):
            self._emit_dot_helper()

        # Emit the splitmix64 hash helpers once if HASH/RAND is used.
        if self._uses_hash(mod):
            self._emit_hash_helper()

        # Embed SPIR-V binaries as byte arrays (if GPU)
        if has_gpu:
            self._emit_spirv_embeds()
            self._put_raw("")

        # Emit functions. Skip definitions with no remaining call sites:
        # subroutine inlining (GPU extraction) can leave dead definitions
        # whose bodies need not be CPU-lowerable (e.g. RING_* intrinsics,
        # which are GPU-only).
        referenced = None
        if not self.jit_mode:
            referenced = self._collect_referenced_funcs(mod)
        for fn in mod.functions:
            if referenced is not None and fn.name not in referenced:
                continue  # dead after inlining — no call sites remain
            self._emit_function(fn)
            self._put_raw("")

        # JIT mode: no main(), just export functions + statics
        if self.jit_mode:
            return "\n".join(self.lines) + "\n"

        # Emit main
        self._put("int main(int argc, char *argv[]) {")
        self.indent += 1
        self._put('fprintf(stderr, "[ergo] Ergo build: %s\\n", ERGO_BUILD_VERSION);')

        # Runtime CLI parsing
        self._emit_cli_parsing()

        # Declare main locals
        self._allocatable.clear()
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

        # Final-state hash hook (ERGO_HASH_FINAL=1)
        if has_gpu:
            self._emit_final_hash_hook()

        # GPU shutdown
        if has_gpu or self.render:
            self._put("ergo_vk_shutdown();")

        # NET shutdown
        if has_net:
            self._put("if (_consensus_enabled) ergo_net_close(&_ergo_net);")

        # File I/O shutdown: flush+close open units in unit order
        self._put("_ergo_io_shutdown();")

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
        if t == IRType.STRING:
            return _c_str_lit(value)
        if t == IRType.REAL and isinstance(value, str):
            # Defensive: during the TYPE_MAP transition a string literal
            # may still arrive REAL-typed — treat it as a string.
            return _c_str_lit(value)
        if t == IRType.REAL:
            return _real_lit(value)
        if t == IRType.INTEGER:
            return str(value)
        if t == IRType.INT64:
            return f"{value}LL"
        if t == IRType.LOGICAL:
            return "1" if value else "0"
        return str(value)

    def _operand(self, op: Operand) -> str:
        if isinstance(op, IRConst):
            return self._const_lit(op.type, op.value)
        if isinstance(op, IRRef):
            # A6: by-reference scalar dummy read — dereference the pointer
            if op.name in self._ref_scalars:
                return f"(*{op.name})"
            return op.name
        return "/* ? */"

    # ── static vars ──────────────────────────────────────────

    def _emit_static_var(self, g: IRVar, mod: IRModule):
        ct = self._c_type(g.type)
        # JIT mode: omit the `static` keyword so the symbol is exported
        # from the shared library and reachable via ctypes (JitLibrary
        # reads/writes STATIC storage directly — the Ergo idiom).
        kw = "" if self.jit_mode else "static "
        if g.shape:
            # Column-major (LOCKED): declare the C array with reversed
            # dims — Ergo A(d0,d1,d2) → C A[d2][d1][d0] — so a reversed
            # subscript (see LOAD/STORE) addresses first-index-fastest.
            dims = "".join(f"[{self._dim_expr(d)}]" for d in reversed(g.shape))
            init = self._data_init(g.name, mod)
            self._put(f"{kw}{ct} {g.name}{dims}{init};")
        else:
            init = ""
            if g.init_value is not None:
                init = f" = {self._const_lit(g.type, g.init_value)}"
            elif g.name in mod.data_inits:
                vals = mod.data_inits[g.name]
                if vals:
                    init = f" = {self._const_lit(g.type, self._ast_lit_value(vals[0]))}"
            self._put(f"{kw}{ct} {g.name}{init};")

    def _data_init(self, name: str, mod: IRModule) -> str:
        if name not in mod.data_inits:
            return ""
        vals = mod.data_inits[name]
        if not vals:
            return ""
        val_strs = [self._ast_lit_str(v) for v in vals]
        return " = {" + ", ".join(val_strs) + "}"

    def _data_values(self, v: IRVar, mod: IRModule) -> list:
        """DATA values for v — module table first, then the IRVar's own
        record (populated by the builder for function-local DATA)."""
        vals = mod.data_inits.get(v.name)
        if vals:
            return vals
        return v.data_init or []

    def _data_array_init(self, v: IRVar, mod: IRModule) -> str:
        """Braced C array initializer from DATA values, or ""."""
        vals = self._data_values(v, mod)
        if not vals:
            return ""
        return " = {" + ", ".join(self._ast_lit_str(x) for x in vals) + "}"

    def _data_scalar_init(self, v: IRVar, mod: IRModule) -> str:
        """C scalar initializer from DATA values, or ""."""
        vals = self._data_values(v, mod)
        if not vals:
            return ""
        return f" = {self._const_lit(v.type, self._ast_lit_value(vals[0]))}"

    def _ast_lit_str(self, node) -> str:
        """Convert an AST literal to a C literal string."""
        if isinstance(node, ast.Literal):
            if node.type == "REAL":
                return _real_lit(node.value)
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

    def _sub_call_args(self, func: str, sub_fn, args) -> str:
        """A6: build a user-subroutine call's argument list.

        Scalar dummies are by-reference: a variable argument passes its
        address (a bare name when the argument is itself a by-reference
        dummy of the subroutine currently being emitted — pass-through
        of an already-pointer value); a constant argument is only
        reachable for read-only dummies (the checker rejects non-lvalue
        arguments to written dummies) and is copied to a temp whose
        address is passed.
        """
        if sub_fn is None:
            return ", ".join(self._operand(a) for a in args)
        parts = []
        for i, arg in enumerate(args):
            p = sub_fn.params[i]
            if p.shape:
                parts.append(self._operand(arg))
                continue
            if isinstance(arg, IRRef):
                if arg.name in self._ref_scalars:
                    parts.append(arg.name)
                else:
                    parts.append(f"&{arg.name}")
                continue
            # constant/expression into a read-only scalar dummy: temp copy
            self._carg_counter += 1
            t = f"_carg_{self._carg_counter}"
            ct = self._c_type(p.type)
            self._put(f"{ct} {t} = {self._operand(arg)};")
            parts.append(f"&{t}")
        return ", ".join(parts)

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
                    # Column-major (LOCKED): the caller's C array has
                    # reversed dims. A C function parameter drops the
                    # outermost C dim, i.e. the first dim of the reversed
                    # shape — so the trailing dims are reversed(shape) minus
                    # its first element.
                    dims = "".join(f"[{self._dim_expr(d)}]"
                                   for d in reversed(p.shape[:-1]))
                    parts.append(f"{ct} {p.name}[]{dims}")
            elif fn.is_subroutine:
                # A6: scalar subroutine dummies are by-reference
                # (Fortran semantics) — writes copy out to the caller.
                parts.append(f"{ct} *{p.name}")
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
        self._allocatable.clear()
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
        # A6: scalar dummies of a subroutine lower to C pointers —
        # reads/writes in the body dereference them.
        saved_ref = self._ref_scalars
        if fn.is_subroutine:
            self._ref_scalars = {p.name for p in fn.params if not p.shape}
        self._emit_body(fn.body)
        self._ref_scalars = saved_ref
        self._kernel_by_line = saved_kernel_map

        # Fortran semantics: falling off the end of a function returns the
        # function-name variable. Emit it explicitly — running off the end
        # of a non-void C function is undefined behavior. An explicit user
        # RETURN simply makes this line unreachable — harmless.
        if not fn.is_subroutine:
            self._put(f"return {fn.name}_;")

        self.indent -= 1
        self._put("}")

    # ── local declarations ───────────────────────────────────

    def _local_array_bytes(self, v: IRVar) -> int | None:
        """Compile-time byte size of a local array, or None."""
        if v.storage == StorageClass.STATIC or not v.shape:
            return None
        total = 1
        for d in v.shape:
            c = d if isinstance(d, int) else self._resolve_const(d)
            if c is None:
                return None
            total *= c
        if v.type == IRType.INTEGER:
            el = 4
        else:
            el = 4 if get_real_precision() == 32 else 8
        return total * el

    def _hoist_local(self, v: IRVar) -> bool:
        """A1: large compile-time-sized local arrays (>1 MB) lower to
        function-local C statics — file-scope lifetime, no stack frame
        pressure, no renaming. Reentrancy is safe because the checker
        rejects recursion cycles involving such functions
        (Checker._check_recursion). Persistence across calls can only
        mask (never create) read-before-write bugs; statics are
        zero-initialized, which is MORE deterministic than stack."""
        nbytes = self._local_array_bytes(v)
        return nbytes is not None and nbytes > 1024 * 1024

    def _warn_large_stack_array(self, v: IRVar):
        """A1: warn when a local array is too big for the stack and is
        NOT hoistable (size not compile-time-known). Hoisted arrays are
        reported as hoisted, not warned."""
        nbytes = self._local_array_bytes(v)
        if nbytes is None or nbytes <= 1024 * 1024:
            return
        import sys as _sys
        dims = ",".join(str(d if isinstance(d, int)
                            else self._resolve_const(d))
                        for d in v.shape)
        if self._hoist_local(v):
            print(f"ERGO NOTE: local array {v.name}({dims}) is "
                  f"{nbytes / 1e6:.1f} MB — hoisted to static storage "
                  f"(A1)", file=_sys.stderr)
        else:
            print(f"ERGO WARNING: local array {v.name}({dims}) is "
                  f"{nbytes / 1e6:.1f} MB on the stack; declare "
                  f"STATIC or raise ulimit", file=_sys.stderr)

    def _emit_local_decl(self, v: IRVar, mod: IRModule):
        self._emit_line(v.line)
        self._warn_large_stack_array(v)
        ct = self._c_type(v.type)
        if v.storage == StorageClass.PARAMETER:
            init = self._const_lit(v.type, v.init_value)
            self._put(f"const {ct} {v.name} = {init};")
        elif v.storage == StorageClass.ALLOCATABLE:
            self._put(f"{ct} *{v.name} = NULL;")
            # Byte-size companion, set by ALLOCATE; used by ZERO.
            self._put(f"size_t _ergo_sz_{v.name} = 0;")
            self._allocatable.add(v.name)
        elif v.shape:
            # Column-major (LOCKED): reversed C dims (see _emit_static_var).
            dims = "".join(f"[{self._dim_expr(d)}]" for d in reversed(v.shape))
            init = self._data_array_init(v, mod)
            # A1: >1MB locals become function-local statics (no stack)
            kw = "static " if self._hoist_local(v) else ""
            self._put(f"{kw}{ct} {v.name}{dims}{init};")
        else:
            init = ""
            if v.init_value is not None:
                init = f" = {self._const_lit(v.type, v.init_value)}"
            else:
                init = self._data_scalar_init(v, mod)
            self._put(f"{ct} {v.name}{init};")

    def _emit_local_decl_simple(self, v: IRVar):
        self._warn_large_stack_array(v)
        ct = self._c_type(v.type)
        if v.storage == StorageClass.PARAMETER:
            init = self._const_lit(v.type, v.init_value)
            self._put(f"const {ct} {v.name} = {init};")
        elif v.storage == StorageClass.ALLOCATABLE:
            self._put(f"{ct} *{v.name} = NULL;")
            # Byte-size companion, set by ALLOCATE; used by ZERO.
            self._put(f"size_t _ergo_sz_{v.name} = 0;")
            self._allocatable.add(v.name)
        elif v.shape:
            # Column-major (LOCKED): reversed C dims (see _emit_static_var).
            dims = "".join(f"[{self._dim_expr(d)}]" for d in reversed(v.shape))
            init = self._data_array_init(v, self.module)
            # A1: >1MB locals become function-local statics (no stack)
            kw = "static " if self._hoist_local(v) else ""
            self._put(f"{kw}{ct} {v.name}{dims}{init};")
        else:
            init = ""
            if v.init_value is not None:
                init = f" = {self._const_lit(v.type, v.init_value)}"
            else:
                init = self._data_scalar_init(v, self.module)
            self._put(f"{ct} {v.name}{init};")

    # ── runtime dirty-interval tracking (Inc-4) ─────────────

    def _rg_tracked(self, arr: str) -> bool:
        """True if arr gets runtime dirty-interval tracking: 1-D,
        GPU-resident, not ping-pong (pp uploads already use upload_at
        with the wr offset). Anything else keeps whole-array uploads —
        never under-approximate."""
        if not self.gpu_plan:
            return False
        if arr in getattr(self, '_pp_arrays', set()):
            return False
        shape = self._array_shapes.get(arr)
        return bool(shape) and len(shape) == 1 and arr in self._gpu_arrays()

    def _put_ranged_upload(self, arr: str, shape, sz: str):
        """Upload only the runtime dirty interval of arr (guarded — no
        upload at all when no tracked CPU write executed). Untracked
        arrays get the whole-array upload."""
        size_expr = " * ".join(self._dim_expr(d) for d in shape)
        if self._rg_tracked(arr):
            self._put(f"if (_rg_hi_{arr} >= 0) {{")
            self.indent += 1
            self._put(f"ergo_vk_upload_at(d_{arr}, {arr} + _rg_lo_{arr}, "
                      f"(size_t)_rg_lo_{arr} * {sz}, "
                      f"(size_t)(_rg_hi_{arr} - _rg_lo_{arr} + 1) * {sz});")
            self._put(f"_rg_lo_{arr} = 2147483647; _rg_hi_{arr} = -1;")
            self.indent -= 1
            self._put("}")
        else:
            self._put(f"ergo_vk_upload(d_{arr}, {arr}, {size_expr} * {sz});")

    def _mod_guard_of(self, item, prev_item) -> tuple[str, int] | None:
        """If item is IRIf whose condition is (MOD(G, k) == 0) computed
        in the immediately preceding IRBlock, return (G, k). Else None."""
        if not isinstance(item, IRIf) or not isinstance(prev_item, IRBlock):
            return None
        cond = item.condition
        if not isinstance(cond, IRRef):
            return None
        mod_result = None
        for inst in prev_item.insts:
            if (inst.result == cond.name and inst.op == Op.EQ
                    and len(inst.args) == 2):
                a0, a1 = inst.args
                if isinstance(a1, IRConst) and a1.value == 0 \
                        and isinstance(a0, IRRef):
                    mod_result = a0.name
                elif isinstance(a0, IRConst) and a0.value == 0 \
                        and isinstance(a1, IRRef):
                    mod_result = a1.name
        if not mod_result:
            return None
        for inst in prev_item.insts:
            if inst.result == mod_result and inst.op == Op.MOD \
                    and len(inst.args) == 2:
                a0, a1 = inst.args
                if isinstance(a0, IRRef) and isinstance(a1, IRConst) \
                        and isinstance(a1.value, int) and a1.value > 1:
                    return (a0.name, a1.value)
        return None

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
        # Instance-level set (shared across nested bodies — a CPU write
        # in an outer body must upload before kernels in inner loops).
        cpu_dirty_arrays = self._cpu_dirty
        gpu_array_set = set(self._gpu_arrays()) if self.gpu_plan else set()

        for i, item in enumerate(items):
            # Coalesced reductions: the first non-dispatch item may read
            # accumulator results — drain the frame once and combine the
            # pending group before any CPU code runs.
            _next_is_gpu = (isinstance(item, IRLoop)
                            and item.line in self._kernel_by_line
                            and self._is_gpu_kernel(
                                self._kernel_by_line[item.line]))
            if self._pending_reductions:
                if not _next_is_gpu:
                    self._flush_pending_reductions()
                else:
                    # A GPU kernel can ALSO consume a pending reduction
                    # accumulator — through its push constants, packed
                    # at record time (tower deflation: the GS overlap OV
                    # feeds the W-update kernel's PC). The "non-dispatch"
                    # test above misses that consumer: the dispatch then
                    # records a one-iteration-stale (or zero) value and
                    # the readback lands too late. Flush first when the
                    # next kernel's PC scalars name a pending accumulator.
                    _kn = self._kernel_by_line[item.line]
                    _acc = set()
                    for _pk in self._pending_reductions:
                        if _pk.reduction_var:
                            _acc.add(_pk.reduction_var)
                        _acc.update(_pk.reduction_vars)
                    _uses = set(_kn.scalars_read)
                    _bnd = getattr(_kn, "loop_bound", None)
                    if isinstance(_bnd, IRRef):
                        _uses.add(_bnd.name)
                    if _acc & _uses:
                        self._flush_pending_reductions()

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
                        pre_reads: set[str] = set()
                        for future in items[i:]:
                            if isinstance(future, IRLoop):
                                if self._kernel_by_line.get(future.line):
                                    more_dispatches = True
                                    break
                            self._collect_cpu_array_reads([future], pre_reads)
                            self._collect_cpu_array_writes([future], pre_reads)
                        # Deferral is only valid when no intervening CPU
                        # item reads (or overwrites) a just-dispatched
                        # array before the next dispatch — otherwise that
                        # CPU code would see a stale host copy (e.g. a
                        # CPU-side reduction between two GPU kernels).
                        if more_dispatches and \
                                (pre_reads & last_dispatch_arrays):
                            more_dispatches = False
                    if more_dispatches:
                        # Keep accumulating dispatch arrays; don't download yet
                        pass
                    else:
                        # Scan remaining items to find which arrays CPU reads
                        # (kernel-aware: reads/writes inside extracted
                        # kernels are device-side, not CPU access)
                        remaining = items[i:]
                        cpu_reads: set[str] = set()
                        # Guard-aware elision (Inc-4): an array whose
                        # remaining CPU reads ALL sit under one
                        # MOD(G,k)==0 guard (e.g. an every-250-steps
                        # residual probe) is downloaded inside that
                        # guard, not every frame. Mixed/unguarded reads
                        # (arr_guard[a] is None) download unconditionally.
                        # Writes alone do NOT force a download for
                        # rg-tracked arrays — the ranged upload covers
                        # the CPU->GPU direction without refreshing the
                        # host copy, and host staleness only matters for
                        # reads. Untracked arrays keep the old
                        # write-triggered download (their whole-array
                        # upload would clobber GPU-fresh data with a
                        # partially-stale host copy otherwise).
                        arr_guard: dict = {}
                        prev_ri = None
                        for ri in remaining:
                            if isinstance(ri, IRLoop):
                                k = self._kernel_by_line.get(ri.line)
                                if k:
                                    prev_ri = ri
                                    continue  # GPU kernel — skip
                            rd: set[str] = set()
                            wr: set[str] = set()
                            self._collect_cpu_array_reads([ri], rd)
                            self._collect_cpu_array_writes([ri], wr)
                            g = self._mod_guard_of(ri, prev_ri)
                            for a in rd:
                                if a in arr_guard:
                                    if arr_guard[a] != g:
                                        arr_guard[a] = None
                                else:
                                    arr_guard[a] = g
                            cpu_reads |= rd
                            for a in wr - rd:
                                if not self._rg_tracked(a):
                                    cpu_reads.add(a)
                                    arr_guard[a] = None
                            prev_ri = ri
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

                            def _dl(arr):
                                shape = self._array_shapes.get(arr)
                                if shape:
                                    self._body_downloaded.add(arr)
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

                            dl_guards: dict = {}
                            for arr in sorted(needed):
                                g = arr_guard.get(arr)
                                if g is None:
                                    _dl(arr)
                                else:
                                    dl_guards.setdefault(g, []).append(arr)
                            for (gv, gk) in sorted(dl_guards):
                                self._put(f"if ({gv} % {gk} == 0) {{")
                                self.indent += 1
                                for arr in sorted(dl_guards[(gv, gk)]):
                                    _dl(arr)
                                self.indent -= 1
                                self._put("}")
                            if verify_guard:
                                self.indent -= 1
                                self._put("}")
                        last_dispatch_arrays = None
                        # Re-open the frame for any subsequent GPU work in
                        # this iteration (e.g. a nested dispatch loop's next
                        # iteration). frame_begin is designed to be called
                        # after frame_wait (see vk_host.c:1354). Without
                        # this, dispatches after an early drain record into
                        # a command buffer that is no longer recording.
                        if self._batched_frame and self._frame_ended_early:
                            self._put("ergo_vk_frame_begin();")
                            self._frame_ended_early = False
                            self._frame_gpu_dirty.clear()

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
                # Track CPU-dirty arrays from IF body writes (skipping
                # sub-loops extracted as GPU kernels — device writes).
                if gpu_array_set:
                    if_writes: set[str] = set()
                    self._collect_cpu_array_writes([item], if_writes)
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
                            # Ordering: a synchronous transfer executes
                            # BEFORE this frame's recorded-but-unsubmitted
                            # dispatches — wrong if one of those kernels
                            # WROTE an array being uploaded (the recorded
                            # write would clobber the upload). Drain only
                            # on actual overlap (e.g. a CPU write between
                            # two kernels of the same array).
                            if (self._batched_frame
                                    and not self._frame_ended_early
                                    and (needed & self._frame_gpu_dirty)):
                                self._put("/* Drain before mid-frame upload */")
                                self._put("ergo_vk_frame_end();")
                                self._put("ergo_vk_frame_wait();")
                                self._put("ergo_vk_frame_begin();")
                                self._frame_gpu_dirty.clear()
                            self._put("/* Upload CPU-modified arrays to GPU */")
                            for arr in sorted(needed):
                                shape = self._array_shapes.get(arr)
                                if shape:
                                    sz = self._gpu_sizeof(arr)
                                    self._put_ranged_upload(arr, shape, sz)
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
                    # CPU loop — track which GPU arrays it may modify.
                    # Sub-loops extracted as GPU kernels write on the
                    # device, not the CPU — excluding them avoids stale
                    # re-uploads of GPU-current data.
                    cpu_writes: set[str] = set()
                    self._collect_cpu_array_writes([item], cpu_writes)
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
                        # GPU kernels inside this loop rewrote these
                        # arrays, so the device copy is now newer: any
                        # CPU-dirty flag set BEFORE the loop is stale and
                        # must be cleared (otherwise a later dispatch
                        # uploads stale host data over the kernel results).
                        # Arrays the CPU also wrote inside this same loop
                        # stay dirty (conservative, order-blind).
                        fresh = inner_gpu_written - cpu_writes
                        cpu_dirty_arrays -= fresh
                        self._gpu_current |= fresh
                        # Reset runtime dirty intervals too — otherwise a
                        # later ranged upload would write the stale host
                        # range over the kernel results.
                        for arr in sorted(fresh):
                            if self._rg_tracked(arr):
                                self._put(f"_rg_lo_{arr} = 2147483647; "
                                          f"_rg_hi_{arr} = -1;")
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

        # Flush any coalesced reduction group still pending at the end of
        # the body (e.g. a reduction as the last item of a frame loop).
        if self._pending_reductions:
            self._flush_pending_reductions()

        # If the body ends after a dispatch, download for any
        # subsequent CPU code (e.g. PRINT after last loop).
        # Suppressed in frame loops where render reads GPU memory directly.
        # Also skipped inside a batched frame: downloads there happen only
        # at drain points driven by actual CPU reads (the mid-body
        # intersection check) — otherwise every nested dispatch loop
        # (e.g. a ping-pong matvec loop) would drain the frame and
        # download full arrays once per iteration.
        if (last_dispatch_arrays is not None and not suppress_final_download
                and not self._batched_frame):
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
            # Re-open the frame for any subsequent GPU work in this
            # iteration (nested dispatch loops). See the note at the
            # mid-body download site above.
            if self._batched_frame and self._frame_ended_early:
                self._put("ergo_vk_frame_begin();")
                self._frame_ended_early = False
                self._frame_gpu_dirty.clear()

        return cpu_dirty_arrays

    def _emit_block(self, block: IRBlock):
        for inst in block.insts:
            self._emit_line(inst.line)
            self._emit_inst(inst)

    def _gpu_kernels_in_body(self, items: list) -> list:
        """Collect all GPU kernels that appear inside an IR body recursively.

        A loop that is not itself extracted as a kernel may still contain
        inner loops that were extracted, so we recurse into its body.
        """
        kernels = []
        for item in items:
            if isinstance(item, IRLoop):
                kernel = self._kernel_by_line.get(item.line)
                if kernel and self._is_gpu_kernel(kernel):
                    kernels.append(kernel)
                else:
                    kernels.extend(self._gpu_kernels_in_body(item.body))
            elif isinstance(item, IRIf):
                kernels.extend(self._gpu_kernels_in_body(item.then_body))
                if item.else_body:
                    kernels.extend(self._gpu_kernels_in_body(item.else_body))
            elif isinstance(item, IRSelect):
                for case in item.cases:
                    kernels.extend(self._gpu_kernels_in_body(case))
            elif isinstance(item, IRWhileLoop):
                kernels.extend(self._gpu_kernels_in_body(item.body))
        return kernels

    def _emit_if(self, node: IRIf):
        self._emit_line(node.line)
        # If this branch contains GPU kernels, any CPU-dirty arrays they need
        # must be uploaded BEFORE the conditional. Otherwise the upload placed
        # inside the branch is skipped when the condition is false, and the
        # next GPU kernel outside the branch reads stale device data.
        gpu_array_set = set(self._gpu_arrays()) if self.gpu_plan else set()
        if gpu_array_set:
            kernels = self._gpu_kernels_in_body([node])
            if kernels and self._cpu_dirty:
                needed = set()
                for k in kernels:
                    needed |= (k.arrays_read | k.arrays_written) & self._cpu_dirty
                if needed:
                    if (self._batched_frame
                            and not self._frame_ended_early
                            and (needed & self._frame_gpu_dirty)):
                        self._put("/* Drain before mid-frame upload */")
                        self._put("ergo_vk_frame_end();")
                        self._put("ergo_vk_frame_wait();")
                        self._put("ergo_vk_frame_begin();")
                        self._frame_gpu_dirty.clear()
                    self._put("/* Upload CPU-modified arrays to GPU before conditional */")
                    for arr in sorted(needed):
                        shape = self._array_shapes.get(arr)
                        if shape:
                            self._put_ranged_upload(arr, shape, self._gpu_sizeof(arr))
                    self._cpu_dirty -= needed
                    self._gpu_current |= needed
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

    @staticmethod
    def _is_simple_bound(s: str) -> bool:
        """True if s is a plain literal or name (safe to evaluate inline)."""
        s = s.strip()
        if s.lstrip("-").isdigit():
            return True
        return s.isidentifier()

    def _emit_do_header(self, var: str, start: str, end: str, step: str):
        """Emit a Fortran-semantics DO loop header (and open its scope).

        Bounds and step are evaluated ONCE into per-loop temporaries
        (Fortran evaluates loop bounds at entry), the comparator follows
        the step sign (so negative-step loops actually run), and the loop
        variable is assigned — not redeclared — so it retains its final
        value after the loop instead of shadowing the outer local.
        """
        self._loop_tmp_counter += 1
        n = self._loop_tmp_counter
        decls = [f"int _ergo_end{n} = ({end})",
                 f"int _ergo_step{n} = ({step})"]
        # Hoist a complex start expression too: it must also be
        # evaluated exactly once at loop entry.
        if not self._is_simple_bound(start):
            decls.append(f"int _ergo_start{n} = ({start})")
            start = f"_ergo_start{n}"
        if var not in self._var_types:
            # Undeclared loop variable: declare it inside the hoist
            # block so the loop still compiles (scoped as before).
            decls.append(f"int {var}")
        self._put("{ " + "; ".join(decls) + ";")
        self.indent += 1
        self._put(f"for ({var} = ({start}); "
                  f"_ergo_step{n} > 0 ? {var} <= _ergo_end{n} "
                  f": {var} >= _ergo_end{n}; "
                  f"{var} += _ergo_step{n}) {{")
        self.indent += 1

    def _emit_do_footer(self):
        """Close the for-loop and the hoist block opened by _emit_do_header."""
        self.indent -= 1
        self._put("}")
        self.indent -= 1
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
                # Kernel references arrays without GPU buffers — run on
                # CPU. Its GPU-RESIDENT reads must be downloaded first:
                # the host copies are stale after GPU dispatches, and the
                # generic download paths skip kernel-planned loops (they
                # assume the loop runs on device). Without this the
                # fallback silently reads stale host memory (tower
                # variant: last state's store ST3:=V and its SECT
                # overlaps read zeros). Only reads need downloads —
                # arrays it writes are covered by the dirty-interval
                # upload machinery; mixed host/device kernels still
                # keep every access coherent.
                # Kernel references arrays without GPU buffers — run on
                # CPU. Its GPU-RESIDENT reads must be downloaded first
                # — but ONLY those whose device copy is actually fresh:
                # an array the CPU wrote since the last upload has its
                # FRESH copy on the host, and downloading would clobber
                # it with stale device memory (the trna_gpu_0 NaN: the
                # coil init ran on the CPU, then this download restored
                # the zero-initialized device positions over them).
                # Uploads of host-dirty arrays are handled by the
                # dirty-interval machinery before the next dispatch.
                fb_dl = sorted(kernel.arrays_read
                               & set(self._gpu_arrays())
                               & (self._gpu_current - self._cpu_dirty))
                if fb_dl:
                    if self._batched_frame and not self._frame_ended_early:
                        self._put("ergo_vk_frame_end();")
                        self._put("ergo_vk_frame_wait();")
                        self._frame_ended_early = True
                    self._put("/* Download GPU arrays for host-fallback "
                              "kernel (host copies stale) */")
                    pp = getattr(self, '_pp_arrays', set())
                    for arr in fb_dl:
                        shape = self._array_shapes.get(arr)
                        if not shape:
                            continue
                        self._body_downloaded.add(arr)
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
                    if self._batched_frame and self._frame_ended_early:
                        self._put("ergo_vk_frame_begin();")
                        self._frame_ended_early = False
                        self._frame_gpu_dirty.clear()
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
                self._emit_do_header(node.var, start, end, step)
                self._emit_body(suffix_items)
                self._emit_do_footer()
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
            # Upload CPU-modified arrays before the frame loop starts.
            # ONLY CPU-dirty ones: arrays written by pre-loop GPU kernels
            # are already current on the device — uploading their stale
            # host copies would clobber the kernel results (e.g. an init
            # kernel's output re-zeroed by its BSS host copy).
            gpu_arrays = self._gpu_arrays()
            to_upload = sorted(a for a in gpu_arrays
                               if a in self._cpu_dirty)
            if to_upload:
                self._put("/* Sync CPU state to GPU before frame loop */")
                for arr in to_upload:
                    shape = self._array_shapes.get(arr)
                    if shape:
                        sz = self._gpu_sizeof(arr)
                        self._put_ranged_upload(arr, shape, sz)
                self._cpu_dirty -= set(to_upload)
                self._gpu_current |= set(to_upload)
            # Use runtime _max_frames if DEFAULT_FRAMES is the bound
            _loop_end = "_max_frames" if end == "DEFAULT_FRAMES" and "DEFAULT_FRAMES" in self._var_types else end
            self._emit_do_header(node.var, start, _loop_end, step)
            if use_batched:
                self._put("ergo_vk_frame_begin();")
                self._frame_gpu_dirty.clear()
                # Ping-pong: swap read/write offsets — but ONLY in loops
                # that actually dispatch a ping-pong kernel. A swap in an
                # unrelated batched loop (e.g. a one-iteration init loop
                # over the same arrays) would desync the halves.
                if getattr(self, '_pp_arrays', set()):
                    _loop_kids: set[int] = set()
                    self._collect_kernel_ids(node.body, _loop_kids)
                    if any((self._kernel_by_id[i].arrays_read
                            & self._kernel_by_id[i].arrays_written
                            & self._pp_arrays)
                           for i in _loop_kids if i in self._kernel_by_id):
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
                # Recurse into nested IF/loop bodies — kernels are not
                # necessarily top-level items of the frame body (a flat
                # scan here silently dropped the upload of CPU-deposited
                # arrays in the DBM solver, whose kernels sit inside
                # IF(DONE==0)/IF(sweep parity)).
                all_kernel_arrays: set[str] = set()
                _kk_ids: set[int] = set()
                self._collect_kernel_ids(node.body, _kk_ids)
                for _kk in _kk_ids:
                    if _kk in self._kernel_by_id:
                        all_kernel_arrays |= (self._kernel_by_id[_kk].arrays_read
                                              | self._kernel_by_id[_kk].arrays_written)
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

                # Runtime color channel: ERGO_COLOR=VEL_X etc.
                # Only GPU-resident arrays have device buffers — filter
                # candidates accordingly (PUMP_RESID etc. are CPU-only).
                gpu_set = set(self._gpu_arrays())
                real_arrays = [a for a in self._array_shapes
                               if a in gpu_set
                               and self._var_types.get(a) == IRType.REAL
                               and self._array_shapes[a] == self._array_shapes.get("POS_X")]
                if real_arrays:
                    self._put("/* Runtime color channel selection */")
                    self._put("const char *_color_env = getenv(\"ERGO_COLOR\");")
                    self._put(f"ErgoVkBuf _color_buf = d_{color_arr};")
                    for arr in real_arrays:
                        if arr != color_arr:
                            self._put(f"if (_color_env && strcmp(_color_env, \"{arr}\") == 0) "
                                      f"_color_buf = d_{arr};")

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
                self._put(f"if (getenv(\"ERGO_RENDER\") && "
                          f"strcmp(getenv(\"ERGO_RENDER\"), \"meshlet\") == 0)")
                self._put(f"  ergo_vk_render_meshlets("
                          f"d_{particle['pos_x']}, d_{particle['pos_y']}, "
                          f"d_{particle['pos_z']}, _color_buf, {count}, "
                          f"d_GRID_GRAD_X, d_GRID_GRAD_Y, "
                          f"d_GRID_GRAD_Z, d_GRID_MET_GATE, "
                          f"GRID_SIZE, _vmin, _vmax, {ws});")
                self._put(f"else if (getenv(\"ERGO_RENDER\") && "
                          f"strcmp(getenv(\"ERGO_RENDER\"), \"grid\") == 0)")
                self._put(f"  ergo_vk_render_grid_gaussians("
                          f"d_GRID_GRAD_X, d_GRID_GRAD_Y, "
                          f"d_GRID_GRAD_Z, d_GRID_MET_GATE, "
                          f"GRID_SIZE, _vmin, _vmax, {ws});")
                self._put(f"else if (getenv(\"ERGO_RENDER\") && "
                          f"strcmp(getenv(\"ERGO_RENDER\"), \"gauss\") == 0)")
                self._put(f"  ergo_vk_render_gaussians("
                          f"d_{particle['pos_x']}, d_{particle['pos_y']}, "
                          f"d_{particle['pos_z']}, _color_buf, "
                          f"{count}, 0.003f, _vmin, _vmax, {ws});")
                self._put(f"else")
                self._put(f"  ergo_vk_render_points("
                          f"d_{particle['pos_x']}, d_{particle['pos_y']}, "
                          f"d_{particle['pos_z']}, _color_buf, "
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
                # Uploads feeding GPU kernels must happen EVERY frame —
                # gating them to oracle frames starves the next dispatch of
                # current data (e.g. a CPU-scattered grid read by the next
                # kernel). Only arrays no kernel reads may share the
                # oracle's gated schedule.
                kernel_reads: set[str] = set()
                # Same nested-body recursion as the upload_set scan above.
                _kr_ids: set[int] = set()
                self._collect_kernel_ids(node.body, _kr_ids)
                for _kr in _kr_ids:
                    if _kr in self._kernel_by_id:
                        kernel_reads |= self._kernel_by_id[_kr].arrays_read
                per_frame = upload_set & kernel_reads
                oracle_only = upload_set - kernel_reads
                # Ensure GPU is idle before transfers (idempotent)
                if use_batched:
                    self._put("ergo_vk_frame_wait();")
                if per_frame:
                    self._put("/* Upload kernel-read arrays (every frame) */")
                    for arr in sorted(per_frame):
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
                                self._put_ranged_upload(arr, shape, sz)
                if oracle_only:
                    verify_meta = self._find_verify_meta(node.body)
                    upload_guard = (verify_meta and
                                    verify_meta.get("every", 1) > 1 and
                                    use_batched)
                    if upload_guard:
                        every = verify_meta["every"]
                        self._put(f"if (!_oracle_init || "
                                  f"_oracle_frame % {every} == 0) {{")
                        self.indent += 1
                    self._put("/* Upload CPU-modified arrays (oracle schedule) */")
                    for arr in sorted(oracle_only):
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
                                self._put_ranged_upload(arr, shape, sz)
                    if upload_guard:
                        self.indent -= 1
                        self._put("}")
            if self.render:
                self._put(f"if (ergo_vk_should_close()) break;")
            self._emit_do_footer()
            if use_batched:
                self._put("/* Flush last frame */")
                self._put("ergo_vk_frame_begin(); ergo_vk_frame_end();")
            self._in_frame_loop = False
            self._batched_frame = False
            self._frame_ended_early = False
        else:
            self._emit_do_header(node.var, start, end, step)
            # Per-loop scoping for the download tracker: nested loops
            # save/merge so an outer loop's end-refresh sees every
            # download in its body.
            saved_downloaded = self._body_downloaded
            self._body_downloaded = set()
            dirty = self._emit_body(node.body)
            this_loop_downloads = self._body_downloaded
            self._body_downloaded = saved_downloaded | this_loop_downloads
            # CPU loop inside a batched frame: the NEXT iteration may
            # read GPU-written arrays on the host (e.g. a CPU stencil
            # interleaved with point-source kernels). The mid-body
            # download logic can't see next-iteration reads, so refresh
            # those arrays at the end of each iteration — but ONLY arrays
            # the body actually reads on the CPU (kernel-aware: a loop of
            # pure GPU work, like a ping-pong matvec nest, pays nothing).
            if self._batched_frame and self.gpu_plan:
                inner_written: set[str] = set()

                def _kernel_writes(items):
                    for bi in items:
                        if isinstance(bi, IRLoop):
                            ik = self._kernel_by_line.get(bi.line)
                            if ik:
                                inner_written.update(ik.arrays_written)
                            else:
                                _kernel_writes(bi.body)
                        elif isinstance(bi, IRIf):
                            _kernel_writes(bi.then_body)
                            if bi.else_body:
                                _kernel_writes(bi.else_body)
                _kernel_writes(node.body)
                cpu_rd: set[str] = set()
                self._collect_cpu_array_reads(node.body, cpu_rd)
                # Skip arrays the mid-body logic already downloaded this
                # iteration — re-downloading would be pure waste.
                needed = (inner_written & cpu_rd) - this_loop_downloads
                if needed:
                    if not self._frame_ended_early:
                        self._put("ergo_vk_frame_end();")
                        self._put("ergo_vk_frame_wait();")
                        self._frame_ended_early = True
                    self._put("/* Refresh host copies for next iteration */")
                    for arr in sorted(needed):
                        shape = self._array_shapes.get(arr)
                        if shape:
                            size_expr = " * ".join(
                                self._dim_expr(d) for d in shape)
                            sz = self._gpu_sizeof(arr)
                            self._put(f"ergo_vk_download(d_{arr}, {arr}, "
                                      f"{size_expr} * {sz});")
                    self._put("ergo_vk_frame_begin();")
                    self._frame_ended_early = False
                    self._frame_gpu_dirty.clear()
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
            # Nested loops inside a frame loop must NOT close the frame:
            # the outer frame loop owns the lifecycle (begin per outer
            # iteration, end at the finalizer), and early drains re-open
            # the frame immediately (see the download sites). A frame_end
            # here lands inside the nested loop's braces — it would close
            # the frame per inner iteration and leave the next iteration's
            # dispatches recording into a dead command buffer.
            self._emit_do_footer()

    def _emit_minmax_scan(self, arr: str, count_expr: str):
        """Emit fixed value range for render color mapping.

        The color array (typically OMEGA_NAT) has known bounds from the
        simulation constants. A CPU-side scan over millions of elements
        would stall the pipeline every frame. Use fixed range instead.
        """
        # Color range: ERGO_VMIN/ERGO_VMAX env vars override defaults.
        # Default 0.0-3.0 covers velocity range with visible palette.
        self._put(f"float _vmin = getenv(\"ERGO_VMIN\") ? "
                  f"atof(getenv(\"ERGO_VMIN\")) : 0.0f;")
        self._put(f"float _vmax = getenv(\"ERGO_VMAX\") ? "
                  f"atof(getenv(\"ERGO_VMAX\")) : 3.0f;")

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

        # Emit as for(;;) with the condition checked at the TOP of each
        # iteration: CYCLE (continue) then naturally re-evaluates the
        # condition. (A trailing re-evaluation is skipped by continue,
        # which previously caused infinite loops.)
        cond = self._operand(node.condition)
        self._put("for (;;) {")
        self.indent += 1

        self._emit_block(node.cond_block)
        self._put(f"if (!({cond})) break;")

        if is_frame_loop and self._batched_frame:
            self._put("ergo_vk_frame_begin();")
            self._frame_gpu_dirty.clear()

        self._emit_body(node.body)

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

    def _subscripts(self, array_name: str, index_args: list) -> str:
        """C subscript string for an array access (column-major LOCKED:
        the C array is declared with reversed dims).

        The loop-linearization pass (ir_gpu) can rewrite a multi-dim
        access to a single 0-based column-major linear index. On the host
        the C array is still multi-dimensional, so a single index arg on
        a multi-rank array must be decomposed back into C subscripts —
        A[lin] on double A[NY][NX] is otherwise a row-pointer type error.
        """
        shape = self._array_shapes.get(array_name)
        if shape and len(shape) > 1 and len(index_args) == 1:
            linear = self._operand(index_args[0])
            subs = []
            rem = linear
            for d in shape[:-1]:
                dim = self._dim_expr(d)
                subs.append(f"({rem}) % ({dim})")
                rem = f"({rem}) / ({dim})"
            subs.append(rem)
            return "][".join(reversed(subs))
        return "][".join(self._operand(a) for a in reversed(index_args))

    # ── instruction emission ─────────────────────────────────

    def _emit_inst(self, inst: IRInst):
        op = inst.op
        args = inst.args
        result = inst.result
        # A6: stores into a by-reference scalar dummy go through the pointer
        if result and result in self._ref_scalars:
            result = f"(*{result})"

        # Simple copy (assignment)
        if op == Op.COPY:
            if inst.meta.get("kind") == "cycle":
                self._put("continue;")
            if inst.meta.get("kind") == "exit":
                self._put("break;")
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
            self._put(f"{result} = {_real_math('pow')}("
                      f"{self._operand(args[0])}, {self._operand(args[1])});")
            return

        if op == Op.MOD:
            a, b = self._operand(args[0]), self._operand(args[1])
            if self._is_int_operand(args[0]) and self._is_int_operand(args[1]):
                self._put(f"{result} = ({a} % {b});")
            else:
                self._put(f"{result} = {_real_math('fmod')}({a}, {b});")
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
        if op == Op.TO_INT64:
            self._put(f"{result} = (long long)({self._operand(args[0])});")
            return
        if op == Op.TO_CHAR:
            self._put(f"{result} = (char)({self._operand(args[0])});")
            return

        # Math intrinsics
        if op in C_MATH:
            c_func = _real_math(C_MATH[op])
            a = ", ".join(self._operand(a) for a in args)
            self._put(f"{result} = {c_func}({a});")
            return

        # DOT_PRODUCT / NORM2 — whole-array reductions. Array names ride in
        # meta; the element count comes from the compile-time shape. Args
        # are 1D so layout is flat (column-major note is moot).
        if op in (Op.DOT_PRODUCT, Op.NORM2):
            arrays = inst.meta.get("arrays", [])
            n = self._dot_size(arrays[0], inst.line)
            if op == Op.DOT_PRODUCT:
                self._put(f"{result} = _ergo_dot({arrays[0]}, {arrays[1]}, {n});")
            else:
                self._put(f"{result} = {_real_math('sqrt')}("
                          f"_ergo_dot({arrays[0]}, {arrays[0]}, {n}));")
            return

        # ABS — type aware
        if op == Op.ABS:
            a = self._operand(args[0])
            if self._is_int_operand(args[0]):
                self._put(f"{result} = abs({a});")
            else:
                self._put(f"{result} = {_real_math('fabs')}({a});")
            return

        # SIGN — type aware: |a| with the sign of b
        if op == Op.SIGN:
            a, b = self._operand(args[0]), self._operand(args[1])
            if self._is_int_operand(args[0]):
                self._put(f"{result} = (abs({a}) * (({b}) >= 0 ? 1 : -1));")
            else:
                self._put(f"{result} = {_real_math('copysign')}({a}, {b});")
            return

        # PRNG intrinsics — splitmix64 at the runtime's native width
        # (see _emit_hash_helper for constants and statistics notes).
        if op == Op.HASH:
            a = self._operand(args[0])
            self._put(f"{result} = _ergo_hash32((unsigned long long)({a}));")
            return
        if op == Op.RAND:
            a = self._operand(args[0])
            self._put(f"{result} = _ergo_rand01((unsigned long long)({a}));")
            return

        # MAX / MIN
        if op == Op.MAX:
            a, b = self._operand(args[0]), self._operand(args[1])
            if self._is_int_operand(args[0]):
                self._put(f"{result} = (({a}) > ({b}) ? ({a}) : ({b}));")
            else:
                self._put(f"{result} = {_real_math('fmax')}({a}, {b});")
            return
        if op == Op.MIN:
            a, b = self._operand(args[0]), self._operand(args[1])
            if self._is_int_operand(args[0]):
                self._put(f"{result} = (({a}) < ({b}) ? ({a}) : ({b}));")
            else:
                self._put(f"{result} = {_real_math('fmin')}({a}, {b});")
            return

        # CLAMP — branchless
        if op == Op.CLAMP:
            x, lo, hi = self._operand(args[0]), self._operand(args[1]), self._operand(args[2])
            if self._is_int_operand(args[0]):
                self._put(f"{result} = (({x}) < ({lo}) ? ({lo}) : (({x}) > ({hi}) ? ({hi}) : ({x})));")
            else:
                fmin = _real_math('fmin')
                fmax = _real_math('fmax')
                self._put(f"{result} = {fmin}({fmax}({x}, {lo}), {hi});")
            return

        # Array LOAD
        if op == Op.LOAD:
            array_name = inst.meta.get("array", "?")
            # Column-major (LOCKED convention, first index fastest): the C
            # array is declared with reversed dims, so emit subscripts in
            # reverse — Ergo A(i,j,k) → C A[k-1][j-1][i-1].
            indices = self._subscripts(array_name, args)
            self._put(f"{result} = {array_name}[{indices}];")
            return

        # Array STORE
        if op == Op.STORE:
            array_name = inst.meta.get("array", "?")
            val = self._operand(args[0])
            # Column-major: reversed subscripts (see LOAD above).
            indices = self._subscripts(array_name, args[1:])
            self._put(f"{array_name}[{indices}] = {val};")
            # Dirty-range tracking: merge the written element into the
            # array's runtime interval. Only EXECUTED writes merge, so
            # guarded writes are exact, and any index expression works
            # (no affine analysis needed). 1-D arrays only.
            if (self.gpu_plan and len(args[1:]) == 1
                    and self._rg_tracked(array_name)):
                self._put(f"_rg_lo_{array_name} = ({indices} < _rg_lo_{array_name})"
                          f" ? {indices} : _rg_lo_{array_name};")
                self._put(f"_rg_hi_{array_name} = ({indices} > _rg_hi_{array_name})"
                          f" ? {indices} : _rg_hi_{array_name};")
            return

        # ALLOC — bump from file-scope arena (see _emit_arena_decl).
        # 64-byte aligned, bounds-checked, abort on exhaustion.
        if op == Op.ALLOC:
            ct = self._c_type(inst.type)
            # Cast each dim to size_t so the product can't overflow int
            # before promotion on large allocations.
            size = " * ".join(f"(size_t)({self._operand(a)})" for a in args)
            self._put("{")
            self.indent += 1
            self._put(f"size_t _sz = {size} * sizeof({ct});")
            if result in self._allocatable:
                self._put(f"_ergo_sz_{result} = _sz;")
            self._put("size_t _aligned = (_sz + 63) & ~(size_t)63;")
            self._put("if (_ergo_arena_offset + _aligned > "
                      "ERGO_ARENA_BYTES) {")
            self.indent += 1
            self._put('fprintf(stderr, "ergo: arena exhausted (need %zu, '
                      'have %zu)\\n",')
            self._put("        _aligned, ERGO_ARENA_BYTES - "
                      "_ergo_arena_offset);")
            self._put("abort();")
            self.indent -= 1
            self._put("}")
            self._put(f"{result} = ({ct} *)(_ergo_arena + "
                      f"_ergo_arena_offset);")
            self._put("_ergo_arena_offset += _aligned;")
            self.indent -= 1
            self._put("}")
            return

        # FREE — DEALLOCATE is a no-op: the arena is bump-only.
        # See Spec/Arena_Lowering_Brief.md "DEALLOCATE semantics".
        if op == Op.FREE:
            name = self._operand(args[0])
            self._put(f"/* DEALLOCATE({name}) — no-op (arena is bump-only) */")
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
                    # D19 (WAW hazard): if an earlier dispatch in this frame
                    # wrote this buffer, the TRANSFER-stage fill must be
                    # ordered after the COMPUTE writes — the pre-dispatch
                    # barrier only covers fill→compute, not compute→fill.
                    # Drain and re-open the frame before filling.
                    if array_name in self._frame_gpu_dirty:
                        self._put("ergo_vk_frame_end();")
                        self._put("ergo_vk_frame_wait();")
                        self._put("ergo_vk_frame_begin();")
                        self._frame_gpu_dirty.clear()
                        self._frame_ended_early = False
                    self._put(f"ergo_vk_frame_fill(d_{array_name}, "
                              f"{size_expr} * {sz});")
                    self._frame_gpu_dirty.add(array_name)
                    return
            # ALLOCATABLE arrays are pointers — sizeof would be the pointer
            # size. Use the byte-size companion recorded at ALLOCATE time.
            if array_name in self._allocatable:
                self._put(f"memset({array_name}, 0, _ergo_sz_{array_name});")
            else:
                self._put(f"memset({array_name}, 0, sizeof({array_name}));")
            # Dirty-range tracking: ZERO writes the whole array.
            if self.gpu_plan and self._rg_tracked(array_name):
                _zs = " * ".join(self._dim_expr(d)
                                 for d in self._array_shapes[array_name])
                self._put(f"_rg_lo_{array_name} = 0; "
                          f"_rg_hi_{array_name} = ({_zs}) - 1;")
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
            # Streaming intrinsics (Inc-2B N=19): explicit host↔device
            # slice transfers. Both are frame sync points: VK_STAGE
            # drains when the recording frame has unsubmitted kernel
            # writes (a transfer would otherwise execute before them);
            # VK_FETCH always drains (the data must exist on device).
            if func in ("VK_STAGE", "VK_FETCH"):
                from .errors import MCLError as _MCLErr
                arr_a = inst.meta["arr_a"]
                arr_b = inst.meta["arr_b"]
                a0 = self._operand(args[0])
                a1 = self._operand(args[1])
                a2 = self._operand(args[2])
                if not (self.gpu_plan and self.gpu_plan.kernels):
                    # CPU build: both arrays are plain host arrays — the
                    # "transfer" is a memmove (same dst-first signature).
                    self._put(f"memmove({arr_a} + (({a1}) - 1), "
                              f"{arr_b} + (({a0}) - 1), "
                              f"(size_t)({a2}) * sizeof({arr_a}[0]));")
                    return
                gpu_set = set(self._gpu_arrays())
                if func == "VK_STAGE":
                    gpu_arr, host_arr = arr_a, arr_b
                else:
                    gpu_arr, host_arr = arr_b, arr_a
                if gpu_arr not in gpu_set:
                    raise _MCLErr(
                        f"{func}: '{gpu_arr}' is not GPU-resident "
                        f"(no kernel touches it)")
                if host_arr in gpu_set:
                    raise _MCLErr(
                        f"{func}: '{host_arr}' is GPU-resident — device "
                        f"buffers are not staged through themselves")
                sz = self._gpu_sizeof(gpu_arr)
                a0 = self._operand(args[0])
                a1 = self._operand(args[1])
                a2 = self._operand(args[2])
                # Drain rules (see comment above)
                if func == "VK_STAGE":
                    if (self._batched_frame and not self._frame_ended_early
                            and self._frame_gpu_dirty):
                        self._put("/* VK_STAGE: drain before transfer */")
                        self._put("ergo_vk_frame_end();")
                        self._put("ergo_vk_frame_wait();")
                        self._put("ergo_vk_frame_begin();")
                        self._frame_gpu_dirty.clear()
                    self._put(f"ergo_vk_upload_at(d_{gpu_arr}, {host_arr} "
                              f"+ (({a0}) - 1), "
                              f"(size_t)(({a1}) - 1) * {sz}, "
                              f"(size_t)({a2}) * {sz});")
                else:
                    if self._batched_frame and not self._frame_ended_early:
                        self._put("/* VK_FETCH: drain before download */")
                        self._put("ergo_vk_frame_end();")
                        self._put("ergo_vk_frame_wait();")
                        self._frame_ended_early = True
                    self._put(f"ergo_vk_download_at(d_{gpu_arr}, {host_arr} "
                              f"+ (({a1}) - 1), "
                              f"(size_t)(({a0}) - 1) * {sz}, "
                              f"(size_t)({a2}) * {sz});")
                    if self._batched_frame and self._frame_ended_early:
                        self._put("ergo_vk_frame_begin();")
                        self._frame_ended_early = False
                        self._frame_gpu_dirty.clear()
                return
            # .esf stream intrinsics (Spec/Ergo_Stream_Format.md)
            if func == "ESF_OPEN":
                u = self._operand(args[0])
                nch = self._operand(args[1])
                path = _c_str_escape(inst.meta["path"])
                self._put(f'esf_open({u}, "{path}", {nch});')
                return
            if func == "ESF_WRITE":
                u = self._operand(args[0])
                ch = self._operand(args[1])
                n = self._operand(args[2])
                arr = inst.meta["array"]
                self._put(f"esf_write({u}, {ch}, {arr}, "
                          f"({n}) * (int)sizeof({arr}[0]));")
                return
            if func == "ESF_CLOSE":
                u = self._operand(args[0])
                self._put(f"esf_close({u});")
                return
            # A6: user subroutine with by-reference scalar dummies —
            # build the argument list signature-aware (addresses for
            # scalar positions; temps for read-only constant arguments).
            sub_fn = self._ir_subs.get(func)
            a = self._sub_call_args(func, sub_fn, args)
            # GPU sync: download arrays before CPU call, upload after.
            # Not gated on _in_frame_loop (D18): a non-inlined subroutine
            # outside the frame loop reads stale CPU copies otherwise.
            # Downloads are filtered to arrays that are actually
            # GPU-resident, so init-region calls (CPU data not yet
            # uploaded) are not clobbered with GPU garbage.
            has_gpu = self.gpu_plan and self.gpu_plan.kernels
            gpu_arrays = set(self._gpu_arrays()) if has_gpu else set()
            sub_access = self._sub_array_access.get(func)
            need_sync = has_gpu and sub_access
            dl_arrays = set()
            ul_arrays = set()
            if need_sync:
                reads, writes = sub_access
                pp = getattr(self, '_pp_arrays', set())
                # Download GPU arrays this sub reads
                dl_arrays = (reads | writes) & gpu_arrays & self._gpu_current
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
                            self._put_ranged_upload(arr, shape, sz)
                self._gpu_current |= ul_arrays
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
            if isinstance(unit, str):
                if unit == "*":
                    stream = "stdout"
                elif unit == "0":
                    stream = "stderr"
                else:
                    # Numeric file unit (Spec Part 10): runtime FILE*
                    # lookup — named error if the unit is not open.
                    stream = f"_ergo_unit({unit})"
            else:
                # File unit expression (Spec Part 10): runtime FILE*
                # lookup — named error if the unit is not open for
                # formatted output.
                stream = f"_ergo_unit({self._operand(unit)})"
            # Raw-record form: WRITE(unit) A(lo:hi), ... — binary
            # block, explicit length, native endianness (Part 10.4).
            if fmt is None:
                for name, lo, hi in inst.meta["sections"]:
                    shape = self._array_shapes.get(name)
                    if not shape or len(shape) != 1:
                        from .errors import MCLError as _MCLErr
                        raise _MCLErr(
                            f"WRITE raw record: '{name}' needs a "
                            f"compile-time-sized 1-D array")
                    slo = self._operand(lo)
                    shi = self._operand(hi)
                    self._put(
                        f"_ergo_raw_write({stream}, {name}, "
                        f"(long)({slo}), (long)({shi}), "
                        f"(long)(sizeof({name}) / sizeof({name}[0])), "
                        f"sizeof({name}[0]), \"{name}\");")
                return
            # The format text is embedded in a C string literal — escape
            # it the same way as string constants.
            fmt = _c_str_escape(fmt)
            if advance:
                fmt = fmt + "\\n"
            if args:
                a = ", ".join(self._operand(a) for a in args)
                self._put(f'fprintf({stream}, "{fmt}", {a});')
            else:
                self._put(f'fprintf({stream}, "{fmt}");')
            return

        # OPEN / CLOSE — file units (Spec Part 10)
        if op == Op.OPEN:
            u = self._operand(args[0])
            path = _c_str_escape(inst.meta["path"])
            mode = "w" if inst.meta["mode"] == "WRITE" else "a"
            self._put(f'_ergo_open({u}, "{path}", "{mode}");')
            return
        if op == Op.CLOSE:
            u = self._operand(args[0])
            self._put(f"_ergo_close({u});")
            return

        # ESF_NEXT — scheduled channel of the stream's next frame
        if op == Op.ESF_NEXT:
            a = self._operand(args[0])
            self._put(f"{result} = esf_next({a});")
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

        # STOP — terminate the whole program from any context.
        # (return 0 would only exit the current function.)
        if op == Op.STOP:
            if self.gpu_plan and self.gpu_plan.kernels:
                self._emit_final_hash_hook()
                self._put("ergo_vk_shutdown();")
            self._put("_ergo_io_shutdown();")
            self._put("exit(0);")
            return

        # HHB_FAIL — Hopf Handshake Bound check failure.
        # The diagnostic message is emitted by the preceding WRITE; this op
        # just performs the ordered shutdown and exits with code 1.
        if op == Op.HHB_FAIL:
            if self.gpu_plan and self.gpu_plan.kernels:
                self._emit_final_hash_hook()
                self._put("ergo_vk_shutdown();")
            self._put("_ergo_io_shutdown();")
            self._put("exit(1);")
            return

        # VERIFY — CPU oracle checkpoint
        if op == Op.VERIFY:
            self._emit_verify(inst)
            return

        # SORT_BY_GEN — compiler-generated sort dispatch
        if op == Op.SORT_BY_GEN:
            self._emit_sort_by_gen(inst)
            return

        # RING_*/WARP_* subgroup intrinsics only exist inside GPU kernels.
        # On the CPU path there is no meaningful lowering — fail loudly
        # instead of leaving an uninitialized temp for later reads.
        if op in (Op.RING_PREV, Op.RING_NEXT, Op.RING_SHIFT, Op.RING_BROADCAST,
                  Op.WARP_BALLOT, Op.WARP_BALLOT_COUNT, Op.WARP_BALLOT_PREFIX,
                  Op.WARP_BROADCAST_FIRST):
            raise MCLError(
                "RING/WARP subgroup intrinsics are only available in GPU "
                "kernels (--target), not on the CPU path")

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
        """Emit sort-by-GEN.

        Default: deterministic CPU counting sort (stable, by GEN class) —
        the GPU scatter assigns slots in atomic-arrival order, which is not
        reproducible. Under --gpu-fast-math: the GPU histogram/scan/scatter
        pipeline (fast, nondeterministic within-class order).
        """
        arrays = inst.meta["arrays"]
        use_gpu_sort = (getattr(self.backend, 'gpu_fast_math', False)
                        if self.backend else False)
        if use_gpu_sort:
            self._emit_sort_by_gen_gpu(inst)
            return
        self._emit_sort_by_gen_cpu(arrays)

    def _emit_sort_by_gen_cpu(self, arrays: list):
        """Deterministic counting sort on the CPU.

        Downloads GPU-resident arrays, stable-sorts by
        (FLAGS[i] >> GEN_SHIFT) & GEN_MASK (≤32 bins) with an explicit
        counting pass (bitwise reproducible), copies back, and re-uploads.
        """
        for name in ("NPART", "GEN_SHIFT", "GEN_MASK"):
            if name not in self._var_types:
                raise MCLError(
                    f"SORT_BY_GEN requires a '{name}' scalar in scope")

        # Drain the frame before host transfers (batched mode).
        drained = False
        if self._batched_frame and not self._frame_ended_early:
            self._put("ergo_vk_frame_end();")
            self._put("ergo_vk_frame_wait();")
            self._frame_ended_early = True
            drained = True

        self._put("/* SORT_BY_GEN — deterministic CPU counting sort */")
        self._put("{")
        self.indent += 1
        self._put("int _cnt[32] = {0};")
        self._put("int _pos[32];")

        # Download arrays that live on the GPU.
        has_gpu = self.gpu_plan and self.gpu_plan.kernels
        all_arrs = list(arrays)
        if "FLAGS" not in all_arrs:
            all_arrs.insert(0, "FLAGS")
        if has_gpu:
            for arr in all_arrs:
                if arr in self._gpu_current:
                    ct = self._c_type(self._var_types.get(arr, IRType.REAL))
                    self._put(f"ergo_vk_download(d_{arr}, {arr}, "
                              f"NPART * sizeof({ct}));")

        # Histogram pass.
        self._put("for (int _i = 0; _i < NPART; _i++)")
        self._put("  _cnt[(FLAGS[_i] >> GEN_SHIFT) & GEN_MASK]++;")

        # Scatter each array into scratch, then copy back and upload.
        for arr in arrays:
            ct = self._c_type(self._var_types.get(arr, IRType.REAL))
            self._put("{")
            self.indent += 1
            self._put(f"static char _st_raw[sizeof({arr})];")
            self._put("_pos[0] = 0;")
            self._put("for (int _b = 1; _b < 32; _b++) "
                      "_pos[_b] = _pos[_b-1] + _cnt[_b-1];")
            self._put("for (int _i = 0; _i < NPART; _i++) {")
            self.indent += 1
            self._put("int _k = (FLAGS[_i] >> GEN_SHIFT) & GEN_MASK;")
            self._put(f"(({ct} *)_st_raw)[_pos[_k]++] = {arr}[_i];")
            self.indent -= 1
            self._put("}")
            self._put(f"memcpy({arr}, _st_raw, sizeof({arr}));")
            if has_gpu:
                self._put(f"ergo_vk_upload(d_{arr}, {arr}, "
                          f"NPART * sizeof({ct}));")
            self._gpu_current.add(arr)
            self.indent -= 1
            self._put("}")

        self.indent -= 1
        self._put("}")

        # Re-open the frame for subsequent GPU work.
        if drained or (self._batched_frame and self._frame_ended_early):
            self._put("ergo_vk_frame_begin();")
            self._frame_ended_early = False
            self._frame_gpu_dirty.clear()

    def _emit_sort_by_gen_gpu(self, inst: IRInst):
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
        # Force render re-record — buffer handles changed
        self._put(f"ergo_vk_render_invalidate();")

        self.indent -= 1
        self._put(f"}}")

    def _emit_verify(self, inst: IRInst):
        """Emit CPU oracle verification checkpoint.

        Downloads a sparse sample from GPU, compares against CPU shadow
        state, and reports divergence. The shadow arrays are evolved
        independently by the CPU each frame using the same physics.
        """
        if self.no_verify:
            # --no-verify: omit the oracle entirely. Also the reason a
            # CPU copy of the physics subroutine (possibly containing
            # GPU-only RING ops) is not needed.
            self._put("/* VERIFY omitted by --no-verify */")
            return

        arrays = inst.meta["arrays"]
        n = inst.meta["oracle_size"]
        every = inst.meta["every"]
        tol = inst.meta["tolerance"]

        # ERGO_NO_VERIFY=1 disables the oracle at runtime (no recompile):
        # no shadow state, no downloads/uploads, no shadow physics.
        self._put(f"if (!getenv(\"ERGO_NO_VERIFY\")) {{")
        self.indent += 1
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
        # For ping-pong arrays, read from the current-state half (PP_WR
        # after the frame's dispatches — the swap happens at frame_begin)
        has_gpu = self.gpu_plan and self.gpu_plan.kernels
        if has_gpu:
            # Ensure GPU cmd buf is submitted and idle before transfer
            if self._batched_frame and not self._frame_ended_early:
                self._put("ergo_vk_frame_end();")
                self._put("ergo_vk_frame_wait();")
                # D21: re-open the frame for the rest of this iteration.
                # The end/wait above is inside the `every` gate, so on
                # non-oracle frames it never executes — but the codegen
                # flag must still reflect the frame as OPEN on every path,
                # or the finalizer skips the close and the fence for this
                # frame is never submitted (the next re-begin then waits
                # on it forever — the galaxy_full freeze).
                self._put("ergo_vk_frame_begin();")
                self._frame_gpu_dirty.clear()
                self._frame_ended_early = False
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

        self.indent -= 1
        self._put(f"}}  /* end oracle (ERGO_NO_VERIFY) */")

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
        # Upload only if GRID_DENSITY_GLOBAL is actually GPU-resident
        # (when the stencil runs on CPU, no device buffer exists).
        gd_global_on_gpu = "GRID_DENSITY_GLOBAL" in self._gpu_arrays()
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
        if has_gpu and gd_global_on_gpu:
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
        if has_gpu and gd_global_on_gpu:
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

    def _emit_final_hash_hook(self) -> None:
        """Emit ERGO_HASH_FINAL=1 state-hash diagnostic.

        Downloads particle position/velocity/omega arrays from GPU and hashes
        NPART elements with FNV-1a. Prints one greppable line to stdout:
        ERGO_FINAL_HASH=<16-hex-digits>. No-op when the env var is unset.
        """
        gpu = set(self._gpu_arrays())
        # Order matters — hashes mix in this fixed sequence for stability.
        hash_arrays = [a for a in
                       ("POS_X", "POS_Y", "POS_Z",
                        "VEL_X", "VEL_Y", "VEL_Z", "OMEGA_NAT")
                       if a in gpu]
        if not hash_arrays:
            return
        # The hook hashes NPART elements per array. A GPU program without
        # an NPART scalar has no countable particle state — skip the hook
        # entirely so the emitted C still compiles.
        if "NPART" not in self._var_types:
            return
        elem = IRType.REAL.c_type  # float in f32 mode, double in f64
        self._put("if (getenv(\"ERGO_HASH_FINAL\")) {")
        self.indent += 1
        self._put("ergo_vk_frame_wait();")
        for arr in hash_arrays:
            self._put(f"ergo_vk_download(d_{arr}, {arr}, "
                      f"NPART * sizeof({elem}));")
        self._put("unsigned long long _h = 14695981039346656037ULL;")
        for arr in hash_arrays:
            self._put(f"_h = _ergo_fnv1a_update(_h, {arr}, "
                      f"NPART * sizeof({elem}));")
        self._put("printf(\"ERGO_FINAL_HASH=%016llx\\n\", _h);")
        self.indent -= 1
        self._put("}")

    # ── arena lowering for ALLOCATABLE ────────────────────────
    # ALLOC bumps an offset into a file-scope BSS arena. FREE is a
    # no-op (the arena is bump-only; see Spec/Arena_Lowering_Brief.md).

    def _uses_allocate(self, mod: IRModule) -> bool:
        """Return True if any ALLOC or FREE instruction is reachable."""
        def walk_items(items) -> bool:
            for item in items:
                if isinstance(item, IRBlock):
                    for inst in item.insts:
                        if inst.op in (Op.ALLOC, Op.FREE):
                            return True
                elif isinstance(item, IRLoop):
                    if walk_items(item.body):
                        return True
                elif isinstance(item, IRWhileLoop):
                    if walk_items(item.body):
                        return True
                elif isinstance(item, IRIf):
                    if walk_items(item.then_body):
                        return True
                    if item.else_body and walk_items(item.else_body):
                        return True
            return False
        if walk_items(mod.main_body):
            return True
        for fn in mod.functions:
            if walk_items(fn.body):
                return True
        return False

    def _emit_arena_decl(self) -> None:
        self._put_raw("/* Ergo arena: STATIC-backed bump allocator for "
                      "ALLOCATABLE arrays.")
        self._put_raw("   No libc, no syscalls — file-scope BSS only. "
                      "DEALLOCATE is a no-op. */")
        self._put_raw("#ifndef ERGO_ARENA_BYTES")
        self._put_raw("#define ERGO_ARENA_BYTES ((size_t)1 << 30)")
        self._put_raw("#endif")
        self._put_raw("static char _ergo_arena[ERGO_ARENA_BYTES] "
                      "__attribute__((aligned(64)));")
        self._put_raw("static size_t _ergo_arena_offset = 0;")
        self._put_raw("")

    # ── DOT_PRODUCT / NORM2 lowering ──────────────────────────
    # Whole-array reductions on 1D constant-shape arrays. No allocation,
    # no hidden temporaries — a flat scalar loop the C compiler vectorizes.

    def _uses_dot(self, mod: IRModule) -> bool:
        """Return True if any DOT_PRODUCT/NORM2 instruction is reachable."""
        def walk_items(items) -> bool:
            for item in items:
                if isinstance(item, IRBlock):
                    for inst in item.insts:
                        if inst.op in (Op.DOT_PRODUCT, Op.NORM2):
                            return True
                elif isinstance(item, IRLoop):
                    if walk_items(item.body):
                        return True
                elif isinstance(item, IRWhileLoop):
                    if walk_items(item.body):
                        return True
                elif isinstance(item, IRIf):
                    if walk_items(item.then_body):
                        return True
                    if item.else_body and walk_items(item.else_body):
                        return True
            return False
        if walk_items(mod.main_body):
            return True
        for fn in mod.functions:
            if walk_items(fn.body):
                return True
        return False

    def _uses_hash(self, mod: IRModule) -> bool:
        """Return True if any HASH/RAND instruction is reachable."""
        def walk_items(items) -> bool:
            for item in items:
                if isinstance(item, IRBlock):
                    for inst in item.insts:
                        if inst.op in (Op.HASH, Op.RAND):
                            return True
                elif isinstance(item, IRLoop):
                    if walk_items(item.body):
                        return True
                elif isinstance(item, IRWhileLoop):
                    if walk_items(item.body):
                        return True
                elif isinstance(item, IRIf):
                    if walk_items(item.then_body):
                        return True
                    if item.else_body and walk_items(item.else_body):
                        return True
            return False
        if walk_items(mod.main_body):
            return True
        for fn in mod.functions:
            if walk_items(fn.body):
                return True
        return False

    def _uses_esf(self, mod: IRModule) -> bool:
        """Return True if any .esf stream op (ESF_* / ESF_NEXT) is
        reachable — gates the ergo_stream.h include."""
        def walk_items(items) -> bool:
            for item in items:
                if isinstance(item, IRBlock):
                    for inst in item.insts:
                        if inst.op == Op.ESF_NEXT:
                            return True
                        if inst.op == Op.CALL_VOID and \
                                str(inst.meta.get("func", "")) \
                                .startswith("ESF_"):
                            return True
                elif isinstance(item, IRLoop):
                    if walk_items(item.body):
                        return True
                elif isinstance(item, IRWhileLoop):
                    if walk_items(item.body):
                        return True
                elif isinstance(item, IRIf):
                    if walk_items(item.then_body):
                        return True
                    if item.else_body and walk_items(item.else_body):
                        return True
            return False
        if walk_items(mod.main_body):
            return True
        for fn in mod.functions:
            if walk_items(fn.body):
                return True
        return False
    # splitmix64 finalizer (Stafford 2013). Constants: the Weyl increment
    # is the golden-ratio 2^64/phi; both multipliers are Stafford's
    # odd 64-bit constants chosen for maximal avalanche. The full 64-bit
    # output passes PractRand and BigCrush; we only use high bits, whose
    # quality dominates the low bits'.
    #   HASH(x) → INTEGER: bits 63..33 of the finalize — non-negative
    #   int32 [0, 2^31-1]. Chaining S := HASH(S) is the canonical
    #   splitmix64 state advance (each call applies the Weyl increment).
    #   RAND(x) → REAL: top 53 bits × 2^-53, uniform on [0, 1), exact
    #   in f64.
    def _emit_hash_helper(self) -> None:
        self._put_raw("/* Ergo PRNG helpers: splitmix64 finalizer "
                      "(see above). */")
        self._put_raw("static inline unsigned long long _ergo_splitmix64("
                      "unsigned long long x) {")
        self._put_raw("    x += 0x9E3779B97F4A7C15ULL;")
        self._put_raw("    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;")
        self._put_raw("    x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;")
        self._put_raw("    return x ^ (x >> 31);")
        self._put_raw("}")
        self._put_raw("static inline int _ergo_hash32(unsigned long long x) {")
        self._put_raw("    return (int)(_ergo_splitmix64(x) >> 33);")
        self._put_raw("}")
        self._put_raw("static inline double _ergo_rand01(unsigned long long x) {")
        self._put_raw("    return (double)(_ergo_splitmix64(x) >> 11) * 0x1.0p-53;")
        self._put_raw("}")
        self._put_raw("")

    def _emit_dot_helper(self) -> None:
        rt = _c_type(IRType.REAL)
        self._put_raw("/* Ergo reduction helper: flat dot product over n "
                      "elements. */")
        self._put_raw("/* No allocation; the C compiler vectorizes the "
                      "loop. */")
        self._put_raw(f"static inline {rt} _ergo_dot(const {rt}* a, "
                      f"const {rt}* b, int n) {{")
        self._put_raw(f"    {rt} acc = 0.0;")
        self._put_raw("    for (int i = 0; i < n; i++) acc += a[i] * b[i];")
        self._put_raw("    return acc;")
        self._put_raw("}")
        self._put_raw("")

    def _dot_size(self, array_name: str, line: int = 0) -> str:
        """Compile-time element count for a 1D constant-shape array."""
        shape = self._array_shapes.get(array_name)
        if shape and len(shape) == 1:
            return self._dim_expr(shape[0])
        raise MCLError(
            f"DOT_PRODUCT/NORM2: '{array_name}' is not a 1D array with a "
            f"compile-time-known shape (ALLOCATABLE, runtime-shaped and "
            f"assumed-shape arguments are not supported)", line or None)

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

    def _kernel_tiled(self, kernel) -> bool:
        """True if this kernel is dispatched in tiles (--gpu-tile-size).

        Must agree EXACTLY with the SPIRV backend's _EmitContext._tiled
        (push-constant layout depends on it): tiling applies to every
        dispatched kernel except segmented reductions, whose
        group→segment mapping assumes a whole-range dispatch. The device
        iteration model is i = gid+1 (+ _tile_base), so any kernel that
        is correct untiled partitions identically under tiling.
        """
        return (self.gpu_tile_size > 0
                and not kernel.reduction_array
                and self._is_gpu_kernel(kernel))

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

    @staticmethod
    def _plan_red_accs(kernel) -> int:
        """Number of scalar accumulators in a reduction kernel."""
        if kernel.reduction_vars:
            return len(kernel.reduction_vars)
        return 1 if kernel.reduction_var else 0

    def _emit_gpu_init(self):
        """Emit Vulkan init, buffer allocation, and pipeline creation."""
        self._put("/* === Vulkan init === */")
        # Ping-pong: arrays read AND written by exactly one frame-loop
        # kernel get 2x buffers + rd/wr offset push constants. Single
        # source of truth shared with the SPIRV backend
        # (ir_gpu.compute_pingpong_arrays) — the two MUST agree.
        from .ir_gpu import compute_pingpong_arrays
        pp_arrays: set[str] = compute_pingpong_arrays(
            self.module, self.gpu_plan) if self.gpu_plan else set()
        self._pp_arrays = pp_arrays

        # Tile clipmap: a CPU-resident STATIC INTEGER array named
        # TILE_CLIP (reserved name) maintained by the program itself.
        # When --gpu-tile-size is active, the host tile loop of each
        # tiled non-reduction kernel skips tiles flagged 0 — the tile's
        # output elements keep their stale device values. ONE array is
        # shared by all tiled kernels: QTILE is compile-time uniform, so
        # tile t covers the same flat element range [t*QTILE, ...) of
        # every tiled kernel. Skipping is never applied to reduction
        # kernels (their ordered combine expects every tile's partials).
        # Inert when tiling is off.
        self._tile_clip_size = None
        if self.gpu_tile_size > 0 and "TILE_CLIP" in self._array_shapes:
            import sys
            if self._var_types.get("TILE_CLIP") == IRType.INTEGER:
                cl_shape = self._array_shapes["TILE_CLIP"]
                self._tile_clip_size = " * ".join(
                    self._dim_expr(d) for d in cl_shape)
                print(f"[spirv] TILE_CLIP: per-tile clip active for "
                      f"tiled non-reduction kernels ({self._tile_clip_size}"
                      f" slots, QTILE={self._qtile})", file=sys.stderr)
            else:
                print("[spirv] WARNING: TILE_CLIP is declared but not "
                      "INTEGER — clip disabled", file=sys.stderr)
        if self.render:
            self._put("ergo_vk_init(0); /* windowed */")
        else:
            self._put("ergo_vk_init(1); /* headless */")
        # Compute VRAM-based particle capacity (50% of DEVICE_LOCAL heap)
        self._emit_vram_capacity()
        self._put("")

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
            # Pre-swapped: first frame_begin swap flips to rd=0, wr=N
            # so frame 1 reads offset 0 (where the initial upload landed)
            # and writes the second half [N..2N). The offset is in
            # ELEMENTS; the detection rule guarantees every pp array
            # shares one shape, so a single global offset pair suffices.
            # (Was hardcoded to CAPACITY — undefined and wrong-sized for
            # programs without MAXPART.)
            ref = sorted(pp_arrays)[0]
            dims = []
            for d in self._array_shapes[ref]:
                expr = self._dim_expr(d)
                dims.append("CAPACITY" if expr == "MAXPART" else expr)
            pp_n = " * ".join(dims)
            self._put(f"int _pp_rd_offset = {pp_n};")
            self._put(f"int _pp_wr_offset = 0;")
        # REDUCTION output buffers: one REAL partial per workgroup per
        # accumulator (layout [acc][workgroup]). Sized
        # n_acc * ceil(bound/256) — the host reads them back in group
        # order and performs the final sum (no atomics device-side).
        for k in self.gpu_plan.kernels:
            n_acc = self._plan_red_accs(k)
            if n_acc or k.reduction_array:
                ct = self._c_type(IRType.REAL)
                rbound = self._operand(k.loop_bound)
                if self._kernel_tiled(k):
                    # Tiled: partials layout [tile][acc][group] with
                    # GPT = QTILE/256 groups per tile (see spirv.py).
                    gpt = self._qtile // 256
                    self._put(f"ErgoVkBuf d__reduce_{k.kernel_id} = "
                              f"ergo_vk_create_buffer((size_t){max(n_acc, 1)} * "
                              f"((({rbound} + {self._qtile - 1}) / {self._qtile})"
                              f" * {gpt} * sizeof({ct})));")
                else:
                    self._put(f"ErgoVkBuf d__reduce_{k.kernel_id} = "
                              f"ergo_vk_create_buffer((size_t){max(n_acc, 1)} * "
                              f"((({rbound} + 255) / 256) * sizeof({ct})));")
        self._put("")

        # Load SPIR-V pipelines — for now, from external .spv files
        # Phase E will embed the binaries
        self._put("/* Load compute pipelines (from external .spv files) */")
        for k in self.gpu_plan.kernels:
            if not self._is_gpu_kernel(k):
                continue  # skip init-only kernels without GPU buffers
            n_bufs = len(k.arrays_written) + len(k.arrays_read - k.arrays_written)
            if k.reduction_var or k.reduction_array or k.reduction_vars:
                n_bufs += 1  # per-workgroup partials output buffer
            scalars = self._kernel_pc_scalars(k)
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
            # Tile bounds: _tile_base/_tile_hi, plus _tile_idx for
            # reduction kernels — appended after all other members,
            # matching the device struct (spirv.py _declare_push_constants).
            if self._kernel_tiled(k):
                n_tile = 3 if (k.reduction_var or k.reduction_vars) else 2
                pc_size += 4 * n_tile
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
                # Size from the array's real shape (mirror of the regular
                # d_ buffer allocation — the handles swap, so sizes must
                # match). Never hardcode MAXPART: not every module has it.
                shape = self._array_shapes.get(arr)
                if shape:
                    dims = []
                    for d in shape:
                        expr = self._dim_expr(d)
                        dims.append("CAPACITY" if expr == "MAXPART" else expr)
                    size_expr = " * ".join(dims)
                else:
                    size_expr = "1"
                self._put(f"ErgoVkBuf d_sort_{arr} = ergo_vk_create_buffer("
                          f"{size_expr} * {sz});")
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

    def _kernel_pc_scalars(self, k) -> list[str]:
        """Push-constant scalar list for a kernel, sorted by type (reals
        first, then ints) to match the SPIRV struct layout.

        Includes the loop-bound variable when it is a runtime ref:
        extraction's scalars_read does not cover loop bounds, which left
        runtime-valued bounds unresolvable in the backend (they silently
        became 0 — an empty kernel)."""
        scalars = set(k.scalars_read)
        bound = getattr(k, "loop_bound", None)
        if isinstance(bound, IRRef):
            scalars.add(bound.name)
        return sorted(
            scalars,
            key=lambda s: (0 if self._var_types.get(s, IRType.REAL) == IRType.REAL else 1, s))

    def _emit_gpu_dispatch(self, kernel: KernelPlan):
        """Emit a GPU kernel dispatch in place of a CPU loop."""
        kid = kernel.kernel_id
        bound = self._operand(kernel.loop_bound)
        red = (kernel.reduction_var or kernel.reduction_array
               or kernel.reduction_vars)

        self._put(f"/* GPU dispatch: kernel_{kid} (source line {kernel.source_line}) */")

        # Bind buffers
        buf_idx = 0
        for arr in sorted(kernel.arrays_written):
            self._put(f"ergo_vk_bind_buffer(pipe_{kid}, {buf_idx}, d_{arr});")
            buf_idx += 1
        for arr in sorted(kernel.arrays_read - kernel.arrays_written):
            self._put(f"ergo_vk_bind_buffer(pipe_{kid}, {buf_idx}, d_{arr});")
            buf_idx += 1
        if red:
            # Per-workgroup partials output (bound last — matches the
            # SPIRV binding order in _declare_buffers).
            self._put(f"ergo_vk_bind_buffer(pipe_{kid}, {buf_idx}, "
                      f"d__reduce_{kid});")
            buf_idx += 1

        # Push constants — member names prefixed with _s_ to avoid
        # collision with #define'd PARAMETER macros (e.g. PFLAG_ACTIVE).
        # Sort by type (doubles first, then ints) to match SPIRV layout
        # and avoid mixed-type padding mismatches.
        scalars = self._kernel_pc_scalars(kernel)
        # Check for ping-pong arrays (read AND written by this kernel).
        # self._pp_arrays comes from ir_gpu.compute_pingpong_arrays —
        # the same set the SPIRV backend used for offset injection.
        pp_arrays = kernel.arrays_read & kernel.arrays_written & getattr(self, '_pp_arrays', set())
        has_pp = len(pp_arrays) > 0 and self._is_gpu_kernel(kernel)

        tiled = self._kernel_tiled(kernel)
        tile_red = tiled and bool(kernel.reduction_var
                                  or kernel.reduction_vars)

        if scalars or has_pp or tiled:
            self._put(f"{{")
            self.indent += 1
            if tiled:
                # Per-tile push constants: _tile_base/_tile_hi (+
                # _tile_idx for reductions) trail the scalar/pp members,
                # matching the device struct. QTILE is a workgroup
                # multiple, so reduction group boundaries coincide with
                # the untiled dispatch (bitwise-identical combine).
                self._put(f"int _tb = 0, _bnd = ({bound}), _tidx = 0;")
                self._put(f"while (_tb < _bnd) {{")
                self.indent += 1
                self._put(f"int _hi = _tb + {self._qtile}; "
                          f"if (_hi > _bnd) _hi = _bnd;")
                if self._tile_clip_size is not None and not tile_red:
                    # Tile clipmap: TILE_CLIP[_tidx] == 0 -> skip this
                    # tile's dispatch entirely; its output elements keep
                    # their stale device values. Soundness of skipping
                    # is the Ergo program's responsibility. The size
                    # guard makes an undersized clip array safe (tiles
                    # beyond it always dispatch).
                    self._put(f"if (_tidx < {self._tile_clip_size} && "
                              f"TILE_CLIP[_tidx] == 0) {{ "
                              f"_tb += {self._qtile}; _tidx++; continue; }}")
                elif self._tile_clip_size is not None and tile_red:
                    # Reductions combine partials in fixed [tile][group]
                    # order expecting every tile present — never clip.
                    if kid not in self._clip_warned:
                        self._clip_warned.add(kid)
                        import sys
                        print(f"[spirv] WARNING: TILE_CLIP ignored for "
                              f"reduction kernel_{kid} (clip unsupported "
                              f"for reductions)", file=sys.stderr)
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
            if tiled:
                self._put(f"int _s__tile_base;")
                self._put(f"int _s__tile_hi;")
                pc_vals.append("_tb")
                pc_vals.append("_hi")
                if tile_red:
                    self._put(f"int _s__tile_idx;")
                    pc_vals.append("_tidx")
            self.indent -= 1
            self._put(f"}} _pc = {{ {', '.join(pc_vals)} }};")
            self._put(f"ergo_vk_push_constants(pipe_{kid}, &_pc, sizeof(_pc));")
            if tiled:
                groups = "((_hi - _tb + 255) / 256)"
                if self._batched_frame:
                    self._put(f"ergo_vk_frame_dispatch(pipe_{kid}, {groups});")
                else:
                    self._put(f"ergo_vk_dispatch(pipe_{kid}, {groups});")
                self._put(f"_tb += {self._qtile}; _tidx++;")
                self.indent -= 1
                self._put(f"}}")
            self.indent -= 1
            self._put(f"}}")

        if self._batched_frame:
            if not tiled:
                self._put(f"ergo_vk_frame_dispatch(pipe_{kid}, ({bound} + 255) / 256);")
            self._frame_gpu_dirty |= kernel.arrays_written
            if red:
                # Coalesced reduction: record the dispatch into the
                # current frame and defer the host read-back — one drain
                # + one combined download for the whole run of
                # consecutive reduction kernels (flushed before the next
                # non-dispatch item; see _emit_body). Tiled reductions
                # skip the combined multi-download at flush time (their
                # partials use the [tile][acc][group] layout).
                self._pending_reductions.append(kernel)
        else:
            if not tiled:
                self._put(f"ergo_vk_dispatch(pipe_{kid}, ({bound} + 255) / 256);")
            if red:
                self._emit_reduction_readback(kernel)

    def _emit_reduction_readback(self, kernel: KernelPlan,
                                 chunk_var: str = "_rchunk",
                                 downloaded: bool = False,
                                 skip_acc_sync: bool = False):
        """Emit the host read-back + ordered combine for one reduction
        kernel's partials buffer.

        Group order is fixed, so the result is deterministic for a fixed
        dispatch shape. The CPU accumulator(s) still hold their pre-loop
        values — the combine ADDS onto them. When `downloaded` is True,
        the partials are already in `chunk_var` (combined multi-download
        of a coalesced group; requires _G <= 1024) and only the combine
        is emitted.
        """
        kid = kernel.kernel_id
        bound = self._operand(kernel.loop_bound)
        red = kernel.reduction_var or kernel.reduction_array
        ct = self._c_type(IRType.REAL)
        # All scalar accumulators of a (multi-)reduction kernel; the
        # partials buffer is laid out [acc][workgroup].
        accs = kernel.reduction_vars or (
            [kernel.reduction_var] if kernel.reduction_var else [])

        if self._kernel_tiled(kernel):
            # Tiled partials use the [tile][acc][group] layout — the
            # generic path below assumes [acc][workgroup].
            self._emit_tiled_reduction_readback(kernel, accs)
            return

        # F98: the accumulator array may ALSO be written by other kernels
        # (e.g. an extracted zeroing loop), making it GPU-resident. Sync
        # the host copy from the device before combining (otherwise the
        # host adds onto stale values and a later download would clobber
        # the combined sums), and write the combined values back after.
        # In a coalesced group (_flush_pending_reductions) the group
        # caller emits one sync per distinct accumulator instead of one
        # per kernel (skip_acc_sync) — same arithmetic, fewer transfers.
        seg_acc = kernel.reduction_array
        seg_acc_gpu = False
        seg_size = seg_sz = None
        if seg_acc and seg_acc in set(self._gpu_arrays()):
            seg_shape = self._array_shapes.get(seg_acc)
            if seg_shape:
                seg_acc_gpu = True
                seg_size = " * ".join(self._dim_expr(d) for d in seg_shape)
                seg_sz = self._gpu_sizeof(seg_acc)
                if not skip_acc_sync:
                    self._put(f"/* Sync segmented accumulator with device copy */")
                    self._put(f"ergo_vk_download(d_{seg_acc}, {seg_acc}, "
                              f"{seg_size} * {seg_sz});")

        self._put(f"/* Reduction read-back: ordered sum of group "
                  f"partials into '{red}' */")
        self._put("{")
        self.indent += 1
        self._put(f"int _G = (({bound}) + 255) / 256;")
        if kernel.reduction_array:
            # Segmented: group g's partial belongs to segment g / Gseg
            # (segments are contiguous, equal-length, 256-padded —
            # validated at extraction).
            nseg = self._dim_expr(
                self._array_shapes[kernel.reduction_array][0])
            self._put(f"int _Nseg = ({nseg});")
            self._put("int _Gseg = _G / _Nseg;")
        if downloaded:
            # Partials already fetched by the coalesced multi-download.
            if kernel.reduction_array:
                self._put(f"for (int _j = 0; _j < _G; _j++) "
                          f"{kernel.reduction_array}[_j / _Gseg] "
                          f"+= {chunk_var}[_j];")
            else:
                for ai, acc in enumerate(accs):
                    cast = ("(int)" if self._var_types.get(acc)
                            == IRType.INTEGER else "")
                    self._put(f"for (int _j = 0; _j < _G; _j++) "
                              f"{acc} += {cast}{chunk_var}[_j "
                              f"+ {ai} * _G];")
        else:
            # One download when the whole [acc][group] partials buffer
            # is small (contiguous layout) — a per-acc chunked loop
            # costs one submit/wait per chunk, which dominated the
            # N=19 ED per-tile reductions. Chunk size 65536 floats
            # (512 KiB stack); the combine order is unchanged either
            # way, so results are bitwise identical.
            if not kernel.reduction_array:
                self._put(f"if ({len(accs)} * _G <= 131072) {{")
                self.indent += 1
                self._put(f"{ct} _rall[{len(accs)} * _G];")
                self._put(f"ergo_vk_download(d__reduce_{kid}, _rall, "
                          f"(size_t){len(accs)} * _G * sizeof({ct}));")
                for ai, acc in enumerate(accs):
                    cast = ("(int)" if self._var_types.get(acc)
                            == IRType.INTEGER else "")
                    self._put(f"for (int _j = 0; _j < _G; _j++) "
                              f"{acc} += {cast}_rall[_j + {ai} * _G];")
                self.indent -= 1
                self._put("} else {")
                self.indent += 1
            self._put(f"{ct} {chunk_var}[65536];")
            if kernel.reduction_array:
                self._put("for (int _c = 0; _c < _G; _c += 65536) {")
                self.indent += 1
                self._put("int _n = (_G - _c < 65536) ? (_G - _c) : 65536;")
                self._put(f"ergo_vk_download_at(d__reduce_{kid}, {chunk_var}, "
                          f"(size_t)_c * sizeof({ct}), _n * sizeof({ct}));")
                self._put(f"for (int _j = 0; _j < _n; _j++) "
                          f"{kernel.reduction_array}[(_c + _j) / _Gseg] "
                          f"+= {chunk_var}[_j];")
                self.indent -= 1
                self._put("}")
            else:
                for ai, acc in enumerate(accs):
                    cast = ("(int)" if self._var_types.get(acc)
                            == IRType.INTEGER else "")
                    self._put("for (int _c = 0; _c < _G; _c += 65536) {")
                    self.indent += 1
                    self._put("int _n = (_G - _c < 65536) ? (_G - _c) : 65536;")
                    self._put(f"ergo_vk_download_at(d__reduce_{kid}, "
                              f"{chunk_var}, (size_t)({ai} * _G + _c) * "
                              f"sizeof({ct}), _n * sizeof({ct}));")
                    self._put(f"for (int _j = 0; _j < _n; _j++) "
                              f"{acc} += {cast}{chunk_var}[_j];")
                    self.indent -= 1
                    self._put("}")
            if not kernel.reduction_array:
                self.indent -= 1
                self._put("}")
        self.indent -= 1
        self._put("}")

        if seg_acc_gpu and not skip_acc_sync:
            self._put(f"ergo_vk_upload(d_{seg_acc}, {seg_acc}, "
                      f"{seg_size} * {seg_sz});")
            self._gpu_current.add(seg_acc)
        self._gpu_current |= kernel.arrays_read

    def _emit_tiled_reduction_readback(self, kernel: KernelPlan,
                                       accs: list):
        """Host read-back + ordered combine for a TILED reduction kernel.

        Partials are laid out [tile][acc][group] with GPT = QTILE/256
        groups per tile. Since QTILE is a workgroup multiple, tile t
        group g covers exactly the elements of untiled group t*GPT+g, so
        summing in [tile][group] order is bitwise identical to the
        untiled combine.
        """
        kid = kernel.kernel_id
        bound = self._operand(kernel.loop_bound)
        ct = self._c_type(IRType.REAL)
        gpt = self._qtile // 256
        n_acc = max(len(accs), 1)
        self._put(f"/* Tiled reduction read-back: ordered sum over "
                  f"[tile][group] partials into "
                  f"'{kernel.reduction_var}' */")
        self._put("{")
        self.indent += 1
        self._put(f"int _G = (({bound}) + 255) / 256;")
        self._put(f"int _NT = (({bound}) + {self._qtile - 1}) / {self._qtile};")
        # The partials buffer is one contiguous [tile][acc][group] block
        # — fetch it in ONE transfer when small (a per-(acc,tile)
        # download costs one submit/wait each, which dominated the DBM
        # solver's transfer count). VLA capped; large buffers take the
        # per-tile path.
        self._put(f"if (_NT * {n_acc * gpt} <= 16384) {{")
        self.indent += 1
        self._put(f"{ct} _rall[_NT * {n_acc * gpt}];")
        self._put(f"ergo_vk_download(d__reduce_{kid}, _rall, "
                  f"(size_t)_NT * {n_acc * gpt} * sizeof({ct}));")
        for ai, acc in enumerate(accs):
            cast = ("(int)" if self._var_types.get(acc)
                    == IRType.INTEGER else "")
            self._put(f"for (int _t = 0; _t < _NT; _t++) {{")
            self.indent += 1
            self._put(f"int _ng = _G - _t * {gpt}; "
                      f"if (_ng > {gpt}) _ng = {gpt};")
            self._put(f"for (int _j = 0; _j < _ng; _j++) "
                      f"{acc} += {cast}_rall[_t * {n_acc * gpt} + "
                      f"{ai * gpt} + _j];")
            self.indent -= 1
            self._put("}")
        self.indent -= 1
        self._put("} else {")
        self.indent += 1
        self._put(f"{ct} _rtile[{gpt}];")
        for ai, acc in enumerate(accs):
            cast = ("(int)" if self._var_types.get(acc)
                    == IRType.INTEGER else "")
            self._put(f"for (int _t = 0; _t < _NT; _t++) {{")
            self.indent += 1
            self._put(f"int _ng = _G - _t * {gpt}; "
                      f"if (_ng > {gpt}) _ng = {gpt};")
            self._put(f"ergo_vk_download_at(d__reduce_{kid}, _rtile, "
                      f"(size_t)(_t * {n_acc * gpt} + {ai * gpt}) * "
                      f"sizeof({ct}), _ng * sizeof({ct}));")
            self._put(f"for (int _j = 0; _j < _ng; _j++) "
                      f"{acc} += {cast}_rtile[_j];")
            self.indent -= 1
            self._put("}")
        self.indent -= 1
        self._put("}")
        self.indent -= 1
        self._put("}")
        self._gpu_current |= kernel.arrays_read

    def _flush_pending_reductions(self):
        """Drain the batched frame ONCE for a run of coalesced reduction
        kernels, download all their partials in ONE transfer (when the
        group counts fit the chunk buffers), then emit the per-kernel
        ordered combines. Called before the next non-dispatch item (the
        F-era intersection check in _emit_body decides when CPU reads
        force this) and at the end of a body."""
        if not self._pending_reductions:
            return
        pending = self._pending_reductions
        self._pending_reductions = []

        if self._batched_frame and not self._frame_ended_early:
            self._put("/* Coalesced reduction group: single drain */")
            self._put("ergo_vk_frame_end();")
            self._put("ergo_vk_frame_wait();")
            self._frame_ended_early = True

        # Combined download for the whole group when every kernel's
        # group count is a compile-time constant <= 1024 (the chunk
        # size); otherwise fall back to per-kernel chunked downloads.
        ct = self._c_type(IRType.REAL)
        gs = [self._resolve_const(k.loop_bound) for k in pending]
        group_counts = [((b + 255) // 256) if b is not None else None
                        for b in gs]
        multi = (len(pending) > 1
                 and all(g is not None and g <= 1024
                         for g in group_counts)
                 # Tiled reductions use the [tile][acc][group] partials
                 # layout — the combined multi-download assumes
                 # [acc][workgroup], so they take the per-kernel path.
                 and not any(self._kernel_tiled(k) for k in pending))
        if multi:
            self._put("/* Coalesced partials download: one transfer for "
                      "the whole reduction group */")
            self._put("{")
            self.indent += 1
            for k in pending:
                self._put(f"{ct} _rc{k.kernel_id}[1024];")
            bufs = ", ".join(f"d__reduce_{k.kernel_id}" for k in pending)
            dsts = ", ".join(f"_rc{k.kernel_id}" for k in pending)
            offs = ", ".join("0" for _ in pending)
            sizes = ", ".join(
                f"{g} * sizeof({ct})" for g in group_counts)
            n = len(pending)
            self._put(f"{{ ErgoVkBuf _mb[{n}] = {{ {bufs} }};")
            self._put(f"  void *_md[{n}] = {{ {dsts} }};")
            self._put(f"  size_t _mo[{n}] = {{ {offs} }};")
            self._put(f"  size_t _ms[{n}] = {{ {sizes} }};")
            self._put(f"  ergo_vk_download_multi(_mb, _md, _mo, _ms, {n}); }}")
            # Segmented accumulators: sync each DISTINCT accumulator
            # once for the whole group (download before its first
            # combine, upload after its last) instead of per kernel —
            # the six pair-force segred kernels share RES_VX/Y/Z.
            # Combine order per accumulator is unchanged (kernel order),
            # so output is bitwise-identical to per-kernel syncs.
            seen_accs: list = []
            for k in pending:
                acc = k.reduction_array
                if acc and acc not in seen_accs:
                    seen_accs.append(acc)
            for acc in seen_accs:
                if acc in set(self._gpu_arrays()):
                    shape = self._array_shapes.get(acc)
                    if shape:
                        sz_expr = " * ".join(self._dim_expr(d)
                                             for d in shape)
                        sz = self._gpu_sizeof(acc)
                        self._put(f"/* Sync segmented accumulator "
                                  f"(once per group) */")
                        self._put(f"ergo_vk_download(d_{acc}, {acc}, "
                                  f"{sz_expr} * {sz});")
            for k in pending:
                self._emit_reduction_readback(
                    k, chunk_var=f"_rc{k.kernel_id}", downloaded=True,
                    skip_acc_sync=True)
            for acc in seen_accs:
                if acc in set(self._gpu_arrays()):
                    shape = self._array_shapes.get(acc)
                    if shape:
                        sz_expr = " * ".join(self._dim_expr(d)
                                             for d in shape)
                        sz = self._gpu_sizeof(acc)
                        self._put(f"ergo_vk_upload(d_{acc}, {acc}, "
                                  f"{sz_expr} * {sz});")
                        self._gpu_current.add(acc)
            self.indent -= 1
            self._put("}")
        else:
            for k in pending:
                self._emit_reduction_readback(k)

        # Re-open the frame for subsequent GPU work.
        if self._batched_frame and self._frame_ended_early:
            self._put("ergo_vk_frame_begin();")
            self._frame_ended_early = False
            self._frame_gpu_dirty.clear()

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
                    self._put_ranged_upload(arr, shape, sz)
        # Mark these arrays as GPU-current
        self._gpu_current |= suffix_writes

    def _collect_referenced_funcs(self, mod: IRModule) -> set[str]:
        """Names of functions/subroutines referenced by any CALL or
        CALL_VOID in the module (main body + every function body)."""
        refs: set[str] = set()

        def scan(items):
            for item in items:
                if isinstance(item, IRBlock):
                    for inst in item.insts:
                        if inst.op in (Op.CALL, Op.CALL_VOID):
                            refs.add(inst.meta.get("func", ""))
                        elif inst.op == Op.VERIFY and not self.no_verify:
                            # The oracle evolves its shadow state by calling
                            # the module's physics subroutine directly
                            # (hardcoded at _emit_verify) — it must be kept.
                            refs.add("SIM_PHYSICS_STEP")
                elif isinstance(item, IRIf):
                    scan(item.then_body)
                    if item.else_body:
                        scan(item.else_body)
                elif isinstance(item, (IRLoop, IRWhileLoop)):
                    scan(item.body)
                elif isinstance(item, IRSelect):
                    for _v, body in item.cases:
                        scan(body)

        scan(mod.main_body)
        for fn in mod.functions:
            scan(fn.body)
        refs.discard("")
        return refs

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

    def _collect_cpu_array_writes(self, items: list, writes: set[str]):
        """Like _collect_array_writes, but skips sub-loops extracted as
        GPU kernels — their writes happen on the device, not the CPU.
        Used for CPU-dirty tracking so a CPU loop wrapping GPU dispatches
        (e.g. a ping-pong matvec loop) doesn't force stale re-uploads."""
        for item in items:
            if isinstance(item, IRLoop):
                if item.line in self._kernel_by_line:
                    continue  # GPU kernel — device write, not a CPU write
                self._collect_cpu_array_writes(item.body, writes)
            elif isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.op in (Op.STORE, Op.ZERO):
                        arr = inst.meta.get("array", "")
                        if arr:
                            writes.add(arr)
            elif isinstance(item, IRIf):
                self._collect_cpu_array_writes(item.then_body, writes)
                if item.else_body:
                    self._collect_cpu_array_writes(item.else_body, writes)
            elif isinstance(item, IRWhileLoop):
                self._collect_cpu_array_writes(item.body, writes)

    def _collect_cpu_array_reads(self, items: list, reads: set[str]):
        """Like _collect_array_reads, but skips sub-loops extracted as
        GPU kernels — their reads happen on the device, not the CPU.
        Without this, a kernel nested in an IF (e.g. a PROF accumulate)
        makes the mid-body download logic see phantom CPU reads and
        download the whole array every iteration — and that download can
        clobber host init values the device never had."""
        for item in items:
            if isinstance(item, IRLoop):
                if item.line in self._kernel_by_line:
                    continue  # GPU kernel — device-side read
                self._collect_cpu_array_reads(item.body, reads)
            elif isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.op == Op.LOAD:
                        arr = inst.meta.get("array", "")
                        if arr:
                            reads.add(arr)
                    elif inst.op in (Op.DOT_PRODUCT, Op.NORM2):
                        for arr in inst.meta.get("arrays", []):
                            if arr and arr != "?":
                                reads.add(arr)
            elif isinstance(item, IRIf):
                self._collect_cpu_array_reads(item.then_body, reads)
                if item.else_body:
                    self._collect_cpu_array_reads(item.else_body, reads)
            elif isinstance(item, IRWhileLoop):
                self._collect_cpu_array_reads(item.body, reads)

    def _collect_array_reads(self, items: list, reads: set[str]):
        """Walk IR items and collect names of arrays read by LOAD ops."""
        for item in items:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.op == Op.LOAD:
                        arr = inst.meta.get("array", "")
                        if arr:
                            reads.add(arr)
                    elif inst.op in (Op.DOT_PRODUCT, Op.NORM2):
                        # Whole-array reductions read every element.
                        for arr in inst.meta.get("arrays", []):
                            if arr and arr != "?":
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
            # Defensive: REAL-typed string literal (TYPE_MAP transition)
            if op.type == IRType.STRING or isinstance(op.value, str):
                return "%s"
            return {
                IRType.INTEGER: "%d", IRType.REAL: "%f",
                IRType.INT64: "%lld",
                IRType.LOGICAL: "%d",
            }.get(op.type, "%f")
        if isinstance(op, IRRef):
            t = self._var_types.get(op.name, op.type)
            return {
                IRType.INTEGER: "%d", IRType.REAL: "%f",
                IRType.INT64: "%lld",
                IRType.LOGICAL: "%d", IRType.STRING: "%s",
            }.get(t, "%f")
        return "%f"

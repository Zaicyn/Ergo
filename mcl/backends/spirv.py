"""SPIR-V compute shader backend for Ergo GPU kernels.

Consumes KernelPlan objects (from ir_gpu.py) and the parent IRModule,
and emits SPIR-V text assembly (.spvasm) for each kernel function.
Also generates the host-side C99 code that loads and launches kernels
via the Vulkan compute API (ergo_vk.h).

The text assembly is assembled to binary with `spirv-as` from the
Vulkan SDK.

Design decisions (locked in):
  - Push constants for scalar parameters (fits 128-byte minimum).
  - Require shaderFloat64 — fail fast, no f32 fallback.
  - SPIR-V text first, binary emission later if needed.
"""

from __future__ import annotations

from ..ir import (
    IRModule, IRVar, IRBlock, IRIf, IRLoop, IRSelect,
    IRInst, IRConst, IRRef, IRType, StorageClass, Op, Operand,
)
from ..ir_gpu import KernelPlan, GPUPlan
from . import KernelBackend, register_backend


# ── GLSL.std.450 extended instruction opcodes ──────────────
# These are the instruction numbers from the GLSL.std.450 spec.
GLSL_STD_450 = {
    Op.SIN:   4,    # Sin
    Op.COS:   14,   # Cos
    Op.TAN:   15,   # Tan
    Op.ASIN:  16,   # Asin
    Op.ACOS:  17,   # Acos
    Op.ATAN:  18,   # Atan
    Op.SINH:  19,   # Sinh
    Op.COSH:  20,   # Cosh
    Op.TANH:  21,   # Tanh
    Op.EXP:   27,   # Exp
    Op.LOG:   28,   # Log
    Op.LOG10: 30,   # not directly available; we'll compute as Log/Log(10)
    Op.SQRT:  31,   # Sqrt
    Op.ABS:   4,    # FAbs (overloaded below)
}

# Correct FAbs vs Sin disambiguation — FAbs is opcode 4 in FP context
# but Sin is also 4. Actually:
#   Sin=13, Cos=14, Tan=15, Asin=16, Acos=17, Atan=18
#   Sinh=19, Cosh=20, Tanh=21
#   Exp=27, Log=28, Exp2=29, Log2=30, Sqrt=31
#   FAbs=4, Floor=8, Ceil=9, Fract=10
#   FMin=37, FMax=40, FClamp=43, Pow=26
# Let me fix these:
GLSL_EXT = {
    Op.SIN:   "Sin",
    Op.COS:   "Cos",
    Op.TAN:   "Tan",
    Op.ASIN:  "Asin",
    Op.ACOS:  "Acos",
    Op.ATAN:  "Atan",
    Op.SINH:  "Sinh",
    Op.COSH:  "Cosh",
    Op.TANH:  "Tanh",
    Op.EXP:   "Exp",
    Op.LOG:   "Log",
    Op.SQRT:  "Sqrt",
    Op.ABS:   "FAbs",
    Op.POW:   "Pow",
    Op.MAX:   "FMax",
    Op.MIN:   "FMin",
}

# GLSL.std.450 ops that require f32 — must cast f64->f32->f64
GLSL_F32_ONLY = {
    Op.SIN, Op.COS, Op.TAN, Op.ASIN, Op.ACOS, Op.ATAN,
    Op.SINH, Op.COSH, Op.TANH, Op.EXP, Op.LOG, Op.SQRT, Op.POW,
}


class SPIRVBackend(KernelBackend):
    """Emit SPIR-V text assembly for a set of extracted kernels."""

    name = "spirv"
    device_ext = ".spvasm"

    def __init__(self, module: IRModule, plan: GPUPlan,
                 fast_math: bool = False):
        super().__init__(module, plan, fast_math)

        # Build type lookup from module
        self._var_types: dict[str, IRType] = {}
        self._var_storage: dict[str, StorageClass] = {}
        for g in module.globals:
            self._var_types[g.name] = g.type
            self._var_storage[g.name] = g.storage
        for v in module.main_locals:
            self._var_types[v.name] = v.type
            self._var_storage[v.name] = v.storage

    # ── top-level ───────────────────────────────────────────

    def generate(self) -> str:
        """Generate one .spvasm file per kernel. Returns all concatenated."""
        parts = []
        for kernel in self.plan.kernels:
            parts.append(self._emit_kernel_module(kernel))
        return "\n".join(parts)

    def generate_host_launches(self) -> str:
        """Generate C99 host code for Vulkan compute dispatch."""
        lines = []
        for kernel in self.plan.kernels:
            lines.extend(self._host_launch_code(kernel))
            lines.append("")
        return "\n".join(lines)

    # ── per-kernel SPIR-V module ────────────────────────────
    #
    # Each kernel is a self-contained SPIR-V module. This is the
    # simplest approach — one .spvasm file per kernel, assembled
    # independently with spirv-as.

    def _emit_kernel_module(self, kernel: KernelPlan) -> str:
        """Emit a complete SPIR-V module for one kernel."""
        # Build array shape lookup
        array_shapes: dict[str, tuple] = {}
        for g in self.module.globals:
            if g.shape:
                array_shapes[g.name] = g.shape
        for v in self.module.main_locals:
            if v.shape:
                array_shapes[v.name] = v.shape
        ctx = _EmitContext(kernel, self._var_types, self.fast_math,
                          array_shapes)
        ctx.emit_module()
        return "\n".join(ctx.lines) + "\n"

    # ── host launch code ────────────────────────────────────

    def _host_launch_code(self, kernel: KernelPlan) -> list[str]:
        """Generate C99 code to dispatch a kernel via ergo_vk API."""
        lines = []
        kid = kernel.kernel_id
        bound = self._host_operand(kernel.loop_bound)

        lines.append(f"    /* Dispatch kernel_{kid} (source line {kernel.source_line}) */")
        lines.append(f"    {{")

        # Buffer binding list: written arrays first, then read-only
        buf_idx = 0
        for arr in sorted(kernel.arrays_written):
            lines.append(f"        ergo_vk_bind_buffer(pipe_{kid}, {buf_idx}, d_{arr});")
            buf_idx += 1
        for arr in sorted(kernel.arrays_read - kernel.arrays_written):
            lines.append(f"        ergo_vk_bind_buffer(pipe_{kid}, {buf_idx}, d_{arr});")
            buf_idx += 1

        # Push constants: scalars packed into a struct (doubles first, then ints)
        scalars = sorted(kernel.scalars_read,
                         key=lambda s: (0 if self._var_types.get(s, IRType.REAL) == IRType.REAL else 1, s))
        if scalars:
            lines.append(f"        struct {{ ")
            for s in scalars:
                t = self._var_types.get(s, IRType.REAL)
                c_type = "double" if t == IRType.REAL else "int"
                lines.append(f"            {c_type} {s};")
            lines.append(f"        }} pc_{kid} = {{ {', '.join(scalars)} }};")
            lines.append(f"        ergo_vk_push_constants(pipe_{kid}, &pc_{kid}, sizeof(pc_{kid}));")

        lines.append(f"        ergo_vk_dispatch(pipe_{kid}, ({bound} + 255) / 256);")
        lines.append(f"    }}")
        return lines

    def _host_operand(self, op: Operand) -> str:
        if isinstance(op, IRConst):
            return str(op.value)
        if isinstance(op, IRRef):
            return op.name
        return "0"


# ── SPIR-V emission context ────────────────────────────────
#
# SPIR-V modules have a strict layout:
#   1. Header (capability, memory model, entry point)
#   2. Decorations (bindings, builtins, offsets)
#   3. Type declarations
#   4. Global variables
#   5. Function body
#
# We collect all sections, then concatenate in order.

class _EmitContext:
    """Stateful context for emitting one SPIR-V kernel module."""

    WORKGROUP_SIZE = 256

    def __init__(self, kernel: KernelPlan, var_types: dict[str, IRType],
                 fast_math: bool,
                 array_shapes: dict[str, tuple] | None = None):
        self.kernel = kernel
        self.var_types = var_types
        self.fast_math = fast_math
        self.array_shapes = array_shapes or {}
        # Ping-pong: arrays that are both read and written get offset push constants
        # Ping-pong disabled until offset injection bug is resolved
        # (particles don't move with PP enabled — SPIRV OpIAdd on indices not working)
        self.pingpong_arrays = set()

        self.lines: list[str] = []

        # SPIR-V ID allocation
        self._next_id = 1
        self._named_ids: dict[str, int] = {}

        # Track which GLSL.std.450 instructions we need
        self._needs_glsl_ext = False

        # Section buffers — filled during emit, flushed in order
        self._header: list[str] = []
        self._decorations: list[str] = []
        self._types: list[str] = []
        self._globals: list[str] = []
        self._function: list[str] = []

        # Pre-allocated type IDs (filled during type declaration)
        self.id_void: int = 0
        self.id_func_void: int = 0
        self.id_bool: int = 0
        self.id_u32: int = 0
        self.id_i32: int = 0
        self.id_f64: int = 0
        self.id_v3uint: int = 0
        self.id_ptr_input_v3uint: int = 0

        # Storage buffer pointer types
        self.id_rta_f64: int = 0        # runtime array of f64
        self.id_ptr_sb_f64: int = 0     # pointer to f64 in StorageBuffer
        self.id_ptr_sb_rta_f64: int = 0 # pointer to runtime array in SB

        # Precision-dependent aliases (point to f32 or f64 types)
        self.id_real: int = 0           # OpTypeFloat for REAL
        self.id_rta_real: int = 0       # runtime array of REAL
        self.id_ptr_sb_real: int = 0    # pointer to REAL in StorageBuffer
        self.real_size: int = 8         # bytes per REAL element

        # Push constant types (built per-kernel)
        self.id_pc_struct: int = 0
        self.id_ptr_pc: int = 0

        # Constant IDs
        self._const_ids: dict[tuple, int] = {}

        # GlobalInvocationID variable
        self.id_gl_global_inv: int = 0

        # Track array element types for LOAD/STORE
        self._array_elem_types: dict[str, IRType] = {}

        # SSA type map: SPIR-V result ID -> SPIR-V type ID
        self._ssa_types: dict[int, int] = {}

        # Cycle guard merge label (set by _emit_if when it detects a guard)
        self._cycle_guard_merge: int | None = None

        # Track current SPIR-V block label for OpPhi predecessors
        self._current_block: int = 0

    def _alloc(self, name: str = "") -> int:
        """Allocate a fresh SPIR-V ID."""
        i = self._next_id
        self._next_id += 1
        if name:
            self._named_ids[name] = i
        return i

    def _id(self, n: int) -> str:
        """Format an ID as %N."""
        return f"%{n}"

    def _get_const(self, ir_type: IRType, value) -> int:
        """Get or create a constant ID."""
        key = (ir_type, value)
        if key in self._const_ids:
            return self._const_ids[key]
        cid = self._alloc()
        if ir_type == IRType.REAL:
            self._types.append(
                f"         {self._id(cid)} = OpConstant {self._id(self.id_real)} {float(value)}")
            self._set_ssa_type(cid, self.id_real)
        elif ir_type == IRType.INTEGER:
            self._types.append(
                f"         {self._id(cid)} = OpConstant {self._id(self.id_i32)} {int(value)}")
            self._set_ssa_type(cid, self.id_i32)
        elif ir_type == IRType.LOGICAL:
            if value:
                self._types.append(
                    f"         {self._id(cid)} = OpConstantTrue {self._id(self.id_bool)}")
            else:
                self._types.append(
                    f"         {self._id(cid)} = OpConstantFalse {self._id(self.id_bool)}")
            self._set_ssa_type(cid, self.id_bool)
        else:
            self._types.append(
                f"         {self._id(cid)} = OpConstant {self._id(self.id_u32)} {int(value)}")
            self._set_ssa_type(cid, self.id_u32)
        self._const_ids[key] = cid
        return cid

    def _get_u32_const(self, value: int) -> int:
        """Get or create a u32 constant."""
        key = ("u32", value)
        if key in self._const_ids:
            return self._const_ids[key]
        cid = self._alloc()
        self._types.append(
            f"         {self._id(cid)} = OpConstant {self._id(self.id_u32)} {value}")
        self._set_ssa_type(cid, self.id_u32)
        self._const_ids[key] = cid
        return cid

    def _spirv_type_id(self, t: IRType) -> int:
        """Get the SPIR-V type ID for an IR type."""
        if t == IRType.REAL:
            return self.id_real
        if t == IRType.INTEGER:
            return self.id_i32
        if t == IRType.LOGICAL:
            return self.id_bool
        return self.id_real  # default

    # ── main emission ──────────────────────────────────────

    def emit_module(self):
        """Build the complete SPIR-V module in section order."""
        k = self.kernel

        # Scan body to determine if we need GLSL extended instructions
        self._scan_for_glsl_ext(k.loop.body)

        # --- Phase 1: Allocate type IDs and declare types ---
        self._declare_types()

        # --- Phase 2: Declare buffer variables and push constants ---
        buf_vars = self._declare_buffers()
        pc_member_ids = self._declare_push_constants()

        # --- Phase 3: Declare GlobalInvocationID ---
        self._declare_builtin()

        # --- Phase 4: Build header (must know all interface variables) ---
        self._build_header(buf_vars, pc_member_ids)

        # --- Phase 5: Emit function body ---
        self._emit_function(buf_vars, pc_member_ids)

        # --- Assemble sections in SPIR-V layout order ---
        self.lines.extend(self._header)
        self.lines.append("")
        self.lines.extend(self._decorations)
        self.lines.append("")
        self.lines.extend(self._types)
        self.lines.append("")
        self.lines.extend(self._globals)
        self.lines.append("")
        self.lines.extend(self._function)

    def _scan_for_glsl_ext(self, items: list):
        """Check if any instruction needs GLSL.std.450."""
        for item in items:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.op in GLSL_EXT:
                        self._needs_glsl_ext = True
                        return
                    if inst.op == Op.CLAMP:
                        self._needs_glsl_ext = True
                        return
                    if inst.op == Op.LOG10:
                        self._needs_glsl_ext = True
                        return
            elif isinstance(item, IRIf):
                self._scan_for_glsl_ext(item.then_body)
                if self._needs_glsl_ext:
                    return
                if item.else_body:
                    self._scan_for_glsl_ext(item.else_body)
                    if self._needs_glsl_ext:
                        return

    # ── type declarations ──────────────────────────────────

    def _declare_types(self):
        """Declare all SPIR-V types needed by the kernel."""
        # Core types
        self.id_void = self._alloc("void")
        self.id_func_void = self._alloc("func_void")
        self.id_bool = self._alloc("bool")
        self.id_u32 = self._alloc("u32")
        self.id_i32 = self._alloc("i32")
        self.id_f64 = self._alloc("f64")
        self.id_v3uint = self._alloc("v3uint")

        self._types.append(f"     {self._id(self.id_void)} = OpTypeVoid")
        self._types.append(f"     {self._id(self.id_func_void)} = OpTypeFunction {self._id(self.id_void)}")
        self._types.append(f"     {self._id(self.id_bool)} = OpTypeBool")
        self._types.append(f"     {self._id(self.id_u32)} = OpTypeInt 32 0")
        self._types.append(f"     {self._id(self.id_i32)} = OpTypeInt 32 1")
        self.id_f32 = self._alloc("f32")
        self._types.append(f"     {self._id(self.id_f32)} = OpTypeFloat 32")
        self._types.append(f"     {self._id(self.id_f64)} = OpTypeFloat 64")
        self._types.append(f"     {self._id(self.id_v3uint)} = OpTypeVector {self._id(self.id_u32)} 3")

        # Pointer to v3uint (Input) — for GlobalInvocationID
        self.id_ptr_input_v3uint = self._alloc("ptr_input_v3uint")
        self._types.append(
            f"     {self._id(self.id_ptr_input_v3uint)} = OpTypePointer Input {self._id(self.id_v3uint)}")

        # Runtime array of f64 (for storage buffers)
        self.id_rta_f64 = self._alloc("rta_f64")
        self._types.append(
            f"     {self._id(self.id_rta_f64)} = OpTypeRuntimeArray {self._id(self.id_f64)}")
        self._decorations.append(
            f"               OpDecorate {self._id(self.id_rta_f64)} ArrayStride 8")

        # Runtime array of f32 (for f32-precision storage buffers)
        self.id_rta_f32 = self._alloc("rta_f32")
        self._types.append(
            f"     {self._id(self.id_rta_f32)} = OpTypeRuntimeArray {self._id(self.id_f32)}")
        self._decorations.append(
            f"               OpDecorate {self._id(self.id_rta_f32)} ArrayStride 4")

        # Runtime array of i32 (for integer storage buffers)
        self.id_rta_i32 = self._alloc("rta_i32")
        self._types.append(
            f"     {self._id(self.id_rta_i32)} = OpTypeRuntimeArray {self._id(self.id_i32)}")
        self._decorations.append(
            f"               OpDecorate {self._id(self.id_rta_i32)} ArrayStride 4")

        # Pointer to f64 in StorageBuffer
        self.id_ptr_sb_f64 = self._alloc("ptr_sb_f64")
        self._types.append(
            f"     {self._id(self.id_ptr_sb_f64)} = OpTypePointer StorageBuffer {self._id(self.id_f64)}")

        # Pointer to f32 in StorageBuffer
        self.id_ptr_sb_f32 = self._alloc("ptr_sb_f32")
        self._types.append(
            f"     {self._id(self.id_ptr_sb_f32)} = OpTypePointer StorageBuffer {self._id(self.id_f32)}")

        # Pointer to i32 in StorageBuffer
        self.id_ptr_sb_i32 = self._alloc("ptr_sb_i32")
        self._types.append(
            f"     {self._id(self.id_ptr_sb_i32)} = OpTypePointer StorageBuffer {self._id(self.id_i32)}")

        # Set precision-dependent aliases
        from ..ir import get_real_precision
        if get_real_precision() == 32:
            self.id_real = self.id_f32
            self.id_rta_real = self.id_rta_f32
            self.id_ptr_sb_real = self.id_ptr_sb_f32
            self.real_size = 4
        else:
            self.id_real = self.id_f64
            self.id_rta_real = self.id_rta_f64
            self.id_ptr_sb_real = self.id_ptr_sb_f64
            self.real_size = 8

    def _declare_buffers(self) -> dict[str, int]:
        """Declare storage buffer variables for arrays.

        Returns a dict: array_name -> variable ID.
        """
        k = self.kernel
        buf_vars: dict[str, int] = {}
        binding = 0

        # Each array gets its own struct wrapping a RuntimeArray,
        # because SPIR-V requires Block-decorated structs for storage buffers.
        all_arrays = list(sorted(k.arrays_written)) + \
                     list(sorted(k.arrays_read - k.arrays_written))

        for arr in all_arrays:
            # Determine element type for this array
            arr_type = self.var_types.get(arr, IRType.REAL)
            if arr_type == IRType.INTEGER or arr_type == IRType.LOGICAL:
                rta_id = self.id_rta_i32
            else:
                rta_id = self.id_rta_real

            # struct { RuntimeArray<element_type> } for this buffer
            struct_id = self._alloc(f"struct_{arr}")
            self._types.append(
                f"     {self._id(struct_id)} = OpTypeStruct {self._id(rta_id)}")

            # Block decoration
            self._decorations.append(
                f"               OpDecorate {self._id(struct_id)} Block")
            # Member 0 offset = 0
            self._decorations.append(
                f"               OpMemberDecorate {self._id(struct_id)} 0 Offset 0")

            # Pointer to struct in StorageBuffer
            ptr_struct_id = self._alloc(f"ptr_sb_{arr}")
            self._types.append(
                f"     {self._id(ptr_struct_id)} = OpTypePointer StorageBuffer {self._id(struct_id)}")

            # Variable
            var_id = self._alloc(f"var_{arr}")
            self._globals.append(
                f"     {self._id(var_id)} = OpVariable {self._id(ptr_struct_id)} StorageBuffer")

            # Descriptor set 0, binding N
            self._decorations.append(
                f"               OpDecorate {self._id(var_id)} DescriptorSet 0")
            self._decorations.append(
                f"               OpDecorate {self._id(var_id)} Binding {binding}")

            buf_vars[arr] = var_id
            self._array_elem_types[arr] = arr_type
            binding += 1

        return buf_vars

    def _declare_push_constants(self) -> dict[str, tuple[int, int]]:
        """Declare push constant block for scalar parameters.

        Returns dict: scalar_name -> (member_index, type_id).
        """
        k = self.kernel
        if not k.scalars_read:
            return {}
        # Sort by type: doubles first, then ints. This avoids mixed-type
        # padding mismatches between C struct layout and SPIRV offsets.
        scalars = sorted(k.scalars_read,
                         key=lambda s: (0 if self.var_types.get(s, IRType.REAL) == IRType.REAL else 1, s))
        if not scalars:
            return {}

        # Build struct members
        member_types = []
        member_info: dict[str, tuple[int, int]] = {}
        offset = 0

        # Pre-allocate the struct type ID so decorations and type def
        # reference the same ID.
        self.id_pc_struct = self._alloc("pc_struct")

        for i, s in enumerate(scalars):
            t = self.var_types.get(s, IRType.REAL)
            if t == IRType.REAL:
                type_id = self.id_real
                size = self.real_size
            else:
                type_id = self.id_i32
                size = 4
            member_types.append(type_id)
            member_info[s] = (i, type_id)

            self._decorations.append(
                f"               OpMemberDecorate {self._id(self.id_pc_struct)} {i} Offset {offset}")
            offset += size
            # Align to natural boundary
            if t == IRType.REAL and offset % self.real_size != 0:
                offset += (self.real_size - offset % self.real_size)

        # Ping-pong offsets: add _pp_rd_offset and _pp_wr_offset as i32 push constants
        if self.pingpong_arrays:
            for pp_name in ("_pp_rd_offset", "_pp_wr_offset"):
                idx = len(member_types)
                member_types.append(self.id_i32)
                member_info[pp_name] = (idx, self.id_i32)
                # Align to 4 bytes (i32)
                if offset % 4 != 0:
                    offset += (4 - offset % 4)
                self._decorations.append(
                    f"               OpMemberDecorate {self._id(self.id_pc_struct)} {idx} Offset {offset}")
                offset += 4

        member_str = " ".join(self._id(t) for t in member_types)
        self._types.append(
            f"     {self._id(self.id_pc_struct)} = OpTypeStruct {member_str}")

        # Block decoration
        self._decorations.append(
            f"               OpDecorate {self._id(self.id_pc_struct)} Block")

        # Pointer to PushConstant
        self.id_ptr_pc = self._alloc("ptr_pc")
        self._types.append(
            f"     {self._id(self.id_ptr_pc)} = OpTypePointer PushConstant {self._id(self.id_pc_struct)}")

        # Pointer to member types in PushConstant
        for s in member_info:
            _, type_id = member_info[s]
            ptr_name = f"ptr_pc_{s}"
            if not self._has_name(ptr_name):
                ptr_id = self._alloc(ptr_name)
                self._types.append(
                    f"     {self._id(ptr_id)} = OpTypePointer PushConstant {self._id(type_id)}")

        # Variable
        pc_var = self._alloc("pc_var")
        self._globals.append(
            f"     {self._id(pc_var)} = OpVariable {self._id(self.id_ptr_pc)} PushConstant")

        # Store the variable ID so the function body can access it
        self._named_ids["pc_var"] = pc_var

        return member_info

    def _declare_builtin(self):
        """Declare the gl_GlobalInvocationID input variable."""
        self.id_gl_global_inv = self._alloc("gl_GlobalInvocationID")
        self._globals.append(
            f"     {self._id(self.id_gl_global_inv)} = OpVariable "
            f"{self._id(self.id_ptr_input_v3uint)} Input")
        self._decorations.append(
            f"               OpDecorate {self._id(self.id_gl_global_inv)} "
            f"BuiltIn GlobalInvocationId")

    def _peek_id(self, name: str) -> int:
        """Get an ID that will be allocated later, pre-allocating it now."""
        if name not in self._named_ids:
            self._alloc(name)
        return self._named_ids[name]

    def _has_name(self, name: str) -> bool:
        return name in self._named_ids

    # ── header ─────────────────────────────────────────────

    def _build_header(self, buf_vars: dict[str, int],
                      pc_member_ids: dict[str, tuple[int, int]]):
        """Build the SPIR-V header section."""
        k = self.kernel

        self._header.append("; SPIR-V")
        self._header.append("; Version: 1.3")
        self._header.append(f"; Generator: Ergo")
        self._header.append(f"; Source: line {k.source_line}")
        if k.is_partial:
            self._header.append(f"; SPLIT kernel: flow prefix of loop at line {k.split_from}")
        self._header.append(f"               OpCapability Shader")
        if self.real_size == 8:
            self._header.append(f"               OpCapability Float64")
            self._header.append(f"               OpCapability Int64")

        # Atomic capabilities for scatter kernels
        if k.atomic_arrays:
            for arr in k.atomic_arrays:
                arr_type = self.var_types.get(arr, IRType.REAL)
                if arr_type == IRType.REAL:
                    if self.real_size == 8:
                        self._header.append(
                            f"               OpCapability AtomicFloat64AddEXT")
                    else:
                        self._header.append(
                            f"               OpCapability AtomicFloat32AddEXT")
                    self._header.append(
                        f"               OpExtension \"SPV_EXT_shader_atomic_float_add\"")
                    break

        # GLSL extended instruction set
        if self._needs_glsl_ext:
            glsl_ext = self._alloc("glsl_ext")
            self._header.append(
                f"     {self._id(glsl_ext)} = OpExtInstImport \"GLSL.std.450\"")

        self._header.append(f"               OpMemoryModel Logical GLSL450")

        # Entry point — only Input/Output variables in the interface
        # (StorageBuffer and PushConstant are NOT listed here in SPIR-V ≤ 1.3)
        interface_ids = [self._id(self.id_gl_global_inv)]

        main_id = self._peek_id("main")
        iface_str = " ".join(interface_ids)
        self._header.append(
            f"               OpEntryPoint GLCompute {self._id(main_id)} \"main\" {iface_str}")
        self._header.append(
            f"               OpExecutionMode {self._id(main_id)} LocalSize {self.WORKGROUP_SIZE} 1 1")

    # ── function body ──────────────────────────────────────

    def _emit_function(self, buf_vars: dict[str, int],
                       pc_member_ids: dict[str, tuple[int, int]]):
        """Emit the compute kernel function."""
        k = self.kernel
        main_id = self._named_ids["main"]

        self._function.append(
            f"     {self._id(main_id)} = OpFunction {self._id(self.id_void)} None {self._id(self.id_func_void)}")

        entry_label = self._alloc("entry")
        self._function.append(f"     {self._id(entry_label)} = OpLabel")
        self._current_block = entry_label

        # Load GlobalInvocationID
        gid_vec = self._alloc()
        self._function.append(
            f"         {self._id(gid_vec)} = OpLoad {self._id(self.id_v3uint)} {self._id(self.id_gl_global_inv)}")

        # Extract .x component (u32)
        gid_x = self._alloc()
        self._function.append(
            f"         {self._id(gid_x)} = OpCompositeExtract {self._id(self.id_u32)} {self._id(gid_vec)} 0")

        # Ergo is 1-based: i = gid + 1 (but gid is u32, loop var is i32)
        # Convert gid to i32 first
        gid_i32 = self._alloc()
        self._function.append(
            f"         {self._id(gid_i32)} = OpBitcast {self._id(self.id_i32)} {self._id(gid_x)}")
        self._set_ssa_type(gid_i32, self.id_i32)

        const_1 = self._get_const(IRType.INTEGER, 1)
        i_val = self._alloc("i_val")
        self._function.append(
            f"         {self._id(i_val)} = OpIAdd {self._id(self.id_i32)} {self._id(gid_i32)} {self._id(const_1)}")
        self._set_ssa_type(i_val, self.id_i32)

        # Bounds check: i <= N
        bound_id = self._load_bound(k.loop_bound, pc_member_ids)

        in_bounds = self._alloc()
        self._function.append(
            f"         {self._id(in_bounds)} = OpSLessThanEqual {self._id(self.id_bool)} {self._id(i_val)} {self._id(bound_id)}")

        body_label = self._alloc("body")
        exit_label = self._alloc("exit")
        self._function.append(
            f"               OpSelectionMerge {self._id(exit_label)} None")
        self._function.append(
            f"               OpBranchConditional {self._id(in_bounds)} {self._id(body_label)} {self._id(exit_label)}")

        # Body
        self._function.append(f"     {self._id(body_label)} = OpLabel")
        self._current_block = body_label

        # 0-based index for array access
        const_1_again = const_1
        idx_0 = self._alloc("idx_0")
        self._function.append(
            f"         {self._id(idx_0)} = OpISub {self._id(self.id_i32)} {self._id(i_val)} {self._id(const_1_again)}")
        self._set_ssa_type(idx_0, self.id_i32)

        # Convert idx_0 to u32 for array indexing (OpAccessChain needs unsigned)
        # Actually SPIR-V AccessChain can use signed — but we cast to be safe
        # since the runtime array index type is typically u32.
        # We'll keep i32 and cast when needed for OpAccessChain.

        # SSA map: Ergo variable name -> SPIR-V ID
        ssa_map: dict[str, int] = {}
        ssa_map[k.loop_var] = i_val

        self._emit_body(k.loop.body, buf_vars, pc_member_ids, ssa_map, idx_0)

        self._function.append(f"               OpBranch {self._id(exit_label)}")

        # Exit
        self._function.append(f"     {self._id(exit_label)} = OpLabel")
        self._function.append(f"               OpReturn")
        self._function.append(f"               OpFunctionEnd")

    def _load_bound(self, bound: Operand,
                    pc_member_ids: dict[str, tuple[int, int]]) -> int:
        """Load the loop bound value, from push constants or as a constant."""
        if isinstance(bound, IRConst):
            if self.var_types.get(str(bound.value)) == IRType.REAL:
                return self._get_const(IRType.INTEGER, int(bound.value))
            return self._get_const(IRType.INTEGER, int(bound.value))

        if isinstance(bound, IRRef):
            if bound.name in pc_member_ids:
                # Load from push constant
                member_idx, type_id = pc_member_ids[bound.name]
                return self._load_push_constant(member_idx, type_id, bound.name)
            # It's a known constant — look up its value
            return self._get_const(IRType.INTEGER, 0)

        return self._get_const(IRType.INTEGER, 0)

    def _load_pc_member(self, name: str, pc_member_ids: dict) -> int:
        """Load a push constant member by name. Returns the SPIR-V value ID."""
        member_idx, type_id = pc_member_ids[name]
        return self._load_push_constant(member_idx, type_id, name)

    def _load_push_constant(self, member_idx: int, type_id: int,
                            name: str) -> int:
        """Emit OpAccessChain + OpLoad for a push constant member."""
        pc_var = self._named_ids["pc_var"]
        idx_const = self._get_const(IRType.INTEGER, member_idx)

        ptr_type_name = f"ptr_pc_{name}"
        ptr_type_id = self._named_ids[ptr_type_name]

        ptr = self._alloc()
        self._function.append(
            f"         {self._id(ptr)} = OpAccessChain {self._id(ptr_type_id)} "
            f"{self._id(pc_var)} {self._id(idx_const)}")

        val = self._alloc()
        self._function.append(
            f"         {self._id(val)} = OpLoad {self._id(type_id)} {self._id(ptr)}")
        self._set_ssa_type(val, type_id)

        return val

    # ── body emission ──────────────────────────────────────

    def _emit_body(self, items: list, buf_vars: dict[str, int],
                   pc_member_ids: dict[str, tuple[int, int]],
                   ssa_map: dict[str, int], idx_0: int) -> bool:
        """Emit SPIR-V for a list of IR body items.

        Returns True if the body ended with a block terminator (OpReturn).
        """
        # Track cycle guard merge labels that need closing
        pending_merges: list[int] = []

        for item in items:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    terminated = self._emit_inst(inst, buf_vars, pc_member_ids,
                                                 ssa_map, idx_0)
                    if terminated:
                        # Close any pending cycle guard merges
                        for m in reversed(pending_merges):
                            self._function.append(
                                f"               OpBranch {self._id(m)}")
                            self._function.append(
                                f"     {self._id(m)} = OpLabel")
                            self._current_block = m
                        return True
            elif isinstance(item, IRIf):
                self._cycle_guard_merge = None
                self._emit_if(item, buf_vars, pc_member_ids, ssa_map, idx_0)
                if self._cycle_guard_merge is not None:
                    # A cycle guard was opened — remaining items go inside
                    # the then-block. Record the merge label to close later.
                    pending_merges.append(self._cycle_guard_merge)
                    self._cycle_guard_merge = None

        # Close all pending cycle guard merges
        for m in reversed(pending_merges):
            self._function.append(f"               OpBranch {self._id(m)}")
            self._function.append(f"     {self._id(m)} = OpLabel")
            self._current_block = m

        return False

    def _emit_inst(self, inst: IRInst, buf_vars: dict[str, int],
                   pc_member_ids: dict[str, tuple[int, int]],
                   ssa_map: dict[str, int], idx_0: int) -> bool:
        """Emit a single IR instruction as SPIR-V.

        Returns True if the instruction terminated the block (e.g. OpReturn).
        """
        op = inst.op

        # SUB for index computation (i - 1) -> reuse idx_0
        if op == Op.SUB and inst.result and inst.result.startswith("_idx"):
            ssa_map[inst.result] = idx_0
            return False

        # LOAD from array
        if op == Op.LOAD:
            arr = inst.meta.get("array", "")
            var_id = buf_vars.get(arr)
            if var_id is None:
                self._function.append(f"         ; WARNING: unknown array '{arr}'")
                return False
            idx = self._linearize_index(arr, inst.args, pc_member_ids, ssa_map)

            # Ping-pong: add read offset for read-write arrays
            if arr in self.pingpong_arrays and "_pp_rd_offset" in pc_member_ids:
                pp_rd = self._load_pc_member("_pp_rd_offset", pc_member_ids)
                new_idx = self._alloc()
                self._function.append(
                    f"         {self._id(new_idx)} = OpIAdd {self._id(self.id_i32)} "
                    f"{self._id(idx)} {self._id(pp_rd)}")
                self._set_ssa_type(new_idx, self.id_i32)
                idx = new_idx

            arr_elem = self._array_elem_types.get(arr, IRType.REAL)
            if arr_elem == IRType.INTEGER or arr_elem == IRType.LOGICAL:
                ptr_type = self.id_ptr_sb_i32
                elem_type = self.id_i32
            else:
                ptr_type = self.id_ptr_sb_real
                elem_type = self.id_real

            const_0 = self._get_u32_const(0)
            ptr = self._alloc()
            self._function.append(
                f"         {self._id(ptr)} = OpAccessChain {self._id(ptr_type)} "
                f"{self._id(var_id)} {self._id(const_0)} {self._id(idx)}")
            result = self._alloc()
            self._function.append(
                f"         {self._id(result)} = OpLoad {self._id(elem_type)} {self._id(ptr)}")
            self._set_ssa_type(result, elem_type)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # STORE to array
        if op == Op.STORE:
            arr = inst.meta.get("array", "")
            var_id = buf_vars.get(arr)
            if var_id is None:
                self._function.append(f"         ; WARNING: unknown array '{arr}'")
                return False
            val = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            idx = self._linearize_index(arr, inst.args[1:], pc_member_ids, ssa_map)

            # Ping-pong: add write offset for read-write arrays
            if arr in self.pingpong_arrays and "_pp_wr_offset" in pc_member_ids:
                pp_wr = self._load_pc_member("_pp_wr_offset", pc_member_ids)
                new_idx = self._alloc()
                self._function.append(
                    f"         {self._id(new_idx)} = OpIAdd {self._id(self.id_i32)} "
                    f"{self._id(idx)} {self._id(pp_wr)}")
                self._set_ssa_type(new_idx, self.id_i32)
                idx = new_idx

            arr_elem = self._array_elem_types.get(arr, IRType.REAL)
            if arr_elem == IRType.INTEGER or arr_elem == IRType.LOGICAL:
                ptr_type = self.id_ptr_sb_i32
            else:
                ptr_type = self.id_ptr_sb_real

            const_0 = self._get_u32_const(0)
            ptr = self._alloc()
            self._function.append(
                f"         {self._id(ptr)} = OpAccessChain {self._id(ptr_type)} "
                f"{self._id(var_id)} {self._id(const_0)} {self._id(idx)}")

            # Atomic store for scatter arrays
            if arr in self.kernel.atomic_arrays:
                # The value being stored is the result of a read-modify-write.
                # For atomicAdd: val = load + delta → emit atomicAdd(ptr, delta)
                # For atomicOr:  val = load | mask  → emit atomicOr(ptr, mask)
                # We detect the pattern from the preceding instruction.
                atomic_op, atomic_arg = self._detect_atomic_pattern(
                    inst, ssa_map, pc_member_ids)
                if atomic_op == "add":
                    if arr_elem == IRType.REAL:
                        # OpAtomicFAddEXT (VK_EXT_shader_atomic_float)
                        # Scope=Device(1), Semantics=None(0)
                        scope = self._get_u32_const(1)
                        sem = self._get_u32_const(0)
                        result = self._alloc()
                        self._function.append(
                            f"         {self._id(result)} = OpAtomicFAddEXT "
                            f"{self._id(self.id_real)} {self._id(ptr)} "
                            f"{self._id(scope)} {self._id(sem)} {self._id(atomic_arg)}")
                    else:
                        scope = self._get_u32_const(1)
                        sem = self._get_u32_const(0)
                        result = self._alloc()
                        self._function.append(
                            f"         {self._id(result)} = OpAtomicIAdd "
                            f"{self._id(self.id_i32)} {self._id(ptr)} "
                            f"{self._id(scope)} {self._id(sem)} {self._id(atomic_arg)}")
                elif atomic_op == "or":
                    scope = self._get_u32_const(1)
                    sem = self._get_u32_const(0)
                    result = self._alloc()
                    self._function.append(
                        f"         {self._id(result)} = OpAtomicOr "
                        f"{self._id(self.id_i32)} {self._id(ptr)} "
                        f"{self._id(scope)} {self._id(sem)} {self._id(atomic_arg)}")
                else:
                    # Fallback: regular store (shouldn't happen for scatter)
                    self._function.append(
                        f"               OpStore {self._id(ptr)} {self._id(val)}")
            else:
                self._function.append(
                    f"               OpStore {self._id(ptr)} {self._id(val)}")
            return False

        # Arithmetic binary ops
        if op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV):
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            b = self._resolve(inst.args[1], pc_member_ids, ssa_map)

            # Determine if this is float or int arithmetic using SSA types
            a_fp = self._is_real_id(a)
            b_fp = self._is_real_id(b)
            is_fp = a_fp or b_fp or inst.type == IRType.REAL

            if is_fp:
                # Ensure both operands are f64
                if not a_fp:
                    a = self._ensure_f64(a)
                if not b_fp:
                    b = self._ensure_f64(b)
                spv_op = {Op.ADD: "OpFAdd", Op.SUB: "OpFSub",
                          Op.MUL: "OpFMul", Op.DIV: "OpFDiv"}[op]
                result = self._alloc()
                self._function.append(
                    f"         {self._id(result)} = {spv_op} {self._id(self.id_real)} {self._id(a)} {self._id(b)}")
                self._set_ssa_type(result, self.id_real)
            else:
                spv_op = {Op.ADD: "OpIAdd", Op.SUB: "OpISub",
                          Op.MUL: "OpIMul", Op.DIV: "OpSDiv"}[op]
                result = self._alloc()
                self._function.append(
                    f"         {self._id(result)} = {spv_op} {self._id(self.id_i32)} {self._id(a)} {self._id(b)}")
                self._set_ssa_type(result, self.id_i32)

            if inst.result:
                ssa_map[inst.result] = result
            return False

        # NEG
        if op == Op.NEG:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            result = self._alloc()
            if self._is_real_id(a):
                self._function.append(
                    f"         {self._id(result)} = OpFNegate {self._id(self.id_real)} {self._id(a)}")
                self._set_ssa_type(result, self.id_real)
            else:
                self._function.append(
                    f"         {self._id(result)} = OpSNegate {self._id(self.id_i32)} {self._id(a)}")
                self._set_ssa_type(result, self.id_i32)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # MOD
        if op == Op.MOD:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            b = self._resolve(inst.args[1], pc_member_ids, ssa_map)
            is_fp = self._is_real_id(a) or self._is_real_id(b)
            result = self._alloc()
            if is_fp:
                a = self._ensure_f64(a)
                b = self._ensure_f64(b)
                self._function.append(
                    f"         {self._id(result)} = OpFRem {self._id(self.id_real)} {self._id(a)} {self._id(b)}")
                self._set_ssa_type(result, self.id_real)
            else:
                self._function.append(
                    f"         {self._id(result)} = OpSRem {self._id(self.id_i32)} {self._id(a)} {self._id(b)}")
                self._set_ssa_type(result, self.id_i32)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # POW — via GLSL.std.450 Pow (f32 cast required)
        if op == Op.POW:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            b = self._resolve(inst.args[1], pc_member_ids, ssa_map)
            glsl = self._named_ids["glsl_ext"]
            # Ensure both operands are REAL first (may be int constants)
            a = self._ensure_f64(a)
            b = self._ensure_f64(b)
            if self.real_size == 4:
                # f32: call GLSL.std.450 directly
                result = self._alloc()
                self._function.append(
                    f"         {self._id(result)} = OpExtInst {self._id(self.id_f32)} "
                    f"{self._id(glsl)} Pow {self._id(a)} {self._id(b)}")
            else:
                # f64: cast to f32, call, cast back
                a32 = self._alloc()
                self._function.append(
                    f"         {self._id(a32)} = OpFConvert {self._id(self.id_f32)} {self._id(a)}")
                b32 = self._alloc()
                self._function.append(
                    f"         {self._id(b32)} = OpFConvert {self._id(self.id_f32)} {self._id(b)}")
                r32 = self._alloc()
                self._function.append(
                    f"         {self._id(r32)} = OpExtInst {self._id(self.id_f32)} "
                    f"{self._id(glsl)} Pow {self._id(a32)} {self._id(b32)}")
                result = self._alloc()
                self._function.append(
                    f"         {self._id(result)} = OpFConvert {self._id(self.id_f64)} {self._id(r32)}")
            self._set_ssa_type(result, self.id_real)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # Relational ops
        if op in (Op.LT, Op.GT, Op.EQ, Op.NE, Op.LE, Op.GE):
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            b = self._resolve(inst.args[1], pc_member_ids, ssa_map)
            is_fp = self._is_real_id(a) or self._is_real_id(b)

            # Ensure matching types for comparison
            if is_fp:
                a = self._ensure_f64(a)
                b = self._ensure_f64(b)

            result = self._alloc()

            if is_fp:
                spv_cmp = {
                    Op.LT: "OpFOrdLessThan",
                    Op.GT: "OpFOrdGreaterThan",
                    Op.EQ: "OpFOrdEqual",
                    Op.NE: "OpFUnordNotEqual",
                    Op.LE: "OpFOrdLessThanEqual",
                    Op.GE: "OpFOrdGreaterThanEqual",
                }[op]
            else:
                spv_cmp = {
                    Op.LT: "OpSLessThan",
                    Op.GT: "OpSGreaterThan",
                    Op.EQ: "OpIEqual",
                    Op.NE: "OpINotEqual",
                    Op.LE: "OpSLessThanEqual",
                    Op.GE: "OpSGreaterThanEqual",
                }[op]

            self._function.append(
                f"         {self._id(result)} = {spv_cmp} {self._id(self.id_bool)} {self._id(a)} {self._id(b)}")
            self._set_ssa_type(result, self.id_bool)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # Math intrinsics via GLSL.std.450
        if op in GLSL_EXT and op not in (Op.POW, Op.MAX, Op.MIN):
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            glsl = self._named_ids["glsl_ext"]

            if op in GLSL_F32_ONLY and self.real_size == 8:
                # Transcendentals at f64: cast f64 -> f32, apply, cast f32 -> f64
                a32 = self._alloc()
                self._function.append(
                    f"         {self._id(a32)} = OpFConvert {self._id(self.id_f32)} {self._id(a)}")
                r32 = self._alloc()
                self._function.append(
                    f"         {self._id(r32)} = OpExtInst {self._id(self.id_f32)} "
                    f"{self._id(glsl)} {GLSL_EXT[op]} {self._id(a32)}")
                result = self._alloc()
                self._function.append(
                    f"         {self._id(result)} = OpFConvert {self._id(self.id_f64)} {self._id(r32)}")
            else:
                # f32 or non-transcendentals: call directly on REAL type
                result = self._alloc()
                self._function.append(
                    f"         {self._id(result)} = OpExtInst {self._id(self.id_real)} "
                    f"{self._id(glsl)} {GLSL_EXT[op]} {self._id(a)}")

            self._set_ssa_type(result, self.id_real)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # LOG10 — computed as Log(x) / Log(10)
        if op == Op.LOG10:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            glsl = self._named_ids["glsl_ext"]
            if self.real_size == 4:
                # f32: call Log directly
                log_a = self._alloc()
                self._function.append(
                    f"         {self._id(log_a)} = OpExtInst {self._id(self.id_f32)} "
                    f"{self._id(glsl)} Log {self._id(a)}")
            else:
                # f64: cast to f32 for Log, cast back
                a32 = self._alloc()
                self._function.append(
                    f"         {self._id(a32)} = OpFConvert {self._id(self.id_f32)} {self._id(a)}")
                log_a32 = self._alloc()
                self._function.append(
                    f"         {self._id(log_a32)} = OpExtInst {self._id(self.id_f32)} "
                    f"{self._id(glsl)} Log {self._id(a32)}")
                log_a = self._alloc()
                self._function.append(
                    f"         {self._id(log_a)} = OpFConvert {self._id(self.id_f64)} {self._id(log_a32)}")
            log_10 = self._get_const(IRType.REAL, 2.302585092994046)  # ln(10)
            result = self._alloc()
            self._function.append(
                f"         {self._id(result)} = OpFDiv {self._id(self.id_real)} {self._id(log_a)} {self._id(log_10)}")
            self._set_ssa_type(result, self.id_real)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # MAX / MIN — GLSL.std.450 FMax / FMin (f64 supported)
        if op in (Op.MAX, Op.MIN):
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            b = self._resolve(inst.args[1], pc_member_ids, ssa_map)
            a = self._ensure_f64(a)
            b = self._ensure_f64(b)
            result = self._alloc()
            glsl = self._named_ids["glsl_ext"]
            self._function.append(
                f"         {self._id(result)} = OpExtInst {self._id(self.id_real)} "
                f"{self._id(glsl)} {GLSL_EXT[op]} {self._id(a)} {self._id(b)}")
            self._set_ssa_type(result, self.id_real)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # CLAMP — GLSL.std.450 FClamp or SClamp
        if op == Op.CLAMP:
            x = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            lo = self._resolve(inst.args[1], pc_member_ids, ssa_map)
            hi = self._resolve(inst.args[2], pc_member_ids, ssa_map)
            # Use integer clamp if all operands are integer
            if self._is_int_id(x) and self._is_int_id(lo) and self._is_int_id(hi):
                result = self._alloc()
                glsl = self._named_ids["glsl_ext"]
                self._function.append(
                    f"         {self._id(result)} = OpExtInst {self._id(self.id_i32)} "
                    f"{self._id(glsl)} SClamp {self._id(x)} {self._id(lo)} {self._id(hi)}")
                self._set_ssa_type(result, self.id_i32)
            else:
                x = self._ensure_f64(x)
                lo = self._ensure_f64(lo)
                hi = self._ensure_f64(hi)
                result = self._alloc()
                glsl = self._named_ids["glsl_ext"]
                self._function.append(
                    f"         {self._id(result)} = OpExtInst {self._id(self.id_real)} "
                    f"{self._id(glsl)} FClamp {self._id(x)} {self._id(lo)} {self._id(hi)}")
                self._set_ssa_type(result, self.id_real)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # Type conversion
        if op == Op.TO_REAL:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            if self._is_real_id(a):
                # Already f64 — skip conversion (can happen when POW
                # promotes integer expressions to f64 at SPIR-V level)
                if inst.result:
                    ssa_map[inst.result] = a
                return False
            result = self._alloc()
            self._function.append(
                f"         {self._id(result)} = OpConvertSToF {self._id(self.id_real)} {self._id(a)}")
            self._set_ssa_type(result, self.id_real)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        if op == Op.TO_INT:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            if self._is_int_id(a):
                # Already i32
                if inst.result:
                    ssa_map[inst.result] = a
                return False
            result = self._alloc()
            self._function.append(
                f"         {self._id(result)} = OpConvertFToS {self._id(self.id_i32)} {self._id(a)}")
            self._set_ssa_type(result, self.id_i32)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # Logical AND/OR/NOT
        if op == Op.AND:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            b = self._resolve(inst.args[1], pc_member_ids, ssa_map)
            result = self._alloc()
            self._function.append(
                f"         {self._id(result)} = OpLogicalAnd {self._id(self.id_bool)} {self._id(a)} {self._id(b)}")
            self._set_ssa_type(result, self.id_bool)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        if op == Op.OR:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            b = self._resolve(inst.args[1], pc_member_ids, ssa_map)
            result = self._alloc()
            self._function.append(
                f"         {self._id(result)} = OpLogicalOr {self._id(self.id_bool)} {self._id(a)} {self._id(b)}")
            self._set_ssa_type(result, self.id_bool)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        if op == Op.NOT:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            result = self._alloc()
            self._function.append(
                f"         {self._id(result)} = OpLogicalNot {self._id(self.id_bool)} {self._id(a)}")
            self._set_ssa_type(result, self.id_bool)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # COPY — scalar assignment or CYCLE
        if op == Op.COPY:
            if inst.meta.get("kind") == "cycle":
                # CYCLE in kernel = early exit for this thread.
                # OpReturn terminates the function for this invocation.
                # The caller (_emit_body) stops emitting after this.
                self._function.append(
                    f"               OpReturn")
                return True
            if inst.result and inst.args:
                val = self._resolve(inst.args[0], pc_member_ids, ssa_map)
                ssa_map[inst.result] = val
            return False

        # Bitwise AND (IAND)
        if op == Op.IAND:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            b = self._resolve(inst.args[1], pc_member_ids, ssa_map)
            # Ensure both are integer
            if self._is_real_id(a):
                a = self._ensure_i32(a)
            if self._is_real_id(b):
                b = self._ensure_i32(b)
            result = self._alloc()
            self._function.append(
                f"         {self._id(result)} = OpBitwiseAnd {self._id(self.id_i32)} {self._id(a)} {self._id(b)}")
            self._set_ssa_type(result, self.id_i32)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # Bitwise OR (IOR)
        if op == Op.IOR:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            b = self._resolve(inst.args[1], pc_member_ids, ssa_map)
            if self._is_real_id(a):
                a = self._ensure_i32(a)
            if self._is_real_id(b):
                b = self._ensure_i32(b)
            result = self._alloc()
            self._function.append(
                f"         {self._id(result)} = OpBitwiseOr {self._id(self.id_i32)} {self._id(a)} {self._id(b)}")
            self._set_ssa_type(result, self.id_i32)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # ZERO — zero an array element at the current thread index
        if op == Op.ZERO:
            arr = inst.meta.get("array", "")
            var_id = buf_vars.get(arr)
            if var_id is None:
                self._function.append(f"         ; WARNING: ZERO unknown array '{arr}'")
                return False
            arr_elem = self._array_elem_types.get(arr, IRType.REAL)
            if arr_elem == IRType.INTEGER or arr_elem == IRType.LOGICAL:
                ptr_type = self.id_ptr_sb_i32
                zero_val = self._get_const(IRType.INTEGER, 0)
            else:
                ptr_type = self.id_ptr_sb_real
                zero_val = self._get_const(IRType.REAL, 0.0)
            const_0 = self._get_u32_const(0)
            ptr = self._alloc()
            self._function.append(
                f"         {self._id(ptr)} = OpAccessChain {self._id(ptr_type)} "
                f"{self._id(var_id)} {self._id(const_0)} {self._id(idx_0)}")
            self._function.append(
                f"               OpStore {self._id(ptr)} {self._id(zero_val)}")
            return False

        # BITNOT — bitwise NOT
        if op == Op.BITNOT:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            if self._is_real_id(a):
                a = self._ensure_i32(a)
            result = self._alloc()
            self._function.append(
                f"         {self._id(result)} = OpNot "
                f"{self._id(self.id_i32)} {self._id(a)}")
            self._set_ssa_type(result, self.id_i32)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # ISHFT — bit shift (positive = left, negative = right)
        if op == Op.ISHFT:
            a = self._resolve(inst.args[0], pc_member_ids, ssa_map)
            b_operand = inst.args[1]
            # Check for constant shift amount to select left vs right
            const_shift = None
            if hasattr(b_operand, 'value') and hasattr(b_operand, 'type'):
                if b_operand.type == IRType.INTEGER:
                    const_shift = b_operand.value
            result = self._alloc()
            if const_shift is not None and const_shift < 0:
                # Constant negative shift → logical right shift
                neg_b = self._get_const(IRType.INTEGER, -const_shift)
                self._function.append(
                    f"         {self._id(result)} = OpShiftRightLogical "
                    f"{self._id(self.id_i32)} {self._id(a)} {self._id(neg_b)}")
            else:
                # Positive or variable shift → left shift
                b = self._resolve(b_operand, pc_member_ids, ssa_map)
                if self._is_real_id(a):
                    a = self._ensure_i32(a)
                if self._is_real_id(b):
                    b = self._ensure_i32(b)
                self._function.append(
                    f"         {self._id(result)} = OpShiftLeftLogical "
                    f"{self._id(self.id_i32)} {self._id(a)} {self._id(b)}")
            self._set_ssa_type(result, self.id_i32)
            if inst.result:
                ssa_map[inst.result] = result
            return False

        # Fallback
        self._function.append(f"         ; unhandled op: {op.value}")
        return False

    def _is_cycle_guard(self, node: IRIf) -> bool:
        """Check if an IF is a guard pattern: IF cond THEN CYCLE (no else).

        This is the pattern 'IF CALIVE(I) != 1 THEN CYCLE' which guards
        the rest of the kernel body. Instead of emitting OpReturn inside
        a selection (which causes SSA domination issues), we invert it
        to wrap the remaining body in the negated condition.
        """
        if node.else_body:
            return False
        if len(node.then_body) != 1:
            return False
        item = node.then_body[0]
        if not isinstance(item, IRBlock):
            return False
        if len(item.insts) != 1:
            return False
        return (item.insts[0].op == Op.COPY and
                item.insts[0].meta.get("kind") == "cycle")

    def _emit_if(self, node: IRIf, buf_vars: dict[str, int],
                 pc_member_ids: dict[str, tuple[int, int]],
                 ssa_map: dict[str, int], idx_0: int):
        """Emit SPIR-V for an IF inside the kernel."""

        # Detect CYCLE guard pattern and convert to inverted wrapping IF.
        # This avoids OpReturn inside structured control flow.
        if self._is_cycle_guard(node):
            cond = self._resolve(node.condition, pc_member_ids, ssa_map)
            # Invert: if (cond) skip -> if (!cond) continue
            inv_cond = self._alloc()
            self._function.append(
                f"         {self._id(inv_cond)} = OpLogicalNot {self._id(self.id_bool)} {self._id(cond)}")
            self._set_ssa_type(inv_cond, self.id_bool)

            then_label = self._alloc()
            merge_label = self._alloc()

            self._function.append(
                f"               OpSelectionMerge {self._id(merge_label)} None")
            self._function.append(
                f"               OpBranchConditional {self._id(inv_cond)} "
                f"{self._id(then_label)} {self._id(merge_label)}")

            self._function.append(f"     {self._id(then_label)} = OpLabel")
            self._current_block = then_label
            # The remaining body items after this IF will be emitted
            # by the caller inside this then-block. We signal this by
            # storing the merge label so the caller can close it.
            self._cycle_guard_merge = merge_label
            return

        cond = self._resolve(node.condition, pc_member_ids, ssa_map)

        then_label = self._alloc()
        merge_label = self._alloc()
        else_label = self._alloc() if node.else_body else merge_label

        # Remember the block we branched from (for OpPhi fallthrough)
        pre_if_block = self._current_block

        self._function.append(
            f"               OpSelectionMerge {self._id(merge_label)} None")
        self._function.append(
            f"               OpBranchConditional {self._id(cond)} "
            f"{self._id(then_label)} {self._id(else_label)}")

        # Use a COPY of ssa_map for each branch so that SSA values
        # defined inside one branch don't leak to the merge block or
        # subsequent code. This prevents domination violations in SPIR-V.
        # After both branches, we emit OpPhi to merge any changed scalars.
        self._function.append(f"     {self._id(then_label)} = OpLabel")
        self._current_block = then_label
        then_map = dict(ssa_map)
        then_term = self._emit_body(node.then_body, buf_vars, pc_member_ids, then_map, idx_0)
        then_exit_block = self._current_block
        if not then_term:
            self._function.append(f"               OpBranch {self._id(merge_label)}")

        if node.else_body:
            self._function.append(f"     {self._id(else_label)} = OpLabel")
            self._current_block = else_label
            else_map = dict(ssa_map)
            else_term = self._emit_body(node.else_body, buf_vars, pc_member_ids,
                                        else_map, idx_0)
            else_exit_block = self._current_block
            if not else_term:
                self._function.append(
                    f"               OpBranch {self._id(merge_label)}")
        else:
            else_map = ssa_map
            else_exit_block = pre_if_block
            else_term = False

        self._function.append(f"     {self._id(merge_label)} = OpLabel")
        self._current_block = merge_label

        # Emit OpPhi for scalars that were modified in either branch.
        # This makes values computed inside IF branches available after
        # the merge point (e.g. WEK from IF/ELSE Nernst computation).
        if not then_term or not else_term:
            # Collect all scalars that differ between branches or from parent
            changed = set()
            for name in then_map:
                if then_map[name] != ssa_map.get(name):
                    changed.add(name)
            for name in else_map:
                if else_map[name] != ssa_map.get(name):
                    changed.add(name)

            for name in sorted(changed):
                then_val = then_map.get(name)
                else_val = else_map.get(name)
                if then_val is None or else_val is None:
                    continue

                # Determine the type from whichever branch produced a value
                val_for_type = then_val if then_val != ssa_map.get(name) else else_val
                type_id = self._ssa_types.get(val_for_type)
                if type_id is None:
                    continue

                phi_id = self._alloc()
                self._set_ssa_type(phi_id, type_id)

                # Build OpPhi operands: value/predecessor pairs
                # for each reachable branch
                phi_args = ""
                if not then_term:
                    phi_args += f" {self._id(then_val)} {self._id(then_exit_block)}"
                if not else_term:
                    phi_args += f" {self._id(else_val)} {self._id(else_exit_block)}"

                self._function.append(
                    f"         {self._id(phi_id)} = OpPhi {self._id(type_id)}{phi_args}")
                ssa_map[name] = phi_id

    # ── operand resolution ──────────────────────────────────

    def _resolve(self, op: Operand,
                 pc_member_ids: dict[str, tuple[int, int]],
                 ssa_map: dict[str, int]) -> int:
        """Resolve an IR operand to a SPIR-V ID."""
        if isinstance(op, IRConst):
            return self._get_const(op.type, op.value)

        if isinstance(op, IRRef):
            if op.name in ssa_map:
                return ssa_map[op.name]
            # Try push constants
            if op.name in pc_member_ids:
                member_idx, type_id = pc_member_ids[op.name]
                val_id = self._load_push_constant(member_idx, type_id, op.name)
                ssa_map[op.name] = val_id
                return val_id
            # Unknown — emit warning
            self._function.append(f"         ; WARNING: unresolved ref '{op.name}'")
            return self._get_const(IRType.REAL, 0.0)

        return self._get_const(IRType.INTEGER, 0)

    def _set_ssa_type(self, result_id: int, type_id: int):
        """Record the SPIR-V type of a result ID."""
        self._ssa_types[result_id] = type_id

    def _is_real_id(self, val_id: int) -> bool:
        """Check if a SPIR-V ID has float type (f64 or f32)."""
        t = self._ssa_types.get(val_id)
        return t == self.id_f64 or t == self.id_f32

    def _is_int_id(self, val_id: int) -> bool:
        """Check if a SPIR-V ID has integer type (i32 or u32)."""
        t = self._ssa_types.get(val_id)
        return t == self.id_i32 or t == self.id_u32

    def _ensure_f64(self, val_id: int) -> int:
        """If the value is integer, convert to REAL (f32 or f64 per precision)."""
        if self._is_int_id(val_id):
            conv = self._alloc()
            self._function.append(
                f"         {self._id(conv)} = OpConvertSToF {self._id(self.id_real)} {self._id(val_id)}")
            self._set_ssa_type(conv, self.id_real)
            return conv
        return val_id

    def _ensure_i32(self, val_id: int) -> int:
        """If the value is float, convert to i32. Returns the i32 ID."""
        if self._is_real_id(val_id):
            conv = self._alloc()
            self._function.append(
                f"         {self._id(conv)} = OpConvertFToS {self._id(self.id_i32)} {self._id(val_id)}")
            self._set_ssa_type(conv, self.id_i32)
            return conv
        return val_id

    def _is_real(self, op: Operand) -> bool:
        if isinstance(op, IRConst):
            return op.type == IRType.REAL
        if isinstance(op, IRRef):
            t = self.var_types.get(op.name, op.type)
            return t == IRType.REAL
        return False

    def _linearize_index(self, arr: str, index_args: list,
                         pc_member_ids: dict, ssa_map: dict) -> int:
        """Linearize multi-dimensional array index to 1D.

        For 1D: returns the single index directly.
        For 3D (i, j, k): returns (k-1)*dim1*dim0 + (j-1)*dim0 + (i-1)
        where dims are from array shape (column-major, Fortran order).
        """
        if len(index_args) == 1:
            return self._resolve(index_args[0], pc_member_ids, ssa_map)

        shape = self.array_shapes.get(arr, ())
        ndims = len(index_args)

        # Resolve all indices
        indices = []
        for arg in index_args:
            idx = self._resolve(arg, pc_member_ids, ssa_map)
            indices.append(idx)

        # Convert each index from 1-based to 0-based (ensure i32)
        const_1 = self._get_const(IRType.INTEGER, 1)
        zero_based = []
        for idx in indices:
            # Ensure index is i32 (may be f64 from FClamp)
            idx = self._ensure_i32(idx)
            zb = self._alloc()
            self._function.append(
                f"         {self._id(zb)} = OpISub {self._id(self.id_i32)} "
                f"{self._id(idx)} {self._id(const_1)}")
            self._set_ssa_type(zb, self.id_i32)
            zero_based.append(zb)

        # Linearize: column-major (Fortran order)
        # linear = i0 + dim0*(i1 + dim1*i2)
        result = zero_based[0]
        stride = 1
        for d in range(1, ndims):
            dim_size = shape[d - 1] if d - 1 < len(shape) else 32
            if isinstance(dim_size, str):
                # PARAMETER name — resolve via push constants
                dim_id = self._resolve(IRRef(dim_size, IRType.INTEGER),
                                       pc_member_ids, ssa_map)
            else:
                dim_id = self._get_const(IRType.INTEGER, int(dim_size))

            # stride *= dim_size (accumulated)
            scaled = self._alloc()
            self._function.append(
                f"         {self._id(scaled)} = OpIMul {self._id(self.id_i32)} "
                f"{self._id(zero_based[d])} {self._id(dim_id)}")
            self._set_ssa_type(scaled, self.id_i32)

            # For 3D: also multiply by earlier dims
            if d >= 2:
                for dd in range(d - 1):
                    prev_dim = shape[dd] if dd < len(shape) else 32
                    if isinstance(prev_dim, str):
                        pd_id = self._resolve(IRRef(prev_dim, IRType.INTEGER),
                                              pc_member_ids, ssa_map)
                    else:
                        pd_id = self._get_const(IRType.INTEGER, int(prev_dim))
                    new_scaled = self._alloc()
                    self._function.append(
                        f"         {self._id(new_scaled)} = OpIMul {self._id(self.id_i32)} "
                        f"{self._id(scaled)} {self._id(pd_id)}")
                    self._set_ssa_type(new_scaled, self.id_i32)
                    scaled = new_scaled

            new_result = self._alloc()
            self._function.append(
                f"         {self._id(new_result)} = OpIAdd {self._id(self.id_i32)} "
                f"{self._id(result)} {self._id(scaled)}")
            self._set_ssa_type(new_result, self.id_i32)
            result = new_result

        return result

    def _detect_atomic_pattern(self, store_inst: IRInst,
                                ssa_map: dict, pc_member_ids: dict
                                ) -> tuple[str, int]:
        """Detect read-modify-write pattern for atomic ops.

        Looks at the value being stored. If it's the result of:
          LOAD arr[idx] + delta  → return ("add", delta_id)
          LOAD arr[idx] | mask   → return ("or", mask_id)
        Otherwise returns ("store", val_id).
        """
        val_ref = store_inst.args[0]
        if not isinstance(val_ref, IRRef):
            return ("store", self._resolve(val_ref, pc_member_ids, ssa_map))

        val_name = val_ref.name

        # Walk the kernel body to find the instruction that defines val_name
        def_inst = self._find_def(val_name, self.kernel.loop.body)
        if def_inst is None:
            return ("store", self._resolve(val_ref, pc_member_ids, ssa_map))

        # Check for ADD pattern: val = load + delta
        if def_inst.op == Op.ADD and len(def_inst.args) == 2:
            a, b = def_inst.args
            # One arg should be a LOAD from the same array
            load_arg, delta_arg = None, None
            for x, y in [(a, b), (b, a)]:
                if isinstance(x, IRRef):
                    ld_inst = self._find_def(x.name, self.kernel.loop.body)
                    if ld_inst and ld_inst.op == Op.LOAD:
                        load_arr = ld_inst.meta.get("array", "")
                        store_arr = store_inst.meta.get("array", "")
                        if load_arr == store_arr:
                            delta_arg = y
                            break
            if delta_arg is not None:
                delta_id = self._resolve(delta_arg, pc_member_ids, ssa_map)
                return ("add", delta_id)

        # Check for IOR pattern: val = load | mask
        if def_inst.op == Op.IOR and len(def_inst.args) == 2:
            a, b = def_inst.args
            for x, y in [(a, b), (b, a)]:
                if isinstance(x, IRRef):
                    ld_inst = self._find_def(x.name, self.kernel.loop.body)
                    if ld_inst and ld_inst.op == Op.LOAD:
                        load_arr = ld_inst.meta.get("array", "")
                        store_arr = store_inst.meta.get("array", "")
                        if load_arr == store_arr:
                            mask_id = self._resolve(y, pc_member_ids, ssa_map)
                            return ("or", mask_id)

        return ("store", self._resolve(val_ref, pc_member_ids, ssa_map))

    def _find_def(self, name: str, items: list) -> IRInst | None:
        """Find the IR instruction that defines a named result."""
        for item in items:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.result == name:
                        return inst
            elif isinstance(item, IRIf):
                r = self._find_def(name, item.then_body)
                if r:
                    return r
                if item.else_body:
                    r = self._find_def(name, item.else_body)
                    if r:
                        return r
        return None


# Register this backend
register_backend("spirv", SPIRVBackend)

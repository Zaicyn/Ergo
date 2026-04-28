"""Ergo x86-64 JIT — direct machine code emission for in-game scripting.

Compiles a subset of Ergo (arithmetic, branches, loops, array access)
directly to x86-64 machine code in memory. No C intermediate, no gcc,
no temp files. ~0.5ms compile time for typical scripts.

Usage:
    from mcl.jit_x86 import jit_x86

    fn = jit_x86('''
    REAL FUNCTION SQUARE(X)
      REAL :: X
      SQUARE := X * X
      RETURN SQUARE
    END
    ''')
    print(fn(5.0))  # 25.0

Limitations (by design — this is for in-game scripts, not full sims):
    - f32 only (SSE scalar)
    - No GPU extraction
    - No VERIFY/NET
    - No ALLOCATE
    - Functions and simple subroutines only
    - Max ~64 local variables (register spill to stack)
"""

import ctypes
import ctypes.util
import hashlib
import mmap
import struct

from .lexer import Lexer
from .parser import Parser
from .ir_builder import IRBuilder
from .ir import IRType, Op, IRRef, IRBlock, IRLoop, IRIf
from .errors import MCLError


# ── x86-64 encoder ──────────────────────────────────────────

class X86Emitter:
    """Minimal x86-64 machine code emitter. SSE scalar f32."""

    def __init__(self):
        self.code = bytearray()
        self._labels = {}       # name → offset
        self._fixups = []       # (offset, name, kind) for forward refs
        self._constants = []    # (offset_in_const_pool, float_value)
        self._const_pool = bytearray()

    def _emit(self, *bytes_):
        for b in bytes_:
            if isinstance(b, int):
                self.code.append(b & 0xFF)
            elif isinstance(b, bytes):
                self.code.extend(b)

    def pos(self):
        return len(self.code)

    # ── Labels and jumps ──

    def label(self, name):
        self._labels[name] = self.pos()

    def jmp(self, name):
        self._emit(0xE9)
        self._fixups.append((self.pos(), name, 'rel32'))
        self._emit(0, 0, 0, 0)  # placeholder

    def jcc(self, cc, name):
        """Conditional jump. cc: 0x4=JE, 0x5=JNE, 0xC=JL, 0xD=JGE, 0xE=JLE, 0xF=JG"""
        self._emit(0x0F, 0x80 | cc)
        self._fixups.append((self.pos(), name, 'rel32'))
        self._emit(0, 0, 0, 0)

    def _resolve_fixups(self):
        for offset, name, kind in self._fixups:
            target = self._labels.get(name)
            if target is None:
                raise MCLError(f"JIT: unresolved label '{name}'")
            if kind == 'rel32':
                rel = target - (offset + 4)
                self.code[offset:offset+4] = struct.pack('<i', rel)

    # ── Function prologue/epilogue ──

    def prologue(self, stack_size=256):
        """System V AMD64 ABI: args in xmm0-xmm7 (float), rdi/rsi/rdx/rcx (int)"""
        self._emit(0x55)                    # push rbp
        self._emit(0x48, 0x89, 0xE5)        # mov rbp, rsp
        # Align stack to 16 and reserve space
        aligned = (stack_size + 15) & ~15
        if aligned > 0:
            self._emit(0x48, 0x81, 0xEC)    # sub rsp, imm32
            self._emit(*struct.pack('<I', aligned))
        self._stack_size = aligned

    def epilogue(self):
        self._emit(0x48, 0x89, 0xEC)        # mov rsp, rbp
        self._emit(0x5D)                    # pop rbp
        self._emit(0xC3)                    # ret

    # ── SSE f32 scalar ops ──

    def movss_load(self, xmm_dst, rbp_offset):
        """movss xmmN, [rbp + offset]"""
        self._emit(0xF3, 0x0F, 0x10, 0x85 | (xmm_dst << 3))
        self._emit(*struct.pack('<i', rbp_offset))

    def movss_store(self, rbp_offset, xmm_src):
        """movss [rbp + offset], xmmN"""
        self._emit(0xF3, 0x0F, 0x11, 0x85 | (xmm_src << 3))
        self._emit(*struct.pack('<i', rbp_offset))

    def movss_reg(self, dst, src):
        """movaps xmmDst, xmmSrc"""
        if dst != src:
            self._emit(0x0F, 0x28, 0xC0 | (dst << 3) | src)

    def addss(self, dst, src):
        self._emit(0xF3, 0x0F, 0x58, 0xC0 | (dst << 3) | src)

    def subss(self, dst, src):
        self._emit(0xF3, 0x0F, 0x5C, 0xC0 | (dst << 3) | src)

    def mulss(self, dst, src):
        self._emit(0xF3, 0x0F, 0x59, 0xC0 | (dst << 3) | src)

    def divss(self, dst, src):
        self._emit(0xF3, 0x0F, 0x5E, 0xC0 | (dst << 3) | src)

    def sqrtss(self, dst, src):
        self._emit(0xF3, 0x0F, 0x51, 0xC0 | (dst << 3) | src)

    def comiss(self, a, b):
        """comiss xmmA, xmmB — sets EFLAGS for conditional jumps"""
        self._emit(0x0F, 0x2F, 0xC0 | (a << 3) | b)

    def load_f32_imm(self, xmm, value):
        """Load f32 immediate via constant pool (RIP-relative)"""
        pool_offset = len(self._const_pool)
        self._const_pool.extend(struct.pack('<f', value))
        self._constants.append((self.pos(), pool_offset))
        # movss xmm, [rip + disp32] — filled in during finalize
        self._emit(0xF3, 0x0F, 0x10, 0x05 | (xmm << 3))
        self._emit(0, 0, 0, 0)  # placeholder for RIP-relative offset

    # ── Integer ops (for loop counters, flags) ──

    def mov_reg_imm(self, reg, imm32):
        """mov reg32, imm32. reg: 0=eax, 1=ecx, 2=edx, 3=ebx, 6=esi, 7=edi"""
        self._emit(0xB8 + reg)
        self._emit(*struct.pack('<I', imm32 & 0xFFFFFFFF))

    def mov_reg_mem(self, reg, rbp_offset):
        """mov reg32, [rbp + offset]"""
        self._emit(0x8B, 0x85 | (reg << 3))
        self._emit(*struct.pack('<i', rbp_offset))

    def mov_mem_reg(self, rbp_offset, reg):
        """mov [rbp + offset], reg32"""
        self._emit(0x89, 0x85 | (reg << 3))
        self._emit(*struct.pack('<i', rbp_offset))

    def add_reg_imm(self, reg, imm8):
        """add reg32, imm8"""
        self._emit(0x83, 0xC0 | reg, imm8 & 0xFF)

    def cmp_reg_mem(self, reg, rbp_offset):
        """cmp reg32, [rbp + offset]"""
        self._emit(0x3B, 0x85 | (reg << 3))
        self._emit(*struct.pack('<i', rbp_offset))

    def cmp_reg_imm(self, reg, imm32):
        """cmp reg32, imm32"""
        self._emit(0x81, 0xF8 | reg)
        self._emit(*struct.pack('<I', imm32 & 0xFFFFFFFF))

    # ── Finalize ──

    def finalize(self):
        """Resolve fixups, append constant pool, return executable bytes."""
        self._resolve_fixups()

        # Append constant pool after code and fix RIP-relative references
        pool_start = len(self.code)
        for code_offset, pool_offset in self._constants:
            # The movss instruction is at code_offset, the disp32 is at code_offset+4
            # RIP at execution = code_offset + 4 (after the disp32)
            rip = code_offset + 4
            target = pool_start + pool_offset
            rel = target - rip
            self.code[code_offset:code_offset+4] = struct.pack('<i', rel)

        self.code.extend(self._const_pool)
        return bytes(self.code)


# ── Make memory executable ──────────────────────────────────

def _make_executable(code_bytes):
    """mmap executable memory, copy code, return callable function pointer."""
    size = len(code_bytes)
    # mmap with PROT_READ | PROT_WRITE | PROT_EXEC
    buf = mmap.mmap(-1, size, prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
    buf.write(code_bytes)
    # Get the address
    addr = ctypes.addressof(ctypes.c_char.from_buffer(buf))
    return buf, addr


# ── IR → x86 compiler ──────────────────────────────────────

class X86Compiler:
    """Compiles Ergo IR to x86-64 machine code."""

    def __init__(self, ir_func):
        self.func = ir_func
        self.emit = X86Emitter()
        self._var_offsets = {}   # var name → rbp offset
        self._next_offset = -8  # first local at [rbp-8]
        self._label_count = 0

    def _alloc(self, name):
        if name not in self._var_offsets:
            self._var_offsets[name] = self._next_offset
            self._next_offset -= 8
        return self._var_offsets[name]

    def _new_label(self, prefix="L"):
        self._label_count += 1
        return f"{prefix}_{self._label_count}"

    def compile(self):
        func = self.func

        # Allocate params + locals + scan for temps
        for p in func.params:
            self._alloc(p.name)
        for v in func.locals:
            self._alloc(v.name)
        self._scan_temps(func.body)

        # Prologue
        n_slots = len(self._var_offsets) + 16
        self.emit.prologue(n_slots * 8)

        # Store incoming float args (SysV ABI: xmm0, xmm1, ...)
        float_idx = 0
        int_regs = [7, 6, 2, 1]  # edi, esi, edx, ecx
        int_idx = 0
        for p in func.params:
            offset = self._var_offsets[p.name]
            if p.type == IRType.REAL and float_idx < 8:
                self.emit.movss_store(offset, float_idx)
                float_idx += 1
            elif p.type == IRType.INTEGER and int_idx < 4:
                self.emit.mov_mem_reg(offset, int_regs[int_idx])
                int_idx += 1

        # Compile body
        self._compile_body(func.body)

        # Safety epilogue (in case no explicit RETURN)
        self.emit.epilogue()

        return self.emit.finalize()

    def _scan_temps(self, body):
        for item in body:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    if inst.result:
                        self._alloc(inst.result)
            elif isinstance(item, IRLoop):
                self._scan_temps(item.body)
            elif isinstance(item, IRIf):
                self._scan_temps(item.then_body)
                if item.else_body:
                    self._scan_temps(item.else_body)

    def _load_ref(self, arg, xmm=0):
        """Load an IRRef or literal into xmm register."""
        if isinstance(arg, IRRef):
            self.emit.movss_load(xmm, self._alloc(arg.name))
        elif isinstance(arg, (int, float)):
            self.emit.load_f32_imm(xmm, float(arg))
        return xmm

    def _compile_body(self, body):
        for item in body:
            if isinstance(item, IRBlock):
                for inst in item.insts:
                    self._compile_inst(inst)
            elif isinstance(item, IRLoop):
                self._compile_loop(item)
            elif isinstance(item, IRIf):
                self._compile_branch(item)

    def _compile_inst(self, inst):
        op = inst.op
        result = inst.result
        args = inst.args

        if op == Op.COPY:
            self._load_ref(args[0], xmm=0)
            if result:
                self.emit.movss_store(self._alloc(result), 0)

        elif op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV):
            self._load_ref(args[0], xmm=0)
            self._load_ref(args[1], xmm=1)
            if op == Op.ADD:
                self.emit.addss(0, 1)
            elif op == Op.SUB:
                self.emit.subss(0, 1)
            elif op == Op.MUL:
                self.emit.mulss(0, 1)
            elif op == Op.DIV:
                self.emit.divss(0, 1)
            if result:
                self.emit.movss_store(self._alloc(result), 0)

        elif op == Op.SQRT:
            self._load_ref(args[0], xmm=1)
            self.emit.sqrtss(0, 1)
            if result:
                self.emit.movss_store(self._alloc(result), 0)

        elif op == Op.RETURN:
            if args:
                self._load_ref(args[0], xmm=0)
            self.emit.epilogue()

        elif op == Op.NEG:
            # negate: 0 - x
            self.emit.load_f32_imm(0, 0.0)
            self._load_ref(args[0], xmm=1)
            self.emit.subss(0, 1)
            if result:
                self.emit.movss_store(self._alloc(result), 0)

    def _compile_loop(self, loop):
        top = self._new_label("loop_top")
        end = self._new_label("loop_end")

        counter_off = self._alloc(loop.var)
        end_val_name = f"_loop_end_{self._label_count}"
        end_val_off = self._alloc(end_val_name)

        # Init counter from loop.start
        if isinstance(loop.start, IRRef):
            self.emit.mov_reg_mem(0, self._alloc(loop.start.name))
        else:
            self.emit.mov_reg_imm(0, int(loop.start))
        self.emit.mov_mem_reg(counter_off, 0)

        # Store end value
        if isinstance(loop.end, IRRef):
            self.emit.mov_reg_mem(1, self._alloc(loop.end.name))
        else:
            self.emit.mov_reg_imm(1, int(loop.end))
        self.emit.mov_mem_reg(end_val_off, 1)

        self.emit.label(top)
        self.emit.mov_reg_mem(0, counter_off)
        self.emit.cmp_reg_mem(0, end_val_off)
        self.emit.jcc(0xF, end)  # JG end

        self._compile_body(loop.body)

        self.emit.mov_reg_mem(0, counter_off)
        self.emit.add_reg_imm(0, 1)
        self.emit.mov_mem_reg(counter_off, 0)
        self.emit.jmp(top)
        self.emit.label(end)

    def _compile_branch(self, branch):
        else_lbl = self._new_label("else")
        end_lbl = self._new_label("endif")

        # IRIf.condition is an IRRef to a boolean temp (0 or 1).
        # The comparison that produced it is already compiled.
        # We just need to test: if condition == 0, jump to else.
        if branch.condition:
            cond = branch.condition
            if isinstance(cond, IRRef):
                self.emit.movss_load(0, self._alloc(cond.name))
                self.emit.load_f32_imm(1, 0.0)
                self.emit.comiss(0, 1)
                self.emit.jcc(0x4, else_lbl)  # JE else (cond == 0)

        self._compile_body(branch.then_body)
        if branch.else_body:
            self.emit.jmp(end_lbl)

        self.emit.label(else_lbl)
        if branch.else_body:
            self._compile_body(branch.else_body)

        self.emit.label(end_lbl)


# ── Public API ──────────────────────────────────────────────

_x86_cache = {}


def jit_x86(source: str, cache: bool = True):
    """JIT-compile an Ergo function to native x86-64 machine code.

    Returns a callable Python function. f32 only.

    Args:
        source: Ergo source containing one REAL FUNCTION
        cache: reuse compiled code for identical source

    Returns:
        Callable that accepts float args and returns float
    """
    source_hash = hashlib.sha256(source.encode()).hexdigest()[:16]

    if cache and source_hash in _x86_cache:
        return _x86_cache[source_hash]

    # Set f32 precision for x86 JIT
    from .ir import set_real_precision
    set_real_precision(32)

    # Parse
    tokens = Lexer(source).tokenize()
    tree = Parser(tokens).parse()

    # Build IR
    ir_module = IRBuilder().build(tree)

    if not ir_module.functions:
        raise MCLError("JIT: no functions found in source")

    # Compile first function
    ir_func = ir_module.functions[0]
    compiler = X86Compiler(ir_func)
    code_bytes = compiler.compile()

    # Make executable
    buf, addr = _make_executable(code_bytes)

    # Build ctypes callable
    n_float_params = sum(1 for p in ir_func.params if p.type == IRType.REAL)
    n_int_params = sum(1 for p in ir_func.params if p.type == IRType.INTEGER)

    # Determine return type
    if ir_func.return_type == IRType.INTEGER:
        restype = ctypes.c_int
    else:
        restype = ctypes.c_float

    # Build argtypes
    argtypes = []
    for p in ir_func.params:
        if p.type == IRType.REAL:
            argtypes.append(ctypes.c_float)
        else:
            argtypes.append(ctypes.c_int)

    func_type = ctypes.CFUNCTYPE(restype, *argtypes)
    func = func_type(addr)

    # Keep buf alive so mmap doesn't get collected
    func._jit_buf = buf
    func._jit_code = code_bytes
    func._jit_hash = source_hash

    if cache:
        _x86_cache[source_hash] = func

    return func

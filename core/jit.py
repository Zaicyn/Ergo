"""Ergo JIT compiler — compile .ergo source to callable functions at runtime.

Usage:
    from core.jit import jit

    lib = jit('''
    REAL FUNCTION SQUARE(X)
      REAL :: X
      SQUARE := X * X
      RETURN SQUARE
    END
    ''')

    result = lib.call('SQUARE', 5.0)  # returns 25.0

Array parameters (assumed-shape dummies) marshal by pointer:

    lib = jit('''
    REAL FUNCTION DOTN(A, B, N)
      INTEGER :: N
      REAL :: A(N)
      REAL :: B(N)
      ...
    END
    ''')
    lib.call('DOTN', a, b, n)   # a/b: numpy arrays, ctypes arrays,
                                # array.array, memoryview, or lists

STATIC storage (the Ergo idiom — subroutines access STATIC arrays
directly, per Spec Part 7) is reachable by name, zero-copy:

    lib.array('M')              # (flat ctypes array, shape tuple)
    lib.array_np('M')           # numpy view, same buffer (needs numpy)
    lib.value('TICK')           # read a STATIC scalar
    lib.set_value('TICK', 12)   # write a STATIC scalar

Load a matrix into STATIC storage, call a subroutine that operates on
it, read the result back — no copying.

Function signatures come from the IR (not from guessing Python value
types): INTEGER functions return Python ints, REAL functions return
Python floats, subroutines return None.

Deterministic: same source + same precision + same flags always produces
the same binary (compiled with driver.DETERMINISTIC_FLAGS).
"""

import ctypes
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

from .lexer import Lexer
from .parser import Parser
from .checker import Checker
from .ir_builder import IRBuilder
from .ir_codegen import IRCodeGen
from .ir import IRType, StorageClass, get_real_precision, set_real_precision
from .errors import MCLError
from .driver import DETERMINISTIC_FLAGS


def _ctype_for(ir_type, real_ctype):
    """Map an IR type to a ctypes scalar type. None = unsupported."""
    if ir_type == IRType.REAL:
        return real_ctype
    if ir_type in (IRType.INTEGER, IRType.LOGICAL):
        return ctypes.c_int
    return None


# numpy dtype expectations per ctypes base (duck-typed checks, no import)
_NP_KIND_SIZE = {
    ctypes.c_double: ("f", 8),
    ctypes.c_float: ("f", 4),
    ctypes.c_int: ("i", 4),
}

# buffer-protocol (memoryview) format expectations per ctypes base
_BUF_FORMAT_SIZE = {
    ctypes.c_double: ({"d"}, 8),
    ctypes.c_float: ({"f"}, 4),
    ctypes.c_int: ({"i"}, 4),
}


class _Sig:
    """Registered signature for one emitted function."""
    __slots__ = ("restype", "argtypes", "unsupported", "params")

    def __init__(self, restype, argtypes, unsupported, params):
        self.restype = restype          # ctypes type or None (subroutine)
        self.argtypes = argtypes        # tuple of ctypes types (POINTER for arrays)
        self.unsupported = unsupported  # list of reasons, or None
        self.params = params            # tuple of (name, ir_type, shape|None)


class JitLibrary:
    """A JIT-compiled Ergo library. Wraps a dlopen'd shared object."""

    def __init__(self, so_path: str, c_code: str, cache_key: str,
                 real_type=ctypes.c_double, lib_dir: str = None):
        self._so_path = so_path
        self._c_code = c_code
        self._cache_key = cache_key
        self._lib = ctypes.CDLL(so_path)
        self._signatures = {}
        self._static_vars = {}          # name → (IRType, shape|None)
        self._real_type = real_type  # c_float for f32, c_double for f64
        self._lib_dir = lib_dir or os.path.dirname(so_path)

    # ── registration ──────────────────────────────────────────

    def register(self, name: str, restype, argtypes):
        """Register a function signature manually (advanced use)."""
        func = getattr(self._lib, name)
        func.restype = restype
        func.argtypes = argtypes
        params = tuple((f"arg{i}", None, None) for i in range(len(argtypes)))
        self._signatures[name] = _Sig(restype, tuple(argtypes), None, params)
        return func

    def register_ir(self, ir_module):
        """Register every function/subroutine in the IR module, plus all
        STATIC globals for direct storage access.

        Signatures come from the IR declarations — the source of truth.
        Array parameters become POINTER types and are marshaled by
        `call()` from numpy arrays, ctypes arrays, buffer-protocol
        objects, or lists. CHARACTER parameters/returns and COMPLEX are
        recorded but marked unsupported (calling raises MCLError).
        """
        for g in ir_module.globals:
            if g.storage == StorageClass.STATIC:
                self._static_vars[g.name] = (g.type, g.shape)

        for fn in ir_module.functions:
            unsupported = []
            argtypes = []
            params = []
            for p in fn.params:
                params.append((p.name, p.type, p.shape))
                base = _ctype_for(p.type, self._real_type)
                if base is None:
                    unsupported.append(
                        f"parameter '{p.name}' of type {p.type.value}")
                    argtypes.append(None)
                elif p.is_array:
                    argtypes.append(ctypes.POINTER(base))
                else:
                    argtypes.append(base)
            if fn.is_subroutine:
                restype = None
            else:
                restype = _ctype_for(fn.return_type, self._real_type)
                if restype is None:
                    unsupported.append(
                        f"return type {fn.return_type.value}")
            self._signatures[fn.name] = _Sig(
                restype, tuple(argtypes), unsupported or None, tuple(params))

    # ── calling ────────────────────────────────────────────────

    def call(self, name: str, *args):
        """Call a JIT-compiled function by name.

        Scalar args convert from Python int/float. Array args marshal by
        pointer (zero-copy except lists, which are copied): numpy arrays
        (dtype must match — float64 for f64 REAL, float32 for f32 REAL,
        int32 for INTEGER; C-contiguous), ctypes arrays, array.array /
        memoryview (matching format), or lists/tuples (copied — callee
        mutations are lost).
        """
        if name not in self._signatures:
            available = ", ".join(sorted(self._signatures)) or "(none)"
            raise MCLError(
                f"Function '{name}' not found in JIT library. "
                f"Available: {available}")
        sig = self._signatures[name]
        if sig.unsupported:
            raise MCLError(
                f"Cannot call '{name}' via JIT: "
                f"{'; '.join(sig.unsupported)} not supported")
        if len(args) != len(sig.argtypes):
            raise MCLError(
                f"'{name}' expects {len(sig.argtypes)} argument(s), "
                f"got {len(args)}")

        func = getattr(self._lib, name)
        func.restype = sig.restype
        func.argtypes = list(sig.argtypes)
        c_args = [
            self._convert(name, args, i, sig)
            for i in range(len(args))
        ]
        return func(*c_args)

    def _convert(self, fname, args, i, sig):
        value = args[i]
        ctype = sig.argtypes[i]
        pname, _ptype, shape = sig.params[i]
        if not issubclass(ctype, ctypes._Pointer):
            return ctype(value)  # scalar
        # Array parameter → pointer marshal
        base = ctype._type_
        ptr, count = self._as_buffer(fname, pname, value, base)
        expected = self._expected_count(shape, args, sig.params)
        if expected is not None and count != expected:
            raise MCLError(
                f"'{fname}' parameter '{pname}': expected {expected} "
                f"element(s) from shape {shape}, got {count}")
        return ptr

    def _as_buffer(self, fname, pname, value, base):
        """Return (POINTER(base), element_count) for an array argument."""
        ptype = ctypes.POINTER(base)

        # numpy array (duck-typed — no hard numpy dependency)
        if hasattr(value, "ctypes") and hasattr(value, "dtype"):
            kind, size = _NP_KIND_SIZE[base]
            dt = value.dtype
            if dt.kind != kind or dt.itemsize != size:
                raise MCLError(
                    f"'{fname}' parameter '{pname}': wrong numpy dtype "
                    f"'{dt}' — need kind '{kind}' itemsize {size} "
                    f"(float64 for f64 REAL, float32 for f32 REAL, "
                    f"int32 for INTEGER)")
            if not value.flags["C_CONTIGUOUS"]:
                raise MCLError(
                    f"'{fname}' parameter '{pname}': numpy array must be "
                    f"C-contiguous (use numpy.ascontiguousarray)")
            return value.ctypes.data_as(ptype), int(value.size)

        # ctypes array
        if isinstance(value, ctypes.Array):
            if value._type_ is not base:
                raise MCLError(
                    f"'{fname}' parameter '{pname}': wrong ctypes element "
                    f"type {value._type_.__name__}, need {base.__name__}")
            return ctypes.cast(value, ptype), len(value)

        # buffer-protocol objects (array.array, memoryview, bytes-like)
        try:
            mv = memoryview(value)
        except TypeError:
            mv = None
        if mv is not None:
            formats, size = _BUF_FORMAT_SIZE[base]
            if mv.format not in formats or mv.itemsize != size:
                raise MCLError(
                    f"'{fname}' parameter '{pname}': wrong buffer format "
                    f"'{mv.format}' — need {sorted(formats)} "
                    f"(e.g. array.array('d') for f64 REAL, 'f' for f32, "
                    f"'i' for INTEGER)")
            c_arr = (base * len(mv)).from_buffer(value)
            return ctypes.cast(c_arr, ptype), len(mv)

        # lists / tuples — copied (callee mutations are lost)
        if isinstance(value, (list, tuple)):
            c_arr = (base * len(value))(*value)
            return ctypes.cast(c_arr, ptype), len(value)

        raise MCLError(
            f"'{fname}' parameter '{pname}': cannot marshal "
            f"{type(value).__name__} as an array — pass a numpy array, "
            f"ctypes array, array.array, memoryview, or list")

    @staticmethod
    def _expected_count(shape, args, params):
        """Expected element count from a declared shape, resolving
        parameter-name dims (e.g. A(N)) against the call arguments.
        None = cannot determine (trust the caller)."""
        if shape is None:
            return None
        total = 1
        for d in shape:
            if isinstance(d, int):
                total *= d
            elif isinstance(d, str):
                for j, (nm, _t, _s) in enumerate(params):
                    if nm == d:
                        try:
                            total *= int(args[j])
                        except (TypeError, ValueError):
                            return None
                        break
                else:
                    return None
            else:
                return None
        return total

    # ── STATIC storage access ─────────────────────────────────

    def _static_entry(self, name):
        if name not in self._static_vars:
            available = ", ".join(sorted(self._static_vars)) or "(none)"
            raise MCLError(
                f"No STATIC variable '{name}' in JIT library. "
                f"Available: {available}")
        return self._static_vars[name]

    def array(self, name: str):
        """Zero-copy access to a STATIC array's storage.

        Returns (flat ctypes array, shape tuple). Writes through the
        returned array are visible to subsequent JIT calls, and callee
        writes are visible to Python. Multi-dimensional arrays are
        flattened COLUMN-MAJOR (first Ergo index fastest — the locked
        convention).
        """
        ir_type, shape = self._static_entry(name)
        if shape is None:
            raise MCLError(
                f"'{name}' is a scalar — use value()/set_value()")
        base = _ctype_for(ir_type, self._real_type)
        total = 1
        for d in shape:
            if not isinstance(d, int):
                raise MCLError(
                    f"STATIC array '{name}' has a non-constant shape "
                    f"{shape} — cannot expose via JIT")
            total *= d
        c_arr = (base * total).in_dll(self._lib, name)
        return c_arr, tuple(shape)

    def array_np(self, name: str):
        """numpy view of a STATIC array (zero-copy). Requires numpy.

        Ergo arrays are COLUMN-MAJOR (first index fastest — the locked
        convention), so the view is reshaped with order='F':
        view[i, j] == Ergo A(i+1, j+1) for 1-based (i, j) in Ergo.
        """
        try:
            import numpy as np
        except ImportError:
            raise MCLError("array_np requires numpy (array() works without)")
        c_arr, shape = self.array(name)
        dtype = {ctypes.c_double: np.float64,
                 ctypes.c_float: np.float32,
                 ctypes.c_int: np.int32}[c_arr._type_]
        return np.frombuffer(c_arr, dtype=dtype).reshape(shape, order='F')

    def value(self, name: str):
        """Read a STATIC scalar."""
        ir_type, shape = self._static_entry(name)
        if shape is not None:
            raise MCLError(f"'{name}' is an array — use array()")
        base = _ctype_for(ir_type, self._real_type)
        return base.in_dll(self._lib, name).value

    def set_value(self, name: str, v):
        """Write a STATIC scalar."""
        ir_type, shape = self._static_entry(name)
        if shape is not None:
            raise MCLError(f"'{name}' is an array — use array()")
        base = _ctype_for(ir_type, self._real_type)
        cell = base.in_dll(self._lib, name)
        cell.value = base(v).value

    # ── misc ──────────────────────────────────────────────────

    def get_function(self, name: str):
        """Get raw ctypes function pointer for advanced use."""
        return getattr(self._lib, name)

    @property
    def path(self):
        return self._so_path

    @property
    def source_hash(self):
        return self._cache_key

    def __del__(self):
        # Cleanup temp directory holding the .so
        try:
            if self._lib_dir and os.path.isdir(self._lib_dir):
                shutil.rmtree(self._lib_dir, ignore_errors=True)
        except Exception:
            pass


# Cache: (source, precision, flags) key → JitLibrary
_jit_cache = {}


def jit(source: str, precision: int = 64,
        cpu_fast_math: bool = False,
        gpu_fast_math: bool = False,
        cache: bool = True) -> JitLibrary:
    """JIT-compile Ergo source code to a callable library.

    Args:
        source: Ergo source code as a string
        precision: 64 (default) or 32 — REAL precision
        cpu_fast_math: pass -ffast-math to GCC (breaks IEEE determinism)
        gpu_fast_math: accepted for signature parity with compile_file;
                       no effect on the JIT path (no GPU codegen here)
        cache: if True, reuse compiled library for identical
               source+precision+flags

    Returns:
        JitLibrary with callable functions and STATIC storage access
    """
    # gpu_fast_math accepted but unused — JIT path is CPU-only.
    del gpu_fast_math
    if precision not in (32, 64):
        raise MCLError(f"precision must be 32 or 64, got {precision}")

    # Cache key must include everything that changes the binary:
    # source, REAL precision, and the fast-math flag.
    source_hash = hashlib.sha256(source.encode()).hexdigest()[:16]
    cache_key = f"{source_hash}:p{precision}:fm{int(cpu_fast_math)}"

    if cache and cache_key in _jit_cache:
        return _jit_cache[cache_key]

    # Precision is a process-global used by IR construction and codegen.
    # Save/restore so a JIT build never leaks its precision into later
    # compile_source/compile_file calls in the same process.
    old_precision = get_real_precision()
    try:
        set_real_precision(precision)
        tokens = Lexer(source).tokenize()
        tree = Parser(tokens).parse()

        errors = Checker().check(tree)
        if errors:
            for e in errors:
                print(e, file=sys.stderr)
            raise MCLError(f"JIT type checking failed ({len(errors)} error(s))")

        ir_module = IRBuilder().build(tree)

        # JIT mode: no main() — export all functions/subroutines, and
        # STATIC storage is emitted without the `static` keyword so
        # ctypes can reach it.
        c_code = IRCodeGen(ir_module, jit_mode=True).generate()
    finally:
        set_real_precision(old_precision)

    real_ctype = ctypes.c_float if precision == 32 else ctypes.c_double

    # Compile to a shared library in a private temp directory (no
    # predictable path for another process to clobber or pre-create).
    lib_dir = tempfile.mkdtemp(prefix="ergo_jit_")
    so_path = os.path.join(lib_dir, "libergo_jit.so")

    runtime_dir = os.path.join(os.path.dirname(__file__), "runtime")
    gcc_flags = ([
        "gcc", "-shared", "-fPIC",
        "-o", so_path,
        "-x", "c", "-",  # read from stdin
    ] + DETERMINISTIC_FLAGS + [
        "-lm",
        f"-I{runtime_dir}",
    ])
    if cpu_fast_math:
        gcc_flags.append("-ffast-math")

    result = subprocess.run(
        gcc_flags,
        input=c_code,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        shutil.rmtree(lib_dir, ignore_errors=True)
        raise MCLError(f"JIT compilation failed:\n{result.stderr}")

    lib = JitLibrary(so_path, c_code, cache_key,
                     real_type=real_ctype, lib_dir=lib_dir)
    lib.register_ir(ir_module)

    if cache:
        _jit_cache[cache_key] = lib

    return lib

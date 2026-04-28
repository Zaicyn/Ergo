"""Ergo JIT compiler — compile .ergo source to callable functions at runtime.

Usage:
    from mcl.jit import jit

    lib = jit('''
    REAL FUNCTION SQUARE(X)
      REAL :: X
      SQUARE := X * X
      RETURN SQUARE
    END
    ''')

    result = lib.call('SQUARE', 5.0)  # returns 25.0

    # Or compile from file:
    lib = jit(open('my_sim.ergo').read())
    lib.call('SIM_INIT', 12, 1000, 42)

The JIT compiles Ergo source → C → shared library (.so) → dlopen.
Functions are callable via ctypes with automatic type marshaling.
Deterministic: same source always produces same binary.
"""

import ctypes
import os
import subprocess
import tempfile
import hashlib

from .lexer import Lexer
from .parser import Parser
from .checker import Checker
from .ir_builder import IRBuilder
from .ir_codegen import IRCodeGen
from .ir import get_real_precision
from .errors import MCLError


class JitLibrary:
    """A JIT-compiled Ergo library. Wraps a dlopen'd shared object."""

    def __init__(self, so_path: str, c_code: str, source_hash: str,
                 real_type=ctypes.c_double):
        self._so_path = so_path
        self._c_code = c_code
        self._source_hash = source_hash
        self._lib = ctypes.CDLL(so_path)
        self._signatures = {}
        self._real_type = real_type  # c_float for f32, c_double for f64

    def register(self, name: str, restype, argtypes):
        """Register a function signature for type-safe calling."""
        func = getattr(self._lib, name)
        func.restype = restype
        func.argtypes = argtypes
        self._signatures[name] = (restype, argtypes)
        return func

    def call(self, name: str, *args):
        """Call a JIT-compiled function by name.

        Auto-detects argument types from Python values:
            int → c_int
            float → c_float
            bytes → c_char_p
        """
        if name not in self._signatures:
            # Auto-detect types from args
            argtypes = []
            for a in args:
                if isinstance(a, int):
                    argtypes.append(ctypes.c_int)
                elif isinstance(a, float):
                    argtypes.append(self._real_type)
                else:
                    raise TypeError(f"Unsupported arg type: {type(a)}")

            # Default: assume REAL return for functions, void for subroutines
            func = getattr(self._lib, name, None)
            if func is None:
                raise MCLError(f"Function '{name}' not found in JIT library")
            func.argtypes = argtypes
            func.restype = self._real_type
            self._signatures[name] = (self._real_type, argtypes)

        func = getattr(self._lib, name)
        # Convert Python floats to correct ctypes precision
        c_args = []
        for a, t in zip(args, self._signatures[name][1]):
            if t in (ctypes.c_float, ctypes.c_double) and isinstance(a, float):
                c_args.append(t(a))
            else:
                c_args.append(a)
        return func(*c_args)

    def get_function(self, name: str):
        """Get raw ctypes function pointer for advanced use."""
        return getattr(self._lib, name)

    @property
    def path(self):
        return self._so_path

    @property
    def source_hash(self):
        return self._source_hash

    def __del__(self):
        # Cleanup temp .so file
        try:
            if os.path.exists(self._so_path):
                os.unlink(self._so_path)
        except Exception:
            pass


# Cache: source hash → JitLibrary
_jit_cache = {}


def jit(source: str, precision: int = 64, fast_math: bool = False,
        cache: bool = True) -> JitLibrary:
    """JIT-compile Ergo source code to a callable library.

    Args:
        source: Ergo source code as a string
        fast_math: enable -ffast-math (breaks determinism)
        cache: if True, reuse compiled library for identical source

    Returns:
        JitLibrary with callable functions
    """
    # Hash source for caching
    source_hash = hashlib.sha256(source.encode()).hexdigest()[:16]

    if cache and source_hash in _jit_cache:
        return _jit_cache[source_hash]

    # Set precision
    from .ir import set_real_precision
    set_real_precision(precision)
    real_ctype = ctypes.c_float if precision == 32 else ctypes.c_double

    # Lex → Parse → Check → IR → C
    tokens = Lexer(source).tokenize()
    tree = Parser(tokens).parse()

    errors = Checker().check(tree)
    if errors:
        for e in errors:
            import sys
            print(e, file=sys.stderr)
        raise MCLError(f"JIT type checking failed ({len(errors)} error(s))")

    ir_module = IRBuilder().build(tree)

    # Generate C with JIT-friendly modifications:
    # - No main() — we want callable functions
    # - Export all subroutines and functions
    c_code = IRCodeGen(ir_module, jit_mode=True).generate()

    # Compile to shared library
    so_path = os.path.join(tempfile.gettempdir(),
                           f"ergo_jit_{source_hash}.so")

    runtime_dir = os.path.join(os.path.dirname(__file__), "runtime")
    gcc_flags = [
        "gcc", "-shared", "-fPIC", "-O2",
        "-o", so_path,
        "-x", "c", "-",  # read from stdin
        "-lm", "-std=c99",
        f"-I{runtime_dir}",
    ]
    if fast_math:
        gcc_flags.append("-ffast-math")

    result = subprocess.run(
        gcc_flags,
        input=c_code,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise MCLError(f"JIT compilation failed:\n{result.stderr}")

    lib = JitLibrary(so_path, c_code, source_hash, real_type=real_ctype)

    if cache:
        _jit_cache[source_hash] = lib

    return lib

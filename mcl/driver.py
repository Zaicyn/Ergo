"""Ergo compiler driver: source -> tokens -> AST -> IR -> C -> executable."""

import subprocess
import tempfile
import os
import sys

from .lexer import Lexer
from .parser import Parser
from .checker import Checker
from .codegen import CodeGen
from .ir_builder import IRBuilder
from .ir_codegen import IRCodeGen
from .ir_gpu import (extract_kernels, promote_locals,
                     linearize_nested_loops, fuse_kernels)
from .errors import MCLError


# Default GCC flags applied to every generated-C compile. Per V22's
# COMPILER_DETERMINISM audit, this combination is performance-positive and
# determinism-neutral: -O3 enables full optimization; -march=x86-64-v3
# guarantees FMA + AVX2 + BMI2 baseline (Haswell/Zen2 or newer);
# -ffp-contract=fast permits FMA fusion within an expression (deterministic
# *if* the source is compiled identically each time); -fno-math-errno
# elides errno writes from libm calls (deterministic, faster). -std=c11
# matches the documented determinism contract in Spec/MCL_Design_COMPLETE.md.
DETERMINISTIC_FLAGS = [
    "-O3",
    "-fwrapv",
    "-march=x86-64-v3",
    "-ffp-contract=fast",
    "-fno-math-errno",
    "-std=c11",
]


def compile_source(source: str, output: str = "a.out", emit_c: bool = False,
                   skip_check: bool = False,
                   cpu_fast_math: bool = False,
                   gpu_fast_math: bool = False,
                   source_path: str = None, use_ir: bool = True,
                   target: str = None, no_split: bool = False,
                   render: bool = False,
                   promote_locals_flag: bool = False,
                   param_overrides: dict = None,
                   arena_size: int = None) -> str:
    """Compile MCL source to an executable (or just emit C if requested).

    target: if set, extract GPU kernels and emit device code via the
            named backend (e.g. "nvvm"). None = CPU-only.

    Returns the generated C code.
    """
    # Lex
    tokens = Lexer(source).tokenize()

    # Parse
    tree = Parser(tokens).parse()

    # Type check
    if not skip_check:
        errors = Checker().check(tree)
        if errors:
            for e in errors:
                print(e, file=sys.stderr)
            raise MCLError(f"Type checking failed ({len(errors)} error(s))")

    # Codegen — IR path (default) or legacy AST path
    if use_ir:
        ir_module = IRBuilder().build(tree, source_file=source_path)

        # Apply -N / -M parameter overrides
        if param_overrides:
            from .ir import StorageClass
            for var in ir_module.globals:
                if (var.storage == StorageClass.PARAMETER and
                        var.name in param_overrides):
                    old = var.init_value
                    var.init_value = param_overrides[var.name]
                    print(f"[override] {var.name} = {old} → {var.init_value}",
                          file=sys.stderr)

        if target:
            if promote_locals_flag:
                promo_diags = promote_locals(ir_module)
                for d in promo_diags:
                    print(d, file=sys.stderr)
            return _compile_target(ir_module, target, output, emit_c,
                                   cpu_fast_math, gpu_fast_math,
                                   no_split, render, arena_size)

        if render:
            from .ir_inline import inline_subroutines
            for d in inline_subroutines(ir_module):
                print(d, file=sys.stderr)
        c_code = IRCodeGen(ir_module, render=render).generate()
    else:
        c_code = CodeGen(tree, source_file=source_path).generate()

    if emit_c:
        return c_code

    # Write C to temp file and compile with gcc
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".c", delete=False, prefix="mcl_"
    ) as f:
        f.write(c_code)
        c_path = f.name

    try:
        runtime_dir = os.path.join(os.path.dirname(__file__), "runtime")
        gcc_flags = (["gcc", "-o", output, c_path] + DETERMINISTIC_FLAGS +
                     ["-lm", f"-I{runtime_dir}"])
        if render:
            # Link against Vulkan runtime for rendering
            vk_host_c = os.path.join(runtime_dir, "vk_host.c")
            gcc_flags.insert(3, vk_host_c)
            gcc_flags.extend(["-lvulkan", "-lglfw"])
        if cpu_fast_math:
            gcc_flags.append("-ffast-math")
        if arena_size is not None:
            gcc_flags.append(f"-DERGO_ARENA_BYTES=((size_t){arena_size})")
        result = subprocess.run(
            gcc_flags,
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print("=== Generated C ===", file=sys.stderr)
            # Print C with line numbers for debugging
            for i, line in enumerate(c_code.splitlines(), 1):
                print(f"{i:4d}  {line}", file=sys.stderr)
            print("=== GCC errors ===", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            raise MCLError(f"C compilation failed (gcc exit code {result.returncode})")
        return c_code
    finally:
        os.unlink(c_path)


def _compile_target(ir_module, target: str, output: str, emit_c: bool,
                    cpu_fast_math: bool, gpu_fast_math: bool,
                    no_split: bool = False,
                    render: bool = False,
                    arena_size: int = None) -> str:
    """Kernel extraction + vendor backend compilation path."""
    # Load the requested backend (vendor-specific, loaded on demand)
    from .backends import get_backend
    _load_backend(target)
    backend_cls = get_backend(target)

    # Inline subroutines to expose inner loops for extraction
    from .ir_inline import inline_subroutines
    inline_diags = inline_subroutines(ir_module)
    for d in inline_diags:
        print(f"[{target}] {d}", file=sys.stderr)

    # Linearize eligible nested loops before extraction
    lin_diags = linearize_nested_loops(ir_module)
    for d in lin_diags:
        print(f"[{target}] {d}", file=sys.stderr)

    # Extract kernels (vendor-neutral analysis)
    plan = extract_kernels(ir_module, allow_split=not no_split)

    # Fuse adjacent compatible kernels
    fuse_diags = fuse_kernels(plan, ir_module)
    for d in fuse_diags:
        print(f"[{target}] {d}", file=sys.stderr)

    # Report extraction results
    for k in plan.kernels:
        dep_str = k.dependence.value
        if k.shift_k is not None:
            dep_str += f"(k={k.shift_k})"
        print(f"[{target}] Extracted kernel_{k.kernel_id} from line "
              f"{k.source_line} [{dep_str}]: "
              f"arrays={sorted(k.arrays_written | k.arrays_read)}, "
              f"scalars={sorted(k.scalars_read)}", file=sys.stderr)
    for line, reason in plan.rejections:
        print(f"[{target}] Loop at line {line} not extracted: {reason}",
              file=sys.stderr)
    for line, msg in plan.warnings:
        print(f"[{target}] WARNING line {line}: {msg}", file=sys.stderr)

    if not plan.kernels:
        print(f"[{target}] No extractable kernels found. "
              f"Falling back to CPU path.", file=sys.stderr)
        c_code = IRCodeGen(ir_module, render=render).generate()
        if emit_c:
            return c_code
        # Still need to compile with vk_host if rendering
        if render:
            runtime_dir = os.path.join(os.path.dirname(__file__), "runtime")
            vk_host_c = os.path.join(runtime_dir, "vk_host.c")
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".c", delete=False, prefix="mcl_"
            ) as f:
                f.write(c_code)
                c_path = f.name
            try:
                gcc_flags = ([
                    "gcc", "-o", output, c_path, vk_host_c,
                ] + DETERMINISTIC_FLAGS + [
                    "-lm", "-lvulkan", "-lglfw",
                    f"-I{runtime_dir}",
                ])
                if cpu_fast_math:
                    gcc_flags.append("-ffast-math")
                if arena_size is not None:
                    gcc_flags.append(
                        f"-DERGO_ARENA_BYTES=((size_t){arena_size})")
                result = subprocess.run(gcc_flags, capture_output=True, text=True)
                if result.returncode != 0:
                    print("=== Generated C ===", file=sys.stderr)
                    for i, line in enumerate(c_code.splitlines(), 1):
                        print(f"{i:4d}  {line}", file=sys.stderr)
                    print("=== GCC errors ===", file=sys.stderr)
                    print(result.stderr, file=sys.stderr)
                    raise MCLError(
                        f"C compilation failed (gcc exit code {result.returncode})")
                print(f"Render executable: {output}", file=sys.stderr)
                return c_code
            finally:
                os.unlink(c_path)
        return c_code

    # Instantiate backend and generate device code
    backend = backend_cls(ir_module, plan, gpu_fast_math=gpu_fast_math)
    device_code = backend.generate()
    host_launches = backend.generate_host_launches()

    # Generate GPU-aware host code (extracted loops -> dispatches)
    c_code = IRCodeGen(ir_module, gpu_plan=plan, backend=backend,
                       render=render).generate()

    if emit_c:
        result = []
        result.append(f"/* ====== Device code ({backend.name}) ====== */")
        result.append("/*")
        result.append(device_code)
        result.append("*/")
        result.append("")
        result.append("/* ====== GPU-aware host C99 ====== */")
        result.append(c_code)
        return "\n".join(result)

    # Write device code to file (for debugging)
    dev_path = output + backend.device_ext
    with open(dev_path, "w") as f:
        f.write(device_code)
    print(f"[{target}] Device code written to {dev_path}", file=sys.stderr)

    # Find vk_host.c runtime
    runtime_dir = os.path.join(os.path.dirname(__file__), "runtime")
    vk_host_c = os.path.join(runtime_dir, "vk_host.c")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".c", delete=False, prefix="mcl_"
    ) as f:
        f.write(c_code)
        c_path = f.name

    try:
        gcc_flags = ([
            "gcc", "-o", output, c_path,
            vk_host_c,
        ] + DETERMINISTIC_FLAGS + [
            "-lm", "-lvulkan",
            f"-I{runtime_dir}",
        ])
        if render:
            gcc_flags.append("-lglfw")
        else:
            gcc_flags.append("-DERGO_VK_HEADLESS_ONLY")
        if cpu_fast_math:
            gcc_flags.append("-ffast-math")
        if arena_size is not None:
            gcc_flags.append(f"-DERGO_ARENA_BYTES=((size_t){arena_size})")
        result = subprocess.run(gcc_flags, capture_output=True, text=True)
        if result.returncode != 0:
            print("=== Generated C ===", file=sys.stderr)
            for i, line in enumerate(c_code.splitlines(), 1):
                print(f"{i:4d}  {line}", file=sys.stderr)
            print("=== GCC errors ===", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            raise MCLError(
                f"C compilation failed (gcc exit code {result.returncode})")
        print(f"[{target}] GPU executable: {output}", file=sys.stderr)
        return c_code
    finally:
        os.unlink(c_path)


def _load_backend(target: str):
    """Import the backend module so it registers itself.

    Backends are loaded on demand — no vendor code is imported until
    the user requests a specific target.
    """
    if target == "nvvm":
        import mcl.backends.nvvm  # noqa: F401
    elif target == "spirv":
        import mcl.backends.spirv  # noqa: F401
    else:
        raise MCLError(f"Unknown target '{target}'. Available: nvvm, spirv")


def compile_file(path: str, output: str = None, emit_c: bool = False,
                 cpu_fast_math: bool = False,
                 gpu_fast_math: bool = False,
                 use_ir: bool = True,
                 target: str = None, no_split: bool = False,
                 render: bool = False,
                 promote_locals: bool = False,
                 param_overrides: dict = None,
                 arena_size: int = None) -> str:
    """Compile an MCL source file."""
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    if output is None:
        base = os.path.splitext(os.path.basename(path))[0]
        output = base

    return compile_source(source, output=output, emit_c=emit_c,
                          cpu_fast_math=cpu_fast_math,
                          gpu_fast_math=gpu_fast_math,
                          source_path=path,
                          use_ir=use_ir, target=target,
                          no_split=no_split, render=render,
                          promote_locals_flag=promote_locals,
                          param_overrides=param_overrides,
                          arena_size=arena_size)

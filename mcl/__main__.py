"""CLI entry point: python -m mcl <source.mcl> [options]"""

import argparse
import sys

from .driver import compile_file
from .errors import MCLError


def main():
    parser = argparse.ArgumentParser(
        prog="mcl",
        description="Ergo compiler — deterministic simulation language",
    )
    parser.add_argument("source", help="Source file to compile")
    parser.add_argument("-o", "--output", help="Output executable name")

    # Emission modes
    parser.add_argument(
        "--emit-c", action="store_true",
        help="Emit generated C code to stdout instead of compiling",
    )
    parser.add_argument(
        "--emit-ir", action="store_true",
        help="Dump Ergo IR to stdout (for debugging)",
    )

    # Compute target
    parser.add_argument(
        "--target",
        help="Extract kernels for a compute target (e.g. nvvm)",
    )
    parser.add_argument(
        "--render", action="store_true",
        help="Enable live window rendering (requires --target spirv)",
    )
    parser.add_argument(
        "--no-split", action="store_true",
        help="Do not auto-split loop bodies into flow/structural "
             "(extract only whole loops)",
    )
    parser.add_argument(
        "--kernel-report", action="store_true",
        help="Analyze and report kernel extraction decisions, "
             "then exit without generating device code",
    )
    parser.add_argument(
        "--promote-locals", action="store_true",
        help="Auto-promote leaked locals to buffer arrays to enable "
             "GPU extraction across flow/structural boundaries",
    )

    # Simulation sizing
    parser.add_argument(
        "-N", type=int, default=None,
        help="Override DEFAULT_N (starting particle count)",
    )
    parser.add_argument(
        "-M", type=int, default=None,
        help="Override MAXPART (max particle capacity). "
             "If omitted, uses the value in the source file; "
             "runtime VRAM capping may reduce it further.",
    )

    # Math — fast-math split into independent CPU/GPU controls.
    # --fast-math kept as a one-release deprecation alias that sets both.
    parser.add_argument(
        "--cpu-fast-math", action="store_true",
        help="Pass -ffast-math to GCC (allows reassociation, breaks IEEE; "
             "use only when no algebraic invariants depend on bit-exact "
             "float math)",
    )
    parser.add_argument(
        "--gpu-fast-math", action="store_true",
        help="Allow GPU fast-math intrinsics on supported backends (NVVM "
             "math intrinsic swap). SPIRV currently does not consume this "
             "flag; CPU codegen is unaffected",
    )
    parser.add_argument(
        "--fast-math", action="store_true",
        help="DEPRECATED: sets both --cpu-fast-math and --gpu-fast-math. "
             "Use the specific flags instead. Will be removed in a "
             "future release.",
    )
    parser.add_argument(
        "--precision", choices=["f32", "f64"], default="f64",
        help="Floating-point precision for REAL type (default: f64)",
    )

    # Arena (for ALLOCATABLE arrays — bump allocator, see
    # Spec/Arena_Lowering_Brief.md)
    parser.add_argument(
        "--arena-size", type=str, default=None,
        help="Override the default 1 GiB ALLOCATABLE arena size. "
             "Accepts plain bytes (16777216), or with K/M/G suffix "
             "(16M, 2G). No effect on programs that don't use ALLOCATABLE.",
    )

    args = parser.parse_args()

    # Set global precision before any IR is built
    from .ir import set_real_precision
    set_real_precision(32 if args.precision == "f32" else 64)

    try:
        # --emit-ir: dump IR and exit
        if args.emit_ir:
            from .lexer import Lexer
            from .parser import Parser
            from .checker import Checker
            from .ir_builder import IRBuilder
            from .ir import dump_module

            with open(args.source) as f:
                source = f.read()
            tokens = Lexer(source).tokenize()
            tree = Parser(tokens).parse()
            Checker().check(tree)
            mod = IRBuilder().build(tree, source_file=args.source)
            print(dump_module(mod))
            return

        # --kernel-report: analyze and report, no codegen
        if args.kernel_report:
            from .lexer import Lexer
            from .parser import Parser
            from .checker import Checker
            from .ir_builder import IRBuilder
            from .ir_gpu import extract_kernels, promote_locals, linearize_nested_loops

            with open(args.source) as f:
                source = f.read()
            tokens = Lexer(source).tokenize()
            tree = Parser(tokens).parse()
            Checker().check(tree)
            mod = IRBuilder().build(tree, source_file=args.source)
            from .ir_inline import inline_subroutines
            inline_diags = inline_subroutines(mod)
            if inline_diags:
                print("Subroutine inlining:")
                for d in inline_diags:
                    print(f"  {d}")
                print()
            if args.promote_locals:
                promo_diags = promote_locals(mod)
                if promo_diags:
                    print("Local promotion:")
                    for d in promo_diags:
                        print(d)
                    print()
            linearize_nested_loops(mod)
            plan = extract_kernels(mod, allow_split=not args.no_split)

            if not plan.kernels and not plan.rejections:
                print("No loops found.")
                return

            if plan.kernels:
                print(f"Extractable kernels: {len(plan.kernels)}")
                for k in plan.kernels:
                    tag = " (SPLIT)" if k.is_partial else ""
                    print(f"  kernel_{k.kernel_id}: line {k.source_line}{tag}")
                    print(f"    loop var:    {k.loop_var}")
                    print(f"    bound:       {k.loop_bound}")
                    print(f"    arrays read: {sorted(k.arrays_read)}")
                    print(f"    arrays write:{sorted(k.arrays_written)}")
                    print(f"    scalars in:  {sorted(k.scalars_read)}")
                    if k.scalars_local:
                        print(f"    locals:      {sorted(k.scalars_local)}")
                print()

            if plan.rejections:
                print(f"Rejected loops: {len(plan.rejections)}")
                for line, reason in plan.rejections:
                    print(f"  line {line}: {reason}")

            return

        # Build parameter overrides from -N and -M flags
        param_overrides = {}
        if args.N is not None:
            param_overrides["DEFAULT_N"] = args.N
        if args.M is not None:
            param_overrides["MAXPART"] = args.M

        # Parse --arena-size with optional K/M/G suffix.
        arena_size = None
        if args.arena_size is not None:
            s = args.arena_size.strip().upper()
            mult = 1
            if s.endswith("K"):
                mult = 1 << 10
                s = s[:-1]
            elif s.endswith("M"):
                mult = 1 << 20
                s = s[:-1]
            elif s.endswith("G"):
                mult = 1 << 30
                s = s[:-1]
            try:
                arena_size = int(s) * mult
            except ValueError:
                print(f"Error: invalid --arena-size '{args.arena_size}'",
                      file=sys.stderr)
                sys.exit(1)
            if arena_size <= 0:
                print(f"Error: --arena-size must be positive",
                      file=sys.stderr)
                sys.exit(1)

        # Resolve fast-math: deprecated --fast-math implies both new flags.
        cpu_fast_math = args.cpu_fast_math
        gpu_fast_math = args.gpu_fast_math
        if args.fast_math:
            print("WARNING: --fast-math is deprecated and applies BOTH "
                  "--cpu-fast-math and --gpu-fast-math. Use the specific "
                  "flags instead. See Spec/x86_Determinism_Audit.md for "
                  "the rationale.", file=sys.stderr)
            cpu_fast_math = True
            gpu_fast_math = True

        c_code = compile_file(args.source, output=args.output, emit_c=args.emit_c,
                              cpu_fast_math=cpu_fast_math,
                              gpu_fast_math=gpu_fast_math,
                              target=args.target,
                              no_split=args.no_split,
                              render=args.render,
                              promote_locals=args.promote_locals,
                              param_overrides=param_overrides,
                              arena_size=arena_size)
        if args.emit_c:
            print(c_code)
        else:
            out_name = args.output or args.source.rsplit(".", 1)[0]
            print(f"Compiled successfully: ./{out_name}")
    except MCLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {args.source}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

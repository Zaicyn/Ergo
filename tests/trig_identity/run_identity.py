#!/usr/bin/env python3
"""run_identity.py — three-path f32 sin/cos bit-identity harness.

Evaluates the shared f32 trig core over one procedurally-generated domain
(tests/trig_identity/dump_trig.ergo writes /tmp/trig32_domain.bin:
[M domain][M sin][M cos], f32 little-endian) on all three paths and
byte-compares the full result sections — no ulp tolerance, no NaN
normalization (all three paths return the canonical qNaN 0xffc00000 for
NaN/Inf input, so even payloads must match):

  CPU   : core/runtime/ergo_math_kernels.h  (_ergo_sinf/_ergo_cosf)
  SPIR-V: core/backends/spirv.py            (_emit_trig32_helper)
  GLSL  : core/runtime/ergo_trig32.glsl     (via glsl_dump.comp + run_glsl)

Usage:  python tests/trig_identity/run_identity.py
Exit 0 on PASS (all three sections byte-identical), 1 otherwise.
"""
import os
import struct
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
M = 1400093  # must match dump_trig.ergo's PARAMETER M

DOM = "/tmp/trig32_domain.bin"
CPU_OUT = "/tmp/trig32_cpu.bin"
GPU_OUT = "/tmp/trig32_gpu.bin"
GLSL_OUT = "/tmp/trig32_glsl.bin"
RUN_GLSL = "/tmp/run_glsl"
GLSL_SPV = "/tmp/glsl_dump.spv"


def run(cmd, **kw):
    print("+", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
        print(f"FAIL: command exited {r.returncode}")
        sys.exit(1)
    return r


def sections(path):
    raw = open(path, "rb").read()
    assert len(raw) == M * 4 * 3, f"{path}: {len(raw)} bytes, expected {M*4*3}"
    return raw[: M * 4], raw[M * 4 : 2 * M * 4], raw[2 * M * 4 :]


def diff_report(name, a_sin, b_sin, a_cos, b_cos):
    sa = struct.unpack(f"<{M}I", a_sin)
    sb = struct.unpack(f"<{M}I", b_sin)
    ca = struct.unpack(f"<{M}I", a_cos)
    cb = struct.unpack(f"<{M}I", b_cos)
    sd = [i for i in range(M) if sa[i] != sb[i]]
    cd = [i for i in range(M) if ca[i] != cb[i]]
    print(f"  {name}: sin diffs {len(sd)}, cos diffs {len(cd)}")
    for i in sd[:8]:
        print(f"    sin[{i}] {sa[i]:08x} vs {sb[i]:08x}")
    for i in cd[:8]:
        print(f"    cos[{i}] {ca[i]:08x} vs {cb[i]:08x}")
    return not sd and not cd


def main():
    # 1. CPU path (owned kernel in the C header, driver build flags)
    run([sys.executable, "-m", "core", "tests/trig_identity/dump_trig.ergo",
         "--precision", "f32", "-o", "/tmp/trig_cpu"])
    run(["/tmp/trig_cpu"])
    os.rename(DOM, CPU_OUT)

    # 2. SPIR-V compute path (owned branchless core)
    run([sys.executable, "-m", "core", "tests/trig_identity/dump_trig.ergo",
         "--precision", "f32", "--target", "spirv", "-o", "/tmp/trig_gpu"])
    run(["/tmp/trig_gpu"])
    os.rename(DOM, GPU_OUT)

    # 3. GLSL render-shader core (same device, via the standalone runner)
    run(["glslc", "-fshader-stage=comp", "-I", "core/runtime",
         "tests/trig_identity/glsl_dump.comp", "-o", GLSL_SPV])
    if not os.path.exists(RUN_GLSL):
        run(["gcc", "-O2", os.path.join(HERE, "run_glsl.c"),
             "-o", RUN_GLSL, "-lvulkan"])
    run([RUN_GLSL, GLSL_SPV, CPU_OUT, GLSL_OUT, str(M)])

    # 4. three-way byte compare
    d_c, s_c, c_c = sections(CPU_OUT)
    d_g, s_g, c_g = sections(GPU_OUT)
    d_l, s_l, c_l = sections(GLSL_OUT)
    ok = True
    if not (d_c == d_g == d_l):
        print("FAIL: domain sections differ between paths")
        ok = False
    if s_c == s_g == s_l and c_c == c_g == c_l:
        print(f"  sin+cos sections byte-identical across CPU/SPIR-V/GLSL "
              f"({M} samples x 2 fns x 3 paths)")
    else:
        ok = False
        diff_report("CPU vs SPIR-V", s_c, s_g, c_c, c_g)
        diff_report("CPU vs GLSL  ", s_c, s_l, c_c, c_l)
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

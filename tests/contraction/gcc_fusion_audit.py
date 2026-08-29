#!/usr/bin/env python3
"""gcc_fusion_audit.py — close the loop between the contraction lint's
rule set (core/ir_contract.py) and gcc's actual behavior, working from
emitted C (what gcc actually sees).

Per program (or raw C file):
  1. emit C (python -m core <prog> --emit-c), parse fp statements
  2. find fusible a*b±c sites; classify each per the documented rule
     (predicted FUSE / NOFUSE) and tag shape classes (call-factor,
     all-const, division, (a+b)*c, NEG-fold, both-mul, multi-use,
     cross-block)
  3. compile with the recipe + -fdump-tree-optimized; for each site,
     read the optimized GIMPLE: is the add's result ever a .FMA
     (fused), only ever plain +/- (unfused), both (path-dependent),
     or absent (folded/eliminated)
  4. report per-site predicted vs actual

Usage:
  python3 tests/contraction/gcc_fusion_audit.py <prog.ergo|file.c> ...
  python3 tests/contraction/gcc_fusion_audit.py --corpus   (all corpus +
      physics engines + the kernel header)
"""
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

RECIPE = ["-O3", "-fwrapv", "-march=x86-64-v3", "-ffp-contract=fast",
          "-fno-math-errno", "-std=c11"]

STMT = re.compile(r"^\s*(?:double\s+|float\s+)?([A-Za-z_]\w*)\s*=\s*(.+?);")
BINOP = re.compile(r"^\(?\s*(.+?)\s*([+\-*/])\s*(.+?)\s*\)?$")
NEG = re.compile(r"^\(?\s*-\s*([A-Za-z_]\w*)\s*\)?$")
CALL = re.compile(r"^[A-Za-z_]\w*\s*\(.*\)\s*$")
LIT = re.compile(r"^-?(\d+\.?\d*(e[+-]?\d+)?|0x[0-9a-fA-Fp\.\+\-]+)f?$")
DECL = re.compile(r"^\s*(double|float|int|long long|char)\s+")


def parse_c(text):
    """returns [(scope_name, decls, defs), ...] — one scope per function
    (headers reuse short names across functions).  Comments stripped;
    inline `x ± a*b` forms recognized."""
    scopes = []
    decls = {}
    defs = {}
    fname = "toplevel"

    def close_scope():
        nonlocal decls, defs, fname
        if defs or decls:
            scopes.append((fname, decls, defs))
        decls, defs = {}, {}
        fname = "toplevel"

    def split_top_commas(s):
        parts, depth, cur = [], 0, ""
        for ch in s:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            if ch == "," and depth == 0:
                parts.append(cur)
                cur = ""
            else:
                cur += ch
        parts.append(cur)
        return parts

    def record(name, expr, ln):
        # strip one layer of fully-enclosing parens (ergo codegen wraps
        # every binary op: "(S1 + _t_5)")
        if expr.startswith("(") and expr.endswith(")"):
            depth = 0
            bal = True
            for j, ch in enumerate(expr):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0 and j < len(expr) - 1:
                        bal = False
                        break
            if bal and depth == 0:
                expr = expr[1:-1].strip()
        kind = "other"
        if NEG.match(expr):
            kind = "neg"
        elif CALL.match(expr):
            kind = "call"
        else:
            # tokenize at paren depth 0; toks[i] = (text, op_after_text)
            toks = []
            depth = 0
            cur = ""
            for ch in expr:
                if ch in "([":
                    depth += 1
                elif ch in ")]":
                    depth -= 1
                if depth == 0 and ch in "+-*/":
                    toks.append((cur.strip(), ch))
                    cur = ""
                else:
                    cur += ch
            toks.append((cur.strip(), ""))
            # a top-level +/- at toks[i][1] splits lhs=toks[..i] from
            # rhs=toks[i+1..]; the LAST such op wins (site op)
            addsub = [i for i, (_, o) in enumerate(toks)
                      if o and o in "+-"]
            if addsub:
                i = addsub[-1]
                op = toks[i][1]
                lhs = ("".join(t[0] + t[1] for t in toks[:i])
                       + toks[i][0]).strip()
                rhs = "".join(t[0] + t[1] for t in toks[i + 1:]).strip()
                # unary minus at start: "-a" — not a binary site
                if lhs == "" and i == 0:
                    defs[name] = ("neg", expr, ln, None, None)
                    return
                defs[name] = ("sub" if op == "-" else "add",
                              expr, ln, lhs, rhs)
                return
            muldiv = [i for i, (_, o) in enumerate(toks)
                      if o and o in "*/"]
            if muldiv:
                i = muldiv[-1]
                lhs = ("".join(t[0] + t[1] for t in toks[:i])
                       + toks[i][0]).strip()
                rhs = "".join(t[0] + t[1] for t in toks[i + 1:]).strip()
                defs[name] = ("div" if toks[i][1] == "/" else "mul",
                              expr, ln, lhs, rhs)
                return
        defs[name] = (kind, expr, ln, None, None)

    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.split("//")[0] if "http" not in raw else raw
        # function boundary: close the current scope
        fm = re.match(r"^(?:static\s+(?:inline\s+)?)?"
                      r"(?:void|int|double|float|long|char)\s+"
                      r"([A-Za-z_]\w*)\s*\([^;]*$", raw.strip())
        if fm and ";" not in raw:
            close_scope()
            fname = fm.group(1)
        m = re.match(r"^\s*return\s+(.+?);", line)
        if m:
            record(f"_ret{ln}", m.group(1).strip(), ln)
            continue
        m = DECL.match(line)
        if m:
            for part in split_top_commas(
                    line.strip().rstrip(";")[len(m.group(1)):]):
                if "=" in part:
                    nm, expr = part.split("=", 1)
                    nm = re.sub(r"\[.*\]", "", nm).strip()
                    if re.match(r"^[A-Za-z_]\w*$", nm.strip()):
                        decls[nm.strip()] = m.group(1)
                        record(nm.strip(), expr.strip(), ln)
                else:
                    nm = re.sub(r"\[.*\]", "", part).strip()
                    if re.match(r"^[A-Za-z_]\w*$", nm):
                        decls[nm] = m.group(1)
            continue
        m = STMT.match(line)
        if not m:
            continue
        record(m.group(1), m.group(2), ln)
    close_scope()
    return scopes


def is_real(name, decls):
    return decls.get(name) in ("double", "float")


def find_sites(decls, defs):
    """fusible add/sub sites; each: dict(name, op, line, side, muldef,
    shape classes)"""
    sites = []

    def as_mul(text):
        """an inline `A * B` mul expression (top-level single *)"""
        toks, depth, cur = [], 0, ""
        for ch in text:
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            if depth == 0 and ch in "*/":
                toks.append((cur.strip(), ch))
                cur = ""
            else:
                cur += ch
        toks.append((cur.strip(), ""))
        muls = [i for i, (_, o) in enumerate(toks) if o == "*"]
        if len(toks) == 2 and len(muls) == 1:
            return ("mul", text, 0, toks[0][0], toks[1][0])
        return None

    for name, d in defs.items():
        kind, expr, ln, lhs, rhs = d
        if kind not in ("add", "sub"):
            continue
        if not is_real(name, decls):
            continue

        def muldef(opname):
            """the mul (inline form, or a def, optionally behind a neg)"""
            if opname is None:
                return None
            dd = defs.get(opname)
            if dd is None:
                # inline mul expression as the operand: `x + a*b`
                return (as_mul(opname) or None) and (as_mul(opname), False)
            if dd[0] == "neg":
                nm = NEG.match(dd[1])
                if not nm:
                    return None
                dd2 = defs.get(nm.group(1))
                if dd2 and dd2[0] == "mul":
                    return dd2, True
                return None
            if dd[0] == "mul":
                return dd, False
            return None

        lm = muldef(lhs)
        rm = muldef(rhs)
        if lm is None and rm is None:
            continue
        side = "L" if lm is not None else "R"
        mul, neg = (lm if lm else rm)
        # all-constant mul?
        m_lhs, m_rhs = mul[3], mul[4]
        allconst = LIT.match(m_lhs or "") and LIT.match(m_rhs or "")
        # call-factor: a mul operand that is a call result
        callfac = any((defs.get(o) and defs[o][0] == "call")
                      for o in (m_lhs, m_rhs) if o)
        classes = []
        if lm and rm:
            classes.append("both-mul")
        if neg:
            classes.append("neg-fold")
        if allconst:
            classes.append("all-const")
        if callfac:
            classes.append("call-factor")
        sites.append({"name": name, "op": kind, "line": ln, "side": side,
                      "mul": mul, "neg": neg, "classes": classes,
                      "expr": expr, "lhs": lhs, "rhs": rhs})
    return sites


def predict(site):
    """the documented rule's prediction"""
    if "all-const" in site["classes"]:
        return "NOFUSE"
    return "FUSE"


def loop_spans(c_text):
    """line spans of for/while loop bodies (1-based, brace-matched)."""
    lines = c_text.splitlines()
    spans = []
    i = 0
    while i < len(lines):
        if re.match(r"^\s*(for|while)\s*\(", lines[i]):
            start = i + 1
            depth = 0
            opened = False
            j = i
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if "{" in lines[j]:
                    opened = True
                if opened and depth == 0:
                    break
                j += 1
            spans.append((start, j + 1))
            i = j + 1
        else:
            i += 1
    return spans


def gcc_truth(c_text, sites):
    """Compile with the recipe (-g); read the RTL final dump, which tags
    every insn with its source line and carries fusion in the pattern
    name ({*fma_fmadd_v4df} / {*adddf3} ...).  Per site: any fma insn at
    the site's line or its mul-def line (±2 drift) => fused; only plain
    add/sub/mul there => unfused; both => mixed (path-dependent);
    neither => absent (folded/eliminated)."""
    if not sites:
        return {}
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "p.c")
        with open(src, "w") as f:
            f.write("\n".join("" if ln.lstrip().startswith("#line")
                              else ln
                              for ln in c_text.splitlines()))
        r = subprocess.run(["gcc", "-c", src, "-g",
                            "-o", os.path.join(td, "p.o"),
                            "-I" + os.path.join(REPO, "core", "runtime")]
                           + RECIPE + ["-fdump-rtl-final"],
                           cwd=td, capture_output=True)
        if r.returncode != 0:
            return None
        rdumps = [f for f in os.listdir(td) if f.endswith(".final")]
        if not rdumps:
            return None
        rtl = open(os.path.join(td, rdumps[0])).read()
    fma_lines = []   # (line, set-of-orig-temp-names)
    plain_lines = set()
    ORIG = re.compile(r"\[orig:\d+\s+([A-Za-z_]\w*)|vect_([A-Za-z_]\w*?)_")
    for line in rtl.splitlines():
        m = re.search(r'"(?:/[^"]*)?p\.c":(\d+)', line)
        if not m:
            continue
        ln = int(m.group(1))
        if re.search(r"\*fn?m|[(]fma[:(]", line):
            names = set()
            for om in ORIG.finditer(line):
                names.add(om.group(1) or om.group(2))
            fma_lines.append((ln, names))
        elif re.search(r"fop_[ds]f|\*?(add|sub|mul|div)[sd]f", line):
            plain_lines.add(ln)
    out = {}
    for s in sites:
        watch = [(s["line"], -2, 6)]
        if s["mul"] and s["mul"][2]:
            watch.append((s["mul"][2], -2, 2))
        # temp names a fused insn at this site would reference: the mul's
        # factor names (mul[3], mul[4]) and the add's other operand
        names = {s["name"]}
        mul = s["mul"]
        if mul and mul[0] == "mul":
            for o in (mul[3], mul[4]):
                if o and re.match(r"^[A-Za-z_]\w*$", o):
                    names.add(o)
        for o in (s.get("lhs"), s.get("rhs")):
            if o and re.match(r"^[A-Za-z_]\w*$", o):
                names.add(o)
        fused = False
        for ln, onames in fma_lines:
            if not any(w + lo <= ln <= w + hi for w, lo, hi in watch):
                continue
            if not onames or onames & names:
                fused = True
                break
        plain = any(any(w + lo <= ln <= w + hi for ln in plain_lines)
                    for w, lo, hi in watch)
        if fused and plain:
            out[s["line"]] = "mixed"
        elif fused:
            out[s["line"]] = "fused"
        elif plain:
            out[s["line"]] = "unfused"
        else:
            out[s["line"]] = "absent"
    return out


def audit_c(c_text, label):
    rows = []
    sites = []
    for scope, decls, defs in parse_c(c_text):
        for s in find_sites(decls, defs):
            s["scope"] = scope
            sites.append(s)
    truth = gcc_truth(c_text, sites) if sites else {}
    for s in sites:
        pred = predict(s)
        act = (truth or {}).get(s["line"], "?")
        # Verdict semantics: the lint's rule is a MAY analysis ("this site
        # is fusible; the CPU recipe may contract it").  Verdicts:
        #   match   — pred FUSE & gcc fuses deterministically, or pred
        #             NOFUSE & gcc never fuses
        #   fragile — pred FUSE & gcc fuses on some paths only (mixed),
        #             or never (unfused) — PHI/callee-shape dependent
        #             (the documented lint gap: reported, not fixed)
        #   absent  — attribution gap (folded/eliminated/drift)
        #   MISMATCH — pred NOFUSE but gcc fuses (dangerous) or pred
        #             FUSE with no possible fusion (does not occur here)
        if act == "absent" or act == "?":
            verdict = "absent"
        elif pred == "FUSE" and act == "fused":
            verdict = "match"
        elif pred == "NOFUSE" and act == "unfused":
            verdict = "match"
        elif pred == "FUSE" and act in ("mixed", "unfused"):
            verdict = "fragile"
        else:
            verdict = "mismatch"
        rows.append({**s, "pred": pred, "actual": act,
                     "match": verdict == "match", "verdict": verdict})
    return rows
    rows = []
    for s in sites:
        pred = predict(s)
        act = (truth or {}).get(s["name"], "?")
        match = (pred == "FUSE" and act == "fused") or \
                (pred == "NOFUSE" and act in ("unfused", "absent"))
        rows.append({**s, "pred": pred, "actual": act, "match": match})
    return rows


def emit_c(path):
    r = subprocess.run([sys.executable, "-m", "core", path, "--emit-c"],
                       cwd=REPO, capture_output=True, text=True,
                       timeout=300)
    if r.returncode != 0:
        return None
    return r.stdout


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    targets = []
    if args[0] == "--corpus":
        import json
        audit = json.load(open(os.path.join(
            REPO, "tests", "golden", "corpus_audit.json")))
        for e in audit["files"]:
            if e["cls"] in ("PASS", "GPU-PASS"):
                targets.append(os.path.join(REPO, e["file"]))
        for extra in ("min/ribosome/ul18_stag5.ergo",
                      "min/wigner/h2_wig_hhb.ergo",
                      "min/ab/schrod_2d_stream.ergo"):
            targets.append(os.path.join(REPO, extra))
        import glob
        for d in ("min/dirac", "min/dendrite"):
            targets += sorted(glob.glob(os.path.join(REPO, d, "*.ergo")))
        targets.append(os.path.join(REPO, "tests", "fusible_stress.ergo"))
        targets.append(os.path.join(REPO, "core", "runtime",
                                    "ergo_math_kernels.h"))
    else:
        targets = [a if a.endswith(".ergo") else a for a in args]

    all_rows = []
    for t in targets:
        label = os.path.relpath(t, REPO) if t.startswith(REPO) else t
        if t.endswith(".c"):
            c_text = open(t).read()
        elif t.endswith(".h"):
            # a kernel header alone is a dead TU (gcc drops uncalled
            # static-inline functions before RTL) — drive every public
            # kernel once so the sites exist in the dump
            c_text = open(t).read() + """
int main(int argc, char **argv) {
    double xd = argc * 1.5, yd = argc * 0.25;
    float xf = (float)xd, yf = (float)yd;
    volatile double sd = _ergo_sin(xd) + _ergo_cos(xd) + _ergo_exp(xd)
        + _ergo_log(xd) + _ergo_atan2(xd, yd) + _ergo_pow(xd, yd);
    volatile float sf = _ergo_sinf(xf) + _ergo_cosf(xf) + _ergo_expf(xf)
        + _ergo_logf(xf) + _ergo_atan2f(xf, yf) + _ergo_powf(xf, yf);
    (void)sd; (void)sf;
    return 0;
}
"""
        else:
            c_text = emit_c(t)
        if c_text is None:
            print(f"SKIP {label} (emit failed)", file=sys.stderr)
            continue
        rows = audit_c(c_text, label)
        for r in rows:
            r["prog"] = label
        all_rows += rows
        print(f"{label}: {len(rows)} sites", file=sys.stderr)

    # aggregate
    n = len(all_rows)
    nmatch = sum(1 for r in all_rows if r["verdict"] == "match")
    nfrag = sum(1 for r in all_rows if r["verdict"] == "fragile")
    nabs = sum(1 for r in all_rows if r["verdict"] == "absent")
    nmism = sum(1 for r in all_rows if r["verdict"] == "mismatch")
    coverable = n - nabs
    print(f"\nsites: {n}  match: {nmatch}  fragile(path-dependent): "
          f"{nfrag}  attribution-gap: {nabs}  MISMATCH: {nmism}")
    print(f"coverage over attributed sites: "
          f"{100.0 * nmatch / max(coverable, 1):.1f}%  "
          f"(fragile {nfrag} = {100.0 * nfrag / max(coverable, 1):.1f}%)")
    from collections import Counter
    by_class = Counter()
    verdict_class = Counter()
    for r in all_rows:
        cls = "+".join(r["classes"]) or "plain"
        by_class[cls] += 1
        verdict_class[(cls, r["verdict"])] += 1
    print("\nby class: total / match / fragile / absent / mismatch")
    for cls, cnt in by_class.most_common():
        print(f"  {cls:24s} {cnt:4d} / {verdict_class[(cls,'match')]}"
              f" / {verdict_class[(cls,'fragile')]} / "
              f"{verdict_class[(cls,'absent')]} / "
              f"{verdict_class[(cls,'mismatch')]}")
    print("\nMISMATCHES (the dangerous direction — none expected):")
    for r in all_rows:
        if r["verdict"] == "mismatch":
            print(f"  {r['prog']}:{r['line']} {r['op']} {r['expr'][:60]}"
                  f"  pred={r['pred']} actual={r['actual']}")
    fragile = Counter()
    for r in all_rows:
        if r["verdict"] == "fragile" or "call-factor" in r["classes"]:
            fragile[r["prog"]] += 1
    print("\nprograms with PHI-shape/inline-fragile fusion sites:")
    for prog, cnt in fragile.most_common():
        print(f"  {prog}  ({cnt} sites)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

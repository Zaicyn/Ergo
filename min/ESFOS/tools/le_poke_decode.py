#!/usr/bin/env python3
"""Decode ESP32-S3 BT register poke tables from linked firmware disassembly.

Abstract-interprets straight-line Xtensa RMW sequences (l32r/movi/and/or/
slli/extui/l32i/s32i) in r_rf_rw_v9_le_init, r_rwble_hw_disable (+ tiny
enable/disable), resolving literal pools from section dumps. Emits the
ordered (addr, and_mask, or_bits) poke ops plus poll loops.

Usage: le_poke_decode.py <firmware.elf> <objdump> ; outputs poke_tables.txt
"""
import re
import subprocess
import sys

MEMW = 0x60000000


def run(objdump, elf, args):
    p = subprocess.run([objdump] + args + [elf],
                       capture_output=True, text=True)
    return p.stdout


def mem_image(objdump, elf, lo, hi):
    """word dict for [lo,hi) via -s dumps."""
    out = run(objdump, elf, ["-s", "--start-address=0x%x" % lo,
                             "--stop-address=0x%x" % hi])
    mem = {}
    for m in re.finditer(r"^\s*([0-9a-f]+) ((?:[0-9a-f]{2,8} ?)+)",
                         out, re.M):
        base = int(m.group(1), 16)
        toks = m.group(2).split()
        raw = "".join(toks)
        # objdump -s groups vary; rebuild bytes: pairs of hex chars
        hx = re.sub(r"\s", "", m.group(2))
        bs = bytes.fromhex(hx)
        for i in range(0, len(bs) - 3, 4):
            mem[base + i] = int.from_bytes(bs[i:i + 4], "little")
    return mem


def dis(objdump, elf, lo, hi):
    out = run(objdump, elf, ["-d", "--start-address=0x%x" % lo,
                             "--stop-address=0x%x" % hi])
    ins = []
    for line in out.splitlines():
        m = re.match(r"^\s*([0-9a-f]+):\t[0-9a-f]+\s*\t(\S+)(?:\t(.*))?$",
                     line)
        if m:
            ins.append((int(m.group(1), 16), m.group(2),
                        (m.group(3) or "").strip()))
    return ins


def reg(s):
    m = re.match(r"a(\d+)$", s)
    return int(m.group(1)) if m else None


def imm(s):
    s = s.strip()
    try:
        return int(s, 0)
    except ValueError:
        return None


def decode(ins, mem):
    regs = {}  # reg -> int | None
    ops = []
    for pc, op, args in ins:
        a = [x.strip() for x in args.split(",")] if args else []
        if op == "l32r" and len(a) == 2:
            r, tgt = reg(a[0]), int(a[1].split()[0], 16)
            regs[r] = mem.get(tgt)
        elif op in ("movi", "movi.n") and len(a) == 2:
            regs[reg(a[0])] = imm(a[1]) & 0xFFFFFFFF
        elif op == "slli" and len(a) == 3:
            v = regs.get(reg(a[1]))
            regs[reg(a[0])] = ((v << imm(a[2])) & 0xFFFFFFFF
                               if v is not None else None)
        elif op == "srli" and len(a) == 3:
            v = regs.get(reg(a[1]))
            regs[reg(a[0])] = ((v >> imm(a[2])) & 0xFFFFFFFF
                               if v is not None else None)
        elif op in ("and", "or", "xor") and len(a) == 3:
            x, y = regs.get(reg(a[1])), regs.get(reg(a[2]))
            d = reg(a[0])
            if isinstance(y, tuple) and isinstance(x, int):
                x, y = y, x
            if isinstance(x, int) and isinstance(y, int):
                regs[d] = x & y if op == "and" else (
                    x | y if op == "or" else x ^ y)
            elif op in ("and", "or") and isinstance(y, int):
                if isinstance(x, tuple) and x[0] == "MEM":
                    _, addr = x
                    regs[d] = ("RMW", addr,
                               y if op == "and" else 0xFFFFFFFF,
                               0 if op == "and" else y)
                elif isinstance(x, tuple) and x[0] == "RMW":
                    _, addr, A, O = x
                    regs[d] = ("RMW", addr, A & y, O & y) if op == "and" \
                        else ("RMW", addr, A, O | y)
                else:
                    regs[d] = None
            else:
                regs[d] = None
        elif op == "extui" and len(a) == 4:
            v = regs.get(reg(a[1]))
            sh, wd = imm(a[2]), imm(a[3])
            regs[reg(a[0])] = (((v >> sh) & ((1 << wd) - 1))
                               if isinstance(v, int) else None)
        elif op in ("l32i", "l32i.n") and len(a) == 3:
            b = regs.get(reg(a[1]))
            try:
                off = imm(a[2])
            except TypeError:
                off = 0
            regs[reg(a[0])] = ("MEM", b + off
                               if isinstance(b, int) else None)
        elif op in ("s32i", "s32i.n") and len(a) == 3:
            v = regs.get(reg(a[0]))
            b = regs.get(reg(a[1]))
            addr = b + imm(a[2]) if isinstance(b, int) else None
            if isinstance(v, tuple) and v[0] == "RMW":
                _, ra, A, O = v
                ops.append(("W", ra if addr is None else addr,
                            "(v&0x%08x)|0x%08x" % (A, O)))
            elif isinstance(v, tuple):
                ops.append(("W", addr, "MEM"))
            else:
                ops.append(("W", addr, v))
        elif op in ("bltz", "bgez", "beqz.n", "bnez", "bne", "beq",
                    "blt", "bge"):
            ops.append(("BR", args))
        elif op in ("entry", "retw", "retw.n", "memw", "isync",
                    "rsync"):
            pass
        else:
            ops.append(("?", "%s %s" % (op, args)))
    return ops


def main():
    elf, objdump = sys.argv[1], sys.argv[2]
    mem = mem_image(objdump, elf, 0x42000000, 0x42027000)
    fns = {
        "le_enable": (0x40004C44, 0x40004C44 + 0x20),
        "le_init": (0x42026630, 0x42026900),
        "hw_disable": (0x42032B30, 0x42032C80),
    }
    out = []
    for name, (lo, hi) in fns.items():
        ins = dis(objdump, elf, lo, hi)
        out.append("== %s @0x%x ==" % (name, lo))
        for o in decode(ins, mem):
            if o[0] == "W" and isinstance(o[1], int):
                out.append("  W 0x%08x <= %s" %
                           (o[1], ("0x%08x" % o[2]
                                   if isinstance(o[2], int) else o[2])))
            else:
                out.append("  %s %s" % (o[0], o[1] if len(o) > 1 else ""))
    txt = "\n".join(out) + "\n"
    open("poke_tables.txt", "w").write(txt)
    print(txt)


if __name__ == "__main__":
    main()

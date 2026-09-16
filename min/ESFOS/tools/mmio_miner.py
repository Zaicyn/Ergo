#!/usr/bin/env python3
"""MMIO miner for the closed ESP32-S3 BT controller blob (libbtdm_app.a).

Disassembles every archive member, decodes literal pools (little-endian .word
preludes embedded in .text sections), propagates constant register values
through a light linear dataflow, and reports every memory access whose base
register is a resolved constant in the ESP32-S3 MMIO window. Purpose: enumerate
the undocumented register blocks the proprietary RF/baseband code touches
(e.g. the 0x60031000 BT-BB cluster, 0x60042000 RF sleep block).

Usage:
  mmio_miner.py --archive <libbtdm_app.a> \
                --objdump <xtensa-esp32s3-elf-objdump> [--work DIR]
                [--reg-base-h <reg_base.h>]

Outputs under <work>/out/:
  mmio_sites.txt        every resolved MMIO site (W/R, addr, size, value)
  undocumented.txt      undocumented clusters + sites (probe targets)
  summary_by_region.txt aggregated per documented peripheral region
  summary_by_fn.txt     functions with the most MMIO sites
  regions.txt           parsed peripheral base table
"""
import argparse
import collections
import os
import re
import subprocess
import sys

MMIO_LO = 0x60000000
MMIO_HI = 0x60200000

REGIONS = {}
REGIONS_SORTED = []

FALLBACK_REGIONS = {
    "UART": 0x60000000, "SPI1": 0x60002000, "SPI0": 0x60003000,
    "GPIO": 0x60004000, "FE2": 0x60005000, "FE": 0x60006000,
    "EFUSE": 0x60007000, "RTCCNTL": 0x60008000, "RTCIO": 0x60008400,
    "SENS": 0x60008800, "RTC_I2C": 0x60008C00, "IO_MUX": 0x60009000,
    "HINF": 0x6000B000, "UHCI1": 0x6000C000, "I2S": 0x6000F000,
    "UART1": 0x60010000, "BT": 0x60011000, "I2C_EXT": 0x60013000,
    "UHCI0": 0x60014000, "SLCHOST": 0x60015000, "RMT": 0x60016000,
    "PCNT": 0x60017000, "SLC": 0x60018000, "LEDC": 0x60019000,
    "NRX": 0x6001CC00, "BB": 0x6001D000, "PWM0": 0x6001E000,
    "TIMG0": 0x6001F000, "TIMG1": 0x60020000, "RTC_SLOWMEM": 0x60021000,
    "SYSTIMER": 0x60023000, "UART2": 0x6002E000, "USB_SERIAL_JTAG": 0x60038000,
    "AES": 0x6003A000, "RSA": 0x6003C000, "DIGITAL_SIGNATURE": 0x6003D000,
    "HMAC": 0x6003E000, "GDMA": 0x6003F000, "APB_SARADC": 0x60040000,
    "LCD_CAM": 0x60041000, "INTERRUPT": 0x600C2000,
}

RE_SECTION = re.compile(r'^Disassembly of section (.+):$')
RE_LABEL = re.compile(r'^([0-9a-fA-F]+) <([^>]+)>:$')
RE_INS = re.compile(r'^\s+([0-9a-fA-F]+):\t[0-9a-fA-F]+\s*\t(\S+)(?:\t(.*))?$')
RE_DATA = re.compile(r'^\s+([0-9a-fA-F]+):\t([0-9a-fA-F]{2}(?: [0-9a-fA-F]{2})*)\s*\t?$')
RE_RELOC = re.compile(r'^\s+([0-9a-fA-F]+): R_XTENSA_\S+\s+(.+)$')

REGS = {'a%d' % i for i in range(16)}
CONST = 0
RELOC = 1


class Site:
    __slots__ = ('member', 'section', 'func', 'offset', 'op', 'addr', 'size',
                 'value', 'memw')

    def __init__(self, member, section, func, offset, op, addr, size, value, memw):
        self.member, self.section = member, section
        self.func, self.offset = func, offset
        self.op, self.addr, self.size = op, addr, size
        self.value, self.memw = value, memw

    def row(self):
        v = '?' if self.value is None else '0x%x' % self.value
        r = classify(self.addr)
        reg = (r[0] + '+0x%x' % r[2]) if r else '?'
        return '%s\t0x%08x\t%s\t%s\t%s\t%s\t%s\t%s' % (
            'W' if self.op.startswith('s') else 'R',
            self.addr, self.size, v, '*' if self.memw else '',
            self.func, self.member, reg)


def load_regions(path):
    if path and os.path.exists(path):
        names = {}
        with open(path) as f:
            for line in f:
                m = re.match(r'#define\s+DR_REG_(\w+)_BASE\s+0x([0-9a-fA-F]+)', line)
                if m:
                    names[m.group(1)] = int(m.group(2), 16)
        if names:
            return names
    return dict(FALLBACK_REGIONS)


def classify(addr):
    if not (MMIO_LO <= addr < MMIO_HI):
        return None
    name, base = None, 0
    for n, b in REGIONS_SORTED:
        if b <= addr and b >= base:
            name, base = n, b
    return (name or 'UNKNOWN', base, addr - base)


def is_reg(s):
    return s in REGS


def _isnum(s):
    try:
        int(s.strip(), 0)
        return True
    except ValueError:
        return False


def _num(s):
    return int(s.strip(), 0)


def constv(v):
    return v[1] if v is not None and v[0] == CONST else None


def mem_site(sites, member, section, fn_name, offset, op, src, base, off,
             size, known, memw_flag):
    if base is None:
        return
    addr = base + off
    if not (MMIO_LO <= addr < MMIO_HI):
        return
    val = constv(known.get(src)) if op.startswith('s') else None
    sites.append(Site(member, section, fn_name, offset, op, addr, size, val,
                      memw_flag))


def analyze(insns, sites, member, section, fn_name, fn_start, cur_lit):
    known = {r: None for r in REGS}
    memw_flag = False
    for addr, mnemo, ops in insns:
        def K(r):
            return known.get(r)

        if mnemo in ('entry', 'nop', 'isync', 'rsync', 'esync', 'dsync'):
            pass
        elif mnemo == 'memw':
            memw_flag = True
        elif mnemo in ('movi', 'movi.n'):
            if len(ops) >= 2 and is_reg(ops[0]):
                known[ops[0]] = (_num(ops[1]), CONST) if _isnum(ops[1]) else None
        elif mnemo == 'l32r':
            if len(ops) >= 2 and is_reg(ops[0]):
                try:
                    t = int(ops[1].split()[0], 0)
                except ValueError:
                    known[ops[0]] = None
                    continue
                known[ops[0]] = cur_lit.get(t)
        elif mnemo in ('l32i', 'l32i.n'):
            if len(ops) >= 3 and is_reg(ops[0]) and is_reg(ops[1]):
                base = constv(K(ops[1]))
                off = _num(ops[2]) if _isnum(ops[2]) else 0
                mem_site(sites, member, section, fn_name, addr, mnemo, ops[0],
                         base, off, 4, known, memw_flag)
                known[ops[0]] = None
            elif len(ops) >= 2 and is_reg(ops[0]):
                known[ops[0]] = None
        elif mnemo in ('s32i', 's32i.n'):
            if len(ops) >= 3 and is_reg(ops[0]) and is_reg(ops[1]):
                base = constv(K(ops[1]))
                off = _num(ops[2]) if _isnum(ops[2]) else 0
                mem_site(sites, member, section, fn_name, addr, mnemo, ops[0],
                         base, off, 4, known, memw_flag)
        elif mnemo in ('l8ui', 'l16ui', 'l16si'):
            if len(ops) >= 3 and is_reg(ops[0]) and is_reg(ops[1]):
                base = constv(K(ops[1]))
                off = _num(ops[2]) if _isnum(ops[2]) else 0
                mem_site(sites, member, section, fn_name, addr, mnemo, ops[0],
                         base, off, 1 if 'l8' in mnemo else 2, known, memw_flag)
                known[ops[0]] = None
            elif len(ops) >= 2 and is_reg(ops[0]):
                known[ops[0]] = None
        elif mnemo in ('s8i', 's16i'):
            if len(ops) >= 3 and is_reg(ops[0]) and is_reg(ops[1]):
                base = constv(K(ops[1]))
                off = _num(ops[2]) if _isnum(ops[2]) else 0
                mem_site(sites, member, section, fn_name, addr, mnemo, ops[0],
                         base, off, 1 if 's8' in mnemo else 2, known, memw_flag)
        elif mnemo in ('mov.n', 'mov'):
            if len(ops) >= 2 and is_reg(ops[0]) and is_reg(ops[1]):
                known[ops[0]] = K(ops[1])
            elif len(ops) >= 2 and is_reg(ops[0]):
                known[ops[0]] = None
        elif mnemo == 'addi' or mnemo == 'addi.n' or mnemo == 'addmi':
            if len(ops) >= 3 and is_reg(ops[0]) and is_reg(ops[1]):
                v = constv(K(ops[1]))
                imm = _num(ops[2]) if _isnum(ops[2]) else 0
                known[ops[0]] = (v + imm, CONST) if v is not None else None
            elif len(ops) >= 2 and is_reg(ops[0]):
                known[ops[0]] = None
        elif mnemo == 'slli':
            if len(ops) >= 3 and is_reg(ops[0]):
                v = constv(K(ops[1]))
                sh = _num(ops[2]) if _isnum(ops[2]) else 0
                known[ops[0]] = (v << sh, CONST) if v is not None else None
            elif len(ops) >= 2 and is_reg(ops[0]):
                known[ops[0]] = None
        elif mnemo in ('srli', 'srai'):
            if len(ops) >= 3 and is_reg(ops[0]):
                v = constv(K(ops[1]))
                sh = _num(ops[2]) if _isnum(ops[2]) else 0
                known[ops[0]] = (v >> sh, CONST) if v is not None else None
            elif len(ops) >= 2 and is_reg(ops[0]):
                known[ops[0]] = None
        elif mnemo.startswith('callx') or mnemo.startswith('call'):
            for r in REGS:
                known[r] = None
        else:
            if len(ops) >= 1 and is_reg(ops[0]):
                known[ops[0]] = None
        memw_flag = False


def analyze_member(text, member, sites):
    work = []
    cur = None
    for raw in text.splitlines():
        s = raw.strip()
        m = RE_SECTION.match(s)
        if m:
            if cur is not None:
                work.append(cur)
            name = m.group(1)
            if name.startswith('.text') or name.startswith('.iram'):
                cur = {'section': name, 'insns': [], 'data': [], 'relocs': {},
                       'lits': {}, 'fn': []}
            else:
                cur = None
            continue
        if cur is None:
            continue
        m = RE_LABEL.match(s)
        if m:
            addr = int(m.group(1), 16)
            sym = m.group(2)
            mm = re.search(r'-0x([0-9a-fA-F]+)$', sym)
            if mm:
                cur['fn'].append((sym[:-(len(mm.group(0)))],
                                  addr + int(mm.group(1), 16)))
            else:
                cur['fn'].append((sym, addr))
            continue
        m = RE_INS.match(raw)
        if m:
            cur['insns'].append((int(m.group(1), 16), m.group(2),
                                 [o.strip() for o in
                                  (m.group(3).split(',') if m.group(3) else [])]))
            continue
        m = RE_DATA.match(raw)
        if m:
            cur['data'].append((int(m.group(1), 16),
                                [int(x, 16) for x in m.group(2).split()]))
            continue
        m = RE_RELOC.match(raw)
        if m:
            cur['relocs'][int(m.group(1), 16)] = m.group(2).split(' ')[0]
            continue
    if cur is not None:
        work.append(cur)

    for sec in work:
        for a, d in sec['data']:
            for off in range(0, len(d) - 3, 4):
                a2 = a + off
                if a2 in sec['relocs']:
                    sec['lits'][a2] = (RELOC, sec['relocs'][a2])
                else:
                    sec['lits'][a2] = (CONST, int.from_bytes(d[off:off + 4], 'little'))
        sec['insns'].sort(key=lambda t: t[0])
        fn = sec['fn']
        for i, (fnname, start) in enumerate(fn):
            nxt = fn[i + 1][1] if i + 1 < len(fn) else (1 << 62)
            seg = [t for t in sec['insns'] if start <= t[0] < nxt]
            if seg:
                analyze(seg, sites, member, sec['section'], fnname, start,
                        sec['lits'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive', required=True)
    ap.add_argument('--objdump', default=None)
    ap.add_argument('--work', default='/tmp/opencode/btdm')
    ap.add_argument('--reg-base-h', default=None)
    ap.add_argument('--no-cache', action='store_true')
    args = ap.parse_args()

    objdir = os.path.join(args.work, 'obj')
    disdir = os.path.join(args.work, 'dis')
    outdir = os.path.join(args.work, 'out')
    for d in (objdir, disdir, outdir):
        os.makedirs(d, exist_ok=True)

    global REGIONS
    REGIONS = load_regions(args.reg_base_h)
    global REGIONS_SORTED
    REGIONS_SORTED = sorted(REGIONS.items(), key=lambda kv: kv[1])
    with open(os.path.join(outdir, 'regions.txt'), 'w') as f:
        for n, b in REGIONS_SORTED:
            f.write('0x%08x  %s\n' % (b, n))

    od = args.objdump or ('/home/zaiken/.platformio/packages/toolchain-xtensa-'
                          'esp32s3/bin/xtensa-esp32s3-elf-objdump')
    if not os.path.exists(od):
        sys.exit('objdump not found: %s' % od)

    members = sorted(f for f in os.listdir(objdir) if f.endswith('.o'))
    if len(members) < 50:
        r = subprocess.run(['ar', 'x', args.archive], cwd=objdir)
        if r.returncode:
            sys.exit('ar x failed')
        members = sorted(f for f in os.listdir(objdir) if f.endswith('.o'))
    print('members: %d' % len(members))

    all_sites = []
    for idx, name in enumerate(members):
        dst = os.path.join(disdir, name + '.txt')
        text = None
        if os.path.exists(dst) and not args.no_cache:
            with open(dst) as f:
                text = f.read()
        else:
            p = subprocess.run([od, '-dr', os.path.join(objdir, name)],
                               capture_output=True)
            text = p.stdout.decode('latin-1')
            with open(dst, 'w') as f:
                f.write(text)
        analyze_member(text, name, all_sites)
        if idx % 25 == 0:
            print('  %d/%d' % (idx, len(members)))

    print('total sites: %d' % len(all_sites))
    write_reports(all_sites, outdir)


def write_reports(sites, outdir):
    by_addr = collections.defaultdict(list)
    for s in sites:
        by_addr[s.addr].append(s)

    with open(os.path.join(outdir, 'mmio_sites.txt'), 'w') as f:
        f.write('# WR\taddr\tsize\tvalue\tmemw\tfn\tmember\tregion\n')
        seen = set()
        for addr in sorted(by_addr):
            for s in sorted(by_addr[addr], key=lambda x: (x.func, x.member)):
                if (addr, s.op) in seen:
                    continue
                seen.add((addr, s.op))
                f.write(s.row() + '\n')

    undoc_blocks = collections.Counter()
    undoc_sites = []
    for s in sites:
        r = classify(s.addr)
        if r is None:
            continue
        name, base, off = r
        blk = s.addr & ~0xFFF
        if name == 'UNKNOWN' or (r[2] >= 0x1000 and r[2] < blk + 0x1000 - base):
            # block far from any documented base, or completely uncovered by floor region
            undoc_blocks[blk] += 1
            if s not in undoc_sites:
                undoc_sites.append(s)
    with open(os.path.join(outdir, 'undocumented.txt'), 'w') as f:
        f.write('# suspected undocumented 4K blocks (far from documented base or unrecognized)\n')
        for blk, cnt in sorted(undoc_blocks.items()):
            r = classify(blk)
            label = r[0] + '+0x%x' % r[2] if r else '?'
            f.write('0x%08x  %4d sites  %s\n' % (blk, cnt, label))
        f.write('\n# sites\n')
        for s in sorted(undoc_sites, key=lambda x: x.addr):
            r = classify(s.addr)
            label = r[0] + '+0x%x' % r[2] if r else '?'
            f.write('0x%08x  %s  %-8s  %-16s %s  %s\n' % (
                s.addr, 'W' if s.op.startswith('s') else 'R', s.op, label,
                s.func, s.member))

    with open(os.path.join(outdir, 'summary_by_block.txt'), 'w') as f:
        f.write('# 0x1000-block census: count, block, floor region name+offset\n')
        blk_sites = collections.defaultdict(list)
        for s in sites:
            blk = s.addr & ~0xFFF
            blk_sites[blk].append(s)
        for blk in sorted(blk_sites):
            r = classify(blk)
            label = r[0] + '+0x%x' % r[2] if r else '?'
            exact = ' block' if r and r[2] == 0 else ''
            f.write('%4d  0x%08x  %s%s\n' % (len(blk_sites[blk]), blk, label, exact))

    with open(os.path.join(outdir, 'summary_by_region.txt'), 'w') as f:
        c = collections.Counter()
        for s in sites:
            r = classify(s.addr)
            if r:
                c[(r[0], r[1])] += 1
        for (n, b), cnt in sorted(c.items(), key=lambda kv: -kv[1]):
            f.write('%-14s 0x%08x  %6d\n' % (n, b, cnt))

    with open(os.path.join(outdir, 'summary_by_fn.txt'), 'w') as f:
        c = collections.Counter()
        for s in sites:
            c[(s.member, s.func)] += 1
        for (m, fn), cnt in sorted(c.items(), key=lambda kv: -kv[1]):
            f.write('%6d  %-20s %s\n' % (cnt, m, fn))


if __name__ == '__main__':
    main()
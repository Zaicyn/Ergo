#!/usr/bin/env python3
"""
genome_preprocess.py — generalized codon-stream preprocessor.

Generalized from the old project's bsu_preprocess.py (2026-08 campaign).
Produces the two files the codon pipeline needs:
  {prefix}_codons.bin  - codon index array, 1 byte/codon, genome frame
  {prefix}_genes.tab   - idx/start/end/strand/codon_start/codon_end/gene/product

Codon encoding (VERIFIED convention, do not change):
  BASE_MAP = {'A':0,'T':1,'G':2,'C':3};  index = b1*16 + b2*4 + b3
  (pole = index//32 splits first base AT vs GC; ring = index mod 32)

Usage:
  python3 genome_preprocess.py PREFIX GENBANK_FILE
  python3 genome_preprocess.py mja gb_NC_000909.gb

Fetch GenBank records with:
  curl -o gb_ACCESSION.gb "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nucleotide&id=ACCESSION&rettype=gbwithparts&retmode=text"

Note: rettype MUST be gbwithparts (plain 'gb' returns CON master records
without sequence for many RefSeq genomes).
"""
import re
import sys

BASE_MAP = {'A': 0, 'T': 1, 'G': 2, 'C': 3}

def parse_genbank(path):
    text = open(path, errors='replace').read()
    seq_match = re.search(r'ORIGIN\s*\n(.*?)(?://|\Z)', text, re.DOTALL)
    if not seq_match:
        raise ValueError('No ORIGIN section found (did you fetch with rettype=gbwithparts?)')
    # strip whitespace/digits, then map IUPAC ambiguity codes to N
    # (DELETING them would shift every downstream frame — mja bug 2026-08-25)
    raw = re.sub(r'[^a-zA-Z]', '', seq_match.group(1)).upper()
    seq = ''.join(b if b in 'ATGC' else 'N' for b in raw)

    feat_match = re.search(r'FEATURES\s+Location/Qualifiers\n(.*?)(?=ORIGIN)', text, re.DOTALL)
    if not feat_match:
        raise ValueError('No FEATURES section found')
    feat_text = feat_match.group(1)

    cds_list = []
    blocks = re.split(r'\n     (\S+)', feat_text)
    i = 1
    while i < len(blocks) - 1:
        key, body = blocks[i].strip(), blocks[i + 1]
        i += 2
        if key != 'CDS':
            continue
        loc = body.split('\n')[0].strip()
        nums = re.findall(r'(\d+)\.\.(\d+)', loc)
        if not nums:
            continue
        if '/pseudo' in body:
            continue
        start, end = int(nums[0][0]), int(nums[-1][1])
        strand = '-' if 'complement' in loc else '+'
        gene = locus = product = ''
        for qm in re.finditer(r'/(\w+)="?([^"\n]*(?:\n\s+[^/\n]*)*)"?', body):
            qk = qm.group(1)
            qv = re.sub(r'\s+', ' ', qm.group(2)).strip().strip('"')
            if qk == 'gene': gene = qv
            elif qk == 'locus_tag': locus = qv
            elif qk == 'product': product = qv
        cds_list.append({'start': start, 'end': end, 'strand': strand,
                         'gene': gene or locus or '?', 'product': product})
    cds_list.sort(key=lambda c: c['start'])
    return seq, cds_list

def encode_codon(t):
    if len(t) != 3 or 'N' in t:
        return 0
    return BASE_MAP[t[0]] * 16 + BASE_MAP[t[1]] * 4 + BASE_MAP[t[2]]

def main():
    prefix, gb = sys.argv[1], sys.argv[2]
    seq, cds = parse_genbank(gb)
    codons = bytes(encode_codon(seq[i*3:i*3+3]) for i in range(len(seq)//3))
    with open(f'{prefix}_codons.bin', 'wb') as f:
        f.write(codons)
    with open(f'{prefix}_genes.tab', 'w') as f:
        f.write(f'# {prefix} gene table: {len(cds)} CDS features\n')
        f.write('# idx\tstart\tend\tstrand\tcodon_start\tcodon_end\tgene\tproduct\n')
        for i, c in enumerate(cds):
            f.write(f"{i}\t{c['start']}\t{c['end']}\t{c['strand']}"
                    f"\t{(c['start']-1)//3}\t{(c['end']-1)//3}\t{c['gene']}\t{c['product']}\n")
    gc = 100 * sum(1 for b in seq if b in 'GC') / len(seq)
    print(f'{prefix}: {len(seq):,} bp, GC {gc:.1f}%, {len(cds)} CDS, {len(codons):,} codons')

if __name__ == '__main__':
    main()

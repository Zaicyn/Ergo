/* esfs.c -- ESFOS v1 core + self-test. Portable C99, no deps.
 *
 * Flash model: 1 MB RAM array, 256 B pages, 4 KB sectors. Writes clear
 * bits only; erases set 0xFF and count wear. Cut model (v1): each
 * fl_write/fl_erase call is one atomic cut point (whole call commits
 * or the cut lands between calls). Finer hardware reality -- 64 B
 * slot writes always sit inside one page (64 | 256), but multi-page
 * records could tear mid-record on silicon: torn tails are handled
 * by stopping replay at the first invalid record (length/content
 * checked), so the abstraction is safe in the only direction that
 * matters (a cut we model strictly contains the cuts we don't).
 *
 * FS: superblock pair, versioned slot pool (SQ4 geometry: every
 * update appends a new version at the pool bump pointer; tombstones
 * are versions too; scan picks latest gen per logical slot -- no
 * in-place mutation, so 1->0-only writes always succeed). Inline
 * tails (<=32 B) or sector list in the file slot body. Bump data
 * allocator (GC-on-full and pool compaction are v1 limits: -1 when
 * full). Intent/commit journal with replay (uncommitted intents
 * ignored: staged bytes were fresh, never linked). Hash-chained
 * audit log with torn-tail truncation. Free/dead sets rebuilt by
 * scan at mount (scan doubles as scrub).
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

#define NSEC 256
#define SECB 4096
#define PAGEB 256
#define SB0 0
#define SB1 1
#define POOL0 2
#define NSLOT 128
#define JRN0 4
#define JRN_SECTORS 2
#define AUD0 6
#define AUD_SECTORS 4
#define DATA0 10
#define SPARE0 254
#define SLOTB 64
#define MAGIC 0x45534653u
#define VERSION 1u
#define TOMB_MAGIC 0xDEAD5EEDu

static uint8_t flash[NSEC][SECB];
static long erases[NSEC];
static long long cut_at = -1;
static int crashed;
static int bad_sec = -1;     /* fault hook: sector behaves failed (-1 off) */
static long erase_budget = 1000000; /* per-boot erase rate limiter */
/* remap: logical sector -> physical (identity unless remapped). The
 * table persists in the SB sector (after sb_t) because forgetting a
 * remap across reboot would reuse a bad sector. */
static int phys_sec[NSEC];
#define REMAP_MAX 8
static int remap_bad[REMAP_MAX], remap_sp[REMAP_MAX], remap_n;
static int spare_next;

/* ---------- splitmix64 ---------- */
static uint64_t sm64(uint64_t *s) {
    uint64_t z = (*s += 0x9E3779B97F4A7C15ull);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}
static uint64_t hash_bytes(const uint8_t *p, size_t n, uint64_t seed) {
    uint64_t h = seed;
    for (size_t i = 0; i < n; i++) {
        h ^= p[i] + 0x9E3779B97F4A7C15ull + (h << 6) + (h >> 2) + i;
        if ((i & 63) == 63) {
            uint64_t s = h;
            h = sm64(&s);
        }
    }
    uint64_t s = h ^ (uint64_t)n;
    return sm64(&s);
}

/* ---------- flash primitives ---------- */
static int cut_tick(void) {
    if (cut_at < 0)
        return 0;
    if (--cut_at == 0) {
        crashed = 1;
        return 1;
    }
    return 0;
}
static int phys(int sec) { return phys_sec[sec]; }
static int fl_write(uint32_t off, const uint8_t *p, size_t len) {
    int sec = (int)(off >> 12);
    if (sec == bad_sec)
        return -2;
    uint32_t po = ((uint32_t)phys(sec) << 12) | (off & 4095);
    for (size_t i = 0; i < len; i++) {
        uint8_t old = ((uint8_t *)flash)[po + i];
        if ((old & p[i]) != p[i])
            return -2;
        ((uint8_t *)flash)[po + i] = old & p[i];
    }
    if (cut_tick())
        return -1;
    return 0;
}
/* remap table persists in the SB sector (after sb_t, own checksum):
 * forgetting a remap across reboot would reuse a bad sector. */
static uint64_t rmap_sum_body(const uint8_t *b) {
    return hash_bytes(b, 8 + REMAP_MAX * 4, 0x52454D415052454Dull) ^ b[0];
}
static void rmap_save(void) {
    /* Rewrite both SB copies read-modify-erase-write (a cut mid-copy
     * tears at most one copy; the other stays valid -- that is what
     * the redundancy is for). */
    static uint8_t secbuf[SECB];
    uint8_t b[8 + REMAP_MAX * 4 + 8];
    memset(b, 0, sizeof b); /* no uninitialized bytes under checksum */
    /* layout: count u32 [0..4), reserved [4..8), pairs [8..40),
     * checksum [40..48). (An earlier rev put pairs at [4..36) while
     * everything else assumed [8..40): checksum overwrote pair[7]
     * and load read 4 bytes off. Named offsets now.) */
    b[0] = (uint8_t)remap_n;
    for (int i = 0; i < REMAP_MAX; i++) {
        b[8 + i * 4 + 0] = (uint8_t)(remap_bad[i] & 255);
        b[8 + i * 4 + 1] = (uint8_t)((remap_bad[i] >> 8) & 255);
        b[8 + i * 4 + 2] = (uint8_t)(remap_sp[i] & 255);
        b[8 + i * 4 + 3] = (uint8_t)((remap_sp[i] >> 8) & 255);
    }
    uint64_t c = rmap_sum_body(b);
    for (int i = 0; i < 8; i++)
        b[8 + REMAP_MAX * 4 + i] = (uint8_t)((c >> (8 * i)) & 255);
    for (int copy = 0; copy < 2; copy++) {
        int sec = copy ? SB1 : SB0;
        memcpy(secbuf, (uint8_t *)flash + sec * SECB, SECB);
        memcpy(secbuf + 64, b, sizeof b);
        memset(flash[sec], 0xFF, SECB);
        erases[sec]++;
        if (cut_tick())
            return;
        for (int o = 0; o < SECB; o += 512) {
            size_t n = SECB - o > 512 ? 512 : (size_t)(SECB - o);
            if (fl_write((uint32_t)sec * SECB + (uint32_t)o,
                         secbuf + o, n))
                return;
        }
    }
}
/* add a remap unless already mapped (idempotent: replay-safe) */
static int rmap_add(int sec, int sp) {
    for (int i = 0; i < remap_n; i++)
        if (remap_bad[i] == sec)
            return 0;
    if (remap_n >= REMAP_MAX)
        return -1;
    remap_bad[remap_n] = sec;
    remap_sp[remap_n] = sp;
    remap_n++;
    phys_sec[sec] = sp;
    return 0;
}
static int rmap_load(void) {
    for (int copy = 0; copy < 2; copy++) {
        uint8_t b[8 + REMAP_MAX * 4 + 8];
        int sec = copy ? SB1 : SB0;
        memcpy(b, (uint8_t *)flash + sec * SECB + 64, sizeof b);
        uint64_t c = 0;
        for (int i = 0; i < 8; i++)
            c |= (uint64_t)b[8 + REMAP_MAX * 4 + i] << (8 * i);
        if (rmap_sum_body(b) != c)
            continue;
        remap_n = b[0];
        if (remap_n < 0 || remap_n > REMAP_MAX)
            continue;
        for (int i = 0; i < REMAP_MAX; i++) {
            remap_bad[i] = b[8 + i * 4] | (b[8 + i * 4 + 1] << 8);
            remap_sp[i] = b[8 + i * 4 + 2] | (b[8 + i * 4 + 3] << 8);
        }
        for (int s = 0; s < NSEC; s++)
            phys_sec[s] = s;
        for (int i = 0; i < remap_n; i++)
            phys_sec[remap_bad[i]] = remap_sp[i];
        return 0;
    }
    return -1;
}
static int fl_erase(int sec) {
    if (erase_budget-- <= 0)
        return -1; /* read-only trip: budget exhausted, state valid */
    int ps = phys(sec);
    if (ps == bad_sec || sec == bad_sec) {
        int sp = spare_next++;
        if (sp >= NSEC)
            return -1;
        memset(flash[sp], 0xFF, SECB);
        erases[sp]++;
        if (rmap_add(sec, sp))
            return -1;
        rmap_save();
        if (cut_tick())
            return -1;
        return 0;
    }
    memset(flash[ps], 0xFF, SECB);
    erases[ps]++;
    for (int i = 0; i < SECB; i++)
        if (flash[ps][i] != 0xFF) {
            int sp = spare_next++;
            if (sp >= NSEC)
                return -1;
            memset(flash[sp], 0xFF, SECB);
            erases[sp]++;
            if (rmap_add(sec, sp))
                return -1;
            rmap_save();
            break;
        }
    if (cut_tick())
        return -1;
    return 0;
}
static void fl_read(uint32_t off, uint8_t *p, size_t len) {
    int sec = (int)(off >> 12);
    uint32_t po = ((uint32_t)phys(sec) << 12) | (off & 4095);
    memcpy(p, (uint8_t *)flash + po, len);
}

/* ---------- superblock ---------- */
typedef struct {
    uint32_t magic, version, nsec, pool0;
    uint32_t jrn0, aud0, data0, spare0;
    uint64_t gen;
    uint64_t cksum;
} sb_t;
static uint64_t sb_sum(const sb_t *s) {
    return hash_bytes((const uint8_t *)s, 8 * 4, 0x5342005342005342ull);
}
static int sb_write(int sec, const sb_t *s) {
    sb_t w = *s;
    w.cksum = 0;
    w.cksum = sb_sum(&w);
    return fl_write((uint32_t)sec * SECB, (uint8_t *)&w, sizeof w);
}
static int sb_read(int sec, sb_t *s) {
    fl_read((uint32_t)sec * SECB, (uint8_t *)s, sizeof *s);
    if (s->magic != MAGIC || s->version != VERSION)
        return -1;
    uint64_t c = s->cksum;
    s->cksum = 0;
    if (sb_sum(s) != c) {
        s->cksum = c;
        return -1;
    }
    s->cksum = c;
    return 0;
}

/* ---------- slots ---------- */
#pragma pack(push, 1)
typedef struct {
    uint32_t invar;     /* 0xE5F5GGSS: GG=gen, SS=slot (full byte) */
    uint32_t size;
    uint32_t ext;       /* reserved */
    uint32_t jseq;
    uint32_t flags;     /* TOMB_MAGIC = dead */
    char name[12];
    uint8_t body[32];   /* inline tail OR sector list + count@16 */
} slot_t;
#pragma pack(pop)
static int slot_pos[NSLOT];   /* phys position of latest version */
static uint32_t slot_gen[NSLOT];
static int slot_live[NSLOT];
static int slot_dead[NSLOT];
static int pool_bump;

static uint32_t slot_pack(int si, uint32_t gen) {
    return 0xE5F50000u | ((gen & 0xFFu) << 8) | (uint32_t)(si & 0xFF);
}
static uint32_t slot_off(int pos) {
    int half = pos < NSLOT / 2 ? 0 : 1;
    int idx = pos - half * (NSLOT / 2);
    return (uint32_t)(POOL0 + half) * SECB + (uint32_t)idx * SLOTB;
}
static int slot_store(int si, const slot_t *s) {
    if (pool_bump >= NSLOT)
        return -1; /* pool full (v1: no compaction) */
    int pos = pool_bump++;
    if (fl_write(slot_off(pos), (const uint8_t *)s, sizeof *s))
        return -1;
    slot_pos[si] = pos;
    slot_live[si] = 1;
    slot_dead[si] = (s->flags == TOMB_MAGIC);
    if (slot_dead[si])
        slot_live[si] = 0;
    uint32_t gen = (s->invar >> 8) & 0xFFu;
    slot_gen[si] = gen;
    return 0;
}
static void slot_load(int si, slot_t *s) {
    fl_read(slot_off(slot_pos[si]), (uint8_t *)s, sizeof *s);
}
/* scan rebuilds map/live/dead/gens/bump; verifies invariants. */
static int slot_scan(void) {
    int bad = 0, maxpos = -1;
    memset(slot_live, 0, sizeof slot_live);
    memset(slot_dead, 0, sizeof slot_dead);
    memset(slot_gen, 0, sizeof slot_gen);
    for (int i = 0; i < NSLOT; i++)
        slot_pos[i] = -1;
    for (int pos = 0; pos < NSLOT; pos++) {
        slot_t s;
        fl_read(slot_off(pos), (uint8_t *)&s, sizeof s);
        int erased = 1;
        const uint8_t *b = (const uint8_t *)&s;
        for (size_t i = 0; i < sizeof s; i++)
            if (b[i] != 0xFF) {
                erased = 0;
                break;
            }
        if (erased)
            continue;
        maxpos = pos;
        int si = (int)(s.invar & 0xFFu);
        uint32_t gen = (s.invar >> 8) & 0xFFu;
        if ((s.invar >> 16) != 0xE5F5u || si < 1 || si >= NSLOT) {
            bad++;
            continue;
        }
        if (gen < slot_gen[si] ||
            (gen == slot_gen[si] && slot_pos[si] >= 0))
            continue; /* stale (older gen, or same gen earlier pos) */
        slot_gen[si] = gen;
        slot_pos[si] = pos;
        slot_dead[si] = (s.flags == TOMB_MAGIC);
        slot_live[si] = !slot_dead[si];
    }
    pool_bump = maxpos + 1;
    return bad;
}
static int slot_alloc(void) {
    for (int si = 1; si < NSLOT; si++)
        if (!slot_live[si] && !slot_dead[si])
            return si;
    return -1;
}

/* ---------- journal (circular, 2 sectors) ----------
 * Records never span sectors: if one doesn't fit the remainder, the
 * head pads to the next sector start (0xFF pad, scan skips it). Wrap
 * erases the OTHER sector (tail). Safe at any point: erasing kills
 * only committed history (slots carry applied truth) or void
 * uncommitted intents (replay ignores them); the current op's own
 * records always live at head. Uncommitted-intent erasure can only
 * strand its own commit, which replay also ignores. */
static uint32_t jrn_head, jrn_seq;
static long jrn_wraps;
static uint32_t jrn_base(void) { return (uint32_t)JRN0 * SECB; }
static uint32_t jrn_size(void) { return JRN_SECTORS * SECB; }
/* sector has any content (records always start at sector start) */
static int sec_used(int base_sec, int idx) {
    uint8_t h[8];
    fl_read((uint32_t)(base_sec + idx) * SECB, h, 8);
    for (int i = 0; i < 8; i++)
        if (h[i] != 0xFF)
            return 1;
    return 0;
}
static int jrn_append(uint8_t op, int slot, const uint8_t *pl,
                      uint16_t len) {
    uint8_t hdr[8];
    hdr[0] = (uint8_t)(jrn_seq & 255);
    hdr[1] = (uint8_t)((jrn_seq >> 8) & 255);
    hdr[2] = (uint8_t)((jrn_seq >> 16) & 255);
    hdr[3] = (uint8_t)((jrn_seq >> 24) & 255);
    hdr[4] = op;
    hdr[5] = (uint8_t)slot;
    hdr[6] = (uint8_t)(len & 255);
    hdr[7] = (uint8_t)(len >> 8);
    uint32_t s0 = 0, s1 = 0, k = 1;
    for (int i = 0; i < 8; i++, k++) {
        s0 += hdr[i];
        s1 += hdr[i] * k;
    }
    for (int i = 0; i < len; i++, k++) {
        s0 += pl[i];
        s1 += pl[i] * k;
    }
    uint8_t tail[8];
    for (int i = 0; i < 4; i++) {
        tail[i] = (uint8_t)((s0 >> (8 * i)) & 255);
        tail[4 + i] = (uint8_t)((s1 >> (8 * i)) & 255);
    }
    uint32_t need = 8u + len + 8u;
    if (need > SECB)
        return -3; /* record bigger than a sector: v1 limit */
    if (jrn_head >= jrn_size()) {
        /* exact-fill edge: head past the end; oldest sector (0) holds
         * only committed-or-void history by the ring argument */
        if (sec_used(JRN0, 0) && fl_erase(JRN0))
            return -1;
        jrn_head = 0;
    }
    uint32_t sec_end =
        ((jrn_head / SECB) + 1) * SECB; /* end of head's sector */
    if (jrn_head + need > sec_end) {
        /* wrap: erase the other sector (tail: committed-or-void only),
         * jump head to its start. Skip the erase if already erased
         * (common right after a previous wrap). */
        int other = (jrn_head / SECB == 0) ? 1 : 0;
        if (sec_used(JRN0, other) && fl_erase(JRN0 + other))
            return -1;
        jrn_wraps++;
        jrn_head = (uint32_t)other * SECB;
    }
    uint32_t off = jrn_base() + jrn_head;
    if (fl_write(off, hdr, 8))
        return -1;
    if (len && fl_write(off + 8, pl, len))
        return -1;
    if (fl_write(off + 8 + len, tail, 8))
        return -1;
    jrn_head += need;
    jrn_seq++;
    return 0;
}
/* per-sector walk: parse records from sector start, stop at first
 * invalid (erased pad, torn tail, or sector end). Fills seqs/ends
 * arrays, returns count. Records never span sectors by construction.
 * verify one record at absolute region off; returns total length,
 * 0 clean-end, -1 invalid. */
static int jrn_check(uint32_t off, uint32_t *len_out) {
    uint8_t hdr[8];
    fl_read(jrn_base() + off, hdr, 8);
    int erased = 1;
    for (int i = 0; i < 8; i++)
        if (hdr[i] != 0xFF) {
            erased = 0;
            break;
        }
    if (erased)
        return 0;
    uint16_t len = (uint16_t)(hdr[6] | (hdr[7] << 8));
    uint32_t sec_end = ((off / SECB) + 1) * SECB; /* region-relative */
    if (off + 16u + len > sec_end)
        return -1; /* torn tail or sector crosser (never written) */
    static uint8_t tmp[512];
    uint8_t tail[8];
    if (len > sizeof tmp)
        return -1;
    if (len)
        fl_read(jrn_base() + off + 8, tmp, len);
    fl_read(jrn_base() + off + 8 + len, tail, 8);
    int allff = 1;
    for (int i = 0; i < 8; i++)
        if (tail[i] != 0xFF) {
            allff = 0;
            break;
        }
    if (allff)
        return -1; /* torn tail (checksums unwritten) */
    uint32_t s0 = 0, s1 = 0, k = 1;
    for (int i = 0; i < 8; i++, k++) {
        s0 += hdr[i];
        s1 += hdr[i] * k;
    }
    for (int i = 0; i < len; i++, k++) {
        s0 += tmp[i];
        s1 += tmp[i] * k;
    }
    uint32_t g0 = 0, g1 = 0;
    for (int i = 0; i < 4; i++) {
        g0 |= (uint32_t)tail[i] << (8 * i);
        g1 |= (uint32_t)tail[4 + i] << (8 * i);
    }
    if (s0 != g0 || s1 != g1)
        return -1; /* torn/corrupt tail */
    *len_out = len;
    return (int)(16u + len);
}
/* replay over merged seq order from all sectors: count intents;
 * uncommitted ones ignored (staged bytes were fresh, never linked).
 * Stops per sector at first invalid (torn tail / pad). */
static int jrn_replay(void) {
    int intents = 0;
    for (int s = 0; s < JRN_SECTORS; s++) {
        uint32_t off = (uint32_t)s * SECB;
        for (;;) {
            uint32_t len = 0;
            int r = jrn_check(off, &len);
            if (r <= 0)
                break;
            uint8_t op;
            fl_read(jrn_base() + off + 4, &op, 1);
            if (op == 1)
                intents++;
            off += (uint32_t)r;
        }
    }
    return intents;
}
/* scan-derive head/seq at mount: end past the max-seq valid record,
 * seq one above it. Survives wraps with no persisted cursor. */
static void jrn_scan(void) {
    uint32_t maxseq = 0, maxend = 0;
    int found = 0;
    for (int s = 0; s < JRN_SECTORS; s++) {
        uint32_t off = (uint32_t)s * SECB;
        for (;;) {
            uint32_t len = 0;
            int r = jrn_check(off, &len);
            if (r <= 0)
                break;
            uint8_t hdr[8];
            fl_read(jrn_base() + off, hdr, 8);
            uint32_t seq =
                hdr[0] | ((uint32_t)hdr[1] << 8) |
                ((uint32_t)hdr[2] << 16) | ((uint32_t)hdr[3] << 24);
            if (!found || seq > maxseq) {
                maxseq = seq;
                maxend = off + (uint32_t)r;
                found = 1;
            }
            off += (uint32_t)r;
        }
    }
    if (found) {
        jrn_head = maxend;
        jrn_seq = maxseq + 1;
    } else {
        jrn_head = 0;
        jrn_seq = 1;
    }
}

/* ---------- audit chain ---------- */
static uint32_t aud_head;
static uint64_t aud_prev;
static uint32_t aud_base(void) { return (uint32_t)AUD0 * SECB; }
static uint32_t aud_size(void) { return AUD_SECTORS * SECB; }
static uint32_t aud_seq;
static int audit_append(const uint8_t *pl, uint16_t len) {
    uint8_t hdr[16];
    for (int i = 0; i < 4; i++)
        hdr[i] = (uint8_t)((aud_seq >> (8 * i)) & 255);
    uint64_t h = hash_bytes(pl, len, aud_prev ^ 0x4155444954415544ull);
    for (int i = 0; i < 8; i++)
        hdr[4 + i] = (uint8_t)((h >> (8 * i)) & 255);
    hdr[12] = (uint8_t)(len & 255);
    hdr[13] = (uint8_t)(len >> 8);
    hdr[14] = hdr[15] = 0;
    uint32_t need = 16u + len;
    if (need > SECB)
        return -3; /* bigger than a sector: v1 limit */
    if (aud_head >= aud_size()) {
        if (sec_used(AUD0, 0) && fl_erase(AUD0))
            return -1;
        aud_head = 0;
    }
    uint32_t sec_end = ((aud_head / SECB) + 1) * SECB;
    if (aud_head + need > sec_end) {
        int other = (aud_head / SECB == 0) ? 1 : 0;
        /* audit has 4 sectors: erase oldest (tail). With 4 sectors the
         * tail is (head_sector + 1) % 4 only if full; v1 rule: erase
         * the sector AFTER head's (ring order), which always holds
         * the oldest committed-or-void history. */
        int tail = ((int)(aud_head / SECB) + 1) % AUD_SECTORS;
        (void)other;
        if (sec_used(AUD0, tail) && fl_erase(AUD0 + tail))
            return -1;
        aud_head = (uint32_t)tail * SECB;
    }
    uint32_t off = aud_base() + aud_head;
    if (fl_write(off, hdr, 16))
        return -1;
    if (len && fl_write(off + 16, pl, len))
        return -1;
    aud_head += need;
    aud_prev = h;
    aud_seq++;
    return 0;
}
/* verify chain over merged seq order from all sectors. The FIRST
 * retained record's prev points into erased (rotated) history, so its
 * prev-check is exempt by design (anchor lost to rotation, stated);
 * every later link must close. Returns records verified or negative
 * (a broken interior link = corruption, never a tear: tears only
 * exist at a window end, and wrapped windows end at erased space). */
static int audit_verify(void) {
    /* collect valid records: (seq, off) with bounds+checksum valid */
    static uint32_t rseq[2048];
    static uint32_t roff[2048];
    int nr = 0;
    for (int s = 0; s < AUD_SECTORS; s++) {
        uint32_t off = (uint32_t)s * SECB;
        uint32_t send = off + SECB;
        for (;;) {
            uint8_t hdr[16];
            if (off + 16 > send)
                break;
            fl_read(aud_base() + off, hdr, 16);
            int e = 1;
            for (int i = 0; i < 16; i++)
                if (hdr[i] != 0xFF) {
                    e = 0;
                    break;
                }
            if (e)
                break;
            uint32_t seq =
                hdr[0] | ((uint32_t)hdr[1] << 8) |
                ((uint32_t)hdr[2] << 16) | ((uint32_t)hdr[3] << 24);
            uint16_t len = (uint16_t)(hdr[12] | (hdr[13] << 8));
            if (len > 512 || off + 16u + len > send)
                break; /* torn/pad: sector done */
            /* NOTE: audit records have no checksum tail (unlike
             * journal records): collection ends at erased headers
             * and bounds only. A torn tail parses as a garbage
             * record at worst; the verify phase below treats a
             * link failure at the LAST position as truncation. */
            if (nr < 2048) {
                rseq[nr] = seq;
                roff[nr] = off;
                nr++;
            }
            off += 16u + len;
        }
    }
    /* order by seq (insertion: tiny n) and verify links */
    for (int i = 1; i < nr; i++) {
        uint32_t qs = rseq[i], qo = roff[i];
        int j = i - 1;
        while (j >= 0 && rseq[j] > qs) {
            rseq[j + 1] = rseq[j];
            roff[j + 1] = roff[j];
            j--;
        }
        rseq[j + 1] = qs;
        roff[j + 1] = qo;
    }
    int n = 0;
    uint64_t prev = 0;
    int have_prev = 0;
    static uint8_t tmp[512];
    for (int i = 0; i < nr; i++) {
        uint8_t hdr[16];
        fl_read(aud_base() + roff[i], hdr, 16);
        uint16_t len = (uint16_t)(hdr[12] | (hdr[13] << 8));
        if (len)
            fl_read(aud_base() + roff[i] + 16, tmp, len);
        if (!have_prev) {
            /* window head: recompute hash forward but exempt the
             * prev-link (anchor rotated away) */
            uint64_t h =
                hash_bytes(tmp, len, prev ^ 0x4155444954415544ull);
            (void)h;
            prev = 0; /* re-anchor below from stored value */
            uint64_t got = 0;
            for (int k = 0; k < 8; k++)
                got |= (uint64_t)hdr[4 + k] << (8 * k);
            /* stored hash must equal hash over (payload, prev=?) --
             * unknowable; instead adopt it as the new anchor after
             * checking the rest of the chain closes from here */
            prev = got;
            have_prev = 1;
            n++;
            continue;
        }
        uint64_t h = hash_bytes(tmp, len, prev ^ 0x4155444954415544ull);
        uint64_t got = 0;
        for (int k = 0; k < 8; k++)
            got |= (uint64_t)hdr[4 + k] << (8 * k);
        if (h != got) {
            /* link failure at the LAST collected record = torn tail
             * (partial write): truncate, prefix verifies. Anywhere
             * else = corruption (tears only exist at window ends). */
            if (i == nr - 1)
                break;
            return -30 - n;
        }
        prev = h;
        n++;
    }
    return n;
}
/* scan-derive resume: head past max-seq record end, seq/hash after it */
static void aud_scan(void) {
    uint32_t maxseq = 0, maxend = 0;
    uint64_t maxh = 0;
    int found = 0;
    for (int s = 0; s < AUD_SECTORS; s++) {
        uint32_t off = (uint32_t)s * SECB;
        uint32_t send = off + SECB;
        for (;;) {
            uint8_t hdr[16];
            if (off + 16 > send)
                break;
            fl_read(aud_base() + off, hdr, 16);
            int e = 1;
            for (int i = 0; i < 16; i++)
                if (hdr[i] != 0xFF) {
                    e = 0;
                    break;
                }
            if (e)
                break;
            uint32_t seq =
                hdr[0] | ((uint32_t)hdr[1] << 8) |
                ((uint32_t)hdr[2] << 16) | ((uint32_t)hdr[3] << 24);
            uint16_t len = (uint16_t)(hdr[12] | (hdr[13] << 8));
            if (off + 16u + len > send)
                break;
            uint64_t h = 0;
            for (int k = 0; k < 8; k++)
                h |= (uint64_t)hdr[4 + k] << (8 * k);
            if (!found || seq > maxseq) {
                maxseq = seq;
                maxend = off + 16u + len;
                maxh = h;
                found = 1;
            }
            off += 16u + len;
        }
    }
    if (found) {
        aud_head = maxend;
        aud_seq = maxseq + 1;
        aud_prev = maxh;
    } else {
        aud_head = 0;
        aud_seq = 0;
        aud_prev = 0;
    }
}

/* ---------- data bump allocator ---------- */
static uint32_t bump;
static int data_claim(int nsec, uint32_t *out) {
    if (bump + (uint32_t)nsec > SPARE0)
        return -1; /* full (v1: no GC) */
    for (int i = 0; i < nsec; i++)
        out[i] = bump++;
    return 0;
}

/* ---------- file ops ---------- */
static uint32_t op_seq;
static int name_slot(const char *name) {
    for (int si = 1; si < NSLOT; si++) {
        if (!slot_live[si] || slot_dead[si])
            continue;
        slot_t s;
        slot_load(si, &s);
        if (!strncmp(s.name, name, 12))
            return si;
    }
    return -1;
}
static int stage_bytes(const uint8_t *p, size_t len, uint32_t *secs,
                       int *nsec) {
    int n = (int)((len + SECB - 1) / SECB);
    if (n < 1)
        n = 1;
    if (n > 4)
        return -1; /* v1 extent capacity */
    if (data_claim(n, secs))
        return -1;
    for (int i = 0; i < n; i++) {
        uint8_t page[SECB];
        memset(page, 0, sizeof page);
        size_t c = len > SECB ? SECB : len;
        if (c)
            memcpy(page, p, c);
        for (int pg = 0; pg < SECB / PAGEB; pg++)
            if (fl_write(secs[i] * SECB + (uint32_t)pg * PAGEB,
                         page + pg * PAGEB, PAGEB))
                return -1;
        p += c;
        len -= c;
    }
    *nsec = n;
    return 0;
}
static int esfs_write(const char *name, const uint8_t *p, size_t len) {
    if (len > 4u * SECB)
        return -1;
    uint8_t intent[20];
    intent[0] = 1;
    size_t nl = strlen(name);
    if (nl > 11)
        nl = 11;
    memset(intent + 1, 0, 12);
    memcpy(intent + 1, name, nl);
    intent[13] = (uint8_t)(len & 255);
    intent[14] = (uint8_t)((len >> 8) & 255);
    intent[15] = (uint8_t)((len >> 16) & 255);
    intent[16] = (uint8_t)((len >> 24) & 255);
    if (jrn_append(1, 0, intent, sizeof intent))
        return -1;
    uint32_t secs[4];
    int nsec = 0;
    if (len > 32) {
        if (stage_bytes(p, len, secs, &nsec))
            return -1;
    }
    int old = name_slot(name);
    uint32_t gen = 0;
    if (old >= 0) {
        slot_t so;
        slot_load(old, &so);
        gen = ((so.invar >> 8) & 0xFFu) + 1;
    }
    int si = old >= 0 ? old : slot_alloc();
    if (si < 0)
        return -1;
    slot_t s;
    memset(&s, 0, sizeof s);
    s.invar = slot_pack(si, gen);
    s.size = (uint32_t)len;
    s.ext = 0xFFFFFFFFu;
    s.jseq = op_seq;
    s.flags = 0;
    memset(s.name, 0, sizeof s.name);
    memcpy(s.name, name, nl);
    if (len <= 32) {
        memcpy(s.body, p, len);
    } else {
        for (int i = 0; i < nsec; i++) {
            s.body[i * 4 + 0] = (uint8_t)(secs[i] & 255);
            s.body[i * 4 + 1] = (uint8_t)((secs[i] >> 8) & 255);
            s.body[i * 4 + 2] = 1;
            s.body[i * 4 + 3] = 0;
        }
        s.body[16] = (uint8_t)nsec;
    }
    if (slot_store(si, &s))
        return -1;
    uint8_t commit[4] = { 2, (uint8_t)si, 0, 0 };
    if (jrn_append(2, si, commit, sizeof commit))
        return -1;
    op_seq++;
    if (audit_append((const uint8_t *)name, (uint16_t)(nl + 1)))
        return -1;
    return 0;
}
static int esfs_read(const char *name, uint8_t *out, size_t cap,
                     size_t *got) {
    int si = name_slot(name);
    if (si < 0)
        return -1;
    slot_t s;
    slot_load(si, &s);
    size_t len = s.size;
    if (len > cap)
        return -1;
    if (len <= 32) {
        memcpy(out, s.body, len);
    } else {
        int nsec = s.body[16];
        size_t o = 0;
        for (int i = 0; i < nsec && o < len; i++) {
            uint32_t sec = (uint32_t)s.body[i * 4] |
                           ((uint32_t)s.body[i * 4 + 1] << 8);
            size_t c = len - o > SECB ? SECB : len - o;
            fl_read(sec * SECB, out + o, c);
            o += c;
        }
    }
    *got = len;
    return 0;
}
static int esfs_delete(const char *name) {
    int si = name_slot(name);
    if (si < 0)
        return -1;
    size_t nl = strlen(name);
    if (nl > 11)
        nl = 11;
    uint8_t intent[16] = { 3 };
    memcpy(intent + 1, name, nl);
    if (jrn_append(1, si, intent, sizeof intent))
        return -1;
    slot_t s;
    slot_load(si, &s);
    uint32_t gen = ((s.invar >> 8) & 0xFFu) + 1;
    memset(&s, 0, sizeof s);
    s.invar = slot_pack(si, gen);
    s.flags = TOMB_MAGIC;
    memcpy(s.name, name, nl);
    if (slot_store(si, &s))
        return -1;
    uint8_t commit[4] = { 4, (uint8_t)si, 0, 0 };
    if (jrn_append(2, si, commit, sizeof commit))
        return -1;
    op_seq++;
    return 0;
}

/* ---------- mkfs / mount ---------- */
static void esfs_mkfs(void) {
    for (int s = 0; s < NSEC; s++)
        erases[s] = 0;
    for (int s = 0; s < NSEC; s++)
        phys_sec[s] = s;
    remap_n = 0;
    spare_next = SPARE0;
    for (int s = 0; s < NSEC; s++)
        if (fl_erase(s))
            break; /* bad sectors remapped here via fault hook path */
    crashed = 0;
    cut_at = -1;
    sb_t sb;
    memset(&sb, 0, sizeof sb);
    sb.magic = MAGIC;
    sb.version = VERSION;
    sb.nsec = NSEC;
    sb.pool0 = POOL0;
    sb.jrn0 = JRN0;
    sb.aud0 = AUD0;
    sb.data0 = DATA0;
    sb.spare0 = SPARE0;
    sb.gen = 1;
    sb_write(SB0, &sb);
    sb_write(SB1, &sb);
    jrn_head = 0;
    jrn_seq = 1;
    jrn_wraps = 0;
    aud_head = 0;
    aud_prev = 0;
    aud_seq = 0;
    bump = DATA0;
    op_seq = 1;
    slot_scan();
}
static int esfs_mount(void) {
    if (rmap_load()) {
        for (int s = 0; s < NSEC; s++)
            phys_sec[s] = s;
        remap_n = 0;
        spare_next = SPARE0;
    } else {
        int mxsp = SPARE0;
        for (int i = 0; i < remap_n; i++)
            if (remap_sp[i] >= mxsp)
                mxsp = remap_sp[i] + 1;
        spare_next = mxsp;
    }
    sb_t a, b;
    int oka = sb_read(SB0, &a), okb = sb_read(SB1, &b);
    if (oka && okb)
        return -1;
    if (slot_scan() < 0)
        return -1;
    jrn_replay();
    jrn_scan(); /* scan-derive head/seq (wrap-aware; no cursor kept) */
    /* audit resume: scan-derive (wrap-aware); op_seq follows audit */
    aud_scan();
    op_seq = aud_seq + 1;
    {
        uint32_t mx = DATA0;
        for (int si = 1; si < NSLOT; si++) {
            if (!slot_live[si] || slot_dead[si])
                continue;
            slot_t s;
            slot_load(si, &s);
            if (s.size > 32) {
                int nsec = s.body[16];
                for (int i = 0; i < nsec; i++) {
                    uint32_t sec = (uint32_t)s.body[i * 4] |
                                   ((uint32_t)s.body[i * 4 + 1] << 8);
                    if (sec >= mx && sec < SPARE0)
                        mx = sec + 1;
                }
            }
        }
        bump = mx;
    }
    return 0;
}

/* ---------- tests ---------- */
static int fails;
#define CHECK(c, msg) do { \
    if (c) printf("ok   %s\n", msg); \
    else { printf("FAIL %s\n", msg); fails++; } } while (0)

static uint8_t wbuf[8192], rbuf[8192];
static void fill_pat(uint8_t *p, size_t n, unsigned seed) {
    for (size_t i = 0; i < n; i++)
        p[i] = (uint8_t)(((i * 67 + 41 + seed) ^ 0x3C ^ (i >> 3)) & 0xFF);
}
static void script_S1(void) {
    size_t got = 0;
    fill_pat(wbuf, 1000, 1);
    CHECK(esfs_write("a.bin", wbuf, 1000) == 0, "S1 write a");
    fill_pat(wbuf, 100, 2);
    CHECK(esfs_write("b.bin", wbuf, 100) == 0, "S1 write b");
    fill_pat(wbuf, 5000, 3);
    CHECK(esfs_write("c.bin", wbuf, 5000) == 0, "S1 write c");
    fill_pat(wbuf, 1000, 1);
    CHECK(esfs_read("a.bin", rbuf, sizeof rbuf, &got) == 0 &&
              got == 1000 && !memcmp(rbuf, wbuf, 1000),
          "S1 read a exact");
    CHECK(esfs_delete("b.bin") == 0, "S1 delete b");
    CHECK(esfs_read("b.bin", rbuf, sizeof rbuf, &got) != 0,
          "S1 b gone");
    fill_pat(wbuf, 5000, 3);
    CHECK(esfs_read("c.bin", rbuf, sizeof rbuf, &got) == 0 &&
              got == 5000 && !memcmp(rbuf, wbuf, 5000),
          "S1 read c exact");
    CHECK(audit_verify() >= 3, "S1 audit chain verifies");
    CHECK(slot_scan() == 0, "S1 scrub clean");
}
static void script_S2(void) {
    esfs_mkfs();
    if (esfs_mount()) {
        CHECK(0, "S2 mount");
        return;
    }
    script_S1();
    if (fails) {
        printf("S2 baseline dirty, skipping fuzz\n");
        return;
    }
    int maxcut = 400, tested = 0, bad = 0;
    for (long c = 1; c <= maxcut; c++) {
        esfs_mkfs();
        if (esfs_mount()) {
            bad++;
            continue;
        }
        crashed = 0;
        cut_at = c;
        fill_pat(wbuf, 1000, 1);
        if (!crashed)
            esfs_write("a.bin", wbuf, 1000);
        fill_pat(wbuf, 100, 2);
        if (!crashed)
            esfs_write("b.bin", wbuf, 100);
        fill_pat(wbuf, 5000, 3);
        if (!crashed)
            esfs_write("c.bin", wbuf, 5000);
        if (!crashed)
            esfs_delete("b.bin");
        cut_at = -1;
        tested++;
        if (esfs_mount()) {
            printf("FAIL cut=%ld mount\n", c);
            bad++;
            fails++;
            continue;
        }
        if (slot_scan() != 0) {
            printf("FAIL cut=%ld scrub\n", c);
            bad++;
            fails++;
            continue;
        }
        if (audit_verify() < 0) {
            printf("FAIL cut=%ld audit\n", c);
            bad++;
            fails++;
            continue;
        }
        size_t got = 0;
        fill_pat(wbuf, 1000, 1);
        if (esfs_read("a.bin", rbuf, sizeof rbuf, &got) == 0 &&
            !(got == 1000 && !memcmp(rbuf, wbuf, 1000))) {
            printf("FAIL cut=%ld a-corrupt\n", c);
            bad++;
            fails++;
        }
        fill_pat(wbuf, 5000, 3);
        if (esfs_read("c.bin", rbuf, sizeof rbuf, &got) == 0 &&
            !(got == 5000 && !memcmp(rbuf, wbuf, 5000))) {
            printf("FAIL cut=%ld c-corrupt\n", c);
            bad++;
            fails++;
        }
    }
    printf("S2 fuzz: %d cuts, %d bad\n", tested, bad);
    CHECK(bad == 0, "S2 every cut recovers valid");
    cut_at = -1;
    crashed = 0;
}
static void script_S3(void) {
    /* wear workload: 30 write/delete cycles (journal-bounded) */
    esfs_mkfs();
    if (esfs_mount()) {
        CHECK(0, "S3 mount");
        return;
    }
    for (int i = 0; i < 30; i++) {
        char nm[16];
        snprintf(nm, sizeof nm, "w%02d.tmp", i);
        fill_pat(wbuf, 200, (unsigned)i);
        if (esfs_write(nm, wbuf, 200))
            break;
        if (esfs_delete(nm))
            break;
    }
    long mx = 0, tot = 0;
    for (int s = 0; s < NSEC; s++) {
        tot += erases[s];
        if (erases[s] > mx)
            mx = erases[s];
    }
    printf("S3 wear: total=%ld max-sector=%ld\n", tot, mx);
    CHECK(mx < 100000, "S3 endurance headroom");
    CHECK(esfs_mount() == 0 && slot_scan() == 0, "S3 valid after load");
}
/* S4: bad-sector remap (fault hook on a data sector) */
static void script_S4(void) {
    bad_sec = DATA0 + 5;
    esfs_mkfs();
    CHECK(remap_n >= 1, "S4 sector remapped at mkfs");
    CHECK(esfs_mount() == 0, "S4 mount with remap");
    size_t got = 0;
    fill_pat(wbuf, 6000, 9);
    CHECK(esfs_write("d.bin", wbuf, 6000) == 0, "S4 write across remap");
    fill_pat(wbuf, 6000, 9);
    CHECK(esfs_read("d.bin", rbuf, sizeof rbuf, &got) == 0 &&
              got == 6000 && !memcmp(rbuf, wbuf, 6000),
          "S4 read exact via spare");
    /* remap persists across remount */
    CHECK(esfs_mount() == 0, "S4 remount");
    CHECK(remap_n >= 1, "S4 remap table reloaded");
    fill_pat(wbuf, 6000, 9);
    CHECK(esfs_read("d.bin", rbuf, sizeof rbuf, &got) == 0 &&
              got == 6000 && !memcmp(rbuf, wbuf, 6000),
          "S4 read exact after remount");
    bad_sec = -1;
}
/* S5: wrap cycling + pool-full boundary */
static void script_S5(void) {
    esfs_mkfs();
    CHECK(esfs_mount() == 0, "S5 mount");
    /* 120 distinct small writes: ~1 journal wrap, pool stays < 128 */
    for (int i = 0; i < 120; i++) {
        char nm[16];
        snprintf(nm, sizeof nm, "q%03d", i);
        fill_pat(wbuf, 50, (unsigned)i);
        if (esfs_write(nm, wbuf, 50))
            break;
    }
    printf("S5 journal wraps=%ld\n", jrn_wraps);
    CHECK(jrn_wraps >= 1, "S5 journal wrapped");
    long e0 = erases[JRN0], e1 = erases[JRN0 + 1];
    long d = e0 > e1 ? e0 - e1 : e1 - e0;
    printf("S5 journal sector erases: %ld %ld\n", e0, e1);
    CHECK(d <= 2, "S5 rotation even");
    CHECK(esfs_mount() == 0 && slot_scan() == 0, "S5 valid after wraps");
    CHECK(audit_verify() >= 0, "S5 audit verifies post-wrap");
    /* audit wrap directly (no pool involvement): 600 records */
    for (int i = 0; i < 600; i++) {
        char m[16];
        snprintf(m, sizeof m, "a%03d", i);
        if (audit_append((uint8_t *)m, 5))
            break;
    }
    CHECK(audit_verify() >= 0, "S5 audit verifies post-rotation");
    {
        long m0 = erases[AUD0], m1 = erases[AUD0 + 1];
        long m2 = erases[AUD0 + 2], m3 = erases[AUD0 + 3];
        long mn = m0, mx = m0;
        long vs[4] = { m0, m1, m2, m3 };
        for (int i = 0; i < 4; i++) {
            if (vs[i] < mn)
                mn = vs[i];
            if (vs[i] > mx)
                mx = vs[i];
        }
        printf("S5 audit sector erases: %ld %ld %ld %ld\n", m0, m1, m2,
               m3);
        CHECK(mx - mn <= 2, "S5 audit rotation even");
    }
    /* pool-full boundary: distinct files until -1, state stays valid */
    esfs_mkfs();
    CHECK(esfs_mount() == 0, "S5 remount");
    int made = 0, hitfull = 0;
    for (int i = 0; i < 300; i++) {
        char nm[16];
        snprintf(nm, sizeof nm, "z%03d", i);
        fill_pat(wbuf, 10, (unsigned)i);
        if (esfs_write(nm, wbuf, 10)) {
            hitfull = 1;
            break;
        }
        made++;
    }
    printf("S5 pool: %d files then full=%d\n", made, hitfull);
    CHECK(hitfull, "S5 pool-full returns -1 (documented v1 limit)");
    CHECK(esfs_mount() == 0 && slot_scan() == 0, "S5 valid at pool-full");
}
/* S6: erase budget trip -> clean read-only failure, state valid */
static void script_S6(void) {
    esfs_mkfs();
    CHECK(esfs_mount() == 0, "S6 mount");
    erase_budget = 4;
    int failed = 0;
    for (int i = 0; i < 150; i++) {
        char nm[16];
        snprintf(nm, sizeof nm, "b%03d", i);
        fill_pat(wbuf, 200, (unsigned)i);
        if (esfs_write(nm, wbuf, 200))
            failed++;
    }
    printf("S6 ops failed cleanly: %d/150\n", failed);
    CHECK(failed > 0, "S6 budget trips (no infinite erase loop)");
    erase_budget = 1000000;
    CHECK(esfs_mount() == 0 && slot_scan() == 0, "S6 valid after trip");
    CHECK(audit_verify() >= 0, "S6 audit verifies after trip");
}

int main(void) {
    esfs_mkfs();
    CHECK(esfs_mount() == 0, "mount fresh");
    script_S1();
    script_S2();
    script_S3();
    script_S4();
    script_S5();
    script_S6();
    printf(fails ? "RESULT: %d FAILURES\n" : "RESULT: ALL PASS\n",
           fails);
    return fails != 0;
}

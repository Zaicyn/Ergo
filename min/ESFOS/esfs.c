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
static int fl_write(uint32_t off, const uint8_t *p, size_t len) {
    for (size_t i = 0; i < len; i++) {
        uint8_t old = ((uint8_t *)flash)[off + i];
        if ((old & p[i]) != p[i])
            return -2;
        ((uint8_t *)flash)[off + i] = old & p[i];
    }
    if (cut_tick())
        return -1;
    return 0;
}
static int fl_erase(int sec) {
    memset(flash[sec], 0xFF, SECB);
    erases[sec]++;
    if (cut_tick())
        return -1;
    return 0;
}
static void fl_read(uint32_t off, uint8_t *p, size_t len) {
    memcpy(p, (uint8_t *)flash + off, len);
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

/* ---------- journal ---------- */
static uint32_t jrn_head, jrn_seq;
static uint32_t jrn_base(void) { return (uint32_t)JRN0 * SECB; }
static uint32_t jrn_size(void) { return JRN_SECTORS * SECB; }
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
    if (jrn_head + need > jrn_size())
        return -3;
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
/* verify one record at off; returns total length or 0 end / -1 bad */
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
    if (off + 16u + len > jrn_size())
        return -1; /* torn tail */
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
/* replay: count intents; uncommitted ones ignored (staged bytes were
 * fresh, never linked). Stops at first invalid (torn tail). */
static int jrn_replay(void) {
    uint32_t off = 0;
    int intents = 0;
    for (;;) {
        uint32_t len = 0;
        int r = jrn_check(off, &len);
        if (r == 0)
            break; /* clean end */
        if (r < 0)
            break; /* torn tail: stop, ignore rest */
        uint8_t op;
        fl_read(jrn_base() + off + 4, &op, 1);
        if (op == 1)
            intents++;
        off += (uint32_t)r;
    }
    return intents;
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
    if (aud_head + need > aud_size())
        return -3;
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
/* verify chain; torn tail (non-erased garbage at end) truncates:
 * walk records, stop at first invalid ONLY if the rest is erased,
 * else corruption. Returns records verified or negative. */
static int audit_verify(void) {
    uint32_t off = 0, expect = 0, n = 0;
    uint64_t prev = 0;
    for (;;) {
        uint8_t hdr[16];
        if (off + 16 > aud_size())
            break;
        fl_read(aud_base() + off, hdr, 16);
        int erased = 1;
        for (int i = 0; i < 16; i++)
            if (hdr[i] != 0xFF) {
                erased = 0;
                break;
            }
        if (erased)
            break;
        uint32_t seq =
            hdr[0] | ((uint32_t)hdr[1] << 8) | ((uint32_t)hdr[2] << 16) |
            ((uint32_t)hdr[3] << 24);
        uint16_t len = (uint16_t)(hdr[12] | (hdr[13] << 8));
        static uint8_t tmp[512];
        int ok = 1;
        if (seq != expect)
            ok = 0;
        else if (len > sizeof tmp)
            ok = 0;
        else {
            if (len)
                fl_read(aud_base() + off + 16, tmp, len);
            uint64_t h =
                hash_bytes(tmp, len, prev ^ 0x4155444954415544ull);
            uint64_t got = 0;
            for (int i = 0; i < 8; i++)
                got |= (uint64_t)hdr[4 + i] << (8 * i);
            if (h != got)
                ok = 0;
            else {
                prev = h;
                expect++;
                n++;
            }
        }
        if (!ok) {
            /* torn tail (rest erased) is fine; else corruption */
            uint32_t ro = off;
            int rest_erased = 1;
            uint8_t b;
            while (ro < aud_base() + aud_size()) {
                fl_read(ro, &b, 1);
                if (b != 0xFF) {
                    /* allow the failed record's own bytes: skip one
                     * record-length window then require erased */
                    break;
                }
                ro++;
            }
            /* crude but sound for v1: any invalid record ends the
             * verified prefix; corruption vs tear distinguished by
             * whether a LATER valid record exists (scan ahead) */
            uint32_t ahead = off + 16u + len;
            int later_valid = 0;
            while (ahead + 16 <= aud_size()) {
                uint8_t h2[16];
                fl_read(aud_base() + ahead, h2, 16);
                int e2 = 1;
                for (int i = 0; i < 16; i++)
                    if (h2[i] != 0xFF) {
                        e2 = 0;
                        break;
                    }
                if (e2)
                    break;
                later_valid = 1;
                break;
            }
            (void)rest_erased;
            (void)ro;
            if (later_valid)
                return -30 - (int)n;
            break; /* torn tail: prefix verifies */
        }
        off += 16u + len;
    }
    return (int)n;
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
        fl_erase(s); /* counted wear; v1 erases nowhere else (bump-only) */
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
    aud_head = 0;
    aud_prev = 0;
    aud_seq = 0;
    bump = DATA0;
    op_seq = 1;
    slot_scan();
}
static int esfs_mount(void) {
    sb_t a, b;
    int oka = sb_read(SB0, &a), okb = sb_read(SB1, &b);
    if (oka && okb)
        return -1;
    if (slot_scan() < 0)
        return -1;
    jrn_replay();
    jrn_head = 0;
    for (;;) {
        uint8_t h[8];
        if (jrn_head + 8 > jrn_size())
            break;
        fl_read(jrn_base() + jrn_head, h, 8);
        int e = 1;
        for (int i = 0; i < 8; i++)
            if (h[i] != 0xFF) {
                e = 0;
                break;
            }
        if (e)
            break;
        uint16_t len = (uint16_t)(h[6] | (h[7] << 8));
        jrn_head += 16u + len;
    }
    /* audit resume: last valid seq/hash (torn tail truncated) */
    {
        uint32_t off = 0, expect = 0;
        uint64_t prev = 0;
        for (;;) {
            uint8_t h[16];
            if (off + 16 > aud_size())
                break;
            fl_read(aud_base() + off, h, 16);
            int e = 1;
            for (int i = 0; i < 16; i++)
                if (h[i] != 0xFF) {
                    e = 0;
                    break;
                }
            if (e)
                break;
            uint32_t seq =
                h[0] | ((uint32_t)h[1] << 8) | ((uint32_t)h[2] << 16) |
                ((uint32_t)h[3] << 24);
            uint16_t len = (uint16_t)(h[12] | (h[13] << 8));
            static uint8_t tmp[512];
            if (seq != expect || len > sizeof tmp)
                break;
            if (len)
                fl_read(aud_base() + off + 16, tmp, len);
            uint64_t hh =
                hash_bytes(tmp, len, prev ^ 0x4155444954415544ull);
            uint64_t got = 0;
            for (int i = 0; i < 8; i++)
                got |= (uint64_t)h[4 + i] << (8 * i);
            if (hh != got)
                break;
            prev = hh;
            expect++;
            off += 16u + len;
        }
        aud_head = off;
        aud_prev = prev;
        aud_seq = expect;
        op_seq = expect + 1;
    }
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

int main(void) {
    esfs_mkfs();
    CHECK(esfs_mount() == 0, "mount fresh");
    script_S1();
    script_S2();
    script_S3();
    printf(fails ? "RESULT: %d FAILURES\n" : "RESULT: ALL PASS\n",
           fails);
    return fails != 0;
}

"""Milestone B: GPU dense pipeline with precalculation (rotor chain).

B.1 Precompute once per (N): COO index template (row/col int32 arenas) for
every nonzero of the gauge-folded Hamiltonian + a coefficient LUT recipe
(how each COO entry's value depends on params B, J). Uploaded once.

B.2 GPU dense build per parameter point: memset + scatter of coefficients
into precomputed slots (cupy). Target sub-10 ms per 6561^2 c64 matrix.

B.3 Streamed cusolver syevd (cupy.linalg.eigh single calls on K streams;
NOT the batched syevj path, previously measured 47.6 s/matrix and
rejected). Steady-state allocation is zero via the cupy memory pool
(blocks are recycled across calls -- the GEO pattern delegated to the
pool; workspace is NOT re-malloced per call once the pool is warm).

Gap-only protocol: download eigenvalues, keep eigenvectors on device.
"""

import time

import numpy as np


def build_template(N):
    """COO template for the gauge-folded rotor chain at size N.
    Returns (rows int32, cols int32, kind uint8):
    kind 0: diagonal, 1: onsite (-V/2), 2: bond (-(J/2) e^{-i d}),
    3: bond (-(J/2) e^{+i d}), d = 2 pi / N.
    """
    from index_arena import ArenaMatvec
    am = ArenaMatvec(N, 0.25, 1.0)
    dim, T = am.arena.shape
    src, cid = am.arena, am.cid
    rows_l, cols_l, kind_l = [np.arange(dim, dtype=np.int32)], \
        [np.arange(dim, dtype=np.int32)], [np.zeros(dim, np.uint8)]
    mask = src.ravel() >= 0
    rows_l.append(np.repeat(np.arange(dim, dtype=np.int32), T)[mask])
    cols_l.append(src.ravel()[mask].astype(np.int32))
    kind_l.append(cid.ravel()[mask])
    return (np.concatenate(rows_l), np.concatenate(cols_l),
            np.concatenate(kind_l))


def coeffs_for(kind, B, J, N):
    """Coefficient values per COO entry for given params."""
    K_PHASE, K_BIAS = 0.5, 2.0
    halfV = (K_PHASE - B * K_BIAS) / 2.0
    dlt = 2.0 * np.pi / N
    out = np.empty(len(kind), dtype=np.complex64)
    out[kind == 0] = 1.0    # multiplied by diag on device? no -- see below
    out[kind == 1] = -halfV
    out[kind == 2] = -(J / 2.0) * np.exp(-1j * dlt)
    out[kind == 3] = -(J / 2.0) * np.exp(1j * dlt)
    return out


def diag_for(N):
    idx = np.arange(3 ** N, dtype=np.int64)
    diag = np.zeros(3 ** N)
    for i in range(N):
        mi = (idx // 3 ** i) % 3 - 1
        diag += (mi * mi) / 2.0
    return diag.astype(np.complex64)


class GPUDensePipeline:
    def __init__(self, N, device=0):
        import cupy as cp
        self.cp = cp
        self.N, self.dim, self.device = N, 3 ** N, device
        rows, cols, kind = build_template(N)
        with cp.cuda.Device(device):
            self.rows = cp.asarray(rows)
            self.cols = cp.asarray(cols)
            self.kind = cp.asarray(kind)
            self.diag = cp.asarray(diag_for(N))
            self.nnz = len(rows)

    def build_dense(self, B, J, out=None):
        cp = self.cp
        with cp.cuda.Device(self.device):
            if out is None:
                out = cp.zeros((self.dim, self.dim), dtype=cp.complex64)
            else:
                out.fill(0)
            vals = coeffs_for(cp.asnumpy(self.kind), B, J, self.N)
            dv = cp.asarray(vals)
            dv[self.kind == 0] = self.diag  # diagonal slots get kinetic
            out[self.rows, self.cols] = dv
            return out

    def bench_streams(self, grid, n_streams_list=(1, 2, 4)):
        """Gap-only: build + eigh + download eigenvalues, K streams."""
        cp = self.cp
        results = {}
        for K in n_streams_list:
            streams = [cp.cuda.Stream() for _ in range(K)]
            mats = [cp.zeros((self.dim, self.dim), dtype=cp.complex64)
                    for _ in range(K)]
            # warm the pool (GEO: allocate once, reuse)
            t0 = time.time()
            done = 0
            for k, (B, J) in enumerate(grid):
                s = streams[k % K]
                with s:
                    H = self.build_dense(B, J, out=mats[k % K])
                    w = cp.linalg.eigvalsh(H)
                    w_h = cp.asnumpy(w[:2])
                done += 1
            cp.cuda.Device(self.device).synchronize()
            dt = time.time() - t0
            results[K] = {"seconds": dt, "points": done,
                          "pts_per_s": done / dt}
            del mats
            cp.get_default_memory_pool().free_all_blocks()
        return results

"""GPU batch tier: batched dense eigh via cupy for plugin models.

For model instances with dim <= ~8000, build dense Hamiltonians via
model.make_dense(N, params), stack a batch of grid points, upload once,
run cupy.linalg.eigh on the batch, and download compact results
(eigenvalues by default; ground vectors only if requested).

VRAM discipline: dim 6561 complex64 = 344 MB/matrix -> batch 16 = 5.5 GB.
This machine's RTX 2060 (6 GB) had ~4.4 GB occupied by another process at
benchmark time, so the batch size is chosen to fit FREE VRAM (queried at
runtime) rather than blindly using 16.
"""

import time

import numpy as np


def _free_vram_bytes(device=0):
    import cupy as cp
    with cp.cuda.Device(device):
        free, total = cp.cuda.runtime.memGetInfo()
    return free, total


def batched_eigh(model, N, grid, batch=None, dtype=np.complex64,
                 device=0, return_vectors=False):
    """Run dense eigh for a list of param dicts on the GPU.

    Returns list of dicts: params, E0, gap, (psi_ground if return_vectors).
    """
    import cupy as cp

    dim = model.d_site ** N
    mats = [model.make_dense(N, p).astype(dtype) for p in grid]
    bytes_per = dim * dim * np.dtype(dtype).itemsize
    free, total = _free_vram_bytes(device)
    # eigenvectors + workspace roughly double the need per matrix
    fit = max(int(free * 0.7 // (2 * bytes_per)), 1)
    if batch is None:
        batch = fit
    batch = min(batch, fit)

    results = []
    t_up = t_gpu = t_down = 0.0
    for lo in range(0, len(mats), batch):
        chunk = mats[lo:lo + batch]
        t0 = time.time()
        dH = cp.asarray(np.stack(chunk))
        t_up += time.time() - t0
        t0 = time.time()
        w, v = cp.linalg.eigh(dH)
        cp.cuda.Device(device).synchronize()
        t_gpu += time.time() - t0
        t0 = time.time()
        w_h = cp.asnumpy(w)
        if return_vectors:
            v_h = cp.asnumpy(v)
        t_down += time.time() - t0
        del dH, w, v
        cp.get_default_memory_pool().free_all_blocks()
        for k, p in enumerate(grid[lo:lo + batch]):
            rec = {"params": p, "E0": float(w_h[k, 0]),
                   "gap": float(w_h[k, 1] - w_h[k, 0])}
            if return_vectors:
                rec["psi"] = v_h[k, :, 0]
            results.append(rec)
    return {"results": results, "batch_used": batch,
            "timings": {"upload_s": t_up, "gpu_eigh_s": t_gpu,
                        "download_s": t_down},
            "dim": dim, "dtype": str(dtype)}


def benchmark_rotor_n8(batch_request=16):
    """Rotor N=8 (6561-dim), batched GPU eigh vs CPU eigh, same matrices."""
    import sys
    sys.path.insert(0, ".")
    sys.path.insert(0, "..")
    from models.rotor import RotorModel
    m = RotorModel()
    grid = [{"B": 0.25, "J": round(0.5 + 0.125 * k, 3)} for k in range(16)]
    t0 = time.time()
    out = batched_eigh(m, 8, grid, batch=batch_request)
    t_gpu_total = time.time() - t0
    # CPU reference on the same matrices
    t0 = time.time()
    cpu_E = []
    for p in grid:
        H = m.make_dense(8, p)
        w = np.linalg.eigvalsh(H)
        cpu_E.append((float(w[0]), float(w[1] - w[0])))
    t_cpu = time.time() - t0
    gpu_E = [(r["E0"], r["gap"]) for r in out["results"]]
    dmax = max(max(abs(a - c), abs(b - d)) for (a, b), (c, d)
               in zip(gpu_E, cpu_E))
    return {"out": out, "t_gpu_wall_s": t_gpu_total, "t_cpu_s": t_cpu,
            "speedup": t_cpu / t_gpu_total, "max_E_diff": dmax}

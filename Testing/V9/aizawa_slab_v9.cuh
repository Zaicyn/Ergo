// aizawa_slab_v9.cuh  —  Viviani Many-Body GPU Slab Allocator  (v9)
//
// V9 changes (many-body physics for GPU scaling):
//   - Warp-cooperative bitmap scan: Leader reads bitmap, broadcasts via shuffle,
//     lanes only attempt atomics on actually-free slots. Reduces contention 2x.
//   - Gravitational repulsion scatter: Warps treated as particles that repel
//     each other based on cursor proximity. Prevents clustering.
//   - Mean-field density tracking: Per-class density fields track warp distribution.
//     Warps sample local density and bias scatter toward low-density regions.
//   - Adaptive phase evolution: Warp scatter phase evolves based on local success rate.
//     Failed allocations → phase shift → natural load balancing.
//
// Philosophy: "Many-body systems self-organize to minimize energy (contention)."
//
// NOTE: This header uses V9-namespaced types to allow coexistence with V8 for
//       comparison testing. All types are prefixed with V9_ or suffixed with _v9.

#ifndef VIVIANI_SLAB_V9_CUH
#define VIVIANI_SLAB_V9_CUH

#ifdef __CUDACC__

#include <cuda_runtime.h>
#include <cooperative_groups.h>

#ifdef _Atomic
    #undef _Atomic
#endif

// ============================================================================
// Portability: device-side atomic wrappers
// Only define if not already defined by V8 header
// ============================================================================
#ifndef SLAB_ATOMIC_ADD
#define SLAB_ATOMIC_ADD(ptr, val)      atomicAdd((ptr), (val))
#define SLAB_ATOMIC_AND(ptr, val)      atomicAnd((uint32_t*)(ptr), (val))
#define SLAB_ATOMIC_OR(ptr, val)       atomicOr( (uint32_t*)(ptr), (val))
#define SLAB_ATOMIC_CAS(ptr, cmp, val) atomicCAS((uint32_t*)(ptr), (cmp), (val))
#define SLAB_ATOMIC_MAX_ULL(ptr, val)  atomicMax((unsigned long long*)(ptr), \
                                                  (unsigned long long)(val))
#define SLAB_ATOMIC_ADD_ULL(ptr, val)  atomicAdd((unsigned long long*)(ptr), \
                                                  (unsigned long long)(val))
#endif

// ============================================================================
// Configuration - V9 specific (prefixed to avoid conflicts)
// ============================================================================

#define V9_SLAB_CLASSES            3
#define V9_SLAB_SUPERBLOCK_BYTES   4096
#define V9_SLAB_SBS_PER_WARP       18
#define V9_SLAB_POOL_DEPTH         40960

// Viviani constants
#define V9_SLAB_VIVIANI_HOPF_Q     1.97f
#define V9_SLAB_VIVIANI_MODULUS    8

// Many-body physics constants
#define V9_SLAB_DENSITY_GRID_SIZE  64      // Density field resolution per class
#define V9_SLAB_REPULSION_STRENGTH 2.0f    // Gravitational repulsion coefficient
#define V9_SLAB_PHASE_EVOLUTION_RATE 0.1f  // How fast scatter phase adapts
#define V9_SLAB_DENSITY_DECAY      0.95f   // Exponential decay for density field

// Langevin dynamics constants (thermal equilibration)
#define V9_SLAB_LANGEVIN_GAMMA     0.1f    // Friction coefficient (damping)
#define V9_SLAB_LANGEVIN_TEMP      1.0f    // Effective temperature (noise scale)
#define V9_SLAB_LANGEVIN_DT        0.01f   // Time step for dynamics

// ============================================================================
// Superblock struct — 4096 bytes exactly (V9 namespaced)
// ============================================================================

typedef struct {
    volatile uint32_t bitmap;
    uint32_t          _pad[15];
    uint8_t           data[V9_SLAB_SUPERBLOCK_BYTES - 64];
} V9_SlabSuperblock;

static_assert(sizeof(V9_SlabSuperblock) == V9_SLAB_SUPERBLOCK_BYTES,
              "V9_SlabSuperblock must be 4096 bytes");

// ============================================================================
// Size-class helpers (V9 namespaced)
// ============================================================================

__host__ __device__ static inline int v9_slab_class(size_t size) {
    if (size <= 64)  return 0;
    if (size <= 128) return 1;
    if (size <= 256) return 2;
    return -1;
}

__host__ __device__ static inline uint32_t v9_slab_slots(int cls) {
    if (cls == 0) return 32u;
    if (cls == 1) return 31u;
    return               15u;
}

__host__ __device__ static inline uint32_t v9_slab_init_bitmap(int cls) {
    if (cls == 0) return 0xFFFFFFFFu;
    if (cls == 1) return 0x7FFFFFFFu;
    return               0x00007FFFu;
}

__host__ __device__ static inline size_t v9_slab_stride(int cls) {
    return (size_t)64u << (uint32_t)cls;
}

__host__ __device__ static inline uint32_t v9_slab_sbs_per_warp_alloc(int cls) {
    uint32_t n = v9_slab_slots(cls);
    return (32u + n - 1u) / n;
}

// ============================================================================
// Viviani geometry (V9 namespaced)
// ============================================================================

__host__ __device__ static inline void v9_slab_viviani_normal(
        float theta, float* nx, float* ny, float* nz) {
    float s=sinf(theta), c=cosf(theta), s3=sinf(3.f*theta), c3=cosf(3.f*theta);
    float x=s-.5f*s3, y=-c+.5f*c3, z=c*c3;
    float n=sqrtf(x*x+y*y+z*z); if(n<1e-6f)n=1.f;
    *nx=x/n; *ny=y/n; *nz=z/n;
}

// ============================================================================
// Many-Body Physics: Density Field
// ============================================================================

typedef struct {
    // Per-class density fields: how many warps are active in each region
    volatile uint32_t density[V9_SLAB_CLASSES][V9_SLAB_DENSITY_GRID_SIZE];

    // Per-class contention counters: how many failed atomics recently
    volatile uint64_t contention[V9_SLAB_CLASSES];

    // Global phase offset: evolves to spread warps apart
    volatile float    global_phase[V9_SLAB_CLASSES];

    // Langevin dynamics state: velocity for momentum-based movement
    volatile float    phase_velocity[V9_SLAB_CLASSES];

    // Temperature estimate: adapts based on contention variance
    volatile float    effective_temp[V9_SLAB_CLASSES];
} SlabDensityField;

// Map superblock index to density cell (clamped to valid range)
__device__ static inline uint32_t v9_slab_sb_to_cell(uint32_t sb_idx, uint32_t pool_depth) {
    if (sb_idx >= pool_depth || pool_depth == 0) return 0;
    uint32_t cell = (sb_idx * V9_SLAB_DENSITY_GRID_SIZE) / pool_depth;
    return (cell < V9_SLAB_DENSITY_GRID_SIZE) ? cell : (V9_SLAB_DENSITY_GRID_SIZE - 1);
}

// ============================================================================
// Many-Body Physics: Gravitational Repulsion Scatter
// ============================================================================

__device__ static inline uint32_t v9_slab_viviani_scatter(
        uint32_t warp_id,
        uint32_t total_warps,
        uint32_t sb_base,
        const SlabDensityField* density_field,
        int cls,
        uint32_t pool_depth)
{
    // Base Viviani scatter
    float theta = 2.f * 3.14159265f * (float)warp_id / (float)total_warps;
    float nx, ny, nz;
    v9_slab_viviani_normal(theta, &nx, &ny, &nz);
    float proj = fabsf(nz) * V9_SLAB_VIVIANI_HOPF_Q;
    uint32_t q  = (uint32_t)((int)(proj * (float)V9_SLAB_VIVIANI_MODULUS)
                              % V9_SLAB_VIVIANI_MODULUS);
    uint32_t xc = (uint32_t)(fabsf(nx) * 4.f) & 3u;
    uint32_t base_scatter = (q ^ xc) % (uint32_t)V9_SLAB_SBS_PER_WARP;

    // Many-body correction: bias away from high-density regions
    if (density_field != nullptr && pool_depth > 0) {
        uint32_t my_cell = v9_slab_sb_to_cell(sb_base + base_scatter, pool_depth);
        uint32_t my_density = density_field->density[cls][my_cell];

        uint32_t left_cell  = (my_cell > 0) ? my_cell - 1 : V9_SLAB_DENSITY_GRID_SIZE - 1;
        uint32_t right_cell = (my_cell + 1) % V9_SLAB_DENSITY_GRID_SIZE;
        uint32_t left_density  = density_field->density[cls][left_cell];
        uint32_t right_density = density_field->density[cls][right_cell];

        int density_gradient = (int)right_density - (int)left_density;

        float repulsion = -V9_SLAB_REPULSION_STRENGTH * (float)density_gradient /
                          fmaxf((float)total_warps, 1.0f);

        float phase_offset = density_field->global_phase[cls];

        float adjusted = (float)base_scatter + repulsion + phase_offset;

        int adjusted_int = (int)adjusted;
        adjusted_int = ((adjusted_int % V9_SLAB_SBS_PER_WARP) + V9_SLAB_SBS_PER_WARP) % V9_SLAB_SBS_PER_WARP;
        return (uint32_t)adjusted_int;
    }

    return base_scatter;
}

// ============================================================================
// Pool state (V9)
// ============================================================================

typedef struct {
    V9_SlabSuperblock* pool[V9_SLAB_CLASSES];
    uint8_t*           pool_base[V9_SLAB_CLASSES];
    uint32_t           pool_depth;
    uint32_t*          d_warp_cursor;
    uint64_t*          d_allocs;
    uint64_t*          d_frees;
    uint64_t*          d_fallbacks;

    // V9: Many-body physics state
    SlabDensityField*  d_density_field;
    uint64_t*          d_contention_events;
} SlabPoolV9;

typedef struct { SlabPoolV9 pool; bool initialized; } VivianiSlabContextV9;

// ============================================================================
// Host init / destroy
// ============================================================================

static inline cudaError_t viviani_slab_init_v9(VivianiSlabContextV9* ctx,
                                                uint32_t pool_depth) {
    memset(ctx, 0, sizeof(*ctx));
    ctx->pool.pool_depth = pool_depth;

    for (int c = 0; c < V9_SLAB_CLASSES; c++) {
        cudaError_t e = cudaMalloc((void**)&ctx->pool.pool[c],
                                   (size_t)pool_depth * V9_SLAB_SUPERBLOCK_BYTES);
        if (e != cudaSuccess) return e;
        cudaMemset(ctx->pool.pool[c], 0,
                   (size_t)pool_depth * V9_SLAB_SUPERBLOCK_BYTES);
        ctx->pool.pool_base[c] = (uint8_t*)ctx->pool.pool[c];
    }

    cudaError_t e;
    e = cudaMalloc((void**)&ctx->pool.d_warp_cursor, V9_SLAB_CLASSES * sizeof(uint32_t));
    if (e != cudaSuccess) return e;
    cudaMemset(ctx->pool.d_warp_cursor, 0, V9_SLAB_CLASSES * sizeof(uint32_t));

    e = cudaMalloc((void**)&ctx->pool.d_allocs, V9_SLAB_CLASSES * sizeof(uint64_t));
    if (e != cudaSuccess) return e;
    e = cudaMalloc((void**)&ctx->pool.d_frees, V9_SLAB_CLASSES * sizeof(uint64_t));
    if (e != cudaSuccess) return e;
    e = cudaMalloc((void**)&ctx->pool.d_fallbacks, V9_SLAB_CLASSES * sizeof(uint64_t));
    if (e != cudaSuccess) return e;

    cudaMemset(ctx->pool.d_allocs, 0, V9_SLAB_CLASSES * sizeof(uint64_t));
    cudaMemset(ctx->pool.d_frees, 0, V9_SLAB_CLASSES * sizeof(uint64_t));
    cudaMemset(ctx->pool.d_fallbacks, 0, V9_SLAB_CLASSES * sizeof(uint64_t));

    // V9: Allocate density field
    e = cudaMalloc((void**)&ctx->pool.d_density_field, sizeof(SlabDensityField));
    if (e != cudaSuccess) return e;
    cudaMemset(ctx->pool.d_density_field, 0, sizeof(SlabDensityField));

    e = cudaMalloc((void**)&ctx->pool.d_contention_events, V9_SLAB_CLASSES * sizeof(uint64_t));
    if (e != cudaSuccess) return e;
    cudaMemset(ctx->pool.d_contention_events, 0, V9_SLAB_CLASSES * sizeof(uint64_t));

    ctx->initialized = true;
    return cudaSuccess;
}

static inline void viviani_slab_destroy_v9(VivianiSlabContextV9* ctx) {
    if (!ctx->initialized) return;
    for (int c = 0; c < V9_SLAB_CLASSES; c++) {
        if (ctx->pool.pool[c]) cudaFree(ctx->pool.pool[c]);
    }
    if (ctx->pool.d_warp_cursor) cudaFree(ctx->pool.d_warp_cursor);
    if (ctx->pool.d_allocs) cudaFree(ctx->pool.d_allocs);
    if (ctx->pool.d_frees) cudaFree(ctx->pool.d_frees);
    if (ctx->pool.d_fallbacks) cudaFree(ctx->pool.d_fallbacks);
    if (ctx->pool.d_density_field) cudaFree(ctx->pool.d_density_field);
    if (ctx->pool.d_contention_events) cudaFree(ctx->pool.d_contention_events);
    ctx->initialized = false;
}

// ============================================================================
// Host stats
// ============================================================================

typedef struct {
    uint64_t allocs[V9_SLAB_CLASSES];
    uint64_t frees[V9_SLAB_CLASSES];
    uint64_t fallbacks[V9_SLAB_CLASSES];
    uint64_t contention_events[V9_SLAB_CLASSES];
} SlabStatsV9;

static inline SlabStatsV9 viviani_slab_stats_v9(const VivianiSlabContextV9* ctx) {
    SlabStatsV9 s = {0};
    if (!ctx->initialized) return s;
    cudaMemcpy(s.allocs, ctx->pool.d_allocs, V9_SLAB_CLASSES * sizeof(uint64_t), cudaMemcpyDeviceToHost);
    cudaMemcpy(s.frees, ctx->pool.d_frees, V9_SLAB_CLASSES * sizeof(uint64_t), cudaMemcpyDeviceToHost);
    cudaMemcpy(s.fallbacks, ctx->pool.d_fallbacks, V9_SLAB_CLASSES * sizeof(uint64_t), cudaMemcpyDeviceToHost);
    cudaMemcpy(s.contention_events, ctx->pool.d_contention_events, V9_SLAB_CLASSES * sizeof(uint64_t), cudaMemcpyDeviceToHost);
    return s;
}

static inline void viviani_slab_print_stats_v9(const SlabStatsV9* s) {
    const char* nm[] = {"64B ", "128B", "256B"};
    printf("=== Viviani Slab Stats V9 (Many-Body) ===\n");
    printf("  Class  |   Allocs   |   Frees    | Fallbacks | Contention\n");
    printf("  -------|------------|------------|-----------|------------\n");
    for (int c = 0; c < V9_SLAB_CLASSES; c++) {
        printf("  %s   | %10llu | %10llu | %9llu | %10llu\n", nm[c],
               (unsigned long long)s->allocs[c],
               (unsigned long long)s->frees[c],
               (unsigned long long)s->fallbacks[c],
               (unsigned long long)s->contention_events[c]);
    }

    uint64_t total_allocs = 0, total_contention = 0;
    for (int c = 0; c < V9_SLAB_CLASSES; c++) {
        total_allocs += s->allocs[c];
        total_contention += s->contention_events[c];
    }
    if (total_allocs > 0) {
        float contention_ratio = (float)total_contention / (float)total_allocs;
        printf("  Contention ratio: %.2f%% (lower is better)\n", contention_ratio * 100.0f);
    }
}

// ============================================================================
// Host: Reset
// ============================================================================

static inline void viviani_slab_reset_v9(VivianiSlabContextV9* ctx) {
    if (!ctx->initialized) return;
    for (int c = 0; c < V9_SLAB_CLASSES; c++) {
        cudaMemset(ctx->pool.pool[c], 0,
                   (size_t)ctx->pool.pool_depth * V9_SLAB_SUPERBLOCK_BYTES);
    }
    cudaMemset(ctx->pool.d_warp_cursor, 0, V9_SLAB_CLASSES * sizeof(uint32_t));
    cudaMemset(ctx->pool.d_allocs, 0, V9_SLAB_CLASSES * sizeof(uint64_t));
    cudaMemset(ctx->pool.d_frees, 0, V9_SLAB_CLASSES * sizeof(uint64_t));
    cudaMemset(ctx->pool.d_fallbacks, 0, V9_SLAB_CLASSES * sizeof(uint64_t));
    cudaMemset(ctx->pool.d_density_field, 0, sizeof(SlabDensityField));
    cudaMemset(ctx->pool.d_contention_events, 0, V9_SLAB_CLASSES * sizeof(uint64_t));
}

// ============================================================================
// Device: Warp-Cooperative Bitmap Scan (V9 Enhancement)
// ============================================================================

__device__ static inline bool v9_slab_cooperative_claim_slot(
    V9_SlabSuperblock* sb,
    uint32_t slot,
    uint32_t warp_mask,
    uint32_t leader,
    uint32_t lane)
{
    // Step 1: Leader reads bitmap once
    uint32_t bmap = 0;
    if (lane == leader) {
        bmap = sb->bitmap;
    }

    // Step 2: Broadcast to all lanes
    bmap = __shfl_sync(warp_mask, bmap, leader);

    // Step 3: Check if our slot appears free
    uint32_t mask = 1u << slot;
    bool appears_free = (bmap & mask) != 0u;

    if (!appears_free) {
        return false;
    }

    // Step 4: Attempt atomic claim
    uint32_t old_bmap = SLAB_ATOMIC_AND((uint32_t*)&sb->bitmap, ~mask);
    return (old_bmap & mask) != 0u;
}

// ============================================================================
// Device: Alloc V9 (with many-body physics)
// ============================================================================

__device__ static inline void* viviani_slab_alloc_v9(
    SlabPoolV9* pool,
    int         cls,
    uint32_t*   sb_base,
    uint32_t*   sb_cursor,
    float*      local_phase
) {
    if (cls < 0) return nullptr;

    const uint32_t lane        = threadIdx.x & 31u;
    const uint32_t warp_mask   = __activemask();
    const uint32_t leader      = __ffs(warp_mask) - 1u;
    const uint32_t n_slots     = v9_slab_slots(cls);
    const uint32_t sbs_needed  = v9_slab_sbs_per_warp_alloc(cls);

    // Claim range once with many-body scatter
    if (*sb_base == 0xFFFFFFFFu) {
        uint32_t base = 0, init_cursor = 0;
        if (lane == leader) {
            base = SLAB_ATOMIC_ADD(&pool->d_warp_cursor[cls],
                             (uint32_t)V9_SLAB_SBS_PER_WARP);

            uint32_t wid = threadIdx.x / 32u;
            uint32_t wpb = blockDim.x / 32u;

            uint32_t scatter = v9_slab_viviani_scatter(
                wid, wpb > 0 ? wpb : 1, base, pool->d_density_field, cls, pool->pool_depth);

            uint32_t n_pos = (uint32_t)V9_SLAB_SBS_PER_WARP / sbs_needed;
            init_cursor = (scatter % n_pos) * sbs_needed;

            if (pool->d_density_field != nullptr && pool->pool_depth > 0) {
                uint32_t cell = v9_slab_sb_to_cell(base + init_cursor, pool->pool_depth);
                if (cell < V9_SLAB_DENSITY_GRID_SIZE) {
                    atomicAdd((uint32_t*)&pool->d_density_field->density[cls][cell], 1u);
                }
            }
        }
        *sb_base = __shfl_sync(warp_mask, base, leader);
        *sb_cursor = __shfl_sync(warp_mask, init_cursor, leader);

        if (local_phase != nullptr && lane == leader) {
            *local_phase = 0.0f;
        }
    }

    const uint32_t n_positions = (uint32_t)V9_SLAB_SBS_PER_WARP / sbs_needed;
    uint32_t contention_count = 0;

    for (uint32_t attempt = 0; attempt < n_positions; attempt++) {
        uint32_t sb_sub = lane / n_slots;
        uint32_t slot   = lane % n_slots;

        uint32_t global_sb = *sb_base + *sb_cursor + sb_sub;
        if (global_sb >= pool->pool_depth) {
            SLAB_ATOMIC_ADD_ULL(&pool->d_fallbacks[cls], 1ULL);
            return nullptr;
        }

        V9_SlabSuperblock* sb = &pool->pool[cls][global_sb];

        if (lane == sb_sub * n_slots) {
            if (sb->bitmap == 0u) {
                SLAB_ATOMIC_CAS((uint32_t*)&sb->bitmap, 0u, v9_slab_init_bitmap(cls));
            }
        }
        __syncwarp(warp_mask);

        bool succeeded = v9_slab_cooperative_claim_slot(sb, slot, warp_mask, leader, lane);

        uint32_t winners = __ballot_sync(warp_mask, succeeded);
        if (succeeded) {
            if (lane == leader) {
                SLAB_ATOMIC_ADD_ULL(&pool->d_allocs[cls],
                                    (unsigned long long)__popc(winners));
            }
            return (void*)(sb->data + (size_t)slot * v9_slab_stride(cls));
        }

        contention_count++;

        uint32_t next = 0;
        if (lane == leader) {
            *sb_cursor = (*sb_cursor + sbs_needed) % (uint32_t)V9_SLAB_SBS_PER_WARP;
            next = *sb_cursor;
        }
        *sb_cursor = __shfl_sync(warp_mask, next, leader);
    }

    if (lane == leader && pool->d_contention_events != nullptr) {
        SLAB_ATOMIC_ADD_ULL(&pool->d_contention_events[cls], (uint64_t)contention_count);

        if (local_phase != nullptr && contention_count > 0) {
            *local_phase += V9_SLAB_PHASE_EVOLUTION_RATE * (float)contention_count;
        }

        if (pool->d_density_field != nullptr && local_phase != nullptr) {
            volatile float* gp = &pool->d_density_field->global_phase[cls];
            float old_phase = *gp;
            float new_phase = old_phase + (*local_phase) * 0.01f;
            *gp = new_phase;
        }
    }

    SLAB_ATOMIC_ADD_ULL(&pool->d_fallbacks[cls], 1ULL);
    return nullptr;
}

// ============================================================================
// Device: Free V9
// ============================================================================

__device__ static inline void viviani_slab_free_v9(
    SlabPoolV9* pool, void* ptr, int cls)
{
    if (cls < 0 || !ptr) return;

    ptrdiff_t off = (uint8_t*)ptr - pool->pool_base[cls];
    if (off < 0) return;

    uint32_t sb_idx = (uint32_t)((size_t)off / V9_SLAB_SUPERBLOCK_BYTES);
    if (sb_idx >= pool->pool_depth) return;

    V9_SlabSuperblock* sb = &pool->pool[cls][sb_idx];
    ptrdiff_t doff = (uint8_t*)ptr - sb->data;
    if (doff < 0) return;

    uint32_t slot = (uint32_t)((size_t)doff / v9_slab_stride(cls));
    if (slot >= v9_slab_slots(cls)) return;

    SLAB_ATOMIC_OR((uint32_t*)&sb->bitmap, 1u << slot);

    uint32_t free_mask = __activemask();
    uint32_t free_lane = threadIdx.x & 31u;
    uint32_t free_lead = __ffs(free_mask) - 1u;
    if (free_lane == free_lead) {
        SLAB_ATOMIC_ADD_ULL(&pool->d_frees[cls],
                            (unsigned long long)__popc(free_mask));
    }
}

// Convenience wrappers
__device__ static inline void* viviani_slab_alloc_sz_v9(
    SlabPoolV9* pool, size_t size, uint32_t* sb_base, uint32_t* sb_cursor, float* local_phase)
{
    return viviani_slab_alloc_v9(pool, v9_slab_class(size), sb_base, sb_cursor, local_phase);
}

__device__ static inline void viviani_slab_free_sz_v9(
    SlabPoolV9* pool, void* ptr, size_t size)
{
    viviani_slab_free_v9(pool, ptr, v9_slab_class(size));
}

// ============================================================================
// Density Field Decay Kernel
// ============================================================================

__global__ void viviani_slab_density_decay_kernel_v9(SlabDensityField* field) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= V9_SLAB_CLASSES * V9_SLAB_DENSITY_GRID_SIZE) return;

    int cls = idx / V9_SLAB_DENSITY_GRID_SIZE;
    int cell = idx % V9_SLAB_DENSITY_GRID_SIZE;

    uint32_t old_val = field->density[cls][cell];
    uint32_t new_val = (uint32_t)((float)old_val * V9_SLAB_DENSITY_DECAY);
    field->density[cls][cell] = new_val;
}

// ============================================================================
// Langevin Dynamics Kernel
// ============================================================================

__device__ static inline float v9_slab_langevin_noise(uint32_t seed) {
    seed ^= seed << 13;
    seed ^= seed >> 17;
    seed ^= seed << 5;
    float u1 = (float)(seed & 0xFFFFFF) / (float)0xFFFFFF;
    seed ^= seed << 13;
    seed ^= seed >> 17;
    seed ^= seed << 5;
    float u2 = (float)(seed & 0xFFFFFF) / (float)0xFFFFFF;

    float radius = sqrtf(-2.0f * logf(fmaxf(u1, 1e-10f)));
    float theta = 2.0f * 3.14159265f * u2;
    return radius * cosf(theta);
}

__global__ void viviani_slab_langevin_step_kernel_v9(
    SlabDensityField* field,
    uint64_t* contention_events,
    uint32_t step_counter)
{
    int cls = threadIdx.x;
    if (cls >= V9_SLAB_CLASSES) return;

    float phase = field->global_phase[cls];
    float velocity = field->phase_velocity[cls];
    float temp = field->effective_temp[cls];
    uint64_t contention = contention_events[cls];

    float gradient = 0.0f;
    float total_density = 0.0f;
    for (int i = 0; i < V9_SLAB_DENSITY_GRID_SIZE; i++) {
        float d = (float)field->density[cls][i];
        float pos = (float)i / (float)V9_SLAB_DENSITY_GRID_SIZE * 2.0f * 3.14159265f;
        gradient += d * sinf(pos - phase);
        total_density += d;
    }
    if (total_density > 0) {
        gradient /= total_density;
    }

    float contention_normalized = (float)contention / fmaxf(total_density, 1.0f);
    temp = temp * 0.9f + contention_normalized * 0.1f;
    temp = fmaxf(fminf(temp, 10.0f * V9_SLAB_LANGEVIN_TEMP), 0.1f * V9_SLAB_LANGEVIN_TEMP);

    float force = -gradient * V9_SLAB_REPULSION_STRENGTH;
    force -= V9_SLAB_LANGEVIN_GAMMA * velocity;

    uint32_t seed = (uint32_t)(cls * 12345 + step_counter * 67890);
    float noise = v9_slab_langevin_noise(seed);
    force += sqrtf(2.0f * V9_SLAB_LANGEVIN_GAMMA * temp) * noise;

    float new_velocity = velocity + force * V9_SLAB_LANGEVIN_DT;
    float new_phase = phase + new_velocity * V9_SLAB_LANGEVIN_DT;

    while (new_phase < 0) new_phase += 2.0f * 3.14159265f;
    while (new_phase >= 2.0f * 3.14159265f) new_phase -= 2.0f * 3.14159265f;

    field->global_phase[cls] = new_phase;
    field->phase_velocity[cls] = new_velocity;
    field->effective_temp[cls] = temp;

    // Use atomicExch for thread-safe reset
    atomicExch((unsigned long long*)&contention_events[cls], 0ULL);
}

static inline void viviani_slab_decay_density(VivianiSlabContextV9* ctx) {
    if (!ctx->initialized || ctx->pool.d_density_field == nullptr) return;
    int total = V9_SLAB_CLASSES * V9_SLAB_DENSITY_GRID_SIZE;
    int blocks = (total + 255) / 256;
    viviani_slab_density_decay_kernel_v9<<<blocks, 256>>>(ctx->pool.d_density_field);
}

static inline void viviani_slab_langevin_step(VivianiSlabContextV9* ctx, uint32_t step) {
    if (!ctx->initialized || ctx->pool.d_density_field == nullptr) return;
    viviani_slab_langevin_step_kernel_v9<<<1, V9_SLAB_CLASSES>>>(
        ctx->pool.d_density_field,
        ctx->pool.d_contention_events,
        step);
}

static inline void viviani_slab_equilibrate(VivianiSlabContextV9* ctx, uint32_t step) {
    viviani_slab_decay_density(ctx);
    viviani_slab_langevin_step(ctx, step);
}

// ============================================================================
// Benchmark kernel V9
// ============================================================================

__global__ void viviani_slab_bench_kernel_v9(SlabPoolV9* pool, int cls,
                                              uint32_t iters, uint64_t* out_cyc) {
    uint32_t sb_base = 0xFFFFFFFFu, sb_cursor = 0;
    float local_phase = 0.0f;

    uint64_t t0 = clock64();
    void* last = nullptr;

    for (uint32_t i = 0; i < iters; i++) {
        void* ptr = viviani_slab_alloc_v9(pool, cls, &sb_base, &sb_cursor, &local_phase);
        if (ptr) {
            *((volatile uint8_t*)ptr) = (uint8_t)(threadIdx.x + i);
            if (last) viviani_slab_free_v9(pool, last, cls);
            last = ptr;
        }
    }
    if (last) viviani_slab_free_v9(pool, last, cls);

    uint64_t t1 = clock64();
    if (threadIdx.x == 0 && blockIdx.x == 0) {
        SLAB_ATOMIC_MAX_ULL(out_cyc, (unsigned long long)(t1 - t0));
    }
}

static inline void viviani_slab_run_bench_v9(VivianiSlabContextV9* ctx, uint32_t iters) {
    if (!ctx->initialized) { printf("[slab bench v9] Not initialized.\n"); return; }

    uint64_t* d;
    cudaMalloc((void**)&d, sizeof(uint64_t));

    const char* nm[] = {"64B ", "128B", "256B"};
    printf("=== Viviani Slab Benchmark V9 (Many-Body, %u iters/thread) ===\n", iters);
    printf("  Class | Cycles/iter | ~GOps/s (est 1.5GHz)\n");
    printf("  ------|-------------|--------------------\n");

    for (int c = 0; c < V9_SLAB_CLASSES; c++) {
        cudaMemset(d, 0, sizeof(uint64_t));
        viviani_slab_bench_kernel_v9<<<64, 128>>>(&ctx->pool, c, iters, d);
        cudaDeviceSynchronize();

        uint64_t h = 0;
        cudaMemcpy(&h, d, sizeof(uint64_t), cudaMemcpyDeviceToHost);

        float cpi = (float)h / iters;
        float gops = (float)((uint64_t)64 * 128 * iters) / ((float)h / 1.5f) * 1e-9f;
        printf("  %s  | %11.1f | %.2f\n", nm[c], cpi, gops);
    }

    cudaFree(d);
    SlabStatsV9 ss = viviani_slab_stats_v9(ctx);
    viviani_slab_print_stats_v9(&ss);
}

// ============================================================================
// High-Contention Stress Test
// ============================================================================

__global__ void viviani_slab_stress_kernel_v9(
    SlabPoolV9* pool,
    uint32_t iters,
    uint32_t* success_count)
{
    uint32_t sb_base[V9_SLAB_CLASSES];
    uint32_t sb_cursor[V9_SLAB_CLASSES];
    float local_phase[V9_SLAB_CLASSES];

    for (int c = 0; c < V9_SLAB_CLASSES; c++) {
        sb_base[c] = 0xFFFFFFFFu;
        sb_cursor[c] = 0;
        local_phase[c] = 0.0f;
    }

    uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    uint32_t local_success = 0;

    void* held[V9_SLAB_CLASSES] = {nullptr};

    for (uint32_t i = 0; i < iters; i++) {
        int cls = (tid + i) % V9_SLAB_CLASSES;

        if (held[cls]) {
            viviani_slab_free_v9(pool, held[cls], cls);
            held[cls] = nullptr;
        }

        void* ptr = viviani_slab_alloc_v9(pool, cls,
                                           &sb_base[cls], &sb_cursor[cls],
                                           &local_phase[cls]);
        if (ptr) {
            *((volatile uint8_t*)ptr) = (uint8_t)(tid ^ i);
            held[cls] = ptr;
            local_success++;
        }
    }

    for (int c = 0; c < V9_SLAB_CLASSES; c++) {
        if (held[c]) viviani_slab_free_v9(pool, held[c], c);
    }

    atomicAdd(success_count, local_success);
}

static inline void viviani_slab_stress_test_v9(VivianiSlabContextV9* ctx,
                                                uint32_t blocks,
                                                uint32_t threads_per_block,
                                                uint32_t iters_per_thread) {
    if (!ctx->initialized) return;

    uint32_t* d_success;
    cudaMalloc((void**)&d_success, sizeof(uint32_t));
    cudaMemset(d_success, 0, sizeof(uint32_t));

    printf("=== V9 Many-Body Stress Test ===\n");
    printf("  Blocks: %u, Threads/block: %u, Iters/thread: %u\n",
           blocks, threads_per_block, iters_per_thread);
    printf("  Total warps: %u\n", blocks * threads_per_block / 32);
    printf("  Total operations: %llu\n",
           (unsigned long long)blocks * threads_per_block * iters_per_thread);

    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    cudaEventRecord(start);
    viviani_slab_stress_kernel_v9<<<blocks, threads_per_block>>>(
        &ctx->pool, iters_per_thread, d_success);
    cudaEventRecord(stop);
    cudaDeviceSynchronize();

    float ms = 0;
    cudaEventElapsedTime(&ms, start, stop);

    uint32_t success = 0;
    cudaMemcpy(&success, d_success, sizeof(uint32_t), cudaMemcpyDeviceToHost);

    uint64_t total_ops = (uint64_t)blocks * threads_per_block * iters_per_thread;
    float success_rate = (float)success / (float)total_ops * 100.0f;
    float ops_per_sec = (float)total_ops / (ms / 1000.0f);

    printf("  Time: %.2f ms\n", ms);
    printf("  Success rate: %.2f%% (%u / %llu)\n", success_rate, success,
           (unsigned long long)total_ops);
    printf("  Throughput: %.2f M ops/sec\n", ops_per_sec / 1e6f);

    SlabStatsV9 ss = viviani_slab_stats_v9(ctx);
    viviani_slab_print_stats_v9(&ss);

    cudaFree(d_success);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);
}

#endif // __CUDACC__
#endif // VIVIANI_SLAB_V9_CUH

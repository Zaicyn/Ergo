/*
 * vk_host.c — Vulkan compute + render runtime for Ergo
 *
 * Single-file C99 implementation. Raw Vulkan C API, no wrappers.
 *
 * This file is compiled once and linked into every Ergo GPU executable.
 * Generated host code includes ergo_vk.h and calls the flat API;
 * it never touches Vulkan types directly.
 *
 * Headless mode:  compute only (no window, no GLFW).
 * Render mode:    compute + GLFW window + swapchain + present.
 * Inc-2B: ergo_vk_create_buffer asserts size <= maxStorageBufferRange
 *   (queried once) — oversized vectors must use gather-window streaming.
 */

#include "ergo_vk.h"

#include <vulkan/vulkan.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <math.h>

/* owned f32 trig for the camera path: same bits as the compute and
 * render-shader cores (trig32 shared core, op map §3) */
#include "ergo_math_kernels.h"

#ifndef ERGO_BUILD_VERSION
#define ERGO_BUILD_VERSION "unknown"
#endif

/*
 * ERGO_BENCH_VK_ALLOC — opt-in instrumentation for Pass 3 of the
 * allocator comparison. When defined at compile time, ergo_vk_create_buffer
 * records per-call wall-clock for each of {vkCreateBuffer, vkAllocateMemory,
 * vkBindBufferMemory} and prints a summary at program exit (registered via
 * atexit). Off by default; the production build path pays zero overhead.
 *
 * Build with: -DERGO_BENCH_VK_ALLOC
 * See Testing/COMPARISON_TABLE.md Sub-table 2 for the measured numbers.
 */
#ifdef ERGO_BENCH_VK_ALLOC
/* Note: requires -D_POSIX_C_SOURCE=199309L on the gcc command line so
 * <time.h> exposes clock_gettime under -std=c99. Defining the macro
 * here is too late — <stdio.h> at the top of the file has already
 * been preprocessed without it. */
#include <time.h>
#define ERGO_BENCH_MAX_CALLS 4096
typedef struct {
    double create_ns;
    double alloc_ns;
    double bind_ns;
    size_t bytes;
} ergo_bench_record;
static ergo_bench_record _ergo_bench_calls[ERGO_BENCH_MAX_CALLS];
static int _ergo_bench_count = 0;
static int _ergo_bench_atexit_registered = 0;

static double _ergo_bench_now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec * 1e9 + (double)t.tv_nsec;
}

static void _ergo_bench_report(void) {
    if (_ergo_bench_count == 0) return;
    fprintf(stderr, "\n=== ERGO_BENCH_VK_ALLOC: %d buffer creations ===\n",
            _ergo_bench_count);
    fprintf(stderr, "%-5s %12s %12s %12s %12s %10s\n",
            "call#", "create(µs)", "alloc(µs)", "bind(µs)", "total(µs)", "bytes");
    double sum_c = 0, sum_a = 0, sum_b = 0, sum_t = 0;
    /* Print first 3 (cold) + last 3 (warm) + summary for everything in between. */
    int print_first = _ergo_bench_count < 6 ? _ergo_bench_count : 3;
    for (int i = 0; i < print_first; i++) {
        double t = _ergo_bench_calls[i].create_ns
                 + _ergo_bench_calls[i].alloc_ns
                 + _ergo_bench_calls[i].bind_ns;
        fprintf(stderr, "%-5d %12.2f %12.2f %12.2f %12.2f %10zu\n",
                i,
                _ergo_bench_calls[i].create_ns / 1000.0,
                _ergo_bench_calls[i].alloc_ns / 1000.0,
                _ergo_bench_calls[i].bind_ns / 1000.0,
                t / 1000.0,
                _ergo_bench_calls[i].bytes);
    }
    if (_ergo_bench_count > 6) {
        fprintf(stderr, "  ...  (calls %d through %d omitted)\n",
                print_first, _ergo_bench_count - 4);
        for (int i = _ergo_bench_count - 3; i < _ergo_bench_count; i++) {
            double t = _ergo_bench_calls[i].create_ns
                     + _ergo_bench_calls[i].alloc_ns
                     + _ergo_bench_calls[i].bind_ns;
            fprintf(stderr, "%-5d %12.2f %12.2f %12.2f %12.2f %10zu\n",
                    i,
                    _ergo_bench_calls[i].create_ns / 1000.0,
                    _ergo_bench_calls[i].alloc_ns / 1000.0,
                    _ergo_bench_calls[i].bind_ns / 1000.0,
                    t / 1000.0,
                    _ergo_bench_calls[i].bytes);
        }
    }
    /* Cold vs warm splits */
    double cold_create = _ergo_bench_calls[0].create_ns;
    double cold_alloc  = _ergo_bench_calls[0].alloc_ns;
    double cold_bind   = _ergo_bench_calls[0].bind_ns;
    for (int i = 0; i < _ergo_bench_count; i++) {
        sum_c += _ergo_bench_calls[i].create_ns;
        sum_a += _ergo_bench_calls[i].alloc_ns;
        sum_b += _ergo_bench_calls[i].bind_ns;
    }
    sum_t = sum_c + sum_a + sum_b;
    if (_ergo_bench_count > 1) {
        double warm_c = (sum_c - cold_create) / (_ergo_bench_count - 1);
        double warm_a = (sum_a - cold_alloc)  / (_ergo_bench_count - 1);
        double warm_b = (sum_b - cold_bind)   / (_ergo_bench_count - 1);
        fprintf(stderr,
                "cold (call 0)         : create=%.2fµs alloc=%.2fµs bind=%.2fµs total=%.2fµs\n",
                cold_create / 1000.0, cold_alloc / 1000.0, cold_bind / 1000.0,
                (cold_create + cold_alloc + cold_bind) / 1000.0);
        fprintf(stderr,
                "warm (mean of %d post): create=%.2fµs alloc=%.2fµs bind=%.2fµs total=%.2fµs\n",
                _ergo_bench_count - 1,
                warm_c / 1000.0, warm_a / 1000.0, warm_b / 1000.0,
                (warm_c + warm_a + warm_b) / 1000.0);
    } else {
        fprintf(stderr, "(only 1 allocation — cold-only; no warm cohort)\n");
    }
    fprintf(stderr, "aggregate sum         : %.2f µs across %d calls\n",
            sum_t / 1000.0, _ergo_bench_count);
}
#endif

#ifdef ERGO_VK_ANDROID
#include <vulkan/vulkan_android.h>
#include <android/native_window.h>
#include <android/log.h>
#define ERGO_LOG(...) __android_log_print(ANDROID_LOG_INFO, "ergo", __VA_ARGS__)
/* Render shaders deferred — headless Android doesn't render yet */
#elif !defined(ERGO_VK_HEADLESS_ONLY)
#define GLFW_INCLUDE_VULKAN
#include <GLFW/glfw3.h>
#include "render_shaders.h"
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ── Limits ──────────────────────────────────────────────── */

#define ERGO_VK_MAX_BUFFERS   64
#define ERGO_VK_MAX_PIPELINES 64
#define ERGO_VK_MAX_BINDINGS  32
#define ERGO_VK_MAX_SWAPCHAIN 4

/* ── Internal state ──────────────────────────────────────── */

typedef struct {
    VkBuffer       buffer;
    VkDeviceMemory memory;
    VkDeviceSize   size;
    int            in_use;
    ErgoVkBuf      pair;  /* paired buffer for double-buffering (0 = none) */
} BufSlot;

typedef struct {
    VkPipeline          pipeline;
    VkPipelineLayout    layout;
    VkDescriptorSetLayout ds_layout;
    VkDescriptorPool    ds_pool;
    /* One descriptor set per frame slot (g.cmd_bufs/g.fences index).
     * Frame N+1's host-side binds write ds[cmd_idx] only, so they never
     * rewrite a set that frame N's still-pending command buffer
     * references (WAR hazard, VUID-vkUpdateDescriptorSets-None-03047). */
    VkDescriptorSet     ds[2];
    VkShaderModule      shader;
    int                 n_buffers;
    size_t              pc_size;
    uint8_t             pc_data[256];
    ErgoVkBuf           bound_bufs[ERGO_VK_MAX_BINDINGS];
    int                 in_use;
} PipeSlot;

static struct {
    /* Core Vulkan */
    VkInstance               instance;
    VkPhysicalDevice         phys_device;
    VkDevice                 device;
    VkQueue                  compute_queue;
    uint32_t                 queue_family;
    VkCommandPool            cmd_pool;
    VkCommandBuffer          cmd_buf;       /* current frame's cmd buf */
    VkFence                  fence;         /* current frame's fence */
    /* Double-buffered cmd bufs + fences for GPU pipelining */
    VkCommandBuffer          cmd_bufs[2];
    VkFence                  fences[2];
    int                      cmd_idx;       /* 0 or 1, flips each frame */
    /* Dedicated sort command buffer (avoids resetting in-flight bufs) */
    VkCommandBuffer          sort_cmd_buf;
    VkPhysicalDeviceMemoryProperties mem_props;

    /* Resources */
    BufSlot                  bufs[ERGO_VK_MAX_BUFFERS];
    PipeSlot                 pipes[ERGO_VK_MAX_PIPELINES];

    /* Ping-pong render offset (set by codegen before render call) */
    size_t                   render_offset;  /* byte offset for PP_WR in render buffers */

    /* GPU timestamp profiling */
    VkQueryPool              ts_pool;
    float                    ts_period;   /* nanoseconds per tick */
    int                      ts_active;   /* profiling enabled */
    int                      ts_idx;      /* next query slot */
    double                   ts_accum[16];/* accumulated ms per slot */
    int                      ts_count;    /* frames profiled */

    /* Double-buffer ping-pong */
    int                      frame_parity;  /* 0 or 1, flips each frame */

    /* Staging buffer for host↔device transfers */
    VkBuffer                 staging_buf;
    VkDeviceMemory           staging_mem;
    size_t                   staging_size;
    void                    *staging_mapped;  /* persistently mapped */

    /* Transfer command buffer — safe to use during frame recording.
     * The main cmd_buf is busy recording compute dispatches between
     * frame_begin/frame_end; xfer_cmd_buf handles mid-frame downloads. */
    VkCommandBuffer          xfer_cmd_buf;
    VkFence                  xfer_fence;

#if defined(ERGO_VK_ANDROID) || !defined(ERGO_VK_HEADLESS_ONLY)
    /* Window + swapchain (render mode) */
#ifdef ERGO_VK_ANDROID
    ANativeWindow           *android_window;
#else
    GLFWwindow              *window;
#endif
    VkSurfaceKHR             surface;
    VkSwapchainKHR           swapchain;
    VkFormat                 sc_format;
    VkExtent2D               sc_extent;
    VkImage                  sc_images[ERGO_VK_MAX_SWAPCHAIN];
    VkImageView              sc_views[ERGO_VK_MAX_SWAPCHAIN];
    VkFramebuffer            sc_fbs[ERGO_VK_MAX_SWAPCHAIN];
    uint32_t                 sc_count;

    /* Depth buffer */
    VkImage                  depth_image;
    VkDeviceMemory           depth_memory;
    VkImageView              depth_view;

    /* Render pass + grid mesh pipeline */
    VkRenderPass             render_pass;
    VkPipeline               gfx_pipeline;
    VkPipelineLayout         gfx_layout;
    VkDescriptorSetLayout    gfx_ds_layout;
    VkDescriptorPool         gfx_ds_pool;
    VkDescriptorSet          gfx_ds;
    VkShaderModule           vert_shader;
    VkShaderModule           frag_shader;

    /* Point cloud pipeline (reads from packed vec4 buffer) */
    VkPipeline               pts_pipeline;
    VkPipelineLayout         pts_layout;
    VkDescriptorSetLayout    pts_ds_layout;
    VkDescriptorPool         pts_ds_pool;
    VkDescriptorSet          pts_ds;
    VkShaderModule           pts_vert_shader;
    VkShaderModule           pts_frag_shader;

    /* Gaussian splat pipeline */
    VkPipeline               gauss_pipeline;
    VkPipelineLayout         gauss_layout;
    VkDescriptorSetLayout    gauss_ds_layout;
    VkDescriptorPool         gauss_ds_pool;
    VkDescriptorSet          gauss_ds;
    VkShaderModule           gauss_vert_shader;
    VkShaderModule           gauss_frag_shader;
    VkImage                  gauss_lut_image;
    VkDeviceMemory           gauss_lut_memory;
    VkImageView              gauss_lut_view;
    VkSampler                gauss_lut_sampler;
    int                      gauss_ds_bound;

    /* Grid gaussian pipeline (O(cells) render from grid moments) */
    VkPipeline               grid_gauss_pipeline;
    VkPipelineLayout         grid_gauss_layout;
    VkDescriptorSetLayout    grid_gauss_ds_layout;
    VkDescriptorPool         grid_gauss_ds_pool;
    VkDescriptorSet          grid_gauss_ds;
    VkShaderModule           grid_gauss_vert_shader;
    int                      grid_gauss_ds_bound;

    /* Meshlet shell pipeline */
    VkPipeline               meshlet_pipeline;
    VkPipelineLayout         meshlet_layout;
    VkDescriptorSetLayout    meshlet_ds_layout;
    VkDescriptorPool         meshlet_ds_pool;
    VkDescriptorSet          meshlet_ds;
    VkShaderModule           meshlet_vert_shader;
    VkShaderModule           meshlet_frag_shader;
    int                      meshlet_ds_bound;

    /* Per-cell octahedral atlas (2048x4096, 128x256 tiles of 16x16) */
    VkImage                  atlas_image;
    VkDeviceMemory           atlas_memory;
    VkImageView              atlas_view;      /* sampled by shell frag shader */
    VkImageView              atlas_storage_view; /* storage image for compute write */
    VkSampler                atlas_sampler;
    int                      atlas_initialized;

    VkCommandBuffer          render_cmd_buf;
    VkSemaphore              sem_available;
    VkSemaphore              sem_finished;
    VkFence                  render_fence;

    /* Render UBO (shared by meshlet + persistent paths) */
    VkBuffer                 render_ubo;
    VkDeviceMemory           render_ubo_mem;
    void                    *render_ubo_mapped;

    /* Orbit camera state */
    float                    cam_azimuth;   /* radians, horizontal angle */
    float                    cam_elevation; /* radians, vertical angle   */
    float                    cam_distance;  /* distance from origin      */
    double                   mouse_last_x;
    double                   mouse_last_y;
    int                      mouse_dragging;
    /* Auto-orbit (2026-09-04): slow camera spin so point-tracer clouds
       read as 3D without mouse input. rad/s; ERGO_ORBIT=deg/s overrides,
       ERGO_ORBIT=0 disables. Suspended 4 s after any mouse interaction. */
    float                    cam_spin_rate;
    double                   cam_idle_until;
    double                   cam_last_tick;
#endif

    int                      headless;
    int                      initialized;
} g;

/* ── Helpers ─────────────────────────────────────────────── */

#ifdef ERGO_VK_ANDROID
#include <android/log.h>
#define VK_CHECK(call) do {                                     \
    VkResult _r = (call);                                       \
    if (_r != VK_SUCCESS) {                                     \
        __android_log_print(ANDROID_LOG_ERROR, "ergo_vk",       \
            "%s failed (%d) at %s:%d",                          \
            #call, (int)_r, __FILE__, __LINE__);                \
    }                                                           \
} while (0)
#else
#define VK_CHECK(call) do {                                     \
    VkResult _r = (call);                                       \
    if (_r != VK_SUCCESS) {                                     \
        fprintf(stderr, "ergo_vk: %s failed (%d) at %s:%d\n",  \
                #call, (int)_r, __FILE__, __LINE__);            \
        exit(1);                                                \
    }                                                           \
} while (0)
#endif

static uint32_t find_memory_type(uint32_t type_bits, VkMemoryPropertyFlags props) {
    for (uint32_t i = 0; i < g.mem_props.memoryTypeCount; i++) {
        if ((type_bits & (1u << i)) &&
            (g.mem_props.memoryTypes[i].propertyFlags & props) == props) {
            return i;
        }
    }
    fprintf(stderr, "ergo_vk: no suitable memory type found\n");
    exit(1);
}

/* Variant with a caller-supplied fallback instead of aborting (Inc-2B
 * staging HOST_CACHED preference). */
static uint32_t find_memory_type_or(uint32_t type_bits,
                                    VkMemoryPropertyFlags props,
                                    uint32_t fallback) {
    for (uint32_t i = 0; i < g.mem_props.memoryTypeCount; i++) {
        if ((type_bits & (1u << i)) &&
            (g.mem_props.memoryTypes[i].propertyFlags & props) == props) {
            return i;
        }
    }
    return fallback;
}

/* Counters (env-gated reporting via ERGO_PROFILE): compute launches and
 * queue submit+wait cycles (drains, sync dispatches, transfers). */
static unsigned long g_launch_count = 0;
static unsigned long g_submit_count = 0;
static unsigned long g_drain_count = 0;

static void submit_and_wait(void) {
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.cmd_buf;

    VK_CHECK(vkResetFences(g.device, 1, &g.fence));
    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.fence));
    VK_CHECK(vkWaitForFences(g.device, 1, &g.fence, VK_TRUE, UINT64_MAX));
    g_submit_count++;
}

/* Transfer submit — uses xfer_cmd_buf + xfer_fence.
 * Safe to call while cmd_buf is recording (mid-frame). */
static int g_frame_waited = 0;  /* 1 = fence already waited since last frame_end */
int pts_ds_bound = 0;           /* 1 = render descriptor set bound; reset on sort swap */

static void xfer_submit_and_wait(void) {
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.xfer_cmd_buf;

    VK_CHECK(vkResetFences(g.device, 1, &g.xfer_fence));
    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.xfer_fence));
    VK_CHECK(vkWaitForFences(g.device, 1, &g.xfer_fence, VK_TRUE, UINT64_MAX));
    g_submit_count++;
}

/* ── Forward declarations for render init ────────────────── */
#ifndef ERGO_VK_HEADLESS_ONLY
static void render_create_swapchain(void);
static void render_create_pipeline(void);
static void render_create_points_pipeline(void);
static void render_create_gauss_pipeline(void);
static void render_create_grid_gauss_pipeline(void);
static void render_create_meshlet_pipeline(void);
static void render_cleanup_swapchain(void);
static void camera_mouse_button_cb(GLFWwindow *w, int button, int action, int mods);
static void camera_cursor_pos_cb(GLFWwindow *w, double xpos, double ypos);
static void camera_scroll_cb(GLFWwindow *w, double xoff, double yoff);
static void camera_key_cb(GLFWwindow *w, int key, int scancode, int action, int mods);
#endif

/* ── ergo_vk_init ────────────────────────────────────────── */

int ergo_vk_init(int headless) {
    if (g.initialized) return 0;

#ifdef ERGO_VK_ANDROID
    /* Check if JNI requested CPU-only mode (Adreno driver workaround) */
    extern int ergo_skip_vulkan __attribute__((weak));
    if (&ergo_skip_vulkan && ergo_skip_vulkan) {
        __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
            "Vulkan SKIPPED (ergo_skip_vulkan=1, CPU-only mode)");
        g.initialized = 1;
        g.headless = 1;
        return 0;
    }
    __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
        "ergo_vk_init(headless=%d) starting", headless);
#endif

    memset(&g, 0, sizeof(g));
    g.headless = headless;
#if defined(ERGO_VK_ANDROID) || !defined(ERGO_VK_HEADLESS_ONLY)
    { const char *_oe = getenv("ERGO_ORBIT");
      g.cam_spin_rate = (_oe ? atof(_oe) : 8.0) * 0.0174532925f;
      g.cam_idle_until = 0.0;
      g.cam_last_tick = 0.0; }  /* lazily set on first tick */
#endif

#ifdef ERGO_VK_ANDROID
    if (!headless && g.android_window) {
        g.cam_azimuth   = 0.5f;
        g.cam_elevation = 0.6f;
        g.cam_distance  = 1.5f;
    }
#elif !defined(ERGO_VK_HEADLESS_ONLY)
    if (!headless) {
        if (!glfwInit()) {
            fprintf(stderr, "ergo_vk: glfwInit failed\n");
            return 1;
        }
        glfwWindowHint(GLFW_CLIENT_API, GLFW_NO_API);
        glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);
        g.window = glfwCreateWindow(1280, 720, "Ergo", NULL, NULL);
        if (!g.window) {
            fprintf(stderr, "ergo_vk: window creation failed\n");
            glfwTerminate();
            return 1;
        }

        /* Default orbit camera */
        g.cam_azimuth   = 0.5f;   /* slight angle */
        g.cam_elevation = 0.6f;   /* looking down */
        g.cam_distance  = 1.5f;
        { const char *_ce = getenv("ERGO_CAM");
          if (_ce) sscanf(_ce, "%f,%f,%f", &g.cam_azimuth,
                          &g.cam_elevation, &g.cam_distance); }

        glfwSetMouseButtonCallback(g.window, camera_mouse_button_cb);
        glfwSetCursorPosCallback(g.window, camera_cursor_pos_cb);
        glfwSetScrollCallback(g.window, camera_scroll_cb);
        glfwSetKeyCallback(g.window, camera_key_cb);
    }
#endif

    /* --- Instance --- */
#ifdef ERGO_VK_ANDROID
    __android_log_print(ANDROID_LOG_INFO, "ergo_vk", "creating instance...");
#endif
    VkApplicationInfo app_info = {0};
    app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app_info.pApplicationName = "Ergo";
    app_info.apiVersion = VK_API_VERSION_1_1;

    /* Collect required extensions */
    const char *exts[16];
    uint32_t ext_count = 0;

#ifdef ERGO_VK_ANDROID
    if (!headless) {
        exts[ext_count++] = VK_KHR_SURFACE_EXTENSION_NAME;
        exts[ext_count++] = VK_KHR_ANDROID_SURFACE_EXTENSION_NAME;
    }
#elif !defined(ERGO_VK_HEADLESS_ONLY)
    if (!headless) {
        uint32_t glfw_ext_count = 0;
        const char **glfw_exts = glfwGetRequiredInstanceExtensions(&glfw_ext_count);
        for (uint32_t i = 0; i < glfw_ext_count && ext_count < 16; i++)
            exts[ext_count++] = glfw_exts[i];
    }
#endif

    VkInstanceCreateInfo inst_ci = {0};
    inst_ci.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    inst_ci.pApplicationInfo = &app_info;
    inst_ci.enabledExtensionCount = ext_count;
    inst_ci.ppEnabledExtensionNames = exts;

    VK_CHECK(vkCreateInstance(&inst_ci, NULL, &g.instance));
#ifdef ERGO_VK_ANDROID
    __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
        "instance created: %p", (void*)g.instance);
#endif

#ifdef ERGO_VK_ANDROID
    /* --- Surface (Android render mode) --- */
    if (!headless && g.android_window) {
        VkAndroidSurfaceCreateInfoKHR sci = {0};
        sci.sType = VK_STRUCTURE_TYPE_ANDROID_SURFACE_CREATE_INFO_KHR;
        sci.window = g.android_window;
        VK_CHECK(vkCreateAndroidSurfaceKHR(g.instance, &sci, NULL,
                                            &g.surface));
    }
#elif !defined(ERGO_VK_HEADLESS_ONLY)
    /* --- Surface (render mode) --- */
    if (!headless) {
        VK_CHECK(glfwCreateWindowSurface(g.instance, g.window, NULL,
                                          &g.surface));
    }
#endif

    /* --- Physical device selection --- */
    uint32_t dev_count = 0;
    VK_CHECK(vkEnumeratePhysicalDevices(g.instance, &dev_count, NULL));
    if (dev_count == 0) {
        fprintf(stderr, "ergo_vk: no Vulkan-capable GPU found\n");
        return 1;
    }

    VkPhysicalDevice *devs = malloc(dev_count * sizeof(VkPhysicalDevice));
    VK_CHECK(vkEnumeratePhysicalDevices(g.instance, &dev_count, devs));
#ifdef ERGO_VK_ANDROID
    __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
        "found %u physical devices", dev_count);
#endif

    int found = 0;
    for (uint32_t d = 0; d < dev_count; d++) {
#ifdef ERGO_VK_ANDROID
        __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
            "checking device %u: %p", d, (void*)devs[d]);
#endif
        VkPhysicalDeviceFeatures feats;
        vkGetPhysicalDeviceFeatures(devs[d], &feats);
#ifdef ERGO_VK_ANDROID
        __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
            "features: f64=%d i64=%d large=%d",
            feats.shaderFloat64, feats.shaderInt64, feats.largePoints);
#endif
#ifndef ERGO_F32_MODE
        if (!feats.shaderFloat64) continue;
#endif
        /* In f32 mode, SPIRV only requires OpCapability Shader —
         * no Int64 or Float64 needed. Device is usable. */

        /* Query queue families. Some Adreno drivers crash on the
         * count-only call (NULL properties). Use a fixed-size buffer
         * to avoid the two-call pattern. */
        uint32_t qf_count = 8;  /* max we'll check */
        VkQueueFamilyProperties qf_buf[8];
        memset(qf_buf, 0, sizeof(qf_buf));
#ifdef ERGO_VK_ANDROID
        __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
            "querying queue families (max=%u)...", qf_count);
#endif
        vkGetPhysicalDeviceQueueFamilyProperties(devs[d], &qf_count, qf_buf);
#ifdef ERGO_VK_ANDROID
        __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
            "queue families: %u (flags[0]=0x%x)",
            qf_count, qf_count > 0 ? qf_buf[0].queueFlags : 0);
#endif
        VkQueueFamilyProperties *qf_props = qf_buf;

        for (uint32_t q = 0; q < qf_count; q++) {
            int ok = (qf_props[q].queueFlags & VK_QUEUE_COMPUTE_BIT) != 0;

#ifndef ERGO_VK_HEADLESS_ONLY
            /* In render mode, also require graphics + present support */
            if (!headless) {
                ok = ok && (qf_props[q].queueFlags & VK_QUEUE_GRAPHICS_BIT);
                VkBool32 present = VK_FALSE;
                vkGetPhysicalDeviceSurfaceSupportKHR(devs[d], q,
                                                      g.surface, &present);
                ok = ok && present;
            }
#endif

            if (ok) {
                g.phys_device = devs[d];
                g.queue_family = q;
                found = 1;
                break;
            }
        }
        /* qf_props is stack-allocated, no free needed */
        if (found) break;
    }
    free(devs);

    if (!found) {
        fprintf(stderr, "ergo_vk: no GPU with required capabilities found\n");
#ifdef ERGO_VK_ANDROID
        __android_log_print(ANDROID_LOG_ERROR, "ergo_vk",
            "no GPU with required capabilities — falling back to CPU");
#endif
        return 1;
    }

    VkPhysicalDeviceProperties dev_props;
    vkGetPhysicalDeviceProperties(g.phys_device, &dev_props);
    fprintf(stderr, "[ergo_vk] Device: %s\n", dev_props.deviceName);
#ifdef ERGO_VK_ANDROID
    __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
        "device: %s maxPushConstants=%u maxWorkgroup=[%u,%u,%u] maxComputeSharedMem=%u",
        dev_props.deviceName,
        dev_props.limits.maxPushConstantsSize,
        dev_props.limits.maxComputeWorkGroupSize[0],
        dev_props.limits.maxComputeWorkGroupSize[1],
        dev_props.limits.maxComputeWorkGroupSize[2],
        dev_props.limits.maxComputeSharedMemorySize);
#endif

    /* --- Logical device + queue --- */
    float queue_priority = 1.0f;
    VkDeviceQueueCreateInfo queue_ci = {0};
    queue_ci.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    queue_ci.queueFamilyIndex = g.queue_family;
    queue_ci.queueCount = 1;
    queue_ci.pQueuePriorities = &queue_priority;

    /* Query supported features and only enable what the device has */
    VkPhysicalDeviceFeatures supported_feats;
    vkGetPhysicalDeviceFeatures(g.phys_device, &supported_feats);

    VkPhysicalDeviceFeatures enabled_feats = {0};
#ifndef ERGO_F32_MODE
    enabled_feats.shaderFloat64 = supported_feats.shaderFloat64;
#endif
    enabled_feats.shaderInt64 = supported_feats.shaderInt64;
    enabled_feats.largePoints = supported_feats.largePoints;

    /* Device extensions */
    const char *dev_exts[8];
    uint32_t dev_ext_count = 0;
#ifndef ERGO_VK_HEADLESS_ONLY
    if (!headless) {
        dev_exts[dev_ext_count++] = VK_KHR_SWAPCHAIN_EXTENSION_NAME;
    }
#endif
    /* Atomic float for scatter kernels (density accumulation).
     * Skip on Android — many mobile drivers don't support it and some
     * (Adreno) crash during extension enumeration. The SPIRV shader
     * will fail to load if it requires OpAtomicFAdd without support. */
    int has_atomic_float = 0;
#ifndef ERGO_VK_ANDROID
    {
        uint32_t ext_count_dev = 0;
        vkEnumerateDeviceExtensionProperties(g.phys_device, NULL,
                                              &ext_count_dev, NULL);
        if (ext_count_dev > 0 && ext_count_dev < 512) {
            VkExtensionProperties *props = malloc(
                ext_count_dev * sizeof(VkExtensionProperties));
            vkEnumerateDeviceExtensionProperties(g.phys_device, NULL,
                                                  &ext_count_dev, props);
            for (uint32_t i = 0; i < ext_count_dev; i++) {
                if (strcmp(props[i].extensionName,
                           "VK_EXT_shader_atomic_float") == 0) {
                    has_atomic_float = 1;
                    break;
                }
            }
            free(props);
        }
    }
#endif

    VkPhysicalDeviceShaderAtomicFloatFeaturesEXT atomic_float_feats = {0};
    atomic_float_feats.sType =
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_ATOMIC_FLOAT_FEATURES_EXT;
    if (has_atomic_float) {
        dev_exts[dev_ext_count++] = "VK_EXT_shader_atomic_float";
#ifdef ERGO_F32_MODE
        atomic_float_feats.shaderBufferFloat32Atomics = VK_TRUE;
        atomic_float_feats.shaderBufferFloat32AtomicAdd = VK_TRUE;
#else
        atomic_float_feats.shaderBufferFloat64Atomics = VK_TRUE;
        atomic_float_feats.shaderBufferFloat64AtomicAdd = VK_TRUE;
#endif
        fprintf(stderr, "[ergo_vk] VK_EXT_shader_atomic_float: supported\n");
    } else {
        fprintf(stderr, "[ergo_vk] VK_EXT_shader_atomic_float: NOT supported "
                "(scatter may fail)\n");
    }

    VkDeviceCreateInfo dev_ci = {0};
    dev_ci.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    dev_ci.pNext = has_atomic_float ? &atomic_float_feats : NULL;
    dev_ci.queueCreateInfoCount = 1;
    dev_ci.pQueueCreateInfos = &queue_ci;
    dev_ci.pEnabledFeatures = &enabled_feats;
    dev_ci.enabledExtensionCount = dev_ext_count;
    dev_ci.ppEnabledExtensionNames = dev_exts;

    VK_CHECK(vkCreateDevice(g.phys_device, &dev_ci, NULL, &g.device));
#ifdef ERGO_VK_ANDROID
    __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
        "vkCreateDevice: device=%p", (void*)g.device);
#endif
    if (!g.device) {
        fprintf(stderr, "[ergo_vk] FATAL: device creation failed\n");
#ifdef ERGO_VK_ANDROID
        __android_log_print(ANDROID_LOG_ERROR, "ergo_vk",
            "FATAL: device creation failed (null handle)");
#endif
        return -1;
    }
    vkGetDeviceQueue(g.device, g.queue_family, 0, &g.compute_queue);

    vkGetPhysicalDeviceMemoryProperties(g.phys_device, &g.mem_props);
#ifdef ERGO_VK_ANDROID
    __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
        "mem_props: %u types, device_local=%zu bytes",
        g.mem_props.memoryTypeCount,
        (size_t)ergo_vk_device_local_bytes());
#endif

    /* --- Command pool + buffer --- */
    VkCommandPoolCreateInfo pool_ci = {0};
    pool_ci.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    pool_ci.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    pool_ci.queueFamilyIndex = g.queue_family;
    VK_CHECK(vkCreateCommandPool(g.device, &pool_ci, NULL, &g.cmd_pool));

    VkCommandBufferAllocateInfo alloc_info = {0};
    alloc_info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    alloc_info.commandPool = g.cmd_pool;
    alloc_info.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    alloc_info.commandBufferCount = 2;
    VK_CHECK(vkAllocateCommandBuffers(g.device, &alloc_info, g.cmd_bufs));
    g.cmd_idx = 0;
    g.cmd_buf = g.cmd_bufs[0];

    /* --- Transfer command buffer (for mid-frame downloads) --- */
    alloc_info.commandBufferCount = 1;
    VK_CHECK(vkAllocateCommandBuffers(g.device, &alloc_info, &g.xfer_cmd_buf));

    /* --- Sort command buffer (separate from frame double-buffer) --- */
    VK_CHECK(vkAllocateCommandBuffers(g.device, &alloc_info, &g.sort_cmd_buf));

    /* --- Fences (signaled so first frame_begin proceeds without wait) --- */
    VkFenceCreateInfo fence_ci = {0};
    fence_ci.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    fence_ci.flags = VK_FENCE_CREATE_SIGNALED_BIT;
    VK_CHECK(vkCreateFence(g.device, &fence_ci, NULL, &g.fences[0]));
    VK_CHECK(vkCreateFence(g.device, &fence_ci, NULL, &g.fences[1]));
    g.fence = g.fences[0];
    VK_CHECK(vkCreateFence(g.device, &fence_ci, NULL, &g.xfer_fence));

    /* --- GPU timestamp query pool (profiling) --- */
    {
        VkPhysicalDeviceProperties dev_props;
        vkGetPhysicalDeviceProperties(g.phys_device, &dev_props);
        g.ts_period = dev_props.limits.timestampPeriod; /* ns per tick */
        VkQueryPoolCreateInfo qp_ci = {0};
        qp_ci.sType = VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO;
        qp_ci.queryType = VK_QUERY_TYPE_TIMESTAMP;
        qp_ci.queryCount = 32;  /* up to 16 intervals (pairs) */
        VK_CHECK(vkCreateQueryPool(g.device, &qp_ci, NULL, &g.ts_pool));
        g.ts_active = (getenv("ERGO_PROFILE") != NULL);
        g.ts_idx = 0;
        g.ts_count = 0;
        memset(g.ts_accum, 0, sizeof(g.ts_accum));
    }

#ifndef ERGO_VK_HEADLESS_ONLY
    /* --- Render mode setup --- */
    if (!headless) {
        render_create_swapchain();
        render_create_pipeline();
        render_create_points_pipeline();
        render_create_gauss_pipeline();
        render_create_grid_gauss_pipeline();
        render_create_meshlet_pipeline();

        /* Separate command buffer for rendering */
        VkCommandBufferAllocateInfo rcb_ai = {0};
        rcb_ai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
        rcb_ai.commandPool = g.cmd_pool;
        rcb_ai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
        rcb_ai.commandBufferCount = 1;
        VK_CHECK(vkAllocateCommandBuffers(g.device, &rcb_ai, &g.render_cmd_buf));

        /* Sync objects for rendering */
        VkSemaphoreCreateInfo sem_ci = {0};
        sem_ci.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
        VK_CHECK(vkCreateSemaphore(g.device, &sem_ci, NULL, &g.sem_available));
        VK_CHECK(vkCreateSemaphore(g.device, &sem_ci, NULL, &g.sem_finished));

        VkFenceCreateInfo rf_ci = {0};
        rf_ci.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
        rf_ci.flags = VK_FENCE_CREATE_SIGNALED_BIT;
        VK_CHECK(vkCreateFence(g.device, &rf_ci, NULL, &g.render_fence));
    }
#endif

    g.initialized = 1;
#ifdef ERGO_VK_ANDROID
    __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
        "init complete: device=%p queue=%u",
        (void*)g.device, g.queue_family);
#endif
    return 0;
}

#ifdef ERGO_VK_ANDROID
int ergo_vk_init_android(void *native_window) {
#if !defined(ERGO_VK_HEADLESS_ONLY)
    g.android_window = (ANativeWindow*)native_window;
#endif
    return ergo_vk_init(native_window ? 0 : 1);
}
#endif

/* ── ergo_vk_shutdown ────────────────────────────────────── */

void ergo_vk_profile_report(void) {
    if (!g.ts_active) return;
    fprintf(stderr, "[ergo_vk] total compute launches: %lu\n",
            g_launch_count);
    fprintf(stderr, "[ergo_vk] total queue submit+wait cycles: %lu\n",
            g_submit_count);
    fprintf(stderr, "[ergo_vk] total frame drains (frame_end submits): %lu\n",
            g_drain_count);
    if (g.ts_count == 0) return;
    fprintf(stderr, "\n[ergo_vk] GPU profile (%d frames, avg per frame):\n",
            g.ts_count);
    const char *names[] = {"k0", "k1", "k2", "k3", "k4", "k5", "k6", "k7",
                           "k8", "k9", "k10", "k11", "k12", "k13", "k14", "k15"};
    double total = 0;
    for (int i = 0; i < 16 && g.ts_accum[i] > 0; i++) {
        double avg = g.ts_accum[i] / g.ts_count;
        fprintf(stderr, "  %-10s %7.3f ms\n", names[i], avg);
        total += avg;
    }
    fprintf(stderr, "  %-10s %7.3f ms  (%.1f fps)\n", "TOTAL", total,
            1000.0 / total);
}

void ergo_vk_shutdown(void) {
    if (!g.initialized) return;
    if (!g.device) { g.initialized = 0; return; }  /* CPU-only mode */
    vkDeviceWaitIdle(g.device);
    ergo_vk_profile_report();

#ifndef ERGO_VK_HEADLESS_ONLY
    if (!g.headless) {
        vkDestroySemaphore(g.device, g.sem_available, NULL);
        vkDestroySemaphore(g.device, g.sem_finished, NULL);
        vkDestroyFence(g.device, g.render_fence, NULL);

        vkDestroyPipeline(g.device, g.gfx_pipeline, NULL);
        vkDestroyPipelineLayout(g.device, g.gfx_layout, NULL);
        vkDestroyDescriptorSetLayout(g.device, g.gfx_ds_layout, NULL);
        vkDestroyDescriptorPool(g.device, g.gfx_ds_pool, NULL);
        vkDestroyShaderModule(g.device, g.vert_shader, NULL);
        vkDestroyShaderModule(g.device, g.frag_shader, NULL);

        vkDestroyPipeline(g.device, g.pts_pipeline, NULL);
        vkDestroyPipelineLayout(g.device, g.pts_layout, NULL);
        vkDestroyDescriptorSetLayout(g.device, g.pts_ds_layout, NULL);
        vkDestroyDescriptorPool(g.device, g.pts_ds_pool, NULL);
        vkDestroyShaderModule(g.device, g.pts_vert_shader, NULL);
        vkDestroyShaderModule(g.device, g.pts_frag_shader, NULL);

        if (g.gauss_pipeline) {
            vkDestroyPipeline(g.device, g.gauss_pipeline, NULL);
            vkDestroyPipelineLayout(g.device, g.gauss_layout, NULL);
            vkDestroyDescriptorSetLayout(g.device, g.gauss_ds_layout, NULL);
            vkDestroyDescriptorPool(g.device, g.gauss_ds_pool, NULL);
            vkDestroyShaderModule(g.device, g.gauss_vert_shader, NULL);
            vkDestroyShaderModule(g.device, g.gauss_frag_shader, NULL);
            vkDestroySampler(g.device, g.gauss_lut_sampler, NULL);
            vkDestroyImageView(g.device, g.gauss_lut_view, NULL);
            vkDestroyImage(g.device, g.gauss_lut_image, NULL);
            vkFreeMemory(g.device, g.gauss_lut_memory, NULL);
        }

        if (g.grid_gauss_pipeline) {
            vkDestroyPipeline(g.device, g.grid_gauss_pipeline, NULL);
            vkDestroyPipelineLayout(g.device, g.grid_gauss_layout, NULL);
            vkDestroyDescriptorSetLayout(g.device, g.grid_gauss_ds_layout, NULL);
            vkDestroyDescriptorPool(g.device, g.grid_gauss_ds_pool, NULL);
            vkDestroyShaderModule(g.device, g.grid_gauss_vert_shader, NULL);
        }

        if (g.meshlet_pipeline) {
            vkDestroyPipeline(g.device, g.meshlet_pipeline, NULL);
            vkDestroyPipelineLayout(g.device, g.meshlet_layout, NULL);
            vkDestroyDescriptorSetLayout(g.device, g.meshlet_ds_layout, NULL);
            vkDestroyDescriptorPool(g.device, g.meshlet_ds_pool, NULL);
            vkDestroyShaderModule(g.device, g.meshlet_vert_shader, NULL);
            vkDestroyShaderModule(g.device, g.meshlet_frag_shader, NULL);
        }
        if (g.render_ubo) {
            vkDestroyBuffer(g.device, g.render_ubo, NULL);
            vkFreeMemory(g.device, g.render_ubo_mem, NULL);
        }

        render_cleanup_swapchain();

        vkDestroySurfaceKHR(g.instance, g.surface, NULL);
        glfwDestroyWindow(g.window);
        glfwTerminate();
    }
#endif

    for (int i = 0; i < ERGO_VK_MAX_PIPELINES; i++) {
        PipeSlot *p = &g.pipes[i];
        if (!p->in_use) continue;
        vkDestroyPipeline(g.device, p->pipeline, NULL);
        vkDestroyPipelineLayout(g.device, p->layout, NULL);
        vkDestroyDescriptorSetLayout(g.device, p->ds_layout, NULL);
        vkDestroyDescriptorPool(g.device, p->ds_pool, NULL);
        vkDestroyShaderModule(g.device, p->shader, NULL);
    }

    for (int i = 0; i < ERGO_VK_MAX_BUFFERS; i++) {
        BufSlot *b = &g.bufs[i];
        if (!b->in_use) continue;
        vkDestroyBuffer(g.device, b->buffer, NULL);
        vkFreeMemory(g.device, b->memory, NULL);
    }

    vkDestroyFence(g.device, g.fence, NULL);
    vkDestroyFence(g.device, g.xfer_fence, NULL);
    vkDestroyCommandPool(g.device, g.cmd_pool, NULL);
    vkDestroyDevice(g.device, NULL);
    vkDestroyInstance(g.instance, NULL);

    memset(&g, 0, sizeof(g));
}

size_t ergo_vk_device_local_bytes(void) {
    if (!g.device) return 0;
    size_t best = 0;
    for (uint32_t i = 0; i < g.mem_props.memoryTypeCount; i++) {
        if (g.mem_props.memoryTypes[i].propertyFlags &
            VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT) {
            uint32_t heap = g.mem_props.memoryTypes[i].heapIndex;
            size_t sz = (size_t)g.mem_props.memoryHeaps[heap].size;
            if (sz > best) best = sz;
        }
    }
    return best;
}

/* ── Staging buffer ─────────────────────────────────────── */

static void ensure_staging(size_t need) {
    if (need <= g.staging_size) return;

    /* Round up to 16 MB granularity to avoid frequent realloc */
    size_t alloc = (need + (16u << 20) - 1) & ~((16u << 20) - 1);

    if (g.staging_buf) {
        vkUnmapMemory(g.device, g.staging_mem);
        vkDestroyBuffer(g.device, g.staging_buf, NULL);
        vkFreeMemory(g.device, g.staging_mem, NULL);
    }

    VkBufferCreateInfo ci = {0};
    ci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    ci.size = alloc;
    ci.usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT
             | VK_BUFFER_USAGE_TRANSFER_DST_BIT;
    ci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    VK_CHECK(vkCreateBuffer(g.device, &ci, NULL, &g.staging_buf));

    VkMemoryRequirements req;
    vkGetBufferMemoryRequirements(g.device, g.staging_buf, &req);

    VkMemoryAllocateInfo ai = {0};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = req.size;
    /* Inc-2B: prefer HOST_CACHED for the staging buffer when the driver
     * offers it — plain memcpy into write-combined host-visible memory
     * measures ~0.6 GB/s (the ED N=19 streamer was memcpy-bound);
     * cached staging runs at normal memory bandwidth. Fall back to the
     * plain VISIBLE|COHERENT type when no cached type matches. */
    ai.memoryTypeIndex = find_memory_type_or(req.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
        VK_MEMORY_PROPERTY_HOST_COHERENT_BIT |
        VK_MEMORY_PROPERTY_HOST_CACHED_BIT, -1);
    if (ai.memoryTypeIndex == (uint32_t)-1) {
        ai.memoryTypeIndex = find_memory_type(req.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
            VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        fprintf(stderr, "[ergo_vk] staging: HOST_CACHED unavailable "
                "(WC fallback — expect ~0.6 GB/s transfers)\n");
    } else {
        fprintf(stderr, "[ergo_vk] staging: HOST_CACHED\n");
    }
    VK_CHECK(vkAllocateMemory(g.device, &ai, NULL, &g.staging_mem));
    VK_CHECK(vkBindBufferMemory(g.device, g.staging_buf, g.staging_mem, 0));
    VK_CHECK(vkMapMemory(g.device, g.staging_mem, 0, alloc, 0,
                          &g.staging_mapped));
    g.staging_size = alloc;
}

/* ── Buffer management ─────────────────────────────────── */

ErgoVkBuf ergo_vk_create_buffer(size_t size) {
    if (!g.device) return 0;  /* CPU-only mode: no GPU buffers */
    if (size == 0) size = 4;  /* guard: 0-byte buffers crash Vulkan drivers */
    /* Inc-2B: enforce the descriptor-range limit up front. A buffer
     * larger than maxStorageBufferRange would fail at bind time (or
     * worse, silently on some drivers) — fail loudly at creation. */
    {
        static size_t max_range = 0;
        if (!max_range) {
            VkPhysicalDeviceProperties props;
            vkGetPhysicalDeviceProperties(g.phys_device, &props);
            max_range = (size_t)props.limits.maxStorageBufferRange;
            fprintf(stderr, "[ergo_vk] maxStorageBufferRange: %.2f GB\n",
                    (double)max_range / 1e9);
        }
        if (size > max_range) {
            fprintf(stderr,
                    "ergo_vk: buffer of %.2f GB exceeds "
                    "maxStorageBufferRange (%.2f GB) — use the "
                    "gather-window streaming path (Inc-2B)\n",
                    (double)size / 1e9, (double)max_range / 1e9);
            exit(1);
        }
    }
    int slot = -1;
    for (int i = 0; i < ERGO_VK_MAX_BUFFERS; i++) {
        if (!g.bufs[i].in_use) { slot = i; break; }
    }
    if (slot < 0) {
        fprintf(stderr, "ergo_vk: buffer limit reached (%d)\n",
                ERGO_VK_MAX_BUFFERS);
        exit(1);
    }

    BufSlot *b = &g.bufs[slot];

    VkBufferCreateInfo buf_ci = {0};
    buf_ci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    buf_ci.size = size;
    buf_ci.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT
                 | VK_BUFFER_USAGE_TRANSFER_DST_BIT
                 | VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
    buf_ci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;

#ifdef ERGO_BENCH_VK_ALLOC
    if (!_ergo_bench_atexit_registered) {
        atexit(_ergo_bench_report);
        _ergo_bench_atexit_registered = 1;
    }
    double _bench_t0 = _ergo_bench_now_ns();
#endif
    VK_CHECK(vkCreateBuffer(g.device, &buf_ci, NULL, &b->buffer));
#ifdef ERGO_BENCH_VK_ALLOC
    double _bench_t1 = _ergo_bench_now_ns();
#endif

    VkMemoryRequirements mem_req;
    vkGetBufferMemoryRequirements(g.device, b->buffer, &mem_req);

    VkMemoryAllocateInfo mem_ai = {0};
    mem_ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    mem_ai.allocationSize = mem_req.size;
#ifdef ERGO_BENCH_VK_ALLOC
    /* Allow bench to select HOST_VISIBLE via ERGO_BENCH_HOST_VISIBLE=1
     * for the Pass 3 DEVICE_LOCAL vs HOST_VISIBLE diagnostic. Print
     * the selected memory type index on first call so we can verify
     * the test actually picked the different type. */
    static int _bench_mem_type_logged = 0;
    if (getenv("ERGO_BENCH_HOST_VISIBLE")) {
        mem_ai.memoryTypeIndex = find_memory_type(
            mem_req.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
            VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    } else {
        mem_ai.memoryTypeIndex = find_memory_type(
            mem_req.memoryTypeBits,
            VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    }
    if (!_bench_mem_type_logged) {
        fprintf(stderr, "[bench] selected memoryTypeIndex=%u  bits=0x%08x  mode=%s\n",
                mem_ai.memoryTypeIndex, mem_req.memoryTypeBits,
                getenv("ERGO_BENCH_HOST_VISIBLE") ? "HOST_VISIBLE" : "DEVICE_LOCAL");
        _bench_mem_type_logged = 1;
    }
#else
    mem_ai.memoryTypeIndex = find_memory_type(
        mem_req.memoryTypeBits,
        VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
#endif

#ifdef ERGO_BENCH_VK_ALLOC
    double _bench_t2 = _ergo_bench_now_ns();
#endif
    VK_CHECK(vkAllocateMemory(g.device, &mem_ai, NULL, &b->memory));
#ifdef ERGO_BENCH_VK_ALLOC
    double _bench_t3 = _ergo_bench_now_ns();
#endif
    VK_CHECK(vkBindBufferMemory(g.device, b->buffer, b->memory, 0));
#ifdef ERGO_BENCH_VK_ALLOC
    double _bench_t4 = _ergo_bench_now_ns();
    if (_ergo_bench_count < ERGO_BENCH_MAX_CALLS) {
        _ergo_bench_calls[_ergo_bench_count].create_ns = _bench_t1 - _bench_t0;
        _ergo_bench_calls[_ergo_bench_count].alloc_ns  = _bench_t3 - _bench_t2;
        _ergo_bench_calls[_ergo_bench_count].bind_ns   = _bench_t4 - _bench_t3;
        _ergo_bench_calls[_ergo_bench_count].bytes     = size;
        _ergo_bench_count++;
    }
#endif

    b->size = size;
    b->in_use = 1;
    return (ErgoVkBuf)slot;
}

ErgoVkBuf ergo_vk_create_buffer_pair(size_t size) {
    if (!g.device) return 0;
    ErgoVkBuf a = ergo_vk_create_buffer(size);
    ErgoVkBuf b = ergo_vk_create_buffer(size);
    g.bufs[a].pair = b;
    g.bufs[b].pair = a;
    return a;
}

ErgoVkBuf ergo_vk_read_buf(ErgoVkBuf buf) {
    if (!g.device) return 0;
    if (!g.bufs[buf].pair) return buf;
    /* Even frames: read A, write B. Odd frames: read B, write A. */
    return (g.frame_parity == 0) ? buf : g.bufs[buf].pair;
}

ErgoVkBuf ergo_vk_write_buf(ErgoVkBuf buf) {
    if (!g.device) return 0;
    if (!g.bufs[buf].pair) return buf;
    return (g.frame_parity == 0) ? g.bufs[buf].pair : buf;
}

void ergo_vk_upload(ErgoVkBuf buf, const void *data, size_t size) {
    if (!g.device) return;
    BufSlot *b = &g.bufs[buf];
    ensure_staging(size);

    /* CPU → staging (persistently mapped) */
    memcpy(g.staging_mapped, data, size);

    /* staging → device (GPU copy via xfer command buffer) */
    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkResetCommandBuffer(g.xfer_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.xfer_cmd_buf, &begin));

    VkBufferCopy region = { .srcOffset = 0, .dstOffset = 0, .size = size };
    vkCmdCopyBuffer(g.xfer_cmd_buf, g.staging_buf, b->buffer, 1, &region);

    VK_CHECK(vkEndCommandBuffer(g.xfer_cmd_buf));
    xfer_submit_and_wait();
}

void ergo_vk_download(ErgoVkBuf buf, void *data, size_t size) {
    if (!g.device) return;
    BufSlot *b = &g.bufs[buf];
    ensure_staging(size);

    /* device → staging (GPU copy via xfer command buffer) */
    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkResetCommandBuffer(g.xfer_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.xfer_cmd_buf, &begin));

    VkBufferCopy region = { .srcOffset = 0, .dstOffset = 0, .size = size };
    vkCmdCopyBuffer(g.xfer_cmd_buf, b->buffer, g.staging_buf, 1, &region);

    VK_CHECK(vkEndCommandBuffer(g.xfer_cmd_buf));
    xfer_submit_and_wait();

    /* staging → CPU */
    memcpy(data, g.staging_mapped, size);
}

void ergo_vk_download_at(ErgoVkBuf buf, void *data, size_t offset, size_t size) {
    if (!g.device) return;
    BufSlot *b = &g.bufs[buf];
    ensure_staging(size);

    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkResetCommandBuffer(g.xfer_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.xfer_cmd_buf, &begin));

    VkBufferCopy region = { .srcOffset = offset, .dstOffset = 0, .size = size };
    vkCmdCopyBuffer(g.xfer_cmd_buf, b->buffer, g.staging_buf, 1, &region);

    VK_CHECK(vkEndCommandBuffer(g.xfer_cmd_buf));
    xfer_submit_and_wait();

    memcpy(data, g.staging_mapped, size);
}

/* Download N buffers in ONE transfer submission: all copies are recorded
 * into a single xfer command buffer (stacked in staging), submitted and
 * waited once, then scattered to their host destinations. Used by the
 * coalesced reduction read-back to replace N submit+wait cycles with 1. */
void ergo_vk_download_multi(const ErgoVkBuf *bufs, void * const *dsts,
                            const size_t *offsets, const size_t *sizes,
                            int n) {
    if (!g.device || n <= 0) return;
    size_t total = 0;
    for (int i = 0; i < n; i++) total += sizes[i];
    ensure_staging(total);

    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkResetCommandBuffer(g.xfer_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.xfer_cmd_buf, &begin));

    size_t staged = 0;
    for (int i = 0; i < n; i++) {
        BufSlot *b = &g.bufs[bufs[i]];
        VkBufferCopy region = { .srcOffset = offsets[i],
                                .dstOffset = staged, .size = sizes[i] };
        vkCmdCopyBuffer(g.xfer_cmd_buf, b->buffer, g.staging_buf, 1, &region);
        staged += sizes[i];
    }

    VK_CHECK(vkEndCommandBuffer(g.xfer_cmd_buf));
    xfer_submit_and_wait();

    staged = 0;
    for (int i = 0; i < n; i++) {
        memcpy(dsts[i], (const char *)g.staging_mapped + staged, sizes[i]);
        staged += sizes[i];
    }
}

void ergo_vk_upload_at(ErgoVkBuf buf, const void *data, size_t offset, size_t size) {
    if (!g.device) return;
    BufSlot *b = &g.bufs[buf];
    ensure_staging(size);

    memcpy(g.staging_mapped, data, size);

    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkResetCommandBuffer(g.xfer_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.xfer_cmd_buf, &begin));

    VkBufferCopy region = { .srcOffset = 0, .dstOffset = offset, .size = size };
    vkCmdCopyBuffer(g.xfer_cmd_buf, g.staging_buf, b->buffer, 1, &region);

    VK_CHECK(vkEndCommandBuffer(g.xfer_cmd_buf));
    xfer_submit_and_wait();
}

/* ── Compute pipeline (unchanged from Phase B) ──────────── */

ErgoVkPipe ergo_vk_load_shader(const void *spirv, size_t spirv_size,
                                int n_buffers, size_t pc_size) {
    if (!g.device) return 0;
    int slot = -1;
    for (int i = 0; i < ERGO_VK_MAX_PIPELINES; i++) {
        if (!g.pipes[i].in_use) { slot = i; break; }
    }
    if (slot < 0) {
        fprintf(stderr, "ergo_vk: pipeline limit reached (%d)\n",
                ERGO_VK_MAX_PIPELINES);
        exit(1);
    }

    PipeSlot *p = &g.pipes[slot];
    p->n_buffers = n_buffers;
    p->pc_size = pc_size;

    VkShaderModuleCreateInfo sm_ci = {0};
    sm_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    sm_ci.codeSize = spirv_size;
    sm_ci.pCode = (const uint32_t *)spirv;
    VK_CHECK(vkCreateShaderModule(g.device, &sm_ci, NULL, &p->shader));
#ifdef ERGO_VK_ANDROID
    __android_log_print(ANDROID_LOG_INFO, "ergo_vk",
        "shader loaded: %zu bytes, %d bufs, %zu pc → module=%p",
        spirv_size, n_buffers, pc_size, (void*)p->shader);
#endif

    VkDescriptorSetLayoutBinding *bindings = NULL;
    if (n_buffers > 0) {
        bindings = calloc(n_buffers, sizeof(VkDescriptorSetLayoutBinding));
        for (int i = 0; i < n_buffers; i++) {
            bindings[i].binding = i;
            bindings[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            bindings[i].descriptorCount = 1;
            bindings[i].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
        }
    }

    VkDescriptorSetLayoutCreateInfo dsl_ci = {0};
    dsl_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dsl_ci.bindingCount = n_buffers;
    dsl_ci.pBindings = bindings;
    VK_CHECK(vkCreateDescriptorSetLayout(g.device, &dsl_ci, NULL,
                                          &p->ds_layout));
    free(bindings);

    VkDescriptorPoolSize pool_size = {0};
    pool_size.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    pool_size.descriptorCount = (n_buffers > 0) ? n_buffers * 2 : 2;

    VkDescriptorPoolCreateInfo dp_ci = {0};
    dp_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dp_ci.maxSets = 2;  /* one descriptor set per frame slot */
    dp_ci.poolSizeCount = 1;
    dp_ci.pPoolSizes = &pool_size;
    VK_CHECK(vkCreateDescriptorPool(g.device, &dp_ci, NULL, &p->ds_pool));

    VkDescriptorSetLayout layouts[2] = { p->ds_layout, p->ds_layout };
    VkDescriptorSetAllocateInfo ds_ai = {0};
    ds_ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    ds_ai.descriptorPool = p->ds_pool;
    ds_ai.descriptorSetCount = 2;
    ds_ai.pSetLayouts = layouts;
    VK_CHECK(vkAllocateDescriptorSets(g.device, &ds_ai, p->ds));

    VkPushConstantRange pc_range = {0};
    pc_range.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    pc_range.offset = 0;
    pc_range.size = (pc_size > 0) ? pc_size : 4;

    VkPipelineLayoutCreateInfo pl_ci = {0};
    pl_ci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    pl_ci.setLayoutCount = 1;
    pl_ci.pSetLayouts = &p->ds_layout;
    if (pc_size > 0) {
        pl_ci.pushConstantRangeCount = 1;
        pl_ci.pPushConstantRanges = &pc_range;
    }

    VK_CHECK(vkCreatePipelineLayout(g.device, &pl_ci, NULL, &p->layout));

    VkComputePipelineCreateInfo cp_ci = {0};
    cp_ci.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
    cp_ci.stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    cp_ci.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    cp_ci.stage.module = p->shader;
    cp_ci.stage.pName = "main";
    cp_ci.layout = p->layout;

    VK_CHECK(vkCreateComputePipelines(g.device, VK_NULL_HANDLE, 1,
                                       &cp_ci, NULL, &p->pipeline));

    p->in_use = 1;
    return (ErgoVkPipe)slot;
}

/* Write a storage-buffer descriptor into ONE of a pipeline's two
 * per-frame-slot descriptor sets. */
static void vk_write_buf_desc(PipeSlot *p, int slot, int binding,
                              VkBuffer buffer, VkDeviceSize size) {
    VkDescriptorBufferInfo buf_info = {0};
    buf_info.buffer = buffer;
    buf_info.offset = 0;
    buf_info.range = size;

    VkWriteDescriptorSet write = {0};
    write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    write.dstSet = p->ds[slot];
    write.dstBinding = binding;
    write.descriptorCount = 1;
    write.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    write.pBufferInfo = &buf_info;

    vkUpdateDescriptorSets(g.device, 1, &write, 0, NULL);
}

/* Init-time bind: write BOTH frame slots. Only safe when no command
 * buffer referencing this pipeline's sets can be in flight — i.e. the
 * pipeline was just created, or its sets are only ever used by
 * submit-and-wait dispatches (xfer_cmd_buf), never by frame cmd bufs. */
static void vk_bind_buf_all_slots(PipeSlot *p, int binding,
                                  VkBuffer buffer, VkDeviceSize size) {
    for (int s = 0; s < 2; s++)
        vk_write_buf_desc(p, s, binding, buffer, size);
}

void ergo_vk_bind_buffer(ErgoVkPipe pipe, int binding, ErgoVkBuf buf) {
    if (!g.device) return;
    PipeSlot *p = &g.pipes[pipe];
    BufSlot  *b = &g.bufs[buf];
    p->bound_bufs[binding] = buf;

    /* Write only the CURRENT frame slot's set. The other slot's set may
     * still be referenced by the previous frame's in-flight cmd buf
     * (WAR hazard, VUID-vkUpdateDescriptorSets-None-03047). The current
     * slot is safe: frame_begin already waited for the fence of the
     * last frame that used it (two frames ago). */
    vk_write_buf_desc(p, g.cmd_idx, binding, b->buffer, b->size);
}

void ergo_vk_push_constants(ErgoVkPipe pipe, const void *data, size_t size) {
    if (!g.device) return;
    PipeSlot *p = &g.pipes[pipe];
    if (size > sizeof(p->pc_data)) {
        fprintf(stderr, "ergo_vk: push constant size %zu exceeds max %zu\n",
                size, sizeof(p->pc_data));
        exit(1);
    }
    memcpy(p->pc_data, data, size);
    p->pc_size = size;
}

void ergo_vk_dispatch(ErgoVkPipe pipe, int n_groups) {
    if (!g.device) return;
    PipeSlot *p = &g.pipes[pipe];

    if (!p->in_use || !p->pipeline) {
        fprintf(stderr, "[ergo_vk] ERROR: pipe %u not initialized!\n", pipe);
        return;
    }

    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;

    VK_CHECK(vkResetCommandBuffer(g.cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.cmd_buf, &begin));

    vkCmdBindPipeline(g.cmd_buf, VK_PIPELINE_BIND_POINT_COMPUTE,
                      p->pipeline);
    vkCmdBindDescriptorSets(g.cmd_buf, VK_PIPELINE_BIND_POINT_COMPUTE,
                            p->layout, 0, 1, &p->ds[g.cmd_idx], 0, NULL);

    if (p->pc_size > 0) {
        vkCmdPushConstants(g.cmd_buf, p->layout, VK_SHADER_STAGE_COMPUTE_BIT,
                           0, p->pc_size, p->pc_data);
    }

    g_launch_count++;
    vkCmdDispatch(g.cmd_buf, n_groups, 1, 1);

    VK_CHECK(vkEndCommandBuffer(g.cmd_buf));
    submit_and_wait();
}

/* ── Batched frame dispatch (no per-dispatch submit) ──────
 *
 * INVARIANT (2026-08-10, tower-variant bug): push constants are packed
 * host-side at RECORD time (see ergo_vk_push_constants /
 * ergo_vk_frame_dispatch below). A kernel whose PCs pack the result of
 * a not-yet-read-back reduction therefore records a STALE scalar — the
 * frame machinery cannot see this; the codegen must drain + read back
 * the reduction BEFORE emitting such a dispatch (ir_codegen.py
 * _emit_body pending-reduction flush, incl. GPU PC consumers), and must
 * download GPU-resident arrays before any host-fallback kernel loop
 * that reads them (_emit_loop). Root cause + fixes documented in
 * min/phase_ed/inc2_check.md ("Inc-2 follow-up"). */

void ergo_vk_frame_begin(void) {
    if (!g.device) return;
    /* Swap to the OTHER cmd_buf/fence so we can record while the
     * previous frame's cmd_buf may still be executing on the GPU.
     * We only wait for the fence we're about to reuse — which was
     * submitted TWO frames ago (or is signaled from init). */
    g.cmd_idx ^= 1;
    g.cmd_buf = g.cmd_bufs[g.cmd_idx];
    g.fence   = g.fences[g.cmd_idx];

    /* Wait for this slot's fence (2 frames ago, not 1).
     * Skip if ergo_vk_frame_wait() already drained it. */
    if (!g_frame_waited)
        VK_CHECK(vkWaitForFences(g.device, 1, &g.fence, VK_TRUE, UINT64_MAX));

    /* Collect timestamps from previous frame */
    if (g.ts_active && g.ts_idx > 0) {
        uint64_t ts[32];
        vkGetQueryPoolResults(g.device, g.ts_pool, 0, g.ts_idx,
            sizeof(ts), ts, sizeof(uint64_t),
            VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WAIT_BIT);
        for (int i = 0; i + 1 < g.ts_idx; i += 2) {
            int slot = i / 2;
            double ms = (double)(ts[i+1] - ts[i]) * g.ts_period / 1e6;
            if (slot < 16) g.ts_accum[slot] += ms;
        }
        g.ts_count++;
    }

    VK_CHECK(vkResetFences(g.device, 1, &g.fence));
    g_frame_waited = 0;  /* new frame — fence not yet waited */

    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkResetCommandBuffer(g.cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.cmd_buf, &begin));

    if (g.ts_active) {
        vkCmdResetQueryPool(g.cmd_buf, g.ts_pool, 0, 32);
        g.ts_idx = 0;
    }

    g.frame_parity ^= 1;
}

void ergo_vk_frame_fill(ErgoVkBuf buf, size_t size) {
    if (!g.device) return;
    BufSlot *b = &g.bufs[buf];
    vkCmdFillBuffer(g.cmd_buf, b->buffer, 0, size, 0);
}

void ergo_vk_frame_barrier(void) {
    if (!g.device) return;
    VkMemoryBarrier mb = {0};
    mb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT | VK_ACCESS_TRANSFER_WRITE_BIT;
    mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT;
    vkCmdPipelineBarrier(g.cmd_buf,
        VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT | VK_PIPELINE_STAGE_TRANSFER_BIT,
        VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
        0, 1, &mb, 0, NULL, 0, NULL);
}

void ergo_vk_frame_dispatch(ErgoVkPipe pipe, int n_groups) {
    if (!g.device) return;
    PipeSlot *p = &g.pipes[pipe];

    /* Timestamp before dispatch */
    if (g.ts_active && g.ts_idx < 30) {
        vkCmdWriteTimestamp(g.cmd_buf, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                            g.ts_pool, g.ts_idx++);
    }

    vkCmdBindPipeline(g.cmd_buf, VK_PIPELINE_BIND_POINT_COMPUTE,
                      p->pipeline);
    vkCmdBindDescriptorSets(g.cmd_buf, VK_PIPELINE_BIND_POINT_COMPUTE,
                            p->layout, 0, 1, &p->ds[g.cmd_idx], 0, NULL);
    if (p->pc_size > 0) {
        vkCmdPushConstants(g.cmd_buf, p->layout, VK_SHADER_STAGE_COMPUTE_BIT,
                           0, p->pc_size, p->pc_data);
    }
    g_launch_count++;
    vkCmdDispatch(g.cmd_buf, n_groups, 1, 1);

    /* Timestamp after dispatch */
    if (g.ts_active && g.ts_idx < 30) {
        vkCmdWriteTimestamp(g.cmd_buf, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                            g.ts_pool, g.ts_idx++);
    }
}

void ergo_vk_frame_end(void) {
    if (!g.device) return;
    VK_CHECK(vkEndCommandBuffer(g.cmd_buf));

    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.cmd_buf;
    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.fence));
    g_drain_count++;
    /* Do NOT wait here — next frame_begin waits for this fence. */
}

void ergo_vk_frame_wait(void) {
    if (!g.device) return;
    if (g_frame_waited) return;  /* idempotent */
    /* When rendering, the compute→vertex pipeline barrier in
     * render_points handles GPU-side sync. Only block on the
     * compute fence when headless (CPU needs results). */
    if (!g.headless) {
        g_frame_waited = 1;
        return;
    }
    VK_CHECK(vkWaitForFences(g.device, 1, &g.fence, VK_TRUE, UINT64_MAX));
    g_frame_waited = 1;
}

void ergo_vk_frame_drain(void) {
    /* Submit current frame command buffer WITHOUT waiting, then switch
     * to the dedicated sort command buffer for subsequent dispatches.
     * GPU ordering is guaranteed within the same queue.
     * frame_end will submit the sort cmd buf with the frame fence. */
    if (!g.device) return;
    VK_CHECK(vkEndCommandBuffer(g.cmd_buf));
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.cmd_buf;
    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, VK_NULL_HANDLE));
    /* Switch to sort command buffer — frame cmd buf stays pending */
    g.cmd_buf = g.sort_cmd_buf;
    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkResetCommandBuffer(g.cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.cmd_buf, &begin));
}

/* ══════════════════════════════════════════════════════════
 * RENDER PASS (Phase D → Phase E: 3D)
 * ══════════════════════════════════════════════════════════ */

#ifndef ERGO_VK_HEADLESS_ONLY

/* ── Inline math (no dependency) ────────────────────────── */

typedef struct { float m[16]; } Mat4;

static Mat4 mat4_identity(void) {
    Mat4 r = {{0}};
    r.m[0] = r.m[5] = r.m[10] = r.m[15] = 1.0f;
    return r;
}

static Mat4 mat4_mul(Mat4 a, Mat4 b) {
    Mat4 r = {{0}};
    for (int c = 0; c < 4; c++)
        for (int rr = 0; rr < 4; rr++)
            for (int k = 0; k < 4; k++)
                r.m[c * 4 + rr] += a.m[k * 4 + rr] * b.m[c * 4 + k];
    return r;
}

static Mat4 mat4_perspective(float fov_rad, float aspect, float znear, float zfar) {
    float f = 1.0f / tanf(fov_rad * 0.5f);
    Mat4 r = {{0}};
    r.m[0]  = f / aspect;
    r.m[5]  = -f;  /* Vulkan Y-flip */
    r.m[10] = zfar / (znear - zfar);
    r.m[11] = -1.0f;
    r.m[14] = (znear * zfar) / (znear - zfar);
    return r;
}

static Mat4 mat4_look_at(float ex, float ey, float ez,
                         float cx, float cy, float cz,
                         float ux, float uy, float uz) {
    float fx = cx - ex, fy = cy - ey, fz = cz - ez;
    float fl = sqrtf(fx*fx + fy*fy + fz*fz);
    fx /= fl; fy /= fl; fz /= fl;
    /* right = cross(forward, up) */
    float rx = fy*uz - fz*uy;
    float ry = fz*ux - fx*uz;
    float rz = fx*uy - fy*ux;
    float rl = sqrtf(rx*rx + ry*ry + rz*rz);
    rx /= rl; ry /= rl; rz /= rl;
    /* true up = cross(right, forward) */
    float tux = ry*fz - rz*fy;
    float tuy = rz*fx - rx*fz;
    float tuz = rx*fy - ry*fx;

    Mat4 r = mat4_identity();
    r.m[0] = rx;  r.m[4] = ry;  r.m[8]  = rz;  r.m[12] = -(rx*ex + ry*ey + rz*ez);
    r.m[1] = tux; r.m[5] = tuy; r.m[9]  = tuz; r.m[13] = -(tux*ex + tuy*ey + tuz*ez);
    r.m[2] = -fx; r.m[6] = -fy; r.m[10] = -fz; r.m[14] = (fx*ex + fy*ey + fz*ez);
    r.m[3] = 0;   r.m[7] = 0;   r.m[11] = 0;   r.m[15] = 1.0f;
    return r;
}

/* ── Camera callbacks ───────────────────────────────────── */

static void camera_mouse_button_cb(GLFWwindow *w, int button, int action, int mods) {
    (void)mods;
    if (button == GLFW_MOUSE_BUTTON_LEFT) {
        g.mouse_dragging = (action == GLFW_PRESS);
        if (g.mouse_dragging)
            glfwGetCursorPos(w, &g.mouse_last_x, &g.mouse_last_y);
        g.cam_idle_until = glfwGetTime() + 4.0;
    }
}

static void camera_cursor_pos_cb(GLFWwindow *w, double xpos, double ypos) {
    (void)w;
    if (!g.mouse_dragging) return;
    g.cam_idle_until = glfwGetTime() + 4.0;
    float dx = (float)(xpos - g.mouse_last_x);
    float dy = (float)(ypos - g.mouse_last_y);
    g.mouse_last_x = xpos;
    g.mouse_last_y = ypos;
    g.cam_azimuth   += dx * 0.005f;
    g.cam_elevation += dy * 0.005f;
    /* Clamp elevation to avoid gimbal lock */
    if (g.cam_elevation >  1.5f) g.cam_elevation =  1.5f;
    if (g.cam_elevation < -1.5f) g.cam_elevation = -1.5f;
}

static int g_culling_enabled = 0;  /* toggle with 'C' key */

static void camera_key_cb(GLFWwindow *w, int key, int scancode, int action, int mods) {
    (void)w; (void)scancode; (void)mods;
    if (action != GLFW_PRESS) return;
    if (key == GLFW_KEY_C) {
        g_culling_enabled = !g_culling_enabled;
        fprintf(stderr, "[ergo_vk] Culling: %s\n",
                g_culling_enabled ? "ON" : "OFF");
    }
}

static void camera_scroll_cb(GLFWwindow *w, double xoff, double yoff) {
    (void)w; (void)xoff;
    g.cam_idle_until = glfwGetTime() + 4.0;
    g.cam_distance -= (float)yoff * 0.1f;
    if (g.cam_distance < 0.1f) g.cam_distance = 0.1f;
    if (g.cam_distance > 10.0f) g.cam_distance = 10.0f;
}

/* Auto-orbit tick (2026-09-04): advance the camera azimuth gently so
 * point clouds read as 3D without mouse input; suspended for 4 s after
 * any mouse interaction (callbacks stamp g.cam_idle_until). */
static void ergo_vk_camera_tick(void) {
    if (g.cam_spin_rate <= 0.0f) return;
    double now = glfwGetTime();
    if (g.cam_last_tick == 0.0) { g.cam_last_tick = now; return; }
    if (now < g.cam_idle_until) { g.cam_last_tick = now; return; }
    double dt = now - g.cam_last_tick;
    g.cam_last_tick = now;
    if (dt <= 0.0 || dt > 0.25) dt = 0.016;  /* stall guard */
    g.cam_azimuth += g.cam_spin_rate * (float)dt;
}

/* ── Swapchain creation ──────────────────────────────────── */

static void render_create_swapchain(void) {
    VkSurfaceCapabilitiesKHR caps;
    VK_CHECK(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(
        g.phys_device, g.surface, &caps));

    /* Pick format: prefer B8G8R8A8_SRGB */
    uint32_t fmt_count = 0;
    vkGetPhysicalDeviceSurfaceFormatsKHR(g.phys_device, g.surface,
                                         &fmt_count, NULL);
    VkSurfaceFormatKHR *fmts = malloc(fmt_count * sizeof(VkSurfaceFormatKHR));
    vkGetPhysicalDeviceSurfaceFormatsKHR(g.phys_device, g.surface,
                                         &fmt_count, fmts);
    g.sc_format = fmts[0].format;
    VkColorSpaceKHR color_space = fmts[0].colorSpace;
    for (uint32_t i = 0; i < fmt_count; i++) {
        if (fmts[i].format == VK_FORMAT_B8G8R8A8_SRGB &&
            fmts[i].colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR) {
            g.sc_format = fmts[i].format;
            color_space = fmts[i].colorSpace;
            break;
        }
    }
    free(fmts);

    /* Extent — query actual framebuffer size from GLFW.
     * On Wayland/Hyprland the compositor may report a different
     * currentExtent than what was requested; use glfwGetFramebufferSize
     * as the authoritative source and clamp to surface limits. */
    {
        int fb_w = 1280, fb_h = 720;
#ifndef ERGO_VK_ANDROID
        if (!g.headless && g.window)
            glfwGetFramebufferSize(g.window, &fb_w, &fb_h);
#endif
        g.sc_extent.width  = (uint32_t)fb_w;
        g.sc_extent.height = (uint32_t)fb_h;
        if (g.sc_extent.width  < caps.minImageExtent.width)
            g.sc_extent.width  = caps.minImageExtent.width;
        if (g.sc_extent.height < caps.minImageExtent.height)
            g.sc_extent.height = caps.minImageExtent.height;
        if (caps.maxImageExtent.width > 0 &&
            g.sc_extent.width > caps.maxImageExtent.width)
            g.sc_extent.width  = caps.maxImageExtent.width;
        if (caps.maxImageExtent.height > 0 &&
            g.sc_extent.height > caps.maxImageExtent.height)
            g.sc_extent.height = caps.maxImageExtent.height;
    }

    uint32_t img_count = caps.minImageCount + 1;
    if (caps.maxImageCount > 0 && img_count > caps.maxImageCount)
        img_count = caps.maxImageCount;
    if (img_count > ERGO_VK_MAX_SWAPCHAIN)
        img_count = ERGO_VK_MAX_SWAPCHAIN;

    VkSwapchainCreateInfoKHR sc_ci = {0};
    sc_ci.sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
    sc_ci.surface = g.surface;
    sc_ci.minImageCount = img_count;
    sc_ci.imageFormat = g.sc_format;
    sc_ci.imageColorSpace = color_space;
    sc_ci.imageExtent = g.sc_extent;
    sc_ci.imageArrayLayers = 1;
    sc_ci.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
    sc_ci.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
    sc_ci.preTransform = caps.currentTransform;
    sc_ci.compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
    /* ERGO_NOVSYNC=1 → uncapped framerate (MAILBOX or IMMEDIATE) */
    sc_ci.presentMode = VK_PRESENT_MODE_FIFO_KHR;
    if (getenv("ERGO_NOVSYNC")) {
        uint32_t n_modes = 0;
        vkGetPhysicalDeviceSurfacePresentModesKHR(g.phys_device, g.surface,
                                                   &n_modes, NULL);
        VkPresentModeKHR *modes = malloc(n_modes * sizeof(VkPresentModeKHR));
        vkGetPhysicalDeviceSurfacePresentModesKHR(g.phys_device, g.surface,
                                                   &n_modes, modes);
        for (uint32_t i = 0; i < n_modes; i++) {
            if (modes[i] == VK_PRESENT_MODE_MAILBOX_KHR) {
                sc_ci.presentMode = VK_PRESENT_MODE_MAILBOX_KHR;
                break;
            }
            if (modes[i] == VK_PRESENT_MODE_IMMEDIATE_KHR)
                sc_ci.presentMode = VK_PRESENT_MODE_IMMEDIATE_KHR;
        }
        free(modes);
    }
    sc_ci.clipped = VK_TRUE;

    VK_CHECK(vkCreateSwapchainKHR(g.device, &sc_ci, NULL, &g.swapchain));

    /* Get swapchain images */
    VK_CHECK(vkGetSwapchainImagesKHR(g.device, g.swapchain,
                                      &g.sc_count, NULL));
    if (g.sc_count > ERGO_VK_MAX_SWAPCHAIN) g.sc_count = ERGO_VK_MAX_SWAPCHAIN;
    VK_CHECK(vkGetSwapchainImagesKHR(g.device, g.swapchain,
                                      &g.sc_count, g.sc_images));

    /* ── Depth buffer ── */
    VkImageCreateInfo depth_ci = {0};
    depth_ci.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    depth_ci.imageType = VK_IMAGE_TYPE_2D;
    depth_ci.format = VK_FORMAT_D32_SFLOAT;
    depth_ci.extent.width = g.sc_extent.width;
    depth_ci.extent.height = g.sc_extent.height;
    depth_ci.extent.depth = 1;
    depth_ci.mipLevels = 1;
    depth_ci.arrayLayers = 1;
    depth_ci.samples = VK_SAMPLE_COUNT_1_BIT;
    depth_ci.tiling = VK_IMAGE_TILING_OPTIMAL;
    depth_ci.usage = VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT;
    VK_CHECK(vkCreateImage(g.device, &depth_ci, NULL, &g.depth_image));

    VkMemoryRequirements depth_mem_req;
    vkGetImageMemoryRequirements(g.device, g.depth_image, &depth_mem_req);
    VkMemoryAllocateInfo depth_mem_ai = {0};
    depth_mem_ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    depth_mem_ai.allocationSize = depth_mem_req.size;
    depth_mem_ai.memoryTypeIndex = find_memory_type(
        depth_mem_req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    VK_CHECK(vkAllocateMemory(g.device, &depth_mem_ai, NULL, &g.depth_memory));
    VK_CHECK(vkBindImageMemory(g.device, g.depth_image, g.depth_memory, 0));

    VkImageViewCreateInfo depth_iv_ci = {0};
    depth_iv_ci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    depth_iv_ci.image = g.depth_image;
    depth_iv_ci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    depth_iv_ci.format = VK_FORMAT_D32_SFLOAT;
    depth_iv_ci.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    depth_iv_ci.subresourceRange.levelCount = 1;
    depth_iv_ci.subresourceRange.layerCount = 1;
    VK_CHECK(vkCreateImageView(g.device, &depth_iv_ci, NULL, &g.depth_view));

    /* ── Render pass (color + depth) ── */
    VkAttachmentDescription attachments[2] = {{0},{0}};
    /* [0] color */
    attachments[0].format = g.sc_format;
    attachments[0].samples = VK_SAMPLE_COUNT_1_BIT;
    attachments[0].loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    attachments[0].storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    attachments[0].initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    attachments[0].finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
    /* [1] depth */
    attachments[1].format = VK_FORMAT_D32_SFLOAT;
    attachments[1].samples = VK_SAMPLE_COUNT_1_BIT;
    attachments[1].loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    attachments[1].storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    attachments[1].stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    attachments[1].stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    attachments[1].initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    attachments[1].finalLayout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    VkAttachmentReference color_ref = {0};
    color_ref.attachment = 0;
    color_ref.layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkAttachmentReference depth_ref = {0};
    depth_ref.attachment = 1;
    depth_ref.layout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    VkSubpassDescription subpass = {0};
    subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1;
    subpass.pColorAttachments = &color_ref;
    subpass.pDepthStencilAttachment = &depth_ref;

    VkSubpassDependency dep = {0};
    dep.srcSubpass = VK_SUBPASS_EXTERNAL;
    dep.dstSubpass = 0;
    dep.srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT |
                       VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT;
    dep.srcAccessMask = 0;
    dep.dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT |
                       VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT;
    dep.dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT |
                        VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;

    VkRenderPassCreateInfo rp_ci = {0};
    rp_ci.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    rp_ci.attachmentCount = 2;
    rp_ci.pAttachments = attachments;
    rp_ci.subpassCount = 1;
    rp_ci.pSubpasses = &subpass;
    rp_ci.dependencyCount = 1;
    rp_ci.pDependencies = &dep;

    VK_CHECK(vkCreateRenderPass(g.device, &rp_ci, NULL, &g.render_pass));

    /* Image views + framebuffers (color + depth) */
    for (uint32_t i = 0; i < g.sc_count; i++) {
        VkImageViewCreateInfo iv_ci = {0};
        iv_ci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        iv_ci.image = g.sc_images[i];
        iv_ci.viewType = VK_IMAGE_VIEW_TYPE_2D;
        iv_ci.format = g.sc_format;
        iv_ci.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        iv_ci.subresourceRange.levelCount = 1;
        iv_ci.subresourceRange.layerCount = 1;
        VK_CHECK(vkCreateImageView(g.device, &iv_ci, NULL, &g.sc_views[i]));

        VkImageView fb_attachments[2] = { g.sc_views[i], g.depth_view };
        VkFramebufferCreateInfo fb_ci = {0};
        fb_ci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fb_ci.renderPass = g.render_pass;
        fb_ci.attachmentCount = 2;
        fb_ci.pAttachments = fb_attachments;
        fb_ci.width = g.sc_extent.width;
        fb_ci.height = g.sc_extent.height;
        fb_ci.layers = 1;
        VK_CHECK(vkCreateFramebuffer(g.device, &fb_ci, NULL, &g.sc_fbs[i]));
    }
}

static void render_cleanup_swapchain(void) {
    for (uint32_t i = 0; i < g.sc_count; i++) {
        vkDestroyFramebuffer(g.device, g.sc_fbs[i], NULL);
        vkDestroyImageView(g.device, g.sc_views[i], NULL);
    }
    vkDestroyImageView(g.device, g.depth_view, NULL);
    vkDestroyImage(g.device, g.depth_image, NULL);
    vkFreeMemory(g.device, g.depth_memory, NULL);
    vkDestroyRenderPass(g.device, g.render_pass, NULL);
    vkDestroySwapchainKHR(g.device, g.swapchain, NULL);
}

/* ── Graphics pipeline ───────────────────────────────────── */

static void render_create_pipeline(void) {
    /* Shader modules from embedded SPIR-V */
    VkShaderModuleCreateInfo vert_ci = {0};
    vert_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    vert_ci.codeSize = render_vert_spv_size;
    vert_ci.pCode = (const uint32_t *)render_vert_spv;
    VK_CHECK(vkCreateShaderModule(g.device, &vert_ci, NULL, &g.vert_shader));

    VkShaderModuleCreateInfo frag_ci = {0};
    frag_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    frag_ci.codeSize = render_frag_spv_size;
    frag_ci.pCode = (const uint32_t *)render_frag_spv;
    VK_CHECK(vkCreateShaderModule(g.device, &frag_ci, NULL, &g.frag_shader));

    VkPipelineShaderStageCreateInfo stages[2] = {{0},{0}};
    stages[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module = g.vert_shader;
    stages[0].pName = "main";
    stages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module = g.frag_shader;
    stages[1].pName = "main";

    /* No vertex input (3D mesh generated from gl_VertexIndex) */
    VkPipelineVertexInputStateCreateInfo vi = {0};
    vi.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;

    VkPipelineInputAssemblyStateCreateInfo ia = {0};
    ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    VkViewport viewport = {0};
    viewport.width = (float)g.sc_extent.width;
    viewport.height = (float)g.sc_extent.height;
    viewport.maxDepth = 1.0f;

    VkRect2D scissor = {0};
    scissor.extent = g.sc_extent;

    VkPipelineViewportStateCreateInfo vp = {0};
    vp.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vp.viewportCount = 1;
    vp.pViewports = &viewport;
    vp.scissorCount = 1;
    vp.pScissors = &scissor;

    VkPipelineRasterizationStateCreateInfo rs = {0};
    rs.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_NONE;
    rs.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    rs.lineWidth = 1.0f;

    VkPipelineMultisampleStateCreateInfo ms = {0};
    ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    /* Depth testing */
    VkPipelineDepthStencilStateCreateInfo ds = {0};
    ds.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    ds.depthTestEnable = VK_TRUE;
    ds.depthWriteEnable = VK_TRUE;
    ds.depthCompareOp = VK_COMPARE_OP_LESS;

    VkPipelineColorBlendAttachmentState blend_att = {0};
    blend_att.colorWriteMask = VK_COLOR_COMPONENT_R_BIT |
                               VK_COLOR_COMPONENT_G_BIT |
                               VK_COLOR_COMPONENT_B_BIT |
                               VK_COLOR_COMPONENT_A_BIT;

    VkPipelineColorBlendStateCreateInfo cb = {0};
    cb.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    cb.attachmentCount = 1;
    cb.pAttachments = &blend_att;

    /* Descriptor set layout: storage buffer visible to vertex + fragment */
    VkDescriptorSetLayoutBinding ds_binding = {0};
    ds_binding.binding = 0;
    ds_binding.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    ds_binding.descriptorCount = 1;
    ds_binding.stageFlags = VK_SHADER_STAGE_VERTEX_BIT |
                            VK_SHADER_STAGE_FRAGMENT_BIT;

    VkDescriptorSetLayoutCreateInfo dsl_ci = {0};
    dsl_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dsl_ci.bindingCount = 1;
    dsl_ci.pBindings = &ds_binding;
    VK_CHECK(vkCreateDescriptorSetLayout(g.device, &dsl_ci, NULL,
                                          &g.gfx_ds_layout));

    /* Descriptor pool */
    VkDescriptorPoolSize dp_size = {0};
    dp_size.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    dp_size.descriptorCount = 1;

    VkDescriptorPoolCreateInfo dp_ci = {0};
    dp_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dp_ci.maxSets = 1;
    dp_ci.poolSizeCount = 1;
    dp_ci.pPoolSizes = &dp_size;
    VK_CHECK(vkCreateDescriptorPool(g.device, &dp_ci, NULL, &g.gfx_ds_pool));

    VkDescriptorSetAllocateInfo ds_ai = {0};
    ds_ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    ds_ai.descriptorPool = g.gfx_ds_pool;
    ds_ai.descriptorSetCount = 1;
    ds_ai.pSetLayouts = &g.gfx_ds_layout;
    VK_CHECK(vkAllocateDescriptorSets(g.device, &ds_ai, &g.gfx_ds));

    /* Push constants: mat4 viewProj (64) + grid_w, grid_h (8) +
       val_min, val_max, height_scale (12) = 84 bytes.
       Visible to both vertex and fragment stages. */
    VkPushConstantRange pc_range = {0};
    pc_range.stageFlags = VK_SHADER_STAGE_VERTEX_BIT |
                          VK_SHADER_STAGE_FRAGMENT_BIT;
    pc_range.size = 84;

    VkPipelineLayoutCreateInfo pl_ci = {0};
    pl_ci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    pl_ci.setLayoutCount = 1;
    pl_ci.pSetLayouts = &g.gfx_ds_layout;
    pl_ci.pushConstantRangeCount = 1;
    pl_ci.pPushConstantRanges = &pc_range;
    VK_CHECK(vkCreatePipelineLayout(g.device, &pl_ci, NULL, &g.gfx_layout));

    /* Graphics pipeline */
    VkGraphicsPipelineCreateInfo gp_ci = {0};
    gp_ci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gp_ci.stageCount = 2;
    gp_ci.pStages = stages;
    gp_ci.pVertexInputState = &vi;
    gp_ci.pInputAssemblyState = &ia;
    gp_ci.pViewportState = &vp;
    gp_ci.pRasterizationState = &rs;
    gp_ci.pMultisampleState = &ms;
    gp_ci.pDepthStencilState = &ds;
    gp_ci.pColorBlendState = &cb;
    gp_ci.layout = g.gfx_layout;
    gp_ci.renderPass = g.render_pass;
    gp_ci.subpass = 0;

    VK_CHECK(vkCreateGraphicsPipelines(g.device, VK_NULL_HANDLE, 1,
                                        &gp_ci, NULL, &g.gfx_pipeline));
}

/* ── Point cloud pipeline ───────────────────────────────── */

static void render_create_points_pipeline(void) {
    /* Shader modules */
    VkShaderModuleCreateInfo vert_ci = {0};
    vert_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    vert_ci.codeSize = render_points_vert_spv_size;
    vert_ci.pCode = (const uint32_t *)render_points_vert_spv;
    VK_CHECK(vkCreateShaderModule(g.device, &vert_ci, NULL, &g.pts_vert_shader));

    VkShaderModuleCreateInfo frag_ci = {0};
    frag_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    frag_ci.codeSize = render_points_frag_spv_size;
    frag_ci.pCode = (const uint32_t *)render_points_frag_spv;
    VK_CHECK(vkCreateShaderModule(g.device, &frag_ci, NULL, &g.pts_frag_shader));

    VkPipelineShaderStageCreateInfo stages[2] = {{0},{0}};
    stages[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module = g.pts_vert_shader;
    stages[0].pName = "main";
    stages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module = g.pts_frag_shader;
    stages[1].pName = "main";

    VkPipelineVertexInputStateCreateInfo vi = {0};
    vi.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;

    VkPipelineInputAssemblyStateCreateInfo ia = {0};
    ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = VK_PRIMITIVE_TOPOLOGY_POINT_LIST;

    VkViewport viewport = {0};
    viewport.width = (float)g.sc_extent.width;
    viewport.height = (float)g.sc_extent.height;
    viewport.maxDepth = 1.0f;

    VkRect2D scissor = {0};
    scissor.extent = g.sc_extent;

    VkPipelineViewportStateCreateInfo vp = {0};
    vp.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vp.viewportCount = 1;
    vp.pViewports = &viewport;
    vp.scissorCount = 1;
    vp.pScissors = &scissor;

    VkPipelineRasterizationStateCreateInfo rs = {0};
    rs.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_NONE;
    rs.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    rs.lineWidth = 1.0f;

    VkPipelineMultisampleStateCreateInfo ms = {0};
    ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    VkPipelineDepthStencilStateCreateInfo ds = {0};
    ds.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    ds.depthTestEnable = VK_TRUE;
    ds.depthWriteEnable = VK_TRUE;
    ds.depthCompareOp = VK_COMPARE_OP_LESS;

    /* Opaque points — no blending, allows early-Z rejection.
     * With blend ON the GPU must shade every fragment (no depth cull). */
    VkPipelineColorBlendAttachmentState blend_att = {0};
    blend_att.blendEnable = VK_FALSE;
    blend_att.colorWriteMask = VK_COLOR_COMPONENT_R_BIT |
                               VK_COLOR_COMPONENT_G_BIT |
                               VK_COLOR_COMPONENT_B_BIT |
                               VK_COLOR_COMPONENT_A_BIT;

    VkPipelineColorBlendStateCreateInfo cb = {0};
    cb.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    cb.attachmentCount = 1;
    cb.pAttachments = &blend_att;

    /* 4 storage buffers: pos_x, pos_y, pos_z, color — direct SoA read */
    VkDescriptorSetLayoutBinding bindings[5];
    for (int i = 0; i < 4; i++) {
        memset(&bindings[i], 0, sizeof(VkDescriptorSetLayoutBinding));
        bindings[i].binding = i;
        bindings[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        bindings[i].descriptorCount = 1;
        bindings[i].stageFlags = VK_SHADER_STAGE_VERTEX_BIT;
    }
    /* UBO at binding 5 — matches shader's RenderParams uniform */
    memset(&bindings[4], 0, sizeof(VkDescriptorSetLayoutBinding));
    bindings[4].binding = 5;
    bindings[4].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    bindings[4].descriptorCount = 1;
    bindings[4].stageFlags = VK_SHADER_STAGE_VERTEX_BIT;

    VkDescriptorSetLayoutCreateInfo dsl_ci = {0};
    dsl_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dsl_ci.bindingCount = 5;
    dsl_ci.pBindings = bindings;
    VK_CHECK(vkCreateDescriptorSetLayout(g.device, &dsl_ci, NULL,
                                          &g.pts_ds_layout));

    VkDescriptorPoolSize dp_sizes[2] = {{0},{0}};
    dp_sizes[0].type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    dp_sizes[0].descriptorCount = 4;
    dp_sizes[1].type = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    dp_sizes[1].descriptorCount = 1;

    VkDescriptorPoolCreateInfo dp_ci = {0};
    dp_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dp_ci.maxSets = 1;
    dp_ci.poolSizeCount = 2;
    dp_ci.pPoolSizes = dp_sizes;
    VK_CHECK(vkCreateDescriptorPool(g.device, &dp_ci, NULL, &g.pts_ds_pool));

    VkDescriptorSetAllocateInfo ds_ai = {0};
    ds_ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    ds_ai.descriptorPool = g.pts_ds_pool;
    ds_ai.descriptorSetCount = 1;
    ds_ai.pSetLayouts = &g.pts_ds_layout;
    VK_CHECK(vkAllocateDescriptorSets(g.device, &ds_ai, &g.pts_ds));

    /* Push constants: mat4(64) + point_size(4) + val_min(4) + val_max(4) + world_scale(4) = 80 */
    VkPushConstantRange pc_range = {0};
    pc_range.stageFlags = VK_SHADER_STAGE_VERTEX_BIT;
    pc_range.size = 96;

    VkPipelineLayoutCreateInfo pl_ci = {0};
    pl_ci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    pl_ci.setLayoutCount = 1;
    pl_ci.pSetLayouts = &g.pts_ds_layout;
    pl_ci.pushConstantRangeCount = 1;
    pl_ci.pPushConstantRanges = &pc_range;
    VK_CHECK(vkCreatePipelineLayout(g.device, &pl_ci, NULL, &g.pts_layout));

    VkGraphicsPipelineCreateInfo gp_ci = {0};
    gp_ci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gp_ci.stageCount = 2;
    gp_ci.pStages = stages;
    gp_ci.pVertexInputState = &vi;
    gp_ci.pInputAssemblyState = &ia;
    gp_ci.pViewportState = &vp;
    gp_ci.pRasterizationState = &rs;
    gp_ci.pMultisampleState = &ms;
    gp_ci.pDepthStencilState = &ds;
    gp_ci.pColorBlendState = &cb;
    gp_ci.layout = g.pts_layout;
    gp_ci.renderPass = g.render_pass;
    gp_ci.subpass = 0;

    VK_CHECK(vkCreateGraphicsPipelines(g.device, VK_NULL_HANDLE, 1,
                                        &gp_ci, NULL, &g.pts_pipeline));
}

/* ── Gaussian splat pipeline ─────────────────────────────── */

static void gauss_create_lut(void) {
    /* Generate 64×64 R8 gaussian falloff texture.
     * Center = 1.0, edges (at 2-sigma) ≈ 0.018, corners = ~0. */
    const int LUT_SIZE = 64;
    uint8_t pixels[64 * 64];
    for (int y = 0; y < LUT_SIZE; y++) {
        for (int x = 0; x < LUT_SIZE; x++) {
            float u = (x + 0.5f) / LUT_SIZE * 2.0f - 1.0f; /* [-1, 1] */
            float v = (y + 0.5f) / LUT_SIZE * 2.0f - 1.0f;
            float d2 = u * u + v * v;
            float w = expf(-2.0f * d2); /* sigma = 1/2, so exp(-0.5*(d/σ)²) = exp(-2*d²) */
            pixels[y * LUT_SIZE + x] = (uint8_t)(w * 255.0f + 0.5f);
        }
    }

    /* Create VkImage */
    VkImageCreateInfo img_ci = {0};
    img_ci.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    img_ci.imageType = VK_IMAGE_TYPE_2D;
    img_ci.format = VK_FORMAT_R8_UNORM;
    img_ci.extent = (VkExtent3D){LUT_SIZE, LUT_SIZE, 1};
    img_ci.mipLevels = 1;
    img_ci.arrayLayers = 1;
    img_ci.samples = VK_SAMPLE_COUNT_1_BIT;
    img_ci.tiling = VK_IMAGE_TILING_OPTIMAL;
    img_ci.usage = VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT;
    img_ci.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    VK_CHECK(vkCreateImage(g.device, &img_ci, NULL, &g.gauss_lut_image));

    VkMemoryRequirements mem_req;
    vkGetImageMemoryRequirements(g.device, g.gauss_lut_image, &mem_req);
    VkMemoryAllocateInfo mem_ai = {0};
    mem_ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    mem_ai.allocationSize = mem_req.size;
    mem_ai.memoryTypeIndex = find_memory_type(mem_req.memoryTypeBits,
        VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    VK_CHECK(vkAllocateMemory(g.device, &mem_ai, NULL, &g.gauss_lut_memory));
    VK_CHECK(vkBindImageMemory(g.device, g.gauss_lut_image, g.gauss_lut_memory, 0));

    /* Upload via staging buffer */
    ensure_staging(LUT_SIZE * LUT_SIZE);
    memcpy(g.staging_mapped, pixels, LUT_SIZE * LUT_SIZE);

    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkResetCommandBuffer(g.xfer_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.xfer_cmd_buf, &begin));

    /* Transition to TRANSFER_DST */
    VkImageMemoryBarrier barrier = {0};
    barrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    barrier.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    barrier.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    barrier.image = g.gauss_lut_image;
    barrier.subresourceRange = (VkImageSubresourceRange){
        VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    barrier.srcAccessMask = 0;
    barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    vkCmdPipelineBarrier(g.xfer_cmd_buf,
        VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
        0, 0, NULL, 0, NULL, 1, &barrier);

    VkBufferImageCopy region = {0};
    region.imageSubresource = (VkImageSubresourceLayers){
        VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    region.imageExtent = (VkExtent3D){LUT_SIZE, LUT_SIZE, 1};
    vkCmdCopyBufferToImage(g.xfer_cmd_buf, g.staging_buf, g.gauss_lut_image,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);

    /* Transition to SHADER_READ */
    barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    barrier.newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
    vkCmdPipelineBarrier(g.xfer_cmd_buf,
        VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
        0, 0, NULL, 0, NULL, 1, &barrier);

    VK_CHECK(vkEndCommandBuffer(g.xfer_cmd_buf));
    xfer_submit_and_wait();

    /* Create image view */
    VkImageViewCreateInfo iv_ci = {0};
    iv_ci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    iv_ci.image = g.gauss_lut_image;
    iv_ci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    iv_ci.format = VK_FORMAT_R8_UNORM;
    iv_ci.subresourceRange = (VkImageSubresourceRange){
        VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    VK_CHECK(vkCreateImageView(g.device, &iv_ci, NULL, &g.gauss_lut_view));

    /* Create sampler */
    VkSamplerCreateInfo samp_ci = {0};
    samp_ci.sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
    samp_ci.magFilter = VK_FILTER_LINEAR;
    samp_ci.minFilter = VK_FILTER_LINEAR;
    samp_ci.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    samp_ci.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    VK_CHECK(vkCreateSampler(g.device, &samp_ci, NULL, &g.gauss_lut_sampler));
}

static void render_create_gauss_pipeline(void) {
    gauss_create_lut();

    VkShaderModuleCreateInfo vert_ci = {0};
    vert_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    vert_ci.codeSize = render_gauss_vert_spv_size;
    vert_ci.pCode = (const uint32_t *)render_gauss_vert_spv;
    VK_CHECK(vkCreateShaderModule(g.device, &vert_ci, NULL, &g.gauss_vert_shader));

    VkShaderModuleCreateInfo frag_ci = {0};
    frag_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    frag_ci.codeSize = render_gauss_frag_spv_size;
    frag_ci.pCode = (const uint32_t *)render_gauss_frag_spv;
    VK_CHECK(vkCreateShaderModule(g.device, &frag_ci, NULL, &g.gauss_frag_shader));

    VkPipelineShaderStageCreateInfo stages[2] = {{0},{0}};
    stages[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module = g.gauss_vert_shader;
    stages[0].pName = "main";
    stages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module = g.gauss_frag_shader;
    stages[1].pName = "main";

    VkPipelineVertexInputStateCreateInfo vi = {0};
    vi.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;

    VkPipelineInputAssemblyStateCreateInfo ia = {0};
    ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    VkViewport viewport = {0};
    viewport.width = (float)g.sc_extent.width;
    viewport.height = (float)g.sc_extent.height;
    viewport.maxDepth = 1.0f;

    VkRect2D scissor = {0};
    scissor.extent = g.sc_extent;

    VkPipelineViewportStateCreateInfo vp = {0};
    vp.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vp.viewportCount = 1;
    vp.pViewports = &viewport;
    vp.scissorCount = 1;
    vp.pScissors = &scissor;

    VkPipelineRasterizationStateCreateInfo rs = {0};
    rs.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_NONE;
    rs.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    rs.lineWidth = 1.0f;

    VkPipelineMultisampleStateCreateInfo ms = {0};
    ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    VkPipelineDepthStencilStateCreateInfo ds = {0};
    ds.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    ds.depthTestEnable = VK_TRUE;
    ds.depthWriteEnable = VK_FALSE; /* Gaussians are translucent — don't write depth */
    ds.depthCompareOp = VK_COMPARE_OP_LESS;

    /* Additive blending: src*srcAlpha + dst*1
     * Gaussian fragments accumulate light additively. */
    VkPipelineColorBlendAttachmentState blend_att = {0};
    blend_att.blendEnable = VK_TRUE;
    blend_att.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
    blend_att.dstColorBlendFactor = VK_BLEND_FACTOR_ONE;
    blend_att.colorBlendOp = VK_BLEND_OP_ADD;
    blend_att.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
    blend_att.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
    blend_att.alphaBlendOp = VK_BLEND_OP_ADD;
    blend_att.colorWriteMask = VK_COLOR_COMPONENT_R_BIT |
                               VK_COLOR_COMPONENT_G_BIT |
                               VK_COLOR_COMPONENT_B_BIT |
                               VK_COLOR_COMPONENT_A_BIT;

    VkPipelineColorBlendStateCreateInfo cb = {0};
    cb.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    cb.attachmentCount = 1;
    cb.pAttachments = &blend_att;

    /* 5 descriptors: 4 storage buffers (pos_x/y/z, color) + 1 combined image sampler (LUT) */
    VkDescriptorSetLayoutBinding bindings[5];
    for (int i = 0; i < 4; i++) {
        memset(&bindings[i], 0, sizeof(VkDescriptorSetLayoutBinding));
        bindings[i].binding = i;
        bindings[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        bindings[i].descriptorCount = 1;
        bindings[i].stageFlags = VK_SHADER_STAGE_VERTEX_BIT;
    }
    memset(&bindings[4], 0, sizeof(VkDescriptorSetLayoutBinding));
    bindings[4].binding = 4;
    bindings[4].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    bindings[4].descriptorCount = 1;
    bindings[4].stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;

    VkDescriptorSetLayoutCreateInfo dsl_ci = {0};
    dsl_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dsl_ci.bindingCount = 5;
    dsl_ci.pBindings = bindings;
    VK_CHECK(vkCreateDescriptorSetLayout(g.device, &dsl_ci, NULL,
                                          &g.gauss_ds_layout));

    VkDescriptorPoolSize dp_sizes[2];
    dp_sizes[0].type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    dp_sizes[0].descriptorCount = 4;
    dp_sizes[1].type = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    dp_sizes[1].descriptorCount = 1;

    VkDescriptorPoolCreateInfo dp_ci = {0};
    dp_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dp_ci.maxSets = 1;
    dp_ci.poolSizeCount = 2;
    dp_ci.pPoolSizes = dp_sizes;
    VK_CHECK(vkCreateDescriptorPool(g.device, &dp_ci, NULL, &g.gauss_ds_pool));

    VkDescriptorSetAllocateInfo ds_ai = {0};
    ds_ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    ds_ai.descriptorPool = g.gauss_ds_pool;
    ds_ai.descriptorSetCount = 1;
    ds_ai.pSetLayouts = &g.gauss_ds_layout;
    VK_CHECK(vkAllocateDescriptorSets(g.device, &ds_ai, &g.gauss_ds));

    /* Bind the LUT texture to binding 4 (static — never changes) */
    VkDescriptorImageInfo img_info = {0};
    img_info.imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    img_info.imageView = g.gauss_lut_view;
    img_info.sampler = g.gauss_lut_sampler;

    VkWriteDescriptorSet lut_write = {0};
    lut_write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    lut_write.dstSet = g.gauss_ds;
    lut_write.dstBinding = 4;
    lut_write.descriptorCount = 1;
    lut_write.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    lut_write.pImageInfo = &img_info;
    vkUpdateDescriptorSets(g.device, 1, &lut_write, 0, NULL);

    /* Push constants: same layout as points (mat4 + 4 floats = 80 bytes) */
    VkPushConstantRange pc_range = {0};
    pc_range.stageFlags = VK_SHADER_STAGE_VERTEX_BIT;
    pc_range.size = 96;

    VkPipelineLayoutCreateInfo pl_ci = {0};
    pl_ci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    pl_ci.setLayoutCount = 1;
    pl_ci.pSetLayouts = &g.gauss_ds_layout;
    pl_ci.pushConstantRangeCount = 1;
    pl_ci.pPushConstantRanges = &pc_range;
    VK_CHECK(vkCreatePipelineLayout(g.device, &pl_ci, NULL, &g.gauss_layout));

    VkGraphicsPipelineCreateInfo gp_ci = {0};
    gp_ci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gp_ci.stageCount = 2;
    gp_ci.pStages = stages;
    gp_ci.pVertexInputState = &vi;
    gp_ci.pInputAssemblyState = &ia;
    gp_ci.pViewportState = &vp;
    gp_ci.pRasterizationState = &rs;
    gp_ci.pMultisampleState = &ms;
    gp_ci.pDepthStencilState = &ds;
    gp_ci.pColorBlendState = &cb;
    gp_ci.layout = g.gauss_layout;
    gp_ci.renderPass = g.render_pass;
    gp_ci.subpass = 0;

    VK_CHECK(vkCreateGraphicsPipelines(g.device, VK_NULL_HANDLE, 1,
                                        &gp_ci, NULL, &g.gauss_pipeline));
}

/* ── Grid gaussian pipeline (O(cells) render from grid moments) ── */

static void render_create_grid_gauss_pipeline(void) {
    VkShaderModuleCreateInfo vert_ci = {0};
    vert_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    vert_ci.codeSize = render_grid_gauss_vert_spv_size;
    vert_ci.pCode = (const uint32_t *)render_grid_gauss_vert_spv;
    VK_CHECK(vkCreateShaderModule(g.device, &vert_ci, NULL, &g.grid_gauss_vert_shader));

    VkPipelineShaderStageCreateInfo stages[2] = {{0},{0}};
    stages[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module = g.grid_gauss_vert_shader;
    stages[0].pName = "main";
    stages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module = g.pts_frag_shader;  /* points frag — no gaussian blur */
    stages[1].pName = "main";

    VkPipelineVertexInputStateCreateInfo vi = {0};
    vi.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    VkPipelineInputAssemblyStateCreateInfo ia = {0};
    ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = VK_PRIMITIVE_TOPOLOGY_POINT_LIST;

    VkViewport viewport = {0};
    viewport.width = (float)g.sc_extent.width;
    viewport.height = (float)g.sc_extent.height;
    viewport.maxDepth = 1.0f;
    VkRect2D scissor = {0};
    scissor.extent = g.sc_extent;
    VkPipelineViewportStateCreateInfo vp = {0};
    vp.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vp.viewportCount = 1; vp.pViewports = &viewport;
    vp.scissorCount = 1; vp.pScissors = &scissor;

    VkPipelineRasterizationStateCreateInfo rs = {0};
    rs.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_NONE;
    rs.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    rs.lineWidth = 1.0f;
    VkPipelineMultisampleStateCreateInfo ms = {0};
    ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    VkPipelineDepthStencilStateCreateInfo ds = {0};
    ds.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    ds.depthTestEnable = VK_TRUE;
    ds.depthWriteEnable = VK_TRUE;
    ds.depthCompareOp = VK_COMPARE_OP_LESS;

    /* Opaque points — no blending, early-Z rejection */
    VkPipelineColorBlendAttachmentState blend_att = {0};
    blend_att.blendEnable = VK_FALSE;
    blend_att.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                               VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
    VkPipelineColorBlendStateCreateInfo cb = {0};
    cb.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    cb.attachmentCount = 1; cb.pAttachments = &blend_att;

    /* 4 SSBOs only — same layout as points pipeline */
    VkDescriptorSetLayoutBinding bindings[4];
    for (int i = 0; i < 4; i++) {
        memset(&bindings[i], 0, sizeof(VkDescriptorSetLayoutBinding));
        bindings[i].binding = i;
        bindings[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        bindings[i].descriptorCount = 1;
        bindings[i].stageFlags = VK_SHADER_STAGE_VERTEX_BIT;
    }

    VkDescriptorSetLayoutCreateInfo dsl_ci = {0};
    dsl_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dsl_ci.bindingCount = 4; dsl_ci.pBindings = bindings;
    VK_CHECK(vkCreateDescriptorSetLayout(g.device, &dsl_ci, NULL, &g.grid_gauss_ds_layout));

    VkDescriptorPoolSize dp_size = {0};
    dp_size.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    dp_size.descriptorCount = 4;
    VkDescriptorPoolCreateInfo dp_ci = {0};
    dp_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dp_ci.maxSets = 1; dp_ci.poolSizeCount = 1; dp_ci.pPoolSizes = &dp_size;
    VK_CHECK(vkCreateDescriptorPool(g.device, &dp_ci, NULL, &g.grid_gauss_ds_pool));

    VkDescriptorSetAllocateInfo ds_ai = {0};
    ds_ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    ds_ai.descriptorPool = g.grid_gauss_ds_pool;
    ds_ai.descriptorSetCount = 1; ds_ai.pSetLayouts = &g.grid_gauss_ds_layout;
    VK_CHECK(vkAllocateDescriptorSets(g.device, &ds_ai, &g.grid_gauss_ds));

    /* Push constants: mat4 + 4 floats = 96 bytes */
    VkPushConstantRange pc_range = {0};
    pc_range.stageFlags = VK_SHADER_STAGE_VERTEX_BIT;
    pc_range.size = 96;

    VkPipelineLayoutCreateInfo pl_ci = {0};
    pl_ci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    pl_ci.setLayoutCount = 1; pl_ci.pSetLayouts = &g.grid_gauss_ds_layout;
    pl_ci.pushConstantRangeCount = 1; pl_ci.pPushConstantRanges = &pc_range;
    VK_CHECK(vkCreatePipelineLayout(g.device, &pl_ci, NULL, &g.grid_gauss_layout));

    VkGraphicsPipelineCreateInfo gp_ci = {0};
    gp_ci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gp_ci.stageCount = 2; gp_ci.pStages = stages;
    gp_ci.pVertexInputState = &vi; gp_ci.pInputAssemblyState = &ia;
    gp_ci.pViewportState = &vp; gp_ci.pRasterizationState = &rs;
    gp_ci.pMultisampleState = &ms; gp_ci.pDepthStencilState = &ds;
    gp_ci.pColorBlendState = &cb;
    gp_ci.layout = g.grid_gauss_layout;
    gp_ci.renderPass = g.render_pass; gp_ci.subpass = 0;

    VK_CHECK(vkCreateGraphicsPipelines(g.device, VK_NULL_HANDLE, 1,
                                        &gp_ci, NULL, &g.grid_gauss_pipeline));
}

/* ── Meshlet shell pipeline ──────────────────────────────────── */

static void render_create_meshlet_pipeline(void) {
    VkShaderModuleCreateInfo vert_ci = {0};
    vert_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    vert_ci.codeSize = render_meshlet_vert_spv_size;
    vert_ci.pCode = (const uint32_t *)render_meshlet_vert_spv;
    VK_CHECK(vkCreateShaderModule(g.device, &vert_ci, NULL, &g.meshlet_vert_shader));

    VkShaderModuleCreateInfo frag_ci = {0};
    frag_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    frag_ci.codeSize = render_meshlet_frag_spv_size;
    frag_ci.pCode = (const uint32_t *)render_meshlet_frag_spv;
    VK_CHECK(vkCreateShaderModule(g.device, &frag_ci, NULL, &g.meshlet_frag_shader));

    VkPipelineShaderStageCreateInfo stages[2] = {{0},{0}};
    stages[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module = g.meshlet_vert_shader;
    stages[0].pName = "main";
    stages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module = g.meshlet_frag_shader;
    stages[1].pName = "main";

    VkPipelineVertexInputStateCreateInfo vi = {0};
    vi.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    VkPipelineInputAssemblyStateCreateInfo ia = {0};
    ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    VkViewport viewport = {0};
    viewport.width = (float)g.sc_extent.width;
    viewport.height = (float)g.sc_extent.height;
    viewport.maxDepth = 1.0f;
    VkRect2D scissor = {0};
    scissor.extent = g.sc_extent;
    VkPipelineViewportStateCreateInfo vp = {0};
    vp.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vp.viewportCount = 1; vp.pViewports = &viewport;
    vp.scissorCount = 1; vp.pScissors = &scissor;

    VkPipelineRasterizationStateCreateInfo rs = {0};
    rs.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_BACK_BIT;
    rs.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    rs.lineWidth = 1.0f;
    VkPipelineMultisampleStateCreateInfo ms = {0};
    ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    VkPipelineDepthStencilStateCreateInfo ds = {0};
    ds.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    ds.depthTestEnable = VK_TRUE;
    ds.depthWriteEnable = VK_TRUE;
    ds.depthCompareOp = VK_COMPARE_OP_LESS;

    /* Opaque shells — no blending, early-Z */
    VkPipelineColorBlendAttachmentState blend_att = {0};
    blend_att.blendEnable = VK_FALSE;
    blend_att.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                               VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
    VkPipelineColorBlendStateCreateInfo cb = {0};
    cb.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    cb.attachmentCount = 1; cb.pAttachments = &blend_att;

    /* 2 SSBOs (binding 0,1) + atlas SSBO (binding 2) + UBO (binding 5) */
    VkDescriptorSetLayoutBinding bindings[4];
    memset(bindings, 0, sizeof(bindings));
    for (int i = 0; i < 3; i++) {
        bindings[i].binding = i;
        bindings[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        bindings[i].descriptorCount = 1;
        bindings[i].stageFlags = (i < 2) ? VK_SHADER_STAGE_VERTEX_BIT
                                         : VK_SHADER_STAGE_FRAGMENT_BIT;
    }
    bindings[3].binding = 5;
    bindings[3].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    bindings[3].descriptorCount = 1;
    bindings[3].stageFlags = VK_SHADER_STAGE_VERTEX_BIT;

    VkDescriptorSetLayoutCreateInfo dsl_ci = {0};
    dsl_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dsl_ci.bindingCount = 4; dsl_ci.pBindings = bindings;
    VK_CHECK(vkCreateDescriptorSetLayout(g.device, &dsl_ci, NULL, &g.meshlet_ds_layout));

    VkDescriptorPoolSize dp_sizes[2] = {{0},{0}};
    dp_sizes[0].type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    dp_sizes[0].descriptorCount = 3;
    dp_sizes[1].type = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    dp_sizes[1].descriptorCount = 1;
    VkDescriptorPoolCreateInfo dp_ci = {0};
    dp_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dp_ci.maxSets = 1; dp_ci.poolSizeCount = 2; dp_ci.pPoolSizes = dp_sizes;
    VK_CHECK(vkCreateDescriptorPool(g.device, &dp_ci, NULL, &g.meshlet_ds_pool));

    VkDescriptorSetAllocateInfo ds_ai = {0};
    ds_ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    ds_ai.descriptorPool = g.meshlet_ds_pool;
    ds_ai.descriptorSetCount = 1; ds_ai.pSetLayouts = &g.meshlet_ds_layout;
    VK_CHECK(vkAllocateDescriptorSets(g.device, &ds_ai, &g.meshlet_ds));

    /* No push constants — uses UBO */
    VkPipelineLayoutCreateInfo pl_ci = {0};
    pl_ci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    pl_ci.setLayoutCount = 1; pl_ci.pSetLayouts = &g.meshlet_ds_layout;
    VK_CHECK(vkCreatePipelineLayout(g.device, &pl_ci, NULL, &g.meshlet_layout));

    VkGraphicsPipelineCreateInfo gp_ci = {0};
    gp_ci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gp_ci.stageCount = 2; gp_ci.pStages = stages;
    gp_ci.pVertexInputState = &vi; gp_ci.pInputAssemblyState = &ia;
    gp_ci.pViewportState = &vp; gp_ci.pRasterizationState = &rs;
    gp_ci.pMultisampleState = &ms; gp_ci.pDepthStencilState = &ds;
    gp_ci.pColorBlendState = &cb;
    gp_ci.layout = g.meshlet_layout;
    gp_ci.renderPass = g.render_pass; gp_ci.subpass = 0;

    VK_CHECK(vkCreateGraphicsPipelines(g.device, VK_NULL_HANDLE, 1,
                                        &gp_ci, NULL, &g.meshlet_pipeline));
}

/* ── ergo_vk_render_grid_gaussians ─────────────────────────── */

void ergo_vk_render_grid_gaussians(ErgoVkBuf buf_grad_x, ErgoVkBuf buf_grad_y,
                                    ErgoVkBuf buf_grad_z, ErgoVkBuf buf_met_gate,
                                    int grid_size, float val_min, float val_max,
                                    float world_scale) {
    if (g.headless) return;

    int n_cells = grid_size * grid_size * grid_size;
    float cell_size = 75.0f;
    float half_gs = (float)grid_size * 0.5f;

    /* Precompute cell center positions + upload to GPU (once) */
    static ErgoVkBuf grid_pos_x = 0, grid_pos_y = 0, grid_pos_z = 0;
    if (!grid_pos_x) {
        size_t sz = n_cells * sizeof(float);
        grid_pos_x = ergo_vk_create_buffer(sz);
        grid_pos_y = ergo_vk_create_buffer(sz);
        grid_pos_z = ergo_vk_create_buffer(sz);
        float *cx = (float *)malloc(sz);
        float *cy = (float *)malloc(sz);
        float *cz = (float *)malloc(sz);
        for (int k = 0; k < grid_size; k++)
            for (int j = 0; j < grid_size; j++)
                for (int i = 0; i < grid_size; i++) {
                    int idx = k * grid_size * grid_size + j * grid_size + i;
                    cx[idx] = ((float)i - half_gs + 0.5f) * cell_size;
                    cy[idx] = ((float)j - half_gs + 0.5f) * cell_size;
                    cz[idx] = ((float)k - half_gs + 0.5f) * cell_size;
                }
        ergo_vk_upload(grid_pos_x, cx, sz);
        ergo_vk_upload(grid_pos_y, cy, sz);
        ergo_vk_upload(grid_pos_z, cz, sz);
        free(cx); free(cy); free(cz);
        fprintf(stderr, "[GRID] Initialized %d cell center positions\n", n_cells);
    }

    /* Use the particle points render with grid cell positions + met_gate as color */
    ergo_vk_render_points(grid_pos_x, grid_pos_y, grid_pos_z, buf_met_gate,
                           n_cells, 3.0f, 0.2f, 1.5f, world_scale);
}

void ergo_vk_render_invalidate(void) {
    pts_ds_bound = 0;
    g.gauss_ds_bound = 0;
    g.grid_gauss_ds_bound = 0;
}

/* ── ergo_vk_render_frame (3D) ───────────────────────────── */

void ergo_vk_render_frame(ErgoVkBuf buf, int width, int height,
                           float val_min, float val_max,
                           float height_scale) {
    if (g.headless) return;

    /* Wait for previous frame */
    VK_CHECK(vkWaitForFences(g.device, 1, &g.render_fence, VK_TRUE, UINT64_MAX));
    VK_CHECK(vkResetFences(g.device, 1, &g.render_fence));

    /* Acquire swapchain image */
    uint32_t img_idx;
    VkResult acq = vkAcquireNextImageKHR(g.device, g.swapchain, UINT64_MAX,
                                          g.sem_available, VK_NULL_HANDLE,
                                          &img_idx);
    if (acq == VK_ERROR_OUT_OF_DATE_KHR) return;

    /* Update descriptor set to point at the sim buffer */
    BufSlot *b = &g.bufs[buf];
    VkDescriptorBufferInfo buf_info = {0};
    buf_info.buffer = b->buffer;
    buf_info.offset = 0;
    buf_info.range = b->size;

    VkWriteDescriptorSet write = {0};
    write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    write.dstSet = g.gfx_ds;
    write.dstBinding = 0;
    write.descriptorCount = 1;
    write.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    write.pBufferInfo = &buf_info;
    vkUpdateDescriptorSets(g.device, 1, &write, 0, NULL);



    /* ── Build camera matrix ── */
    ergo_vk_camera_tick();
    float aspect = (float)g.sc_extent.width / (float)g.sc_extent.height;
    ergo_vk_camera_tick();
    Mat4 proj = mat4_perspective(45.0f * (float)M_PI / 180.0f, aspect, 0.01f, 100.0f);

    float ca = _ergo_cosf(g.cam_azimuth), sa = _ergo_sinf(g.cam_azimuth);
    float ce = _ergo_cosf(g.cam_elevation), se = _ergo_sinf(g.cam_elevation);
    float ex = g.cam_distance * ce * sa;
    float ey = g.cam_distance * se;
    float ez = g.cam_distance * ce * ca;
    Mat4 view = mat4_look_at(ex, ey, ez, 0, 0, 0, 0, 1, 0);
    Mat4 viewProj = mat4_mul(proj, view);

    /* ── Push constant block (must match shader layout) ── */
    struct {
        float viewProj[16]; /* mat4  */
        int   grid_w;       /* int   */
        int   grid_h;       /* int   */
        float val_min;      /* float */
        float val_max;      /* float */
        float height_scale; /* float */
    } pc;
    memcpy(pc.viewProj, viewProj.m, 64);
    pc.grid_w = width;
    pc.grid_h = height;
    pc.val_min = val_min;
    pc.val_max = val_max;
    pc.height_scale = height_scale;

    /* Record command buffer */
    VkCommandBufferBeginInfo begin_info = {0};
    begin_info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin_info.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;

    /* Wait for any in-flight compute to finish before rendering */
    VK_CHECK(vkWaitForFences(g.device, 1, &g.fence, VK_TRUE, UINT64_MAX));

    VK_CHECK(vkResetCommandBuffer(g.render_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.render_cmd_buf, &begin_info));

    VkClearValue clears[2];
    clears[0].color = (VkClearColorValue){{0.0f, 0.0f, 0.0f, 1.0f}};
    clears[1].depthStencil = (VkClearDepthStencilValue){1.0f, 0};

    VkRenderPassBeginInfo rp_begin = {0};
    rp_begin.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rp_begin.renderPass = g.render_pass;
    rp_begin.framebuffer = g.sc_fbs[img_idx];
    rp_begin.renderArea.extent = g.sc_extent;
    rp_begin.clearValueCount = 2;
    rp_begin.pClearValues = clears;

    vkCmdBeginRenderPass(g.render_cmd_buf, &rp_begin, VK_SUBPASS_CONTENTS_INLINE);

    vkCmdBindPipeline(g.render_cmd_buf, VK_PIPELINE_BIND_POINT_GRAPHICS,
                      g.gfx_pipeline);
    vkCmdBindDescriptorSets(g.render_cmd_buf, VK_PIPELINE_BIND_POINT_GRAPHICS,
                            g.gfx_layout, 0, 1, &g.gfx_ds, 0, NULL);

    vkCmdPushConstants(g.render_cmd_buf, g.gfx_layout,
                       VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
                       0, sizeof(pc), &pc);

    /* Draw: (grid_w - 1) * (grid_h - 1) cells, 6 vertices per cell */
    int n_cells = (width - 1) * (height - 1);
    vkCmdDraw(g.render_cmd_buf, n_cells * 6, 1, 0, 0);

    vkCmdEndRenderPass(g.render_cmd_buf);
    VK_CHECK(vkEndCommandBuffer(g.render_cmd_buf));

    /* Submit with semaphore synchronization */
    VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.waitSemaphoreCount = 1;
    si.pWaitSemaphores = &g.sem_available;
    si.pWaitDstStageMask = &wait_stage;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.render_cmd_buf;
    si.signalSemaphoreCount = 1;
    si.pSignalSemaphores = &g.sem_finished;

    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.render_fence));

    /* Present */
    VkPresentInfoKHR present = {0};
    present.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    present.waitSemaphoreCount = 1;
    present.pWaitSemaphores = &g.sem_finished;
    present.swapchainCount = 1;
    present.pSwapchains = &g.swapchain;
    present.pImageIndices = &img_idx;

    vkQueuePresentKHR(g.compute_queue, &present);
}

/* ── ergo_vk_render_points (particle cloud) ─────────────── */

void ergo_vk_set_render_offset(size_t byte_offset) {
    g.render_offset = byte_offset;
}

void ergo_vk_render_points(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                            ErgoVkBuf buf_color, int n_points,
                            float point_size, float val_min, float val_max,
                            float world_scale) {
    if (g.headless) return;

    /* Wait for previous render to finish before reusing command buffer */
    VK_CHECK(vkWaitForFences(g.device, 1, &g.render_fence, VK_TRUE, UINT64_MAX));
    VK_CHECK(vkResetFences(g.device, 1, &g.render_fence));

    /* Acquire swapchain image */
    uint32_t img_idx;
    VkResult acq = vkAcquireNextImageKHR(g.device, g.swapchain, UINT64_MAX,
                                          g.sem_available, VK_NULL_HANDLE,
                                          &img_idx);
    if (acq == VK_ERROR_OUT_OF_DATE_KHR) return;

    /* Bind 4 SoA buffers — rebind after sort pointer swaps */
    if (!pts_ds_bound) {
        ErgoVkBuf bufs_arr[4] = { buf_x, buf_y, buf_z, buf_color };
        VkDescriptorBufferInfo buf_infos[4];
        VkWriteDescriptorSet writes[4];
        for (int i = 0; i < 4; i++) {
            BufSlot *b = &g.bufs[bufs_arr[i]];
            buf_infos[i].buffer = b->buffer;
            buf_infos[i].offset = g.render_offset;
            buf_infos[i].range = b->size - g.render_offset;

            memset(&writes[i], 0, sizeof(VkWriteDescriptorSet));
            writes[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            writes[i].dstSet = g.pts_ds;
            writes[i].dstBinding = i;
            writes[i].descriptorCount = 1;
            writes[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            writes[i].pBufferInfo = &buf_infos[i];
        }
        vkUpdateDescriptorSets(g.device, 4, writes, 0, NULL);
        pts_ds_bound = 1;
    }

    /* Build camera matrix */
    float aspect = (float)g.sc_extent.width / (float)g.sc_extent.height;
    ergo_vk_camera_tick();
    Mat4 proj = mat4_perspective(45.0f * (float)M_PI / 180.0f, aspect, 0.01f, 100.0f);

    float ca = _ergo_cosf(g.cam_azimuth), sa = _ergo_sinf(g.cam_azimuth);
    float ce = _ergo_cosf(g.cam_elevation), se = _ergo_sinf(g.cam_elevation);
    float ex = g.cam_distance * ce * sa;
    float ey = g.cam_distance * se;
    float ez = g.cam_distance * ce * ca;
    Mat4 view = mat4_look_at(ex, ey, ez, 0, 0, 0, 0, 1, 0);
    Mat4 viewProj = mat4_mul(proj, view);

    /* Push constants — must match render_points.vert PC layout (96 bytes) */
    struct {
        float viewProj[16];
        float point_size;
        float val_min;
        float val_max;
        float world_scale;
        float cam_x;
        float cam_y;
        float cam_z;
        float cull_mode;
    } pc;
    memcpy(pc.viewProj, viewProj.m, 64);
    pc.point_size = point_size;
    pc.val_min = val_min;
    pc.val_max = val_max;
    pc.world_scale = world_scale;
    pc.cam_x = ex;
    pc.cam_y = ey;
    pc.cam_z = ez;
    pc.cull_mode = g_culling_enabled ? 1.0f : 0.0f;

    /* Record command buffer */
    VkCommandBufferBeginInfo begin_info = {0};
    begin_info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin_info.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;

    VK_CHECK(vkResetCommandBuffer(g.render_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.render_cmd_buf, &begin_info));

    /* Barrier: compute shader writes → vertex shader reads */
    {
        VkMemoryBarrier mb = {0};
        mb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
        vkCmdPipelineBarrier(g.render_cmd_buf,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            VK_PIPELINE_STAGE_VERTEX_SHADER_BIT,
            0, 1, &mb, 0, NULL, 0, NULL);
    }

    VkClearValue clears[2];
    clears[0].color = (VkClearColorValue){{0.0f, 0.0f, 0.0f, 1.0f}};
    clears[1].depthStencil = (VkClearDepthStencilValue){1.0f, 0};

    VkRenderPassBeginInfo rp_begin = {0};
    rp_begin.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rp_begin.renderPass = g.render_pass;
    rp_begin.framebuffer = g.sc_fbs[img_idx];
    rp_begin.renderArea.extent = g.sc_extent;
    rp_begin.clearValueCount = 2;
    rp_begin.pClearValues = clears;

    vkCmdBeginRenderPass(g.render_cmd_buf, &rp_begin, VK_SUBPASS_CONTENTS_INLINE);

    vkCmdBindPipeline(g.render_cmd_buf, VK_PIPELINE_BIND_POINT_GRAPHICS,
                      g.pts_pipeline);
    vkCmdBindDescriptorSets(g.render_cmd_buf, VK_PIPELINE_BIND_POINT_GRAPHICS,
                            g.pts_layout, 0, 1, &g.pts_ds, 0, NULL);

    vkCmdPushConstants(g.render_cmd_buf, g.pts_layout,
                       VK_SHADER_STAGE_VERTEX_BIT,
                       0, sizeof(pc), &pc);

    vkCmdDraw(g.render_cmd_buf, n_points, 1, 0, 0);

    vkCmdEndRenderPass(g.render_cmd_buf);
    VK_CHECK(vkEndCommandBuffer(g.render_cmd_buf));

    /* Submit */
    VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.waitSemaphoreCount = 1;
    si.pWaitSemaphores = &g.sem_available;
    si.pWaitDstStageMask = &wait_stage;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.render_cmd_buf;
    si.signalSemaphoreCount = 1;
    si.pSignalSemaphores = &g.sem_finished;

    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.render_fence));

    /* Present */
    VkPresentInfoKHR present = {0};
    present.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    present.waitSemaphoreCount = 1;
    present.pWaitSemaphores = &g.sem_finished;
    present.swapchainCount = 1;
    present.pSwapchains = &g.swapchain;
    present.pImageIndices = &img_idx;

    vkQueuePresentKHR(g.compute_queue, &present);
}

/* ── ergo_vk_render_gaussians ──────────────────────────────── */

void ergo_vk_render_gaussians(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                               ErgoVkBuf buf_color, int n_points,
                               float point_size, float val_min, float val_max,
                               float world_scale) {
    if (g.headless) return;

    VK_CHECK(vkWaitForFences(g.device, 1, &g.render_fence, VK_TRUE, UINT64_MAX));
    VK_CHECK(vkResetFences(g.device, 1, &g.render_fence));

    uint32_t img_idx;
    VkResult acq = vkAcquireNextImageKHR(g.device, g.swapchain, UINT64_MAX,
                                          g.sem_available, VK_NULL_HANDLE,
                                          &img_idx);
    if (acq == VK_ERROR_OUT_OF_DATE_KHR) return;

    /* Bind 4 SoA buffers */
    if (!g.gauss_ds_bound) {
        ErgoVkBuf bufs_arr[4] = { buf_x, buf_y, buf_z, buf_color };
        VkDescriptorBufferInfo buf_infos[4];
        VkWriteDescriptorSet writes[4];
        for (int i = 0; i < 4; i++) {
            BufSlot *b = &g.bufs[bufs_arr[i]];
            buf_infos[i].buffer = b->buffer;
            buf_infos[i].offset = g.render_offset;
            buf_infos[i].range = b->size - g.render_offset;

            memset(&writes[i], 0, sizeof(VkWriteDescriptorSet));
            writes[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            writes[i].dstSet = g.gauss_ds;
            writes[i].dstBinding = i;
            writes[i].descriptorCount = 1;
            writes[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            writes[i].pBufferInfo = &buf_infos[i];
        }
        vkUpdateDescriptorSets(g.device, 4, writes, 0, NULL);
        g.gauss_ds_bound = 1;
    }

    /* Camera */
    float aspect = (float)g.sc_extent.width / (float)g.sc_extent.height;
    ergo_vk_camera_tick();
    Mat4 proj = mat4_perspective(45.0f * 3.14159265f / 180.0f, aspect,
                                 0.01f, 100.0f);
    float ca = _ergo_cosf(g.cam_azimuth), sa = _ergo_sinf(g.cam_azimuth);
    float ce = _ergo_cosf(g.cam_elevation), se = _ergo_sinf(g.cam_elevation);
    float ex = g.cam_distance * ce * sa;
    float ey = g.cam_distance * se;
    float ez = g.cam_distance * ce * ca;
    Mat4 view = mat4_look_at(ex, ey, ez, 0, 0, 0, 0, 1, 0);
    Mat4 viewProj = mat4_mul(proj, view);

    /* Push constants — must match render_gauss.vert PC layout (96 bytes) */
    struct {
        float viewProj[16];
        float point_size;
        float val_min;
        float val_max;
        float world_scale;
        float cam_x;
        float cam_y;
        float cam_z;
        float cull_mode;
    } pc;
    memcpy(pc.viewProj, viewProj.m, 64);
    pc.point_size = point_size;
    pc.val_min = val_min;
    pc.val_max = val_max;
    pc.world_scale = world_scale;
    pc.cam_x = ex;
    pc.cam_y = ey;
    pc.cam_z = ez;
    pc.cull_mode = g_culling_enabled ? 1.0f : 0.0f;

    VkCommandBufferBeginInfo begin_info = {0};
    begin_info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin_info.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;

    VK_CHECK(vkResetCommandBuffer(g.render_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.render_cmd_buf, &begin_info));

    if (g.cmd_buf) {
        VkMemoryBarrier mb = {0};
        mb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
        vkCmdPipelineBarrier(g.render_cmd_buf,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            VK_PIPELINE_STAGE_VERTEX_SHADER_BIT,
            0, 1, &mb, 0, NULL, 0, NULL);
    }

    VkClearValue clears[2];
    clears[0].color = (VkClearColorValue){{0.0f, 0.0f, 0.0f, 1.0f}};
    clears[1].depthStencil = (VkClearDepthStencilValue){1.0f, 0};

    VkRenderPassBeginInfo rp_begin = {0};
    rp_begin.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rp_begin.renderPass = g.render_pass;
    rp_begin.framebuffer = g.sc_fbs[img_idx];
    rp_begin.renderArea.extent = g.sc_extent;
    rp_begin.clearValueCount = 2;
    rp_begin.pClearValues = clears;

    vkCmdBeginRenderPass(g.render_cmd_buf, &rp_begin, VK_SUBPASS_CONTENTS_INLINE);

    vkCmdBindPipeline(g.render_cmd_buf, VK_PIPELINE_BIND_POINT_GRAPHICS,
                      g.gauss_pipeline);
    vkCmdBindDescriptorSets(g.render_cmd_buf, VK_PIPELINE_BIND_POINT_GRAPHICS,
                            g.gauss_layout, 0, 1, &g.gauss_ds, 0, NULL);

    vkCmdPushConstants(g.render_cmd_buf, g.gauss_layout,
                       VK_SHADER_STAGE_VERTEX_BIT,
                       0, sizeof(pc), &pc);

    /* Instanced draw: 6 vertices per quad, n_points instances */
    vkCmdDraw(g.render_cmd_buf, 6, n_points, 0, 0);

    vkCmdEndRenderPass(g.render_cmd_buf);
    VK_CHECK(vkEndCommandBuffer(g.render_cmd_buf));

    VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.waitSemaphoreCount = 1;
    si.pWaitSemaphores = &g.sem_available;
    si.pWaitDstStageMask = &wait_stage;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.render_cmd_buf;
    si.signalSemaphoreCount = 1;
    si.pSignalSemaphores = &g.sem_finished;

    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.render_fence));

    VkPresentInfoKHR present = {0};
    present.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    present.waitSemaphoreCount = 1;
    present.pWaitSemaphores = &g.sem_finished;
    present.swapchainCount = 1;
    present.pSwapchains = &g.swapchain;
    present.pImageIndices = &img_idx;

    vkQueuePresentKHR(g.compute_queue, &present);
}

/* (removed duplicate — actual octa section follows) */
#if 0  /* duplicate octa section removed */
static void _octa_old_removed_(void) {
    if (g.octa_initialized) return;

    /* Color image — single 2D texture */
    VkImageCreateInfo img_ci = {0};
    img_ci.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    img_ci.imageType = VK_IMAGE_TYPE_2D;
    img_ci.format = VK_FORMAT_R8G8B8A8_UNORM;
    img_ci.extent = (VkExtent3D){OCTA_SIZE, OCTA_SIZE, 1};
    img_ci.mipLevels = 1;
    img_ci.arrayLayers = 1;
    img_ci.samples = VK_SAMPLE_COUNT_1_BIT;
    img_ci.tiling = VK_IMAGE_TILING_OPTIMAL;
    img_ci.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
    img_ci.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    VK_CHECK(vkCreateImage(g.device, &img_ci, NULL, &g.octa_image));

    VkMemoryRequirements mem_req;
    vkGetImageMemoryRequirements(g.device, g.octa_image, &mem_req);
    VkMemoryAllocateInfo mem_ai = {0};
    mem_ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    mem_ai.allocationSize = mem_req.size;
    mem_ai.memoryTypeIndex = find_memory_type(mem_req.memoryTypeBits,
        VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    VK_CHECK(vkAllocateMemory(g.device, &mem_ai, NULL, &g.octa_memory));
    VK_CHECK(vkBindImageMemory(g.device, g.octa_image, g.octa_memory, 0));

    VkImageViewCreateInfo iv_ci = {0};
    iv_ci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    iv_ci.image = g.octa_image;
    iv_ci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    iv_ci.format = VK_FORMAT_R8G8B8A8_UNORM;
    iv_ci.subresourceRange = (VkImageSubresourceRange){
        VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    VK_CHECK(vkCreateImageView(g.device, &iv_ci, NULL, &g.octa_view));

    VkSamplerCreateInfo samp_ci = {0};
    samp_ci.sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
    samp_ci.magFilter = VK_FILTER_LINEAR;
    samp_ci.minFilter = VK_FILTER_LINEAR;
    samp_ci.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    samp_ci.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    VK_CHECK(vkCreateSampler(g.device, &samp_ci, NULL, &g.octa_sampler));

    /* Depth */
    VkImageCreateInfo depth_ci = {0};
    depth_ci.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    depth_ci.imageType = VK_IMAGE_TYPE_2D;
    depth_ci.format = VK_FORMAT_D32_SFLOAT;
    depth_ci.extent = (VkExtent3D){OCTA_SIZE, OCTA_SIZE, 1};
    depth_ci.mipLevels = 1;
    depth_ci.arrayLayers = 1;
    depth_ci.samples = VK_SAMPLE_COUNT_1_BIT;
    depth_ci.tiling = VK_IMAGE_TILING_OPTIMAL;
    depth_ci.usage = VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT;
    VK_CHECK(vkCreateImage(g.device, &depth_ci, NULL, &g.octa_depth));

    vkGetImageMemoryRequirements(g.device, g.octa_depth, &mem_req);
    mem_ai.allocationSize = mem_req.size;
    mem_ai.memoryTypeIndex = find_memory_type(mem_req.memoryTypeBits,
        VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    VK_CHECK(vkAllocateMemory(g.device, &mem_ai, NULL, &g.octa_depth_mem));
    VK_CHECK(vkBindImageMemory(g.device, g.octa_depth, g.octa_depth_mem, 0));

    VkImageViewCreateInfo dv_ci = {0};
    dv_ci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    dv_ci.image = g.octa_depth;
    dv_ci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    dv_ci.format = VK_FORMAT_D32_SFLOAT;
    dv_ci.subresourceRange = (VkImageSubresourceRange){
        VK_IMAGE_ASPECT_DEPTH_BIT, 0, 1, 0, 1};
    VK_CHECK(vkCreateImageView(g.device, &dv_ci, NULL, &g.octa_depth_view));

    /* Render pass */
    VkAttachmentDescription atts[2] = {{0},{0}};
    atts[0].format = VK_FORMAT_R8G8B8A8_UNORM;
    atts[0].samples = VK_SAMPLE_COUNT_1_BIT;
    atts[0].loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    atts[0].storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    atts[0].initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    atts[0].finalLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    atts[1].format = VK_FORMAT_D32_SFLOAT;
    atts[1].samples = VK_SAMPLE_COUNT_1_BIT;
    atts[1].loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    atts[1].storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    atts[1].initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    atts[1].finalLayout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    VkAttachmentReference color_ref = {0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};
    VkAttachmentReference depth_ref = {1, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL};
    VkSubpassDescription subpass = {0};
    subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1;
    subpass.pColorAttachments = &color_ref;
    subpass.pDepthStencilAttachment = &depth_ref;

    VkRenderPassCreateInfo rp_ci = {0};
    rp_ci.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    rp_ci.attachmentCount = 2;
    rp_ci.pAttachments = atts;
    rp_ci.subpassCount = 1;
    rp_ci.pSubpasses = &subpass;
    VK_CHECK(vkCreateRenderPass(g.device, &rp_ci, NULL, &g.octa_render_pass));

    /* Framebuffer */
    VkImageView fb_atts[2] = {g.octa_view, g.octa_depth_view};
    VkFramebufferCreateInfo fb_ci = {0};
    fb_ci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
    fb_ci.renderPass = g.octa_render_pass;
    fb_ci.attachmentCount = 2;
    fb_ci.pAttachments = fb_atts;
    fb_ci.width = OCTA_SIZE;
    fb_ci.height = OCTA_SIZE;
    fb_ci.layers = 1;
    VK_CHECK(vkCreateFramebuffer(g.device, &fb_ci, NULL, &g.octa_fb));

    /* Octahedral point pipeline — uses octa vertex shader */
    {
        VkShaderModuleCreateInfo vert_ci = {0};
        vert_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        vert_ci.codeSize = render_octa_points_vert_spv_size;
        vert_ci.pCode = (const uint32_t *)render_octa_points_vert_spv;
        VK_CHECK(vkCreateShaderModule(g.device, &vert_ci, NULL, &g.octa_vert_shader));

        VkPipelineShaderStageCreateInfo stages[2] = {{0},{0}};
        stages[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
        stages[0].module = g.octa_vert_shader;
        stages[0].pName = "main";
        stages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
        stages[1].module = g.pts_frag_shader;  /* same heat palette frag */
        stages[1].pName = "main";

        VkPipelineVertexInputStateCreateInfo vi = {0};
        vi.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
        VkPipelineInputAssemblyStateCreateInfo ia = {0};
        ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
        ia.topology = VK_PRIMITIVE_TOPOLOGY_POINT_LIST;

        VkViewport viewport = {0, 0, OCTA_SIZE, OCTA_SIZE, 0, 1};
        VkRect2D scissor = {{0,0}, {OCTA_SIZE, OCTA_SIZE}};
        VkPipelineViewportStateCreateInfo vp = {0};
        vp.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
        vp.viewportCount = 1; vp.pViewports = &viewport;
        vp.scissorCount = 1; vp.pScissors = &scissor;

        VkPipelineRasterizationStateCreateInfo rs = {0};
        rs.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
        rs.polygonMode = VK_POLYGON_MODE_FILL;
        rs.cullMode = VK_CULL_MODE_NONE;
        rs.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
        rs.lineWidth = 1.0f;
        VkPipelineMultisampleStateCreateInfo ms = {0};
        ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
        ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

        VkPipelineDepthStencilStateCreateInfo ds = {0};
        ds.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
        ds.depthTestEnable = VK_TRUE;
        ds.depthWriteEnable = VK_TRUE;
        ds.depthCompareOp = VK_COMPARE_OP_LESS;

        VkPipelineColorBlendAttachmentState blend_att = {0};
        blend_att.blendEnable = VK_FALSE;
        blend_att.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                                   VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
        VkPipelineColorBlendStateCreateInfo cb = {0};
        cb.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
        cb.attachmentCount = 1; cb.pAttachments = &blend_att;

        VkGraphicsPipelineCreateInfo gp_ci = {0};
        gp_ci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
        gp_ci.stageCount = 2; gp_ci.pStages = stages;
        gp_ci.pVertexInputState = &vi; gp_ci.pInputAssemblyState = &ia;
        gp_ci.pViewportState = &vp; gp_ci.pRasterizationState = &rs;
        gp_ci.pMultisampleState = &ms; gp_ci.pDepthStencilState = &ds;
        gp_ci.pColorBlendState = &cb;
        gp_ci.layout = g.pts_layout;
        gp_ci.renderPass = g.octa_render_pass;
        gp_ci.subpass = 0;

        VK_CHECK(vkCreateGraphicsPipelines(g.device, VK_NULL_HANDLE, 1,
                                            &gp_ci, NULL, &g.octa_pts_pipeline));
    }

    g.octa_initialized = 1;
    fprintf(stderr, "[ergo_vk] Octahedral map initialized: %dx%d\n",
            OCTA_SIZE, OCTA_SIZE);
}

/* Render points into octahedral map — single pass, single submit */
static void octa_render_points(int n_points, float val_min, float val_max,
                                float world_scale) {
    /* UBO — octa vertex shader reads it but doesn't use viewProj
     * (it projects manually via octahedral mapping) */
    struct {
        float viewProj[16];
        float cam_x, cam_y, cam_z;
        float cull_mode;
        float val_min, val_max;
        float world_scale;
        float pad;
    } ubo;
    memset(ubo.viewProj, 0, 64);  /* unused */
    ubo.cam_x = ubo.cam_y = ubo.cam_z = 0.0f;
    ubo.cull_mode = 0.0f;
    ubo.val_min = val_min;
    ubo.val_max = val_max;
    ubo.world_scale = world_scale;
    ubo.pad = 0.0f;
    memcpy(g.render_ubo_mapped, &ubo, 96);

    /* Bind UBO to pts_ds at binding 5 */
    {
        VkDescriptorBufferInfo ubo_info = {0};
        ubo_info.buffer = g.render_ubo;
        ubo_info.offset = 0;
        ubo_info.range = 96;

        VkWriteDescriptorSet write = {0};
        write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        write.dstSet = g.pts_ds;
        write.dstBinding = 5;
        write.descriptorCount = 1;
        write.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
        write.pBufferInfo = &ubo_info;
        vkUpdateDescriptorSets(g.device, 1, &write, 0, NULL);
    }

    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkResetCommandBuffer(g.xfer_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.xfer_cmd_buf, &begin));

    /* Barrier: compute writes -> vertex reads */
    {
        VkMemoryBarrier mb = {0};
        mb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
        vkCmdPipelineBarrier(g.xfer_cmd_buf,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            VK_PIPELINE_STAGE_VERTEX_SHADER_BIT,
            0, 1, &mb, 0, NULL, 0, NULL);
    }

    VkClearValue clears[2];
    clears[0].color = (VkClearColorValue){{0.0f, 0.0f, 0.0f, 0.0f}};
    clears[1].depthStencil = (VkClearDepthStencilValue){1.0f, 0};

    VkRenderPassBeginInfo rp_begin = {0};
    rp_begin.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rp_begin.renderPass = g.octa_render_pass;
    rp_begin.framebuffer = g.octa_fb;
    rp_begin.renderArea.extent = (VkExtent2D){OCTA_SIZE, OCTA_SIZE};
    rp_begin.clearValueCount = 2;
    rp_begin.pClearValues = clears;

    vkCmdBeginRenderPass(g.xfer_cmd_buf, &rp_begin, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdBindPipeline(g.xfer_cmd_buf, VK_PIPELINE_BIND_POINT_GRAPHICS,
                      g.octa_pts_pipeline);
    vkCmdBindDescriptorSets(g.xfer_cmd_buf, VK_PIPELINE_BIND_POINT_GRAPHICS,
                            g.pts_layout, 0, 1, &g.pts_ds, 0, NULL);
    vkCmdDraw(g.xfer_cmd_buf, n_points, 1, 0, 0);
    vkCmdEndRenderPass(g.xfer_cmd_buf);

    VK_CHECK(vkEndCommandBuffer(g.xfer_cmd_buf));

    VK_CHECK(vkResetFences(g.device, 1, &g.xfer_fence));
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.xfer_cmd_buf;
    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.xfer_fence));
    VK_CHECK(vkWaitForFences(g.device, 1, &g.xfer_fence, VK_TRUE, UINT64_MAX));
}
#endif /* end duplicate octa section */

/* ── Per-cell octahedral atlas ──────────────────────────── */

#define TILE_SIZE 64
#define ATLAS_W (128 * TILE_SIZE)   /* 8192 */
#define ATLAS_H (256 * TILE_SIZE)   /* 16384 */

static ErgoVkPipe g_atlas_gen_pipe;
static ErgoVkBuf  g_atlas_ssbo;  /* 2048*4096 uint32 = 32MB */

static void atlas_lazy_init(void) {
    if (g.atlas_initialized) return;

    /* Atlas SSBO: 2048 * 4096 * 4 bytes = 32MB */
    size_t atlas_size = (size_t)ATLAS_W * ATLAS_H * sizeof(uint32_t);
    g_atlas_ssbo = ergo_vk_create_buffer(atlas_size);

    /* Load atlas gen compute shader: 5 SSBOs (4 particle + 1 atlas) + 32B push constants */
    g_atlas_gen_pipe = ergo_vk_load_shader(
        atlas_gen_comp_spv, atlas_gen_comp_spv_size, 5, 32);
    /* Binding 4 is bound once here and never per-frame, so seed both
     * frame-slot sets (safe: the pipeline was just created — nothing
     * references its sets yet). */
    vk_bind_buf_all_slots(&g.pipes[g_atlas_gen_pipe], 4,
                          g.bufs[g_atlas_ssbo].buffer,
                          g.bufs[g_atlas_ssbo].size);

    /* No image transitions needed — pure SSBO path */
    {
    }

    g.atlas_initialized = 1;
    fprintf(stderr, "[ergo_vk] Atlas initialized: %dx%d (%d tiles of %dx%d)\n",
            ATLAS_W, ATLAS_H, 32*32*32, TILE_SIZE, TILE_SIZE);
}

/* Dispatch atlas generation: clear SSBO, scatter particles into tiles */
static void atlas_gen_dispatch(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                                ErgoVkBuf buf_color, int n_points,
                                float val_min, float val_max) {
    /* Bind particle SSBOs (atlas SSBO already bound at init) */
    ergo_vk_bind_buffer(g_atlas_gen_pipe, 0, buf_x);
    ergo_vk_bind_buffer(g_atlas_gen_pipe, 1, buf_y);
    ergo_vk_bind_buffer(g_atlas_gen_pipe, 2, buf_z);
    ergo_vk_bind_buffer(g_atlas_gen_pipe, 3, buf_color);

    struct {
        int   n_points;
        int   grid_size;
        float cell_size;
        float val_min;
        float val_max;
        float pad1, pad2, pad3;
    } pc;
    pc.n_points = n_points;
    pc.grid_size = 32;
    pc.cell_size = 75.0f;
    pc.val_min = val_min;
    pc.val_max = val_max;
    pc.pad1 = pc.pad2 = pc.pad3 = 0.0f;
    ergo_vk_push_constants(g_atlas_gen_pipe, &pc, 32);

    PipeSlot *p = &g.pipes[g_atlas_gen_pipe];

    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkResetCommandBuffer(g.xfer_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.xfer_cmd_buf, &begin));

    /* Clear atlas SSBO to zero */
    BufSlot *ab = &g.bufs[g_atlas_ssbo];
    vkCmdFillBuffer(g.xfer_cmd_buf, ab->buffer, 0, ab->size, 0);

    /* Barrier: fill -> compute write */
    {
        VkMemoryBarrier mb = {0};
        mb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        mb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        mb.dstAccessMask = VK_ACCESS_SHADER_WRITE_BIT | VK_ACCESS_SHADER_READ_BIT;
        vkCmdPipelineBarrier(g.xfer_cmd_buf,
            VK_PIPELINE_STAGE_TRANSFER_BIT,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            0, 1, &mb, 0, NULL, 0, NULL);
    }

    /* Dispatch atlas gen: one thread per particle */
    vkCmdBindPipeline(g.xfer_cmd_buf, VK_PIPELINE_BIND_POINT_COMPUTE, p->pipeline);
    vkCmdBindDescriptorSets(g.xfer_cmd_buf, VK_PIPELINE_BIND_POINT_COMPUTE,
                            p->layout, 0, 1, &p->ds[g.cmd_idx], 0, NULL);
    if (p->pc_size > 0)
        vkCmdPushConstants(g.xfer_cmd_buf, p->layout,
                           VK_SHADER_STAGE_COMPUTE_BIT, 0, p->pc_size, p->pc_data);
    vkCmdDispatch(g.xfer_cmd_buf, (n_points + 255) / 256, 1, 1);

    VK_CHECK(vkEndCommandBuffer(g.xfer_cmd_buf));

    VK_CHECK(vkResetFences(g.device, 1, &g.xfer_fence));
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.xfer_cmd_buf;
    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.xfer_fence));
    VK_CHECK(vkWaitForFences(g.device, 1, &g.xfer_fence, VK_TRUE, UINT64_MAX));
}

/* ── ergo_vk_render_meshlets (shell-based O(cells) render) ── */

/* Icosphere template: 1-subdivision icosahedron → 42 verts, 80 faces */
#define ICO_NVERTS 42
#define ICO_NFACES 80
#define ICO_NIDX   (ICO_NFACES * 3)
#define ICO_NVERTS_EXPANDED ICO_NIDX
#define MESHLET_MAX 32768
#define MESHLET_COUNTER_SIZE 20

static int              g_meshlet_initialized = 0;
static ErgoVkPipe       g_meshlet_compute_pipe;
static ErgoVkBuf        g_meshlet_tmpl_pos;
static ErgoVkBuf        g_meshlet_tmpl_idx;
static ErgoVkBuf        g_meshlet_out_pos[2];   /* double-buffered */
static ErgoVkBuf        g_meshlet_out_nv[2];    /* double-buffered */
static int              g_meshlet_write_idx = 0; /* compute writes to this, render reads other */
static VkBuffer         g_meshlet_counter_buf;
static VkDeviceMemory   g_meshlet_counter_mem;
static void            *g_meshlet_counter_mapped;

static void icosphere_generate(float *out_pos, uint32_t *out_idx) {
    const float phi = 1.6180339887f;
    const float inv_len = 1.0f / sqrtf(1.0f + phi * phi);
    const float a = inv_len;
    const float b = phi * inv_len;

    float base[12][3] = {
        {-a,  b,  0}, { a,  b,  0}, {-a, -b,  0}, { a, -b,  0},
        { 0, -a,  b}, { 0,  a,  b}, { 0, -a, -b}, { 0,  a, -b},
        { b,  0, -a}, { b,  0,  a}, {-b,  0, -a}, {-b,  0,  a}
    };

    int base_tri[20][3] = {
        {0,11,5},  {0,5,1},   {0,1,7},   {0,7,10},  {0,10,11},
        {1,5,9},   {5,11,4},  {11,10,2},  {10,7,6},  {7,1,8},
        {3,9,4},   {3,4,2},   {3,2,6},   {3,6,8},   {3,8,9},
        {4,9,5},   {2,4,11},  {6,2,10},  {8,6,7},   {9,8,1}
    };

    int nverts = 12;
    float verts[ICO_NVERTS][3];
    for (int i = 0; i < 12; i++) {
        verts[i][0] = base[i][0];
        verts[i][1] = base[i][1];
        verts[i][2] = base[i][2];
    }

    int mid_cache[64 * 64];
    memset(mid_cache, -1, sizeof(mid_cache));

    int nfaces = 0;
    int tris[ICO_NFACES][3];

    for (int f = 0; f < 20; f++) {
        int v0 = base_tri[f][0], v1 = base_tri[f][1], v2 = base_tri[f][2];

        /* Midpoint helper — inline to avoid macro issues */
        int edges[3][2] = {{v0,v1}, {v1,v2}, {v2,v0}};
        int mids[3];
        for (int e = 0; e < 3; e++) {
            int lo = edges[e][0] < edges[e][1] ? edges[e][0] : edges[e][1];
            int hi = edges[e][0] < edges[e][1] ? edges[e][1] : edges[e][0];
            int key = lo * 64 + hi;
            if (mid_cache[key] < 0) {
                int m = nverts++;
                verts[m][0] = (verts[lo][0] + verts[hi][0]) * 0.5f;
                verts[m][1] = (verts[lo][1] + verts[hi][1]) * 0.5f;
                verts[m][2] = (verts[lo][2] + verts[hi][2]) * 0.5f;
                float len = sqrtf(verts[m][0]*verts[m][0] +
                                  verts[m][1]*verts[m][1] +
                                  verts[m][2]*verts[m][2]);
                verts[m][0] /= len;
                verts[m][1] /= len;
                verts[m][2] /= len;
                mid_cache[key] = m;
            }
            mids[e] = mid_cache[key];
        }
        int ma = mids[0], mb = mids[1], mc = mids[2];
        tris[nfaces][0] = v0; tris[nfaces][1] = ma; tris[nfaces][2] = mc; nfaces++;
        tris[nfaces][0] = ma; tris[nfaces][1] = v1; tris[nfaces][2] = mb; nfaces++;
        tris[nfaces][0] = mc; tris[nfaces][1] = mb; tris[nfaces][2] = v2; nfaces++;
        tris[nfaces][0] = ma; tris[nfaces][1] = mb; tris[nfaces][2] = mc; nfaces++;
    }

    for (int i = 0; i < nverts; i++) {
        out_pos[i * 4 + 0] = verts[i][0];
        out_pos[i * 4 + 1] = verts[i][1];
        out_pos[i * 4 + 2] = verts[i][2];
        out_pos[i * 4 + 3] = 0.0f;
    }
    for (int f = 0; f < nfaces; f++) {
        out_idx[f * 3 + 0] = (uint32_t)tris[f][0];
        out_idx[f * 3 + 1] = (uint32_t)tris[f][1];
        out_idx[f * 3 + 2] = (uint32_t)tris[f][2];
    }
}

static void meshlet_create_host_buffer(VkBuffer *buf, VkDeviceMemory *mem,
                                        void **mapped, size_t size,
                                        VkBufferUsageFlags usage) {
    VkBufferCreateInfo ci = {0};
    ci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    ci.size = size;
    ci.usage = usage;
    VK_CHECK(vkCreateBuffer(g.device, &ci, NULL, buf));

    VkMemoryRequirements req;
    vkGetBufferMemoryRequirements(g.device, *buf, &req);
    VkMemoryAllocateInfo ai = {0};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = req.size;
    ai.memoryTypeIndex = find_memory_type(req.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
        VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    VK_CHECK(vkAllocateMemory(g.device, &ai, NULL, mem));
    VK_CHECK(vkBindBufferMemory(g.device, *buf, *mem, 0));
    VK_CHECK(vkMapMemory(g.device, *mem, 0, size, 0, mapped));
}

static void meshlet_lazy_init(void) {
    if (g_meshlet_initialized) return;

    float tmpl_pos[ICO_NVERTS * 4];
    uint32_t tmpl_idx[ICO_NIDX];
    icosphere_generate(tmpl_pos, tmpl_idx);

    g_meshlet_tmpl_pos = ergo_vk_create_buffer(ICO_NVERTS * 4 * sizeof(float));
    g_meshlet_tmpl_idx = ergo_vk_create_buffer(ICO_NIDX * sizeof(uint32_t));
    ergo_vk_upload(g_meshlet_tmpl_pos, tmpl_pos, ICO_NVERTS * 4 * sizeof(float));
    ergo_vk_upload(g_meshlet_tmpl_idx, tmpl_idx, ICO_NIDX * sizeof(uint32_t));

    size_t out_size = (size_t)MESHLET_MAX * ICO_NVERTS_EXPANDED * 4 * sizeof(float);
    g_meshlet_out_pos[0] = ergo_vk_create_buffer(out_size);
    g_meshlet_out_nv[0]  = ergo_vk_create_buffer(out_size);
    g_meshlet_out_pos[1] = ergo_vk_create_buffer(out_size);
    g_meshlet_out_nv[1]  = ergo_vk_create_buffer(out_size);

    meshlet_create_host_buffer(&g_meshlet_counter_buf, &g_meshlet_counter_mem,
                               &g_meshlet_counter_mapped, MESHLET_COUNTER_SIZE,
                               VK_BUFFER_USAGE_STORAGE_BUFFER_BIT |
                               VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT);

    g_meshlet_compute_pipe = ergo_vk_load_shader(
        meshlet_gen_comp_spv, meshlet_gen_comp_spv_size, 9, 96);

    /* Template bindings (4,5) are bound once here and never per-frame;
     * output buffers (6,7) are re-bound per-frame for double-buffering.
     * Seed both frame-slot sets for all of them (safe: the pipeline was
     * just created — nothing references its sets yet). */
    {
        PipeSlot *mp = &g.pipes[g_meshlet_compute_pipe];
        vk_bind_buf_all_slots(mp, 4, g.bufs[g_meshlet_tmpl_pos].buffer,
                              g.bufs[g_meshlet_tmpl_pos].size);
        vk_bind_buf_all_slots(mp, 5, g.bufs[g_meshlet_tmpl_idx].buffer,
                              g.bufs[g_meshlet_tmpl_idx].size);
        vk_bind_buf_all_slots(mp, 6, g.bufs[g_meshlet_out_pos[0]].buffer,
                              g.bufs[g_meshlet_out_pos[0]].size);
        vk_bind_buf_all_slots(mp, 7, g.bufs[g_meshlet_out_nv[0]].buffer,
                              g.bufs[g_meshlet_out_nv[0]].size);
        /* Counter buffer (binding 8) — raw VkBuffer, both slots */
        vk_bind_buf_all_slots(mp, 8, g_meshlet_counter_buf,
                              MESHLET_COUNTER_SIZE);
    }

    g_meshlet_initialized = 1;
    fprintf(stderr, "[ergo_vk] Meshlet pipeline: %d max meshlets, "
            "%d verts/meshlet\n", MESHLET_MAX, ICO_NVERTS_EXPANDED);
}

void ergo_vk_render_meshlets(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                              ErgoVkBuf buf_color, int n_points,
                              ErgoVkBuf buf_grad_x, ErgoVkBuf buf_grad_y,
                              ErgoVkBuf buf_grad_z, ErgoVkBuf buf_met_gate,
                              int grid_size, float val_min, float val_max,
                              float world_scale) {
    if (g.headless) return;

    meshlet_lazy_init();
    atlas_lazy_init();

    static int meshlet_frame = 0;
    if (meshlet_frame++ < 3)
        fprintf(stderr, "[ergo_vk] Meshlet frame %d\n", meshlet_frame);

    /* Bind grid buffers to compute (bindings 0-3). Cached across frames,
     * so write BOTH frame-slot sets on a cache miss — otherwise the
     * other slot keeps stale descriptors. Safe here because this
     * pipeline's sets are only ever referenced by submit-and-wait
     * xfer_cmd_buf dispatches, never by in-flight frame cmd bufs. */
    static ErgoVkBuf last_grad_x = 0;
    if (last_grad_x != buf_grad_x) {
        PipeSlot *mp = &g.pipes[g_meshlet_compute_pipe];
        vk_bind_buf_all_slots(mp, 0, g.bufs[buf_grad_x].buffer,
                              g.bufs[buf_grad_x].size);
        vk_bind_buf_all_slots(mp, 1, g.bufs[buf_grad_y].buffer,
                              g.bufs[buf_grad_y].size);
        vk_bind_buf_all_slots(mp, 2, g.bufs[buf_grad_z].buffer,
                              g.bufs[buf_grad_z].size);
        vk_bind_buf_all_slots(mp, 3, g.bufs[buf_met_gate].buffer,
                              g.bufs[buf_met_gate].size);
        last_grad_x = buf_grad_x;
    }

    /* Wait for previous render to finish reading output buffers
     * before we overwrite them with new compute results */
    VK_CHECK(vkWaitForFences(g.device, 1, &g.render_fence, VK_TRUE, UINT64_MAX));

    /* Swap double-buffer: compute writes to current, render reads previous */
    int wr = g_meshlet_write_idx;
    int rd = wr ^ 1;
    g_meshlet_write_idx = rd;  /* flip for next frame */

    /* Bind compute output to write-side buffers */
    ergo_vk_bind_buffer(g_meshlet_compute_pipe, 6, g_meshlet_out_pos[wr]);
    ergo_vk_bind_buffer(g_meshlet_compute_pipe, 7, g_meshlet_out_nv[wr]);

    /* Zero counter + indirect command */
    uint32_t zero[5] = {0, 0, 1, 0, 0};
    memcpy(g_meshlet_counter_mapped, zero, MESHLET_COUNTER_SIZE);

    /* Camera */
    float aspect = (float)g.sc_extent.width / (float)g.sc_extent.height;
    ergo_vk_camera_tick();
    Mat4 proj = mat4_perspective(45.0f * (float)M_PI / 180.0f, aspect,
                                 0.01f, 100.0f);
    float ca = _ergo_cosf(g.cam_azimuth), sa = _ergo_sinf(g.cam_azimuth);
    float ce = _ergo_cosf(g.cam_elevation), se = _ergo_sinf(g.cam_elevation);
    float ex = g.cam_distance * ce * sa;
    float ey = g.cam_distance * se;
    float ez = g.cam_distance * ce * ca;
    Mat4 view = mat4_look_at(ex, ey, ez, 0, 0, 0, 0, 1, 0);
    Mat4 viewProj = mat4_mul(proj, view);

    /* Compute push constants */
    struct {
        float viewProj[16];
        float density_threshold;
        float shell_radius;
        float world_scale;
        float cell_size;
        int   grid_size;
        float viewport_height;
        int   max_meshlets;
        float pad;
    } compute_pc;

    memcpy(compute_pc.viewProj, viewProj.m, 64);
    compute_pc.density_threshold = 0.05f;
    compute_pc.shell_radius = 75.0f * 0.4f;
    compute_pc.world_scale = world_scale;
    compute_pc.cell_size = 75.0f;
    compute_pc.grid_size = grid_size;
    compute_pc.viewport_height = (float)g.sc_extent.height;
    compute_pc.max_meshlets = MESHLET_MAX;
    compute_pc.pad = 0.0f;

    ergo_vk_push_constants(g_meshlet_compute_pipe, &compute_pc, 96);

    /* Record compute dispatch into xfer command buffer to avoid
     * disturbing the frame system's cmd_buf/fence state. */
    {
        PipeSlot *p = &g.pipes[g_meshlet_compute_pipe];
        VkCommandBufferBeginInfo begin = {0};
        begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
        begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        VK_CHECK(vkResetCommandBuffer(g.xfer_cmd_buf, 0));
        VK_CHECK(vkBeginCommandBuffer(g.xfer_cmd_buf, &begin));
        vkCmdBindPipeline(g.xfer_cmd_buf, VK_PIPELINE_BIND_POINT_COMPUTE,
                          p->pipeline);
        vkCmdBindDescriptorSets(g.xfer_cmd_buf, VK_PIPELINE_BIND_POINT_COMPUTE,
                                p->layout, 0, 1, &p->ds[g.cmd_idx], 0, NULL);
        if (p->pc_size > 0)
            vkCmdPushConstants(g.xfer_cmd_buf, p->layout,
                               VK_SHADER_STAGE_COMPUTE_BIT, 0,
                               p->pc_size, p->pc_data);
        int total_cells = grid_size * grid_size * grid_size;
        vkCmdDispatch(g.xfer_cmd_buf, (total_cells + 255) / 256, 1, 1);
        VK_CHECK(vkEndCommandBuffer(g.xfer_cmd_buf));

        VkSubmitInfo si = {0};
        si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
        si.commandBufferCount = 1;
        si.pCommandBuffers = &g.xfer_cmd_buf;
        VK_CHECK(vkResetFences(g.device, 1, &g.xfer_fence));
        VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.xfer_fence));
        VK_CHECK(vkWaitForFences(g.device, 1, &g.xfer_fence, VK_TRUE, UINT64_MAX));
    }

    /* Debug: read counter to see how many meshlets were generated */
    {
        uint32_t *ctr = (uint32_t *)g_meshlet_counter_mapped;
        if (meshlet_frame <= 3)
            fprintf(stderr, "[ergo_vk] Meshlet compute: %u meshlets, "
                    "vertexCount=%u instanceCount=%u\n",
                    ctr[0], ctr[1], ctr[2]);
    }

    /* Now render — render_fence already waited above before compute */
    VK_CHECK(vkResetFences(g.device, 1, &g.render_fence));

    uint32_t img_idx;
    VkResult acq = vkAcquireNextImageKHR(g.device, g.swapchain, UINT64_MAX,
                                          g.sem_available, VK_NULL_HANDLE,
                                          &img_idx);
    if (acq == VK_ERROR_OUT_OF_DATE_KHR) {
        ergo_vk_frame_begin();
        return;
    }

    /* One-time: create render UBO if needed */
    if (!g.render_ubo) {
        VkBufferCreateInfo ubo_ci = {0};
        ubo_ci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        ubo_ci.size = 96;
        ubo_ci.usage = VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT;
        VK_CHECK(vkCreateBuffer(g.device, &ubo_ci, NULL, &g.render_ubo));
        VkMemoryRequirements req;
        vkGetBufferMemoryRequirements(g.device, g.render_ubo, &req);
        VkMemoryAllocateInfo ai = {0};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = find_memory_type(req.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
            VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        VK_CHECK(vkAllocateMemory(g.device, &ai, NULL, &g.render_ubo_mem));
        VK_CHECK(vkBindBufferMemory(g.device, g.render_ubo, g.render_ubo_mem, 0));
        VK_CHECK(vkMapMemory(g.device, g.render_ubo_mem, 0, 96, 0,
                             &g.render_ubo_mapped));
    }

    /* Bind read-side output buffers + octa sampler + UBO */
    {
        VkDescriptorBufferInfo buf_infos[2];
        VkWriteDescriptorSet writes[4];

        BufSlot *bp = &g.bufs[g_meshlet_out_pos[rd]];
        buf_infos[0].buffer = bp->buffer;
        buf_infos[0].offset = 0;
        buf_infos[0].range = bp->size;

        BufSlot *bn = &g.bufs[g_meshlet_out_nv[rd]];
        buf_infos[1].buffer = bn->buffer;
        buf_infos[1].offset = 0;
        buf_infos[1].range = bn->size;

        for (int i = 0; i < 2; i++) {
            memset(&writes[i], 0, sizeof(VkWriteDescriptorSet));
            writes[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            writes[i].dstSet = g.meshlet_ds;
            writes[i].dstBinding = i;
            writes[i].descriptorCount = 1;
            writes[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            writes[i].pBufferInfo = &buf_infos[i];
        }

        /* Atlas SSBO at binding 2 */
        VkDescriptorBufferInfo atlas_info = {0};
        BufSlot *ba = &g.bufs[g_atlas_ssbo];
        atlas_info.buffer = ba->buffer;
        atlas_info.offset = 0;
        atlas_info.range = ba->size;

        memset(&writes[2], 0, sizeof(VkWriteDescriptorSet));
        writes[2].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[2].dstSet = g.meshlet_ds;
        writes[2].dstBinding = 2;
        writes[2].descriptorCount = 1;
        writes[2].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        writes[2].pBufferInfo = &atlas_info;

        VkDescriptorBufferInfo ubo_info = {0};
        ubo_info.buffer = g.render_ubo;
        ubo_info.offset = 0;
        ubo_info.range = 96;

        memset(&writes[3], 0, sizeof(VkWriteDescriptorSet));
        writes[3].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[3].dstSet = g.meshlet_ds;
        writes[3].dstBinding = 5;
        writes[3].descriptorCount = 1;
        writes[3].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
        writes[3].pBufferInfo = &ubo_info;

        vkUpdateDescriptorSets(g.device, 4, writes, 0, NULL);
    }

    /* Update render UBO */
    struct {
        float viewProj[16];
        float cam_x, cam_y, cam_z;
        float cull_mode;
        float val_min, val_max;
        float world_scale;
        float pad;
    } render_params;
    memcpy(render_params.viewProj, viewProj.m, 64);
    render_params.cam_x = ex;
    render_params.cam_y = ey;
    render_params.cam_z = ez;
    render_params.cull_mode = g_culling_enabled ? 1.0f : 0.0f;
    render_params.val_min = val_min;
    render_params.val_max = val_max;
    render_params.world_scale = world_scale;
    render_params.pad = 0.0f;
    /* Bind particle SoA buffers for octa point render */
    if (!pts_ds_bound) {
        ErgoVkBuf bufs_arr[4] = { buf_x, buf_y, buf_z, buf_color };
        VkDescriptorBufferInfo buf_infos[4];
        VkWriteDescriptorSet writes[4];
        for (int i = 0; i < 4; i++) {
            BufSlot *b = &g.bufs[bufs_arr[i]];
            buf_infos[i].buffer = b->buffer;
            buf_infos[i].offset = g.render_offset;
            buf_infos[i].range = b->size - g.render_offset;
            memset(&writes[i], 0, sizeof(VkWriteDescriptorSet));
            writes[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            writes[i].dstSet = g.pts_ds;
            writes[i].dstBinding = i;
            writes[i].descriptorCount = 1;
            writes[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            writes[i].pBufferInfo = &buf_infos[i];
        }
        vkUpdateDescriptorSets(g.device, 4, writes, 0, NULL);
        pts_ds_bound = 1;
    }

    /* Generate per-cell atlas from particle data */
    atlas_gen_dispatch(buf_x, buf_y, buf_z, buf_color, n_points, val_min, val_max);

    /* Update UBO with user camera for shell render */
    memcpy(g.render_ubo_mapped, &render_params, 96);

    /* Record shell render command buffer */
    VkCommandBufferBeginInfo begin_info = {0};
    begin_info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin_info.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;

    VK_CHECK(vkResetCommandBuffer(g.render_cmd_buf, 0));
    VK_CHECK(vkBeginCommandBuffer(g.render_cmd_buf, &begin_info));

    /* Barrier: compute -> vertex + indirect (for meshlet shell data) */
    {
        VkMemoryBarrier mb = {0};
        mb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT |
                           VK_ACCESS_INDIRECT_COMMAND_READ_BIT;
        vkCmdPipelineBarrier(g.render_cmd_buf,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            VK_PIPELINE_STAGE_VERTEX_SHADER_BIT |
            VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT,
            0, 1, &mb, 0, NULL, 0, NULL);
    }

    /* Render meshlet shells sampling cubemap */
    VkClearValue clears[2];
    clears[0].color = (VkClearColorValue){{0.0f, 0.0f, 0.0f, 1.0f}};
    clears[1].depthStencil = (VkClearDepthStencilValue){1.0f, 0};

    VkRenderPassBeginInfo rp_begin = {0};
    rp_begin.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rp_begin.renderPass = g.render_pass;
    rp_begin.framebuffer = g.sc_fbs[img_idx];
    rp_begin.renderArea.extent = g.sc_extent;
    rp_begin.clearValueCount = 2;
    rp_begin.pClearValues = clears;

    vkCmdBeginRenderPass(g.render_cmd_buf, &rp_begin, VK_SUBPASS_CONTENTS_INLINE);

    vkCmdBindPipeline(g.render_cmd_buf, VK_PIPELINE_BIND_POINT_GRAPHICS,
                      g.meshlet_pipeline);
    vkCmdBindDescriptorSets(g.render_cmd_buf, VK_PIPELINE_BIND_POINT_GRAPHICS,
                            g.meshlet_layout, 0, 1,
                            &g.meshlet_ds, 0, NULL);

    /* Indirect draw: vertexCount at offset 4 in counter buffer */
    vkCmdDrawIndirect(g.render_cmd_buf, g_meshlet_counter_buf,
                      4, 1, sizeof(VkDrawIndirectCommand));

    vkCmdEndRenderPass(g.render_cmd_buf);
    VK_CHECK(vkEndCommandBuffer(g.render_cmd_buf));

    VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.waitSemaphoreCount = 1;
    si.pWaitSemaphores = &g.sem_available;
    si.pWaitDstStageMask = &wait_stage;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.render_cmd_buf;
    si.signalSemaphoreCount = 1;
    si.pSignalSemaphores = &g.sem_finished;

    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.render_fence));

    VkPresentInfoKHR present = {0};
    present.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    present.waitSemaphoreCount = 1;
    present.pWaitSemaphores = &g.sem_finished;
    present.swapchainCount = 1;
    present.pSwapchains = &g.swapchain;
    present.pImageIndices = &img_idx;

    vkQueuePresentKHR(g.compute_queue, &present);
}

int ergo_vk_should_close(void) {
    if (g.headless) return 0;
#ifdef ERGO_VK_ANDROID
    return 0;  /* Android lifecycle managed by Java layer */
#else
    glfwPollEvents();
    return glfwWindowShouldClose(g.window);
#endif
}

#else /* ERGO_VK_HEADLESS_ONLY */

void ergo_vk_render_frame(ErgoVkBuf buf, int width, int height,
                           float val_min, float val_max,
                           float height_scale) {
    (void)buf; (void)width; (void)height;
    (void)val_min; (void)val_max; (void)height_scale;
}

void ergo_vk_render_points(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                            ErgoVkBuf buf_color, int n_points,
                            float point_size, float val_min, float val_max,
                            float world_scale) {
    (void)buf_x; (void)buf_y; (void)buf_z; (void)buf_color;
    (void)n_points; (void)point_size;
    (void)val_min; (void)val_max; (void)world_scale;
}

void ergo_vk_render_gaussians(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                               ErgoVkBuf buf_color, int n_points,
                               float point_size, float val_min, float val_max,
                               float world_scale) {
    (void)buf_x; (void)buf_y; (void)buf_z; (void)buf_color;
    (void)n_points; (void)point_size;
    (void)val_min; (void)val_max; (void)world_scale;
}

void ergo_vk_render_grid_gaussians(ErgoVkBuf buf_grad_x, ErgoVkBuf buf_grad_y,
                                    ErgoVkBuf buf_grad_z, ErgoVkBuf buf_met_gate,
                                    int grid_size, float val_min, float val_max,
                                    float world_scale) {
    (void)buf_grad_x; (void)buf_grad_y; (void)buf_grad_z; (void)buf_met_gate;
    (void)grid_size; (void)val_min; (void)val_max; (void)world_scale;
}

void ergo_vk_render_meshlets(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                              ErgoVkBuf buf_color, int n_points,
                              ErgoVkBuf buf_grad_x, ErgoVkBuf buf_grad_y,
                              ErgoVkBuf buf_grad_z, ErgoVkBuf buf_met_gate,
                              int grid_size, float val_min, float val_max,
                              float world_scale) {
    (void)buf_x; (void)buf_y; (void)buf_z; (void)buf_color; (void)n_points;
    (void)buf_grad_x; (void)buf_grad_y; (void)buf_grad_z; (void)buf_met_gate;
    (void)grid_size; (void)val_min; (void)val_max; (void)world_scale;
}

void ergo_vk_render_invalidate(void) {}

int ergo_vk_should_close(void) {
    return 0;
}

#endif /* ERGO_VK_HEADLESS_ONLY */

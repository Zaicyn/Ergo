/*
 * vk_render.c — Persistent render pipeline for Ergo
 *
 * Included from vk_host.c. Uses the global state 'g' and helpers
 * defined there (find_memory_type, Mat4, etc.)
 *
 * Architecture:
 *   - Pre-recorded command buffers (one per swapchain image)
 *   - Render params via single UBO (persistently mapped, updated per-frame)
 *   - Draw count via indirect buffer (host-visible, updated per-frame)
 *   - Per-swapchain-image fences + semaphores (frames in flight)
 *   - Zero command buffer recording at runtime
 *
 * Single UBO rationale (Option 3 from handoff doc):
 *   The fence wait guarantees the GPU finished reading the UBO before
 *   we overwrite it. Camera params are 96 bytes — no bandwidth concern.
 *   We still get frames-in-flight benefit for cmd buf + swapchain image.
 */

/* ── Render params (matches shader UBO layout) ───────────── */

typedef struct {
    float viewProj[16];   /* 64 bytes */
    float cam_x, cam_y, cam_z;  /* 12 bytes */
    float cull_mode;      /* 4 bytes */
    float val_min;        /* 4 bytes */
    float val_max;        /* 4 bytes */
    float world_scale;    /* 4 bytes */
    float pad;            /* 4 bytes — align to 96 */
} RenderParams;

/* g_culling_enabled and camera_key_cb are defined in vk_host.c */

/* ── Create host-visible buffer (UBO / indirect) ─────────── */

static void create_host_buffer(VkBuffer *buf, VkDeviceMemory *mem,
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

/* ── Init persistent render resources ────────────────────── */

static void render_persistent_init(void) {
    /* Per-swapchain-image command buffers */
    VkCommandBufferAllocateInfo rcb_ai = {0};
    rcb_ai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    rcb_ai.commandPool = g.cmd_pool;
    rcb_ai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    rcb_ai.commandBufferCount = g.sc_count;
    VK_CHECK(vkAllocateCommandBuffers(g.device, &rcb_ai, g.render_cmd_buf));

    /* Per-swapchain-image sync objects */
    VkSemaphoreCreateInfo sem_ci = {0};
    sem_ci.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
    VkFenceCreateInfo rf_ci = {0};
    rf_ci.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    rf_ci.flags = VK_FENCE_CREATE_SIGNALED_BIT;
    for (uint32_t i = 0; i < g.sc_count; i++) {
        VK_CHECK(vkCreateSemaphore(g.device, &sem_ci, NULL, &g.sem_available[i]));
        VK_CHECK(vkCreateSemaphore(g.device, &sem_ci, NULL, &g.sem_finished[i]));
        VK_CHECK(vkCreateFence(g.device, &rf_ci, NULL, &g.render_fence[i]));
    }
    g.current_frame = 0;

    /* Single render params UBO — persistently mapped */
    create_host_buffer(&g.render_ubo, &g.render_ubo_mem,
                       &g.render_ubo_mapped, sizeof(RenderParams),
                       VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT);

    /* Indirect draw buffer — single, host-visible */
    create_host_buffer(&g.indirect_buf, &g.indirect_mem,
                       &g.indirect_mapped, 16,
                       VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT);
    uint32_t init_cmd[4] = {0, 1, 0, 0};
    memcpy(g.indirect_mapped, init_cmd, 16);

    /* Detect render mode from environment */
    g.render_mode = (getenv("ERGO_RENDER") &&
                     strcmp(getenv("ERGO_RENDER"), "gauss") == 0) ? 1 : 0;
    g.render_recorded = 0;
}

/* ── Pre-record persistent command buffers ───────────────── */

static void render_record_persistent(ErgoVkBuf buf_x, ErgoVkBuf buf_y,
                                      ErgoVkBuf buf_z, ErgoVkBuf buf_color) {
    /* Bind SoA buffers + UBO to points descriptor set */
    {
        ErgoVkBuf bufs_arr[4] = { buf_x, buf_y, buf_z, buf_color };
        VkDescriptorBufferInfo buf_infos[4];
        VkWriteDescriptorSet writes[5];
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
        /* UBO at binding 5 */
        VkDescriptorBufferInfo ubo_info = {0};
        ubo_info.buffer = g.render_ubo;
        ubo_info.offset = 0;
        ubo_info.range = sizeof(RenderParams);

        memset(&writes[4], 0, sizeof(VkWriteDescriptorSet));
        writes[4].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[4].dstSet = g.pts_ds;
        writes[4].dstBinding = 5;
        writes[4].descriptorCount = 1;
        writes[4].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
        writes[4].pBufferInfo = &ubo_info;

        vkUpdateDescriptorSets(g.device, 5, writes, 0, NULL);
    }

    /* Same for gaussian descriptor set */
    if (g.gauss_pipeline) {
        ErgoVkBuf bufs_arr[4] = { buf_x, buf_y, buf_z, buf_color };
        VkDescriptorBufferInfo buf_infos[4];
        VkWriteDescriptorSet writes[5];
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
        VkDescriptorBufferInfo ubo_info = {0};
        ubo_info.buffer = g.render_ubo;
        ubo_info.offset = 0;
        ubo_info.range = sizeof(RenderParams);

        memset(&writes[4], 0, sizeof(VkWriteDescriptorSet));
        writes[4].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[4].dstSet = g.gauss_ds;
        writes[4].dstBinding = 5;
        writes[4].descriptorCount = 1;
        writes[4].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
        writes[4].pBufferInfo = &ubo_info;

        vkUpdateDescriptorSets(g.device, 5, writes, 0, NULL);
    }

    /* Record one command buffer per swapchain image */
    VkPipeline pipe = g.render_mode ? g.gauss_pipeline : g.pts_pipeline;
    VkPipelineLayout layout = g.render_mode ? g.gauss_layout : g.pts_layout;
    VkDescriptorSet ds = g.render_mode ? g.gauss_ds : g.pts_ds;

    for (uint32_t i = 0; i < g.sc_count; i++) {
        VkCommandBuffer cmd = g.render_cmd_buf[i];

        VkCommandBufferBeginInfo begin = {0};
        begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
        /* No ONE_TIME_SUBMIT — this buffer will be resubmitted every frame */
        VK_CHECK(vkBeginCommandBuffer(cmd, &begin));

        /* GPU sync: compute writes -> vertex/indirect reads */
        {
            VkMemoryBarrier mb = {0};
            mb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
            mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT |
                               VK_ACCESS_INDIRECT_COMMAND_READ_BIT;
            vkCmdPipelineBarrier(cmd,
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                VK_PIPELINE_STAGE_VERTEX_SHADER_BIT |
                VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT,
                0, 1, &mb, 0, NULL, 0, NULL);
        }

        VkClearValue clears[2];
        clears[0].color = (VkClearColorValue){{0.0f, 0.0f, 0.0f, 1.0f}};
        clears[1].depthStencil = (VkClearDepthStencilValue){1.0f, 0};

        VkRenderPassBeginInfo rp_begin = {0};
        rp_begin.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
        rp_begin.renderPass = g.render_pass;
        rp_begin.framebuffer = g.sc_fbs[i];  /* THIS image's framebuffer */
        rp_begin.renderArea.extent = g.sc_extent;
        rp_begin.clearValueCount = 2;
        rp_begin.pClearValues = clears;

        vkCmdBeginRenderPass(cmd, &rp_begin, VK_SUBPASS_CONTENTS_INLINE);

        vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, pipe);
        vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS,
                                layout, 0, 1, &ds, 0, NULL);

        /* Indirect draw — count comes from the indirect buffer at draw time */
        vkCmdDrawIndirect(cmd, g.indirect_buf, 0, 1,
                          sizeof(VkDrawIndirectCommand));

        vkCmdEndRenderPass(cmd);
        VK_CHECK(vkEndCommandBuffer(cmd));
    }

    g.render_recorded = 1;
    fprintf(stderr, "[ergo_vk] Persistent render: %u cmd bufs recorded (%s)\n",
            g.sc_count, g.render_mode ? "gaussian" : "points");
}

/* ── Per-frame render (trivial CPU path) ─────────────────── */

void ergo_vk_render_points(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                            ErgoVkBuf buf_color, int n_points,
                            float point_size, float val_min, float val_max,
                            float world_scale) {
    if (g.headless) return;
    (void)point_size;  /* size now controlled by shader / UBO */

    /* First call: record persistent command buffers */
    if (!g.render_recorded) {
        render_record_persistent(buf_x, buf_y, buf_z, buf_color);
    }

    /* Acquire swapchain image first, then wait on ITS fence */
    uint32_t img_idx;
    VkResult acq = vkAcquireNextImageKHR(g.device, g.swapchain, UINT64_MAX,
                                          g.sem_available[0], VK_NULL_HANDLE,
                                          &img_idx);
    if (acq == VK_ERROR_OUT_OF_DATE_KHR) return;

    /* Wait on this image's fence (ensures its previous submit completed) */
    VK_CHECK(vkWaitForFences(g.device, 1, &g.render_fence[img_idx],
                              VK_TRUE, UINT64_MAX));
    VK_CHECK(vkResetFences(g.device, 1, &g.render_fence[img_idx]));

    /* Update UBO (just a memcpy — zero Vulkan calls) */
    float aspect = (float)g.sc_extent.width / (float)g.sc_extent.height;
    Mat4 proj = mat4_perspective(45.0f * 3.14159265f / 180.0f, aspect,
                                 0.01f, 100.0f);
    float ca = cosf(g.cam_azimuth), sa = sinf(g.cam_azimuth);
    float ce = cosf(g.cam_elevation), se = sinf(g.cam_elevation);
    float ex = g.cam_distance * ce * sa;
    float ey = g.cam_distance * se;
    float ez = g.cam_distance * ce * ca;
    Mat4 view = mat4_look_at(ex, ey, ez, 0, 0, 0, 0, 1, 0);
    Mat4 viewProj = mat4_mul(proj, view);

    RenderParams params;
    memcpy(params.viewProj, viewProj.m, 64);
    params.cam_x = ex;
    params.cam_y = ey;
    params.cam_z = ez;
    params.cull_mode = g_culling_enabled ? 1.0f : 0.0f;
    params.val_min = val_min;
    params.val_max = val_max;
    params.world_scale = world_scale;
    params.pad = 0.0f;

    /* Write to UBO (safe — fence guarantees GPU finished reading) */
    memcpy(g.render_ubo_mapped, &params, sizeof(RenderParams));

    /* Update indirect draw count */
    if (g.render_mode == 0) {
        /* Points: vertexCount = n_points, instanceCount = 1 */
        uint32_t draw_cmd[4] = { (uint32_t)n_points, 1, 0, 0 };
        memcpy(g.indirect_mapped, draw_cmd, 16);
    } else {
        /* Gaussians: vertexCount = 6, instanceCount = n_points */
        uint32_t draw_cmd[4] = { 6, (uint32_t)n_points, 0, 0 };
        memcpy(g.indirect_mapped, draw_cmd, 16);
    }

    /* Submit pre-recorded command buffer for the ACQUIRED image */
    VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.waitSemaphoreCount = 1;
    si.pWaitSemaphores = &g.sem_available[0];
    si.pWaitDstStageMask = &wait_stage;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g.render_cmd_buf[img_idx];
    si.signalSemaphoreCount = 1;
    si.pSignalSemaphores = &g.sem_finished[img_idx];

    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.render_fence[img_idx]));

    /* Present */
    VkPresentInfoKHR present = {0};
    present.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    present.waitSemaphoreCount = 1;
    present.pWaitSemaphores = &g.sem_finished[img_idx];
    present.swapchainCount = 1;
    present.pSwapchains = &g.swapchain;
    present.pImageIndices = &img_idx;

    vkQueuePresentKHR(g.compute_queue, &present);
}

/* Gaussian render uses the same path — just routes through render_points */
void ergo_vk_render_gaussians(ErgoVkBuf buf_x, ErgoVkBuf buf_y, ErgoVkBuf buf_z,
                               ErgoVkBuf buf_color, int n_points,
                               float point_size, float val_min, float val_max,
                               float world_scale) {
    ergo_vk_render_points(buf_x, buf_y, buf_z, buf_color, n_points,
                           point_size, val_min, val_max, world_scale);
}

/* ── Grid gaussian render (O(cells) path) ────────────────── */

static int g_grid_gauss_ds_bound = 0;

void ergo_vk_render_grid_gaussians(ErgoVkBuf buf_grad_x, ErgoVkBuf buf_grad_y,
                                    ErgoVkBuf buf_grad_z, ErgoVkBuf buf_met_gate,
                                    int grid_size, float val_min, float val_max,
                                    float world_scale) {
    if (g.headless) return;

    static int grid_frame = 0;
    if (grid_frame++ < 3)
        fprintf(stderr, "[ergo_vk] Grid gaussian frame %d, sc_count=%u\n",
                grid_frame, g.sc_count);

    /* Simple single-flight: wait on slot 0, no overlap */
    VK_CHECK(vkWaitForFences(g.device, 1, &g.render_fence[0],
                              VK_TRUE, UINT64_MAX));
    VK_CHECK(vkResetFences(g.device, 1, &g.render_fence[0]));

    uint32_t img_idx;
    VkResult acq = vkAcquireNextImageKHR(g.device, g.swapchain, UINT64_MAX,
                                          g.sem_available[0], VK_NULL_HANDLE,
                                          &img_idx);
    if (acq == VK_ERROR_OUT_OF_DATE_KHR) return;

    /* Bind grid buffers + UBO to descriptor set (once) */
    if (!g_grid_gauss_ds_bound) {
        ErgoVkBuf bufs_arr[4] = { buf_grad_x, buf_grad_y, buf_grad_z, buf_met_gate };
        VkDescriptorBufferInfo buf_infos[4];
        VkWriteDescriptorSet writes[5];
        for (int i = 0; i < 4; i++) {
            BufSlot *b = &g.bufs[bufs_arr[i]];
            buf_infos[i].buffer = b->buffer;
            buf_infos[i].offset = 0;
            buf_infos[i].range = b->size;

            memset(&writes[i], 0, sizeof(VkWriteDescriptorSet));
            writes[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            writes[i].dstSet = g.grid_gauss_ds;
            writes[i].dstBinding = i;
            writes[i].descriptorCount = 1;
            writes[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            writes[i].pBufferInfo = &buf_infos[i];
        }
        /* UBO at binding 5 */
        VkDescriptorBufferInfo ubo_info = {0};
        ubo_info.buffer = g.render_ubo;
        ubo_info.offset = 0;
        ubo_info.range = sizeof(RenderParams);

        memset(&writes[4], 0, sizeof(VkWriteDescriptorSet));
        writes[4].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[4].dstSet = g.grid_gauss_ds;
        writes[4].dstBinding = 5;
        writes[4].descriptorCount = 1;
        writes[4].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
        writes[4].pBufferInfo = &ubo_info;

        vkUpdateDescriptorSets(g.device, 5, writes, 0, NULL);
        g_grid_gauss_ds_bound = 1;
    }

    /* Update UBO — repurpose pad field as grid_size */
    float aspect = (float)g.sc_extent.width / (float)g.sc_extent.height;
    Mat4 proj = mat4_perspective(45.0f * 3.14159265f / 180.0f, aspect,
                                 0.01f, 100.0f);
    float ca = cosf(g.cam_azimuth), sa = sinf(g.cam_azimuth);
    float ce = cosf(g.cam_elevation), se = sinf(g.cam_elevation);
    float ex = g.cam_distance * ce * sa;
    float ey = g.cam_distance * se;
    float ez = g.cam_distance * ce * ca;
    Mat4 view = mat4_look_at(ex, ey, ez, 0, 0, 0, 0, 1, 0);
    Mat4 viewProj = mat4_mul(proj, view);

    RenderParams params;
    memcpy(params.viewProj, viewProj.m, 64);
    params.cam_x = ex;
    params.cam_y = ey;
    params.cam_z = ez;
    params.cull_mode = g_culling_enabled ? 1.0f : 0.0f;
    params.val_min = val_min;
    params.val_max = val_max;
    params.world_scale = world_scale;
    params.pad = (float)grid_size;  /* shader reads this as grid_size */

    memcpy(g.render_ubo_mapped, &params, sizeof(RenderParams));

    /* Record per-frame (grid data changes each frame from scatter+stencil) */
    int n_cells = grid_size * grid_size * grid_size;
    VkCommandBuffer cmd = g.render_cmd_buf[0];
    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;

    VK_CHECK(vkResetCommandBuffer(cmd, 0));
    VK_CHECK(vkBeginCommandBuffer(cmd, &begin));

    /* Barrier: compute writes -> vertex reads */
    {
        VkMemoryBarrier mb = {0};
        mb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
        vkCmdPipelineBarrier(cmd,
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

    vkCmdBeginRenderPass(cmd, &rp_begin, VK_SUBPASS_CONTENTS_INLINE);

    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS,
                      g.grid_gauss_pipeline);
    vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS,
                            g.grid_gauss_layout, 0, 1,
                            &g.grid_gauss_ds, 0, NULL);

    /* Instanced: 6 verts per quad, n_cells instances */
    vkCmdDraw(cmd, 6, n_cells, 0, 0);

    vkCmdEndRenderPass(cmd);
    VK_CHECK(vkEndCommandBuffer(cmd));

    VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.waitSemaphoreCount = 1;
    si.pWaitSemaphores = &g.sem_available[0];
    si.pWaitDstStageMask = &wait_stage;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &cmd;
    si.signalSemaphoreCount = 1;
    si.pSignalSemaphores = &g.sem_finished[0];

    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.render_fence[0]));

    VkPresentInfoKHR present = {0};
    present.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    present.waitSemaphoreCount = 1;
    present.pWaitSemaphores = &g.sem_finished[0];
    present.swapchainCount = 1;
    present.pSwapchains = &g.swapchain;
    present.pImageIndices = &img_idx;

    VkResult pr = vkQueuePresentKHR(g.compute_queue, &present);
    if (grid_frame <= 3)
        fprintf(stderr, "[ergo_vk] Grid present result=%d img_idx=%u\n", (int)pr, img_idx);
}

/* ── Meshlet shell render (O(cells) with compute pre-pass) ── */

/* Icosphere template: 1-subdivision icosahedron → 42 verts, 80 faces */

#define ICO_NVERTS 42
#define ICO_NFACES 80
#define ICO_NIDX   (ICO_NFACES * 3)   /* 240 indices */
#define ICO_NVERTS_EXPANDED ICO_NIDX  /* 240 expanded triangle verts */

#define MESHLET_MAX 8192  /* max meshlets per frame */
#define MESHLET_COUNTER_SIZE 20  /* 5 uint32: counter + VkDrawIndirectCommand */

/* Meshlet compute + render state (lazy-initialized on first call) */
static int              g_meshlet_initialized = 0;
static ErgoVkPipe       g_meshlet_compute_pipe;
static ErgoVkBuf        g_meshlet_tmpl_pos;     /* vec4[42] */
static ErgoVkBuf        g_meshlet_tmpl_idx;     /* uint[240] */
static ErgoVkBuf        g_meshlet_out_pos;      /* vec4[MESHLET_MAX * 240] */
static ErgoVkBuf        g_meshlet_out_nv;       /* vec4[MESHLET_MAX * 240] */
static VkBuffer         g_meshlet_counter_buf;  /* counter + indirect cmd */
static VkDeviceMemory   g_meshlet_counter_mem;
static void            *g_meshlet_counter_mapped;

static void icosphere_generate(float *out_pos, uint32_t *out_idx) {
    /* Golden ratio */
    const float phi = 1.6180339887f;
    const float inv_len = 1.0f / sqrtf(1.0f + phi * phi);
    const float a = inv_len;
    const float b = phi * inv_len;

    /* 12 base icosahedron vertices (normalized to unit sphere) */
    float base[12][3] = {
        {-a,  b,  0}, { a,  b,  0}, {-a, -b,  0}, { a, -b,  0},
        { 0, -a,  b}, { 0,  a,  b}, { 0, -a, -b}, { 0,  a, -b},
        { b,  0, -a}, { b,  0,  a}, {-b,  0, -a}, {-b,  0,  a}
    };

    /* 20 base triangles (CCW winding) */
    int base_tri[20][3] = {
        {0,11,5},  {0,5,1},   {0,1,7},   {0,7,10},  {0,10,11},
        {1,5,9},   {5,11,4},  {11,10,2},  {10,7,6},  {7,1,8},
        {3,9,4},   {3,4,2},   {3,2,6},   {3,6,8},   {3,8,9},
        {4,9,5},   {2,4,11},  {6,2,10},  {8,6,7},   {9,8,1}
    };

    /* Subdivision: split each triangle into 4.
     * Use a midpoint cache keyed by sorted edge pairs. */
    int nverts = 12;
    float verts[ICO_NVERTS][3];
    for (int i = 0; i < 12; i++) {
        verts[i][0] = base[i][0];
        verts[i][1] = base[i][1];
        verts[i][2] = base[i][2];
    }

    /* Edge midpoint cache: key = min(a,b)*64 + max(a,b) */
    int mid_cache[64 * 64];
    memset(mid_cache, -1, sizeof(mid_cache));

    #define ICO_MIDPOINT(a, b) ({ \
        int _lo = (a) < (b) ? (a) : (b); \
        int _hi = (a) < (b) ? (b) : (a); \
        int _key = _lo * 64 + _hi; \
        if (mid_cache[_key] < 0) { \
            int _m = nverts++; \
            verts[_m][0] = (verts[_lo][0] + verts[_hi][0]) * 0.5f; \
            verts[_m][1] = (verts[_lo][1] + verts[_hi][1]) * 0.5f; \
            verts[_m][2] = (verts[_lo][2] + verts[_hi][2]) * 0.5f; \
            float _len = sqrtf(verts[_m][0]*verts[_m][0] + \
                               verts[_m][1]*verts[_m][1] + \
                               verts[_m][2]*verts[_m][2]); \
            verts[_m][0] /= _len; \
            verts[_m][1] /= _len; \
            verts[_m][2] /= _len; \
            mid_cache[_key] = _m; \
        } \
        mid_cache[_key]; \
    })

    int nfaces = 0;
    int tris[ICO_NFACES][3];

    for (int f = 0; f < 20; f++) {
        int v0 = base_tri[f][0], v1 = base_tri[f][1], v2 = base_tri[f][2];
        int a = ICO_MIDPOINT(v0, v1);
        int b_mid = ICO_MIDPOINT(v1, v2);
        int c = ICO_MIDPOINT(v2, v0);
        tris[nfaces][0] = v0; tris[nfaces][1] = a;     tris[nfaces][2] = c;     nfaces++;
        tris[nfaces][0] = a;  tris[nfaces][1] = v1;    tris[nfaces][2] = b_mid;  nfaces++;
        tris[nfaces][0] = c;  tris[nfaces][1] = b_mid;  tris[nfaces][2] = v2;    nfaces++;
        tris[nfaces][0] = a;  tris[nfaces][1] = b_mid;  tris[nfaces][2] = c;     nfaces++;
    }
    #undef ICO_MIDPOINT

    /* Output positions as vec4 (w=0 padding) */
    for (int i = 0; i < nverts; i++) {
        out_pos[i * 4 + 0] = verts[i][0];
        out_pos[i * 4 + 1] = verts[i][1];
        out_pos[i * 4 + 2] = verts[i][2];
        out_pos[i * 4 + 3] = 0.0f;
    }

    /* Output face indices */
    for (int f = 0; f < nfaces; f++) {
        out_idx[f * 3 + 0] = (uint32_t)tris[f][0];
        out_idx[f * 3 + 1] = (uint32_t)tris[f][1];
        out_idx[f * 3 + 2] = (uint32_t)tris[f][2];
    }
}

static void meshlet_lazy_init(void) {
    if (g_meshlet_initialized) return;

    /* Generate icosphere template */
    float tmpl_pos[ICO_NVERTS * 4];
    uint32_t tmpl_idx[ICO_NIDX];
    icosphere_generate(tmpl_pos, tmpl_idx);

    /* Upload template to GPU */
    g_meshlet_tmpl_pos = ergo_vk_create_buffer(ICO_NVERTS * 4 * sizeof(float));
    g_meshlet_tmpl_idx = ergo_vk_create_buffer(ICO_NIDX * sizeof(uint32_t));
    ergo_vk_upload(g_meshlet_tmpl_pos, tmpl_pos, ICO_NVERTS * 4 * sizeof(float));
    ergo_vk_upload(g_meshlet_tmpl_idx, tmpl_idx, ICO_NIDX * sizeof(uint32_t));

    /* Allocate output buffers */
    size_t out_size = (size_t)MESHLET_MAX * ICO_NVERTS_EXPANDED * 4 * sizeof(float);
    g_meshlet_out_pos = ergo_vk_create_buffer(out_size);
    g_meshlet_out_nv  = ergo_vk_create_buffer(out_size);

    /* Counter + indirect draw buffer (host-visible for zeroing) */
    create_host_buffer(&g_meshlet_counter_buf, &g_meshlet_counter_mem,
                       &g_meshlet_counter_mapped, MESHLET_COUNTER_SIZE,
                       VK_BUFFER_USAGE_STORAGE_BUFFER_BIT |
                       VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT);

    /* Load meshlet compute shader */
    g_meshlet_compute_pipe = ergo_vk_load_shader(
        meshlet_gen_comp_spv, meshlet_gen_comp_spv_size,
        9,   /* bindings 0-8 */
        96   /* push constants: mat4(64) + 8 floats(32) = 96 bytes */
    );

    /* Bind template + output buffers (grid buffers bound per-frame) */
    ergo_vk_bind_buffer(g_meshlet_compute_pipe, 4, g_meshlet_tmpl_pos);
    ergo_vk_bind_buffer(g_meshlet_compute_pipe, 5, g_meshlet_tmpl_idx);
    ergo_vk_bind_buffer(g_meshlet_compute_pipe, 6, g_meshlet_out_pos);
    ergo_vk_bind_buffer(g_meshlet_compute_pipe, 7, g_meshlet_out_nv);

    /* Bind counter buffer (binding 8) — need manual descriptor write
     * since it's a raw VkBuffer, not an ErgoVkBuf */
    {
        VkDescriptorBufferInfo buf_info = {0};
        buf_info.buffer = g_meshlet_counter_buf;
        buf_info.offset = 0;
        buf_info.range = MESHLET_COUNTER_SIZE;

        VkWriteDescriptorSet write = {0};
        write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        write.dstSet = g.pipes[g_meshlet_compute_pipe].ds;
        write.dstBinding = 8;
        write.descriptorCount = 1;
        write.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        write.pBufferInfo = &buf_info;
        vkUpdateDescriptorSets(g.device, 1, &write, 0, NULL);
    }

    g_meshlet_initialized = 1;
    fprintf(stderr, "[ergo_vk] Meshlet pipeline initialized: %d max meshlets, "
            "%d verts/meshlet\n", MESHLET_MAX, ICO_NVERTS_EXPANDED);
}

void ergo_vk_render_meshlets(ErgoVkBuf buf_grad_x, ErgoVkBuf buf_grad_y,
                              ErgoVkBuf buf_grad_z, ErgoVkBuf buf_met_gate,
                              int grid_size, float val_min, float val_max,
                              float world_scale) {
    if (g.headless) return;

    meshlet_lazy_init();

    static int meshlet_frame = 0;
    if (meshlet_frame++ < 3)
        fprintf(stderr, "[ergo_vk] Meshlet frame %d\n", meshlet_frame);

    /* Bind grid buffers to compute pipeline (bindings 0-3) */
    static ErgoVkBuf last_grad_x = 0;
    if (last_grad_x != buf_grad_x) {
        ergo_vk_bind_buffer(g_meshlet_compute_pipe, 0, buf_grad_x);
        ergo_vk_bind_buffer(g_meshlet_compute_pipe, 1, buf_grad_y);
        ergo_vk_bind_buffer(g_meshlet_compute_pipe, 2, buf_grad_z);
        ergo_vk_bind_buffer(g_meshlet_compute_pipe, 3, buf_met_gate);
        last_grad_x = buf_grad_x;
    }

    /* Zero the counter + indirect command */
    uint32_t zero[5] = {0, 0, 1, 0, 0};  /* count=0, vtx=0, inst=1, first=0, firstInst=0 */
    memcpy(g_meshlet_counter_mapped, zero, MESHLET_COUNTER_SIZE);

    /* Build push constants for compute shader */
    float aspect = (float)g.sc_extent.width / (float)g.sc_extent.height;
    Mat4 proj = mat4_perspective(45.0f * 3.14159265f / 180.0f, aspect,
                                 0.01f, 100.0f);
    float ca = cosf(g.cam_azimuth), sa = sinf(g.cam_azimuth);
    float ce = cosf(g.cam_elevation), se = sinf(g.cam_elevation);
    float ex = g.cam_distance * ce * sa;
    float ey = g.cam_distance * se;
    float ez = g.cam_distance * ce * ca;
    Mat4 view = mat4_look_at(ex, ey, ez, 0, 0, 0, 0, 1, 0);
    Mat4 viewProj = mat4_mul(proj, view);

    struct {
        float viewProj[16];       /* 64 bytes */
        float density_threshold;  /* 4 */
        float shell_radius;       /* 4 */
        float world_scale;        /* 4 */
        float cell_size;          /* 4 */
        int   grid_size;          /* 4 */
        float viewport_height;    /* 4 */
        int   max_meshlets;       /* 4 */
        float pad;                /* 4 — total 96 */
    } compute_pc;

    memcpy(compute_pc.viewProj, viewProj.m, 64);
    compute_pc.density_threshold = 0.01f;
    compute_pc.shell_radius = 75.0f * 0.4f;  /* 40% of cell_size */
    compute_pc.world_scale = world_scale;
    compute_pc.cell_size = 75.0f;
    compute_pc.grid_size = grid_size;
    compute_pc.viewport_height = (float)g.sc_extent.height;
    compute_pc.max_meshlets = MESHLET_MAX;
    compute_pc.pad = 0.0f;

    ergo_vk_push_constants(g_meshlet_compute_pipe, &compute_pc, 96);

    /* Dispatch compute: ceil(total_cells / 256) workgroups */
    int total_cells = grid_size * grid_size * grid_size;
    ergo_vk_frame_dispatch(g_meshlet_compute_pipe, (total_cells + 255) / 256);

    /* Barrier: compute writes -> vertex reads + indirect reads.
     * This is recorded into g.cmd_buf by the frame system.
     * But we need the render to happen AFTER compute finishes.
     * Submit the compute frame first, then render. */
    ergo_vk_frame_barrier();

    /* Wait for compute to finish (need counter result for indirect draw) */
    ergo_vk_frame_end();
    ergo_vk_frame_wait();

    /* Now render using the computed meshlet data */
    VK_CHECK(vkWaitForFences(g.device, 1, &g.render_fence[0],
                              VK_TRUE, UINT64_MAX));
    VK_CHECK(vkResetFences(g.device, 1, &g.render_fence[0]));

    uint32_t img_idx;
    VkResult acq = vkAcquireNextImageKHR(g.device, g.swapchain, UINT64_MAX,
                                          g.sem_available[0], VK_NULL_HANDLE,
                                          &img_idx);
    if (acq == VK_ERROR_OUT_OF_DATE_KHR) {
        ergo_vk_frame_begin();
        return;
    }

    /* Bind meshlet output SSBOs + UBO to graphics descriptor set */
    if (!g.meshlet_ds_bound) {
        VkDescriptorBufferInfo buf_infos[2];
        VkWriteDescriptorSet writes[3];

        BufSlot *bp = &g.bufs[g_meshlet_out_pos];
        buf_infos[0].buffer = bp->buffer;
        buf_infos[0].offset = 0;
        buf_infos[0].range = bp->size;

        BufSlot *bn = &g.bufs[g_meshlet_out_nv];
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

        /* UBO at binding 5 */
        VkDescriptorBufferInfo ubo_info = {0};
        ubo_info.buffer = g.render_ubo;
        ubo_info.offset = 0;
        ubo_info.range = sizeof(RenderParams);

        memset(&writes[2], 0, sizeof(VkWriteDescriptorSet));
        writes[2].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[2].dstSet = g.meshlet_ds;
        writes[2].dstBinding = 5;
        writes[2].descriptorCount = 1;
        writes[2].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
        writes[2].pBufferInfo = &ubo_info;

        vkUpdateDescriptorSets(g.device, 3, writes, 0, NULL);
        g.meshlet_ds_bound = 1;
    }

    /* Update render UBO */
    RenderParams params;
    memcpy(params.viewProj, viewProj.m, 64);
    params.cam_x = ex;
    params.cam_y = ey;
    params.cam_z = ez;
    params.cull_mode = g_culling_enabled ? 1.0f : 0.0f;
    params.val_min = val_min;
    params.val_max = val_max;
    params.world_scale = world_scale;
    params.pad = 0.0f;
    memcpy(g.render_ubo_mapped, &params, sizeof(RenderParams));

    /* Record render command buffer */
    VkCommandBuffer cmd = g.render_cmd_buf[0];
    VkCommandBufferBeginInfo begin = {0};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;

    VK_CHECK(vkResetCommandBuffer(cmd, 0));
    VK_CHECK(vkBeginCommandBuffer(cmd, &begin));

    /* Barrier: compute writes -> vertex + indirect reads */
    {
        VkMemoryBarrier mb = {0};
        mb.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT |
                           VK_ACCESS_INDIRECT_COMMAND_READ_BIT;
        vkCmdPipelineBarrier(cmd,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
            VK_PIPELINE_STAGE_VERTEX_SHADER_BIT |
            VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT,
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

    vkCmdBeginRenderPass(cmd, &rp_begin, VK_SUBPASS_CONTENTS_INLINE);

    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS,
                      g.meshlet_pipeline);
    vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS,
                            g.meshlet_layout, 0, 1,
                            &g.meshlet_ds, 0, NULL);

    /* Indirect draw: vertexCount comes from counter buffer offset 4 */
    vkCmdDrawIndirect(cmd, g_meshlet_counter_buf,
                      4,  /* offset past meshlet_count to vertexCount */
                      1, sizeof(VkDrawIndirectCommand));

    vkCmdEndRenderPass(cmd);
    VK_CHECK(vkEndCommandBuffer(cmd));

    VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    VkSubmitInfo si = {0};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.waitSemaphoreCount = 1;
    si.pWaitSemaphores = &g.sem_available[0];
    si.pWaitDstStageMask = &wait_stage;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &cmd;
    si.signalSemaphoreCount = 1;
    si.pSignalSemaphores = &g.sem_finished[0];

    VK_CHECK(vkQueueSubmit(g.compute_queue, 1, &si, g.render_fence[0]));

    VkPresentInfoKHR present = {0};
    present.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    present.waitSemaphoreCount = 1;
    present.pWaitSemaphores = &g.sem_finished[0];
    present.swapchainCount = 1;
    present.pSwapchains = &g.swapchain;
    present.pImageIndices = &img_idx;

    vkQueuePresentKHR(g.compute_queue, &present);

    /* Re-open compute command buffer for next frame */
    ergo_vk_frame_begin();
}

/* ── Cleanup persistent render resources ─────────────────── */

static void render_persistent_cleanup(void) {
    for (uint32_t i = 0; i < g.sc_count; i++) {
        vkDestroySemaphore(g.device, g.sem_available[i], NULL);
        vkDestroySemaphore(g.device, g.sem_finished[i], NULL);
        vkDestroyFence(g.device, g.render_fence[i], NULL);
    }
    if (g.render_ubo) {
        vkDestroyBuffer(g.device, g.render_ubo, NULL);
        vkFreeMemory(g.device, g.render_ubo_mem, NULL);
    }
    if (g.indirect_buf) {
        vkDestroyBuffer(g.device, g.indirect_buf, NULL);
        vkFreeMemory(g.device, g.indirect_mem, NULL);
    }
    if (g_meshlet_counter_buf) {
        vkDestroyBuffer(g.device, g_meshlet_counter_buf, NULL);
        vkFreeMemory(g.device, g_meshlet_counter_mem, NULL);
    }
}

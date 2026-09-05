/* run_glsl.c — trig_identity harness: minimal headless Vulkan runner.
 *
 * Loads a compute SPIR-V (glsl_dump.spv, built from glsl_dump.comp which
 * includes the shared GLSL core ergo_trig32.glsl), feeds it the harness
 * domain file written by dump_trig.ergo ([M f32 domain][M sin][M cos]),
 * re-evaluates sin/cos through the GLSL core, and writes the result file
 * in the same 3-section layout for the byte-compare.
 *
 * Usage: run_glsl <shader.spv> <in.bin> <out.bin> <M>
 *
 * Test-harness simplicity choices (never in the shipping runtime):
 * host-visible COHERENT memory for all SSBOs, one queue, one fence.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vulkan/vulkan.h>

#define CK(expr) do { VkResult r_ = (expr); if (r_ != VK_SUCCESS) { \
    fprintf(stderr, "VK fail %d at %s:%d\n", r_, __FILE__, __LINE__); \
    exit(1); } } while (0)

static void *slurp(const char *path, size_t *n) {
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); exit(1); }
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    void *p = malloc(sz);
    if (fread(p, 1, sz, f) != (size_t)sz) { perror("read"); exit(1); }
    fclose(f); *n = sz; return p;
}

static uint32_t mem_type(VkPhysicalDevice pd, uint32_t bits,
                         VkMemoryPropertyFlags want) {
    VkPhysicalDeviceMemoryProperties mp;
    vkGetPhysicalDeviceMemoryProperties(pd, &mp);
    for (uint32_t i = 0; i < mp.memoryTypeCount; i++)
        if ((bits & (1u << i)) &&
            (mp.memoryTypes[i].propertyFlags & want) == want)
            return i;
    fprintf(stderr, "no memory type\n"); exit(1);
}

int main(int argc, char **argv) {
    if (argc != 5) {
        fprintf(stderr, "usage: run_glsl <shader.spv> <in.bin> <out.bin> <M>\n");
        return 1;
    }
    const char *spv_path = argv[1], *in_path = argv[2], *out_path = argv[3];
    size_t M = (size_t)atol(argv[4]);

    size_t spv_n; void *spv = slurp(spv_path, &spv_n);
    size_t in_n; float *dom = slurp(in_path, &in_n);
    if (in_n < M * 4) { fprintf(stderr, "in.bin too small\n"); return 1; }

    /* instance (headless, no extensions) */
    VkInstance inst;
    VkInstanceCreateInfo ici = { .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO };
    CK(vkCreateInstance(&ici, NULL, &inst));

    /* device with shaderFloat64 + shaderInt64 (required by the core) */
    uint32_t npd = 0;
    CK(vkEnumeratePhysicalDevices(inst, &npd, NULL));
    VkPhysicalDevice *pds = malloc(npd * sizeof(*pds));
    CK(vkEnumeratePhysicalDevices(inst, &npd, pds));
    VkPhysicalDevice pd = VK_NULL_HANDLE;
    uint32_t qfam = 0;
    for (uint32_t i = 0; i < npd && !pd; i++) {
        VkPhysicalDeviceFeatures f;
        vkGetPhysicalDeviceFeatures(pds[i], &f);
        if (!f.shaderFloat64 || !f.shaderInt64) continue;
        uint32_t nq = 0;
        vkGetPhysicalDeviceQueueFamilyProperties(pds[i], &nq, NULL);
        VkQueueFamilyProperties *qp = malloc(nq * sizeof(*qp));
        vkGetPhysicalDeviceQueueFamilyProperties(pds[i], &nq, qp);
        for (uint32_t q = 0; q < nq; q++)
            if (qp[q].queueFlags & VK_QUEUE_COMPUTE_BIT) { pd = pds[i]; qfam = q; break; }
        free(qp);
    }
    if (!pd) { fprintf(stderr, "no fp64+int64 compute device\n"); return 1; }
    VkPhysicalDeviceProperties props;
    vkGetPhysicalDeviceProperties(pd, &props);
    fprintf(stderr, "[run_glsl] device: %s\n", props.deviceName);

    float prio = 1.0f;
    VkDeviceQueueCreateInfo qci = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
        .queueFamilyIndex = qfam, .queueCount = 1, .pQueuePriorities = &prio };
    VkPhysicalDeviceFeatures feats = { .shaderFloat64 = VK_TRUE,
                                       .shaderInt64 = VK_TRUE };
    VkDeviceCreateInfo dci = { .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
        .queueCreateInfoCount = 1, .pQueueCreateInfos = &qci,
        .pEnabledFeatures = &feats };
    VkDevice dev;
    CK(vkCreateDevice(pd, &dci, NULL, &dev));
    VkQueue q;
    vkGetDeviceQueue(dev, qfam, 0, &q);

    /* buffers: domain in, sin bits out, cos bits out (host-visible) */
    VkBuffer bufs[3];
    VkDeviceMemory mems[3];
    size_t sz = M * 4;
    for (int i = 0; i < 3; i++) {
        VkBufferCreateInfo bci = { .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
            .size = sz, .usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT };
        CK(vkCreateBuffer(dev, &bci, NULL, &bufs[i]));
        VkMemoryRequirements req;
        vkGetBufferMemoryRequirements(dev, bufs[i], &req);
        VkMemoryAllocateInfo ai = { .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
            .allocationSize = req.size,
            .memoryTypeIndex = mem_type(pd, req.memoryTypeBits,
                VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                VK_MEMORY_PROPERTY_HOST_COHERENT_BIT) };
        CK(vkAllocateMemory(dev, &ai, NULL, &mems[i]));
        CK(vkBindBufferMemory(dev, bufs[i], mems[i], 0));
    }
    void *mapped;
    CK(vkMapMemory(dev, mems[0], 0, sz, 0, &mapped));
    memcpy(mapped, dom, sz);
    vkUnmapMemory(dev, mems[0]);

    /* descriptors */
    VkDescriptorSetLayoutBinding bnd[3];
    for (int i = 0; i < 3; i++)
        bnd[i] = (VkDescriptorSetLayoutBinding){
            .binding = (uint32_t)i, .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
            .descriptorCount = 1, .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT };
    VkDescriptorSetLayoutCreateInfo lci = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
        .bindingCount = 3, .pBindings = bnd };
    VkDescriptorSetLayout dsl;
    CK(vkCreateDescriptorSetLayout(dev, &lci, NULL, &dsl));
    VkDescriptorPoolSize ps = { VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 3 };
    VkDescriptorPoolCreateInfo pci = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
        .maxSets = 1, .poolSizeCount = 1, .pPoolSizes = &ps };
    VkDescriptorPool dp;
    CK(vkCreateDescriptorPool(dev, &pci, NULL, &dp));
    VkDescriptorSetAllocateInfo dai = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
        .descriptorPool = dp, .descriptorSetCount = 1, .pSetLayouts = &dsl };
    VkDescriptorSet ds;
    CK(vkAllocateDescriptorSets(dev, &dai, &ds));
    for (int i = 0; i < 3; i++) {
        VkDescriptorBufferInfo bi = { bufs[i], 0, sz };
        VkWriteDescriptorSet w = {
            .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
            .dstSet = ds, .dstBinding = (uint32_t)i, .descriptorCount = 1,
            .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
            .pBufferInfo = &bi };
        vkUpdateDescriptorSets(dev, 1, &w, 0, NULL);
    }

    /* pipeline */
    VkShaderModuleCreateInfo sci = {
        .sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
        .codeSize = spv_n, .pCode = spv };
    VkShaderModule sm;
    CK(vkCreateShaderModule(dev, &sci, NULL, &sm));
    VkPipelineLayoutCreateInfo plci = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
        .setLayoutCount = 1, .pSetLayouts = &dsl };
    VkPipelineLayout pl;
    CK(vkCreatePipelineLayout(dev, &plci, NULL, &pl));
    VkComputePipelineCreateInfo cpci = {
        .sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,
        .stage = { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
                   .stage = VK_SHADER_STAGE_COMPUTE_BIT, .module = sm,
                   .pName = "main" },
        .layout = pl };
    VkPipeline pipe;
    CK(vkCreateComputePipelines(dev, VK_NULL_HANDLE, 1, &cpci, NULL, &pipe));

    /* dispatch */
    VkCommandPoolCreateInfo cpi = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
        .queueFamilyIndex = qfam };
    VkCommandPool cp;
    CK(vkCreateCommandPool(dev, &cpi, NULL, &cp));
    VkCommandBufferAllocateInfo cai = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
        .commandPool = cp, .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        .commandBufferCount = 1 };
    VkCommandBuffer cb;
    CK(vkAllocateCommandBuffers(dev, &cai, &cb));
    VkCommandBufferBeginInfo bbi = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO };
    CK(vkBeginCommandBuffer(cb, &bbi));
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_COMPUTE, pipe);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_COMPUTE, pl, 0, 1,
                            &ds, 0, NULL);
    vkCmdDispatch(cb, (uint32_t)((M + 63) / 64), 1, 1);
    CK(vkEndCommandBuffer(cb));
    VkFenceCreateInfo fci = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
    VkFence fence;
    CK(vkCreateFence(dev, &fci, NULL, &fence));
    VkSubmitInfo si = { .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
        .commandBufferCount = 1, .pCommandBuffers = &cb };
    CK(vkQueueSubmit(q, 1, &si, fence));
    CK(vkWaitForFences(dev, 1, &fence, VK_TRUE, UINT64_MAX));

    /* write the same 3-section layout: [domain][sin bits][cos bits] */
    FILE *out = fopen(out_path, "wb");
    if (!out) { perror(out_path); return 1; }
    fwrite(dom, 4, M, out);
    for (int i = 1; i < 3; i++) {
        CK(vkMapMemory(dev, mems[i], 0, sz, 0, &mapped));
        fwrite(mapped, 4, M, out);
        vkUnmapMemory(dev, mems[i]);
    }
    fclose(out);
    fprintf(stderr, "[run_glsl] wrote %s (%zu x f32 x3)\n", out_path, M);
    return 0;
}

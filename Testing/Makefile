# Testing/Makefile — emit assembly for the 4 allocators we care about.
#
# Targets:
#   make ptx     — CUDA PTX (intermediate ISA) for GEO + V8
#   make sass    — real SM_75 machine code for GEO + V8 (RTX 2060)
#   make host    — x86-64 host-side asm for all four (V22 is host-only)
#   make all     — everything
#   make clean
#
# Outputs land in ./asm/.

NVCC        := nvcc
CC          := gcc
CXX         := g++

# RTX 2060 is sm_75. Build for that exact arch so SASS is meaningful.
SM_ARCH     := sm_75
NVCC_ARCH   := -arch=$(SM_ARCH)

# -O3 to see what the optimizer actually does; -lineinfo so SASS keeps source
# correspondence; --ptxas-options=-v dumps register/stack stats during build.
NVCC_OPT    := -O3 -lineinfo --ptxas-options=-v
CFLAGS_HOST := -O3 -march=native -std=c11 -Wall
# -ffp-contract=fast: let GCC fuse separate mul+add into FMA across statements.
# Default 'on' only fuses within a single expression (and SSE intrinsics
# inhibit it entirely). 'fast' is what's needed to see vfmadd in hand-SSE code.
CFLAGS_FMA  := -ffp-contract=fast

ASMDIR      := asm

GEO_SRCS    := GEO/geo_32D_1024_streams.cu GEO/geo_min.cu
V8_SRCS     := V8/aizawa_slab_test.cu
V22_SRC     := V22/v22_driver.c

GEO_NAMES   := geo_32D_1024_streams geo_min
V8_NAMES    := aizawa_slab_test
V9_NAMES    := slab_comparison_test
V16_NAMES   := test_halfstep
V22_NAME    := v22_driver

# V9's slab_comparison_test.cu pulls in V8 headers via "V8/aizawa.cuh"
# so its compile needs -I. (Testing/ as the include root).
NVCC_INCLUDE := -I.

# ----------------------------------------------------------------------------
# Convenience top-level targets
# ----------------------------------------------------------------------------
.PHONY: all ptx sass host bins clean dirs
all: ptx sass host
ptx:  dirs $(addprefix $(ASMDIR)/, $(addsuffix .ptx, $(GEO_NAMES) $(V8_NAMES) $(V9_NAMES) $(V16_NAMES)))
sass: dirs $(addprefix $(ASMDIR)/, $(addsuffix .sass, $(GEO_NAMES) $(V8_NAMES) $(V9_NAMES) $(V16_NAMES)))
host: dirs \
      $(addprefix $(ASMDIR)/, $(addsuffix .host.s, $(GEO_NAMES) $(V8_NAMES) $(V9_NAMES) $(V16_NAMES))) \
      $(ASMDIR)/$(V22_NAME).s \
      $(ASMDIR)/$(V22_NAME).fma.s
bins: dirs \
      $(addprefix $(ASMDIR)/, $(addsuffix .elf, $(GEO_NAMES) $(V8_NAMES))) \
      $(ASMDIR)/$(V22_NAME).elf

dirs:
	@mkdir -p $(ASMDIR)

# ----------------------------------------------------------------------------
# PTX — CUDA's portable IR. One file per .cu.
# ----------------------------------------------------------------------------
$(ASMDIR)/geo_32D_1024_streams.ptx: GEO/geo_32D_1024_streams.cu | dirs
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) -ptx $< -o $@

$(ASMDIR)/geo_min.ptx: GEO/geo_min.cu | dirs
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) -ptx $< -o $@

$(ASMDIR)/aizawa_slab_test.ptx: V8/aizawa_slab_test.cu | dirs
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) -ptx $< -o $@

# V9: slab_comparison_test.cu pulls in V8/*.cuh via path "V8/aizawa.cuh"
# so it needs Testing/ in the include path.
$(ASMDIR)/slab_comparison_test.ptx: V9/slab_comparison_test.cu V9/aizawa_slab_v9.cuh V8/aizawa.cuh V8/aizawa_slab.cuh | dirs
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) $(NVCC_INCLUDE) -ptx $< -o $@

# V16: test_halfstep.cu is self-contained.
$(ASMDIR)/test_halfstep.ptx: V16/test_halfstep.cu V16/viviani_v16_gpu.cuh | dirs
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) -ptx $< -o $@

# ----------------------------------------------------------------------------
# Real binaries — needed before we can dump SASS.
# ----------------------------------------------------------------------------
$(ASMDIR)/geo_32D_1024_streams.elf: GEO/geo_32D_1024_streams.cu | dirs
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) $< -o $@

$(ASMDIR)/geo_min.elf: GEO/geo_min.cu | dirs
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) $< -o $@

$(ASMDIR)/aizawa_slab_test.elf: V8/aizawa_slab_test.cu | dirs
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) $< -o $@

$(ASMDIR)/slab_comparison_test.elf: V9/slab_comparison_test.cu V9/aizawa_slab_v9.cuh V8/aizawa.cuh V8/aizawa_slab.cuh | dirs
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) $(NVCC_INCLUDE) $< -o $@

$(ASMDIR)/test_halfstep.elf: V16/test_halfstep.cu V16/viviani_v16_gpu.cuh | dirs
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) $< -o $@

$(ASMDIR)/$(V22_NAME).elf: $(V22_SRC) V22/squaragon_v2.h V22/squaragon_v2_forces.h V22/squaragon_v2_dna.h | dirs
	$(CC) $(CFLAGS_HOST) $(V22_SRC) -o $@ -lm

# ----------------------------------------------------------------------------
# SASS — actual SM machine code (post register allocation).
# ----------------------------------------------------------------------------
$(ASMDIR)/%.sass: $(ASMDIR)/%.elf
	cuobjdump --dump-sass $< > $@

# ----------------------------------------------------------------------------
# Host x86-64 asm for .cu files.
#   nvcc with -keep emits the host-side .s; we copy the most useful one
#   (the post-cudafe combined .cpp1.ii intermediate) out of the keep dir.
# ----------------------------------------------------------------------------
define HOST_ASM_RULE
$(ASMDIR)/$(2).host.s: $(1) | dirs
	@mkdir -p $(ASMDIR)/keep_$(2)
	@# Step 1: nvcc -keep emits foo.cpp1.ii — fully preprocessed host TU
	@# with all CUDA constructs already lowered to host-side stubs.
	$(NVCC) $(NVCC_ARCH) $(NVCC_OPT) $(3) -keep -keep-dir $(ASMDIR)/keep_$(2) -c $(1) -o $(ASMDIR)/$(2).tmp.o
	@# Step 2: cudafe1.cpp is the fully-lowered host TU (no <<<>>>, no __global__).
	@# It still includes crt/host_runtime.h, so we need CUDA's include path.
	$(CXX) -O3 -march=native -std=c++17 -S -masm=intel -fverbose-asm \
	    -fext-numeric-literals \
	    -I$(shell dirname $(shell which nvcc))/../include \
	    -x c++ $(ASMDIR)/keep_$(2)/$(2).cudafe1.cpp \
	    -o $$@
endef

$(eval $(call HOST_ASM_RULE,GEO/geo_32D_1024_streams.cu,geo_32D_1024_streams,))
$(eval $(call HOST_ASM_RULE,GEO/geo_min.cu,geo_min,))
$(eval $(call HOST_ASM_RULE,V8/aizawa_slab_test.cu,aizawa_slab_test,))
$(eval $(call HOST_ASM_RULE,V9/slab_comparison_test.cu,slab_comparison_test,$(NVCC_INCLUDE)))
$(eval $(call HOST_ASM_RULE,V16/test_halfstep.cu,test_halfstep,))

# V22 is pure C — straight gcc -S.
# Two variants:
#   v22_driver.s         — strict IEEE math, no FMA fusion (baseline)
#   v22_driver.fma.s     — same source with -ffp-contract=fast (allows vfmadd*)
$(ASMDIR)/$(V22_NAME).s: $(V22_SRC) V22/squaragon_v2.h V22/squaragon_v2_forces.h V22/squaragon_v2_dna.h | dirs
	$(CC) $(CFLAGS_HOST) -S -masm=intel -fverbose-asm $(V22_SRC) -o $@

$(ASMDIR)/$(V22_NAME).fma.s: $(V22_SRC) V22/squaragon_v2.h V22/squaragon_v2_forces.h V22/squaragon_v2_dna.h | dirs
	$(CC) $(CFLAGS_HOST) $(CFLAGS_FMA) -S -masm=intel -fverbose-asm $(V22_SRC) -o $@

# Comparison driver — emit each function as a labeled, non-inlined symbol so
# we can compare scalar vs hand-rolled SSE under three flag regimes.
V22_CMP_SRC := V22/v22_compare.c
V22_CMP_DEPS := V22/v22_compare.c V22/squaragon_v2.h

$(ASMDIR)/v22_compare.base.s: $(V22_CMP_DEPS) | dirs
	$(CC) $(CFLAGS_HOST) -S -masm=intel -fverbose-asm $(V22_CMP_SRC) -o $@

$(ASMDIR)/v22_compare.fma.s: $(V22_CMP_DEPS) | dirs
	$(CC) $(CFLAGS_HOST) -ffp-contract=fast -S -masm=intel -fverbose-asm $(V22_CMP_SRC) -o $@

$(ASMDIR)/v22_compare.fast.s: $(V22_CMP_DEPS) | dirs
	$(CC) $(CFLAGS_HOST) -ffast-math -S -masm=intel -fverbose-asm $(V22_CMP_SRC) -o $@

# And the matching binaries, for runtime correctness/timing checks.
$(ASMDIR)/v22_compare.base.elf: $(V22_CMP_DEPS) | dirs
	$(CC) $(CFLAGS_HOST) $(V22_CMP_SRC) -o $@ -lm

$(ASMDIR)/v22_compare.fma.elf: $(V22_CMP_DEPS) | dirs
	$(CC) $(CFLAGS_HOST) -ffp-contract=fast $(V22_CMP_SRC) -o $@ -lm

$(ASMDIR)/v22_compare.fast.elf: $(V22_CMP_DEPS) | dirs
	$(CC) $(CFLAGS_HOST) -ffast-math $(V22_CMP_SRC) -o $@ -lm

.PHONY: compare
compare: $(ASMDIR)/v22_compare.base.s $(ASMDIR)/v22_compare.fma.s $(ASMDIR)/v22_compare.fast.s \
         $(ASMDIR)/v22_compare.base.elf $(ASMDIR)/v22_compare.fma.elf $(ASMDIR)/v22_compare.fast.elf

# ----------------------------------------------------------------------------
clean:
	rm -rf $(ASMDIR)

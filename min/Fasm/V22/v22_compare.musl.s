	.file	"v22_compare.c"
	.text
	.p2align 4
	.globl	bench_scalar
	.type	bench_scalar, @function
bench_scalar:
.LFB597:
	.cfi_startproc
	vmovss	.LC0(%rip), %xmm1
	vmovss	(%rdi), %xmm2
	vxorps	%xmm7, %xmm7, %xmm7
	vmovss	4(%rdi), %xmm8
	vmovss	.LC1(%rip), %xmm0
	vmovaps	%xmm2, %xmm4
	vmovss	8(%rdi), %xmm5
	vmovss	16(%rdi), %xmm9
	vmulss	%xmm1, %xmm8, %xmm3
	vfmsub132ss	%xmm0, %xmm3, %xmm4
	vmovaps	%xmm3, %xmm6
	vmulss	%xmm0, %xmm8, %xmm3
	vfmadd231ss	%xmm0, %xmm2, %xmm6
	vaddss	%xmm2, %xmm4, %xmm4
	vaddss	%xmm4, %xmm6, %xmm6
	vmovaps	%xmm2, %xmm4
	vfmadd132ss	%xmm1, %xmm3, %xmm4
	vfnmadd231ss	%xmm1, %xmm2, %xmm3
	vmovss	12(%rdi), %xmm2
	vmovaps	%xmm2, %xmm10
	vaddss	%xmm7, %xmm6, %xmm6
	vaddss	%xmm8, %xmm4, %xmm4
	vaddss	%xmm4, %xmm3, %xmm3
	vmovss	.LC3(%rip), %xmm4
	vfmadd132ss	%xmm4, %xmm5, %xmm5
	vaddss	%xmm7, %xmm3, %xmm3
	vaddss	%xmm7, %xmm5, %xmm8
	vmulss	%xmm1, %xmm9, %xmm5
	vmovss	20(%rdi), %xmm7
	vfmadd132ss	%xmm4, %xmm7, %xmm7
	vfmsub132ss	%xmm0, %xmm5, %xmm10
	vfmadd231ss	%xmm0, %xmm2, %xmm5
	vaddss	%xmm8, %xmm7, %xmm7
	vmovss	32(%rdi), %xmm8
	vaddss	%xmm2, %xmm10, %xmm10
	vaddss	%xmm10, %xmm5, %xmm5
	vmulss	%xmm0, %xmm9, %xmm10
	vaddss	%xmm6, %xmm5, %xmm5
	vmovaps	%xmm2, %xmm6
	vfmadd132ss	%xmm1, %xmm10, %xmm6
	vfnmadd132ss	%xmm1, %xmm10, %xmm2
	vaddss	%xmm9, %xmm6, %xmm6
	vmovss	28(%rdi), %xmm9
	vaddss	%xmm6, %xmm2, %xmm2
	vaddss	%xmm3, %xmm2, %xmm6
	vmulss	%xmm1, %xmm9, %xmm3
	vmovss	24(%rdi), %xmm2
	vmovaps	%xmm2, %xmm10
	vfmsub132ss	%xmm0, %xmm3, %xmm10
	vfmadd231ss	%xmm0, %xmm2, %xmm3
	vaddss	%xmm2, %xmm10, %xmm10
	vaddss	%xmm10, %xmm3, %xmm3
	vmulss	%xmm0, %xmm9, %xmm10
	vaddss	%xmm5, %xmm3, %xmm3
	vmovaps	%xmm2, %xmm5
	vfmadd132ss	%xmm1, %xmm10, %xmm5
	vfnmadd132ss	%xmm1, %xmm10, %xmm2
	vaddss	%xmm9, %xmm5, %xmm5
	vmovss	40(%rdi), %xmm9
	vaddss	%xmm5, %xmm2, %xmm2
	vmulss	%xmm1, %xmm9, %xmm5
	vaddss	%xmm6, %xmm2, %xmm6
	vmovaps	%xmm8, %xmm2
	vfmadd132ss	%xmm4, %xmm8, %xmm2
	vaddss	%xmm7, %xmm2, %xmm8
	vmovss	36(%rdi), %xmm2
	vmovss	44(%rdi), %xmm7
	vmovaps	%xmm2, %xmm10
	vfmadd132ss	%xmm4, %xmm7, %xmm7
	vfmsub132ss	%xmm0, %xmm5, %xmm10
	vfmadd231ss	%xmm0, %xmm2, %xmm5
	vaddss	%xmm8, %xmm7, %xmm7
	vmovss	56(%rdi), %xmm8
	vaddss	%xmm2, %xmm10, %xmm10
	vaddss	%xmm10, %xmm5, %xmm5
	vmulss	%xmm0, %xmm9, %xmm10
	vaddss	%xmm3, %xmm5, %xmm5
	vmovaps	%xmm2, %xmm3
	vfmadd132ss	%xmm1, %xmm10, %xmm3
	vfnmadd132ss	%xmm1, %xmm10, %xmm2
	vaddss	%xmm9, %xmm3, %xmm3
	vmovss	52(%rdi), %xmm9
	vaddss	%xmm3, %xmm2, %xmm2
	vmulss	%xmm1, %xmm9, %xmm3
	vaddss	%xmm6, %xmm2, %xmm6
	vmovss	48(%rdi), %xmm2
	vmovaps	%xmm2, %xmm10
	vfmsub132ss	%xmm0, %xmm3, %xmm10
	vfmadd231ss	%xmm0, %xmm2, %xmm3
	vaddss	%xmm2, %xmm10, %xmm10
	vaddss	%xmm10, %xmm3, %xmm3
	vmulss	%xmm0, %xmm9, %xmm10
	vaddss	%xmm5, %xmm3, %xmm3
	vmovaps	%xmm2, %xmm5
	vfmadd132ss	%xmm1, %xmm10, %xmm5
	vfnmadd132ss	%xmm1, %xmm10, %xmm2
	vaddss	%xmm9, %xmm5, %xmm5
	vmovss	64(%rdi), %xmm9
	vaddss	%xmm5, %xmm2, %xmm2
	vmulss	%xmm1, %xmm9, %xmm5
	vaddss	%xmm6, %xmm2, %xmm6
	vmovaps	%xmm8, %xmm2
	vfmadd132ss	%xmm4, %xmm8, %xmm2
	vaddss	%xmm7, %xmm2, %xmm8
	vmovss	60(%rdi), %xmm2
	vmovss	68(%rdi), %xmm7
	vmovaps	%xmm2, %xmm10
	vfmadd132ss	%xmm4, %xmm7, %xmm7
	vfmsub132ss	%xmm0, %xmm5, %xmm10
	vfmadd231ss	%xmm0, %xmm2, %xmm5
	vaddss	%xmm8, %xmm7, %xmm7
	vmovss	80(%rdi), %xmm8
	vaddss	%xmm2, %xmm10, %xmm10
	vaddss	%xmm10, %xmm5, %xmm5
	vmulss	%xmm0, %xmm9, %xmm10
	vaddss	%xmm3, %xmm5, %xmm5
	vmovaps	%xmm2, %xmm3
	vfmadd132ss	%xmm1, %xmm10, %xmm3
	vfnmadd132ss	%xmm1, %xmm10, %xmm2
	vaddss	%xmm9, %xmm3, %xmm3
	vmovss	76(%rdi), %xmm9
	vaddss	%xmm3, %xmm2, %xmm2
	vmulss	%xmm1, %xmm9, %xmm3
	vaddss	%xmm6, %xmm2, %xmm6
	vmovss	72(%rdi), %xmm2
	vmovaps	%xmm2, %xmm10
	vfmsub132ss	%xmm0, %xmm3, %xmm10
	vfmadd231ss	%xmm0, %xmm2, %xmm3
	vaddss	%xmm2, %xmm10, %xmm10
	vaddss	%xmm10, %xmm3, %xmm3
	vmulss	%xmm0, %xmm9, %xmm10
	vaddss	%xmm5, %xmm3, %xmm3
	vmovaps	%xmm2, %xmm5
	vfmadd132ss	%xmm1, %xmm10, %xmm5
	vfnmadd132ss	%xmm1, %xmm10, %xmm2
	vaddss	%xmm9, %xmm5, %xmm5
	vmovss	88(%rdi), %xmm9
	vaddss	%xmm5, %xmm2, %xmm2
	vmulss	%xmm1, %xmm9, %xmm5
	vaddss	%xmm6, %xmm2, %xmm6
	vmovaps	%xmm8, %xmm2
	vfmadd132ss	%xmm4, %xmm8, %xmm2
	vaddss	%xmm7, %xmm2, %xmm8
	vmovss	84(%rdi), %xmm2
	vmovss	92(%rdi), %xmm7
	vmovaps	%xmm2, %xmm10
	vfmadd132ss	%xmm4, %xmm7, %xmm7
	vfmsub132ss	%xmm0, %xmm5, %xmm10
	vfmadd231ss	%xmm0, %xmm2, %xmm5
	vaddss	%xmm8, %xmm7, %xmm7
	vmovss	104(%rdi), %xmm8
	vaddss	%xmm2, %xmm10, %xmm10
	vaddss	%xmm10, %xmm5, %xmm5
	vmulss	%xmm0, %xmm9, %xmm10
	vaddss	%xmm3, %xmm5, %xmm5
	vmovaps	%xmm2, %xmm3
	vfmadd132ss	%xmm1, %xmm10, %xmm3
	vfnmadd132ss	%xmm1, %xmm10, %xmm2
	vaddss	%xmm9, %xmm3, %xmm3
	vmovss	100(%rdi), %xmm9
	vaddss	%xmm3, %xmm2, %xmm2
	vmulss	%xmm1, %xmm9, %xmm3
	vaddss	%xmm6, %xmm2, %xmm6
	vmovss	96(%rdi), %xmm2
	vmovaps	%xmm2, %xmm10
	vfmsub132ss	%xmm0, %xmm3, %xmm10
	vfmadd231ss	%xmm0, %xmm2, %xmm3
	vaddss	%xmm2, %xmm10, %xmm10
	vaddss	%xmm10, %xmm3, %xmm3
	vmulss	%xmm0, %xmm9, %xmm10
	vaddss	%xmm5, %xmm3, %xmm3
	vmovaps	%xmm2, %xmm5
	vfmadd132ss	%xmm1, %xmm10, %xmm5
	vfnmadd132ss	%xmm1, %xmm10, %xmm2
	vaddss	%xmm9, %xmm5, %xmm5
	vmovss	112(%rdi), %xmm9
	vaddss	%xmm5, %xmm2, %xmm2
	vmulss	%xmm1, %xmm9, %xmm5
	vaddss	%xmm6, %xmm2, %xmm6
	vmovaps	%xmm8, %xmm2
	vfmadd132ss	%xmm4, %xmm8, %xmm2
	vaddss	%xmm7, %xmm2, %xmm8
	vmovss	108(%rdi), %xmm2
	vmovss	116(%rdi), %xmm7
	vmovaps	%xmm2, %xmm10
	vfmadd132ss	%xmm4, %xmm7, %xmm7
	vfmsub132ss	%xmm0, %xmm5, %xmm10
	vfmadd231ss	%xmm0, %xmm2, %xmm5
	vaddss	%xmm2, %xmm10, %xmm10
	vaddss	%xmm10, %xmm5, %xmm5
	vmulss	%xmm0, %xmm9, %xmm10
	vaddss	%xmm3, %xmm5, %xmm5
	vmovaps	%xmm2, %xmm3
	vfmadd132ss	%xmm1, %xmm10, %xmm3
	vfnmadd132ss	%xmm1, %xmm10, %xmm2
	vmovss	124(%rdi), %xmm10
	vaddss	%xmm9, %xmm3, %xmm3
	vaddss	%xmm8, %xmm7, %xmm9
	vmovss	128(%rdi), %xmm7
	vfmadd132ss	%xmm4, %xmm7, %xmm7
	vaddss	%xmm3, %xmm2, %xmm2
	vmulss	%xmm1, %xmm10, %xmm3
	vaddss	%xmm6, %xmm2, %xmm6
	vmovss	120(%rdi), %xmm2
	vaddss	%xmm9, %xmm7, %xmm7
	vmovss	136(%rdi), %xmm9
	vmovaps	%xmm2, %xmm8
	vfmsub132ss	%xmm0, %xmm3, %xmm8
	vfmadd231ss	%xmm0, %xmm2, %xmm3
	vaddss	%xmm2, %xmm8, %xmm8
	vaddss	%xmm8, %xmm3, %xmm3
	vaddss	%xmm5, %xmm3, %xmm8
	vmulss	%xmm0, %xmm10, %xmm5
	vmovaps	%xmm2, %xmm3
	vfmadd132ss	%xmm1, %xmm5, %xmm3
	vfnmadd132ss	%xmm1, %xmm5, %xmm2
	vmulss	%xmm1, %xmm9, %xmm5
	vaddss	%xmm10, %xmm3, %xmm3
	vaddss	%xmm3, %xmm2, %xmm2
	vmovss	140(%rdi), %xmm3
	vfmadd132ss	%xmm4, %xmm3, %xmm3
	vaddss	%xmm6, %xmm2, %xmm6
	vmovss	132(%rdi), %xmm2
	vmovaps	%xmm2, %xmm10
	vfmsub132ss	%xmm0, %xmm5, %xmm10
	vfmadd231ss	%xmm0, %xmm2, %xmm5
	vmulss	%xmm0, %xmm9, %xmm0
	vaddss	%xmm2, %xmm10, %xmm10
	vaddss	%xmm10, %xmm5, %xmm5
	vaddss	%xmm8, %xmm5, %xmm5
	vmovaps	%xmm2, %xmm8
	vfmadd132ss	%xmm1, %xmm0, %xmm8
	vfnmadd132ss	%xmm1, %xmm0, %xmm2
	vaddss	%xmm7, %xmm3, %xmm0
	vaddss	%xmm9, %xmm8, %xmm8
	vaddss	%xmm8, %xmm2, %xmm2
	vaddss	%xmm6, %xmm2, %xmm2
	vmulss	%xmm2, %xmm2, %xmm2
	vfmadd132ss	%xmm5, %xmm2, %xmm5
	vfmadd132ss	%xmm0, %xmm5, %xmm0
	vsqrtss	%xmm0, %xmm0, %xmm0
	vdivss	144(%rdi), %xmm0, %xmm0
	ret
	.cfi_endproc
.LFE597:
	.size	bench_scalar, .-bench_scalar
	.p2align 4
	.globl	bench_handsse
	.type	bench_handsse, @function
bench_handsse:
.LFB598:
	.cfi_startproc
	vbroadcastss	%xmm0, %xmm1
	vxorps	%xmm3, %xmm3, %xmm3
	vmovaps	%xmm0, %xmm2
	vbroadcastss	.LC0(%rip), %xmm14
	vmulps	.LC5(%rip), %xmm1, %xmm4
	vxorps	%xmm0, %xmm0, %xmm0
	vmulps	.LC4(%rip), %xmm1, %xmm7
	vmulss	%xmm0, %xmm2, %xmm2
	vmulss	.LC0(%rip), %xmm2, %xmm15
	vaddps	%xmm3, %xmm4, %xmm6
	vmovaps	%xmm4, %xmm8
	vmovaps	%xmm4, %xmm12
	vaddps	%xmm3, %xmm7, %xmm5
	vmulps	%xmm14, %xmm7, %xmm11
	vbroadcastss	.LC1(%rip), %xmm3
	vaddss	%xmm0, %xmm2, %xmm0
	vbroadcastss	%xmm2, %xmm10
	vmulps	%xmm3, %xmm7, %xmm9
	vbroadcastss	%xmm15, %xmm15
	vaddss	%xmm0, %xmm2, %xmm0
	vfmadd132ps	%xmm3, %xmm11, %xmm12
	vfmsub132ps	%xmm4, %xmm11, %xmm3
	vfnmadd132ps	%xmm14, %xmm9, %xmm8
	vfmadd132ps	%xmm4, %xmm9, %xmm14
	vaddss	%xmm0, %xmm2, %xmm0
	vaddps	%xmm6, %xmm12, %xmm12
	vmulss	.LC1(%rip), %xmm2, %xmm6
	vbroadcastss	%xmm0, %xmm0
	vaddps	%xmm4, %xmm0, %xmm0
	vaddps	%xmm8, %xmm5, %xmm5
	vsubps	%xmm15, %xmm9, %xmm8
	vaddps	%xmm12, %xmm3, %xmm2
	vaddps	%xmm15, %xmm9, %xmm9
	vaddps	%xmm4, %xmm0, %xmm0
	vaddps	%xmm14, %xmm5, %xmm5
	vbroadcastss	%xmm6, %xmm6
	vaddps	%xmm6, %xmm11, %xmm13
	vaddps	%xmm10, %xmm2, %xmm2
	vsubps	%xmm11, %xmm6, %xmm6
	vaddps	%xmm4, %xmm0, %xmm0
	vaddps	%xmm7, %xmm5, %xmm5
	vaddps	%xmm13, %xmm2, %xmm2
	vaddps	%xmm4, %xmm0, %xmm0
	vaddps	%xmm8, %xmm5, %xmm5
	vaddps	%xmm6, %xmm2, %xmm2
	vaddps	%xmm4, %xmm0, %xmm0
	vaddps	%xmm9, %xmm5, %xmm5
	vaddps	%xmm7, %xmm2, %xmm2
	vaddps	%xmm4, %xmm0, %xmm0
	vaddps	%xmm10, %xmm5, %xmm5
	vaddps	%xmm9, %xmm2, %xmm2
	vhaddps	%xmm0, %xmm0, %xmm0
	vaddps	%xmm6, %xmm5, %xmm5
	vaddps	%xmm8, %xmm2, %xmm2
	vhaddps	%xmm0, %xmm0, %xmm0
	vaddps	%xmm13, %xmm5, %xmm5
	vhaddps	%xmm2, %xmm2, %xmm2
	vhaddps	%xmm5, %xmm5, %xmm5
	vhaddps	%xmm2, %xmm2, %xmm2
	vhaddps	%xmm5, %xmm5, %xmm5
	vmulps	%xmm5, %xmm5, %xmm5
	vfmadd132ps	%xmm2, %xmm5, %xmm2
	vfmadd132ps	%xmm0, %xmm2, %xmm0
	vsqrtps	%xmm0, %xmm0
	vdivps	%xmm1, %xmm0, %xmm0
	ret
	.cfi_endproc
.LFE598:
	.size	bench_handsse, .-bench_handsse
	.section	.rodata.str1.1,"aMS",@progbits,1
.LC8:
	.string	"faster"
.LC9:
	.string	"slower"
	.section	.rodata.str1.8,"aMS",@progbits,1
	.align 8
.LC19:
	.string	"scalar:   r=%g  %.3f ns/call  (sink=%g)\n"
	.align 8
.LC20:
	.string	"hand-sse: r=%g  %.3f ns/call  (sink=%g)\n"
	.align 8
.LC21:
	.string	"speedup: hand-sse is %.2fx %s than scalar\n"
	.section	.text.startup,"ax",@progbits
	.p2align 4
	.globl	main
	.type	main, @function
main:
.LFB599:
	.cfi_startproc
	vxorps	%xmm2, %xmm2, %xmm2
	subq	$296, %rsp
	.cfi_def_cfa_offset 304
	vmovss	.LC11(%rip), %xmm7
	vmovss	.LC13(%rip), %xmm5
	vcvtsi2ssl	%edi, %xmm2, %xmm3
	movq	%rbp, 256(%rsp)
	vfmadd132ss	.LC10(%rip), %xmm7, %xmm3
	.cfi_offset 6, -48
	movl	$1000000, %ebp
	movq	%r14, 280(%rsp)
	vmovss	.LC12(%rip), %xmm4
	movq	%r15, 288(%rsp)
	movq	%rbx, 248(%rsp)
	movq	%r12, 264(%rsp)
	vmulss	%xmm5, %xmm3, %xmm1
	movq	%fs:40, %rax
	movq	%rax, 232(%rsp)
	movl	%edi, %eax
	leaq	80(%rsp), %rdi
	vmovss	%xmm3, 8(%rsp)
	vmovss	%xmm3, 224(%rsp)
	vmovss	%xmm4, 228(%rsp)
	vmovsldup	%xmm1, %xmm0
	vmovss	%xmm1, 92(%rsp)
	vmovss	%xmm1, 108(%rsp)
	vmovss	%xmm1, 128(%rsp)
	vmovss	%xmm1, 136(%rsp)
	vmovlps	%xmm0, 80(%rsp)
	vxorps	.LC14(%rip), %xmm1, %xmm0
	vmovss	%xmm1, 140(%rsp)
	vmovss	%xmm0, 96(%rsp)
	vmovss	%xmm0, 104(%rsp)
	vmovss	%xmm0, 116(%rsp)
	vmovss	%xmm0, 120(%rsp)
	movl	$0x00000000, 88(%rsp)
	movl	$0x00000000, 100(%rsp)
	movl	$0x00000000, 112(%rsp)
	movl	$0x00000000, 124(%rsp)
	movl	$0x00000000, 132(%rsp)
	movl	$0x00000000, 144(%rsp)
	vmovss	%xmm1, 160(%rsp)
	vmovss	%xmm1, 180(%rsp)
	vmovss	%xmm1, 184(%rsp)
	vmovss	%xmm1, 192(%rsp)
	vmovss	%xmm1, 208(%rsp)
	movl	$0x00000000, 156(%rsp)
	movl	$0x00000000, 168(%rsp)
	movl	$0x00000000, 176(%rsp)
	movl	$0x00000000, 188(%rsp)
	movl	$0x00000000, 200(%rsp)
	movl	$0x00000000, 212(%rsp)
	vmovss	%xmm0, 148(%rsp)
	vmovss	%xmm0, 152(%rsp)
	vmovss	%xmm0, 164(%rsp)
	vmovss	%xmm0, 172(%rsp)
	vmovss	%xmm0, 196(%rsp)
	vmovss	%xmm0, 204(%rsp)
	vmovss	%xmm0, 216(%rsp)
	vmovss	%xmm0, 220(%rsp)
	.cfi_offset 14, -24
	.cfi_offset 15, -16
	.cfi_offset 3, -56
	.cfi_offset 12, -40
	call	bench_scalar
	vmovd	%xmm0, %r14d
	vmovss	8(%rsp), %xmm0
	call	bench_handsse
	cmpl	$1, %eax
	vmovss	8(%rsp), %xmm3
	vmovd	%xmm0, %r15d
	jle	.L5
	movq	8(%rsi), %rdi
	call	atoi@PLT
	vmovss	8(%rsp), %xmm3
	movl	%eax, %ebp
.L5:
	movl	$38912, %edi
	vmovss	%xmm3, 8(%rsp)
	call	malloc@PLT
	vmovss	.LC15(%rip), %xmm6
	xorl	%edx, %edx
	vmovss	.LC13(%rip), %xmm5
	vmovss	.LC12(%rip), %xmm4
	vmovss	8(%rsp), %xmm3
	movq	%rax, %rbx
	vxorps	%xmm2, %xmm2, %xmm2
	.p2align 4
	.p2align 3
.L6:
	vcvtsi2ssl	%edx, %xmm2, %xmm0
	addl	$1, %edx
	movl	$0x00000000, 8(%rax)
	addq	$152, %rax
	vmovss	%xmm4, -4(%rax)
	movl	$0x00000000, -132(%rax)
	movl	$0x00000000, -120(%rax)
	vfmadd132ss	%xmm6, %xmm3, %xmm0
	movl	$0x00000000, -108(%rax)
	movl	$0x00000000, -100(%rax)
	movl	$0x00000000, -88(%rax)
	movl	$0x00000000, -76(%rax)
	movl	$0x00000000, -64(%rax)
	vmovss	%xmm0, -8(%rax)
	vmulss	%xmm5, %xmm0, %xmm0
	movl	$0x00000000, -56(%rax)
	movl	$0x00000000, -44(%rax)
	vmovsldup	%xmm0, %xmm1
	vmovss	%xmm0, -140(%rax)
	vmovss	%xmm0, -124(%rax)
	vmovss	%xmm0, -104(%rax)
	vmovss	%xmm0, -96(%rax)
	vmovlps	%xmm1, -152(%rax)
	vxorps	.LC14(%rip), %xmm0, %xmm1
	vmovss	%xmm0, -92(%rax)
	vmovss	%xmm1, -136(%rax)
	vmovss	%xmm1, -128(%rax)
	vmovss	%xmm1, -116(%rax)
	vmovss	%xmm1, -112(%rax)
	vmovss	%xmm1, -84(%rax)
	vmovss	%xmm1, -80(%rax)
	vmovss	%xmm0, -72(%rax)
	vmovss	%xmm1, -68(%rax)
	vmovss	%xmm1, -60(%rax)
	vmovss	%xmm0, -52(%rax)
	vmovss	%xmm0, -48(%rax)
	vmovss	%xmm0, -40(%rax)
	vmovss	%xmm1, -36(%rax)
	movl	$0x00000000, -32(%rax)
	vmovss	%xmm1, -28(%rax)
	vmovss	%xmm0, -24(%rax)
	movl	$0x00000000, -20(%rax)
	vmovss	%xmm1, -16(%rax)
	vmovss	%xmm1, -12(%rax)
	cmpl	$256, %edx
	jne	.L6
	leaq	48(%rsp), %rsi
	movl	$1, %edi
	movq	$0x000000000, 32(%rsp)
	movq	$0x000000000, 40(%rsp)
	call	clock_gettime@PLT
	testl	%ebp, %ebp
	jle	.L7
	movq	%r13, 272(%rsp)
	.cfi_offset 13, -32
	xorl	%r13d, %r13d
	.p2align 4
	.p2align 3
.L8:
	movzbl	%r13b, %edi
	addl	$1, %r13d
	imulq	$152, %rdi, %rdi
	addq	%rbx, %rdi
	call	bench_scalar
	vcvtss2sd	%xmm0, %xmm0, %xmm0
	vaddsd	32(%rsp), %xmm0, %xmm0
	vmovsd	%xmm0, 32(%rsp)
	cmpl	%r13d, %ebp
	jne	.L8
	leaq	64(%rsp), %r12
	movl	$1, %edi
	movq	%r12, %rsi
	call	clock_gettime@PLT
	vxorps	%xmm2, %xmm2, %xmm2
	movq	72(%rsp), %rax
	vmovsd	.LC17(%rip), %xmm7
	subq	56(%rsp), %rax
	leaq	48(%rsp), %rsi
	movl	$1, %edi
	vcvtsi2sdq	%rax, %xmm2, %xmm1
	movq	64(%rsp), %rax
	subq	48(%rsp), %rax
	vmovsd	%xmm7, 8(%rsp)
	vcvtsi2sdq	%rax, %xmm2, %xmm0
	vfmadd132sd	%xmm7, %xmm0, %xmm1
	vmovsd	%xmm1, 16(%rsp)
	call	clock_gettime@PLT
	xorl	%eax, %eax
	.p2align 4
	.p2align 3
.L9:
	movzbl	%al, %edx
	addl	$1, %eax
	imulq	$152, %rdx, %rdx
	vmovss	144(%rbx,%rdx), %xmm0
	call	bench_handsse
	vcvtss2sd	%xmm0, %xmm0, %xmm0
	vaddsd	40(%rsp), %xmm0, %xmm0
	vmovsd	%xmm0, 40(%rsp)
	cmpl	%eax, %r13d
	jne	.L9
	movq	272(%rsp), %r13
	.cfi_restore 13
.L12:
	movq	%r12, %rsi
	movl	$1, %edi
	call	clock_gettime@PLT
	vxorps	%xmm2, %xmm2, %xmm2
	movq	72(%rsp), %rax
	movq	%rbx, %rdi
	subq	56(%rsp), %rax
	vcvtsi2sdq	%rax, %xmm2, %xmm1
	movq	64(%rsp), %rax
	subq	48(%rsp), %rax
	vcvtsi2sdq	%rax, %xmm2, %xmm0
	vfmadd132sd	8(%rsp), %xmm0, %xmm1
	vmovsd	%xmm1, 8(%rsp)
	call	free@PLT
	vxorps	%xmm2, %xmm2, %xmm2
	vmovd	%r14d, %xmm6
	vmovsd	.LC18(%rip), %xmm4
	vmulsd	16(%rsp), %xmm4, %xmm1
	vcvtsi2sdl	%ebp, %xmm2, %xmm2
	vmovapd	%xmm2, %xmm3
	vmovsd	32(%rsp), %xmm2
	leaq	.LC19(%rip), %rdi
	movl	$3, %eax
	vcvtss2sd	%xmm6, %xmm6, %xmm0
	vmovsd	%xmm3, 24(%rsp)
	vdivsd	%xmm3, %xmm1, %xmm1
	call	printf@PLT
	vmovsd	40(%rsp), %xmm2
	vmovd	%r15d, %xmm4
	vmovsd	.LC18(%rip), %xmm5
	leaq	.LC20(%rip), %rdi
	vmulsd	8(%rsp), %xmm5, %xmm1
	movl	$3, %eax
	vcvtss2sd	%xmm4, %xmm4, %xmm0
	vdivsd	24(%rsp), %xmm1, %xmm1
	call	printf@PLT
	vmovsd	16(%rsp), %xmm6
	vmovsd	8(%rsp), %xmm7
	leaq	.LC9(%rip), %rax
	leaq	.LC8(%rip), %rsi
	vdivsd	%xmm7, %xmm6, %xmm0
	vcomisd	%xmm7, %xmm6
	leaq	.LC21(%rip), %rdi
	cmovbe	%rax, %rsi
	movl	$1, %eax
	call	printf@PLT
	movq	232(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L23
	movq	248(%rsp), %rbx
	movq	256(%rsp), %rbp
	xorl	%eax, %eax
	movq	264(%rsp), %r12
	movq	280(%rsp), %r14
	movq	288(%rsp), %r15
	addq	$296, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
.L7:
	.cfi_restore_state
	leaq	64(%rsp), %r12
	movl	$1, %edi
	movq	%r12, %rsi
	call	clock_gettime@PLT
	vxorps	%xmm2, %xmm2, %xmm2
	movq	72(%rsp), %rax
	vmovsd	.LC17(%rip), %xmm7
	subq	56(%rsp), %rax
	leaq	48(%rsp), %rsi
	movl	$1, %edi
	vcvtsi2sdq	%rax, %xmm2, %xmm1
	movq	64(%rsp), %rax
	subq	48(%rsp), %rax
	vmovsd	%xmm7, 8(%rsp)
	vcvtsi2sdq	%rax, %xmm2, %xmm0
	vfmadd132sd	%xmm7, %xmm0, %xmm1
	vmovsd	%xmm1, 16(%rsp)
	call	clock_gettime@PLT
	jmp	.L12
.L23:
	movq	%r13, 272(%rsp)
	.cfi_offset 13, -32
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE599:
	.size	main, .-main
	.section	.rodata.cst4,"aM",@progbits,4
	.align 4
.LC0:
	.long	1063105495
	.align 4
.LC1:
	.long	-1090519040
	.align 4
.LC3:
	.long	1073741824
	.section	.rodata.cst16,"aM",@progbits,16
	.align 16
.LC4:
	.long	1060439283
	.long	1060439283
	.long	-1087044365
	.long	-1087044365
	.align 16
.LC5:
	.long	1060439283
	.long	-1087044365
	.long	1060439283
	.long	-1087044365
	.section	.rodata.cst4
	.align 4
.LC10:
	.long	1008981770
	.align 4
.LC11:
	.long	1065353216
	.align 4
.LC12:
	.long	1061158912
	.set	.LC13,.LC4
	.section	.rodata.cst16
	.align 16
.LC14:
	.long	-2147483648
	.long	0
	.long	0
	.long	0
	.section	.rodata.cst4
	.align 4
.LC15:
	.long	953267991
	.section	.rodata.cst8,"aM",@progbits,8
	.align 8
.LC17:
	.long	-400107883
	.long	1041313291
	.align 8
.LC18:
	.long	0
	.long	1104006501
	.ident	"GCC: (GNU) 16.1.1 20260625"
	.section	.note.GNU-stack,"",@progbits

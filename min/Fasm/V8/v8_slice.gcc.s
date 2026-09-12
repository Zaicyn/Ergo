	.file	"v8_slice.c"
	.text
	.p2align 4
	.type	viviani_normal, @function
viviani_normal:
.LFB0:
	.cfi_startproc
	leaq	8(%rsp), %r10
	.cfi_def_cfa 10, 0
	andq	$-32, %rsp
	pushq	-8(%r10)
	pushq	%rbp
	movq	%rsp, %rbp
	.cfi_escape 0x10,0x6,0x2,0x76,0
	pushq	%r10
	.cfi_escape 0xf,0x3,0x76,0x78,0x6
	leaq	-40(%rbp), %rsi
	leaq	-36(%rbp), %rdi
	subq	$104, %rsp
	vmovss	%xmm0, -92(%rbp)
	call	sincosf@PLT
	vmovss	-92(%rbp), %xmm0
	vmovss	-40(%rbp), %xmm1
	leaq	-40(%rbp), %rsi
	vmulss	.LC0(%rip), %xmm0, %xmm0
	vmovss	-36(%rbp), %xmm2
	leaq	-36(%rbp), %rdi
	vmovss	%xmm1, -88(%rbp)
	vmovss	%xmm2, -84(%rbp)
	call	sincosf@PLT
	vmovss	-40(%rbp), %xmm4
	vmovss	-88(%rbp), %xmm1
	vmovss	.LC1(%rip), %xmm3
	vmovss	-84(%rbp), %xmm2
	vfnmadd231ss	-36(%rbp), %xmm3, %xmm2
	vfmsub132ss	%xmm4, %xmm1, %xmm3
	vmulss	%xmm4, %xmm1, %xmm1
	vunpcklps	%xmm3, %xmm2, %xmm0
	vmulss	%xmm3, %xmm3, %xmm3
	vfmadd132ss	%xmm2, %xmm3, %xmm2
	vmovss	.LC2(%rip), %xmm3
	vfmadd231ss	%xmm1, %xmm1, %xmm2
	vsqrtss	%xmm2, %xmm2, %xmm2
	vcomiss	%xmm2, %xmm3
	ja	.L3
	vdivss	%xmm2, %xmm1, %xmm1
	vmovsldup	%xmm2, %xmm3
	vmovq	%xmm0, %xmm0
	vmovhps	.LC3(%rip), %xmm3, %xmm3
	vdivps	%xmm3, %xmm0, %xmm0
.L3:
	movq	-8(%rbp), %r10
	.cfi_def_cfa 10, 0
	leave
	leaq	-8(%r10), %rsp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE0:
	.size	viviani_normal, .-viviani_normal
	.p2align 4
	.type	compute_invariant, @function
compute_invariant:
.LFB1:
	.cfi_startproc
	movq	%rsi, %rax
	shrq	$3, %rax
	je	.L6
	leaq	-1(%rax), %rdx
	cmpq	$2, %rdx
	jbe	.L11
	movq	%rsi, %rcx
	andq	$-32, %rsi
	vpxor	%xmm0, %xmm0, %xmm0
	movq	%rdi, %rdx
	shrq	$5, %rcx
	addq	%rdi, %rsi
	.p2align 4
	.p2align 4
	.p2align 3
.L9:
	vpxor	(%rdx), %ymm0, %ymm0
	addq	$32, %rdx
	cmpq	%rdx, %rsi
	jne	.L9
	vextracti128	$0x1, %ymm0, %xmm1
	salq	$2, %rcx
	vpxor	%xmm0, %xmm1, %xmm0
	vpsrldq	$8, %xmm0, %xmm1
	vpxor	%xmm1, %xmm0, %xmm0
	vmovq	%xmm0, %rdx
	cmpq	%rcx, %rax
	je	.L17
	vzeroupper
.L8:
	leaq	1(%rcx), %rsi
	xorq	(%rdi,%rcx,8), %rdx
	cmpq	%rax, %rsi
	jnb	.L10
	leaq	2(%rcx), %rsi
	xorq	8(%rdi,%rcx,8), %rdx
	cmpq	%rax, %rsi
	jnb	.L10
	xorq	16(%rdi,%rcx,8), %rdx
.L10:
	movq	%rdx, %rax
	shrq	$32, %rax
	xorq	%rdx, %rax
	movq	%rax, %rdx
	shrq	$16, %rdx
	xorq	%rax, %rdx
	movq	%rdx, %rax
	shrq	$8, %rax
	xorq	%rdx, %rax
.L6:
	ret
	.p2align 4,,10
	.p2align 3
.L17:
	vzeroupper
	jmp	.L10
.L11:
	xorl	%ecx, %ecx
	xorl	%edx, %edx
	jmp	.L8
	.cfi_endproc
.LFE1:
	.size	compute_invariant, .-compute_invariant
	.section	.rodata.cst4,"aM",@progbits,4
	.align 4
.LC0:
	.long	1077936128
	.align 4
.LC1:
	.long	1056964608
	.align 4
.LC2:
	.long	897988541
	.section	.rodata.cst8,"aM",@progbits,8
	.align 8
.LC3:
	.long	1065353216
	.long	1065353216
	.ident	"GCC: (GNU) 16.1.1 20260625"
	.section	.note.GNU-stack,"",@progbits

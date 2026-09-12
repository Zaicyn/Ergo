	.file	"sq2b_cert.c"
	.text
	.p2align 4
	.type	sqb_sweep, @function
sqb_sweep:
.LFB41:
	.cfi_startproc
	pushq	%r15
	.cfi_def_cfa_offset 16
	.cfi_offset 15, -16
	pcmpeqd	%xmm0, %xmm0
	pxor	%xmm6, %xmm6
	xorl	%edx, %edx
	pushq	%r14
	.cfi_def_cfa_offset 24
	.cfi_offset 14, -24
	psubb	%xmm0, %xmm6
	psrld	$31, %xmm0
	xorl	%eax, %eax
	pushq	%r13
	.cfi_def_cfa_offset 32
	.cfi_offset 13, -32
	leaq	10752(%rdi), %r15
	pxor	%xmm11, %xmm11
	leaq	86016(%rdi), %rcx
	pushq	%r12
	.cfi_def_cfa_offset 40
	.cfi_offset 12, -40
	pushq	%rbp
	.cfi_def_cfa_offset 48
	.cfi_offset 6, -48
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	subq	$328, %rsp
	.cfi_def_cfa_offset 384
	movq	%rdi, 104(%rsp)
	movq	%fs:40, %r13
	movq	%r13, 312(%rsp)
	movq	%rsi, %r13
	movaps	%xmm6, 16(%rsp)
	movq	$0, 128(%rsp)
	movaps	%xmm0, (%rsp)
.L2:
	movl	$1431655765, %esi
	movq	104(%rsp), %rbx
	movl	%eax, %r12d
	movq	%rcx, %rbp
	movq	%rax, 136(%rsp)
	movd	%esi, %xmm6
	movl	$9, %esi
	leaq	-10440(%r15), %r10
	movq	%rcx, 144(%rsp)
	pshufd	$0, %xmm6, %xmm7
	leaq	(%rbx,%rdx), %rdi
	movd	%esi, %xmm6
	movaps	%xmm7, 112(%rsp)
	leaq	-10584(%r15), %r11
	leaq	-10600(%r15), %r9
	sall	$5, %r12d
	movq	%rdx, 152(%rsp)
	pshufd	$0, %xmm6, %xmm12
	.p2align 4
	.p2align 3
.L53:
	cmpb	$0, 0(%rbp)
	je	.L4
	testq	%r13, %r13
	je	.L5
	movl	%r12d, %eax
	movb	$0, 0(%r13,%rax)
.L5:
	cmpl	$-559063315, 164(%rdi)
	je	.L4
	xorl	%eax, %eax
	pxor	%xmm1, %xmm1
	pxor	%xmm4, %xmm4
	.p2align 4
	.p2align 3
.L7:
	movdqu	(%r11,%rax), %xmm0
	movdqu	(%rdi,%rax), %xmm5
	addq	$16, %rax
	pxor	%xmm5, %xmm0
	pcmpeqb	%xmm7, %xmm0
	pcmpeqb	%xmm11, %xmm0
	pand	16(%rsp), %xmm0
	movdqa	%xmm0, %xmm2
	punpckhbw	%xmm11, %xmm0
	punpcklbw	%xmm11, %xmm2
	movdqa	%xmm2, %xmm3
	punpckhwd	%xmm4, %xmm2
	punpcklwd	%xmm4, %xmm3
	paddd	%xmm3, %xmm1
	paddd	%xmm2, %xmm1
	movdqa	%xmm0, %xmm2
	punpckhwd	%xmm4, %xmm0
	punpcklwd	%xmm4, %xmm2
	paddd	%xmm2, %xmm1
	paddd	%xmm0, %xmm1
	cmpq	$144, %rax
	jne	.L7
	movdqa	%xmm1, %xmm0
	leaq	-168(%r10), %rbx
	psrldq	$8, %xmm0
	movq	%rbx, %rdx
	paddd	%xmm0, %xmm1
	movdqa	%xmm1, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm1
	movd	%xmm1, %eax
	.p2align 5
	.p2align 4
	.p2align 3
.L8:
	movzbl	(%rdx), %ecx
	xorb	168(%rdx), %cl
	cmpb	$85, %cl
	setne	%cl
	addq	$1, %rdx
	movzbl	%cl, %ecx
	addl	%ecx, %eax
	cmpq	%r9, %rdx
	jne	.L8
	movl	$16, %edx
	pxor	%xmm4, %xmm4
	pxor	%xmm10, %xmm10
	movaps	%xmm7, 32(%rsp)
	movd	%edx, %xmm5
	movl	$5, %edx
	movd	%edx, %xmm6
	movl	$13, %edx
	pshufd	$0, %xmm5, %xmm9
	movdqa	%xmm9, %xmm13
	movd	%edx, %xmm5
	pshufd	$0, %xmm6, %xmm8
	movq	%rdi, %rdx
	movdqa	.LC0(%rip), %xmm6
	pshufd	$0, %xmm5, %xmm3
	movdqa	%xmm8, %xmm14
	movdqa	%xmm4, %xmm5
	movdqa	%xmm3, %xmm15
	movaps	%xmm3, 48(%rsp)
	movaps	%xmm8, 64(%rsp)
	.p2align 4
	.p2align 3
.L9:
	movdqu	(%rdx), %xmm0
	addq	$16, %rdx
	movdqa	%xmm0, %xmm1
	punpckhbw	%xmm11, %xmm0
	punpcklbw	%xmm11, %xmm1
	movdqa	%xmm0, %xmm2
	punpckhwd	%xmm10, %xmm0
	movdqa	%xmm1, %xmm3
	punpckhwd	%xmm10, %xmm1
	punpcklwd	%xmm10, %xmm2
	punpcklwd	%xmm10, %xmm3
	movdqa	%xmm0, %xmm7
	movdqa	%xmm1, %xmm8
	paddd	%xmm3, %xmm8
	paddd	%xmm2, %xmm7
	paddd	%xmm8, %xmm7
	movdqa	%xmm6, %xmm8
	paddd	%xmm12, %xmm8
	paddd	%xmm7, %xmm4
	movdqa	%xmm8, %xmm7
	psrlq	$32, %xmm8
	pmuludq	%xmm2, %xmm7
	psrlq	$32, %xmm2
	pmuludq	%xmm8, %xmm2
	movdqa	%xmm6, %xmm8
	paddd	%xmm15, %xmm8
	pshufd	$8, %xmm7, %xmm7
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm7
	movdqa	%xmm8, %xmm2
	pmuludq	%xmm0, %xmm2
	psrlq	$32, %xmm8
	psrlq	$32, %xmm0
	pmuludq	%xmm8, %xmm0
	pshufd	$8, %xmm2, %xmm2
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm2
	paddd	%xmm7, %xmm2
	movdqa	(%rsp), %xmm7
	paddd	%xmm6, %xmm7
	movdqa	%xmm7, %xmm0
	psrlq	$32, %xmm7
	pmuludq	%xmm3, %xmm0
	psrlq	$32, %xmm3
	pmuludq	%xmm7, %xmm3
	movdqa	%xmm6, %xmm7
	paddd	%xmm13, %xmm6
	paddd	%xmm14, %xmm7
	pshufd	$8, %xmm0, %xmm0
	pshufd	$8, %xmm3, %xmm3
	punpckldq	%xmm3, %xmm0
	movdqa	%xmm7, %xmm3
	pmuludq	%xmm1, %xmm3
	psrlq	$32, %xmm7
	psrlq	$32, %xmm1
	pmuludq	%xmm7, %xmm1
	pshufd	$8, %xmm3, %xmm3
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm3
	paddd	%xmm3, %xmm0
	paddd	%xmm0, %xmm2
	paddd	%xmm2, %xmm5
	cmpq	%rbx, %rdx
	jne	.L9
	movdqa	%xmm4, %xmm0
	movdqa	32(%rsp), %xmm7
	movdqa	48(%rsp), %xmm3
	movl	$145, %esi
	psrldq	$8, %xmm0
	movdqa	64(%rsp), %xmm8
	paddd	%xmm0, %xmm4
	movdqa	%xmm4, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm4
	movdqa	%xmm5, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm4, %edx
	paddd	%xmm0, %xmm5
	movdqa	%xmm5, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm5
	movd	%xmm5, %ecx
	.p2align 5
	.p2align 4
	.p2align 3
.L10:
	movzbl	-1(%rdi,%rsi), %r8d
	addl	%r8d, %edx
	imull	%esi, %r8d
	addq	$1, %rsi
	addl	%r8d, %ecx
	cmpq	$153, %rsi
	jne	.L10
	movl	$0, 32(%rsp)
	xorl	%r14d, %r14d
	cmpl	%edx, 152(%rdi)
	jne	.L11
	cmpl	%ecx, 156(%rdi)
	sete	%sil
	sete	%dl
	testl	%eax, %eax
	movzbl	%sil, %esi
	sete	%r14b
	movl	%esi, 32(%rsp)
	andl	%edx, %r14d
.L11:
	leaq	160(%rsp), %r8
	movq	%r11, %rax
	movq	%r8, %rdx
	.p2align 5
	.p2align 4
	.p2align 3
.L12:
	movdqu	(%rax), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm7, %xmm0
	movaps	%xmm0, -16(%rdx)
	cmpq	%r10, %rax
	jne	.L12
	leaq	168(%rsp), %rsi
	leaq	160(%rsp), %rax
	movq	%r10, %rcx
	.p2align 5
	.p2align 4
	.p2align 3
.L13:
	movzbl	(%rcx), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, 143(%rax)
	cmpq	%rax, %rsi
	jne	.L13
	pxor	%xmm4, %xmm4
	movdqa	.LC0(%rip), %xmm6
	leaq	304(%rsp), %rdx
	leaq	160(%rsp), %rax
	movdqa	%xmm4, %xmm5
	pxor	%xmm10, %xmm10
	movdqa	%xmm3, %xmm15
	movaps	%xmm7, 48(%rsp)
	movdqa	%xmm8, %xmm14
	movdqa	%xmm9, %xmm13
	movaps	%xmm3, 64(%rsp)
	movaps	%xmm8, 80(%rsp)
	.p2align 4
	.p2align 3
.L14:
	movdqa	(%rax), %xmm0
	addq	$16, %rax
	movdqa	%xmm0, %xmm1
	punpckhbw	%xmm11, %xmm0
	punpcklbw	%xmm11, %xmm1
	movdqa	%xmm0, %xmm2
	punpckhwd	%xmm10, %xmm0
	movdqa	%xmm1, %xmm3
	punpckhwd	%xmm10, %xmm1
	punpcklwd	%xmm10, %xmm2
	punpcklwd	%xmm10, %xmm3
	movdqa	%xmm0, %xmm7
	movdqa	%xmm1, %xmm8
	paddd	%xmm3, %xmm8
	paddd	%xmm2, %xmm7
	paddd	%xmm8, %xmm7
	movdqa	%xmm6, %xmm8
	paddd	%xmm12, %xmm8
	paddd	%xmm7, %xmm4
	movdqa	%xmm8, %xmm7
	psrlq	$32, %xmm8
	pmuludq	%xmm2, %xmm7
	psrlq	$32, %xmm2
	pmuludq	%xmm8, %xmm2
	movdqa	%xmm6, %xmm8
	paddd	%xmm15, %xmm8
	pshufd	$8, %xmm7, %xmm7
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm7
	movdqa	%xmm8, %xmm2
	pmuludq	%xmm0, %xmm2
	psrlq	$32, %xmm8
	psrlq	$32, %xmm0
	pmuludq	%xmm8, %xmm0
	pshufd	$8, %xmm2, %xmm2
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm2
	paddd	%xmm7, %xmm2
	movdqa	(%rsp), %xmm7
	paddd	%xmm6, %xmm7
	movdqa	%xmm7, %xmm0
	psrlq	$32, %xmm7
	pmuludq	%xmm3, %xmm0
	psrlq	$32, %xmm3
	pmuludq	%xmm7, %xmm3
	movdqa	%xmm6, %xmm7
	paddd	%xmm13, %xmm6
	paddd	%xmm14, %xmm7
	pshufd	$8, %xmm0, %xmm0
	pshufd	$8, %xmm3, %xmm3
	punpckldq	%xmm3, %xmm0
	movdqa	%xmm7, %xmm3
	pmuludq	%xmm1, %xmm3
	psrlq	$32, %xmm7
	psrlq	$32, %xmm1
	pmuludq	%xmm7, %xmm1
	pshufd	$8, %xmm3, %xmm3
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm3
	paddd	%xmm3, %xmm0
	paddd	%xmm0, %xmm2
	paddd	%xmm2, %xmm5
	cmpq	%rdx, %rax
	jne	.L14
	movdqa	%xmm4, %xmm0
	movdqa	48(%rsp), %xmm7
	movdqa	64(%rsp), %xmm3
	movl	$144, %edx
	psrldq	$8, %xmm0
	movdqa	80(%rsp), %xmm8
	paddd	%xmm0, %xmm4
	movdqa	%xmm4, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm4
	movdqa	%xmm5, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm4, %ecx
	paddd	%xmm0, %xmm5
	movdqa	%xmm5, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm5
	movd	%xmm5, %esi
	.p2align 5
	.p2align 4
	.p2align 3
.L15:
	movzbl	144(%r8), %eax
	addl	$1, %edx
	addq	$1, %r8
	addl	%eax, %ecx
	imull	%edx, %eax
	addl	%eax, %esi
	cmpl	$152, %edx
	jne	.L15
	cmpl	%ecx, 320(%rdi)
	je	.L98
.L16:
	testb	%r14b, %r14b
	je	.L99
	testq	%r13, %r13
	je	.L22
.L21:
	movl	%r12d, %eax
	movb	$1, 0(%r13,%rax)
	movl	32(%rsp), %edx
	testl	%edx, %edx
	jne	.L22
	movl	$-559063315, 164(%rdi)
	movq	104(%rsp), %rsi
	movl	$-559063315, 332(%rdi)
	addq	$1, 86320(%rsi)
	movb	$2, 0(%r13,%rax)
.L30:
	cmpl	$-559063315, 164(%rdi)
	jne	.L36
	.p2align 4
	.p2align 3
.L4:
	addq	$336, %rdi
	addq	$1, %rbp
	addq	$336, %r10
	addq	$336, %r11
	addq	$336, %r9
	addl	$1, %r12d
	cmpq	%r15, %rdi
	jne	.L53
	movq	136(%rsp), %rax
	movq	144(%rsp), %rcx
	leaq	10752(%rdi), %r15
	movq	152(%rsp), %rdx
	addq	$1, %rax
	addq	$32, %rcx
	addq	$10752, %rdx
	cmpq	$8, %rax
	jne	.L2
	movq	312(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L100
	movq	128(%rsp), %rax
	addq	$328, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 56
	popq	%rbx
	.cfi_def_cfa_offset 48
	popq	%rbp
	.cfi_def_cfa_offset 40
	popq	%r12
	.cfi_def_cfa_offset 32
	popq	%r13
	.cfi_def_cfa_offset 24
	popq	%r14
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	ret
.L99:
	.cfi_restore_state
	testq	%r13, %r13
	jne	.L21
	movl	32(%rsp), %eax
	testl	%eax, %eax
	jne	.L22
	movl	$-559063315, 164(%rdi)
	movq	104(%rsp), %rax
	movl	$-559063315, 332(%rdi)
	addq	$1, 86320(%rax)
	jmp	.L4
.L98:
	cmpl	%esi, 324(%rdi)
	jne	.L16
	testb	%r14b, %r14b
	jne	.L17
	testq	%r13, %r13
	je	.L23
	movl	%r12d, %eax
	movb	$1, 0(%r13,%rax)
.L23:
	cmpl	$1, 32(%rsp)
	je	.L31
	leaq	160(%rsp), %r8
	movq	%r11, %rax
	movq	%r8, %rdx
	.p2align 5
	.p2align 4
	.p2align 3
.L32:
	movdqu	(%rax), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm7, %xmm0
	movaps	%xmm0, -16(%rdx)
	cmpq	%r10, %rax
	jne	.L32
	leaq	168(%rsp), %rsi
	leaq	160(%rsp), %rax
	movq	%r10, %rcx
	.p2align 5
	.p2align 4
	.p2align 3
.L33:
	movzbl	(%rcx), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, 143(%rax)
	cmpq	%rsi, %rax
	jne	.L33
	movdqa	160(%rsp), %xmm0
	pxor	%xmm6, %xmm6
	movq	304(%rsp), %rax
	leaq	304(%rsp), %rdx
	movdqa	.LC0(%rip), %xmm10
	movdqa	%xmm6, %xmm5
	pxor	%xmm15, %xmm15
	movups	%xmm0, (%rdi)
	movdqa	176(%rsp), %xmm0
	movq	%rax, 144(%rdi)
	leaq	160(%rsp), %rax
	movups	%xmm0, 16(%rdi)
	movdqa	192(%rsp), %xmm0
	movups	%xmm0, 32(%rdi)
	movdqa	208(%rsp), %xmm0
	movups	%xmm0, 48(%rdi)
	movdqa	224(%rsp), %xmm0
	movups	%xmm0, 64(%rdi)
	movdqa	240(%rsp), %xmm0
	movups	%xmm0, 80(%rdi)
	movdqa	256(%rsp), %xmm0
	movups	%xmm0, 96(%rdi)
	movdqa	272(%rsp), %xmm0
	movups	%xmm0, 112(%rdi)
	movdqa	288(%rsp), %xmm0
	movups	%xmm0, 128(%rdi)
	.p2align 4
	.p2align 3
.L34:
	movdqa	(%rax), %xmm0
	addq	$16, %rax
	movdqa	%xmm0, %xmm2
	punpckhbw	%xmm11, %xmm0
	punpcklbw	%xmm11, %xmm2
	movdqa	%xmm0, %xmm14
	punpckhwd	%xmm15, %xmm0
	movdqa	%xmm2, %xmm4
	punpckhwd	%xmm15, %xmm2
	punpcklwd	%xmm15, %xmm14
	punpcklwd	%xmm15, %xmm4
	movdqa	%xmm0, %xmm1
	movdqa	%xmm2, %xmm13
	paddd	%xmm4, %xmm13
	paddd	%xmm14, %xmm1
	paddd	%xmm13, %xmm1
	paddd	%xmm1, %xmm6
	movdqa	%xmm10, %xmm1
	paddd	%xmm12, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm14, %xmm13
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm1
	movdqa	.LC4(%rip), %xmm14
	paddd	%xmm10, %xmm14
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	movdqa	%xmm14, %xmm1
	pmuludq	%xmm0, %xmm1
	psrlq	$32, %xmm14
	psrlq	$32, %xmm0
	pmuludq	%xmm14, %xmm0
	pshufd	$8, %xmm1, %xmm1
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm1
	movdqa	%xmm13, %xmm0
	paddd	%xmm1, %xmm0
	movdqa	(%rsp), %xmm1
	paddd	%xmm10, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm4, %xmm13
	psrlq	$32, %xmm4
	pmuludq	%xmm4, %xmm1
	pshufd	$8, %xmm13, %xmm4
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm4
	movdqa	.LC6(%rip), %xmm1
	paddd	%xmm10, %xmm1
	paddd	.LC7(%rip), %xmm10
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm2, %xmm13
	psrlq	$32, %xmm2
	pmuludq	%xmm2, %xmm1
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	paddd	%xmm13, %xmm4
	paddd	%xmm4, %xmm0
	paddd	%xmm0, %xmm5
	cmpq	%rax, %rdx
	jne	.L34
	movdqa	%xmm6, %xmm0
	movl	$144, %edx
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm6
	movdqa	%xmm6, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm6
	movdqa	%xmm5, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm6, %esi
	paddd	%xmm0, %xmm5
	movdqa	%xmm5, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm5
	movd	%xmm5, %ecx
	.p2align 5
	.p2align 4
	.p2align 3
.L35:
	movzbl	144(%r8), %eax
	addl	$1, %edx
	addq	$1, %r8
	addl	%eax, %esi
	imull	%edx, %eax
	addl	%eax, %ecx
	cmpl	$152, %edx
	jne	.L35
	movl	%esi, 152(%rdi)
	movl	%ecx, 156(%rdi)
	movl	$0, 164(%rdi)
.L36:
	xorl	%eax, %eax
	pxor	%xmm1, %xmm1
	pxor	%xmm2, %xmm2
	.p2align 4
	.p2align 3
.L42:
	movdqu	(%r11,%rax), %xmm5
	movdqu	(%rdi,%rax), %xmm0
	addq	$16, %rax
	pxor	%xmm5, %xmm0
	pcmpeqb	%xmm7, %xmm0
	pcmpeqb	%xmm11, %xmm0
	pand	16(%rsp), %xmm0
	movdqa	%xmm0, %xmm4
	punpckhbw	%xmm11, %xmm0
	punpcklbw	%xmm11, %xmm4
	movdqa	%xmm4, %xmm5
	punpckhwd	%xmm2, %xmm4
	punpcklwd	%xmm2, %xmm5
	paddd	%xmm5, %xmm1
	paddd	%xmm4, %xmm1
	movdqa	%xmm0, %xmm4
	punpckhwd	%xmm2, %xmm0
	punpcklwd	%xmm2, %xmm4
	paddd	%xmm4, %xmm1
	paddd	%xmm0, %xmm1
	cmpq	$144, %rax
	jne	.L42
	movdqa	%xmm1, %xmm0
	movq	%rbx, %rdx
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm1
	movdqa	%xmm1, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm1
	movd	%xmm1, %eax
	.p2align 5
	.p2align 4
	.p2align 3
.L43:
	movzbl	(%rdx), %ecx
	xorb	168(%rdx), %cl
	cmpb	$85, %cl
	setne	%cl
	addq	$1, %rdx
	movzbl	%cl, %ecx
	addl	%ecx, %eax
	cmpq	%r9, %rdx
	jne	.L43
	testl	%eax, %eax
	jne	.L44
	pxor	%xmm6, %xmm6
	movq	%rdi, %rax
	pxor	%xmm15, %xmm15
	movdqa	.LC0(%rip), %xmm10
	movdqa	%xmm6, %xmm5
	.p2align 4
	.p2align 3
.L45:
	movdqu	(%rax), %xmm0
	addq	$16, %rax
	movdqa	%xmm0, %xmm2
	punpckhbw	%xmm11, %xmm0
	punpcklbw	%xmm11, %xmm2
	movdqa	%xmm0, %xmm14
	punpckhwd	%xmm15, %xmm0
	movdqa	%xmm2, %xmm4
	punpckhwd	%xmm15, %xmm2
	punpcklwd	%xmm15, %xmm14
	punpcklwd	%xmm15, %xmm4
	movdqa	%xmm0, %xmm1
	movdqa	%xmm2, %xmm13
	paddd	%xmm4, %xmm13
	paddd	%xmm14, %xmm1
	paddd	%xmm13, %xmm1
	paddd	%xmm1, %xmm6
	movdqa	%xmm10, %xmm1
	paddd	%xmm12, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm14, %xmm13
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm1
	movdqa	.LC4(%rip), %xmm14
	paddd	%xmm10, %xmm14
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	movdqa	%xmm14, %xmm1
	pmuludq	%xmm0, %xmm1
	psrlq	$32, %xmm14
	psrlq	$32, %xmm0
	pmuludq	%xmm14, %xmm0
	pshufd	$8, %xmm1, %xmm1
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm1
	movdqa	%xmm13, %xmm0
	paddd	%xmm1, %xmm0
	movdqa	(%rsp), %xmm1
	paddd	%xmm10, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm4, %xmm13
	psrlq	$32, %xmm4
	pmuludq	%xmm4, %xmm1
	pshufd	$8, %xmm13, %xmm4
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm4
	movdqa	.LC6(%rip), %xmm1
	paddd	%xmm10, %xmm1
	paddd	.LC7(%rip), %xmm10
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm2, %xmm13
	psrlq	$32, %xmm2
	pmuludq	%xmm2, %xmm1
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	paddd	%xmm13, %xmm4
	paddd	%xmm4, %xmm0
	paddd	%xmm0, %xmm5
	cmpq	%rbx, %rax
	jne	.L45
	movdqa	%xmm6, %xmm0
	movl	$145, %eax
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm6
	movdqa	%xmm6, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm6
	movdqa	%xmm5, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm6, %esi
	paddd	%xmm0, %xmm5
	movdqa	%xmm5, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm5
	movd	%xmm5, %ecx
	.p2align 5
	.p2align 4
	.p2align 3
.L46:
	movzbl	-1(%rdi,%rax), %edx
	addl	%edx, %esi
	imull	%eax, %edx
	addq	$1, %rax
	addl	%edx, %ecx
	cmpq	$153, %rax
	jne	.L46
	cmpl	%esi, 152(%rdi)
	je	.L101
.L44:
	addq	$1, 128(%rsp)
	jmp	.L4
.L22:
	movdqu	(%rdi), %xmm0
	movq	144(%rdi), %rax
	leaq	160(%rsp), %r8
	movl	328(%rdi), %r14d
	movq	%r8, %rdx
	movaps	%xmm0, 160(%rsp)
	movdqu	16(%rdi), %xmm0
	movq	%rax, 304(%rsp)
	movq	%r11, %rax
	movaps	%xmm0, 176(%rsp)
	movdqu	32(%rdi), %xmm0
	movaps	%xmm0, 192(%rsp)
	movdqu	48(%rdi), %xmm0
	movaps	%xmm0, 208(%rsp)
	movdqu	64(%rdi), %xmm0
	movaps	%xmm0, 224(%rsp)
	movdqu	80(%rdi), %xmm0
	movaps	%xmm0, 240(%rsp)
	movdqu	96(%rdi), %xmm0
	movaps	%xmm0, 256(%rsp)
	movdqu	112(%rdi), %xmm0
	movaps	%xmm0, 272(%rsp)
	movdqu	128(%rdi), %xmm0
	movaps	%xmm0, 288(%rsp)
	.p2align 5
	.p2align 4
	.p2align 3
.L26:
	movdqa	(%rdx), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm7, %xmm0
	movups	%xmm0, -16(%rax)
	cmpq	%r10, %rax
	jne	.L26
	leaq	168(%rsp), %rsi
	movq	%r10, %rcx
	leaq	160(%rsp), %rax
	.p2align 5
	.p2align 4
	.p2align 3
.L27:
	movzbl	144(%rax), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, -1(%rcx)
	cmpq	%rsi, %rax
	jne	.L27
	pxor	%xmm6, %xmm6
	leaq	304(%rsp), %rdx
	movdqa	.LC0(%rip), %xmm10
	leaq	160(%rsp), %rax
	movdqa	%xmm6, %xmm5
	pxor	%xmm15, %xmm15
	.p2align 4
	.p2align 3
.L28:
	movdqa	(%rax), %xmm0
	addq	$16, %rax
	movdqa	%xmm0, %xmm2
	punpckhbw	%xmm11, %xmm0
	punpcklbw	%xmm11, %xmm2
	movdqa	%xmm0, %xmm14
	punpckhwd	%xmm15, %xmm0
	movdqa	%xmm2, %xmm13
	punpckhwd	%xmm15, %xmm2
	punpcklwd	%xmm15, %xmm14
	punpcklwd	%xmm15, %xmm13
	movdqa	%xmm0, %xmm1
	movdqa	%xmm2, %xmm4
	paddd	%xmm13, %xmm4
	paddd	%xmm14, %xmm1
	paddd	%xmm4, %xmm1
	paddd	%xmm1, %xmm6
	movdqa	%xmm10, %xmm1
	paddd	%xmm12, %xmm1
	movdqa	%xmm1, %xmm4
	psrlq	$32, %xmm1
	pmuludq	%xmm14, %xmm4
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm1
	movdqa	.LC4(%rip), %xmm14
	paddd	%xmm10, %xmm14
	pshufd	$8, %xmm4, %xmm4
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm4
	movdqa	%xmm14, %xmm1
	pmuludq	%xmm0, %xmm1
	psrlq	$32, %xmm14
	psrlq	$32, %xmm0
	pmuludq	%xmm14, %xmm0
	pshufd	$8, %xmm1, %xmm1
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm1
	paddd	%xmm1, %xmm4
	movdqa	(%rsp), %xmm1
	movdqa	%xmm4, %xmm0
	paddd	%xmm10, %xmm1
	movdqa	%xmm1, %xmm4
	psrlq	$32, %xmm1
	pmuludq	%xmm13, %xmm4
	psrlq	$32, %xmm13
	pmuludq	%xmm13, %xmm1
	pshufd	$8, %xmm4, %xmm4
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm4
	movdqa	.LC6(%rip), %xmm1
	paddd	%xmm10, %xmm1
	paddd	.LC7(%rip), %xmm10
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm2, %xmm13
	psrlq	$32, %xmm2
	pmuludq	%xmm2, %xmm1
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	paddd	%xmm13, %xmm4
	paddd	%xmm4, %xmm0
	paddd	%xmm0, %xmm5
	cmpq	%rdx, %rax
	jne	.L28
	movdqa	%xmm6, %xmm0
	movl	$144, %edx
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm6
	movdqa	%xmm6, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm6
	movdqa	%xmm5, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm6, %esi
	paddd	%xmm0, %xmm5
	movdqa	%xmm5, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm5
	movd	%xmm5, %ecx
	.p2align 5
	.p2align 4
	.p2align 3
.L29:
	movzbl	144(%r8), %eax
	addl	$1, %edx
	addq	$1, %r8
	addl	%eax, %esi
	imull	%edx, %eax
	addl	%eax, %ecx
	cmpl	$152, %edx
	jne	.L29
	movl	%esi, 320(%rdi)
	movl	%ecx, 324(%rdi)
	movl	$0, 332(%rdi)
	movl	%r14d, 328(%rdi)
	jmp	.L30
.L17:
	addl	$1, 160(%rdi)
	addl	$1, 328(%rdi)
	jmp	.L4
.L31:
	movdqu	(%rdi), %xmm0
	movq	144(%rdi), %rax
	leaq	160(%rsp), %r8
	movl	328(%rdi), %r14d
	movq	%r8, %rdx
	movaps	%xmm0, 160(%rsp)
	movdqu	16(%rdi), %xmm0
	movq	%rax, 304(%rsp)
	movq	%r11, %rax
	movaps	%xmm0, 176(%rsp)
	movdqu	32(%rdi), %xmm0
	movaps	%xmm0, 192(%rsp)
	movdqu	48(%rdi), %xmm0
	movaps	%xmm0, 208(%rsp)
	movdqu	64(%rdi), %xmm0
	movaps	%xmm0, 224(%rsp)
	movdqu	80(%rdi), %xmm0
	movaps	%xmm0, 240(%rsp)
	movdqu	96(%rdi), %xmm0
	movaps	%xmm0, 256(%rsp)
	movdqu	112(%rdi), %xmm0
	movaps	%xmm0, 272(%rsp)
	movdqu	128(%rdi), %xmm0
	movaps	%xmm0, 288(%rsp)
.L38:
	movdqa	(%rdx), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm7, %xmm0
	movups	%xmm0, -16(%rax)
	cmpq	%r10, %rax
	jne	.L38
	leaq	168(%rsp), %rsi
	movq	%r10, %rcx
	leaq	160(%rsp), %rax
	.p2align 5
	.p2align 4
	.p2align 3
.L39:
	movzbl	144(%rax), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, -1(%rcx)
	cmpq	%rsi, %rax
	jne	.L39
	pxor	%xmm6, %xmm6
	leaq	304(%rsp), %rdx
	movdqa	.LC0(%rip), %xmm10
	leaq	160(%rsp), %rax
	movdqa	%xmm6, %xmm5
	pxor	%xmm15, %xmm15
.L40:
	movdqa	(%rax), %xmm0
	addq	$16, %rax
	movdqa	%xmm0, %xmm2
	punpckhbw	%xmm11, %xmm0
	punpcklbw	%xmm11, %xmm2
	movdqa	%xmm0, %xmm14
	punpckhwd	%xmm15, %xmm0
	movdqa	%xmm2, %xmm4
	punpckhwd	%xmm15, %xmm2
	punpcklwd	%xmm15, %xmm14
	punpcklwd	%xmm15, %xmm4
	movdqa	%xmm0, %xmm1
	movdqa	%xmm2, %xmm13
	paddd	%xmm4, %xmm13
	paddd	%xmm14, %xmm1
	paddd	%xmm13, %xmm1
	paddd	%xmm1, %xmm6
	movdqa	%xmm10, %xmm1
	paddd	%xmm12, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm14, %xmm13
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm1
	movdqa	.LC4(%rip), %xmm14
	paddd	%xmm10, %xmm14
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	movdqa	%xmm14, %xmm1
	pmuludq	%xmm0, %xmm1
	psrlq	$32, %xmm14
	psrlq	$32, %xmm0
	pmuludq	%xmm14, %xmm0
	pshufd	$8, %xmm1, %xmm1
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm1
	movdqa	%xmm13, %xmm0
	paddd	%xmm1, %xmm0
	movdqa	(%rsp), %xmm1
	paddd	%xmm10, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm4, %xmm13
	psrlq	$32, %xmm4
	pmuludq	%xmm4, %xmm1
	pshufd	$8, %xmm13, %xmm4
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm4
	movdqa	.LC6(%rip), %xmm1
	paddd	%xmm10, %xmm1
	paddd	.LC7(%rip), %xmm10
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm2, %xmm13
	psrlq	$32, %xmm2
	pmuludq	%xmm2, %xmm1
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	paddd	%xmm13, %xmm4
	paddd	%xmm4, %xmm0
	paddd	%xmm0, %xmm5
	cmpq	%rdx, %rax
	jne	.L40
	movdqa	%xmm6, %xmm0
	movl	$144, %edx
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm6
	movdqa	%xmm6, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm6
	movdqa	%xmm5, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm6, %esi
	paddd	%xmm0, %xmm5
	movdqa	%xmm5, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm5
	movd	%xmm5, %ecx
	.p2align 5
	.p2align 4
	.p2align 3
.L41:
	movzbl	144(%r8), %eax
	addl	$1, %edx
	addq	$1, %r8
	addl	%eax, %esi
	imull	%edx, %eax
	addl	%eax, %ecx
	cmpl	$152, %edx
	jne	.L41
	movq	104(%rsp), %rax
	movl	%esi, 320(%rdi)
	movl	%ecx, 324(%rdi)
	movl	$0, 332(%rdi)
	movl	%r14d, 328(%rdi)
	addq	$1, 86328(%rax)
	jmp	.L30
.L101:
	cmpl	%ecx, 156(%rdi)
	jne	.L44
	leaq	160(%rsp), %r8
	movdqa	112(%rsp), %xmm1
	movq	%r11, %rax
	movq	%r8, %rdx
.L47:
	movdqu	(%rax), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm1, %xmm0
	movaps	%xmm0, -16(%rdx)
	cmpq	%r10, %rax
	jne	.L47
	leaq	168(%rsp), %rsi
	leaq	160(%rsp), %rax
	movq	%r10, %rcx
.L48:
	movzbl	(%rcx), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, 143(%rax)
	cmpq	%rax, %rsi
	jne	.L48
	pxor	%xmm10, %xmm10
	movdqa	.LC0(%rip), %xmm4
	pxor	%xmm5, %xmm5
	leaq	304(%rsp), %rdx
	leaq	160(%rsp), %rax
	movdqa	%xmm10, %xmm6
.L49:
	movdqa	(%rax), %xmm0
	addq	$16, %rax
	movdqa	%xmm0, %xmm1
	punpckhbw	%xmm11, %xmm0
	punpcklbw	%xmm11, %xmm1
	movdqa	%xmm0, %xmm14
	punpckhwd	%xmm5, %xmm0
	movdqa	%xmm1, %xmm15
	punpcklwd	%xmm5, %xmm14
	punpckhwd	%xmm5, %xmm1
	punpcklwd	%xmm5, %xmm15
	movdqa	%xmm14, %xmm13
	movdqa	%xmm15, %xmm2
	paddd	%xmm0, %xmm13
	paddd	%xmm1, %xmm2
	paddd	%xmm13, %xmm2
	paddd	%xmm2, %xmm10
	movdqa	%xmm4, %xmm2
	paddd	%xmm8, %xmm2
	movdqa	%xmm2, %xmm13
	psrlq	$32, %xmm2
	pmuludq	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm1, %xmm2
	pshufd	$8, %xmm13, %xmm1
	movdqa	(%rsp), %xmm13
	pshufd	$8, %xmm2, %xmm2
	paddd	%xmm4, %xmm13
	punpckldq	%xmm2, %xmm1
	movdqa	%xmm13, %xmm2
	psrlq	$32, %xmm13
	pmuludq	%xmm15, %xmm2
	psrlq	$32, %xmm15
	pmuludq	%xmm15, %xmm13
	pshufd	$8, %xmm2, %xmm2
	pshufd	$8, %xmm13, %xmm13
	punpckldq	%xmm13, %xmm2
	paddd	%xmm2, %xmm1
	movdqa	%xmm4, %xmm2
	paddd	%xmm3, %xmm2
	movdqa	%xmm2, %xmm13
	psrlq	$32, %xmm2
	pmuludq	%xmm0, %xmm13
	psrlq	$32, %xmm0
	pmuludq	%xmm2, %xmm0
	pshufd	$8, %xmm13, %xmm2
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm2
	movdqa	%xmm4, %xmm0
	paddd	%xmm9, %xmm4
	paddd	%xmm12, %xmm0
	movdqa	%xmm0, %xmm13
	psrlq	$32, %xmm0
	pmuludq	%xmm14, %xmm13
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm0
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm13
	paddd	%xmm13, %xmm2
	paddd	%xmm2, %xmm1
	paddd	%xmm1, %xmm6
	cmpq	%rax, %rdx
	jne	.L49
	movdqa	%xmm10, %xmm0
	movl	$144, %edx
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm10
	movdqa	%xmm10, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm10
	movdqa	%xmm6, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm10, %esi
	paddd	%xmm0, %xmm6
	movdqa	%xmm6, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm6
	movd	%xmm6, %ecx
	.p2align 5
	.p2align 4
	.p2align 3
.L50:
	movzbl	144(%r8), %eax
	addl	$1, %edx
	addq	$1, %r8
	addl	%eax, %esi
	imull	%edx, %eax
	addl	%eax, %ecx
	cmpl	$152, %edx
	jne	.L50
	cmpl	320(%rdi), %esi
	jne	.L44
	cmpl	324(%rdi), %ecx
	jne	.L44
	jmp	.L4
.L100:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE41:
	.size	sqb_sweep, .-sqb_sweep
	.p2align 4
	.type	sq2b_blind_pass.constprop.0, @function
sq2b_blind_pass.constprop.0:
.LFB46:
	.cfi_startproc
	pushq	%r15
	.cfi_def_cfa_offset 16
	.cfi_offset 15, -16
	movl	$10, %ecx
	movabsq	$-7046029254386307790, %r9
	pushq	%r14
	.cfi_def_cfa_offset 24
	.cfi_offset 14, -24
	movabsq	$-4658895280553044828, %r14
	pushq	%r13
	.cfi_def_cfa_offset 32
	.cfi_offset 13, -32
	pushq	%r12
	.cfi_def_cfa_offset 40
	.cfi_offset 12, -40
	pushq	%rbp
	.cfi_def_cfa_offset 48
	.cfi_offset 6, -48
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	subq	$86568, %rsp
	.cfi_def_cfa_offset 86624
	movq	%rdi, 40(%rsp)
	movq	%rdx, 48(%rsp)
	movq	%fs:40, %rax
	movq	%rax, 86552(%rsp)
	xorl	%eax, %eax
	movq	$0, (%rdx)
	movabsq	$-7723592293110660344, %rax
	movq	$0, (%rsi)
	movq	$0, (%rdi)
	movabsq	$-1100507917760571142, %rdi
	.p2align 5
	.p2align 4
	.p2align 3
.L103:
	movq	%r14, %rdx
	xorq	%r9, %rax
	xorq	%r14, %rdi
	salq	$17, %rdx
	xorq	%rax, %r14
	xorq	%rdi, %r9
	rorq	$19, %rdi
	xorq	%rdx, %rax
	subl	$1, %ecx
	jne	.L103
	movl	$2000, 36(%rsp)
	leaq	86544(%rsp), %r15
	movq	%rax, 8(%rsp)
	movq	%rdi, 16(%rsp)
	movq	%rsi, 56(%rsp)
	movq	%r14, (%rsp)
	movq	%r9, %r14
.L108:
	movq	(%rsp), %rcx
	movq	16(%rsp), %rdi
	movq	%r14, %rbx
	movq	8(%rsp), %rax
	movq	%rcx, %rsi
	movq	%rcx, %rdx
	salq	$17, %rcx
	leaq	(%r14,%rdi), %r13
	xorq	%r14, %rax
	xorq	%rdi, %rsi
	rolq	$17, %r13
	xorq	%rax, %rdx
	xorq	%rsi, %rbx
	xorq	%rax, %rcx
	rorq	$19, %rsi
	xorq	%rbx, %rcx
	movq	%rdx, %r9
	xorq	%rsi, %r9
	movq	%rcx, %rax
	xorq	%rdx, %rax
	movq	%r9, %r8
	rorq	$19, %r9
	xorq	%rbx, %r8
	addq	%rsi, %rbx
	movq	%rax, %rsi
	salq	$17, %rdx
	xorq	%r9, %rsi
	xorq	%rcx, %rdx
	rolq	$17, %rbx
	movq	%rsi, %rcx
	xorq	%r8, %rdx
	rorq	$19, %rsi
	xorq	%r8, %rcx
	addq	%r9, %r8
	movq	%rdx, %rdi
	rolq	$17, %r8
	xorq	%rax, %rdi
	salq	$17, %rax
	movl	%r8d, %ebp
	xorq	%rdx, %rax
	movq	%rdi, %rdx
	shrl	$3, %ebp
	xorq	%rcx, %rax
	imulq	$452101821, %rbp, %rbp
	movq	%rax, %r10
	shrq	$33, %rbp
	imull	$152, %ebp, %r9d
	movl	%r8d, %ebp
	subl	%r9d, %ebp
	xorq	%rsi, %rdx
	xorq	%rdi, %r10
	salq	$17, %rdi
	movq	%rdx, %r14
	rorq	$19, %rdx
	xorq	%rax, %rdi
	andl	$7, %r13d
	xorq	%rcx, %r14
	addq	%rsi, %rcx
	movq	%rdx, 16(%rsp)
	movl	$2155905153, %edx
	rolq	$17, %rcx
	movq	%rdi, 8(%rsp)
	andl	$31, %ebx
	leaq	64(%rsp), %rdi
	movl	%ecx, %eax
	leaq	clean.1(%rip), %rsi
	movq	%r10, (%rsp)
	imulq	%rdx, %rax
	movl	$86336, %edx
	shrq	$39, %rax
	leal	1(%rcx,%rax), %r12d
	call	memcpy@PLT
	imulq	$336, %rbx, %rax
	xorl	%esi, %esi
	leaq	64(%rsp), %rdi
	imulq	$10752, %r13, %rdx
	addq	%rax, %rdx
	leaq	86560(%rsp,%rdx), %rax
	movq	%rdx, 24(%rsp)
	addq	%rbp, %rax
	xorb	%r12b, -86496(%rax)
	xorb	%r12b, -86328(%rax)
	call	sqb_sweep
	movq	24(%rsp), %rdx
	cmpl	$-559063315, 228(%rsp,%rdx)
	jne	.L104
	movq	40(%rsp), %rax
	addq	$1, (%rax)
	movq	56(%rsp), %rax
	addq	$1, (%rax)
.L104:
	movl	$86336, %edx
	leaq	clean.1(%rip), %rsi
	leaq	64(%rsp), %rdi
	call	memcpy@PLT
	imulq	$336, %rbx, %rax
	pxor	%xmm4, %xmm4
	leaq	86400(%rsp), %rdi
	imulq	$10752, %r13, %rdx
	movl	$16, %esi
	movdqa	.LC0(%rip), %xmm5
	movdqa	.LC3(%rip), %xmm9
	movd	%esi, %xmm8
	movdqa	%xmm4, %xmm3
	pxor	%xmm7, %xmm7
	movdqa	.LC4(%rip), %xmm10
	movdqa	.LC5(%rip), %xmm11
	pxor	%xmm6, %xmm6
	pshufd	$0, %xmm8, %xmm8
	movdqa	.LC6(%rip), %xmm12
	addq	%rax, %rdx
	leaq	86560(%rsp,%rdx), %rax
	addq	%rax, %rbp
	xorb	%r12b, -86496(%rbp)
	movdqa	64(%rsp,%rdx), %xmm0
	xorb	%r12b, -86328(%rbp)
	movaps	%xmm0, 86400(%rsp)
	movdqa	-86480(%rax), %xmm0
	movaps	%xmm0, 86416(%rsp)
	movdqa	-86464(%rax), %xmm0
	movaps	%xmm0, 86432(%rsp)
	movdqa	-86448(%rax), %xmm0
	movaps	%xmm0, 86448(%rsp)
	movdqa	-86432(%rax), %xmm0
	movaps	%xmm0, 86464(%rsp)
	movdqa	-86416(%rax), %xmm0
	movaps	%xmm0, 86480(%rsp)
	movdqa	-86400(%rax), %xmm0
	movaps	%xmm0, 86496(%rsp)
	movdqa	-86384(%rax), %xmm0
	movaps	%xmm0, 86512(%rsp)
	movdqa	-86368(%rax), %xmm0
	movq	-86352(%rax), %rax
	movaps	%xmm0, 86528(%rsp)
	movq	%rax, 86544(%rsp)
	movq	%rdi, %rax
	.p2align 4
	.p2align 3
.L105:
	movdqa	(%rax), %xmm0
	addq	$16, %rax
	movdqa	%xmm0, %xmm2
	punpckhbw	%xmm7, %xmm0
	punpcklbw	%xmm7, %xmm2
	movdqa	%xmm0, %xmm14
	punpckhwd	%xmm6, %xmm0
	movdqa	%xmm2, %xmm15
	punpcklwd	%xmm6, %xmm14
	punpckhwd	%xmm6, %xmm2
	punpcklwd	%xmm6, %xmm15
	movdqa	%xmm14, %xmm1
	movdqa	%xmm15, %xmm13
	paddd	%xmm0, %xmm1
	paddd	%xmm2, %xmm13
	paddd	%xmm13, %xmm1
	movdqa	%xmm5, %xmm13
	paddd	%xmm12, %xmm13
	paddd	%xmm1, %xmm4
	movdqa	%xmm13, %xmm1
	psrlq	$32, %xmm13
	pmuludq	%xmm2, %xmm1
	psrlq	$32, %xmm2
	pmuludq	%xmm13, %xmm2
	movdqa	%xmm5, %xmm13
	paddd	%xmm11, %xmm13
	pshufd	$8, %xmm1, %xmm1
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm1
	movdqa	%xmm13, %xmm2
	pmuludq	%xmm15, %xmm2
	psrlq	$32, %xmm13
	psrlq	$32, %xmm15
	pmuludq	%xmm15, %xmm13
	pshufd	$8, %xmm2, %xmm2
	pshufd	$8, %xmm13, %xmm13
	punpckldq	%xmm13, %xmm2
	movdqa	%xmm5, %xmm13
	paddd	%xmm10, %xmm13
	paddd	%xmm2, %xmm1
	movdqa	%xmm13, %xmm2
	psrlq	$32, %xmm13
	pmuludq	%xmm0, %xmm2
	psrlq	$32, %xmm0
	pmuludq	%xmm0, %xmm13
	movdqa	%xmm5, %xmm0
	paddd	%xmm8, %xmm5
	paddd	%xmm9, %xmm0
	pshufd	$8, %xmm2, %xmm2
	pshufd	$8, %xmm13, %xmm13
	punpckldq	%xmm13, %xmm2
	movdqa	%xmm0, %xmm13
	pmuludq	%xmm14, %xmm13
	psrlq	$32, %xmm0
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm0
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm13
	paddd	%xmm13, %xmm2
	paddd	%xmm2, %xmm1
	paddd	%xmm1, %xmm3
	cmpq	%r15, %rax
	jne	.L105
	movdqa	%xmm4, %xmm0
	movl	$144, %edx
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm4
	movdqa	%xmm4, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm4
	movdqa	%xmm3, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm4, %esi
	paddd	%xmm0, %xmm3
	movdqa	%xmm3, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm3
	movd	%xmm3, %ecx
	.p2align 5
	.p2align 4
	.p2align 3
.L106:
	movzbl	144(%rdi), %eax
	addl	$1, %edx
	addq	$1, %rdi
	addl	%eax, %esi
	imull	%edx, %eax
	addl	%eax, %ecx
	cmpl	$152, %edx
	jne	.L106
	imulq	$336, %rbx, %rbx
	leaq	64(%rsp), %rdi
	imulq	$10752, %r13, %r13
	addq	%r13, %rbx
	movl	%esi, 216(%rsp,%rbx)
	movl	%esi, 384(%rsp,%rbx)
	xorl	%esi, %esi
	movl	%ecx, 220(%rsp,%rbx)
	movl	%ecx, 388(%rsp,%rbx)
	call	sqb_sweep
	testq	%rax, %rax
	jne	.L107
	cmpl	$-559063315, 228(%rsp,%rbx)
	je	.L107
	movq	48(%rsp), %rax
	addq	$1, (%rax)
.L107:
	subl	$1, 36(%rsp)
	jne	.L108
	movq	86552(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L115
	addq	$86568, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 56
	popq	%rbx
	.cfi_def_cfa_offset 48
	popq	%rbp
	.cfi_def_cfa_offset 40
	popq	%r12
	.cfi_def_cfa_offset 32
	popq	%r13
	.cfi_def_cfa_offset 24
	popq	%r14
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	ret
.L115:
	.cfi_restore_state
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE46:
	.size	sq2b_blind_pass.constprop.0, .-sq2b_blind_pass.constprop.0
	.p2align 4
	.type	cert_round.constprop.0, @function
cert_round.constprop.0:
.LFB47:
	.cfi_startproc
	pushq	%r15
	.cfi_def_cfa_offset 16
	.cfi_offset 15, -16
	pushq	%r14
	.cfi_def_cfa_offset 24
	.cfi_offset 14, -24
	pushq	%r13
	.cfi_def_cfa_offset 32
	.cfi_offset 13, -32
	pushq	%r12
	.cfi_def_cfa_offset 40
	.cfi_offset 12, -40
	movl	%esi, %r12d
	leaq	clean.1(%rip), %rsi
	pushq	%rbp
	.cfi_def_cfa_offset 48
	.cfi_offset 6, -48
	movq	%rdi, %rbp
	leaq	cell.2(%rip), %rdi
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	subq	$1736, %rsp
	.cfi_def_cfa_offset 1792
	movl	%edx, (%rsp)
	movl	$86336, %edx
	leaq	32(%rsp), %r15
	movq	%r15, %r13
	movq	%fs:40, %rbx
	movq	%rbx, 1720(%rsp)
	movq	%rcx, %rbx
	call	memcpy@PLT
	movl	%r12d, %eax
	movq	%r15, 24(%rsp)
	movsd	.LC9(%rip), %xmm1
	leaq	(%rax,%rax,2), %rax
	movsd	.LC10(%rip), %xmm2
	leaq	(%r15,%rax,8), %rax
	movq	%rax, 16(%rsp)
	jmp	.L121
.L178:
	movl	%eax, %edi
	imulq	$336, %rdx, %rax
	imulq	$168, %rcx, %rdx
	addq	%rdx, %rax
	imulq	$10752, %rdi, %rdx
	leaq	cell.2(%rip), %rdi
	addq	%rdx, %rax
	addq	%rdi, %rax
	xorb	%sil, (%rax,%r9)
.L119:
	addq	$1, (%rbx,%r11,8)
	addq	$24, %r13
	cmpq	16(%rsp), %r13
	je	.L176
.L121:
	movl	(%rsp), %esi
	movq	0(%rbp), %rax
	movq	24(%rbp), %rdi
	movq	8(%rbp), %rcx
	movq	16(%rbp), %r8
	movl	%esi, %r11d
	cmpl	$-1, %esi
	je	.L177
.L117:
	movq	%rdi, %r9
	xorq	%rax, %r8
	movl	%r11d, 0(%r13)
	xorq	%rcx, %r9
	movq	%r8, %rsi
	movq	%r9, %rdx
	xorq	%rcx, %rsi
	rorq	$19, %r9
	xorq	%rax, %rdx
	addq	%rdi, %rax
	movq	%rcx, %rdi
	movq	%rsi, %r12
	salq	$17, %rdi
	xorq	%r9, %r12
	rolq	$17, %rax
	xorq	%r8, %rdi
	movq	%r12, %rcx
	rorq	$19, %r12
	andl	$7, %eax
	xorq	%rdx, %rdi
	xorq	%rdx, %rcx
	addq	%r9, %rdx
	movl	%eax, 4(%r13)
	movq	%rdi, %r8
	rolq	$17, %rdx
	xorq	%rsi, %r8
	salq	$17, %rsi
	andl	$31, %edx
	xorq	%rdi, %rsi
	movq	%r8, %r10
	movl	%edx, 8(%r13)
	xorq	%rcx, %rsi
	xorq	%r12, %r10
	movq	%rsi, %rdi
	movq	%r10, %r9
	rorq	$19, %r10
	xorq	%r8, %rdi
	salq	$17, %r8
	xorq	%rcx, %r9
	addq	%r12, %rcx
	xorq	%rsi, %r8
	rolq	$17, %rcx
	movq	%rdi, %r14
	xorq	%r9, %r8
	xorq	%r10, %r14
	andl	$1, %ecx
	movq	%r8, %r12
	movq	%r14, %rsi
	movl	%ecx, 12(%r13)
	xorq	%rdi, %r12
	addq	%r9, %r10
	xorq	%r9, %rsi
	salq	$17, %rdi
	rolq	$17, %r10
	xorq	%r8, %rdi
	rorq	$19, %r14
	movq	%r12, %r8
	movl	%r10d, %r9d
	xorq	%rsi, %rdi
	xorq	%r14, %r8
	shrl	$3, %r9d
	imulq	$452101821, %r9, %r9
	shrq	$33, %r9
	imull	$152, %r9d, %r15d
	movl	%r10d, %r9d
	movq	%rdi, %r10
	xorq	%r12, %r10
	salq	$17, %r12
	movq	%r10, 8(%rbp)
	movq	%r8, %r10
	xorq	%rdi, %r12
	rorq	$19, %r8
	xorq	%rsi, %r10
	addq	%r14, %rsi
	movl	$2155905153, %r14d
	movq	%r12, 16(%rbp)
	rolq	$17, %rsi
	movq	%r10, 0(%rbp)
	subl	%r15d, %r9d
	movl	%esi, %edi
	movq	%r8, 24(%rbp)
	imulq	%r14, %rdi
	shrq	$39, %rdi
	leal	1(%rsi,%rdi), %esi
	testl	%r11d, %r11d
	je	.L178
	imulq	$336, %rdx, %rdx
	andl	$7, %r9d
	imulq	$10752, %rax, %rax
	addq	%rdx, %rax
	movl	%ecx, %edx
	negq	%rdx
	andl	$168, %edx
	addq	%rdx, %rax
	cmpl	$1, %r11d
	je	.L179
	leaq	160(%r9,%rax), %rax
	leaq	cell.2(%rip), %rdi
	addq	$24, %r13
	xorb	%sil, (%rdi,%rax)
	addq	$1, (%rbx,%r11,8)
	cmpq	16(%rsp), %r13
	jne	.L121
.L176:
	movl	$1431655765, %eax
	leaq	action.0(%rip), %r14
	movq	24(%rsp), %r15
	leaq	cell.2(%rip), %rdi
	movd	%eax, %xmm6
	movq	%r14, %rsi
	pshufd	$0, %xmm6, %xmm4
	movaps	%xmm4, (%rsp)
	call	sqb_sweep
	movdqu	72(%rbx), %xmm0
	movdqu	88(%rbx), %xmm6
	leaq	1576(%rsp), %r9
	paddq	86320+cell.2(%rip), %xmm0
	movdqa	(%rsp), %xmm4
	movups	%xmm0, 72(%rbx)
	movq	%rax, %xmm0
	movhps	86312+cell.2(%rip), %xmm0
	paddq	%xmm6, %xmm0
	movups	%xmm0, 88(%rbx)
	leaq	1720(%rsp), %rax
.L141:
	movslq	4(%r15), %rdx
	movslq	8(%r15), %rcx
	movl	%edx, %esi
	sall	$5, %esi
	addl	%ecx, %esi
	movslq	%esi, %rsi
	movzbl	(%r14,%rsi), %edi
	movl	(%r15), %esi
	testl	%esi, %esi
	jne	.L122
	testl	%edi, %edi
	je	.L123
	addq	$1, 24(%rbx)
.L123:
	movslq	12(%r15), %rsi
	testl	%esi, %esi
	jne	.L124
	imulq	$10752, %rdx, %rdi
	imulq	$336, %rcx, %rsi
	addq	%rdi, %rsi
	leaq	cell.2(%rip), %rdi
	addq	%rdi, %rsi
	movdqa	(%rsi), %xmm0
	movaps	%xmm0, 1568(%rsp)
	movdqa	16(%rsi), %xmm0
	movaps	%xmm0, 1584(%rsp)
	movdqa	32(%rsi), %xmm0
	movaps	%xmm0, 1600(%rsp)
	movdqa	48(%rsi), %xmm0
	movaps	%xmm0, 1616(%rsp)
	movdqa	64(%rsi), %xmm0
	movaps	%xmm0, 1632(%rsp)
	movdqa	80(%rsi), %xmm0
	movaps	%xmm0, 1648(%rsp)
	movdqa	96(%rsi), %xmm0
	movaps	%xmm0, 1664(%rsp)
	movdqa	112(%rsi), %xmm0
	movaps	%xmm0, 1680(%rsp)
	movdqa	128(%rsi), %xmm0
	movq	144(%rsi), %rsi
	movq	%rsi, 1712(%rsp)
	movaps	%xmm0, 1696(%rsp)
.L125:
	salq	$5, %rdx
	leaq	sqb_item_at(%rip), %rdi
	addq	%rcx, %rdx
	movl	(%rdi,%rdx,4), %edx
	movl	%edx, %ecx
	sall	$4, %ecx
	addl	%edx, %ecx
	leaq	1568(%rsp), %rdx
	jmp	.L129
	.p2align 5
	.p2align 4,,10
	.p2align 3
.L181:
	addq	$1, %rdx
	addl	$91, %ecx
	cmpq	%rax, %rdx
	je	.L180
.L129:
	movl	%ecx, %esi
	xorl	$-91, %esi
	cmpb	%sil, (%rdx)
	je	.L181
	xorl	%edx, %edx
.L128:
	addq	%rdx, 48(%rbx)
.L130:
	addq	$24, %r15
	cmpq	16(%rsp), %r15
	jne	.L141
	leaq	cell.2(%rip), %r11
	leaq	sqb_item_at(%rip), %r10
	leaq	1024(%r10), %rbp
	movq	%r11, %r9
	leaq	1720(%rsp), %rdi
.L142:
	movq	%r11, %rsi
	xorl	%r8d, %r8d
	.p2align 4
	.p2align 3
.L147:
	cmpb	$0, 86016(%r9,%r8)
	je	.L143
	cmpl	$-559063315, 164(%rsi)
	je	.L145
	movdqa	(%rsi), %xmm0
	movq	144(%rsi), %rax
	movaps	%xmm0, 1568(%rsp)
	movdqa	16(%rsi), %xmm0
	movq	%rax, 1712(%rsp)
	movl	(%r10,%r8,4), %eax
	movaps	%xmm0, 1584(%rsp)
	movdqa	32(%rsi), %xmm0
	movl	%eax, %edx
	movaps	%xmm0, 1600(%rsp)
	movdqa	48(%rsi), %xmm0
	sall	$4, %edx
	addl	%eax, %edx
	leaq	1568(%rsp), %rax
	movaps	%xmm0, 1616(%rsp)
	movdqa	64(%rsi), %xmm0
	movaps	%xmm0, 1632(%rsp)
	movdqa	80(%rsi), %xmm0
	movaps	%xmm0, 1648(%rsp)
	movdqa	96(%rsi), %xmm0
	movaps	%xmm0, 1664(%rsp)
	movdqa	112(%rsi), %xmm0
	movaps	%xmm0, 1680(%rsp)
	movdqa	128(%rsi), %xmm0
	movaps	%xmm0, 1696(%rsp)
	jmp	.L146
	.p2align 5
	.p2align 4,,10
	.p2align 3
.L182:
	addq	$1, %rax
	addl	$91, %edx
	cmpq	%rdi, %rax
	je	.L143
.L146:
	movl	%edx, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, (%rax)
	je	.L182
.L145:
	addq	$1, 104(%rbx)
.L143:
	addq	$1, %r8
	addq	$336, %rsi
	cmpq	$32, %r8
	jne	.L147
	subq	$-128, %r10
	addq	$10752, %r11
	addq	$32, %r9
	cmpq	%r10, %rbp
	jne	.L142
	addl	$1, 112(%rbx)
	movq	1720(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L183
	addq	$1736, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 56
	popq	%rbx
	.cfi_def_cfa_offset 48
	popq	%rbp
	.cfi_def_cfa_offset 40
	popq	%r12
	.cfi_def_cfa_offset 32
	popq	%r13
	.cfi_def_cfa_offset 24
	popq	%r14
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	ret
.L177:
	.cfi_restore_state
	leaq	(%rax,%rdi), %rdx
	pxor	%xmm0, %xmm0
	xorq	%rax, %r8
	xorq	%rcx, %rdi
	rolq	$17, %rdx
	movq	%rcx, %rsi
	salq	$17, %rcx
	xorq	%rdi, %rax
	shrq	$11, %rdx
	xorq	%r8, %rsi
	rorq	$19, %rdi
	xorq	%rcx, %r8
	cvtsi2sdq	%rdx, %xmm0
	mulsd	%xmm1, %xmm0
	xorl	%r11d, %r11d
	movq	%rsi, %rcx
	comisd	%xmm0, %xmm2
	ja	.L117
	leaq	(%rax,%rdi), %rdx
	pxor	%xmm0, %xmm0
	xorq	%rax, %r8
	xorq	%rsi, %rdi
	rolq	$17, %rdx
	salq	$17, %rsi
	xorq	%r8, %rcx
	xorq	%rdi, %rax
	shrq	$11, %rdx
	xorl	%r11d, %r11d
	xorq	%rsi, %r8
	rorq	$19, %rdi
	cvtsi2sdq	%rdx, %xmm0
	mulsd	%xmm1, %xmm0
	movsd	.LC11(%rip), %xmm3
	ucomisd	%xmm0, %xmm3
	setbe	%r11b
	addl	$1, %r11d
	jmp	.L117
.L179:
	leaq	152(%r9,%rax), %rax
	leaq	cell.2(%rip), %rdi
	xorb	%sil, (%rdi,%rax)
	jmp	.L119
.L122:
	cmpl	$1, %esi
	jne	.L130
	testl	%edi, %edi
	je	.L131
	addq	$1, 32(%rbx)
.L131:
	movl	$16, %edi
	movslq	12(%r15), %rsi
	movd	%edi, %xmm2
	movl	$9, %edi
	movd	%edi, %xmm9
	movl	$13, %edi
	pshufd	$0, %xmm2, %xmm2
	movd	%edi, %xmm10
	movl	$5, %edi
	pshufd	$0, %xmm9, %xmm9
	movd	%edi, %xmm11
	pshufd	$0, %xmm10, %xmm10
	pshufd	$0, %xmm11, %xmm11
	testl	%esi, %esi
	jne	.L132
	imulq	$336, %rcx, %rsi
	leaq	cell.2(%rip), %rdi
	pxor	%xmm1, %xmm1
	movdqa	.LC0(%rip), %xmm6
	imulq	$10752, %rdx, %r11
	pcmpeqd	%xmm13, %xmm13
	movdqa	%xmm1, %xmm0
	movaps	%xmm2, (%rsp)
	pxor	%xmm14, %xmm14
	psrld	$31, %xmm13
	pxor	%xmm12, %xmm12
	addq	%rsi, %r11
	addq	%rdi, %r11
	movq	%r11, %rsi
	leaq	144(%r11), %rdi
.L133:
	movdqa	(%rsi), %xmm2
	addq	$16, %rsi
	movdqa	%xmm2, %xmm3
	punpckhbw	%xmm14, %xmm2
	punpcklbw	%xmm14, %xmm3
	movdqa	%xmm2, %xmm8
	punpckhwd	%xmm12, %xmm2
	movdqa	%xmm3, %xmm15
	punpcklwd	%xmm12, %xmm8
	punpckhwd	%xmm12, %xmm3
	punpcklwd	%xmm12, %xmm15
	movdqa	%xmm8, %xmm5
	movdqa	%xmm15, %xmm7
	paddd	%xmm2, %xmm5
	paddd	%xmm3, %xmm7
	paddd	%xmm7, %xmm5
	paddd	%xmm5, %xmm1
	movdqa	%xmm6, %xmm5
	paddd	%xmm11, %xmm5
	movdqa	%xmm5, %xmm7
	psrlq	$32, %xmm5
	pmuludq	%xmm3, %xmm7
	psrlq	$32, %xmm3
	pmuludq	%xmm3, %xmm5
	pshufd	$8, %xmm7, %xmm3
	movdqa	%xmm6, %xmm7
	pshufd	$8, %xmm5, %xmm5
	paddd	%xmm13, %xmm7
	punpckldq	%xmm5, %xmm3
	movdqa	%xmm7, %xmm5
	pmuludq	%xmm15, %xmm5
	psrlq	$32, %xmm7
	psrlq	$32, %xmm15
	pmuludq	%xmm15, %xmm7
	pshufd	$8, %xmm5, %xmm5
	pshufd	$8, %xmm7, %xmm7
	punpckldq	%xmm7, %xmm5
	paddd	%xmm5, %xmm3
	movdqa	%xmm6, %xmm5
	paddd	%xmm10, %xmm5
	movdqa	%xmm5, %xmm7
	psrlq	$32, %xmm5
	pmuludq	%xmm2, %xmm7
	psrlq	$32, %xmm2
	pmuludq	%xmm5, %xmm2
	pshufd	$8, %xmm7, %xmm5
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm5
	movdqa	%xmm6, %xmm2
	paddd	(%rsp), %xmm6
	paddd	%xmm9, %xmm2
	movdqa	%xmm2, %xmm7
	psrlq	$32, %xmm2
	pmuludq	%xmm8, %xmm7
	psrlq	$32, %xmm8
	pmuludq	%xmm8, %xmm2
	pshufd	$8, %xmm7, %xmm7
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm7
	paddd	%xmm7, %xmm5
	paddd	%xmm5, %xmm3
	paddd	%xmm3, %xmm0
	cmpq	%rdi, %rsi
	jne	.L133
	movdqa	%xmm1, %xmm2
	movl	$145, %esi
	psrldq	$8, %xmm2
	paddd	%xmm2, %xmm1
	movdqa	%xmm1, %xmm2
	psrldq	$4, %xmm2
	paddd	%xmm2, %xmm1
	movd	%xmm1, %r10d
	movdqa	%xmm0, %xmm1
	psrldq	$8, %xmm1
	paddd	%xmm1, %xmm0
	movdqa	%xmm0, %xmm1
	psrldq	$4, %xmm1
	paddd	%xmm1, %xmm0
	movd	%xmm0, %edi
.L134:
	movzbl	-1(%r11,%rsi), %r8d
	addl	%r8d, %r10d
	imull	%esi, %r8d
	addq	$1, %rsi
	addl	%r8d, %edi
	cmpq	$153, %rsi
	jne	.L134
	xorl	%esi, %esi
.L135:
	imulq	$168, %rsi, %rsi
	imulq	$10752, %rdx, %rdx
	imulq	$336, %rcx, %rcx
	addq	%rsi, %rdx
	leaq	cell.2(%rip), %rsi
	addq	%rcx, %rdx
	xorl	%ecx, %ecx
	addq	%rsi, %rdx
	cmpl	%r10d, 152(%rdx)
	jne	.L140
	xorl	%ecx, %ecx
	cmpl	%edi, 156(%rdx)
	sete	%cl
.L140:
	addq	%rcx, 56(%rbx)
	jmp	.L130
.L124:
	imulq	$336, %rcx, %r11
	leaq	cell.2(%rip), %rbp
	imulq	$168, %rsi, %rsi
	leaq	1568(%rsp), %rdi
	imulq	$10752, %rdx, %r10
	leaq	(%rsi,%r11), %r8
	addq	%r10, %r8
	addq	%rbp, %r8
	movq	%rdi, %rbp
	leaq	144(%r8), %r12
.L126:
	movdqu	(%r8), %xmm0
	addq	$16, %r8
	addq	$16, %rbp
	pxor	.LC8(%rip), %xmm0
	movaps	%xmm0, -16(%rbp)
	cmpq	%r8, %r12
	jne	.L126
	leaq	144+cell.2(%rip), %r8
	addq	%r8, %rsi
	addq	%r11, %rsi
	addq	%r10, %rsi
.L127:
	movzbl	(%rsi), %r8d
	addq	$1, %rdi
	addq	$1, %rsi
	xorl	$85, %r8d
	movb	%r8b, 143(%rdi)
	cmpq	%r9, %rdi
	jne	.L127
	jmp	.L125
.L132:
	imulq	$336, %rcx, %rbp
	leaq	cell.2(%rip), %r10
	movdqa	%xmm4, %xmm1
	imulq	$168, %rsi, %r12
	leaq	1568(%rsp), %r8
	imulq	$10752, %rdx, %r11
	leaq	(%r12,%rbp), %rdi
	addq	%r11, %rdi
	addq	%r10, %rdi
	movq	%r8, %r10
	leaq	144(%rdi), %r13
.L136:
	movdqu	(%rdi), %xmm0
	addq	$16, %rdi
	addq	$16, %r10
	pxor	%xmm1, %xmm0
	movaps	%xmm0, -16(%r10)
	cmpq	%rdi, %r13
	jne	.L136
	leaq	144+cell.2(%rip), %rdi
	leaq	1568(%rsp), %r10
	addq	%r12, %rdi
	addq	%rbp, %rdi
	leaq	1576(%rsp), %rbp
	addq	%r11, %rdi
.L137:
	movzbl	(%rdi), %r11d
	addq	$1, %r10
	addq	$1, %rdi
	xorl	$85, %r11d
	movb	%r11b, 143(%r10)
	cmpq	%r10, %rbp
	jne	.L137
	pxor	%xmm1, %xmm1
	pcmpeqd	%xmm12, %xmm12
	movdqa	.LC0(%rip), %xmm6
	leaq	1712(%rsp), %r10
	leaq	1568(%rsp), %rdi
	movdqa	%xmm1, %xmm0
	pxor	%xmm13, %xmm13
	movaps	%xmm2, (%rsp)
	pxor	%xmm8, %xmm8
	psrld	$31, %xmm12
.L138:
	movdqa	(%rdi), %xmm2
	addq	$16, %rdi
	movdqa	%xmm2, %xmm3
	punpckhbw	%xmm13, %xmm2
	punpcklbw	%xmm13, %xmm3
	movdqa	%xmm2, %xmm14
	punpckhwd	%xmm8, %xmm2
	movdqa	%xmm3, %xmm15
	punpcklwd	%xmm8, %xmm14
	punpckhwd	%xmm8, %xmm3
	punpcklwd	%xmm8, %xmm15
	movdqa	%xmm14, %xmm7
	movdqa	%xmm15, %xmm5
	paddd	%xmm2, %xmm7
	paddd	%xmm3, %xmm5
	paddd	%xmm7, %xmm5
	paddd	%xmm5, %xmm1
	movdqa	%xmm6, %xmm5
	paddd	%xmm11, %xmm5
	movdqa	%xmm5, %xmm7
	psrlq	$32, %xmm5
	pmuludq	%xmm3, %xmm7
	psrlq	$32, %xmm3
	pmuludq	%xmm3, %xmm5
	pshufd	$8, %xmm7, %xmm3
	movdqa	%xmm6, %xmm7
	pshufd	$8, %xmm5, %xmm5
	paddd	%xmm12, %xmm7
	punpckldq	%xmm5, %xmm3
	movdqa	%xmm7, %xmm5
	pmuludq	%xmm15, %xmm5
	psrlq	$32, %xmm7
	psrlq	$32, %xmm15
	pmuludq	%xmm15, %xmm7
	pshufd	$8, %xmm5, %xmm5
	pshufd	$8, %xmm7, %xmm7
	punpckldq	%xmm7, %xmm5
	paddd	%xmm5, %xmm3
	movdqa	%xmm6, %xmm5
	paddd	%xmm10, %xmm5
	movdqa	%xmm5, %xmm7
	psrlq	$32, %xmm5
	pmuludq	%xmm2, %xmm7
	psrlq	$32, %xmm2
	pmuludq	%xmm5, %xmm2
	pshufd	$8, %xmm7, %xmm5
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm5
	movdqa	%xmm6, %xmm2
	paddd	(%rsp), %xmm6
	paddd	%xmm9, %xmm2
	movdqa	%xmm2, %xmm7
	psrlq	$32, %xmm2
	pmuludq	%xmm14, %xmm7
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm2
	pshufd	$8, %xmm7, %xmm7
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm7
	paddd	%xmm7, %xmm5
	paddd	%xmm5, %xmm3
	paddd	%xmm3, %xmm0
	cmpq	%r10, %rdi
	jne	.L138
	movdqa	%xmm1, %xmm2
	movl	$144, %ebp
	psrldq	$8, %xmm2
	paddd	%xmm2, %xmm1
	movdqa	%xmm1, %xmm2
	psrldq	$4, %xmm2
	paddd	%xmm2, %xmm1
	movd	%xmm1, %r10d
	movdqa	%xmm0, %xmm1
	psrldq	$8, %xmm1
	paddd	%xmm1, %xmm0
	movdqa	%xmm0, %xmm1
	psrldq	$4, %xmm1
	paddd	%xmm1, %xmm0
	movd	%xmm0, %edi
.L139:
	movzbl	144(%r8), %r11d
	addl	$1, %ebp
	addq	$1, %r8
	addl	%r11d, %r10d
	imull	%ebp, %r11d
	addl	%r11d, %edi
	cmpl	$152, %ebp
	jne	.L139
	jmp	.L135
.L180:
	movl	$1, %edx
	jmp	.L128
.L183:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE47:
	.size	cert_round.constprop.0, .-cert_round.constprop.0
	.section	.rodata.str1.8,"aMS",@progbits,1
	.align 8
.LC18:
	.string	"SQ2BOR O1_payload_det   %lld/%lld = %.6f  expect=1.000000 counting [A]\n"
	.align 8
.LC19:
	.string	"SQ2BOR O2_payload_rep   %lld/%lld = %.6f  expect>=0.990 measurement [A]\n"
	.align 8
.LC20:
	.string	"SQ2BOR O3_syndrome_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n"
	.align 8
.LC21:
	.string	"SQ2BOR O4_syndrome_rep  %lld/%lld = %.6f  expect=1.000000 measurement [A]\n"
	.align 8
.LC22:
	.string	"SQ2BOR O5_closure       %lld unresolved [A]  expect=0\n"
	.align 8
.LC23:
	.string	"SQ2BOR O6_apoptosis     %lld [A]  expect=0 isolated\n"
	.align 8
.LC25:
	.string	"SQ2BOR O7_blind_random  %lld/%lld detected+tombstoned (never silent)  expect=1.000000\n"
	.align 8
.LC26:
	.string	"SQ2BOR O8_blind_crafted %lld/%lld blind  expect=all-blind documented-exclusion\n"
	.align 8
.LC27:
	.string	"SQ2BOR auxB_det         %lld/%lld = %.6f  poisson tail\n"
	.align 8
.LC28:
	.string	"SQ2BOR auxB_rep         %lld/%lld = %.6f  poisson tail\n"
	.align 8
.LC29:
	.string	"SQ2BOR auxB_tombs       %lld  auxB_coh_fail %lld  auxB_slippage %lld  auxB_unresolved %lld\n"
	.align 8
.LC30:
	.string	"SQ2BOR aux_proofread_retries %lld (GTP bill, should be 0 absent injection)\n"
	.section	.text.startup,"ax",@progbits
	.p2align 4
	.globl	main
	.type	main, @function
main:
.LFB45:
	.cfi_startproc
	pushq	%r15
	.cfi_def_cfa_offset 16
	.cfi_offset 15, -16
	pushq	%r14
	.cfi_def_cfa_offset 24
	.cfi_offset 14, -24
	pushq	%r13
	.cfi_def_cfa_offset 32
	.cfi_offset 13, -32
	pushq	%r12
	.cfi_def_cfa_offset 40
	.cfi_offset 12, -40
	pushq	%rbp
	.cfi_def_cfa_offset 48
	.cfi_offset 6, -48
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	subq	$728, %rsp
	.cfi_def_cfa_offset 784
	movq	%fs:40, %rax
	movq	%rax, 712(%rsp)
	xorl	%eax, %eax
	movl	$1500, 204(%rsp)
	cmpl	$1, %edi
	jle	.L185
	movq	8(%rsi), %rdi
	movl	$10, %edx
	xorl	%esi, %esi
	call	__isoc23_strtol@PLT
	movl	%eax, 204(%rsp)
.L185:
	movabsq	$-1100507917760583744, %r12
	movl	$10, %eax
	movabsq	$-7723592293110652910, %r13
	movabsq	$-4658895280553055330, %rbx
	movabsq	$-7046029254386300356, %rbp
.L186:
	movq	%rbx, %rdx
	xorq	%rbp, %r13
	xorq	%rbx, %r12
	salq	$17, %rdx
	xorq	%r13, %rbx
	xorq	%r12, %rbp
	rorq	$19, %r12
	xorq	%rdx, %r13
	subl	$1, %eax
	jne	.L186
	leaq	cell.2(%rip), %r15
	movl	$86336, %edx
	xorl	%esi, %esi
	xorl	%r14d, %r14d
	movq	%r15, %rdi
	call	memset@PLT
	leaq	144(%r15), %rax
	xorl	%ecx, %ecx
	xorl	%esi, %esi
	pxor	%xmm12, %xmm12
	movq	%rax, 192(%rsp)
	movl	$1431655765, %eax
	pcmpeqd	%xmm0, %xmm0
	movd	%eax, %xmm3
	movb	$0, 191(%rsp)
	movl	$48, %r8d
	movl	$6, %edx
	pshufd	$0, %xmm3, %xmm13
	movb	$0, 176(%rsp)
	movdqa	%xmm12, %xmm3
	movl	$0, 200(%rsp)
	psubb	%xmm0, %xmm3
	movq	%r13, 208(%rsp)
	movq	%rbx, 216(%rsp)
	movq	%rbp, 224(%rsp)
	movq	%r12, 232(%rsp)
	movaps	%xmm3, 48(%rsp)
.L199:
	xorl	%eax, %eax
	jmp	.L189
	.p2align 5
	.p2align 4,,10
	.p2align 3
.L240:
	leal	(%rdx,%rax), %ecx
	andl	$7, %ecx
	movl	86272(%r15,%rcx,4), %ecx
.L189:
	cmpl	$31, %ecx
	jle	.L187
	addl	$1, %eax
	cmpl	$8, %eax
	jne	.L240
.L188:
	addl	$1, %esi
	cmpl	$256, %esi
	je	.L198
.L242:
	movl	%esi, %edx
	leaq	SQB_SCATLT(%rip), %rax
	addl	$17, %r8d
	andl	$31, %edx
	movl	(%rax,%rdx,4), %eax
	movl	86272(%r15,%rax,4), %ecx
	movq	%rax, %rdx
	jmp	.L199
.L187:
	movl	$16, %ecx
	movl	$12, %edi
	movl	$4, %ebx
	movd	%ecx, %xmm3
	movl	$13, %ecx
	movd	%edi, %xmm4
	movl	$-1515870811, %edi
	pshufd	$0, %xmm3, %xmm5
	movd	%ecx, %xmm3
	movl	$9, %ecx
	pxor	%xmm6, %xmm6
	pshufd	$0, %xmm3, %xmm0
	movd	%ecx, %xmm3
	movl	$5, %ecx
	pshufd	$0, %xmm4, %xmm4
	pshufd	$0, %xmm3, %xmm1
	movd	%ecx, %xmm3
	leal	(%rax,%rdx), %ecx
	movaps	%xmm4, (%rsp)
	andl	$7, %ecx
	movd	%edi, %xmm4
	movd	%ebx, %xmm15
	pshufd	$0, %xmm3, %xmm2
	pshufd	$0, %xmm4, %xmm4
	movaps	%xmm4, 16(%rsp)
	pcmpeqd	%xmm4, %xmm4
	movl	86272(%r15,%rcx,4), %eax
	movl	$8, %ebx
	pcmpeqd	%xmm10, %xmm10
	movdqa	.LC0(%rip), %xmm3
	leaq	704(%rsp), %rdx
	movl	%eax, 88(%rsp)
	leal	-48(%r8), %eax
	psrld	$31, %xmm4
	movd	%ebx, %xmm14
	movd	%eax, %xmm11
	movdqa	%xmm6, %xmm7
	movaps	%xmm4, 32(%rsp)
	leaq	560(%rsp), %rax
	punpcklbw	%xmm11, %xmm11
	psrlw	$8, %xmm10
	movaps	%xmm2, 64(%rsp)
	pshufd	$0, %xmm15, %xmm15
	punpcklwd	%xmm11, %xmm11
	movaps	%xmm1, 96(%rsp)
	pshufd	$0, %xmm14, %xmm14
	pshufd	$0, %xmm11, %xmm11
	movaps	%xmm0, 112(%rsp)
	movaps	%xmm5, 128(%rsp)
	.p2align 4
	.p2align 3
.L190:
	movdqa	%xmm3, %xmm2
	movdqa	%xmm3, %xmm0
	movdqa	%xmm3, %xmm1
	addq	$16, %rax
	paddd	%xmm15, %xmm2
	movdqa	(%rsp), %xmm4
	pxor	%xmm8, %xmm8
	punpcklwd	%xmm2, %xmm0
	punpckhwd	%xmm2, %xmm1
	movdqa	%xmm0, %xmm2
	punpcklwd	%xmm1, %xmm0
	paddd	%xmm3, %xmm4
	punpckhwd	%xmm1, %xmm2
	movdqa	%xmm3, %xmm1
	paddd	%xmm14, %xmm1
	punpcklwd	%xmm2, %xmm0
	movdqa	%xmm1, %xmm2
	punpcklwd	%xmm4, %xmm1
	pand	%xmm10, %xmm0
	punpckhwd	%xmm4, %xmm2
	movdqa	%xmm1, %xmm4
	punpckhwd	%xmm2, %xmm4
	punpcklwd	%xmm2, %xmm1
	movdqa	%xmm0, %xmm2
	punpcklwd	%xmm4, %xmm1
	pand	%xmm10, %xmm1
	packuswb	%xmm1, %xmm2
	movdqa	%xmm2, %xmm1
	paddb	%xmm2, %xmm1
	paddb	%xmm2, %xmm1
	paddb	%xmm1, %xmm1
	paddb	%xmm1, %xmm1
	paddb	%xmm1, %xmm1
	psubb	%xmm2, %xmm1
	paddb	%xmm1, %xmm1
	paddb	%xmm1, %xmm1
	movdqa	%xmm1, %xmm0
	psubb	%xmm2, %xmm0
	paddb	%xmm11, %xmm0
	pxor	16(%rsp), %xmm0
	movdqa	%xmm0, %xmm2
	movdqa	%xmm0, %xmm1
	movaps	%xmm0, -16(%rax)
	punpcklbw	%xmm12, %xmm2
	punpckhbw	%xmm12, %xmm1
	movdqa	%xmm2, %xmm4
	movdqa	%xmm1, %xmm5
	punpckhwd	%xmm8, %xmm2
	punpckhwd	%xmm8, %xmm1
	punpcklwd	%xmm8, %xmm4
	punpcklwd	%xmm8, %xmm5
	movdqa	%xmm1, %xmm9
	movdqa	%xmm2, %xmm8
	paddd	%xmm5, %xmm9
	paddd	%xmm4, %xmm8
	paddd	%xmm9, %xmm8
	movdqa	32(%rsp), %xmm9
	paddd	%xmm8, %xmm6
	paddd	%xmm3, %xmm9
	movdqa	%xmm9, %xmm8
	psrlq	$32, %xmm9
	pmuludq	%xmm4, %xmm8
	psrlq	$32, %xmm4
	pmuludq	%xmm9, %xmm4
	movdqa	.LC6(%rip), %xmm9
	paddd	%xmm3, %xmm9
	pshufd	$8, %xmm8, %xmm8
	pshufd	$8, %xmm4, %xmm4
	punpckldq	%xmm4, %xmm8
	movdqa	%xmm9, %xmm4
	pmuludq	%xmm2, %xmm4
	psrlq	$32, %xmm9
	psrlq	$32, %xmm2
	pmuludq	%xmm9, %xmm2
	pshufd	$8, %xmm4, %xmm4
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm4
	paddd	%xmm8, %xmm4
	movdqa	.LC3(%rip), %xmm8
	paddd	%xmm3, %xmm8
	movdqa	%xmm8, %xmm2
	psrlq	$32, %xmm8
	pmuludq	%xmm5, %xmm2
	psrlq	$32, %xmm5
	pmuludq	%xmm8, %xmm5
	movdqa	.LC4(%rip), %xmm8
	paddd	%xmm3, %xmm8
	paddd	.LC7(%rip), %xmm3
	pshufd	$8, %xmm2, %xmm2
	pshufd	$8, %xmm5, %xmm5
	punpckldq	%xmm5, %xmm2
	movdqa	%xmm8, %xmm5
	pmuludq	%xmm1, %xmm5
	psrlq	$32, %xmm8
	psrlq	$32, %xmm1
	pmuludq	%xmm8, %xmm1
	pshufd	$8, %xmm5, %xmm5
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm5
	paddd	%xmm5, %xmm2
	paddd	%xmm2, %xmm4
	paddd	%xmm4, %xmm7
	cmpq	%rdx, %rax
	jne	.L190
	movdqa	%xmm6, %xmm3
	movdqa	64(%rsp), %xmm2
	movdqa	96(%rsp), %xmm1
	leaq	560(%rsp), %r11
	psrldq	$8, %xmm3
	movdqa	112(%rsp), %xmm0
	movl	%r8d, %edi
	movl	$144, %edx
	movdqa	128(%rsp), %xmm5
	paddd	%xmm3, %xmm6
	movdqa	%xmm6, %xmm3
	psrldq	$4, %xmm3
	paddd	%xmm3, %xmm6
	movdqa	%xmm7, %xmm3
	psrldq	$8, %xmm3
	movd	%xmm6, %r9d
	paddd	%xmm3, %xmm7
	movdqa	%xmm7, %xmm3
	psrldq	$4, %xmm3
	paddd	%xmm3, %xmm7
	movd	%xmm7, %r10d
	.p2align 6
	.p2align 4
	.p2align 3
.L191:
	movl	%edi, %eax
	addl	$1, %edx
	addl	$91, %edi
	addq	$1, %r11
	xorl	$-91, %eax
	movb	%al, 143(%r11)
	movzbl	%al, %eax
	addl	%eax, %r9d
	imull	%edx, %eax
	addl	%eax, %r10d
	cmpl	$152, %edx
	jne	.L191
	leaq	2(%r14), %rax
	leaq	312+cell.2(%rip), %rbx
	movdqa	%xmm0, %xmm14
	movl	%esi, 128(%rsp)
	imulq	$10752, %rcx, %rdx
	pcmpeqd	%xmm0, %xmm0
	movq	%rax, 168(%rsp)
	movslq	88(%rsp), %rax
	psrld	$31, %xmm0
	movdqa	%xmm1, %xmm11
	movaps	%xmm2, (%rsp)
	imulq	$336, %rax, %rdi
	movb	%r8b, 152(%rsp)
	addq	%rdx, %rbx
	movq	%rcx, 160(%rsp)
	movaps	%xmm0, 16(%rsp)
	leaq	(%rdi,%rdx), %rbp
	addq	%rdi, %rbx
	movaps	%xmm5, 32(%rsp)
	leaq	168(%rdi,%rdx), %r11
	movq	%rbx, 96(%rsp)
	leaq	168(%r15,%rbp), %r12
	leaq	(%r15,%rbp), %rbx
	addq	%r15, %r11
	movq	192(%rsp), %rbp
	movq	%r11, 144(%rsp)
	leaq	144(%r11), %r13
	movq	%rax, %r11
	addq	%rbp, %rdx
	leaq	568(%rsp), %rbp
	addq	%rdx, %rdi
	movq	%rdi, 112(%rsp)
.L197:
	movq	704(%rsp), %rax
	leaq	560(%rsp), %rdx
	movdqa	560(%rsp), %xmm0
	movaps	%xmm0, (%rbx)
	movdqa	576(%rsp), %xmm0
	movq	%rax, 144(%rbx)
	movq	144(%rsp), %rax
	movaps	%xmm0, 16(%rbx)
	movdqa	592(%rsp), %xmm0
	movaps	%xmm0, 32(%rbx)
	movdqa	608(%rsp), %xmm0
	movaps	%xmm0, 48(%rbx)
	movdqa	624(%rsp), %xmm0
	movaps	%xmm0, 64(%rbx)
	movdqa	640(%rsp), %xmm0
	movaps	%xmm0, 80(%rbx)
	movdqa	656(%rsp), %xmm0
	movaps	%xmm0, 96(%rbx)
	movdqa	672(%rsp), %xmm0
	movaps	%xmm0, 112(%rbx)
	movdqa	688(%rsp), %xmm0
	movaps	%xmm0, 128(%rbx)
	.p2align 5
	.p2align 4
	.p2align 3
.L192:
	movdqa	(%rdx), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm13, %xmm0
	movups	%xmm0, -16(%rax)
	cmpq	%rax, %r13
	jne	.L192
	movq	96(%rsp), %rcx
	leaq	560(%rsp), %rax
	.p2align 5
	.p2align 4
	.p2align 3
.L193:
	movzbl	144(%rax), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, -1(%rcx)
	cmpq	%rax, %rbp
	jne	.L193
	pxor	%xmm5, %xmm5
	movdqa	.LC0(%rip), %xmm2
	xorl	%eax, %eax
	pxor	%xmm1, %xmm1
	movdqa	%xmm5, %xmm4
	movdqa	%xmm5, %xmm3
	.p2align 4
	.p2align 3
.L194:
	movdqa	(%rbx,%rax), %xmm8
	movdqa	%xmm8, %xmm9
	movdqa	%xmm8, %xmm6
	punpcklbw	%xmm12, %xmm9
	punpckhbw	%xmm12, %xmm6
	movdqa	%xmm9, %xmm10
	movdqa	%xmm6, %xmm15
	punpckhwd	%xmm1, %xmm9
	punpcklwd	%xmm1, %xmm10
	punpcklwd	%xmm1, %xmm15
	punpckhwd	%xmm1, %xmm6
	movdqa	%xmm15, %xmm0
	movdqa	%xmm10, %xmm7
	paddd	%xmm9, %xmm7
	paddd	%xmm6, %xmm0
	paddd	%xmm7, %xmm0
	movdqa	%xmm2, %xmm7
	paddd	%xmm14, %xmm7
	paddd	%xmm0, %xmm4
	movdqa	%xmm7, %xmm0
	psrlq	$32, %xmm7
	pmuludq	%xmm6, %xmm0
	psrlq	$32, %xmm6
	pmuludq	%xmm7, %xmm6
	movdqa	%xmm2, %xmm7
	paddd	%xmm11, %xmm7
	pshufd	$8, %xmm0, %xmm0
	pshufd	$8, %xmm6, %xmm6
	punpckldq	%xmm6, %xmm0
	movdqa	%xmm7, %xmm6
	pmuludq	%xmm15, %xmm6
	psrlq	$32, %xmm7
	psrlq	$32, %xmm15
	pmuludq	%xmm15, %xmm7
	pshufd	$8, %xmm6, %xmm6
	pshufd	$8, %xmm7, %xmm7
	punpckldq	%xmm7, %xmm6
	paddd	%xmm6, %xmm0
	movdqa	(%rsp), %xmm6
	paddd	%xmm2, %xmm6
	movdqa	%xmm6, %xmm7
	psrlq	$32, %xmm6
	pmuludq	%xmm9, %xmm7
	psrlq	$32, %xmm9
	pmuludq	%xmm9, %xmm6
	pshufd	$8, %xmm7, %xmm7
	pshufd	$8, %xmm6, %xmm6
	punpckldq	%xmm6, %xmm7
	movdqa	16(%rsp), %xmm6
	paddd	%xmm2, %xmm6
	paddd	32(%rsp), %xmm2
	movdqa	%xmm6, %xmm9
	psrlq	$32, %xmm6
	pmuludq	%xmm10, %xmm9
	psrlq	$32, %xmm10
	pmuludq	%xmm10, %xmm6
	pshufd	$8, %xmm9, %xmm9
	pshufd	$8, %xmm6, %xmm6
	punpckldq	%xmm6, %xmm9
	paddd	%xmm9, %xmm7
	paddd	%xmm7, %xmm0
	paddd	%xmm0, %xmm3
	movdqu	(%r12,%rax), %xmm0
	addq	$16, %rax
	pxor	%xmm8, %xmm0
	pcmpeqb	%xmm13, %xmm0
	pcmpeqb	%xmm12, %xmm0
	pand	48(%rsp), %xmm0
	movdqa	%xmm0, %xmm6
	punpckhbw	%xmm12, %xmm0
	punpcklbw	%xmm12, %xmm6
	movdqa	%xmm6, %xmm7
	punpckhwd	%xmm1, %xmm6
	punpcklwd	%xmm1, %xmm7
	por	%xmm7, %xmm6
	movdqa	%xmm0, %xmm7
	punpckhwd	%xmm1, %xmm0
	punpcklwd	%xmm1, %xmm7
	por	%xmm7, %xmm0
	por	%xmm0, %xmm6
	por	%xmm6, %xmm5
	cmpq	$144, %rax
	jne	.L194
	movdqa	%xmm5, %xmm0
	movq	%r12, 64(%rsp)
	movq	112(%rsp), %rsi
	movl	$144, %ecx
	psrldq	$8, %xmm0
	por	%xmm0, %xmm5
	movdqa	%xmm5, %xmm0
	psrldq	$4, %xmm0
	por	%xmm0, %xmm5
	movdqa	%xmm4, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm5, %edx
	paddd	%xmm0, %xmm4
	movdqa	%xmm4, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm4
	movdqa	%xmm3, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm4, %edi
	paddd	%xmm0, %xmm3
	movdqa	%xmm3, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm3
	movd	%xmm3, %r8d
	.p2align 6
	.p2align 4
	.p2align 3
.L195:
	movzbl	(%rsi), %eax
	movzbl	168(%rsi), %r12d
	xorl	%eax, %r12d
	cmpb	$85, %r12b
	setne	%r12b
	addl	$1, %ecx
	addl	%eax, %edi
	addq	$1, %rsi
	imull	%ecx, %eax
	movzbl	%r12b, %r12d
	orl	%r12d, %edx
	addl	%eax, %r8d
	cmpl	$152, %ecx
	jne	.L195
	cmpl	%r10d, %r8d
	movq	64(%rsp), %r12
	sete	%al
	cmpl	%r9d, %edi
	sete	%cl
	xorl	$1, %edx
	andl	%eax, %ecx
	andb	%dl, %cl
	jne	.L241
	movb	$1, 176(%rsp)
	addq	$1, %r14
	cmpq	168(%rsp), %r14
	jne	.L197
	imulq	$336, %r11, %rax
	movl	128(%rsp), %esi
	movzbl	152(%rsp), %r8d
	imulq	$10752, 160(%rsp), %rcx
	addl	$1, %esi
	addq	%rcx, %rax
	movl	%r10d, 324(%r15,%rax)
	movl	%r9d, 320(%r15,%rax)
	movl	%r10d, 156(%r15,%rax)
	movl	%r9d, 152(%r15,%rax)
	cmpl	$256, %esi
	jne	.L242
.L198:
	movq	208(%rsp), %r13
	movq	216(%rsp), %rbx
	movq	224(%rsp), %rbp
	movq	232(%rsp), %r12
	cmpb	$0, 191(%rsp)
	je	.L200
	movl	200(%rsp), %eax
	movl	%eax, 86304+cell.2(%rip)
.L200:
	cmpb	$0, 176(%rsp)
	je	.L201
	movq	%r14, 86312+cell.2(%rip)
.L201:
	movl	$86336, %edx
	movq	%r15, %rsi
	leaq	clean.1(%rip), %rdi
	call	memcpy@PLT
	movl	204(%rsp), %r14d
	pxor	%xmm0, %xmm0
	movq	$0, 416(%rsp)
	movq	$0, 544(%rsp)
	movaps	%xmm0, 304(%rsp)
	movaps	%xmm0, 320(%rsp)
	movaps	%xmm0, 336(%rsp)
	movaps	%xmm0, 352(%rsp)
	movaps	%xmm0, 368(%rsp)
	movaps	%xmm0, 384(%rsp)
	movaps	%xmm0, 400(%rsp)
	movaps	%xmm0, 432(%rsp)
	movaps	%xmm0, 448(%rsp)
	movaps	%xmm0, 464(%rsp)
	movaps	%xmm0, 480(%rsp)
	movaps	%xmm0, 496(%rsp)
	movaps	%xmm0, 512(%rsp)
	movaps	%xmm0, 528(%rsp)
	testl	%r14d, %r14d
	jle	.L202
	pxor	%xmm1, %xmm1
	xorl	%ecx, %ecx
	xorl	%r15d, %r15d
	movl	$3435973837, %r8d
	movdqa	%xmm1, %xmm2
	movdqa	%xmm1, %xmm3
	movdqa	%xmm1, %xmm0
.L204:
	movl	%r15d, %eax
	imulq	%r8, %rax
	shrq	$34, %rax
	leal	(%rax,%rax,4), %edx
	movl	%r15d, %eax
	subl	%edx, %eax
	xorl	%edx, %edx
	cmpl	$2, %eax
	jle	.L203
	xorl	%edx, %edx
	cmpl	$3, %eax
	setne	%dl
	addl	$1, %edx
.L203:
	movq	%rcx, 376(%rsp)
	movl	$1, %esi
	addl	$1, %r15d
	leaq	304(%rsp), %rcx
	leaq	272(%rsp), %rdi
	movq	%rbp, 272(%rsp)
	movq	%rbx, 280(%rsp)
	movq	%r13, 288(%rsp)
	movq	%r12, 296(%rsp)
	movaps	%xmm0, 304(%rsp)
	movups	%xmm3, 328(%rsp)
	movaps	%xmm2, 352(%rsp)
	movups	%xmm1, 392(%rsp)
	call	cert_round.constprop.0
	cmpl	%r15d, 204(%rsp)
	movq	272(%rsp), %rbp
	movl	$3435973837, %r8d
	movq	280(%rsp), %rbx
	movq	288(%rsp), %r13
	movq	296(%rsp), %r12
	movdqa	304(%rsp), %xmm0
	movdqu	328(%rsp), %xmm3
	movdqa	352(%rsp), %xmm2
	movq	376(%rsp), %rcx
	movdqu	392(%rsp), %xmm1
	jne	.L204
	movl	204(%rsp), %eax
	movq	%rcx, 168(%rsp)
	movq	%xmm3, %rcx
	movhps	%xmm0, 32(%rsp)
	movq	%xmm0, 48(%rsp)
	movhps	%xmm3, 64(%rsp)
	movhps	%xmm2, 88(%rsp)
	movq	%xmm2, 96(%rsp)
	movhps	%xmm1, 160(%rsp)
	movq	%xmm1, 152(%rsp)
	cmpl	$2, %eax
	jle	.L218
	movl	$2863311531, %edx
	xorl	%edi, %edi
	xorl	%r11d, %r11d
	xorl	%r9d, %r9d
	imulq	%rdx, %rax
	movq	$0, (%rsp)
	xorl	%esi, %esi
	xorl	%edx, %edx
	xorl	%r10d, %r10d
	xorl	%r15d, %r15d
	xorl	%r14d, %r14d
	movq	%rdi, %rcx
	movq	$0, 16(%rsp)
	movq	%xmm3, 128(%rsp)
	shrq	$33, %rax
	movq	%rax, 112(%rsp)
	movq	%rbx, %rax
	xorl	%ebx, %ebx
.L206:
	movq	%rax, 280(%rsp)
	movq	(%rsp), %rax
	addl	$1, %ebx
	movq	%rcx, 432(%rsp)
	leaq	432(%rsp), %rcx
	movq	%rax, 456(%rsp)
	movq	16(%rsp), %rax
	movq	%rdx, 440(%rsp)
	movl	$-1, %edx
	movq	%rsi, 504(%rsp)
	movl	$12, %esi
	movq	%rdi, 512(%rsp)
	leaq	272(%rsp), %rdi
	movq	%rbp, 272(%rsp)
	movq	%r13, 288(%rsp)
	movq	%r12, 296(%rsp)
	movq	%rax, 464(%rsp)
	movq	%r14, 480(%rsp)
	movq	%r15, 488(%rsp)
	movq	%r9, 520(%rsp)
	movq	%r10, 528(%rsp)
	movq	%r11, 536(%rsp)
	call	cert_round.constprop.0
	movq	456(%rsp), %rdi
	movq	272(%rsp), %rbp
	movq	280(%rsp), %rax
	movq	288(%rsp), %r13
	movq	%rdi, (%rsp)
	movq	464(%rsp), %rdi
	movq	296(%rsp), %r12
	movq	432(%rsp), %rcx
	movq	%rdi, 16(%rsp)
	movq	440(%rsp), %rdx
	movq	480(%rsp), %r14
	movq	488(%rsp), %r15
	movq	504(%rsp), %rsi
	movq	512(%rsp), %rdi
	movq	520(%rsp), %r9
	movq	528(%rsp), %r10
	movq	536(%rsp), %r11
	cmpl	%ebx, 112(%rsp)
	jg	.L206
	movq	%rcx, %rbp
	movq	%r9, 112(%rsp)
	movq	%rdx, %rbx
	movq	%rsi, %r13
	movq	128(%rsp), %rcx
	movq	%r11, 144(%rsp)
	movq	%rdi, %r12
	movq	%r10, 128(%rsp)
.L205:
	leaq	264(%rsp), %rdx
	leaq	256(%rsp), %rsi
	movq	%rcx, 176(%rsp)
	leaq	248(%rsp), %rdi
	movq	$0, 248(%rsp)
	movq	$0, 256(%rsp)
	movq	$0, 264(%rsp)
	call	sq2b_blind_pass.constprop.0
	cmpq	$0, 48(%rsp)
	movq	176(%rsp), %rcx
	je	.L207
	movq	48(%rsp), %rdx
	pxor	%xmm1, %xmm1
	pxor	%xmm0, %xmm0
	movq	%rcx, %rsi
	cvtsi2sdq	%rcx, %xmm0
	leaq	.LC18(%rip), %rdi
	movl	$1, %eax
	cvtsi2sdq	%rdx, %xmm1
	divsd	%xmm1, %xmm0
	movsd	%xmm1, 176(%rsp)
	call	printf@PLT
	pxor	%xmm0, %xmm0
	cvtsi2sdq	96(%rsp), %xmm0
	divsd	176(%rsp), %xmm0
.L209:
	movq	48(%rsp), %rdx
	movq	96(%rsp), %rsi
	movl	$1, %eax
	leaq	.LC19(%rip), %rdi
	call	printf@PLT
	cmpq	$0, 32(%rsp)
	jne	.L210
	movq	64(%rsp), %rsi
	pxor	%xmm0, %xmm0
	xorl	%edx, %edx
	movl	$1, %eax
	leaq	.LC20(%rip), %rdi
	call	printf@PLT
	pxor	%xmm0, %xmm0
.L211:
	movq	32(%rsp), %rdx
	movq	88(%rsp), %rsi
	movl	$1, %eax
	addq	%r15, %r14
	leaq	.LC21(%rip), %rdi
	call	printf@PLT
	movq	152(%rsp), %rsi
	leaq	.LC22(%rip), %rdi
	xorl	%eax, %eax
	call	printf@PLT
	movq	168(%rsp), %rsi
	leaq	.LC23(%rip), %rdi
	xorl	%eax, %eax
	call	printf@PLT
	movl	$2000, %edx
	leaq	.LC25(%rip), %rdi
	movq	248(%rsp), %rsi
	pxor	%xmm0, %xmm0
	movl	$1, %eax
	cvtsi2sdq	%rsi, %xmm0
	divsd	.LC24(%rip), %xmm0
	call	printf@PLT
	xorl	%eax, %eax
	movq	264(%rsp), %rsi
	movl	$2000, %edx
	leaq	.LC26(%rip), %rdi
	call	printf@PLT
	movq	(%rsp), %rsi
	addq	16(%rsp), %rsi
	addq	%rbp, %rbx
	jne	.L212
	pxor	%xmm0, %xmm0
	xorl	%edx, %edx
	movl	$1, %eax
	leaq	.LC27(%rip), %rdi
	call	printf@PLT
	pxor	%xmm0, %xmm0
.L213:
	movq	%rbx, %rdx
	movq	%r14, %rsi
	movl	$1, %eax
	leaq	.LC28(%rip), %rdi
	call	printf@PLT
	movq	112(%rsp), %r8
	movq	%r13, %rsi
	xorl	%eax, %eax
	movq	144(%rsp), %rdx
	leaq	.LC29(%rip), %rdi
	movq	%r12, %rcx
	call	printf@PLT
	movq	128(%rsp), %rsi
	xorl	%eax, %eax
	addq	160(%rsp), %rsi
	leaq	.LC30(%rip), %rdi
	call	printf@PLT
	movq	712(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L243
	addq	$728, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 56
	xorl	%eax, %eax
	popq	%rbx
	.cfi_def_cfa_offset 48
	popq	%rbp
	.cfi_def_cfa_offset 40
	popq	%r12
	.cfi_def_cfa_offset 32
	popq	%r13
	.cfi_def_cfa_offset 24
	popq	%r14
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	ret
.L241:
	.cfi_restore_state
	movl	%ecx, %edi
	movq	160(%rsp), %rcx
	movq	%r11, %rax
	movl	128(%rsp), %esi
	imulq	$336, %r11, %rdx
	addl	$1, 200(%rsp)
	movzbl	152(%rsp), %r8d
	imulq	$10752, %rcx, %r11
	movb	%dil, 191(%rsp)
	addq	%r11, %rdx
	movl	%r9d, 320(%r15,%rdx)
	movl	%r9d, 152(%r15,%rdx)
	movl	%r10d, 324(%r15,%rdx)
	movl	%r10d, 156(%r15,%rdx)
	movq	%rcx, %rdx
	salq	$5, %rdx
	leaq	(%r15,%rdx), %r9
	addq	%rax, %rdx
	movb	$1, 86016(%r9,%rax)
	leaq	sqb_item_at(%rip), %rax
	movl	%esi, (%rax,%rdx,4)
	movl	88(%rsp), %eax
	addl	$1, %eax
	movl	%eax, 86272(%r15,%rcx,4)
	jmp	.L188
.L202:
	xorl	%edi, %edi
	leaq	264(%rsp), %rdx
	xorl	%r12d, %r12d
	xorl	%r13d, %r13d
	movq	%rdi, 248(%rsp)
	xorl	%r15d, %r15d
	xorl	%r14d, %r14d
	xorl	%ebx, %ebx
	movq	%rdi, 256(%rsp)
	leaq	256(%rsp), %rsi
	xorl	%ebp, %ebp
	movq	%rdi, 264(%rsp)
	leaq	248(%rsp), %rdi
	call	sq2b_blind_pass.constprop.0
	xorl	%r8d, %r8d
	xorl	%r9d, %r9d
	xorl	%r10d, %r10d
	xorl	%r11d, %r11d
	movq	%r8, 88(%rsp)
	xorl	%ecx, %ecx
	movq	%r8, 168(%rsp)
	movq	%r8, 152(%rsp)
	movq	%r8, 160(%rsp)
	movq	%r8, 96(%rsp)
	movq	%r9, 32(%rsp)
	movq	%r9, 64(%rsp)
	movq	%r9, 144(%rsp)
	movq	%r9, 128(%rsp)
	movq	%r9, 112(%rsp)
	movq	%r10, (%rsp)
	movq	%r11, 16(%rsp)
.L207:
	pxor	%xmm0, %xmm0
	xorl	%edx, %edx
	movq	%rcx, %rsi
	movl	$1, %eax
	leaq	.LC18(%rip), %rdi
	call	printf@PLT
	xorl	%eax, %eax
	pxor	%xmm0, %xmm0
	movq	%rax, 48(%rsp)
	jmp	.L209
.L212:
	pxor	%xmm1, %xmm1
	pxor	%xmm0, %xmm0
	movq	%rbx, %rdx
	movl	$1, %eax
	cvtsi2sdq	%rbx, %xmm1
	cvtsi2sdq	%rsi, %xmm0
	divsd	%xmm1, %xmm0
	leaq	.LC27(%rip), %rdi
	movsd	%xmm1, (%rsp)
	call	printf@PLT
	pxor	%xmm0, %xmm0
	cvtsi2sdq	%r14, %xmm0
	divsd	(%rsp), %xmm0
	jmp	.L213
.L210:
	movq	32(%rsp), %rdx
	movq	64(%rsp), %rsi
	pxor	%xmm1, %xmm1
	pxor	%xmm0, %xmm0
	leaq	.LC20(%rip), %rdi
	movl	$1, %eax
	cvtsi2sdq	%rdx, %xmm1
	cvtsi2sdq	%rsi, %xmm0
	divsd	%xmm1, %xmm0
	movsd	%xmm1, 48(%rsp)
	call	printf@PLT
	pxor	%xmm0, %xmm0
	cvtsi2sdq	88(%rsp), %xmm0
	divsd	48(%rsp), %xmm0
	jmp	.L211
.L218:
	xorl	%edx, %edx
	xorl	%esi, %esi
	xorl	%r12d, %r12d
	xorl	%r13d, %r13d
	movq	%rdx, 144(%rsp)
	xorl	%r15d, %r15d
	xorl	%r14d, %r14d
	xorl	%ebx, %ebx
	movq	%rdx, 128(%rsp)
	xorl	%ebp, %ebp
	movq	%rdx, 112(%rsp)
	movq	%rsi, 16(%rsp)
	movq	%rsi, (%rsp)
	jmp	.L205
.L243:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE45:
	.size	main, .-main
	.local	action.0
	.comm	action.0,256,32
	.local	clean.1
	.comm	clean.1,86336,32
	.local	cell.2
	.comm	cell.2,86336,32
	.local	sqb_item_at
	.comm	sqb_item_at,1024,32
	.section	.rodata
	.align 32
	.type	SQB_SCATLT, @object
	.size	SQB_SCATLT, 128
SQB_SCATLT:
	.long	6
	.long	5
	.long	4
	.long	0
	.long	2
	.long	3
	.long	4
	.long	7
	.long	4
	.long	6
	.long	3
	.long	0
	.long	1
	.long	2
	.long	1
	.long	0
	.long	3
	.long	6
	.long	4
	.long	7
	.long	4
	.long	3
	.long	2
	.long	0
	.long	4
	.long	5
	.long	6
	.long	5
	.long	4
	.long	0
	.long	2
	.long	3
	.section	.rodata.cst16,"aM",@progbits,16
	.align 16
.LC0:
	.long	0
	.long	1
	.long	2
	.long	3
	.align 16
.LC3:
	.long	9
	.long	9
	.long	9
	.long	9
	.align 16
.LC4:
	.long	13
	.long	13
	.long	13
	.long	13
	.align 16
.LC5:
	.long	1
	.long	1
	.long	1
	.long	1
	.align 16
.LC6:
	.long	5
	.long	5
	.long	5
	.long	5
	.align 16
.LC7:
	.long	16
	.long	16
	.long	16
	.long	16
	.align 16
.LC8:
	.long	1431655765
	.long	1431655765
	.long	1431655765
	.long	1431655765
	.section	.rodata.cst8,"aM",@progbits,8
	.align 8
.LC9:
	.long	0
	.long	1017118720
	.align 8
.LC10:
	.long	858993459
	.long	1072378675
	.align 8
.LC11:
	.long	858993459
	.long	1071854387
	.align 8
.LC24:
	.long	0
	.long	1084178432
	.ident	"GCC: (GNU) 16.1.1 20260625"
	.section	.note.GNU-stack,"",@progbits

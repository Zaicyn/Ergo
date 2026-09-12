	.file	"sqm_cert.c"
	.text
	.p2align 4
	.type	sqm_write.constprop.0.isra.0, @function
sqm_write.constprop.0.isra.0:
.LFB7312:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movl	%esi, %r10d
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%r15
	pushq	%r14
	pushq	%r13
	pushq	%r12
	.cfi_offset 15, -24
	.cfi_offset 14, -32
	.cfi_offset 13, -40
	.cfi_offset 12, -48
	movl	%edi, %r12d
	pushq	%rbx
	andq	$-32, %rsp
	subq	$256, %rsp
	.cfi_offset 3, -56
	movq	%fs:40, %r11
	movq	%r11, 248(%rsp)
	movq	%rdx, %r11
	leaq	sqm_slot_of(%rip), %rdx
	movl	(%rdx,%r12,4), %ebx
	vmovdqu	(%r11), %xmm13
	vmovdqu	16(%r11), %xmm12
	vpsrldq	$4, %xmm13, %xmm9
	vpsrldq	$8, %xmm13, %xmm10
	vpmovzxbd	%xmm13, %xmm11
	vpmulld	.LC0(%rip), %xmm11, %xmm7
	vpsrldq	$12, %xmm13, %xmm8
	vpmovzxbd	%xmm10, %xmm10
	vpmovzxbd	%xmm9, %xmm9
	vpmulld	.LC1(%rip), %xmm9, %xmm5
	vpmovzxbd	%xmm8, %xmm8
	vpsrldq	$8, %xmm12, %xmm1
	vpaddd	%xmm11, %xmm9, %xmm9
	vpmulld	.LC3(%rip), %xmm8, %xmm4
	vpsrldq	$12, %xmm12, %xmm0
	vpmovzxbd	%xmm1, %xmm1
	vpaddd	%xmm10, %xmm8, %xmm8
	vpmulld	.LC2(%rip), %xmm10, %xmm6
	vpmovzxbd	%xmm0, %xmm0
	vpsrldq	$4, %xmm12, %xmm3
	vpmovzxbd	%xmm12, %xmm2
	vpmovzxbd	%xmm3, %xmm3
	vpaddd	%xmm0, %xmm9, %xmm9
	vpaddd	%xmm1, %xmm8, %xmm8
	vpmulld	.LC7(%rip), %xmm0, %xmm0
	vpaddd	%xmm3, %xmm9, %xmm9
	vpaddd	%xmm2, %xmm8, %xmm8
	vpmulld	.LC5(%rip), %xmm3, %xmm3
	vpmulld	.LC4(%rip), %xmm2, %xmm2
	vpmulld	.LC6(%rip), %xmm1, %xmm1
	vpaddd	%xmm8, %xmm9, %xmm11
	vpaddd	%xmm6, %xmm4, %xmm9
	vpaddd	%xmm7, %xmm5, %xmm8
	vpaddd	%xmm3, %xmm9, %xmm9
	vmovdqa	%xmm11, 32(%rsp)
	vpaddd	%xmm2, %xmm8, %xmm8
	vpaddd	%xmm0, %xmm9, %xmm9
	vpaddd	%xmm1, %xmm8, %xmm8
	vpaddd	%xmm8, %xmm9, %xmm14
	vpmulld	.LC0(%rip), %xmm7, %xmm9
	vpmulld	.LC1(%rip), %xmm5, %xmm8
	vpaddd	%xmm8, %xmm9, %xmm8
	vmovdqa	%xmm14, 48(%rsp)
	vpmulld	.LC6(%rip), %xmm1, %xmm9
	vpaddd	%xmm9, %xmm8, %xmm9
	vpmulld	.LC3(%rip), %xmm4, %xmm10
	vpmulld	.LC4(%rip), %xmm2, %xmm8
	vpaddd	%xmm8, %xmm9, %xmm9
	vpmulld	.LC2(%rip), %xmm6, %xmm8
	vpaddd	%xmm10, %xmm8, %xmm10
	vpmulld	.LC8(%rip), %xmm7, %xmm7
	vpmulld	.LC7(%rip), %xmm0, %xmm8
	vpaddd	%xmm8, %xmm10, %xmm8
	vpmulld	.LC9(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	.LC5(%rip), %xmm3, %xmm10
	vpaddd	%xmm10, %xmm8, %xmm8
	vpmulld	.LC12(%rip), %xmm6, %xmm6
	vpmulld	.LC10(%rip), %xmm1, %xmm1
	vpaddd	%xmm1, %xmm5, %xmm1
	vpmulld	.LC13(%rip), %xmm4, %xmm4
	vpaddd	%xmm4, %xmm6, %xmm4
	vpaddd	%xmm8, %xmm9, %xmm15
	vpmulld	.LC11(%rip), %xmm2, %xmm2
	vpaddd	%xmm2, %xmm1, %xmm2
	vpmulld	.LC14(%rip), %xmm0, %xmm0
	vmovdqu	32(%r11), %xmm1
	vpaddd	%xmm0, %xmm4, %xmm0
	vpmulld	.LC15(%rip), %xmm3, %xmm3
	vmovdqa	%xmm15, 64(%rsp)
	vpaddd	%xmm3, %xmm0, %xmm0
	vmovdqa	.LC16(%rip), %xmm15
	vmovdqa	.LC18(%rip), %xmm14
	vpaddd	%xmm0, %xmm2, %xmm7
	vpmovzxbd	%xmm1, %xmm8
	vmovdqu	48(%r11), %xmm0
	vmovdqa	%xmm7, 80(%rsp)
	vpmulld	%xmm15, %xmm8, %xmm7
	vpsrldq	$4, %xmm1, %xmm2
	vpsrldq	$8, %xmm1, %xmm6
	vpsrldq	$12, %xmm1, %xmm1
	vpmovzxbd	%xmm2, %xmm2
	vpmulld	.LC17(%rip), %xmm2, %xmm9
	vpmovzxbd	%xmm6, %xmm6
	vpmovzxbd	%xmm1, %xmm1
	vpmovzxbd	%xmm0, %xmm5
	vmovdqa	%xmm9, 96(%rsp)
	vpsrldq	$4, %xmm0, %xmm3
	vpsrldq	$8, %xmm0, %xmm4
	vpaddd	%xmm8, %xmm2, %xmm2
	vmovdqa	.LC20(%rip), %xmm8
	vpmovzxbd	%xmm3, %xmm3
	vpsrldq	$12, %xmm0, %xmm0
	vpmovzxbd	%xmm4, %xmm4
	vmovdqa	%xmm7, 112(%rsp)
	vpaddd	%xmm3, %xmm2, %xmm2
	vpmulld	.LC19(%rip), %xmm1, %xmm7
	vpaddd	%xmm6, %xmm1, %xmm1
	vpmovzxbd	%xmm0, %xmm0
	vpaddd	%xmm5, %xmm1, %xmm1
	vpmulld	.LC21(%rip), %xmm3, %xmm3
	vpmulld	112(%rsp), %xmm15, %xmm15
	vpmulld	%xmm14, %xmm6, %xmm10
	vpaddd	%xmm1, %xmm2, %xmm1
	vpaddd	%xmm0, %xmm4, %xmm2
	vpmulld	.LC22(%rip), %xmm4, %xmm4
	vpaddd	%xmm11, %xmm2, %xmm2
	vpmulld	%xmm8, %xmm5, %xmm5
	vpaddd	112(%rsp), %xmm9, %xmm6
	vpmulld	.LC17(%rip), %xmm9, %xmm9
	vpaddd	%xmm2, %xmm1, %xmm1
	vmovdqa	.LC23(%rip), %xmm2
	vpaddd	%xmm9, %xmm15, %xmm9
	vpaddd	%xmm4, %xmm6, %xmm6
	vpmulld	%xmm2, %xmm0, %xmm0
	vpmulld	%xmm14, %xmm10, %xmm14
	vpaddd	%xmm10, %xmm7, %xmm11
	vpmulld	%xmm8, %xmm5, %xmm8
	vpmulld	%xmm2, %xmm0, %xmm2
	vpaddd	%xmm0, %xmm11, %xmm11
	vpaddd	%xmm6, %xmm11, %xmm11
	vpaddd	%xmm3, %xmm5, %xmm6
	vpaddd	48(%rsp), %xmm6, %xmm6
	vpaddd	%xmm8, %xmm9, %xmm8
	vpmulld	.LC19(%rip), %xmm7, %xmm9
	vpmulld	.LC24(%rip), %xmm10, %xmm10
	vpmulld	.LC25(%rip), %xmm7, %xmm7
	vpaddd	%xmm9, %xmm14, %xmm9
	vpaddd	%xmm7, %xmm10, %xmm7
	vpmulld	.LC29(%rip), %xmm5, %xmm5
	vpmulld	.LC30(%rip), %xmm0, %xmm0
	vpaddd	%xmm6, %xmm11, %xmm6
	vpmulld	.LC21(%rip), %xmm3, %xmm11
	vpaddd	%xmm11, %xmm9, %xmm9
	vpaddd	%xmm9, %xmm8, %xmm9
	vmovdqa	112(%rsp), %xmm11
	vpmulld	.LC22(%rip), %xmm4, %xmm8
	vpaddd	%xmm8, %xmm2, %xmm2
	vpmulld	.LC26(%rip), %xmm3, %xmm3
	vpaddd	64(%rsp), %xmm2, %xmm2
	vpaddd	%xmm3, %xmm7, %xmm3
	vpmulld	.LC27(%rip), %xmm11, %xmm7
	vpmulld	.LC31(%rip), %xmm4, %xmm4
	vpaddd	%xmm4, %xmm0, %xmm0
	vpaddd	80(%rsp), %xmm0, %xmm0
	vpaddd	%xmm2, %xmm9, %xmm2
	vmovdqa	96(%rsp), %xmm9
	vpmulld	.LC28(%rip), %xmm9, %xmm8
	vpaddd	%xmm8, %xmm7, %xmm8
	vpaddd	%xmm5, %xmm8, %xmm8
	vpaddd	%xmm8, %xmm3, %xmm8
	vpunpckhqdq	%xmm1, %xmm1, %xmm3
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm8, %xmm0
	vpshufd	$177, %xmm1, %xmm3
	vpaddd	%xmm1, %xmm3, %xmm3
	vpunpckhqdq	%xmm6, %xmm6, %xmm1
	vpaddd	%xmm1, %xmm6, %xmm1
	vmovd	%xmm3, %esi
	vpshufd	$177, %xmm1, %xmm3
	movq	%rsi, 128(%rsp)
	vpaddd	%xmm1, %xmm3, %xmm3
	vpunpckhqdq	%xmm2, %xmm2, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm1
	vmovd	%xmm3, %ecx
	vpshufd	$177, %xmm1, %xmm2
	movq	%rcx, 136(%rsp)
	vpaddd	%xmm1, %xmm2, %xmm2
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm2, %edi
	vpshufd	$177, %xmm0, %xmm1
	movq	%rdi, 144(%rsp)
	vpaddd	%xmm0, %xmm1, %xmm1
	vmovd	%xmm1, %r8d
	movq	%r8, 152(%rsp)
	testl	%ebx, %ebx
	js	.L2
	movl	%ebx, %r10d
	movzbl	%bl, %ebx
	leaq	cell.5(%rip), %r9
	vmovdqa	128(%rsp), %ymm0
	sarl	$8, %r10d
	movq	%r10, %rdx
	salq	$5, %rdx
	addq	%rbx, %rdx
	leaq	512(%rdx), %rax
	salq	$5, %rax
	addq	%r9, %rax
	vpxor	(%rax), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L3
	addq	$1, 41256+cell.5(%rip)
	vzeroupper
.L1:
	movq	248(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L60
	leaq	-40(%rbp), %rsp
	popq	%rbx
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%r15
	popq	%rbp
	.cfi_remember_state
	.cfi_def_cfa 7, 8
	ret
	.p2align 4,,10
	.p2align 3
.L3:
	.cfi_restore_state
	vmovdqa	128(%rsp), %ymm0
	vpsubq	(%rax), %ymm0, %ymm0
	salq	$6, %rdx
	leaq	(%r9,%rdx), %rax
	movq	%rdx, %r12
	vmovq	%xmm0, %r14
	movq	%rax, 112(%rsp)
	testq	%r14, %r14
	je	.L8
	vpextrq	$1, %xmm0, %r13
	leaq	255(%r14), %rax
	vextracti128	$0x1, %ymm0, %xmm0
	vmovq	%xmm0, %r15
	vmovq	%xmm0, 96(%rsp)
	vpextrq	$1, %xmm0, 80(%rsp)
	cmpq	$510, %rax
	ja	.L9
	movq	%r13, %rax
	cqto
	idivq	%r14
	testq	%rdx, %rdx
	jne	.L9
	leaq	-1(%rax), %rdx
	cmpq	$63, %rdx
	ja	.L9
	movq	%rax, %rdx
	imulq	%rax, %rdx
	imulq	%r14, %rdx
	cmpq	%rdx, %r15
	jne	.L9
	movq	%r15, %rdx
	imulq	%rax, %rdx
	cmpq	%rdx, 80(%rsp)
	jne	.L9
	movq	112(%rsp), %rdx
	leal	-1(%rax), %r13d
	movq	%r13, %rax
	addq	%r13, %rdx
	movzbl	(%r11,%r13), %r13d
	movzbl	(%rdx), %r15d
	addq	$1, 41288+cell.5(%rip)
	addl	%r14d, %r15d
	cmpb	%r13b, %r15b
	jne	.L11
	addb	%r14b, (%rdx)
	movq	41296+cell.5(%rip), %rdi
	movl	%r14d, %ecx
	movl	$1, %r8d
	leaq	1(%rdi), %rdx
.L24:
	salq	$5, %r10
	movq	%rdx, 41296+cell.5(%rip)
	vmovdqa	128(%rsp), %ymm0
	leaq	(%r10,%rbx), %rdx
	movq	%rdx, %rsi
	addq	%rdx, %rdx
	salq	$5, %rsi
	vmovdqa	%ymm0, 16384(%rsi,%r9)
	movl	%eax, %esi
	sarl	$5, %eax
	andl	$31, %esi
	leaq	1(%rsi), %rdi
	leaq	768(%rax,%rdx), %rsi
	movslq	%ecx, %rax
	movq	%rdi, %r10
	movq	%rdi, %rcx
	vmovq	%rax, %xmm5
	salq	$5, %rsi
	imulq	%rax, %r10
	imulq	%r10, %rcx
	vpinsrq	$1, %r10, %xmm5, %xmm0
	imulq	%rcx, %rdi
	vmovq	%rcx, %xmm4
	vpinsrq	$1, %rdi, %xmm4, %xmm1
	vinserti128	$0x1, %xmm1, %ymm0, %ymm0
	vpaddq	(%r9,%rsi), %ymm0, %ymm0
	vmovdqa	%ymm0, (%r9,%rsi)
	cmpl	$2, %r8d
	jne	.L15
	movl	24(%rsp), %eax
	subl	$1, %eax
	movl	%eax, %ecx
	sarl	$5, %eax
	andl	$31, %ecx
	addq	%rdx, %rax
	leaq	1(%rcx), %rsi
	leaq	768(%rax), %rdx
	movslq	20(%rsp), %rcx
	salq	$5, %rax
	salq	$5, %rdx
	addq	%r9, %rax
	addq	%rcx, (%r9,%rdx)
	imulq	%rsi, %rcx
	addq	%rcx, 24584(%rax)
	movq	%rcx, %rdx
	imulq	%rsi, %rdx
	addq	%rdx, 24592(%rax)
	imulq	%rsi, %rdx
	addq	%rdx, 24600(%rax)
.L15:
	addq	$1, 41264+cell.5(%rip)
	vzeroupper
	jmp	.L1
	.p2align 4,,10
	.p2align 3
.L9:
	movq	96(%rsp), %rdx
	movq	%r13, %rax
	imulq	%r13, %rax
	imulq	%r14, %rdx
	movq	%rdx, %r15
	subq	%rax, %r15
	jne	.L61
.L8:
	vpsrldq	$4, %xmm13, %xmm2
	vpsrldq	$8, %xmm13, %xmm8
	vpmovzxbd	%xmm13, %xmm9
	vpmulld	.LC0(%rip), %xmm9, %xmm1
	vpsrldq	$12, %xmm13, %xmm0
	vpmovzxbd	%xmm8, %xmm8
	vpmovzxbd	%xmm2, %xmm2
	vpmulld	.LC1(%rip), %xmm2, %xmm7
	vpmovzxbd	%xmm0, %xmm0
	vpsrldq	$8, %xmm12, %xmm4
	vpaddd	%xmm9, %xmm2, %xmm2
	vpmulld	.LC3(%rip), %xmm0, %xmm3
	vpsrldq	$12, %xmm12, %xmm11
	vpsrldq	$4, %xmm12, %xmm5
	vpmovzxbd	%xmm4, %xmm4
	vpmulld	.LC2(%rip), %xmm8, %xmm10
	vpmovzxbd	%xmm11, %xmm11
	vpaddd	%xmm8, %xmm0, %xmm0
	vpmovzxbd	%xmm12, %xmm6
	vpmulld	.LC3(%rip), %xmm3, %xmm9
	vpmovzxbd	%xmm5, %xmm5
	vpaddd	%xmm11, %xmm2, %xmm2
	vpaddd	%xmm4, %xmm0, %xmm0
	vpmulld	.LC7(%rip), %xmm11, %xmm11
	vpaddd	%xmm5, %xmm2, %xmm2
	vpaddd	%xmm6, %xmm0, %xmm0
	vpmulld	.LC5(%rip), %xmm5, %xmm5
	vpmulld	.LC4(%rip), %xmm6, %xmm6
	vpaddd	%xmm0, %xmm2, %xmm0
	vpaddd	%xmm1, %xmm7, %xmm8
	vpmulld	.LC6(%rip), %xmm4, %xmm4
	vpmulld	.LC1(%rip), %xmm7, %xmm12
	vpaddd	%xmm10, %xmm3, %xmm2
	vpaddd	%xmm6, %xmm8, %xmm8
	vpmulld	.LC13(%rip), %xmm3, %xmm3
	vpmulld	.LC9(%rip), %xmm7, %xmm7
	vpaddd	%xmm5, %xmm2, %xmm2
	vpaddd	%xmm4, %xmm8, %xmm8
	vpaddd	%xmm11, %xmm2, %xmm2
	vpaddd	%xmm2, %xmm8, %xmm2
	vpmulld	.LC2(%rip), %xmm10, %xmm8
	vpaddd	%xmm9, %xmm8, %xmm9
	vpmulld	.LC7(%rip), %xmm11, %xmm8
	vpmulld	.LC12(%rip), %xmm10, %xmm10
	vpaddd	%xmm8, %xmm9, %xmm8
	vpaddd	%xmm3, %xmm10, %xmm3
	vpmulld	.LC5(%rip), %xmm5, %xmm9
	vpmulld	.LC14(%rip), %xmm11, %xmm11
	vpaddd	%xmm9, %xmm8, %xmm9
	vpmulld	.LC0(%rip), %xmm1, %xmm8
	vpmulld	.LC8(%rip), %xmm1, %xmm1
	vpaddd	%xmm7, %xmm1, %xmm1
	vpaddd	%xmm12, %xmm8, %xmm12
	vpmulld	.LC6(%rip), %xmm4, %xmm8
	vpmulld	.LC10(%rip), %xmm4, %xmm4
	vpaddd	%xmm11, %xmm3, %xmm3
	vpaddd	%xmm4, %xmm1, %xmm1
	vpmulld	.LC15(%rip), %xmm5, %xmm5
	vpaddd	%xmm8, %xmm12, %xmm8
	vpaddd	%xmm5, %xmm3, %xmm3
	vpmulld	.LC4(%rip), %xmm6, %xmm12
	vpmulld	.LC11(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm1, %xmm1
	vpaddd	%xmm12, %xmm8, %xmm8
	vpaddd	%xmm1, %xmm3, %xmm1
	vpunpckhqdq	%xmm0, %xmm0, %xmm3
	vpaddd	%xmm8, %xmm9, %xmm9
	vpaddd	%xmm3, %xmm0, %xmm0
	vpshufd	$177, %xmm0, %xmm3
	vpaddd	%xmm0, %xmm3, %xmm0
	vmovd	%xmm0, %r14d
	vpunpckhqdq	%xmm2, %xmm2, %xmm0
	vpaddd	%xmm0, %xmm2, %xmm2
	subq	%r14, %rsi
	movq	%r14, 160(%rsp)
	vpshufd	$177, %xmm2, %xmm0
	movq	%rsi, 192(%rsp)
	vpaddd	%xmm2, %xmm0, %xmm0
	vmovd	%xmm0, %r13d
	vpunpckhqdq	%xmm9, %xmm9, %xmm0
	vpaddd	%xmm0, %xmm9, %xmm9
	subq	%r13, %rcx
	movq	%r13, 168(%rsp)
	movq	%rsi, %r13
	vpshufd	$177, %xmm9, %xmm0
	salq	$5, %r13
	vpaddd	%xmm9, %xmm0, %xmm0
	vmovd	%xmm0, %edx
	vpunpckhqdq	%xmm1, %xmm1, %xmm0
	subq	%rdx, %rdi
	movq	%rdx, 176(%rsp)
	movq	%rcx, %rdx
	vpaddd	%xmm0, %xmm1, %xmm1
	subq	%r13, %rdx
	vpshufd	$177, %xmm1, %xmm0
	movq	%rcx, %r13
	salq	$10, %rcx
	movq	%rdx, 200(%rsp)
	movq	%rsi, %rdx
	vpaddd	%xmm1, %xmm0, %xmm0
	salq	$6, %r13
	salq	$10, %rdx
	vmovd	%xmm0, %eax
	salq	$15, %rsi
	addq	%rdi, %rdx
	salq	$5, %rdi
	subq	%rax, %r8
	movq	%rax, 184(%rsp)
	subq	%r13, %rdx
	subq	%rdi, %rcx
	subq	%rsi, %r8
	xorl	%edi, %edi
	movq	%rdx, 208(%rsp)
	leaq	(%rcx,%rcx,2), %rdx
	leaq	(%rdx,%r8), %rax
	movq	%rax, 216(%rsp)
	vmovdqa	160(%rsp), %ymm0
	vpxor	24576(%r9,%r12), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	vmovdqa	192(%rsp), %ymm0
	vpxor	24608(%r9,%r12), %ymm0, %ymm0
	setne	%dil
	vptest	%ymm0, %ymm0
	setne	%al
	cmpb	%dil, %al
	je	.L20
	addq	$32, 41288+cell.5(%rip)
	xorl	$1, %edi
	xorl	%eax, %eax
	xorl	%esi, %esi
	movq	112(%rsp), %rcx
	sall	$5, %edi
	addq	%rdi, %rcx
	addq	%r11, %rdi
	.p2align 5
	.p2align 4
	.p2align 3
.L22:
	movzbl	(%rdi,%rax), %edx
	cmpb	%dl, (%rcx,%rax)
	je	.L21
	movb	%dl, (%rcx,%rax)
	addl	$1, %esi
.L21:
	addq	$1, %rax
	cmpq	$32, %rax
	jne	.L22
	movslq	%esi, %rsi
	addq	$1, 41272+cell.5(%rip)
	addq	%rsi, 41296+cell.5(%rip)
.L23:
	vmovdqa	128(%rsp), %ymm0
	salq	$5, %r10
	leaq	(%r10,%rbx), %rax
	salq	$5, %rax
	vmovdqa	%ymm0, 16384(%rax,%r9)
	leaq	(%r10,%rbx), %rax
	vmovdqa	160(%rsp), %ymm0
	salq	$6, %rax
	vmovdqa	%ymm0, 24576(%rax,%r9)
	movq	%rax, %r10
	vmovdqa	192(%rsp), %ymm0
	leaq	24608+cell.5(%rip), %rax
	vmovdqa	%ymm0, (%rax,%r10)
	vzeroupper
	jmp	.L1
	.p2align 4,,10
	.p2align 3
.L2:
	vmovdqa	32(%rsp), %xmm5
	vmovdqa	48(%rsp), %xmm4
	movq	%r12, %rax
	vmovdqa	80(%rsp), %xmm7
	andl	$31, %eax
	vpunpckhqdq	%xmm5, %xmm5, %xmm0
	vpaddd	%xmm5, %xmm0, %xmm0
	vmovdqa	64(%rsp), %xmm5
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	vmovd	%xmm0, %r14d
	vpunpckhqdq	%xmm4, %xmm4, %xmm0
	vpaddd	%xmm4, %xmm0, %xmm0
	subq	%r14, %rsi
	movq	%r14, 160(%rsp)
	vpshufd	$177, %xmm0, %xmm1
	movq	%rsi, 192(%rsp)
	vpaddd	%xmm0, %xmm1, %xmm0
	vmovd	%xmm0, %r13d
	vpunpckhqdq	%xmm5, %xmm5, %xmm0
	vpaddd	%xmm5, %xmm0, %xmm0
	subq	%r13, %rcx
	movq	%r13, 168(%rsp)
	movq	%rsi, %r13
	vpshufd	$177, %xmm0, %xmm1
	salq	$5, %r13
	vpaddd	%xmm0, %xmm1, %xmm0
	vmovd	%xmm0, %ebx
	vpunpckhqdq	%xmm7, %xmm7, %xmm0
	subq	%rbx, %rdi
	movq	%rbx, 176(%rsp)
	movq	%rcx, %rbx
	vpaddd	%xmm7, %xmm0, %xmm0
	subq	%r13, %rbx
	vpshufd	$177, %xmm0, %xmm1
	movq	%rcx, %r13
	salq	$10, %rcx
	movq	%rbx, 200(%rsp)
	movq	%rsi, %rbx
	vpaddd	%xmm0, %xmm1, %xmm0
	salq	$15, %rsi
	salq	$10, %rbx
	vmovd	%xmm0, %r9d
	salq	$6, %r13
	addq	%rdi, %rbx
	salq	$5, %rdi
	subq	%r9, %r8
	movq	%r9, 184(%rsp)
	subq	%rdi, %rcx
	subq	%rsi, %r8
	leaq	cell.5(%rip), %r9
	subq	%r13, %rbx
	leaq	(%rcx,%rcx,2), %rcx
	movq	%rbx, 208(%rsp)
	addq	%r8, %rcx
	movq	%rcx, 216(%rsp)
	leaq	SQM_SCATLT(%rip), %rcx
	movl	(%rcx,%rax,4), %eax
	movq	%rax, %rcx
	cmpl	$31, 41216(%r9,%rax,4)
	jle	.L7
	leal	1(%rax), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%r9,%rax,4)
	jle	.L31
	leal	2(%rcx), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%r9,%rax,4)
	jle	.L31
	leal	3(%rcx), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%r9,%rax,4)
	jle	.L31
	leal	4(%rcx), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%r9,%rax,4)
	jle	.L31
	leal	5(%rcx), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%r9,%rax,4)
	jle	.L31
	leal	6(%rcx), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%r9,%rax,4)
	jle	.L31
	leal	7(%rcx), %eax
	movl	%eax, %ecx
	andl	$7, %eax
	andl	$7, %ecx
	cmpl	$31, 41216(%r9,%rax,4)
	jg	.L1
.L7:
	leaq	10304(%rax), %rdi
	salq	$5, %rax
	vmovdqu	(%r11), %ymm0
	sall	$8, %ecx
	movslq	(%r9,%rdi,4), %rbx
	leaq	(%rax,%rbx), %rsi
	addq	%r9, %rax
	orl	%ebx, %ecx
	movq	%rsi, %r13
	movl	%ecx, (%rdx,%r12,4)
	salq	$6, %r13
	vmovdqa	%ymm0, (%r9,%r13)
	vmovdqu	32(%r11), %ymm0
	movq	%rsi, %r11
	salq	$5, %r11
	vmovdqa	%ymm0, 32(%r9,%r13)
	vmovdqa	128(%rsp), %ymm0
	movb	$1, 40960(%rbx,%rax)
	leaq	sqm_item_at(%rip), %rax
	vmovdqa	%ymm0, 16384(%r11,%r9)
	leaq	24608+cell.5(%rip), %r11
	vmovdqa	160(%rsp), %ymm0
	addl	$1, (%r9,%rdi,4)
	addl	$1, 41248+cell.5(%rip)
	addq	$1, 41280+cell.5(%rip)
	addq	$64, 41296+cell.5(%rip)
	vmovdqa	%ymm0, 24576(%r9,%r13)
	vmovdqa	192(%rsp), %ymm0
	movl	%r10d, (%rax,%rsi,4)
	vmovdqa	%ymm0, (%r11,%r13)
	vzeroupper
	jmp	.L1
	.p2align 4,,10
	.p2align 3
.L61:
	movq	80(%rsp), %rax
	movq	96(%rsp), %rdx
	movq	%r15, 64(%rsp)
	imulq	%r13, %rdx
	imulq	%r14, %rax
	subq	%rdx, %rax
	cqto
	idivq	%r15
	movq	%rax, 48(%rsp)
	testq	%rdx, %rdx
	jne	.L8
	movq	96(%rsp), %r15
	movq	80(%rsp), %rax
	movq	%r15, %rdx
	imulq	%r13, %rax
	imulq	%r15, %rdx
	subq	%rdx, %rax
	cqto
	idivq	64(%rsp)
	testq	%rdx, %rdx
	jne	.L8
	movq	48(%rsp), %r15
	negq	%rax
	movq	%r15, %rdx
	imulq	%r15, %rdx
	leaq	(%rdx,%rax,4), %rdx
	testq	%rdx, %rdx
	jle	.L8
	movl	$1, %eax
	cmpq	$1, %rdx
	je	.L12
	movq	112(%rsp), %r15
	movq	%rsi, 64(%rsp)
	movq	%rdx, %rsi
	.p2align 4
	.p2align 4
	.p2align 3
.L13:
	addq	$1, %rax
	movq	%rax, %rdx
	imulq	%rax, %rdx
	cmpq	%rdx, %rsi
	jg	.L13
	movq	%r15, 112(%rsp)
	movq	64(%rsp), %rsi
	jne	.L8
.L12:
	movq	48(%rsp), %r15
	leaq	(%rax,%r15), %rdx
	testb	$1, %dl
	jne	.L8
	subq	%rax, %r15
	leaq	-2(%rdx), %rax
	cmpq	$127, %rax
	ja	.L8
	leaq	-2(%r15), %rax
	cmpq	$127, %rax
	ja	.L8
	movq	%rdx, %rax
	sarq	%r15
	sarq	%rax
	movq	%r15, 24(%rsp)
	movq	%rax, 48(%rsp)
	cmpq	%r15, %rax
	je	.L8
	movq	%r15, %rdx
	movq	%r13, %rax
	movq	48(%rsp), %r13
	imulq	%r14, %rdx
	subq	%r15, %r13
	subq	%rdx, %rax
	cqto
	idivq	%r13
	testq	%rdx, %rdx
	jne	.L8
	movq	%rax, %rdx
	addq	$255, %rax
	cmpq	$510, %rax
	ja	.L8
	subq	%rdx, %r14
	leaq	255(%r14), %rax
	movq	%r14, 32(%rsp)
	cmpq	$510, %rax
	ja	.L8
	movq	%rdx, 64(%rsp)
	testq	%rdx, %rdx
	je	.L8
	testq	%r14, %r14
	je	.L8
	movq	48(%rsp), %r13
	movq	%r13, %rdx
	imulq	%r13, %rdx
	movq	%rdx, %rax
	movq	64(%rsp), %rdx
	imulq	%rax, %rdx
	movq	%r15, %rax
	imulq	%r15, %rax
	imulq	%rax, %r14
	leaq	(%rdx,%r14), %rax
	cmpq	%rax, 96(%rsp)
	jne	.L8
	movq	%r15, %rax
	imulq	48(%rsp), %rdx
	imulq	%r14, %rax
	addq	%rdx, %rax
	cmpq	%rax, 80(%rsp)
	jne	.L8
	movl	48(%rsp), %eax
	movq	112(%rsp), %r15
	movq	41288+cell.5(%rip), %r13
	leal	-1(%rax), %edx
	leaq	(%r15,%rdx), %r14
	movq	%rdx, %rax
	movzbl	(%r11,%rdx), %edx
	movq	%r13, 96(%rsp)
	movzbl	64(%rsp), %r15d
	addq	$1, %r13
	addb	(%r14), %r15b
	movq	%r13, 41288+cell.5(%rip)
	cmpb	%dl, %r15b
	jne	.L11
	movq	24(%rsp), %r15
	movzbl	32(%rsp), %edx
	leal	-1(%r15), %r13d
	movl	%r15d, 24(%rsp)
	movq	112(%rsp), %r15
	addq	%r13, %r15
	movzbl	(%r11,%r13), %r13d
	addb	(%r15), %dl
	movq	%r15, 80(%rsp)
	movl	%edx, %r15d
	movq	96(%rsp), %rdx
	addq	$2, %rdx
	movq	%rdx, 41288+cell.5(%rip)
	cmpb	%r13b, %r15b
	je	.L62
.L11:
	addq	$1, 41304+cell.5(%rip)
	vmovdqu	(%r11), %xmm13
	vmovdqu	16(%r11), %xmm12
	jmp	.L8
.L31:
	andl	$7, %esi
	movl	%esi, %ecx
	jmp	.L7
.L20:
	vmovdqu	(%r11), %ymm0
	movq	112(%rsp), %rax
	vmovdqa	%ymm0, (%rax)
	vmovdqu	32(%r11), %ymm0
	vmovdqa	%ymm0, 32(%rax)
	vmovdqa	.LC32(%rip), %xmm0
	vpaddq	41280+cell.5(%rip), %xmm0, %xmm0
	addq	$64, 41296+cell.5(%rip)
	vmovdqa	%xmm0, 41280+cell.5(%rip)
	jmp	.L23
.L62:
	movq	64(%rsp), %rsi
	movq	32(%rsp), %rdi
	movl	$2, %r8d
	addb	%sil, (%r14)
	movl	%esi, %ecx
	movq	80(%rsp), %rsi
	movl	%edi, 20(%rsp)
	addq	$1, 41296+cell.5(%rip)
	addb	%dil, (%rsi)
	movq	41296+cell.5(%rip), %rdi
	leaq	1(%rdi), %rdx
	jmp	.L24
.L60:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE7312:
	.size	sqm_write.constprop.0.isra.0, .-sqm_write.constprop.0.isra.0
	.section	.rodata.str1.1,"aMS",@progbits,1
.LC33:
	.string	"clock_gettime failed\n"
	.text
	.p2align 4
	.type	cmp_now_sec, @function
cmp_now_sec:
.LFB0:
	.cfi_startproc
	subq	$40, %rsp
	.cfi_def_cfa_offset 48
	movl	$1, %edi
	movq	%fs:40, %rsi
	movq	%rsi, 24(%rsp)
	movq	%rsp, %rsi
	call	clock_gettime@PLT
	testl	%eax, %eax
	jne	.L67
	vxorps	%xmm1, %xmm1, %xmm1
	vcvtsi2sdq	8(%rsp), %xmm1, %xmm0
	vcvtsi2sdq	(%rsp), %xmm1, %xmm1
	vfmadd132sd	.LC34(%rip), %xmm1, %xmm0
	movq	24(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L68
	addq	$40, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
.L67:
	.cfi_restore_state
	movq	stderr(%rip), %rcx
	movl	$21, %edx
	movl	$1, %esi
	leaq	.LC33(%rip), %rdi
	call	fwrite@PLT
	movl	$1, %edi
	call	exit@PLT
.L68:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE0:
	.size	cmp_now_sec, .-cmp_now_sec
	.p2align 4
	.type	cmp_xoshiro256ss, @function
cmp_xoshiro256ss:
.LFB1:
	.cfi_startproc
	movq	(%rdi), %rax
	movq	8(%rdi), %rdx
	movq	16(%rdi), %r8
	movq	24(%rdi), %rsi
	movq	%rdx, %r9
	xorq	%rax, %r8
	movq	%rsi, %rcx
	xorq	%r8, %r9
	xorq	%rdx, %rcx
	salq	$17, %rdx
	movq	%r9, 8(%rdi)
	movq	%rax, %r9
	xorq	%r8, %rdx
	addq	%rsi, %rax
	xorq	%rcx, %r9
	movq	%rdx, 16(%rdi)
	rorx	$19, %rcx, %rcx
	rorx	$47, %rax, %rax
	movq	%r9, (%rdi)
	movq	%rcx, 24(%rdi)
	ret
	.cfi_endproc
.LFE1:
	.size	cmp_xoshiro256ss, .-cmp_xoshiro256ss
	.p2align 4
	.type	cmp_rand_u32, @function
cmp_rand_u32:
.LFB2:
	.cfi_startproc
	movq	(%rdi), %rax
	movq	8(%rdi), %rdx
	movq	16(%rdi), %r8
	movq	24(%rdi), %rsi
	movq	%rdx, %r9
	xorq	%rax, %r8
	movq	%rsi, %rcx
	xorq	%r8, %r9
	xorq	%rdx, %rcx
	salq	$17, %rdx
	movq	%r9, 8(%rdi)
	movq	%rax, %r9
	xorq	%r8, %rdx
	addq	%rsi, %rax
	xorq	%rcx, %r9
	movq	%rdx, 16(%rdi)
	rorx	$19, %rcx, %rcx
	rorx	$47, %rax, %rax
	movq	%r9, (%rdi)
	movq	%rcx, 24(%rdi)
	ret
	.cfi_endproc
.LFE2:
	.size	cmp_rand_u32, .-cmp_rand_u32
	.p2align 4
	.type	cmp_rand01, @function
cmp_rand01:
.LFB3:
	.cfi_startproc
	movq	(%rdi), %rax
	movq	8(%rdi), %rdx
	vxorps	%xmm0, %xmm0, %xmm0
	movq	16(%rdi), %r8
	movq	24(%rdi), %rsi
	movq	%rdx, %r9
	xorq	%rax, %r8
	movq	%rsi, %rcx
	xorq	%r8, %r9
	xorq	%rdx, %rcx
	salq	$17, %rdx
	movq	%r9, 8(%rdi)
	movq	%rax, %r9
	addq	%rsi, %rax
	xorq	%r8, %rdx
	xorq	%rcx, %r9
	rorx	$47, %rax, %rax
	shrq	$11, %rax
	rorx	$19, %rcx, %rcx
	vcvtsi2sdq	%rax, %xmm0, %xmm0
	movq	%r9, (%rdi)
	vmulsd	.LC35(%rip), %xmm0, %xmm0
	movq	%rdx, 16(%rdi)
	movq	%rcx, 24(%rdi)
	ret
	.cfi_endproc
.LFE3:
	.size	cmp_rand01, .-cmp_rand01
	.p2align 4
	.type	cmp_seed, @function
cmp_seed:
.LFB4:
	.cfi_startproc
	movabsq	$-7723592293110705685, %rdx
	movabsq	$-7046029254386353131, %rax
	movabsq	$-4658895280553007687, %rcx
	addq	%rsi, %rax
	xorq	%rsi, %rcx
	addq	%rdx, %rsi
	movabsq	$5756289220251749470, %rdx
	xorq	%rax, %rsi
	movq	%rcx, %r9
	salq	$17, %rcx
	xorq	%rax, %rdx
	movabsq	$-9111967335571159376, %rax
	xorq	%rsi, %rcx
	xorq	%rsi, %r9
	xorq	%rdx, %rcx
	xorq	%r9, %rax
	movq	%rcx, %r8
	xorq	%rax, %rdx
	rorx	$19, %rax, %rax
	xorq	%r9, %r8
	salq	$17, %r9
	xorq	%rcx, %r9
	xorq	%r8, %rax
	movq	%r8, %rsi
	salq	$17, %r8
	xorq	%rdx, %r9
	xorq	%rax, %rdx
	rorx	$19, %rax, %rax
	xorq	%r9, %rsi
	xorq	%r9, %r8
	xorq	%rdx, %r8
	xorq	%rsi, %rax
	movq	%rsi, %rcx
	salq	$17, %rsi
	xorq	%r8, %rcx
	movq	%rsi, %r9
	xorq	%rax, %rdx
	rorx	$19, %rax, %rax
	xorq	%r8, %r9
	xorq	%rcx, %rax
	movq	%rcx, %rsi
	salq	$17, %rcx
	xorq	%rdx, %r9
	movq	%rcx, %r8
	xorq	%rax, %rdx
	rorx	$19, %rax, %rax
	xorq	%r9, %rsi
	xorq	%r9, %r8
	xorq	%rdx, %r8
	movq	%rsi, %rcx
	xorq	%rsi, %rax
	salq	$17, %rsi
	xorq	%r8, %rcx
	movq	%rsi, %r9
	xorq	%rax, %rdx
	rorx	$19, %rax, %rax
	xorq	%r8, %r9
	xorq	%rcx, %rax
	movq	%rcx, %rsi
	salq	$17, %rcx
	xorq	%rdx, %r9
	movq	%rcx, %r8
	xorq	%rax, %rdx
	rorx	$19, %rax, %rax
	xorq	%r9, %rsi
	xorq	%r9, %r8
	xorq	%rdx, %r8
	xorq	%rsi, %rax
	movq	%rsi, %rcx
	salq	$17, %rsi
	xorq	%r8, %rcx
	xorq	%rax, %rdx
	xorq	%r8, %rsi
	rorx	$19, %rax, %rax
	xorq	%rdx, %rsi
	xorq	%rcx, %rax
	movq	%rcx, %r8
	salq	$17, %rcx
	xorq	%rax, %rdx
	xorq	%rsi, %rcx
	xorq	%rsi, %r8
	rorx	$19, %rax, %rax
	xorq	%rdx, %rcx
	xorq	%r8, %rax
	movq	%rcx, %rsi
	xorq	%rax, %rdx
	rorx	$19, %rax, %rax
	movq	%rax, 24(%rdi)
	xorq	%r8, %rsi
	salq	$17, %r8
	movq	%rdx, (%rdi)
	xorq	%rcx, %r8
	movq	%rsi, 8(%rdi)
	movq	%r8, 16(%rdi)
	ret
	.cfi_endproc
.LFE4:
	.size	cmp_seed, .-cmp_seed
	.p2align 4
	.type	cmp_pick_unique, @function
cmp_pick_unique:
.LFB5:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%r14
	pushq	%r13
	.cfi_offset 14, -24
	.cfi_offset 13, -32
	movq	%rsi, %r13
	pushq	%r12
	.cfi_offset 12, -40
	movq	%rdx, %r12
	pushq	%rbx
	.cfi_offset 3, -48
	movq	%rdi, %rbx
	salq	$3, %rdi
	andq	$-32, %rsp
	call	malloc@PLT
	movq	%rax, %r9
	testq	%rax, %rax
	je	.L73
	cmpq	%rbx, %r13
	movq	%r13, %r10
	cmovg	%rbx, %r10
	testq	%rbx, %rbx
	jle	.L75
	leaq	-1(%rbx), %rax
	cmpq	$2, %rax
	jbe	.L80
	movq	%rbx, %rcx
	vmovdqa	.LC36(%rip), %ymm0
	movq	%r9, %rax
	vpbroadcastq	.LC38(%rip), %ymm1
	shrq	$2, %rcx
	movq	%rcx, %rdx
	salq	$5, %rdx
	addq	%r9, %rdx
	.p2align 5
	.p2align 4
	.p2align 3
.L77:
	vmovdqu	%ymm0, (%rax)
	addq	$32, %rax
	vpaddq	%ymm1, %ymm0, %ymm0
	cmpq	%rax, %rdx
	jne	.L77
	leaq	0(,%rcx,4), %rax
	cmpq	%rax, %rbx
	je	.L86
	vzeroupper
.L76:
	leaq	1(%rax), %rdx
	movq	%rax, (%r9,%rax,8)
	cmpq	%rdx, %rbx
	jle	.L75
	movq	%rdx, 8(%r9,%rax,8)
	leaq	2(%rax), %rdx
	cmpq	%rdx, %rbx
	jle	.L75
	movq	%rdx, 16(%r9,%rax,8)
.L75:
	testq	%r10, %r10
	jle	.L73
	movq	(%r12), %rdi
	movq	24(%r12), %rcx
	vxorps	%xmm2, %xmm2, %xmm2
	xorl	%eax, %eax
	movq	8(%r12), %r8
	movq	16(%r12), %rsi
	leaq	-1(%rbx), %r11
	vmovsd	.LC35(%rip), %xmm3
	.p2align 4
	.p2align 3
.L79:
	leaq	(%rcx,%rdi), %rdx
	movq	%r8, %r13
	xorq	%rdi, %rsi
	xorq	%r8, %rcx
	rorx	$47, %rdx, %rdx
	shrq	$11, %rdx
	salq	$17, %r13
	xorq	%rsi, %r8
	vcvtsi2sdq	%rdx, %xmm2, %xmm0
	vmulsd	%xmm3, %xmm0, %xmm0
	movq	%rbx, %rdx
	xorq	%rcx, %rdi
	subq	%rax, %rdx
	xorq	%r13, %rsi
	movq	(%r9,%rax,8), %r13
	rorx	$19, %rcx, %rcx
	vcvtsi2sdq	%rdx, %xmm2, %xmm1
	vmulsd	%xmm1, %xmm0, %xmm0
	vcvttsd2siq	%xmm0, %rdx
	addq	%rax, %rdx
	cmpq	%rdx, %rbx
	cmovle	%r11, %rdx
	movq	(%r9,%rdx,8), %r14
	movq	%r14, (%r9,%rax,8)
	addq	$1, %rax
	movq	%r13, (%r9,%rdx,8)
	cmpq	%rax, %r10
	jne	.L79
	movq	%r14, -8(%r9,%r10,8)
	movq	%r8, 8(%r12)
	movq	%rdi, (%r12)
	movq	%rsi, 16(%r12)
	movq	%rcx, 24(%r12)
	movq	%r13, (%r9,%rdx,8)
.L73:
	leaq	-32(%rbp), %rsp
	movq	%r9, %rax
	popq	%rbx
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%rbp
	.cfi_remember_state
	.cfi_def_cfa 7, 8
	ret
	.p2align 4,,10
	.p2align 3
.L86:
	.cfi_restore_state
	vzeroupper
	jmp	.L75
.L80:
	xorl	%eax, %eax
	jmp	.L76
	.cfi_endproc
.LFE5:
	.size	cmp_pick_unique, .-cmp_pick_unique
	.section	.rodata.str1.1
.LC40:
	.string	"%-12s  not built / not run\n"
	.section	.rodata.str1.8,"aMS",@progbits,1
	.align 8
.LC42:
	.string	"%-12s  items=%10lld  alloc=%8.3f M/s  %8.2f ns/item  det=%6.2f%%  rep=%6.2f%%  coh_fail=%6.4f%% (%lld/%lld)\n"
	.section	.rodata.str1.1
.LC43:
	.string	""
	.section	.rodata.str1.8
	.align 8
.LC44:
	.string	"%-12s  WARNING: %lld allocation attempts silently rejected (throughput includes fast-fail no-ops)\n"
	.align 8
.LC45:
	.string	"%-12s  cache: L1_hit=%5.2f%%  LLC_hit=%5.2f%%  L1_miss/item=%.4f  LLC_miss/item=%.4f  instr/item=%.1f\n"
	.text
	.p2align 4
	.type	cmp_print_result, @function
cmp_print_result:
.LFB6:
	.cfi_startproc
	movl	112(%rdi), %edx
	testl	%edx, %edx
	je	.L124
	pushq	%rbx
	.cfi_def_cfa_offset 16
	.cfi_offset 3, -16
	movq	64(%rdi), %rdx
	vxorps	%xmm5, %xmm5, %xmm5
	vxorpd	%xmm2, %xmm2, %xmm2
	movq	72(%rdi), %rax
	testq	%rdx, %rdx
	je	.L90
	vcvtsi2sdq	%rax, %xmm5, %xmm2
	vmulsd	.LC41(%rip), %xmm2, %xmm2
	vcvtsi2sdq	%rdx, %xmm5, %xmm0
	vdivsd	%xmm0, %xmm2, %xmm2
.L90:
	vxorpd	%xmm3, %xmm3, %xmm3
	testq	%rax, %rax
	je	.L91
	vcvtsi2sdq	80(%rdi), %xmm5, %xmm3
	vmulsd	.LC41(%rip), %xmm3, %xmm3
	vcvtsi2sdq	%rax, %xmm5, %xmm0
	vdivsd	%xmm0, %xmm3, %xmm3
.L91:
	movq	96(%rdi), %r8
	movq	88(%rdi), %rcx
	vxorpd	%xmm4, %xmm4, %xmm4
	testq	%r8, %r8
	je	.L92
	vcvtsi2sdq	%rcx, %xmm5, %xmm4
	vmulsd	.LC41(%rip), %xmm4, %xmm4
	vcvtsi2sdq	%r8, %xmm5, %xmm0
	vdivsd	%xmm0, %xmm4, %xmm4
.L92:
	movq	32(%rdi), %rdx
	vmovsd	48(%rdi), %xmm0
	movq	%rdi, %rbx
	movq	%rdi, %rsi
	vmovsd	56(%rdi), %xmm1
	movl	$5, %eax
	leaq	.LC42(%rip), %rdi
	call	printf@PLT
	movq	104(%rbx), %rdx
	vxorps	%xmm5, %xmm5, %xmm5
	testq	%rdx, %rdx
	jg	.L125
	movl	116(%rbx), %eax
	testl	%eax, %eax
	je	.L121
.L126:
	movq	120(%rbx), %rdx
	movq	128(%rbx), %rax
	vxorpd	%xmm0, %xmm0, %xmm0
	cmpq	%rdx, %rax
	jnb	.L95
	movq	%rdx, %rcx
	subq	%rax, %rcx
	js	.L96
	vcvtsi2sdq	%rcx, %xmm5, %xmm0
.L97:
	vmulsd	.LC41(%rip), %xmm0, %xmm0
	testq	%rdx, %rdx
	js	.L98
	vcvtsi2sdq	%rdx, %xmm5, %xmm1
.L99:
	vdivsd	%xmm1, %xmm0, %xmm0
.L95:
	movq	136(%rbx), %rcx
	movq	144(%rbx), %rdx
	vxorpd	%xmm1, %xmm1, %xmm1
	cmpq	%rcx, %rdx
	jnb	.L100
	movq	%rcx, %rsi
	subq	%rdx, %rsi
	js	.L101
	vcvtsi2sdq	%rsi, %xmm5, %xmm1
.L102:
	vmulsd	.LC41(%rip), %xmm1, %xmm1
	testq	%rcx, %rcx
	js	.L103
	vcvtsi2sdq	%rcx, %xmm5, %xmm2
.L104:
	vdivsd	%xmm2, %xmm1, %xmm1
.L100:
	movq	32(%rbx), %rcx
	testq	%rcx, %rcx
	je	.L117
	vcvtsi2sdq	%rcx, %xmm5, %xmm6
	movq	152(%rbx), %rcx
	testq	%rcx, %rcx
	js	.L106
	vcvtsi2sdq	%rcx, %xmm5, %xmm4
.L107:
	vdivsd	%xmm6, %xmm4, %xmm4
	testq	%rdx, %rdx
	js	.L108
	vcvtsi2sdq	%rdx, %xmm5, %xmm3
.L109:
	vdivsd	%xmm6, %xmm3, %xmm3
	testq	%rax, %rax
	js	.L110
	vcvtsi2sdq	%rax, %xmm5, %xmm2
.L111:
	vdivsd	%xmm6, %xmm2, %xmm2
	jmp	.L105
	.p2align 4,,10
	.p2align 3
.L121:
	popq	%rbx
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L125:
	.cfi_restore_state
	leaq	.LC43(%rip), %rsi
	leaq	.LC44(%rip), %rdi
	xorl	%eax, %eax
	call	printf@PLT
	movl	116(%rbx), %eax
	vxorps	%xmm5, %xmm5, %xmm5
	testl	%eax, %eax
	je	.L121
	jmp	.L126
	.p2align 4,,10
	.p2align 3
.L124:
	.cfi_def_cfa_offset 8
	.cfi_restore 3
	movq	%rdi, %rsi
	xorl	%eax, %eax
	leaq	.LC40(%rip), %rdi
	jmp	printf@PLT
	.p2align 4,,10
	.p2align 3
.L117:
	.cfi_def_cfa_offset 16
	.cfi_offset 3, -16
	vxorpd	%xmm3, %xmm3, %xmm3
	vmovapd	%xmm3, %xmm4
	vmovapd	%xmm3, %xmm2
.L105:
	movq	%rbx, %rsi
	leaq	.LC45(%rip), %rdi
	movl	$5, %eax
	popq	%rbx
	.cfi_remember_state
	.cfi_restore 3
	.cfi_def_cfa_offset 8
	jmp	printf@PLT
	.p2align 4,,10
	.p2align 3
.L110:
	.cfi_restore_state
	movq	%rax, %rdx
	andl	$1, %eax
	shrq	%rdx
	orq	%rax, %rdx
	vcvtsi2sdq	%rdx, %xmm5, %xmm2
	vaddsd	%xmm2, %xmm2, %xmm2
	jmp	.L111
	.p2align 4,,10
	.p2align 3
.L98:
	movq	%rdx, %rcx
	andl	$1, %edx
	shrq	%rcx
	orq	%rdx, %rcx
	vcvtsi2sdq	%rcx, %xmm5, %xmm1
	vaddsd	%xmm1, %xmm1, %xmm1
	jmp	.L99
	.p2align 4,,10
	.p2align 3
.L96:
	movq	%rcx, %rsi
	andl	$1, %ecx
	shrq	%rsi
	orq	%rcx, %rsi
	vcvtsi2sdq	%rsi, %xmm5, %xmm0
	vaddsd	%xmm0, %xmm0, %xmm0
	jmp	.L97
	.p2align 4,,10
	.p2align 3
.L108:
	movq	%rdx, %rcx
	andl	$1, %edx
	shrq	%rcx
	orq	%rdx, %rcx
	vcvtsi2sdq	%rcx, %xmm5, %xmm3
	vaddsd	%xmm3, %xmm3, %xmm3
	jmp	.L109
	.p2align 4,,10
	.p2align 3
.L106:
	movq	%rcx, %rsi
	andl	$1, %ecx
	shrq	%rsi
	orq	%rcx, %rsi
	vcvtsi2sdq	%rsi, %xmm5, %xmm4
	vaddsd	%xmm4, %xmm4, %xmm4
	jmp	.L107
	.p2align 4,,10
	.p2align 3
.L103:
	movq	%rcx, %rsi
	andl	$1, %ecx
	shrq	%rsi
	orq	%rcx, %rsi
	vcvtsi2sdq	%rsi, %xmm5, %xmm2
	vaddsd	%xmm2, %xmm2, %xmm2
	jmp	.L104
	.p2align 4,,10
	.p2align 3
.L101:
	movq	%rsi, %rdi
	andl	$1, %esi
	shrq	%rdi
	orq	%rsi, %rdi
	vcvtsi2sdq	%rdi, %xmm5, %xmm1
	vaddsd	%xmm1, %xmm1, %xmm1
	jmp	.L102
	.cfi_endproc
.LFE6:
	.size	cmp_print_result, .-cmp_print_result
	.p2align 4
	.type	esf_v2_init_tables, @function
esf_v2_init_tables:
.LFB7:
	.cfi_startproc
	movl	esf_v2_tables_ready(%rip), %eax
	testl	%eax, %eax
	jne	.L131
	movl	$13, %edx
	xorl	%eax, %eax
	vmovdqa	.LC46(%rip), %ymm1
	leaq	esf_idx_table(%rip), %rsi
	vmovd	%edx, %xmm3
	movl	$8, %edx
	leaq	esf_idx2_table(%rip), %rcx
	vmovd	%edx, %xmm2
	vpbroadcastd	%xmm3, %ymm3
	vpbroadcastd	%xmm2, %ymm2
	.p2align 6
	.p2align 4
	.p2align 3
.L129:
	vpaddd	%ymm3, %ymm1, %ymm0
	vpaddd	%ymm2, %ymm1, %ymm1
	vmovdqa	%ymm0, (%rsi,%rax)
	vpmulld	%ymm0, %ymm0, %ymm0
	vmovdqa	%ymm0, (%rcx,%rax)
	addq	$32, %rax
	cmpq	$16256, %rax
	jne	.L129
	vmovdqa	.LC49(%rip), %xmm0
	movl	$1, esf_v2_tables_ready(%rip)
	vmovdqa	%xmm0, 16256+esf_idx_table(%rip)
	vmovdqa	.LC50(%rip), %xmm0
	vmovdqa	%xmm0, 16256+esf_idx2_table(%rip)
	vzeroupper
.L131:
	ret
	.cfi_endproc
.LFE7:
	.size	esf_v2_init_tables, .-esf_v2_init_tables
	.p2align 4
	.type	esf_scalar_syndromes, @function
esf_scalar_syndromes:
.LFB8:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	vmovq	.LC51(%rip), %xmm10
	movq	%rsi, %r8
	movq	%rdx, %r9
	vmovq	.LC52(%rip), %xmm9
	vmovq	.LC53(%rip), %xmm8
	movq	%rcx, %r10
	vpxor	%xmm3, %xmm3, %xmm3
	vmovq	.LC54(%rip), %xmm7
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%r15
	pushq	%r14
	pushq	%r13
	pushq	%r12
	pushq	%rbx
	.cfi_offset 15, -24
	.cfi_offset 14, -32
	.cfi_offset 13, -40
	.cfi_offset 12, -48
	.cfi_offset 3, -56
	vmovq	4(%rdi), %xmm0
	movzbl	14(%rdi), %eax
	movzbl	13(%rdi), %edx
	vpmovzxbw	%xmm0, %xmm2
	vpsrlq	$32, %xmm0, %xmm0
	movzbl	12(%rdi), %esi
	movzbl	15(%rdi), %ecx
	vpmovzxbw	%xmm0, %xmm0
	vpmovzxwd	%xmm2, %xmm1
	leal	(%rdx,%rdx,4), %r13d
	vpmovzxwd	%xmm0, %xmm4
	vpsrlq	$32, %xmm2, %xmm2
	leal	(%rsi,%rdx), %r14d
	vpsrlq	$32, %xmm0, %xmm0
	vpmovzxwd	%xmm2, %xmm2
	leal	(%rsi,%rsi,8), %esi
	addl	%eax, %r14d
	vpmovzxwd	%xmm0, %xmm0
	vpaddd	%xmm2, %xmm1, %xmm5
	leal	(%rax,%rax,4), %r15d
	addl	%ecx, %r14d
	vpaddd	%xmm0, %xmm4, %xmm6
	vpmulld	%xmm10, %xmm1, %xmm1
	leal	(%rax,%r15,2), %r15d
	vpmulld	%xmm9, %xmm2, %xmm2
	vpmulld	%xmm8, %xmm4, %xmm4
	leal	(%rsi,%r13,2), %r13d
	vpmulld	%xmm7, %xmm0, %xmm0
	imull	$100, %edx, %edx
	addl	%r15d, %r13d
	vpaddd	%xmm5, %xmm6, %xmm6
	leal	(%rcx,%rcx,2), %r15d
	imull	$121, %eax, %eax
	leal	0(%r13,%r15,4), %r15d
	leal	(%rsi,%rsi,8), %r13d
	vpaddd	%xmm2, %xmm1, %xmm5
	vpmulld	%xmm10, %xmm1, %xmm1
	addl	%edx, %r13d
	vpaddd	%xmm0, %xmm4, %xmm11
	vpmulld	%xmm9, %xmm2, %xmm2
	addl	%eax, %r13d
	vpmulld	%xmm8, %xmm4, %xmm4
	vpmulld	%xmm7, %xmm0, %xmm0
	leal	(%rcx,%rcx,8), %eax
	sall	$4, %eax
	leaq	28(%rdi), %rcx
	leaq	esf_idx_table(%rip), %rdx
	vpaddd	%xmm11, %xmm5, %xmm5
	addl	%eax, %r13d
	leaq	esf_idx2_table(%rip), %rax
	leaq	16256(%rax), %rsi
	vpaddd	%xmm2, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm4, %xmm0
	vmovdqa	%ymm3, %ymm4
	vpaddd	%xmm0, %xmm1, %xmm0
	vpsrlq	$32, %xmm6, %xmm1
	vpaddd	%xmm1, %xmm6, %xmm6
	vpsrlq	$32, %xmm5, %xmm1
	vpaddd	%xmm1, %xmm5, %xmm5
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm6, %ebx
	vmovd	%xmm5, %r12d
	vmovdqa	%ymm3, %ymm5
	vmovd	%xmm0, %r11d
	.p2align 4
	.p2align 3
.L133:
	vmovdqu	(%rcx), %ymm2
	subq	$-128, %rax
	addq	$32, %rcx
	subq	$-128, %rdx
	vpmovzxbw	%xmm2, %ymm0
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm2, %ymm2
	vpmovzxwd	%xmm0, %ymm8
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm2, %ymm6
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm0, %ymm7
	vpmulld	-96(%rdx), %ymm7, %ymm9
	vpmovzxwd	%xmm2, %ymm0
	vpaddd	%ymm7, %ymm8, %ymm2
	vpaddd	%ymm0, %ymm6, %ymm1
	vpaddd	%ymm2, %ymm1, %ymm1
	vpmulld	-32(%rdx), %ymm0, %ymm2
	vpaddd	%ymm1, %ymm4, %ymm4
	vpmulld	-64(%rdx), %ymm6, %ymm1
	vpaddd	%ymm2, %ymm1, %ymm1
	vpmulld	-128(%rdx), %ymm8, %ymm2
	vpaddd	%ymm9, %ymm2, %ymm2
	vpaddd	%ymm2, %ymm1, %ymm1
	vpmulld	-96(%rax), %ymm7, %ymm2
	vpaddd	%ymm1, %ymm5, %ymm5
	vpmulld	-64(%rax), %ymm6, %ymm1
	vpmulld	-32(%rax), %ymm0, %ymm6
	vpaddd	%ymm6, %ymm1, %ymm0
	vpmulld	-128(%rax), %ymm8, %ymm1
	vpaddd	%ymm2, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm3, %ymm3
	cmpq	%rsi, %rax
	jne	.L133
	movzbl	4092(%rdi), %eax
	movl	16256+esf_idx_table(%rip), %edx
	vextracti128	$0x1, %ymm5, %xmm0
	movzbl	4093(%rdi), %esi
	movzbl	4094(%rdi), %ecx
	vpaddd	%xmm5, %xmm0, %xmm0
	imull	%eax, %edx
	movzbl	4095(%rdi), %edi
	vpsrldq	$8, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$4, %xmm0, %xmm1
	addl	%r15d, %edx
	movl	16260+esf_idx_table(%rip), %r15d
	vpaddd	%xmm1, %xmm0, %xmm0
	imull	%esi, %r15d
	addl	%r15d, %edx
	movl	16264+esf_idx_table(%rip), %r15d
	imull	%ecx, %r15d
	addl	%r15d, %edx
	movl	16268+esf_idx_table(%rip), %r15d
	imull	%edi, %r15d
	addl	%r15d, %edx
	addl	%r12d, %edx
	vmovd	%xmm0, %r12d
	vextracti128	$0x1, %ymm3, %xmm0
	addl	%r12d, %edx
	movl	16256+esf_idx2_table(%rip), %r12d
	vpaddd	%xmm3, %xmm0, %xmm0
	vpsrldq	$8, %xmm0, %xmm1
	imull	%eax, %r12d
	vpaddd	%xmm1, %xmm0, %xmm0
	addl	%r14d, %eax
	vpsrldq	$4, %xmm0, %xmm1
	addl	%esi, %eax
	vpaddd	%xmm1, %xmm0, %xmm0
	addl	%ecx, %eax
	addl	%r13d, %r12d
	movl	16260+esf_idx2_table(%rip), %r13d
	addl	%edi, %eax
	addl	%ebx, %eax
	imull	%esi, %r13d
	addl	%r13d, %r12d
	movl	16264+esf_idx2_table(%rip), %r13d
	imull	%ecx, %r13d
	addl	%r13d, %r12d
	movl	16268+esf_idx2_table(%rip), %r13d
	imull	%edi, %r13d
	addl	%r13d, %r12d
	addl	%r12d, %r11d
	vmovd	%xmm0, %r12d
	vextracti128	$0x1, %ymm4, %xmm0
	vpaddd	%xmm4, %xmm0, %xmm0
	addl	%r12d, %r11d
	vpsrldq	$8, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$4, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %ecx
	addl	%ecx, %eax
	movl	%eax, (%r8)
	movl	%edx, (%r9)
	movl	%r11d, (%r10)
	vzeroupper
	popq	%rbx
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%r15
	popq	%rbp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE8:
	.size	esf_scalar_syndromes, .-esf_scalar_syndromes
	.p2align 4
	.type	_mm_malloc, @function
_mm_malloc:
.LFB138:
	.cfi_startproc
	pushq	%rbx
	.cfi_def_cfa_offset 16
	.cfi_offset 3, -16
	movq	%rdi, %rdx
	subq	$16, %rsp
	.cfi_def_cfa_offset 32
	movq	%fs:40, %rbx
	movq	%rbx, 8(%rsp)
	xorl	%ebx, %ebx
	cmpq	$1, %rsi
	je	.L146
	leaq	-2(%rsi), %rax
	movq	%rsp, %rdi
	testq	$-3, %rax
	movl	$8, %eax
	cmove	%rax, %rsi
	call	posix_memalign@PLT
	testl	%eax, %eax
	movq	%rbx, %rax
	cmove	(%rsp), %rax
	movq	8(%rsp), %rdx
	subq	%fs:40, %rdx
	jne	.L145
	addq	$16, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 16
	popq	%rbx
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L146:
	.cfi_restore_state
	movq	8(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L145
	addq	$16, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 16
	popq	%rbx
	.cfi_def_cfa_offset 8
	jmp	malloc@PLT
.L145:
	.cfi_restore_state
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE138:
	.size	_mm_malloc, .-_mm_malloc
	.p2align 4
	.type	_mm_free, @function
_mm_free:
.LFB139:
	.cfi_startproc
	jmp	free@PLT
	.cfi_endproc
.LFE139:
	.size	_mm_free, .-_mm_free
	.p2align 4
	.type	esf_hsum_epi32, @function
esf_hsum_epi32:
.LFB650:
	.cfi_startproc
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	vmovd	%xmm0, %eax
	ret
	.cfi_endproc
.LFE650:
	.size	esf_hsum_epi32, .-esf_hsum_epi32
	.p2align 4
	.type	esf_sse41_syndromes, @function
esf_sse41_syndromes:
.LFB651:
	.cfi_startproc
	pushq	%r15
	.cfi_def_cfa_offset 16
	.cfi_offset 15, -16
	vmovq	.LC51(%rip), %xmm9
	vpxor	%xmm4, %xmm4, %xmm4
	pushq	%r14
	.cfi_def_cfa_offset 24
	.cfi_offset 14, -24
	vmovq	.LC52(%rip), %xmm10
	movq	%rcx, %r14
	pushq	%r13
	.cfi_def_cfa_offset 32
	.cfi_offset 13, -32
	vmovq	.LC53(%rip), %xmm7
	movq	%rdx, %r13
	pushq	%r12
	.cfi_def_cfa_offset 40
	.cfi_offset 12, -40
	vmovq	.LC54(%rip), %xmm8
	movq	%rsi, %r12
	pushq	%rbp
	.cfi_def_cfa_offset 48
	.cfi_offset 6, -48
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	vmovq	4(%rdi), %xmm1
	movzbl	13(%rdi), %edx
	movzbl	12(%rdi), %r10d
	vpmovzxbw	%xmm1, %xmm0
	vpsrlq	$32, %xmm1, %xmm1
	movzbl	14(%rdi), %r8d
	movzbl	15(%rdi), %r9d
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm0, %xmm3
	leal	(%rdx,%r10), %r11d
	vpmovzxwd	%xmm1, %xmm2
	vpsrlq	$32, %xmm0, %xmm0
	leal	(%r10,%r10,8), %r10d
	addl	%r8d, %r11d
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm0, %xmm0
	leal	(%r11,%r9), %ebx
	vpmovzxwd	%xmm1, %xmm1
	vpaddd	%xmm3, %xmm0, %xmm6
	leal	(%rdx,%rdx,4), %r11d
	movl	%ebx, -16(%rsp)
	vpaddd	%xmm2, %xmm1, %xmm5
	vpmulld	%xmm9, %xmm3, %xmm3
	leal	(%r8,%r8,4), %ebx
	vpmulld	%xmm10, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm2, %xmm2
	leal	(%r8,%rbx,2), %ebx
	vpmulld	%xmm8, %xmm1, %xmm1
	imull	$100, %edx, %edx
	leal	(%r10,%r11,2), %r11d
	vpaddd	%xmm5, %xmm6, %xmm6
	leal	(%r10,%r10,8), %r10d
	addl	%ebx, %r11d
	imull	$121, %r8d, %r8d
	leal	(%r9,%r9,2), %ebx
	addl	%r10d, %edx
	leal	(%r11,%rbx,4), %r15d
	vpaddd	%xmm3, %xmm0, %xmm5
	vpmulld	%xmm9, %xmm3, %xmm3
	vpaddd	%xmm2, %xmm1, %xmm11
	vpmulld	%xmm10, %xmm0, %xmm0
	addl	%r8d, %edx
	vpmulld	%xmm8, %xmm1, %xmm1
	vpmulld	%xmm7, %xmm2, %xmm2
	leal	(%r9,%r9,8), %r8d
	sall	$4, %r8d
	leaq	28(%rdi), %r9
	vpaddd	%xmm11, %xmm5, %xmm5
	leal	(%rdx,%r8), %ebx
	movl	%ebx, -12(%rsp)
	leaq	esf_idx_table(%rip), %rdx
	leaq	esf_idx2_table(%rip), %r8
	vpaddd	%xmm3, %xmm0, %xmm0
	leaq	16256(%rdx), %r10
	vmovdqa	%xmm4, %xmm3
	vpaddd	%xmm2, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm6, %xmm1
	vpaddd	%xmm1, %xmm6, %xmm6
	vpsrlq	$32, %xmm5, %xmm1
	vpaddd	%xmm1, %xmm5, %xmm5
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm6, %ecx
	vmovd	%xmm5, %esi
	vmovdqa	%xmm4, %xmm5
	vmovd	%xmm0, %eax
	.p2align 4
	.p2align 3
.L150:
	vmovdqu	(%r9), %xmm2
	addq	$64, %rdx
	addq	$16, %r9
	addq	$64, %r8
	vpsrldq	$8, %xmm2, %xmm6
	vpsrldq	$12, %xmm2, %xmm0
	vpmovzxbd	%xmm2, %xmm8
	vpmovzxbd	%xmm6, %xmm6
	vpsrldq	$4, %xmm2, %xmm1
	vpmovzxbd	%xmm0, %xmm0
	vpmulld	-16(%rdx), %xmm0, %xmm9
	vpaddd	%xmm0, %xmm6, %xmm7
	vpmovzxbd	%xmm1, %xmm1
	vpmulld	-16(%r8), %xmm0, %xmm0
	vpaddd	%xmm1, %xmm8, %xmm2
	vpaddd	%xmm4, %xmm7, %xmm4
	vpaddd	%xmm2, %xmm4, %xmm7
	vpmulld	-32(%rdx), %xmm6, %xmm2
	vpmulld	-32(%r8), %xmm6, %xmm6
	vpaddd	%xmm9, %xmm2, %xmm2
	vpaddd	%xmm6, %xmm0, %xmm0
	vpmulld	-48(%rdx), %xmm1, %xmm9
	vpaddd	%xmm5, %xmm2, %xmm2
	vmovdqa	%xmm7, %xmm4
	vpaddd	%xmm3, %xmm0, %xmm0
	vpmulld	-64(%rdx), %xmm8, %xmm5
	vpmulld	-64(%r8), %xmm8, %xmm3
	vpaddd	%xmm9, %xmm5, %xmm5
	vpmulld	-48(%r8), %xmm1, %xmm1
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm5, %xmm2, %xmm2
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovdqa	%xmm2, %xmm5
	vmovdqa	%xmm0, %xmm3
	cmpq	%rdx, %r10
	jne	.L150
	movzbl	4092(%rdi), %ebp
	movl	16256+esf_idx_table(%rip), %edx
	vpunpckhqdq	%xmm7, %xmm7, %xmm1
	movzbl	4093(%rdi), %ebx
	movzbl	4094(%rdi), %r11d
	vpaddd	%xmm1, %xmm7, %xmm7
	imull	%ebp, %edx
	movzbl	4095(%rdi), %edi
	vpshufd	$177, %xmm7, %xmm1
	vpaddd	%xmm7, %xmm1, %xmm1
	vmovd	%xmm1, %r8d
	vpunpckhqdq	%xmm2, %xmm2, %xmm1
	addl	%r15d, %edx
	movl	16260+esf_idx_table(%rip), %r15d
	vpaddd	%xmm1, %xmm2, %xmm2
	vpshufd	$177, %xmm2, %xmm1
	imull	%ebx, %r15d
	vpaddd	%xmm2, %xmm1, %xmm1
	vmovd	%xmm1, %r10d
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	addl	%edx, %r15d
	movl	16264+esf_idx_table(%rip), %edx
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	imull	%r11d, %edx
	vmovd	%xmm0, %r9d
	addl	%r15d, %edx
	movl	16268+esf_idx_table(%rip), %r15d
	imull	%edi, %r15d
	addl	%r15d, %edx
	addl	%esi, %edx
	movl	16256+esf_idx2_table(%rip), %esi
	addl	%r10d, %edx
	movl	16260+esf_idx2_table(%rip), %r10d
	imull	%ebp, %esi
	addl	-12(%rsp), %esi
	imull	%ebx, %r10d
	addl	%r10d, %esi
	movl	16264+esf_idx2_table(%rip), %r10d
	imull	%r11d, %r10d
	addl	%r10d, %esi
	movl	16268+esf_idx2_table(%rip), %r10d
	imull	%edi, %r10d
	addl	%r10d, %esi
	addl	%esi, %eax
	movl	-16(%rsp), %esi
	addl	%r9d, %eax
	addl	%ebp, %esi
	addl	%ebx, %esi
	addl	%r11d, %esi
	addl	%edi, %esi
	addl	%esi, %ecx
	addl	%r8d, %ecx
	movl	%ecx, (%r12)
	movl	%edx, 0(%r13)
	movl	%eax, (%r14)
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
	.cfi_endproc
.LFE651:
	.size	esf_sse41_syndromes, .-esf_sse41_syndromes
	.p2align 4
	.type	esf_hsum_epi32_avx2, @function
esf_hsum_epi32_avx2:
.LFB7297:
	.cfi_startproc
	vextracti128	$0x1, %ymm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	vmovd	%xmm0, %eax
	ret
	.cfi_endproc
.LFE7297:
	.size	esf_hsum_epi32_avx2, .-esf_hsum_epi32_avx2
	.p2align 4
	.type	esf_avx2_syndromes, @function
esf_avx2_syndromes:
.LFB7298:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	vpxor	%xmm6, %xmm6, %xmm6
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%r15
	pushq	%r14
	.cfi_offset 15, -24
	.cfi_offset 14, -32
	movq	%rcx, %r14
	pushq	%r13
	.cfi_offset 13, -40
	movq	%rdx, %r13
	pushq	%r12
	pushq	%rbx
	andq	$-32, %rsp
	.cfi_offset 12, -48
	.cfi_offset 3, -56
	movq	%rsi, -16(%rsp)
	vmovq	4(%rdi), %xmm1
	vmovq	.LC51(%rip), %xmm9
	vmovq	.LC52(%rip), %xmm10
	vmovq	.LC53(%rip), %xmm7
	vpmovzxbw	%xmm1, %xmm0
	vpsrlq	$32, %xmm1, %xmm1
	movzbl	13(%rdi), %edx
	vmovq	.LC54(%rip), %xmm8
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm0, %xmm3
	movzbl	12(%rdi), %r10d
	movzbl	14(%rdi), %r9d
	vpmovzxwd	%xmm1, %xmm2
	vpsrlq	$32, %xmm0, %xmm0
	movzbl	15(%rdi), %r8d
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm0, %xmm0
	leal	(%rdx,%r10), %r11d
	vpmovzxwd	%xmm1, %xmm1
	vpaddd	%xmm3, %xmm0, %xmm5
	leal	(%r10,%r10,8), %r10d
	addl	%r9d, %r11d
	vpaddd	%xmm2, %xmm1, %xmm4
	vpmulld	%xmm9, %xmm3, %xmm3
	leal	(%r11,%r8), %ebx
	vpmulld	%xmm10, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm2, %xmm2
	leal	(%rdx,%rdx,4), %r11d
	movl	%ebx, -4(%rsp)
	vpmulld	%xmm8, %xmm1, %xmm1
	leal	(%r9,%r9,4), %ebx
	leal	(%r10,%r11,2), %r11d
	vpaddd	%xmm4, %xmm5, %xmm5
	leal	(%r9,%rbx,2), %ebx
	imull	$100, %edx, %edx
	leal	(%r10,%r10,8), %r10d
	addl	%ebx, %r11d
	imull	$121, %r9d, %r9d
	leal	(%r8,%r8,2), %ebx
	vpaddd	%xmm3, %xmm0, %xmm4
	vpmulld	%xmm9, %xmm3, %xmm3
	leal	(%r8,%r8,8), %r8d
	vpaddd	%xmm2, %xmm1, %xmm11
	addl	%r10d, %edx
	sall	$4, %r8d
	leal	(%r11,%rbx,4), %r15d
	vpmulld	%xmm10, %xmm0, %xmm0
	vpmulld	%xmm8, %xmm1, %xmm1
	addl	%r9d, %edx
	vpmulld	%xmm7, %xmm2, %xmm2
	leal	(%rdx,%r8), %ebx
	leaq	esf_idx_table(%rip), %rdx
	vpaddd	%xmm11, %xmm4, %xmm4
	movl	%ebx, -8(%rsp)
	leaq	28(%rdi), %r9
	leaq	esf_idx2_table(%rip), %r8
	leaq	16256(%rdx), %r10
	vpaddd	%xmm3, %xmm0, %xmm0
	vmovdqa	%ymm6, %ymm3
	vpaddd	%xmm2, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm5, %xmm1
	vpaddd	%xmm1, %xmm5, %xmm5
	vpsrlq	$32, %xmm4, %xmm1
	vpaddd	%xmm1, %xmm4, %xmm4
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm5, %ecx
	vmovd	%xmm4, %esi
	vmovdqa	%ymm6, %ymm4
	vmovd	%xmm0, %eax
	.p2align 4
	.p2align 3
.L155:
	vmovdqu	(%r9), %ymm2
	subq	$-128, %rdx
	addq	$32, %r9
	subq	$-128, %r8
	vmovdqa	%xmm2, %xmm1
	vextracti128	$0x1, %ymm2, %xmm2
	vpsrldq	$8, %xmm2, %xmm0
	vpmovzxbd	%xmm1, %ymm7
	vpmovzxbd	%xmm2, %ymm8
	vpmovzxbd	%xmm0, %ymm0
	vpsrldq	$8, %xmm1, %xmm1
	vpmulld	-32(%rdx), %ymm0, %ymm9
	vpmovzxbd	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm8, %ymm5
	vpmulld	-32(%r8), %ymm0, %ymm0
	vpaddd	%ymm1, %ymm7, %ymm2
	vpaddd	%ymm6, %ymm5, %ymm5
	vpaddd	%ymm2, %ymm5, %ymm5
	vpmulld	-64(%rdx), %ymm8, %ymm2
	vpmulld	-64(%r8), %ymm8, %ymm8
	vpaddd	%ymm9, %ymm2, %ymm2
	vpaddd	%ymm8, %ymm0, %ymm0
	vpmulld	-96(%rdx), %ymm1, %ymm9
	vpaddd	%ymm4, %ymm2, %ymm2
	vmovdqa	%ymm5, %ymm6
	vpmulld	-128(%rdx), %ymm7, %ymm4
	vpaddd	%ymm3, %ymm0, %ymm0
	vpaddd	%ymm9, %ymm4, %ymm4
	vpmulld	-96(%r8), %ymm1, %ymm1
	vpmulld	-128(%r8), %ymm7, %ymm7
	vpaddd	%ymm7, %ymm1, %ymm1
	vpaddd	%ymm4, %ymm2, %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vmovdqa	%ymm2, %ymm4
	vmovdqa	%ymm0, %ymm3
	cmpq	%rdx, %r10
	jne	.L155
	movzbl	4092(%rdi), %ebx
	movl	16256+esf_idx_table(%rip), %edx
	vextracti128	$0x1, %ymm5, %xmm5
	vextracti128	$0x1, %ymm2, %xmm2
	movzbl	4093(%rdi), %r11d
	movzbl	4094(%rdi), %r10d
	vpaddd	%xmm5, %xmm6, %xmm1
	imull	%ebx, %edx
	vpunpckhqdq	%xmm1, %xmm1, %xmm3
	movzbl	4095(%rdi), %edi
	vpaddd	%xmm3, %xmm1, %xmm1
	vpshufd	$177, %xmm1, %xmm3
	addl	%r15d, %edx
	movl	16260+esf_idx_table(%rip), %r15d
	vpaddd	%xmm1, %xmm3, %xmm1
	vmovd	%xmm1, %r12d
	vpaddd	%xmm2, %xmm4, %xmm1
	imull	%r11d, %r15d
	vpunpckhqdq	%xmm1, %xmm1, %xmm2
	vpaddd	%xmm2, %xmm1, %xmm1
	vpshufd	$177, %xmm1, %xmm2
	addl	%edx, %r15d
	movl	16264+esf_idx_table(%rip), %edx
	vpaddd	%xmm1, %xmm2, %xmm1
	vmovd	%xmm1, %r9d
	vmovdqa	%xmm0, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	imull	%r10d, %edx
	vpaddd	%xmm0, %xmm1, %xmm0
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	addl	%r15d, %edx
	movl	16268+esf_idx_table(%rip), %r15d
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	imull	%edi, %r15d
	vmovd	%xmm0, %r8d
	addl	%r15d, %edx
	addl	%esi, %edx
	leal	(%rdx,%r9), %esi
	movl	16260+esf_idx2_table(%rip), %r9d
	movl	16256+esf_idx2_table(%rip), %edx
	imull	%r11d, %r9d
	imull	%ebx, %edx
	addl	-8(%rsp), %edx
	addl	%edx, %r9d
	movl	16264+esf_idx2_table(%rip), %edx
	imull	%r10d, %edx
	addl	%r9d, %edx
	movl	16268+esf_idx2_table(%rip), %r9d
	imull	%edi, %r9d
	addl	%r9d, %edx
	addl	%eax, %edx
	movl	-4(%rsp), %eax
	addl	%r8d, %edx
	addl	%ebx, %eax
	addl	%r11d, %eax
	addl	%r10d, %eax
	addl	%edi, %eax
	addl	%ecx, %eax
	movq	-16(%rsp), %rcx
	addl	%r12d, %eax
	movl	%eax, (%rcx)
	movl	%esi, 0(%r13)
	movl	%edx, (%r14)
	vzeroupper
	leaq	-40(%rbp), %rsp
	popq	%rbx
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%r15
	popq	%rbp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE7298:
	.size	esf_avx2_syndromes, .-esf_avx2_syndromes
	.p2align 4
	.type	esf_compute_syndromes_v2, @function
esf_compute_syndromes_v2:
.LFB7299:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	vpxor	%xmm6, %xmm6, %xmm6
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%r15
	pushq	%r14
	.cfi_offset 15, -24
	.cfi_offset 14, -32
	movq	%rcx, %r14
	pushq	%r13
	.cfi_offset 13, -40
	movq	%rdx, %r13
	pushq	%r12
	pushq	%rbx
	andq	$-32, %rsp
	.cfi_offset 12, -48
	.cfi_offset 3, -56
	movq	%rsi, -16(%rsp)
	vmovq	4(%rdi), %xmm1
	vmovq	.LC51(%rip), %xmm9
	vmovq	.LC52(%rip), %xmm10
	vmovq	.LC53(%rip), %xmm7
	vpmovzxbw	%xmm1, %xmm0
	vpsrlq	$32, %xmm1, %xmm1
	movzbl	13(%rdi), %edx
	vmovq	.LC54(%rip), %xmm8
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm0, %xmm3
	movzbl	12(%rdi), %r10d
	movzbl	14(%rdi), %r9d
	vpmovzxwd	%xmm1, %xmm2
	vpsrlq	$32, %xmm0, %xmm0
	movzbl	15(%rdi), %ecx
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm0, %xmm0
	leal	(%rdx,%r10), %r11d
	vpmovzxwd	%xmm1, %xmm1
	vpaddd	%xmm3, %xmm0, %xmm5
	leal	(%r10,%r10,8), %r10d
	addl	%r9d, %r11d
	vpaddd	%xmm2, %xmm1, %xmm4
	vpmulld	%xmm9, %xmm3, %xmm3
	leal	(%r11,%rcx), %ebx
	vpmulld	%xmm10, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm2, %xmm2
	leal	(%rdx,%rdx,4), %r11d
	movl	%ebx, -4(%rsp)
	vpmulld	%xmm8, %xmm1, %xmm1
	leal	(%r9,%r9,4), %ebx
	leal	(%r10,%r11,2), %r11d
	vpaddd	%xmm4, %xmm5, %xmm5
	leal	(%r9,%rbx,2), %ebx
	imull	$100, %edx, %edx
	leal	(%r10,%r10,8), %r10d
	addl	%ebx, %r11d
	imull	$121, %r9d, %r9d
	leal	(%rcx,%rcx,2), %ebx
	vpaddd	%xmm3, %xmm0, %xmm4
	vpmulld	%xmm9, %xmm3, %xmm3
	leal	(%rcx,%rcx,8), %ecx
	vpaddd	%xmm2, %xmm1, %xmm11
	vpmulld	%xmm10, %xmm0, %xmm0
	addl	%r10d, %edx
	sall	$4, %ecx
	vpmulld	%xmm8, %xmm1, %xmm1
	vpmulld	%xmm7, %xmm2, %xmm2
	leal	(%r11,%rbx,4), %r15d
	addl	%r9d, %edx
	leal	(%rdx,%rcx), %ebx
	leaq	esf_idx_table(%rip), %rdx
	vpaddd	%xmm11, %xmm4, %xmm4
	movl	%ebx, -8(%rsp)
	leaq	28(%rdi), %r9
	leaq	esf_idx2_table(%rip), %rcx
	leaq	16256(%rdx), %r10
	vpaddd	%xmm3, %xmm0, %xmm0
	vmovdqa	%ymm6, %ymm3
	vpaddd	%xmm2, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm5, %xmm1
	vpaddd	%xmm1, %xmm5, %xmm5
	vpsrlq	$32, %xmm4, %xmm1
	vpaddd	%xmm1, %xmm4, %xmm4
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm5, %esi
	vmovd	%xmm4, %r8d
	vmovdqa	%ymm6, %ymm4
	vmovd	%xmm0, %eax
	.p2align 4
	.p2align 3
.L159:
	vmovdqu	(%r9), %ymm2
	subq	$-128, %rdx
	addq	$32, %r9
	subq	$-128, %rcx
	vmovdqa	%xmm2, %xmm1
	vextracti128	$0x1, %ymm2, %xmm2
	vpsrldq	$8, %xmm2, %xmm0
	vpmovzxbd	%xmm1, %ymm7
	vpmovzxbd	%xmm2, %ymm8
	vpmulld	-64(%rdx), %ymm8, %ymm9
	vpmovzxbd	%xmm0, %ymm0
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxbd	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm8, %ymm5
	vpmulld	-64(%rcx), %ymm8, %ymm8
	vpaddd	%ymm1, %ymm7, %ymm2
	vpaddd	%ymm6, %ymm5, %ymm5
	vpaddd	%ymm2, %ymm5, %ymm5
	vpmulld	-32(%rdx), %ymm0, %ymm2
	vpmulld	-32(%rcx), %ymm0, %ymm0
	vpaddd	%ymm9, %ymm2, %ymm2
	vpaddd	%ymm8, %ymm0, %ymm0
	vpmulld	-128(%rdx), %ymm7, %ymm9
	vpaddd	%ymm4, %ymm2, %ymm2
	vmovdqa	%ymm5, %ymm6
	vpmulld	-96(%rdx), %ymm1, %ymm4
	vpaddd	%ymm3, %ymm0, %ymm0
	vpaddd	%ymm9, %ymm4, %ymm4
	vpmulld	-96(%rcx), %ymm1, %ymm1
	vpmulld	-128(%rcx), %ymm7, %ymm7
	vpaddd	%ymm7, %ymm1, %ymm1
	vpaddd	%ymm4, %ymm2, %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vmovdqa	%ymm2, %ymm4
	vmovdqa	%ymm0, %ymm3
	cmpq	%rdx, %r10
	jne	.L159
	movzbl	4092(%rdi), %edx
	movl	16256+esf_idx_table(%rip), %ecx
	vextracti128	$0x1, %ymm5, %xmm5
	vextracti128	$0x1, %ymm2, %xmm2
	movzbl	4093(%rdi), %ebx
	movzbl	4094(%rdi), %r11d
	vpaddd	%xmm5, %xmm6, %xmm1
	imull	%edx, %ecx
	vpunpckhqdq	%xmm1, %xmm1, %xmm3
	movzbl	4095(%rdi), %edi
	vpaddd	%xmm3, %xmm1, %xmm1
	vpshufd	$177, %xmm1, %xmm3
	addl	%r15d, %ecx
	movl	16260+esf_idx_table(%rip), %r15d
	vpaddd	%xmm1, %xmm3, %xmm1
	vmovd	%xmm1, %r12d
	vpaddd	%xmm2, %xmm4, %xmm1
	imull	%ebx, %r15d
	vpunpckhqdq	%xmm1, %xmm1, %xmm2
	vpaddd	%xmm2, %xmm1, %xmm1
	vpshufd	$177, %xmm1, %xmm2
	addl	%ecx, %r15d
	movl	16264+esf_idx_table(%rip), %ecx
	vpaddd	%xmm1, %xmm2, %xmm1
	vmovd	%xmm1, %r10d
	vmovdqa	%xmm0, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	imull	%r11d, %ecx
	vpaddd	%xmm0, %xmm1, %xmm0
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	addl	%r15d, %ecx
	movl	16268+esf_idx_table(%rip), %r15d
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	imull	%edi, %r15d
	vmovd	%xmm0, %r9d
	addl	%r15d, %ecx
	addl	%r8d, %ecx
	leal	(%rcx,%r10), %r8d
	movl	16260+esf_idx2_table(%rip), %r10d
	movl	16256+esf_idx2_table(%rip), %ecx
	imull	%ebx, %r10d
	imull	%edx, %ecx
	addl	-8(%rsp), %ecx
	addl	%ecx, %r10d
	movl	16264+esf_idx2_table(%rip), %ecx
	imull	%r11d, %ecx
	addl	%r10d, %ecx
	movl	16268+esf_idx2_table(%rip), %r10d
	imull	%edi, %r10d
	addl	%r10d, %ecx
	addl	%eax, %ecx
	movl	-4(%rsp), %eax
	addl	%r9d, %ecx
	addl	%edx, %eax
	addl	%ebx, %eax
	addl	%r11d, %eax
	addl	%edi, %eax
	addl	%esi, %eax
	movq	-16(%rsp), %rsi
	addl	%r12d, %eax
	movl	%eax, (%rsi)
	movl	%r8d, 0(%r13)
	movl	%ecx, (%r14)
	vzeroupper
	leaq	-40(%rbp), %rsp
	popq	%rbx
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%r15
	popq	%rbp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE7299:
	.size	esf_compute_syndromes_v2, .-esf_compute_syndromes_v2
	.p2align 4
	.type	sqm_init, @function
sqm_init:
.LFB7300:
	.cfi_startproc
	subq	$8, %rsp
	.cfi_def_cfa_offset 16
	movl	$41312, %edx
	xorl	%esi, %esi
	call	memset@PLT
	movl	$4096, %edx
	movl	$255, %esi
	leaq	sqm_slot_of(%rip), %rdi
	addq	$8, %rsp
	.cfi_def_cfa_offset 8
	jmp	memset@PLT
	.cfi_endproc
.LFE7300:
	.size	sqm_init, .-sqm_init
	.p2align 4
	.type	sqm_fill, @function
sqm_fill:
.LFB7301:
	.cfi_startproc
	movl	%esi, %eax
	sall	$4, %eax
	addl	%esi, %eax
	vmovd	%eax, %xmm0
	movl	$-1515870811, %eax
	vpbroadcastb	%xmm0, %ymm0
	vmovd	%eax, %xmm1
	vpaddb	.LC55(%rip), %ymm0, %ymm2
	vpaddb	.LC57(%rip), %ymm0, %ymm0
	vpbroadcastd	%xmm1, %ymm1
	vpxor	%ymm1, %ymm2, %ymm2
	vpxor	%ymm1, %ymm0, %ymm0
	vmovdqu	%ymm2, (%rdi)
	vmovdqu	%ymm0, 32(%rdi)
	vzeroupper
	ret
	.cfi_endproc
.LFE7301:
	.size	sqm_fill, .-sqm_fill
	.p2align 4
	.type	sqm_pay_ok, @function
sqm_pay_ok:
.LFB7302:
	.cfi_startproc
	movq	%rdi, %r8
	movl	%esi, %r9d
	negq	%r8
	andl	$31, %r8d
	je	.L176
	movl	%esi, %eax
	movl	$1, %edx
	sall	$4, %eax
	addl	%esi, %eax
	leal	1(%r8), %esi
	jmp	.L168
	.p2align 5
	.p2align 4,,10
	.p2align 3
.L181:
	leaq	1(%rdx), %rcx
	addl	$91, %eax
	cmpq	%rsi, %rcx
	je	.L180
	movq	%rcx, %rdx
.L168:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, -1(%rdi,%rdx)
	je	.L181
	xorl	%eax, %eax
	ret
	.p2align 4,,10
	.p2align 3
.L180:
	movl	$64, %esi
	movl	%edx, %eax
	subl	%edx, %esi
.L166:
	vmovd	%eax, %xmm4
	vpxor	%xmm6, %xmm6, %xmm6
	movl	%r9d, %edx
	movl	%r8d, %ecx
	vpbroadcastd	%xmm4, %ymm4
	vpaddd	.LC46(%rip), %ymm4, %ymm1
	sall	$4, %edx
	addq	%rdi, %rcx
	vpaddd	.LC59(%rip), %ymm4, %ymm0
	vpaddd	.LC61(%rip), %ymm4, %ymm5
	addl	%r9d, %edx
	vpblendw	$85, %ymm1, %ymm6, %ymm1
	vmovd	%edx, %xmm2
	movl	$-522133280, %edx
	vpblendw	$85, %ymm0, %ymm6, %ymm0
	vpblendw	$85, %ymm5, %ymm6, %ymm5
	vpbroadcastb	%xmm2, %ymm2
	vpackusdw	%ymm0, %ymm1, %ymm1
	vpaddd	.LC60(%rip), %ymm4, %ymm0
	vpermq	$216, %ymm1, %ymm1
	vpblendw	$85, %ymm0, %ymm6, %ymm0
	vpackusdw	%ymm5, %ymm0, %ymm0
	vpcmpeqd	%ymm5, %ymm5, %ymm5
	vpsrlw	$8, %ymm5, %ymm5
	vpermq	$216, %ymm0, %ymm0
	vpand	%ymm0, %ymm5, %ymm0
	vpand	%ymm1, %ymm5, %ymm1
	vpackuswb	%ymm0, %ymm1, %ymm1
	vpermq	$216, %ymm1, %ymm1
	vpaddb	%ymm1, %ymm1, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm0
	vpaddb	%ymm1, %ymm0, %ymm0
	vmovd	%edx, %xmm1
	movl	$-1515870811, %edx
	vpsllw	$5, %ymm0, %ymm7
	vpbroadcastd	%xmm1, %ymm1
	vpand	%ymm7, %ymm1, %ymm7
	vpaddb	%ymm7, %ymm0, %ymm0
	vmovd	%edx, %xmm7
	vpsubb	%ymm0, %ymm2, %ymm0
	vpbroadcastd	%xmm7, %ymm7
	vpxor	%ymm7, %ymm0, %ymm0
	vpcmpeqb	(%rcx), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L178
	movl	$64, %edx
	subl	%r8d, %edx
	shrl	$5, %edx
	cmpl	$2, %edx
	jne	.L170
	vpaddd	.LC64(%rip), %ymm4, %ymm0
	vpaddd	.LC65(%rip), %ymm4, %ymm8
	movl	$32, %edx
	vpblendw	$85, %ymm8, %ymm6, %ymm8
	vpblendw	$85, %ymm0, %ymm6, %ymm0
	vpackusdw	%ymm8, %ymm0, %ymm0
	vpaddd	.LC66(%rip), %ymm4, %ymm8
	vpaddd	.LC67(%rip), %ymm4, %ymm4
	vpermq	$216, %ymm0, %ymm0
	vpblendw	$85, %ymm8, %ymm6, %ymm8
	vpblendw	$85, %ymm4, %ymm6, %ymm3
	vpand	%ymm0, %ymm5, %ymm0
	vpackusdw	%ymm3, %ymm8, %ymm3
	vpermq	$216, %ymm3, %ymm3
	vpand	%ymm3, %ymm5, %ymm5
	vpackuswb	%ymm5, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm3
	vpaddb	%ymm3, %ymm3, %ymm3
	vpaddb	%ymm0, %ymm3, %ymm0
	vpsllw	$5, %ymm0, %ymm3
	vpand	%ymm1, %ymm3, %ymm1
	vpaddb	%ymm1, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm2, %ymm0
	vpxor	%ymm7, %ymm0, %ymm0
	vpcmpeqb	32(%rcx), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L169
.L171:
	movl	$1, %eax
	vzeroupper
	ret
.L178:
	xorl	%edx, %edx
.L169:
	subl	%edx, %esi
	addl	%edx, %eax
	movl	%esi, %r8d
.L175:
	movl	$91, %ecx
	movl	%eax, %esi
	imull	%ecx, %eax
	movl	%r9d, %ecx
	leaq	(%rdi,%rsi), %rdx
	sall	$4, %ecx
	leaq	1(%rdi,%rsi), %rsi
	addl	%r9d, %ecx
	addl	%ecx, %eax
	leal	-1(%r8), %ecx
	addq	%rcx, %rsi
	jmp	.L174
	.p2align 5
	.p2align 4,,10
	.p2align 3
.L172:
	addq	$1, %rdx
	addl	$91, %eax
	cmpq	%rsi, %rdx
	je	.L171
.L174:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, (%rdx)
	je	.L172
	vzeroupper
	xorl	%eax, %eax
	ret
.L176:
	movl	$64, %esi
	xorl	%eax, %eax
	jmp	.L166
.L170:
	addl	$32, %eax
	leal	-32(%rsi), %r8d
	jmp	.L175
	.cfi_endproc
.LFE7302:
	.size	sqm_pay_ok, .-sqm_pay_ok
	.p2align 4
	.type	sqm_mom, @function
sqm_mom:
.LFB7303:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movl	$16, %eax
	vpxor	%xmm13, %xmm13, %xmm13
	movl	%edx, %r10d
	vmovd	%eax, %xmm0
	movl	$8, %eax
	vmovd	%eax, %xmm2
	movl	%edx, %eax
	vpbroadcastd	%xmm0, %ymm0
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%r12
	vpbroadcastd	%xmm2, %ymm2
	.cfi_offset 12, -24
	movl	%esi, %r12d
	pushq	%rbx
	.cfi_offset 3, -32
	movq	%rdi, %rbx
	andq	$-32, %rsp
	subq	$520, %rsp
	andl	$15, %eax
	je	.L183
	testl	%edx, %edx
	jle	.L197
	leal	-1(%rdx), %eax
	cmpl	$30, %eax
	jbe	.L192
	addl	$1, %r12d
	movl	%edx, %r11d
	vmovdqa	%ymm2, -56(%rsp)
	movq	%rdi, %rax
	vmovd	%r12d, %xmm4
	shrl	$5, %r11d
	movl	$32, %esi
	vmovdqa	.LC46(%rip), %ymm7
	vpbroadcastd	%xmm4, %ymm4
	movl	%r11d, %edx
	vmovdqa	%ymm13, 136(%rsp)
	vpaddd	%ymm2, %ymm4, %ymm2
	salq	$5, %rdx
	vmovdqa	%ymm4, 8(%rsp)
	vmovdqa	%ymm2, -88(%rsp)
	vmovd	%esi, %xmm2
	addq	%rdi, %rdx
	vpbroadcastd	%xmm2, %ymm2
	vmovdqa	%ymm13, 104(%rsp)
	vmovdqa	%ymm13, 72(%rsp)
	vmovdqa	%ymm13, 40(%rsp)
	vmovdqa	%ymm7, 488(%rsp)
	vmovdqa	%ymm0, -24(%rsp)
	vmovdqa	%ymm2, -120(%rsp)
	.p2align 4
	.p2align 3
.L189:
	vmovdqa	488(%rsp), %ymm6
	vmovdqa	8(%rsp), %ymm1
	addq	$32, %rax
	vpaddd	-56(%rsp), %ymm6, %ymm4
	vpaddd	-24(%rsp), %ymm6, %ymm0
	vpaddd	%ymm1, %ymm6, %ymm2
	vpaddd	%ymm1, %ymm4, %ymm4
	vpaddd	%ymm1, %ymm0, %ymm6
	vpmovsxdq	%xmm2, %ymm12
	vextracti128	$0x1, %ymm4, %xmm3
	vpaddd	-88(%rsp), %ymm0, %ymm0
	vpmovsxdq	%xmm6, %ymm7
	vmovdqa	%ymm12, 296(%rsp)
	vpmovsxdq	%xmm3, %ymm14
	vextracti128	$0x1, %ymm6, %xmm3
	vextracti128	$0x1, %ymm2, %xmm1
	vmovdqa	%ymm7, 392(%rsp)
	vpmovsxdq	%xmm3, %ymm3
	vmovdqu	-32(%rax), %ymm7
	vpmovsxdq	%xmm0, %ymm5
	vpermq	$216, %ymm2, %ymm2
	vpmovsxdq	%xmm4, %ymm15
	vpermq	$216, %ymm4, %ymm4
	vpermq	$216, %ymm6, %ymm6
	vmovdqa	%ymm3, 424(%rsp)
	vextracti128	$0x1, %ymm0, %xmm3
	vpermq	$216, %ymm0, %ymm0
	vmovdqa	%ymm5, 456(%rsp)
	vpmovsxdq	%xmm1, %ymm1
	vmovdqa	%ymm15, 328(%rsp)
	vpmovsxdq	%xmm3, %ymm13
	vpmovzxbw	%xmm7, %ymm3
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxwd	%xmm3, %ymm8
	vpmovzxbw	%xmm7, %ymm7
	vextracti128	$0x1, %ymm3, %xmm3
	vmovdqa	%ymm14, 360(%rsp)
	vpmovzxwd	%xmm7, %ymm9
	vextracti128	$0x1, %ymm8, %xmm5
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxwd	%xmm7, %ymm7
	vpmovzxdq	%xmm8, %ymm10
	vpmovzxdq	%xmm5, %ymm5
	vpaddq	%ymm10, %ymm5, %ymm5
	vpmovzxdq	%xmm7, %ymm10
	vpmovzxdq	%xmm9, %ymm11
	vpaddq	%ymm10, %ymm5, %ymm5
	vextracti128	$0x1, %ymm9, %xmm10
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxdq	%xmm10, %ymm10
	vpermq	$216, %ymm9, %ymm9
	vpaddq	%ymm11, %ymm10, %ymm10
	vpmovzxdq	%xmm3, %ymm11
	vpaddq	%ymm10, %ymm5, %ymm5
	vextracti128	$0x1, %ymm3, %xmm10
	vpmovzxdq	%xmm10, %ymm10
	vpaddq	%ymm11, %ymm10, %ymm10
	vextracti128	$0x1, %ymm7, %xmm11
	vpermq	$216, %ymm7, %ymm7
	vpmovzxdq	%xmm11, %ymm11
	vpaddq	%ymm11, %ymm10, %ymm10
	vpaddq	%ymm10, %ymm5, %ymm5
	vpaddq	136(%rsp), %ymm5, %ymm11
	vpermq	$216, %ymm8, %ymm5
	vpshufd	$80, %ymm5, %ymm10
	vpshufd	$80, %ymm2, %ymm8
	vpshufd	$250, %ymm5, %ymm5
	vpshufd	$250, %ymm2, %ymm2
	vpmuldq	%ymm10, %ymm8, %ymm8
	vmovdqa	%ymm11, 136(%rsp)
	vpmuldq	%ymm5, %ymm2, %ymm2
	vpermq	$216, %ymm3, %ymm5
	vpshufd	$80, %ymm4, %ymm3
	vpshufd	$80, %ymm5, %ymm10
	vpshufd	$250, %ymm4, %ymm4
	vpshufd	$250, %ymm5, %ymm5
	vpmuldq	%ymm10, %ymm3, %ymm3
	vpmuldq	%ymm5, %ymm4, %ymm4
	vpshufd	$80, %ymm9, %ymm10
	vpshufd	$80, %ymm6, %ymm5
	vpshufd	$250, %ymm9, %ymm9
	vpshufd	$250, %ymm6, %ymm6
	vpmuldq	%ymm10, %ymm5, %ymm5
	vpmuldq	%ymm9, %ymm6, %ymm6
	vpshufd	$80, %ymm7, %ymm10
	vpshufd	$80, %ymm0, %ymm9
	vpshufd	$250, %ymm7, %ymm7
	vpshufd	$250, %ymm0, %ymm0
	vpmuldq	%ymm10, %ymm9, %ymm9
	vpmuldq	%ymm7, %ymm0, %ymm0
	vpaddq	%ymm8, %ymm2, %ymm7
	vpaddq	%ymm5, %ymm6, %ymm10
	vpaddq	%ymm9, %ymm7, %ymm7
	vpaddq	%ymm10, %ymm7, %ymm7
	vpaddq	%ymm3, %ymm4, %ymm10
	vpaddq	%ymm0, %ymm10, %ymm10
	vpaddq	%ymm10, %ymm7, %ymm7
	vpaddq	104(%rsp), %ymm7, %ymm11
	vpmuludq	%ymm12, %ymm8, %ymm7
	vpsrlq	$32, %ymm8, %ymm10
	vpmuludq	296(%rsp), %ymm10, %ymm10
	vmovdqa	%ymm11, 104(%rsp)
	vpsrlq	$32, %ymm12, %ymm11
	vpsrlq	$32, %ymm1, %ymm12
	vmovdqa	%ymm11, 264(%rsp)
	vpsrlq	$32, %ymm15, %ymm11
	vpmuludq	264(%rsp), %ymm8, %ymm8
	vpaddq	%ymm10, %ymm8, %ymm8
	vpsrlq	$32, %ymm2, %ymm10
	vpsllq	$32, %ymm8, %ymm8
	vmovdqa	%ymm12, 232(%rsp)
	vpmuludq	%ymm1, %ymm10, %ymm10
	vpsrlq	$32, %ymm14, %ymm12
	vpaddq	%ymm8, %ymm7, %ymm7
	vmovdqa	%ymm11, 200(%rsp)
	vpmuludq	%ymm2, %ymm1, %ymm8
	vpsrlq	$32, %ymm5, %ymm11
	vpmuludq	232(%rsp), %ymm2, %ymm2
	vmovdqa	%ymm12, 168(%rsp)
	vpmuludq	392(%rsp), %ymm11, %ymm11
	vpsrlq	$32, %ymm6, %ymm12
	vpmuludq	424(%rsp), %ymm12, %ymm12
	vpaddq	%ymm10, %ymm2, %ymm2
	vpsrlq	$32, %ymm3, %ymm10
	vpmuludq	328(%rsp), %ymm10, %ymm10
	vpsllq	$32, %ymm2, %ymm2
	vpaddq	%ymm2, %ymm8, %ymm8
	vpmuludq	%ymm15, %ymm3, %ymm2
	vpmuludq	200(%rsp), %ymm3, %ymm3
	vpaddq	%ymm10, %ymm3, %ymm3
	vpsllq	$32, %ymm3, %ymm3
	vpsrlq	$32, %ymm4, %ymm10
	vpmuludq	360(%rsp), %ymm10, %ymm10
	vpaddq	%ymm3, %ymm2, %ymm2
	vpmuludq	%ymm14, %ymm4, %ymm3
	vpmuludq	168(%rsp), %ymm4, %ymm4
	vpaddq	%ymm10, %ymm4, %ymm4
	vmovdqa	392(%rsp), %ymm10
	vpsllq	$32, %ymm4, %ymm4
	vmovdqa	424(%rsp), %ymm14
	vpsrlq	$32, %ymm10, %ymm10
	vpaddq	%ymm4, %ymm3, %ymm3
	vpmuludq	392(%rsp), %ymm5, %ymm4
	vpmuludq	%ymm5, %ymm10, %ymm5
	vmovdqa	456(%rsp), %ymm15
	vpaddq	%ymm11, %ymm5, %ymm5
	vpsrlq	$32, %ymm14, %ymm11
	vpsllq	$32, %ymm5, %ymm5
	vpaddq	%ymm5, %ymm4, %ymm4
	vpmuludq	%ymm14, %ymm6, %ymm5
	vpmuludq	%ymm6, %ymm11, %ymm6
	vpsrlq	$32, %ymm9, %ymm14
	vpmuludq	456(%rsp), %ymm14, %ymm14
	vpmuludq	%ymm4, %ymm10, %ymm10
	vpaddq	%ymm12, %ymm6, %ymm6
	vpsrlq	$32, %ymm15, %ymm12
	vpsllq	$32, %ymm6, %ymm6
	vpaddq	%ymm6, %ymm5, %ymm5
	vpmuludq	%ymm15, %ymm9, %ymm6
	vpmuludq	%ymm9, %ymm12, %ymm9
	vpmuludq	%ymm0, %ymm13, %ymm15
	vpmuludq	%ymm5, %ymm11, %ymm11
	vpaddq	%ymm14, %ymm9, %ymm9
	vpsrlq	$32, %ymm0, %ymm14
	vpsllq	$32, %ymm9, %ymm9
	vpmuludq	%ymm13, %ymm14, %ymm14
	vpaddq	%ymm9, %ymm6, %ymm6
	vpsrlq	$32, %ymm13, %ymm9
	vpmuludq	%ymm0, %ymm9, %ymm0
	vpmuludq	%ymm6, %ymm12, %ymm12
	vpaddq	%ymm14, %ymm0, %ymm0
	vpaddq	%ymm7, %ymm8, %ymm14
	vpsllq	$32, %ymm0, %ymm0
	vpaddq	%ymm6, %ymm14, %ymm14
	vpaddq	%ymm0, %ymm15, %ymm0
	vpaddq	%ymm4, %ymm5, %ymm15
	vpaddq	%ymm15, %ymm14, %ymm14
	vpaddq	%ymm2, %ymm3, %ymm15
	vpmuludq	%ymm0, %ymm9, %ymm9
	vpaddq	%ymm0, %ymm15, %ymm15
	vpaddq	%ymm15, %ymm14, %ymm14
	vpaddq	72(%rsp), %ymm14, %ymm14
	vpmuludq	%ymm1, %ymm8, %ymm15
	vmovdqa	%ymm14, 72(%rsp)
	vpsrlq	$32, %ymm8, %ymm14
	vpmuludq	%ymm1, %ymm14, %ymm14
	vpmuludq	232(%rsp), %ymm8, %ymm1
	vpmuludq	296(%rsp), %ymm7, %ymm8
	vpaddq	%ymm1, %ymm14, %ymm14
	vpsrlq	$32, %ymm7, %ymm1
	vpmuludq	264(%rsp), %ymm7, %ymm7
	vpmuludq	296(%rsp), %ymm1, %ymm1
	vpaddq	%ymm7, %ymm1, %ymm1
	vpsllq	$32, %ymm14, %ymm14
	vpmuludq	456(%rsp), %ymm6, %ymm7
	vpsllq	$32, %ymm1, %ymm1
	vpaddq	%ymm14, %ymm15, %ymm15
	vpaddq	%ymm1, %ymm8, %ymm8
	vpsrlq	$32, %ymm6, %ymm1
	vpmuludq	456(%rsp), %ymm1, %ymm1
	vpaddq	%ymm12, %ymm1, %ymm1
	vpsllq	$32, %ymm1, %ymm1
	vpsrlq	$32, %ymm5, %ymm6
	vpaddq	%ymm8, %ymm15, %ymm8
	vpmuludq	424(%rsp), %ymm6, %ymm6
	vpaddq	%ymm1, %ymm7, %ymm7
	vpaddq	%ymm11, %ymm6, %ymm6
	vpmuludq	424(%rsp), %ymm5, %ymm1
	vpsrlq	$32, %ymm4, %ymm5
	vpmuludq	392(%rsp), %ymm5, %ymm5
	vpaddq	%ymm10, %ymm5, %ymm5
	vpsllq	$32, %ymm6, %ymm6
	vpaddq	%ymm7, %ymm8, %ymm7
	vpsllq	$32, %ymm5, %ymm5
	vpaddq	%ymm6, %ymm1, %ymm1
	vpmuludq	392(%rsp), %ymm4, %ymm6
	vpsrlq	$32, %ymm3, %ymm4
	vpaddq	%ymm5, %ymm6, %ymm6
	vpmuludq	360(%rsp), %ymm4, %ymm4
	vpmuludq	360(%rsp), %ymm3, %ymm5
	vpmuludq	168(%rsp), %ymm3, %ymm3
	vpaddq	%ymm3, %ymm4, %ymm4
	vpmuludq	328(%rsp), %ymm2, %ymm3
	vpaddq	%ymm6, %ymm1, %ymm1
	vpsllq	$32, %ymm4, %ymm4
	vpaddq	%ymm1, %ymm7, %ymm1
	vmovdqa	488(%rsp), %ymm6
	vpaddq	%ymm4, %ymm5, %ymm5
	vpsrlq	$32, %ymm2, %ymm4
	vpmuludq	200(%rsp), %ymm2, %ymm2
	vpmuludq	328(%rsp), %ymm4, %ymm4
	vpaddq	%ymm2, %ymm4, %ymm4
	vpsrlq	$32, %ymm0, %ymm2
	vpmuludq	%ymm13, %ymm2, %ymm2
	vpsllq	$32, %ymm4, %ymm4
	vpaddq	%ymm4, %ymm3, %ymm3
	vpmuludq	%ymm13, %ymm0, %ymm4
	vpaddq	%ymm3, %ymm5, %ymm3
	vpaddq	%ymm9, %ymm2, %ymm2
	vpsllq	$32, %ymm2, %ymm2
	vpaddq	%ymm2, %ymm4, %ymm0
	vpaddq	%ymm0, %ymm3, %ymm3
	vpaddd	-120(%rsp), %ymm6, %ymm0
	vpaddq	%ymm3, %ymm1, %ymm1
	vpaddq	40(%rsp), %ymm1, %ymm2
	vmovdqa	%ymm0, 488(%rsp)
	vmovdqa	%ymm2, 40(%rsp)
	cmpq	%rdx, %rax
	jne	.L189
	vmovdqa	136(%rsp), %ymm4
	sall	$5, %r11d
	vextracti128	$0x1, %ymm4, %xmm1
	vpaddq	%xmm4, %xmm1, %xmm0
	vmovdqa	104(%rsp), %ymm4
	vpsrldq	$8, %xmm0, %xmm1
	vpaddq	%xmm1, %xmm0, %xmm0
	vextracti128	$0x1, %ymm4, %xmm1
	vmovq	%xmm0, %r9
	vpaddq	%xmm4, %xmm1, %xmm0
	vpsrldq	$8, %xmm0, %xmm1
	vpaddq	%xmm1, %xmm0, %xmm0
	vmovq	%xmm0, %r8
	vmovdqa	72(%rsp), %ymm0
	vextracti128	$0x1, %ymm0, %xmm1
	vpaddq	%xmm0, %xmm1, %xmm0
	vpsrldq	$8, %xmm0, %xmm1
	vpaddq	%xmm1, %xmm0, %xmm0
	vextracti128	$0x1, %ymm2, %xmm1
	vmovq	%xmm0, %rdi
	vpaddq	%xmm2, %xmm1, %xmm0
	vpsrldq	$8, %xmm0, %xmm1
	vpaddq	%xmm1, %xmm0, %xmm0
	vmovq	%xmm0, %rsi
	cmpl	%r10d, %r11d
	je	.L185
.L188:
	movl	%r11d, %eax
	leaq	(%rbx,%rax), %rdx
	leal	(%r12,%r11), %ebx
	movq	%rcx, %r12
	subl	%edx, %ebx
	subl	%edx, %r11d
	.p2align 6
	.p2align 4
	.p2align 3
.L190:
	movzbl	(%rdx), %eax
	leal	(%rbx,%rdx), %ecx
	addq	$1, %rdx
	movslq	%ecx, %rcx
	addq	%rax, %r9
	imulq	%rcx, %rax
	addq	%rax, %r8
	imulq	%rcx, %rax
	addq	%rax, %rdi
	imulq	%rcx, %rax
	addq	%rax, %rsi
	leal	(%r11,%rdx), %eax
	cmpl	%eax, %r10d
	jg	.L190
	movq	%r12, %rcx
.L185:
	movq	%r9, (%rcx)
	movq	%r8, 8(%rcx)
	movq	%rdi, 16(%rcx)
	movq	%rsi, 24(%rcx)
	vzeroupper
	leaq	-16(%rbp), %rsp
	popq	%rbx
	popq	%r12
	popq	%rbp
	.cfi_remember_state
	.cfi_def_cfa 7, 8
	ret
	.p2align 4,,10
	.p2align 3
.L183:
	.cfi_restore_state
	testl	%edx, %edx
	jle	.L191
	movl	$4, %edx
	vmovd	%esi, %xmm4
	vmovdqa	%xmm13, %xmm1
	vmovdqa	%xmm2, 456(%rsp)
	vmovd	%edx, %xmm7
	movl	$12, %edx
	vpbroadcastd	%xmm4, %xmm4
	vmovdqa	%xmm0, 392(%rsp)
	vmovd	%edx, %xmm2
	vpbroadcastd	%xmm7, %xmm7
	vpaddd	.LC0(%rip), %xmm4, %xmm4
	vpbroadcastd	%xmm2, %xmm2
	vmovdqa	%xmm13, %xmm8
	vmovdqa	%xmm13, %xmm14
	vmovdqa	%xmm7, 488(%rsp)
	vmovdqa	%xmm2, 424(%rsp)
	.p2align 4
	.p2align 3
.L187:
	vpaddd	488(%rsp), %xmm4, %xmm2
	movslq	%eax, %rdx
	addl	$16, %eax
	vpaddd	456(%rsp), %xmm4, %xmm6
	vmovdqu	(%rbx,%rdx), %xmm0
	vpsrldq	$8, %xmm0, %xmm7
	vpsrldq	$12, %xmm0, %xmm10
	vpmovzxbd	%xmm0, %xmm3
	vpsrldq	$4, %xmm0, %xmm5
	vpmovzxbd	%xmm7, %xmm7
	vpmovzxbd	%xmm10, %xmm10
	vpaddd	%xmm10, %xmm7, %xmm12
	vpmulld	%xmm6, %xmm7, %xmm7
	vpmovzxbd	%xmm5, %xmm5
	vpaddd	%xmm5, %xmm3, %xmm0
	vpaddd	%xmm13, %xmm12, %xmm12
	vpmulld	%xmm4, %xmm3, %xmm3
	vpaddd	%xmm0, %xmm12, %xmm12
	vpmulld	%xmm2, %xmm5, %xmm5
	vpaddd	424(%rsp), %xmm4, %xmm0
	vmovdqa	%xmm12, %xmm13
	vpmulld	%xmm0, %xmm10, %xmm10
	vpmulld	%xmm7, %xmm6, %xmm15
	vpmulld	%xmm6, %xmm6, %xmm6
	vpaddd	%xmm5, %xmm3, %xmm11
	vpaddd	%xmm14, %xmm11, %xmm11
	vpaddd	%xmm10, %xmm7, %xmm9
	vpaddd	%xmm9, %xmm11, %xmm11
	vpmulld	%xmm10, %xmm0, %xmm9
	vpmulld	%xmm0, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm6, %xmm6
	vmovdqa	%xmm11, %xmm14
	vpaddd	%xmm15, %xmm9, %xmm9
	vpmulld	%xmm4, %xmm3, %xmm15
	vpmulld	%xmm10, %xmm0, %xmm0
	vpaddd	%xmm8, %xmm9, %xmm9
	vpmulld	%xmm5, %xmm2, %xmm8
	vpmulld	%xmm2, %xmm2, %xmm2
	vpaddd	%xmm6, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpmulld	%xmm4, %xmm4, %xmm1
	vpaddd	%xmm15, %xmm8, %xmm8
	vpmulld	%xmm5, %xmm2, %xmm2
	vpaddd	%xmm8, %xmm9, %xmm9
	vpaddd	392(%rsp), %xmm4, %xmm4
	vmovdqa	%xmm9, %xmm8
	vpmulld	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vmovdqa	%xmm0, %xmm1
	cmpl	%eax, %r10d
	jg	.L187
.L186:
	vpunpckhqdq	%xmm13, %xmm13, %xmm13
	vpunpckhqdq	%xmm14, %xmm14, %xmm14
	vpunpckhqdq	%xmm1, %xmm1, %xmm1
	vpaddd	%xmm13, %xmm12, %xmm12
	vpaddd	%xmm14, %xmm11, %xmm11
	vpunpckhqdq	%xmm8, %xmm8, %xmm8
	vpshufd	$177, %xmm12, %xmm2
	vpaddd	%xmm8, %xmm9, %xmm9
	vpaddd	%xmm1, %xmm0, %xmm0
	vpaddd	%xmm12, %xmm2, %xmm2
	vpshufd	$177, %xmm0, %xmm1
	vmovd	%xmm2, %r9d
	vpshufd	$177, %xmm11, %xmm2
	vpaddd	%xmm0, %xmm1, %xmm0
	vpaddd	%xmm11, %xmm2, %xmm2
	vmovd	%xmm0, %esi
	vmovd	%xmm2, %r8d
	vpshufd	$177, %xmm9, %xmm2
	vpaddd	%xmm9, %xmm2, %xmm2
	vmovd	%xmm2, %edi
	jmp	.L185
	.p2align 4,,10
	.p2align 3
.L197:
	xorl	%r9d, %r9d
	xorl	%r8d, %r8d
	xorl	%edi, %edi
	xorl	%esi, %esi
	jmp	.L185
.L192:
	xorl	%r11d, %r11d
	xorl	%esi, %esi
	xorl	%edi, %edi
	xorl	%r8d, %r8d
	xorl	%r9d, %r9d
	addl	$1, %r12d
	jmp	.L188
.L191:
	vmovdqa	%xmm13, %xmm0
	vmovdqa	%xmm13, %xmm9
	vmovdqa	%xmm13, %xmm11
	vmovdqa	%xmm13, %xmm12
	vmovdqa	%xmm13, %xmm1
	vmovdqa	%xmm13, %xmm8
	vmovdqa	%xmm13, %xmm14
	jmp	.L186
	.cfi_endproc
.LFE7303:
	.size	sqm_mom, .-sqm_mom
	.p2align 4
	.type	sqm_mom_eq, @function
sqm_mom_eq:
.LFB7304:
	.cfi_startproc
	vmovdqu	(%rdi), %ymm0
	vpxor	(%rsi), %ymm0, %ymm0
	xorl	%eax, %eax
	vptest	%ymm0, %ymm0
	sete	%al
	vzeroupper
	ret
	.cfi_endproc
.LFE7304:
	.size	sqm_mom_eq, .-sqm_mom_eq
	.p2align 4
	.type	sqm_solve, @function
sqm_solve:
.LFB7305:
	.cfi_startproc
	subq	$32, %rsp
	.cfi_def_cfa_offset 40
	movq	%r15, 24(%rsp)
	.cfi_offset 15, -16
	movq	%rcx, %r15
	movq	(%rdi), %rcx
	testq	%rcx, %rcx
	je	.L205
	movq	%rbx, (%rsp)
	movq	%rsi, %r11
	movq	16(%rdi), %r9
	movq	%rdx, %r10
	leaq	255(%rcx), %rax
	movq	8(%rdi), %rsi
	.cfi_offset 3, -40
	movq	24(%rdi), %rbx
	cmpq	$510, %rax
	ja	.L204
	movq	%rsi, %rax
	cqto
	idivq	%rcx
	testq	%rdx, %rdx
	jne	.L204
	leaq	-1(%rax), %rdx
	cmpq	$63, %rdx
	ja	.L204
	movq	%rax, %rdx
	imulq	%rax, %rdx
	imulq	%rcx, %rdx
	cmpq	%r9, %rdx
	je	.L245
	.p2align 4
	.p2align 3
.L204:
	movq	%rcx, %rdx
	movq	%rsi, %rax
	imulq	%r9, %rdx
	imulq	%rsi, %rax
	movq	%rdx, %rdi
	subq	%rax, %rdi
	je	.L236
	movq	%rcx, %rax
	movq	%rsi, %rdx
	imulq	%r9, %rdx
	imulq	%rbx, %rax
	subq	%rdx, %rax
	cqto
	idivq	%rdi
	movq	%rax, -8(%rsp)
	testq	%rdx, %rdx
	jne	.L236
	movq	%rsi, %rdx
	imulq	%rbx, %rdx
	movq	%rdx, %rax
	movq	%r9, %rdx
	imulq	%r9, %rdx
	subq	%rdx, %rax
	cqto
	idivq	%rdi
	testq	%rdx, %rdx
	jne	.L236
	movq	-8(%rsp), %rdi
	negq	%rax
	movq	%rdi, %rdx
	imulq	%rdi, %rdx
	leaq	(%rdx,%rax,4), %rdi
	testq	%rdi, %rdi
	jle	.L236
	movl	$1, %edx
	cmpq	$1, %rdi
	je	.L206
	.p2align 4
	.p2align 4
	.p2align 3
.L207:
	addq	$1, %rdx
	movq	%rdx, %rax
	imulq	%rdx, %rax
	cmpq	%rax, %rdi
	jg	.L207
	jne	.L236
.L206:
	movq	-8(%rsp), %rax
	leaq	(%rax,%rdx), %rdi
	testb	$1, %dil
	jne	.L236
	subq	%rdx, %rax
	leaq	-2(%rdi), %rdx
	cmpq	$127, %rdx
	ja	.L236
	leaq	-2(%rax), %rdx
	cmpq	$127, %rdx
	ja	.L236
	sarq	%rdi
	sarq	%rax
	movq	%rbp, 8(%rsp)
	movq	%rdi, %rdx
	.cfi_offset 6, -32
	movq	%rdi, %rbp
	movq	%rax, %rdi
	cmpq	%rax, %rdx
	jne	.L246
.L242:
	movq	(%rsp), %rbx
	.cfi_restore 3
	movq	8(%rsp), %rbp
	.cfi_restore 6
	.p2align 4
	.p2align 3
.L205:
	xorl	%eax, %eax
.L201:
	movq	24(%rsp), %r15
	addq	$32, %rsp
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L236:
	.cfi_def_cfa_offset 40
	.cfi_offset 3, -40
	movq	(%rsp), %rbx
	.cfi_remember_state
	.cfi_restore 3
	jmp	.L205
	.p2align 4,,10
	.p2align 3
.L245:
	.cfi_restore_state
	imulq	%rax, %rdx
	cmpq	%rbx, %rdx
	jne	.L204
	movl	%eax, (%r11)
	movq	(%rsp), %rbx
	.cfi_restore 3
	movl	$1, %eax
	movl	%ecx, (%r10)
	jmp	.L201
.L246:
	.cfi_offset 3, -40
	.cfi_offset 6, -32
	movq	%rcx, %rax
	subq	%rdi, %rdx
	imulq	%rdi, %rax
	subq	%rax, %rsi
	movq	%rsi, %rax
	movq	%rdx, %rsi
	cqto
	idivq	%rsi
	movq	%rax, %rsi
	testq	%rdx, %rdx
	jne	.L242
	leaq	255(%rax), %rax
	cmpq	$510, %rax
	ja	.L242
	subq	%rsi, %rcx
	leaq	255(%rcx), %rax
	cmpq	$510, %rax
	ja	.L242
	testq	%rsi, %rsi
	je	.L242
	testq	%rcx, %rcx
	je	.L242
	movq	%rbp, %rax
	movq	%rdi, %rdx
	movq	%r14, 16(%rsp)
	.cfi_offset 14, -24
	imulq	%rbp, %rax
	imulq	%rdi, %rdx
	imulq	%rsi, %rax
	imulq	%rcx, %rdx
	leaq	(%rax,%rdx), %r14
	cmpq	%r9, %r14
	je	.L247
.L244:
	movq	(%rsp), %rbx
	.cfi_remember_state
	.cfi_restore 3
	movq	8(%rsp), %rbp
	.cfi_restore 6
	movq	16(%rsp), %r14
	.cfi_restore 14
	jmp	.L205
.L247:
	.cfi_restore_state
	imulq	%rbp, %rax
	imulq	%rdi, %rdx
	addq	%rdx, %rax
	cmpq	%rbx, %rax
	jne	.L244
	movl	%ebp, (%r11)
	movq	(%rsp), %rbx
	.cfi_restore 3
	movl	$2, %eax
	movq	8(%rsp), %rbp
	.cfi_restore 6
	movq	16(%rsp), %r14
	.cfi_restore 14
	movl	%esi, (%r10)
	movl	%edi, (%r15)
	movl	%ecx, (%r8)
	jmp	.L201
	.cfi_endproc
.LFE7305:
	.size	sqm_solve, .-sqm_solve
	.p2align 4
	.type	sqm_write, @function
sqm_write:
.LFB7306:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movl	$-1, %r11d
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%r15
	pushq	%r14
	pushq	%r13
	pushq	%r12
	pushq	%rbx
	.cfi_offset 15, -24
	.cfi_offset 14, -32
	.cfi_offset 13, -40
	.cfi_offset 12, -48
	.cfi_offset 3, -56
	movslq	%esi, %rbx
	andq	$-32, %rsp
	subq	$256, %rsp
	movq	%fs:40, %r10
	movq	%r10, 248(%rsp)
	movq	%rcx, %r10
	cmpl	$1023, %ebx
	jg	.L249
	movslq	%ebx, %rax
	leaq	sqm_slot_of(%rip), %rcx
	movl	(%rcx,%rax,4), %r11d
.L249:
	vmovdqu	(%r10), %xmm13
	vmovdqu	16(%r10), %xmm12
	vpsrldq	$4, %xmm13, %xmm8
	vpsrldq	$8, %xmm13, %xmm10
	vpmovzxbd	%xmm13, %xmm11
	vpmulld	.LC0(%rip), %xmm11, %xmm7
	vpsrldq	$12, %xmm13, %xmm9
	vpmovzxbd	%xmm10, %xmm10
	vpmovzxbd	%xmm8, %xmm8
	vpmulld	.LC1(%rip), %xmm8, %xmm5
	vpmovzxbd	%xmm9, %xmm9
	vpsrldq	$8, %xmm12, %xmm1
	vpaddd	%xmm11, %xmm8, %xmm8
	vpmulld	.LC3(%rip), %xmm9, %xmm4
	vpsrldq	$12, %xmm12, %xmm0
	vpmovzxbd	%xmm1, %xmm1
	vpaddd	%xmm10, %xmm9, %xmm9
	vpmulld	.LC2(%rip), %xmm10, %xmm6
	vpmovzxbd	%xmm0, %xmm0
	vpsrldq	$4, %xmm12, %xmm3
	vpmovzxbd	%xmm12, %xmm2
	vpmulld	.LC3(%rip), %xmm4, %xmm10
	vpmovzxbd	%xmm3, %xmm3
	vpaddd	%xmm1, %xmm9, %xmm9
	vpaddd	%xmm0, %xmm8, %xmm8
	vpmulld	.LC6(%rip), %xmm1, %xmm1
	vpaddd	%xmm2, %xmm9, %xmm9
	vpaddd	%xmm3, %xmm8, %xmm8
	vpmulld	.LC4(%rip), %xmm2, %xmm2
	vpmulld	.LC5(%rip), %xmm3, %xmm3
	vpmulld	.LC7(%rip), %xmm0, %xmm0
	vpaddd	%xmm8, %xmm9, %xmm11
	vpaddd	%xmm6, %xmm4, %xmm9
	vpmulld	.LC13(%rip), %xmm4, %xmm4
	vpaddd	%xmm7, %xmm5, %xmm8
	vpaddd	%xmm3, %xmm9, %xmm9
	vmovdqa	%xmm11, 32(%rsp)
	vpaddd	%xmm2, %xmm8, %xmm8
	vpaddd	%xmm0, %xmm9, %xmm9
	vpaddd	%xmm1, %xmm8, %xmm8
	vpaddd	%xmm8, %xmm9, %xmm14
	vpmulld	.LC0(%rip), %xmm7, %xmm9
	vpmulld	.LC1(%rip), %xmm5, %xmm8
	vpaddd	%xmm8, %xmm9, %xmm8
	vpmulld	.LC6(%rip), %xmm1, %xmm9
	vpaddd	%xmm9, %xmm8, %xmm9
	vmovdqa	%xmm14, 48(%rsp)
	vpmulld	.LC4(%rip), %xmm2, %xmm8
	vpmulld	.LC8(%rip), %xmm7, %xmm7
	vpaddd	%xmm8, %xmm9, %xmm9
	vpmulld	.LC2(%rip), %xmm6, %xmm8
	vpaddd	%xmm10, %xmm8, %xmm10
	vpmulld	.LC9(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	.LC7(%rip), %xmm0, %xmm8
	vpaddd	%xmm8, %xmm10, %xmm8
	vpmulld	.LC12(%rip), %xmm6, %xmm6
	vpaddd	%xmm4, %xmm6, %xmm4
	vpmulld	.LC5(%rip), %xmm3, %xmm10
	vpmulld	.LC10(%rip), %xmm1, %xmm1
	vpaddd	%xmm10, %xmm8, %xmm8
	vpaddd	%xmm1, %xmm5, %xmm1
	vpmulld	.LC11(%rip), %xmm2, %xmm2
	vpmulld	.LC14(%rip), %xmm0, %xmm0
	vpaddd	%xmm8, %xmm9, %xmm15
	vpaddd	%xmm2, %xmm1, %xmm2
	vmovdqu	32(%r10), %xmm1
	vpmulld	.LC15(%rip), %xmm3, %xmm3
	vpaddd	%xmm0, %xmm4, %xmm0
	vmovdqa	%xmm15, 64(%rsp)
	vmovdqa	.LC16(%rip), %xmm15
	vpaddd	%xmm3, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm6
	vpmovzxbd	%xmm1, %xmm8
	vpaddd	%xmm0, %xmm2, %xmm7
	vpsrldq	$4, %xmm1, %xmm2
	vpmovzxbd	%xmm6, %xmm6
	vmovdqa	%xmm7, 80(%rsp)
	vpmulld	%xmm15, %xmm8, %xmm7
	vpsrldq	$12, %xmm1, %xmm1
	vpmovzxbd	%xmm2, %xmm2
	vpmovzxbd	%xmm1, %xmm1
	vmovdqa	%xmm7, 112(%rsp)
	vmovdqu	48(%r10), %xmm0
	vpmulld	.LC17(%rip), %xmm2, %xmm9
	vpmulld	.LC19(%rip), %xmm1, %xmm7
	vpaddd	%xmm8, %xmm2, %xmm2
	vpaddd	%xmm6, %xmm1, %xmm1
	vmovdqa	.LC18(%rip), %xmm14
	vmovdqa	.LC20(%rip), %xmm8
	vpsrldq	$4, %xmm0, %xmm3
	vpsrldq	$8, %xmm0, %xmm4
	vpmovzxbd	%xmm0, %xmm5
	vmovdqa	%xmm9, 96(%rsp)
	vpmovzxbd	%xmm3, %xmm3
	vpsrldq	$12, %xmm0, %xmm0
	vpmovzxbd	%xmm4, %xmm4
	vpmulld	112(%rsp), %xmm15, %xmm15
	vpaddd	%xmm3, %xmm2, %xmm2
	vpmovzxbd	%xmm0, %xmm0
	vpaddd	%xmm5, %xmm1, %xmm1
	vpmulld	.LC21(%rip), %xmm3, %xmm3
	vpmulld	%xmm14, %xmm6, %xmm10
	vpaddd	%xmm1, %xmm2, %xmm1
	vpaddd	%xmm0, %xmm4, %xmm2
	vpmulld	.LC22(%rip), %xmm4, %xmm4
	vpaddd	%xmm11, %xmm2, %xmm2
	vpmulld	%xmm8, %xmm5, %xmm5
	vpaddd	112(%rsp), %xmm9, %xmm6
	vpmulld	.LC17(%rip), %xmm9, %xmm9
	vpaddd	%xmm2, %xmm1, %xmm1
	vmovdqa	.LC23(%rip), %xmm2
	vpaddd	%xmm9, %xmm15, %xmm9
	vpaddd	%xmm4, %xmm6, %xmm6
	vpmulld	%xmm2, %xmm0, %xmm0
	vpmulld	%xmm14, %xmm10, %xmm14
	vpaddd	%xmm10, %xmm7, %xmm11
	vpmulld	.LC24(%rip), %xmm10, %xmm10
	vpmulld	%xmm8, %xmm5, %xmm8
	vpmulld	%xmm2, %xmm0, %xmm2
	vpaddd	%xmm0, %xmm11, %xmm11
	vpmulld	.LC30(%rip), %xmm0, %xmm0
	vpaddd	%xmm6, %xmm11, %xmm11
	vpaddd	%xmm3, %xmm5, %xmm6
	vpmulld	.LC29(%rip), %xmm5, %xmm5
	vpaddd	48(%rsp), %xmm6, %xmm6
	vpaddd	%xmm8, %xmm9, %xmm8
	vpmulld	.LC19(%rip), %xmm7, %xmm9
	vpmulld	.LC25(%rip), %xmm7, %xmm7
	vpaddd	%xmm9, %xmm14, %xmm9
	vpaddd	%xmm7, %xmm10, %xmm7
	vpaddd	%xmm6, %xmm11, %xmm6
	vpmulld	.LC21(%rip), %xmm3, %xmm11
	vpaddd	%xmm11, %xmm9, %xmm9
	vmovdqa	112(%rsp), %xmm11
	vpmulld	.LC26(%rip), %xmm3, %xmm3
	vpaddd	%xmm9, %xmm8, %xmm9
	vpmulld	.LC22(%rip), %xmm4, %xmm8
	vpaddd	%xmm8, %xmm2, %xmm2
	vpaddd	64(%rsp), %xmm2, %xmm2
	vpaddd	%xmm3, %xmm7, %xmm3
	vpmulld	.LC27(%rip), %xmm11, %xmm7
	vpmulld	.LC31(%rip), %xmm4, %xmm4
	vpaddd	%xmm4, %xmm0, %xmm0
	vpaddd	80(%rsp), %xmm0, %xmm0
	vpaddd	%xmm2, %xmm9, %xmm2
	vmovdqa	96(%rsp), %xmm9
	vpmulld	.LC28(%rip), %xmm9, %xmm8
	vpaddd	%xmm8, %xmm7, %xmm8
	vpaddd	%xmm5, %xmm8, %xmm8
	vpaddd	%xmm8, %xmm3, %xmm8
	vpunpckhqdq	%xmm1, %xmm1, %xmm3
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm8, %xmm0
	vpshufd	$177, %xmm1, %xmm3
	vpaddd	%xmm1, %xmm3, %xmm3
	vpunpckhqdq	%xmm6, %xmm6, %xmm1
	vpaddd	%xmm1, %xmm6, %xmm1
	vmovd	%xmm3, %esi
	vpshufd	$177, %xmm1, %xmm3
	movq	%rsi, 128(%rsp)
	vpaddd	%xmm1, %xmm3, %xmm3
	vpunpckhqdq	%xmm2, %xmm2, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm1
	vmovd	%xmm3, %ecx
	vpshufd	$177, %xmm1, %xmm2
	movq	%rcx, 136(%rsp)
	vpaddd	%xmm1, %xmm2, %xmm2
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm2, %r8d
	vpshufd	$177, %xmm0, %xmm1
	movq	%r8, 144(%rsp)
	vpaddd	%xmm0, %xmm1, %xmm1
	vmovd	%xmm1, %r9d
	movq	%r9, 152(%rsp)
	testl	%r11d, %r11d
	js	.L250
	vmovdqa	128(%rsp), %ymm0
	movl	%r11d, %r12d
	movzbl	%r11b, %r11d
	sarl	$8, %r12d
	movq	%r12, %rbx
	salq	$5, %rbx
	addq	%r11, %rbx
	leaq	512(%rbx), %rax
	salq	$5, %rax
	addq	%rdi, %rax
	vpxor	(%rax), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L251
	addq	$1, 41256(%rdi)
	xorl	%esi, %esi
	vzeroupper
.L248:
	movq	248(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L310
	leaq	-40(%rbp), %rsp
	movl	%esi, %eax
	popq	%rbx
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%r15
	popq	%rbp
	.cfi_remember_state
	.cfi_def_cfa 7, 8
	ret
	.p2align 4,,10
	.p2align 3
.L251:
	.cfi_restore_state
	vmovdqa	128(%rsp), %ymm0
	movq	%rbx, %r15
	vpsubq	(%rax), %ymm0, %ymm0
	salq	$6, %r15
	leaq	(%rdi,%r15), %rax
	vmovq	%xmm0, %r14
	movq	%r15, 96(%rsp)
	movq	%rax, 112(%rsp)
	testq	%r14, %r14
	je	.L256
	vpextrq	$1, %xmm0, %r13
	leaq	255(%r14), %rax
	vextracti128	$0x1, %ymm0, %xmm0
	vmovq	%xmm0, %r15
	vmovq	%xmm0, 80(%rsp)
	vpextrq	$1, %xmm0, 64(%rsp)
	cmpq	$510, %rax
	ja	.L257
	movq	%r13, %rax
	cqto
	idivq	%r14
	testq	%rdx, %rdx
	jne	.L257
	leaq	-1(%rax), %rdx
	cmpq	$63, %rdx
	ja	.L257
	movq	%rax, %rdx
	imulq	%rax, %rdx
	imulq	%r14, %rdx
	cmpq	%rdx, %r15
	jne	.L257
	movq	%r15, %rdx
	imulq	%rax, %rdx
	cmpq	%rdx, 64(%rsp)
	jne	.L257
	movq	112(%rsp), %rdx
	leal	-1(%rax), %r13d
	movq	%r13, %rax
	addq	%r13, %rdx
	movzbl	(%r10,%r13), %r13d
	movzbl	(%rdx), %r15d
	addq	$1, 41288(%rdi)
	addl	%r14d, %r15d
	cmpb	%r13b, %r15b
	jne	.L259
	addb	%r14b, (%rdx)
	movq	41296(%rdi), %rsi
	movslq	%r14d, %rcx
	leaq	1(%rsi), %rdx
	movl	$1, %esi
.L273:
	movq	%rdx, 41296(%rdi)
	movq	%r12, %rdx
	movq	%rcx, %r10
	vmovq	%rcx, %xmm5
	vmovdqa	128(%rsp), %ymm0
	salq	$5, %rdx
	addq	%r11, %rdx
	movq	%rdx, %r8
	addq	%rdx, %rdx
	salq	$5, %r8
	vmovdqu	%ymm0, 16384(%rdi,%r8)
	movl	%eax, %r8d
	sarl	$5, %eax
	andl	$31, %r8d
	leaq	768(%rax,%rdx), %rax
	addq	$1, %r8
	salq	$5, %rax
	imulq	%r8, %r10
	movq	%r10, %r9
	vpinsrq	$1, %r10, %xmm5, %xmm0
	imulq	%r8, %r9
	imulq	%r9, %r8
	vmovq	%r9, %xmm4
	vpinsrq	$1, %r8, %xmm4, %xmm1
	vinserti128	$0x1, %xmm1, %ymm0, %ymm0
	vpaddq	(%rdi,%rax), %ymm0, %ymm0
	vmovdqu	%ymm0, (%rdi,%rax)
	cmpl	$2, %esi
	jne	.L263
	movl	24(%rsp), %eax
	subl	$1, %eax
	movl	%eax, %ecx
	sarl	$5, %eax
	andl	$31, %ecx
	leaq	(%rax,%rbx,2), %rsi
	addq	%rax, %rdx
	leaq	1(%rcx), %r8
	movslq	16(%rsp), %rcx
	salq	$5, %rsi
	salq	$5, %rdx
	addq	%rcx, 24576(%rdi,%rsi)
	leaq	(%rdi,%rdx), %rax
	imulq	%r8, %rcx
	addq	%rcx, 24584(%rax)
	imulq	%r8, %rcx
	addq	%rcx, 24592(%rax)
	movq	%rcx, %rdx
	imulq	%r8, %rdx
	addq	%rdx, 24600(%rax)
.L263:
	addq	$1, 41264(%rdi)
	jmp	.L264
	.p2align 4,,10
	.p2align 3
.L257:
	movq	80(%rsp), %rdx
	movq	%r13, %rax
	imulq	%r13, %rax
	imulq	%r14, %rdx
	movq	%rdx, %r15
	subq	%rax, %r15
	jne	.L311
.L256:
	vpsrldq	$4, %xmm13, %xmm2
	vpsrldq	$8, %xmm13, %xmm8
	vpmovzxbd	%xmm13, %xmm9
	vpmulld	.LC0(%rip), %xmm9, %xmm1
	vpsrldq	$12, %xmm13, %xmm0
	vpmovzxbd	%xmm8, %xmm8
	vpmovzxbd	%xmm2, %xmm2
	vpmulld	.LC1(%rip), %xmm2, %xmm7
	vpmovzxbd	%xmm0, %xmm0
	vpsrldq	$8, %xmm12, %xmm4
	vpaddd	%xmm9, %xmm2, %xmm2
	vpmulld	.LC3(%rip), %xmm0, %xmm3
	vpsrldq	$12, %xmm12, %xmm11
	vpsrldq	$4, %xmm12, %xmm5
	vpmovzxbd	%xmm4, %xmm4
	vpmulld	.LC2(%rip), %xmm8, %xmm10
	vpmovzxbd	%xmm11, %xmm11
	vpaddd	%xmm8, %xmm0, %xmm0
	vpmovzxbd	%xmm12, %xmm6
	vpmulld	.LC3(%rip), %xmm3, %xmm9
	vpmovzxbd	%xmm5, %xmm5
	vpaddd	%xmm11, %xmm2, %xmm2
	vpaddd	%xmm4, %xmm0, %xmm0
	vpmulld	.LC7(%rip), %xmm11, %xmm11
	vpaddd	%xmm5, %xmm2, %xmm2
	vpaddd	%xmm6, %xmm0, %xmm0
	vpmulld	.LC5(%rip), %xmm5, %xmm5
	vpmulld	.LC4(%rip), %xmm6, %xmm6
	vpaddd	%xmm0, %xmm2, %xmm0
	vpaddd	%xmm10, %xmm3, %xmm8
	vpmulld	.LC6(%rip), %xmm4, %xmm4
	vpmulld	.LC1(%rip), %xmm7, %xmm12
	vpaddd	%xmm1, %xmm7, %xmm2
	vpaddd	%xmm5, %xmm8, %xmm8
	vpmulld	.LC13(%rip), %xmm3, %xmm3
	vpmulld	.LC9(%rip), %xmm7, %xmm7
	vpaddd	%xmm6, %xmm2, %xmm2
	vpaddd	%xmm11, %xmm8, %xmm8
	vpaddd	%xmm4, %xmm2, %xmm2
	vpaddd	%xmm2, %xmm8, %xmm2
	vpmulld	.LC2(%rip), %xmm10, %xmm8
	vpaddd	%xmm9, %xmm8, %xmm9
	vpmulld	.LC7(%rip), %xmm11, %xmm8
	vpmulld	.LC12(%rip), %xmm10, %xmm10
	vpaddd	%xmm8, %xmm9, %xmm8
	vpaddd	%xmm3, %xmm10, %xmm3
	vpmulld	.LC5(%rip), %xmm5, %xmm9
	vpmulld	.LC14(%rip), %xmm11, %xmm11
	vpaddd	%xmm9, %xmm8, %xmm9
	vpmulld	.LC0(%rip), %xmm1, %xmm8
	vpmulld	.LC8(%rip), %xmm1, %xmm1
	vpaddd	%xmm7, %xmm1, %xmm1
	vpaddd	%xmm12, %xmm8, %xmm12
	vpmulld	.LC6(%rip), %xmm4, %xmm8
	vpmulld	.LC10(%rip), %xmm4, %xmm4
	vpaddd	%xmm11, %xmm3, %xmm3
	vpaddd	%xmm4, %xmm1, %xmm1
	vpmulld	.LC15(%rip), %xmm5, %xmm5
	vpaddd	%xmm8, %xmm12, %xmm8
	vpaddd	%xmm5, %xmm3, %xmm3
	vpmulld	.LC4(%rip), %xmm6, %xmm12
	vpmulld	.LC11(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm1, %xmm1
	vpaddd	%xmm12, %xmm8, %xmm8
	vpaddd	%xmm1, %xmm3, %xmm1
	vpunpckhqdq	%xmm0, %xmm0, %xmm3
	vpaddd	%xmm8, %xmm9, %xmm9
	vpaddd	%xmm3, %xmm0, %xmm0
	vpshufd	$177, %xmm0, %xmm3
	vpaddd	%xmm0, %xmm3, %xmm0
	vmovd	%xmm0, %r13d
	vpunpckhqdq	%xmm2, %xmm2, %xmm0
	vpaddd	%xmm0, %xmm2, %xmm2
	subq	%r13, %rsi
	movq	%r13, 160(%rsp)
	vpshufd	$177, %xmm2, %xmm0
	movq	%rsi, 192(%rsp)
	vpaddd	%xmm2, %xmm0, %xmm0
	vmovd	%xmm0, %ebx
	vpunpckhqdq	%xmm9, %xmm9, %xmm0
	vpaddd	%xmm0, %xmm9, %xmm9
	subq	%rbx, %rcx
	movq	%rbx, 168(%rsp)
	movq	%rsi, %rbx
	vpshufd	$177, %xmm9, %xmm0
	salq	$5, %rbx
	vpaddd	%xmm9, %xmm0, %xmm0
	vmovd	%xmm0, %edx
	vpunpckhqdq	%xmm1, %xmm1, %xmm0
	subq	%rdx, %r8
	movq	%rdx, 176(%rsp)
	movq	%rcx, %rdx
	vpaddd	%xmm0, %xmm1, %xmm1
	subq	%rbx, %rdx
	vpshufd	$177, %xmm1, %xmm0
	movq	%rcx, %rbx
	salq	$10, %rcx
	movq	%rdx, 200(%rsp)
	movq	%rsi, %rdx
	vpaddd	%xmm1, %xmm0, %xmm0
	salq	$6, %rbx
	salq	$10, %rdx
	vmovd	%xmm0, %eax
	salq	$15, %rsi
	addq	%r8, %rdx
	salq	$5, %r8
	subq	%rax, %r9
	movq	%rax, 184(%rsp)
	subq	%rbx, %rdx
	subq	%r8, %rcx
	subq	%rsi, %r9
	xorl	%r8d, %r8d
	movq	%rdx, 208(%rsp)
	leaq	(%rcx,%rcx,2), %rdx
	leaq	(%rdx,%r9), %rax
	movq	%rax, 216(%rsp)
	vmovdqa	160(%rsp), %ymm0
	movq	96(%rsp), %rax
	vpxor	24576(%rdi,%rax), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	vmovdqa	192(%rsp), %ymm0
	vpxor	24608(%rdi,%rax), %ymm0, %ymm0
	setne	%r8b
	vptest	%ymm0, %ymm0
	setne	%al
	cmpb	%r8b, %al
	je	.L269
	addq	$32, 41288(%rdi)
	xorl	$1, %r8d
	xorl	%eax, %eax
	xorl	%esi, %esi
	movq	112(%rsp), %rcx
	sall	$5, %r8d
	addq	%r8, %rcx
	addq	%r10, %r8
	.p2align 5
	.p2align 4
	.p2align 3
.L271:
	movzbl	(%r8,%rax), %edx
	cmpb	%dl, (%rcx,%rax)
	je	.L270
	movb	%dl, (%rcx,%rax)
	addl	$1, %esi
.L270:
	addq	$1, %rax
	cmpq	$32, %rax
	jne	.L271
	movslq	%esi, %rsi
	addq	$1, 41272(%rdi)
	addq	%rsi, 41296(%rdi)
.L272:
	vmovdqa	128(%rsp), %ymm0
	movq	%r12, %rax
	salq	$5, %rax
	leaq	(%rax,%r11), %rdx
	salq	$5, %rdx
	vmovdqu	%ymm0, 16384(%rdi,%rdx)
	leaq	(%rax,%r11), %rdx
	vmovdqa	160(%rsp), %ymm0
	salq	$6, %rdx
	vmovdqu	%ymm0, 24576(%rdi,%rdx)
	vmovdqa	192(%rsp), %ymm0
	vmovdqu	%ymm0, 24608(%rdi,%rdx)
.L264:
	xorl	%esi, %esi
	vzeroupper
	jmp	.L248
	.p2align 4,,10
	.p2align 3
.L250:
	vmovdqa	32(%rsp), %xmm5
	vmovdqa	48(%rsp), %xmm4
	vmovdqa	80(%rsp), %xmm7
	vpunpckhqdq	%xmm5, %xmm5, %xmm0
	vpaddd	%xmm5, %xmm0, %xmm0
	vmovdqa	64(%rsp), %xmm5
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	vmovd	%xmm0, %r11d
	vpunpckhqdq	%xmm4, %xmm4, %xmm0
	vpaddd	%xmm4, %xmm0, %xmm0
	subq	%r11, %rsi
	movq	%r11, 160(%rsp)
	vpshufd	$177, %xmm0, %xmm1
	movq	%rsi, %r11
	movq	%rsi, 192(%rsp)
	vpaddd	%xmm0, %xmm1, %xmm0
	salq	$5, %r11
	vmovd	%xmm0, %eax
	vpunpckhqdq	%xmm5, %xmm5, %xmm0
	vpaddd	%xmm5, %xmm0, %xmm0
	subq	%rax, %rcx
	movq	%rax, 168(%rsp)
	vpshufd	$177, %xmm0, %xmm1
	movq	%rcx, %rax
	vpaddd	%xmm0, %xmm1, %xmm0
	subq	%r11, %rax
	movq	%rcx, %r11
	salq	$10, %rcx
	vmovd	%xmm0, %r13d
	vpunpckhqdq	%xmm7, %xmm7, %xmm0
	movq	%rax, 200(%rsp)
	movq	%rsi, %rax
	vpaddd	%xmm7, %xmm0, %xmm0
	salq	$10, %rax
	subq	%r13, %r8
	salq	$6, %r11
	vpshufd	$177, %xmm0, %xmm1
	addq	%r8, %rax
	salq	$5, %r8
	movq	%r13, 176(%rsp)
	vpaddd	%xmm0, %xmm1, %xmm0
	subq	%r11, %rax
	subq	%r8, %rcx
	salq	$15, %rsi
	vmovd	%xmm0, %r12d
	movq	%rax, 208(%rsp)
	leaq	(%rcx,%rcx,2), %rax
	movl	%ebx, %ecx
	subq	%r12, %r9
	andl	$31, %ecx
	movq	%r12, 184(%rsp)
	subq	%rsi, %r9
	addq	%r9, %rax
	movq	%rax, 216(%rsp)
	leaq	SQM_SCATLT(%rip), %rax
	movl	(%rax,%rcx,4), %eax
	movq	%rax, %rcx
	cmpl	$31, 41216(%rdi,%rax,4)
	jle	.L255
	leal	1(%rax), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%rdi,%rax,4)
	jle	.L281
	leal	2(%rcx), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%rdi,%rax,4)
	jle	.L281
	leal	3(%rcx), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%rdi,%rax,4)
	jle	.L281
	leal	4(%rcx), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%rdi,%rax,4)
	jle	.L281
	leal	5(%rcx), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%rdi,%rax,4)
	jle	.L281
	leal	6(%rcx), %esi
	movl	%esi, %eax
	andl	$7, %eax
	cmpl	$31, 41216(%rdi,%rax,4)
	jle	.L281
	leal	7(%rcx), %eax
	movl	$-1, %esi
	movl	%eax, %ecx
	andl	$7, %eax
	andl	$7, %ecx
	cmpl	$31, 41216(%rdi,%rax,4)
	jg	.L248
.L255:
	leaq	(%rdi,%rax,4), %r8
	salq	$5, %rax
	vmovdqu	(%r10), %ymm0
	sall	$8, %ecx
	movslq	41216(%r8), %r12
	leaq	(%rax,%r12), %r11
	addq	%rdi, %rax
	orl	%r12d, %ecx
	movq	%r11, %rsi
	salq	$6, %rsi
	vmovdqu	%ymm0, (%rdi,%rsi)
	vmovdqu	32(%r10), %ymm0
	movq	%r11, %r10
	salq	$5, %r10
	vmovdqu	%ymm0, 32(%rdi,%rsi)
	vmovdqa	128(%rsp), %ymm0
	vmovdqu	%ymm0, 16384(%rdi,%r10)
	movq	%r11, %r10
	vmovdqa	160(%rsp), %ymm0
	salq	$6, %r10
	vmovdqu	%ymm0, 24576(%rdi,%r10)
	vmovdqa	192(%rsp), %ymm0
	vmovdqu	%ymm0, 24608(%rdi,%rsi)
	movb	$1, 40960(%r12,%rax)
	leaq	sqm_item_at(%rip), %rax
	movl	%edx, (%rax,%r11,4)
	leaq	sqm_slot_of(%rip), %rax
	addl	$1, 41216(%r8)
	movl	%ecx, (%rax,%rbx,4)
	addl	$1, 41248(%rdi)
	addq	$1, 41280(%rdi)
	addq	$64, 41296(%rdi)
	jmp	.L264
	.p2align 4,,10
	.p2align 3
.L311:
	movq	64(%rsp), %rax
	movq	80(%rsp), %rdx
	movq	%r15, 48(%rsp)
	imulq	%r13, %rdx
	imulq	%r14, %rax
	subq	%rdx, %rax
	cqto
	idivq	%r15
	movq	%rax, 32(%rsp)
	testq	%rdx, %rdx
	jne	.L256
	movq	80(%rsp), %r15
	movq	64(%rsp), %rax
	movq	%r15, %rdx
	imulq	%r13, %rax
	imulq	%r15, %rdx
	subq	%rdx, %rax
	cqto
	idivq	48(%rsp)
	testq	%rdx, %rdx
	jne	.L256
	movq	32(%rsp), %r15
	negq	%rax
	movq	%r15, %rdx
	imulq	%r15, %rdx
	leaq	(%rdx,%rax,4), %rdx
	testq	%rdx, %rdx
	jle	.L256
	movl	$1, %eax
	cmpq	$1, %rdx
	je	.L260
	movq	96(%rsp), %r15
	movq	%rsi, 48(%rsp)
	movq	%rdx, %rsi
	.p2align 4
	.p2align 4
	.p2align 3
.L261:
	addq	$1, %rax
	movq	%rax, %rdx
	imulq	%rax, %rdx
	cmpq	%rdx, %rsi
	jg	.L261
	movq	%r15, 96(%rsp)
	movq	48(%rsp), %rsi
	jne	.L256
.L260:
	movq	32(%rsp), %r15
	leaq	(%rax,%r15), %rdx
	testb	$1, %dl
	jne	.L256
	subq	%rax, %r15
	leaq	-2(%r15), %rax
	cmpq	$127, %rax
	ja	.L256
	leaq	-2(%rdx), %rax
	cmpq	$127, %rax
	ja	.L256
	movq	%rdx, %rax
	sarq	%r15
	sarq	%rax
	movq	%r15, 24(%rsp)
	movq	%rax, 32(%rsp)
	cmpq	%r15, %rax
	je	.L256
	movq	%r15, %rdx
	movq	%r13, %rax
	movq	32(%rsp), %r13
	imulq	%r14, %rdx
	subq	%r15, %r13
	subq	%rdx, %rax
	cqto
	idivq	%r13
	testq	%rdx, %rdx
	jne	.L256
	movq	%rax, %rdx
	addq	$255, %rax
	cmpq	$510, %rax
	ja	.L256
	subq	%rdx, %r14
	leaq	255(%r14), %rax
	movq	%r14, 16(%rsp)
	cmpq	$510, %rax
	ja	.L256
	movq	%rdx, 48(%rsp)
	testq	%rdx, %rdx
	je	.L256
	testq	%r14, %r14
	je	.L256
	movq	32(%rsp), %r13
	movq	%r13, %rdx
	imulq	%r13, %rdx
	movq	%rdx, %rax
	movq	48(%rsp), %rdx
	imulq	%rax, %rdx
	movq	%r15, %rax
	imulq	%r15, %rax
	imulq	%rax, %r14
	leaq	(%rdx,%r14), %rax
	cmpq	%rax, 80(%rsp)
	jne	.L256
	movq	%r15, %rax
	imulq	32(%rsp), %rdx
	imulq	%r14, %rax
	addq	%rax, %rdx
	cmpq	%rdx, 64(%rsp)
	jne	.L256
	movl	32(%rsp), %eax
	movq	112(%rsp), %r14
	movzbl	48(%rsp), %r15d
	leal	-1(%rax), %edx
	leaq	(%r14,%rdx), %r13
	movq	%rdx, %rax
	movzbl	(%r10,%rdx), %edx
	addb	0(%r13), %r15b
	movq	%r13, 64(%rsp)
	movb	%dl, 80(%rsp)
	movq	41288(%rdi), %rdx
	leaq	1(%rdx), %r13
	movq	%r13, 41288(%rdi)
	cmpb	80(%rsp), %r15b
	jne	.L259
	movq	24(%rsp), %r13
	addq	$2, %rdx
	movl	%r13d, 24(%rsp)
	subl	$1, %r13d
	leaq	(%r14,%r13), %r15
	movzbl	16(%rsp), %r14d
	addb	(%r15), %r14b
	movq	%r15, 80(%rsp)
	movl	%r14d, %r15d
	movzbl	(%r10,%r13), %r14d
	movq	%rdx, 41288(%rdi)
	cmpb	%r14b, %r15b
	je	.L312
.L259:
	addq	$1, 41304(%rdi)
	vmovdqu	(%r10), %xmm13
	vmovdqu	16(%r10), %xmm12
	jmp	.L256
.L281:
	andl	$7, %esi
	movl	%esi, %ecx
	jmp	.L255
.L269:
	vmovdqu	(%r10), %ymm0
	movq	112(%rsp), %rax
	vmovdqu	%ymm0, (%rax)
	vmovdqu	32(%r10), %ymm0
	vmovdqu	%ymm0, 32(%rax)
	vmovdqa	.LC32(%rip), %xmm0
	vpaddq	41280(%rdi), %xmm0, %xmm0
	addq	$64, 41296(%rdi)
	vmovdqu	%xmm0, 41280(%rdi)
	jmp	.L272
.L312:
	movq	48(%rsp), %rdx
	movq	64(%rsp), %r14
	movq	16(%rsp), %rsi
	addb	%dl, (%r14)
	movslq	%edx, %rcx
	movq	80(%rsp), %rdx
	addq	$1, 41296(%rdi)
	movl	%esi, 16(%rsp)
	addb	%sil, (%rdx)
	movq	41296(%rdi), %rsi
	leaq	1(%rsi), %rdx
	movl	$2, %esi
	jmp	.L273
.L310:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE7306:
	.size	sqm_write, .-sqm_write
	.p2align 4
	.type	sqm_sweep, @function
sqm_sweep:
.LFB7307:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	leaq	16384(%rdi), %r11
	xorl	%r9d, %r9d
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%r15
	pushq	%r14
	.cfi_offset 15, -24
	.cfi_offset 14, -32
	xorl	%r14d, %r14d
	pushq	%r13
	pushq	%r12
	pushq	%rbx
	.cfi_offset 13, -40
	.cfi_offset 12, -48
	.cfi_offset 3, -56
	movq	%rdi, %rbx
	andq	$-32, %rsp
	subq	$416, %rsp
	movq	%rdi, 40(%rsp)
	movq	%fs:40, %r15
	movq	%r15, 408(%rsp)
	movq	%rsi, %r15
.L314:
	movl	%r9d, 36(%rsp)
	movq	%r9, %rcx
	movl	%r9d, %r8d
	movq	%r11, %rdi
	movq	%r11, 24(%rsp)
	salq	$11, %rcx
	sall	$5, %r8d
	xorl	%esi, %esi
	movq	%r9, 16(%rsp)
	addq	40(%rsp), %rcx
	.p2align 4
	.p2align 3
.L328:
	cmpb	$0, 40960(%rbx,%rsi)
	je	.L327
	testq	%r15, %r15
	je	.L316
	movl	%r8d, %eax
	movb	$0, (%r15,%rax)
.L316:
	vmovdqu	(%rcx), %xmm7
	vmovdqu	16(%rcx), %xmm8
	vpmovzxbd	%xmm7, %xmm5
	vpsrldq	$8, %xmm8, %xmm1
	vpmovzxbd	%xmm8, %xmm0
	vpmulld	.LC0(%rip), %xmm5, %xmm6
	vpsrldq	$4, %xmm7, %xmm11
	vpsrldq	$8, %xmm7, %xmm2
	vpmovzxbd	%xmm1, %xmm1
	vmovdqa	%xmm6, 336(%rsp)
	vmovdqu	32(%rcx), %xmm6
	vpsrldq	$4, %xmm8, %xmm10
	vpsrldq	$12, %xmm7, %xmm7
	vpmulld	.LC6(%rip), %xmm1, %xmm13
	vpsrldq	$12, %xmm8, %xmm8
	vpmovzxbd	%xmm11, %xmm11
	vpmovzxbd	%xmm7, %xmm7
	vmovdqa	%xmm13, 256(%rsp)
	vpsrldq	$8, %xmm6, %xmm13
	vpmovzxbd	%xmm8, %xmm8
	vpmulld	.LC1(%rip), %xmm11, %xmm4
	vmovdqa	%xmm0, 192(%rsp)
	vpmovzxbd	%xmm2, %xmm2
	vpmovzxbd	%xmm6, %xmm9
	vpmovzxbd	%xmm10, %xmm10
	vpmulld	.LC4(%rip), %xmm0, %xmm0
	vmovdqa	%xmm4, 320(%rsp)
	vpmovzxbd	%xmm13, %xmm4
	vpmulld	.LC2(%rip), %xmm2, %xmm14
	vpmulld	.LC7(%rip), %xmm8, %xmm12
	vmovdqa	%xmm0, 288(%rsp)
	vmovdqu	48(%rcx), %xmm0
	vpaddd	%xmm8, %xmm1, %xmm1
	vpaddd	%xmm11, %xmm5, %xmm5
	vpaddd	%xmm7, %xmm2, %xmm2
	vpaddd	%xmm10, %xmm5, %xmm5
	vmovdqa	%xmm4, 160(%rsp)
	vpmulld	.LC16(%rip), %xmm9, %xmm13
	vpaddd	160(%rsp), %xmm1, %xmm1
	vpaddd	192(%rsp), %xmm2, %xmm2
	vmovdqa	%xmm12, 240(%rsp)
	vpsrldq	$4, %xmm6, %xmm12
	vpsrldq	$12, %xmm6, %xmm6
	vpmovzxbd	%xmm12, %xmm12
	vpmulld	.LC3(%rip), %xmm7, %xmm3
	vmovdqa	%xmm9, 176(%rsp)
	vpmovzxbd	%xmm6, %xmm6
	vpaddd	%xmm12, %xmm1, %xmm1
	vpmulld	.LC18(%rip), %xmm4, %xmm9
	vpaddd	176(%rsp), %xmm5, %xmm5
	vpmulld	.LC19(%rip), %xmm6, %xmm4
	vpaddd	%xmm6, %xmm2, %xmm2
	vmovdqa	%xmm3, 304(%rsp)
	vpsrldq	$8, %xmm0, %xmm3
	vmovdqa	%xmm9, 224(%rsp)
	vpmovzxbd	%xmm0, %xmm9
	vpmulld	.LC5(%rip), %xmm10, %xmm15
	vmovdqa	.LC20(%rip), %xmm8
	vmovdqa	%xmm4, 208(%rsp)
	vpsrldq	$4, %xmm0, %xmm4
	vpsrldq	$12, %xmm0, %xmm0
	vpaddd	%xmm9, %xmm1, %xmm1
	vpmovzxbd	%xmm3, %xmm3
	vpmovzxbd	%xmm0, %xmm0
	vpmovzxbd	%xmm4, %xmm4
	vmovdqa	%xmm15, 272(%rsp)
	vpaddd	%xmm0, %xmm5, %xmm5
	vpaddd	%xmm3, %xmm2, %xmm2
	vpmulld	%xmm8, %xmm9, %xmm9
	vpmulld	.LC17(%rip), %xmm12, %xmm15
	vmovdqa	.LC21(%rip), %xmm12
	vpaddd	%xmm4, %xmm2, %xmm2
	vmovdqa	.LC22(%rip), %xmm10
	vpaddd	%xmm5, %xmm1, %xmm1
	vpaddd	%xmm2, %xmm1, %xmm1
	vmovdqa	272(%rsp), %xmm5
	vpaddd	288(%rsp), %xmm5, %xmm2
	vpmulld	%xmm12, %xmm4, %xmm4
	vpmulld	%xmm10, %xmm3, %xmm3
	vmovdqa	.LC23(%rip), %xmm11
	vpaddd	304(%rsp), %xmm14, %xmm5
	vpaddd	240(%rsp), %xmm5, %xmm5
	vpaddd	%xmm13, %xmm2, %xmm2
	vmovdqa	320(%rsp), %xmm7
	vpaddd	208(%rsp), %xmm2, %xmm2
	vpmulld	%xmm11, %xmm0, %xmm0
	vpaddd	224(%rsp), %xmm5, %xmm5
	vmovdqa	336(%rsp), %xmm6
	vpaddd	%xmm4, %xmm5, %xmm5
	vpaddd	%xmm3, %xmm2, %xmm2
	vpaddd	%xmm5, %xmm2, %xmm2
	vpaddd	%xmm6, %xmm7, %xmm5
	vpmulld	.LC0(%rip), %xmm6, %xmm6
	vpaddd	256(%rsp), %xmm5, %xmm5
	vpaddd	%xmm15, %xmm5, %xmm5
	vpaddd	%xmm9, %xmm5, %xmm5
	vpaddd	%xmm0, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm2, %xmm2
	vpmulld	.LC1(%rip), %xmm7, %xmm5
	vpaddd	%xmm6, %xmm5, %xmm6
	vmovdqa	288(%rsp), %xmm5
	vpmulld	.LC4(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm5
	vpmulld	.LC17(%rip), %xmm15, %xmm6
	vmovdqa	240(%rsp), %xmm7
	vpmulld	.LC7(%rip), %xmm7, %xmm7
	vpaddd	%xmm6, %xmm5, %xmm6
	vpmulld	%xmm10, %xmm3, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm6
	vmovdqa	256(%rsp), %xmm5
	vpmulld	.LC6(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vmovdqa	208(%rsp), %xmm7
	vpmulld	.LC19(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm7
	vpmulld	.LC16(%rip), %xmm13, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	%xmm12, %xmm4, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm5
	vpmulld	.LC2(%rip), %xmm14, %xmm7
	vpaddd	%xmm5, %xmm6, %xmm6
	vmovdqa	304(%rsp), %xmm5
	vpmulld	.LC3(%rip), %xmm5, %xmm5
	vpaddd	%xmm7, %xmm5, %xmm7
	vmovdqa	272(%rsp), %xmm5
	vpmulld	.LC5(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vmovdqa	224(%rsp), %xmm7
	vpmulld	.LC18(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm7
	vpmulld	%xmm11, %xmm0, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	%xmm8, %xmm9, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm5
	vmovdqa	320(%rsp), %xmm7
	vpaddd	%xmm5, %xmm6, %xmm5
	vpmulld	.LC9(%rip), %xmm7, %xmm6
	vmovdqa	336(%rsp), %xmm7
	vpmulld	.LC8(%rip), %xmm7, %xmm7
	vpmulld	.LC31(%rip), %xmm3, %xmm3
	vpaddd	%xmm7, %xmm6, %xmm7
	vmovdqa	288(%rsp), %xmm6
	vpmulld	.LC11(%rip), %xmm6, %xmm6
	vpmulld	.LC26(%rip), %xmm4, %xmm4
	vpaddd	%xmm6, %xmm7, %xmm6
	vpmulld	.LC28(%rip), %xmm15, %xmm7
	vmovdqa	.LC14(%rip), %xmm15
	vpmulld	.LC30(%rip), %xmm0, %xmm0
	vpaddd	%xmm7, %xmm6, %xmm7
	vpmulld	240(%rsp), %xmm15, %xmm6
	vpmulld	.LC29(%rip), %xmm9, %xmm9
	vpaddd	%xmm3, %xmm7, %xmm3
	vmovdqa	256(%rsp), %xmm7
	vpmulld	.LC10(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm7
	vmovdqa	208(%rsp), %xmm6
	vpmulld	.LC25(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm7, %xmm6
	vpmulld	.LC27(%rip), %xmm13, %xmm7
	vmovdqa	.LC12(%rip), %xmm13
	vpaddd	%xmm7, %xmm6, %xmm7
	vmovdqa	224(%rsp), %xmm6
	vpaddd	%xmm4, %xmm7, %xmm7
	vpmulld	%xmm13, %xmm14, %xmm4
	vpaddd	%xmm7, %xmm3, %xmm7
	vmovdqa	304(%rsp), %xmm3
	vpmulld	.LC13(%rip), %xmm3, %xmm3
	vmovdqa	.LC15(%rip), %xmm14
	vpaddd	%xmm4, %xmm3, %xmm4
	vpmulld	272(%rsp), %xmm14, %xmm3
	vpaddd	%xmm3, %xmm4, %xmm3
	vpmulld	.LC24(%rip), %xmm6, %xmm4
	vpaddd	%xmm4, %xmm3, %xmm4
	vpunpckhqdq	%xmm1, %xmm1, %xmm3
	vpaddd	%xmm3, %xmm1, %xmm3
	vpaddd	%xmm0, %xmm4, %xmm0
	vpshufd	$177, %xmm3, %xmm1
	vpaddd	%xmm9, %xmm0, %xmm0
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm7, %xmm0
	vmovd	%xmm1, %r9d
	vpunpckhqdq	%xmm2, %xmm2, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm2
	movq	%r9, 352(%rsp)
	vpshufd	$177, %xmm2, %xmm1
	vpaddd	%xmm2, %xmm1, %xmm1
	vpunpckhqdq	%xmm5, %xmm5, %xmm2
	vpaddd	%xmm2, %xmm5, %xmm2
	vmovd	%xmm1, %r10d
	vpshufd	$177, %xmm2, %xmm1
	movq	%r10, 360(%rsp)
	vpaddd	%xmm2, %xmm1, %xmm1
	vmovd	%xmm1, %r11d
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	movq	%r11, 368(%rsp)
	vpshufd	$177, %xmm1, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %eax
	movq	%rax, 376(%rsp)
	vmovdqa	352(%rsp), %ymm0
	vpxor	(%rdi), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	je	.L327
	testq	%r15, %r15
	je	.L319
	movl	%r8d, %edx
	movb	$1, (%r15,%rdx)
.L319:
	subq	(%rdi), %r9
	je	.L320
	subq	24(%rdi), %rax
	subq	8(%rdi), %r10
	movq	%rax, %r13
	leaq	255(%r9), %rax
	subq	16(%rdi), %r11
	cmpq	$510, %rax
	ja	.L321
	movq	%r10, %rax
	cqto
	idivq	%r9
	testq	%rdx, %rdx
	jne	.L321
	leaq	-1(%rax), %rdx
	cmpq	$63, %rdx
	ja	.L321
	movq	%rax, %rdx
	imulq	%rax, %rdx
	imulq	%r9, %rdx
	cmpq	%rdx, %r11
	je	.L363
	.p2align 4
	.p2align 3
.L321:
	movq	%r9, %r12
	movq	%r10, %rax
	imulq	%r11, %r12
	imulq	%r10, %rax
	subq	%rax, %r12
	je	.L320
	movq	%r9, %rax
	movq	%r10, %rdx
	imulq	%r11, %rdx
	imulq	%r13, %rax
	subq	%rdx, %rax
	cqto
	idivq	%r12
	movq	%rax, 336(%rsp)
	testq	%rdx, %rdx
	jne	.L320
	movq	%r10, %rdx
	imulq	%r13, %rdx
	movq	%rdx, %rax
	movq	%r11, %rdx
	imulq	%r11, %rdx
	subq	%rdx, %rax
	cqto
	idivq	%r12
	testq	%rdx, %rdx
	jne	.L320
	movq	336(%rsp), %r12
	negq	%rax
	movq	%r12, %rdx
	imulq	%r12, %rdx
	leaq	(%rdx,%rax,4), %r12
	testq	%r12, %r12
	jle	.L320
	movl	$1, %eax
	cmpq	$1, %r12
	je	.L323
	.p2align 4
	.p2align 4
	.p2align 3
.L324:
	addq	$1, %rax
	movq	%rax, %rdx
	imulq	%rax, %rdx
	cmpq	%rdx, %r12
	jg	.L324
	je	.L323
	.p2align 4
	.p2align 3
.L320:
	addq	$1, %r14
.L327:
	addq	$1, %rsi
	addq	$64, %rcx
	addq	$32, %rdi
	addl	$1, %r8d
	cmpq	$32, %rsi
	jne	.L328
	movq	16(%rsp), %r9
	movq	24(%rsp), %r11
	addq	$32, %rbx
	addq	$1, %r9
	addq	$1024, %r11
	cmpq	$8, %r9
	jne	.L314
	movq	408(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L364
	vzeroupper
	leaq	-40(%rbp), %rsp
	movq	%r14, %rax
	popq	%rbx
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%r15
	popq	%rbp
	.cfi_remember_state
	.cfi_def_cfa 7, 8
	ret
.L363:
	.cfi_restore_state
	movq	%rax, %rdx
	imulq	%r11, %rdx
	cmpq	%rdx, %r13
	jne	.L321
	subl	$1, %eax
	subb	%r9b, (%rcx,%rax)
.L322:
	vmovdqu	(%rcx), %xmm1
	vpsrldq	$4, %xmm1, %xmm0
	vpmovzxbd	%xmm1, %xmm5
	vpmulld	.LC0(%rip), %xmm5, %xmm4
	vmovdqa	%xmm4, 176(%rsp)
	vpmovzxbd	%xmm0, %xmm3
	vpsrldq	$8, %xmm1, %xmm0
	vpmulld	.LC1(%rip), %xmm3, %xmm7
	vmovdqa	%xmm7, 336(%rsp)
	vpsrldq	$12, %xmm1, %xmm1
	vmovdqu	16(%rcx), %xmm7
	vpmovzxbd	%xmm0, %xmm0
	vmovdqa	%xmm3, 192(%rsp)
	vpmulld	.LC2(%rip), %xmm0, %xmm3
	vpmovzxbd	%xmm1, %xmm2
	vmovdqa	%xmm3, 160(%rsp)
	vpmovzxbd	%xmm7, %xmm6
	vpsrldq	$4, %xmm7, %xmm1
	vmovdqa	%xmm2, 144(%rsp)
	vpmulld	.LC3(%rip), %xmm2, %xmm2
	vmovdqa	%xmm2, 320(%rsp)
	vpsrldq	$8, %xmm7, %xmm2
	vpmovzxbd	%xmm1, %xmm9
	vpmulld	.LC4(%rip), %xmm6, %xmm1
	vpmovzxbd	%xmm2, %xmm2
	vmovdqa	%xmm9, 112(%rsp)
	vpsrldq	$12, %xmm7, %xmm7
	vpmulld	.LC5(%rip), %xmm9, %xmm9
	vmovdqa	%xmm6, 128(%rsp)
	vpmovzxbd	%xmm7, %xmm7
	vpmulld	.LC6(%rip), %xmm2, %xmm6
	vpmulld	.LC7(%rip), %xmm7, %xmm4
	vmovdqa	%xmm6, 272(%rsp)
	vmovdqu	32(%rcx), %xmm6
	vpaddd	%xmm7, %xmm2, %xmm2
	vmovdqa	%xmm1, 304(%rsp)
	vmovdqa	%xmm9, 288(%rsp)
	vpsrldq	$4, %xmm6, %xmm1
	vmovdqa	%xmm4, 256(%rsp)
	vpmovzxbd	%xmm1, %xmm9
	vpsrldq	$8, %xmm6, %xmm1
	vpmovzxbd	%xmm6, %xmm4
	vpmovzxbd	%xmm1, %xmm1
	vmovdqa	%xmm4, 96(%rsp)
	vpmulld	.LC16(%rip), %xmm4, %xmm3
	vpsrldq	$12, %xmm6, %xmm6
	vmovdqa	%xmm1, 64(%rsp)
	vmovdqa	64(%rsp), %xmm4
	vpmovzxbd	%xmm6, %xmm6
	vmovdqa	.LC17(%rip), %xmm1
	vmovdqa	%xmm3, 240(%rsp)
	vpmulld	%xmm9, %xmm1, %xmm1
	vmovdqa	%xmm9, 80(%rsp)
	vpmulld	.LC18(%rip), %xmm4, %xmm9
	vmovdqa	%xmm1, 224(%rsp)
	vmovdqa	%xmm9, 208(%rsp)
	vmovdqu	48(%rcx), %xmm1
	vpaddd	144(%rsp), %xmm0, %xmm0
	vpmulld	.LC19(%rip), %xmm6, %xmm9
	vpaddd	128(%rsp), %xmm0, %xmm0
	vpaddd	64(%rsp), %xmm2, %xmm2
	vpmovzxbd	%xmm1, %xmm4
	vpsrldq	$4, %xmm1, %xmm3
	vpaddd	192(%rsp), %xmm5, %xmm5
	vmovdqa	336(%rsp), %xmm7
	vmovdqa	%xmm4, 48(%rsp)
	vpsrldq	$8, %xmm1, %xmm4
	vpaddd	%xmm6, %xmm0, %xmm0
	vpaddd	112(%rsp), %xmm5, %xmm5
	vpmovzxbd	%xmm4, %xmm4
	vpsrldq	$12, %xmm1, %xmm1
	vpmovzxbd	%xmm3, %xmm3
	vpmulld	48(%rsp), %xmm8, %xmm6
	vpaddd	96(%rsp), %xmm5, %xmm5
	vpaddd	80(%rsp), %xmm2, %xmm2
	vpmovzxbd	%xmm1, %xmm1
	vmovdqa	%xmm6, 192(%rsp)
	vpaddd	48(%rsp), %xmm2, %xmm2
	vpaddd	%xmm4, %xmm0, %xmm0
	vpmulld	%xmm10, %xmm4, %xmm4
	vpaddd	%xmm1, %xmm5, %xmm5
	vpaddd	%xmm3, %xmm0, %xmm0
	vpmulld	%xmm12, %xmm3, %xmm3
	vpaddd	%xmm5, %xmm2, %xmm2
	vpmulld	%xmm11, %xmm1, %xmm1
	vmovdqa	288(%rsp), %xmm5
	vpaddd	%xmm0, %xmm2, %xmm0
	vpaddd	304(%rsp), %xmm5, %xmm2
	vmovdqa	320(%rsp), %xmm5
	vpaddd	240(%rsp), %xmm2, %xmm2
	vpaddd	160(%rsp), %xmm5, %xmm5
	vpaddd	256(%rsp), %xmm5, %xmm5
	vpaddd	208(%rsp), %xmm5, %xmm5
	vpaddd	%xmm9, %xmm2, %xmm2
	vpaddd	%xmm3, %xmm5, %xmm5
	vpaddd	%xmm4, %xmm2, %xmm2
	vpaddd	%xmm5, %xmm2, %xmm2
	vpaddd	176(%rsp), %xmm7, %xmm5
	vpmulld	.LC1(%rip), %xmm7, %xmm7
	vpaddd	272(%rsp), %xmm5, %xmm5
	vpaddd	224(%rsp), %xmm5, %xmm5
	vpaddd	%xmm6, %xmm5, %xmm5
	vpaddd	%xmm1, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm2, %xmm2
	vmovdqa	256(%rsp), %xmm5
	vpmulld	.LC7(%rip), %xmm5, %xmm6
	vmovdqa	272(%rsp), %xmm5
	vpmulld	.LC6(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm5
	vpmulld	.LC19(%rip), %xmm9, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm5
	vmovdqa	240(%rsp), %xmm6
	vpmulld	.LC16(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm6
	vpmulld	%xmm12, %xmm3, %xmm5
	vmovdqa	176(%rsp), %xmm12
	vpmulld	.LC25(%rip), %xmm9, %xmm9
	vpmulld	.LC26(%rip), %xmm3, %xmm3
	vpaddd	%xmm5, %xmm6, %xmm6
	vpmulld	.LC0(%rip), %xmm12, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vmovdqa	304(%rsp), %xmm7
	vpmulld	.LC4(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm7
	vmovdqa	224(%rsp), %xmm5
	vpmulld	.LC17(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	%xmm10, %xmm4, %xmm7
	vmovdqa	160(%rsp), %xmm10
	vpmulld	.LC31(%rip), %xmm4, %xmm4
	vpaddd	%xmm7, %xmm5, %xmm5
	vpmulld	.LC2(%rip), %xmm10, %xmm7
	vpaddd	%xmm5, %xmm6, %xmm5
	vmovdqa	320(%rsp), %xmm6
	vpmulld	.LC3(%rip), %xmm6, %xmm6
	vpaddd	%xmm7, %xmm6, %xmm7
	vmovdqa	288(%rsp), %xmm6
	vpmulld	.LC5(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm7, %xmm6
	vmovdqa	208(%rsp), %xmm7
	vpmulld	.LC18(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm7
	vpmulld	%xmm11, %xmm1, %xmm6
	vmovdqa	272(%rsp), %xmm11
	vpaddd	%xmm6, %xmm7, %xmm6
	vpmulld	192(%rsp), %xmm8, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vpmulld	.LC10(%rip), %xmm11, %xmm7
	vmovdqa	240(%rsp), %xmm11
	vpaddd	%xmm6, %xmm5, %xmm6
	vpmulld	256(%rsp), %xmm15, %xmm5
	vpaddd	%xmm7, %xmm5, %xmm5
	vpmulld	.LC27(%rip), %xmm11, %xmm7
	vpaddd	%xmm9, %xmm5, %xmm5
	vpaddd	%xmm7, %xmm5, %xmm5
	vmovdqa	336(%rsp), %xmm7
	vpaddd	%xmm3, %xmm5, %xmm3
	vpmulld	.LC9(%rip), %xmm7, %xmm5
	vpmulld	.LC8(%rip), %xmm12, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm7
	vmovdqa	304(%rsp), %xmm12
	vpmulld	.LC11(%rip), %xmm12, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vmovdqa	224(%rsp), %xmm7
	vpmulld	.LC28(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm7
	vmovdqa	320(%rsp), %xmm5
	vpaddd	%xmm4, %xmm7, %xmm7
	vpmulld	%xmm10, %xmm13, %xmm4
	vpaddd	%xmm7, %xmm3, %xmm7
	vpmulld	.LC13(%rip), %xmm5, %xmm3
	vpaddd	%xmm4, %xmm3, %xmm4
	vpmulld	288(%rsp), %xmm14, %xmm3
	vmovdqa	208(%rsp), %xmm9
	vpmulld	.LC30(%rip), %xmm1, %xmm1
	vmovdqa	192(%rsp), %xmm11
	vpaddd	%xmm3, %xmm4, %xmm4
	vpmulld	.LC24(%rip), %xmm9, %xmm3
	vpmulld	.LC29(%rip), %xmm11, %xmm8
	vpaddd	%xmm3, %xmm4, %xmm4
	vpunpckhqdq	%xmm0, %xmm0, %xmm3
	vpaddd	%xmm3, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm4, %xmm4
	vpshufd	$177, %xmm0, %xmm3
	vpaddd	%xmm8, %xmm4, %xmm1
	vpaddd	%xmm0, %xmm3, %xmm0
	vpaddd	%xmm1, %xmm7, %xmm1
	vpmovzxdq	%xmm0, %xmm4
	vpunpckhqdq	%xmm2, %xmm2, %xmm0
	vmovq	%xmm4, 352(%rsp)
	vpaddd	%xmm0, %xmm2, %xmm2
	vpshufd	$177, %xmm2, %xmm0
	vpaddd	%xmm2, %xmm0, %xmm0
	vpmovzxdq	%xmm0, %xmm4
	vpunpckhqdq	%xmm6, %xmm6, %xmm0
	vmovq	%xmm4, 360(%rsp)
	vpaddd	%xmm0, %xmm6, %xmm6
	vpshufd	$177, %xmm6, %xmm0
	vpaddd	%xmm6, %xmm0, %xmm0
	vpmovzxdq	%xmm0, %xmm4
	vpunpckhqdq	%xmm1, %xmm1, %xmm0
	vmovq	%xmm4, 368(%rsp)
	vpaddd	%xmm0, %xmm1, %xmm1
	vpshufd	$177, %xmm1, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpmovzxdq	%xmm0, %xmm4
	vmovq	%xmm4, 376(%rsp)
	vmovdqa	352(%rsp), %ymm0
	vpxor	(%rdi), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L320
	movl	36(%rsp), %eax
	movl	%esi, %edx
	movq	40(%rsp), %r11
	vpxor	%xmm0, %xmm0, %xmm0
	salq	$5, %rax
	addq	%rax, %rdx
	salq	$6, %rdx
	vmovdqu	%ymm0, 24576(%r11,%rdx)
	vmovdqu	%ymm0, 24608(%r11,%rdx)
	vmovdqu	(%rcx), %xmm0
	vmovdqu	16(%rcx), %xmm2
	vpmovzxbd	%xmm0, %xmm1
	vpsrldq	$4, %xmm0, %xmm11
	vpmovzxbd	%xmm2, %xmm6
	vpmulld	.LC0(%rip), %xmm1, %xmm8
	vpsrldq	$8, %xmm0, %xmm3
	vpsrldq	$12, %xmm0, %xmm0
	vpmovzxbd	%xmm11, %xmm11
	vpmulld	.LC1(%rip), %xmm11, %xmm12
	vpmovzxbd	%xmm0, %xmm4
	vpmovzxbd	%xmm3, %xmm3
	vpaddd	%xmm11, %xmm1, %xmm1
	vpmulld	.LC2(%rip), %xmm3, %xmm9
	vpsrldq	$4, %xmm2, %xmm7
	vpsrldq	$8, %xmm2, %xmm5
	vpaddd	%xmm4, %xmm3, %xmm3
	vpmulld	.LC3(%rip), %xmm4, %xmm0
	vpsrldq	$12, %xmm2, %xmm2
	vpmovzxbd	%xmm5, %xmm5
	vpmovzxbd	%xmm7, %xmm7
	vpmulld	.LC1(%rip), %xmm12, %xmm11
	vpmovzxbd	%xmm2, %xmm2
	vpaddd	%xmm5, %xmm3, %xmm3
	vpaddd	%xmm0, %xmm9, %xmm4
	vpmulld	.LC6(%rip), %xmm5, %xmm5
	vpaddd	%xmm2, %xmm1, %xmm1
	vpaddd	%xmm6, %xmm3, %xmm3
	vpmulld	.LC4(%rip), %xmm6, %xmm6
	vpmulld	.LC7(%rip), %xmm2, %xmm2
	vpmulld	.LC2(%rip), %xmm9, %xmm10
	vpaddd	%xmm7, %xmm1, %xmm1
	vpmulld	.LC5(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm4, %xmm4
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm12, %xmm8, %xmm3
	vpmulld	%xmm13, %xmm9, %xmm9
	vpaddd	%xmm6, %xmm3, %xmm3
	vpaddd	%xmm2, %xmm4, %xmm4
	vpaddd	%xmm5, %xmm3, %xmm3
	vpaddd	%xmm3, %xmm4, %xmm4
	vpmulld	.LC0(%rip), %xmm8, %xmm3
	vpaddd	%xmm3, %xmm11, %xmm3
	vpmulld	.LC6(%rip), %xmm5, %xmm11
	vpmulld	.LC8(%rip), %xmm8, %xmm8
	vpaddd	%xmm11, %xmm3, %xmm11
	vpmulld	.LC4(%rip), %xmm6, %xmm3
	vpmulld	.LC10(%rip), %xmm5, %xmm5
	vpmulld	.LC11(%rip), %xmm6, %xmm6
	vpaddd	%xmm3, %xmm11, %xmm11
	vpmulld	.LC3(%rip), %xmm0, %xmm3
	vpaddd	%xmm10, %xmm3, %xmm3
	vpmulld	.LC7(%rip), %xmm2, %xmm10
	vpmulld	%xmm15, %xmm2, %xmm2
	vpmulld	.LC13(%rip), %xmm0, %xmm0
	vpaddd	%xmm9, %xmm0, %xmm0
	vpaddd	%xmm10, %xmm3, %xmm3
	vpmulld	.LC5(%rip), %xmm7, %xmm10
	vpmulld	%xmm14, %xmm7, %xmm7
	vpaddd	%xmm10, %xmm3, %xmm3
	vpmulld	.LC9(%rip), %xmm12, %xmm10
	vpaddd	%xmm8, %xmm10, %xmm8
	vpaddd	%xmm3, %xmm11, %xmm3
	vpaddd	%xmm5, %xmm8, %xmm5
	vpaddd	%xmm6, %xmm5, %xmm6
	vpaddd	%xmm2, %xmm0, %xmm0
	vpunpckhqdq	%xmm1, %xmm1, %xmm2
	vpaddd	%xmm2, %xmm1, %xmm1
	vpaddd	%xmm7, %xmm0, %xmm0
	vpshufd	$177, %xmm1, %xmm2
	vpaddd	%xmm0, %xmm6, %xmm0
	vpaddd	%xmm1, %xmm2, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm4, %xmm4, %xmm1
	vpaddd	%xmm1, %xmm4, %xmm4
	vmovq	%xmm2, 24576(%rcx)
	vpshufd	$177, %xmm4, %xmm1
	vpaddd	%xmm4, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm4
	vpunpckhqdq	%xmm3, %xmm3, %xmm1
	vpaddd	%xmm1, %xmm3, %xmm3
	vmovq	%xmm4, 24584(%rcx)
	vpshufd	$177, %xmm3, %xmm1
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm4
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovq	%xmm4, 24592(%rcx)
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	vpmovzxdq	%xmm0, %xmm4
	vmovdqu	32(%rcx), %xmm0
	vmovq	%xmm4, 24600(%rcx)
	vpsrldq	$4, %xmm0, %xmm1
	vpsrldq	$8, %xmm0, %xmm4
	vpmovzxbd	%xmm0, %xmm11
	vpmulld	.LC0(%rip), %xmm11, %xmm5
	vmovdqu	48(%rcx), %xmm2
	vpsrldq	$12, %xmm0, %xmm0
	vpmovzxbd	%xmm4, %xmm4
	vpmovzxbd	%xmm1, %xmm1
	vpmulld	.LC1(%rip), %xmm1, %xmm12
	vpmovzxbd	%xmm0, %xmm3
	vpaddd	%xmm11, %xmm1, %xmm1
	vpmulld	.LC3(%rip), %xmm3, %xmm0
	vpmovzxbd	%xmm2, %xmm8
	vpsrldq	$4, %xmm2, %xmm6
	vpaddd	%xmm4, %xmm3, %xmm3
	vpmulld	.LC2(%rip), %xmm4, %xmm9
	vpsrldq	$8, %xmm2, %xmm7
	vpsrldq	$12, %xmm2, %xmm2
	vpmovzxbd	%xmm6, %xmm6
	vpmulld	.LC0(%rip), %xmm5, %xmm11
	vpmovzxbd	%xmm7, %xmm7
	vpmovzxbd	%xmm2, %xmm2
	vpaddd	%xmm0, %xmm9, %xmm4
	vpmulld	.LC3(%rip), %xmm0, %xmm10
	vpaddd	%xmm2, %xmm1, %xmm1
	vpaddd	%xmm7, %xmm3, %xmm3
	vpmulld	.LC7(%rip), %xmm2, %xmm2
	vpmulld	.LC6(%rip), %xmm7, %xmm7
	vpaddd	%xmm8, %xmm3, %xmm3
	vpaddd	%xmm6, %xmm1, %xmm1
	vpmulld	.LC4(%rip), %xmm8, %xmm8
	vpmulld	.LC5(%rip), %xmm6, %xmm6
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm5, %xmm12, %xmm3
	vpmulld	.LC13(%rip), %xmm0, %xmm0
	vpmulld	.LC8(%rip), %xmm5, %xmm5
	vpaddd	%xmm6, %xmm4, %xmm4
	vpaddd	%xmm8, %xmm3, %xmm3
	vpaddd	%xmm7, %xmm3, %xmm3
	vpaddd	%xmm2, %xmm4, %xmm4
	vpaddd	%xmm3, %xmm4, %xmm4
	vpmulld	.LC1(%rip), %xmm12, %xmm3
	vpaddd	%xmm11, %xmm3, %xmm11
	vpmulld	.LC6(%rip), %xmm7, %xmm3
	vpmulld	.LC10(%rip), %xmm7, %xmm7
	vpaddd	%xmm3, %xmm11, %xmm3
	vpmulld	.LC4(%rip), %xmm8, %xmm11
	vpmulld	.LC11(%rip), %xmm8, %xmm8
	vpaddd	%xmm11, %xmm3, %xmm3
	vpmulld	.LC2(%rip), %xmm9, %xmm11
	vpmulld	%xmm13, %xmm9, %xmm9
	vpaddd	%xmm10, %xmm11, %xmm11
	vpmulld	.LC7(%rip), %xmm2, %xmm10
	vpmulld	%xmm15, %xmm2, %xmm2
	vpaddd	%xmm10, %xmm11, %xmm11
	vpmulld	.LC5(%rip), %xmm6, %xmm10
	vpmulld	%xmm14, %xmm6, %xmm6
	vpaddd	%xmm10, %xmm11, %xmm11
	vpmulld	.LC9(%rip), %xmm12, %xmm10
	vpaddd	%xmm5, %xmm10, %xmm5
	vpaddd	%xmm11, %xmm3, %xmm3
	vpaddd	%xmm7, %xmm5, %xmm5
	vpaddd	%xmm8, %xmm5, %xmm5
	vpaddd	%xmm9, %xmm0, %xmm0
	vpaddd	%xmm2, %xmm0, %xmm0
	vpunpckhqdq	%xmm1, %xmm1, %xmm2
	vpaddd	%xmm2, %xmm1, %xmm1
	vpaddd	%xmm6, %xmm0, %xmm0
	vpshufd	$177, %xmm1, %xmm2
	vpaddd	%xmm0, %xmm5, %xmm0
	vpaddd	%xmm1, %xmm2, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm4, %xmm4, %xmm1
	vpaddd	%xmm1, %xmm4, %xmm4
	vmovq	%xmm2, 24608(%rcx)
	vpshufd	$177, %xmm4, %xmm1
	vpaddd	%xmm4, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm4
	vpunpckhqdq	%xmm3, %xmm3, %xmm1
	vpaddd	%xmm1, %xmm3, %xmm3
	vmovq	%xmm4, 24616(%rcx)
	vpshufd	$177, %xmm3, %xmm1
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm4
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovq	%xmm4, 24624(%rcx)
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	vpmovzxdq	%xmm0, %xmm4
	vmovq	%xmm4, 24632(%rcx)
	jmp	.L327
.L323:
	movq	336(%rsp), %r12
	leaq	(%rax,%r12), %rdx
	testb	$1, %dl
	jne	.L320
	subq	%rax, %r12
	leaq	-2(%r12), %rax
	cmpq	$127, %rax
	ja	.L320
	leaq	-2(%rdx), %rax
	cmpq	$127, %rax
	ja	.L320
	movq	%rdx, %rax
	sarq	%r12
	sarq	%rax
	movq	%rax, 336(%rsp)
	cmpq	%r12, %rax
	je	.L320
	movq	%r9, %rdx
	movq	%r10, %rax
	movq	336(%rsp), %r10
	imulq	%r12, %rdx
	subq	%r12, %r10
	subq	%rdx, %rax
	cqto
	idivq	%r10
	testq	%rdx, %rdx
	jne	.L320
	leaq	255(%rax), %rdx
	cmpq	$510, %rdx
	ja	.L320
	subq	%rax, %r9
	leaq	255(%r9), %rdx
	cmpq	$510, %rdx
	ja	.L320
	testq	%rax, %rax
	je	.L320
	testq	%r9, %r9
	je	.L320
	movq	336(%rsp), %r10
	movq	%r10, %rdx
	imulq	%r10, %rdx
	movq	%r12, %r10
	imulq	%r12, %r10
	imulq	%rax, %rdx
	imulq	%r9, %r10
	movq	%rdx, 320(%rsp)
	movq	320(%rsp), %rdx
	addq	%r10, %rdx
	cmpq	%rdx, %r11
	jne	.L320
	movq	320(%rsp), %rdx
	movq	336(%rsp), %r11
	imulq	%r12, %r10
	imulq	%r11, %rdx
	addq	%r10, %rdx
	cmpq	%rdx, %r13
	jne	.L320
	leal	-1(%r11), %edx
	subb	%al, (%rcx,%rdx)
	leal	-1(%r12), %eax
	subb	%r9b, (%rcx,%rax)
	jmp	.L322
.L364:
	vzeroupper
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE7307:
	.size	sqm_sweep, .-sqm_sweep
	.section	.rodata.str1.8
	.align 8
.LC81:
	.string	"SQMOR O1_skip_exact    %lld/%d = %.6f  expect=1.000000 (0 rd 0 wr)\n"
	.align 8
.LC82:
	.string	"SQMOR O2_diff_correct  %lld/%lld = %.6f  expect=1.000000 (content+journal closure)\n"
	.align 8
.LC83:
	.string	"SQMOR O3_amplification 1-byte: %.2f rd %.2f wr | 2-byte: %.2f rd %.2f wr (bytes/write)\n"
	.align 8
.LC84:
	.string	"SQMOR O4_sweep_det     %lld/%lld = %.6f  expect=1.000000 counting\n"
	.align 8
.LC85:
	.string	"SQMOR O4_sweep_rep     %lld/%lld = %.6f  expect>=0.990 measurement\n"
	.align 8
.LC86:
	.string	"SQMOR O4_unresolved    %lld  expect=0\n"
	.align 8
.LC87:
	.string	"SQMOR O5_quad_caught   %lld/%lld = %.6f  expect=1.000000 (blind to SQ5, caught by s3)\n"
	.align 8
.LC88:
	.string	"SQMOR O5_pent_blind    %lld/%lld = %.6f  expect=1.000000 documented-exclusion\n"
	.align 8
.LC89:
	.string	"SQMOR O6_skip_window   %lld/%lld stale-after-skip  expect=all-stale documented-window (sweep closes it)\n"
	.section	.text.startup,"ax",@progbits
	.p2align 4
	.globl	main
	.type	main, @function
main:
.LFB7309:
	.cfi_startproc
	leaq	8(%rsp), %r10
	.cfi_def_cfa 10, 0
	andq	$-32, %rsp
	pushq	-8(%r10)
	pushq	%rbp
	movq	%rsp, %rbp
	.cfi_escape 0x10,0x6,0x2,0x76,0
	pushq	%r15
	pushq	%r14
	.cfi_escape 0x10,0xf,0x2,0x76,0x78
	.cfi_escape 0x10,0xe,0x2,0x76,0x70
	movl	$1000, %r14d
	pushq	%r13
	pushq	%r12
	pushq	%r10
	.cfi_escape 0xf,0x3,0x76,0x58,0x6
	.cfi_escape 0x10,0xd,0x2,0x76,0x68
	.cfi_escape 0x10,0xc,0x2,0x76,0x60
	pushq	%rbx
	subq	$608, %rsp
	.cfi_escape 0x10,0x3,0x2,0x76,0x50
	movq	%fs:40, %rax
	movq	%rax, -56(%rbp)
	xorl	%eax, %eax
	cmpl	$1, %edi
	jle	.L366
	movq	8(%rsi), %rdi
	call	atoi@PLT
	movl	%eax, %r14d
.L366:
	leaq	cell.5(%rip), %rax
	movl	$41312, %edx
	xorl	%esi, %esi
	xorl	%ebx, %ebx
	movq	%rax, %rdi
	movq	%rax, -424(%rbp)
	leaq	contents.4(%rip), %r13
	call	memset@PLT
	movl	$4096, %edx
	movl	$255, %esi
	movq	%r13, %r12
	leaq	sqm_slot_of(%rip), %rdi
	call	memset@PLT
	movl	$-1515870811, %eax
	vmovd	%eax, %xmm2
	vpbroadcastd	%xmm2, %ymm2
	vmovdqa	%ymm2, -176(%rbp)
.L367:
	movl	%ebx, %eax
	vmovdqa	-176(%rbp), %ymm2
	movq	%r12, %rdx
	movl	%ebx, %esi
	sall	$4, %eax
	movl	%ebx, %edi
	addl	%ebx, %eax
	vmovd	%eax, %xmm0
	vpbroadcastb	%xmm0, %ymm0
	vpaddb	.LC55(%rip), %ymm0, %ymm1
	vpaddb	.LC57(%rip), %ymm0, %ymm0
	vpxor	%ymm2, %ymm1, %ymm1
	vpxor	%ymm2, %ymm0, %ymm0
	vmovdqa	%ymm1, (%r12)
	vmovdqa	%ymm0, 32(%r12)
	vzeroupper
	call	sqm_write.constprop.0.isra.0
	addl	$1, %ebx
	addq	$64, %r12
	cmpl	$256, %ebx
	jne	.L367
	movl	%r14d, -176(%rbp)
	movq	41288+cell.5(%rip), %r15
	xorl	%r12d, %r12d
	movq	$0, -616(%rbp)
	movq	-424(%rbp), %r14
	jmp	.L373
.L369:
	addq	$1, %r12
	addq	$64, %r13
	cmpq	$256, %r12
	je	.L511
.L373:
	movq	%r13, %rdx
	movl	%r12d, %edi
	movl	%r12d, %esi
	movq	41296(%r14), %rbx
	call	sqm_write.constprop.0.isra.0
	movq	%r15, %rdx
	movq	41288(%r14), %r15
	cmpq	%rdx, %r15
	jne	.L369
	cmpq	%rbx, 41296(%r14)
	jne	.L369
	leaq	sqm_slot_of(%rip), %rax
	movl	(%rax,%r12,4), %ecx
	movl	%ecx, %edx
	movzbl	%cl, %ecx
	sarl	$8, %edx
	movslq	%edx, %rdx
	salq	$5, %rdx
	addq	%rcx, %rdx
	salq	$6, %rdx
	addq	%r14, %rdx
	vmovdqa	(%rdx), %ymm0
	vpxor	0(%r13), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L371
	vmovdqa	32(%rdx), %ymm0
	vpxor	32(%r13), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L371
	xorl	%edx, %edx
.L372:
	cmpl	$1, %edx
	adcq	$0, -616(%rbp)
	vzeroupper
	jmp	.L369
.L371:
	movl	$1, %edx
	jmp	.L372
.L511:
	movl	-176(%rbp), %r14d
	testl	%r14d, %r14d
	jle	.L374
	movabsq	$7683277266246660415, %rax
	movl	$2155905153, %ebx
	movl	$0, -480(%rbp)
	movabsq	$-8050056175193481693, %r12
	movq	%rax, -432(%rbp)
	movabsq	$-1749540032614691874, %rax
	movabsq	$1600686389938274267, %r13
	movq	%rax, -496(%rbp)
	movq	$0, -584(%rbp)
	movq	$0, -536(%rbp)
	movq	$0, -528(%rbp)
	movq	$0, -576(%rbp)
	movq	$0, -520(%rbp)
	movq	$0, -512(%rbp)
	movq	$0, -560(%rbp)
	movl	%r14d, -352(%rbp)
	jmp	.L383
.L514:
	vmovdqa	32(%rcx), %ymm0
	vpxor	32(%rax), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L376
	xorl	%eax, %eax
.L377:
	vmovdqa	(%rcx), %xmm0
	vpsrldq	$8, %xmm0, %xmm2
	vpsrldq	$4, %xmm0, %xmm4
	vpmovzxbd	%xmm0, %xmm1
	vpmulld	.LC0(%rip), %xmm1, %xmm12
	vpmovzxbd	%xmm2, %xmm2
	vpsrldq	$12, %xmm0, %xmm0
	vpmovzxbd	%xmm4, %xmm4
	vpmulld	.LC2(%rip), %xmm2, %xmm8
	vmovdqa	%xmm2, -208(%rbp)
	vmovdqa	16(%rcx), %xmm2
	vpmovzxbd	%xmm0, %xmm5
	vpmulld	.LC3(%rip), %xmm5, %xmm0
	vmovdqa	%xmm5, -224(%rbp)
	vpaddd	%xmm4, %xmm1, %xmm1
	vpmulld	.LC1(%rip), %xmm4, %xmm3
	vpsrldq	$4, %xmm2, %xmm5
	vpmovzxbd	%xmm2, %xmm6
	vpmulld	.LC4(%rip), %xmm6, %xmm11
	vpmovzxbd	%xmm5, %xmm7
	vpsrldq	$8, %xmm2, %xmm5
	vmovdqa	%xmm6, -240(%rbp)
	vpsrldq	$12, %xmm2, %xmm2
	vpmovzxbd	%xmm5, %xmm14
	vmovdqa	%xmm7, -256(%rbp)
	vpaddd	-256(%rbp), %xmm1, %xmm1
	vpmovzxbd	%xmm2, %xmm15
	vmovdqa	%xmm14, -272(%rbp)
	vpmulld	.LC5(%rip), %xmm7, %xmm2
	vpmulld	.LC6(%rip), %xmm14, %xmm7
	vmovdqa	%xmm2, -176(%rbp)
	vmovdqa	32(%rcx), %xmm2
	vpmulld	.LC7(%rip), %xmm15, %xmm14
	vmovdqa	%xmm15, -288(%rbp)
	vpsrldq	$4, %xmm2, %xmm5
	vpmovzxbd	%xmm2, %xmm15
	vpmovzxbd	%xmm5, %xmm10
	vpsrldq	$8, %xmm2, %xmm5
	vpaddd	%xmm15, %xmm1, %xmm1
	vpsrldq	$12, %xmm2, %xmm2
	vpmovzxbd	%xmm5, %xmm13
	vpmulld	.LC18(%rip), %xmm13, %xmm6
	vmovdqa	%xmm6, -192(%rbp)
	vpmovzxbd	%xmm2, %xmm9
	vmovdqa	48(%rcx), %xmm2
	vpmulld	.LC19(%rip), %xmm9, %xmm6
	vmovdqa	%xmm13, -320(%rbp)
	vmovdqa	%xmm9, -336(%rbp)
	vpmulld	.LC16(%rip), %xmm15, %xmm5
	vmovdqa	-288(%rbp), %xmm15
	vpmovzxbd	%xmm2, %xmm13
	vpsrldq	$4, %xmm2, %xmm9
	vmovdqa	%xmm10, -304(%rbp)
	vpmulld	.LC17(%rip), %xmm10, %xmm10
	vmovdqa	%xmm13, -400(%rbp)
	vpmovzxbd	%xmm9, %xmm13
	vpsrldq	$8, %xmm2, %xmm9
	vpsrldq	$12, %xmm2, %xmm2
	vpmovzxbd	%xmm9, %xmm9
	vpmovzxbd	%xmm2, %xmm2
	vpaddd	%xmm2, %xmm1, %xmm1
	vmovdqa	%xmm2, -256(%rbp)
	vpaddd	-272(%rbp), %xmm15, %xmm2
	vpaddd	-320(%rbp), %xmm2, %xmm2
	vmovdqa	-400(%rbp), %xmm15
	vpaddd	-304(%rbp), %xmm2, %xmm2
	vmovdqa	-224(%rbp), %xmm4
	vpaddd	%xmm15, %xmm2, %xmm2
	vpaddd	%xmm2, %xmm1, %xmm2
	vpaddd	-208(%rbp), %xmm4, %xmm1
	vmovdqa	.LC20(%rip), %xmm4
	vpaddd	-240(%rbp), %xmm1, %xmm1
	vpaddd	-336(%rbp), %xmm1, %xmm1
	vpmulld	%xmm15, %xmm4, %xmm4
	vpaddd	%xmm9, %xmm1, %xmm1
	vpmulld	.LC22(%rip), %xmm9, %xmm9
	vpaddd	%xmm13, %xmm1, %xmm1
	vpmulld	.LC21(%rip), %xmm13, %xmm13
	vpaddd	%xmm1, %xmm2, %xmm1
	vmovdqa	-256(%rbp), %xmm2
	vpmulld	.LC23(%rip), %xmm2, %xmm15
	vpaddd	-176(%rbp), %xmm11, %xmm2
	vmovdqa	%xmm15, -224(%rbp)
	vmovdqa	%xmm4, -208(%rbp)
	vpaddd	%xmm0, %xmm8, %xmm4
	vpaddd	%xmm5, %xmm2, %xmm2
	vpaddd	%xmm14, %xmm4, %xmm4
	vpaddd	-192(%rbp), %xmm4, %xmm4
	vpaddd	%xmm6, %xmm2, %xmm2
	vpaddd	%xmm9, %xmm2, %xmm2
	vpaddd	%xmm13, %xmm4, %xmm4
	vpaddd	%xmm2, %xmm4, %xmm4
	vpaddd	%xmm3, %xmm12, %xmm2
	vpaddd	%xmm7, %xmm2, %xmm2
	vpaddd	%xmm10, %xmm2, %xmm2
	vpaddd	-208(%rbp), %xmm2, %xmm2
	vpaddd	%xmm15, %xmm2, %xmm2
	vpmulld	.LC1(%rip), %xmm3, %xmm15
	vpaddd	%xmm2, %xmm4, %xmm2
	vpmulld	.LC0(%rip), %xmm12, %xmm4
	vpaddd	%xmm4, %xmm15, %xmm4
	vpmulld	.LC4(%rip), %xmm11, %xmm15
	vpaddd	%xmm15, %xmm4, %xmm15
	vpmulld	.LC17(%rip), %xmm10, %xmm4
	vpaddd	%xmm4, %xmm15, %xmm4
	vpmulld	.LC22(%rip), %xmm9, %xmm15
	vpaddd	%xmm15, %xmm4, %xmm4
	vpmulld	.LC7(%rip), %xmm14, %xmm15
	vmovdqa	%xmm4, -240(%rbp)
	vpmulld	.LC6(%rip), %xmm7, %xmm4
	vpaddd	%xmm4, %xmm15, %xmm4
	vpmulld	.LC19(%rip), %xmm6, %xmm15
	vpaddd	%xmm15, %xmm4, %xmm15
	vpmulld	.LC16(%rip), %xmm5, %xmm4
	vpaddd	%xmm4, %xmm15, %xmm4
	vpmulld	.LC21(%rip), %xmm13, %xmm15
	vpaddd	%xmm15, %xmm4, %xmm4
	vpaddd	-240(%rbp), %xmm4, %xmm4
	vpmulld	.LC2(%rip), %xmm8, %xmm15
	vmovdqa	%xmm4, -240(%rbp)
	vpmulld	.LC3(%rip), %xmm0, %xmm4
	vpaddd	%xmm15, %xmm4, %xmm15
	vmovdqa	-176(%rbp), %xmm4
	vpmulld	.LC14(%rip), %xmm14, %xmm14
	vpmulld	.LC10(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm14, %xmm7
	vpmulld	.LC9(%rip), %xmm3, %xmm3
	vpmulld	.LC8(%rip), %xmm12, %xmm12
	vpaddd	%xmm12, %xmm3, %xmm3
	vpmulld	.LC25(%rip), %xmm6, %xmm6
	vpmulld	.LC11(%rip), %xmm11, %xmm11
	vpaddd	%xmm6, %xmm7, %xmm6
	vpaddd	%xmm11, %xmm3, %xmm3
	vpmulld	.LC5(%rip), %xmm4, %xmm4
	vpmulld	.LC27(%rip), %xmm5, %xmm5
	vpaddd	%xmm4, %xmm15, %xmm4
	vpaddd	%xmm5, %xmm6, %xmm5
	vpmulld	.LC28(%rip), %xmm10, %xmm10
	vmovdqa	-192(%rbp), %xmm15
	vpmulld	.LC26(%rip), %xmm13, %xmm13
	vpaddd	%xmm10, %xmm3, %xmm3
	vpaddd	%xmm13, %xmm5, %xmm5
	vpmulld	.LC18(%rip), %xmm15, %xmm15
	vpmulld	.LC31(%rip), %xmm9, %xmm9
	vpaddd	%xmm15, %xmm4, %xmm15
	vpaddd	%xmm9, %xmm3, %xmm3
	vpmulld	.LC13(%rip), %xmm0, %xmm0
	vpmulld	.LC12(%rip), %xmm8, %xmm8
	vpaddd	%xmm8, %xmm0, %xmm0
	vpaddd	%xmm3, %xmm5, %xmm3
	vmovdqa	-224(%rbp), %xmm4
	vmovdqa	-176(%rbp), %xmm5
	vpmulld	.LC23(%rip), %xmm4, %xmm4
	vpaddd	%xmm4, %xmm15, %xmm4
	vpmulld	.LC15(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm0
	vmovdqa	-208(%rbp), %xmm15
	vpmulld	.LC20(%rip), %xmm15, %xmm15
	vpaddd	%xmm15, %xmm4, %xmm4
	vmovdqa	-192(%rbp), %xmm15
	vpaddd	-240(%rbp), %xmm4, %xmm4
	vpmulld	.LC24(%rip), %xmm15, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm0
	vmovdqa	-224(%rbp), %xmm5
	vmovdqa	-208(%rbp), %xmm15
	vpmulld	.LC30(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm0
	vpmulld	.LC29(%rip), %xmm15, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm3, %xmm0
	vpunpckhqdq	%xmm1, %xmm1, %xmm3
	vpaddd	%xmm3, %xmm1, %xmm1
	vpshufd	$177, %xmm1, %xmm3
	vpaddd	%xmm1, %xmm3, %xmm1
	vpmovzxdq	%xmm1, %xmm3
	vpunpckhqdq	%xmm2, %xmm2, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm2
	vmovq	%xmm3, -112(%rbp)
	vpshufd	$177, %xmm2, %xmm1
	vpaddd	%xmm2, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm4, %xmm4, %xmm1
	vpaddd	%xmm1, %xmm4, %xmm4
	vmovq	%xmm2, -104(%rbp)
	vpshufd	$177, %xmm4, %xmm1
	vpaddd	%xmm4, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovq	%xmm2, -96(%rbp)
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	vpmovzxdq	%xmm0, %xmm2
	vmovq	%xmm2, -88(%rbp)
	testl	%eax, %eax
	jne	.L378
	movq	-424(%rbp), %rax
	salq	$5, %rdx
	vmovdqa	-112(%rbp), %ymm0
	vpxor	16384(%rdx,%rax), %ymm0, %ymm0
	xorl	%eax, %eax
	vptest	%ymm0, %ymm0
	sete	%al
	addq	%rax, -560(%rbp)
.L378:
	movq	-424(%rbp), %rax
	movq	41288(%rax), %rax
	cmpl	$1, -368(%rbp)
	je	.L512
	movq	-528(%rbp), %rdx
	movq	-424(%rbp), %rcx
	addq	$1, -584(%rbp)
	addq	%rax, %rdx
	subq	%r15, %rdx
	movq	%rdx, -528(%rbp)
	movq	-536(%rbp), %rdx
	addq	41296(%rcx), %rdx
	subq	%r14, %rdx
	movq	%rdx, -536(%rbp)
.L382:
	movl	-480(%rbp), %edx
	addl	$1, %edx
	cmpl	%edx, -352(%rbp)
	je	.L513
	movl	%edx, -480(%rbp)
	movq	%rax, %r15
	vzeroupper
.L383:
	movq	-496(%rbp), %rcx
	movq	-432(%rbp), %rax
	movl	-480(%rbp), %r11d
	xorq	%r13, %rax
	movq	%rcx, %r9
	addq	%r13, %rcx
	andl	$1, %r11d
	xorq	%r12, %r9
	movq	%rax, %rdx
	rorx	$47, %rcx, %rcx
	leal	1(%r11), %esi
	xorq	%r12, %rdx
	movq	%r9, %rdi
	salq	$17, %r12
	movl	%esi, -368(%rbp)
	xorq	%r13, %rdi
	xorq	%rax, %r12
	movq	%rdx, %r13
	xorq	%rdi, %r12
	rorx	$19, %r9, %r9
	movq	%rdi, %rax
	xorq	%r9, %r13
	addq	%r9, %rdi
	xorq	%r13, %rax
	rorx	$19, %r13, %r8
	movzbl	%cl, %r10d
	movq	-424(%rbp), %rsi
	rorx	$47, %rdi, %r9
	movzbl	%cl, %ecx
	movq	%rax, %r13
	andl	$63, %r9d
	movq	41296(%rsi), %r14
	movq	%rdx, %rsi
	salq	$17, %rdx
	xorq	%r12, %rsi
	xorq	%r12, %rdx
	movq	%rsi, %rdi
	xorq	%rax, %rdx
	movq	%rsi, %r12
	salq	$17, %rsi
	xorq	%r8, %rdi
	xorq	%rdx, %rsi
	xorq	%rdx, %r12
	addq	%r8, %rax
	rorx	$19, %rdi, %rdx
	xorq	%rdi, %r13
	movq	%rdx, -496(%rbp)
	movq	%rcx, %rdx
	leaq	contents.4(%rip), %rdi
	salq	$6, %rdx
	rorx	$47, %rax, %rax
	movq	%rsi, -432(%rbp)
	addq	%rdi, %rdx
	movl	%eax, %edi
	imulq	%rbx, %rdi
	shrq	$39, %rdi
	leal	1(%rax,%rdi), %eax
	xorb	%al, (%rdx,%r9)
	testl	%r11d, %r11d
	je	.L375
	movq	-496(%rbp), %r8
	xorq	%r13, %rsi
	movq	%r12, %r11
	movq	%rsi, %r9
	salq	$17, %r11
	movq	%r8, %rdi
	xorq	%r12, %r9
	xorq	%r11, %rsi
	xorq	%r12, %rdi
	movq	%r9, %r11
	movq	%rdi, %rax
	rorx	$19, %rdi, %rdi
	xorq	%rdi, %r11
	xorq	%r13, %rax
	addq	%r8, %r13
	rorx	$47, %r13, %r8
	movq	%r11, %r13
	xorq	%rax, %rsi
	xorq	%rax, %r13
	addq	%rdi, %rax
	movq	%rsi, %r12
	rorx	$47, %rax, %rax
	movl	%eax, %edi
	xorq	%r9, %r12
	salq	$17, %r9
	imulq	%rbx, %rdi
	xorq	%rsi, %r9
	rorx	$19, %r11, %rsi
	movq	%rsi, -496(%rbp)
	movq	%r8, %rsi
	movq	%r9, -432(%rbp)
	andl	$63, %esi
	shrq	$39, %rdi
	leal	1(%rax,%rdi), %eax
	xorb	%al, (%rdx,%rsi)
.L375:
	movq	%rcx, %rax
	leaq	contents.4(%rip), %rdx
	movl	%r10d, %esi
	movl	%r10d, %edi
	salq	$6, %rax
	movq	%rcx, -192(%rbp)
	addq	%rdx, %rax
	movq	%rax, %rdx
	movq	%rax, -176(%rbp)
	call	sqm_write.constprop.0.isra.0
	movq	-192(%rbp), %rcx
	leaq	sqm_slot_of(%rip), %rax
	movl	(%rax,%rcx,4), %ecx
	movq	-176(%rbp), %rax
	movl	%ecx, %edx
	movzbl	%cl, %ecx
	sarl	$8, %edx
	movslq	%edx, %rdx
	salq	$5, %rdx
	addq	%rcx, %rdx
	movq	%rdx, %rcx
	salq	$6, %rcx
	addq	-424(%rbp), %rcx
	vmovdqa	(%rcx), %ymm0
	vpxor	(%rax), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	je	.L514
.L376:
	movl	$1, %eax
	jmp	.L377
.L512:
	movq	-512(%rbp), %rdx
	movq	-424(%rbp), %rcx
	addq	$1, -576(%rbp)
	addq	%rax, %rdx
	subq	%r15, %rdx
	movq	%rdx, -512(%rbp)
	movq	-520(%rbp), %rdx
	addq	41296(%rcx), %rdx
	subq	%r14, %rdx
	movq	%rdx, -520(%rbp)
	jmp	.L382
.L513:
	movl	-352(%rbp), %eax
	movq	%r13, -568(%rbp)
	movl	$41312, %edx
	leaq	slot_snap.1(%rip), %rbx
	movq	-424(%rbp), %rsi
	leaq	action.0(%rip), %r14
	movq	%rax, -504(%rbp)
	leaq	snap.3(%rip), %rax
	movq	%rax, -488(%rbp)
	movq	%rax, %rdi
	vzeroupper
	call	memcpy@PLT
	leaq	csnap.2(%rip), %rax
	movl	$16384, %edx
	leaq	contents.4(%rip), %rsi
	movq	%rax, %rdi
	movq	%rax, -608(%rbp)
	call	memcpy@PLT
	movl	$4096, %edx
	leaq	sqm_slot_of(%rip), %rsi
	movq	%rbx, %rdi
	call	memcpy@PLT
	movq	%rbx, -624(%rbp)
	vpxor	%xmm2, %xmm2, %xmm2
	movl	$0, -600(%rbp)
	movq	$0, -592(%rbp)
	movq	$0, -552(%rbp)
	movq	$0, -544(%rbp)
	vmovdqa	%ymm2, -400(%rbp)
.L400:
	movq	-424(%rbp), %r15
	movq	-488(%rbp), %rsi
	movl	$41312, %edx
	vzeroupper
	movq	%r15, %rdi
	call	memcpy@PLT
	movq	-568(%rbp), %rbx
	movq	-496(%rbp), %rcx
	movq	-432(%rbp), %rdx
	leaq	(%rcx,%rbx), %rdi
	movq	%rcx, %r8
	movq	%r12, %rcx
	movq	%rbx, %rsi
	xorq	%rbx, %rdx
	xorq	%r12, %r8
	salq	$17, %rcx
	rorx	$47, %rdi, %rdi
	movq	%rdx, %rax
	xorq	%r8, %rsi
	xorq	%rdx, %rcx
	rorx	$19, %r8, %r8
	xorq	%r12, %rax
	xorq	%rsi, %rcx
	movl	%edi, %r9d
	andl	$7, %edi
	movq	%rax, %r12
	movq	%rcx, %rbx
	andl	$7, %r9d
	movq	%rdi, -648(%rbp)
	xorq	%r8, %r12
	xorq	%rax, %rbx
	salq	$17, %rax
	movl	%r9d, -628(%rbp)
	movq	%r12, %rdx
	xorq	%rax, %rcx
	movq	%rbx, %r11
	rorx	$19, %r12, %r12
	xorq	%rsi, %rdx
	xorq	%r12, %r11
	addq	%r8, %rsi
	xorq	%rdx, %rcx
	rorx	$47, %rsi, %r10
	movq	%r11, %rsi
	rorx	$19, %r11, %r11
	movq	%rcx, %rax
	xorq	%rdx, %rsi
	addq	%r12, %rdx
	movl	%r10d, %r8d
	xorq	%rbx, %rax
	salq	$17, %rbx
	andl	$31, %r8d
	rorx	$47, %rdx, %rdx
	xorq	%rbx, %rcx
	movq	%rax, %rbx
	andl	$63, %edx
	movl	%r8d, -632(%rbp)
	xorq	%rsi, %rcx
	xorq	%r11, %rbx
	movq	%rcx, %r12
	movq	%rbx, %r13
	xorq	%rax, %r12
	salq	$17, %rax
	xorq	%rsi, %r13
	xorq	%rcx, %rax
	movq	%r10, %rcx
	movq	%rdi, %r10
	movq	%r12, -640(%rbp)
	andl	$31, %ecx
	movq	%rax, -432(%rbp)
	salq	$5, %r10
	rorx	$19, %rbx, %rax
	movq	%rax, -496(%rbp)
	leaq	(%rsi,%r11), %rax
	addq	%rcx, %r10
	movl	$2155905153, %r11d
	rorx	$47, %rax, %rax
	movl	%eax, %esi
	salq	$6, %r10
	movq	%rcx, -656(%rbp)
	imulq	%r11, %rsi
	addq	%r15, %r10
	leaq	cell.5(%rip), %r15
	xorl	%r11d, %r11d
	movq	%r15, -424(%rbp)
	movq	%r13, -568(%rbp)
	xorl	%r13d, %r13d
	shrq	$39, %rsi
	leal	1(%rax,%rsi), %eax
	leaq	16384+cell.5(%rip), %rsi
	xorb	%al, (%r10,%rdx)
	xorl	%edx, %edx
	leaq	cell.5(%rip), %r10
.L384:
	movl	%edx, %eax
	movq	%r10, -416(%rbp)
	movq	%rsi, %r9
	movq	%r10, %rcx
	salq	$5, %rax
	movl	%edx, -448(%rbp)
	xorl	%edi, %edi
	movq	%r11, %r12
	movq	%rax, -368(%rbp)
	movq	%rsi, -464(%rbp)
	.p2align 4
	.p2align 3
.L396:
	cmpb	$0, 40960(%r15,%rdi)
	je	.L395
	vmovdqa	(%rcx), %xmm7
	vmovdqa	16(%rcx), %xmm8
	leal	(%rdi,%r13), %eax
	movb	$0, (%r14,%rax)
	vpsrldq	$4, %xmm7, %xmm13
	vpmovzxbd	%xmm7, %xmm0
	vpmovzxbd	%xmm8, %xmm5
	vpmulld	.LC0(%rip), %xmm0, %xmm2
	vpsrldq	$4, %xmm8, %xmm12
	vpsrldq	$8, %xmm7, %xmm3
	vpmovzxbd	%xmm13, %xmm1
	vpmulld	.LC1(%rip), %xmm1, %xmm6
	vpsrldq	$8, %xmm8, %xmm4
	vmovdqa	%xmm6, -192(%rbp)
	vmovdqa	32(%rcx), %xmm6
	vpsrldq	$12, %xmm8, %xmm8
	vpsrldq	$12, %xmm7, %xmm7
	vpmovzxbd	%xmm12, %xmm15
	vpmovzxbd	%xmm8, %xmm14
	vmovdqa	%xmm1, -256(%rbp)
	vpsrldq	$8, %xmm6, %xmm11
	vpsrldq	$4, %xmm6, %xmm10
	vpmovzxbd	%xmm6, %xmm9
	vmovdqa	%xmm2, -176(%rbp)
	vpmovzxbd	%xmm7, %xmm7
	vpmovzxbd	%xmm11, %xmm2
	vpmovzxbd	%xmm10, %xmm10
	vpmulld	.LC3(%rip), %xmm7, %xmm1
	vpmovzxbd	%xmm3, %xmm3
	vpsrldq	$12, %xmm6, %xmm6
	vmovdqa	%xmm1, -208(%rbp)
	vmovdqa	48(%rcx), %xmm1
	vpmulld	.LC2(%rip), %xmm3, %xmm13
	vmovdqa	%xmm15, -288(%rbp)
	vpmulld	.LC16(%rip), %xmm9, %xmm8
	vpmulld	.LC17(%rip), %xmm10, %xmm11
	vpmovzxbd	%xmm6, %xmm6
	vmovdqa	%xmm9, -320(%rbp)
	vpmulld	.LC5(%rip), %xmm15, %xmm15
	vpaddd	-256(%rbp), %xmm0, %xmm0
	vpmovzxbd	%xmm4, %xmm4
	vpaddd	-288(%rbp), %xmm0, %xmm0
	vpmulld	.LC6(%rip), %xmm4, %xmm12
	vpaddd	-320(%rbp), %xmm0, %xmm0
	vmovdqa	%xmm5, -272(%rbp)
	vpaddd	%xmm7, %xmm3, %xmm3
	vpmulld	.LC4(%rip), %xmm5, %xmm5
	vpmovzxbd	%xmm1, %xmm9
	vmovdqa	%xmm5, -224(%rbp)
	vpsrldq	$4, %xmm1, %xmm5
	vmovdqa	%xmm14, -304(%rbp)
	vpmovzxbd	%xmm5, %xmm5
	vpmulld	.LC7(%rip), %xmm14, %xmm14
	vmovdqa	%xmm10, -336(%rbp)
	vpmulld	.LC19(%rip), %xmm6, %xmm10
	vmovdqa	%xmm14, -240(%rbp)
	vpmulld	.LC18(%rip), %xmm2, %xmm14
	vmovdqa	%xmm2, -352(%rbp)
	vpaddd	-304(%rbp), %xmm4, %xmm4
	vpaddd	-272(%rbp), %xmm3, %xmm3
	vpsrldq	$8, %xmm1, %xmm2
	vpaddd	-352(%rbp), %xmm4, %xmm4
	vpsrldq	$12, %xmm1, %xmm1
	vpaddd	-336(%rbp), %xmm4, %xmm4
	vpmovzxbd	%xmm2, %xmm2
	vpmovzxbd	%xmm1, %xmm1
	vpaddd	%xmm6, %xmm3, %xmm3
	vmovdqa	-176(%rbp), %xmm7
	vpaddd	%xmm9, %xmm4, %xmm4
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovdqa	-192(%rbp), %xmm6
	vpmulld	.LC20(%rip), %xmm9, %xmm9
	vpaddd	%xmm2, %xmm3, %xmm3
	vpaddd	%xmm4, %xmm0, %xmm0
	vpmulld	.LC22(%rip), %xmm2, %xmm2
	vpmulld	.LC23(%rip), %xmm1, %xmm1
	vpaddd	%xmm5, %xmm3, %xmm3
	vpaddd	-224(%rbp), %xmm15, %xmm4
	vpmulld	.LC21(%rip), %xmm5, %xmm5
	vpaddd	%xmm3, %xmm0, %xmm0
	vpaddd	-208(%rbp), %xmm13, %xmm3
	vpaddd	-240(%rbp), %xmm3, %xmm3
	vpaddd	%xmm8, %xmm4, %xmm4
	vpaddd	%xmm10, %xmm4, %xmm4
	vpaddd	%xmm14, %xmm3, %xmm3
	vpaddd	%xmm2, %xmm4, %xmm4
	vpaddd	%xmm5, %xmm3, %xmm3
	vpaddd	%xmm4, %xmm3, %xmm3
	vpaddd	%xmm7, %xmm6, %xmm4
	vpaddd	%xmm12, %xmm4, %xmm4
	vpaddd	%xmm11, %xmm4, %xmm4
	vpaddd	%xmm9, %xmm4, %xmm4
	vpaddd	%xmm1, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm3, %xmm3
	vpmulld	.LC1(%rip), %xmm6, %xmm4
	vpmulld	.LC0(%rip), %xmm7, %xmm6
	vpaddd	%xmm6, %xmm4, %xmm6
	vmovdqa	-224(%rbp), %xmm4
	vpmulld	.LC4(%rip), %xmm4, %xmm4
	vpaddd	%xmm4, %xmm6, %xmm4
	vpmulld	.LC17(%rip), %xmm11, %xmm6
	vpaddd	%xmm6, %xmm4, %xmm6
	vpmulld	.LC22(%rip), %xmm2, %xmm4
	vpaddd	%xmm4, %xmm6, %xmm6
	vmovdqa	-240(%rbp), %xmm4
	vpmulld	.LC7(%rip), %xmm4, %xmm7
	vpmulld	.LC6(%rip), %xmm12, %xmm4
	vpaddd	%xmm4, %xmm7, %xmm4
	vpmulld	.LC19(%rip), %xmm10, %xmm7
	vpaddd	%xmm7, %xmm4, %xmm7
	vpmulld	.LC16(%rip), %xmm8, %xmm4
	vpaddd	%xmm4, %xmm7, %xmm4
	vpmulld	.LC21(%rip), %xmm5, %xmm7
	vpaddd	%xmm7, %xmm4, %xmm4
	vpmulld	.LC2(%rip), %xmm13, %xmm7
	vpaddd	%xmm4, %xmm6, %xmm6
	vmovdqa	-208(%rbp), %xmm4
	vpmulld	.LC3(%rip), %xmm4, %xmm4
	vpaddd	%xmm7, %xmm4, %xmm7
	vpmulld	.LC5(%rip), %xmm15, %xmm4
	vpaddd	%xmm4, %xmm7, %xmm4
	vpmulld	.LC18(%rip), %xmm14, %xmm7
	vpaddd	%xmm7, %xmm4, %xmm7
	vpmulld	.LC23(%rip), %xmm1, %xmm4
	vpaddd	%xmm4, %xmm7, %xmm4
	vpmulld	.LC20(%rip), %xmm9, %xmm7
	vpaddd	%xmm7, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm6, %xmm4
	vmovdqa	-192(%rbp), %xmm6
	vmovdqa	-176(%rbp), %xmm7
	vpmulld	.LC9(%rip), %xmm6, %xmm6
	vpmulld	.LC8(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm7
	vmovdqa	-224(%rbp), %xmm6
	vpmulld	.LC11(%rip), %xmm6, %xmm6
	vpmulld	.LC31(%rip), %xmm2, %xmm2
	vpaddd	%xmm6, %xmm7, %xmm6
	vpmulld	.LC28(%rip), %xmm11, %xmm7
	vpmulld	.LC26(%rip), %xmm5, %xmm5
	vpmulld	.LC30(%rip), %xmm1, %xmm1
	vpaddd	%xmm7, %xmm6, %xmm7
	vpmulld	.LC29(%rip), %xmm9, %xmm9
	vpaddd	%xmm2, %xmm7, %xmm2
	vmovdqa	-240(%rbp), %xmm7
	vpmulld	.LC14(%rip), %xmm7, %xmm6
	vpmulld	.LC10(%rip), %xmm12, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vpmulld	.LC25(%rip), %xmm10, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vpmulld	.LC27(%rip), %xmm8, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vpaddd	%xmm5, %xmm6, %xmm5
	vpmulld	.LC12(%rip), %xmm13, %xmm6
	vpaddd	%xmm5, %xmm2, %xmm2
	vmovdqa	-208(%rbp), %xmm5
	vpmulld	.LC13(%rip), %xmm5, %xmm5
	vpaddd	%xmm6, %xmm5, %xmm5
	vpmulld	.LC15(%rip), %xmm15, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm5
	vpmulld	.LC24(%rip), %xmm14, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm5
	vpaddd	%xmm1, %xmm5, %xmm1
	vpaddd	%xmm9, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm1
	vpunpckhqdq	%xmm0, %xmm0, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vpshufd	$177, %xmm0, %xmm2
	vpaddd	%xmm0, %xmm2, %xmm0
	vmovd	%xmm0, %esi
	vpunpckhqdq	%xmm3, %xmm3, %xmm0
	vpaddd	%xmm0, %xmm3, %xmm3
	movq	%rsi, -112(%rbp)
	vpshufd	$177, %xmm3, %xmm0
	vpaddd	%xmm3, %xmm0, %xmm0
	vmovd	%xmm0, %r8d
	vpunpckhqdq	%xmm4, %xmm4, %xmm0
	vpaddd	%xmm0, %xmm4, %xmm4
	movq	%r8, -104(%rbp)
	vpshufd	$177, %xmm4, %xmm0
	vpaddd	%xmm4, %xmm0, %xmm0
	vmovd	%xmm0, %r10d
	vpunpckhqdq	%xmm1, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	movq	%r10, -96(%rbp)
	vpshufd	$177, %xmm1, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %r11d
	movq	%r11, -88(%rbp)
	vmovdqa	-112(%rbp), %ymm0
	vpxor	(%r9), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	je	.L395
	movb	$1, (%r14,%rax)
	subq	(%r9), %rsi
	je	.L388
	leaq	255(%rsi), %rax
	subq	8(%r9), %r8
	subq	16(%r9), %r10
	subq	24(%r9), %r11
	cmpq	$510, %rax
	ja	.L389
	movq	%r8, %rax
	cqto
	idivq	%rsi
	testq	%rdx, %rdx
	jne	.L389
	leaq	-1(%rax), %rdx
	cmpq	$63, %rdx
	ja	.L389
	movq	%rax, %rdx
	imulq	%rax, %rdx
	imulq	%rsi, %rdx
	cmpq	%rdx, %r10
	je	.L515
	.p2align 4
	.p2align 3
.L389:
	movq	%rsi, %rbx
	movq	%r8, %rax
	imulq	%r10, %rbx
	imulq	%r8, %rax
	subq	%rax, %rbx
	je	.L388
	movq	%rsi, %rax
	movq	%r8, %rdx
	imulq	%r10, %rdx
	imulq	%r11, %rax
	subq	%rdx, %rax
	cqto
	idivq	%rbx
	movq	%rax, -176(%rbp)
	testq	%rdx, %rdx
	jne	.L388
	movq	%r8, %rdx
	imulq	%r11, %rdx
	movq	%rdx, %rax
	movq	%r10, %rdx
	imulq	%r10, %rdx
	subq	%rdx, %rax
	cqto
	idivq	%rbx
	testq	%rdx, %rdx
	jne	.L388
	movq	-176(%rbp), %rbx
	negq	%rax
	movq	%rbx, %rdx
	imulq	%rbx, %rdx
	leaq	(%rdx,%rax,4), %rbx
	testq	%rbx, %rbx
	jle	.L388
	movl	$1, %eax
	cmpq	$1, %rbx
	je	.L391
	.p2align 4
	.p2align 4
	.p2align 3
.L392:
	addq	$1, %rax
	movq	%rax, %rdx
	imulq	%rax, %rdx
	cmpq	%rbx, %rdx
	jl	.L392
	je	.L391
	.p2align 4
	.p2align 3
.L388:
	addq	$1, %r12
.L395:
	addq	$1, %rdi
	addq	$64, %rcx
	addq	$32, %r9
	cmpq	$32, %rdi
	jne	.L396
	movl	-448(%rbp), %edx
	movq	%r12, %r11
	addq	$32, %r13
	addq	$32, %r15
	movq	-416(%rbp), %r10
	movq	-464(%rbp), %rsi
	addl	$1, %edx
	addq	$2048, %r10
	addq	$1024, %rsi
	cmpl	$8, %edx
	jne	.L384
	movl	-628(%rbp), %r9d
	movl	-632(%rbp), %r8d
	leaq	sqm_item_at(%rip), %rbx
	movq	-648(%rbp), %rdi
	addq	%r11, -592(%rbp)
	sall	$5, %r9d
	movq	-656(%rbp), %rcx
	movq	-640(%rbp), %r12
	leal	(%r9,%r8), %eax
	cmpb	$1, (%r14,%rax)
	movq	%rdi, %rax
	sbbq	$-1, -544(%rbp)
	salq	$5, %rax
	addq	%rcx, %rax
	movq	%rax, %rdx
	movslq	(%rbx,%rax,4), %rax
	salq	$6, %rdx
	addq	-424(%rbp), %rdx
	salq	$6, %rax
	addq	-608(%rbp), %rax
	vmovdqa	(%rdx), %ymm0
	vpxor	(%rax), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L398
	vmovdqa	32(%rdx), %ymm0
	vpxor	32(%rax), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L398
	xorl	%eax, %eax
.L399:
	cmpl	$1, %eax
	movl	-480(%rbp), %edx
	adcq	$0, -552(%rbp)
	cmpl	%edx, -600(%rbp)
	je	.L516
	movl	-600(%rbp), %eax
	addl	$1, %eax
	movl	%eax, -600(%rbp)
	jmp	.L400
.L515:
	movq	%rax, %rdx
	imulq	%r10, %rdx
	cmpq	%rdx, %r11
	jne	.L389
	subl	$1, %eax
	subb	%sil, (%rcx,%rax)
.L390:
	vmovdqa	(%rcx), %xmm7
	vmovdqa	16(%rcx), %xmm8
	vpsrldq	$4, %xmm7, %xmm11
	vpmovzxbd	%xmm8, %xmm4
	vpmovzxbd	%xmm7, %xmm5
	vpmulld	.LC0(%rip), %xmm5, %xmm2
	vpsrldq	$4, %xmm8, %xmm10
	vpsrldq	$8, %xmm8, %xmm0
	vpmovzxbd	%xmm11, %xmm1
	vpmulld	.LC1(%rip), %xmm1, %xmm6
	vpsrldq	$12, %xmm8, %xmm8
	vpmovzxbd	%xmm10, %xmm13
	vmovdqa	%xmm6, -192(%rbp)
	vmovdqa	32(%rcx), %xmm6
	vpmovzxbd	%xmm8, %xmm12
	vpsrldq	$8, %xmm7, %xmm3
	vpmulld	.LC5(%rip), %xmm13, %xmm15
	vmovdqa	%xmm13, -288(%rbp)
	vpsrldq	$12, %xmm7, %xmm7
	vpmovzxbd	%xmm6, %xmm14
	vpmovzxbd	%xmm3, %xmm3
	vpmulld	.LC7(%rip), %xmm12, %xmm13
	vmovdqa	%xmm12, -304(%rbp)
	vpsrldq	$4, %xmm6, %xmm12
	vpmovzxbd	%xmm7, %xmm7
	vpmulld	.LC2(%rip), %xmm3, %xmm11
	vpmovzxbd	%xmm12, %xmm8
	vpmovzxbd	%xmm0, %xmm0
	vmovdqa	%xmm13, -240(%rbp)
	vpmulld	.LC4(%rip), %xmm4, %xmm10
	vpsrldq	$8, %xmm6, %xmm13
	vmovdqa	%xmm1, -256(%rbp)
	vpsrldq	$12, %xmm6, %xmm6
	vpmulld	.LC3(%rip), %xmm7, %xmm1
	vpmovzxbd	%xmm13, %xmm9
	vpmovzxbd	%xmm6, %xmm6
	vmovdqa	%xmm1, -208(%rbp)
	vmovdqa	48(%rcx), %xmm1
	vpmulld	.LC16(%rip), %xmm14, %xmm12
	vmovdqa	%xmm8, -336(%rbp)
	vpmulld	.LC19(%rip), %xmm6, %xmm13
	vpmulld	.LC17(%rip), %xmm8, %xmm8
	vmovdqa	%xmm9, -352(%rbp)
	vpaddd	%xmm7, %xmm3, %xmm3
	vpaddd	-256(%rbp), %xmm5, %xmm5
	vmovdqa	%xmm2, -176(%rbp)
	vpsrldq	$4, %xmm1, %xmm2
	vmovdqa	%xmm4, -272(%rbp)
	vpmovzxbd	%xmm2, %xmm2
	vpmulld	.LC6(%rip), %xmm0, %xmm4
	vpaddd	-304(%rbp), %xmm0, %xmm0
	vmovdqa	%xmm4, -224(%rbp)
	vpaddd	-352(%rbp), %xmm0, %xmm0
	vpaddd	-336(%rbp), %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm4
	vmovdqa	%xmm14, -320(%rbp)
	vpmovzxbd	%xmm4, %xmm4
	vpmulld	.LC18(%rip), %xmm9, %xmm14
	vpaddd	-288(%rbp), %xmm5, %xmm5
	vpaddd	-272(%rbp), %xmm3, %xmm3
	vpmovzxbd	%xmm1, %xmm9
	vpaddd	-320(%rbp), %xmm5, %xmm5
	vpsrldq	$12, %xmm1, %xmm1
	vpaddd	%xmm9, %xmm0, %xmm0
	vmovdqa	-176(%rbp), %xmm7
	vpmulld	.LC20(%rip), %xmm9, %xmm9
	vpmovzxbd	%xmm1, %xmm1
	vpaddd	%xmm6, %xmm3, %xmm3
	vmovdqa	-192(%rbp), %xmm6
	vpaddd	%xmm1, %xmm5, %xmm5
	vpaddd	%xmm4, %xmm3, %xmm3
	vpmulld	.LC22(%rip), %xmm4, %xmm4
	vpmulld	.LC23(%rip), %xmm1, %xmm1
	vpaddd	%xmm2, %xmm3, %xmm3
	vpaddd	%xmm5, %xmm0, %xmm0
	vpmulld	.LC21(%rip), %xmm2, %xmm2
	vpaddd	%xmm3, %xmm0, %xmm0
	vpaddd	-208(%rbp), %xmm11, %xmm5
	vpaddd	%xmm15, %xmm10, %xmm3
	vpaddd	-240(%rbp), %xmm5, %xmm5
	vpaddd	%xmm12, %xmm3, %xmm3
	vpaddd	%xmm13, %xmm3, %xmm3
	vpaddd	%xmm14, %xmm5, %xmm5
	vpaddd	%xmm2, %xmm5, %xmm5
	vpaddd	%xmm4, %xmm3, %xmm3
	vpaddd	%xmm5, %xmm3, %xmm3
	vpaddd	%xmm7, %xmm6, %xmm5
	vpaddd	-224(%rbp), %xmm5, %xmm5
	vpaddd	%xmm8, %xmm5, %xmm5
	vpaddd	%xmm9, %xmm5, %xmm5
	vpaddd	%xmm1, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm3, %xmm3
	vpmulld	.LC1(%rip), %xmm6, %xmm5
	vpmulld	.LC0(%rip), %xmm7, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm6
	vpmulld	.LC4(%rip), %xmm10, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm5
	vpmulld	.LC17(%rip), %xmm8, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm6
	vpmulld	.LC22(%rip), %xmm4, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm6
	vmovdqa	-240(%rbp), %xmm5
	vpmulld	.LC7(%rip), %xmm5, %xmm7
	vmovdqa	-224(%rbp), %xmm5
	vpmulld	.LC6(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	.LC19(%rip), %xmm13, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm7
	vpmulld	.LC16(%rip), %xmm12, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	.LC21(%rip), %xmm2, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm5
	vpmulld	.LC2(%rip), %xmm11, %xmm7
	vpaddd	%xmm5, %xmm6, %xmm6
	vmovdqa	-208(%rbp), %xmm5
	vpmulld	.LC3(%rip), %xmm5, %xmm5
	vpaddd	%xmm7, %xmm5, %xmm7
	vpmulld	.LC5(%rip), %xmm15, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	.LC18(%rip), %xmm14, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm7
	vpmulld	.LC23(%rip), %xmm1, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	.LC20(%rip), %xmm9, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm5
	vmovdqa	-240(%rbp), %xmm6
	vpmulld	.LC14(%rip), %xmm6, %xmm6
	vmovdqa	-224(%rbp), %xmm7
	vpmulld	.LC10(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm7
	vpmulld	.LC25(%rip), %xmm13, %xmm6
	vpmulld	.LC26(%rip), %xmm2, %xmm2
	vpmulld	.LC31(%rip), %xmm4, %xmm4
	vpaddd	%xmm6, %xmm7, %xmm6
	vpmulld	.LC27(%rip), %xmm12, %xmm7
	vpmulld	.LC30(%rip), %xmm1, %xmm1
	vpmulld	.LC29(%rip), %xmm9, %xmm9
	vpaddd	%xmm7, %xmm6, %xmm7
	vmovdqa	-192(%rbp), %xmm6
	vpmulld	.LC9(%rip), %xmm6, %xmm6
	vpaddd	%xmm2, %xmm7, %xmm2
	vmovdqa	-176(%rbp), %xmm7
	vpmulld	.LC8(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vpmulld	.LC11(%rip), %xmm10, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vpmulld	.LC28(%rip), %xmm8, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vmovdqa	-208(%rbp), %xmm7
	vpaddd	%xmm4, %xmm6, %xmm4
	vpmulld	.LC12(%rip), %xmm11, %xmm6
	vpaddd	%xmm4, %xmm2, %xmm2
	vpmulld	.LC13(%rip), %xmm7, %xmm4
	vpaddd	%xmm6, %xmm4, %xmm4
	vpmulld	.LC15(%rip), %xmm15, %xmm6
	vpaddd	%xmm6, %xmm4, %xmm4
	vpmulld	.LC24(%rip), %xmm14, %xmm6
	vpaddd	%xmm6, %xmm4, %xmm4
	vpaddd	%xmm1, %xmm4, %xmm1
	vpaddd	%xmm9, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm1
	vpunpckhqdq	%xmm0, %xmm0, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vpshufd	$177, %xmm0, %xmm2
	vpaddd	%xmm0, %xmm2, %xmm0
	vpmovzxdq	%xmm0, %xmm2
	vpunpckhqdq	%xmm3, %xmm3, %xmm0
	vpaddd	%xmm0, %xmm3, %xmm3
	vmovq	%xmm2, -112(%rbp)
	vpshufd	$177, %xmm3, %xmm0
	vpaddd	%xmm3, %xmm0, %xmm0
	vpmovzxdq	%xmm0, %xmm2
	vpunpckhqdq	%xmm5, %xmm5, %xmm0
	vpaddd	%xmm0, %xmm5, %xmm5
	vmovq	%xmm2, -104(%rbp)
	vpshufd	$177, %xmm5, %xmm0
	vpaddd	%xmm5, %xmm0, %xmm0
	vpmovzxdq	%xmm0, %xmm2
	vpunpckhqdq	%xmm1, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vmovq	%xmm2, -96(%rbp)
	vpshufd	$177, %xmm1, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpmovzxdq	%xmm0, %xmm2
	vmovq	%xmm2, -88(%rbp)
	vmovdqa	-112(%rbp), %ymm0
	vpxor	(%r9), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L388
	movl	%edi, %eax
	addq	-368(%rbp), %rax
	vmovdqa	-400(%rbp), %ymm2
	movq	-424(%rbp), %rbx
	movq	%rax, %rdx
	salq	$6, %rdx
	vmovdqa	%ymm2, 24576(%rdx,%rbx)
	movq	%rdx, %rax
	leaq	24608+cell.5(%rip), %rdx
	vmovdqa	%ymm2, (%rdx,%rax)
	vmovdqa	(%rcx), %xmm0
	vmovdqa	16(%rcx), %xmm3
	vpmovzxbd	%xmm0, %xmm2
	vpsrldq	$4, %xmm0, %xmm11
	vpmovzxbd	%xmm3, %xmm9
	vpmulld	.LC0(%rip), %xmm2, %xmm10
	vpsrldq	$8, %xmm0, %xmm4
	vpsrldq	$12, %xmm0, %xmm0
	vpmovzxbd	%xmm11, %xmm11
	vpmovzxbd	%xmm0, %xmm5
	vpmovzxbd	%xmm4, %xmm4
	vpaddd	%xmm11, %xmm2, %xmm2
	vpmulld	.LC2(%rip), %xmm4, %xmm8
	vpsrldq	$4, %xmm3, %xmm6
	vpsrldq	$8, %xmm3, %xmm7
	vpaddd	%xmm5, %xmm4, %xmm4
	vpmulld	.LC1(%rip), %xmm11, %xmm0
	vpsrldq	$12, %xmm3, %xmm3
	vpmovzxbd	%xmm7, %xmm7
	vpmovzxbd	%xmm6, %xmm6
	vpmulld	.LC3(%rip), %xmm5, %xmm1
	vpmovzxbd	%xmm3, %xmm3
	vpaddd	%xmm7, %xmm4, %xmm4
	vpaddd	%xmm1, %xmm8, %xmm5
	vpmulld	.LC6(%rip), %xmm7, %xmm7
	vpaddd	%xmm3, %xmm2, %xmm2
	vpaddd	%xmm9, %xmm4, %xmm4
	vpmulld	.LC4(%rip), %xmm9, %xmm9
	vpmulld	.LC7(%rip), %xmm3, %xmm3
	vpmulld	.LC0(%rip), %xmm10, %xmm11
	vpaddd	%xmm6, %xmm2, %xmm2
	vpmulld	.LC5(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm5
	vpaddd	%xmm4, %xmm2, %xmm2
	vpaddd	%xmm0, %xmm10, %xmm4
	vpmulld	.LC2(%rip), %xmm8, %xmm12
	vpmulld	.LC8(%rip), %xmm10, %xmm10
	vpaddd	%xmm9, %xmm4, %xmm4
	vpaddd	%xmm3, %xmm5, %xmm5
	vpmulld	.LC12(%rip), %xmm8, %xmm8
	vpaddd	%xmm7, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm5, %xmm5
	vpmulld	.LC1(%rip), %xmm0, %xmm4
	vpaddd	%xmm11, %xmm4, %xmm4
	vpmulld	.LC6(%rip), %xmm7, %xmm11
	vpmulld	.LC9(%rip), %xmm0, %xmm0
	vpaddd	%xmm11, %xmm4, %xmm4
	vpaddd	%xmm10, %xmm0, %xmm0
	vpmulld	.LC4(%rip), %xmm9, %xmm11
	vpmulld	.LC10(%rip), %xmm7, %xmm7
	vpaddd	%xmm11, %xmm4, %xmm4
	vpmulld	.LC3(%rip), %xmm1, %xmm11
	vpmulld	.LC13(%rip), %xmm1, %xmm1
	vpaddd	%xmm8, %xmm1, %xmm1
	vpaddd	%xmm12, %xmm11, %xmm11
	vpmulld	.LC7(%rip), %xmm3, %xmm12
	vpmulld	.LC14(%rip), %xmm3, %xmm3
	vpaddd	%xmm7, %xmm0, %xmm0
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmulld	.LC11(%rip), %xmm9, %xmm9
	vpaddd	%xmm12, %xmm11, %xmm11
	vpaddd	%xmm9, %xmm0, %xmm0
	vpmulld	.LC5(%rip), %xmm6, %xmm12
	vpmulld	.LC15(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm1, %xmm1
	vpaddd	%xmm12, %xmm11, %xmm11
	vpaddd	%xmm1, %xmm0, %xmm0
	vpunpckhqdq	%xmm2, %xmm2, %xmm1
	vpaddd	%xmm11, %xmm4, %xmm4
	vpaddd	%xmm1, %xmm2, %xmm2
	vpshufd	$177, %xmm2, %xmm1
	vpaddd	%xmm2, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm5, %xmm5, %xmm1
	vpaddd	%xmm1, %xmm5, %xmm5
	vmovq	%xmm2, 24576(%rcx)
	vpshufd	$177, %xmm5, %xmm1
	vpaddd	%xmm5, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm4, %xmm4, %xmm1
	vpaddd	%xmm1, %xmm4, %xmm4
	vmovq	%xmm2, 24584(%rcx)
	vmovdqa	48(%rcx), %xmm3
	vpshufd	$177, %xmm4, %xmm1
	vpaddd	%xmm4, %xmm1, %xmm1
	vpsrldq	$4, %xmm3, %xmm6
	vpmovzxbd	%xmm3, %xmm10
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpmovzxbd	%xmm6, %xmm6
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovq	%xmm2, 24592(%rcx)
	vpsrldq	$8, %xmm3, %xmm7
	vpshufd	$177, %xmm0, %xmm1
	vpsrldq	$12, %xmm3, %xmm3
	vpmovzxbd	%xmm7, %xmm7
	vpaddd	%xmm0, %xmm1, %xmm0
	vpmovzxbd	%xmm3, %xmm3
	vpmovzxdq	%xmm0, %xmm2
	vmovdqa	32(%rcx), %xmm0
	vmovq	%xmm2, 24600(%rcx)
	vpsrldq	$4, %xmm0, %xmm11
	vpsrldq	$8, %xmm0, %xmm4
	vpmovzxbd	%xmm0, %xmm2
	vpmulld	.LC0(%rip), %xmm2, %xmm9
	vpsrldq	$12, %xmm0, %xmm0
	vpmovzxbd	%xmm11, %xmm11
	vpmovzxbd	%xmm4, %xmm4
	vpmulld	.LC2(%rip), %xmm4, %xmm8
	vpmovzxbd	%xmm0, %xmm5
	vpaddd	%xmm11, %xmm2, %xmm2
	vpmulld	.LC1(%rip), %xmm11, %xmm0
	vpmulld	.LC3(%rip), %xmm5, %xmm1
	vpaddd	%xmm5, %xmm4, %xmm4
	vpaddd	%xmm3, %xmm2, %xmm2
	vpmulld	.LC7(%rip), %xmm3, %xmm3
	vpmulld	.LC0(%rip), %xmm9, %xmm11
	vpaddd	%xmm7, %xmm4, %xmm4
	vpaddd	%xmm6, %xmm2, %xmm2
	vpmulld	.LC5(%rip), %xmm6, %xmm6
	vpmulld	.LC6(%rip), %xmm7, %xmm7
	vpaddd	%xmm10, %xmm4, %xmm4
	vpaddd	%xmm1, %xmm8, %xmm5
	vpmulld	.LC4(%rip), %xmm10, %xmm10
	vpmulld	.LC2(%rip), %xmm8, %xmm12
	vpaddd	%xmm4, %xmm2, %xmm2
	vpaddd	%xmm0, %xmm9, %xmm4
	vpmulld	.LC12(%rip), %xmm8, %xmm8
	vpmulld	.LC8(%rip), %xmm9, %xmm9
	vpaddd	%xmm6, %xmm5, %xmm5
	vpaddd	%xmm10, %xmm4, %xmm4
	vpaddd	%xmm7, %xmm4, %xmm4
	vpaddd	%xmm3, %xmm5, %xmm5
	vpaddd	%xmm4, %xmm5, %xmm5
	vpmulld	.LC1(%rip), %xmm0, %xmm4
	vpaddd	%xmm11, %xmm4, %xmm4
	vpmulld	.LC6(%rip), %xmm7, %xmm11
	vpmulld	.LC9(%rip), %xmm0, %xmm0
	vpaddd	%xmm11, %xmm4, %xmm4
	vpaddd	%xmm9, %xmm0, %xmm0
	vpmulld	.LC4(%rip), %xmm10, %xmm11
	vpmulld	.LC10(%rip), %xmm7, %xmm7
	vpaddd	%xmm11, %xmm4, %xmm4
	vpmulld	.LC3(%rip), %xmm1, %xmm11
	vpmulld	.LC13(%rip), %xmm1, %xmm1
	vpaddd	%xmm8, %xmm1, %xmm1
	vpaddd	%xmm12, %xmm11, %xmm11
	vpmulld	.LC7(%rip), %xmm3, %xmm12
	vpmulld	.LC14(%rip), %xmm3, %xmm3
	vpaddd	%xmm7, %xmm0, %xmm0
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmulld	.LC11(%rip), %xmm10, %xmm10
	vpaddd	%xmm12, %xmm11, %xmm11
	vpaddd	%xmm10, %xmm0, %xmm0
	vpmulld	.LC5(%rip), %xmm6, %xmm12
	vpmulld	.LC15(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm1, %xmm1
	vpaddd	%xmm12, %xmm11, %xmm11
	vpaddd	%xmm1, %xmm0, %xmm0
	vpunpckhqdq	%xmm2, %xmm2, %xmm1
	vpaddd	%xmm11, %xmm4, %xmm4
	vpaddd	%xmm1, %xmm2, %xmm2
	vpshufd	$177, %xmm2, %xmm1
	vpaddd	%xmm2, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm5, %xmm5, %xmm1
	vpaddd	%xmm1, %xmm5, %xmm5
	vmovq	%xmm2, 24608(%rcx)
	vpshufd	$177, %xmm5, %xmm1
	vpaddd	%xmm5, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm4, %xmm4, %xmm1
	vpaddd	%xmm1, %xmm4, %xmm4
	vmovq	%xmm2, 24616(%rcx)
	vpshufd	$177, %xmm4, %xmm1
	vpaddd	%xmm4, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovq	%xmm2, 24624(%rcx)
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	vpmovzxdq	%xmm0, %xmm2
	vmovq	%xmm2, 24632(%rcx)
	jmp	.L395
.L391:
	movq	-176(%rbp), %rbx
	leaq	(%rbx,%rax), %rdx
	testb	$1, %dl
	jne	.L388
	subq	%rax, %rbx
	leaq	-2(%rbx), %rax
	cmpq	$127, %rax
	ja	.L388
	leaq	-2(%rdx), %rax
	cmpq	$127, %rax
	ja	.L388
	movq	%rdx, %rax
	sarq	%rbx
	sarq	%rax
	movq	%rax, -176(%rbp)
	cmpq	%rbx, %rax
	je	.L388
	movq	%rsi, %rdx
	movq	%r8, %rax
	movq	-176(%rbp), %r8
	imulq	%rbx, %rdx
	subq	%rbx, %r8
	subq	%rdx, %rax
	cqto
	idivq	%r8
	movq	%rax, %r8
	testq	%rdx, %rdx
	jne	.L388
	leaq	255(%rax), %rax
	cmpq	$510, %rax
	ja	.L388
	subq	%r8, %rsi
	leaq	255(%rsi), %rax
	movq	%rsi, -192(%rbp)
	cmpq	$510, %rax
	ja	.L388
	testq	%r8, %r8
	je	.L388
	testq	%rsi, %rsi
	je	.L388
	movq	-176(%rbp), %rdx
	movq	%rdx, %rax
	imulq	%rdx, %rax
	movq	%rbx, %rdx
	imulq	%rbx, %rdx
	imulq	%r8, %rax
	imulq	%rsi, %rdx
	leaq	(%rax,%rdx), %rsi
	cmpq	%rsi, %r10
	jne	.L388
	movq	-176(%rbp), %rsi
	imulq	%rbx, %rdx
	imulq	%rsi, %rax
	addq	%rdx, %rax
	cmpq	%rax, %r11
	jne	.L388
	leal	-1(%rsi), %eax
	movzbl	-192(%rbp), %edx
	subb	%r8b, (%rcx,%rax)
	leal	-1(%rbx), %eax
	subb	%dl, (%rcx,%rax)
	jmp	.L390
.L398:
	movl	$1, %eax
	jmp	.L399
.L516:
	movq	-624(%rbp), %rbx
	vzeroupper
.L438:
	movq	-488(%rbp), %rsi
	xorl	%r13d, %r13d
	xorl	%r15d, %r15d
	xorl	%r14d, %r14d
	movq	-424(%rbp), %rdi
	movl	$41312, %edx
	call	memcpy@PLT
	movq	-608(%rbp), %rsi
	movl	$16384, %edx
	leaq	contents.4(%rip), %rdi
	call	memcpy@PLT
	movq	%rbx, %rsi
	movl	$4096, %edx
	xorl	%ebx, %ebx
	leaq	sqm_slot_of(%rip), %rdi
	call	memcpy@PLT
	leaq	60+cell.5(%rip), %rsi
	xorl	%edi, %edi
.L401:
	movq	%r12, -600(%rbp)
	leaq	2048(%rsi), %rdx
	movq	%rdi, -608(%rbp)
	.p2align 4
	.p2align 3
.L422:
	leaq	-60(%rsi), %rax
	jmp	.L421
	.p2align 4,,10
	.p2align 3
.L402:
	leaq	1(%rax), %r11
	cmpq	$1999, %r13
	jle	.L411
.L403:
	movq	%r11, %rax
	cmpq	%r11, %rsi
	je	.L409
.L421:
	cmpq	$1999, %rbx
	jg	.L402
.L410:
	movzbl	(%rax), %edi
	movq	%rax, %rcx
	leaq	1(%rax), %r11
	cmpb	$-1, %dil
	je	.L403
	movzbl	1(%rax), %r9d
	movq	%r11, %r8
	cmpb	$2, %r9b
	jbe	.L404
	movq	%r11, %r10
.L437:
	movzbl	2(%rcx), %r12d
	leal	3(%r12), %r11d
	cmpl	$255, %r11d
	jg	.L405
	movzbl	3(%rcx), %r11d
	testb	%r11b, %r11b
	jne	.L517
.L405:
	leaq	1(%rax), %r11
	cmpq	$1999, %r13
	jle	.L435
.L436:
	cmpq	%rsi, %r8
	je	.L409
	movzbl	(%r8), %edi
	movq	%r8, %rcx
	cmpb	$-1, %dil
	je	.L449
	movzbl	1(%r8), %r9d
	cmpb	$2, %r9b
	jbe	.L450
	leaq	1(%r8), %r10
	movq	%r8, %rax
	movq	%r10, %r8
	jmp	.L437
	.p2align 4,,10
	.p2align 3
.L506:
	movq	%r11, %rax
	cmpq	%rsi, %r11
	je	.L409
.L503:
	cmpq	$1999, %rbx
	jle	.L410
.L411:
	movzbl	(%rax), %edi
	movq	%rax, %rcx
	cmpb	$-1, %dil
	je	.L518
	leaq	1(%rax), %r11
	movzbl	1(%rax), %r9d
	movq	%r11, %r10
.L435:
	cmpb	$3, %r9b
	jbe	.L508
	movzbl	2(%rcx), %eax
	addl	$6, %eax
	cmpl	$255, %eax
	jg	.L506
	cmpb	$3, 3(%rcx)
	jbe	.L506
	cmpb	$-1, 4(%rcx)
	je	.L508
	vmovdqa	-60(%rsi), %xmm7
	vmovdqa	-44(%rsi), %xmm8
	addl	$1, %edi
	vpsrldq	$4, %xmm7, %xmm11
	vpmovzxbd	%xmm7, %xmm5
	vpmovzxbd	%xmm8, %xmm14
	vpmulld	.LC0(%rip), %xmm5, %xmm3
	vpsrldq	$8, %xmm7, %xmm2
	vpmovzxbd	%xmm11, %xmm1
	vpmulld	.LC4(%rip), %xmm14, %xmm0
	vmovdqa	%xmm0, -240(%rbp)
	vpsrldq	$12, %xmm7, %xmm7
	vpsrldq	$4, %xmm8, %xmm10
	vmovdqa	-12(%rsi), %xmm0
	vmovdqa	%xmm1, -304(%rbp)
	vpmovzxbd	%xmm7, %xmm7
	vpmovzxbd	%xmm10, %xmm4
	vpmulld	.LC3(%rip), %xmm7, %xmm6
	vpmulld	.LC1(%rip), %xmm1, %xmm1
	vmovdqa	%xmm6, -224(%rbp)
	vmovdqa	-28(%rsi), %xmm6
	vpmulld	.LC5(%rip), %xmm4, %xmm10
	vpaddd	-304(%rbp), %xmm5, %xmm5
	vmovdqa	%xmm1, -176(%rbp)
	vpsrldq	$8, %xmm8, %xmm1
	vpsrldq	$12, %xmm8, %xmm8
	vpmovzxbd	%xmm2, %xmm2
	vpmovzxbd	%xmm8, %xmm15
	vpsrldq	$4, %xmm6, %xmm12
	vpmulld	.LC7(%rip), %xmm15, %xmm13
	vmovdqa	%xmm4, -320(%rbp)
	vmovdqa	%xmm15, -336(%rbp)
	vpaddd	-320(%rbp), %xmm5, %xmm5
	vpmovzxbd	%xmm1, %xmm1
	vpmulld	.LC6(%rip), %xmm1, %xmm4
	vmovdqa	%xmm13, -256(%rbp)
	vpsrldq	$8, %xmm6, %xmm13
	vpmovzxbd	%xmm6, %xmm15
	vpaddd	-336(%rbp), %xmm1, %xmm1
	vpmovzxbd	%xmm12, %xmm8
	vpmovzxbd	%xmm13, %xmm13
	vpmulld	.LC2(%rip), %xmm2, %xmm11
	vpaddd	%xmm7, %xmm2, %xmm2
	vpsrldq	$12, %xmm6, %xmm6
	vpaddd	%xmm13, %xmm1, %xmm1
	vpaddd	%xmm15, %xmm5, %xmm5
	vpmulld	.LC16(%rip), %xmm15, %xmm12
	vpmovzxbd	%xmm6, %xmm6
	vmovdqa	%xmm8, -352(%rbp)
	vpmulld	.LC19(%rip), %xmm6, %xmm9
	vpaddd	-352(%rbp), %xmm1, %xmm1
	vmovdqa	%xmm3, -208(%rbp)
	vpaddd	%xmm14, %xmm2, %xmm2
	vpsrldq	$4, %xmm0, %xmm3
	vmovdqa	%xmm4, -192(%rbp)
	vpsrldq	$8, %xmm0, %xmm4
	vpaddd	%xmm6, %xmm2, %xmm2
	vpmovzxbd	%xmm3, %xmm3
	vmovdqa	%xmm12, -272(%rbp)
	vpmovzxbd	%xmm4, %xmm4
	vpmulld	.LC17(%rip), %xmm8, %xmm12
	vpmulld	.LC18(%rip), %xmm13, %xmm8
	vmovdqa	%xmm9, -288(%rbp)
	vmovdqa	.LC20(%rip), %xmm13
	vpaddd	%xmm4, %xmm2, %xmm2
	vmovdqa	.LC22(%rip), %xmm15
	vpmovzxbd	%xmm0, %xmm9
	vpsrldq	$12, %xmm0, %xmm0
	vpaddd	%xmm3, %xmm2, %xmm2
	vmovdqa	.LC23(%rip), %xmm14
	vpmulld	%xmm15, %xmm4, %xmm4
	vpmovzxbd	%xmm0, %xmm0
	vpaddd	%xmm9, %xmm1, %xmm1
	vpmulld	.LC21(%rip), %xmm3, %xmm3
	vpaddd	%xmm0, %xmm5, %xmm5
	vpmulld	%xmm13, %xmm9, %xmm9
	vmovdqa	-176(%rbp), %xmm7
	vmovdqa	-192(%rbp), %xmm6
	vpaddd	%xmm5, %xmm1, %xmm1
	vpaddd	-224(%rbp), %xmm11, %xmm5
	vpmulld	%xmm14, %xmm0, %xmm0
	vpaddd	-256(%rbp), %xmm5, %xmm5
	vpaddd	%xmm2, %xmm1, %xmm1
	vpaddd	-240(%rbp), %xmm10, %xmm2
	vpaddd	-272(%rbp), %xmm2, %xmm2
	vpaddd	-288(%rbp), %xmm2, %xmm2
	vpaddd	%xmm8, %xmm5, %xmm5
	vpaddd	%xmm3, %xmm5, %xmm5
	vpaddd	%xmm4, %xmm2, %xmm2
	vpaddd	%xmm5, %xmm2, %xmm2
	vpaddd	-208(%rbp), %xmm7, %xmm5
	vpmulld	.LC1(%rip), %xmm7, %xmm7
	vpaddd	%xmm6, %xmm5, %xmm5
	vpmulld	.LC6(%rip), %xmm6, %xmm6
	vpaddd	%xmm12, %xmm5, %xmm5
	vpaddd	%xmm9, %xmm5, %xmm5
	vpaddd	%xmm0, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm2, %xmm2
	vmovdqa	-256(%rbp), %xmm5
	vpmulld	.LC7(%rip), %xmm5, %xmm5
	vpaddd	%xmm6, %xmm5, %xmm6
	vmovdqa	-288(%rbp), %xmm5
	vpmulld	.LC19(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm5
	vmovdqa	-272(%rbp), %xmm6
	vpmulld	.LC16(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm6
	vpmulld	.LC21(%rip), %xmm3, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm6
	vmovdqa	-208(%rbp), %xmm5
	vpmulld	.LC0(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vmovdqa	-240(%rbp), %xmm7
	vpmulld	.LC4(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm7
	vpmulld	.LC17(%rip), %xmm12, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	%xmm15, %xmm4, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm5
	vpmulld	.LC2(%rip), %xmm11, %xmm7
	vpaddd	%xmm5, %xmm6, %xmm6
	vmovdqa	-224(%rbp), %xmm5
	vpmulld	.LC3(%rip), %xmm5, %xmm5
	vpaddd	%xmm7, %xmm5, %xmm7
	vpmulld	.LC5(%rip), %xmm10, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	.LC18(%rip), %xmm8, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm7
	vpmulld	%xmm14, %xmm0, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm5
	vpmulld	%xmm13, %xmm9, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm5
	vmovdqa	-256(%rbp), %xmm7
	vpaddd	%xmm5, %xmm6, %xmm5
	vpmulld	.LC14(%rip), %xmm7, %xmm6
	vmovdqa	-192(%rbp), %xmm7
	movb	%dil, (%rcx)
	vpmulld	.LC10(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm7
	vmovdqa	-288(%rbp), %xmm6
	vpmulld	.LC25(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm7, %xmm6
	subb	$4, (%r10)
	vmovdqa	-272(%rbp), %xmm7
	vpmulld	.LC27(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm7
	movzbl	2(%rcx), %eax
	movb	3(%rcx), %ah
	vpmulld	.LC26(%rip), %xmm3, %xmm3
	vmovdqa	-176(%rbp), %xmm6
	vpaddd	%xmm3, %xmm7, %xmm3
	vpmulld	.LC9(%rip), %xmm6, %xmm6
	vmovdqa	-208(%rbp), %xmm7
	vpmulld	.LC8(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm7
	vmovdqa	-240(%rbp), %xmm6
	vpmulld	.LC11(%rip), %xmm6, %xmm6
	vpmulld	.LC31(%rip), %xmm4, %xmm4
	vpaddd	%xmm6, %xmm7, %xmm6
	vpmulld	.LC28(%rip), %xmm12, %xmm7
	vpmulld	.LC30(%rip), %xmm0, %xmm0
	vpmulld	.LC29(%rip), %xmm9, %xmm9
	vpaddd	%xmm7, %xmm6, %xmm7
	vmovdqa	-224(%rbp), %xmm6
	vpaddd	%xmm4, %xmm7, %xmm7
	vpmulld	.LC12(%rip), %xmm11, %xmm4
	vpaddd	%xmm7, %xmm3, %xmm7
	vpmulld	.LC13(%rip), %xmm6, %xmm3
	vpaddd	%xmm4, %xmm3, %xmm4
	vpmulld	.LC15(%rip), %xmm10, %xmm3
	vpaddd	%xmm3, %xmm4, %xmm3
	vpmulld	.LC24(%rip), %xmm8, %xmm4
	vpaddd	%xmm4, %xmm3, %xmm4
	vpunpckhqdq	%xmm1, %xmm1, %xmm3
	vpaddd	%xmm3, %xmm1, %xmm3
	vpaddd	%xmm0, %xmm4, %xmm0
	vpshufd	$177, %xmm3, %xmm1
	vpaddd	%xmm9, %xmm0, %xmm0
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm7, %xmm0
	vpmovzxdq	%xmm1, %xmm3
	vpunpckhqdq	%xmm2, %xmm2, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm2
	vmovq	%xmm3, -144(%rbp)
	vpshufd	$177, %xmm2, %xmm1
	vpaddd	%xmm2, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vmovq	%xmm2, -136(%rbp)
	vpunpckhqdq	%xmm5, %xmm5, %xmm2
	vpaddd	%xmm2, %xmm5, %xmm2
	vpshufd	$177, %xmm2, %xmm1
	vpaddd	%xmm2, %xmm1, %xmm1
	vpmovzxdq	%xmm1, %xmm2
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vmovq	%xmm2, -128(%rbp)
	vpshufd	$177, %xmm1, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpmovzxdq	%xmm0, %xmm2
	vmovq	%xmm2, -120(%rbp)
	vmovd	%eax, %xmm2
	xorl	%eax, %eax
	vpinsrw	$0, .LC78(%rip), %xmm0, %xmm0
	vpaddb	%xmm0, %xmm2, %xmm0
	addb	$1, 4(%rcx)
	vpextrw	$0, %xmm0, 2(%rcx)
	vmovdqa	-60(%rsi), %xmm7
	vmovdqa	-44(%rsi), %xmm8
	vpmovzxbd	%xmm7, %xmm2
	vpsrldq	$4, %xmm7, %xmm3
	vpmovzxbd	%xmm8, %xmm4
	vpsrldq	$8, %xmm7, %xmm0
	vpsrldq	$12, %xmm7, %xmm7
	vmovdqa	%xmm2, -304(%rbp)
	vpmulld	.LC0(%rip), %xmm2, %xmm2
	vpmovzxbd	%xmm7, %xmm7
	vpsrldq	$4, %xmm8, %xmm10
	vpmulld	.LC3(%rip), %xmm7, %xmm6
	vmovdqa	%xmm6, -192(%rbp)
	vmovdqa	-28(%rsi), %xmm6
	vpmovzxbd	%xmm10, %xmm11
	vmovdqa	%xmm2, -176(%rbp)
	vpsrldq	$8, %xmm8, %xmm2
	vpsrldq	$12, %xmm8, %xmm8
	vpmovzxbd	%xmm2, %xmm2
	vpmulld	.LC4(%rip), %xmm4, %xmm10
	vpmulld	.LC6(%rip), %xmm2, %xmm12
	vpmovzxbd	%xmm8, %xmm8
	vmovdqa	%xmm4, -320(%rbp)
	vpmulld	.LC5(%rip), %xmm11, %xmm4
	vpmovzxbd	%xmm6, %xmm9
	vmovdqa	%xmm11, -336(%rbp)
	vpmovzxbd	%xmm3, %xmm3
	vpmovzxbd	%xmm0, %xmm0
	vpmulld	.LC7(%rip), %xmm8, %xmm11
	vmovdqa	%xmm12, -240(%rbp)
	vpsrldq	$8, %xmm6, %xmm12
	vpmulld	.LC1(%rip), %xmm3, %xmm1
	vpmulld	.LC2(%rip), %xmm0, %xmm5
	vmovdqa	%xmm11, -256(%rbp)
	vpsrldq	$4, %xmm6, %xmm11
	vpaddd	%xmm7, %xmm0, %xmm0
	vmovdqa	%xmm1, -208(%rbp)
	vpmovzxbd	%xmm11, %xmm1
	vpmulld	.LC16(%rip), %xmm9, %xmm11
	vpsrldq	$12, %xmm6, %xmm6
	vmovdqa	%xmm5, -288(%rbp)
	vpmovzxbd	%xmm12, %xmm5
	vpmovzxbd	%xmm6, %xmm6
	vmovdqa	%xmm4, -224(%rbp)
	vmovdqa	%xmm8, -352(%rbp)
	vpmulld	.LC17(%rip), %xmm1, %xmm8
	vmovdqa	%xmm9, -368(%rbp)
	vpmulld	.LC18(%rip), %xmm5, %xmm9
	vmovdqa	%xmm1, -400(%rbp)
	vmovdqa	%xmm5, -416(%rbp)
	vmovdqa	%xmm9, -272(%rbp)
	vmovdqa	-12(%rsi), %xmm1
	vpaddd	-320(%rbp), %xmm0, %xmm0
	vpmulld	.LC19(%rip), %xmm6, %xmm12
	vpaddd	-352(%rbp), %xmm2, %xmm2
	vpaddd	-304(%rbp), %xmm3, %xmm3
	vpmovzxbd	%xmm1, %xmm9
	vpsrldq	$4, %xmm1, %xmm5
	vpaddd	%xmm6, %xmm0, %xmm0
	vmovdqa	-176(%rbp), %xmm7
	vpaddd	-416(%rbp), %xmm2, %xmm2
	vpsrldq	$8, %xmm1, %xmm4
	vpmovzxbd	%xmm5, %xmm5
	vpaddd	-400(%rbp), %xmm2, %xmm2
	vpsrldq	$12, %xmm1, %xmm1
	vpmovzxbd	%xmm4, %xmm4
	vpaddd	-336(%rbp), %xmm3, %xmm3
	vpmovzxbd	%xmm1, %xmm1
	vpaddd	-368(%rbp), %xmm3, %xmm3
	vpaddd	%xmm9, %xmm2, %xmm2
	vpaddd	%xmm4, %xmm0, %xmm0
	vpmulld	%xmm15, %xmm4, %xmm4
	vpaddd	%xmm1, %xmm3, %xmm3
	vpaddd	%xmm5, %xmm0, %xmm0
	vpmulld	%xmm13, %xmm9, %xmm9
	vpmulld	.LC21(%rip), %xmm5, %xmm5
	vpaddd	%xmm3, %xmm2, %xmm2
	vmovdqa	-192(%rbp), %xmm3
	vpmulld	%xmm14, %xmm1, %xmm1
	vpaddd	-288(%rbp), %xmm3, %xmm3
	vpaddd	%xmm0, %xmm2, %xmm0
	vpaddd	-224(%rbp), %xmm10, %xmm2
	vpaddd	-256(%rbp), %xmm3, %xmm3
	vpaddd	-272(%rbp), %xmm3, %xmm3
	vpaddd	%xmm11, %xmm2, %xmm2
	vpaddd	%xmm12, %xmm2, %xmm2
	vpaddd	%xmm5, %xmm3, %xmm3
	vpaddd	%xmm4, %xmm2, %xmm2
	vpaddd	%xmm3, %xmm2, %xmm2
	vmovdqa	-208(%rbp), %xmm3
	vpaddd	%xmm7, %xmm3, %xmm3
	vpaddd	-240(%rbp), %xmm3, %xmm3
	vpmulld	.LC0(%rip), %xmm7, %xmm7
	vpaddd	%xmm8, %xmm3, %xmm3
	vpaddd	%xmm9, %xmm3, %xmm3
	vpaddd	%xmm1, %xmm3, %xmm3
	vpaddd	%xmm3, %xmm2, %xmm2
	vmovdqa	-256(%rbp), %xmm3
	vpmulld	.LC7(%rip), %xmm3, %xmm6
	vmovdqa	-240(%rbp), %xmm3
	vpmulld	.LC6(%rip), %xmm3, %xmm3
	vpaddd	%xmm3, %xmm6, %xmm3
	vpmulld	.LC19(%rip), %xmm12, %xmm6
	vpaddd	%xmm6, %xmm3, %xmm3
	vpmulld	.LC16(%rip), %xmm11, %xmm6
	vpaddd	%xmm6, %xmm3, %xmm6
	vpmulld	.LC21(%rip), %xmm5, %xmm3
	vpaddd	%xmm3, %xmm6, %xmm6
	vmovdqa	-208(%rbp), %xmm3
	vpmulld	.LC1(%rip), %xmm3, %xmm3
	vpaddd	%xmm3, %xmm7, %xmm3
	vpmulld	.LC4(%rip), %xmm10, %xmm7
	vpaddd	%xmm7, %xmm3, %xmm7
	vpmulld	.LC17(%rip), %xmm8, %xmm3
	vpaddd	%xmm3, %xmm7, %xmm3
	vpmulld	%xmm15, %xmm4, %xmm7
	vmovdqa	-192(%rbp), %xmm15
	vpaddd	%xmm7, %xmm3, %xmm3
	vpmulld	.LC3(%rip), %xmm15, %xmm7
	vmovdqa	-288(%rbp), %xmm15
	vpmulld	.LC26(%rip), %xmm5, %xmm5
	vpmulld	.LC31(%rip), %xmm4, %xmm4
	vpaddd	%xmm3, %xmm6, %xmm6
	vpmulld	.LC2(%rip), %xmm15, %xmm3
	vpaddd	%xmm3, %xmm7, %xmm3
	vmovdqa	-224(%rbp), %xmm7
	vpmulld	.LC5(%rip), %xmm7, %xmm7
	vpaddd	%xmm7, %xmm3, %xmm7
	vmovdqa	-272(%rbp), %xmm3
	vpmulld	.LC18(%rip), %xmm3, %xmm3
	vpaddd	%xmm3, %xmm7, %xmm3
	vpmulld	%xmm14, %xmm1, %xmm7
	vmovdqa	-256(%rbp), %xmm14
	vpmulld	.LC30(%rip), %xmm1, %xmm1
	vpaddd	%xmm7, %xmm3, %xmm7
	vpmulld	%xmm13, %xmm9, %xmm3
	vmovdqa	-240(%rbp), %xmm13
	vpmulld	.LC29(%rip), %xmm9, %xmm9
	vpaddd	%xmm3, %xmm7, %xmm7
	vpmulld	.LC14(%rip), %xmm14, %xmm3
	vpaddd	%xmm7, %xmm6, %xmm7
	vpmulld	.LC10(%rip), %xmm13, %xmm6
	vpaddd	%xmm6, %xmm3, %xmm6
	vpmulld	.LC25(%rip), %xmm12, %xmm3
	vpaddd	%xmm3, %xmm6, %xmm3
	vpmulld	.LC27(%rip), %xmm11, %xmm6
	vpaddd	%xmm6, %xmm3, %xmm3
	vmovdqa	-176(%rbp), %xmm6
	vpmulld	.LC8(%rip), %xmm6, %xmm6
	vpaddd	%xmm5, %xmm3, %xmm3
	vmovdqa	-208(%rbp), %xmm5
	vpmulld	.LC9(%rip), %xmm5, %xmm5
	vpaddd	%xmm6, %xmm5, %xmm5
	vpmulld	.LC11(%rip), %xmm10, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm5
	vpmulld	.LC28(%rip), %xmm8, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm5
	vmovdqa	-224(%rbp), %xmm6
	vpaddd	%xmm4, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm3, %xmm5
	vpmulld	.LC12(%rip), %xmm15, %xmm3
	vmovdqa	-192(%rbp), %xmm15
	vpmulld	.LC13(%rip), %xmm15, %xmm4
	vpaddd	%xmm4, %xmm3, %xmm3
	vpmulld	.LC15(%rip), %xmm6, %xmm4
	vmovdqa	-272(%rbp), %xmm6
	vpaddd	%xmm4, %xmm3, %xmm3
	vpmulld	.LC24(%rip), %xmm6, %xmm4
	vpaddd	%xmm4, %xmm3, %xmm3
	vpaddd	%xmm1, %xmm3, %xmm1
	vpunpckhqdq	%xmm0, %xmm0, %xmm3
	vpaddd	%xmm3, %xmm0, %xmm0
	vpaddd	%xmm9, %xmm1, %xmm1
	vpshufd	$177, %xmm0, %xmm3
	vpaddd	%xmm1, %xmm5, %xmm1
	vpaddd	%xmm0, %xmm3, %xmm0
	vpmovzxdq	%xmm0, %xmm3
	vpunpckhqdq	%xmm2, %xmm2, %xmm0
	vpaddd	%xmm0, %xmm2, %xmm2
	vmovq	%xmm3, -112(%rbp)
	vpshufd	$177, %xmm2, %xmm0
	vpaddd	%xmm2, %xmm0, %xmm0
	vpmovzxdq	%xmm0, %xmm2
	vpunpckhqdq	%xmm7, %xmm7, %xmm0
	vpaddd	%xmm0, %xmm7, %xmm7
	vmovq	%xmm2, -104(%rbp)
	vpshufd	$177, %xmm7, %xmm0
	vpaddd	%xmm7, %xmm0, %xmm0
	vpmovzxdq	%xmm0, %xmm2
	vpunpckhqdq	%xmm1, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vmovq	%xmm2, -96(%rbp)
	vpshufd	$177, %xmm1, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpmovzxdq	%xmm0, %xmm2
	vmovq	%xmm2, -88(%rbp)
	vmovdqa	-144(%rbp), %ymm0
	vpxor	-112(%rbp), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	vpinsrw	$0, .LC79(%rip), %xmm0, %xmm0
	sete	%al
	subb	$1, (%rcx)
	addq	$1, %r13
	addb	$4, (%r10)
	addq	%rax, %r15
	movzbl	2(%rcx), %eax
	movb	3(%rcx), %ah
	subb	$1, 4(%rcx)
	vmovd	%eax, %xmm2
	movq	%r11, %rax
	vpaddb	%xmm0, %xmm2, %xmm0
	vpextrw	$0, %xmm0, 2(%rcx)
	cmpq	%r11, %rsi
	jne	.L421
	.p2align 4
	.p2align 3
.L409:
	addq	$64, %rsi
	cmpq	%rdx, %rsi
	jne	.L422
.L521:
	movq	-608(%rbp), %rdi
	movq	-600(%rbp), %r12
	addq	$32, %rdi
	cmpq	$256, %rdi
	jne	.L401
	movq	-424(%rbp), %rsi
	movq	-488(%rbp), %rdi
	movl	$41312, %edx
	vzeroupper
	call	memcpy@PLT
	movq	%r13, -224(%rbp)
	movq	-568(%rbp), %r13
	movq	%rbx, -240(%rbp)
	movq	-496(%rbp), %rbx
	movl	$200, -192(%rbp)
	movq	$0, -176(%rbp)
	movq	%r15, -208(%rbp)
	movq	%r14, -256(%rbp)
	jmp	.L426
.L520:
	vmovdqa	32(%r15), %ymm0
	vpxor	32(%r14), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L424
	xorl	%eax, %eax
.L425:
	andl	$1, %eax
	addq	%rax, -176(%rbp)
	subl	$1, -192(%rbp)
	je	.L519
	vzeroupper
.L426:
	movq	-424(%rbp), %r15
	movq	-488(%rbp), %rsi
	movl	$41312, %edx
	movq	%r15, %rdi
	call	memcpy@PLT
	movq	-432(%rbp), %rsi
	movq	%r12, %r11
	leaq	0(%r13,%rbx), %rdx
	xorq	%rbx, %r11
	movq	%r12, %rbx
	rorx	$47, %rdx, %rdx
	movzbl	%dl, %r9d
	xorq	%r13, %rsi
	movq	%r11, %rcx
	salq	$17, %rbx
	rorx	$19, %r11, %r11
	movq	%rsi, %rax
	xorq	%r13, %rcx
	xorq	%rsi, %rbx
	movzbl	%dl, %edx
	xorq	%r12, %rax
	xorq	%rcx, %rbx
	movq	%rax, %rdi
	movq	%rbx, %r10
	leaq	sqm_slot_of(%rip), %rax
	movq	%rdi, %r8
	movl	(%rax,%rdx,4), %r14d
	xorq	%rdi, %r10
	salq	$17, %rdi
	xorq	%r11, %r8
	xorq	%rbx, %rdi
	movq	%r10, %rbx
	salq	$6, %rdx
	movq	%r8, %rsi
	movl	%r14d, %eax
	rorx	$19, %r8, %r8
	xorq	%r8, %rbx
	xorq	%rcx, %rsi
	sarl	$8, %eax
	movq	%rbx, %r13
	addq	%r11, %rcx
	xorq	%rsi, %rdi
	cltq
	xorq	%rsi, %r13
	addq	%r8, %rsi
	movq	%rdi, %r12
	salq	$5, %rax
	rorx	$47, %rsi, %rsi
	rorx	$47, %rcx, %rcx
	xorq	%r10, %r12
	salq	$17, %r10
	andl	$63, %ecx
	rorx	$19, %rbx, %rbx
	xorq	%rdi, %r10
	movzbl	%r14b, %edi
	addq	%rdi, %rax
	movl	%esi, %edi
	movq	%r10, -432(%rbp)
	salq	$6, %rax
	addq	%rax, %r15
	movl	$2155905153, %eax
	imulq	%rax, %rdi
	leaq	contents.4(%rip), %rax
	leaq	(%rax,%rdx), %r14
	movq	%r14, %rdx
	shrq	$39, %rdi
	leal	1(%rsi,%rdi), %esi
	movl	%r9d, %edi
	xorb	%sil, (%r15,%rcx)
	movl	%r9d, %esi
	call	sqm_write.constprop.0.isra.0
	vmovdqa	(%r15), %ymm0
	vpxor	(%r14), %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	je	.L520
.L424:
	movl	$1, %eax
	jmp	.L425
	.p2align 4,,10
	.p2align 3
.L404:
	cmpq	$1999, %r13
	jle	.L403
	jmp	.L436
	.p2align 4,,10
	.p2align 3
.L508:
	movq	%r11, %rax
	cmpq	%r11, %rsi
	jne	.L503
	addq	$64, %rsi
	cmpq	%rdx, %rsi
	jne	.L422
	jmp	.L521
	.p2align 4,,10
	.p2align 3
.L518:
	addq	$1, %rax
	cmpq	%rsi, %rax
	jne	.L503
	addq	$64, %rsi
	cmpq	%rdx, %rsi
	jne	.L422
	jmp	.L521
	.p2align 4,,10
	.p2align 3
.L449:
	leaq	1(%r8), %r11
	jmp	.L403
	.p2align 4,,10
	.p2align 3
.L450:
	addq	$1, %r8
	jmp	.L436
	.p2align 4,,10
	.p2align 3
.L517:
	vmovdqa	-60(%rsi), %xmm0
	movzbl	%r11b, %r8d
	sall	$8, %r8d
	vpsrldq	$4, %xmm0, %xmm1
	vpmovzxbd	%xmm0, %xmm2
	orl	%r12d, %r8d
	vpmovzxbd	%xmm1, %xmm6
	vpsrldq	$8, %xmm0, %xmm1
	vmovdqa	%xmm2, -288(%rbp)
	sall	$8, %r8d
	vpsrldq	$12, %xmm0, %xmm0
	vpmovzxbd	%xmm1, %xmm3
	orl	%r9d, %r8d
	vpmulld	.LC1(%rip), %xmm6, %xmm13
	vpmovzxbd	%xmm0, %xmm1
	vmovdqa	-44(%rsi), %xmm0
	vmovdqa	%xmm13, -176(%rbp)
	vpaddd	-288(%rbp), %xmm6, %xmm6
	vmovdqa	%xmm1, -320(%rbp)
	sall	$8, %r8d
	vpmulld	.LC3(%rip), %xmm1, %xmm1
	vpmulld	.LC0(%rip), %xmm2, %xmm2
	vpmovzxbd	%xmm0, %xmm7
	vpsrldq	$4, %xmm0, %xmm12
	vmovdqa	%xmm1, -224(%rbp)
	vpmulld	.LC4(%rip), %xmm7, %xmm8
	vpsrldq	$8, %xmm0, %xmm1
	vpsrldq	$12, %xmm0, %xmm0
	vpmovzxbd	%xmm12, %xmm12
	vmovdqa	%xmm3, -304(%rbp)
	vpmovzxbd	%xmm0, %xmm0
	vpmovzxbd	%xmm1, %xmm1
	vpaddd	%xmm12, %xmm6, %xmm6
	vpmulld	.LC7(%rip), %xmm0, %xmm11
	vmovdqa	%xmm0, -352(%rbp)
	vmovdqa	-28(%rsi), %xmm0
	orl	%edi, %r8d
	vpmulld	.LC6(%rip), %xmm1, %xmm10
	vpaddd	-352(%rbp), %xmm1, %xmm1
	vmovdqa	%xmm2, -192(%rbp)
	vpmulld	.LC2(%rip), %xmm3, %xmm3
	vpsrldq	$4, %xmm0, %xmm13
	vpmovzxbd	%xmm0, %xmm15
	vmovdqa	%xmm3, -208(%rbp)
	vpmulld	.LC16(%rip), %xmm15, %xmm4
	vpsrldq	$8, %xmm0, %xmm14
	vpsrldq	$12, %xmm0, %xmm0
	vpmovzxbd	%xmm13, %xmm13
	vmovdqa	%xmm7, -336(%rbp)
	vpmovzxbd	%xmm0, %xmm5
	vpmovzxbd	%xmm14, %xmm14
	vpaddd	%xmm15, %xmm6, %xmm6
	vpmulld	.LC17(%rip), %xmm13, %xmm0
	vmovdqa	%xmm0, -256(%rbp)
	vmovdqa	-12(%rsi), %xmm0
	vpmulld	.LC5(%rip), %xmm12, %xmm7
	vpaddd	%xmm14, %xmm1, %xmm1
	vmovdqa	%xmm7, -240(%rbp)
	vpaddd	%xmm13, %xmm1, %xmm1
	vpmulld	.LC18(%rip), %xmm14, %xmm9
	vmovdqa	-320(%rbp), %xmm15
	vpsrldq	$4, %xmm0, %xmm3
	vpmovzxbd	%xmm0, %xmm7
	vmovdqa	%xmm9, -272(%rbp)
	vpmulld	.LC19(%rip), %xmm5, %xmm9
	vpsrldq	$8, %xmm0, %xmm2
	vpsrldq	$12, %xmm0, %xmm0
	vpaddd	%xmm7, %xmm1, %xmm1
	vpmovzxbd	%xmm0, %xmm0
	vpmovzxbd	%xmm2, %xmm2
	vpmovzxbd	%xmm3, %xmm3
	vpaddd	%xmm0, %xmm6, %xmm6
	vpaddd	%xmm6, %xmm1, %xmm1
	vpaddd	-304(%rbp), %xmm15, %xmm6
	vpaddd	-336(%rbp), %xmm6, %xmm6
	vmovdqa	.LC20(%rip), %xmm14
	vpmulld	.LC6(%rip), %xmm10, %xmm12
	vmovdqa	.LC23(%rip), %xmm15
	vmovdqa	-176(%rbp), %xmm13
	vpaddd	%xmm5, %xmm6, %xmm5
	vpmulld	%xmm14, %xmm7, %xmm7
	vpaddd	%xmm2, %xmm5, %xmm5
	vpmulld	%xmm15, %xmm0, %xmm0
	vpmulld	.LC22(%rip), %xmm2, %xmm2
	vpaddd	%xmm3, %xmm5, %xmm5
	vpmulld	.LC21(%rip), %xmm3, %xmm3
	vpaddd	%xmm5, %xmm1, %xmm6
	vpaddd	-240(%rbp), %xmm8, %xmm1
	vmovdqa	-224(%rbp), %xmm5
	vpaddd	-208(%rbp), %xmm5, %xmm5
	vpaddd	%xmm4, %xmm1, %xmm1
	vpaddd	%xmm11, %xmm5, %xmm5
	vpaddd	-272(%rbp), %xmm5, %xmm5
	vpaddd	%xmm9, %xmm1, %xmm1
	vpaddd	%xmm3, %xmm5, %xmm5
	vpaddd	%xmm2, %xmm1, %xmm1
	vpaddd	%xmm5, %xmm1, %xmm1
	vpaddd	-192(%rbp), %xmm13, %xmm5
	vpmulld	.LC1(%rip), %xmm13, %xmm13
	vpaddd	%xmm10, %xmm5, %xmm5
	vpaddd	-256(%rbp), %xmm5, %xmm5
	vpaddd	%xmm7, %xmm5, %xmm5
	vpaddd	%xmm0, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm1, %xmm1
	vpmulld	.LC7(%rip), %xmm11, %xmm5
	vpaddd	%xmm12, %xmm5, %xmm12
	vpmulld	.LC19(%rip), %xmm9, %xmm5
	vpaddd	%xmm5, %xmm12, %xmm5
	vpmulld	.LC16(%rip), %xmm4, %xmm12
	vpaddd	%xmm12, %xmm5, %xmm12
	vpmulld	.LC21(%rip), %xmm3, %xmm5
	vpaddd	%xmm5, %xmm12, %xmm12
	vmovdqa	-192(%rbp), %xmm5
	vpmulld	.LC0(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm13, %xmm5
	vpmulld	.LC4(%rip), %xmm8, %xmm13
	vpaddd	%xmm13, %xmm5, %xmm13
	vmovdqa	-256(%rbp), %xmm5
	vpmulld	.LC17(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm13, %xmm5
	vpmulld	.LC22(%rip), %xmm2, %xmm13
	vpaddd	%xmm13, %xmm5, %xmm5
	vmovdqa	-208(%rbp), %xmm13
	vpmulld	.LC2(%rip), %xmm13, %xmm13
	vpaddd	%xmm5, %xmm12, %xmm12
	vmovdqa	-224(%rbp), %xmm5
	vpmulld	.LC3(%rip), %xmm5, %xmm5
	vpaddd	%xmm13, %xmm5, %xmm13
	vmovdqa	-240(%rbp), %xmm5
	vpmulld	.LC5(%rip), %xmm5, %xmm5
	vpaddd	%xmm5, %xmm13, %xmm5
	vmovdqa	-272(%rbp), %xmm13
	vpmulld	.LC18(%rip), %xmm13, %xmm13
	vpaddd	%xmm13, %xmm5, %xmm13
	vpmulld	%xmm15, %xmm0, %xmm5
	vpmulld	.LC14(%rip), %xmm11, %xmm11
	vpmulld	.LC10(%rip), %xmm10, %xmm10
	vpaddd	%xmm10, %xmm11, %xmm10
	vpmulld	.LC25(%rip), %xmm9, %xmm9
	vpmulld	.LC27(%rip), %xmm4, %xmm4
	vpmulld	.LC26(%rip), %xmm3, %xmm3
	vpaddd	%xmm9, %xmm10, %xmm9
	vpmulld	.LC11(%rip), %xmm8, %xmm8
	vpmulld	.LC31(%rip), %xmm2, %xmm2
	vpmulld	.LC30(%rip), %xmm0, %xmm0
	vpaddd	%xmm4, %xmm9, %xmm4
	vpaddd	%xmm3, %xmm4, %xmm3
	vmovdqa	-192(%rbp), %xmm4
	vpmulld	.LC8(%rip), %xmm4, %xmm4
	vpaddd	%xmm5, %xmm13, %xmm5
	vpmulld	%xmm14, %xmm7, %xmm13
	vpmulld	.LC29(%rip), %xmm7, %xmm7
	vpaddd	%xmm13, %xmm5, %xmm5
	vmovdqa	-176(%rbp), %xmm13
	vpmulld	.LC9(%rip), %xmm13, %xmm9
	vpaddd	%xmm4, %xmm9, %xmm4
	vpaddd	%xmm8, %xmm4, %xmm8
	vmovdqa	-256(%rbp), %xmm4
	vmovdqa	-208(%rbp), %xmm13
	vpaddd	%xmm5, %xmm12, %xmm5
	vpmulld	.LC28(%rip), %xmm4, %xmm4
	vpaddd	%xmm4, %xmm8, %xmm4
	vmovdqa	-240(%rbp), %xmm12
	vpaddd	%xmm2, %xmm4, %xmm4
	vmovdqa	-224(%rbp), %xmm2
	vpmulld	.LC13(%rip), %xmm2, %xmm2
	vpaddd	%xmm4, %xmm3, %xmm4
	vpmulld	.LC12(%rip), %xmm13, %xmm3
	vpaddd	%xmm3, %xmm2, %xmm3
	vmovdqa	-272(%rbp), %xmm13
	vpmulld	.LC15(%rip), %xmm12, %xmm2
	vpaddd	%xmm2, %xmm3, %xmm2
	vpmulld	.LC24(%rip), %xmm13, %xmm3
	vpaddd	%xmm3, %xmm2, %xmm3
	vpunpckhqdq	%xmm6, %xmm6, %xmm2
	vpaddd	%xmm2, %xmm6, %xmm2
	vpaddd	%xmm0, %xmm3, %xmm0
	vpshufd	$177, %xmm2, %xmm3
	vpaddd	%xmm7, %xmm0, %xmm0
	vmovd	%r8d, %xmm7
	vpaddd	%xmm2, %xmm3, %xmm2
	vpaddd	%xmm0, %xmm4, %xmm0
	vmovdqa	%xmm2, -416(%rbp)
	vpunpckhqdq	%xmm1, %xmm1, %xmm2
	vpaddd	%xmm2, %xmm1, %xmm1
	vpshufd	$177, %xmm1, %xmm2
	vpaddd	%xmm1, %xmm2, %xmm3
	vpunpckhqdq	%xmm5, %xmm5, %xmm1
	vpaddd	%xmm1, %xmm5, %xmm1
	vmovdqa	%xmm3, -448(%rbp)
	vpshufd	$177, %xmm1, %xmm2
	vpaddd	%xmm1, %xmm2, %xmm1
	vmovdqa	%xmm1, -464(%rbp)
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpshufd	$177, %xmm0, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm5
	vmovd	.LC76(%rip), %xmm0
	vmovdqa	%xmm5, -480(%rbp)
	vpaddb	%xmm0, %xmm7, %xmm7
	vmovd	%xmm7, (%rcx)
	vmovdqa	-60(%rsi), %xmm1
	vmovd	%xmm7, %r8d
	vpsrldq	$4, %xmm1, %xmm10
	vpsrldq	$8, %xmm1, %xmm2
	vpmovzxbd	%xmm1, %xmm0
	vpmovzxbd	%xmm10, %xmm3
	vpsrldq	$12, %xmm1, %xmm1
	vpmovzxbd	%xmm2, %xmm4
	vpmulld	.LC0(%rip), %xmm0, %xmm2
	vmovdqa	%xmm2, -208(%rbp)
	vpmovzxbd	%xmm1, %xmm6
	vmovdqa	%xmm3, -288(%rbp)
	vmovdqa	-44(%rsi), %xmm2
	vpmulld	.LC2(%rip), %xmm4, %xmm10
	vpmulld	.LC1(%rip), %xmm3, %xmm3
	vmovdqa	%xmm4, -304(%rbp)
	vpaddd	-288(%rbp), %xmm0, %xmm0
	vpmulld	.LC3(%rip), %xmm6, %xmm13
	vpsrldq	$4, %xmm2, %xmm9
	vpmovzxbd	%xmm2, %xmm11
	vmovdqa	%xmm3, -176(%rbp)
	vpmulld	.LC4(%rip), %xmm11, %xmm4
	vpsrldq	$8, %xmm2, %xmm1
	vpsrldq	$12, %xmm2, %xmm2
	vpmovzxbd	%xmm9, %xmm9
	vmovdqa	%xmm11, -320(%rbp)
	vpmovzxbd	%xmm2, %xmm7
	vmovdqa	-28(%rsi), %xmm2
	vpaddd	%xmm9, %xmm0, %xmm0
	vpmulld	.LC5(%rip), %xmm9, %xmm11
	vpmovzxbd	%xmm1, %xmm1
	vmovdqa	%xmm11, -240(%rbp)
	vpmulld	.LC6(%rip), %xmm1, %xmm12
	vpmulld	.LC7(%rip), %xmm7, %xmm8
	vpmovzxbd	%xmm2, %xmm3
	vmovdqa	%xmm12, -192(%rbp)
	vpaddd	%xmm7, %xmm1, %xmm1
	vpsrldq	$8, %xmm2, %xmm12
	vpsrldq	$4, %xmm2, %xmm11
	vmovdqa	%xmm4, -224(%rbp)
	vpsrldq	$12, %xmm2, %xmm2
	vpmovzxbd	%xmm12, %xmm4
	vpmovzxbd	%xmm11, %xmm11
	vpmulld	.LC16(%rip), %xmm3, %xmm12
	vpmovzxbd	%xmm2, %xmm5
	vmovdqa	.LC18(%rip), %xmm2
	vmovdqa	%xmm4, -368(%rbp)
	vpaddd	-368(%rbp), %xmm1, %xmm1
	vmovdqa	%xmm3, -336(%rbp)
	vpaddd	-336(%rbp), %xmm0, %xmm0
	vpmulld	.LC19(%rip), %xmm5, %xmm3
	vpmulld	%xmm4, %xmm2, %xmm2
	vmovdqa	-12(%rsi), %xmm4
	vmovdqa	%xmm3, -272(%rbp)
	vmovdqa	%xmm11, -352(%rbp)
	vpaddd	-352(%rbp), %xmm1, %xmm1
	vpmulld	.LC17(%rip), %xmm11, %xmm11
	vpsrldq	$4, %xmm4, %xmm3
	vpmovzxbd	%xmm3, %xmm3
	vmovdqa	%xmm2, -256(%rbp)
	vpmovzxbd	%xmm4, %xmm2
	vmovdqa	%xmm2, -400(%rbp)
	vpsrldq	$8, %xmm4, %xmm2
	vpsrldq	$12, %xmm4, %xmm4
	vpaddd	-400(%rbp), %xmm1, %xmm1
	vpmovzxbd	%xmm4, %xmm4
	vpmovzxbd	%xmm2, %xmm2
	vpaddd	%xmm4, %xmm0, %xmm0
	vpmulld	%xmm15, %xmm4, %xmm7
	vpaddd	%xmm0, %xmm1, %xmm0
	vpaddd	-304(%rbp), %xmm6, %xmm1
	vpaddd	-320(%rbp), %xmm1, %xmm1
	vmovdqa	-176(%rbp), %xmm6
	vpmulld	-400(%rbp), %xmm14, %xmm9
	vpaddd	%xmm5, %xmm1, %xmm1
	vmovdqa	-192(%rbp), %xmm5
	vpaddd	%xmm2, %xmm1, %xmm1
	vpmulld	.LC22(%rip), %xmm2, %xmm2
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmulld	.LC21(%rip), %xmm3, %xmm3
	vpaddd	%xmm1, %xmm0, %xmm1
	vmovdqa	-240(%rbp), %xmm0
	vpaddd	-224(%rbp), %xmm0, %xmm4
	vpaddd	%xmm13, %xmm10, %xmm0
	vpaddd	%xmm8, %xmm0, %xmm0
	vpaddd	%xmm12, %xmm4, %xmm4
	vpaddd	-256(%rbp), %xmm0, %xmm0
	vpaddd	-272(%rbp), %xmm4, %xmm4
	vpaddd	%xmm3, %xmm0, %xmm0
	vpaddd	%xmm2, %xmm4, %xmm4
	vpaddd	%xmm0, %xmm4, %xmm4
	vpaddd	-208(%rbp), %xmm6, %xmm0
	vpmulld	.LC1(%rip), %xmm6, %xmm6
	vpaddd	%xmm5, %xmm0, %xmm0
	vpmulld	.LC6(%rip), %xmm5, %xmm5
	vpaddd	%xmm11, %xmm0, %xmm0
	vpaddd	%xmm9, %xmm0, %xmm0
	vpaddd	%xmm7, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm4, %xmm4
	vpmulld	.LC7(%rip), %xmm8, %xmm0
	vpaddd	%xmm5, %xmm0, %xmm5
	vmovdqa	-272(%rbp), %xmm0
	vpmulld	.LC19(%rip), %xmm0, %xmm0
	vpaddd	%xmm0, %xmm5, %xmm0
	vpmulld	.LC16(%rip), %xmm12, %xmm5
	vpmulld	.LC14(%rip), %xmm8, %xmm8
	vpaddd	%xmm5, %xmm0, %xmm5
	vpmulld	.LC21(%rip), %xmm3, %xmm0
	vpaddd	%xmm0, %xmm5, %xmm5
	vmovdqa	-208(%rbp), %xmm0
	vpmulld	.LC0(%rip), %xmm0, %xmm0
	vpaddd	%xmm0, %xmm6, %xmm0
	vmovdqa	-224(%rbp), %xmm6
	vpmulld	.LC4(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm0, %xmm6
	vpmulld	.LC17(%rip), %xmm11, %xmm0
	vpaddd	%xmm0, %xmm6, %xmm0
	vpmulld	.LC22(%rip), %xmm2, %xmm6
	vpaddd	%xmm6, %xmm0, %xmm0
	vpmulld	.LC2(%rip), %xmm10, %xmm6
	vpaddd	%xmm0, %xmm5, %xmm5
	vpmulld	.LC3(%rip), %xmm13, %xmm0
	vpaddd	%xmm6, %xmm0, %xmm6
	vmovdqa	-240(%rbp), %xmm0
	vpmulld	.LC5(%rip), %xmm0, %xmm0
	vpaddd	%xmm0, %xmm6, %xmm0
	vmovdqa	-256(%rbp), %xmm6
	vpmulld	.LC18(%rip), %xmm6, %xmm6
	vpaddd	%xmm6, %xmm0, %xmm6
	vpmulld	%xmm15, %xmm7, %xmm0
	vmovdqa	-192(%rbp), %xmm15
	vpaddd	%xmm0, %xmm6, %xmm0
	vpmulld	%xmm14, %xmm9, %xmm6
	vpaddd	%xmm6, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm5, %xmm0
	vpmulld	.LC10(%rip), %xmm15, %xmm5
	vpaddd	%xmm5, %xmm8, %xmm5
	vmovdqa	-272(%rbp), %xmm14
	vpmulld	.LC25(%rip), %xmm14, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm6
	vpmulld	.LC27(%rip), %xmm12, %xmm5
	vpmulld	.LC26(%rip), %xmm3, %xmm3
	vpaddd	%xmm5, %xmm6, %xmm6
	movl	-416(%rbp), %r9d
	vmovdqa	-208(%rbp), %xmm5
	vpmulld	.LC8(%rip), %xmm5, %xmm5
	vpmulld	.LC31(%rip), %xmm2, %xmm2
	vpaddd	%xmm3, %xmm6, %xmm6
	vmovdqa	-176(%rbp), %xmm3
	vpmulld	.LC9(%rip), %xmm3, %xmm3
	vpmulld	.LC30(%rip), %xmm7, %xmm7
	vpaddd	%xmm5, %xmm3, %xmm3
	vmovdqa	-224(%rbp), %xmm5
	vpmulld	.LC11(%rip), %xmm5, %xmm5
	vpmulld	.LC29(%rip), %xmm9, %xmm9
	vpaddd	%xmm5, %xmm3, %xmm3
	vpmulld	.LC28(%rip), %xmm11, %xmm5
	vmovdqa	-240(%rbp), %xmm11
	vpaddd	%xmm5, %xmm3, %xmm3
	vpaddd	%xmm2, %xmm3, %xmm3
	vpmulld	.LC13(%rip), %xmm13, %xmm2
	vpaddd	%xmm3, %xmm6, %xmm6
	vpmulld	.LC12(%rip), %xmm10, %xmm3
	vpaddd	%xmm3, %xmm2, %xmm2
	vpmulld	.LC15(%rip), %xmm11, %xmm3
	vpaddd	%xmm3, %xmm2, %xmm2
	vmovdqa	-256(%rbp), %xmm3
	vpmulld	.LC24(%rip), %xmm3, %xmm3
	vpaddd	%xmm3, %xmm2, %xmm2
	vpunpckhqdq	%xmm1, %xmm1, %xmm3
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm7, %xmm2, %xmm2
	vpshufd	$177, %xmm1, %xmm3
	vpaddd	%xmm9, %xmm2, %xmm2
	vpaddd	%xmm1, %xmm3, %xmm3
	vpunpckhqdq	%xmm4, %xmm4, %xmm1
	vpaddd	%xmm2, %xmm6, %xmm2
	vpaddd	%xmm1, %xmm4, %xmm4
	vmovd	%xmm3, %edi
	vpshufd	$177, %xmm4, %xmm1
	subq	%r9, %rdi
	movl	-448(%rbp), %r9d
	vpaddd	%xmm4, %xmm1, %xmm4
	vpunpckhqdq	%xmm0, %xmm0, %xmm1
	movq	%rdi, -144(%rbp)
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm4, %edi
	vpshufd	$177, %xmm0, %xmm1
	subq	%r9, %rdi
	movl	-464(%rbp), %r9d
	vpaddd	%xmm0, %xmm1, %xmm1
	vpunpckhqdq	%xmm2, %xmm2, %xmm0
	movq	%rdi, -136(%rbp)
	vpaddd	%xmm0, %xmm2, %xmm2
	vmovd	%xmm1, %edi
	vpshufd	$177, %xmm2, %xmm0
	subq	%r9, %rdi
	movl	-480(%rbp), %r9d
	vpaddd	%xmm2, %xmm0, %xmm0
	movq	%rdi, -128(%rbp)
	vmovd	%r8d, %xmm2
	vmovd	%xmm0, %edi
	vpxor	%xmm0, %xmm0, %xmm0
	vpextrb	$0, %xmm2, %r8d
	subq	%r9, %rdi
	vmovdqa	%ymm0, -112(%rbp)
	movq	%rdi, -120(%rbp)
	vpxor	-144(%rbp), %ymm0, %ymm0
	xorl	%edi, %edi
	vptest	%ymm0, %ymm0
	setne	%dil
	addq	$1, %rbx
	addq	%rdi, %r14
	movzbl	3(%rcx), %edi
	movzbl	2(%rcx), %r9d
	vmovd	.LC77(%rip), %xmm0
	sall	$8, %edi
	orl	%r9d, %edi
	movzbl	1(%rcx), %r9d
	sall	$8, %edi
	orl	%r9d, %edi
	sall	$8, %edi
	orl	%r8d, %edi
	vmovd	%edi, %xmm2
	vpaddb	%xmm0, %xmm2, %xmm0
	vmovd	%xmm0, (%rcx)
	jmp	.L402
.L519:
	vxorps	%xmm4, %xmm4, %xmm4
	movq	-488(%rbp), %rsi
	movq	-424(%rbp), %rdi
	movl	$41312, %edx
	vmovaps	%xmm4, -192(%rbp)
	movq	-208(%rbp), %r15
	movq	-224(%rbp), %r13
	movq	-240(%rbp), %rbx
	movq	-256(%rbp), %r14
	vzeroupper
	call	memcpy@PLT
	movl	$256, %edx
	vmovaps	-192(%rbp), %xmm4
	movq	-616(%rbp), %rsi
	leaq	.LC81(%rip), %rdi
	movl	$1, %eax
	vcvtsi2sdq	%rsi, %xmm4, %xmm0
	vmulsd	.LC80(%rip), %xmm0, %xmm0
	call	printf@PLT
	movq	-504(%rbp), %rax
	vxorpd	%xmm0, %xmm0, %xmm0
	vmovaps	-192(%rbp), %xmm4
	testq	%rax, %rax
	je	.L427
	vcvtsi2sdq	-560(%rbp), %xmm4, %xmm0
	vcvtsi2sdq	%rax, %xmm4, %xmm1
	vdivsd	%xmm1, %xmm0, %xmm0
.L427:
	movq	-504(%rbp), %rdx
	movq	-560(%rbp), %rsi
	leaq	.LC82(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm4, -192(%rbp)
	call	printf@PLT
	movq	-584(%rbp), %rax
	vmovaps	-192(%rbp), %xmm4
	testq	%rax, %rax
	je	.L445
	vcvtsi2sdq	-536(%rbp), %xmm4, %xmm3
	vcvtsi2sdq	%rax, %xmm4, %xmm0
	vcvtsi2sdq	-528(%rbp), %xmm4, %xmm2
	vdivsd	%xmm0, %xmm3, %xmm3
	vdivsd	%xmm0, %xmm2, %xmm2
.L428:
	movq	-576(%rbp), %rax
	testq	%rax, %rax
	je	.L446
	vcvtsi2sdq	-520(%rbp), %xmm4, %xmm1
	vcvtsi2sdq	%rax, %xmm4, %xmm5
	vcvtsi2sdq	-512(%rbp), %xmm4, %xmm0
	vdivsd	%xmm5, %xmm1, %xmm1
	vdivsd	%xmm5, %xmm0, %xmm0
.L429:
	leaq	.LC83(%rip), %rdi
	movl	$4, %eax
	vmovaps	%xmm4, -192(%rbp)
	call	printf@PLT
	cmpq	$0, -504(%rbp)
	vmovaps	-192(%rbp), %xmm4
	jne	.L430
	movq	-544(%rbp), %rsi
	vxorpd	%xmm0, %xmm0, %xmm0
	xorl	%edx, %edx
	leaq	.LC84(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	vmovaps	-192(%rbp), %xmm4
	vxorpd	%xmm0, %xmm0, %xmm0
.L431:
	movq	-504(%rbp), %rdx
	movq	-552(%rbp), %rsi
	leaq	.LC85(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm4, -192(%rbp)
	call	printf@PLT
	movq	-592(%rbp), %rsi
	xorl	%eax, %eax
	leaq	.LC86(%rip), %rdi
	call	printf@PLT
	testq	%rbx, %rbx
	vxorpd	%xmm0, %xmm0, %xmm0
	vmovaps	-192(%rbp), %xmm4
	je	.L432
	vcvtsi2sdq	%r14, %xmm4, %xmm0
	vcvtsi2sdq	%rbx, %xmm4, %xmm1
	vdivsd	%xmm1, %xmm0, %xmm0
.L432:
	movq	%rbx, %rdx
	movq	%r14, %rsi
	leaq	.LC87(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm4, -192(%rbp)
	call	printf@PLT
	vxorpd	%xmm0, %xmm0, %xmm0
	testq	%r13, %r13
	je	.L433
	vmovaps	-192(%rbp), %xmm4
	vcvtsi2sdq	%r15, %xmm4, %xmm0
	vcvtsi2sdq	%r13, %xmm4, %xmm1
	vdivsd	%xmm1, %xmm0, %xmm0
.L433:
	movq	%r13, %rdx
	movq	%r15, %rsi
	movl	$1, %eax
	leaq	.LC88(%rip), %rdi
	call	printf@PLT
	movq	-176(%rbp), %rsi
	xorl	%eax, %eax
	movl	$200, %edx
	leaq	.LC89(%rip), %rdi
	call	printf@PLT
	movq	-56(%rbp), %rax
	subq	%fs:40, %rax
	jne	.L522
	addq	$608, %rsp
	xorl	%eax, %eax
	popq	%rbx
	popq	%r10
	.cfi_remember_state
	.cfi_def_cfa 10, 0
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%r15
	popq	%rbp
	leaq	-8(%r10), %rsp
	.cfi_def_cfa 7, 8
	ret
.L430:
	.cfi_restore_state
	movq	-504(%rbp), %rdx
	movq	-544(%rbp), %rsi
	leaq	.LC84(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm4, -208(%rbp)
	vcvtsi2sdq	%rdx, %xmm4, %xmm1
	vcvtsi2sdq	%rsi, %xmm4, %xmm0
	vdivsd	%xmm1, %xmm0, %xmm0
	vmovsd	%xmm1, -192(%rbp)
	call	printf@PLT
	vmovaps	-208(%rbp), %xmm4
	vcvtsi2sdq	-552(%rbp), %xmm4, %xmm0
	vdivsd	-192(%rbp), %xmm0, %xmm0
	jmp	.L431
.L446:
	vxorpd	%xmm1, %xmm1, %xmm1
	vmovapd	%xmm1, %xmm0
	jmp	.L429
.L445:
	vxorpd	%xmm3, %xmm3, %xmm3
	vmovapd	%xmm3, %xmm2
	jmp	.L428
.L374:
	leaq	snap.3(%rip), %rax
	movq	-424(%rbp), %rsi
	movl	$41312, %edx
	leaq	slot_snap.1(%rip), %rbx
	movq	%rax, %rdi
	movq	%rax, -488(%rbp)
	movabsq	$-8050056175193481693, %r12
	call	memcpy@PLT
	leaq	csnap.2(%rip), %rax
	movl	$16384, %edx
	leaq	contents.4(%rip), %rsi
	movq	%rax, %rdi
	movq	%rax, -608(%rbp)
	call	memcpy@PLT
	movl	$4096, %edx
	leaq	sqm_slot_of(%rip), %rsi
	movq	%rbx, %rdi
	call	memcpy@PLT
	xorl	%eax, %eax
	xorl	%edx, %edx
	movq	%rax, -560(%rbp)
	movq	%rax, -584(%rbp)
	movq	%rax, -536(%rbp)
	movq	%rax, -528(%rbp)
	movq	%rax, -576(%rbp)
	movq	%rax, -520(%rbp)
	movq	%rax, -512(%rbp)
	movabsq	$7683277266246660415, %rax
	movq	%rax, -432(%rbp)
	movabsq	$-1749540032614691874, %rax
	movq	%rax, -496(%rbp)
	movabsq	$1600686389938274267, %rax
	movq	%rax, -568(%rbp)
	movq	%rdx, -592(%rbp)
	movq	%rdx, -504(%rbp)
	movq	%rdx, -552(%rbp)
	movq	%rdx, -544(%rbp)
	jmp	.L438
.L522:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE7309:
	.size	main, .-main
	.local	action.0
	.comm	action.0,256,32
	.local	slot_snap.1
	.comm	slot_snap.1,4096,32
	.local	csnap.2
	.comm	csnap.2,16384,32
	.local	snap.3
	.comm	snap.3,41312,32
	.local	contents.4
	.comm	contents.4,16384,32
	.local	cell.5
	.comm	cell.5,41312,32
	.local	sqm_item_at
	.comm	sqm_item_at,1024,32
	.local	sqm_slot_of
	.comm	sqm_slot_of,4096,32
	.section	.rodata
	.align 32
	.type	SQM_SCATLT, @object
	.size	SQM_SCATLT, 128
SQM_SCATLT:
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
	.local	esf_v2_tables_ready
	.comm	esf_v2_tables_ready,4,4
	.local	esf_idx2_table
	.comm	esf_idx2_table,16272,32
	.local	esf_idx_table
	.comm	esf_idx_table,16272,32
	.section	.rodata.cst16,"aM",@progbits,16
	.align 16
.LC0:
	.long	1
	.long	2
	.long	3
	.long	4
	.align 16
.LC1:
	.long	5
	.long	6
	.long	7
	.long	8
	.align 16
.LC2:
	.long	9
	.long	10
	.long	11
	.long	12
	.align 16
.LC3:
	.long	13
	.long	14
	.long	15
	.long	16
	.align 16
.LC4:
	.long	17
	.long	18
	.long	19
	.long	20
	.align 16
.LC5:
	.long	21
	.long	22
	.long	23
	.long	24
	.align 16
.LC6:
	.long	25
	.long	26
	.long	27
	.long	28
	.align 16
.LC7:
	.long	29
	.long	30
	.long	31
	.long	32
	.align 16
.LC8:
	.long	1
	.long	4
	.long	9
	.long	16
	.align 16
.LC9:
	.long	25
	.long	36
	.long	49
	.long	64
	.align 16
.LC10:
	.long	625
	.long	676
	.long	729
	.long	784
	.align 16
.LC11:
	.long	289
	.long	324
	.long	361
	.long	400
	.align 16
.LC12:
	.long	81
	.long	100
	.long	121
	.long	144
	.align 16
.LC13:
	.long	169
	.long	196
	.long	225
	.long	256
	.align 16
.LC14:
	.long	841
	.long	900
	.long	961
	.long	1024
	.align 16
.LC15:
	.long	441
	.long	484
	.long	529
	.long	576
	.align 16
.LC16:
	.long	33
	.long	34
	.long	35
	.long	36
	.align 16
.LC17:
	.long	37
	.long	38
	.long	39
	.long	40
	.align 16
.LC18:
	.long	41
	.long	42
	.long	43
	.long	44
	.align 16
.LC19:
	.long	45
	.long	46
	.long	47
	.long	48
	.align 16
.LC20:
	.long	49
	.long	50
	.long	51
	.long	52
	.align 16
.LC21:
	.long	53
	.long	54
	.long	55
	.long	56
	.align 16
.LC22:
	.long	57
	.long	58
	.long	59
	.long	60
	.align 16
.LC23:
	.long	61
	.long	62
	.long	63
	.long	64
	.align 16
.LC24:
	.long	1681
	.long	1764
	.long	1849
	.long	1936
	.align 16
.LC25:
	.long	2025
	.long	2116
	.long	2209
	.long	2304
	.align 16
.LC26:
	.long	2809
	.long	2916
	.long	3025
	.long	3136
	.align 16
.LC27:
	.long	1089
	.long	1156
	.long	1225
	.long	1296
	.align 16
.LC28:
	.long	1369
	.long	1444
	.long	1521
	.long	1600
	.align 16
.LC29:
	.long	2401
	.long	2500
	.long	2601
	.long	2704
	.align 16
.LC30:
	.long	3721
	.long	3844
	.long	3969
	.long	4096
	.align 16
.LC31:
	.long	3249
	.long	3364
	.long	3481
	.long	3600
	.align 16
.LC32:
	.quad	1
	.quad	64
	.section	.rodata.cst8,"aM",@progbits,8
	.align 8
.LC34:
	.long	-400107883
	.long	1041313291
	.align 8
.LC35:
	.long	0
	.long	1017118720
	.section	.rodata.cst32,"aM",@progbits,32
	.align 32
.LC36:
	.quad	0
	.quad	1
	.quad	2
	.quad	3
	.section	.rodata.cst8
	.align 8
.LC38:
	.quad	4
	.align 8
.LC41:
	.long	0
	.long	1079574528
	.section	.rodata.cst32
	.align 32
.LC46:
	.long	0
	.long	1
	.long	2
	.long	3
	.long	4
	.long	5
	.long	6
	.long	7
	.section	.rodata.cst16
	.align 16
.LC49:
	.long	4077
	.long	4078
	.long	4079
	.long	4080
	.align 16
.LC50:
	.long	16621929
	.long	16630084
	.long	16638241
	.long	16646400
	.set	.LC51,.LC0
	.set	.LC52,.LC0+8
	.set	.LC53,.LC1
	.set	.LC54,.LC1+8
	.section	.rodata.cst32
	.align 32
.LC55:
	.byte	0
	.byte	91
	.byte	-74
	.byte	17
	.byte	108
	.byte	-57
	.byte	34
	.byte	125
	.byte	-40
	.byte	51
	.byte	-114
	.byte	-23
	.byte	68
	.byte	-97
	.byte	-6
	.byte	85
	.byte	-80
	.byte	11
	.byte	102
	.byte	-63
	.byte	28
	.byte	119
	.byte	-46
	.byte	45
	.byte	-120
	.byte	-29
	.byte	62
	.byte	-103
	.byte	-12
	.byte	79
	.byte	-86
	.byte	5
	.align 32
.LC57:
	.byte	96
	.byte	-69
	.byte	22
	.byte	113
	.byte	-52
	.byte	39
	.byte	-126
	.byte	-35
	.byte	56
	.byte	-109
	.byte	-18
	.byte	73
	.byte	-92
	.byte	-1
	.byte	90
	.byte	-75
	.byte	16
	.byte	107
	.byte	-58
	.byte	33
	.byte	124
	.byte	-41
	.byte	50
	.byte	-115
	.byte	-24
	.byte	67
	.byte	-98
	.byte	-7
	.byte	84
	.byte	-81
	.byte	10
	.byte	101
	.align 32
.LC59:
	.long	8
	.long	9
	.long	10
	.long	11
	.long	12
	.long	13
	.long	14
	.long	15
	.align 32
.LC60:
	.long	16
	.long	17
	.long	18
	.long	19
	.long	20
	.long	21
	.long	22
	.long	23
	.align 32
.LC61:
	.long	24
	.long	25
	.long	26
	.long	27
	.long	28
	.long	29
	.long	30
	.long	31
	.align 32
.LC64:
	.long	32
	.long	33
	.long	34
	.long	35
	.long	36
	.long	37
	.long	38
	.long	39
	.align 32
.LC65:
	.long	40
	.long	41
	.long	42
	.long	43
	.long	44
	.long	45
	.long	46
	.long	47
	.align 32
.LC66:
	.long	48
	.long	49
	.long	50
	.long	51
	.long	52
	.long	53
	.long	54
	.long	55
	.align 32
.LC67:
	.long	56
	.long	57
	.long	58
	.long	59
	.long	60
	.long	61
	.long	62
	.long	63
	.section	.rodata.cst4,"aM",@progbits,4
	.align 4
.LC76:
	.byte	1
	.byte	-3
	.byte	3
	.byte	-1
	.align 4
.LC77:
	.byte	-1
	.byte	3
	.byte	-3
	.byte	1
	.section	.rodata.cst2,"aM",@progbits,2
	.align 2
.LC78:
	.byte	6
	.byte	-4
	.align 2
.LC79:
	.byte	-6
	.byte	4
	.section	.rodata.cst8
	.align 8
.LC80:
	.long	0
	.long	1064304640
	.ident	"GCC: (GNU) 16.1.1 20260625"
	.section	.note.GNU-stack,"",@progbits

	.file	"sqw_cert.c"
	.text
	.p2align 4
	.type	verify_all_items.constprop.0, @function
verify_all_items.constprop.0:
.LFB53:
	.cfi_startproc
	movq	%rdi, %r11
	leaq	stream.3(%rip), %rdi
	pushq	%rbx
	.cfi_def_cfa_offset 16
	.cfi_offset 3, -16
	leaq	sqw_item_slot_b(%rip), %r9
	leaq	1024(%rdi), %r10
	xorl	%ebx, %ebx
	leaq	sqw_item_slot_g(%rip), %r8
	.p2align 4
	.p2align 3
.L6:
	movslq	(%rdi), %rdx
	movslq	(%r8,%rdx,4), %rax
	movq	%rdx, %rcx
	movslq	(%r9,%rdx,4), %rdx
	imulq	$336, %rax, %rax
	imulq	$10752, %rdx, %rdx
	addq	%rdx, %rax
	addq	%r11, %rax
	cmpl	$-559063315, 164(%rax)
	je	.L3
	movl	%ecx, %edx
	leaq	152(%rax), %rsi
	sall	$4, %edx
	addl	%ecx, %edx
	jmp	.L5
	.p2align 5
	.p2align 4,,10
	.p2align 3
.L12:
	addq	$1, %rax
	addl	$91, %edx
	cmpq	%rsi, %rax
	je	.L11
.L5:
	movl	%edx, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, (%rax)
	je	.L12
.L3:
	addq	$4, %rdi
	cmpq	%r10, %rdi
	jne	.L6
.L13:
	movq	%rbx, %rax
	popq	%rbx
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L11:
	.cfi_restore_state
	addq	$4, %rdi
	addq	$1, %rbx
	cmpq	%r10, %rdi
	jne	.L6
	jmp	.L13
	.cfi_endproc
.LFE53:
	.size	verify_all_items.constprop.0, .-verify_all_items.constprop.0
	.p2align 4
	.type	__bswap_16, @function
__bswap_16:
.LFB14:
	.cfi_startproc
	movl	%edi, %eax
	rolw	$8, %ax
	ret
	.cfi_endproc
.LFE14:
	.size	__bswap_16, .-__bswap_16
	.p2align 4
	.type	__bswap_32, @function
__bswap_32:
.LFB15:
	.cfi_startproc
	movl	%edi, %eax
	bswap	%eax
	ret
	.cfi_endproc
.LFE15:
	.size	__bswap_32, .-__bswap_32
	.p2align 4
	.type	__bswap_64, @function
__bswap_64:
.LFB16:
	.cfi_startproc
	movq	%rdi, %rax
	bswap	%rax
	ret
	.cfi_endproc
.LFE16:
	.size	__bswap_64, .-__bswap_64
	.p2align 4
	.type	__uint16_identity, @function
__uint16_identity:
.LFB17:
	.cfi_startproc
	movl	%edi, %eax
	ret
	.cfi_endproc
.LFE17:
	.size	__uint16_identity, .-__uint16_identity
	.p2align 4
	.type	__uint32_identity, @function
__uint32_identity:
.LFB18:
	.cfi_startproc
	movl	%edi, %eax
	ret
	.cfi_endproc
.LFE18:
	.size	__uint32_identity, .-__uint32_identity
	.p2align 4
	.type	__uint64_identity, @function
__uint64_identity:
.LFB19:
	.cfi_startproc
	movq	%rdi, %rax
	ret
	.cfi_endproc
.LFE19:
	.size	__uint64_identity, .-__uint64_identity
	.section	.rodata.str1.1,"aMS",@progbits,1
.LC0:
	.string	"clock_gettime failed\n"
	.text
	.p2align 4
	.type	cmp_now_sec, @function
cmp_now_sec:
.LFB22:
	.cfi_startproc
	subq	$40, %rsp
	.cfi_def_cfa_offset 48
	movl	$1, %edi
	movq	%fs:40, %rsi
	movq	%rsi, 24(%rsp)
	movq	%rsp, %rsi
	call	clock_gettime@PLT
	testl	%eax, %eax
	jne	.L24
	pxor	%xmm0, %xmm0
	cvtsi2sdq	8(%rsp), %xmm0
	pxor	%xmm1, %xmm1
	cvtsi2sdq	(%rsp), %xmm1
	mulsd	.LC1(%rip), %xmm0
	addsd	%xmm1, %xmm0
	movq	24(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L25
	addq	$40, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
.L24:
	.cfi_restore_state
	movq	stderr(%rip), %rcx
	movl	$21, %edx
	movl	$1, %esi
	leaq	.LC0(%rip), %rdi
	call	fwrite@PLT
	movl	$1, %edi
	call	exit@PLT
.L25:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE22:
	.size	cmp_now_sec, .-cmp_now_sec
	.p2align 4
	.type	cmp_xoshiro256ss, @function
cmp_xoshiro256ss:
.LFB23:
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
	rorq	$19, %rcx
	movq	%rdx, 16(%rdi)
	movq	%r9, (%rdi)
	rolq	$17, %rax
	movq	%rcx, 24(%rdi)
	ret
	.cfi_endproc
.LFE23:
	.size	cmp_xoshiro256ss, .-cmp_xoshiro256ss
	.p2align 4
	.type	cmp_rand_u32, @function
cmp_rand_u32:
.LFB24:
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
	rorq	$19, %rcx
	movq	%rdx, 16(%rdi)
	movq	%r9, (%rdi)
	rolq	$17, %rax
	movq	%rcx, 24(%rdi)
	ret
	.cfi_endproc
.LFE24:
	.size	cmp_rand_u32, .-cmp_rand_u32
	.p2align 4
	.type	cmp_rand01, @function
cmp_rand01:
.LFB25:
	.cfi_startproc
	movq	(%rdi), %rax
	movq	8(%rdi), %rdx
	pxor	%xmm0, %xmm0
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
	rolq	$17, %rax
	xorq	%rcx, %r9
	rorq	$19, %rcx
	movq	%rdx, 16(%rdi)
	shrq	$11, %rax
	movq	%r9, (%rdi)
	cvtsi2sdq	%rax, %xmm0
	movq	%rcx, 24(%rdi)
	mulsd	.LC2(%rip), %xmm0
	ret
	.cfi_endproc
.LFE25:
	.size	cmp_rand01, .-cmp_rand01
	.p2align 4
	.type	cmp_seed, @function
cmp_seed:
.LFB26:
	.cfi_startproc
	movabsq	$-7046029254386353131, %rcx
	movq	%rdi, %r9
	movabsq	$-4658895280553007687, %rdx
	movabsq	$-1100507917760534041, %rdi
	movabsq	$-7723592293110705685, %rax
	addq	%rsi, %rcx
	xorq	%rsi, %rdx
	addq	%rsi, %rax
	xorq	%rdi, %rsi
	movl	$10, %edi
	.p2align 5
	.p2align 4
	.p2align 3
.L30:
	movq	%rdx, %r8
	xorq	%rcx, %rax
	xorq	%rdx, %rsi
	salq	$17, %r8
	xorq	%rax, %rdx
	xorq	%rsi, %rcx
	rorq	$19, %rsi
	xorq	%r8, %rax
	subl	$1, %edi
	jne	.L30
	movq	%rdx, 8(%r9)
	movq	%rcx, (%r9)
	movq	%rax, 16(%r9)
	movq	%rsi, 24(%r9)
	ret
	.cfi_endproc
.LFE26:
	.size	cmp_seed, .-cmp_seed
	.p2align 4
	.type	cmp_pick_unique, @function
cmp_pick_unique:
.LFB27:
	.cfi_startproc
	subq	$40, %rsp
	.cfi_def_cfa_offset 48
	movq	%rbx, 8(%rsp)
	.cfi_offset 3, -40
	movq	%rdi, %rbx
	salq	$3, %rdi
	movq	%rbp, 16(%rsp)
	.cfi_offset 6, -32
	movq	%rdx, %rbp
	movq	%r12, 24(%rsp)
	.cfi_offset 12, -24
	movq	%rsi, %r12
	call	malloc@PLT
	movq	%rax, %rdi
	testq	%rax, %rax
	je	.L32
	cmpq	%rbx, %r12
	movq	%r12, %r10
	cmovg	%rbx, %r10
	testq	%rbx, %rbx
	jle	.L34
	xorl	%eax, %eax
	testb	$1, %bl
	je	.L35
	movq	$0, (%rdi)
	movl	$1, %eax
	cmpq	$1, %rbx
	je	.L34
	.p2align 5
	.p2align 4
	.p2align 3
.L35:
	movq	%rax, (%rdi,%rax,8)
	leaq	1(%rax), %rdx
	addq	$2, %rax
	movq	%rdx, (%rdi,%rdx,8)
	cmpq	%rax, %rbx
	jne	.L35
.L34:
	testq	%r10, %r10
	jle	.L32
	movq	%r13, 32(%rsp)
	.cfi_offset 13, -16
	movq	0(%rbp), %r8
	xorl	%eax, %eax
	leaq	-1(%rbx), %r11
	movq	24(%rbp), %rcx
	movq	8(%rbp), %r9
	movq	16(%rbp), %rsi
	movsd	.LC2(%rip), %xmm2
	.p2align 4
	.p2align 3
.L37:
	leaq	(%rcx,%r8), %rdx
	pxor	%xmm0, %xmm0
	pxor	%xmm1, %xmm1
	movq	%r9, %r12
	rolq	$17, %rdx
	xorq	%r8, %rsi
	xorq	%r9, %rcx
	salq	$17, %r12
	shrq	$11, %rdx
	xorq	%rsi, %r9
	xorq	%rcx, %r8
	xorq	%r12, %rsi
	cvtsi2sdq	%rdx, %xmm0
	mulsd	%xmm2, %xmm0
	movq	%rbx, %rdx
	rorq	$19, %rcx
	subq	%rax, %rdx
	movq	(%rdi,%rax,8), %r12
	cvtsi2sdq	%rdx, %xmm1
	mulsd	%xmm1, %xmm0
	cvttsd2siq	%xmm0, %rdx
	addq	%rax, %rdx
	cmpq	%rdx, %rbx
	cmovle	%r11, %rdx
	movq	(%rdi,%rdx,8), %r13
	movq	%r13, (%rdi,%rax,8)
	addq	$1, %rax
	movq	%r12, (%rdi,%rdx,8)
	cmpq	%rax, %r10
	jne	.L37
	movq	%r13, -8(%rdi,%r10,8)
	movq	32(%rsp), %r13
	.cfi_restore 13
	movq	%r9, 8(%rbp)
	movq	%r8, 0(%rbp)
	movq	%rsi, 16(%rbp)
	movq	%rcx, 24(%rbp)
	movq	%r12, (%rdi,%rdx,8)
.L32:
	movq	8(%rsp), %rbx
	movq	16(%rsp), %rbp
	movq	%rdi, %rax
	movq	24(%rsp), %r12
	addq	$40, %rsp
	.cfi_def_cfa_offset 8
	ret
	.cfi_endproc
.LFE27:
	.size	cmp_pick_unique, .-cmp_pick_unique
	.section	.rodata.str1.1
.LC4:
	.string	"%-12s  not built / not run\n"
	.section	.rodata.str1.8,"aMS",@progbits,1
	.align 8
.LC6:
	.string	"%-12s  items=%10lld  alloc=%8.3f M/s  %8.2f ns/item  det=%6.2f%%  rep=%6.2f%%  coh_fail=%6.4f%% (%lld/%lld)\n"
	.section	.rodata.str1.1
.LC7:
	.string	""
	.section	.rodata.str1.8
	.align 8
.LC8:
	.string	"%-12s  WARNING: %lld allocation attempts silently rejected (throughput includes fast-fail no-ops)\n"
	.align 8
.LC9:
	.string	"%-12s  cache: L1_hit=%5.2f%%  LLC_hit=%5.2f%%  L1_miss/item=%.4f  LLC_miss/item=%.4f  instr/item=%.1f\n"
	.text
	.p2align 4
	.type	cmp_print_result, @function
cmp_print_result:
.LFB28:
	.cfi_startproc
	movl	112(%rdi), %edx
	testl	%edx, %edx
	je	.L84
	pushq	%rbx
	.cfi_def_cfa_offset 16
	.cfi_offset 3, -16
	movq	64(%rdi), %rdx
	pxor	%xmm2, %xmm2
	movq	72(%rdi), %rax
	testq	%rdx, %rdx
	je	.L51
	pxor	%xmm2, %xmm2
	pxor	%xmm0, %xmm0
	cvtsi2sdq	%rax, %xmm2
	mulsd	.LC5(%rip), %xmm2
	cvtsi2sdq	%rdx, %xmm0
	divsd	%xmm0, %xmm2
.L51:
	pxor	%xmm3, %xmm3
	testq	%rax, %rax
	je	.L52
	pxor	%xmm3, %xmm3
	cvtsi2sdq	80(%rdi), %xmm3
	pxor	%xmm0, %xmm0
	mulsd	.LC5(%rip), %xmm3
	cvtsi2sdq	%rax, %xmm0
	divsd	%xmm0, %xmm3
.L52:
	movq	96(%rdi), %r8
	movq	88(%rdi), %rcx
	pxor	%xmm4, %xmm4
	testq	%r8, %r8
	je	.L53
	pxor	%xmm4, %xmm4
	pxor	%xmm0, %xmm0
	cvtsi2sdq	%rcx, %xmm4
	mulsd	.LC5(%rip), %xmm4
	cvtsi2sdq	%r8, %xmm0
	divsd	%xmm0, %xmm4
.L53:
	movq	32(%rdi), %rdx
	movsd	48(%rdi), %xmm0
	movq	%rdi, %rbx
	movq	%rdi, %rsi
	movsd	56(%rdi), %xmm1
	movl	$5, %eax
	leaq	.LC6(%rip), %rdi
	call	printf@PLT
	movq	104(%rbx), %rdx
	testq	%rdx, %rdx
	jg	.L85
	movl	116(%rbx), %eax
	testl	%eax, %eax
	je	.L49
.L86:
	movq	120(%rbx), %rdx
	movq	128(%rbx), %rax
	pxor	%xmm0, %xmm0
	cmpq	%rdx, %rax
	jnb	.L56
	movq	%rdx, %rcx
	subq	%rax, %rcx
	js	.L57
	pxor	%xmm0, %xmm0
	cvtsi2sdq	%rcx, %xmm0
.L58:
	mulsd	.LC5(%rip), %xmm0
	testq	%rdx, %rdx
	js	.L59
	pxor	%xmm1, %xmm1
	cvtsi2sdq	%rdx, %xmm1
.L60:
	divsd	%xmm1, %xmm0
.L56:
	movq	136(%rbx), %rcx
	movq	144(%rbx), %rdx
	pxor	%xmm1, %xmm1
	cmpq	%rcx, %rdx
	jnb	.L61
	movq	%rcx, %rsi
	subq	%rdx, %rsi
	js	.L62
	pxor	%xmm1, %xmm1
	cvtsi2sdq	%rsi, %xmm1
.L63:
	mulsd	.LC5(%rip), %xmm1
	testq	%rcx, %rcx
	js	.L64
	pxor	%xmm2, %xmm2
	cvtsi2sdq	%rcx, %xmm2
.L65:
	divsd	%xmm2, %xmm1
.L61:
	movq	32(%rbx), %rcx
	testq	%rcx, %rcx
	je	.L78
	pxor	%xmm5, %xmm5
	cvtsi2sdq	%rcx, %xmm5
	movq	152(%rbx), %rcx
	testq	%rcx, %rcx
	js	.L67
	pxor	%xmm4, %xmm4
	cvtsi2sdq	%rcx, %xmm4
.L68:
	divsd	%xmm5, %xmm4
	testq	%rdx, %rdx
	js	.L69
	pxor	%xmm3, %xmm3
	cvtsi2sdq	%rdx, %xmm3
.L70:
	divsd	%xmm5, %xmm3
	testq	%rax, %rax
	js	.L71
	pxor	%xmm2, %xmm2
	cvtsi2sdq	%rax, %xmm2
.L72:
	divsd	%xmm5, %xmm2
	jmp	.L66
	.p2align 4,,10
	.p2align 3
.L49:
	popq	%rbx
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L85:
	.cfi_restore_state
	leaq	.LC7(%rip), %rsi
	leaq	.LC8(%rip), %rdi
	xorl	%eax, %eax
	call	printf@PLT
	movl	116(%rbx), %eax
	testl	%eax, %eax
	je	.L49
	jmp	.L86
	.p2align 4,,10
	.p2align 3
.L84:
	.cfi_def_cfa_offset 8
	.cfi_restore 3
	movq	%rdi, %rsi
	xorl	%eax, %eax
	leaq	.LC4(%rip), %rdi
	jmp	printf@PLT
	.p2align 4,,10
	.p2align 3
.L78:
	.cfi_def_cfa_offset 16
	.cfi_offset 3, -16
	pxor	%xmm3, %xmm3
	movapd	%xmm3, %xmm4
	movapd	%xmm3, %xmm2
.L66:
	movq	%rbx, %rsi
	leaq	.LC9(%rip), %rdi
	movl	$5, %eax
	popq	%rbx
	.cfi_remember_state
	.cfi_restore 3
	.cfi_def_cfa_offset 8
	jmp	printf@PLT
	.p2align 4,,10
	.p2align 3
.L71:
	.cfi_restore_state
	movq	%rax, %rdx
	andl	$1, %eax
	pxor	%xmm2, %xmm2
	shrq	%rdx
	orq	%rax, %rdx
	cvtsi2sdq	%rdx, %xmm2
	addsd	%xmm2, %xmm2
	jmp	.L72
	.p2align 4,,10
	.p2align 3
.L59:
	movq	%rdx, %rcx
	andl	$1, %edx
	pxor	%xmm1, %xmm1
	shrq	%rcx
	orq	%rdx, %rcx
	cvtsi2sdq	%rcx, %xmm1
	addsd	%xmm1, %xmm1
	jmp	.L60
	.p2align 4,,10
	.p2align 3
.L57:
	movq	%rcx, %rsi
	andl	$1, %ecx
	pxor	%xmm0, %xmm0
	shrq	%rsi
	orq	%rcx, %rsi
	cvtsi2sdq	%rsi, %xmm0
	addsd	%xmm0, %xmm0
	jmp	.L58
	.p2align 4,,10
	.p2align 3
.L69:
	movq	%rdx, %rcx
	andl	$1, %edx
	pxor	%xmm3, %xmm3
	shrq	%rcx
	orq	%rdx, %rcx
	cvtsi2sdq	%rcx, %xmm3
	addsd	%xmm3, %xmm3
	jmp	.L70
	.p2align 4,,10
	.p2align 3
.L67:
	movq	%rcx, %rsi
	andl	$1, %ecx
	pxor	%xmm4, %xmm4
	shrq	%rsi
	orq	%rcx, %rsi
	cvtsi2sdq	%rsi, %xmm4
	addsd	%xmm4, %xmm4
	jmp	.L68
	.p2align 4,,10
	.p2align 3
.L64:
	movq	%rcx, %rsi
	andl	$1, %ecx
	pxor	%xmm2, %xmm2
	shrq	%rsi
	orq	%rcx, %rsi
	cvtsi2sdq	%rsi, %xmm2
	addsd	%xmm2, %xmm2
	jmp	.L65
	.p2align 4,,10
	.p2align 3
.L62:
	movq	%rsi, %rdi
	andl	$1, %esi
	pxor	%xmm1, %xmm1
	shrq	%rdi
	orq	%rsi, %rdi
	cvtsi2sdq	%rdi, %xmm1
	addsd	%xmm1, %xmm1
	jmp	.L63
	.cfi_endproc
.LFE28:
	.size	cmp_print_result, .-cmp_print_result
	.p2align 4
	.type	sqb_init, @function
sqb_init:
.LFB29:
	.cfi_startproc
	movl	$86336, %edx
	xorl	%esi, %esi
	jmp	memset@PLT
	.cfi_endproc
.LFE29:
	.size	sqb_init, .-sqb_init
	.p2align 4
	.type	sqb_fill, @function
sqb_fill:
.LFB30:
	.cfi_startproc
	movl	%esi, %edx
	pcmpeqd	%xmm2, %xmm2
	leaq	144(%rdi), %rax
	movq	%rdi, %rcx
	sall	$4, %edx
	movdqa	.LC10(%rip), %xmm1
	psrlw	$8, %xmm2
	addl	%esi, %edx
	movl	$4, %esi
	movd	%esi, %xmm8
	movl	$8, %esi
	movd	%edx, %xmm3
	movd	%esi, %xmm7
	movl	$12, %esi
	punpcklbw	%xmm3, %xmm3
	pshufd	$0, %xmm8, %xmm8
	movd	%esi, %xmm6
	movl	$-1515870811, %esi
	punpcklwd	%xmm3, %xmm3
	pshufd	$0, %xmm7, %xmm7
	movd	%esi, %xmm5
	movl	$16, %esi
	pshufd	$0, %xmm3, %xmm3
	pshufd	$0, %xmm6, %xmm6
	movd	%esi, %xmm4
	pshufd	$0, %xmm5, %xmm5
	pshufd	$0, %xmm4, %xmm4
	.p2align 4
	.p2align 3
.L89:
	movdqa	%xmm1, %xmm10
	movdqa	%xmm1, %xmm9
	movdqa	%xmm1, %xmm0
	addq	$16, %rcx
	paddd	%xmm8, %xmm10
	movdqa	%xmm1, %xmm11
	punpcklwd	%xmm10, %xmm9
	punpckhwd	%xmm10, %xmm0
	paddd	%xmm6, %xmm11
	movdqa	%xmm9, %xmm10
	punpcklwd	%xmm0, %xmm9
	punpckhwd	%xmm0, %xmm10
	movdqa	%xmm1, %xmm0
	paddd	%xmm4, %xmm1
	paddd	%xmm7, %xmm0
	punpcklwd	%xmm10, %xmm9
	movdqa	%xmm0, %xmm10
	punpcklwd	%xmm11, %xmm0
	pand	%xmm2, %xmm9
	punpckhwd	%xmm11, %xmm10
	movdqa	%xmm0, %xmm11
	punpckhwd	%xmm10, %xmm11
	punpcklwd	%xmm10, %xmm0
	punpcklwd	%xmm11, %xmm0
	pand	%xmm2, %xmm0
	packuswb	%xmm0, %xmm9
	movdqa	%xmm9, %xmm0
	paddb	%xmm9, %xmm0
	paddb	%xmm9, %xmm0
	paddb	%xmm0, %xmm0
	paddb	%xmm0, %xmm0
	paddb	%xmm0, %xmm0
	psubb	%xmm9, %xmm0
	paddb	%xmm0, %xmm0
	paddb	%xmm0, %xmm0
	psubb	%xmm9, %xmm0
	paddb	%xmm3, %xmm0
	pxor	%xmm5, %xmm0
	movups	%xmm0, -16(%rcx)
	cmpq	%rax, %rcx
	jne	.L89
	addl	$48, %edx
	leaq	152(%rdi), %rsi
	.p2align 5
	.p2align 4
	.p2align 3
.L90:
	movl	%edx, %ecx
	addq	$1, %rax
	addl	$91, %edx
	xorl	$-91, %ecx
	movb	%cl, -1(%rax)
	cmpq	%rsi, %rax
	jne	.L90
	ret
	.cfi_endproc
.LFE30:
	.size	sqb_fill, .-sqb_fill
	.p2align 4
	.type	sqb_pay_ok, @function
sqb_pay_ok:
.LFB31:
	.cfi_startproc
	movl	%esi, %eax
	leaq	152(%rdi), %rcx
	sall	$4, %eax
	addl	%esi, %eax
	jmp	.L95
	.p2align 5
	.p2align 4,,10
	.p2align 3
.L99:
	addq	$1, %rdi
	addl	$91, %eax
	cmpq	%rcx, %rdi
	je	.L98
.L95:
	movl	%eax, %edx
	xorl	$-91, %edx
	cmpb	%dl, (%rdi)
	je	.L99
	xorl	%eax, %eax
	ret
	.p2align 4,,10
	.p2align 3
.L98:
	movl	$1, %eax
	ret
	.cfi_endproc
.LFE31:
	.size	sqb_pay_ok, .-sqb_pay_ok
	.p2align 4
	.type	sqb_syn, @function
sqb_syn:
.LFB32:
	.cfi_startproc
	movl	$9, %ecx
	movq	%rsi, %r9
	movl	$13, %esi
	movq	%rdx, %r8
	pxor	%xmm6, %xmm6
	movd	%ecx, %xmm12
	movq	%rdi, %rax
	movl	$5, %ecx
	movd	%esi, %xmm11
	pcmpeqd	%xmm10, %xmm10
	movl	$16, %esi
	movdqa	.LC10(%rip), %xmm5
	movd	%ecx, %xmm9
	movd	%esi, %xmm8
	leaq	144(%rdi), %rdx
	pshufd	$0, %xmm12, %xmm12
	movdqa	%xmm6, %xmm4
	movdqa	%xmm6, %xmm3
	movdqa	%xmm6, %xmm7
	pshufd	$0, %xmm11, %xmm11
	psrld	$31, %xmm10
	pshufd	$0, %xmm9, %xmm9
	pshufd	$0, %xmm8, %xmm8
	.p2align 4
	.p2align 3
.L101:
	movdqu	(%rax), %xmm0
	addq	$16, %rax
	movdqa	%xmm0, %xmm2
	punpckhbw	%xmm7, %xmm0
	punpcklbw	%xmm7, %xmm2
	movdqa	%xmm0, %xmm15
	punpckhwd	%xmm6, %xmm0
	movdqa	%xmm2, %xmm14
	punpckhwd	%xmm6, %xmm2
	punpcklwd	%xmm6, %xmm15
	punpcklwd	%xmm6, %xmm14
	movdqa	%xmm0, %xmm1
	movdqa	%xmm2, %xmm13
	paddd	%xmm14, %xmm13
	paddd	%xmm15, %xmm1
	paddd	%xmm13, %xmm1
	paddd	%xmm1, %xmm4
	movdqa	%xmm5, %xmm1
	paddd	%xmm12, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm15, %xmm13
	psrlq	$32, %xmm15
	pmuludq	%xmm15, %xmm1
	movdqa	%xmm5, %xmm15
	paddd	%xmm11, %xmm15
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	movdqa	%xmm15, %xmm1
	pmuludq	%xmm0, %xmm1
	psrlq	$32, %xmm15
	psrlq	$32, %xmm0
	pmuludq	%xmm15, %xmm0
	pshufd	$8, %xmm1, %xmm1
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm1
	movdqa	%xmm13, %xmm0
	paddd	%xmm1, %xmm0
	movdqa	%xmm5, %xmm1
	paddd	%xmm10, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm14, %xmm13
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm1
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	movdqa	%xmm5, %xmm1
	paddd	%xmm8, %xmm5
	paddd	%xmm9, %xmm1
	movdqa	%xmm1, %xmm14
	psrlq	$32, %xmm1
	pmuludq	%xmm2, %xmm14
	psrlq	$32, %xmm2
	pmuludq	%xmm2, %xmm1
	pshufd	$8, %xmm14, %xmm14
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm14
	paddd	%xmm14, %xmm13
	paddd	%xmm13, %xmm0
	paddd	%xmm0, %xmm3
	cmpq	%rdx, %rax
	jne	.L101
	movdqa	%xmm4, %xmm0
	movl	$145, %eax
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
.L102:
	movzbl	-1(%rdi,%rax), %edx
	addl	%edx, %esi
	imull	%eax, %edx
	addq	$1, %rax
	addl	%edx, %ecx
	cmpq	$153, %rax
	jne	.L102
	movl	%esi, (%r9)
	movl	%ecx, (%r8)
	ret
	.cfi_endproc
.LFE32:
	.size	sqb_syn, .-sqb_syn
	.p2align 4
	.type	sqb_strand_ok, @function
sqb_strand_ok:
.LFB33:
	.cfi_startproc
	movl	$16, %eax
	subq	$168, %rsp
	.cfi_def_cfa_offset 176
	pcmpeqd	%xmm9, %xmm9
	movq	%fs:40, %r8
	movq	%r8, 152(%rsp)
	movq	%rdi, %r8
	movd	%eax, %xmm7
	movl	$5, %eax
	pxor	%xmm3, %xmm3
	movd	%eax, %xmm8
	movl	$13, %eax
	pshufd	$0, %xmm7, %xmm7
	movd	%eax, %xmm10
	movl	$9, %eax
	pshufd	$0, %xmm8, %xmm8
	movd	%eax, %xmm11
	pshufd	$0, %xmm10, %xmm10
	pshufd	$0, %xmm11, %xmm11
	testl	%esi, %esi
	jne	.L106
	movdqa	%xmm3, %xmm0
	movdqa	%xmm3, %xmm1
	movdqa	%xmm3, %xmm12
	movq	%r8, %rax
	movdqa	.LC10(%rip), %xmm6
	leaq	144(%r8), %rdx
	psrld	$31, %xmm9
	.p2align 4
	.p2align 3
.L107:
	movdqu	(%rax), %xmm2
	addq	$16, %rax
	movdqa	%xmm2, %xmm5
	punpckhbw	%xmm12, %xmm2
	punpcklbw	%xmm12, %xmm5
	movdqa	%xmm2, %xmm15
	punpckhwd	%xmm3, %xmm2
	movdqa	%xmm5, %xmm14
	punpckhwd	%xmm3, %xmm5
	punpcklwd	%xmm3, %xmm15
	punpcklwd	%xmm3, %xmm14
	movdqa	%xmm2, %xmm4
	movdqa	%xmm5, %xmm13
	paddd	%xmm14, %xmm13
	paddd	%xmm15, %xmm4
	paddd	%xmm13, %xmm4
	paddd	%xmm4, %xmm0
	movdqa	%xmm6, %xmm4
	paddd	%xmm11, %xmm4
	movdqa	%xmm4, %xmm13
	psrlq	$32, %xmm4
	pmuludq	%xmm15, %xmm13
	psrlq	$32, %xmm15
	pmuludq	%xmm15, %xmm4
	movdqa	%xmm6, %xmm15
	paddd	%xmm10, %xmm15
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm4, %xmm4
	punpckldq	%xmm4, %xmm13
	movdqa	%xmm15, %xmm4
	pmuludq	%xmm2, %xmm4
	psrlq	$32, %xmm15
	psrlq	$32, %xmm2
	pmuludq	%xmm15, %xmm2
	pshufd	$8, %xmm4, %xmm4
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm4
	movdqa	%xmm13, %xmm2
	paddd	%xmm4, %xmm2
	movdqa	%xmm6, %xmm4
	paddd	%xmm9, %xmm4
	movdqa	%xmm4, %xmm13
	psrlq	$32, %xmm4
	pmuludq	%xmm14, %xmm13
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm4
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm4, %xmm4
	punpckldq	%xmm4, %xmm13
	movdqa	%xmm6, %xmm4
	paddd	%xmm7, %xmm6
	paddd	%xmm8, %xmm4
	movdqa	%xmm4, %xmm14
	psrlq	$32, %xmm4
	pmuludq	%xmm5, %xmm14
	psrlq	$32, %xmm5
	pmuludq	%xmm5, %xmm4
	pshufd	$8, %xmm14, %xmm14
	pshufd	$8, %xmm4, %xmm4
	punpckldq	%xmm4, %xmm14
	paddd	%xmm14, %xmm13
	paddd	%xmm13, %xmm2
	paddd	%xmm2, %xmm1
	cmpq	%rdx, %rax
	jne	.L107
	movdqa	%xmm0, %xmm2
	movl	$145, %ecx
	psrldq	$8, %xmm2
	paddd	%xmm2, %xmm0
	movdqa	%xmm0, %xmm2
	psrldq	$4, %xmm2
	paddd	%xmm2, %xmm0
	movd	%xmm0, %eax
	movdqa	%xmm1, %xmm0
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm1
	movdqa	%xmm1, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm1
	movd	%xmm1, %edx
	.p2align 5
	.p2align 4
	.p2align 3
.L108:
	movzbl	-1(%r8,%rcx), %esi
	addl	%esi, %eax
	imull	%ecx, %esi
	addq	$1, %rcx
	addl	%esi, %edx
	cmpq	$153, %rcx
	jne	.L108
.L109:
	xorl	%ecx, %ecx
	cmpl	%eax, 152(%r8)
	jne	.L105
	xorl	%ecx, %ecx
	cmpl	%edx, 156(%r8)
	sete	%cl
.L105:
	movq	152(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L124
	movl	%ecx, %eax
	addq	$168, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
.L106:
	.cfi_restore_state
	movl	$1431655765, %esi
	movq	%rsp, %rdi
	movq	%rsp, %rcx
	movq	%r8, %rdx
	movd	%esi, %xmm1
	leaq	144(%r8), %rax
	pshufd	$0, %xmm1, %xmm1
	.p2align 5
	.p2align 4
	.p2align 3
.L110:
	movdqu	(%rdx), %xmm0
	addq	$16, %rdx
	addq	$16, %rcx
	pxor	%xmm1, %xmm0
	movaps	%xmm0, -16(%rcx)
	cmpq	%rax, %rdx
	jne	.L110
	leaq	144(%rdi), %r9
	leaq	152(%r8), %rsi
	movq	%r9, %rcx
	.p2align 5
	.p2align 4
	.p2align 3
.L111:
	movzbl	(%rax), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, -1(%rcx)
	cmpq	%rax, %rsi
	jne	.L111
	movdqa	%xmm3, %xmm0
	movdqa	%xmm3, %xmm1
	movdqa	%xmm3, %xmm12
	movq	%rdi, %rax
	movdqa	.LC10(%rip), %xmm6
	psrld	$31, %xmm9
	.p2align 4
	.p2align 3
.L112:
	movdqa	(%rax), %xmm2
	addq	$16, %rax
	movdqa	%xmm2, %xmm5
	punpckhbw	%xmm12, %xmm2
	punpcklbw	%xmm12, %xmm5
	movdqa	%xmm2, %xmm15
	punpckhwd	%xmm3, %xmm2
	movdqa	%xmm5, %xmm14
	punpckhwd	%xmm3, %xmm5
	punpcklwd	%xmm3, %xmm15
	punpcklwd	%xmm3, %xmm14
	movdqa	%xmm5, %xmm4
	movdqa	%xmm2, %xmm13
	paddd	%xmm15, %xmm13
	paddd	%xmm14, %xmm4
	paddd	%xmm13, %xmm4
	paddd	%xmm4, %xmm0
	movdqa	%xmm6, %xmm4
	paddd	%xmm11, %xmm4
	movdqa	%xmm4, %xmm13
	psrlq	$32, %xmm4
	pmuludq	%xmm15, %xmm13
	psrlq	$32, %xmm15
	pmuludq	%xmm15, %xmm4
	movdqa	%xmm6, %xmm15
	paddd	%xmm10, %xmm15
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm4, %xmm4
	punpckldq	%xmm4, %xmm13
	movdqa	%xmm15, %xmm4
	pmuludq	%xmm2, %xmm4
	psrlq	$32, %xmm15
	psrlq	$32, %xmm2
	pmuludq	%xmm15, %xmm2
	pshufd	$8, %xmm4, %xmm4
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm4
	movdqa	%xmm13, %xmm2
	paddd	%xmm4, %xmm2
	movdqa	%xmm6, %xmm4
	paddd	%xmm9, %xmm4
	movdqa	%xmm4, %xmm13
	psrlq	$32, %xmm4
	pmuludq	%xmm14, %xmm13
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm4
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm4, %xmm4
	punpckldq	%xmm4, %xmm13
	movdqa	%xmm6, %xmm4
	paddd	%xmm7, %xmm6
	paddd	%xmm8, %xmm4
	movdqa	%xmm4, %xmm14
	psrlq	$32, %xmm4
	pmuludq	%xmm5, %xmm14
	psrlq	$32, %xmm5
	pmuludq	%xmm5, %xmm4
	pshufd	$8, %xmm14, %xmm14
	pshufd	$8, %xmm4, %xmm4
	punpckldq	%xmm4, %xmm14
	paddd	%xmm14, %xmm13
	paddd	%xmm13, %xmm2
	paddd	%xmm2, %xmm1
	cmpq	%r9, %rax
	jne	.L112
	movdqa	%xmm0, %xmm2
	movl	$144, %esi
	psrldq	$8, %xmm2
	paddd	%xmm2, %xmm0
	movdqa	%xmm0, %xmm2
	psrldq	$4, %xmm2
	paddd	%xmm2, %xmm0
	movd	%xmm0, %eax
	movdqa	%xmm1, %xmm0
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm1
	movdqa	%xmm1, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm1
	movd	%xmm1, %edx
	.p2align 5
	.p2align 4
	.p2align 3
.L113:
	movzbl	144(%rdi), %ecx
	addl	$1, %esi
	addq	$1, %rdi
	addl	%ecx, %eax
	imull	%esi, %ecx
	addl	%ecx, %edx
	cmpl	$152, %esi
	jne	.L113
	jmp	.L109
.L124:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE33:
	.size	sqb_strand_ok, .-sqb_strand_ok
	.p2align 4
	.type	sqb_duplex_mismatch, @function
sqb_duplex_mismatch:
.LFB34:
	.cfi_startproc
	movq	%rsi, %r8
	movq	%rdi, %r9
	movq	%rdx, %rsi
	xorl	%eax, %eax
	xorl	%ecx, %ecx
	.p2align 6
	.p2align 4
	.p2align 3
.L127:
	movzbl	(%r9,%rax), %edx
	xorb	(%r8,%rax), %dl
	cmpb	$85, %dl
	setne	%dl
	setne	%dil
	movzbl	%dl, %edx
	testq	%rsi, %rsi
	je	.L126
	movb	%dil, (%rsi,%rax)
.L126:
	addq	$1, %rax
	addl	%edx, %ecx
	cmpq	$152, %rax
	jne	.L127
	movl	%ecx, %eax
	ret
	.cfi_endproc
.LFE34:
	.size	sqb_duplex_mismatch, .-sqb_duplex_mismatch
	.p2align 4
	.type	sqb_strand_write, @function
sqb_strand_write:
.LFB35:
	.cfi_startproc
	xorl	%eax, %eax
	testl	%edx, %edx
	je	.L142
	.p2align 5
	.p2align 4
	.p2align 3
.L133:
	movzbl	(%rsi,%rax), %edx
	xorl	$85, %edx
	movb	%dl, (%rdi,%rax)
	addq	$1, %rax
	cmpq	$152, %rax
	jne	.L133
.L134:
	movl	$9, %ecx
	pxor	%xmm6, %xmm6
	pcmpeqd	%xmm10, %xmm10
	movdqa	.LC10(%rip), %xmm5
	movd	%ecx, %xmm12
	movdqa	%xmm6, %xmm4
	movdqa	%xmm6, %xmm3
	movq	%rsi, %rax
	movl	$13, %ecx
	movdqa	%xmm6, %xmm7
	leaq	144(%rsi), %rdx
	pshufd	$0, %xmm12, %xmm12
	movd	%ecx, %xmm11
	psrld	$31, %xmm10
	movl	$5, %ecx
	movd	%ecx, %xmm9
	movl	$16, %ecx
	pshufd	$0, %xmm11, %xmm11
	movd	%ecx, %xmm8
	pshufd	$0, %xmm9, %xmm9
	pshufd	$0, %xmm8, %xmm8
	.p2align 4
	.p2align 3
.L135:
	movdqu	(%rax), %xmm0
	addq	$16, %rax
	movdqa	%xmm0, %xmm2
	punpckhbw	%xmm7, %xmm0
	punpcklbw	%xmm7, %xmm2
	movdqa	%xmm0, %xmm15
	punpckhwd	%xmm6, %xmm0
	movdqa	%xmm2, %xmm14
	punpckhwd	%xmm6, %xmm2
	punpcklwd	%xmm6, %xmm15
	punpcklwd	%xmm6, %xmm14
	movdqa	%xmm0, %xmm1
	movdqa	%xmm2, %xmm13
	paddd	%xmm14, %xmm13
	paddd	%xmm15, %xmm1
	paddd	%xmm13, %xmm1
	paddd	%xmm1, %xmm4
	movdqa	%xmm5, %xmm1
	paddd	%xmm12, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm15, %xmm13
	psrlq	$32, %xmm15
	pmuludq	%xmm15, %xmm1
	movdqa	%xmm5, %xmm15
	paddd	%xmm11, %xmm15
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	movdqa	%xmm15, %xmm1
	pmuludq	%xmm0, %xmm1
	psrlq	$32, %xmm15
	psrlq	$32, %xmm0
	pmuludq	%xmm15, %xmm0
	pshufd	$8, %xmm1, %xmm1
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm1
	movdqa	%xmm13, %xmm0
	paddd	%xmm1, %xmm0
	movdqa	%xmm5, %xmm1
	paddd	%xmm10, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm14, %xmm13
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm1
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	movdqa	%xmm5, %xmm1
	paddd	%xmm8, %xmm5
	paddd	%xmm9, %xmm1
	movdqa	%xmm1, %xmm14
	psrlq	$32, %xmm1
	pmuludq	%xmm2, %xmm14
	psrlq	$32, %xmm2
	pmuludq	%xmm2, %xmm1
	pshufd	$8, %xmm14, %xmm14
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm14
	paddd	%xmm14, %xmm13
	paddd	%xmm13, %xmm0
	paddd	%xmm0, %xmm3
	cmpq	%rdx, %rax
	jne	.L135
	movdqa	%xmm4, %xmm0
	movl	$145, %eax
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm4
	movdqa	%xmm4, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm4
	movdqa	%xmm3, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm4, %r8d
	paddd	%xmm0, %xmm3
	movdqa	%xmm3, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm3
	movd	%xmm3, %ecx
	.p2align 5
	.p2align 4
	.p2align 3
.L136:
	movzbl	-1(%rsi,%rax), %edx
	addl	%edx, %r8d
	imull	%eax, %edx
	addq	$1, %rax
	addl	%edx, %ecx
	cmpq	$153, %rax
	jne	.L136
	movl	%r8d, 152(%rdi)
	movl	%ecx, 156(%rdi)
	movq	$0, 160(%rdi)
	ret
.L142:
	movdqu	(%rsi), %xmm0
	movups	%xmm0, (%rdi)
	movdqu	16(%rsi), %xmm0
	movups	%xmm0, 16(%rdi)
	movdqu	32(%rsi), %xmm0
	movups	%xmm0, 32(%rdi)
	movdqu	48(%rsi), %xmm0
	movups	%xmm0, 48(%rdi)
	movdqu	64(%rsi), %xmm0
	movups	%xmm0, 64(%rdi)
	movdqu	80(%rsi), %xmm0
	movups	%xmm0, 80(%rdi)
	movdqu	96(%rsi), %xmm0
	movups	%xmm0, 96(%rdi)
	movdqu	112(%rsi), %xmm0
	movups	%xmm0, 112(%rdi)
	movdqu	128(%rsi), %xmm0
	movups	%xmm0, 128(%rdi)
	movq	144(%rsi), %rax
	movq	%rax, 144(%rdi)
	jmp	.L134
	.cfi_endproc
.LFE35:
	.size	sqb_strand_write, .-sqb_strand_write
	.p2align 4
	.type	sqb_excise, @function
sqb_excise:
.LFB36:
	.cfi_startproc
	subq	$168, %rsp
	.cfi_def_cfa_offset 176
	movq	%fs:40, %rax
	movq	%rax, 152(%rsp)
	xorl	%eax, %eax
	cmpq	%rdi, %rsi
	je	.L143
	movl	$1431655765, %eax
	movq	%rdi, %r8
	movl	%edx, %r9d
	movd	%eax, %xmm1
	pshufd	$0, %xmm1, %xmm1
	cmpl	$1, %edx
	je	.L165
	movq	%rsp, %rdi
	leaq	144(%rsi), %rax
	movq	%rsp, %rcx
	movq	%rsi, %rdx
	movdqa	%xmm1, %xmm2
	.p2align 5
	.p2align 4
	.p2align 3
.L147:
	movdqu	(%rdx), %xmm0
	addq	$16, %rdx
	addq	$16, %rcx
	pxor	%xmm2, %xmm0
	movaps	%xmm0, -16(%rcx)
	cmpq	%rax, %rdx
	jne	.L147
	leaq	144(%rdi), %rcx
	addq	$152, %rsi
	.p2align 5
	.p2align 4
	.p2align 3
.L148:
	movzbl	(%rax), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, -1(%rcx)
	cmpq	%rsi, %rax
	jne	.L148
	testl	%r9d, %r9d
	je	.L149
.L146:
	movq	%rdi, %rax
	movq	%r8, %rdx
	leaq	144(%r8), %rcx
	movq	%rdi, %rsi
	.p2align 5
	.p2align 4
	.p2align 3
.L150:
	movdqa	(%rsi), %xmm0
	addq	$16, %rdx
	addq	$16, %rsi
	pxor	%xmm1, %xmm0
	movups	%xmm0, -16(%rdx)
	cmpq	%rcx, %rdx
	jne	.L150
	leaq	8(%rdi), %rsi
	.p2align 5
	.p2align 4
	.p2align 3
.L152:
	movzbl	144(%rax), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, -1(%rcx)
	cmpq	%rsi, %rax
	jne	.L152
.L151:
	movl	$9, %esi
	pxor	%xmm6, %xmm6
	pcmpeqd	%xmm10, %xmm10
	movdqa	.LC10(%rip), %xmm5
	movd	%esi, %xmm12
	movdqa	%xmm6, %xmm4
	movdqa	%xmm6, %xmm3
	movq	%rdi, %rax
	movl	$13, %esi
	movdqa	%xmm6, %xmm7
	leaq	144(%rsp), %rdx
	pshufd	$0, %xmm12, %xmm12
	movd	%esi, %xmm11
	psrld	$31, %xmm10
	movl	$5, %esi
	movd	%esi, %xmm9
	movl	$16, %esi
	pshufd	$0, %xmm11, %xmm11
	movd	%esi, %xmm8
	pshufd	$0, %xmm9, %xmm9
	pshufd	$0, %xmm8, %xmm8
	.p2align 4
	.p2align 3
.L154:
	movdqa	(%rax), %xmm0
	addq	$16, %rax
	movdqa	%xmm0, %xmm2
	punpckhbw	%xmm7, %xmm0
	punpcklbw	%xmm7, %xmm2
	movdqa	%xmm0, %xmm15
	punpckhwd	%xmm6, %xmm0
	movdqa	%xmm2, %xmm14
	punpckhwd	%xmm6, %xmm2
	punpcklwd	%xmm6, %xmm15
	punpcklwd	%xmm6, %xmm14
	movdqa	%xmm0, %xmm1
	movdqa	%xmm2, %xmm13
	paddd	%xmm14, %xmm13
	paddd	%xmm15, %xmm1
	paddd	%xmm13, %xmm1
	paddd	%xmm1, %xmm4
	movdqa	%xmm5, %xmm1
	paddd	%xmm12, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm15, %xmm13
	psrlq	$32, %xmm15
	pmuludq	%xmm15, %xmm1
	movdqa	%xmm5, %xmm15
	paddd	%xmm11, %xmm15
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	movdqa	%xmm15, %xmm1
	pmuludq	%xmm0, %xmm1
	psrlq	$32, %xmm15
	psrlq	$32, %xmm0
	pmuludq	%xmm15, %xmm0
	pshufd	$8, %xmm1, %xmm1
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm1
	movdqa	%xmm13, %xmm0
	paddd	%xmm1, %xmm0
	movdqa	%xmm5, %xmm1
	paddd	%xmm10, %xmm1
	movdqa	%xmm1, %xmm13
	psrlq	$32, %xmm1
	pmuludq	%xmm14, %xmm13
	psrlq	$32, %xmm14
	pmuludq	%xmm14, %xmm1
	pshufd	$8, %xmm13, %xmm13
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm13
	movdqa	%xmm5, %xmm1
	paddd	%xmm8, %xmm5
	paddd	%xmm9, %xmm1
	movdqa	%xmm1, %xmm14
	psrlq	$32, %xmm1
	pmuludq	%xmm2, %xmm14
	psrlq	$32, %xmm2
	pmuludq	%xmm2, %xmm1
	pshufd	$8, %xmm14, %xmm14
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm14
	paddd	%xmm14, %xmm13
	paddd	%xmm13, %xmm0
	paddd	%xmm0, %xmm3
	cmpq	%rdx, %rax
	jne	.L154
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
.L155:
	movzbl	144(%rdi), %eax
	addl	$1, %edx
	addq	$1, %rdi
	addl	%eax, %esi
	imull	%edx, %eax
	addl	%eax, %ecx
	cmpl	$152, %edx
	jne	.L155
	movl	%esi, 152(%r8)
	movl	%ecx, 156(%r8)
	movl	$0, 164(%r8)
.L143:
	movq	152(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L166
	addq	$168, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
.L149:
	.cfi_restore_state
	movdqa	(%rsp), %xmm0
	movq	144(%rsp), %rax
	movups	%xmm0, (%r8)
	movdqa	16(%rsp), %xmm0
	movq	%rax, 144(%r8)
	movups	%xmm0, 16(%r8)
	movdqa	32(%rsp), %xmm0
	movups	%xmm0, 32(%r8)
	movdqa	48(%rsp), %xmm0
	movups	%xmm0, 48(%r8)
	movdqa	64(%rsp), %xmm0
	movups	%xmm0, 64(%r8)
	movdqa	80(%rsp), %xmm0
	movups	%xmm0, 80(%r8)
	movdqa	96(%rsp), %xmm0
	movups	%xmm0, 96(%r8)
	movdqa	112(%rsp), %xmm0
	movups	%xmm0, 112(%r8)
	movdqa	128(%rsp), %xmm0
	movups	%xmm0, 128(%r8)
	jmp	.L151
.L165:
	movdqu	(%rsi), %xmm0
	movq	144(%rsi), %rax
	movq	%rsp, %rdi
	movaps	%xmm0, (%rsp)
	movdqu	16(%rsi), %xmm0
	movq	%rax, 144(%rsp)
	movaps	%xmm0, 16(%rsp)
	movdqu	32(%rsi), %xmm0
	movaps	%xmm0, 32(%rsp)
	movdqu	48(%rsi), %xmm0
	movaps	%xmm0, 48(%rsp)
	movdqu	64(%rsi), %xmm0
	movaps	%xmm0, 64(%rsp)
	movdqu	80(%rsi), %xmm0
	movaps	%xmm0, 80(%rsp)
	movdqu	96(%rsi), %xmm0
	movaps	%xmm0, 96(%rsp)
	movdqu	112(%rsi), %xmm0
	movaps	%xmm0, 112(%rsp)
	movdqu	128(%rsi), %xmm0
	movaps	%xmm0, 128(%rsp)
	jmp	.L146
.L166:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE36:
	.size	sqb_excise, .-sqb_excise
	.p2align 4
	.type	sqb_proofread_commit, @function
sqb_proofread_commit:
.LFB37:
	.cfi_startproc
	pushq	%r15
	.cfi_def_cfa_offset 16
	.cfi_offset 15, -16
	movl	$16, %eax
	pcmpeqd	%xmm1, %xmm1
	pxor	%xmm14, %xmm14
	pushq	%r14
	.cfi_def_cfa_offset 24
	.cfi_offset 14, -24
	movd	%eax, %xmm7
	movl	$5, %eax
	pcmpeqd	%xmm10, %xmm10
	pushq	%r13
	.cfi_def_cfa_offset 32
	.cfi_offset 13, -32
	movd	%eax, %xmm6
	movl	$13, %eax
	pshufd	$0, %xmm7, %xmm7
	pushq	%r12
	.cfi_def_cfa_offset 40
	.cfi_offset 12, -40
	movq	%rdi, %r12
	movl	%esi, %edi
	movl	%ecx, %esi
	pushq	%rbp
	.cfi_def_cfa_offset 48
	.cfi_offset 6, -48
	sall	$4, %esi
	movl	$-1515870811, %r8d
	pshufd	$0, %xmm6, %xmm5
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	addl	%ecx, %esi
	movl	$4, %ebx
	movd	%r8d, %xmm4
	movd	%esi, %xmm11
	movd	%ebx, %xmm15
	movl	$8, %ebx
	pshufd	$0, %xmm4, %xmm4
	punpcklbw	%xmm11, %xmm11
	psrld	$31, %xmm1
	movd	%ebx, %xmm13
	movl	$12, %ebx
	punpcklwd	%xmm11, %xmm11
	subq	$440, %rsp
	.cfi_def_cfa_offset 496
	movdqa	.LC10(%rip), %xmm3
	movd	%ebx, %xmm12
	movaps	%xmm7, 64(%rsp)
	movd	%eax, %xmm7
	movl	$9, %eax
	pshufd	$0, %xmm11, %xmm11
	movd	%eax, %xmm6
	pshufd	$0, %xmm7, %xmm2
	leaq	272(%rsp), %rax
	movdqa	%xmm14, %xmm7
	movq	%fs:40, %r11
	movq	%r11, 424(%rsp)
	movl	%edx, %r11d
	pshufd	$0, %xmm6, %xmm0
	psrlw	$8, %xmm10
	leaq	416(%rsp), %rdx
	movdqa	%xmm14, %xmm6
	movaps	%xmm4, (%rsp)
	pshufd	$0, %xmm15, %xmm15
	pshufd	$0, %xmm13, %xmm13
	movaps	%xmm1, 16(%rsp)
	pshufd	$0, %xmm12, %xmm12
	movaps	%xmm0, 32(%rsp)
	movaps	%xmm2, 48(%rsp)
	movaps	%xmm5, 80(%rsp)
	.p2align 4
	.p2align 3
.L168:
	movdqa	%xmm3, %xmm2
	movdqa	%xmm3, %xmm1
	movdqa	%xmm3, %xmm0
	addq	$16, %rax
	paddd	%xmm15, %xmm2
	movdqa	%xmm3, %xmm4
	punpcklwd	%xmm2, %xmm1
	punpckhwd	%xmm2, %xmm0
	paddd	%xmm12, %xmm4
	movdqa	%xmm1, %xmm2
	punpcklwd	%xmm0, %xmm1
	punpckhwd	%xmm0, %xmm2
	movdqa	%xmm3, %xmm0
	paddd	%xmm13, %xmm0
	punpcklwd	%xmm2, %xmm1
	movdqa	%xmm0, %xmm2
	punpcklwd	%xmm4, %xmm0
	pand	%xmm10, %xmm1
	punpckhwd	%xmm4, %xmm2
	movdqa	%xmm0, %xmm4
	punpckhwd	%xmm2, %xmm4
	punpcklwd	%xmm2, %xmm0
	punpcklwd	%xmm4, %xmm0
	pand	%xmm10, %xmm0
	packuswb	%xmm0, %xmm1
	movdqa	%xmm1, %xmm0
	paddb	%xmm1, %xmm0
	paddb	%xmm1, %xmm0
	paddb	%xmm0, %xmm0
	paddb	%xmm0, %xmm0
	paddb	%xmm0, %xmm0
	psubb	%xmm1, %xmm0
	paddb	%xmm0, %xmm0
	paddb	%xmm0, %xmm0
	psubb	%xmm1, %xmm0
	paddb	%xmm11, %xmm0
	pxor	(%rsp), %xmm0
	movdqa	%xmm0, %xmm1
	movdqa	%xmm0, %xmm2
	movaps	%xmm0, -16(%rax)
	punpcklbw	%xmm14, %xmm1
	punpckhbw	%xmm14, %xmm2
	movdqa	%xmm1, %xmm5
	movdqa	%xmm2, %xmm4
	punpckhwd	%xmm14, %xmm1
	punpckhwd	%xmm14, %xmm2
	punpcklwd	%xmm14, %xmm5
	punpcklwd	%xmm14, %xmm4
	movdqa	%xmm1, %xmm8
	movdqa	%xmm2, %xmm9
	paddd	%xmm4, %xmm9
	paddd	%xmm5, %xmm8
	paddd	%xmm9, %xmm8
	movdqa	.LC18(%rip), %xmm9
	paddd	%xmm8, %xmm6
	paddd	%xmm3, %xmm9
	movdqa	%xmm9, %xmm8
	psrlq	$32, %xmm9
	pmuludq	%xmm4, %xmm8
	psrlq	$32, %xmm4
	pmuludq	%xmm9, %xmm4
	movdqa	.LC19(%rip), %xmm9
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
	movdqa	16(%rsp), %xmm8
	paddd	%xmm3, %xmm8
	movdqa	%xmm8, %xmm2
	psrlq	$32, %xmm8
	pmuludq	%xmm5, %xmm2
	psrlq	$32, %xmm5
	pmuludq	%xmm8, %xmm5
	movdqa	.LC21(%rip), %xmm8
	paddd	%xmm3, %xmm8
	paddd	.LC16(%rip), %xmm3
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
	jne	.L168
	movdqa	%xmm6, %xmm1
	movdqa	32(%rsp), %xmm0
	movdqa	48(%rsp), %xmm2
	addl	$48, %esi
	psrldq	$8, %xmm1
	movdqa	80(%rsp), %xmm5
	movl	$144, %edx
	leaq	272(%rsp), %r8
	paddd	%xmm1, %xmm6
	movdqa	%xmm6, %xmm1
	psrldq	$4, %xmm1
	paddd	%xmm1, %xmm6
	movdqa	%xmm7, %xmm1
	psrldq	$8, %xmm1
	movd	%xmm6, %r9d
	paddd	%xmm1, %xmm7
	movdqa	%xmm7, %xmm1
	psrldq	$4, %xmm1
	paddd	%xmm1, %xmm7
	movd	%xmm7, %r10d
	.p2align 6
	.p2align 4
	.p2align 3
.L169:
	movl	%esi, %eax
	addl	$1, %edx
	addl	$91, %esi
	addq	$1, %r8
	xorl	$-91, %eax
	movb	%al, 143(%r8)
	movzbl	%al, %eax
	addl	%eax, %r9d
	imull	%edx, %eax
	addl	%eax, %r10d
	cmpl	$152, %edx
	jne	.L169
	movslq	%r11d, %rax
	movslq	%edi, %rdx
	movdqa	%xmm0, %xmm15
	movaps	%xmm5, 32(%rsp)
	imulq	$336, %rax, %r8
	pcmpeqd	%xmm0, %xmm0
	movdqa	%xmm14, %xmm5
	movdqa	352(%rsp), %xmm7
	imulq	$10752, %rdx, %rsi
	psrld	$31, %xmm0
	movdqa	288(%rsp), %xmm3
	movdqa	304(%rsp), %xmm6
	movaps	%xmm7, 224(%rsp)
	movdqa	%xmm14, %xmm4
	movdqa	368(%rsp), %xmm7
	movdqa	400(%rsp), %xmm12
	movaps	%xmm0, 16(%rsp)
	pcmpeqd	%xmm0, %xmm0
	movdqa	320(%rsp), %xmm8
	movdqa	336(%rsp), %xmm9
	leaq	312(%r8,%rsi), %rdi
	psubb	%xmm0, %xmm5
	movaps	%xmm7, 192(%rsp)
	movdqa	384(%rsp), %xmm7
	addq	%r12, %rdi
	leaq	168(%r8,%rsi), %r15
	movl	$2, 264(%rsp)
	movdqa	272(%rsp), %xmm10
	movq	%rdi, 240(%rsp)
	leaq	(%r8,%rsi), %rdi
	addq	%r12, %r15
	movdqa	%xmm3, %xmm0
	leaq	144(%r8,%rsi), %rsi
	leaq	(%r12,%rdi), %rbx
	movq	%rdx, 256(%rsp)
	movq	416(%rsp), %r11
	leaq	168(%r12,%rdi), %r13
	leaq	(%r12,%rsi), %rdi
	movl	%ecx, 268(%rsp)
	movdqa	%xmm6, %xmm3
	movq	%rdi, 184(%rsp)
	movl	$1431655765, %edi
	leaq	144(%r15), %r14
	leaq	280(%rsp), %rbp
	movq	%r15, 248(%rsp)
	movd	%edi, %xmm13
	movq	%rax, %r15
	movaps	%xmm7, 208(%rsp)
	movdqa	%xmm14, %xmm7
	pshufd	$0, %xmm13, %xmm13
	movaps	%xmm2, (%rsp)
	movdqa	%xmm12, %xmm2
	movaps	%xmm5, 48(%rsp)
.L176:
	movdqa	224(%rsp), %xmm6
	movq	248(%rsp), %rax
	movq	%r11, 144(%rbx)
	leaq	272(%rsp), %rdx
	movups	%xmm10, (%rbx)
	movups	%xmm6, 80(%rbx)
	movdqa	192(%rsp), %xmm6
	movups	%xmm0, 16(%rbx)
	movups	%xmm6, 96(%rbx)
	movdqa	208(%rsp), %xmm6
	movups	%xmm3, 32(%rbx)
	movups	%xmm8, 48(%rbx)
	movups	%xmm9, 64(%rbx)
	movups	%xmm6, 112(%rbx)
	movups	%xmm2, 128(%rbx)
	.p2align 5
	.p2align 4
	.p2align 3
.L170:
	movdqa	(%rdx), %xmm1
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm13, %xmm1
	movups	%xmm1, -16(%rax)
	cmpq	%r14, %rax
	jne	.L170
	movq	240(%rsp), %rcx
	leaq	272(%rsp), %rax
	.p2align 5
	.p2align 4
	.p2align 3
.L171:
	movzbl	144(%rax), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, -1(%rcx)
	cmpq	%rax, %rbp
	jne	.L171
	movdqa	.LC10(%rip), %xmm6
	xorl	%eax, %eax
	movdqa	%xmm14, %xmm12
	movdqa	%xmm14, %xmm11
	movdqa	%xmm14, %xmm5
	movaps	%xmm2, 80(%rsp)
	movaps	%xmm10, 96(%rsp)
	movaps	%xmm0, 112(%rsp)
	movaps	%xmm3, 128(%rsp)
	movaps	%xmm8, 144(%rsp)
	movaps	%xmm9, 160(%rsp)
	.p2align 4
	.p2align 3
.L172:
	movdqu	(%rbx,%rax), %xmm10
	movdqa	%xmm10, %xmm0
	movdqa	%xmm10, %xmm1
	punpcklbw	%xmm7, %xmm0
	punpckhbw	%xmm7, %xmm1
	movdqa	%xmm0, %xmm3
	movdqa	%xmm1, %xmm2
	punpckhwd	%xmm4, %xmm0
	punpckhwd	%xmm4, %xmm1
	punpcklwd	%xmm4, %xmm3
	punpcklwd	%xmm4, %xmm2
	movdqa	%xmm1, %xmm8
	movdqa	%xmm0, %xmm9
	paddd	%xmm3, %xmm9
	paddd	%xmm2, %xmm8
	paddd	%xmm9, %xmm8
	movdqa	%xmm6, %xmm9
	paddd	%xmm15, %xmm9
	paddd	%xmm8, %xmm12
	movdqa	%xmm9, %xmm8
	psrlq	$32, %xmm9
	pmuludq	%xmm2, %xmm8
	psrlq	$32, %xmm2
	pmuludq	%xmm9, %xmm2
	movdqa	(%rsp), %xmm9
	paddd	%xmm6, %xmm9
	pshufd	$8, %xmm8, %xmm8
	pshufd	$8, %xmm2, %xmm2
	punpckldq	%xmm2, %xmm8
	movdqa	%xmm9, %xmm2
	pmuludq	%xmm1, %xmm2
	psrlq	$32, %xmm9
	psrlq	$32, %xmm1
	pmuludq	%xmm9, %xmm1
	pshufd	$8, %xmm2, %xmm2
	pshufd	$8, %xmm1, %xmm1
	punpckldq	%xmm1, %xmm2
	paddd	%xmm8, %xmm2
	movdqa	16(%rsp), %xmm8
	paddd	%xmm6, %xmm8
	movdqa	%xmm8, %xmm1
	psrlq	$32, %xmm8
	pmuludq	%xmm3, %xmm1
	psrlq	$32, %xmm3
	pmuludq	%xmm8, %xmm3
	movdqa	32(%rsp), %xmm8
	paddd	%xmm6, %xmm8
	paddd	64(%rsp), %xmm6
	pshufd	$8, %xmm1, %xmm1
	pshufd	$8, %xmm3, %xmm3
	punpckldq	%xmm3, %xmm1
	movdqa	%xmm8, %xmm3
	pmuludq	%xmm0, %xmm3
	psrlq	$32, %xmm8
	psrlq	$32, %xmm0
	pmuludq	%xmm8, %xmm0
	pshufd	$8, %xmm3, %xmm3
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm3
	movdqu	0(%r13,%rax), %xmm0
	addq	$16, %rax
	paddd	%xmm3, %xmm1
	pxor	%xmm10, %xmm0
	paddd	%xmm1, %xmm2
	pcmpeqb	%xmm13, %xmm0
	paddd	%xmm2, %xmm11
	pcmpeqb	%xmm7, %xmm0
	pand	48(%rsp), %xmm0
	movdqa	%xmm0, %xmm1
	punpckhbw	%xmm7, %xmm0
	movdqa	%xmm0, %xmm2
	punpcklbw	%xmm7, %xmm1
	punpckhwd	%xmm4, %xmm0
	punpcklwd	%xmm4, %xmm2
	por	%xmm2, %xmm0
	movdqa	%xmm1, %xmm2
	punpckhwd	%xmm4, %xmm1
	punpcklwd	%xmm4, %xmm2
	por	%xmm2, %xmm1
	por	%xmm1, %xmm0
	por	%xmm0, %xmm5
	cmpq	$144, %rax
	jne	.L172
	movdqa	%xmm12, %xmm1
	movdqa	80(%rsp), %xmm2
	movq	%r14, 80(%rsp)
	movl	$144, %edx
	psrldq	$8, %xmm1
	movdqa	96(%rsp), %xmm10
	movdqa	112(%rsp), %xmm0
	paddd	%xmm12, %xmm1
	movdqa	128(%rsp), %xmm3
	movdqa	144(%rsp), %xmm8
	movdqa	%xmm1, %xmm6
	movq	184(%rsp), %rcx
	movdqa	160(%rsp), %xmm9
	psrldq	$4, %xmm6
	paddd	%xmm6, %xmm1
	movd	%xmm1, %edi
	movdqa	%xmm11, %xmm1
	psrldq	$8, %xmm1
	paddd	%xmm11, %xmm1
	movdqa	%xmm1, %xmm6
	psrldq	$4, %xmm6
	paddd	%xmm6, %xmm1
	movd	%xmm1, %r8d
	movdqa	%xmm5, %xmm1
	psrldq	$8, %xmm1
	por	%xmm1, %xmm5
	movdqa	%xmm5, %xmm1
	psrldq	$4, %xmm1
	por	%xmm1, %xmm5
	movd	%xmm5, %esi
	.p2align 6
	.p2align 4
	.p2align 3
.L173:
	movzbl	(%rcx), %eax
	movzbl	168(%rcx), %r14d
	xorl	%eax, %r14d
	cmpb	$85, %r14b
	setne	%r14b
	addl	$1, %edx
	addl	%eax, %edi
	addq	$1, %rcx
	imull	%edx, %eax
	movzbl	%r14b, %r14d
	orl	%r14d, %esi
	addl	%eax, %r8d
	cmpl	$152, %edx
	jne	.L173
	cmpl	%r10d, %r8d
	movq	80(%rsp), %r14
	sete	%al
	cmpl	%r9d, %edi
	sete	%dl
	testb	%dl, %al
	je	.L174
	andl	$1, %esi
	je	.L192
.L174:
	addq	$1, 86312(%r12)
	cmpl	$1, 264(%rsp)
	jne	.L178
	imulq	$336, %r15, %rax
	imulq	$10752, 256(%rsp), %rdx
	addq	%rdx, %rax
	movq	$0, 328(%r12,%rax)
	movl	%r10d, 324(%r12,%rax)
	movl	%r9d, 320(%r12,%rax)
	movq	$0, 160(%r12,%rax)
	movl	%r10d, 156(%r12,%rax)
	movl	%r9d, 152(%r12,%rax)
	movl	$-1, %eax
.L167:
	movq	424(%rsp), %rdx
	subq	%fs:40, %rdx
	jne	.L193
	addq	$440, %rsp
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
.L178:
	.cfi_restore_state
	movl	$1, 264(%rsp)
	jmp	.L176
.L192:
	movq	256(%rsp), %rdx
	imulq	$336, %r15, %rsi
	movl	268(%rsp), %ecx
	leaq	sqb_item_at(%rip), %rax
	imulq	$10752, %rdx, %rdi
	salq	$5, %rdx
	addq	%rdi, %rsi
	movq	$0, 328(%r12,%rsi)
	movl	%r10d, 324(%r12,%rsi)
	movl	%r9d, 320(%r12,%rsi)
	movq	$0, 160(%r12,%rsi)
	movl	%r10d, 156(%r12,%rsi)
	movl	%r9d, 152(%r12,%rsi)
	addq	%rdx, %r12
	addq	%r15, %rdx
	movl	%ecx, (%rax,%rdx,4)
	xorl	%eax, %eax
	movb	$1, 86016(%r12,%r15)
	jmp	.L167
.L193:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE37:
	.size	sqb_proofread_commit, .-sqb_proofread_commit
	.p2align 4
	.type	sqb_alloc_slot, @function
sqb_alloc_slot:
.LFB38:
	.cfi_startproc
	subq	$56, %rsp
	.cfi_def_cfa_offset 64
	andl	$31, %esi
	leaq	SQB_SCATLT(%rip), %rax
	movl	(%rax,%rsi,4), %eax
	movq	%rbp, 16(%rsp)
	leal	8(%rax), %r9d
	.p2align 5
	.cfi_offset 6, -48
	.p2align 4
	.p2align 3
.L196:
	movl	%eax, %esi
	movl	%eax, %ebp
	andl	$7, %esi
	andl	$7, %ebp
	cmpl	$31, 86272(%rdi,%rsi,4)
	jle	.L195
	addl	$1, %eax
	cmpl	%eax, %r9d
	jne	.L196
.L201:
	movq	16(%rsp), %rbp
	movl	$-1, %eax
	addq	$56, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L195:
	.cfi_restore_state
	movq	%r14, 40(%rsp)
	.cfi_offset 14, -24
	leaq	(%rdi,%rsi,4), %r14
	movl	%ebp, %esi
	movq	%r15, 48(%rsp)
	.cfi_offset 15, -16
	movl	86272(%r14), %r15d
	movq	%r12, 24(%rsp)
	.cfi_offset 12, -40
	movq	%rcx, %r12
	movl	%edx, %ecx
	movl	%r15d, %edx
	movq	%rbx, 8(%rsp)
	.cfi_offset 3, -56
	movq	%rdi, %rbx
	movq	%r13, 32(%rsp)
	.cfi_offset 13, -32
	movq	%r8, %r13
	call	sqb_proofread_commit
	testl	%eax, %eax
	jne	.L210
	addl	$1, 86272(%r14)
	addl	$1, 86304(%rbx)
	testq	%r12, %r12
	je	.L198
	movl	%ebp, (%r12)
.L198:
	testq	%r13, %r13
	je	.L209
	movl	%r15d, 0(%r13)
.L209:
	movq	8(%rsp), %rbx
	.cfi_remember_state
	.cfi_restore 3
	movq	24(%rsp), %r12
	.cfi_restore 12
	movq	32(%rsp), %r13
	.cfi_restore 13
	movq	40(%rsp), %r14
	.cfi_restore 14
	movq	48(%rsp), %r15
	.cfi_restore 15
	movq	16(%rsp), %rbp
	addq	$56, %rsp
	.cfi_def_cfa_offset 8
	ret
.L210:
	.cfi_restore_state
	movq	8(%rsp), %rbx
	.cfi_restore 3
	movq	24(%rsp), %r12
	.cfi_restore 12
	movq	32(%rsp), %r13
	.cfi_restore 13
	movq	40(%rsp), %r14
	.cfi_restore 14
	movq	48(%rsp), %r15
	.cfi_restore 15
	jmp	.L201
	.cfi_endproc
.LFE38:
	.size	sqb_alloc_slot, .-sqb_alloc_slot
	.p2align 4
	.type	sqb_alloc, @function
sqb_alloc:
.LFB39:
	.cfi_startproc
	andl	$31, %esi
	leaq	SQB_SCATLT(%rip), %rax
	movl	(%rax,%rsi,4), %eax
	leal	8(%rax), %r9d
	.p2align 5
	.p2align 4
	.p2align 3
.L213:
	movl	%eax, %esi
	movl	%eax, %r8d
	andl	$7, %esi
	andl	$7, %r8d
	cmpl	$31, 86272(%rdi,%rsi,4)
	jle	.L212
	addl	$1, %eax
	cmpl	%eax, %r9d
	jne	.L213
	movl	$-1, %eax
	ret
	.p2align 4,,10
	.p2align 3
.L212:
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	leaq	(%rdi,%rsi,4), %rbp
	movl	%edx, %ecx
	movl	%r8d, %esi
	pushq	%rbx
	.cfi_def_cfa_offset 24
	.cfi_offset 3, -24
	movq	%rdi, %rbx
	subq	$8, %rsp
	.cfi_def_cfa_offset 32
	movl	86272(%rbp), %edx
	call	sqb_proofread_commit
	testl	%eax, %eax
	jne	.L222
	addl	$1, 86272(%rbp)
	addl	$1, 86304(%rbx)
.L211:
	addq	$8, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 24
	popq	%rbx
	.cfi_def_cfa_offset 16
	popq	%rbp
	.cfi_def_cfa_offset 8
	ret
.L222:
	.cfi_restore_state
	movl	$-1, %eax
	jmp	.L211
	.cfi_endproc
.LFE39:
	.size	sqb_alloc, .-sqb_alloc
	.p2align 4
	.type	sqb_transcribe, @function
sqb_transcribe:
.LFB40:
	.cfi_startproc
	movslq	%edx, %rdx
	movslq	%esi, %rsi
	movl	$1, %eax
	imulq	$336, %rdx, %rdx
	imulq	$10752, %rsi, %rsi
	addq	%rsi, %rdx
	addq	%rdx, %rdi
	cmpl	$-559063315, 164(%rdi)
	je	.L223
	movdqu	(%rdi), %xmm0
	movups	%xmm0, (%rcx)
	movdqu	16(%rdi), %xmm0
	movups	%xmm0, 16(%rcx)
	movdqu	32(%rdi), %xmm0
	movups	%xmm0, 32(%rcx)
	movdqu	48(%rdi), %xmm0
	movups	%xmm0, 48(%rcx)
	movdqu	64(%rdi), %xmm0
	movups	%xmm0, 64(%rcx)
	movdqu	80(%rdi), %xmm0
	movups	%xmm0, 80(%rcx)
	movdqu	96(%rdi), %xmm0
	movups	%xmm0, 96(%rcx)
	movdqu	112(%rdi), %xmm0
	movups	%xmm0, 112(%rcx)
	movdqu	128(%rdi), %xmm0
	movups	%xmm0, 128(%rcx)
	movq	144(%rdi), %rax
	movq	%rax, 144(%rcx)
	xorl	%eax, %eax
.L223:
	ret
	.cfi_endproc
.LFE40:
	.size	sqb_transcribe, .-sqb_transcribe
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
.L227:
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
.L278:
	cmpb	$0, 0(%rbp)
	je	.L229
	testq	%r13, %r13
	je	.L230
	movl	%r12d, %eax
	movb	$0, 0(%r13,%rax)
.L230:
	cmpl	$-559063315, 164(%rdi)
	je	.L229
	xorl	%eax, %eax
	pxor	%xmm1, %xmm1
	pxor	%xmm4, %xmm4
	.p2align 4
	.p2align 3
.L232:
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
	jne	.L232
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
.L233:
	movzbl	(%rdx), %ecx
	xorb	168(%rdx), %cl
	cmpb	$85, %cl
	setne	%cl
	addq	$1, %rdx
	movzbl	%cl, %ecx
	addl	%ecx, %eax
	cmpq	%r9, %rdx
	jne	.L233
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
	movdqa	.LC10(%rip), %xmm6
	pshufd	$0, %xmm5, %xmm3
	movdqa	%xmm8, %xmm14
	movdqa	%xmm4, %xmm5
	movdqa	%xmm3, %xmm15
	movaps	%xmm3, 48(%rsp)
	movaps	%xmm8, 64(%rsp)
	.p2align 4
	.p2align 3
.L234:
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
	jne	.L234
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
.L235:
	movzbl	-1(%rdi,%rsi), %r8d
	addl	%r8d, %edx
	imull	%esi, %r8d
	addq	$1, %rsi
	addl	%r8d, %ecx
	cmpq	$153, %rsi
	jne	.L235
	movl	$0, 32(%rsp)
	xorl	%r14d, %r14d
	cmpl	%edx, 152(%rdi)
	jne	.L236
	cmpl	%ecx, 156(%rdi)
	sete	%sil
	sete	%dl
	testl	%eax, %eax
	movzbl	%sil, %esi
	sete	%r14b
	movl	%esi, 32(%rsp)
	andl	%edx, %r14d
.L236:
	leaq	160(%rsp), %r8
	movq	%r11, %rax
	movq	%r8, %rdx
	.p2align 5
	.p2align 4
	.p2align 3
.L237:
	movdqu	(%rax), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm7, %xmm0
	movaps	%xmm0, -16(%rdx)
	cmpq	%r10, %rax
	jne	.L237
	leaq	168(%rsp), %rsi
	leaq	160(%rsp), %rax
	movq	%r10, %rcx
	.p2align 5
	.p2align 4
	.p2align 3
.L238:
	movzbl	(%rcx), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, 143(%rax)
	cmpq	%rax, %rsi
	jne	.L238
	pxor	%xmm4, %xmm4
	movdqa	.LC10(%rip), %xmm6
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
.L239:
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
	jne	.L239
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
.L240:
	movzbl	144(%r8), %eax
	addl	$1, %edx
	addq	$1, %r8
	addl	%eax, %ecx
	imull	%edx, %eax
	addl	%eax, %esi
	cmpl	$152, %edx
	jne	.L240
	cmpl	%ecx, 320(%rdi)
	je	.L322
.L241:
	testb	%r14b, %r14b
	je	.L323
	testq	%r13, %r13
	je	.L247
.L246:
	movl	%r12d, %eax
	movb	$1, 0(%r13,%rax)
	movl	32(%rsp), %edx
	testl	%edx, %edx
	jne	.L247
	movl	$-559063315, 164(%rdi)
	movq	104(%rsp), %rsi
	movl	$-559063315, 332(%rdi)
	addq	$1, 86320(%rsi)
	movb	$2, 0(%r13,%rax)
.L255:
	cmpl	$-559063315, 164(%rdi)
	jne	.L261
	.p2align 4
	.p2align 3
.L229:
	addq	$336, %rdi
	addq	$1, %rbp
	addq	$336, %r10
	addq	$336, %r11
	addq	$336, %r9
	addl	$1, %r12d
	cmpq	%r15, %rdi
	jne	.L278
	movq	136(%rsp), %rax
	movq	144(%rsp), %rcx
	leaq	10752(%rdi), %r15
	movq	152(%rsp), %rdx
	addq	$1, %rax
	addq	$32, %rcx
	addq	$10752, %rdx
	cmpq	$8, %rax
	jne	.L227
	movq	312(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L324
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
.L323:
	.cfi_restore_state
	testq	%r13, %r13
	jne	.L246
	movl	32(%rsp), %eax
	testl	%eax, %eax
	jne	.L247
	movl	$-559063315, 164(%rdi)
	movq	104(%rsp), %rax
	movl	$-559063315, 332(%rdi)
	addq	$1, 86320(%rax)
	jmp	.L229
.L322:
	cmpl	%esi, 324(%rdi)
	jne	.L241
	testb	%r14b, %r14b
	jne	.L242
	testq	%r13, %r13
	je	.L248
	movl	%r12d, %eax
	movb	$1, 0(%r13,%rax)
.L248:
	cmpl	$1, 32(%rsp)
	je	.L256
	leaq	160(%rsp), %r8
	movq	%r11, %rax
	movq	%r8, %rdx
	.p2align 5
	.p2align 4
	.p2align 3
.L257:
	movdqu	(%rax), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm7, %xmm0
	movaps	%xmm0, -16(%rdx)
	cmpq	%r10, %rax
	jne	.L257
	leaq	168(%rsp), %rsi
	leaq	160(%rsp), %rax
	movq	%r10, %rcx
	.p2align 5
	.p2align 4
	.p2align 3
.L258:
	movzbl	(%rcx), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, 143(%rax)
	cmpq	%rsi, %rax
	jne	.L258
	movdqa	160(%rsp), %xmm0
	pxor	%xmm6, %xmm6
	movq	304(%rsp), %rax
	leaq	304(%rsp), %rdx
	movdqa	.LC10(%rip), %xmm10
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
.L259:
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
	movdqa	.LC19(%rip), %xmm14
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
	movdqa	.LC21(%rip), %xmm1
	paddd	%xmm10, %xmm1
	paddd	.LC16(%rip), %xmm10
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
	jne	.L259
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
.L260:
	movzbl	144(%r8), %eax
	addl	$1, %edx
	addq	$1, %r8
	addl	%eax, %esi
	imull	%edx, %eax
	addl	%eax, %ecx
	cmpl	$152, %edx
	jne	.L260
	movl	%esi, 152(%rdi)
	movl	%ecx, 156(%rdi)
	movl	$0, 164(%rdi)
.L261:
	xorl	%eax, %eax
	pxor	%xmm1, %xmm1
	pxor	%xmm2, %xmm2
	.p2align 4
	.p2align 3
.L267:
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
	jne	.L267
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
.L268:
	movzbl	(%rdx), %ecx
	xorb	168(%rdx), %cl
	cmpb	$85, %cl
	setne	%cl
	addq	$1, %rdx
	movzbl	%cl, %ecx
	addl	%ecx, %eax
	cmpq	%r9, %rdx
	jne	.L268
	testl	%eax, %eax
	jne	.L269
	pxor	%xmm6, %xmm6
	movq	%rdi, %rax
	pxor	%xmm15, %xmm15
	movdqa	.LC10(%rip), %xmm10
	movdqa	%xmm6, %xmm5
	.p2align 4
	.p2align 3
.L270:
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
	movdqa	.LC19(%rip), %xmm14
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
	movdqa	.LC21(%rip), %xmm1
	paddd	%xmm10, %xmm1
	paddd	.LC16(%rip), %xmm10
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
	jne	.L270
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
.L271:
	movzbl	-1(%rdi,%rax), %edx
	addl	%edx, %esi
	imull	%eax, %edx
	addq	$1, %rax
	addl	%edx, %ecx
	cmpq	$153, %rax
	jne	.L271
	cmpl	%esi, 152(%rdi)
	je	.L325
.L269:
	addq	$1, 128(%rsp)
	jmp	.L229
.L247:
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
.L251:
	movdqa	(%rdx), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm7, %xmm0
	movups	%xmm0, -16(%rax)
	cmpq	%r10, %rax
	jne	.L251
	leaq	168(%rsp), %rsi
	movq	%r10, %rcx
	leaq	160(%rsp), %rax
	.p2align 5
	.p2align 4
	.p2align 3
.L252:
	movzbl	144(%rax), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, -1(%rcx)
	cmpq	%rsi, %rax
	jne	.L252
	pxor	%xmm6, %xmm6
	leaq	304(%rsp), %rdx
	movdqa	.LC10(%rip), %xmm10
	leaq	160(%rsp), %rax
	movdqa	%xmm6, %xmm5
	pxor	%xmm15, %xmm15
	.p2align 4
	.p2align 3
.L253:
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
	movdqa	.LC19(%rip), %xmm14
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
	movdqa	.LC21(%rip), %xmm1
	paddd	%xmm10, %xmm1
	paddd	.LC16(%rip), %xmm10
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
	jne	.L253
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
.L254:
	movzbl	144(%r8), %eax
	addl	$1, %edx
	addq	$1, %r8
	addl	%eax, %esi
	imull	%edx, %eax
	addl	%eax, %ecx
	cmpl	$152, %edx
	jne	.L254
	movl	%esi, 320(%rdi)
	movl	%ecx, 324(%rdi)
	movl	$0, 332(%rdi)
	movl	%r14d, 328(%rdi)
	jmp	.L255
.L242:
	addl	$1, 160(%rdi)
	addl	$1, 328(%rdi)
	jmp	.L229
.L256:
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
.L263:
	movdqa	(%rdx), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm7, %xmm0
	movups	%xmm0, -16(%rax)
	cmpq	%r10, %rax
	jne	.L263
	leaq	168(%rsp), %rsi
	movq	%r10, %rcx
	leaq	160(%rsp), %rax
	.p2align 5
	.p2align 4
	.p2align 3
.L264:
	movzbl	144(%rax), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, -1(%rcx)
	cmpq	%rsi, %rax
	jne	.L264
	pxor	%xmm6, %xmm6
	leaq	304(%rsp), %rdx
	movdqa	.LC10(%rip), %xmm10
	leaq	160(%rsp), %rax
	movdqa	%xmm6, %xmm5
	pxor	%xmm15, %xmm15
.L265:
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
	movdqa	.LC19(%rip), %xmm14
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
	movdqa	.LC21(%rip), %xmm1
	paddd	%xmm10, %xmm1
	paddd	.LC16(%rip), %xmm10
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
	jne	.L265
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
.L266:
	movzbl	144(%r8), %eax
	addl	$1, %edx
	addq	$1, %r8
	addl	%eax, %esi
	imull	%edx, %eax
	addl	%eax, %ecx
	cmpl	$152, %edx
	jne	.L266
	movq	104(%rsp), %rax
	movl	%esi, 320(%rdi)
	movl	%ecx, 324(%rdi)
	movl	$0, 332(%rdi)
	movl	%r14d, 328(%rdi)
	addq	$1, 86328(%rax)
	jmp	.L255
.L325:
	cmpl	%ecx, 156(%rdi)
	jne	.L269
	leaq	160(%rsp), %r8
	movdqa	112(%rsp), %xmm1
	movq	%r11, %rax
	movq	%r8, %rdx
.L272:
	movdqu	(%rax), %xmm0
	addq	$16, %rax
	addq	$16, %rdx
	pxor	%xmm1, %xmm0
	movaps	%xmm0, -16(%rdx)
	cmpq	%r10, %rax
	jne	.L272
	leaq	168(%rsp), %rsi
	leaq	160(%rsp), %rax
	movq	%r10, %rcx
.L273:
	movzbl	(%rcx), %edx
	addq	$1, %rax
	addq	$1, %rcx
	xorl	$85, %edx
	movb	%dl, 143(%rax)
	cmpq	%rax, %rsi
	jne	.L273
	pxor	%xmm10, %xmm10
	movdqa	.LC10(%rip), %xmm4
	pxor	%xmm5, %xmm5
	leaq	304(%rsp), %rdx
	leaq	160(%rsp), %rax
	movdqa	%xmm10, %xmm6
.L274:
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
	jne	.L274
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
.L275:
	movzbl	144(%r8), %eax
	addl	$1, %edx
	addq	$1, %r8
	addl	%eax, %esi
	imull	%edx, %eax
	addl	%eax, %ecx
	cmpl	$152, %edx
	jne	.L275
	cmpl	320(%rdi), %esi
	jne	.L269
	cmpl	324(%rdi), %ecx
	jne	.L269
	jmp	.L229
.L324:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE41:
	.size	sqb_sweep, .-sqb_sweep
	.p2align 4
	.type	cert_round.constprop.0, @function
cert_round.constprop.0:
.LFB61:
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
	movl	%esi, %ebp
	leaq	clean.1(%rip), %rsi
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	movq	%rdi, %rbx
	leaq	w.2(%rip), %rdi
	subq	$2776, %rsp
	.cfi_def_cfa_offset 2832
	movl	%edx, 32(%rsp)
	movl	$152920, %edx
	movq	%fs:40, %r14
	movq	%r14, 2760(%rsp)
	movq	%rcx, %r14
	call	memcpy@PLT
	leaq	w.2(%rip), %rdx
	xorl	%r8d, %r8d
	xorl	%ecx, %ecx
	.p2align 4
	.p2align 3
.L327:
	xorl	%eax, %eax
	.p2align 6
	.p2align 4
	.p2align 3
.L329:
	cmpb	$0, 86016(%rdx,%rax)
	je	.L328
	movl	%r8d, %edi
	movl	%ecx, %esi
	addl	$1, %ecx
	orl	%eax, %edi
	movl	%edi, 48(%rsp,%rsi,4)
.L328:
	addq	$1, %rax
	cmpq	$32, %rax
	jne	.L329
	addl	$256, %r8d
	addq	$32, %rdx
	cmpl	$2048, %r8d
	jne	.L327
	leaq	1072(%rsp), %r12
	leaq	0(%rbp,%rbp,2), %rax
	movl	%ecx, 36(%rsp)
	movsd	.LC2(%rip), %xmm1
	leaq	(%r12,%rax,8), %rax
	movq	%r12, 40(%rsp)
	movq	%r12, %r15
	movsd	.LC25(%rip), %xmm2
	movq	%rax, 8(%rsp)
	movq	%r14, 16(%rsp)
	jmp	.L337
	.p2align 4,,10
	.p2align 3
.L395:
	movl	%eax, %edi
	imulq	$336, %r9, %rax
	movslq	%ebp, %rcx
	imulq	$168, %rdi, %rdi
	imulq	$10752, %rcx, %rcx
	addq	%rdi, %rax
	leaq	w.2(%rip), %rdi
	addq	%rcx, %rax
	addq	%rdi, %rax
	xorb	%dl, (%rax,%rsi)
.L334:
	movq	16(%rsp), %rax
	addq	$24, %r15
	addq	$1, (%rax,%r10,8)
	cmpq	%r15, 8(%rsp)
	je	.L393
.L337:
	movl	32(%rsp), %edi
	movq	(%rbx), %rax
	movq	24(%rbx), %rdx
	movq	8(%rbx), %rcx
	movq	16(%rbx), %rsi
	movl	%edi, %r10d
	cmpl	$-1, %edi
	je	.L394
.L331:
	movq	%rdx, %r12
	xorq	%rax, %rsi
	movl	%r10d, (%r15)
	xorq	%rcx, %r12
	movq	%rsi, %rdi
	movq	%r12, %r11
	xorq	%rcx, %rdi
	salq	$17, %rcx
	xorq	%rax, %r11
	addq	%rdx, %rax
	xorl	%edx, %edx
	xorq	%rsi, %rcx
	rolq	$17, %rax
	xorq	%r11, %rcx
	rorq	$19, %r12
	movq	%rdi, %rsi
	divl	36(%rsp)
	xorq	%r12, %rsi
	leaq	(%r11,%r12), %rax
	movq	%rsi, %r8
	rorq	$19, %rsi
	xorq	%r11, %r8
	rolq	$17, %rax
	andl	$1, %eax
	movl	%eax, 12(%r15)
	movl	48(%rsp,%rdx,4), %r13d
	movq	%rcx, %rdx
	xorq	%rdi, %rdx
	salq	$17, %rdi
	xorq	%rcx, %rdi
	movq	%rdx, %r12
	movl	%r13d, %ebp
	movzbl	%r13b, %r9d
	xorq	%r8, %rdi
	xorq	%rsi, %r12
	sarl	$8, %ebp
	movl	%r9d, 8(%r15)
	movq	%rdi, %rcx
	movq	%rdi, %r11
	movq	%r12, %rdi
	rorq	$19, %r12
	xorq	%r8, %rdi
	addq	%rsi, %r8
	xorq	%rdx, %r11
	movl	%ebp, 4(%r15)
	rolq	$17, %r8
	movl	%r8d, %esi
	shrl	$3, %esi
	imulq	$452101821, %rsi, %rsi
	shrq	$33, %rsi
	imull	$152, %esi, %r14d
	movl	%r8d, %esi
	subl	%r14d, %esi
	salq	$17, %rdx
	xorq	%rcx, %rdx
	movq	%r11, %rcx
	xorq	%rdi, %rdx
	xorq	%r12, %rcx
	movq	%rdx, %r8
	xorq	%r11, %r8
	salq	$17, %r11
	movq	%r8, 8(%rbx)
	movq	%rcx, %r8
	rorq	$19, %rcx
	xorq	%rdx, %r11
	xorq	%rdi, %r8
	addq	%r12, %rdi
	movq	%rcx, 24(%rbx)
	movl	$2155905153, %ecx
	rolq	$17, %rdi
	movq	%r8, (%rbx)
	movl	%edi, %edx
	movq	%r11, 16(%rbx)
	imulq	%rcx, %rdx
	shrq	$39, %rdx
	leal	1(%rdi,%rdx), %edx
	testl	%r10d, %r10d
	je	.L395
	cmpl	$1, %r10d
	je	.L396
	cmpl	$2, %r10d
	je	.L397
	leal	5396(%rsi), %eax
	andl	$15, %r13d
	leaq	w.2(%rip), %rsi
	salq	$4, %rax
	addq	%r13, %rax
	xorb	%dl, (%rsi,%rax)
	jmp	.L334
.L394:
	xorq	%rax, %rsi
	leaq	(%rax,%rdx), %r8
	movq	%rcx, %rdi
	xorq	%rcx, %rdx
	salq	$17, %rcx
	xorq	%rsi, %rdi
	pxor	%xmm0, %xmm0
	xorq	%rdx, %rax
	xorq	%rcx, %rsi
	movq	%r8, %rcx
	rorq	$19, %rdx
	xorl	%r10d, %r10d
	rolq	$17, %rcx
	shrq	$11, %rcx
	cvtsi2sdq	%rcx, %xmm0
	mulsd	%xmm1, %xmm0
	movq	%rdi, %rcx
	comisd	%xmm0, %xmm2
	ja	.L331
	xorq	%rax, %rsi
	leaq	(%rax,%rdx), %r8
	xorq	%rdi, %rdx
	salq	$17, %rdi
	xorq	%rsi, %rcx
	xorq	%rdi, %rsi
	movq	%r8, %rdi
	xorq	%rdx, %rax
	rolq	$17, %rdi
	pxor	%xmm0, %xmm0
	rorq	$19, %rdx
	movsd	.LC26(%rip), %xmm3
	shrq	$11, %rdi
	movl	$1, %r10d
	cvtsi2sdq	%rdi, %xmm0
	mulsd	%xmm1, %xmm0
	comisd	%xmm0, %xmm3
	ja	.L331
	leaq	(%rax,%rdx), %rdi
	pxor	%xmm0, %xmm0
	xorq	%rax, %rsi
	movsd	.LC27(%rip), %xmm3
	rolq	$17, %rdi
	movq	%rsi, %r8
	movq	%rcx, %rsi
	xorq	%rcx, %rdx
	shrq	$11, %rdi
	salq	$17, %rsi
	xorq	%rdx, %rax
	xorq	%r8, %rcx
	cvtsi2sdq	%rdi, %xmm0
	mulsd	%xmm1, %xmm0
	xorq	%r8, %rsi
	rorq	$19, %rdx
	movl	$2, %r10d
	movl	$3, %edi
	comisd	%xmm0, %xmm3
	cmovbe	%rdi, %r10
	jmp	.L331
.L396:
	movl	%r9d, %ecx
	negq	%rax
	andl	$7, %esi
	imulq	$336, %rcx, %rcx
	andl	$168, %eax
	leaq	152(%rcx,%rax), %rax
	movslq	%ebp, %rcx
	imulq	$10752, %rcx, %rcx
	addq	%rcx, %rax
	addq	%rsi, %rax
	leaq	w.2(%rip), %rsi
	xorb	%dl, (%rsi,%rax)
	jmp	.L334
.L393:
	movq	%rax, %r14
	movl	$1431655765, %eax
	movq	40(%rsp), %r12
	leaq	action.0(%rip), %r13
	movd	%eax, %xmm2
	movq	%r13, %rsi
	leaq	w.2(%rip), %rdi
	pshufd	$0, %xmm2, %xmm7
	movaps	%xmm7, 16(%rsp)
	leaq	sqb_item_at(%rip), %r15
	leaq	2760(%rsp), %rbx
	call	sqb_sweep
	addq	%rax, 144(%r14)
	movdqa	16(%rsp), %xmm15
	leaq	2616(%rsp), %rbp
	.p2align 4
	.p2align 3
.L359:
	movslq	4(%r12), %rdx
	movslq	8(%r12), %rsi
	movl	%edx, %eax
	sall	$5, %eax
	addl	%esi, %eax
	cltq
	movzbl	0(%r13,%rax), %ecx
	movl	(%r12), %eax
	testl	%eax, %eax
	jne	.L338
	testl	%ecx, %ecx
	je	.L339
	addq	$1, 32(%r14)
.L339:
	movslq	12(%r12), %rax
	testl	%eax, %eax
	jne	.L340
	imulq	$336, %rsi, %rax
	leaq	w.2(%rip), %rdi
	imulq	$10752, %rdx, %rcx
	addq	%rcx, %rax
	addq	%rdi, %rax
	movdqa	(%rax), %xmm0
	movaps	%xmm0, 2608(%rsp)
	movdqa	16(%rax), %xmm0
	movaps	%xmm0, 2624(%rsp)
	movdqa	32(%rax), %xmm0
	movaps	%xmm0, 2640(%rsp)
	movdqa	48(%rax), %xmm0
	movaps	%xmm0, 2656(%rsp)
	movdqa	64(%rax), %xmm0
	movaps	%xmm0, 2672(%rsp)
	movdqa	80(%rax), %xmm0
	movaps	%xmm0, 2688(%rsp)
	movdqa	96(%rax), %xmm0
	movaps	%xmm0, 2704(%rsp)
	movdqa	112(%rax), %xmm0
	movaps	%xmm0, 2720(%rsp)
	movdqa	128(%rax), %xmm0
	movq	144(%rax), %rax
	movq	%rax, 2752(%rsp)
	movaps	%xmm0, 2736(%rsp)
.L341:
	salq	$5, %rdx
	leaq	(%rdx,%rsi), %rax
	movl	(%r15,%rax,4), %eax
	movl	%eax, %edx
	sall	$4, %edx
	addl	%eax, %edx
	leaq	2608(%rsp), %rax
	jmp	.L345
	.p2align 5
	.p2align 4,,10
	.p2align 3
.L399:
	addq	$1, %rax
	addl	$91, %edx
	cmpq	%rbx, %rax
	je	.L398
.L345:
	movl	%edx, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, (%rax)
	je	.L399
	xorl	%eax, %eax
.L344:
	addq	%rax, 64(%r14)
.L346:
	addq	$24, %r12
	cmpq	%r12, 8(%rsp)
	jne	.L359
	movq	86320+w.2(%rip), %rax
	testq	%rax, %rax
	jle	.L360
	addq	%rax, 128(%r14)
	leaq	10916+w.2(%rip), %rsi
	leaq	140956(%rsi), %r8
	leaq	86016(%rsi), %r9
	.p2align 4
	.p2align 3
.L361:
	leaq	-10752(%rsi), %rax
	movq	%r8, %rcx
	jmp	.L363
	.p2align 5
	.p2align 4,,10
	.p2align 3
.L362:
	addq	$336, %rax
	addq	$4, %rcx
	cmpq	%rsi, %rax
	je	.L400
.L363:
	cmpl	$-559063315, (%rax)
	jne	.L362
	movl	(%rcx), %edx
	movzwl	%dx, %edi
	shrl	$16, %edx
	addl	%edi, %edx
	cmpl	$65535, %edx
	jne	.L362
	addq	$336, %rax
	addq	%rdi, 136(%r14)
	addq	$4, %rcx
	cmpq	%rsi, %rax
	jne	.L363
	.p2align 4
	.p2align 3
.L400:
	addq	$10752, %rsi
	subq	$-128, %r8
	cmpq	%rsi, %r9
	jne	.L361
.L360:
	leaq	w.2(%rip), %rdi
	call	verify_all_items.constprop.0
	addl	$1, 160(%r14)
	movq	%rax, %rdx
	movl	$256, %eax
	subq	%rdx, %rax
	addq	%rax, 152(%r14)
	movq	2760(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L401
	addq	$2776, %rsp
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
	.p2align 4,,10
	.p2align 3
.L338:
	.cfi_restore_state
	cmpl	$1, %eax
	je	.L402
	cmpl	$2, %eax
	je	.L403
	addq	$1, 120(%r14)
	leaq	w.2(%rip), %rdi
	call	verify_all_items.constprop.0
	cmpq	$256, %rax
	sete	%al
	movzbl	%al, %eax
	addq	%rax, 112(%r14)
	jmp	.L346
.L402:
	testl	%ecx, %ecx
	je	.L348
	addq	$1, 40(%r14)
.L348:
	movl	$16, %eax
	movslq	12(%r12), %r8
	movd	%eax, %xmm9
	movl	$9, %eax
	movd	%eax, %xmm11
	movl	$13, %eax
	pshufd	$0, %xmm9, %xmm9
	movd	%eax, %xmm12
	movl	$5, %eax
	pshufd	$0, %xmm11, %xmm11
	movd	%eax, %xmm10
	pshufd	$0, %xmm12, %xmm12
	pshufd	$0, %xmm10, %xmm10
	testl	%r8d, %r8d
	jne	.L349
	imulq	$10752, %rdx, %rax
	pxor	%xmm1, %xmm1
	pcmpeqd	%xmm14, %xmm14
	movdqa	.LC10(%rip), %xmm5
	imulq	$336, %rsi, %r9
	movdqa	%xmm1, %xmm2
	pxor	%xmm13, %xmm13
	movaps	%xmm15, 16(%rsp)
	pxor	%xmm8, %xmm8
	psrld	$31, %xmm14
	addq	%rax, %r9
	leaq	w.2(%rip), %rax
	addq	%rax, %r9
	movq	%r9, %rax
	leaq	144(%r9), %rcx
	.p2align 4
	.p2align 3
.L350:
	movdqa	(%rax), %xmm3
	addq	$16, %rax
	movdqa	%xmm3, %xmm0
	punpckhbw	%xmm13, %xmm3
	punpcklbw	%xmm13, %xmm0
	movdqa	%xmm3, %xmm6
	punpckhwd	%xmm8, %xmm3
	movdqa	%xmm0, %xmm4
	punpcklwd	%xmm8, %xmm6
	punpckhwd	%xmm8, %xmm0
	punpcklwd	%xmm8, %xmm4
	movdqa	%xmm6, %xmm15
	movdqa	%xmm4, %xmm7
	paddd	%xmm3, %xmm15
	paddd	%xmm0, %xmm7
	paddd	%xmm15, %xmm7
	movdqa	%xmm5, %xmm15
	paddd	%xmm10, %xmm15
	paddd	%xmm7, %xmm1
	movdqa	%xmm15, %xmm7
	psrlq	$32, %xmm15
	pmuludq	%xmm0, %xmm7
	psrlq	$32, %xmm0
	pmuludq	%xmm15, %xmm0
	movdqa	%xmm5, %xmm15
	paddd	%xmm14, %xmm15
	pshufd	$8, %xmm7, %xmm7
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm7
	movdqa	%xmm15, %xmm0
	pmuludq	%xmm4, %xmm0
	psrlq	$32, %xmm15
	psrlq	$32, %xmm4
	pmuludq	%xmm15, %xmm4
	pshufd	$8, %xmm0, %xmm0
	pshufd	$8, %xmm4, %xmm4
	punpckldq	%xmm4, %xmm0
	paddd	%xmm7, %xmm0
	movdqa	%xmm5, %xmm7
	paddd	%xmm12, %xmm7
	movdqa	%xmm7, %xmm4
	psrlq	$32, %xmm7
	pmuludq	%xmm3, %xmm4
	psrlq	$32, %xmm3
	pmuludq	%xmm7, %xmm3
	movdqa	%xmm5, %xmm7
	paddd	%xmm9, %xmm5
	paddd	%xmm11, %xmm7
	pshufd	$8, %xmm4, %xmm4
	pshufd	$8, %xmm3, %xmm3
	punpckldq	%xmm3, %xmm4
	movdqa	%xmm7, %xmm3
	pmuludq	%xmm6, %xmm3
	psrlq	$32, %xmm7
	psrlq	$32, %xmm6
	pmuludq	%xmm7, %xmm6
	pshufd	$8, %xmm3, %xmm3
	pshufd	$8, %xmm6, %xmm6
	punpckldq	%xmm6, %xmm3
	paddd	%xmm3, %xmm4
	paddd	%xmm4, %xmm0
	paddd	%xmm0, %xmm2
	cmpq	%rcx, %rax
	jne	.L350
	movdqa	%xmm1, %xmm0
	movdqa	16(%rsp), %xmm15
	movl	$145, %eax
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm1
	movdqa	%xmm1, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm1
	movdqa	%xmm2, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm1, %ecx
	paddd	%xmm0, %xmm2
	movdqa	%xmm2, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm2
	movd	%xmm2, %edi
	.p2align 5
	.p2align 4
	.p2align 3
.L351:
	movzbl	-1(%r9,%rax), %r8d
	addl	%r8d, %ecx
	imull	%eax, %r8d
	addq	$1, %rax
	addl	%r8d, %edi
	cmpq	$153, %rax
	jne	.L351
	xorl	%r8d, %r8d
.L352:
	imulq	$10752, %rdx, %rdx
	imulq	$168, %r8, %rax
	imulq	$336, %rsi, %rsi
	addq	%rdx, %rax
	xorl	%edx, %edx
	addq	%rsi, %rax
	leaq	w.2(%rip), %rsi
	addq	%rsi, %rax
	cmpl	%ecx, 152(%rax)
	jne	.L357
	xorl	%edx, %edx
	cmpl	%edi, 156(%rax)
	sete	%dl
.L357:
	addq	%rdx, 72(%r14)
	jmp	.L346
.L340:
	imulq	$168, %rax, %r8
	leaq	w.2(%rip), %rdi
	imulq	$336, %rsi, %r11
	leaq	2608(%rsp), %rax
	imulq	$10752, %rdx, %r10
	leaq	(%r8,%r11), %rcx
	addq	%r10, %rcx
	addq	%rdi, %rcx
	movq	%rax, %rdi
	leaq	144(%rcx), %r9
	.p2align 5
	.p2align 4
	.p2align 3
.L342:
	movdqu	(%rcx), %xmm0
	pxor	.LC23(%rip), %xmm0
	addq	$16, %rcx
	addq	$16, %rdi
	movaps	%xmm0, -16(%rdi)
	cmpq	%rcx, %r9
	jne	.L342
	leaq	w.2(%rip), %rdi
	leaq	144(%rdi,%r8), %rdi
	addq	%r11, %rdi
	addq	%r10, %rdi
	.p2align 5
	.p2align 4
	.p2align 3
.L343:
	movzbl	(%rdi), %ecx
	addq	$1, %rax
	addq	$1, %rdi
	xorl	$85, %ecx
	movb	%cl, 143(%rax)
	cmpq	%rbp, %rax
	jne	.L343
	jmp	.L341
.L397:
	movslq	%ebp, %rax
	leal	37968(%r9), %ecx
	andl	$3, %esi
	salq	$5, %rax
	addq	%rcx, %rax
	leaq	(%rsi,%rax,4), %rax
	leaq	w.2(%rip), %rsi
	xorb	%dl, (%rsi,%rax)
	jmp	.L334
.L403:
	salq	$5, %rdx
	leaq	37968(%rsi,%rdx), %rax
	leaq	w.2(%rip), %rsi
	movl	(%rsi,%rax,4), %eax
	movzwl	%ax, %edx
	shrl	$16, %eax
	addl	%edx, %eax
	cmpl	$65535, %eax
	setne	%al
	movzbl	%al, %eax
	addq	%rax, 48(%r14)
	jmp	.L346
.L349:
	imulq	$336, %rsi, %r11
	leaq	2608(%rsp), %rax
	movdqa	%xmm15, %xmm1
	imulq	$168, %r8, %r10
	imulq	$10752, %rdx, %rdi
	leaq	(%r10,%r11), %rcx
	addq	%rdi, %rcx
	movq	%rdi, 16(%rsp)
	leaq	w.2(%rip), %rdi
	addq	%rdi, %rcx
	movq	%rax, %rdi
	leaq	144(%rcx), %r9
	.p2align 5
	.p2align 4
	.p2align 3
.L353:
	movdqu	(%rcx), %xmm0
	addq	$16, %rcx
	addq	$16, %rdi
	pxor	%xmm1, %xmm0
	movaps	%xmm0, -16(%rdi)
	cmpq	%r9, %rcx
	jne	.L353
	leaq	w.2(%rip), %rdi
	leaq	2608(%rsp), %rcx
	leaq	144(%rdi,%r10), %r9
	leaq	2616(%rsp), %r10
	addq	%r11, %r9
	addq	16(%rsp), %r9
	.p2align 5
	.p2align 4
	.p2align 3
.L354:
	movzbl	(%r9), %edi
	addq	$1, %rcx
	addq	$1, %r9
	xorl	$85, %edi
	movb	%dil, 143(%rcx)
	cmpq	%r10, %rcx
	jne	.L354
	pxor	%xmm1, %xmm1
	pcmpeqd	%xmm14, %xmm14
	movdqa	.LC10(%rip), %xmm5
	leaq	2752(%rsp), %rdi
	movdqa	%xmm1, %xmm2
	pxor	%xmm13, %xmm13
	pxor	%xmm8, %xmm8
	movaps	%xmm15, 16(%rsp)
	leaq	2608(%rsp), %rcx
	psrld	$31, %xmm14
	.p2align 4
	.p2align 3
.L355:
	movdqa	(%rcx), %xmm0
	addq	$16, %rcx
	movdqa	%xmm0, %xmm4
	punpckhbw	%xmm13, %xmm0
	punpcklbw	%xmm13, %xmm4
	movdqa	%xmm0, %xmm3
	punpckhwd	%xmm8, %xmm0
	movdqa	%xmm4, %xmm6
	punpcklwd	%xmm8, %xmm3
	punpckhwd	%xmm8, %xmm4
	punpcklwd	%xmm8, %xmm6
	movdqa	%xmm3, %xmm15
	movdqa	%xmm6, %xmm7
	paddd	%xmm0, %xmm15
	paddd	%xmm4, %xmm7
	paddd	%xmm15, %xmm7
	movdqa	%xmm5, %xmm15
	paddd	%xmm12, %xmm15
	paddd	%xmm7, %xmm1
	movdqa	%xmm15, %xmm7
	psrlq	$32, %xmm15
	pmuludq	%xmm0, %xmm7
	psrlq	$32, %xmm0
	pmuludq	%xmm15, %xmm0
	movdqa	%xmm5, %xmm15
	paddd	%xmm11, %xmm15
	pshufd	$8, %xmm7, %xmm7
	pshufd	$8, %xmm0, %xmm0
	punpckldq	%xmm0, %xmm7
	movdqa	%xmm15, %xmm0
	pmuludq	%xmm3, %xmm0
	psrlq	$32, %xmm15
	psrlq	$32, %xmm3
	pmuludq	%xmm15, %xmm3
	pshufd	$8, %xmm0, %xmm0
	pshufd	$8, %xmm3, %xmm3
	punpckldq	%xmm3, %xmm0
	paddd	%xmm7, %xmm0
	movdqa	%xmm5, %xmm7
	paddd	%xmm10, %xmm7
	movdqa	%xmm7, %xmm3
	psrlq	$32, %xmm7
	pmuludq	%xmm4, %xmm3
	psrlq	$32, %xmm4
	pmuludq	%xmm7, %xmm4
	movdqa	%xmm5, %xmm7
	paddd	%xmm9, %xmm5
	paddd	%xmm14, %xmm7
	pshufd	$8, %xmm3, %xmm3
	pshufd	$8, %xmm4, %xmm4
	punpckldq	%xmm4, %xmm3
	movdqa	%xmm7, %xmm4
	pmuludq	%xmm6, %xmm4
	psrlq	$32, %xmm7
	psrlq	$32, %xmm6
	pmuludq	%xmm7, %xmm6
	pshufd	$8, %xmm4, %xmm4
	pshufd	$8, %xmm6, %xmm6
	punpckldq	%xmm6, %xmm4
	paddd	%xmm4, %xmm3
	paddd	%xmm3, %xmm0
	paddd	%xmm0, %xmm2
	cmpq	%rdi, %rcx
	jne	.L355
	movdqa	%xmm1, %xmm0
	movdqa	16(%rsp), %xmm15
	movl	$144, %r10d
	psrldq	$8, %xmm0
	paddd	%xmm0, %xmm1
	movdqa	%xmm1, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm1
	movdqa	%xmm2, %xmm0
	psrldq	$8, %xmm0
	movd	%xmm1, %ecx
	paddd	%xmm0, %xmm2
	movdqa	%xmm2, %xmm0
	psrldq	$4, %xmm0
	paddd	%xmm0, %xmm2
	movd	%xmm2, %edi
	.p2align 6
	.p2align 4
	.p2align 3
.L356:
	movzbl	144(%rax), %r9d
	addl	$1, %r10d
	addq	$1, %rax
	addl	%r9d, %ecx
	imull	%r10d, %r9d
	addl	%r9d, %edi
	cmpl	$152, %r10d
	jne	.L356
	jmp	.L352
.L398:
	movl	$1, %eax
	jmp	.L344
.L401:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE61:
	.size	cert_round.constprop.0, .-cert_round.constprop.0
	.p2align 4
	.type	sqw_init, @function
sqw_init:
.LFB42:
	.cfi_startproc
	movl	$152920, %edx
	xorl	%esi, %esi
	jmp	memset@PLT
	.cfi_endproc
.LFE42:
	.size	sqw_init, .-sqw_init
	.p2align 4
	.type	sqw_hash, @function
sqw_hash:
.LFB43:
	.cfi_startproc
	leaq	152(%rdi), %rcx
	movabsq	$-7046029254386353131, %rax
	movabsq	$1099511628211, %rdx
	.p2align 4
	.p2align 4
	.p2align 3
.L406:
	xorq	(%rdi), %rax
	addq	$8, %rdi
	imulq	%rdx, %rax
	cmpq	%rdi, %rcx
	jne	.L406
	movq	%rax, %rdx
	shrq	$29, %rdx
	xorq	%rax, %rdx
	movabsq	$-4658895280553007687, %rax
	imulq	%rax, %rdx
	movq	%rdx, %rax
	shrq	$32, %rax
	xorq	%rdx, %rax
	ret
	.cfi_endproc
.LFE43:
	.size	sqw_hash, .-sqw_hash
	.p2align 4
	.type	sqw_ref_ok, @function
sqw_ref_ok:
.LFB44:
	.cfi_startproc
	movzwl	%di, %eax
	shrl	$16, %edi
	addl	%edi, %eax
	cmpl	$65535, %eax
	sete	%al
	movzbl	%al, %eax
	ret
	.cfi_endproc
.LFE44:
	.size	sqw_ref_ok, .-sqw_ref_ok
	.p2align 4
	.type	sqw_ref_inc, @function
sqw_ref_inc:
.LFB45:
	.cfi_startproc
	movzwl	%di, %edi
	addl	$1, %edi
	movl	%edi, %eax
	notl	%eax
	sall	$16, %eax
	orl	%edi, %eax
	ret
	.cfi_endproc
.LFE45:
	.size	sqw_ref_inc, .-sqw_ref_inc
	.p2align 4
	.type	sqw_ref_one, @function
sqw_ref_one:
.LFB46:
	.cfi_startproc
	movl	$-131071, %eax
	ret
	.cfi_endproc
.LFE46:
	.size	sqw_ref_one, .-sqw_ref_one
	.p2align 4
	.type	sqw_alloc, @function
sqw_alloc:
.LFB47:
	.cfi_startproc
	pushq	%r15
	.cfi_def_cfa_offset 16
	.cfi_offset 15, -16
	movl	%esi, %r8d
	pcmpeqd	%xmm2, %xmm2
	pushq	%r14
	.cfi_def_cfa_offset 24
	.cfi_offset 14, -24
	psrlw	$8, %xmm2
	pushq	%r13
	.cfi_def_cfa_offset 32
	.cfi_offset 13, -32
	pushq	%r12
	.cfi_def_cfa_offset 40
	.cfi_offset 12, -40
	movslq	%edx, %r12
	movl	%r12d, %ecx
	pushq	%rbp
	.cfi_def_cfa_offset 48
	.cfi_offset 6, -48
	movq	%rdi, %rbp
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	sall	$4, %ecx
	movl	$4, %ebx
	movd	%ebx, %xmm8
	addl	%r12d, %ecx
	movl	$8, %ebx
	movd	%ebx, %xmm7
	movd	%ecx, %xmm3
	movl	$12, %ebx
	pshufd	$0, %xmm8, %xmm8
	subq	$184, %rsp
	.cfi_def_cfa_offset 240
	movd	%ebx, %xmm6
	punpcklbw	%xmm3, %xmm3
	movl	$-1515870811, %ebx
	leaq	16(%rsp), %rsi
	movd	%ebx, %xmm5
	punpcklwd	%xmm3, %xmm3
	movl	$16, %ebx
	movq	%fs:40, %rax
	movq	%rax, 168(%rsp)
	xorl	%eax, %eax
	movdqa	.LC10(%rip), %xmm1
	movq	%rsi, %rdi
	movq	%rsi, %rax
	movd	%ebx, %xmm4
	pshufd	$0, %xmm3, %xmm3
	pshufd	$0, %xmm7, %xmm7
	leaq	160(%rsp), %rdx
	pshufd	$0, %xmm6, %xmm6
	pshufd	$0, %xmm5, %xmm5
	pshufd	$0, %xmm4, %xmm4
	.p2align 4
	.p2align 3
.L412:
	movdqa	%xmm1, %xmm10
	movdqa	%xmm1, %xmm9
	movdqa	%xmm1, %xmm0
	addq	$16, %rax
	paddd	%xmm8, %xmm10
	movdqa	%xmm1, %xmm11
	punpcklwd	%xmm10, %xmm9
	punpckhwd	%xmm10, %xmm0
	paddd	%xmm6, %xmm11
	movdqa	%xmm9, %xmm10
	punpcklwd	%xmm0, %xmm9
	punpckhwd	%xmm0, %xmm10
	movdqa	%xmm1, %xmm0
	paddd	%xmm4, %xmm1
	paddd	%xmm7, %xmm0
	punpcklwd	%xmm10, %xmm9
	movdqa	%xmm0, %xmm10
	punpcklwd	%xmm11, %xmm0
	pand	%xmm2, %xmm9
	punpckhwd	%xmm11, %xmm10
	movdqa	%xmm0, %xmm11
	punpckhwd	%xmm10, %xmm11
	punpcklwd	%xmm10, %xmm0
	punpcklwd	%xmm11, %xmm0
	pand	%xmm2, %xmm0
	packuswb	%xmm0, %xmm9
	movdqa	%xmm9, %xmm0
	paddb	%xmm9, %xmm0
	paddb	%xmm9, %xmm0
	paddb	%xmm0, %xmm0
	paddb	%xmm0, %xmm0
	paddb	%xmm0, %xmm0
	psubb	%xmm9, %xmm0
	paddb	%xmm0, %xmm0
	paddb	%xmm0, %xmm0
	psubb	%xmm9, %xmm0
	paddb	%xmm3, %xmm0
	pxor	%xmm5, %xmm0
	movaps	%xmm0, -16(%rax)
	cmpq	%rdx, %rax
	jne	.L412
	addl	$48, %ecx
	leaq	8(%rsi), %rax
	movq	%rsi, %rdx
	.p2align 5
	.p2align 4
	.p2align 3
.L413:
	movl	%ecx, %r9d
	addq	$1, %rdx
	addl	$91, %ecx
	xorl	$-91, %r9d
	movb	%r9b, 143(%rdx)
	cmpq	%rax, %rdx
	jne	.L413
	leaq	152(%rsi), %r9
	movabsq	$-7046029254386353131, %rdx
	movabsq	$1099511628211, %rcx
	jmp	.L414
	.p2align 5
	.p2align 4,,10
	.p2align 3
.L429:
	addq	$8, %rax
.L414:
	xorq	(%rdi), %rdx
	movq	%rax, %rdi
	imulq	%rcx, %rdx
	cmpq	%r9, %rax
	jne	.L429
	movq	%rdx, %rax
	movq	%rdx, %rbx
	shrq	$29, %rax
	xorq	%rax, %rbx
	movabsq	$-4658895280553007687, %rax
	imulq	%rax, %rbx
	movq	%rbx, %rax
	shrq	$32, %rax
	xorq	%rax, %rbx
	movq	%rbx, %r14
	andl	$4095, %r14d
	salq	$4, %r14
	addq	%rbp, %r14
	cmpb	$0, 86346(%r14)
	je	.L415
	cmpq	%rbx, 86336(%r14)
	je	.L430
.L415:
	andl	$31, %r8d
	leaq	SQB_SCATLT(%rip), %rax
	movl	(%rax,%r8,4), %eax
	leal	8(%rax), %edx
	.p2align 5
	.p2align 4
	.p2align 3
.L418:
	movl	%eax, %r13d
	movl	%eax, %r15d
	andl	$7, %r13d
	andl	$7, %r15d
	cmpl	$31, 86272(%rbp,%r13,4)
	jle	.L417
	addl	$1, %eax
	cmpl	%eax, %edx
	jne	.L418
.L419:
	movl	$-1, %eax
.L411:
	movq	168(%rsp), %rdx
	subq	%fs:40, %rdx
	jne	.L431
	addq	$184, %rsp
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
.L417:
	.cfi_restore_state
	leaq	0(%rbp,%r13,4), %r8
	movl	%r12d, %ecx
	movl	%r15d, %esi
	movq	%rbp, %rdi
	movl	86272(%r8), %edx
	movq	%r8, (%rsp)
	movl	%edx, 8(%rsp)
	call	sqb_proofread_commit
	movl	8(%rsp), %edx
	movq	(%rsp), %r8
	testl	%eax, %eax
	jne	.L419
	movslq	%edx, %rcx
	salq	$5, %r13
	addl	$1, 86272(%r8)
	leaq	37968(%rcx,%r13), %rcx
	addl	$1, 86304(%rbp)
	movl	$-131071, 0(%rbp,%rcx,4)
	leaq	sqw_item_slot_b(%rip), %rcx
	movl	%r15d, (%rcx,%r12,4)
	leaq	sqw_item_slot_g(%rip), %rcx
	addq	$1, 152896(%rbp)
	addq	$1, 152912(%rbp)
	movl	%edx, (%rcx,%r12,4)
	movq	%rbx, 86336(%r14)
	movb	%r15b, 86344(%r14)
	movb	%dl, 86345(%r14)
	movb	$1, 86346(%r14)
	jmp	.L411
.L430:
	movzbl	86344(%r14), %r9d
	movzbl	86345(%r14), %ecx
	movzbl	%r9b, %r13d
	movzbl	%cl, %r15d
	imulq	$336, %r15, %rdi
	imulq	$10752, %r13, %r10
	addq	%r10, %rdi
	cmpl	$-559063315, 164(%rbp,%rdi)
	je	.L415
	imulq	$336, %r15, %rax
	movl	$152, %edx
	movl	%r8d, 8(%rsp)
	movl	%ecx, (%rsp)
	movl	%r9d, 12(%rsp)
	leaq	(%r10,%rax), %rdi
	addq	%rbp, %rdi
	call	memcmp@PLT
	movl	8(%rsp), %r8d
	movl	(%rsp), %ecx
	testl	%eax, %eax
	movl	12(%rsp), %r9d
	jne	.L415
	salq	$5, %r13
	movdqu	152896(%rbp), %xmm4
	leaq	37968(%r15,%r13), %rdi
	movzwl	0(%rbp,%rdi,4), %esi
	addl	$1, %esi
	movl	%esi, %edx
	notl	%edx
	sall	$16, %edx
	orl	%esi, %edx
	movl	$1, %esi
	movq	%rsi, %xmm0
	movl	%edx, 0(%rbp,%rdi,4)
	leaq	sqw_item_slot_b(%rip), %rdx
	punpcklqdq	%xmm0, %xmm0
	movl	%r9d, (%rdx,%r12,4)
	leaq	sqw_item_slot_g(%rip), %rdx
	paddq	%xmm4, %xmm0
	movl	%ecx, (%rdx,%r12,4)
	movups	%xmm0, 152896(%rbp)
	jmp	.L411
.L431:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE47:
	.size	sqw_alloc, .-sqw_alloc
	.p2align 4
	.type	sqw_ref_audit, @function
sqw_ref_audit:
.LFB48:
	.cfi_startproc
	leaq	0(,%rdi,4), %rax
	movq	%rdi, %r8
	pushq	%rbx
	.cfi_def_cfa_offset 16
	.cfi_offset 3, -16
	movq	%rdi, %r11
	movq	%rsi, %rbx
	leaq	86304(%rdi), %r10
	subq	%rax, %r8
	xorl	%r9d, %r9d
	leaq	86048(%rdi), %rsi
	xorl	%edi, %edi
	.p2align 4
	.p2align 3
.L433:
	leaq	-32(%rsi), %rax
	jmp	.L436
	.p2align 4,,10
	.p2align 3
.L441:
	addq	$1, %rdi
.L434:
	addq	$1, %rax
	cmpq	%rsi, %rax
	je	.L440
.L436:
	cmpb	$0, (%rax)
	je	.L434
	movl	-192192(%r8,%rax,4), %edx
	movzwl	%dx, %ecx
	shrl	$16, %edx
	addl	%ecx, %edx
	cmpl	$65535, %edx
	jne	.L441
	addq	$1, %rax
	addq	%rcx, %r9
	cmpq	%rsi, %rax
	jne	.L436
.L440:
	leaq	32(%rax), %rsi
	cmpq	%r10, %rsi
	jne	.L433
	xorl	%eax, %eax
	cmpq	%r9, 152896(%r11)
	sete	%al
	movl	%eax, (%rbx)
	movq	%rdi, %rax
	popq	%rbx
	.cfi_def_cfa_offset 8
	ret
	.cfi_endproc
.LFE48:
	.size	sqw_ref_audit, .-sqw_ref_audit
	.section	.rodata.str1.8
	.align 8
.LC30:
	.string	"SQWOR O1_recognition  %lld/%d = %.6f  expect=1.000000 counting (memoization exactness)\n"
	.align 8
.LC31:
	.string	"SQWOR O2_refpair_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n"
	.align 8
.LC32:
	.string	"SQWOR O3_payload_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n"
	.align 8
.LC33:
	.string	"SQWOR O3_payload_rep  %lld/%lld = %.6f  expect>=0.990 measurement [A]\n"
	.align 8
.LC34:
	.string	"SQWOR O4_syndrome_det %lld/%lld = %.6f  expect=1.000000 counting [A]\n"
	.align 8
.LC35:
	.string	"SQWOR O4_syndrome_rep %lld/%lld = %.6f  expect=1.000000 measurement [A]\n"
	.align 8
.LC36:
	.string	"SQWOR O5_closure      %lld unresolved [A]  expect=0\n"
	.align 8
.LC37:
	.string	"SQWOR O6_apoptosis    %lld [A]  expect=0 isolated\n"
	.align 8
.LC38:
	.string	"SQWOR O7_idx_failsafe %lld/%lld = %.6f  expect=1.000000 (poisoned cache never serves wrong content) [A isolated]\n"
	.align 8
.LC39:
	.string	"SQWOR auxB_det        %lld/%lld = %.6f  poisson tail (content classes)\n"
	.align 8
.LC40:
	.string	"SQWOR auxB_rep        %lld/%lld = %.6f  poisson tail\n"
	.align 8
.LC41:
	.string	"SQWOR auxB_tombs      %lld  tomb_refs %lld (amplification: %.2f logical items lost per tombstone)  auxB_coh_fail %lld  auxB_unresolved %lld\n"
	.section	.text.startup,"ax",@progbits
	.p2align 4
	.globl	main
	.type	main, @function
main:
.LFB52:
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
	subq	$536, %rsp
	.cfi_def_cfa_offset 592
	movq	%fs:40, %rax
	movq	%rax, 520(%rsp)
	xorl	%eax, %eax
	movl	$1500, (%rsp)
	cmpl	$1, %edi
	jle	.L443
	movq	8(%rsi), %rdi
	movl	$10, %edx
	xorl	%esi, %esi
	call	__isoc23_strtol@PLT
	movl	%eax, (%rsp)
.L443:
	movabsq	$-1100507917760583744, %rbx
	movl	$10, %eax
	movabsq	$-7723592293110652910, %rbp
	movabsq	$-4658895280553055330, %r12
	movabsq	$-7046029254386300356, %r13
	.p2align 5
	.p2align 4
	.p2align 3
.L444:
	movq	%r12, %rdx
	xorq	%r13, %rbp
	xorq	%r12, %rbx
	salq	$17, %rdx
	xorq	%rbp, %r12
	xorq	%rbx, %r13
	rorq	$19, %rbx
	xorq	%rdx, %rbp
	subl	$1, %eax
	jne	.L444
	leaq	stream.3(%rip), %r15
	movl	$4, %edi
	movdqa	.LC10(%rip), %xmm0
	movd	%edi, %xmm1
	leaq	512(%r15), %rsi
	movq	%r15, %rax
	pshufd	$0, %xmm1, %xmm1
	.p2align 4
	.p2align 4
	.p2align 3
.L445:
	movaps	%xmm0, (%rax)
	addq	$16, %rax
	paddd	%xmm1, %xmm0
	cmpq	%rsi, %rax
	jne	.L445
	leaq	508+stream.3(%rip), %rcx
	movl	$128, %edi
	.p2align 4
	.p2align 3
.L446:
	movq	%r12, %rdx
	leaq	(%rbx,%r13), %rax
	xorq	%r13, %rbp
	xorq	%r12, %rbx
	salq	$17, %rdx
	xorq	%rbp, %r12
	rolq	$17, %rax
	movl	(%rcx), %r9d
	xorq	%rdx, %rbp
	xorl	%edx, %edx
	movq	%rcx, %r8
	subq	$4, %rcx
	divl	%edi
	xorq	%rbx, %r13
	subl	$1, %edi
	rorq	$19, %rbx
	movl	(%r15,%rdx,4), %eax
	movl	%eax, 4(%rcx)
	movl	%r9d, (%r15,%rdx,4)
	cmpq	%rcx, %r15
	jne	.L446
	addq	$1020, %r8
	.p2align 6
	.p2align 4
	.p2align 3
.L447:
	leaq	(%rbx,%r13), %rax
	movq	%r12, %rdx
	xorq	%r13, %rbp
	xorq	%r12, %rbx
	rolq	$17, %rax
	salq	$17, %rdx
	addq	$4, %rsi
	xorq	%rbp, %r12
	andl	$127, %eax
	xorq	%rbx, %r13
	xorq	%rdx, %rbp
	rorq	$19, %rbx
	movl	%eax, -4(%rsi)
	cmpq	%r8, %rsi
	jne	.L447
	movl	$152920, %edx
	xorl	%esi, %esi
	leaq	w.2(%rip), %rdi
	xorl	%r14d, %r14d
	call	memset@PLT
	.p2align 4
	.p2align 3
.L448:
	movl	(%r15,%r14,4), %edx
	movl	%r14d, %esi
	leaq	w.2(%rip), %rdi
	addq	$1, %r14
	call	sqw_alloc
	cmpq	$256, %r14
	jne	.L448
	movl	$152920, %edx
	leaq	w.2(%rip), %rsi
	leaq	clean.1(%rip), %rdi
	call	memcpy@PLT
	leaq	clean.1(%rip), %rdi
	pxor	%xmm0, %xmm0
	call	verify_all_items.constprop.0
	movdqa	%xmm0, %xmm1
	movq	%rax, 88(%rsp)
	xorl	%eax, %eax
.L449:
	movl	%eax, %edx
	addl	$64, %eax
	movaps	%xmm1, 176(%rsp,%rdx)
	movaps	%xmm1, 192(%rsp,%rdx)
	movaps	%xmm1, 208(%rsp,%rdx)
	movaps	%xmm1, 224(%rsp,%rdx)
	cmpl	$128, %eax
	jb	.L449
	xorl	%r8d, %r8d
	movaps	%xmm1, 176(%rsp,%rax)
	movaps	%xmm1, 192(%rsp,%rax)
	movdqa	%xmm0, %xmm1
	movq	%r8, 208(%rsp,%rax)
	xorl	%eax, %eax
.L451:
	movl	%eax, %edx
	addl	$64, %eax
	movaps	%xmm1, 352(%rsp,%rdx)
	movaps	%xmm1, 368(%rsp,%rdx)
	movaps	%xmm1, 384(%rsp,%rdx)
	movaps	%xmm1, 400(%rsp,%rdx)
	cmpl	$128, %eax
	jb	.L451
	movl	(%rsp), %r14d
	xorl	%edi, %edi
	movaps	%xmm1, 352(%rsp,%rax)
	movq	%rdi, 384(%rsp,%rax)
	movaps	%xmm1, 368(%rsp,%rax)
	testl	%r14d, %r14d
	jle	.L453
	movdqa	%xmm0, %xmm1
	movdqa	%xmm0, %xmm2
	movdqa	%xmm0, %xmm3
	xorl	%r10d, %r10d
	xorl	%r9d, %r9d
	xorl	%r8d, %r8d
	xorl	%ecx, %ecx
	xorl	%r15d, %r15d
	.p2align 4
	.p2align 3
.L455:
	movl	%r15d, %edx
	movl	%r15d, %eax
	imulq	$613566757, %rdx, %rdx
	shrq	$32, %rdx
	subl	%edx, %eax
	shrl	%eax
	addl	%edx, %eax
	shrl	$2, %eax
	leal	0(,%rax,8), %edx
	subl	%eax, %edx
	movl	%r15d, %eax
	subl	%edx, %eax
	xorl	%edx, %edx
	cmpl	$2, %eax
	jle	.L454
	movl	$1, %edx
	cmpl	$3, %eax
	je	.L454
	xorl	%edx, %edx
	cmpl	$4, %eax
	setne	%dl
	addl	$2, %edx
.L454:
	movq	%rcx, 192(%rsp)
	movl	$1, %esi
	addl	$1, %r15d
	leaq	176(%rsp), %rcx
	leaq	144(%rsp), %rdi
	movq	%r13, 144(%rsp)
	movq	%r12, 152(%rsp)
	movq	%rbp, 160(%rsp)
	movq	%rbx, 168(%rsp)
	movq	%r8, 224(%rsp)
	movq	%r9, 304(%rsp)
	movq	%r10, 320(%rsp)
	movaps	%xmm0, 176(%rsp)
	movaps	%xmm3, 208(%rsp)
	movaps	%xmm2, 240(%rsp)
	movaps	%xmm1, 288(%rsp)
	call	cert_round.constprop.0
	movq	144(%rsp), %r13
	movq	152(%rsp), %r12
	movq	160(%rsp), %rbp
	movq	168(%rsp), %rbx
	movq	192(%rsp), %rcx
	movq	224(%rsp), %r8
	movdqa	176(%rsp), %xmm0
	movdqa	208(%rsp), %xmm3
	movq	304(%rsp), %r9
	movq	320(%rsp), %r10
	movdqa	240(%rsp), %xmm2
	movdqa	288(%rsp), %xmm1
	cmpl	%r15d, %r14d
	jne	.L455
	movl	(%rsp), %eax
	movhps	%xmm0, 8(%rsp)
	movq	%xmm0, 16(%rsp)
	movhps	%xmm3, 104(%rsp)
	movq	%xmm3, 80(%rsp)
	movhps	%xmm2, 48(%rsp)
	movq	%xmm2, 56(%rsp)
	movhps	%xmm1, 24(%rsp)
	movq	%xmm1, 40(%rsp)
	cmpl	$2, %eax
	jle	.L472
	movl	%eax, %r14d
	movl	$2863311531, %eax
	movq	%rbx, 112(%rsp)
	xorl	%edi, %edi
	imulq	%rax, %r14
	movq	112(%rsp), %rax
	movq	%rcx, 32(%rsp)
	xorl	%esi, %esi
	movq	%r8, 64(%rsp)
	xorl	%r11d, %r11d
	xorl	%r15d, %r15d
	xorl	%edx, %edx
	movq	%r9, 72(%rsp)
	xorl	%ebx, %ebx
	movq	%rdi, %rcx
	xorl	%r8d, %r8d
	shrq	$33, %r14
	movq	%r10, 96(%rsp)
	xorl	%r9d, %r9d
	xorl	%r10d, %r10d
	movq	%r14, (%rsp)
	xorl	%r14d, %r14d
	.p2align 4
	.p2align 3
.L457:
	movq	%rdx, 352(%rsp)
	movl	$-1, %edx
	addl	$1, %ebx
	movq	%rcx, 360(%rsp)
	leaq	352(%rsp), %rcx
	movq	%rsi, 384(%rsp)
	movl	$12, %esi
	movq	%rdi, 480(%rsp)
	leaq	144(%rsp), %rdi
	movq	%r13, 144(%rsp)
	movq	%r12, 152(%rsp)
	movq	%rbp, 160(%rsp)
	movq	%rax, 168(%rsp)
	movq	%r15, 392(%rsp)
	movq	%r11, 416(%rsp)
	movq	%r14, 424(%rsp)
	movq	%r8, 488(%rsp)
	movq	%r9, 496(%rsp)
	movq	%r10, 504(%rsp)
	call	cert_round.constprop.0
	movq	144(%rsp), %r13
	movq	152(%rsp), %r12
	movq	160(%rsp), %rbp
	movq	168(%rsp), %rax
	movq	352(%rsp), %rdx
	movq	360(%rsp), %rcx
	movq	384(%rsp), %rsi
	movq	392(%rsp), %r15
	movq	416(%rsp), %r11
	movq	424(%rsp), %r14
	movq	480(%rsp), %rdi
	movq	488(%rsp), %r8
	movq	496(%rsp), %r9
	movq	504(%rsp), %r10
	cmpl	%ebx, (%rsp)
	jg	.L457
	movq	%rdi, (%rsp)
	movq	%rcx, %rbx
	movq	32(%rsp), %rcx
	movq	%rdx, %rbp
	movq	%r8, 32(%rsp)
	movq	64(%rsp), %r8
	movq	%rsi, %r13
	movq	%r9, 64(%rsp)
	movq	72(%rsp), %r9
	movq	%r10, 72(%rsp)
	movq	96(%rsp), %r10
.L456:
	movq	88(%rsp), %rsi
	pxor	%xmm0, %xmm0
	movl	$256, %edx
	leaq	.LC30(%rip), %rdi
	movl	$1, %eax
	movq	%r11, 136(%rsp)
	cvtsi2sdq	%rsi, %xmm0
	mulsd	.LC29(%rip), %xmm0
	movq	%r9, 120(%rsp)
	movq	%r10, 128(%rsp)
	movq	%r8, 112(%rsp)
	movq	%rcx, 96(%rsp)
	call	printf@PLT
	movq	96(%rsp), %rcx
	movq	112(%rsp), %r8
	pxor	%xmm0, %xmm0
	movq	120(%rsp), %r9
	movq	128(%rsp), %r10
	testq	%rcx, %rcx
	movq	136(%rsp), %r11
	je	.L459
	pxor	%xmm0, %xmm0
	pxor	%xmm1, %xmm1
	cvtsi2sdq	%r8, %xmm0
	cvtsi2sdq	%rcx, %xmm1
	divsd	%xmm1, %xmm0
.L459:
	movq	%rcx, %rdx
	movq	%r8, %rsi
	movl	$1, %eax
	movq	%r11, 112(%rsp)
	leaq	.LC31(%rip), %rdi
	movq	%r10, 96(%rsp)
	movq	%r9, 88(%rsp)
	call	printf@PLT
	cmpq	$0, 16(%rsp)
	movq	88(%rsp), %r9
	movq	96(%rsp), %r10
	movq	112(%rsp), %r11
	je	.L458
	movq	80(%rsp), %rsi
	pxor	%xmm0, %xmm0
	pxor	%xmm1, %xmm1
	cvtsi2sdq	16(%rsp), %xmm1
	movq	16(%rsp), %rdx
	leaq	.LC32(%rip), %rdi
	movl	$1, %eax
	movsd	%xmm1, 80(%rsp)
	cvtsi2sdq	%rsi, %xmm0
	divsd	%xmm1, %xmm0
	call	printf@PLT
	movq	88(%rsp), %r9
	movq	96(%rsp), %r10
	pxor	%xmm0, %xmm0
	movq	112(%rsp), %r11
	cvtsi2sdq	56(%rsp), %xmm0
	divsd	80(%rsp), %xmm0
.L460:
	movq	16(%rsp), %rdx
	movq	56(%rsp), %rsi
	movl	$1, %eax
	leaq	.LC33(%rip), %rdi
	movq	%r11, 96(%rsp)
	movq	%r10, 88(%rsp)
	movq	%r9, 80(%rsp)
	call	printf@PLT
	cmpq	$0, 8(%rsp)
	movq	80(%rsp), %r9
	movq	88(%rsp), %r10
	movq	96(%rsp), %r11
	jne	.L461
	movq	104(%rsp), %rsi
	pxor	%xmm0, %xmm0
	xorl	%edx, %edx
	movl	$1, %eax
	leaq	.LC34(%rip), %rdi
	movq	%r11, 80(%rsp)
	movq	%r10, 56(%rsp)
	movq	%r9, 16(%rsp)
	call	printf@PLT
	movq	16(%rsp), %r9
	movq	56(%rsp), %r10
	pxor	%xmm0, %xmm0
	movq	80(%rsp), %r11
.L462:
	movq	8(%rsp), %rdx
	movq	48(%rsp), %rsi
	movl	$1, %eax
	leaq	.LC35(%rip), %rdi
	movq	%r11, 80(%rsp)
	movq	%r10, 56(%rsp)
	movq	%r9, 16(%rsp)
	call	printf@PLT
	movq	56(%rsp), %rsi
	leaq	.LC36(%rip), %rdi
	xorl	%eax, %eax
	call	printf@PLT
	movq	16(%rsp), %rsi
	xorl	%eax, %eax
	leaq	.LC37(%rip), %rdi
	call	printf@PLT
	movq	24(%rsp), %rax
	movq	80(%rsp), %r11
	pxor	%xmm0, %xmm0
	testq	%rax, %rax
	je	.L463
	pxor	%xmm1, %xmm1
	pxor	%xmm0, %xmm0
	cvtsi2sdq	40(%rsp), %xmm0
	cvtsi2sdq	%rax, %xmm1
	divsd	%xmm1, %xmm0
.L463:
	movq	40(%rsp), %rsi
	movq	24(%rsp), %rdx
	movl	$1, %eax
	leaq	.LC38(%rip), %rdi
	movq	%r11, 8(%rsp)
	call	printf@PLT
	addq	8(%rsp), %r14
	leaq	0(%r13,%r15), %rsi
	addq	%rbp, %rbx
	jne	.L464
	pxor	%xmm0, %xmm0
	xorl	%edx, %edx
	movl	$1, %eax
	leaq	.LC39(%rip), %rdi
	call	printf@PLT
	pxor	%xmm0, %xmm0
.L465:
	movq	%rbx, %rdx
	movq	%r14, %rsi
	movl	$1, %eax
	leaq	.LC40(%rip), %rdi
	call	printf@PLT
	movq	(%rsp), %rax
	pxor	%xmm0, %xmm0
	testq	%rax, %rax
	je	.L466
	pxor	%xmm1, %xmm1
	pxor	%xmm0, %xmm0
	cvtsi2sdq	32(%rsp), %xmm0
	cvtsi2sdq	%rax, %xmm1
	divsd	%xmm1, %xmm0
.L466:
	movq	64(%rsp), %r8
	movq	72(%rsp), %rcx
	movl	$1, %eax
	leaq	.LC41(%rip), %rdi
	movq	32(%rsp), %rdx
	movq	(%rsp), %rsi
	call	printf@PLT
	movq	520(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L493
	addq	$536, %rsp
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
.L464:
	.cfi_restore_state
	pxor	%xmm1, %xmm1
	pxor	%xmm0, %xmm0
	movq	%rbx, %rdx
	movl	$1, %eax
	cvtsi2sdq	%rbx, %xmm1
	cvtsi2sdq	%rsi, %xmm0
	divsd	%xmm1, %xmm0
	leaq	.LC39(%rip), %rdi
	movsd	%xmm1, 8(%rsp)
	call	printf@PLT
	pxor	%xmm0, %xmm0
	cvtsi2sdq	%r14, %xmm0
	divsd	8(%rsp), %xmm0
	jmp	.L465
.L461:
	movq	8(%rsp), %rdx
	movq	104(%rsp), %rsi
	pxor	%xmm1, %xmm1
	pxor	%xmm0, %xmm0
	leaq	.LC34(%rip), %rdi
	movl	$1, %eax
	movq	%r11, 88(%rsp)
	cvtsi2sdq	%rdx, %xmm1
	cvtsi2sdq	%rsi, %xmm0
	divsd	%xmm1, %xmm0
	movq	%r10, 80(%rsp)
	movq	%r9, 56(%rsp)
	movsd	%xmm1, 16(%rsp)
	call	printf@PLT
	pxor	%xmm0, %xmm0
	movq	88(%rsp), %r11
	cvtsi2sdq	48(%rsp), %xmm0
	movq	80(%rsp), %r10
	movq	56(%rsp), %r9
	divsd	16(%rsp), %xmm0
	jmp	.L462
.L453:
	movq	88(%rsp), %rsi
	pxor	%xmm0, %xmm0
	movl	$256, %edx
	xorl	%ebx, %ebx
	leaq	.LC30(%rip), %rdi
	xorl	%r14d, %r14d
	xorl	%r15d, %r15d
	xorl	%r13d, %r13d
	cvtsi2sdq	%rsi, %xmm0
	mulsd	.LC29(%rip), %xmm0
	movl	$1, %eax
	xorl	%ebp, %ebp
	call	printf@PLT
	xorl	%esi, %esi
	pxor	%xmm0, %xmm0
	xorl	%edx, %edx
	leaq	.LC31(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	xorl	%ecx, %ecx
	xorl	%esi, %esi
	xorl	%r11d, %r11d
	movq	%rcx, 80(%rsp)
	xorl	%r10d, %r10d
	xorl	%r9d, %r9d
	movq	%rcx, 8(%rsp)
	movq	%rcx, 72(%rsp)
	movq	%rcx, 64(%rsp)
	movq	%rcx, 32(%rsp)
	movq	%rcx, (%rsp)
	movq	%rsi, 24(%rsp)
	movq	%rsi, 40(%rsp)
	movq	%rsi, 48(%rsp)
	movq	%rsi, 56(%rsp)
	movq	%rsi, 104(%rsp)
.L458:
	movq	80(%rsp), %rsi
	pxor	%xmm0, %xmm0
	xorl	%edx, %edx
	movl	$1, %eax
	leaq	.LC32(%rip), %rdi
	movq	%r11, 112(%rsp)
	movq	%r10, 96(%rsp)
	movq	%r9, 88(%rsp)
	call	printf@PLT
	xorl	%eax, %eax
	movq	112(%rsp), %r11
	pxor	%xmm0, %xmm0
	movq	96(%rsp), %r10
	movq	88(%rsp), %r9
	movq	%rax, 16(%rsp)
	jmp	.L460
.L472:
	xorl	%edx, %edx
	xorl	%r14d, %r14d
	xorl	%r11d, %r11d
	xorl	%r15d, %r15d
	movq	%rdx, 72(%rsp)
	xorl	%r13d, %r13d
	xorl	%ebx, %ebx
	xorl	%ebp, %ebp
	movq	%rdx, 64(%rsp)
	movq	%rdx, 32(%rsp)
	movq	%rdx, (%rsp)
	jmp	.L456
.L493:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE52:
	.size	main, .-main
	.local	action.0
	.comm	action.0,256,32
	.local	clean.1
	.comm	clean.1,152920,32
	.local	w.2
	.comm	w.2,152920,32
	.local	stream.3
	.comm	stream.3,1024,32
	.local	sqw_item_slot_g
	.comm	sqw_item_slot_g,4096,32
	.local	sqw_item_slot_b
	.comm	sqw_item_slot_b,4096,32
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
	.section	.rodata.cst8,"aM",@progbits,8
	.align 8
.LC1:
	.long	-400107883
	.long	1041313291
	.align 8
.LC2:
	.long	0
	.long	1017118720
	.align 8
.LC5:
	.long	0
	.long	1079574528
	.section	.rodata.cst16,"aM",@progbits,16
	.align 16
.LC10:
	.long	0
	.long	1
	.long	2
	.long	3
	.align 16
.LC16:
	.long	16
	.long	16
	.long	16
	.long	16
	.align 16
.LC18:
	.long	9
	.long	9
	.long	9
	.long	9
	.align 16
.LC19:
	.long	13
	.long	13
	.long	13
	.long	13
	.align 16
.LC21:
	.long	5
	.long	5
	.long	5
	.long	5
	.align 16
.LC23:
	.long	1431655765
	.long	1431655765
	.long	1431655765
	.long	1431655765
	.section	.rodata.cst8
	.align 8
.LC25:
	.long	1717986918
	.long	1072064102
	.align 8
.LC26:
	.long	0
	.long	1071644672
	.align 8
.LC27:
	.long	-687194767
	.long	1072001187
	.align 8
.LC29:
	.long	0
	.long	1064304640
	.ident	"GCC: (GNU) 16.1.1 20260625"
	.section	.note.GNU-stack,"",@progbits

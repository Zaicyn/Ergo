	.file	"v8_slice.c"
	.text
	.p2align 4
	.type	__FLOAT_BITS, @function
__FLOAT_BITS:
.LFB0:
	.cfi_startproc
	vmovd	%xmm0, %eax
	ret
	.cfi_endproc
.LFE0:
	.size	__FLOAT_BITS, .-__FLOAT_BITS
	.p2align 4
	.type	__DOUBLE_BITS, @function
__DOUBLE_BITS:
.LFB1:
	.cfi_startproc
	vmovq	%xmm0, %rax
	ret
	.cfi_endproc
.LFE1:
	.size	__DOUBLE_BITS, .-__DOUBLE_BITS
	.p2align 4
	.type	__islessf, @function
__islessf:
.LFB2:
	.cfi_startproc
	vmovd	%xmm0, %eax
	andl	$2147483647, %eax
	cmpl	$2139095040, %eax
	ja	.L7
	vmovd	%xmm1, %eax
	andl	$2147483647, %eax
	cmpl	$2139095040, %eax
	ja	.L7
	xorl	%eax, %eax
	vcomiss	%xmm0, %xmm1
	seta	%al
	ret
	.p2align 4,,10
	.p2align 3
.L7:
	xorl	%eax, %eax
	ret
	.cfi_endproc
.LFE2:
	.size	__islessf, .-__islessf
	.p2align 4
	.type	__isless, @function
__isless:
.LFB3:
	.cfi_startproc
	movabsq	$9223372036854775807, %rax
	vmovq	%xmm0, %rcx
	movabsq	$9218868437227405312, %rdx
	andq	%rcx, %rax
	cmpq	%rax, %rdx
	jb	.L11
	movabsq	$9223372036854775807, %rax
	vmovq	%xmm1, %rsi
	andq	%rsi, %rax
	cmpq	%rax, %rdx
	jb	.L11
	xorl	%eax, %eax
	vcomisd	%xmm0, %xmm1
	seta	%al
	ret
	.p2align 4,,10
	.p2align 3
.L11:
	xorl	%eax, %eax
	ret
	.cfi_endproc
.LFE3:
	.size	__isless, .-__isless
	.p2align 4
	.type	__islessl, @function
__islessl:
.LFB4:
	.cfi_startproc
	subq	$8, %rsp
	.cfi_def_cfa_offset 16
	pushq	24(%rsp)
	.cfi_def_cfa_offset 24
	pushq	24(%rsp)
	.cfi_def_cfa_offset 32
	call	__fpclassifyl@PLT
	popq	%rsi
	.cfi_def_cfa_offset 24
	popq	%rdi
	.cfi_def_cfa_offset 16
	testl	%eax, %eax
	jne	.L21
.L12:
	addq	$8, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L21:
	.cfi_restore_state
	pushq	40(%rsp)
	.cfi_def_cfa_offset 24
	pushq	40(%rsp)
	.cfi_def_cfa_offset 32
	call	__fpclassifyl@PLT
	popq	%rdx
	.cfi_def_cfa_offset 24
	popq	%rcx
	.cfi_def_cfa_offset 16
	testl	%eax, %eax
	je	.L12
	fldt	16(%rsp)
	fldt	32(%rsp)
	xorl	%eax, %eax
	fcomip	%st(1), %st
	fstp	%st(0)
	seta	%al
	addq	$8, %rsp
	.cfi_def_cfa_offset 8
	ret
	.cfi_endproc
.LFE4:
	.size	__islessl, .-__islessl
	.p2align 4
	.type	__islessequalf, @function
__islessequalf:
.LFB5:
	.cfi_startproc
	vmovd	%xmm0, %eax
	andl	$2147483647, %eax
	cmpl	$2139095040, %eax
	ja	.L25
	vmovd	%xmm1, %eax
	andl	$2147483647, %eax
	cmpl	$2139095040, %eax
	ja	.L25
	xorl	%eax, %eax
	vcomiss	%xmm0, %xmm1
	setnb	%al
	ret
	.p2align 4,,10
	.p2align 3
.L25:
	xorl	%eax, %eax
	ret
	.cfi_endproc
.LFE5:
	.size	__islessequalf, .-__islessequalf
	.p2align 4
	.type	__islessequal, @function
__islessequal:
.LFB6:
	.cfi_startproc
	movabsq	$9223372036854775807, %rax
	vmovq	%xmm0, %rcx
	movabsq	$9218868437227405312, %rdx
	andq	%rcx, %rax
	cmpq	%rax, %rdx
	jb	.L29
	movabsq	$9223372036854775807, %rax
	vmovq	%xmm1, %rsi
	andq	%rsi, %rax
	cmpq	%rax, %rdx
	jb	.L29
	xorl	%eax, %eax
	vcomisd	%xmm0, %xmm1
	setnb	%al
	ret
	.p2align 4,,10
	.p2align 3
.L29:
	xorl	%eax, %eax
	ret
	.cfi_endproc
.LFE6:
	.size	__islessequal, .-__islessequal
	.p2align 4
	.type	__islessequall, @function
__islessequall:
.LFB7:
	.cfi_startproc
	subq	$8, %rsp
	.cfi_def_cfa_offset 16
	pushq	24(%rsp)
	.cfi_def_cfa_offset 24
	pushq	24(%rsp)
	.cfi_def_cfa_offset 32
	call	__fpclassifyl@PLT
	popq	%rsi
	.cfi_def_cfa_offset 24
	popq	%rdi
	.cfi_def_cfa_offset 16
	testl	%eax, %eax
	jne	.L39
.L30:
	addq	$8, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L39:
	.cfi_restore_state
	pushq	40(%rsp)
	.cfi_def_cfa_offset 24
	pushq	40(%rsp)
	.cfi_def_cfa_offset 32
	call	__fpclassifyl@PLT
	popq	%rdx
	.cfi_def_cfa_offset 24
	popq	%rcx
	.cfi_def_cfa_offset 16
	testl	%eax, %eax
	je	.L30
	fldt	16(%rsp)
	fldt	32(%rsp)
	xorl	%eax, %eax
	fcomip	%st(1), %st
	fstp	%st(0)
	setnb	%al
	addq	$8, %rsp
	.cfi_def_cfa_offset 8
	ret
	.cfi_endproc
.LFE7:
	.size	__islessequall, .-__islessequall
	.p2align 4
	.type	__islessgreaterf, @function
__islessgreaterf:
.LFB8:
	.cfi_startproc
	vmovd	%xmm0, %edx
	xorl	%eax, %eax
	andl	$2147483647, %edx
	cmpl	$2139095040, %edx
	ja	.L40
	vmovd	%xmm1, %eax
	movl	$1, %ecx
	andl	$2147483647, %eax
	cmpl	$2139095040, %eax
	setbe	%al
	vucomiss	%xmm1, %xmm0
	setp	%dl
	cmovne	%ecx, %edx
	andl	%edx, %eax
	movzbl	%al, %eax
.L40:
	ret
	.cfi_endproc
.LFE8:
	.size	__islessgreaterf, .-__islessgreaterf
	.p2align 4
	.type	__islessgreater, @function
__islessgreater:
.LFB9:
	.cfi_startproc
	movabsq	$9223372036854775807, %rcx
	vmovq	%xmm0, %rax
	movabsq	$9218868437227405312, %rdx
	andq	%rax, %rcx
	xorl	%eax, %eax
	cmpq	%rcx, %rdx
	jb	.L43
	movabsq	$9223372036854775807, %rax
	vmovq	%xmm1, %rsi
	movl	$1, %ecx
	andq	%rsi, %rax
	cmpq	%rax, %rdx
	setnb	%al
	vucomisd	%xmm1, %xmm0
	setp	%dl
	cmovne	%ecx, %edx
	andl	%edx, %eax
	movzbl	%al, %eax
.L43:
	ret
	.cfi_endproc
.LFE9:
	.size	__islessgreater, .-__islessgreater
	.p2align 4
	.type	__islessgreaterl, @function
__islessgreaterl:
.LFB10:
	.cfi_startproc
	subq	$8, %rsp
	.cfi_def_cfa_offset 16
	pushq	24(%rsp)
	.cfi_def_cfa_offset 24
	pushq	24(%rsp)
	.cfi_def_cfa_offset 32
	call	__fpclassifyl@PLT
	popq	%rsi
	.cfi_def_cfa_offset 24
	popq	%rdi
	.cfi_def_cfa_offset 16
	testl	%eax, %eax
	jne	.L52
	addq	$8, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L52:
	.cfi_restore_state
	pushq	40(%rsp)
	.cfi_def_cfa_offset 24
	pushq	40(%rsp)
	.cfi_def_cfa_offset 32
	call	__fpclassifyl@PLT
	popq	%rdx
	.cfi_def_cfa_offset 24
	popq	%rcx
	.cfi_def_cfa_offset 16
	movl	$1, %ecx
	fldt	16(%rsp)
	fldt	32(%rsp)
	fucomip	%st(1), %st
	fstp	%st(0)
	setp	%dl
	cmovne	%ecx, %edx
	testl	%eax, %eax
	setne	%al
	addq	$8, %rsp
	.cfi_def_cfa_offset 8
	movzbl	%al, %eax
	andl	%edx, %eax
	ret
	.cfi_endproc
.LFE10:
	.size	__islessgreaterl, .-__islessgreaterl
	.p2align 4
	.type	__isgreaterf, @function
__isgreaterf:
.LFB11:
	.cfi_startproc
	vmovd	%xmm0, %eax
	andl	$2147483647, %eax
	cmpl	$2139095040, %eax
	ja	.L56
	vmovd	%xmm1, %eax
	andl	$2147483647, %eax
	cmpl	$2139095040, %eax
	ja	.L56
	xorl	%eax, %eax
	vcomiss	%xmm1, %xmm0
	seta	%al
	ret
	.p2align 4,,10
	.p2align 3
.L56:
	xorl	%eax, %eax
	ret
	.cfi_endproc
.LFE11:
	.size	__isgreaterf, .-__isgreaterf
	.p2align 4
	.type	__isgreater, @function
__isgreater:
.LFB12:
	.cfi_startproc
	movabsq	$9223372036854775807, %rax
	vmovq	%xmm0, %rcx
	movabsq	$9218868437227405312, %rdx
	andq	%rcx, %rax
	cmpq	%rax, %rdx
	jb	.L60
	movabsq	$9223372036854775807, %rax
	vmovq	%xmm1, %rsi
	andq	%rsi, %rax
	cmpq	%rax, %rdx
	jb	.L60
	xorl	%eax, %eax
	vcomisd	%xmm1, %xmm0
	seta	%al
	ret
	.p2align 4,,10
	.p2align 3
.L60:
	xorl	%eax, %eax
	ret
	.cfi_endproc
.LFE12:
	.size	__isgreater, .-__isgreater
	.p2align 4
	.type	__isgreaterl, @function
__isgreaterl:
.LFB13:
	.cfi_startproc
	subq	$8, %rsp
	.cfi_def_cfa_offset 16
	pushq	24(%rsp)
	.cfi_def_cfa_offset 24
	pushq	24(%rsp)
	.cfi_def_cfa_offset 32
	call	__fpclassifyl@PLT
	popq	%rsi
	.cfi_def_cfa_offset 24
	popq	%rdi
	.cfi_def_cfa_offset 16
	testl	%eax, %eax
	jne	.L70
.L61:
	addq	$8, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L70:
	.cfi_restore_state
	pushq	40(%rsp)
	.cfi_def_cfa_offset 24
	pushq	40(%rsp)
	.cfi_def_cfa_offset 32
	call	__fpclassifyl@PLT
	popq	%rdx
	.cfi_def_cfa_offset 24
	popq	%rcx
	.cfi_def_cfa_offset 16
	testl	%eax, %eax
	je	.L61
	fldt	32(%rsp)
	fldt	16(%rsp)
	xorl	%eax, %eax
	fcomip	%st(1), %st
	fstp	%st(0)
	seta	%al
	addq	$8, %rsp
	.cfi_def_cfa_offset 8
	ret
	.cfi_endproc
.LFE13:
	.size	__isgreaterl, .-__isgreaterl
	.p2align 4
	.type	__isgreaterequalf, @function
__isgreaterequalf:
.LFB14:
	.cfi_startproc
	vmovd	%xmm0, %eax
	andl	$2147483647, %eax
	cmpl	$2139095040, %eax
	ja	.L74
	vmovd	%xmm1, %eax
	andl	$2147483647, %eax
	cmpl	$2139095040, %eax
	ja	.L74
	xorl	%eax, %eax
	vcomiss	%xmm1, %xmm0
	setnb	%al
	ret
	.p2align 4,,10
	.p2align 3
.L74:
	xorl	%eax, %eax
	ret
	.cfi_endproc
.LFE14:
	.size	__isgreaterequalf, .-__isgreaterequalf
	.p2align 4
	.type	__isgreaterequal, @function
__isgreaterequal:
.LFB15:
	.cfi_startproc
	movabsq	$9223372036854775807, %rax
	vmovq	%xmm0, %rcx
	movabsq	$9218868437227405312, %rdx
	andq	%rcx, %rax
	cmpq	%rax, %rdx
	jb	.L78
	movabsq	$9223372036854775807, %rax
	vmovq	%xmm1, %rsi
	andq	%rsi, %rax
	cmpq	%rax, %rdx
	jb	.L78
	xorl	%eax, %eax
	vcomisd	%xmm1, %xmm0
	setnb	%al
	ret
	.p2align 4,,10
	.p2align 3
.L78:
	xorl	%eax, %eax
	ret
	.cfi_endproc
.LFE15:
	.size	__isgreaterequal, .-__isgreaterequal
	.p2align 4
	.type	__isgreaterequall, @function
__isgreaterequall:
.LFB16:
	.cfi_startproc
	subq	$8, %rsp
	.cfi_def_cfa_offset 16
	pushq	24(%rsp)
	.cfi_def_cfa_offset 24
	pushq	24(%rsp)
	.cfi_def_cfa_offset 32
	call	__fpclassifyl@PLT
	popq	%rsi
	.cfi_def_cfa_offset 24
	popq	%rdi
	.cfi_def_cfa_offset 16
	testl	%eax, %eax
	jne	.L88
.L79:
	addq	$8, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L88:
	.cfi_restore_state
	pushq	40(%rsp)
	.cfi_def_cfa_offset 24
	pushq	40(%rsp)
	.cfi_def_cfa_offset 32
	call	__fpclassifyl@PLT
	popq	%rdx
	.cfi_def_cfa_offset 24
	popq	%rcx
	.cfi_def_cfa_offset 16
	testl	%eax, %eax
	je	.L79
	fldt	32(%rsp)
	fldt	16(%rsp)
	xorl	%eax, %eax
	fcomip	%st(1), %st
	fstp	%st(0)
	setnb	%al
	addq	$8, %rsp
	.cfi_def_cfa_offset 8
	ret
	.cfi_endproc
.LFE16:
	.size	__isgreaterequall, .-__isgreaterequall
	.p2align 4
	.type	viviani_normal, @function
viviani_normal:
.LFB17:
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
	vmulss	.LC1(%rip), %xmm0, %xmm0
	vmovss	-36(%rbp), %xmm2
	leaq	-36(%rbp), %rdi
	vmovss	%xmm1, -88(%rbp)
	vmovss	%xmm2, -84(%rbp)
	call	sincosf@PLT
	vmovss	-40(%rbp), %xmm4
	vmovss	-88(%rbp), %xmm1
	vmovss	.LC2(%rip), %xmm3
	vmovss	-84(%rbp), %xmm2
	vfnmadd231ss	-36(%rbp), %xmm3, %xmm2
	vfmsub132ss	%xmm4, %xmm1, %xmm3
	vmulss	%xmm4, %xmm1, %xmm1
	vunpcklps	%xmm3, %xmm2, %xmm0
	vmulss	%xmm3, %xmm3, %xmm3
	vfmadd132ss	%xmm2, %xmm3, %xmm2
	vmovss	.LC3(%rip), %xmm3
	vfmadd231ss	%xmm1, %xmm1, %xmm2
	vsqrtss	%xmm2, %xmm2, %xmm2
	vcomiss	%xmm2, %xmm3
	ja	.L91
	vdivss	%xmm2, %xmm1, %xmm1
	vmovsldup	%xmm2, %xmm3
	vmovq	%xmm0, %xmm0
	vmovhps	.LC4(%rip), %xmm3, %xmm3
	vdivps	%xmm3, %xmm0, %xmm0
.L91:
	movq	-8(%rbp), %r10
	.cfi_def_cfa 10, 0
	leave
	leaq	-8(%r10), %rsp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE17:
	.size	viviani_normal, .-viviani_normal
	.p2align 4
	.type	compute_invariant, @function
compute_invariant:
.LFB18:
	.cfi_startproc
	movq	%rsi, %rax
	shrq	$3, %rax
	je	.L93
	leaq	-1(%rax), %rdx
	cmpq	$2, %rdx
	jbe	.L98
	movq	%rsi, %rcx
	andq	$-32, %rsi
	vpxor	%xmm0, %xmm0, %xmm0
	movq	%rdi, %rdx
	shrq	$5, %rcx
	addq	%rdi, %rsi
	.p2align 4
	.p2align 4
	.p2align 3
.L96:
	vpxor	(%rdx), %ymm0, %ymm0
	addq	$32, %rdx
	cmpq	%rdx, %rsi
	jne	.L96
	vextracti128	$0x1, %ymm0, %xmm1
	salq	$2, %rcx
	vpxor	%xmm0, %xmm1, %xmm0
	vpsrldq	$8, %xmm0, %xmm1
	vpxor	%xmm1, %xmm0, %xmm0
	vmovq	%xmm0, %rdx
	cmpq	%rcx, %rax
	je	.L104
	vzeroupper
.L95:
	leaq	1(%rcx), %rsi
	xorq	(%rdi,%rcx,8), %rdx
	cmpq	%rax, %rsi
	jnb	.L97
	leaq	2(%rcx), %rsi
	xorq	8(%rdi,%rcx,8), %rdx
	cmpq	%rax, %rsi
	jnb	.L97
	xorq	16(%rdi,%rcx,8), %rdx
.L97:
	movq	%rdx, %rax
	shrq	$32, %rax
	xorq	%rdx, %rax
	movq	%rax, %rdx
	shrq	$16, %rdx
	xorq	%rax, %rdx
	movq	%rdx, %rax
	shrq	$8, %rax
	xorq	%rdx, %rax
.L93:
	ret
	.p2align 4,,10
	.p2align 3
.L104:
	vzeroupper
	jmp	.L97
.L98:
	xorl	%ecx, %ecx
	xorl	%edx, %edx
	jmp	.L95
	.cfi_endproc
.LFE18:
	.size	compute_invariant, .-compute_invariant
	.section	.rodata.cst4,"aM",@progbits,4
	.align 4
.LC1:
	.long	1077936128
	.align 4
.LC2:
	.long	1056964608
	.align 4
.LC3:
	.long	897988541
	.section	.rodata.cst8,"aM",@progbits,8
	.align 8
.LC4:
	.long	1065353216
	.long	1065353216
	.ident	"GCC: (GNU) 16.1.1 20260625"
	.section	.note.GNU-stack,"",@progbits

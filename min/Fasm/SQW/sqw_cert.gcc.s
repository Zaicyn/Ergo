	.file	"sqw_cert.c"
	.text
	.p2align 4
	.type	sqw_apply_event.constprop.0, @function
sqw_apply_event.constprop.0:
.LFB54:
	.cfi_startproc
	movl	(%rdi), %edx
	movslq	4(%rdi), %r8
	movslq	8(%rdi), %rax
	movslq	12(%rdi), %rsi
	movl	16(%rdi), %ecx
	movzbl	20(%rdi), %edi
	testl	%edx, %edx
	jne	.L2
	movslq	%ecx, %rdx
	imulq	$336, %rax, %rax
	movl	%ecx, %r9d
	imulq	$1808407283, %rdx, %rdx
	sarl	$31, %r9d
	imulq	$168, %rsi, %rsi
	imulq	$10752, %r8, %r8
	sarq	$38, %rdx
	subl	%r9d, %edx
	addq	%rsi, %rax
	imull	$152, %edx, %r9d
	addq	%r8, %rax
	subl	%r9d, %ecx
	movslq	%ecx, %rdx
	leaq	w.2(%rip), %rcx
	addq	%rcx, %rax
	xorb	%dil, (%rax,%rdx)
	ret
	.p2align 4
	.p2align 3
.L2:
	cmpl	$1, %edx
	je	.L8
	cmpl	$2, %edx
	je	.L9
	andl	$4095, %ecx
	andl	$15, %eax
	leaq	5396(%rcx), %rdx
	salq	$4, %rdx
	addq	%rdx, %rax
	leaq	w.2(%rip), %rdx
	xorb	%dil, (%rdx,%rax)
	ret
	.p2align 4
	.p2align 3
.L8:
	imulq	$336, %rax, %rax
	imulq	$168, %rsi, %rsi
	imulq	$10752, %r8, %r8
	addq	%rax, %rsi
	leaq	152(%rsi,%r8), %rdx
	movl	%ecx, %esi
	sarl	$31, %esi
	shrl	$29, %esi
	leal	(%rcx,%rsi), %eax
	andl	$7, %eax
	subl	%esi, %eax
	cltq
	addq	%rdx, %rax
	leaq	w.2(%rip), %rdx
	xorb	%dil, (%rdx,%rax)
	ret
	.p2align 4
	.p2align 3
.L9:
	salq	$5, %r8
	andl	$3, %ecx
	leaq	w.2(%rip), %rdx
	leaq	37968(%r8,%rax), %rax
	leaq	(%rcx,%rax,4), %rax
	xorb	%dil, (%rdx,%rax)
	ret
	.cfi_endproc
.LFE54:
	.size	sqw_apply_event.constprop.0, .-sqw_apply_event.constprop.0
	.p2align 4
	.type	sqb_sweep.constprop.0, @function
sqb_sweep.constprop.0:
.LFB55:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	xorl	%r10d, %r10d
	xorl	%r9d, %r9d
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%r15
	pushq	%r14
	pushq	%r13
	pushq	%r12
	pushq	%rbx
	andq	$-32, %rsp
	subq	$1408, %rsp
	.cfi_offset 15, -24
	.cfi_offset 14, -32
	.cfi_offset 13, -40
	.cfi_offset 12, -48
	.cfi_offset 3, -56
	movq	%fs:40, %r11
	movq	%r11, 1400(%rsp)
	leaq	w.2(%rip), %r11
	movq	$0, 744(%rsp)
	leaq	86048(%r11), %r14
	leaq	86016(%r11), %r15
.L11:
	movq	%r11, %rcx
	movq	%r11, 72(%rsp)
	movq	%r15, %rdi
	movq	%r15, %r8
	movl	%r10d, %r11d
	movq	%r9, 64(%rsp)
	jmp	.L26
.L17:
	movb	$1, (%rsi)
.L21:
	vmovdqu	96(%rcx), %ymm1
	movabsq	$627065225361, %r15
	movabsq	$635655159955, %r12
	movabsq	$644245094549, %rdx
	vmovdqu	64(%rcx), %ymm13
	vmovdqa	1024(%rsp), %ymm10
	vmovdqu	32(%rcx), %ymm11
	vmovdqu	(%rcx), %ymm0
	vmovq	992(%rsp), %xmm14
	vmovdqa	%ymm1, 1344(%rsp)
	vmovdqu	120(%rcx), %ymm1
	vpxor	%ymm10, %ymm13, %ymm12
	vmovdqa	%ymm13, 1312(%rsp)
	vpxor	%ymm10, %ymm11, %ymm3
	vpxor	%ymm10, %ymm0, %ymm2
	vmovdqa	%ymm12, 1152(%rsp)
	vmovdqu	%ymm12, 232(%rcx)
	vmovdqa	%ymm0, 1248(%rsp)
	vmovdqa	%ymm3, 1184(%rsp)
	vmovdqu	%ymm3, 200(%rcx)
	vmovdqa	%ymm11, 1280(%rsp)
	vmovdqu	%ymm2, 168(%rcx)
	vmovdqu	%ymm1, 1368(%rsp)
	vmovq	1392(%rsp), %xmm15
	vpxor	1344(%rsp), %ymm10, %ymm1
	vpxor	1376(%rsp), %xmm10, %xmm10
	vpxor	%xmm14, %xmm15, %xmm12
	vmovdqa	.LC7(%rip), %ymm14
	vmovdqa	%ymm1, 1120(%rsp)
	vmovdqu	%ymm1, 264(%rcx)
	vpmovzxbw	%xmm0, %ymm1
	vmovdqa	%xmm10, 1104(%rsp)
	vmovdqu	%xmm10, 296(%rcx)
	vpmovzxwd	%xmm1, %ymm9
	vextracti128	$0x1, %ymm1, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vmovq	%xmm12, 312(%rcx)
	vpmovzxwd	%xmm1, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm9, %ymm10
	vpmovzxwd	%xmm0, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm10, %ymm3, %ymm10
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm10, %ymm0, %ymm10
	vpmulld	%ymm14, %ymm1, %ymm1
	vmovdqa	%ymm14, 288(%rsp)
	vmovdqa	.LC6(%rip), %ymm14
	vpmulld	%ymm14, %ymm9, %ymm9
	vmovdqa	%ymm14, 320(%rsp)
	vmovdqa	.LC8(%rip), %ymm14
	vpaddd	%ymm9, %ymm1, %ymm1
	vpmulld	%ymm14, %ymm3, %ymm3
	vmovdqa	%ymm14, 256(%rsp)
	vmovdqa	.LC9(%rip), %ymm14
	vpaddd	%ymm1, %ymm3, %ymm1
	vpmulld	%ymm14, %ymm0, %ymm0
	vmovdqa	%ymm14, 224(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm14
	vpmovzxbw	%xmm11, %ymm1
	vextracti128	$0x1, %ymm11, %xmm0
	vpmovzxwd	%xmm1, %ymm9
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm9, %ymm10, %ymm10
	vpmovzxwd	%xmm0, %ymm3
	vpaddd	%ymm1, %ymm10, %ymm10
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm10, %ymm3, %ymm10
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm10, %ymm0, %ymm11
	vmovdqa	.LC10(%rip), %ymm10
	vpmulld	%ymm10, %ymm9, %ymm9
	vmovdqa	%ymm10, 640(%rsp)
	vpaddd	%ymm14, %ymm9, %ymm10
	vmovdqa	.LC11(%rip), %ymm14
	vpmulld	%ymm14, %ymm1, %ymm1
	vmovdqa	%ymm14, 608(%rsp)
	vmovdqa	.LC12(%rip), %ymm14
	vpaddd	%ymm10, %ymm1, %ymm9
	vpmulld	%ymm14, %ymm3, %ymm1
	vmovdqa	%ymm14, 928(%rsp)
	vmovdqa	.LC13(%rip), %ymm14
	vpaddd	%ymm9, %ymm1, %ymm1
	vpmulld	%ymm14, %ymm0, %ymm0
	vmovdqa	%ymm14, 576(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm14
	vpmovzxbw	%xmm13, %ymm1
	vextracti128	$0x1, %ymm13, %xmm0
	vmovdqa	.LC14(%rip), %ymm13
	vpmovzxwd	%xmm1, %ymm9
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm9, %ymm11, %ymm10
	vpmovzxwd	%xmm1, %ymm1
	vpmovzxwd	%xmm0, %ymm3
	vpaddd	%ymm10, %ymm1, %ymm10
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm10, %ymm3, %ymm10
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm10, %ymm0, %ymm11
	vpmulld	%ymm13, %ymm9, %ymm9
	vmovdqa	%ymm13, 544(%rsp)
	vmovdqa	.LC15(%rip), %ymm13
	vpaddd	%ymm14, %ymm9, %ymm10
	vpmulld	%ymm13, %ymm1, %ymm1
	vmovdqa	%ymm13, 512(%rsp)
	vmovdqa	.LC16(%rip), %ymm13
	vpaddd	%ymm10, %ymm1, %ymm9
	vpmulld	%ymm13, %ymm3, %ymm1
	vmovdqa	%ymm13, 896(%rsp)
	vmovdqa	.LC17(%rip), %ymm13
	vpaddd	%ymm9, %ymm1, %ymm1
	vpmulld	%ymm13, %ymm0, %ymm0
	vmovdqa	%ymm13, 480(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm14
	vpmovzxbw	1344(%rsp), %ymm1
	vmovdqa	1344(%rsp), %ymm0
	vpmovzxwd	%xmm1, %ymm9
	vextracti128	$0x1, %ymm1, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm11, %ymm9, %ymm10
	vmovdqa	.LC18(%rip), %ymm11
	vpmovzxwd	%xmm1, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm10, %ymm1, %ymm10
	vpmovzxwd	%xmm0, %ymm3
	vpaddd	%ymm10, %ymm3, %ymm10
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm10, %ymm0, %ymm13
	vpmulld	%ymm11, %ymm9, %ymm9
	vmovdqa	%ymm11, 448(%rsp)
	vmovdqa	.LC19(%rip), %ymm11
	vpaddd	%ymm14, %ymm9, %ymm9
	vpmulld	%ymm11, %ymm1, %ymm1
	vmovdqa	%ymm11, 832(%rsp)
	vmovdqa	.LC20(%rip), %ymm11
	vpaddd	%ymm9, %ymm1, %ymm1
	vpmulld	%ymm11, %ymm3, %ymm3
	vmovdqa	%ymm11, 960(%rsp)
	vmovdqa	.LC21(%rip), %ymm11
	vpaddd	%ymm1, %ymm3, %ymm1
	vpmulld	%ymm11, %ymm0, %ymm0
	vmovdqa	%ymm11, 800(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm14
	vmovdqa	1376(%rsp), %xmm0
	vpmovzxbw	%xmm0, %xmm1
	vmovdqa	1376(%rsp), %xmm0
	vpmovzxwd	%xmm1, %xmm10
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm1
	vpaddd	%xmm1, %xmm10, %xmm9
	vpsrldq	$8, %xmm0, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm3
	vpsrldq	$8, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm0
	vpaddd	%xmm3, %xmm9, %xmm9
	vpaddd	%xmm0, %xmm9, %xmm9
	vpaddd	%xmm13, %xmm9, %xmm11
	vextracti128	$0x1, %ymm13, %xmm9
	vpaddd	%xmm9, %xmm11, %xmm13
	vmovdqa	.LC22(%rip), %xmm11
	vpmulld	%xmm11, %xmm10, %xmm9
	vmovdqa	%xmm11, 768(%rsp)
	vmovdqa	.LC23(%rip), %xmm11
	vpmulld	%xmm11, %xmm1, %xmm1
	vmovdqa	%xmm11, 1088(%rsp)
	vmovdqa	.LC24(%rip), %xmm11
	movl	$0, 332(%rcx)
	vmovdqa	%ymm2, 1216(%rsp)
	vmovq	%xmm12, 1056(%rsp)
	vpaddd	%xmm1, %xmm9, %xmm1
	vpmulld	%xmm11, %xmm3, %xmm3
	vmovdqa	%xmm11, 752(%rsp)
	vmovdqa	.LC25(%rip), %xmm11
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmovzxbw	%xmm15, %xmm3
	vpmulld	%xmm11, %xmm0, %xmm0
	vmovdqa	%xmm11, 704(%rsp)
	vpmovzxwd	%xmm3, %xmm11
	vpsrlq	$32, %xmm3, %xmm3
	vpmovzxwd	%xmm3, %xmm3
	vpaddd	%xmm0, %xmm1, %xmm0
	vextracti128	$0x1, %ymm14, %xmm1
	vpaddd	%xmm14, %xmm0, %xmm0
	vpaddd	%xmm3, %xmm11, %xmm14
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm15, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vmovq	.LC29(%rip), %xmm15
	vpmovzxwd	%xmm1, %xmm10
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm1
	vpaddd	%xmm10, %xmm14, %xmm14
	vpaddd	%xmm1, %xmm14, %xmm14
	vpaddd	%xmm13, %xmm14, %xmm9
	vpsrldq	$8, %xmm13, %xmm13
	vpmulld	%xmm15, %xmm1, %xmm1
	vpaddd	%xmm13, %xmm9, %xmm9
	vmovq	%r15, %xmm13
	vpmulld	%xmm13, %xmm11, %xmm11
	vmovq	%r12, %xmm13
	vpmulld	%xmm13, %xmm3, %xmm3
	vmovq	%rdx, %xmm13
	vpmulld	%xmm13, %xmm10, %xmm10
	vpaddd	%xmm3, %xmm11, %xmm3
	vpaddd	%xmm10, %xmm3, %xmm3
	vpaddd	%xmm1, %xmm3, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm1
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm0
	vpsrlq	$32, %xmm9, %xmm1
	vpaddd	%xmm1, %xmm9, %xmm1
	vpsrlq	$32, %xmm0, %xmm3
	vpaddd	%xmm3, %xmm0, %xmm0
	vinsertps	$16, %xmm0, %xmm1, %xmm1
	vmovq	%xmm1, 320(%rcx)
.L23:
	vmovdqa	1024(%rsp), %ymm13
	vpxor	%xmm12, %xmm12, %xmm12
	vpcmpeqd	%ymm1, %ymm1, %ymm1
	vpxor	1216(%rsp), %ymm8, %ymm0
	vpabsb	%ymm1, %ymm11
	vmovdqa	864(%rsp), %ymm2
	vmovdqa	%ymm13, %ymm10
	vpcmpeqb	%ymm13, %ymm0, %ymm0
	vpcmpeqb	%ymm12, %ymm0, %ymm0
	vpand	%ymm11, %ymm0, %ymm0
	vpmovzxbw	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm1, %ymm3, %ymm3
	vpmovzxwd	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm3, %ymm1, %ymm1
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpxor	1184(%rsp), %ymm2, %ymm1
	vpcmpeqb	%ymm13, %ymm1, %ymm1
	vpcmpeqb	%ymm12, %ymm1, %ymm1
	vpand	%ymm11, %ymm1, %ymm1
	vpmovzxbw	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm3, %ymm9
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm9, %ymm9
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm1, %ymm0
	vpaddd	%ymm9, %ymm3, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm3, %ymm0, %ymm0
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm1
	vpxor	1152(%rsp), %ymm5, %ymm0
	vpcmpeqb	%ymm13, %ymm0, %ymm0
	vpcmpeqb	%ymm12, %ymm0, %ymm0
	vpand	%ymm11, %ymm0, %ymm0
	vpmovzxbw	%xmm0, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm3, %ymm9
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm9, %ymm9
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm9, %ymm3, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm3, %ymm1, %ymm1
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm1
	vpxor	1120(%rsp), %ymm6, %ymm0
	vpcmpeqb	%ymm13, %ymm0, %ymm0
	vpcmpeqb	%ymm12, %ymm0, %ymm0
	vpand	%ymm11, %ymm0, %ymm0
	vmovdqa	%xmm13, %xmm11
	vpmovzxbw	%xmm0, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm3, %ymm9
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm9, %ymm9
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm9, %ymm3, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm3, %ymm1, %ymm1
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm1
	vpxor	1104(%rsp), %xmm7, %xmm0
	vpcmpeqb	%xmm13, %xmm0, %xmm2
	vpxor	%xmm0, %xmm0, %xmm0
	vpcmpeqb	%xmm0, %xmm2, %xmm2
	vpcmpeqd	%xmm0, %xmm0, %xmm0
	vpabsb	%xmm0, %xmm0
	vpand	%xmm0, %xmm2, %xmm0
	vpmovzxbw	%xmm0, %xmm2
	vpsrldq	$8, %xmm0, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpmovzxwd	%xmm2, %xmm9
	vpsrldq	$8, %xmm2, %xmm3
	vpmovzxwd	%xmm3, %xmm3
	vpmovzxwd	%xmm0, %xmm2
	vpaddd	%xmm3, %xmm9, %xmm3
	vpsrldq	$8, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm0
	vpaddd	%xmm2, %xmm3, %xmm2
	vpaddd	%xmm0, %xmm2, %xmm2
	vpaddd	%xmm1, %xmm2, %xmm0
	vmovq	1056(%rsp), %xmm2
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpxor	%xmm2, %xmm4, %xmm1
	vmovq	992(%rsp), %xmm2
	vpcmpeqb	%xmm2, %xmm1, %xmm1
	vpxor	%xmm2, %xmm2, %xmm2
	vpcmpeqb	%xmm2, %xmm1, %xmm2
	vmovq	.LC5(%rip), %xmm1
	vpand	%xmm1, %xmm2, %xmm1
	vpmovzxbw	%xmm1, %xmm2
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm2, %xmm3
	vpsrlq	$32, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm2
	vpaddd	%xmm2, %xmm3, %xmm2
	vpmovzxwd	%xmm1, %xmm3
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm1
	vpaddd	%xmm3, %xmm2, %xmm3
	vpaddd	%xmm1, %xmm3, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm1
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm0
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %eax
	testl	%eax, %eax
	je	.L37
.L25:
	incq	744(%rsp)
	.p2align 5
	.p2align 4
	.p2align 3
.L24:
	incq	%rdi
	addq	$336, %rcx
	cmpq	%r14, %rdi
	je	.L38
.L26:
	cmpb	$0, (%rdi)
	je	.L24
	movl	%r11d, %eax
	subl	%r8d, %eax
	leal	(%rax,%rdi), %esi
	leaq	action.0(%rip), %rax
	addq	%rax, %rsi
	cmpl	$-559063315, 164(%rcx)
	movb	$0, (%rsi)
	je	.L24
	vmovdqu	(%rcx), %ymm8
	vmovdqu	200(%rcx), %ymm5
	movl	$1431655765, %eax
	vmovd	%eax, %xmm6
	vmovdqu	32(%rcx), %ymm15
	vmovdqu	264(%rcx), %ymm4
	vpbroadcastd	%xmm6, %ymm6
	vmovdqu	168(%rcx), %ymm7
	movq	312(%rcx), %rax
	vmovdqa	%ymm6, 1024(%rsp)
	vmovdqu	232(%rcx), %ymm6
	movq	%rax, 1056(%rsp)
	vmovdqa	%ymm5, 1184(%rsp)
	vpmovzxbw	%xmm8, %ymm3
	vmovdqu	64(%rcx), %ymm5
	vextracti128	$0x1, %ymm8, %xmm0
	vpmovzxwd	%xmm3, %ymm2
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxbw	%xmm15, %ymm9
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxwd	%xmm0, %ymm12
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm9, %ymm14
	vpmovzxwd	%xmm3, %ymm11
	vpmovzxwd	%xmm0, %ymm13
	vmovdqa	%ymm6, 1152(%rsp)
	vmovdqu	96(%rcx), %ymm6
	vpaddd	%ymm2, %ymm11, %ymm0
	vextracti128	$0x1, %ymm15, %xmm3
	vmovdqa	%ymm15, 864(%rsp)
	vpaddd	%ymm0, %ymm12, %ymm0
	vextracti128	$0x1, %ymm9, %xmm9
	vpmovzxbw	%xmm3, %ymm3
	vmovdqa	%ymm2, 704(%rsp)
	vpaddd	%ymm0, %ymm13, %ymm0
	vpmovzxwd	%xmm9, %ymm15
	vpmovzxwd	%xmm3, %ymm10
	vmovdqa	%ymm4, 1120(%rsp)
	vpaddd	%ymm14, %ymm0, %ymm0
	vextracti128	$0x1, %ymm3, %xmm3
	vmovdqa	%ymm10, 672(%rsp)
	vmovdqu	296(%rcx), %xmm4
	vpaddd	%ymm0, %ymm15, %ymm0
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxbw	%xmm5, %ymm9
	vpaddd	%ymm10, %ymm0, %ymm0
	vmovdqa	%ymm3, 640(%rsp)
	vpmovzxwd	%xmm9, %ymm10
	vmovdqa	%ymm7, 1216(%rsp)
	vpaddd	%ymm3, %ymm0, %ymm0
	vextracti128	$0x1, %ymm9, %xmm9
	vextracti128	$0x1, %ymm5, %xmm3
	vmovdqa	%ymm10, 608(%rsp)
	vpmovzxwd	%xmm9, %ymm1
	vpmovzxbw	%xmm3, %ymm3
	vpaddd	%ymm10, %ymm0, %ymm0
	vpmovzxbw	%xmm6, %ymm9
	vpmovzxwd	%xmm3, %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxwd	%xmm9, %ymm10
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm2, %ymm0, %ymm0
	vextracti128	$0x1, %ymm9, %xmm9
	vmovdqa	128(%rcx), %xmm7
	vpaddd	%ymm3, %ymm0, %ymm0
	vmovdqa	%ymm3, 512(%rsp)
	vpmovzxwd	%xmm9, %ymm9
	vextracti128	$0x1, %ymm6, %xmm3
	vmovdqa	%ymm9, 960(%rsp)
	vmovdqa	%ymm2, 544(%rsp)
	vmovdqa	%xmm4, 1104(%rsp)
	vpmovzxbw	%xmm3, %ymm3
	vmovdqa	%ymm10, 928(%rsp)
	vmovdqa	%ymm1, 576(%rsp)
	vpmovzxwd	%xmm3, %ymm9
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxwd	%xmm3, %ymm2
	vpaddd	%ymm10, %ymm0, %ymm3
	vpaddd	960(%rsp), %ymm3, %ymm3
	vmovq	144(%rcx), %xmm4
	vmovdqa	%ymm9, 896(%rsp)
	vmovdqa	%ymm2, 832(%rsp)
	vpsrldq	$8, %xmm7, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm1
	vpsrldq	$8, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm0
	vpaddd	%ymm9, %ymm3, %ymm3
	vpmovzxbw	%xmm7, %xmm9
	vpmovzxwd	%xmm9, %xmm10
	vpsrldq	$8, %xmm9, %xmm9
	vpmovzxwd	%xmm9, %xmm9
	vpaddd	%ymm2, %ymm3, %ymm3
	vmovdqa	%xmm10, 800(%rsp)
	vmovdqa	%xmm9, 768(%rsp)
	vpaddd	%xmm10, %xmm9, %xmm9
	vmovdqa	%xmm0, 752(%rsp)
	vpaddd	%xmm1, %xmm9, %xmm9
	vmovdqa	%xmm1, 1088(%rsp)
	vpaddd	%xmm0, %xmm9, %xmm9
	vpaddd	%xmm3, %xmm9, %xmm0
	vpmovzxbw	%xmm4, %xmm9
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxwd	%xmm9, %xmm2
	vpaddd	%xmm3, %xmm0, %xmm0
	vpsrlq	$32, %xmm9, %xmm9
	vpsrlq	$32, %xmm4, %xmm3
	vmovq	%xmm2, %rbx
	vpmovzxbw	%xmm3, %xmm3
	vpmovzxwd	%xmm9, %xmm2
	vmovq	%xmm2, %rdx
	vpmovzxwd	%xmm3, %xmm2
	vpsrlq	$32, %xmm3, %xmm3
	vmovq	%xmm2, %r10
	vpmovzxwd	%xmm3, %xmm2
	vmovq	%rdx, %xmm3
	vmovq	%xmm2, %rax
	vmovq	%rbx, %xmm2
	vpaddd	%xmm3, %xmm2, %xmm3
	vmovq	%r10, %xmm2
	vpaddd	%xmm2, %xmm3, %xmm3
	vmovq	%rax, %xmm2
	vpaddd	%xmm2, %xmm3, %xmm3
	vpaddd	%xmm0, %xmm3, %xmm3
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm3, %xmm0
	vpsrlq	$32, %xmm0, %xmm3
	vpaddd	%xmm3, %xmm0, %xmm0
	vmovd	%xmm0, %r9d
	cmpl	%r9d, 152(%rcx)
	je	.L39
	movabsq	$6148914691236517205, %rax
	xorl	%r10d, %r10d
	xorl	%r9d, %r9d
	movq	%rax, 992(%rsp)
	vmovq	%rax, %xmm1
.L13:
	vmovdqa	1024(%rsp), %ymm3
	vmovdqa	1104(%rsp), %xmm2
	vpxor	1216(%rsp), %ymm3, %ymm11
	vpxor	.LC31(%rip), %xmm2, %xmm13
	vmovq	1056(%rsp), %xmm2
	vpxor	1184(%rsp), %ymm3, %ymm10
	vpxor	1152(%rsp), %ymm3, %ymm9
	vpxor	1120(%rsp), %ymm3, %ymm12
	vextracti128	$0x1, %ymm11, %xmm0
	vpxor	%xmm1, %xmm2, %xmm2
	vpmovzxbw	%xmm11, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm15
	vextracti128	$0x1, %ymm1, %xmm1
	vmovq	%xmm2, %rbx
	vpmovzxwd	%xmm1, %ymm14
	vpmovzxwd	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vmovdqa	%ymm15, 640(%rsp)
	vpmovzxwd	%xmm0, %ymm2
	vmovdqa	%ymm14, 608(%rsp)
	vpaddd	%ymm15, %ymm14, %ymm0
	vpmovzxbw	%xmm10, %ymm14
	vpmovzxwd	%xmm14, %ymm15
	vpaddd	%ymm1, %ymm0, %ymm0
	vextracti128	$0x1, %ymm14, %xmm14
	vmovdqa	%ymm1, 576(%rsp)
	vpaddd	%ymm2, %ymm0, %ymm0
	vpmovzxwd	%xmm14, %ymm14
	vextracti128	$0x1, %ymm10, %xmm1
	vmovdqa	%ymm15, 512(%rsp)
	vmovdqa	%ymm14, 928(%rsp)
	vpaddd	%ymm15, %ymm0, %ymm0
	vpaddd	928(%rsp), %ymm0, %ymm0
	vpmovzxbw	%xmm1, %ymm1
	vpmovzxwd	%xmm1, %ymm14
	vextracti128	$0x1, %ymm1, %xmm1
	vmovdqa	%ymm2, 544(%rsp)
	vmovdqa	%ymm14, 480(%rsp)
	vpmovzxwd	%xmm1, %ymm1
	vmovdqa	%ymm1, 448(%rsp)
	vpaddd	%ymm14, %ymm0, %ymm0
	vpmovzxbw	%xmm9, %ymm14
	vpmovzxwd	%xmm14, %ymm15
	vextracti128	$0x1, %ymm14, %xmm14
	vpaddd	%ymm1, %ymm0, %ymm0
	vextracti128	$0x1, %ymm9, %xmm1
	vpmovzxwd	%xmm14, %ymm14
	vpaddd	%ymm15, %ymm0, %ymm0
	vpmovzxbw	%xmm1, %ymm1
	vmovdqa	%ymm15, 416(%rsp)
	vmovdqa	%ymm14, 896(%rsp)
	vpaddd	896(%rsp), %ymm0, %ymm0
	vpmovzxwd	%xmm1, %ymm14
	vextracti128	$0x1, %ymm1, %xmm1
	vmovdqa	%ymm14, 384(%rsp)
	vpmovzxwd	%xmm1, %ymm1
	vmovdqa	%ymm1, 352(%rsp)
	vpaddd	%ymm14, %ymm0, %ymm0
	vpmovzxbw	%xmm12, %ymm14
	vpmovzxwd	%xmm14, %ymm15
	vextracti128	$0x1, %ymm14, %xmm14
	vpaddd	%ymm1, %ymm0, %ymm0
	vextracti128	$0x1, %ymm12, %xmm1
	vpmovzxwd	%xmm14, %ymm14
	vpaddd	%ymm15, %ymm0, %ymm0
	vpmovzxbw	%xmm1, %ymm1
	vmovdqa	%ymm15, 832(%rsp)
	vmovdqa	%ymm14, 960(%rsp)
	vpaddd	960(%rsp), %ymm0, %ymm0
	vpmovzxwd	%xmm1, %ymm14
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm1, %ymm1
	vmovdqa	%ymm14, 800(%rsp)
	vmovdqa	%ymm1, 768(%rsp)
	vpaddd	%ymm14, %ymm0, %ymm0
	vpmovzxbw	%xmm13, %xmm14
	vpmovzxwd	%xmm14, %xmm15
	vpaddd	%ymm1, %ymm0, %ymm0
	vpsrldq	$8, %xmm14, %xmm14
	vpsrldq	$8, %xmm13, %xmm1
	vpmovzxwd	%xmm14, %xmm14
	vpmovzxbw	%xmm1, %xmm1
	vmovdqa	%xmm15, 1088(%rsp)
	vpmovzxwd	%xmm1, %xmm2
	vmovdqa	%xmm14, 752(%rsp)
	vpaddd	%xmm15, %xmm14, %xmm14
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm2, %xmm14, %xmm14
	vpmovzxwd	%xmm1, %xmm1
	vmovdqa	%xmm2, 704(%rsp)
	vmovq	%rbx, %xmm2
	vpaddd	%xmm1, %xmm14, %xmm14
	vmovdqa	%xmm1, 672(%rsp)
	vpaddd	%xmm0, %xmm14, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxbw	%xmm2, %xmm14
	vpaddd	%xmm0, %xmm1, %xmm1
	vpsrlq	$32, %xmm2, %xmm0
	vpmovzxwd	%xmm14, %xmm2
	vpmovzxbw	%xmm0, %xmm0
	vmovq	%xmm2, %r12
	vpsrlq	$32, %xmm14, %xmm14
	vpmovzxwd	%xmm14, %xmm2
	vpmovzxwd	%xmm0, %xmm15
	vmovq	%xmm2, %rdx
	vpsrlq	$32, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm2
	vmovq	%xmm2, %rax
	vmovq	%rdx, %xmm0
	vmovq	%r12, %xmm2
	vpaddd	%xmm0, %xmm2, %xmm0
	vmovq	%rax, %xmm2
	vpaddd	%xmm15, %xmm0, %xmm0
	vpaddd	%xmm2, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpsrlq	$32, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm2
	vmovq	%xmm2, %r13
	cmpl	%r13d, 320(%rcx)
	je	.L40
.L14:
	testb	%r10b, %r10b
	jne	.L17
	movb	$1, (%rsi)
	testl	%r9d, %r9d
	jne	.L21
	incq	%rdi
	movl	$-559063315, 164(%rcx)
	movl	$-559063315, 332(%rcx)
	movb	$2, (%rsi)
	addq	$336, %rcx
	incq	86320+w.2(%rip)
	cmpq	%r14, %rdi
	jne	.L26
.L38:
	movq	64(%rsp), %r9
	leal	32(%r11), %r10d
	movq	72(%rsp), %r11
	leaq	32(%rdi), %r14
	leaq	32(%r8), %r15
	addq	$10752, %r9
	addq	$10752, %r11
	cmpq	$86016, %r9
	jne	.L11
	movq	1400(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L41
	movq	744(%rsp), %rax
	vzeroupper
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
.L40:
	.cfi_restore_state
	vmovdqa	.LC6(%rip), %ymm2
	movabsq	$627065225361, %r15
	vpmulld	640(%rsp), %ymm2, %ymm1
	vmovdqa	%ymm2, 320(%rsp)
	vmovdqa	.LC7(%rip), %ymm2
	vpmulld	608(%rsp), %ymm2, %ymm0
	vmovdqa	%ymm2, 288(%rsp)
	vmovdqa	.LC8(%rip), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	576(%rsp), %ymm2, %ymm1
	vmovdqa	%ymm2, 256(%rsp)
	vmovdqa	.LC9(%rip), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	544(%rsp), %ymm2, %ymm0
	vmovdqa	%ymm2, 224(%rsp)
	vmovdqa	.LC10(%rip), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	512(%rsp), %ymm2, %ymm1
	vmovdqa	%ymm2, 640(%rsp)
	vmovdqa	.LC11(%rip), %ymm2
	vmovdqa	%ymm2, 608(%rsp)
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	928(%rsp), %ymm2, %ymm0
	vmovdqa	.LC12(%rip), %ymm2
	vmovdqa	%ymm2, 928(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	480(%rsp), %ymm2, %ymm1
	vmovdqa	.LC13(%rip), %ymm2
	vmovdqa	%ymm2, 576(%rsp)
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	448(%rsp), %ymm2, %ymm0
	vmovdqa	.LC14(%rip), %ymm2
	vmovdqa	%ymm2, 544(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	416(%rsp), %ymm2, %ymm1
	vmovdqa	.LC15(%rip), %ymm2
	vmovdqa	%ymm2, 512(%rsp)
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	896(%rsp), %ymm2, %ymm0
	vmovdqa	.LC16(%rip), %ymm2
	vmovdqa	%ymm2, 896(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	384(%rsp), %ymm2, %ymm1
	vmovdqa	.LC17(%rip), %ymm2
	vmovdqa	%ymm2, 480(%rsp)
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	352(%rsp), %ymm2, %ymm0
	vmovdqa	.LC18(%rip), %ymm2
	vmovdqa	%ymm2, 448(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	832(%rsp), %ymm2, %ymm1
	vmovdqa	.LC19(%rip), %ymm2
	vmovdqa	%ymm2, 832(%rsp)
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	960(%rsp), %ymm2, %ymm0
	vmovdqa	.LC20(%rip), %ymm2
	vmovdqa	%ymm2, 960(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	800(%rsp), %ymm2, %ymm1
	vmovdqa	.LC21(%rip), %ymm2
	vmovdqa	%ymm2, 800(%rsp)
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	768(%rsp), %ymm2, %ymm0
	vmovdqa	.LC22(%rip), %xmm2
	vmovdqa	%xmm2, 768(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	1088(%rsp), %xmm2, %xmm1
	vmovdqa	.LC23(%rip), %xmm2
	vpmulld	752(%rsp), %xmm2, %xmm14
	vmovdqa	%xmm2, 1088(%rsp)
	vmovdqa	.LC24(%rip), %xmm2
	vpaddd	%xmm14, %xmm1, %xmm14
	vpmulld	704(%rsp), %xmm2, %xmm1
	vmovdqa	%xmm2, 752(%rsp)
	vmovdqa	.LC25(%rip), %xmm2
	vpaddd	%xmm1, %xmm14, %xmm1
	vpmulld	672(%rsp), %xmm2, %xmm14
	vmovdqa	%xmm2, 704(%rsp)
	vmovq	%r12, %xmm2
	movabsq	$635655159955, %r12
	vpaddd	%xmm14, %xmm1, %xmm14
	vpaddd	%xmm0, %xmm14, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vmovq	%r12, %xmm14
	vpaddd	%xmm0, %xmm1, %xmm1
	vmovq	%r15, %xmm0
	vpmulld	%xmm0, %xmm2, %xmm0
	vmovq	%rdx, %xmm2
	movabsq	$644245094549, %rdx
	vpmulld	%xmm14, %xmm2, %xmm14
	vmovq	%rdx, %xmm2
	vpaddd	%xmm14, %xmm0, %xmm14
	vpmulld	%xmm2, %xmm15, %xmm0
	vmovq	.LC29(%rip), %xmm15
	vmovq	%rax, %xmm2
	vpaddd	%xmm0, %xmm14, %xmm0
	vpmulld	%xmm15, %xmm2, %xmm14
	vpaddd	%xmm14, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpsrlq	$32, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm0
	vmovd	%xmm0, %eax
	cmpl	%eax, 324(%rcx)
	jne	.L14
	testb	%r10b, %r10b
	je	.L42
	incl	160(%rcx)
	incl	328(%rcx)
	jmp	.L24
.L39:
	vpxor	1216(%rsp), %ymm8, %ymm0
	vpxor	%xmm2, %xmm2, %xmm2
	vpcmpeqd	%ymm3, %ymm3, %ymm3
	movabsq	$6148914691236517205, %r15
	vpabsb	%ymm3, %ymm1
	vpmulld	.LC7(%rip), %ymm11, %ymm11
	movq	%r15, 992(%rsp)
	vpmulld	.LC8(%rip), %ymm12, %ymm12
	vpmulld	.LC9(%rip), %ymm13, %ymm13
	vpmulld	.LC10(%rip), %ymm14, %ymm14
	vpmulld	.LC11(%rip), %ymm15, %ymm15
	vpcmpeqb	.LC30(%rip), %ymm0, %ymm0
	vpcmpeqb	%ymm2, %ymm0, %ymm0
	vpand	%ymm1, %ymm0, %ymm0
	vpmovzxbw	%xmm0, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm3, %ymm9
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm3, %ymm9, %ymm3
	vpmovzxwd	%xmm0, %ymm9
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm3, %ymm9, %ymm9
	vmovdqa	864(%rsp), %ymm3
	vpmovzxwd	%xmm0, %ymm0
	vpxor	1184(%rsp), %ymm3, %ymm3
	vpaddd	%ymm9, %ymm0, %ymm0
	vpcmpeqb	.LC30(%rip), %ymm3, %ymm3
	vpcmpeqb	%ymm2, %ymm3, %ymm3
	vpand	%ymm1, %ymm3, %ymm3
	vpmovzxbw	%xmm3, %ymm9
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxwd	%xmm9, %ymm10
	vpmovzxbw	%xmm3, %ymm3
	vpaddd	%ymm0, %ymm10, %ymm10
	vextracti128	$0x1, %ymm9, %xmm0
	vpmovzxwd	%xmm3, %ymm9
	vpmovzxwd	%xmm0, %ymm0
	vextracti128	$0x1, %ymm3, %xmm3
	vpaddd	%ymm10, %ymm0, %ymm0
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm0, %ymm9, %ymm9
	vpxor	1152(%rsp), %ymm5, %ymm0
	vpaddd	%ymm9, %ymm3, %ymm3
	vpcmpeqb	.LC30(%rip), %ymm0, %ymm0
	vpcmpeqb	%ymm2, %ymm0, %ymm0
	vpand	%ymm1, %ymm0, %ymm0
	vpmovzxbw	%xmm0, %ymm9
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm9, %ymm10
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm3, %ymm10, %ymm10
	vextracti128	$0x1, %ymm9, %xmm3
	vpmovzxwd	%xmm0, %ymm9
	vpmovzxwd	%xmm3, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm10, %ymm3, %ymm3
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm3, %ymm9, %ymm9
	vpxor	1120(%rsp), %ymm6, %ymm3
	vpaddd	%ymm9, %ymm0, %ymm0
	vpcmpeqb	.LC30(%rip), %ymm3, %ymm3
	vpcmpeqb	%ymm2, %ymm3, %ymm3
	vmovq	1056(%rsp), %xmm2
	vpand	%ymm1, %ymm3, %ymm3
	vpmovzxbw	%xmm3, %ymm9
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxwd	%xmm9, %ymm10
	vpmovzxbw	%xmm3, %ymm3
	vpaddd	%ymm0, %ymm10, %ymm10
	vextracti128	$0x1, %ymm9, %xmm0
	vpmovzxwd	%xmm3, %ymm9
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm10, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm9, %ymm9
	vextracti128	$0x1, %ymm3, %xmm0
	vpxor	%xmm3, %xmm3, %xmm3
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm9, %ymm0, %ymm0
	vpxor	1104(%rsp), %xmm7, %xmm9
	vpcmpeqb	1024(%rsp), %xmm9, %xmm9
	vpcmpeqb	%xmm3, %xmm9, %xmm9
	vpcmpeqd	%xmm3, %xmm3, %xmm3
	vpabsb	%xmm3, %xmm3
	vpand	%xmm3, %xmm9, %xmm3
	vpmovzxbw	%xmm3, %xmm9
	vpsrldq	$8, %xmm3, %xmm3
	vpmovzxbw	%xmm3, %xmm3
	vpmovzxwd	%xmm9, %xmm10
	vpsrldq	$8, %xmm9, %xmm9
	vpmovzxwd	%xmm9, %xmm9
	vpaddd	%xmm9, %xmm10, %xmm9
	vpmovzxwd	%xmm3, %xmm10
	vpsrldq	$8, %xmm3, %xmm3
	vpmovzxwd	%xmm3, %xmm3
	vpaddd	%xmm10, %xmm9, %xmm10
	vpaddd	%xmm3, %xmm10, %xmm3
	vpaddd	%xmm0, %xmm3, %xmm9
	vpxor	%xmm2, %xmm4, %xmm3
	vextracti128	$0x1, %ymm0, %xmm0
	vmovq	%r15, %xmm2
	vpaddd	%xmm0, %xmm9, %xmm0
	vpcmpeqb	%xmm2, %xmm3, %xmm3
	vpxor	%xmm9, %xmm9, %xmm9
	vmovdqa	672(%rsp), %ymm2
	vpcmpeqb	%xmm9, %xmm3, %xmm9
	vmovq	.LC5(%rip), %xmm3
	vpand	%xmm3, %xmm9, %xmm3
	vpmovzxbw	%xmm3, %xmm9
	vpsrlq	$32, %xmm3, %xmm3
	vpmovzxbw	%xmm3, %xmm3
	vpmovzxwd	%xmm9, %xmm10
	vpsrlq	$32, %xmm9, %xmm9
	vpmovzxwd	%xmm9, %xmm9
	vpaddd	%xmm9, %xmm10, %xmm9
	vpmovzxwd	%xmm3, %xmm10
	vpsrlq	$32, %xmm3, %xmm3
	vpmovzxwd	%xmm3, %xmm3
	vpaddd	%xmm10, %xmm9, %xmm10
	vpaddd	%xmm3, %xmm10, %xmm3
	vpaddd	%xmm0, %xmm3, %xmm9
	vmovdqa	704(%rsp), %ymm3
	vpsrldq	$8, %xmm0, %xmm0
	vpmulld	.LC6(%rip), %ymm3, %ymm1
	vpaddd	%xmm0, %xmm9, %xmm9
	vpmulld	.LC12(%rip), %ymm2, %ymm0
	vmovdqa	640(%rsp), %ymm2
	vpaddd	%ymm11, %ymm1, %ymm11
	vpmulld	.LC13(%rip), %ymm2, %ymm1
	vmovdqa	608(%rsp), %ymm2
	vpaddd	%ymm11, %ymm12, %ymm12
	vpaddd	%ymm12, %ymm13, %ymm13
	vpaddd	%ymm13, %ymm14, %ymm14
	vpaddd	%ymm14, %ymm15, %ymm15
	vpaddd	%ymm15, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC14(%rip), %ymm2, %ymm0
	vmovdqa	576(%rsp), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	.LC15(%rip), %ymm2, %ymm1
	vmovdqa	544(%rsp), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC16(%rip), %ymm2, %ymm0
	vmovdqa	512(%rsp), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	.LC17(%rip), %ymm2, %ymm1
	vmovdqa	928(%rsp), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC18(%rip), %ymm2, %ymm0
	vmovdqa	960(%rsp), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	.LC19(%rip), %ymm2, %ymm1
	vmovdqa	896(%rsp), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC20(%rip), %ymm2, %ymm0
	vmovdqa	832(%rsp), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	.LC21(%rip), %ymm2, %ymm1
	vmovdqa	800(%rsp), %xmm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC22(%rip), %xmm2, %xmm0
	vmovdqa	768(%rsp), %xmm2
	vpmulld	.LC23(%rip), %xmm2, %xmm3
	vmovdqa	1088(%rsp), %xmm2
	vpaddd	%xmm3, %xmm0, %xmm3
	vpmulld	.LC24(%rip), %xmm2, %xmm0
	vmovdqa	752(%rsp), %xmm2
	vpaddd	%xmm0, %xmm3, %xmm0
	vpmulld	.LC25(%rip), %xmm2, %xmm3
	vmovq	%rbx, %xmm2
	vpaddd	%xmm3, %xmm0, %xmm3
	vpaddd	%xmm1, %xmm3, %xmm0
	vextracti128	$0x1, %ymm1, %xmm1
	vmovq	.LC27(%rip), %xmm3
	vpaddd	%xmm1, %xmm0, %xmm1
	vmovq	.LC26(%rip), %xmm0
	vpmulld	%xmm0, %xmm2, %xmm0
	vmovq	%rdx, %xmm2
	vpmulld	%xmm3, %xmm2, %xmm3
	vmovq	%r10, %xmm2
	vpaddd	%xmm3, %xmm0, %xmm0
	vmovq	.LC28(%rip), %xmm3
	vpmulld	%xmm3, %xmm2, %xmm3
	vmovq	%rax, %xmm2
	vpaddd	%xmm3, %xmm0, %xmm0
	vmovq	.LC29(%rip), %xmm3
	vpmulld	%xmm3, %xmm2, %xmm3
	vpaddd	%xmm3, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpsrlq	$32, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vpsrlq	$32, %xmm9, %xmm0
	vpaddd	%xmm0, %xmm9, %xmm9
	vmovd	%xmm1, %eax
	cmpl	156(%rcx), %eax
	vmovd	%xmm9, %edx
	vmovq	%r15, %xmm1
	sete	%al
	sete	%r9b
	testl	%edx, %edx
	sete	%dl
	movzbl	%r9b, %r9d
	andl	%eax, %edx
	movl	%edx, %r10d
	jmp	.L13
.L42:
	movb	$1, (%rsi)
	cmpl	$1, %r9d
	je	.L43
	vmovdqa	%ymm12, 1344(%rsp)
	vmovdqa	%xmm13, 1376(%rsp)
	movq	%rbx, 1392(%rsp)
	vmovdqu	1368(%rsp), %ymm1
	vmovq	%r13, %xmm7
	vmovdqu	%ymm12, 96(%rcx)
	vmovdqa	%ymm11, 1248(%rsp)
	movl	$0, 164(%rcx)
	vinsertps	$16, %xmm0, %xmm7, %xmm0
	vmovdqa	%ymm10, 1280(%rsp)
	vmovdqa	%ymm9, 1312(%rsp)
	vmovdqu	%ymm11, (%rcx)
	vmovdqu	%ymm10, 32(%rcx)
	vmovdqu	%ymm9, 64(%rcx)
	vmovq	%xmm0, 152(%rcx)
	vmovdqa	%ymm11, %ymm8
	vmovdqa	%ymm10, 864(%rsp)
	vmovdqa	%ymm9, %ymm5
	vmovdqu	%ymm1, 120(%rcx)
	vmovdqu	96(%rcx), %ymm6
	vmovdqa	128(%rcx), %xmm7
	vmovq	144(%rcx), %xmm4
	jmp	.L23
.L43:
	vmovdqu	96(%rcx), %ymm0
	vmovdqu	(%rcx), %ymm4
	vmovq	%r15, %xmm2
	vmovdqu	32(%rcx), %ymm7
	vmovdqu	64(%rcx), %ymm8
	vmovq	992(%rsp), %xmm6
	vmovdqa	%ymm0, 1344(%rsp)
	vmovdqu	120(%rcx), %ymm0
	vpmovzxbw	%xmm4, %ymm1
	vmovdqa	%ymm4, 1248(%rsp)
	vmovdqa	%ymm7, 1280(%rsp)
	vmovdqa	%ymm8, 1312(%rsp)
	vmovdqu	%ymm0, 1368(%rsp)
	vpxor	%ymm3, %ymm4, %ymm0
	vmovdqa	1376(%rsp), %xmm12
	vmovq	1392(%rsp), %xmm11
	vmovdqu	%ymm0, 168(%rcx)
	vpxor	%ymm3, %ymm7, %ymm0
	vmovdqa	1344(%rsp), %ymm13
	vmovdqu	%ymm0, 200(%rcx)
	vpxor	%ymm3, %ymm8, %ymm0
	vmovdqu	%ymm0, 232(%rcx)
	vpxor	.LC31(%rip), %xmm12, %xmm0
	vpxor	%ymm3, %ymm13, %ymm3
	vmovdqu	%ymm3, 264(%rcx)
	vpmovzxwd	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vmovdqu	%xmm0, 296(%rcx)
	vpxor	%xmm6, %xmm11, %xmm0
	vmovq	%xmm0, 312(%rcx)
	vextracti128	$0x1, %ymm4, %xmm0
	vpmovzxwd	%xmm1, %ymm4
	vpmulld	288(%rsp), %ymm4, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm0, %ymm5
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm6
	vpaddd	%ymm4, %ymm3, %ymm0
	vpaddd	%ymm0, %ymm5, %ymm0
	vpaddd	%ymm0, %ymm6, %ymm9
	vpmulld	320(%rsp), %ymm3, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm1
	vpmulld	256(%rsp), %ymm5, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	224(%rsp), %ymm6, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm10
	vextracti128	$0x1, %ymm7, %xmm0
	vpmovzxbw	%xmm7, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm0, %ymm5
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm4
	vpmulld	608(%rsp), %ymm4, %ymm1
	vpmovzxwd	%xmm0, %ymm6
	vpaddd	%ymm9, %ymm3, %ymm0
	vpaddd	%ymm4, %ymm0, %ymm0
	vpaddd	%ymm5, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm6, %ymm7
	vpmulld	640(%rsp), %ymm3, %ymm0
	vpaddd	%ymm10, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	928(%rsp), %ymm5, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	576(%rsp), %ymm6, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm9
	vextracti128	$0x1, %ymm8, %xmm0
	vpmovzxbw	%xmm8, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm0, %ymm5
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm4
	vpmulld	512(%rsp), %ymm4, %ymm1
	vpmovzxwd	%xmm0, %ymm6
	vpaddd	%ymm7, %ymm3, %ymm0
	vpaddd	%ymm4, %ymm0, %ymm0
	vpaddd	%ymm5, %ymm0, %ymm0
	vpaddd	%ymm6, %ymm0, %ymm8
	vpmulld	544(%rsp), %ymm3, %ymm0
	vpaddd	%ymm9, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	896(%rsp), %ymm5, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	480(%rsp), %ymm6, %ymm1
	movl	$0, 332(%rcx)
	vpaddd	%ymm0, %ymm1, %ymm9
	vextracti128	$0x1, %ymm13, %xmm0
	vpmovzxbw	%xmm13, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm4
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm0, %ymm6
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm5
	vpmulld	832(%rsp), %ymm5, %ymm1
	vpmovzxwd	%xmm0, %ymm7
	vpaddd	%ymm4, %ymm8, %ymm0
	vpaddd	%ymm0, %ymm5, %ymm0
	vpaddd	%ymm0, %ymm6, %ymm0
	vpaddd	%ymm0, %ymm7, %ymm3
	vpmulld	448(%rsp), %ymm4, %ymm0
	vpaddd	%ymm9, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	960(%rsp), %ymm6, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	800(%rsp), %ymm7, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm4
	vpmovzxbw	%xmm12, %xmm1
	vpsrldq	$8, %xmm12, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpmovzxwd	%xmm1, %xmm5
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm6
	vpmovzxwd	%xmm0, %xmm7
	vpsrldq	$8, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm9
	vpaddd	%xmm6, %xmm5, %xmm0
	vpaddd	%xmm7, %xmm0, %xmm0
	vpaddd	%xmm9, %xmm0, %xmm0
	vpaddd	%xmm3, %xmm0, %xmm1
	vextracti128	$0x1, %ymm3, %xmm0
	vpmovzxbw	%xmm11, %xmm3
	vpaddd	%xmm0, %xmm1, %xmm8
	vpmulld	768(%rsp), %xmm5, %xmm0
	vpmulld	1088(%rsp), %xmm6, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpmulld	752(%rsp), %xmm7, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm0
	vpmulld	704(%rsp), %xmm9, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpaddd	%xmm4, %xmm1, %xmm0
	vextracti128	$0x1, %ymm4, %xmm1
	vpmovzxwd	%xmm3, %xmm4
	vpsrlq	$32, %xmm3, %xmm3
	vpaddd	%xmm1, %xmm0, %xmm0
	vpmovzxwd	%xmm3, %xmm5
	vpsrlq	$32, %xmm11, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm6
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm7
	vpaddd	%xmm5, %xmm4, %xmm1
	vpmulld	%xmm2, %xmm4, %xmm4
	vmovq	%r12, %xmm2
	vpmulld	%xmm2, %xmm5, %xmm5
	vpaddd	%xmm6, %xmm1, %xmm1
	vpaddd	%xmm5, %xmm4, %xmm5
	vmovq	%rdx, %xmm4
	vpmulld	%xmm4, %xmm6, %xmm6
	vpaddd	%xmm7, %xmm1, %xmm1
	vpmulld	%xmm15, %xmm7, %xmm7
	vpaddd	%xmm6, %xmm5, %xmm6
	vpaddd	%xmm8, %xmm1, %xmm3
	vpsrldq	$8, %xmm8, %xmm8
	vpaddd	%xmm7, %xmm6, %xmm7
	vpaddd	%xmm8, %xmm3, %xmm3
	vpaddd	%xmm0, %xmm7, %xmm1
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm0
	vpsrlq	$32, %xmm3, %xmm1
	vpaddd	%xmm1, %xmm3, %xmm1
	vpsrlq	$32, %xmm0, %xmm3
	vpaddd	%xmm3, %xmm0, %xmm0
	vinsertps	$16, %xmm0, %xmm1, %xmm1
	vmovq	%xmm1, 320(%rcx)
	incq	86328+w.2(%rip)
	vmovdqu	168(%rcx), %ymm7
	vmovdqu	296(%rcx), %xmm4
	movq	312(%rcx), %rax
	vmovdqu	(%rcx), %ymm8
	vmovdqu	64(%rcx), %ymm5
	vmovdqu	96(%rcx), %ymm6
	movq	%rax, 1056(%rsp)
	vmovdqa	%ymm7, 1216(%rsp)
	vmovdqu	32(%rcx), %ymm7
	vmovdqa	%xmm4, 1104(%rsp)
	vmovq	144(%rcx), %xmm4
	vmovdqa	%ymm7, 864(%rsp)
	vmovdqu	200(%rcx), %ymm7
	vmovdqa	%ymm7, 1184(%rsp)
	vmovdqu	232(%rcx), %ymm7
	vmovdqa	%ymm7, 1152(%rsp)
	vmovdqu	264(%rcx), %ymm7
	vmovdqa	%ymm7, 1120(%rsp)
	vmovdqa	128(%rcx), %xmm7
	jmp	.L23
.L37:
	vmovdqa	864(%rsp), %ymm2
	vpmovzxbw	%xmm8, %ymm1
	vextracti128	$0x1, %ymm8, %xmm0
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm8
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm0, %ymm12
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm9
	vpmovzxwd	%xmm0, %ymm13
	vpaddd	%ymm9, %ymm8, %ymm0
	vpaddd	%ymm0, %ymm12, %ymm0
	vpaddd	%ymm0, %ymm13, %ymm3
	vpmovzxbw	%xmm2, %ymm1
	vextracti128	$0x1, %ymm2, %xmm0
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm14
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm1, %ymm2
	vpmovzxwd	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm0
	vmovdqa	%ymm1, 32(%rsp)
	vmovdqa	%ymm2, (%rsp)
	vmovdqa	%ymm0, 1024(%rsp)
	vpaddd	%ymm3, %ymm14, %ymm0
	vpaddd	%ymm2, %ymm0, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpaddd	1024(%rsp), %ymm0, %ymm3
	vpmovzxbw	%xmm5, %ymm1
	vextracti128	$0x1, %ymm5, %xmm0
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm5
	vextracti128	$0x1, %ymm1, %xmm1
	vmovdqa	%ymm5, 672(%rsp)
	vpmovzxwd	%xmm1, %ymm2
	vpmovzxwd	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm0
	vmovdqa	%ymm1, 384(%rsp)
	vmovdqa	%ymm2, 416(%rsp)
	vmovdqa	%ymm0, 864(%rsp)
	vpaddd	%ymm5, %ymm3, %ymm0
	vpaddd	%ymm2, %ymm0, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpaddd	864(%rsp), %ymm0, %ymm3
	vextracti128	$0x1, %ymm6, %xmm0
	vpmovzxbw	%xmm6, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm6
	vpmovzxwd	%xmm0, %ymm2
	vextracti128	$0x1, %ymm1, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vmovdqa	%ymm6, 352(%rsp)
	vpmovzxwd	%xmm1, %ymm5
	vpmovzxwd	%xmm0, %ymm1
	vmovdqa	%ymm2, 160(%rsp)
	vmovdqa	%ymm1, 128(%rsp)
	vmovdqa	%ymm5, 192(%rsp)
	vpaddd	%ymm6, %ymm3, %ymm0
	vpaddd	%ymm5, %ymm0, %ymm0
	vpaddd	%ymm2, %ymm0, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm2
	vpmovzxbw	%xmm7, %xmm0
	vpsrldq	$8, %xmm7, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm0, %xmm7
	vpsrldq	$8, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm6
	vpmovzxwd	%xmm1, %xmm5
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm3
	vpaddd	%xmm6, %xmm7, %xmm1
	vmovdqa	%xmm5, 96(%rsp)
	vpaddd	%xmm5, %xmm1, %xmm1
	vmovdqa	%xmm3, 80(%rsp)
	vmovdqa	%xmm6, 112(%rsp)
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm2, %xmm1, %xmm0
	vextracti128	$0x1, %ymm2, %xmm1
	vpsrlq	$32, %xmm4, %xmm2
	vpmovzxbw	%xmm2, %xmm2
	vpaddd	%xmm1, %xmm0, %xmm0
	vpmovzxbw	%xmm4, %xmm1
	vpmovzxwd	%xmm2, %xmm5
	vpsrlq	$32, %xmm2, %xmm2
	vpmovzxwd	%xmm1, %xmm3
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm4
	vpmovzxwd	%xmm2, %xmm6
	vpaddd	%xmm4, %xmm3, %xmm1
	vpaddd	%xmm5, %xmm1, %xmm1
	vpaddd	%xmm6, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm1
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm0
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %eax
	cmpl	%eax, 152(%rcx)
	jne	.L25
	vpmulld	320(%rsp), %ymm8, %ymm0
	vmovdqa	(%rsp), %ymm2
	vpmulld	288(%rsp), %ymm9, %ymm1
	vpaddd	%ymm1, %ymm0, %ymm1
	vpmulld	256(%rsp), %ymm12, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	224(%rsp), %ymm13, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	640(%rsp), %ymm14, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	608(%rsp), %ymm2, %ymm1
	vmovdqa	32(%rsp), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	928(%rsp), %ymm2, %ymm0
	vmovdqa	1024(%rsp), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	576(%rsp), %ymm2, %ymm1
	vmovdqa	672(%rsp), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	544(%rsp), %ymm2, %ymm0
	vmovdqa	416(%rsp), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	512(%rsp), %ymm2, %ymm1
	vmovdqa	384(%rsp), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	896(%rsp), %ymm2, %ymm0
	vmovdqa	864(%rsp), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	480(%rsp), %ymm2, %ymm1
	vmovdqa	352(%rsp), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	448(%rsp), %ymm2, %ymm0
	vmovdqa	192(%rsp), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	832(%rsp), %ymm2, %ymm1
	vmovdqa	160(%rsp), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	960(%rsp), %ymm2, %ymm0
	vmovdqa	128(%rsp), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	800(%rsp), %ymm2, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm2
	vpmulld	768(%rsp), %xmm7, %xmm0
	vmovdqa	112(%rsp), %xmm7
	vpmulld	1088(%rsp), %xmm7, %xmm1
	vmovdqa	96(%rsp), %xmm7
	vpaddd	%xmm1, %xmm0, %xmm1
	vpmulld	752(%rsp), %xmm7, %xmm0
	vmovdqa	80(%rsp), %xmm7
	vpaddd	%xmm0, %xmm1, %xmm0
	vpmulld	704(%rsp), %xmm7, %xmm1
	vmovq	%r15, %xmm7
	vpmulld	%xmm7, %xmm3, %xmm3
	vmovq	%r12, %xmm7
	vpaddd	%xmm1, %xmm0, %xmm1
	vpaddd	%xmm2, %xmm1, %xmm0
	vextracti128	$0x1, %ymm2, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm4, %xmm1
	vmovq	%rdx, %xmm7
	vpmulld	%xmm7, %xmm5, %xmm2
	vpaddd	%xmm1, %xmm3, %xmm1
	vpaddd	%xmm2, %xmm1, %xmm2
	vpmulld	%xmm15, %xmm6, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm1
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm0
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %eax
	cmpl	%eax, 156(%rcx)
	jne	.L25
	vpxor	1216(%rsp), %ymm10, %ymm0
	vmovq	992(%rsp), %xmm2
	vmovq	1056(%rsp), %xmm7
	vpxor	1184(%rsp), %ymm10, %ymm4
	vpxor	1152(%rsp), %ymm10, %ymm5
	vpxor	1120(%rsp), %ymm10, %ymm6
	vpxor	1104(%rsp), %xmm11, %xmm3
	vpmovzxbw	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpxor	%xmm2, %xmm7, %xmm7
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm8
	vextracti128	$0x1, %ymm1, %xmm1
	vmovq	%xmm7, %r9
	vpmovzxwd	%xmm0, %ymm9
	vpmovzxwd	%xmm1, %ymm7
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxbw	%xmm4, %ymm1
	vpmovzxwd	%xmm0, %ymm10
	vpaddd	%ymm7, %ymm8, %ymm0
	vpmovzxwd	%xmm1, %ymm11
	vpaddd	%ymm0, %ymm9, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm0, %ymm10, %ymm2
	vextracti128	$0x1, %ymm4, %xmm0
	vpmovzxwd	%xmm1, %ymm12
	vpmovzxbw	%xmm5, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm0, %ymm13
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm14
	vpaddd	%ymm2, %ymm11, %ymm0
	vpaddd	%ymm0, %ymm12, %ymm0
	vpaddd	%ymm13, %ymm0, %ymm0
	vpaddd	%ymm14, %ymm0, %ymm4
	vextracti128	$0x1, %ymm5, %xmm0
	vpmovzxwd	%xmm1, %ymm5
	vpmovzxbw	%xmm0, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vmovdqa	%ymm5, 384(%rsp)
	vpmovzxwd	%xmm1, %ymm2
	vpmovzxwd	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm0
	vmovdqa	%ymm1, 416(%rsp)
	vmovdqa	%ymm2, 672(%rsp)
	vmovdqa	%ymm0, 1216(%rsp)
	vpaddd	%ymm5, %ymm4, %ymm0
	vpaddd	%ymm2, %ymm0, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpaddd	1216(%rsp), %ymm0, %ymm4
	vextracti128	$0x1, %ymm6, %xmm0
	vpmovzxbw	%xmm6, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm6
	vpmovzxwd	%xmm0, %ymm2
	vextracti128	$0x1, %ymm1, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vmovdqa	%ymm6, 864(%rsp)
	vpmovzxwd	%xmm1, %ymm5
	vpmovzxwd	%xmm0, %ymm1
	vmovdqa	%ymm2, 1024(%rsp)
	vmovdqa	%ymm1, 1056(%rsp)
	vmovdqa	%ymm5, 992(%rsp)
	vpaddd	%ymm6, %ymm4, %ymm0
	vpaddd	%ymm5, %ymm0, %ymm0
	vpaddd	%ymm2, %ymm0, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm2
	vpmovzxbw	%xmm3, %xmm1
	vpsrldq	$8, %xmm3, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpmovzxwd	%xmm1, %xmm6
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm4
	vpmovzxwd	%xmm0, %xmm5
	vpaddd	%xmm6, %xmm4, %xmm1
	vpsrldq	$8, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm3
	vmovdqa	%xmm6, 1104(%rsp)
	vpaddd	%xmm5, %xmm1, %xmm1
	vmovq	%r9, %xmm6
	vmovdqa	%xmm3, 1184(%rsp)
	vmovdqa	%xmm4, 1120(%rsp)
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmovzxbw	%xmm6, %xmm3
	vmovdqa	%xmm5, 1152(%rsp)
	vpaddd	%xmm2, %xmm1, %xmm0
	vextracti128	$0x1, %ymm2, %xmm1
	vpmovzxwd	%xmm3, %xmm2
	vpsrlq	$32, %xmm3, %xmm3
	vpaddd	%xmm1, %xmm0, %xmm0
	vpmovzxwd	%xmm3, %xmm4
	vpsrlq	$32, %xmm6, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm5
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm6
	vpaddd	%xmm2, %xmm4, %xmm1
	vpaddd	%xmm5, %xmm1, %xmm1
	vpaddd	%xmm6, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm1
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm0
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %eax
	cmpl	%eax, 320(%rcx)
	jne	.L25
	vpmulld	288(%rsp), %ymm7, %ymm0
	vmovdqa	384(%rsp), %ymm7
	vpmulld	%xmm15, %xmm6, %xmm6
	vpmulld	320(%rsp), %ymm8, %ymm1
	vpaddd	%ymm1, %ymm0, %ymm1
	vpmulld	256(%rsp), %ymm9, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	224(%rsp), %ymm10, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	640(%rsp), %ymm11, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	608(%rsp), %ymm12, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	928(%rsp), %ymm13, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	576(%rsp), %ymm14, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	544(%rsp), %ymm7, %ymm0
	vmovdqa	672(%rsp), %ymm7
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	512(%rsp), %ymm7, %ymm1
	vmovdqa	416(%rsp), %ymm7
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	896(%rsp), %ymm7, %ymm0
	vmovdqa	1216(%rsp), %ymm7
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	480(%rsp), %ymm7, %ymm1
	vmovdqa	864(%rsp), %ymm7
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	448(%rsp), %ymm7, %ymm0
	vmovdqa	992(%rsp), %ymm7
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	832(%rsp), %ymm7, %ymm1
	vmovdqa	1024(%rsp), %ymm7
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	960(%rsp), %ymm7, %ymm0
	vmovdqa	1056(%rsp), %ymm7
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	800(%rsp), %ymm7, %ymm1
	vmovdqa	1120(%rsp), %xmm7
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	1088(%rsp), %xmm7, %xmm0
	vmovdqa	1104(%rsp), %xmm7
	vpmulld	768(%rsp), %xmm7, %xmm3
	vmovdqa	1152(%rsp), %xmm7
	vpaddd	%xmm3, %xmm0, %xmm0
	vpmulld	752(%rsp), %xmm7, %xmm3
	vmovdqa	1184(%rsp), %xmm7
	vpaddd	%xmm3, %xmm0, %xmm0
	vpmulld	704(%rsp), %xmm7, %xmm3
	vmovq	%r15, %xmm7
	vpaddd	%xmm3, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpmulld	%xmm7, %xmm2, %xmm0
	vmovq	%r12, %xmm7
	vpmulld	%xmm7, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm0, %xmm0
	vmovq	%rdx, %xmm4
	vpmulld	%xmm4, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm0
	vpaddd	%xmm6, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %eax
	cmpl	%eax, 324(%rcx)
	jne	.L25
	jmp	.L24
.L41:
	vzeroupper
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE55:
	.size	sqb_sweep.constprop.0, .-sqb_sweep.constprop.0
	.section	.rodata.str1.8,"aMS",@progbits,1
	.align 8
.LC68:
	.string	"SQWOR O1_recognition  %lld/%d = %.6f  expect=1.000000 counting (memoization exactness)\n"
	.align 8
.LC69:
	.string	"SQWOR O2_refpair_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n"
	.align 8
.LC70:
	.string	"SQWOR O3_payload_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n"
	.align 8
.LC71:
	.string	"SQWOR O3_payload_rep  %lld/%lld = %.6f  expect>=0.990 measurement [A]\n"
	.align 8
.LC72:
	.string	"SQWOR O4_syndrome_det %lld/%lld = %.6f  expect=1.000000 counting [A]\n"
	.align 8
.LC73:
	.string	"SQWOR O4_syndrome_rep %lld/%lld = %.6f  expect=1.000000 measurement [A]\n"
	.align 8
.LC74:
	.string	"SQWOR O5_closure      %lld unresolved [A]  expect=0\n"
	.align 8
.LC75:
	.string	"SQWOR O6_apoptosis    %lld [A]  expect=0 isolated\n"
	.align 8
.LC76:
	.string	"SQWOR O7_idx_failsafe %lld/%lld = %.6f  expect=1.000000 (poisoned cache never serves wrong content) [A isolated]\n"
	.align 8
.LC77:
	.string	"SQWOR auxB_det        %lld/%lld = %.6f  poisson tail (content classes)\n"
	.align 8
.LC78:
	.string	"SQWOR auxB_rep        %lld/%lld = %.6f  poisson tail\n"
	.align 8
.LC79:
	.string	"SQWOR auxB_tombs      %lld  tomb_refs %lld (amplification: %.2f logical items lost per tombstone)  auxB_coh_fail %lld  auxB_unresolved %lld\n"
	.align 8
.LC80:
	.string	"SQWOR O8_main_cohere  %lld  expect=0 audit [A]\n"
	.section	.text.startup,"ax",@progbits
	.p2align 4
	.globl	main
	.type	main, @function
main:
.LFB53:
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
	pushq	%r13
	pushq	%r12
	pushq	%r10
	.cfi_escape 0xf,0x3,0x76,0x58,0x6
	.cfi_escape 0x10,0xf,0x2,0x76,0x78
	.cfi_escape 0x10,0xe,0x2,0x76,0x70
	.cfi_escape 0x10,0xd,0x2,0x76,0x68
	.cfi_escape 0x10,0xc,0x2,0x76,0x60
	pushq	%rbx
	subq	$3808, %rsp
	.cfi_escape 0x10,0x3,0x2,0x76,0x50
	movq	%fs:40, %rax
	movq	%rax, -56(%rbp)
	xorl	%eax, %eax
	movl	$1500, -3768(%rbp)
	cmpl	$1, %edi
	jle	.L45
	movq	8(%rsi), %rdi
	movl	$10, %edx
	xorl	%esi, %esi
	call	__isoc23_strtol@PLT
	movl	%eax, -3768(%rbp)
.L45:
	vmovdqa	.LC33(%rip), %ymm7
	leaq	508+stream.3(%rip), %r15
	movl	$128, %ecx
	movabsq	$-1749540032614691874, %rdi
	movabsq	$7683277266246660415, %r14
	movabsq	$-8050056175193481693, %r13
	movabsq	$1600686389938274267, %r8
	vmovdqa	%ymm7, stream.3(%rip)
	vmovdqa	.LC34(%rip), %ymm7
	vmovdqa	%ymm7, 32+stream.3(%rip)
	vmovdqa	.LC35(%rip), %ymm7
	vmovdqa	%ymm7, 64+stream.3(%rip)
	vmovdqa	.LC36(%rip), %ymm7
	vmovdqa	%ymm7, 96+stream.3(%rip)
	vmovdqa	.LC37(%rip), %ymm7
	vmovdqa	%ymm7, 128+stream.3(%rip)
	vmovdqa	.LC38(%rip), %ymm7
	vmovdqa	%ymm7, 160+stream.3(%rip)
	vmovdqa	.LC39(%rip), %ymm7
	vmovdqa	%ymm7, 192+stream.3(%rip)
	vmovdqa	.LC40(%rip), %ymm7
	vmovdqa	%ymm7, 224+stream.3(%rip)
	vmovdqa	.LC41(%rip), %ymm7
	vmovdqa	%ymm7, 256+stream.3(%rip)
	vmovdqa	.LC42(%rip), %ymm7
	vmovdqa	%ymm7, 288+stream.3(%rip)
	vmovdqa	.LC43(%rip), %ymm7
	vmovdqa	%ymm7, 320+stream.3(%rip)
	vmovdqa	.LC44(%rip), %ymm7
	vmovdqa	%ymm7, 352+stream.3(%rip)
	vmovdqa	.LC45(%rip), %ymm7
	vmovdqa	%ymm7, 384+stream.3(%rip)
	vmovdqa	.LC46(%rip), %ymm7
	vmovdqa	%ymm7, 416+stream.3(%rip)
	vmovdqa	.LC47(%rip), %ymm7
	vmovdqa	%ymm7, 448+stream.3(%rip)
	vmovdqa	.LC48(%rip), %ymm7
	vmovdqa	%ymm7, 480+stream.3(%rip)
	.p2align 4
	.p2align 3
.L46:
	movq	%r13, %rdx
	leaq	(%r8,%rdi), %rax
	xorq	%r8, %r14
	xorq	%r13, %rdi
	salq	$17, %rdx
	xorq	%r14, %r13
	rorx	$47, %rax, %rax
	leaq	stream.3(%rip), %rbx
	xorq	%rdx, %r14
	xorl	%edx, %edx
	movl	(%r15), %r9d
	movq	%r15, %rsi
	divl	%ecx
	subq	$4, %r15
	xorq	%rdi, %r8
	decl	%ecx
	rorx	$19, %rdi, %rdi
	movl	(%rbx,%rdx,4), %eax
	movl	%eax, 4(%r15)
	movl	%r9d, (%rbx,%rdx,4)
	cmpq	%r15, %rbx
	jne	.L46
	leaq	1020(%rsi), %rbx
	leaq	508(%rsi), %rdx
	movq	%rdi, %rax
	movq	%r8, %rsi
	movq	%rbx, -3760(%rbp)
	movq	%rbx, %r8
	.p2align 6
	.p2align 4
	.p2align 3
.L47:
	leaq	(%rsi,%rax), %rcx
	movq	%r13, %rdi
	xorq	%rsi, %r14
	xorq	%r13, %rax
	rorx	$47, %rcx, %rcx
	salq	$17, %rdi
	addq	$4, %rdx
	xorq	%r14, %r13
	andl	$127, %ecx
	xorq	%rax, %rsi
	xorq	%rdi, %r14
	rorx	$19, %rax, %rax
	movl	%ecx, -4(%rdx)
	cmpq	%rdx, %r8
	jne	.L47
	movq	%rsi, -3744(%rbp)
	movq	%rax, -3752(%rbp)
	xorl	%esi, %esi
	movl	$152920, %edx
	leaq	w.2(%rip), %rdi
	vzeroupper
	call	memset@PLT
	movq	$0, -3296(%rbp)
	leaq	-216(%rbp), %r10
	movq	%r13, -3776(%rbp)
	movq	%r14, -3784(%rbp)
	movq	%r15, -3792(%rbp)
	movq	%rax, %rbx
	.p2align 4
	.p2align 3
.L55:
	movl	$-1515870811, %eax
	leaq	-368(%rbp), %rdx
	movabsq	$1099511628211, %rcx
	movq	-3296(%rbp), %rdi
	vmovd	%eax, %xmm14
	leaq	stream.3(%rip), %rax
	vpbroadcastd	%xmm14, %ymm14
	movl	(%rax,%rdi,4), %edi
	movl	%edi, %eax
	movl	%edi, -3704(%rbp)
	sall	$4, %eax
	addl	%edi, %eax
	vmovd	%eax, %xmm2
	movzbl	%al, %eax
	movb	%al, %ah
	vpbroadcastb	%xmm2, %ymm2
	vpaddb	.LC49(%rip), %ymm2, %ymm8
	vpaddb	.LC51(%rip), %ymm2, %ymm5
	vmovd	%eax, %xmm7
	vpaddb	.LC52(%rip), %ymm2, %ymm4
	vpaddb	.LC53(%rip), %ymm2, %ymm3
	movabsq	$-7046029254386353131, %rax
	vpshuflw	$0, %xmm7, %xmm6
	vmovq	.LC56(%rip), %xmm7
	vpaddb	.LC54(%rip), %xmm2, %xmm2
	vpxor	%ymm14, %ymm8, %ymm8
	vpxor	%ymm14, %ymm5, %ymm5
	vpxor	%ymm14, %ymm4, %ymm4
	vpxor	%ymm14, %ymm3, %ymm3
	vmovdqa	%ymm8, -368(%rbp)
	vmovdqa	%ymm5, -336(%rbp)
	vpaddb	%xmm6, %xmm7, %xmm6
	vpxor	%xmm14, %xmm2, %xmm2
	vmovdqa	%ymm4, -304(%rbp)
	vmovdqa	%ymm3, -272(%rbp)
	vmovdqa	%xmm2, -240(%rbp)
	vmovq	.LC57(%rip), %xmm7
	vpxor	%xmm7, %xmm6, %xmm6
	vmovq	%xmm6, -224(%rbp)
	.p2align 4
	.p2align 4
	.p2align 3
.L48:
	xorq	(%rdx), %rax
	addq	$8, %rdx
	imulq	%rcx, %rax
	cmpq	%rdx, %r10
	jne	.L48
	movl	$1431655765, %edx
	vmovd	%edx, %xmm15
	movq	%rax, %rdx
	shrq	$29, %rdx
	vpbroadcastd	%xmm15, %ymm15
	xorq	%rdx, %rax
	movabsq	$-4658895280553007687, %rdx
	imulq	%rdx, %rax
	movq	%rax, %rdx
	shrq	$32, %rdx
	xorq	%rdx, %rax
	movq	%rax, %rdi
	movq	%rax, -3712(%rbp)
	andl	$4095, %eax
	addq	$5396, %rax
	movq	%rax, -3720(%rbp)
	salq	$4, %rax
	addq	%rbx, %rax
	cmpb	$0, 10(%rax)
	je	.L49
	cmpq	(%rax), %rdi
	je	.L255
.L49:
	movq	-3296(%rbp), %rdx
	leaq	SQB_SCATLT(%rip), %rax
	andl	$31, %edx
	movl	(%rax,%rdx,4), %edx
	movl	86272(%rbx,%rdx,4), %edi
	movq	%rdx, %r8
	cmpl	$31, %edi
	jle	.L51
	leal	1(%rdx), %eax
	movl	%eax, %edx
	andl	$7, %edx
	movl	86272(%rbx,%rdx,4), %edi
	cmpl	$31, %edi
	jle	.L156
	leal	2(%r8), %eax
	movl	%eax, %edx
	andl	$7, %edx
	movl	86272(%rbx,%rdx,4), %edi
	cmpl	$31, %edi
	jle	.L156
	leal	3(%r8), %eax
	movl	%eax, %edx
	andl	$7, %edx
	movl	86272(%rbx,%rdx,4), %edi
	cmpl	$31, %edi
	jle	.L156
	leal	4(%r8), %eax
	movl	%eax, %edx
	andl	$7, %edx
	movl	86272(%rbx,%rdx,4), %edi
	cmpl	$31, %edi
	jle	.L156
	leal	5(%r8), %eax
	movl	%eax, %edx
	andl	$7, %edx
	movl	86272(%rbx,%rdx,4), %edi
	cmpl	$31, %edi
	jle	.L156
	leal	6(%r8), %eax
	movl	%eax, %edx
	andl	$7, %edx
	movl	86272(%rbx,%rdx,4), %edi
	cmpl	$31, %edi
	jle	.L156
	leal	7(%r8), %edx
	movl	%edx, %r8d
	andl	$7, %edx
	movl	86272(%rbx,%rdx,4), %edi
	andl	$7, %r8d
	cmpl	$31, %edi
	jle	.L51
.L50:
	incq	-3296(%rbp)
	cmpq	$256, -3296(%rbp)
	jne	.L55
	movl	$-522133280, %eax
	vmovdqa	%ymm14, -3376(%rbp)
	vmovdqa	%ymm15, -3344(%rbp)
	movq	%rbx, %rsi
	vmovd	%eax, %xmm7
	movq	%rbx, -3296(%rbp)
	movl	$152920, %edx
	leaq	clean.1(%rip), %rdi
	vpbroadcastd	%xmm7, %ymm7
	movq	-3792(%rbp), %r15
	vmovdqa	%ymm7, -3600(%rbp)
	movq	-3776(%rbp), %r13
	movq	-3784(%rbp), %r14
	vzeroupper
	call	memcpy@PLT
	vpcmpeqd	%ymm4, %ymm4, %ymm4
	xorl	%ebx, %ebx
	vmovdqa	-3376(%rbp), %ymm14
	vmovdqa	-3600(%rbp), %ymm7
	vpxor	%xmm2, %xmm2, %xmm2
	vpxor	%xmm6, %xmm6, %xmm6
	vmovdqa	-3344(%rbp), %ymm15
	movq	-3296(%rbp), %r11
	movq	%r15, %r12
	vpsrlw	$8, %ymm4, %ymm4
	vmovdqa	%ymm14, %ymm5
	jmp	.L64
.L62:
	addq	$4, %r12
	cmpq	%r12, -3760(%rbp)
	je	.L256
.L64:
	movslq	(%r12), %rax
	leaq	sqw_item_slot_g(%rip), %rdi
	movslq	(%rdi,%rax,4), %r8
	leaq	sqw_item_slot_b(%rip), %rdi
	movq	%rax, %r10
	movslq	(%rdi,%rax,4), %rax
	imulq	$336, %r8, %r8
	imulq	$10752, %rax, %rax
	addq	%rax, %r8
	leaq	clean.1(%rip), %rax
	leaq	(%rax,%r8), %rsi
	cmpl	$-559063315, 164(%rsi)
	je	.L62
	movq	%rsi, %r9
	negq	%r9
	andl	$31, %r9d
	je	.L157
	movl	%r10d, %eax
	leal	1(%r9), %edi
	movl	$1, %edx
	sall	$4, %eax
	addl	%r10d, %eax
	jmp	.L58
	.p2align 5
	.p2align 4
	.p2align 3
.L158:
	movq	%rcx, %rdx
.L58:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	-1(%rsi,%rdx), %cl
	jne	.L62
	leaq	1(%rdx), %rcx
	addl	$91, %eax
	cmpq	%rcx, %rdi
	jne	.L158
	movl	$152, %ecx
	movl	%edx, %eax
	subl	%edx, %ecx
.L57:
	vmovd	%eax, %xmm0
	movl	%r10d, %edx
	movl	%r9d, %edi
	leaq	clean.1(%rip), %r9
	vpbroadcastd	%xmm0, %ymm0
	vpaddd	.LC33(%rip), %ymm0, %ymm8
	vpaddd	.LC34(%rip), %ymm0, %ymm1
	sall	$4, %edx
	vpaddd	.LC36(%rip), %ymm0, %ymm9
	addl	%r10d, %edx
	addq	%r8, %rdi
	vmovd	%edx, %xmm3
	addq	%r9, %rdi
	vpbroadcastb	%xmm3, %ymm3
	vpblendw	$170, %ymm2, %ymm1, %ymm1
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm1, %ymm8, %ymm8
	vpaddd	.LC35(%rip), %ymm0, %ymm1
	vpblendw	$170, %ymm2, %ymm9, %ymm9
	vpermq	$216, %ymm8, %ymm8
	vpand	%ymm8, %ymm4, %ymm8
	vpblendw	$170, %ymm2, %ymm1, %ymm1
	vpackusdw	%ymm9, %ymm1, %ymm1
	vpermq	$216, %ymm1, %ymm1
	vpand	%ymm1, %ymm4, %ymm1
	vpackuswb	%ymm1, %ymm8, %ymm8
	vpermq	$216, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm8, %ymm1
	vpaddb	%ymm1, %ymm1, %ymm1
	vpaddb	%ymm8, %ymm1, %ymm1
	vpsllw	$5, %ymm1, %ymm8
	vpand	%ymm8, %ymm7, %ymm8
	vpaddb	%ymm8, %ymm1, %ymm1
	vpsubb	%ymm1, %ymm3, %ymm1
	vpxor	%ymm5, %ymm1, %ymm1
	vpcmpeqb	(%rdi), %ymm1, %ymm1
	vpcmpeqb	%ymm6, %ymm1, %ymm1
	vptest	%ymm1, %ymm1
	jne	.L159
	vpaddd	.LC37(%rip), %ymm0, %ymm8
	vpaddd	.LC38(%rip), %ymm0, %ymm1
	vpaddd	.LC40(%rip), %ymm0, %ymm9
	vpblendw	$170, %ymm2, %ymm1, %ymm1
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm1, %ymm8, %ymm8
	vpaddd	.LC39(%rip), %ymm0, %ymm1
	vpblendw	$170, %ymm2, %ymm9, %ymm9
	vpermq	$216, %ymm8, %ymm8
	vpand	%ymm8, %ymm4, %ymm8
	vpblendw	$170, %ymm2, %ymm1, %ymm1
	vpackusdw	%ymm9, %ymm1, %ymm1
	vpermq	$216, %ymm1, %ymm1
	vpand	%ymm1, %ymm4, %ymm1
	vpackuswb	%ymm1, %ymm8, %ymm8
	vpermq	$216, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm8, %ymm1
	vpaddb	%ymm1, %ymm1, %ymm1
	vpaddb	%ymm8, %ymm1, %ymm1
	vpsllw	$5, %ymm1, %ymm8
	vpand	%ymm7, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm1, %ymm1
	vpsubb	%ymm1, %ymm3, %ymm1
	vpxor	%ymm5, %ymm1, %ymm1
	vpcmpeqb	32(%rdi), %ymm1, %ymm1
	vpcmpeqb	%ymm6, %ymm1, %ymm1
	vptest	%ymm1, %ymm1
	jne	.L160
	vpaddd	.LC41(%rip), %ymm0, %ymm8
	vpaddd	.LC42(%rip), %ymm0, %ymm1
	vpaddd	.LC44(%rip), %ymm0, %ymm9
	vpblendw	$170, %ymm2, %ymm1, %ymm1
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm1, %ymm8, %ymm8
	vpaddd	.LC43(%rip), %ymm0, %ymm1
	vpblendw	$170, %ymm2, %ymm9, %ymm9
	vpermq	$216, %ymm8, %ymm8
	vpand	%ymm8, %ymm4, %ymm8
	vpblendw	$170, %ymm2, %ymm1, %ymm1
	vpackusdw	%ymm9, %ymm1, %ymm1
	vpermq	$216, %ymm1, %ymm1
	vpand	%ymm1, %ymm4, %ymm1
	vpackuswb	%ymm1, %ymm8, %ymm8
	vpermq	$216, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm8, %ymm1
	vpaddb	%ymm1, %ymm1, %ymm1
	vpaddb	%ymm8, %ymm1, %ymm1
	vpsllw	$5, %ymm1, %ymm8
	vpand	%ymm7, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm1, %ymm1
	vpsubb	%ymm1, %ymm3, %ymm1
	vpxor	%ymm5, %ymm1, %ymm1
	vpcmpeqb	64(%rdi), %ymm1, %ymm1
	vpcmpeqb	%ymm6, %ymm1, %ymm1
	vptest	%ymm1, %ymm1
	jne	.L161
	vpaddd	.LC45(%rip), %ymm0, %ymm1
	vpaddd	.LC46(%rip), %ymm0, %ymm8
	vpblendw	$170, %ymm2, %ymm1, %ymm1
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm8, %ymm1, %ymm1
	vpaddd	.LC47(%rip), %ymm0, %ymm8
	vpaddd	.LC48(%rip), %ymm0, %ymm0
	vpermq	$216, %ymm1, %ymm1
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm0, %ymm8, %ymm8
	vpand	%ymm1, %ymm4, %ymm0
	vpermq	$216, %ymm8, %ymm8
	vpand	%ymm8, %ymm4, %ymm1
	vpackuswb	%ymm1, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm1
	vpaddb	%ymm1, %ymm1, %ymm1
	vpaddb	%ymm0, %ymm1, %ymm0
	vpsllw	$5, %ymm0, %ymm1
	vpand	%ymm7, %ymm1, %ymm1
	vpaddb	%ymm1, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm3, %ymm0
	vpxor	%ymm5, %ymm0, %ymm0
	vpcmpeqb	96(%rdi), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L162
	subl	$-128, %eax
	addl	$-128, %ecx
.L60:
	movl	$91, %r9d
	movl	%eax, %edi
	movl	%r10d, %r8d
	decl	%ecx
	imull	%r9d, %eax
	sall	$4, %r8d
	addq	%rdi, %rcx
	leaq	(%rsi,%rdi), %rdx
	addl	%r10d, %r8d
	leaq	1(%rsi,%rcx), %rsi
	addl	%r8d, %eax
	.p2align 5
	.p2align 4
	.p2align 3
.L63:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	(%rdx), %cl
	jne	.L62
	incq	%rdx
	addl	$91, %eax
	cmpq	%rdx, %rsi
	jne	.L63
	incq	%rbx
	jmp	.L62
	.p2align 4
	.p2align 3
.L156:
	andl	$7, %eax
	movl	%eax, %r8d
.L51:
	vpmovzxbw	%xmm8, %ymm1
	vextracti128	$0x1, %ymm8, %xmm0
	vmovdqa	%ymm5, -176(%rbp)
	vmovdqa	%ymm8, -208(%rbp)
	vpmovzxwd	%xmm1, %ymm7
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm0, %ymm0
	vmovq	%xmm6, -64(%rbp)
	vpmovzxwd	%xmm1, %ymm1
	vpmovzxwd	%xmm0, %ymm9
	vextracti128	$0x1, %ymm0, %xmm0
	vmovdqa	%ymm4, -144(%rbp)
	vpaddd	%ymm1, %ymm7, %ymm12
	vpmulld	.LC7(%rip), %ymm1, %ymm1
	vpmovzxwd	%xmm0, %ymm0
	vmovdqa	%ymm3, -112(%rbp)
	vpmulld	.LC6(%rip), %ymm7, %ymm7
	vpaddd	%ymm12, %ymm9, %ymm12
	vmovdqa	%xmm2, -80(%rbp)
	movslq	%edi, %r13
	vpaddd	%ymm12, %ymm0, %ymm12
	vpmulld	.LC9(%rip), %ymm0, %ymm0
	imulq	$336, %r13, %rcx
	vpaddd	%ymm1, %ymm7, %ymm7
	vpmulld	.LC8(%rip), %ymm9, %ymm1
	vpaddd	%ymm7, %ymm1, %ymm1
	vextracti128	$0x1, %ymm5, %xmm7
	vpaddd	%ymm1, %ymm0, %ymm9
	vpmovzxbw	%xmm5, %ymm1
	vpmovzxbw	%xmm7, %ymm7
	vpxor	%ymm15, %ymm5, %ymm5
	vpmovzxwd	%xmm1, %ymm11
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm7, %ymm10
	vpaddd	%ymm11, %ymm12, %ymm0
	vpmovzxwd	%xmm1, %ymm1
	vpmulld	.LC10(%rip), %ymm11, %ymm11
	vextracti128	$0x1, %ymm7, %xmm7
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC11(%rip), %ymm1, %ymm1
	vpmovzxwd	%xmm7, %ymm7
	vpaddd	%ymm0, %ymm10, %ymm0
	vpmulld	.LC12(%rip), %ymm10, %ymm10
	vpaddd	%ymm0, %ymm7, %ymm0
	vpmulld	.LC13(%rip), %ymm7, %ymm7
	vpaddd	%ymm9, %ymm11, %ymm11
	vpaddd	%ymm11, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm10, %ymm10
	vpmovzxbw	%xmm4, %ymm1
	vpaddd	%ymm10, %ymm7, %ymm7
	vpmovzxwd	%xmm1, %ymm11
	vextracti128	$0x1, %ymm4, %xmm10
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm10, %ymm10
	vpaddd	%ymm11, %ymm0, %ymm0
	vpmulld	.LC14(%rip), %ymm11, %ymm11
	vpmovzxwd	%xmm1, %ymm1
	vpmovzxwd	%xmm10, %ymm9
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC15(%rip), %ymm1, %ymm1
	vextracti128	$0x1, %ymm10, %xmm10
	vpaddd	%ymm0, %ymm9, %ymm0
	vpmulld	.LC16(%rip), %ymm9, %ymm9
	vpmovzxwd	%xmm10, %ymm10
	vpaddd	%ymm0, %ymm10, %ymm0
	vpmulld	.LC17(%rip), %ymm10, %ymm10
	vpaddd	%ymm7, %ymm11, %ymm11
	vpmovzxbw	%xmm3, %ymm7
	vpaddd	%ymm11, %ymm1, %ymm1
	vpmovzxwd	%xmm7, %ymm11
	vextracti128	$0x1, %ymm7, %xmm7
	vpaddd	%ymm1, %ymm9, %ymm9
	vextracti128	$0x1, %ymm3, %xmm1
	vpmovzxwd	%xmm7, %ymm7
	vpaddd	%ymm0, %ymm11, %ymm0
	vpmovzxbw	%xmm1, %ymm1
	vpmulld	.LC18(%rip), %ymm11, %ymm11
	vpaddd	%ymm9, %ymm10, %ymm10
	vpaddd	%ymm0, %ymm7, %ymm0
	vpmovzxwd	%xmm1, %ymm9
	vpmulld	.LC19(%rip), %ymm7, %ymm7
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm9, %ymm0
	vpmulld	.LC20(%rip), %ymm9, %ymm9
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC21(%rip), %ymm1, %ymm1
	vpaddd	%ymm10, %ymm11, %ymm11
	vpaddd	%ymm11, %ymm7, %ymm7
	vpaddd	%ymm7, %ymm9, %ymm9
	vpsrldq	$8, %xmm2, %xmm7
	vpmovzxbw	%xmm7, %xmm7
	vpaddd	%ymm9, %ymm1, %ymm1
	vpmovzxbw	%xmm2, %xmm9
	vpmovzxwd	%xmm7, %xmm10
	vpsrldq	$8, %xmm7, %xmm7
	vpmovzxwd	%xmm9, %xmm12
	vpsrldq	$8, %xmm9, %xmm9
	vpmovzxwd	%xmm9, %xmm9
	vpmovzxwd	%xmm7, %xmm7
	vpaddd	%xmm9, %xmm12, %xmm11
	vpmulld	.LC22(%rip), %xmm12, %xmm12
	vpmulld	.LC23(%rip), %xmm9, %xmm9
	vpaddd	%xmm10, %xmm11, %xmm11
	vpmulld	.LC24(%rip), %xmm10, %xmm10
	vpaddd	%xmm7, %xmm11, %xmm11
	vpmulld	.LC25(%rip), %xmm7, %xmm7
	vpaddd	%xmm0, %xmm11, %xmm13
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm13, %xmm0
	vmovq	.LC27(%rip), %xmm13
	vpaddd	%xmm9, %xmm12, %xmm9
	vpaddd	%xmm10, %xmm9, %xmm10
	vpaddd	%xmm7, %xmm10, %xmm7
	vpaddd	%xmm1, %xmm7, %xmm9
	vextracti128	$0x1, %ymm1, %xmm1
	vpsrlq	$32, %xmm6, %xmm7
	vpmovzxbw	%xmm7, %xmm7
	vpaddd	%xmm1, %xmm9, %xmm1
	vpmovzxbw	%xmm6, %xmm9
	vpmovzxwd	%xmm7, %xmm10
	vpsrlq	$32, %xmm7, %xmm7
	vpmovzxwd	%xmm9, %xmm12
	vpsrlq	$32, %xmm9, %xmm9
	vpmovzxwd	%xmm9, %xmm9
	vpmovzxwd	%xmm7, %xmm7
	vpaddd	%xmm9, %xmm12, %xmm11
	vpmulld	%xmm13, %xmm9, %xmm9
	vmovq	.LC28(%rip), %xmm13
	vpaddd	%xmm10, %xmm11, %xmm11
	vpaddd	%xmm7, %xmm11, %xmm11
	vpmulld	%xmm13, %xmm10, %xmm10
	vpaddd	%xmm0, %xmm11, %xmm11
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm11, %xmm0
	vmovq	.LC26(%rip), %xmm11
	vpmulld	%xmm11, %xmm12, %xmm12
	vpaddd	%xmm9, %xmm12, %xmm9
	vmovq	.LC29(%rip), %xmm12
	vpaddd	%xmm10, %xmm9, %xmm9
	vpmulld	%xmm12, %xmm7, %xmm7
	vpaddd	%xmm7, %xmm9, %xmm7
	vpaddd	%xmm1, %xmm7, %xmm9
	vpsrldq	$8, %xmm1, %xmm1
	vmovdqa	%ymm15, %ymm7
	vpaddd	%xmm1, %xmm9, %xmm1
	vpsrlq	$32, %xmm0, %xmm9
	vpaddd	%xmm9, %xmm0, %xmm9
	vpsrlq	$32, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm0
	vmovd	%xmm9, -3504(%rbp)
	vpxor	%ymm15, %ymm8, %ymm1
	vpcmpeqd	%ymm8, %ymm8, %ymm8
	vpabsb	%ymm8, %ymm8
	vmovd	%xmm0, -3472(%rbp)
	movq	86312(%rbx), %r9
	vmovdqa	%ymm5, -3568(%rbp)
	vpxor	%ymm15, %ymm4, %ymm5
	vmovdqa	%ymm5, -3600(%rbp)
	vpxor	%ymm15, %ymm3, %ymm5
	vinsertps	$16, %xmm0, %xmm9, %xmm9
	vmovdqa	%ymm14, -3664(%rbp)
	vmovdqa	%ymm5, -3376(%rbp)
	vpcmpeqd	%xmm0, %xmm0, %xmm0
	vmovdqa	%ymm15, -3696(%rbp)
	vmovdqa	%ymm1, -3536(%rbp)
	movb	$0, -3344(%rbp)
	movq	$0, -3624(%rbp)
	movl	%edi, -3736(%rbp)
	vpxor	%xmm14, %xmm14, %xmm14
	leaq	2(%r9), %rax
	movl	%r8d, -3728(%rbp)
	vpxor	.LC31(%rip), %xmm2, %xmm5
	movq	%rax, -3632(%rbp)
	imulq	$10752, %rdx, %rax
	leaq	(%rcx,%rax), %r12
	leaq	168(%rcx,%rax), %rsi
	leaq	296(%rcx,%rax), %r11
	leaq	312(%rcx,%rax), %rax
	addq	%rbx, %rax
	addq	%rbx, %rsi
	addq	%rbx, %r11
	leaq	(%rbx,%r12), %rcx
	movq	%rax, -3440(%rbp)
	leaq	128(%rbx,%r12), %r15
	leaq	144(%rbx,%r12), %r14
	vmovdqa	%xmm5, -3408(%rbp)
	vmovq	.LC4(%rip), %xmm5
	vpxor	%xmm5, %xmm6, %xmm6
	vpxor	%xmm5, %xmm5, %xmm5
	vmovdqa	%xmm5, -3312(%rbp)
	vpabsb	%xmm0, %xmm5
	vmovdqa	%xmm6, %xmm15
	vmovdqa	%xmm5, -3616(%rbp)
.L54:
	vmovdqa	-208(%rbp), %ymm0
	vmovdqa	-3536(%rbp), %ymm6
	movq	-3440(%rbp), %rax
	vmovdqu	%ymm0, (%rcx)
	vmovdqa	-176(%rbp), %ymm0
	vmovdqu	%ymm0, 32(%rcx)
	vmovdqa	-144(%rbp), %ymm0
	vmovdqu	%ymm0, 64(%rcx)
	vmovdqa	-112(%rbp), %ymm0
	vmovdqu	%ymm0, 96(%rcx)
	vmovdqu	-88(%rbp), %ymm0
	vmovdqu	%ymm0, 120(%rcx)
	vmovdqu	%ymm6, (%rsi)
	vmovdqa	-3568(%rbp), %ymm6
	vmovdqu	%ymm6, 32(%rsi)
	vmovdqa	-3600(%rbp), %ymm6
	vmovdqu	%ymm6, 64(%rsi)
	vmovdqa	-3376(%rbp), %ymm6
	vmovdqu	%ymm6, 96(%rsi)
	vmovdqa	-3408(%rbp), %xmm6
	vmovdqu	%xmm6, (%r11)
	vmovq	%xmm15, (%rax)
	vmovdqu	(%rcx), %ymm1
	vpmovzxbw	%xmm1, %ymm2
	vextracti128	$0x1, %ymm1, %xmm5
	vpmovzxwd	%xmm2, %ymm4
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm5, %ymm5
	vpmovzxwd	%xmm2, %ymm2
	vpmovzxwd	%xmm5, %ymm3
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%ymm2, %ymm4, %ymm0
	vpmulld	.LC6(%rip), %ymm4, %ymm4
	vpmovzxwd	%xmm5, %ymm5
	vpmulld	.LC7(%rip), %ymm2, %ymm2
	vpaddd	%ymm0, %ymm3, %ymm0
	vpmulld	.LC8(%rip), %ymm3, %ymm3
	vpaddd	%ymm0, %ymm5, %ymm0
	vpmulld	.LC9(%rip), %ymm5, %ymm5
	vpaddd	%ymm2, %ymm4, %ymm2
	vpaddd	%ymm2, %ymm3, %ymm3
	vpxor	(%rsi), %ymm1, %ymm2
	vpaddd	%ymm3, %ymm5, %ymm5
	vpcmpeqb	%ymm7, %ymm2, %ymm2
	vpcmpeqb	%ymm14, %ymm2, %ymm2
	vpand	%ymm8, %ymm2, %ymm2
	vpmovzxbw	%xmm2, %ymm1
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm2, %ymm2
	vpmovzxwd	%xmm1, %ymm1
	vpor	%ymm1, %ymm3, %ymm1
	vpmovzxwd	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vpor	%ymm1, %ymm3, %ymm3
	vmovdqu	32(%rcx), %ymm1
	vpmovzxwd	%xmm2, %ymm2
	vpor	%ymm3, %ymm2, %ymm2
	vpmovzxbw	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm4
	vpmovzxwd	%xmm3, %ymm10
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm4, %ymm4
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm10, %ymm0, %ymm0
	vpmovzxwd	%xmm4, %ymm6
	vpmulld	.LC10(%rip), %ymm10, %ymm10
	vpaddd	%ymm0, %ymm3, %ymm0
	vextracti128	$0x1, %ymm4, %xmm4
	vpmulld	.LC11(%rip), %ymm3, %ymm3
	vpmovzxwd	%xmm4, %ymm4
	vpaddd	%ymm0, %ymm6, %ymm0
	vpmulld	.LC12(%rip), %ymm6, %ymm6
	vpaddd	%ymm0, %ymm4, %ymm0
	vpmulld	.LC13(%rip), %ymm4, %ymm4
	vpxor	32(%rsi), %ymm1, %ymm1
	vpaddd	%ymm5, %ymm10, %ymm10
	vpcmpeqb	%ymm7, %ymm1, %ymm1
	vpaddd	%ymm10, %ymm3, %ymm3
	vpcmpeqb	%ymm14, %ymm1, %ymm1
	vpaddd	%ymm3, %ymm6, %ymm6
	vpand	%ymm8, %ymm1, %ymm1
	vpaddd	%ymm6, %ymm4, %ymm4
	vpmovzxbw	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm3, %ymm5
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm1, %ymm1
	vpor	%ymm2, %ymm5, %ymm5
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm1, %ymm2
	vpor	%ymm5, %ymm3, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpor	%ymm3, %ymm2, %ymm2
	vpmovzxwd	%xmm1, %ymm1
	vpor	%ymm2, %ymm1, %ymm1
	vmovdqu	64(%rcx), %ymm2
	vpmovzxbw	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm5
	vpxor	64(%rsi), %ymm2, %ymm2
	vpmovzxwd	%xmm3, %ymm10
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm5, %ymm5
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm10, %ymm0, %ymm0
	vpmulld	.LC14(%rip), %ymm10, %ymm10
	vpmovzxwd	%xmm5, %ymm6
	vpaddd	%ymm0, %ymm3, %ymm0
	vpmulld	.LC15(%rip), %ymm3, %ymm3
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%ymm0, %ymm6, %ymm0
	vpmulld	.LC16(%rip), %ymm6, %ymm6
	vpmovzxwd	%xmm5, %ymm5
	vpaddd	%ymm0, %ymm5, %ymm0
	vpmulld	.LC17(%rip), %ymm5, %ymm5
	vpcmpeqb	%ymm7, %ymm2, %ymm2
	vpcmpeqb	%ymm14, %ymm2, %ymm2
	vpand	%ymm8, %ymm2, %ymm2
	vpaddd	%ymm4, %ymm10, %ymm10
	vpaddd	%ymm10, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm6, %ymm6
	vpmovzxbw	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm3, %ymm4
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm2, %ymm2
	vpaddd	%ymm6, %ymm5, %ymm5
	vpor	%ymm1, %ymm4, %ymm4
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm2, %ymm1
	vpor	%ymm4, %ymm3, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vpor	%ymm3, %ymm1, %ymm1
	vpmovzxwd	%xmm2, %ymm2
	vpor	%ymm1, %ymm2, %ymm2
	vmovdqu	96(%rcx), %ymm1
	vpmovzxbw	%xmm1, %ymm4
	vextracti128	$0x1, %ymm1, %xmm3
	vpxor	96(%rsi), %ymm1, %ymm1
	vpmovzxwd	%xmm4, %ymm10
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxbw	%xmm3, %ymm3
	vpmovzxwd	%xmm4, %ymm4
	vpaddd	%ymm0, %ymm10, %ymm0
	vpmulld	.LC18(%rip), %ymm10, %ymm10
	vpmovzxwd	%xmm3, %ymm6
	vpaddd	%ymm0, %ymm4, %ymm0
	vpmulld	.LC19(%rip), %ymm4, %ymm4
	vextracti128	$0x1, %ymm3, %xmm3
	vpaddd	%ymm0, %ymm6, %ymm0
	vpmulld	.LC20(%rip), %ymm6, %ymm6
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm0, %ymm3, %ymm0
	vpmulld	.LC21(%rip), %ymm3, %ymm3
	vpcmpeqb	%ymm7, %ymm1, %ymm1
	vpcmpeqb	%ymm14, %ymm1, %ymm1
	vpand	%ymm8, %ymm1, %ymm1
	vpaddd	%ymm5, %ymm10, %ymm10
	vpaddd	%ymm10, %ymm4, %ymm4
	vpaddd	%ymm4, %ymm6, %ymm6
	vpmovzxbw	%xmm1, %ymm4
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm4, %ymm5
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm6, %ymm3, %ymm3
	vpor	%ymm2, %ymm5, %ymm5
	vpmovzxwd	%xmm4, %ymm4
	vpmovzxwd	%xmm1, %ymm2
	vpor	%ymm5, %ymm4, %ymm4
	vextracti128	$0x1, %ymm1, %xmm1
	vpor	%ymm4, %ymm2, %ymm2
	vpmovzxwd	%xmm1, %ymm1
	vpor	%ymm2, %ymm1, %ymm1
	vmovdqa	(%r15), %xmm2
	vpmovzxbw	%xmm2, %xmm5
	vpsrldq	$8, %xmm2, %xmm4
	vpxor	(%r11), %xmm2, %xmm2
	vpmovzxbw	%xmm4, %xmm4
	vpmovzxwd	%xmm5, %xmm10
	vpsrldq	$8, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpmovzxwd	%xmm4, %xmm12
	vpaddd	%xmm5, %xmm10, %xmm13
	vpmulld	.LC22(%rip), %xmm10, %xmm10
	vpsrldq	$8, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpmulld	.LC23(%rip), %xmm5, %xmm5
	vpaddd	%xmm12, %xmm13, %xmm13
	vpmulld	.LC24(%rip), %xmm12, %xmm12
	vpaddd	%xmm4, %xmm13, %xmm13
	vpmulld	.LC25(%rip), %xmm4, %xmm4
	vpaddd	%xmm0, %xmm13, %xmm13
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm13, %xmm0
	vpcmpeqb	.LC31(%rip), %xmm2, %xmm2
	vpcmpeqb	-3312(%rbp), %xmm2, %xmm2
	vpand	-3616(%rbp), %xmm2, %xmm2
	vpaddd	%xmm5, %xmm10, %xmm5
	vpaddd	%xmm12, %xmm5, %xmm12
	vpaddd	%xmm4, %xmm12, %xmm4
	vpaddd	%xmm3, %xmm4, %xmm5
	vextracti128	$0x1, %ymm3, %xmm3
	vpaddd	%xmm3, %xmm5, %xmm5
	vpmovzxbw	%xmm2, %xmm3
	vpsrldq	$8, %xmm2, %xmm2
	vpmovzxbw	%xmm2, %xmm2
	vpmovzxwd	%xmm3, %xmm4
	vpsrldq	$8, %xmm3, %xmm3
	vpmovzxwd	%xmm3, %xmm3
	vpor	%xmm3, %xmm4, %xmm3
	vpmovzxwd	%xmm2, %xmm4
	vpsrldq	$8, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm2
	vpor	%xmm4, %xmm3, %xmm4
	vpor	%xmm2, %xmm4, %xmm2
	vpor	%xmm1, %xmm2, %xmm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpor	%xmm1, %xmm3, %xmm3
	vmovq	(%r14), %xmm1
	vpmovzxbw	%xmm1, %xmm4
	vpsrlq	$32, %xmm1, %xmm2
	vpmovzxbw	%xmm2, %xmm2
	vpxor	%xmm15, %xmm1, %xmm1
	vpmovzxwd	%xmm4, %xmm12
	vpsrlq	$32, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpmovzxwd	%xmm2, %xmm6
	vpaddd	%xmm4, %xmm12, %xmm10
	vpsrlq	$32, %xmm2, %xmm2
	vpmulld	%xmm11, %xmm12, %xmm12
	vpmovzxwd	%xmm2, %xmm2
	vpaddd	%xmm6, %xmm10, %xmm10
	vpaddd	%xmm2, %xmm10, %xmm10
	vpaddd	%xmm0, %xmm10, %xmm13
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm13, %xmm0
	vmovq	.LC27(%rip), %xmm13
	vpmulld	%xmm13, %xmm4, %xmm4
	vmovq	.LC28(%rip), %xmm13
	vpaddd	%xmm4, %xmm12, %xmm4
	vpmulld	%xmm13, %xmm6, %xmm6
	vpaddd	%xmm6, %xmm4, %xmm6
	vmovq	.LC29(%rip), %xmm4
	vpmulld	%xmm4, %xmm2, %xmm2
	vpaddd	%xmm2, %xmm6, %xmm2
	vmovq	.LC4(%rip), %xmm6
	vpaddd	%xmm5, %xmm2, %xmm4
	vpsrldq	$8, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm4, %xmm5
	vpcmpeqb	%xmm6, %xmm1, %xmm1
	vmovq	-3624(%rbp), %xmm6
	vpcmpeqb	%xmm6, %xmm1, %xmm1
	vmovq	.LC5(%rip), %xmm6
	vpand	%xmm6, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm2
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm2, %xmm4
	vpsrlq	$32, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm2
	vpor	%xmm2, %xmm4, %xmm2
	vpmovzxwd	%xmm1, %xmm4
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm1
	vpor	%xmm4, %xmm2, %xmm4
	vpor	%xmm1, %xmm4, %xmm1
	vpor	%xmm3, %xmm1, %xmm2
	vpsrlq	$32, %xmm5, %xmm1
	vpaddd	%xmm1, %xmm5, %xmm5
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm3, %xmm3
	vpor	%xmm3, %xmm2, %xmm3
	vmovd	%xmm5, %r8d
	cmpl	-3472(%rbp), %r8d
	vmovd	%xmm0, %eax
	sete	%r8b
	cmpl	-3504(%rbp), %eax
	sete	%al
	testb	%al, %r8b
	je	.L52
	vpsrlq	$32, %xmm3, %xmm0
	vpor	%xmm0, %xmm3, %xmm3
	vmovd	%xmm3, %eax
	testl	%eax, %eax
	je	.L257
.L52:
	incq	%r9
	cmpq	-3632(%rbp), %r9
	movb	$1, -3344(%rbp)
	jne	.L54
	imulq	$336, %r13, %r13
	leaq	24+w.2(%rip), %rax
	vmovdqa	-3664(%rbp), %ymm14
	vmovdqa	-3696(%rbp), %ymm15
	imulq	$10752, %rdx, %rdx
	leaq	296(%r13,%rdx), %rcx
	leaq	128(%r13,%rdx), %rdx
	vmovq	%xmm9, (%rax,%rcx)
	vmovq	%xmm9, (%rax,%rdx)
	movq	%r9, 86312(%rbx)
	jmp	.L50
.L257:
	cmpb	$0, -3344(%rbp)
	leaq	24+w.2(%rip), %rax
	vmovdqa	-3664(%rbp), %ymm14
	vmovdqa	-3696(%rbp), %ymm15
	movl	-3728(%rbp), %r8d
	vmovq	%xmm9, 296(%rax,%r12)
	vmovq	%xmm9, 128(%rax,%r12)
	movl	-3736(%rbp), %edi
	je	.L53
	movq	%r9, 86312(%rbx)
.L53:
	movl	-3704(%rbp), %esi
	movq	%rdx, %rax
	salq	$5, %rax
	incl	86304(%rbx)
	incq	152896(%rbx)
	leaq	(%rbx,%rax), %rcx
	addq	%r13, %rax
	incq	152912(%rbx)
	movb	$1, 86016(%rcx,%r13)
	leaq	sqb_item_at(%rip), %rcx
	movl	$-131071, 151872(%rbx,%rax,4)
	movl	%esi, (%rcx,%rax,4)
	leal	1(%rdi), %ecx
	movq	-3720(%rbp), %rax
	movl	%ecx, 86272(%rbx,%rdx,4)
	movq	-3712(%rbp), %rcx
	salq	$4, %rax
	movq	%rcx, (%rbx,%rax)
	movb	%r8b, 8(%rbx,%rax)
	movb	%dil, 9(%rbx,%rax)
	movb	$1, 10(%rbx,%rax)
	movslq	%esi, %rax
	leaq	sqw_item_slot_b(%rip), %rsi
	movl	%r8d, (%rsi,%rax,4)
	leaq	sqw_item_slot_g(%rip), %rsi
	movl	%edi, (%rsi,%rax,4)
	jmp	.L50
	.p2align 4
	.p2align 3
.L255:
	movzbl	8(%rax), %r13d
	movzbl	9(%rax), %r12d
	movzbl	%r13b, %r14d
	movzbl	%r12b, %r15d
	imulq	$336, %r15, %rcx
	imulq	$10752, %r14, %rsi
	addq	%rsi, %rcx
	cmpl	$-559063315, 164(%rbx,%rcx)
	je	.L49
	vmovdqa	%ymm15, -3568(%rbp)
	vmovdqa	%ymm14, -3536(%rbp)
	vmovdqa	%ymm4, -3504(%rbp)
	leaq	(%rbx,%rcx), %rdi
	vmovdqa	%ymm5, -3472(%rbp)
	vmovdqa	%ymm8, -3440(%rbp)
	vmovq	%xmm6, -3408(%rbp)
	movl	$152, %edx
	vmovdqa	%xmm2, -3376(%rbp)
	vmovdqa	%ymm3, -3344(%rbp)
	leaq	-368(%rbp), %rsi
	vzeroupper
	call	memcmp@PLT
	leaq	-216(%rbp), %r10
	testl	%eax, %eax
	vmovdqa	-3344(%rbp), %ymm3
	vmovdqa	-3376(%rbp), %xmm2
	vmovq	-3408(%rbp), %xmm6
	vmovdqa	-3440(%rbp), %ymm8
	vmovdqa	-3472(%rbp), %ymm5
	vmovdqa	-3504(%rbp), %ymm4
	vmovdqa	-3536(%rbp), %ymm14
	vmovdqa	-3568(%rbp), %ymm15
	jne	.L49
	salq	$5, %r14
	leaq	sqw_item_slot_b(%rip), %rdi
	leaq	37968(%r15,%r14), %rcx
	movzwl	(%rbx,%rcx,4), %edx
	incl	%edx
	movl	%edx, %eax
	notl	%eax
	sall	$16, %eax
	orl	%edx, %eax
	movl	%eax, (%rbx,%rcx,4)
	movl	$1, %eax
	vmovq	%rax, %xmm0
	movslq	-3704(%rbp), %rax
	vpunpcklqdq	%xmm0, %xmm0, %xmm0
	vpaddq	152896(%rbx), %xmm0, %xmm0
	movl	%r13d, (%rdi,%rax,4)
	leaq	sqw_item_slot_g(%rip), %rdi
	movl	%r12d, (%rdi,%rax,4)
	vmovdqa	%xmm0, 152896(%rbx)
	jmp	.L50
.L256:
	movl	-3768(%rbp), %esi
	vpxor	%xmm0, %xmm0, %xmm0
	vxorps	%xmm2, %xmm2, %xmm2
	movq	$0, -3120(%rbp)
	vmovdqa	%ymm0, -3280(%rbp)
	vmovdqa	%ymm0, -3248(%rbp)
	vmovdqa	%ymm0, -3216(%rbp)
	vmovdqa	%ymm0, -3184(%rbp)
	vmovdqa	%ymm0, -3152(%rbp)
	vmovdqu	%ymm0, -3104(%rbp)
	vmovdqu	%ymm0, -3072(%rbp)
	vmovdqu	%ymm0, -3040(%rbp)
	vmovdqu	%ymm0, -3008(%rbp)
	vmovdqu	%ymm0, -2976(%rbp)
	movq	$0, -2944(%rbp)
	testl	%esi, %esi
	jle	.L163
	movq	%rbx, -3312(%rbp)
	movq	$0, -3568(%rbp)
	movq	$0, -3664(%rbp)
	xorl	%r12d, %r12d
	movq	$0, -3696(%rbp)
	movq	$0, -3728(%rbp)
	movq	$0, -3776(%rbp)
	movq	$0, -3712(%rbp)
	movq	$0, -3736(%rbp)
	movq	$0, -3784(%rbp)
	movq	$0, -3800(%rbp)
	movq	$0, -3792(%rbp)
	movq	%r14, -3296(%rbp)
	movq	%r15, -3408(%rbp)
	movq	%r11, -3344(%rbp)
	vmovaps	%xmm2, -3616(%rbp)
	vmovdqa	%ymm14, -3376(%rbp)
	vmovdqa	%ymm15, -3536(%rbp)
	movq	-3760(%rbp), %rbx
.L109:
	movl	%r12d, %edx
	movl	%r12d, %eax
	xorl	%r15d, %r15d
	imulq	$613566757, %rdx, %rdx
	shrq	$32, %rdx
	subl	%edx, %eax
	shrl	%eax
	addl	%edx, %eax
	shrl	$2, %eax
	leal	0(,%rax,8), %edx
	subl	%eax, %edx
	movl	%r12d, %eax
	subl	%edx, %eax
	cmpl	$2, %eax
	jle	.L66
	movl	$1, %r15d
	cmpl	$3, %eax
	je	.L66
	xorl	%r15d, %r15d
	cmpl	$4, %eax
	setne	%r15b
	addl	$2, %r15d
.L66:
	movq	-3344(%rbp), %rdi
	movl	$152920, %edx
	leaq	clean.1(%rip), %rsi
	vzeroupper
	call	memcpy@PLT
	leaq	w.2(%rip), %rax
	xorl	%r9d, %r9d
	xorl	%esi, %esi
	movq	%rax, -3344(%rbp)
	movq	%rax, %rdx
	.p2align 4
	.p2align 3
.L69:
	xorl	%eax, %eax
	.p2align 6
	.p2align 4
	.p2align 3
.L68:
	cmpb	$0, 86016(%rdx,%rax)
	je	.L67
	movl	%r9d, %edi
	movslq	%esi, %rcx
	incl	%esi
	orl	%eax, %edi
	movl	%edi, -2928(%rbp,%rcx,4)
.L67:
	incq	%rax
	cmpq	$32, %rax
	jne	.L68
	addl	$256, %r9d
	addq	$32, %rdx
	cmpl	$2048, %r9d
	jne	.L69
	movq	-3744(%rbp), %rcx
	movq	-3752(%rbp), %rax
	xorl	%edx, %edx
	movq	%r13, %r9
	movq	-3296(%rbp), %rdi
	movq	-3752(%rbp), %r14
	movl	%r15d, -1904(%rbp)
	addq	%rcx, %rax
	movq	%rcx, %r11
	rorx	$47, %rax, %rax
	xorq	%rcx, %rdi
	xorq	%r13, %r14
	divl	%esi
	movq	%r13, %rax
	xorq	%r14, %r11
	xorq	%rdi, %r9
	salq	$17, %rax
	rorx	$19, %r14, %r14
	movq	%r9, %r13
	movq	%r11, %r10
	xorq	%rdi, %rax
	movq	%r9, %rdi
	salq	$17, %r9
	xorq	%r14, %r13
	xorq	%r11, %rax
	xorq	%r13, %r10
	rorx	$19, %r13, %r13
	xorq	%rax, %r9
	xorq	%rax, %rdi
	movq	%r10, %rax
	movl	-2928(%rbp,%rdx,4), %esi
	leaq	(%r11,%r14), %rdx
	movq	%r9, %r11
	movq	%rdi, %r9
	xorq	%r10, %r11
	addq	%r13, %r10
	xorq	%r13, %r9
	movq	%rdi, %r14
	rorx	$47, %r10, %r10
	salq	$17, %rdi
	xorq	%r9, %rax
	xorq	%r11, %r14
	movl	%r10d, %r13d
	xorq	%r11, %rdi
	rorx	$19, %r9, %r9
	rorx	$47, %rdx, %rdx
	shrl	$3, %r13d
	xorq	%rax, %rdi
	movl	%esi, %r8d
	movzbl	%sil, %esi
	imulq	$452101821, %r13, %r13
	movl	%esi, -1896(%rbp)
	movl	%esi, -3472(%rbp)
	movq	%rax, %rsi
	sarl	$8, %r8d
	andl	$1, %edx
	movl	%r8d, -1900(%rbp)
	movl	%r8d, -3504(%rbp)
	movl	%edx, -1892(%rbp)
	shrq	$33, %r13
	movl	%edx, -3440(%rbp)
	imull	$152, %r13d, %r13d
	subl	%r13d, %r10d
	movq	%r14, %r13
	movl	%r10d, -1888(%rbp)
	movq	%rdi, %r10
	movq	%r14, %rdi
	xorq	%r9, %rdi
	xorq	%r10, %r13
	xorq	%rdi, %rsi
	addq	%r9, %rax
	rorx	$19, %rdi, %rdi
	movl	$2155905153, %r9d
	rorx	$47, %rax, %rax
	movq	%rdi, -3752(%rbp)
	salq	$17, %r14
	movq	%rsi, -3744(%rbp)
	movl	%eax, %edi
	xorq	%r10, %r14
	imulq	%r9, %rdi
	movq	%r14, -3296(%rbp)
	shrq	$39, %rdi
	leal	1(%rax,%rdi), %eax
	leaq	-1904(%rbp), %rdi
	movb	%al, -1884(%rbp)
	call	sqw_apply_event.constprop.0
	movl	%r15d, %eax
	incq	-3280(%rbp,%rax,8)
	call	sqb_sweep.constprop.0
	leaq	action.0(%rip), %rdi
	movslq	-3504(%rbp), %r8
	movl	-3472(%rbp), %esi
	addq	%rax, -3664(%rbp)
	movl	-3440(%rbp), %edx
	movl	%r8d, %eax
	sall	$5, %eax
	addl	%esi, %eax
	testl	%r15d, %r15d
	cltq
	movzbl	(%rdi,%rax), %eax
	je	.L70
	cmpl	$1, %r15d
	je	.L71
	cmpl	$2, %r15d
	je	.L72
	vpcmpeqd	%ymm4, %ymm4, %ymm4
	vmovdqa	-3600(%rbp), %ymm7
	vmovdqa	-3376(%rbp), %ymm5
	xorl	%r14d, %r14d
	incq	-3728(%rbp)
	movq	-3408(%rbp), %r11
	vpxor	%xmm2, %xmm2, %xmm2
	movl	$91, %ecx
	vpxor	%xmm6, %xmm6, %xmm6
	vpsrlw	$8, %ymm4, %ymm4
	jmp	.L73
	.p2align 4
	.p2align 3
.L83:
	addq	$4, %r11
	cmpq	%rbx, %r11
	je	.L258
.L73:
	movslq	(%r11), %rax
	leaq	sqw_item_slot_g(%rip), %rdi
	movslq	(%rdi,%rax,4), %r8
	leaq	sqw_item_slot_b(%rip), %rdi
	movq	%rax, %r10
	movslq	(%rdi,%rax,4), %rax
	imulq	$336, %r8, %r8
	imulq	$10752, %rax, %rax
	addq	%rax, %r8
	leaq	w.2(%rip), %rax
	leaq	(%rax,%r8), %rdi
	cmpl	$-559063315, 164(%rdi)
	je	.L83
	movq	%rdi, %r15
	negq	%r15
	andl	$31, %r15d
	je	.L167
	movl	%r10d, %eax
	leal	1(%r15), %r9d
	movl	$1, %edx
	sall	$4, %eax
	addl	%r10d, %eax
	jmp	.L79
	.p2align 5
	.p2align 4
	.p2align 3
.L168:
	movq	%rsi, %rdx
.L79:
	movl	%eax, %esi
	xorl	$-91, %esi
	cmpb	%sil, -1(%rdi,%rdx)
	jne	.L83
	leaq	1(%rdx), %rsi
	addl	$91, %eax
	cmpq	%rsi, %r9
	jne	.L168
	movl	$152, %r9d
	movl	%edx, %esi
	subl	%edx, %r9d
.L78:
	vmovd	%esi, %xmm1
	movl	%r10d, %eax
	leaq	w.2(%rip), %rdx
	vpbroadcastd	%xmm1, %ymm1
	vpaddd	.LC33(%rip), %ymm1, %ymm8
	vpaddd	.LC34(%rip), %ymm1, %ymm0
	sall	$4, %eax
	vpaddd	.LC36(%rip), %ymm1, %ymm9
	addl	%r10d, %eax
	vmovd	%eax, %xmm3
	movl	%r15d, %eax
	vpbroadcastb	%xmm3, %ymm3
	addq	%r8, %rax
	addq	%rdx, %rax
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm0, %ymm8, %ymm8
	vpaddd	.LC35(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm2, %ymm9, %ymm9
	vpermq	$216, %ymm8, %ymm8
	vpand	%ymm8, %ymm4, %ymm8
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpackusdw	%ymm9, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpand	%ymm0, %ymm4, %ymm0
	vpackuswb	%ymm0, %ymm8, %ymm8
	vpermq	$216, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm8, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm0
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsllw	$5, %ymm0, %ymm8
	vpand	%ymm8, %ymm7, %ymm8
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm3, %ymm0
	vpxor	%ymm5, %ymm0, %ymm0
	vpcmpeqb	(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L169
	vpaddd	.LC37(%rip), %ymm1, %ymm8
	vpaddd	.LC38(%rip), %ymm1, %ymm0
	vpaddd	.LC40(%rip), %ymm1, %ymm9
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm0, %ymm8, %ymm8
	vpaddd	.LC39(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm2, %ymm9, %ymm9
	vpermq	$216, %ymm8, %ymm8
	vpand	%ymm8, %ymm4, %ymm8
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpackusdw	%ymm9, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpand	%ymm0, %ymm4, %ymm0
	vpackuswb	%ymm0, %ymm8, %ymm8
	vpermq	$216, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm8, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm0
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsllw	$5, %ymm0, %ymm8
	vpand	%ymm7, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm3, %ymm0
	vpxor	%ymm5, %ymm0, %ymm0
	vpcmpeqb	32(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L170
	vpaddd	.LC41(%rip), %ymm1, %ymm8
	vpaddd	.LC42(%rip), %ymm1, %ymm0
	vpaddd	.LC44(%rip), %ymm1, %ymm9
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm0, %ymm8, %ymm8
	vpaddd	.LC43(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm2, %ymm9, %ymm9
	vpermq	$216, %ymm8, %ymm8
	vpand	%ymm8, %ymm4, %ymm8
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpackusdw	%ymm9, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpand	%ymm0, %ymm4, %ymm0
	vpackuswb	%ymm0, %ymm8, %ymm8
	vpermq	$216, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm8, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm0
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsllw	$5, %ymm0, %ymm8
	vpand	%ymm7, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm3, %ymm0
	vpxor	%ymm5, %ymm0, %ymm0
	vpcmpeqb	64(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L171
	vpaddd	.LC45(%rip), %ymm1, %ymm0
	vpaddd	.LC46(%rip), %ymm1, %ymm8
	vpaddd	.LC47(%rip), %ymm1, %ymm9
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpackusdw	%ymm8, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm8
	vpaddd	.LC48(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm2, %ymm9, %ymm1
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpackusdw	%ymm0, %ymm1, %ymm1
	vpand	%ymm8, %ymm4, %ymm0
	vpermq	$216, %ymm1, %ymm1
	vpand	%ymm1, %ymm4, %ymm1
	vpackuswb	%ymm1, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm1
	vpaddb	%ymm1, %ymm1, %ymm1
	vpaddb	%ymm0, %ymm1, %ymm0
	vpsllw	$5, %ymm0, %ymm1
	vpand	%ymm7, %ymm1, %ymm1
	vpaddb	%ymm1, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm3, %ymm0
	vpxor	%ymm5, %ymm0, %ymm0
	vpcmpeqb	96(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L172
	leal	128(%rsi), %eax
	addl	$-128, %r9d
.L81:
	movl	%eax, %r8d
	imull	%ecx, %eax
	movl	%r10d, %esi
	sall	$4, %esi
	leaq	(%rdi,%r8), %rdx
	addl	%r10d, %esi
	addl	%esi, %eax
	leal	-1(%r9), %esi
	addq	%r8, %rsi
	leaq	1(%rdi,%rsi), %rdi
	.p2align 5
	.p2align 4
	.p2align 3
.L84:
	movl	%eax, %esi
	xorl	$-91, %esi
	cmpb	%sil, (%rdx)
	jne	.L83
	incq	%rdx
	addl	$91, %eax
	cmpq	%rdx, %rdi
	jne	.L84
	addq	$4, %r11
	incq	%r14
	cmpq	%rbx, %r11
	jne	.L73
.L258:
	xorl	%eax, %eax
	cmpq	$256, %r14
	sete	%al
	addq	%rax, -3776(%rbp)
.L74:
	movq	86320+w.2(%rip), %rax
	xorl	%edx, %edx
	vpcmpeqd	%ymm4, %ymm4, %ymm4
	vmovdqa	-3600(%rbp), %ymm7
	vmovdqa	-3376(%rbp), %ymm5
	vpxor	%xmm2, %xmm2, %xmm2
	vpxor	%xmm6, %xmm6, %xmm6
	movl	$91, %r11d
	movq	-3408(%rbp), %r10
	vpsrlw	$8, %ymm4, %ymm4
	testq	%rax, %rax
	cmovs	%rdx, %rax
	xorl	%r14d, %r14d
	addq	%rax, -3696(%rbp)
	jmp	.L108
	.p2align 4
	.p2align 3
.L106:
	addq	$4, %r10
	cmpq	%rbx, %r10
	je	.L259
.L108:
	movslq	(%r10), %rax
	leaq	sqw_item_slot_b(%rip), %rsi
	leaq	sqw_item_slot_g(%rip), %rdi
	movslq	(%rdi,%rax,4), %rdi
	movq	%rax, %r9
	movslq	(%rsi,%rax,4), %rax
	imulq	$336, %rdi, %rdi
	imulq	$10752, %rax, %rax
	addq	%rax, %rdi
	leaq	w.2(%rip), %rax
	leaq	(%rax,%rdi), %rsi
	cmpl	$-559063315, 164(%rsi)
	je	.L106
	movq	%rsi, %r15
	negq	%r15
	andl	$31, %r15d
	je	.L177
	movl	%r9d, %eax
	leal	1(%r15), %r8d
	movl	$1, %edx
	sall	$4, %eax
	addl	%r9d, %eax
	jmp	.L102
	.p2align 5
	.p2align 4
	.p2align 3
.L178:
	movq	%rcx, %rdx
.L102:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, -1(%rsi,%rdx)
	jne	.L106
	leaq	1(%rdx), %rcx
	addl	$91, %eax
	cmpq	%rcx, %r8
	jne	.L178
	movl	$152, %r8d
	movl	%edx, %ecx
	subl	%edx, %r8d
.L101:
	vmovd	%ecx, %xmm1
	movl	%r9d, %edx
	movl	%r15d, %eax
	vpbroadcastd	%xmm1, %ymm1
	vpaddd	.LC33(%rip), %ymm1, %ymm8
	vpaddd	.LC34(%rip), %ymm1, %ymm0
	sall	$4, %edx
	vpaddd	.LC36(%rip), %ymm1, %ymm9
	addl	%r9d, %edx
	addq	%rdi, %rax
	leaq	w.2(%rip), %rdi
	vmovd	%edx, %xmm3
	addq	%rdi, %rax
	vpbroadcastb	%xmm3, %ymm3
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm0, %ymm8, %ymm8
	vpaddd	.LC35(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm2, %ymm9, %ymm9
	vpermq	$216, %ymm8, %ymm8
	vpand	%ymm8, %ymm4, %ymm8
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpackusdw	%ymm9, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpand	%ymm0, %ymm4, %ymm0
	vpackuswb	%ymm0, %ymm8, %ymm8
	vpermq	$216, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm8, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm0
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsllw	$5, %ymm0, %ymm8
	vpand	%ymm8, %ymm7, %ymm8
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm3, %ymm0
	vpxor	%ymm5, %ymm0, %ymm0
	vpcmpeqb	(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L179
	vpaddd	.LC37(%rip), %ymm1, %ymm8
	vpaddd	.LC38(%rip), %ymm1, %ymm0
	vpaddd	.LC40(%rip), %ymm1, %ymm9
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm0, %ymm8, %ymm8
	vpaddd	.LC39(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm2, %ymm9, %ymm9
	vpermq	$216, %ymm8, %ymm8
	vpand	%ymm8, %ymm4, %ymm8
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpackusdw	%ymm9, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpand	%ymm0, %ymm4, %ymm0
	vpackuswb	%ymm0, %ymm8, %ymm8
	vpermq	$216, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm8, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm0
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsllw	$5, %ymm0, %ymm8
	vpand	%ymm7, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm3, %ymm0
	vpxor	%ymm5, %ymm0, %ymm0
	vpcmpeqb	32(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L180
	vpaddd	.LC41(%rip), %ymm1, %ymm8
	vpaddd	.LC42(%rip), %ymm1, %ymm0
	vpaddd	.LC44(%rip), %ymm1, %ymm9
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpackusdw	%ymm0, %ymm8, %ymm8
	vpaddd	.LC43(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm2, %ymm9, %ymm9
	vpermq	$216, %ymm8, %ymm8
	vpand	%ymm8, %ymm4, %ymm8
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpackusdw	%ymm9, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpand	%ymm0, %ymm4, %ymm0
	vpackuswb	%ymm0, %ymm8, %ymm8
	vpermq	$216, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm8, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm0
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsllw	$5, %ymm0, %ymm8
	vpand	%ymm7, %ymm8, %ymm8
	vpaddb	%ymm8, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm3, %ymm0
	vpxor	%ymm5, %ymm0, %ymm0
	vpcmpeqb	64(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L181
	vpaddd	.LC45(%rip), %ymm1, %ymm0
	vpaddd	.LC46(%rip), %ymm1, %ymm8
	vpaddd	.LC47(%rip), %ymm1, %ymm9
	vpblendw	$170, %ymm2, %ymm8, %ymm8
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpackusdw	%ymm8, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm8
	vpaddd	.LC48(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm2, %ymm9, %ymm1
	vpblendw	$170, %ymm2, %ymm0, %ymm0
	vpackusdw	%ymm0, %ymm1, %ymm1
	vpand	%ymm8, %ymm4, %ymm0
	vpermq	$216, %ymm1, %ymm1
	vpand	%ymm1, %ymm4, %ymm1
	vpackuswb	%ymm1, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm1
	vpaddb	%ymm1, %ymm1, %ymm1
	vpaddb	%ymm0, %ymm1, %ymm0
	vpsllw	$5, %ymm0, %ymm1
	vpand	%ymm7, %ymm1, %ymm1
	vpaddb	%ymm1, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm3, %ymm0
	vpxor	%ymm5, %ymm0, %ymm0
	vpcmpeqb	96(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm6, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L182
	leal	128(%rcx), %eax
	addl	$-128, %r8d
.L104:
	movl	%eax, %edi
	imull	%r11d, %eax
	movl	%r9d, %ecx
	sall	$4, %ecx
	leaq	(%rsi,%rdi), %rdx
	addl	%r9d, %ecx
	addl	%ecx, %eax
	leal	-1(%r8), %ecx
	addq	%rdi, %rcx
	leaq	1(%rsi,%rcx), %rsi
	.p2align 5
	.p2align 4
	.p2align 3
.L107:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, (%rdx)
	jne	.L106
	incq	%rdx
	addl	$91, %eax
	cmpq	%rdx, %rsi
	jne	.L107
	addq	$4, %r10
	incq	%r14
	cmpq	%rbx, %r10
	jne	.L108
.L259:
	movq	-3568(%rbp), %rax
	incl	%r12d
	addq	$256, %rax
	subq	%r14, %rax
	cmpl	%r12d, -3768(%rbp)
	movq	%rax, -3568(%rbp)
	jne	.L109
	movl	-3768(%rbp), %eax
	vmovaps	-3616(%rbp), %xmm2
	vmovdqa	-3376(%rbp), %ymm14
	vmovdqa	-3536(%rbp), %ymm15
	movq	-3296(%rbp), %r14
	movq	-3312(%rbp), %rbx
	movq	-3408(%rbp), %r15
	cmpl	$2, %eax
	jle	.L183
	movl	$2863311531, %edx
	vpxor	%xmm4, %xmm4, %xmm4
	movq	%rbx, -3816(%rbp)
	movq	$0, -3504(%rbp)
	imulq	%rdx, %rax
	movq	$0, -3616(%rbp)
	movq	$0, -3312(%rbp)
	movq	$0, -3624(%rbp)
	movq	$0, -3720(%rbp)
	movq	$0, -3472(%rbp)
	movq	$0, -3536(%rbp)
	vmovq	%xmm4, %rbx
	movl	$0, -3440(%rbp)
	movq	%r15, -3808(%rbp)
	vmovdqa	%ymm14, -3408(%rbp)
	shrq	$33, %rax
	vmovdqa	%ymm15, -3856(%rbp)
	movq	%rax, -3768(%rbp)
.L139:
	vmovq	%xmm4, -3344(%rbp)
	vmovaps	%xmm2, -3296(%rbp)
	movl	$152920, %edx
	leaq	w.2(%rip), %rdi
	leaq	clean.1(%rip), %rsi
	vzeroupper
	call	memcpy@PLT
	vmovaps	-3296(%rbp), %xmm2
	leaq	w.2(%rip), %rdx
	xorl	%edi, %edi
	vmovq	-3344(%rbp), %xmm4
	xorl	%r10d, %r10d
	.p2align 4
	.p2align 3
.L112:
	xorl	%eax, %eax
	.p2align 6
	.p2align 4
	.p2align 3
.L111:
	cmpb	$0, 86016(%rdx,%rax)
	je	.L110
	movl	%edi, %esi
	movslq	%r10d, %rcx
	incl	%r10d
	orl	%eax, %esi
	movl	%esi, -2928(%rbp,%rcx,4)
.L110:
	incq	%rax
	cmpq	$32, %rax
	jne	.L111
	addl	$256, %edi
	addq	$32, %rdx
	cmpl	$2048, %edi
	jne	.L112
	leaq	-1904(%rbp), %r12
	movl	%r10d, -3376(%rbp)
	movq	%rbx, -3632(%rbp)
	movq	-3752(%rbp), %r10
	movq	%r12, %r15
	movq	%r12, -3704(%rbp)
	movq	-3744(%rbp), %r12
	jmp	.L114
.L261:
	leaq	(%r8,%rdi), %rax
	vmovsd	.LC64(%rip), %xmm7
	movq	-3296(%rbp), %rcx
	movq	%r14, %rdx
	rorx	$47, %rax, %rax
	movq	-3344(%rbp), %rsi
	movl	$3, %r11d
	shrq	$11, %rax
	vcvtsi2sdq	%rax, %xmm2, %xmm0
	vmulsd	.LC61(%rip), %xmm0, %xmm0
	rorx	$19, %r13, %rax
	vcomisd	%xmm0, %xmm7
	jbe	.L113
	movl	$2, %r11d
	.p2align 4
	.p2align 3
.L113:
	xorq	%rsi, %rdx
	movq	%rax, %r9
	addq	%rsi, %rax
	movl	$2155905153, %ebx
	movq	%rdx, %r10
	movq	%rdx, %rdi
	rorx	$47, %rax, %rax
	xorl	%edx, %edx
	divl	-3376(%rbp)
	xorq	%rcx, %r9
	xorq	%rcx, %rdi
	salq	$17, %rcx
	movq	%r9, %r8
	xorq	%r10, %rcx
	rorx	$19, %r9, %r9
	movq	%rdi, %r10
	xorq	%rsi, %r8
	xorq	%r9, %r10
	movl	%r11d, (%r15)
	xorq	%r8, %rcx
	movq	%r8, %rsi
	addq	%r9, %r8
	xorq	%r10, %rsi
	rorx	$19, %r10, %r10
	rorx	$47, %r8, %r8
	andl	$1, %r8d
	movl	%r8d, 12(%r15)
	movl	-2928(%rbp,%rdx,4), %eax
	movl	%eax, %edx
	andl	$255, %eax
	sarl	$8, %edx
	movl	%eax, 8(%r15)
	movq	%rsi, %rax
	movl	%edx, 4(%r15)
	movq	%rdi, %rdx
	salq	$17, %rdi
	xorq	%rcx, %rdi
	xorq	%rcx, %rdx
	xorq	%rsi, %rdi
	addq	%r10, %rsi
	movq	%rdx, %rcx
	movq	%rdx, %r14
	rorx	$47, %rsi, %rsi
	xorq	%rdi, %r14
	xorq	%r10, %rcx
	salq	$17, %rdx
	movl	%esi, %r8d
	xorq	%rcx, %rax
	xorq	%rdi, %rdx
	rorx	$19, %rcx, %rcx
	shrl	$3, %r8d
	movq	%r14, %r10
	xorq	%rax, %rdx
	movq	%rax, %r12
	imulq	$452101821, %r8, %r8
	movq	%r14, %r13
	movq	%r15, %rdi
	shrq	$33, %r8
	imull	$152, %r8d, %r8d
	subl	%r8d, %esi
	xorq	%rcx, %r10
	addq	%rcx, %rax
	salq	$17, %r14
	rorx	$47, %rax, %rax
	xorq	%rdx, %r13
	xorq	%rdx, %r14
	movl	%esi, 16(%r15)
	movl	%eax, %edx
	addq	$24, %r15
	xorq	%r10, %r12
	rorx	$19, %r10, %r10
	imulq	%rbx, %rdx
	shrq	$39, %rdx
	leal	1(%rax,%rdx), %eax
	movb	%al, -4(%r15)
	call	sqw_apply_event.constprop.0
	leaq	-1616(%rbp), %rax
	incq	-3104(%rbp,%r11,8)
	cmpq	%rax, %r15
	je	.L260
.L114:
	xorq	%r12, %r14
	movq	%r10, %rax
	addq	%r12, %r10
	vmovsd	.LC62(%rip), %xmm7
	xorq	%r13, %rax
	movq	%r14, %rcx
	rorx	$47, %r10, %r10
	movq	%r13, %rdx
	xorq	%r13, %rcx
	movq	%rax, %rsi
	shrq	$11, %r10
	salq	$17, %rdx
	xorq	%r12, %rsi
	rorx	$19, %rax, %rax
	movq	%rcx, %rdi
	vcvtsi2sdq	%r10, %xmm2, %xmm0
	vmulsd	.LC61(%rip), %xmm0, %xmm0
	xorq	%r14, %rdx
	xorq	%rax, %rdi
	movq	%rsi, %r11
	movq	%rsi, %r8
	movq	%rcx, %rbx
	xorq	%rdx, %r11
	movq	%rcx, %r9
	xorq	%rdi, %r8
	salq	$17, %rbx
	xorq	%r11, %r9
	rorx	$19, %rdi, %rdi
	xorq	%r11, %rbx
	movq	%r8, %r11
	movq	%r9, %r14
	movq	%r9, %r13
	xorq	%rbx, %r11
	xorq	%rdi, %r13
	xorq	%r11, %r14
	movq	%r14, -3296(%rbp)
	movq	%r8, %r14
	xorq	%r13, %r14
	movq	%r14, -3344(%rbp)
	movq	%r9, %r14
	salq	$17, %r14
	xorq	%r11, %r14
	xorl	%r11d, %r11d
	vcomisd	%xmm0, %xmm7
	ja	.L113
	addq	%rsi, %rax
	vmovsd	.LC63(%rip), %xmm7
	rorx	$47, %rax, %rax
	shrq	$11, %rax
	vcvtsi2sdq	%rax, %xmm2, %xmm0
	vmulsd	.LC61(%rip), %xmm0, %xmm0
	vcomisd	%xmm0, %xmm7
	jbe	.L261
	movq	%rdi, %rax
	movq	%rbx, %rdx
	movq	%r9, %rcx
	movq	%r8, %rsi
	movl	$1, %r11d
	jmp	.L113
.L260:
	movq	%r12, -3744(%rbp)
	vmovaps	%xmm2, -3344(%rbp)
	vmovq	%xmm4, -3296(%rbp)
	movq	-3632(%rbp), %rbx
	movq	%r10, -3752(%rbp)
	movq	-3704(%rbp), %r12
	call	sqb_sweep.constprop.0
	vmovaps	-3344(%rbp), %xmm2
	vmovdqa	-3856(%rbp), %ymm3
	vmovq	-3296(%rbp), %xmm4
	addq	%rax, -3616(%rbp)
	movq	-3472(%rbp), %rdi
	movq	-3536(%rbp), %rsi
	jmp	.L127
	.p2align 4
	.p2align 3
.L115:
	cmpl	$1, %eax
	je	.L262
.L123:
	addq	$24, %r12
	leaq	-1616(%rbp), %rax
	cmpq	%rax, %r12
	je	.L263
.L127:
	movslq	4(%r12), %rdx
	movslq	8(%r12), %rcx
	leaq	action.0(%rip), %r15
	movl	%edx, %eax
	sall	$5, %eax
	addl	%ecx, %eax
	cltq
	movzbl	(%r15,%rax), %r8d
	movl	(%r12), %eax
	testl	%eax, %eax
	jne	.L115
	movslq	12(%r12), %rax
	cmpl	$1, %r8d
	sbbq	$-1, %rsi
	testl	%eax, %eax
	jne	.L117
	imulq	$336, %rcx, %rax
	leaq	w.2(%rip), %r11
	imulq	$10752, %rdx, %r8
	addq	%r8, %rax
	addq	%r11, %rax
	vmovdqu	(%rax), %ymm0
	vmovdqa	%ymm0, -208(%rbp)
	vmovdqu	32(%rax), %ymm0
	vmovdqa	%ymm0, -176(%rbp)
	vmovdqu	64(%rax), %ymm0
	vmovdqa	%ymm0, -144(%rbp)
	vmovdqu	96(%rax), %ymm0
	vmovdqa	%ymm0, -112(%rbp)
	vmovdqu	120(%rax), %ymm0
	vmovdqu	%ymm0, -88(%rbp)
.L118:
	salq	$5, %rdx
	vmovdqa	-3408(%rbp), %ymm6
	vpxor	%xmm5, %xmm5, %xmm5
	leaq	(%rdx,%rcx), %rax
	leaq	sqb_item_at(%rip), %rcx
	movl	(%rcx,%rax,4), %ecx
	movl	%ecx, %eax
	sall	$4, %eax
	addl	%ecx, %eax
	vmovd	%eax, %xmm0
	vpbroadcastb	%xmm0, %ymm0
	vpaddb	.LC49(%rip), %ymm0, %ymm1
	vpxor	%ymm6, %ymm1, %ymm1
	vpcmpeqb	-208(%rbp), %ymm1, %ymm1
	vpcmpeqb	%ymm5, %ymm1, %ymm1
	vptest	%ymm1, %ymm1
	jne	.L187
	vpaddb	.LC51(%rip), %ymm0, %ymm1
	vpxor	%ymm6, %ymm1, %ymm1
	vpcmpeqb	-176(%rbp), %ymm1, %ymm1
	vpcmpeqb	%ymm5, %ymm1, %ymm1
	vptest	%ymm1, %ymm1
	jne	.L188
	vpaddb	.LC52(%rip), %ymm0, %ymm1
	vpxor	%ymm6, %ymm1, %ymm1
	vpcmpeqb	-144(%rbp), %ymm1, %ymm1
	vpcmpeqb	%ymm5, %ymm1, %ymm1
	vptest	%ymm1, %ymm1
	jne	.L189
	vpaddb	.LC53(%rip), %ymm0, %ymm0
	movl	$24, %r8d
	movl	$128, %eax
	vpxor	%ymm6, %ymm0, %ymm0
	vpcmpeqb	-112(%rbp), %ymm0, %ymm0
	vpcmpeqb	%ymm5, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L264
.L120:
	movl	$91, %r10d
	movl	%eax, %r9d
	imull	%r10d, %eax
	movl	%ecx, %r10d
	leaq	-208(%rbp,%r9), %rdx
	sall	$4, %r10d
	addl	%r10d, %ecx
	addl	%ecx, %eax
	leal	-1(%r8), %ecx
	addq	%r9, %rcx
	leaq	-207(%rbp,%rcx), %r8
	.p2align 5
	.p2align 4
	.p2align 3
.L122:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, (%rdx)
	jne	.L123
	incq	%rdx
	addl	$91, %eax
	cmpq	%r8, %rdx
	jne	.L122
	addq	$24, %r12
	leaq	-1616(%rbp), %rax
	incq	-3720(%rbp)
	cmpq	%rax, %r12
	jne	.L127
.L263:
	movq	%rdi, -3472(%rbp)
	leaq	w.2(%rip), %rdi
	movq	%rsi, -3536(%rbp)
	movq	86320(%rdi), %rax
	testq	%rax, %rax
	jle	.L128
	movl	$-559063315, %esi
	addq	%rax, -3312(%rbp)
	vpcmpeqd	%ymm1, %ymm1, %ymm1
	leaq	86016(%rdi), %rcx
	vmovd	%esi, %xmm3
	movq	%rdi, %rdx
	movq	%rdi, %rax
	vpsrld	$16, %ymm1, %ymm1
	vpbroadcastd	%xmm3, %ymm3
	.p2align 4
	.p2align 3
.L129:
	vmovd	2180(%rax), %xmm7
	addq	$10752, %rax
	subq	$-128, %rdx
	vpinsrd	$1, -8236(%rax), %xmm7, %xmm5
	vmovd	-9244(%rax), %xmm7
	vpinsrd	$1, -8908(%rax), %xmm7, %xmm0
	vmovd	-9916(%rax), %xmm7
	vpinsrd	$1, -9580(%rax), %xmm7, %xmm6
	vmovd	-10588(%rax), %xmm7
	vpunpcklqdq	%xmm5, %xmm0, %xmm0
	vpinsrd	$1, -10252(%rax), %xmm7, %xmm5
	vmovd	-5884(%rax), %xmm7
	vpunpcklqdq	%xmm6, %xmm5, %xmm5
	vinserti128	$0x1, %xmm0, %ymm5, %ymm5
	vpcmpeqd	%ymm3, %ymm5, %ymm5
	vpmaskmovd	151744(%rdx), %ymm5, %ymm0
	vpand	%ymm1, %ymm0, %ymm6
	vpsrld	$16, %ymm0, %ymm0
	vpaddd	%ymm6, %ymm0, %ymm0
	vpcmpeqd	%ymm1, %ymm0, %ymm0
	vpand	%ymm5, %ymm0, %ymm0
	vpmovzxdq	%xmm6, %ymm5
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovsxdq	%xmm0, %ymm8
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxdq	%xmm6, %ymm6
	vpmovsxdq	%xmm0, %ymm0
	vpand	%ymm5, %ymm8, %ymm8
	vpinsrd	$1, -5548(%rax), %xmm7, %xmm5
	vmovd	-6556(%rax), %xmm7
	vpand	%ymm6, %ymm0, %ymm0
	vpaddq	%ymm0, %ymm8, %ymm8
	vpinsrd	$1, -6220(%rax), %xmm7, %xmm0
	vmovd	-7228(%rax), %xmm7
	vpinsrd	$1, -6892(%rax), %xmm7, %xmm6
	vmovd	-7900(%rax), %xmm7
	vpunpcklqdq	%xmm5, %xmm0, %xmm0
	vpinsrd	$1, -7564(%rax), %xmm7, %xmm5
	vpunpcklqdq	%xmm6, %xmm5, %xmm5
	vinserti128	$0x1, %xmm0, %ymm5, %ymm5
	vpcmpeqd	%ymm3, %ymm5, %ymm5
	vpmaskmovd	151776(%rdx), %ymm5, %ymm0
	vpand	%ymm1, %ymm0, %ymm7
	vpsrld	$16, %ymm0, %ymm0
	vpaddd	%ymm7, %ymm0, %ymm0
	vpcmpeqd	%ymm1, %ymm0, %ymm0
	vpand	%ymm5, %ymm0, %ymm0
	vpmovzxdq	%xmm7, %ymm5
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovsxdq	%xmm0, %ymm6
	vpmovzxdq	%xmm7, %ymm7
	vpand	%ymm5, %ymm6, %ymm6
	vextracti128	$0x1, %ymm0, %xmm5
	vpmovsxdq	%xmm5, %ymm5
	vpaddq	%ymm8, %ymm6, %ymm6
	vpand	%ymm7, %ymm5, %ymm5
	vmovd	-3196(%rax), %xmm7
	vpaddq	%ymm6, %ymm5, %ymm5
	vpinsrd	$1, -2860(%rax), %xmm7, %xmm6
	vmovd	-3868(%rax), %xmm7
	vpinsrd	$1, -3532(%rax), %xmm7, %xmm0
	vmovd	-4540(%rax), %xmm7
	vpinsrd	$1, -4204(%rax), %xmm7, %xmm7
	vpunpcklqdq	%xmm6, %xmm0, %xmm0
	vmovd	-5212(%rax), %xmm6
	vpinsrd	$1, -4876(%rax), %xmm6, %xmm6
	vpunpcklqdq	%xmm7, %xmm6, %xmm6
	vinserti128	$0x1, %xmm0, %ymm6, %ymm6
	vpcmpeqd	%ymm3, %ymm6, %ymm6
	vpmaskmovd	151808(%rdx), %ymm6, %ymm0
	vpand	%ymm1, %ymm0, %ymm7
	vpsrld	$16, %ymm0, %ymm0
	vpaddd	%ymm7, %ymm0, %ymm0
	vpmovzxdq	%xmm7, %ymm8
	vextracti128	$0x1, %ymm7, %xmm7
	vpcmpeqd	%ymm1, %ymm0, %ymm0
	vpmovzxdq	%xmm7, %ymm7
	vpand	%ymm6, %ymm0, %ymm0
	vpmovsxdq	%xmm0, %ymm6
	vpand	%ymm8, %ymm6, %ymm6
	vpaddq	%ymm5, %ymm6, %ymm6
	vextracti128	$0x1, %ymm0, %xmm5
	vpmovsxdq	%xmm5, %ymm5
	vpand	%ymm7, %ymm5, %ymm5
	vmovd	-508(%rax), %xmm7
	vpaddq	%ymm6, %ymm5, %ymm5
	vpinsrd	$1, -172(%rax), %xmm7, %xmm6
	vmovd	-1180(%rax), %xmm7
	vpinsrd	$1, -844(%rax), %xmm7, %xmm0
	vmovd	-1852(%rax), %xmm7
	vpinsrd	$1, -1516(%rax), %xmm7, %xmm7
	vpunpcklqdq	%xmm6, %xmm0, %xmm0
	vmovd	-2524(%rax), %xmm6
	vpinsrd	$1, -2188(%rax), %xmm6, %xmm6
	vpunpcklqdq	%xmm7, %xmm6, %xmm6
	vinserti128	$0x1, %xmm0, %ymm6, %ymm6
	vpcmpeqd	%ymm3, %ymm6, %ymm6
	vpmaskmovd	151840(%rdx), %ymm6, %ymm0
	vpand	%ymm1, %ymm0, %ymm7
	vpsrld	$16, %ymm0, %ymm0
	vpaddd	%ymm7, %ymm0, %ymm0
	vpmovzxdq	%xmm7, %ymm8
	vextracti128	$0x1, %ymm7, %xmm7
	vpcmpeqd	%ymm1, %ymm0, %ymm0
	vpmovzxdq	%xmm7, %ymm7
	vpand	%ymm6, %ymm0, %ymm0
	vpmovsxdq	%xmm0, %ymm6
	vextracti128	$0x1, %ymm0, %xmm0
	vpand	%ymm8, %ymm6, %ymm6
	vpmovsxdq	%xmm0, %ymm0
	vpaddq	%ymm5, %ymm6, %ymm5
	vpand	%ymm7, %ymm0, %ymm0
	vpaddq	%ymm5, %ymm0, %ymm0
	vextracti128	$0x1, %ymm0, %xmm5
	vpaddq	%xmm0, %xmm5, %xmm0
	vpsrldq	$8, %xmm0, %xmm5
	vpaddq	%xmm5, %xmm0, %xmm0
	vpaddq	%xmm0, %xmm4, %xmm4
	vmovq	%xmm4, %rbx
	cmpq	%rax, %rcx
	jne	.L129
.L128:
	vpcmpeqd	%ymm6, %ymm6, %ymm6
	vmovdqa	-3600(%rbp), %ymm9
	vmovdqa	-3408(%rbp), %ymm7
	movq	$0, -3296(%rbp)
	movq	-3808(%rbp), %r10
	vpxor	%xmm3, %xmm3, %xmm3
	movl	$91, %r12d
	vpsrlw	$8, %ymm6, %ymm6
	movq	-3760(%rbp), %rdi
	vpxor	%xmm8, %xmm8, %xmm8
	jmp	.L138
	.p2align 4
	.p2align 3
.L136:
	addq	$4, %r10
	cmpq	%rdi, %r10
	je	.L265
.L138:
	movslq	(%r10), %rax
	leaq	sqw_item_slot_g(%rip), %rsi
	movslq	(%rsi,%rax,4), %r8
	leaq	sqw_item_slot_b(%rip), %rsi
	movq	%rax, %r11
	movslq	(%rsi,%rax,4), %rax
	imulq	$336, %r8, %r8
	imulq	$10752, %rax, %rax
	addq	%rax, %r8
	leaq	w.2(%rip), %rax
	leaq	(%rax,%r8), %rsi
	cmpl	$-559063315, 164(%rsi)
	je	.L136
	movq	%rsi, %r15
	negq	%r15
	andl	$31, %r15d
	je	.L191
	movl	%r11d, %eax
	leal	1(%r15), %r9d
	movl	$1, %edx
	sall	$4, %eax
	addl	%r11d, %eax
	jmp	.L132
	.p2align 5
	.p2align 4
	.p2align 3
.L192:
	movq	%rcx, %rdx
.L132:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, -1(%rsi,%rdx)
	jne	.L136
	leaq	1(%rdx), %rcx
	addl	$91, %eax
	cmpq	%r9, %rcx
	jne	.L192
	movl	$152, %r9d
	movl	%edx, %ecx
	subl	%edx, %r9d
.L131:
	vmovd	%ecx, %xmm1
	movl	%r11d, %edx
	movl	%r15d, %eax
	leaq	w.2(%rip), %r15
	vpbroadcastd	%xmm1, %ymm1
	vpaddd	.LC33(%rip), %ymm1, %ymm10
	vpaddd	.LC34(%rip), %ymm1, %ymm0
	sall	$4, %edx
	vpaddd	.LC36(%rip), %ymm1, %ymm11
	addl	%r11d, %edx
	addq	%r8, %rax
	vmovd	%edx, %xmm5
	addq	%r15, %rax
	vpbroadcastb	%xmm5, %ymm5
	vpblendw	$170, %ymm3, %ymm0, %ymm0
	vpblendw	$170, %ymm3, %ymm10, %ymm10
	vpackusdw	%ymm0, %ymm10, %ymm10
	vpaddd	.LC35(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm3, %ymm11, %ymm11
	vpermq	$216, %ymm10, %ymm10
	vpand	%ymm10, %ymm6, %ymm10
	vpblendw	$170, %ymm3, %ymm0, %ymm0
	vpackusdw	%ymm11, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpand	%ymm0, %ymm6, %ymm0
	vpackuswb	%ymm0, %ymm10, %ymm10
	vpermq	$216, %ymm10, %ymm10
	vpaddb	%ymm10, %ymm10, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm0
	vpaddb	%ymm10, %ymm0, %ymm0
	vpsllw	$5, %ymm0, %ymm10
	vpand	%ymm10, %ymm9, %ymm10
	vpaddb	%ymm10, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm5, %ymm0
	vpxor	%ymm7, %ymm0, %ymm0
	vpcmpeqb	(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm8, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L193
	vpaddd	.LC37(%rip), %ymm1, %ymm10
	vpaddd	.LC38(%rip), %ymm1, %ymm0
	vpaddd	.LC40(%rip), %ymm1, %ymm11
	vpblendw	$170, %ymm3, %ymm0, %ymm0
	vpblendw	$170, %ymm3, %ymm10, %ymm10
	vpackusdw	%ymm0, %ymm10, %ymm10
	vpaddd	.LC39(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm3, %ymm11, %ymm11
	vpermq	$216, %ymm10, %ymm10
	vpand	%ymm10, %ymm6, %ymm10
	vpblendw	$170, %ymm3, %ymm0, %ymm0
	vpackusdw	%ymm11, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpand	%ymm0, %ymm6, %ymm0
	vpackuswb	%ymm0, %ymm10, %ymm10
	vpermq	$216, %ymm10, %ymm10
	vpaddb	%ymm10, %ymm10, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm0
	vpaddb	%ymm10, %ymm0, %ymm0
	vpsllw	$5, %ymm0, %ymm10
	vpand	%ymm9, %ymm10, %ymm10
	vpaddb	%ymm10, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm5, %ymm0
	vpxor	%ymm7, %ymm0, %ymm0
	vpcmpeqb	32(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm8, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L194
	vpaddd	.LC41(%rip), %ymm1, %ymm10
	vpaddd	.LC42(%rip), %ymm1, %ymm0
	vpaddd	.LC44(%rip), %ymm1, %ymm11
	vpblendw	$170, %ymm3, %ymm0, %ymm0
	vpblendw	$170, %ymm3, %ymm10, %ymm10
	vpackusdw	%ymm0, %ymm10, %ymm10
	vpaddd	.LC43(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm3, %ymm11, %ymm11
	vpermq	$216, %ymm10, %ymm10
	vpand	%ymm10, %ymm6, %ymm10
	vpblendw	$170, %ymm3, %ymm0, %ymm0
	vpackusdw	%ymm11, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpand	%ymm0, %ymm6, %ymm0
	vpackuswb	%ymm0, %ymm10, %ymm10
	vpermq	$216, %ymm10, %ymm10
	vpaddb	%ymm10, %ymm10, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm0
	vpaddb	%ymm10, %ymm0, %ymm0
	vpsllw	$5, %ymm0, %ymm10
	vpand	%ymm9, %ymm10, %ymm10
	vpaddb	%ymm10, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm5, %ymm0
	vpxor	%ymm7, %ymm0, %ymm0
	vpcmpeqb	64(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm8, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L195
	vpaddd	.LC45(%rip), %ymm1, %ymm0
	vpaddd	.LC46(%rip), %ymm1, %ymm10
	vpaddd	.LC47(%rip), %ymm1, %ymm11
	vpblendw	$170, %ymm3, %ymm10, %ymm10
	vpblendw	$170, %ymm3, %ymm0, %ymm0
	vpackusdw	%ymm10, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm10
	vpaddd	.LC48(%rip), %ymm1, %ymm0
	vpblendw	$170, %ymm3, %ymm11, %ymm1
	vpblendw	$170, %ymm3, %ymm0, %ymm0
	vpackusdw	%ymm0, %ymm1, %ymm1
	vpand	%ymm10, %ymm6, %ymm0
	vpermq	$216, %ymm1, %ymm1
	vpand	%ymm1, %ymm6, %ymm1
	vpackuswb	%ymm1, %ymm0, %ymm0
	vpermq	$216, %ymm0, %ymm0
	vpaddb	%ymm0, %ymm0, %ymm1
	vpaddb	%ymm1, %ymm1, %ymm1
	vpaddb	%ymm0, %ymm1, %ymm0
	vpsllw	$5, %ymm0, %ymm1
	vpand	%ymm9, %ymm1, %ymm1
	vpaddb	%ymm1, %ymm0, %ymm0
	vpsubb	%ymm0, %ymm5, %ymm0
	vpxor	%ymm7, %ymm0, %ymm0
	vpcmpeqb	96(%rax), %ymm0, %ymm0
	vpcmpeqb	%ymm8, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L196
	leal	128(%rcx), %eax
	addl	$-128, %r9d
.L134:
	movl	%eax, %r8d
	imull	%r12d, %eax
	movl	%r11d, %ecx
	sall	$4, %ecx
	leaq	(%r8,%rsi), %rdx
	addl	%r11d, %ecx
	addl	%ecx, %eax
	leal	-1(%r9), %ecx
	addq	%r8, %rcx
	leaq	1(%rsi,%rcx), %rsi
	.p2align 5
	.p2align 4
	.p2align 3
.L137:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, (%rdx)
	jne	.L136
	incq	%rdx
	addl	$91, %eax
	cmpq	%rsi, %rdx
	jne	.L137
	addq	$4, %r10
	incq	-3296(%rbp)
	cmpq	%rdi, %r10
	jne	.L138
.L265:
	movq	-3504(%rbp), %rax
	incl	-3440(%rbp)
	addq	$256, %rax
	subq	-3296(%rbp), %rax
	movq	%rax, -3504(%rbp)
	movl	-3440(%rbp), %eax
	cmpl	%eax, -3768(%rbp)
	jg	.L139
	movq	%rbx, %r12
	movq	-3816(%rbp), %rbx
.L65:
	vcvtsi2sdq	%rbx, %xmm2, %xmm0
	vmulsd	.LC67(%rip), %xmm0, %xmm0
	vmovaps	%xmm2, -3296(%rbp)
	movl	$256, %edx
	movq	%rbx, %rsi
	leaq	.LC68(%rip), %rdi
	movl	$1, %eax
	vzeroupper
	call	printf@PLT
	movq	-3264(%rbp), %rdx
	vxorpd	%xmm0, %xmm0, %xmm0
	vmovaps	-3296(%rbp), %xmm2
	testq	%rdx, %rdx
	je	.L140
	vcvtsi2sdq	-3784(%rbp), %xmm2, %xmm0
	vcvtsi2sdq	%rdx, %xmm2, %xmm1
	vdivsd	%xmm1, %xmm0, %xmm0
.L140:
	movq	-3784(%rbp), %rsi
	leaq	.LC69(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm2, -3296(%rbp)
	call	printf@PLT
	movq	-3280(%rbp), %rbx
	vmovaps	-3296(%rbp), %xmm2
	testq	%rbx, %rbx
	jne	.L141
	movq	-3792(%rbp), %rsi
	vxorpd	%xmm0, %xmm0, %xmm0
	xorl	%edx, %edx
	leaq	.LC70(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	vmovaps	-3296(%rbp), %xmm2
	vxorpd	%xmm0, %xmm0, %xmm0
.L142:
	movq	-3736(%rbp), %rsi
	movq	%rbx, %rdx
	leaq	.LC71(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm2, -3296(%rbp)
	call	printf@PLT
	movq	-3272(%rbp), %rbx
	vmovaps	-3296(%rbp), %xmm2
	testq	%rbx, %rbx
	jne	.L143
	movq	-3800(%rbp), %rsi
	vxorpd	%xmm0, %xmm0, %xmm0
	xorl	%edx, %edx
	leaq	.LC72(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	vmovaps	-3296(%rbp), %xmm2
	vxorpd	%xmm0, %xmm0, %xmm0
.L144:
	movq	-3712(%rbp), %rsi
	movq	%rbx, %rdx
	leaq	.LC73(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm2, -3296(%rbp)
	call	printf@PLT
	movq	-3664(%rbp), %rsi
	leaq	.LC74(%rip), %rdi
	xorl	%eax, %eax
	call	printf@PLT
	movq	-3696(%rbp), %rsi
	xorl	%eax, %eax
	leaq	.LC75(%rip), %rdi
	call	printf@PLT
	movq	-3728(%rbp), %rax
	vxorpd	%xmm0, %xmm0, %xmm0
	vmovaps	-3296(%rbp), %xmm2
	testq	%rax, %rax
	je	.L145
	vcvtsi2sdq	-3776(%rbp), %xmm2, %xmm0
	vcvtsi2sdq	%rax, %xmm2, %xmm1
	vdivsd	%xmm1, %xmm0, %xmm0
.L145:
	movq	-3776(%rbp), %rsi
	movq	-3728(%rbp), %rdx
	leaq	.LC76(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm2, -3296(%rbp)
	call	printf@PLT
	vmovdqa	-3104(%rbp), %xmm0
	movq	-3720(%rbp), %r13
	movq	-3536(%rbp), %rsi
	addq	-3624(%rbp), %r13
	addq	-3472(%rbp), %rsi
	vmovaps	-3296(%rbp), %xmm2
	vpsrldq	$8, %xmm0, %xmm1
	vpaddq	%xmm1, %xmm0, %xmm0
	vmovq	%xmm0, %rbx
	testq	%rbx, %rbx
	jne	.L146
	vxorpd	%xmm0, %xmm0, %xmm0
	xorl	%edx, %edx
	leaq	.LC77(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	vmovaps	-3296(%rbp), %xmm2
	vxorpd	%xmm0, %xmm0, %xmm0
.L147:
	movq	%rbx, %rdx
	movq	%r13, %rsi
	leaq	.LC78(%rip), %rdi
	vmovaps	%xmm2, -3296(%rbp)
	movl	$1, %eax
	call	printf@PLT
	movq	-3312(%rbp), %rax
	vxorpd	%xmm0, %xmm0, %xmm0
	testq	%rax, %rax
	je	.L148
	vmovaps	-3296(%rbp), %xmm2
	vcvtsi2sdq	%r12, %xmm2, %xmm0
	vcvtsi2sdq	%rax, %xmm2, %xmm2
	vdivsd	%xmm2, %xmm0, %xmm0
.L148:
	movq	-3616(%rbp), %r8
	movq	-3504(%rbp), %rcx
	movq	%r12, %rdx
	leaq	.LC79(%rip), %rdi
	movq	-3312(%rbp), %rsi
	movl	$1, %eax
	call	printf@PLT
	movq	-3568(%rbp), %rsi
	xorl	%eax, %eax
	leaq	.LC80(%rip), %rdi
	call	printf@PLT
	movq	-56(%rbp), %rax
	subq	%fs:40, %rax
	jne	.L266
	addq	$3808, %rsp
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
.L262:
	.cfi_restore_state
	cmpl	$1, %r8d
	movslq	12(%r12), %r8
	sbbq	$-1, %rdi
	testl	%r8d, %r8d
	jne	.L125
	imulq	$10752, %rdx, %r8
	leaq	w.2(%rip), %r11
	imulq	$336, %rcx, %rax
	addq	%r8, %rax
	leaq	(%r11,%rax), %r8
	vmovdqu	(%r8), %ymm0
	vpmovzxbw	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm7
	vpmovzxbw	%xmm0, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm0, %ymm6
	vpmovzxwd	%xmm1, %ymm5
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm5, %ymm7, %ymm0
	vpmulld	.LC7(%rip), %ymm5, %ymm5
	vpmulld	.LC6(%rip), %ymm7, %ymm7
	vpaddd	%ymm0, %ymm6, %ymm0
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC9(%rip), %ymm1, %ymm1
	vpaddd	%ymm5, %ymm7, %ymm7
	vpmulld	.LC8(%rip), %ymm6, %ymm5
	vpaddd	%ymm7, %ymm5, %ymm5
	vpaddd	%ymm5, %ymm1, %ymm1
	vmovdqu	32(%r8), %ymm5
	vpmovzxbw	%xmm5, %ymm6
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm6, %ymm8
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxbw	%xmm5, %ymm5
	vpaddd	%ymm0, %ymm8, %ymm7
	vpmulld	.LC10(%rip), %ymm8, %ymm0
	vpmovzxwd	%xmm6, %ymm6
	vpmovzxwd	%xmm5, %ymm9
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%ymm7, %ymm6, %ymm7
	vpmovzxwd	%xmm5, %ymm5
	vpaddd	%ymm7, %ymm9, %ymm7
	vpaddd	%ymm5, %ymm7, %ymm7
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	.LC11(%rip), %ymm6, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC12(%rip), %ymm9, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	.LC13(%rip), %ymm5, %ymm1
	vpaddd	%ymm0, %ymm1, %ymm1
	vmovdqu	64(%r8), %ymm0
	vpmovzxbw	%xmm0, %ymm5
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm5, %ymm8
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm7, %ymm8, %ymm6
	vpmulld	.LC14(%rip), %ymm8, %ymm7
	vpmovzxwd	%xmm5, %ymm5
	vpmovzxwd	%xmm0, %ymm9
	vpaddd	%ymm5, %ymm6, %ymm6
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm9, %ymm6, %ymm6
	vpaddd	%ymm0, %ymm6, %ymm6
	vpmulld	.LC17(%rip), %ymm0, %ymm0
	vpaddd	%ymm1, %ymm7, %ymm7
	vpmulld	.LC15(%rip), %ymm5, %ymm1
	vpmulld	.LC16(%rip), %ymm9, %ymm5
	vpaddd	%ymm7, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm5, %ymm5
	vpaddd	%ymm5, %ymm0, %ymm1
	vmovdqu	96(%r8), %ymm0
	xorl	%r8d, %r8d
	vpmovzxbw	%xmm0, %ymm5
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm5, %ymm9
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm5, %ymm8
	vpaddd	%ymm9, %ymm6, %ymm5
	vpmovzxwd	%xmm0, %ymm10
	vpmulld	.LC18(%rip), %ymm9, %ymm9
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm8, %ymm5, %ymm5
	vpmovzxwd	%xmm0, %ymm7
	vpaddd	%ymm10, %ymm5, %ymm5
	vpmulld	.LC21(%rip), %ymm7, %ymm6
	vpaddd	%ymm7, %ymm5, %ymm0
	vpmulld	.LC19(%rip), %ymm8, %ymm5
	vpaddd	%ymm1, %ymm9, %ymm1
	vpaddd	%ymm1, %ymm5, %ymm5
	vpmulld	.LC20(%rip), %ymm10, %ymm1
	vpaddd	%ymm5, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm6, %ymm6
	vmovdqa	128(%rax,%r11), %xmm1
	vpmovzxbw	%xmm1, %xmm7
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm5
	vpmovzxwd	%xmm7, %xmm9
	vpsrldq	$8, %xmm7, %xmm1
	vpmovzxwd	%xmm1, %xmm1
	vpmovzxwd	%xmm5, %xmm8
	vpaddd	%xmm9, %xmm1, %xmm7
	vpmulld	.LC22(%rip), %xmm9, %xmm9
	vpsrldq	$8, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpmulld	.LC23(%rip), %xmm1, %xmm1
	vpaddd	%xmm8, %xmm7, %xmm7
	vpmulld	.LC24(%rip), %xmm8, %xmm8
	vpaddd	%xmm5, %xmm7, %xmm7
	vpmulld	.LC25(%rip), %xmm5, %xmm5
	vpaddd	%xmm0, %xmm7, %xmm7
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm7, %xmm7
	vpaddd	%xmm9, %xmm1, %xmm1
	vpaddd	%xmm8, %xmm1, %xmm1
	vpaddd	%xmm5, %xmm1, %xmm1
	vmovq	144(%rax,%r11), %xmm5
	vpaddd	%xmm6, %xmm1, %xmm1
	vextracti128	$0x1, %ymm6, %xmm6
	vpaddd	%xmm6, %xmm1, %xmm1
	vpmovzxbw	%xmm5, %xmm0
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxbw	%xmm5, %xmm5
	vpmovzxwd	%xmm0, %xmm9
	vpsrlq	$32, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm0
	vpmovzxwd	%xmm5, %xmm8
	vpaddd	%xmm9, %xmm0, %xmm6
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpaddd	%xmm8, %xmm6, %xmm6
	vpaddd	%xmm5, %xmm6, %xmm6
	vpaddd	%xmm7, %xmm6, %xmm6
	vpsrldq	$8, %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vmovq	.LC27(%rip), %xmm7
	vpmulld	%xmm7, %xmm0, %xmm0
	vmovq	.LC26(%rip), %xmm7
	vpmulld	%xmm7, %xmm9, %xmm9
	vmovq	.LC28(%rip), %xmm7
	vpaddd	%xmm9, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm8, %xmm8
	vmovq	.LC29(%rip), %xmm7
	vpaddd	%xmm8, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm6, %xmm1
	vpaddd	%xmm1, %xmm6, %xmm6
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm6, %r9d
	vmovd	%xmm0, %eax
.L126:
	imulq	$168, %r8, %r8
	imulq	$10752, %rdx, %rdx
	imulq	$336, %rcx, %rcx
	addq	%r8, %rdx
	addq	%rcx, %rdx
	leaq	w.2(%rip), %rcx
	addq	%rcx, %rdx
	cmpl	%r9d, 152(%rdx)
	jne	.L123
	cmpl	%eax, 156(%rdx)
	sete	%al
	movzbl	%al, %eax
	addq	%rax, -3624(%rbp)
	jmp	.L123
.L125:
	imulq	$336, %rcx, %r9
	leaq	w.2(%rip), %r11
	vmovq	.LC4(%rip), %xmm0
	imulq	$168, %r8, %rax
	addq	%r9, %rax
	imulq	$10752, %rdx, %r9
	addq	%r9, %rax
	leaq	(%r11,%rax), %r9
	vmovq	144(%rax,%r11), %xmm5
	vpxor	128(%rax,%r11), %xmm3, %xmm6
	vpxor	(%r9), %ymm3, %ymm7
	vpxor	32(%r9), %ymm3, %ymm10
	vpxor	64(%r9), %ymm3, %ymm1
	vpxor	96(%r9), %ymm3, %ymm8
	vpxor	%xmm0, %xmm5, %xmm5
	vpmovzxbw	%xmm7, %ymm0
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxwd	%xmm0, %ymm9
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxbw	%xmm7, %ymm7
	vpmovzxwd	%xmm0, %ymm0
	vpmovzxwd	%xmm7, %ymm11
	vextracti128	$0x1, %ymm7, %xmm7
	vpaddd	%ymm9, %ymm0, %ymm13
	vpmulld	.LC7(%rip), %ymm0, %ymm0
	vpmovzxwd	%xmm7, %ymm7
	vpmulld	.LC6(%rip), %ymm9, %ymm9
	vpaddd	%ymm13, %ymm11, %ymm13
	vpaddd	%ymm13, %ymm7, %ymm13
	vpmulld	.LC9(%rip), %ymm7, %ymm7
	vpaddd	%ymm0, %ymm9, %ymm9
	vpmulld	.LC8(%rip), %ymm11, %ymm0
	vpaddd	%ymm9, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm7, %ymm9
	vpmovzxbw	%xmm10, %ymm0
	vextracti128	$0x1, %ymm10, %xmm7
	vpmovzxwd	%xmm0, %ymm12
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxbw	%xmm7, %ymm7
	vpmovzxwd	%xmm0, %ymm10
	vpaddd	%ymm13, %ymm12, %ymm0
	vpmulld	.LC10(%rip), %ymm12, %ymm12
	vpmovzxwd	%xmm7, %ymm11
	vpaddd	%ymm10, %ymm0, %ymm0
	vpmulld	.LC11(%rip), %ymm10, %ymm10
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxwd	%xmm7, %ymm7
	vpaddd	%ymm11, %ymm0, %ymm0
	vpaddd	%ymm7, %ymm0, %ymm0
	vpmulld	.LC13(%rip), %ymm7, %ymm7
	vpaddd	%ymm9, %ymm12, %ymm9
	vpaddd	%ymm9, %ymm10, %ymm10
	vpmulld	.LC12(%rip), %ymm11, %ymm9
	vpaddd	%ymm10, %ymm9, %ymm9
	vpaddd	%ymm9, %ymm7, %ymm7
	vpmovzxbw	%xmm1, %ymm9
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm9, %ymm11
	vextracti128	$0x1, %ymm9, %xmm9
	vpmovzxbw	%xmm1, %ymm1
	vpmovzxwd	%xmm9, %ymm9
	vpaddd	%ymm0, %ymm11, %ymm0
	vpmovzxwd	%xmm1, %ymm10
	vpaddd	%ymm9, %ymm0, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm10, %ymm0, %ymm0
	vpmovzxwd	%xmm1, %ymm12
	vpaddd	%ymm0, %ymm12, %ymm1
	vpmulld	.LC14(%rip), %ymm11, %ymm0
	vpaddd	%ymm7, %ymm0, %ymm0
	vpmulld	.LC15(%rip), %ymm9, %ymm7
	vpmovzxbw	%xmm8, %ymm9
	vpaddd	%ymm0, %ymm7, %ymm7
	vpmulld	.LC16(%rip), %ymm10, %ymm0
	vpmovzxwd	%xmm9, %ymm10
	vpaddd	%ymm1, %ymm10, %ymm1
	vpmulld	.LC18(%rip), %ymm10, %ymm10
	vpaddd	%ymm7, %ymm0, %ymm0
	vpmulld	.LC17(%rip), %ymm12, %ymm7
	vpaddd	%ymm0, %ymm7, %ymm7
	vextracti128	$0x1, %ymm8, %xmm0
	vextracti128	$0x1, %ymm9, %xmm8
	vpmovzxwd	%xmm8, %ymm8
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm7, %ymm10, %ymm7
	vpmovzxwd	%xmm0, %ymm9
	vpaddd	%ymm8, %ymm1, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm9, %ymm1, %ymm1
	vpmovzxwd	%xmm0, %ymm11
	vpaddd	%ymm11, %ymm1, %ymm0
	vpmulld	.LC19(%rip), %ymm8, %ymm1
	vpaddd	%ymm7, %ymm1, %ymm1
	vpmulld	.LC20(%rip), %ymm9, %ymm7
	vpaddd	%ymm1, %ymm7, %ymm7
	vpmulld	.LC21(%rip), %ymm11, %ymm1
	vpaddd	%ymm7, %ymm1, %ymm1
	vpmovzxbw	%xmm6, %xmm7
	vpsrldq	$8, %xmm6, %xmm6
	vpmovzxbw	%xmm6, %xmm6
	vpmovzxwd	%xmm7, %xmm10
	vpsrldq	$8, %xmm7, %xmm7
	vpmovzxwd	%xmm7, %xmm8
	vpmovzxwd	%xmm6, %xmm9
	vpaddd	%xmm10, %xmm8, %xmm7
	vpsrldq	$8, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vpmulld	.LC22(%rip), %xmm10, %xmm10
	vpaddd	%xmm9, %xmm7, %xmm7
	vpmulld	.LC24(%rip), %xmm9, %xmm9
	vpaddd	%xmm6, %xmm7, %xmm7
	vpmulld	.LC25(%rip), %xmm6, %xmm6
	vpaddd	%xmm0, %xmm7, %xmm7
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm7, %xmm7
	vpmulld	.LC23(%rip), %xmm8, %xmm0
	vpaddd	%xmm10, %xmm0, %xmm0
	vpaddd	%xmm9, %xmm0, %xmm0
	vpaddd	%xmm6, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpmovzxbw	%xmm5, %xmm0
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxbw	%xmm5, %xmm5
	vpmovzxwd	%xmm0, %xmm9
	vpsrlq	$32, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm0
	vpmovzxwd	%xmm5, %xmm8
	vpaddd	%xmm9, %xmm0, %xmm6
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpaddd	%xmm8, %xmm6, %xmm6
	vpaddd	%xmm5, %xmm6, %xmm6
	vpaddd	%xmm7, %xmm6, %xmm6
	vpsrldq	$8, %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vmovq	.LC27(%rip), %xmm7
	vpmulld	%xmm7, %xmm0, %xmm0
	vmovq	.LC26(%rip), %xmm7
	vpmulld	%xmm7, %xmm9, %xmm9
	vmovq	.LC28(%rip), %xmm7
	vpaddd	%xmm9, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm8, %xmm8
	vmovq	.LC29(%rip), %xmm7
	vpaddd	%xmm8, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm6, %xmm1
	vpaddd	%xmm1, %xmm6, %xmm6
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm6, %r9d
	vmovd	%xmm0, %eax
	jmp	.L126
.L117:
	imulq	$336, %rcx, %r8
	leaq	w.2(%rip), %r11
	vmovq	.LC4(%rip), %xmm7
	imulq	$168, %rax, %rax
	addq	%r8, %rax
	imulq	$10752, %rdx, %r8
	addq	%r8, %rax
	leaq	(%r11,%rax), %r8
	vpxor	(%r8), %ymm3, %ymm1
	vmovdqa	%ymm1, -208(%rbp)
	vpxor	32(%r8), %ymm3, %ymm1
	vmovdqa	%ymm1, -176(%rbp)
	vpxor	64(%r8), %ymm3, %ymm1
	vmovdqa	%ymm1, -144(%rbp)
	vpxor	96(%r8), %ymm3, %ymm0
	vmovdqa	%ymm0, -112(%rbp)
	vpxor	128(%rax,%r11), %xmm3, %xmm0
	vmovdqa	%xmm0, -80(%rbp)
	vmovq	144(%rax,%r11), %xmm0
	vpxor	%xmm7, %xmm0, %xmm0
	vmovq	%xmm0, -64(%rbp)
	jmp	.L118
.L70:
	cmpl	$1, %eax
	sbbq	$-1, -3792(%rbp)
	testl	%edx, %edx
	jne	.L267
	imulq	$336, %rsi, %rax
	leaq	w.2(%rip), %rdi
	imulq	$10752, %r8, %rdx
	addq	%rdx, %rax
	addq	%rdi, %rax
	vmovdqu	(%rax), %ymm0
	vmovdqa	%ymm0, -208(%rbp)
	vmovdqu	32(%rax), %ymm0
	vmovdqa	%ymm0, -176(%rbp)
	vmovdqu	64(%rax), %ymm0
	vmovdqa	%ymm0, -144(%rbp)
	vmovdqu	96(%rax), %ymm0
	vmovdqa	%ymm0, -112(%rbp)
	vmovdqu	120(%rax), %ymm0
	vmovdqu	%ymm0, -88(%rbp)
.L97:
	salq	$5, %r8
	leaq	sqb_item_at(%rip), %rdi
	vmovdqa	-3376(%rbp), %ymm3
	vpxor	%xmm2, %xmm2, %xmm2
	leaq	(%r8,%rsi), %rax
	movl	(%rdi,%rax,4), %esi
	movl	%esi, %eax
	sall	$4, %eax
	addl	%esi, %eax
	vmovd	%eax, %xmm0
	vpbroadcastb	%xmm0, %ymm0
	vpaddb	.LC49(%rip), %ymm0, %ymm1
	vpxor	%ymm3, %ymm1, %ymm1
	vpcmpeqb	-208(%rbp), %ymm1, %ymm1
	vpcmpeqb	%ymm2, %ymm1, %ymm1
	vptest	%ymm1, %ymm1
	jne	.L173
	vpaddb	.LC51(%rip), %ymm0, %ymm1
	vpxor	%ymm3, %ymm1, %ymm1
	vpcmpeqb	-176(%rbp), %ymm1, %ymm1
	vpcmpeqb	%ymm2, %ymm1, %ymm1
	vptest	%ymm1, %ymm1
	jne	.L174
	vpaddb	.LC52(%rip), %ymm0, %ymm1
	vpxor	%ymm3, %ymm1, %ymm1
	vpcmpeqb	-144(%rbp), %ymm1, %ymm1
	vpcmpeqb	%ymm2, %ymm1, %ymm1
	vptest	%ymm1, %ymm1
	jne	.L268
	vpaddb	.LC53(%rip), %ymm0, %ymm0
	movl	$24, %edi
	movl	$128, %eax
	vpxor	%ymm3, %ymm0, %ymm0
	vpcmpeqb	-112(%rbp), %ymm0, %ymm0
	vpcmpeqb	%ymm2, %ymm0, %ymm0
	vptest	%ymm0, %ymm0
	jne	.L269
.L96:
	movl	$91, %r9d
	movl	%eax, %r8d
	imull	%r9d, %eax
	movl	%esi, %r9d
	leaq	-208(%rbp,%r8), %rdx
	sall	$4, %r9d
	addl	%r9d, %esi
	addl	%esi, %eax
	leal	-1(%rdi), %esi
	addq	%r8, %rsi
	leaq	-207(%rbp,%rsi), %rdi
	.p2align 5
	.p2align 4
	.p2align 3
.L94:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, (%rdx)
	jne	.L74
	incq	%rdx
	addl	$91, %eax
	cmpq	%rdi, %rdx
	jne	.L94
	incq	-3736(%rbp)
	jmp	.L74
.L71:
	cmpl	$1, %eax
	sbbq	$-1, -3800(%rbp)
	testl	%edx, %edx
	je	.L86
	imulq	$336, %rsi, %rax
	leaq	w.2(%rip), %rcx
	vmovdqa	-3536(%rbp), %ymm7
	imulq	$10752, %r8, %r9
	leaq	(%rax,%r9), %rdi
	leaq	168(%rax,%r9), %rax
	addq	%rcx, %rax
	vpxor	296(%rcx,%rdi), %xmm7, %xmm1
	vmovq	312(%rcx,%rdi), %xmm3
	vpxor	(%rax), %ymm7, %ymm0
	vpxor	32(%rax), %ymm7, %ymm5
	vpxor	64(%rax), %ymm7, %ymm4
	vpxor	96(%rax), %ymm7, %ymm2
	vmovq	.LC4(%rip), %xmm7
	vpmovzxbw	%xmm0, %ymm6
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm6, %ymm9
	vextracti128	$0x1, %ymm6, %xmm6
	vpmulld	.LC6(%rip), %ymm9, %ymm10
	vpmovzxbw	%xmm0, %ymm0
	vpxor	%xmm7, %xmm3, %xmm3
	vpmovzxwd	%xmm6, %ymm6
	vpmulld	.LC7(%rip), %ymm6, %ymm7
	vpmovzxwd	%xmm0, %ymm8
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm9, %ymm6, %ymm6
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm6, %ymm8, %ymm6
	vpaddd	%ymm10, %ymm7, %ymm7
	vpmulld	.LC8(%rip), %ymm8, %ymm10
	vpaddd	%ymm0, %ymm6, %ymm8
	vpmovzxbw	%xmm5, %ymm6
	vpaddd	%ymm7, %ymm10, %ymm10
	vpmulld	.LC9(%rip), %ymm0, %ymm7
	vextracti128	$0x1, %ymm5, %xmm0
	vextracti128	$0x1, %ymm6, %xmm5
	vpmovzxwd	%xmm5, %ymm5
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm0, %ymm9
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm10, %ymm7, %ymm7
	vpmovzxwd	%xmm6, %ymm10
	vpmulld	.LC10(%rip), %ymm10, %ymm6
	vpaddd	%ymm10, %ymm8, %ymm8
	vpaddd	%ymm7, %ymm6, %ymm7
	vpmulld	.LC11(%rip), %ymm5, %ymm6
	vpaddd	%ymm8, %ymm5, %ymm5
	vpaddd	%ymm5, %ymm9, %ymm5
	vpaddd	%ymm7, %ymm6, %ymm6
	vpmulld	.LC12(%rip), %ymm9, %ymm7
	vpaddd	%ymm6, %ymm7, %ymm7
	vpmulld	.LC13(%rip), %ymm0, %ymm6
	vpaddd	%ymm7, %ymm6, %ymm6
	vpaddd	%ymm5, %ymm0, %ymm7
	vpmovzxbw	%xmm4, %ymm5
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxwd	%xmm5, %ymm9
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxbw	%xmm4, %ymm4
	vpmovzxwd	%xmm5, %ymm5
	vpaddd	%ymm9, %ymm7, %ymm7
	vpmovzxwd	%xmm4, %ymm8
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxwd	%xmm4, %ymm0
	vpmulld	.LC14(%rip), %ymm9, %ymm4
	vpaddd	%ymm6, %ymm4, %ymm4
	vpmulld	.LC15(%rip), %ymm5, %ymm6
	vpaddd	%ymm7, %ymm5, %ymm5
	vpaddd	%ymm4, %ymm6, %ymm6
	vpmulld	.LC16(%rip), %ymm8, %ymm4
	vpaddd	%ymm6, %ymm4, %ymm4
	vpmulld	.LC17(%rip), %ymm0, %ymm6
	vpaddd	%ymm4, %ymm6, %ymm6
	vpaddd	%ymm5, %ymm8, %ymm4
	vpaddd	%ymm4, %ymm0, %ymm4
	vpmovzxbw	%xmm2, %ymm0
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm0, %ymm8
	vpmovzxbw	%xmm2, %ymm2
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm2, %ymm7
	vpmovzxwd	%xmm0, %ymm5
	vextracti128	$0x1, %ymm2, %xmm0
	vpmulld	.LC18(%rip), %ymm8, %ymm2
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm4, %ymm8, %ymm4
	vpaddd	%ymm6, %ymm2, %ymm2
	vpmulld	.LC19(%rip), %ymm5, %ymm6
	vpaddd	%ymm4, %ymm5, %ymm5
	vpmovzxbw	%xmm1, %xmm4
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vpaddd	%ymm2, %ymm6, %ymm6
	vpmulld	.LC20(%rip), %ymm7, %ymm2
	vpaddd	%ymm6, %ymm2, %ymm2
	vpmulld	.LC21(%rip), %ymm0, %ymm6
	vpaddd	%ymm2, %ymm6, %ymm6
	vpaddd	%ymm5, %ymm7, %ymm2
	vpmovzxwd	%xmm1, %xmm5
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%ymm2, %ymm0, %ymm0
	vpmovzxwd	%xmm4, %xmm2
	vpsrldq	$8, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm7
	vpmulld	.LC22(%rip), %xmm2, %xmm4
	vpaddd	%xmm7, %xmm2, %xmm2
	vpmovzxwd	%xmm1, %xmm1
	vpmulld	.LC23(%rip), %xmm7, %xmm8
	vmovq	.LC26(%rip), %xmm7
	vpaddd	%xmm5, %xmm2, %xmm2
	vpaddd	%xmm8, %xmm4, %xmm4
	vpmulld	.LC24(%rip), %xmm5, %xmm8
	vpmovzxbw	%xmm3, %xmm5
	vpsrlq	$32, %xmm3, %xmm3
	vpmovzxbw	%xmm3, %xmm3
	vpaddd	%xmm8, %xmm4, %xmm4
	vpmulld	.LC25(%rip), %xmm1, %xmm8
	vpaddd	%xmm1, %xmm2, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vpmovzxwd	%xmm5, %xmm0
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpmulld	%xmm7, %xmm0, %xmm2
	vmovq	.LC27(%rip), %xmm7
	vpaddd	%xmm5, %xmm0, %xmm0
	vpaddd	%xmm8, %xmm4, %xmm4
	vpmulld	%xmm7, %xmm5, %xmm7
	vpaddd	%xmm6, %xmm4, %xmm4
	vextracti128	$0x1, %ymm6, %xmm6
	vpaddd	%xmm6, %xmm4, %xmm4
	vpmovzxwd	%xmm3, %xmm6
	vpsrlq	$32, %xmm3, %xmm3
	vpmovzxwd	%xmm3, %xmm3
	vpaddd	%xmm6, %xmm0, %xmm0
	vpaddd	%xmm7, %xmm2, %xmm2
	vmovq	.LC28(%rip), %xmm7
	vpaddd	%xmm3, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpmulld	%xmm7, %xmm6, %xmm7
	vpaddd	%xmm1, %xmm0, %xmm0
	vpaddd	%xmm7, %xmm2, %xmm2
	vmovq	.LC29(%rip), %xmm7
	vpmulld	%xmm7, %xmm3, %xmm7
	vpaddd	%xmm7, %xmm2, %xmm2
	vpaddd	%xmm4, %xmm2, %xmm2
	vpsrldq	$8, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm2, %xmm2
	vpsrlq	$32, %xmm2, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm2
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm2, %eax
	vmovd	%xmm0, %edi
.L87:
	imulq	$168, %rdx, %rdx
	imulq	$10752, %r8, %r8
	imulq	$336, %rsi, %rsi
	addq	%r8, %rdx
	addq	%rsi, %rdx
	leaq	w.2(%rip), %rsi
	addq	%rsi, %rdx
	cmpl	%edi, 152(%rdx)
	jne	.L74
	cmpl	%eax, 156(%rdx)
	sete	%al
	movzbl	%al, %eax
	addq	%rax, -3712(%rbp)
	jmp	.L74
.L194:
	movl	$32, %edx
.L133:
	leal	(%rdx,%rcx), %eax
	subl	%edx, %r9d
	jmp	.L134
.L180:
	movl	$32, %edx
.L103:
	leal	(%rdx,%rcx), %eax
	subl	%edx, %r8d
	jmp	.L104
.L179:
	xorl	%edx, %edx
	jmp	.L103
.L193:
	xorl	%edx, %edx
	jmp	.L133
.L196:
	movl	$96, %edx
	jmp	.L133
.L195:
	movl	$64, %edx
	jmp	.L133
.L181:
	movl	$64, %edx
	jmp	.L103
.L182:
	movl	$96, %edx
	jmp	.L103
.L72:
	movslq	%r8d, %rax
	leaq	w.2(%rip), %rdi
	salq	$5, %rax
	leaq	37968(%rsi,%rax), %rax
	movl	(%rdi,%rax,4), %eax
	movzwl	%ax, %edx
	shrl	$16, %eax
	addl	%edx, %eax
	cmpl	$65535, %eax
	setne	%al
	movzbl	%al, %eax
	addq	%rax, -3784(%rbp)
	jmp	.L74
.L86:
	imulq	$336, %rsi, %rdi
	imulq	$10752, %r8, %rax
	addq	%rdi, %rax
	leaq	w.2(%rip), %rdi
	addq	%rax, %rdi
	vmovdqu	(%rdi), %ymm0
	vpmovzxbw	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm1
	vpmovzxwd	%xmm0, %ymm2
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm1, %ymm3, %ymm4
	vpmulld	.LC6(%rip), %ymm3, %ymm3
	vpmovzxwd	%xmm0, %ymm0
	vpmulld	.LC7(%rip), %ymm1, %ymm1
	vpaddd	%ymm2, %ymm4, %ymm4
	vpmulld	.LC8(%rip), %ymm2, %ymm2
	vpaddd	%ymm4, %ymm0, %ymm4
	vpmulld	.LC9(%rip), %ymm0, %ymm0
	vpaddd	%ymm3, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm2, %ymm1
	vpaddd	%ymm1, %ymm0, %ymm2
	vmovdqu	32(%rdi), %ymm0
	vpmovzxbw	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm6
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm0, %ymm5
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm3
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm6, %ymm4, %ymm0
	vpmulld	.LC10(%rip), %ymm6, %ymm4
	vpaddd	%ymm0, %ymm3, %ymm0
	vpaddd	%ymm5, %ymm0, %ymm0
	vpmulld	.LC12(%rip), %ymm5, %ymm5
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	.LC13(%rip), %ymm1, %ymm1
	vpaddd	%ymm2, %ymm4, %ymm4
	vpmulld	.LC11(%rip), %ymm3, %ymm2
	vpaddd	%ymm4, %ymm2, %ymm2
	vpaddd	%ymm2, %ymm5, %ymm2
	vpaddd	%ymm2, %ymm1, %ymm2
	vmovdqu	64(%rdi), %ymm1
	vpmovzxbw	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm3, %ymm5
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm5, %ymm0
	vpmulld	.LC14(%rip), %ymm5, %ymm5
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm1, %ymm4
	vpaddd	%ymm3, %ymm0, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm4, %ymm0
	vpmulld	.LC16(%rip), %ymm4, %ymm4
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC17(%rip), %ymm1, %ymm1
	vpaddd	%ymm2, %ymm5, %ymm5
	vpmulld	.LC15(%rip), %ymm3, %ymm2
	vpaddd	%ymm5, %ymm2, %ymm2
	vpaddd	%ymm2, %ymm4, %ymm2
	vpaddd	%ymm2, %ymm1, %ymm2
	vmovdqu	96(%rdi), %ymm1
	leaq	128+w.2(%rip), %rdi
	vpmovzxbw	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm3, %ymm6
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm6, %ymm0, %ymm5
	vpmulld	.LC18(%rip), %ymm6, %ymm6
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm1, %ymm4
	vpmulld	.LC19(%rip), %ymm3, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm5, %ymm3, %ymm5
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm5, %ymm4, %ymm5
	vpaddd	%ymm5, %ymm1, %ymm5
	vpaddd	%ymm2, %ymm6, %ymm2
	vpaddd	%ymm2, %ymm0, %ymm0
	vpmulld	.LC20(%rip), %ymm4, %ymm2
	vpaddd	%ymm0, %ymm2, %ymm2
	vpmulld	.LC21(%rip), %ymm1, %ymm0
	vmovdqa	(%rdi,%rax), %xmm1
	vpaddd	%ymm2, %ymm0, %ymm0
	vpmovzxbw	%xmm1, %xmm2
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm4
	vpmovzxwd	%xmm2, %xmm1
	vpsrldq	$8, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm3
	vpmovzxwd	%xmm4, %xmm7
	vpaddd	%xmm3, %xmm1, %xmm2
	vpsrldq	$8, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm6
	vpmulld	.LC23(%rip), %xmm3, %xmm3
	vpaddd	%xmm7, %xmm2, %xmm2
	vpmulld	.LC24(%rip), %xmm7, %xmm7
	vpaddd	%xmm6, %xmm2, %xmm2
	vpmulld	.LC25(%rip), %xmm6, %xmm6
	vpaddd	%xmm5, %xmm2, %xmm2
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%xmm5, %xmm2, %xmm4
	vpmulld	.LC22(%rip), %xmm1, %xmm2
	vmovq	16(%rdi,%rax), %xmm1
	vpmovzxbw	%xmm1, %xmm5
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vpaddd	%xmm3, %xmm2, %xmm2
	vpaddd	%xmm7, %xmm2, %xmm2
	vmovq	.LC26(%rip), %xmm7
	vpaddd	%xmm6, %xmm2, %xmm2
	vpmovzxwd	%xmm1, %xmm6
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm1
	vpaddd	%xmm0, %xmm2, %xmm2
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm2, %xmm2
	vpmovzxwd	%xmm5, %xmm0
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm3
	vpaddd	%xmm6, %xmm3, %xmm3
	vpmulld	%xmm7, %xmm0, %xmm0
	vmovq	.LC27(%rip), %xmm7
	vpaddd	%xmm1, %xmm3, %xmm3
	vpaddd	%xmm4, %xmm3, %xmm3
	vpsrldq	$8, %xmm4, %xmm4
	vpmulld	%xmm7, %xmm5, %xmm5
	vmovq	.LC28(%rip), %xmm7
	vpaddd	%xmm4, %xmm3, %xmm3
	vpaddd	%xmm5, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm6, %xmm6
	vmovq	.LC29(%rip), %xmm7
	vpaddd	%xmm6, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm3, %xmm1
	vpaddd	%xmm1, %xmm3, %xmm3
	vpaddd	%xmm2, %xmm0, %xmm0
	vpsrldq	$8, %xmm2, %xmm2
	vmovd	%xmm3, %edi
	vpaddd	%xmm2, %xmm0, %xmm0
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %eax
	jmp	.L87
.L187:
	xorl	%eax, %eax
.L119:
	movl	$152, %r8d
	subl	%eax, %r8d
	jmp	.L120
.L264:
	movl	$96, %eax
	jmp	.L119
.L189:
	movl	$64, %eax
	jmp	.L119
.L188:
	movl	$32, %eax
	jmp	.L119
.L177:
	movl	$152, %r8d
	xorl	%ecx, %ecx
	jmp	.L101
.L191:
	movl	$152, %r9d
	xorl	%ecx, %ecx
	jmp	.L131
.L267:
	imulq	$336, %rsi, %rdx
	leaq	w.2(%rip), %rdi
	vmovdqa	-3536(%rbp), %ymm7
	imulq	$10752, %r8, %rax
	addq	%rdx, %rax
	leaq	168(%rdi,%rax), %rdx
	vpxor	(%rdx), %ymm7, %ymm1
	vmovdqa	%ymm1, -208(%rbp)
	vpxor	32(%rdx), %ymm7, %ymm1
	vmovdqa	%ymm1, -176(%rbp)
	vpxor	64(%rdx), %ymm7, %ymm1
	vmovdqa	%ymm1, -144(%rbp)
	vpxor	96(%rdx), %ymm7, %ymm0
	vmovq	.LC4(%rip), %xmm1
	vmovdqa	%ymm0, -112(%rbp)
	vpxor	296(%rax,%rdi), %xmm7, %xmm0
	vmovdqa	%xmm0, -80(%rbp)
	vmovq	312(%rax,%rdi), %xmm0
	vpxor	%xmm1, %xmm0, %xmm0
	vmovq	%xmm0, -64(%rbp)
	jmp	.L97
.L146:
	vcvtsi2sdq	%rbx, %xmm2, %xmm1
	vcvtsi2sdq	%rsi, %xmm2, %xmm0
	vdivsd	%xmm1, %xmm0, %xmm0
	movq	%rbx, %rdx
	leaq	.LC77(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm2, -3344(%rbp)
	vmovsd	%xmm1, -3296(%rbp)
	call	printf@PLT
	vmovaps	-3344(%rbp), %xmm2
	vcvtsi2sdq	%r13, %xmm2, %xmm0
	vdivsd	-3296(%rbp), %xmm0, %xmm0
	jmp	.L147
.L143:
	movq	-3800(%rbp), %rsi
	vcvtsi2sdq	%rbx, %xmm2, %xmm1
	movq	%rbx, %rdx
	leaq	.LC72(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm2, -3344(%rbp)
	vmovsd	%xmm1, -3296(%rbp)
	vcvtsi2sdq	%rsi, %xmm2, %xmm0
	vdivsd	%xmm1, %xmm0, %xmm0
	call	printf@PLT
	vmovaps	-3344(%rbp), %xmm2
	vcvtsi2sdq	-3712(%rbp), %xmm2, %xmm0
	vdivsd	-3296(%rbp), %xmm0, %xmm0
	jmp	.L144
.L141:
	movq	-3792(%rbp), %rsi
	vcvtsi2sdq	%rbx, %xmm2, %xmm1
	movq	%rbx, %rdx
	leaq	.LC70(%rip), %rdi
	movl	$1, %eax
	vmovaps	%xmm2, -3344(%rbp)
	vmovsd	%xmm1, -3296(%rbp)
	vcvtsi2sdq	%rsi, %xmm2, %xmm0
	vdivsd	%xmm1, %xmm0, %xmm0
	call	printf@PLT
	vmovaps	-3344(%rbp), %xmm2
	vcvtsi2sdq	-3736(%rbp), %xmm2, %xmm0
	vdivsd	-3296(%rbp), %xmm0, %xmm0
	jmp	.L142
.L172:
	movl	$96, %edx
.L80:
	leal	(%rdx,%rsi), %eax
	subl	%edx, %r9d
	jmp	.L81
.L171:
	movl	$64, %edx
	jmp	.L80
.L170:
	movl	$32, %edx
	jmp	.L80
.L169:
	xorl	%edx, %edx
	jmp	.L80
.L167:
	movl	$152, %r9d
	xorl	%esi, %esi
	jmp	.L78
.L268:
	movl	$64, %eax
.L91:
	movl	$152, %edi
	subl	%eax, %edi
	jmp	.L96
.L157:
	movl	$152, %ecx
	xorl	%eax, %eax
	jmp	.L57
.L159:
	xorl	%edx, %edx
.L59:
	addl	%edx, %eax
	subl	%edx, %ecx
	jmp	.L60
.L160:
	movl	$32, %edx
	jmp	.L59
.L161:
	movl	$64, %edx
	jmp	.L59
.L162:
	movl	$96, %edx
	jmp	.L59
.L163:
	xorl	%ecx, %ecx
	movq	%rcx, -3696(%rbp)
	movq	%rcx, -3728(%rbp)
	movq	%rcx, -3784(%rbp)
	movq	%rcx, -3800(%rbp)
	movq	%rcx, -3712(%rbp)
	movq	%rcx, -3792(%rbp)
	movq	%rcx, -3776(%rbp)
	movq	%rcx, -3568(%rbp)
	movq	%rcx, -3664(%rbp)
	movq	%rcx, -3736(%rbp)
.L183:
	xorl	%edx, %edx
	xorl	%eax, %eax
	xorl	%r12d, %r12d
	movq	%rax, -3504(%rbp)
	movq	%rax, -3616(%rbp)
	movq	%rdx, -3312(%rbp)
	movq	%rdx, -3624(%rbp)
	movq	%rdx, -3720(%rbp)
	movq	%rdx, -3472(%rbp)
	movq	%rdx, -3536(%rbp)
	jmp	.L65
.L173:
	xorl	%eax, %eax
	jmp	.L91
.L174:
	movl	$32, %eax
	jmp	.L91
.L269:
	movl	$96, %eax
	jmp	.L91
.L266:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE53:
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
	.set	.LC4,.LC30
	.section	.rodata.cst8,"aM",@progbits,8
	.align 8
.LC5:
	.byte	1
	.byte	1
	.byte	1
	.byte	1
	.byte	1
	.byte	1
	.byte	1
	.byte	1
	.section	.rodata.cst32,"aM",@progbits,32
	.align 32
.LC6:
	.long	1
	.long	2
	.long	3
	.long	4
	.long	5
	.long	6
	.long	7
	.long	8
	.align 32
.LC7:
	.long	9
	.long	10
	.long	11
	.long	12
	.long	13
	.long	14
	.long	15
	.long	16
	.align 32
.LC8:
	.long	17
	.long	18
	.long	19
	.long	20
	.long	21
	.long	22
	.long	23
	.long	24
	.align 32
.LC9:
	.long	25
	.long	26
	.long	27
	.long	28
	.long	29
	.long	30
	.long	31
	.long	32
	.align 32
.LC10:
	.long	33
	.long	34
	.long	35
	.long	36
	.long	37
	.long	38
	.long	39
	.long	40
	.align 32
.LC11:
	.long	41
	.long	42
	.long	43
	.long	44
	.long	45
	.long	46
	.long	47
	.long	48
	.align 32
.LC12:
	.long	49
	.long	50
	.long	51
	.long	52
	.long	53
	.long	54
	.long	55
	.long	56
	.align 32
.LC13:
	.long	57
	.long	58
	.long	59
	.long	60
	.long	61
	.long	62
	.long	63
	.long	64
	.align 32
.LC14:
	.long	65
	.long	66
	.long	67
	.long	68
	.long	69
	.long	70
	.long	71
	.long	72
	.align 32
.LC15:
	.long	73
	.long	74
	.long	75
	.long	76
	.long	77
	.long	78
	.long	79
	.long	80
	.align 32
.LC16:
	.long	81
	.long	82
	.long	83
	.long	84
	.long	85
	.long	86
	.long	87
	.long	88
	.align 32
.LC17:
	.long	89
	.long	90
	.long	91
	.long	92
	.long	93
	.long	94
	.long	95
	.long	96
	.align 32
.LC18:
	.long	97
	.long	98
	.long	99
	.long	100
	.long	101
	.long	102
	.long	103
	.long	104
	.align 32
.LC19:
	.long	105
	.long	106
	.long	107
	.long	108
	.long	109
	.long	110
	.long	111
	.long	112
	.align 32
.LC20:
	.long	113
	.long	114
	.long	115
	.long	116
	.long	117
	.long	118
	.long	119
	.long	120
	.align 32
.LC21:
	.long	121
	.long	122
	.long	123
	.long	124
	.long	125
	.long	126
	.long	127
	.long	128
	.section	.rodata.cst16,"aM",@progbits,16
	.align 16
.LC22:
	.long	129
	.long	130
	.long	131
	.long	132
	.align 16
.LC23:
	.long	133
	.long	134
	.long	135
	.long	136
	.align 16
.LC24:
	.long	137
	.long	138
	.long	139
	.long	140
	.align 16
.LC25:
	.long	141
	.long	142
	.long	143
	.long	144
	.section	.rodata.cst8
	.align 8
.LC26:
	.long	145
	.long	146
	.align 8
.LC27:
	.long	147
	.long	148
	.align 8
.LC28:
	.long	149
	.long	150
	.align 8
.LC29:
	.long	151
	.long	152
	.section	.rodata.cst32
	.align 32
.LC30:
	.long	1431655765
	.long	1431655765
	.long	1431655765
	.long	1431655765
	.long	1431655765
	.long	1431655765
	.long	1431655765
	.long	1431655765
	.set	.LC31,.LC30
	.align 32
.LC33:
	.long	0
	.long	1
	.long	2
	.long	3
	.long	4
	.long	5
	.long	6
	.long	7
	.align 32
.LC34:
	.long	8
	.long	9
	.long	10
	.long	11
	.long	12
	.long	13
	.long	14
	.long	15
	.align 32
.LC35:
	.long	16
	.long	17
	.long	18
	.long	19
	.long	20
	.long	21
	.long	22
	.long	23
	.align 32
.LC36:
	.long	24
	.long	25
	.long	26
	.long	27
	.long	28
	.long	29
	.long	30
	.long	31
	.align 32
.LC37:
	.long	32
	.long	33
	.long	34
	.long	35
	.long	36
	.long	37
	.long	38
	.long	39
	.align 32
.LC38:
	.long	40
	.long	41
	.long	42
	.long	43
	.long	44
	.long	45
	.long	46
	.long	47
	.align 32
.LC39:
	.long	48
	.long	49
	.long	50
	.long	51
	.long	52
	.long	53
	.long	54
	.long	55
	.align 32
.LC40:
	.long	56
	.long	57
	.long	58
	.long	59
	.long	60
	.long	61
	.long	62
	.long	63
	.align 32
.LC41:
	.long	64
	.long	65
	.long	66
	.long	67
	.long	68
	.long	69
	.long	70
	.long	71
	.align 32
.LC42:
	.long	72
	.long	73
	.long	74
	.long	75
	.long	76
	.long	77
	.long	78
	.long	79
	.align 32
.LC43:
	.long	80
	.long	81
	.long	82
	.long	83
	.long	84
	.long	85
	.long	86
	.long	87
	.align 32
.LC44:
	.long	88
	.long	89
	.long	90
	.long	91
	.long	92
	.long	93
	.long	94
	.long	95
	.align 32
.LC45:
	.long	96
	.long	97
	.long	98
	.long	99
	.long	100
	.long	101
	.long	102
	.long	103
	.align 32
.LC46:
	.long	104
	.long	105
	.long	106
	.long	107
	.long	108
	.long	109
	.long	110
	.long	111
	.align 32
.LC47:
	.long	112
	.long	113
	.long	114
	.long	115
	.long	116
	.long	117
	.long	118
	.long	119
	.align 32
.LC48:
	.long	120
	.long	121
	.long	122
	.long	123
	.long	124
	.long	125
	.long	126
	.long	127
	.align 32
.LC49:
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
.LC51:
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
.LC52:
	.byte	-64
	.byte	27
	.byte	118
	.byte	-47
	.byte	44
	.byte	-121
	.byte	-30
	.byte	61
	.byte	-104
	.byte	-13
	.byte	78
	.byte	-87
	.byte	4
	.byte	95
	.byte	-70
	.byte	21
	.byte	112
	.byte	-53
	.byte	38
	.byte	-127
	.byte	-36
	.byte	55
	.byte	-110
	.byte	-19
	.byte	72
	.byte	-93
	.byte	-2
	.byte	89
	.byte	-76
	.byte	15
	.byte	106
	.byte	-59
	.align 32
.LC53:
	.byte	32
	.byte	123
	.byte	-42
	.byte	49
	.byte	-116
	.byte	-25
	.byte	66
	.byte	-99
	.byte	-8
	.byte	83
	.byte	-82
	.byte	9
	.byte	100
	.byte	-65
	.byte	26
	.byte	117
	.byte	-48
	.byte	43
	.byte	-122
	.byte	-31
	.byte	60
	.byte	-105
	.byte	-14
	.byte	77
	.byte	-88
	.byte	3
	.byte	94
	.byte	-71
	.byte	20
	.byte	111
	.byte	-54
	.byte	37
	.section	.rodata.cst16
	.align 16
.LC54:
	.byte	-128
	.byte	-37
	.byte	54
	.byte	-111
	.byte	-20
	.byte	71
	.byte	-94
	.byte	-3
	.byte	88
	.byte	-77
	.byte	14
	.byte	105
	.byte	-60
	.byte	31
	.byte	122
	.byte	-43
	.section	.rodata.cst8
	.align 8
.LC56:
	.byte	48
	.byte	-117
	.byte	-26
	.byte	65
	.byte	-100
	.byte	-9
	.byte	82
	.byte	-83
	.align 8
.LC57:
	.byte	-91
	.byte	-91
	.byte	-91
	.byte	-91
	.byte	-91
	.byte	-91
	.byte	-91
	.byte	-91
	.align 8
.LC61:
	.long	0
	.long	1017118720
	.align 8
.LC62:
	.long	1717986918
	.long	1072064102
	.align 8
.LC63:
	.long	0
	.long	1071644672
	.align 8
.LC64:
	.long	-687194767
	.long	1072001187
	.align 8
.LC67:
	.long	0
	.long	1064304640
	.ident	"GCC: (GNU) 16.1.1 20260625"
	.section	.note.GNU-stack,"",@progbits

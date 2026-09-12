	.file	"sq2b_cert.c"
	.text
	.p2align 4
	.type	sqb_sweep.constprop.1, @function
sqb_sweep.constprop.1:
.LFB24:
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
	leaq	cell.2(%rip), %r11
	movq	$0, 744(%rsp)
	leaq	86048(%r11), %r14
	leaq	86016(%r11), %r15
.L2:
	movq	%r11, %rcx
	movq	%r11, 72(%rsp)
	movq	%r15, %rdi
	movq	%r15, %r8
	movl	%r10d, %r11d
	movq	%r9, 64(%rsp)
	jmp	.L17
.L8:
	movb	$1, (%rsi)
.L12:
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
.L14:
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
	je	.L29
.L16:
	incq	744(%rsp)
	.p2align 5
	.p2align 4
	.p2align 3
.L15:
	incq	%rdi
	addq	$336, %rcx
	cmpq	%r14, %rdi
	je	.L30
.L17:
	cmpb	$0, (%rdi)
	je	.L15
	movl	%r11d, %eax
	subl	%r8d, %eax
	leal	(%rax,%rdi), %esi
	leaq	action.0(%rip), %rax
	addq	%rax, %rsi
	cmpl	$-559063315, 164(%rcx)
	movb	$0, (%rsi)
	je	.L15
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
	je	.L31
	movabsq	$6148914691236517205, %rax
	xorl	%r10d, %r10d
	xorl	%r9d, %r9d
	movq	%rax, 992(%rsp)
	vmovq	%rax, %xmm1
.L4:
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
	je	.L32
.L5:
	testb	%r10b, %r10b
	jne	.L8
	movb	$1, (%rsi)
	testl	%r9d, %r9d
	jne	.L12
	incq	%rdi
	movl	$-559063315, 164(%rcx)
	movl	$-559063315, 332(%rcx)
	movb	$2, (%rsi)
	addq	$336, %rcx
	incq	86320+cell.2(%rip)
	cmpq	%r14, %rdi
	jne	.L17
.L30:
	movq	64(%rsp), %r9
	leal	32(%r11), %r10d
	movq	72(%rsp), %r11
	leaq	32(%rdi), %r14
	leaq	32(%r8), %r15
	addq	$10752, %r9
	addq	$10752, %r11
	cmpq	$86016, %r9
	jne	.L2
	movq	1400(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L33
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
.L32:
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
	jne	.L5
	testb	%r10b, %r10b
	je	.L34
	incl	160(%rcx)
	incl	328(%rcx)
	jmp	.L15
.L31:
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
	jmp	.L4
.L34:
	movb	$1, (%rsi)
	cmpl	$1, %r9d
	je	.L35
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
	jmp	.L14
.L35:
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
	incq	86328+cell.2(%rip)
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
	jmp	.L14
.L29:
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
	jne	.L16
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
	jne	.L16
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
	jne	.L16
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
	jne	.L16
	jmp	.L15
.L33:
	vzeroupper
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE24:
	.size	sqb_sweep.constprop.1, .-sqb_sweep.constprop.1
	.p2align 4
	.type	sq2b_blind_pass.constprop.0, @function
sq2b_blind_pass.constprop.0:
.LFB28:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movabsq	$-4579973394783843406, %r9
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%r15
	pushq	%r14
	pushq	%r13
	pushq	%r12
	pushq	%rbx
	andq	$-32, %rsp
	subq	$87616, %rsp
	.cfi_offset 15, -24
	.cfi_offset 14, -32
	.cfi_offset 13, -40
	.cfi_offset 12, -48
	.cfi_offset 3, -56
	movq	%rdi, 16(%rsp)
	movq	%rsi, 8(%rsp)
	movq	%rdx, (%rsp)
	movq	%fs:40, %rax
	movq	%rax, 87608(%rsp)
	xorl	%eax, %eax
	movabsq	$102502573457256094, %rax
	movq	$0, (%rdx)
	movl	$2000, 28(%rsp)
	movq	$0, (%rsi)
	movq	%rax, 64(%rsp)
	movabsq	$-8913248024320420735, %rax
	movq	$0, (%rdi)
	movq	%r9, 48(%rsp)
	movq	%rax, 56(%rsp)
	movabsq	$7482802359357942451, %rax
	movq	%rax, 72(%rsp)
.L64:
	movq	72(%rsp), %rbx
	movq	48(%rsp), %rsi
	movq	64(%rsp), %rax
	movq	56(%rsp), %rdx
	movq	%rbx, %rdi
	xorq	%rbx, %rax
	movq	%rsi, %r8
	movq	%rsi, %rcx
	salq	$17, %rsi
	xorq	%rdx, %r8
	xorq	%rax, %rcx
	xorq	%rax, %rsi
	addq	%rdx, %rbx
	xorq	%r8, %rdi
	movq	%rcx, %r9
	rorx	$19, %r8, %r8
	movq	%rcx, %rax
	xorq	%rdi, %rsi
	xorq	%r8, %r9
	movq	%rdi, %rdx
	salq	$17, %rcx
	xorq	%r9, %rdx
	xorq	%rsi, %rcx
	rorx	$19, %r9, %r9
	xorq	%rsi, %rax
	xorq	%rdx, %rcx
	movq	%rdx, %rsi
	addq	%r9, %rdx
	addq	%r8, %rdi
	rorx	$47, %rdx, %rdx
	rorx	$47, %rdi, %r13
	movq	%rax, %r8
	movq	%rax, %rdi
	movl	%edx, %r14d
	xorq	%r9, %rdi
	xorq	%rcx, %r8
	salq	$17, %rax
	shrl	$3, %r14d
	xorq	%rdi, %rsi
	xorq	%rcx, %rax
	rorx	$19, %rdi, %rdi
	imulq	$452101821, %r14, %r14
	xorq	%rsi, %rax
	movq	%r8, %rcx
	rorx	$47, %rbx, %rbx
	xorq	%rax, %rcx
	movq	%rcx, 48(%rsp)
	movq	%rsi, %rcx
	shrq	$33, %r14
	imull	$152, %r14d, %r9d
	movl	%edx, %r14d
	movq	%r8, %rdx
	salq	$17, %r8
	xorq	%rdi, %rdx
	xorq	%rax, %r8
	rorx	$19, %rdx, %rax
	xorq	%rdx, %rcx
	movq	%r8, 64(%rsp)
	movq	%rax, 56(%rsp)
	leaq	(%rsi,%rdi), %rax
	movq	%rcx, 72(%rsp)
	movl	$2155905153, %ecx
	rorx	$47, %rax, %rax
	subl	%r9d, %r14d
	leaq	960(%rsp), %rdi
	leaq	clean.1(%rip), %rsi
	movl	%eax, %edx
	imulq	%rcx, %rdx
	andl	$7, %ebx
	shrq	$39, %rdx
	leal	1(%rax,%rdx), %r12d
	movl	$86336, %edx
	call	memcpy@PLT
	movq	%r13, %r10
	imulq	$10752, %rbx, %rax
	movl	%r14d, %ecx
	andl	$31, %r10d
	vpcmpeqd	%ymm0, %ymm0, %ymm0
	leaq	86976(%rsp), %r13
	leaq	11712(%rsp), %r14
	imulq	$336, %r10, %rdx
	vpabsb	%ymm0, %ymm5
	vpcmpeqd	%xmm0, %xmm0, %xmm0
	movq	%r13, %rdi
	vmovdqa	%ymm5, 768(%rsp)
	vpabsb	%xmm0, %xmm5
	movq	%r13, 160(%rsp)
	movq	%r14, %r11
	vmovdqa	%xmm5, 256(%rsp)
	movb	%r12b, 184(%rsp)
	movq	%r14, 128(%rsp)
	movq	%r10, %r8
	leaq	87616(%rax,%rdx), %rax
	movq	%rbx, 96(%rsp)
	movq	%rcx, %r13
	addq	%rsp, %rax
	addq	%rcx, %rax
	xorb	%r12b, -86656(%rax)
	xorb	%r12b, -86488(%rax)
	.p2align 4
	.p2align 3
.L37:
	movl	$1431655765, %eax
	movq	%rdi, %rsi
	vmovd	%eax, %xmm11
	movq	%rdi, 224(%rsp)
	leaq	-10752(%r11), %rax
	movq	%r8, %r15
	vpbroadcastd	%xmm11, %ymm11
	vmovdqa	%ymm11, 192(%rsp)
	jmp	.L46
	.p2align 4
	.p2align 3
.L67:
	xorl	%r10d, %r10d
	xorl	%ebx, %ebx
	movabsq	$6148914691236517205, %r8
.L39:
	vmovdqa	864(%rsp), %ymm3
	vmovdqa	928(%rsp), %ymm5
	vmovq	%r8, %xmm2
	vpxor	.LC30(%rip), %ymm3, %ymm4
	vmovdqa	832(%rsp), %ymm3
	vpxor	.LC30(%rip), %ymm3, %ymm7
	vpxor	.LC30(%rip), %ymm5, %ymm6
	vmovdqa	800(%rsp), %ymm3
	vmovdqa	896(%rsp), %xmm5
	vpxor	.LC30(%rip), %ymm3, %ymm3
	vpxor	.LC31(%rip), %xmm5, %xmm15
	vmovq	%rdi, %xmm5
	vpxor	%xmm2, %xmm5, %xmm5
	vmovq	%xmm5, %rdi
	vpmovzxbw	%xmm4, %ymm1
	vextracti128	$0x1, %ymm4, %xmm0
	vmovdqa	%ymm4, 448(%rsp)
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm4
	vextracti128	$0x1, %ymm1, %xmm1
	vmovdqa	%ymm7, 416(%rsp)
	vpmovzxwd	%xmm1, %ymm5
	vpmovzxwd	%xmm0, %ymm2
	vextracti128	$0x1, %ymm0, %xmm0
	vmovdqa	%ymm4, 864(%rsp)
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm4, %ymm5, %ymm0
	vmovdqa	%ymm2, 800(%rsp)
	vmovdqa	%ymm5, 832(%rsp)
	vpaddd	%ymm2, %ymm0, %ymm0
	vpmovzxbw	%xmm7, %ymm2
	vmovdqa	%ymm1, 608(%rsp)
	vmovdqa	%ymm3, 384(%rsp)
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmovzxwd	%xmm2, %ymm12
	vextracti128	$0x1, %ymm7, %xmm1
	vmovdqa	%ymm6, 480(%rsp)
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm12, %ymm0, %ymm0
	vpmovzxbw	%xmm15, %xmm7
	vpmovzxwd	%xmm2, %ymm4
	vpmovzxwd	%xmm1, %ymm5
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm4, %ymm0, %ymm0
	vpmovzxwd	%xmm1, %ymm2
	vmovdqa	%ymm5, 544(%rsp)
	vmovdqa	%ymm4, 576(%rsp)
	vpaddd	%ymm5, %ymm0, %ymm0
	vpmovzxbw	%xmm3, %ymm5
	vextracti128	$0x1, %ymm3, %xmm4
	vpmovzxbw	%xmm6, %ymm3
	vpaddd	%ymm2, %ymm0, %ymm0
	vpmovzxwd	%xmm5, %ymm11
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxbw	%xmm4, %ymm4
	vpmovzxwd	%xmm5, %ymm5
	vpaddd	%ymm11, %ymm0, %ymm0
	vpmovzxwd	%xmm4, %ymm10
	vpmovzxwd	%xmm3, %ymm9
	vextracti128	$0x1, %ymm4, %xmm4
	vpaddd	%ymm0, %ymm5, %ymm0
	vextracti128	$0x1, %ymm6, %xmm1
	vmovdqa	%ymm2, 512(%rsp)
	vpmovzxwd	%xmm4, %ymm4
	vpaddd	%ymm0, %ymm10, %ymm0
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm4, %ymm0
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm1, %ymm8
	vpmovzxwd	%xmm7, %xmm2
	vpaddd	%ymm0, %ymm9, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpsrldq	$8, %xmm7, %xmm7
	vpmovzxwd	%xmm7, %xmm7
	vpaddd	%ymm0, %ymm3, %ymm0
	vpmovzxwd	%xmm1, %ymm6
	vmovdqa	%xmm2, 896(%rsp)
	vpaddd	%xmm2, %xmm7, %xmm2
	vpaddd	%ymm0, %ymm8, %ymm0
	vmovdqa	%ymm6, 928(%rsp)
	vpaddd	%ymm6, %ymm0, %ymm0
	vpsrldq	$8, %xmm15, %xmm6
	vpmovzxbw	%xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm13
	vmovdqa	%xmm0, %xmm14
	vextracti128	$0x1, %ymm0, %xmm0
	vpsrldq	$8, %xmm6, %xmm6
	vpaddd	%xmm0, %xmm14, %xmm14
	vpmovzxwd	%xmm6, %xmm6
	vpaddd	%xmm13, %xmm2, %xmm2
	vmovq	%rdi, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpaddd	%xmm6, %xmm2, %xmm2
	vpaddd	%xmm14, %xmm2, %xmm2
	vpmovzxwd	%xmm0, %xmm1
	vmovq	%rdi, %xmm14
	vpsrlq	$32, %xmm0, %xmm0
	vmovq	%xmm1, %rcx
	vpsrlq	$32, %xmm14, %xmm14
	vpmovzxwd	%xmm0, %xmm1
	vpmovzxbw	%xmm14, %xmm14
	vmovq	%xmm1, %rdx
	vpmovzxwd	%xmm14, %xmm1
	vpsrlq	$32, %xmm14, %xmm14
	vpmovzxwd	%xmm14, %xmm14
	vmovq	%xmm1, %r9
	vmovq	%rdx, %xmm0
	vmovq	%rcx, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	vmovq	%r9, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpaddd	%xmm14, %xmm0, %xmm0
	vpaddd	%xmm2, %xmm0, %xmm0
	vpsrldq	$8, %xmm2, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm2
	vpsrlq	$32, %xmm2, %xmm0
	vpaddd	%xmm0, %xmm2, %xmm2
	vmovq	%xmm2, %r12
	cmpl	%r12d, 320(%rax)
	je	.L81
.L40:
	testl	%ebx, %ebx
	jne	.L43
	testb	%r10b, %r10b
	jne	.L43
	movl	$-559063315, 164(%rax)
	movl	$-559063315, 332(%rax)
	incq	87280(%rsp)
	.p2align 5
	.p2align 4
	.p2align 3
.L38:
	addq	$336, %rax
	incq	%rsi
	cmpq	%rax, %r11
	je	.L82
.L46:
	cmpb	$0, (%rsi)
	je	.L38
	cmpl	$-559063315, 164(%rax)
	je	.L38
	vmovdqu	168(%rax), %ymm3
	vmovdqu	(%rax), %ymm7
	vmovdqu	200(%rax), %ymm5
	vmovdqu	232(%rax), %ymm4
	vmovdqu	296(%rax), %xmm6
	vmovdqu	96(%rax), %ymm15
	vmovq	144(%rax), %xmm11
	movq	312(%rax), %rdi
	vmovdqa	%ymm3, 864(%rsp)
	vmovdqu	32(%rax), %ymm3
	vpmovzxbw	%xmm7, %ymm1
	vmovdqa	%ymm7, 704(%rsp)
	vmovdqa	%ymm5, 832(%rsp)
	vextracti128	$0x1, %ymm7, %xmm0
	vmovdqa	%ymm4, 800(%rsp)
	vpmovzxwd	%xmm1, %ymm7
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm0, %ymm0
	vmovdqa	%xmm6, 896(%rsp)
	vmovdqu	64(%rax), %ymm5
	vpmovzxwd	%xmm1, %ymm2
	vpmovzxwd	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vmovdqu	264(%rax), %ymm4
	vpaddd	%ymm7, %ymm2, %ymm6
	vpmovzxwd	%xmm0, %ymm0
	vmovdqa	%ymm1, 448(%rsp)
	vpaddd	%ymm1, %ymm6, %ymm6
	vmovdqa	%ymm0, 416(%rsp)
	vmovdqa	%ymm7, 512(%rsp)
	vpaddd	%ymm0, %ymm6, %ymm6
	vmovdqa	%ymm2, 480(%rsp)
	vmovdqa	%ymm15, 736(%rsp)
	vpmovzxbw	%xmm3, %ymm1
	vmovdqa	%ymm3, 672(%rsp)
	vextracti128	$0x1, %ymm3, %xmm0
	vpmovzxwd	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm7
	vpaddd	%ymm3, %ymm6, %ymm6
	vpmovzxwd	%xmm0, %ymm2
	vmovdqa	%ymm3, 384(%rsp)
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm7, %ymm6, %ymm6
	vpmovzxbw	%xmm5, %ymm3
	vmovdqa	%ymm2, 320(%rsp)
	vpmovzxwd	%xmm0, %ymm1
	vmovdqa	%ymm4, 928(%rsp)
	vpaddd	%ymm2, %ymm6, %ymm6
	vmovdqa	128(%rax), %xmm4
	vpaddd	%ymm1, %ymm6, %ymm6
	vextracti128	$0x1, %ymm5, %xmm2
	vpmovzxwd	%xmm3, %ymm10
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm2, %ymm2
	vpaddd	%ymm10, %ymm6, %ymm6
	vmovdqa	%ymm1, 288(%rsp)
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm2, %ymm9
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm15, %ymm1
	vpaddd	%ymm6, %ymm3, %ymm6
	vpmovzxwd	%xmm2, %ymm2
	vextracti128	$0x1, %ymm15, %xmm0
	vpmovzxwd	%xmm1, %ymm8
	vpaddd	%ymm6, %ymm9, %ymm6
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm0, %ymm0
	vmovdqa	%ymm5, 640(%rsp)
	vpaddd	%ymm6, %ymm2, %ymm6
	vpmovzxwd	%xmm1, %ymm1
	vpmovzxwd	%xmm0, %ymm5
	vmovdqa	%ymm7, 352(%rsp)
	vpaddd	%ymm6, %ymm8, %ymm6
	vmovdqa	%ymm5, 608(%rsp)
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm6, %ymm1, %ymm6
	vpmovzxwd	%xmm0, %ymm7
	vpsrldq	$8, %xmm4, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpaddd	%ymm5, %ymm6, %ymm6
	vpmovzxbw	%xmm4, %xmm5
	vmovdqa	%ymm7, 576(%rsp)
	vpmovzxwd	%xmm5, %xmm12
	vpsrldq	$8, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpaddd	%ymm7, %ymm6, %ymm6
	vpaddd	%xmm5, %xmm12, %xmm13
	vpmovzxwd	%xmm0, %xmm7
	vpsrldq	$8, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm0
	vpaddd	%xmm7, %xmm13, %xmm13
	vmovdqa	%xmm7, 544(%rsp)
	vpaddd	%xmm0, %xmm13, %xmm13
	vpaddd	%xmm6, %xmm13, %xmm7
	vpmovzxbw	%xmm11, %xmm13
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm13, %xmm15
	vpaddd	%xmm6, %xmm7, %xmm7
	vpsrlq	$32, %xmm13, %xmm13
	vpsrlq	$32, %xmm11, %xmm6
	vmovq	%xmm15, %rcx
	vpmovzxbw	%xmm6, %xmm6
	vpmovzxwd	%xmm13, %xmm15
	vmovq	%xmm15, %r9
	vpmovzxwd	%xmm6, %xmm15
	vpsrlq	$32, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vmovq	%xmm15, %r10
	vmovq	%xmm6, %rdx
	vmovq	%r9, %xmm15
	vmovq	%rcx, %xmm6
	vpaddd	%xmm15, %xmm6, %xmm6
	vmovq	%r10, %xmm15
	vpaddd	%xmm15, %xmm6, %xmm6
	vmovq	%rdx, %xmm15
	vpaddd	%xmm15, %xmm6, %xmm6
	vpaddd	%xmm7, %xmm6, %xmm6
	vpsrldq	$8, %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm7
	vpsrlq	$32, %xmm7, %xmm6
	vpaddd	%xmm6, %xmm7, %xmm7
	vmovd	%xmm7, %ebx
	cmpl	%ebx, 152(%rax)
	jne	.L67
	vmovdqa	704(%rsp), %ymm7
	vmovdqa	768(%rsp), %ymm15
	vpxor	%xmm13, %xmm13, %xmm13
	movabsq	$6148914691236517205, %r8
	vpxor	864(%rsp), %ymm7, %ymm6
	vpxor	896(%rsp), %xmm4, %xmm4
	vpcmpeqb	.LC30(%rip), %ymm6, %ymm6
	vpcmpeqb	.LC31(%rip), %xmm4, %xmm4
	vpcmpeqb	%ymm13, %ymm6, %ymm6
	vpand	%ymm15, %ymm6, %ymm6
	vpmovzxbw	%xmm6, %ymm7
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm7, %ymm14
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxbw	%xmm6, %ymm6
	vpmovzxwd	%xmm7, %ymm7
	vpaddd	%ymm7, %ymm14, %ymm7
	vpmovzxwd	%xmm6, %ymm14
	vextracti128	$0x1, %ymm6, %xmm6
	vpaddd	%ymm7, %ymm14, %ymm14
	vmovdqa	672(%rsp), %ymm7
	vpmovzxwd	%xmm6, %ymm6
	vpxor	832(%rsp), %ymm7, %ymm7
	vpaddd	%ymm14, %ymm6, %ymm6
	vpcmpeqb	.LC30(%rip), %ymm7, %ymm7
	vpcmpeqb	%ymm13, %ymm7, %ymm7
	vpand	%ymm15, %ymm7, %ymm7
	vpmovzxbw	%xmm7, %ymm14
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxwd	%xmm14, %ymm15
	vextracti128	$0x1, %ymm14, %xmm14
	vpmovzxbw	%xmm7, %ymm7
	vpaddd	%ymm6, %ymm15, %ymm15
	vpmovzxwd	%xmm14, %ymm14
	vpmovzxwd	%xmm7, %ymm6
	vpaddd	%ymm15, %ymm14, %ymm14
	vextracti128	$0x1, %ymm7, %xmm7
	vpaddd	%ymm14, %ymm6, %ymm6
	vpmovzxwd	%xmm7, %ymm7
	vpaddd	%ymm6, %ymm7, %ymm7
	vmovdqa	640(%rsp), %ymm6
	vpxor	800(%rsp), %ymm6, %ymm6
	vpcmpeqb	.LC30(%rip), %ymm6, %ymm6
	vpcmpeqb	%ymm13, %ymm6, %ymm6
	vpand	768(%rsp), %ymm6, %ymm6
	vpmovzxbw	%xmm6, %ymm14
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm14, %ymm15
	vextracti128	$0x1, %ymm14, %xmm14
	vpmovzxbw	%xmm6, %ymm6
	vpaddd	%ymm7, %ymm15, %ymm15
	vpmovzxwd	%xmm14, %ymm14
	vpmovzxwd	%xmm6, %ymm7
	vpaddd	%ymm15, %ymm14, %ymm14
	vextracti128	$0x1, %ymm6, %xmm6
	vpaddd	%ymm14, %ymm7, %ymm7
	vpmovzxwd	%xmm6, %ymm6
	vpaddd	%ymm7, %ymm6, %ymm6
	vmovdqa	736(%rsp), %ymm7
	vpxor	928(%rsp), %ymm7, %ymm7
	vpcmpeqb	.LC30(%rip), %ymm7, %ymm7
	vpcmpeqb	%ymm13, %ymm7, %ymm7
	vpand	768(%rsp), %ymm7, %ymm7
	vpmovzxbw	%xmm7, %ymm13
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxwd	%xmm13, %ymm14
	vextracti128	$0x1, %ymm13, %xmm13
	vpmovzxbw	%xmm7, %ymm7
	vpaddd	%ymm6, %ymm14, %ymm14
	vpmovzxwd	%xmm13, %ymm13
	vpmovzxwd	%xmm7, %ymm6
	vpaddd	%ymm14, %ymm13, %ymm13
	vextracti128	$0x1, %ymm7, %xmm7
	vpaddd	%ymm13, %ymm6, %ymm6
	vpmovzxwd	%xmm7, %ymm7
	vpaddd	%ymm6, %ymm7, %ymm7
	vpxor	%xmm6, %xmm6, %xmm6
	vpcmpeqb	%xmm6, %xmm4, %xmm4
	vpand	256(%rsp), %xmm4, %xmm4
	vpmovzxbw	%xmm4, %xmm6
	vpsrldq	$8, %xmm4, %xmm4
	vpmovzxbw	%xmm4, %xmm4
	vpmovzxwd	%xmm6, %xmm13
	vpsrldq	$8, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vpaddd	%xmm6, %xmm13, %xmm6
	vpmovzxwd	%xmm4, %xmm13
	vpsrldq	$8, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpaddd	%xmm13, %xmm6, %xmm13
	vpaddd	%xmm4, %xmm13, %xmm4
	vpaddd	%xmm7, %xmm4, %xmm6
	vextracti128	$0x1, %ymm7, %xmm7
	vmovq	%rdi, %xmm4
	vpaddd	%xmm7, %xmm6, %xmm6
	vpxor	%xmm4, %xmm11, %xmm4
	vmovq	%r8, %xmm7
	vpcmpeqb	%xmm7, %xmm4, %xmm4
	vpxor	%xmm7, %xmm7, %xmm7
	vpcmpeqb	%xmm7, %xmm4, %xmm4
	vmovq	.LC5(%rip), %xmm7
	vpand	%xmm7, %xmm4, %xmm4
	vpmovzxbw	%xmm4, %xmm7
	vpsrlq	$32, %xmm4, %xmm4
	vpmovzxbw	%xmm4, %xmm4
	vpmovzxwd	%xmm7, %xmm13
	vpsrlq	$32, %xmm7, %xmm7
	vpmovzxwd	%xmm7, %xmm7
	vpaddd	%xmm7, %xmm13, %xmm7
	vpmovzxwd	%xmm4, %xmm13
	vpsrlq	$32, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpaddd	%xmm13, %xmm7, %xmm13
	vmovdqa	480(%rsp), %ymm7
	vpmulld	.LC7(%rip), %ymm7, %ymm7
	vpaddd	%xmm4, %xmm13, %xmm4
	vpaddd	%xmm6, %xmm4, %xmm4
	vpsrldq	$8, %xmm6, %xmm6
	vpaddd	%xmm6, %xmm4, %xmm6
	vmovdqa	512(%rsp), %ymm4
	vpmulld	.LC6(%rip), %ymm4, %ymm4
	vpaddd	%ymm7, %ymm4, %ymm7
	vmovdqa	448(%rsp), %ymm4
	vpmulld	.LC8(%rip), %ymm4, %ymm4
	vpaddd	%ymm7, %ymm4, %ymm4
	vmovdqa	416(%rsp), %ymm7
	vpmulld	.LC9(%rip), %ymm7, %ymm7
	vpaddd	%ymm4, %ymm7, %ymm7
	vmovdqa	384(%rsp), %ymm4
	vpmulld	.LC10(%rip), %ymm4, %ymm4
	vpaddd	%ymm7, %ymm4, %ymm4
	vmovdqa	352(%rsp), %ymm7
	vpmulld	.LC11(%rip), %ymm7, %ymm7
	vpaddd	%ymm4, %ymm7, %ymm7
	vmovdqa	320(%rsp), %ymm4
	vpmulld	.LC12(%rip), %ymm4, %ymm4
	vpmulld	.LC14(%rip), %ymm10, %ymm10
	vpmulld	.LC15(%rip), %ymm3, %ymm3
	vpmulld	.LC16(%rip), %ymm9, %ymm9
	vpmulld	.LC17(%rip), %ymm2, %ymm2
	vpmulld	.LC18(%rip), %ymm8, %ymm8
	vpmulld	.LC19(%rip), %ymm1, %ymm1
	vpmulld	.LC22(%rip), %xmm12, %xmm12
	vpmulld	.LC23(%rip), %xmm5, %xmm5
	vpmulld	.LC25(%rip), %xmm0, %xmm0
	vpaddd	%ymm7, %ymm4, %ymm4
	vmovdqa	288(%rsp), %ymm7
	vpmulld	.LC13(%rip), %ymm7, %ymm7
	vpaddd	%xmm5, %xmm12, %xmm5
	vpaddd	%ymm4, %ymm7, %ymm7
	vmovq	%rcx, %xmm4
	vpaddd	%ymm7, %ymm10, %ymm10
	vpaddd	%ymm10, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm9, %ymm9
	vmovdqa	608(%rsp), %ymm3
	vpaddd	%ymm9, %ymm2, %ymm2
	vpaddd	%ymm2, %ymm8, %ymm8
	vpmulld	.LC20(%rip), %ymm3, %ymm2
	vmovdqa	576(%rsp), %ymm3
	vpaddd	%ymm8, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm2, %ymm2
	vpmulld	.LC21(%rip), %ymm3, %ymm1
	vmovdqa	544(%rsp), %xmm3
	vpmulld	.LC24(%rip), %xmm3, %xmm11
	vmovq	.LC26(%rip), %xmm3
	vpaddd	%ymm2, %ymm1, %ymm1
	vpaddd	%xmm11, %xmm5, %xmm11
	vpaddd	%xmm0, %xmm11, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm2
	vextracti128	$0x1, %ymm1, %xmm1
	vpmulld	%xmm3, %xmm4, %xmm0
	vmovq	.LC27(%rip), %xmm3
	vmovq	%r9, %xmm4
	vpaddd	%xmm1, %xmm2, %xmm1
	vpmulld	%xmm3, %xmm4, %xmm2
	vmovq	.LC28(%rip), %xmm3
	vmovq	%r10, %xmm4
	vpaddd	%xmm2, %xmm0, %xmm0
	vpmulld	%xmm3, %xmm4, %xmm2
	vmovq	.LC29(%rip), %xmm3
	vmovq	%rdx, %xmm4
	vpaddd	%xmm2, %xmm0, %xmm0
	vpmulld	%xmm3, %xmm4, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpsrlq	$32, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vpsrlq	$32, %xmm6, %xmm0
	vpaddd	%xmm0, %xmm6, %xmm6
	vmovd	%xmm1, %edx
	cmpl	156(%rax), %edx
	vmovd	%xmm6, %ecx
	sete	%dl
	sete	%bl
	testl	%ecx, %ecx
	sete	%r10b
	movzbl	%bl, %ebx
	andl	%edx, %r10d
	jmp	.L39
	.p2align 4
	.p2align 3
.L81:
	vmovdqa	832(%rsp), %ymm1
	vmovdqa	864(%rsp), %ymm2
	vpmulld	.LC6(%rip), %ymm2, %ymm2
	vpmulld	.LC7(%rip), %ymm1, %ymm0
	vmovdqa	608(%rsp), %ymm1
	vpmulld	.LC10(%rip), %ymm12, %ymm12
	vpmulld	.LC14(%rip), %ymm11, %ymm11
	vpmulld	.LC15(%rip), %ymm5, %ymm5
	vpmulld	.LC16(%rip), %ymm10, %ymm10
	vpmulld	.LC17(%rip), %ymm4, %ymm4
	vpmulld	.LC18(%rip), %ymm9, %ymm9
	vpmulld	.LC19(%rip), %ymm3, %ymm3
	vpmulld	.LC20(%rip), %ymm8, %ymm8
	vpmulld	.LC23(%rip), %xmm7, %xmm7
	vpaddd	%ymm0, %ymm2, %ymm0
	vpmulld	.LC24(%rip), %xmm13, %xmm13
	vmovdqa	800(%rsp), %ymm2
	vpmulld	.LC8(%rip), %ymm2, %ymm2
	vpmulld	.LC25(%rip), %xmm6, %xmm6
	vpaddd	%ymm0, %ymm2, %ymm2
	vpmulld	.LC9(%rip), %ymm1, %ymm0
	vpaddd	%ymm2, %ymm0, %ymm0
	vmovdqa	576(%rsp), %ymm2
	vpaddd	%ymm0, %ymm12, %ymm12
	vpmulld	.LC11(%rip), %ymm2, %ymm0
	vmovdqa	544(%rsp), %ymm2
	vpaddd	%ymm12, %ymm0, %ymm0
	vpmulld	.LC12(%rip), %ymm2, %ymm12
	vmovdqa	512(%rsp), %ymm2
	vpaddd	%ymm0, %ymm12, %ymm12
	vpmulld	.LC13(%rip), %ymm2, %ymm0
	vpaddd	%ymm12, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm11, %ymm11
	vpaddd	%ymm11, %ymm5, %ymm5
	vpaddd	%ymm5, %ymm10, %ymm10
	vpaddd	%ymm10, %ymm4, %ymm4
	vpaddd	%ymm4, %ymm9, %ymm9
	vmovdqa	896(%rsp), %xmm4
	vpaddd	%ymm9, %ymm3, %ymm3
	vpmulld	.LC22(%rip), %xmm4, %xmm0
	vmovq	.LC26(%rip), %xmm4
	vpaddd	%ymm3, %ymm8, %ymm8
	vmovdqa	928(%rsp), %ymm3
	vpmulld	.LC21(%rip), %ymm3, %ymm1
	vmovq	%rcx, %xmm3
	vpaddd	%xmm7, %xmm0, %xmm7
	vpaddd	%xmm13, %xmm7, %xmm13
	vmovq	%r9, %xmm7
	vpaddd	%ymm8, %ymm1, %ymm1
	vpaddd	%xmm6, %xmm13, %xmm13
	vmovdqa	%xmm1, %xmm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpmulld	%xmm4, %xmm3, %xmm0
	vmovq	.LC27(%rip), %xmm4
	vmovq	%rdx, %xmm3
	vpaddd	%xmm1, %xmm13, %xmm1
	vpmulld	%xmm4, %xmm3, %xmm2
	vmovq	.LC28(%rip), %xmm3
	vmovq	.LC29(%rip), %xmm4
	vpaddd	%xmm2, %xmm0, %xmm0
	vpmulld	%xmm3, %xmm7, %xmm2
	vpmulld	%xmm4, %xmm14, %xmm14
	vpaddd	%xmm2, %xmm0, %xmm0
	vpaddd	%xmm14, %xmm0, %xmm14
	vpaddd	%xmm1, %xmm14, %xmm14
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm14, %xmm1
	vpsrlq	$32, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vmovd	%xmm1, %edx
	cmpl	%edx, 324(%rax)
	jne	.L40
	testb	%r10b, %r10b
	je	.L83
	incl	160(%rax)
	incl	328(%rax)
	addq	$336, %rax
	incq	%rsi
	cmpq	%rax, %r11
	jne	.L46
	.p2align 4
	.p2align 3
.L82:
	movq	224(%rsp), %rdi
	leaq	87232(%rsp), %rax
	vmovdqa	192(%rsp), %ymm11
	movq	%r15, %r8
	addq	$10752, %r11
	addq	$32, %rdi
	cmpq	%rax, %rdi
	jne	.L37
	movq	96(%rsp), %r8
	imulq	$336, %r15, %rax
	movq	%r13, %rcx
	movzbl	184(%rsp), %r12d
	movq	128(%rsp), %r14
	movq	160(%rsp), %r13
	movq	%r15, %r10
	vmovdqa	%ymm11, 96(%rsp)
	imulq	$10752, %r8, %rdx
	addq	%rdx, %rax
	cmpl	$-559063315, 1124(%rsp,%rax)
	jne	.L48
	movq	16(%rsp), %rax
	incq	(%rax)
	movq	8(%rsp), %rax
	incq	(%rax)
.L48:
	movq	%rcx, 864(%rsp)
	movq	%r10, 896(%rsp)
	movl	$86336, %edx
	movq	%r8, 928(%rsp)
	leaq	clean.1(%rip), %rsi
	leaq	960(%rsp), %rdi
	vzeroupper
	call	memcpy@PLT
	movq	%r14, %r11
	xorl	%r14d, %r14d
	movq	928(%rsp), %r8
	movq	896(%rsp), %r10
	movq	864(%rsp), %rcx
	imulq	$336, %r10, %rdx
	imulq	$10752, %r8, %rax
	addq	%rdx, %rax
	leaq	87616(%rsp,%rax), %rdx
	addq	%rdx, %rcx
	xorb	%r12b, -86656(%rcx)
	vmovdqu	-86560(%rdx), %ymm2
	vmovdqu	-86656(%rdx), %ymm1
	vmovdqu	-86624(%rdx), %ymm3
	vmovdqu	-86592(%rdx), %ymm0
	xorb	%r12b, -86488(%rcx)
	vmovdqa	%ymm2, 87392(%rsp)
	vmovdqu	-86536(%rdx), %ymm2
	vmovdqa	%ymm1, 87296(%rsp)
	vmovdqa	%ymm3, 87328(%rsp)
	vmovdqa	%ymm0, 87360(%rsp)
	vmovdqu	%ymm2, 87416(%rsp)
	vpmovzxbw	%xmm1, %ymm2
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm2, %ymm6
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm1, %ymm1
	vpmovzxwd	%xmm2, %ymm2
	vpmovzxwd	%xmm1, %ymm5
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm6, %ymm2, %ymm4
	vpmulld	.LC6(%rip), %ymm6, %ymm6
	vpmovzxwd	%xmm1, %ymm1
	vpmulld	.LC7(%rip), %ymm2, %ymm2
	vpaddd	%ymm5, %ymm4, %ymm4
	vpmulld	.LC8(%rip), %ymm5, %ymm5
	vpaddd	%ymm1, %ymm4, %ymm4
	vpmulld	.LC9(%rip), %ymm1, %ymm1
	vpaddd	%ymm6, %ymm2, %ymm2
	vpaddd	%ymm2, %ymm5, %ymm2
	vpmovzxbw	%xmm3, %ymm5
	vpmovzxwd	%xmm5, %ymm6
	vpaddd	%ymm2, %ymm1, %ymm1
	vextracti128	$0x1, %ymm3, %xmm2
	vextracti128	$0x1, %ymm5, %xmm3
	vpaddd	%ymm4, %ymm6, %ymm4
	vpmulld	.LC10(%rip), %ymm6, %ymm6
	vpmovzxbw	%xmm2, %ymm2
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm2, %ymm5
	vpaddd	%ymm3, %ymm4, %ymm4
	vpmulld	.LC11(%rip), %ymm3, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm2, %ymm2
	vpaddd	%ymm5, %ymm4, %ymm4
	vpaddd	%ymm2, %ymm4, %ymm4
	vpmulld	.LC13(%rip), %ymm2, %ymm2
	vpaddd	%ymm1, %ymm6, %ymm1
	vpaddd	%ymm1, %ymm3, %ymm3
	vpmulld	.LC12(%rip), %ymm5, %ymm1
	vpaddd	%ymm3, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm2, %ymm3
	vpmovzxbw	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm6
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm0, %ymm5
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm2
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm4, %ymm6, %ymm0
	vpmulld	.LC14(%rip), %ymm6, %ymm6
	vpaddd	%ymm2, %ymm0, %ymm0
	vpmulld	.LC15(%rip), %ymm2, %ymm2
	vpaddd	%ymm5, %ymm0, %ymm0
	vpmulld	.LC16(%rip), %ymm5, %ymm5
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC17(%rip), %ymm1, %ymm1
	vpaddd	%ymm3, %ymm6, %ymm3
	vpaddd	%ymm3, %ymm2, %ymm2
	vpaddd	%ymm2, %ymm5, %ymm2
	vpaddd	%ymm2, %ymm1, %ymm3
	vmovdqa	87392(%rsp), %ymm2
	vpmovzxbw	%xmm2, %ymm1
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm1, %ymm6
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm2, %ymm2
	vpaddd	%ymm6, %ymm0, %ymm5
	vpmulld	.LC18(%rip), %ymm6, %ymm6
	vpmovzxwd	%xmm1, %ymm1
	vpmovzxwd	%xmm2, %ymm4
	vpmulld	.LC19(%rip), %ymm1, %ymm0
	vpaddd	%ymm5, %ymm1, %ymm5
	vextracti128	$0x1, %ymm2, %xmm2
	vpmulld	.LC20(%rip), %ymm4, %ymm1
	vpmovzxwd	%xmm2, %ymm2
	vpaddd	%ymm5, %ymm4, %ymm5
	movq	%r8, 40(%rsp)
	vpaddd	%ymm5, %ymm2, %ymm5
	movq	%r10, 32(%rsp)
	vpaddd	%ymm3, %ymm6, %ymm3
	vpaddd	%ymm3, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC21(%rip), %ymm2, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vmovdqa	87424(%rsp), %xmm1
	vpmovzxbw	%xmm1, %xmm3
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm3, %xmm2
	vpsrldq	$8, %xmm3, %xmm3
	vpmovzxwd	%xmm3, %xmm3
	vpmovzxwd	%xmm1, %xmm6
	vpaddd	%xmm3, %xmm2, %xmm4
	vpmulld	.LC23(%rip), %xmm3, %xmm3
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm1
	vpmulld	.LC22(%rip), %xmm2, %xmm2
	vpaddd	%xmm6, %xmm4, %xmm4
	vpmulld	.LC24(%rip), %xmm6, %xmm6
	vpaddd	%xmm1, %xmm4, %xmm4
	vpmulld	.LC25(%rip), %xmm1, %xmm1
	vpaddd	%xmm5, %xmm4, %xmm4
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%xmm5, %xmm4, %xmm4
	vpaddd	%xmm3, %xmm2, %xmm2
	vpaddd	%xmm6, %xmm2, %xmm2
	vpaddd	%xmm1, %xmm2, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vmovq	87440(%rsp), %xmm0
	vpmovzxbw	%xmm0, %xmm5
	vpsrlq	$32, %xmm0, %xmm3
	vpmovzxbw	%xmm3, %xmm3
	vpmovzxwd	%xmm5, %xmm0
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpmovzxwd	%xmm3, %xmm6
	vpaddd	%xmm5, %xmm0, %xmm2
	vpsrlq	$32, %xmm3, %xmm3
	vpmovzxwd	%xmm3, %xmm3
	vpaddd	%xmm6, %xmm2, %xmm2
	vpaddd	%xmm3, %xmm2, %xmm2
	vpaddd	%xmm4, %xmm2, %xmm2
	vpsrldq	$8, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm2, %xmm2
	vmovq	.LC26(%rip), %xmm4
	vpmulld	%xmm4, %xmm0, %xmm0
	vmovq	.LC27(%rip), %xmm4
	vpmulld	%xmm4, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm0
	vmovq	.LC28(%rip), %xmm5
	vpmulld	%xmm5, %xmm6, %xmm6
	vmovq	.LC29(%rip), %xmm5
	vpaddd	%xmm6, %xmm0, %xmm0
	vpmulld	%xmm5, %xmm3, %xmm3
	vpaddd	%xmm3, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm2, %xmm1
	vpaddd	%xmm1, %xmm2, %xmm2
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vinsertps	$16, %xmm0, %xmm2, %xmm0
	vmovq	%xmm0, 1112(%rsp,%rax)
	vmovq	%xmm0, 1280(%rsp,%rax)
	vpcmpeqd	%ymm0, %ymm0, %ymm0
	vpabsb	%ymm0, %ymm5
	vmovdqa	%ymm5, 576(%rsp)
	.p2align 4
	.p2align 3
.L49:
	vpcmpeqd	%xmm0, %xmm0, %xmm0
	movq	%r14, %rbx
	vmovdqa	96(%rsp), %ymm10
	leaq	-10752(%r11), %rax
	vpabsb	%xmm0, %xmm3
	movq	%r13, %rsi
	movq	%r11, %r14
	movq	%r13, 176(%rsp)
	vmovdqa	%xmm3, 80(%rsp)
	jmp	.L61
	.p2align 4
	.p2align 3
.L68:
	movabsq	$6148914691236517205, %rcx
	xorl	%r12d, %r12d
	xorl	%r13d, %r13d
	movq	%rcx, 768(%rsp)
	vmovq	%rcx, %xmm5
.L51:
	vpxor	928(%rsp), %ymm10, %ymm4
	vpxor	896(%rsp), %ymm10, %ymm7
	vmovdqa	800(%rsp), %xmm3
	vpxor	.LC31(%rip), %xmm3, %xmm14
	vmovq	%r8, %xmm3
	vpxor	864(%rsp), %ymm10, %ymm15
	vpxor	%xmm5, %xmm3, %xmm3
	vpxor	832(%rsp), %ymm10, %ymm9
	vmovq	%xmm3, %r10
	vpmovzxbw	%xmm4, %ymm1
	vextracti128	$0x1, %ymm4, %xmm0
	vmovdqa	%ymm4, 192(%rsp)
	vpmovzxwd	%xmm1, %ymm3
	vpmovzxbw	%xmm0, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vmovdqa	%ymm7, 224(%rsp)
	vpmovzxwd	%xmm1, %ymm5
	vpmovzxwd	%xmm0, %ymm4
	vextracti128	$0x1, %ymm0, %xmm0
	vmovdqa	%ymm3, 352(%rsp)
	vpmovzxwd	%xmm0, %ymm2
	vpaddd	%ymm3, %ymm5, %ymm0
	vextracti128	$0x1, %ymm7, %xmm1
	vmovdqa	%ymm5, 320(%rsp)
	vpaddd	%ymm4, %ymm0, %ymm0
	vmovdqa	%ymm2, 256(%rsp)
	vpmovzxbw	%xmm1, %ymm1
	vmovdqa	%ymm4, 288(%rsp)
	vpaddd	%ymm2, %ymm0, %ymm0
	vpmovzxbw	%xmm7, %ymm2
	vpmovzxwd	%xmm1, %ymm4
	vpmovzxbw	%xmm15, %ymm6
	vpmovzxwd	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm6, %ymm12
	vpmovzxwd	%xmm2, %ymm5
	vpaddd	%ymm3, %ymm0, %ymm0
	vpmovzxwd	%xmm1, %ymm7
	vmovdqa	%ymm4, 512(%rsp)
	vpaddd	%ymm5, %ymm0, %ymm0
	vmovdqa	%ymm5, 480(%rsp)
	vextracti128	$0x1, %ymm6, %xmm6
	vmovdqa	%ymm9, 128(%rsp)
	vpaddd	%ymm4, %ymm0, %ymm0
	vextracti128	$0x1, %ymm15, %xmm5
	vpmovzxwd	%xmm6, %ymm6
	vpmovzxbw	%xmm9, %ymm4
	vpaddd	%ymm7, %ymm0, %ymm0
	vpmovzxbw	%xmm5, %ymm5
	vmovdqa	%ymm3, 448(%rsp)
	vmovdqa	%ymm7, 544(%rsp)
	vpaddd	%ymm12, %ymm0, %ymm0
	vpmovzxwd	%xmm5, %ymm11
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxbw	%xmm14, %xmm7
	vpaddd	%ymm0, %ymm6, %ymm0
	vpmovzxwd	%xmm5, %ymm5
	vextracti128	$0x1, %ymm9, %xmm3
	vpmovzxwd	%xmm4, %ymm9
	vpaddd	%ymm0, %ymm11, %ymm0
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxbw	%xmm3, %ymm3
	vpmovzxwd	%xmm7, %xmm1
	vpaddd	%ymm5, %ymm0, %ymm0
	vpmovzxwd	%xmm4, %ymm4
	vpmovzxwd	%xmm3, %ymm8
	vpsrldq	$8, %xmm14, %xmm2
	vpaddd	%ymm9, %ymm0, %ymm0
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm2, %xmm2
	vpsrldq	$8, %xmm7, %xmm7
	vpaddd	%ymm0, %ymm4, %ymm0
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm7, %xmm7
	vmovdqa	%xmm14, 160(%rsp)
	vpaddd	%ymm0, %ymm8, %ymm0
	vpmovzxwd	%xmm2, %xmm14
	vmovdqa	%xmm1, 416(%rsp)
	vpaddd	%xmm1, %xmm7, %xmm1
	vpaddd	%ymm0, %ymm3, %ymm0
	vpaddd	%xmm14, %xmm1, %xmm1
	vpsrldq	$8, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm2
	vmovdqa	%xmm0, %xmm13
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm2, %xmm1, %xmm1
	vmovdqa	%xmm2, 384(%rsp)
	vpaddd	%xmm0, %xmm13, %xmm13
	vmovq	%r10, %xmm0
	vpaddd	%xmm13, %xmm1, %xmm1
	vpmovzxbw	%xmm0, %xmm13
	vpsrlq	$32, %xmm0, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpmovzxwd	%xmm13, %xmm2
	vpsrlq	$32, %xmm13, %xmm13
	vmovq	%xmm2, %r11
	vpmovzxwd	%xmm13, %xmm2
	vmovq	%xmm2, %rcx
	vpmovzxwd	%xmm0, %xmm2
	vpsrlq	$32, %xmm0, %xmm0
	vmovq	%xmm2, %r9
	vpmovzxwd	%xmm0, %xmm2
	vmovq	%rcx, %xmm0
	vmovq	%xmm2, %rdx
	vmovq	%r11, %xmm2
	vpaddd	%xmm0, %xmm2, %xmm0
	vmovq	%r9, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vmovq	%rdx, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpsrlq	$32, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vmovd	%xmm1, %r15d
	cmpl	%r15d, 320(%rax)
	vmovq	%xmm1, 184(%rsp)
	je	.L84
.L52:
	testl	%r13d, %r13d
	jne	.L55
	testb	%r12b, %r12b
	jne	.L55
	movl	$-559063315, 164(%rax)
	movl	$-559063315, 332(%rax)
	incq	87280(%rsp)
	.p2align 5
	.p2align 4
	.p2align 3
.L59:
	addq	$336, %rax
	incq	%rsi
	cmpq	%r14, %rax
	je	.L85
.L61:
	cmpb	$0, (%rsi)
	je	.L59
	cmpl	$-559063315, 164(%rax)
	je	.L59
	vmovdqu	232(%rax), %ymm5
	vmovdqu	168(%rax), %ymm3
	vmovdqu	(%rax), %ymm4
	vmovdqu	32(%rax), %ymm7
	vmovdqu	96(%rax), %ymm6
	vmovdqa	128(%rax), %xmm12
	movq	144(%rax), %rdi
	movq	312(%rax), %r8
	vmovdqa	%ymm5, 864(%rsp)
	vmovdqu	264(%rax), %ymm5
	vmovdqa	%ymm3, 928(%rsp)
	vmovdqu	200(%rax), %ymm3
	vpmovzxbw	%xmm4, %ymm1
	vmovdqa	%ymm4, 672(%rsp)
	vextracti128	$0x1, %ymm4, %xmm0
	vpmovzxwd	%xmm1, %ymm4
	vextracti128	$0x1, %ymm1, %xmm1
	vmovdqa	%ymm7, 736(%rsp)
	vpmovzxbw	%xmm0, %ymm0
	vmovdqa	%ymm4, 416(%rsp)
	vmovdqa	%ymm6, 640(%rsp)
	vmovdqa	%xmm12, 608(%rsp)
	vpmovzxwd	%xmm0, %ymm2
	vextracti128	$0x1, %ymm0, %xmm0
	vmovdqa	%ymm2, 352(%rsp)
	vmovdqa	%ymm5, 832(%rsp)
	vmovdqu	296(%rax), %xmm5
	vmovdqa	%ymm3, 896(%rsp)
	vmovdqu	64(%rax), %ymm3
	vmovdqa	%xmm5, 800(%rsp)
	vpmovzxwd	%xmm1, %ymm5
	vpmovzxwd	%xmm0, %ymm1
	vmovdqa	%ymm3, 704(%rsp)
	vmovdqa	%ymm5, 384(%rsp)
	vpaddd	%ymm4, %ymm5, %ymm5
	vextracti128	$0x1, %ymm7, %xmm0
	vmovdqa	%ymm1, 320(%rsp)
	vpaddd	%ymm2, %ymm5, %ymm5
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm5, %ymm5
	vpmovzxbw	%xmm7, %ymm1
	vpmovzxwd	%xmm0, %ymm2
	vpmovzxwd	%xmm1, %ymm4
	vextracti128	$0x1, %ymm1, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vmovdqa	%ymm2, 480(%rsp)
	vpmovzxwd	%xmm1, %ymm7
	vpaddd	%ymm4, %ymm5, %ymm5
	vpmovzxwd	%xmm0, %ymm1
	vmovdqa	%ymm4, 544(%rsp)
	vpaddd	%ymm7, %ymm5, %ymm5
	vmovdqa	%ymm3, %ymm4
	vpmovzxbw	%xmm3, %ymm3
	vmovdqa	%ymm1, 448(%rsp)
	vpaddd	%ymm2, %ymm5, %ymm5
	vpmovzxwd	%xmm3, %ymm9
	vextracti128	$0x1, %ymm4, %xmm2
	vmovdqa	%ymm7, 512(%rsp)
	vpaddd	%ymm1, %ymm5, %ymm5
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm2, %ymm2
	vpmovzxbw	%xmm6, %ymm1
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm9, %ymm5, %ymm5
	vpmovzxwd	%xmm2, %ymm8
	vpmovzxwd	%xmm1, %ymm7
	vextracti128	$0x1, %ymm2, %xmm2
	vpaddd	%ymm5, %ymm3, %ymm5
	vextracti128	$0x1, %ymm6, %xmm0
	vpmovzxwd	%xmm2, %ymm2
	vpaddd	%ymm5, %ymm8, %ymm5
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm5, %ymm2, %ymm5
	vpmovzxwd	%xmm1, %ymm1
	vpmovzxwd	%xmm0, %ymm4
	vpaddd	%ymm7, %ymm5, %ymm5
	vmovdqa	%ymm4, 288(%rsp)
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm5, %ymm1, %ymm5
	vpmovzxwd	%xmm0, %ymm6
	vpsrldq	$8, %xmm12, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpaddd	%ymm4, %ymm5, %ymm5
	vpmovzxbw	%xmm12, %xmm4
	vpmovzxwd	%xmm0, %xmm11
	vpsrldq	$8, %xmm0, %xmm0
	vpmovzxwd	%xmm4, %xmm12
	vpsrldq	$8, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpmovzxwd	%xmm0, %xmm0
	vpaddd	%xmm4, %xmm12, %xmm13
	vpaddd	%ymm6, %ymm5, %ymm5
	vmovdqa	%ymm6, 256(%rsp)
	vpaddd	%xmm11, %xmm13, %xmm13
	vpaddd	%xmm0, %xmm13, %xmm13
	vpaddd	%xmm5, %xmm13, %xmm6
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm6
	vmovq	%rdi, %xmm5
	vpmovzxbw	%xmm5, %xmm13
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxbw	%xmm5, %xmm5
	vpmovzxwd	%xmm13, %xmm15
	vpsrlq	$32, %xmm13, %xmm13
	vmovq	%xmm15, %rcx
	vpmovzxwd	%xmm13, %xmm15
	vmovq	%xmm15, %r9
	vpmovzxwd	%xmm5, %xmm15
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vmovq	%xmm15, %r10
	vmovq	%xmm5, %rdx
	vmovq	%r9, %xmm15
	vmovq	%rcx, %xmm5
	vpaddd	%xmm15, %xmm5, %xmm5
	vmovq	%r10, %xmm15
	vpaddd	%xmm15, %xmm5, %xmm5
	vmovq	%rdx, %xmm15
	vpaddd	%xmm15, %xmm5, %xmm5
	vpaddd	%xmm6, %xmm5, %xmm5
	vpsrldq	$8, %xmm6, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm6
	vpsrlq	$32, %xmm6, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm6
	vmovd	%xmm6, %r11d
	cmpl	%r11d, 152(%rax)
	jne	.L68
	vmovdqa	672(%rsp), %ymm5
	vmovdqa	576(%rsp), %ymm15
	vpxor	%xmm13, %xmm13, %xmm13
	movabsq	$6148914691236517205, %r15
	vpxor	928(%rsp), %ymm5, %ymm5
	movq	%r15, 768(%rsp)
	vpcmpeqb	%ymm10, %ymm5, %ymm5
	vpcmpeqb	%ymm13, %ymm5, %ymm5
	vpand	%ymm15, %ymm5, %ymm5
	vpmovzxbw	%xmm5, %ymm6
	vextracti128	$0x1, %ymm5, %xmm5
	vextracti128	$0x1, %ymm6, %xmm14
	vpmovzxbw	%xmm5, %ymm5
	vpmovzxwd	%xmm6, %ymm6
	vpmovzxwd	%xmm14, %ymm14
	vpaddd	%ymm6, %ymm14, %ymm6
	vpmovzxwd	%xmm5, %ymm14
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%ymm6, %ymm14, %ymm14
	vmovdqa	896(%rsp), %ymm6
	vpmovzxwd	%xmm5, %ymm5
	vpxor	736(%rsp), %ymm6, %ymm6
	vpaddd	%ymm14, %ymm5, %ymm5
	vpcmpeqb	%ymm10, %ymm6, %ymm6
	vpcmpeqb	%ymm13, %ymm6, %ymm6
	vpand	%ymm15, %ymm6, %ymm6
	vpmovzxbw	%xmm6, %ymm14
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm14, %ymm15
	vextracti128	$0x1, %ymm14, %xmm14
	vpmovzxbw	%xmm6, %ymm6
	vpaddd	%ymm5, %ymm15, %ymm15
	vpmovzxwd	%xmm14, %ymm14
	vpmovzxwd	%xmm6, %ymm5
	vpaddd	%ymm15, %ymm14, %ymm14
	vextracti128	$0x1, %ymm6, %xmm6
	vpaddd	%ymm14, %ymm5, %ymm5
	vpmovzxwd	%xmm6, %ymm6
	vpaddd	%ymm5, %ymm6, %ymm6
	vmovdqa	864(%rsp), %ymm5
	vpxor	704(%rsp), %ymm5, %ymm5
	vpcmpeqb	%ymm10, %ymm5, %ymm5
	vpcmpeqb	%ymm13, %ymm5, %ymm5
	vpand	576(%rsp), %ymm5, %ymm5
	vpmovzxbw	%xmm5, %ymm14
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm14, %ymm15
	vextracti128	$0x1, %ymm14, %xmm14
	vpmovzxbw	%xmm5, %ymm5
	vpaddd	%ymm6, %ymm15, %ymm15
	vpmovzxwd	%xmm14, %ymm14
	vpmovzxwd	%xmm5, %ymm6
	vpaddd	%ymm15, %ymm14, %ymm14
	vmovq	%r8, %xmm15
	vpaddd	%ymm14, %ymm6, %ymm6
	vextracti128	$0x1, %ymm5, %xmm14
	vmovdqa	640(%rsp), %ymm5
	vpxor	832(%rsp), %ymm5, %ymm5
	vpmovzxwd	%xmm14, %ymm14
	vpaddd	%ymm6, %ymm14, %ymm14
	vpcmpeqb	%ymm10, %ymm5, %ymm5
	vpcmpeqb	%ymm13, %ymm5, %ymm5
	vpand	576(%rsp), %ymm5, %ymm5
	vpmovzxbw	%xmm5, %ymm6
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm6, %ymm13
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxbw	%xmm5, %ymm5
	vpaddd	%ymm14, %ymm13, %ymm13
	vpmovzxwd	%xmm6, %ymm6
	vpaddd	%ymm13, %ymm6, %ymm6
	vpmovzxwd	%xmm5, %ymm13
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%ymm6, %ymm13, %ymm13
	vmovdqa	608(%rsp), %xmm6
	vpmovzxwd	%xmm5, %ymm5
	vpxor	800(%rsp), %xmm6, %xmm6
	vpaddd	%ymm13, %ymm5, %ymm5
	vpxor	%xmm13, %xmm13, %xmm13
	vpcmpeqb	96(%rsp), %xmm6, %xmm6
	vpcmpeqb	%xmm13, %xmm6, %xmm6
	vpand	80(%rsp), %xmm6, %xmm6
	vpmovzxbw	%xmm6, %xmm13
	vpsrldq	$8, %xmm6, %xmm6
	vpmovzxbw	%xmm6, %xmm6
	vpmovzxwd	%xmm13, %xmm14
	vpsrldq	$8, %xmm13, %xmm13
	vpmovzxwd	%xmm13, %xmm13
	vpaddd	%xmm13, %xmm14, %xmm13
	vpmovzxwd	%xmm6, %xmm14
	vpsrldq	$8, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vpaddd	%xmm14, %xmm13, %xmm14
	vpaddd	%xmm6, %xmm14, %xmm6
	vpaddd	%xmm5, %xmm6, %xmm13
	vmovq	%rdi, %xmm6
	vextracti128	$0x1, %ymm5, %xmm5
	vpxor	%xmm15, %xmm6, %xmm6
	vmovq	%r15, %xmm15
	vpaddd	%xmm5, %xmm13, %xmm5
	vpxor	%xmm13, %xmm13, %xmm13
	vpcmpeqb	%xmm15, %xmm6, %xmm6
	vmovq	.LC5(%rip), %xmm15
	vpcmpeqb	%xmm13, %xmm6, %xmm6
	vpand	%xmm15, %xmm6, %xmm6
	vmovdqa	384(%rsp), %ymm15
	vpmovzxbw	%xmm6, %xmm13
	vpsrlq	$32, %xmm6, %xmm6
	vpmovzxbw	%xmm6, %xmm6
	vpmovzxwd	%xmm13, %xmm14
	vpsrlq	$32, %xmm13, %xmm13
	vpmovzxwd	%xmm13, %xmm13
	vpaddd	%xmm13, %xmm14, %xmm13
	vpmovzxwd	%xmm6, %xmm14
	vpsrlq	$32, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vpaddd	%xmm14, %xmm13, %xmm14
	vpmulld	.LC7(%rip), %ymm15, %ymm13
	vmovdqa	320(%rsp), %ymm15
	vpaddd	%xmm6, %xmm14, %xmm6
	vpaddd	%xmm5, %xmm6, %xmm6
	vpsrldq	$8, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm6, %xmm5
	vmovdqa	416(%rsp), %ymm6
	vpmulld	.LC6(%rip), %ymm6, %ymm6
	vpaddd	%ymm13, %ymm6, %ymm13
	vmovdqa	352(%rsp), %ymm6
	vpmulld	.LC8(%rip), %ymm6, %ymm6
	vpaddd	%ymm13, %ymm6, %ymm6
	vpmulld	.LC9(%rip), %ymm15, %ymm13
	vmovdqa	512(%rsp), %ymm15
	vpaddd	%ymm6, %ymm13, %ymm13
	vmovdqa	544(%rsp), %ymm6
	vpmulld	.LC10(%rip), %ymm6, %ymm6
	vpaddd	%ymm13, %ymm6, %ymm6
	vpmulld	.LC11(%rip), %ymm15, %ymm13
	vmovdqa	448(%rsp), %ymm15
	vpaddd	%ymm6, %ymm13, %ymm13
	vmovdqa	480(%rsp), %ymm6
	vpmulld	.LC12(%rip), %ymm6, %ymm6
	vpaddd	%ymm13, %ymm6, %ymm6
	vpmulld	.LC13(%rip), %ymm15, %ymm13
	vpmulld	.LC14(%rip), %ymm9, %ymm9
	vpmulld	.LC15(%rip), %ymm3, %ymm3
	vpmulld	.LC16(%rip), %ymm8, %ymm8
	vpmulld	.LC17(%rip), %ymm2, %ymm2
	vpmulld	.LC18(%rip), %ymm7, %ymm7
	vpmulld	.LC19(%rip), %ymm1, %ymm1
	vpmulld	.LC22(%rip), %xmm12, %xmm12
	vpmulld	.LC23(%rip), %xmm4, %xmm4
	vpmulld	.LC24(%rip), %xmm11, %xmm11
	vpaddd	%ymm6, %ymm13, %ymm13
	vpmulld	.LC25(%rip), %xmm0, %xmm0
	vpaddd	%ymm13, %ymm9, %ymm9
	vpaddd	%ymm9, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm8, %ymm8
	vmovdqa	256(%rsp), %ymm3
	vpaddd	%ymm8, %ymm2, %ymm2
	vpaddd	%ymm2, %ymm7, %ymm7
	vpaddd	%ymm7, %ymm1, %ymm1
	vmovdqa	288(%rsp), %ymm7
	vpmulld	.LC20(%rip), %ymm7, %ymm2
	vmovq	.LC26(%rip), %xmm7
	vpaddd	%xmm4, %xmm12, %xmm4
	vpaddd	%xmm11, %xmm4, %xmm11
	vmovq	%rcx, %xmm4
	vpaddd	%xmm0, %xmm11, %xmm0
	vpaddd	%ymm1, %ymm2, %ymm2
	vpmulld	.LC21(%rip), %ymm3, %ymm1
	vmovq	%r9, %xmm3
	vpaddd	%ymm2, %ymm1, %ymm1
	vpaddd	%xmm1, %xmm0, %xmm2
	vextracti128	$0x1, %ymm1, %xmm1
	vpmulld	%xmm7, %xmm4, %xmm0
	vmovq	.LC27(%rip), %xmm4
	vpaddd	%xmm1, %xmm2, %xmm1
	vmovq	%r10, %xmm7
	vpmulld	%xmm4, %xmm3, %xmm2
	vmovq	.LC28(%rip), %xmm3
	vmovq	%rdx, %xmm4
	vpaddd	%xmm2, %xmm0, %xmm0
	vpmulld	%xmm3, %xmm7, %xmm2
	vmovq	.LC29(%rip), %xmm7
	vpaddd	%xmm2, %xmm0, %xmm0
	vpmulld	%xmm7, %xmm4, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpsrlq	$32, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vpsrlq	$32, %xmm5, %xmm0
	vpaddd	%xmm0, %xmm5, %xmm5
	vmovd	%xmm1, %edx
	cmpl	156(%rax), %edx
	vmovd	%xmm5, %ecx
	vmovq	%r15, %xmm5
	sete	%dl
	sete	%r13b
	testl	%ecx, %ecx
	sete	%r12b
	movzbl	%r13b, %r13d
	andl	%edx, %r12d
	jmp	.L51
	.p2align 4
	.p2align 3
.L43:
	vmovdqu	96(%rax), %ymm2
	vmovdqa	704(%rsp), %ymm5
	vmovq	%r8, %xmm3
	vmovdqa	736(%rsp), %ymm7
	vmovdqu	(%rax), %ymm0
	vmovdqu	32(%rax), %ymm4
	vmovdqu	64(%rax), %ymm1
	vmovdqa	%ymm2, 87552(%rsp)
	vmovdqu	120(%rax), %ymm2
	vmovdqa	%ymm0, 87456(%rsp)
	vmovdqa	%ymm4, 87488(%rsp)
	vmovdqa	%ymm1, 87520(%rsp)
	vmovdqu	%ymm2, 87576(%rsp)
	vpxor	.LC30(%rip), %ymm5, %ymm2
	vmovdqa	672(%rsp), %ymm5
	vmovdqu	%ymm2, 168(%rax)
	vpxor	.LC30(%rip), %ymm5, %ymm2
	vmovdqa	640(%rsp), %ymm5
	vmovdqu	%ymm2, 200(%rax)
	vpxor	.LC30(%rip), %ymm5, %ymm2
	vmovdqa	87584(%rsp), %xmm5
	vmovdqu	%ymm2, 232(%rax)
	vpxor	.LC30(%rip), %ymm7, %ymm2
	vmovdqu	%ymm2, 264(%rax)
	vpxor	.LC31(%rip), %xmm5, %xmm2
	vmovdqu	%xmm2, 296(%rax)
	vmovq	87600(%rsp), %xmm2
	vpxor	%xmm3, %xmm2, %xmm3
	vmovq	%xmm3, 312(%rax)
	vpmovzxbw	%xmm0, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm3, %ymm7
	vpmovzxbw	%xmm0, %ymm0
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxwd	%xmm0, %ymm8
	vpmovzxwd	%xmm3, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm6
	vpaddd	%ymm3, %ymm7, %ymm0
	vpmulld	.LC7(%rip), %ymm3, %ymm3
	vpmulld	.LC6(%rip), %ymm7, %ymm7
	vpaddd	%ymm0, %ymm8, %ymm0
	vpaddd	%ymm0, %ymm6, %ymm0
	vpmulld	.LC9(%rip), %ymm6, %ymm6
	vpaddd	%ymm3, %ymm7, %ymm7
	vpmulld	.LC8(%rip), %ymm8, %ymm3
	vpaddd	%ymm7, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm6, %ymm6
	vpmovzxbw	%xmm4, %ymm3
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxwd	%xmm3, %ymm8
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm4, %ymm4
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm8, %ymm0, %ymm0
	vpmulld	.LC10(%rip), %ymm8, %ymm8
	vpmovzxwd	%xmm4, %ymm7
	vpaddd	%ymm0, %ymm3, %ymm0
	vpmulld	.LC11(%rip), %ymm3, %ymm3
	vextracti128	$0x1, %ymm4, %xmm4
	movl	$0, 332(%rax)
	vpaddd	%ymm0, %ymm7, %ymm0
	vpmulld	.LC12(%rip), %ymm7, %ymm7
	vpmovzxwd	%xmm4, %ymm4
	vpaddd	%ymm0, %ymm4, %ymm0
	vpmulld	.LC13(%rip), %ymm4, %ymm4
	vpaddd	%ymm6, %ymm8, %ymm8
	vpaddd	%ymm8, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm7, %ymm7
	vpmovzxbw	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm3, %ymm6
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm7, %ymm4, %ymm4
	vpaddd	%ymm6, %ymm0, %ymm0
	vpmulld	.LC14(%rip), %ymm6, %ymm6
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm1, %ymm7
	vpaddd	%ymm0, %ymm3, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpmulld	.LC15(%rip), %ymm3, %ymm3
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm7, %ymm0
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC17(%rip), %ymm1, %ymm1
	vpaddd	%ymm4, %ymm6, %ymm6
	vpmulld	.LC16(%rip), %ymm7, %ymm4
	vpaddd	%ymm6, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm4, %ymm4
	vpaddd	%ymm4, %ymm1, %ymm3
	vmovdqa	87552(%rsp), %ymm1
	vpmovzxbw	%xmm1, %ymm4
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm4, %ymm6
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm6, %ymm0
	vpmulld	.LC18(%rip), %ymm6, %ymm6
	vpmovzxwd	%xmm4, %ymm4
	vpmovzxwd	%xmm1, %ymm7
	vpaddd	%ymm0, %ymm4, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpmulld	.LC19(%rip), %ymm4, %ymm4
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm7, %ymm0
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC21(%rip), %ymm1, %ymm1
	vpaddd	%ymm3, %ymm6, %ymm6
	vpmulld	.LC20(%rip), %ymm7, %ymm3
	vpmovzxbw	%xmm5, %xmm7
	vpaddd	%ymm6, %ymm4, %ymm4
	vpaddd	%ymm4, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm1, %ymm1
	vpsrldq	$8, %xmm5, %xmm3
	vpmovzxwd	%xmm7, %xmm5
	vpmovzxbw	%xmm3, %xmm3
	vpsrldq	$8, %xmm7, %xmm7
	vpmovzxwd	%xmm7, %xmm7
	vpmovzxwd	%xmm3, %xmm6
	vpsrldq	$8, %xmm3, %xmm3
	vpaddd	%xmm7, %xmm5, %xmm4
	vpmovzxwd	%xmm3, %xmm3
	vpmulld	.LC23(%rip), %xmm7, %xmm7
	vpaddd	%xmm6, %xmm4, %xmm4
	vpmulld	.LC24(%rip), %xmm6, %xmm6
	vpaddd	%xmm3, %xmm4, %xmm4
	vpmulld	.LC25(%rip), %xmm3, %xmm3
	vpaddd	%xmm0, %xmm4, %xmm4
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm4, %xmm4
	vpmulld	.LC22(%rip), %xmm5, %xmm0
	vpmovzxbw	%xmm2, %xmm5
	vpsrlq	$32, %xmm2, %xmm2
	vpmovzxbw	%xmm2, %xmm2
	vpaddd	%xmm7, %xmm0, %xmm0
	vpaddd	%xmm6, %xmm0, %xmm0
	vpmovzxwd	%xmm2, %xmm6
	vpsrlq	$32, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm2
	vpaddd	%xmm3, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpmovzxwd	%xmm5, %xmm0
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm3
	vpaddd	%xmm6, %xmm3, %xmm3
	vpaddd	%xmm2, %xmm3, %xmm3
	vpaddd	%xmm4, %xmm3, %xmm3
	vpsrldq	$8, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm3, %xmm3
	vmovq	.LC26(%rip), %xmm4
	vpmulld	%xmm4, %xmm0, %xmm0
	vmovq	.LC27(%rip), %xmm4
	vpmulld	%xmm4, %xmm5, %xmm5
	vmovq	.LC29(%rip), %xmm4
	vpaddd	%xmm5, %xmm0, %xmm0
	vmovq	.LC28(%rip), %xmm5
	vpmulld	%xmm4, %xmm2, %xmm2
	vpmulld	%xmm5, %xmm6, %xmm6
	vpaddd	%xmm6, %xmm0, %xmm0
	vpaddd	%xmm2, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm3, %xmm1
	vpaddd	%xmm1, %xmm3, %xmm3
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vinsertps	$16, %xmm0, %xmm3, %xmm3
	vmovq	%xmm3, 320(%rax)
	jmp	.L38
	.p2align 4
	.p2align 3
.L83:
	cmpl	$1, %ebx
	je	.L45
	vmovdqa	480(%rsp), %ymm3
	vmovdqa	384(%rsp), %ymm7
	vmovdqa	%xmm15, 87584(%rsp)
	movq	%rdi, 87600(%rsp)
	movl	$0, 164(%rax)
	vmovdqa	448(%rsp), %ymm4
	vmovdqa	416(%rsp), %ymm5
	vmovdqa	%ymm3, 87552(%rsp)
	vmovdqu	87576(%rsp), %ymm0
	vmovdqa	%ymm7, 87520(%rsp)
	vmovdqu	%ymm7, 64(%rax)
	vmovq	%r12, %xmm7
	vmovdqu	%ymm3, 96(%rax)
	vinsertps	$16, %xmm1, %xmm7, %xmm1
	vmovdqa	%ymm4, 87456(%rsp)
	vmovdqu	%ymm4, (%rax)
	vmovdqa	%ymm5, 87488(%rsp)
	vmovdqu	%ymm5, 32(%rax)
	vmovq	%xmm1, 152(%rax)
	vmovdqu	%ymm0, 120(%rax)
	jmp	.L38
	.p2align 4
	.p2align 3
.L45:
	vmovdqu	96(%rax), %ymm0
	vmovdqa	704(%rsp), %ymm4
	vmovdqu	(%rax), %ymm3
	vmovdqu	32(%rax), %ymm2
	vmovdqu	64(%rax), %ymm1
	vmovdqa	%ymm0, 87552(%rsp)
	vmovdqu	120(%rax), %ymm0
	vmovdqa	%ymm3, 87456(%rsp)
	vmovdqa	%ymm2, 87488(%rsp)
	vmovdqa	%ymm1, 87520(%rsp)
	vmovdqu	%ymm0, 87576(%rsp)
	vpxor	.LC30(%rip), %ymm4, %ymm0
	vmovdqa	672(%rsp), %ymm4
	vmovdqa	87584(%rsp), %xmm6
	vmovq	87600(%rsp), %xmm5
	vmovdqu	%ymm0, 168(%rax)
	vpxor	.LC30(%rip), %ymm4, %ymm0
	vmovdqa	640(%rsp), %ymm4
	vmovdqu	%ymm0, 200(%rax)
	vpxor	.LC30(%rip), %ymm4, %ymm0
	vmovdqa	736(%rsp), %ymm4
	vmovdqu	%ymm0, 232(%rax)
	vpxor	.LC30(%rip), %ymm4, %ymm0
	vmovq	%r8, %xmm4
	vmovdqu	%ymm0, 264(%rax)
	vpxor	.LC31(%rip), %xmm6, %xmm0
	vmovdqu	%xmm0, 296(%rax)
	vpxor	%xmm4, %xmm5, %xmm0
	vpmovzxbw	%xmm3, %ymm4
	vmovq	%xmm0, 312(%rax)
	vextracti128	$0x1, %ymm3, %xmm0
	vpmovzxwd	%xmm4, %ymm3
	vpmulld	.LC6(%rip), %ymm3, %ymm8
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm4, %ymm4
	vpmovzxwd	%xmm0, %ymm9
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm4, %ymm3, %ymm7
	vpmulld	.LC7(%rip), %ymm4, %ymm4
	vpmovzxwd	%xmm0, %ymm0
	vpmulld	.LC8(%rip), %ymm9, %ymm3
	vpaddd	%ymm7, %ymm9, %ymm7
	vpaddd	%ymm7, %ymm0, %ymm7
	vpmulld	.LC9(%rip), %ymm0, %ymm0
	vpaddd	%ymm4, %ymm8, %ymm4
	vpaddd	%ymm4, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm0, %ymm0
	vpmovzxbw	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm3, %ymm9
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm2, %ymm2
	vpaddd	%ymm9, %ymm7, %ymm4
	vpmovzxwd	%xmm3, %ymm3
	vpmulld	.LC10(%rip), %ymm9, %ymm9
	vpmovzxwd	%xmm2, %ymm8
	vpaddd	%ymm4, %ymm3, %ymm4
	vpmulld	.LC11(%rip), %ymm3, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	movl	$0, 332(%rax)
	vpaddd	%ymm4, %ymm8, %ymm4
	vpmulld	.LC12(%rip), %ymm8, %ymm8
	vpmovzxwd	%xmm2, %ymm2
	vpaddd	%ymm4, %ymm2, %ymm4
	vpmulld	.LC13(%rip), %ymm2, %ymm2
	vpaddd	%ymm0, %ymm9, %ymm9
	vpmovzxbw	%xmm1, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm9, %ymm3, %ymm3
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm3, %ymm8, %ymm8
	vpmovzxwd	%xmm0, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm3, %ymm4, %ymm7
	vpmovzxwd	%xmm0, %ymm0
	vpmulld	.LC14(%rip), %ymm3, %ymm3
	vpaddd	%ymm8, %ymm2, %ymm2
	vpaddd	%ymm7, %ymm0, %ymm7
	vpmulld	.LC15(%rip), %ymm0, %ymm0
	vpmovzxwd	%xmm1, %ymm8
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm7, %ymm8, %ymm7
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm7, %ymm1, %ymm7
	vpmulld	.LC17(%rip), %ymm1, %ymm1
	vpaddd	%ymm2, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm0, %ymm2
	vpmulld	.LC16(%rip), %ymm8, %ymm0
	vpaddd	%ymm2, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm1, %ymm1
	vmovdqa	87552(%rsp), %ymm0
	vpmovzxbw	%xmm0, %ymm2
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm7, %ymm3, %ymm7
	vpmulld	.LC18(%rip), %ymm3, %ymm3
	vpmovzxwd	%xmm2, %ymm2
	vpmovzxwd	%xmm0, %ymm4
	vpaddd	%ymm7, %ymm2, %ymm7
	vextracti128	$0x1, %ymm0, %xmm0
	vpmulld	.LC19(%rip), %ymm2, %ymm2
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm7, %ymm4, %ymm7
	vpaddd	%ymm7, %ymm0, %ymm7
	vpmulld	.LC21(%rip), %ymm0, %ymm0
	vpaddd	%ymm1, %ymm3, %ymm3
	vpmulld	.LC20(%rip), %ymm4, %ymm1
	vpaddd	%ymm3, %ymm2, %ymm2
	vpaddd	%ymm2, %ymm1, %ymm1
	vpmovzxbw	%xmm6, %xmm2
	vpaddd	%ymm1, %ymm0, %ymm3
	vpmovzxwd	%xmm2, %xmm1
	vpsrldq	$8, %xmm6, %xmm0
	vpsrldq	$8, %xmm2, %xmm2
	vpmovzxbw	%xmm0, %xmm0
	vpmovzxwd	%xmm2, %xmm2
	vpmovzxwd	%xmm0, %xmm6
	vpaddd	%xmm2, %xmm1, %xmm4
	vpmulld	.LC23(%rip), %xmm2, %xmm2
	vpsrldq	$8, %xmm0, %xmm0
	vpmulld	.LC22(%rip), %xmm1, %xmm1
	vpmovzxwd	%xmm0, %xmm0
	vpaddd	%xmm6, %xmm4, %xmm4
	vpmulld	.LC24(%rip), %xmm6, %xmm6
	vpaddd	%xmm0, %xmm4, %xmm4
	vpmulld	.LC25(%rip), %xmm0, %xmm0
	vpaddd	%xmm7, %xmm4, %xmm4
	vextracti128	$0x1, %ymm7, %xmm7
	vpaddd	%xmm7, %xmm4, %xmm4
	vpaddd	%xmm2, %xmm1, %xmm1
	vpsrlq	$32, %xmm5, %xmm2
	vpmovzxbw	%xmm2, %xmm2
	vpaddd	%xmm6, %xmm1, %xmm1
	vpmovzxwd	%xmm2, %xmm6
	vpsrlq	$32, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm2
	vpaddd	%xmm0, %xmm1, %xmm1
	vpaddd	%xmm3, %xmm1, %xmm1
	vextracti128	$0x1, %ymm3, %xmm3
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmovzxbw	%xmm5, %xmm3
	vpmovzxwd	%xmm3, %xmm0
	vpsrlq	$32, %xmm3, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm3
	vpaddd	%xmm6, %xmm3, %xmm3
	vpaddd	%xmm2, %xmm3, %xmm3
	vpaddd	%xmm4, %xmm3, %xmm3
	vpsrldq	$8, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm3, %xmm3
	vmovq	.LC26(%rip), %xmm4
	vpmulld	%xmm4, %xmm0, %xmm0
	vmovq	.LC27(%rip), %xmm4
	vpmulld	%xmm4, %xmm5, %xmm5
	vmovq	.LC28(%rip), %xmm4
	vpaddd	%xmm5, %xmm0, %xmm0
	vpmulld	%xmm4, %xmm6, %xmm6
	vmovq	.LC29(%rip), %xmm4
	vpaddd	%xmm6, %xmm0, %xmm0
	vpmulld	%xmm4, %xmm2, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm3, %xmm1
	vpaddd	%xmm1, %xmm3, %xmm3
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vinsertps	$16, %xmm0, %xmm3, %xmm3
	vmovq	%xmm3, 320(%rax)
	incq	87288(%rsp)
	jmp	.L38
	.p2align 4
	.p2align 3
.L84:
	vpmulld	.LC14(%rip), %ymm12, %ymm12
	vmovdqa	320(%rsp), %ymm2
	vpmulld	.LC7(%rip), %ymm2, %ymm1
	vmovdqa	352(%rsp), %ymm2
	vpmulld	.LC6(%rip), %ymm2, %ymm0
	vmovdqa	288(%rsp), %ymm2
	vpmulld	.LC15(%rip), %ymm6, %ymm6
	vpmulld	.LC16(%rip), %ymm11, %ymm11
	vpmulld	.LC17(%rip), %ymm5, %ymm5
	vpmulld	.LC18(%rip), %ymm9, %ymm9
	vpmulld	.LC19(%rip), %ymm4, %ymm4
	vpmulld	.LC20(%rip), %ymm8, %ymm8
	vpmulld	.LC23(%rip), %xmm7, %xmm7
	vpmulld	.LC24(%rip), %xmm14, %xmm14
	vpmulld	.LC21(%rip), %ymm3, %ymm3
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC8(%rip), %ymm2, %ymm1
	vmovdqa	256(%rsp), %ymm2
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC9(%rip), %ymm2, %ymm0
	vmovdqa	448(%rsp), %ymm2
	vpmulld	.LC10(%rip), %ymm2, %ymm13
	vmovdqa	480(%rsp), %ymm2
	vpaddd	%ymm1, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm13, %ymm13
	vpmulld	.LC11(%rip), %ymm2, %ymm0
	vmovdqa	512(%rsp), %ymm2
	vpaddd	%ymm13, %ymm0, %ymm0
	vpmulld	.LC12(%rip), %ymm2, %ymm13
	vmovdqa	544(%rsp), %ymm2
	vpaddd	%ymm0, %ymm13, %ymm13
	vpmulld	.LC13(%rip), %ymm2, %ymm0
	vpaddd	%ymm13, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm12, %ymm12
	vpaddd	%ymm12, %ymm6, %ymm6
	vpaddd	%ymm6, %ymm11, %ymm11
	vpaddd	%ymm11, %ymm5, %ymm5
	vpaddd	%ymm5, %ymm9, %ymm9
	vmovdqa	384(%rsp), %xmm5
	vpaddd	%ymm9, %ymm4, %ymm4
	vpmulld	.LC25(%rip), %xmm5, %xmm2
	vpaddd	%ymm4, %ymm8, %ymm8
	vmovdqa	416(%rsp), %xmm4
	vpmulld	.LC22(%rip), %xmm4, %xmm0
	vmovq	.LC27(%rip), %xmm4
	vpaddd	%ymm8, %ymm3, %ymm3
	vpaddd	%xmm7, %xmm0, %xmm7
	vmovdqa	%xmm3, %xmm0
	vextracti128	$0x1, %ymm3, %xmm3
	vpaddd	%xmm14, %xmm7, %xmm14
	vmovq	.LC26(%rip), %xmm7
	vpaddd	%xmm3, %xmm0, %xmm0
	vmovq	%r11, %xmm3
	vpaddd	%xmm2, %xmm14, %xmm2
	vpaddd	%xmm0, %xmm2, %xmm2
	vpmulld	%xmm7, %xmm3, %xmm0
	vmovq	%rcx, %xmm3
	vmovq	%r9, %xmm7
	vpmulld	%xmm4, %xmm3, %xmm1
	vmovq	.LC28(%rip), %xmm3
	vmovq	.LC29(%rip), %xmm5
	vmovq	%rdx, %xmm4
	vpaddd	%xmm1, %xmm0, %xmm1
	vpmulld	%xmm3, %xmm7, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm0
	vpmulld	%xmm5, %xmm4, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpaddd	%xmm2, %xmm0, %xmm0
	vpsrldq	$8, %xmm2, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm2
	vpsrlq	$32, %xmm2, %xmm0
	vpaddd	%xmm0, %xmm2, %xmm0
	vmovd	%xmm0, %edx
	cmpl	%edx, 324(%rax)
	jne	.L52
	testb	%r12b, %r12b
	je	.L86
	incl	160(%rax)
	incl	328(%rax)
	addq	$336, %rax
	incq	%rsi
	cmpq	%r14, %rax
	jne	.L61
	.p2align 4
	.p2align 3
.L85:
	movq	176(%rsp), %r13
	leaq	10752(%rax), %r11
	leaq	87232(%rsp), %rax
	movq	%rbx, %r14
	addq	$32, %r13
	cmpq	%r13, %rax
	jne	.L49
	testq	%rbx, %rbx
	jne	.L63
	imulq	$336, 32(%rsp), %rax
	imulq	$10752, 40(%rsp), %rbx
	addq	%rbx, %rax
	cmpl	$-559063315, 1124(%rsp,%rax)
	je	.L63
	movq	(%rsp), %rax
	incq	(%rax)
.L63:
	decl	28(%rsp)
	je	.L87
	vzeroupper
	jmp	.L64
	.p2align 4
	.p2align 3
.L55:
	vmovdqu	96(%rax), %ymm1
	vmovdqu	(%rax), %ymm2
	vmovq	768(%rsp), %xmm4
	vmovdqu	32(%rax), %ymm7
	vmovdqu	64(%rax), %ymm0
	vpxor	672(%rsp), %ymm10, %ymm11
	vpxor	736(%rsp), %ymm10, %ymm12
	vpxor	704(%rsp), %ymm10, %ymm13
	vpxor	640(%rsp), %ymm10, %ymm6
	vmovdqa	%ymm1, 87552(%rsp)
	vmovdqu	120(%rax), %ymm1
	vmovdqa	%ymm2, 87456(%rsp)
	vmovdqa	%ymm7, 87488(%rsp)
	vmovdqa	%ymm0, 87520(%rsp)
	vmovdqu	%ymm11, 168(%rax)
	vmovdqu	%ymm12, 200(%rax)
	vmovdqu	%ymm13, 232(%rax)
	vmovdqu	%ymm6, 264(%rax)
	vmovdqu	%ymm1, 87576(%rsp)
	vmovq	87600(%rsp), %xmm14
	vpmovzxbw	%xmm2, %ymm1
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm1, %ymm8
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm2, %ymm2
	vmovdqa	87584(%rsp), %xmm9
	vpmovzxwd	%xmm1, %ymm1
	vpxor	96(%rsp), %xmm9, %xmm5
	vpaddd	%ymm1, %ymm8, %ymm3
	vpmulld	.LC6(%rip), %ymm8, %ymm8
	vpmulld	.LC7(%rip), %ymm1, %ymm1
	vpxor	%xmm4, %xmm14, %xmm15
	vpmovzxwd	%xmm2, %ymm4
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm2, %ymm2
	vpaddd	%ymm3, %ymm4, %ymm3
	vpmulld	.LC8(%rip), %ymm4, %ymm4
	vmovq	%xmm15, 312(%rax)
	vpaddd	%ymm3, %ymm2, %ymm3
	vpmulld	.LC9(%rip), %ymm2, %ymm2
	vmovdqu	%xmm5, 296(%rax)
	vmovq	%xmm15, %r8
	vpaddd	%ymm1, %ymm8, %ymm1
	vpaddd	%ymm1, %ymm4, %ymm4
	vextracti128	$0x1, %ymm7, %xmm1
	vpaddd	%ymm4, %ymm2, %ymm2
	vpmovzxbw	%xmm7, %ymm4
	vpmovzxbw	%xmm1, %ymm1
	vpmovzxwd	%xmm4, %ymm8
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxwd	%xmm1, %ymm7
	vpmovzxwd	%xmm4, %ymm4
	vpaddd	%ymm8, %ymm3, %ymm3
	vpmulld	.LC10(%rip), %ymm8, %ymm8
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm3, %ymm4, %ymm3
	vpmulld	.LC11(%rip), %ymm4, %ymm4
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm3, %ymm7, %ymm3
	vpmulld	.LC12(%rip), %ymm7, %ymm7
	vpaddd	%ymm3, %ymm1, %ymm3
	vpmulld	.LC13(%rip), %ymm1, %ymm1
	vpaddd	%ymm2, %ymm8, %ymm8
	vpmovzxbw	%xmm0, %ymm2
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm8, %ymm4, %ymm4
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm4, %ymm7, %ymm7
	vpmovzxwd	%xmm0, %ymm4
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm7, %ymm1, %ymm1
	vpmovzxwd	%xmm2, %ymm7
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm3, %ymm7, %ymm3
	vpmulld	.LC14(%rip), %ymm7, %ymm7
	vpmovzxwd	%xmm2, %ymm2
	movl	$0, 332(%rax)
	vpaddd	%ymm3, %ymm2, %ymm3
	vpmulld	.LC15(%rip), %ymm2, %ymm2
	vmovdqa	%ymm11, 928(%rsp)
	vmovdqa	%ymm12, 896(%rsp)
	vpaddd	%ymm3, %ymm4, %ymm3
	vmovdqa	%ymm13, 864(%rsp)
	vmovdqa	%ymm6, 832(%rsp)
	vpaddd	%ymm3, %ymm0, %ymm3
	vmovdqa	%xmm5, 800(%rsp)
	vpmulld	.LC16(%rip), %ymm4, %ymm4
	vpmulld	.LC17(%rip), %ymm0, %ymm0
	vpaddd	%ymm1, %ymm7, %ymm7
	vmovdqa	87552(%rsp), %ymm1
	vpaddd	%ymm7, %ymm2, %ymm2
	vpaddd	%ymm2, %ymm4, %ymm4
	vpaddd	%ymm4, %ymm0, %ymm2
	vpmovzxbw	%xmm1, %ymm4
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm4, %ymm8
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm3, %ymm8, %ymm0
	vpmovzxwd	%xmm4, %ymm4
	vpmulld	.LC18(%rip), %ymm8, %ymm8
	vpmovzxwd	%xmm1, %ymm7
	vpaddd	%ymm0, %ymm4, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpmulld	.LC19(%rip), %ymm4, %ymm4
	vpmovzxbw	%xmm9, %xmm3
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm7, %ymm0
	vpmulld	.LC20(%rip), %ymm7, %ymm7
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC21(%rip), %ymm1, %ymm1
	vpaddd	%ymm2, %ymm8, %ymm8
	vpsrldq	$8, %xmm9, %xmm2
	vpmovzxbw	%xmm2, %xmm2
	vpaddd	%ymm8, %ymm4, %ymm4
	vpmovzxwd	%xmm3, %xmm8
	vpsrldq	$8, %xmm3, %xmm3
	vpmovzxwd	%xmm3, %xmm3
	vpaddd	%ymm4, %ymm7, %ymm7
	vpmovzxwd	%xmm2, %xmm4
	vpsrldq	$8, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm2
	vpaddd	%ymm7, %ymm1, %ymm1
	vpaddd	%xmm3, %xmm8, %xmm7
	vpmulld	.LC22(%rip), %xmm8, %xmm8
	vpmulld	.LC23(%rip), %xmm3, %xmm3
	vpaddd	%xmm4, %xmm7, %xmm7
	vpmulld	.LC24(%rip), %xmm4, %xmm4
	vpaddd	%xmm2, %xmm7, %xmm7
	vpmulld	.LC25(%rip), %xmm2, %xmm2
	vpaddd	%xmm0, %xmm7, %xmm9
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm9, %xmm0
	vpaddd	%xmm3, %xmm8, %xmm3
	vpaddd	%xmm4, %xmm3, %xmm4
	vpaddd	%xmm2, %xmm4, %xmm2
	vpmovzxbw	%xmm14, %xmm4
	vpsrlq	$32, %xmm14, %xmm14
	vpmovzxbw	%xmm14, %xmm14
	vpaddd	%xmm1, %xmm2, %xmm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm14, %xmm8
	vpsrlq	$32, %xmm14, %xmm14
	vpaddd	%xmm1, %xmm3, %xmm3
	vpmovzxwd	%xmm4, %xmm1
	vpsrlq	$32, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpaddd	%xmm4, %xmm1, %xmm7
	vpmovzxwd	%xmm14, %xmm14
	vpaddd	%xmm8, %xmm7, %xmm7
	vpaddd	%xmm14, %xmm7, %xmm7
	vpaddd	%xmm0, %xmm7, %xmm2
	vmovq	.LC26(%rip), %xmm7
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm2, %xmm2
	vpmulld	%xmm7, %xmm1, %xmm0
	vmovq	.LC27(%rip), %xmm7
	vpmulld	%xmm7, %xmm4, %xmm4
	vmovq	.LC28(%rip), %xmm7
	vpaddd	%xmm4, %xmm0, %xmm0
	vmovq	.LC29(%rip), %xmm4
	vpmulld	%xmm7, %xmm8, %xmm8
	vpmulld	%xmm4, %xmm14, %xmm14
	vpaddd	%xmm8, %xmm0, %xmm0
	vpaddd	%xmm14, %xmm0, %xmm0
	vpaddd	%xmm3, %xmm0, %xmm0
	vpsrldq	$8, %xmm3, %xmm3
	vpaddd	%xmm3, %xmm0, %xmm3
	vpsrlq	$32, %xmm2, %xmm0
	vpaddd	%xmm0, %xmm2, %xmm2
	vpsrlq	$32, %xmm3, %xmm0
	vpaddd	%xmm0, %xmm3, %xmm3
	vinsertps	$16, %xmm3, %xmm2, %xmm2
	vmovq	%xmm2, 320(%rax)
.L57:
	vmovdqa	672(%rsp), %ymm3
	vpxor	%xmm2, %xmm2, %xmm2
	vpxor	928(%rsp), %ymm3, %ymm0
	vmovdqa	576(%rsp), %ymm7
	vpcmpeqb	%ymm10, %ymm0, %ymm0
	vpcmpeqb	%ymm2, %ymm0, %ymm0
	vpand	%ymm7, %ymm0, %ymm0
	vpmovzxbw	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm1, %ymm3, %ymm3
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm3, %ymm1, %ymm3
	vextracti128	$0x1, %ymm0, %xmm1
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm3, %ymm1, %ymm1
	vmovdqa	896(%rsp), %ymm3
	vpxor	736(%rsp), %ymm3, %ymm0
	vpcmpeqb	%ymm10, %ymm0, %ymm0
	vpcmpeqb	%ymm2, %ymm0, %ymm0
	vpand	%ymm7, %ymm0, %ymm0
	vpmovzxbw	%xmm0, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm3, %ymm4
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm4, %ymm4
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm4, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm1, %ymm3
	vextracti128	$0x1, %ymm0, %xmm1
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm3, %ymm1, %ymm1
	vmovdqa	704(%rsp), %ymm3
	vpxor	864(%rsp), %ymm3, %ymm0
	vpcmpeqb	%ymm10, %ymm0, %ymm0
	vpcmpeqb	%ymm2, %ymm0, %ymm0
	vpand	%ymm7, %ymm0, %ymm0
	vpmovzxbw	%xmm0, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm3, %ymm4
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm4, %ymm4
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm4, %ymm3, %ymm3
	vmovdqa	96(%rsp), %xmm4
	vpaddd	%ymm3, %ymm1, %ymm3
	vextracti128	$0x1, %ymm0, %xmm1
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm3, %ymm1, %ymm1
	vmovdqa	832(%rsp), %ymm3
	vpxor	640(%rsp), %ymm3, %ymm0
	vpcmpeqb	%ymm10, %ymm0, %ymm0
	vpcmpeqb	%ymm2, %ymm0, %ymm0
	vpand	%ymm7, %ymm0, %ymm0
	vmovq	%rdi, %xmm7
	vpmovzxbw	%xmm0, %ymm2
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm3, %ymm3
	vpmovzxwd	%xmm2, %ymm2
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm3, %ymm2, %ymm2
	vmovdqa	608(%rsp), %xmm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm2, %ymm1, %ymm1
	vpxor	800(%rsp), %xmm3, %xmm2
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpxor	%xmm1, %xmm1, %xmm1
	vpcmpeqb	%xmm4, %xmm2, %xmm2
	vpcmpeqb	%xmm1, %xmm2, %xmm1
	vpand	80(%rsp), %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm2
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm2, %xmm3
	vpsrldq	$8, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm2
	vpaddd	%xmm2, %xmm3, %xmm2
	vpmovzxwd	%xmm1, %xmm3
	vpsrldq	$8, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm1
	vpaddd	%xmm3, %xmm2, %xmm3
	vpaddd	%xmm1, %xmm3, %xmm1
	vmovq	%r8, %xmm3
	vpaddd	%xmm0, %xmm1, %xmm2
	vextracti128	$0x1, %ymm0, %xmm0
	vpxor	%xmm1, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm2, %xmm2
	vpxor	%xmm3, %xmm7, %xmm0
	vmovq	768(%rsp), %xmm7
	vmovq	.LC5(%rip), %xmm3
	vpcmpeqb	%xmm7, %xmm0, %xmm0
	vpcmpeqb	%xmm1, %xmm0, %xmm0
	vpand	%xmm3, %xmm0, %xmm0
	vpmovzxbw	%xmm0, %xmm3
	vpsrlq	$32, %xmm0, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpmovzxwd	%xmm3, %xmm1
	vpsrlq	$32, %xmm3, %xmm3
	vpmovzxwd	%xmm3, %xmm3
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmovzxwd	%xmm0, %xmm3
	vpsrlq	$32, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm0
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm0
	vpaddd	%xmm2, %xmm0, %xmm0
	vpsrldq	$8, %xmm2, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm2
	vpsrlq	$32, %xmm2, %xmm0
	vpaddd	%xmm0, %xmm2, %xmm2
	vmovd	%xmm2, %edx
	testl	%edx, %edx
	je	.L88
.L60:
	incq	%rbx
	jmp	.L59
	.p2align 4
	.p2align 3
.L86:
	cmpl	$1, %r13d
	je	.L58
	vmovdqa	128(%rsp), %ymm4
	vmovdqa	160(%rsp), %xmm5
	movq	%r10, 87600(%rsp)
	vmovdqa	%ymm15, 87520(%rsp)
	vmovdqu	%ymm15, 64(%rax)
	movl	$0, 164(%rax)
	vmovdqa	%ymm15, 704(%rsp)
	vmovdqa	192(%rsp), %ymm7
	vmovdqa	224(%rsp), %ymm3
	vmovdqa	%xmm5, 87584(%rsp)
	vmovdqa	%ymm4, 87552(%rsp)
	vmovdqu	87576(%rsp), %ymm1
	vmovq	184(%rsp), %xmm5
	vmovdqu	%ymm4, 96(%rax)
	vmovdqa	%ymm7, 87456(%rsp)
	vmovdqa	%ymm3, 87488(%rsp)
	vmovdqu	%ymm7, (%rax)
	vmovdqu	%ymm3, 32(%rax)
	vmovdqa	%ymm7, 672(%rsp)
	vmovdqa	%ymm3, 736(%rsp)
	vmovdqu	%ymm1, 120(%rax)
	vmovdqu	96(%rax), %ymm3
	vmovdqa	128(%rax), %xmm7
	vinsertps	$16, %xmm0, %xmm5, %xmm0
	movq	144(%rax), %rdi
	vmovq	%xmm0, 152(%rax)
	vmovdqa	%ymm3, 640(%rsp)
	vmovdqa	%xmm7, 608(%rsp)
	jmp	.L57
	.p2align 4
	.p2align 3
.L58:
	vmovdqu	96(%rax), %ymm0
	vmovq	768(%rsp), %xmm7
	vmovdqu	(%rax), %ymm5
	vmovdqu	32(%rax), %ymm3
	vmovdqu	64(%rax), %ymm1
	vmovdqa	%ymm0, 87552(%rsp)
	vmovdqu	120(%rax), %ymm0
	vmovdqa	%ymm5, 87456(%rsp)
	vmovdqa	%ymm3, 87488(%rsp)
	vmovdqa	%ymm1, 87520(%rsp)
	vmovdqu	%ymm0, 87576(%rsp)
	vpxor	672(%rsp), %ymm10, %ymm0
	vmovdqa	87584(%rsp), %xmm4
	vmovq	87600(%rsp), %xmm2
	vmovdqu	%ymm0, 168(%rax)
	vpxor	736(%rsp), %ymm10, %ymm0
	vmovdqu	%ymm0, 200(%rax)
	vpxor	704(%rsp), %ymm10, %ymm0
	vmovdqu	%ymm0, 232(%rax)
	vpxor	640(%rsp), %ymm10, %ymm0
	vmovdqu	%ymm0, 264(%rax)
	vpxor	.LC31(%rip), %xmm4, %xmm0
	vmovdqu	%xmm0, 296(%rax)
	vpxor	%xmm7, %xmm2, %xmm0
	vmovq	%xmm0, 312(%rax)
	vpmovzxbw	%xmm5, %ymm0
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm0, %ymm8
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxbw	%xmm5, %ymm5
	vpmovzxwd	%xmm0, %ymm0
	vpmulld	.LC7(%rip), %ymm0, %ymm6
	vpmovzxwd	%xmm5, %ymm9
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%ymm0, %ymm8, %ymm7
	vpmulld	.LC6(%rip), %ymm8, %ymm8
	vpmovzxwd	%xmm5, %ymm5
	vpmulld	.LC8(%rip), %ymm9, %ymm0
	vpaddd	%ymm7, %ymm9, %ymm7
	vpaddd	%ymm7, %ymm5, %ymm7
	vpmulld	.LC9(%rip), %ymm5, %ymm5
	vpaddd	%ymm8, %ymm6, %ymm6
	vpaddd	%ymm6, %ymm0, %ymm0
	vpmovzxbw	%xmm3, %ymm6
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxwd	%xmm6, %ymm9
	vextracti128	$0x1, %ymm6, %xmm6
	vpaddd	%ymm0, %ymm5, %ymm5
	vpmovzxbw	%xmm3, %ymm3
	vpaddd	%ymm7, %ymm9, %ymm0
	vpmovzxwd	%xmm6, %ymm6
	vpmulld	.LC10(%rip), %ymm9, %ymm9
	vpmovzxwd	%xmm3, %ymm8
	vpaddd	%ymm0, %ymm6, %ymm0
	vextracti128	$0x1, %ymm3, %xmm3
	vpmulld	.LC11(%rip), %ymm6, %ymm6
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm0, %ymm8, %ymm0
	vpmulld	.LC12(%rip), %ymm8, %ymm8
	vpaddd	%ymm0, %ymm3, %ymm0
	vpmulld	.LC13(%rip), %ymm3, %ymm3
	vpaddd	%ymm5, %ymm9, %ymm9
	vpmovzxbw	%xmm1, %ymm5
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm9, %ymm6, %ymm6
	vpmovzxbw	%xmm1, %ymm1
	vpaddd	%ymm6, %ymm8, %ymm8
	vpmovzxwd	%xmm1, %ymm7
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm8, %ymm3, %ymm3
	vpmovzxwd	%xmm5, %ymm8
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm8, %ymm0, %ymm6
	vpmovzxwd	%xmm5, %ymm5
	vpmulld	.LC14(%rip), %ymm8, %ymm8
	vmovdqa	87552(%rsp), %ymm0
	vpaddd	%ymm5, %ymm6, %ymm6
	vpmulld	.LC15(%rip), %ymm5, %ymm5
	movl	$0, 332(%rax)
	vpaddd	%ymm6, %ymm7, %ymm6
	vpmulld	.LC16(%rip), %ymm7, %ymm7
	vpaddd	%ymm6, %ymm1, %ymm6
	vpmulld	.LC17(%rip), %ymm1, %ymm1
	vpaddd	%ymm3, %ymm8, %ymm8
	vpmovzxbw	%xmm0, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm8, %ymm5, %ymm5
	vpmovzxwd	%xmm3, %ymm8
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm5, %ymm7, %ymm7
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm6, %ymm8, %ymm5
	vpmulld	.LC18(%rip), %ymm8, %ymm8
	vpaddd	%ymm7, %ymm1, %ymm1
	vpaddd	%ymm5, %ymm3, %ymm5
	vpmovzxwd	%xmm0, %ymm7
	vpmulld	.LC19(%rip), %ymm3, %ymm3
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm5, %ymm7, %ymm5
	vpmulld	.LC20(%rip), %ymm7, %ymm7
	vpmovzxbw	%xmm4, %xmm6
	vpmovzxwd	%xmm0, %ymm0
	vpaddd	%ymm5, %ymm0, %ymm5
	vpmulld	.LC21(%rip), %ymm0, %ymm0
	vpaddd	%ymm1, %ymm8, %ymm8
	vpmovzxwd	%xmm6, %xmm1
	vpsrldq	$8, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vpaddd	%ymm8, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm7, %ymm7
	vpsrldq	$8, %xmm4, %xmm3
	vpmovzxbw	%xmm3, %xmm3
	vpaddd	%xmm6, %xmm1, %xmm4
	vpmulld	.LC23(%rip), %xmm6, %xmm6
	vpaddd	%ymm7, %ymm0, %ymm0
	vpmulld	.LC22(%rip), %xmm1, %xmm1
	vpmovzxwd	%xmm3, %xmm7
	vpsrldq	$8, %xmm3, %xmm3
	vpaddd	%xmm7, %xmm4, %xmm4
	vpmovzxwd	%xmm3, %xmm3
	vpmulld	.LC24(%rip), %xmm7, %xmm7
	vpaddd	%xmm3, %xmm4, %xmm4
	vpmulld	.LC25(%rip), %xmm3, %xmm3
	vpaddd	%xmm5, %xmm4, %xmm4
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%xmm5, %xmm4, %xmm4
	vpmovzxbw	%xmm2, %xmm5
	vpsrlq	$32, %xmm2, %xmm2
	vpmovzxbw	%xmm2, %xmm2
	vpaddd	%xmm6, %xmm1, %xmm1
	vpmovzxwd	%xmm2, %xmm6
	vpsrlq	$32, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm2
	vpaddd	%xmm7, %xmm1, %xmm1
	vpaddd	%xmm3, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vpmovzxwd	%xmm5, %xmm0
	vpsrlq	$32, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm3
	vpaddd	%xmm6, %xmm3, %xmm3
	vpaddd	%xmm2, %xmm3, %xmm3
	vpaddd	%xmm4, %xmm3, %xmm3
	vpsrldq	$8, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm3, %xmm3
	vmovq	.LC26(%rip), %xmm4
	vpmulld	%xmm4, %xmm0, %xmm0
	vmovq	.LC27(%rip), %xmm4
	vpmulld	%xmm4, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm0, %xmm0
	vmovq	.LC28(%rip), %xmm5
	vpmulld	%xmm5, %xmm6, %xmm6
	vmovq	.LC29(%rip), %xmm5
	vpaddd	%xmm6, %xmm0, %xmm0
	vpmulld	%xmm5, %xmm2, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm3, %xmm1
	vpaddd	%xmm1, %xmm3, %xmm3
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vinsertps	$16, %xmm0, %xmm3, %xmm3
	vmovq	%xmm3, 320(%rax)
	incq	87288(%rsp)
	vmovdqu	(%rax), %ymm3
	vmovdqa	%ymm3, 672(%rsp)
	vmovdqu	168(%rax), %ymm3
	vmovdqa	%ymm3, 928(%rsp)
	vmovdqu	32(%rax), %ymm3
	vmovdqa	%ymm3, 736(%rsp)
	vmovdqu	200(%rax), %ymm3
	vmovdqa	%ymm3, 896(%rsp)
	vmovdqu	64(%rax), %ymm3
	vmovdqa	%ymm3, 704(%rsp)
	vmovdqu	232(%rax), %ymm3
	vmovdqa	%ymm3, 864(%rsp)
	vmovdqu	96(%rax), %ymm3
	vmovdqu	296(%rax), %xmm5
	movq	144(%rax), %rdi
	movq	312(%rax), %r8
	vmovdqa	%ymm3, 640(%rsp)
	vmovdqu	264(%rax), %ymm3
	vmovdqa	%xmm5, 800(%rsp)
	vmovdqa	%ymm3, 832(%rsp)
	vmovdqa	128(%rax), %xmm3
	vmovdqa	%xmm3, 608(%rsp)
	jmp	.L57
	.p2align 4
	.p2align 3
.L88:
	vmovdqa	672(%rsp), %ymm3
	vpmovzxbw	%xmm3, %ymm1
	vextracti128	$0x1, %ymm3, %xmm0
	vpmovzxwd	%xmm1, %ymm7
	vpmovzxbw	%xmm0, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm1, %ymm3
	vpmovzxwd	%xmm0, %ymm5
	vextracti128	$0x1, %ymm0, %xmm0
	vmovdqa	%ymm7, 672(%rsp)
	vpmovzxwd	%xmm0, %ymm6
	vpaddd	%ymm7, %ymm3, %ymm0
	vmovdqa	736(%rsp), %ymm7
	vmovdqa	%ymm3, 544(%rsp)
	vpaddd	%ymm5, %ymm0, %ymm0
	vmovdqa	%ymm6, 480(%rsp)
	vmovdqa	%ymm5, 512(%rsp)
	vpaddd	%ymm6, %ymm0, %ymm0
	vpmovzxbw	%xmm7, %ymm3
	vextracti128	$0x1, %ymm7, %xmm1
	vmovdqa	704(%rsp), %ymm7
	vpmovzxbw	%xmm1, %ymm1
	vpmovzxwd	%xmm3, %ymm6
	vpmovzxwd	%xmm1, %ymm11
	vextracti128	$0x1, %ymm1, %xmm1
	vextracti128	$0x1, %ymm3, %xmm3
	vpaddd	%ymm6, %ymm0, %ymm0
	vpmovzxwd	%xmm1, %ymm12
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm0, %ymm3, %ymm0
	vpaddd	%ymm0, %ymm11, %ymm0
	vpaddd	%ymm0, %ymm12, %ymm0
	vpmovzxbw	%xmm7, %ymm2
	vextracti128	$0x1, %ymm7, %xmm1
	vmovdqa	640(%rsp), %ymm7
	vpmovzxwd	%xmm2, %ymm13
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm1, %ymm1
	vpmovzxwd	%xmm2, %ymm14
	vpaddd	%ymm0, %ymm13, %ymm0
	vpmovzxwd	%xmm1, %ymm15
	vpaddd	%ymm14, %ymm0, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm1, %ymm5
	vpaddd	%ymm15, %ymm0, %ymm0
	vpaddd	%ymm5, %ymm0, %ymm0
	vmovdqa	%ymm5, 384(%rsp)
	vpmovzxbw	%xmm7, %ymm2
	vextracti128	$0x1, %ymm7, %xmm1
	vpmovzxwd	%xmm2, %ymm5
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm1, %ymm1
	vpmovzxwd	%xmm2, %ymm7
	vpaddd	%ymm5, %ymm0, %ymm0
	vpmovzxwd	%xmm1, %ymm2
	vmovdqa	%ymm5, 416(%rsp)
	vpaddd	%ymm7, %ymm0, %ymm0
	vmovdqa	%ymm7, 448(%rsp)
	vmovdqa	608(%rsp), %xmm7
	vmovdqa	%ymm2, 640(%rsp)
	vpaddd	%ymm2, %ymm0, %ymm0
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm1, %ymm0, %ymm0
	vmovdqa	%ymm1, 704(%rsp)
	vpmovzxbw	%xmm7, %xmm5
	vpsrldq	$8, %xmm7, %xmm2
	vpmovzxbw	%xmm2, %xmm2
	vpmovzxwd	%xmm5, %xmm9
	vpsrldq	$8, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpmovzxwd	%xmm2, %xmm8
	vpaddd	%xmm9, %xmm5, %xmm7
	vpsrldq	$8, %xmm2, %xmm2
	vpmovzxwd	%xmm2, %xmm2
	vpaddd	%xmm8, %xmm7, %xmm7
	vmovdqa	%xmm2, 736(%rsp)
	vpaddd	%xmm2, %xmm7, %xmm7
	vpaddd	%xmm0, %xmm7, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vmovq	%rdi, %xmm7
	vpaddd	%xmm0, %xmm1, %xmm1
	vpmovzxbw	%xmm7, %xmm7
	vmovq	%rdi, %xmm0
	vpmovzxwd	%xmm7, %xmm2
	vpsrlq	$32, %xmm0, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vpsrlq	$32, %xmm7, %xmm7
	vmovq	%xmm2, %rcx
	vpmovzxwd	%xmm0, %xmm2
	vpsrlq	$32, %xmm0, %xmm0
	vpmovzxwd	%xmm7, %xmm7
	vmovq	%xmm2, %rdx
	vpmovzxwd	%xmm0, %xmm2
	vmovq	%xmm2, %rdi
	vmovq	%rcx, %xmm2
	vpaddd	%xmm2, %xmm7, %xmm0
	vmovq	%rdx, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vmovq	%rdi, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm1
	vpsrlq	$32, %xmm1, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vmovd	%xmm1, %r9d
	cmpl	152(%rax), %r9d
	jne	.L60
	vpmulld	.LC10(%rip), %ymm6, %ymm6
	vmovdqa	672(%rsp), %ymm2
	vpmulld	.LC6(%rip), %ymm2, %ymm1
	vmovdqa	544(%rsp), %ymm2
	vpmulld	.LC7(%rip), %ymm2, %ymm0
	vmovdqa	512(%rsp), %ymm2
	vpmulld	.LC11(%rip), %ymm3, %ymm3
	vpmulld	.LC12(%rip), %ymm11, %ymm11
	vpmulld	.LC13(%rip), %ymm12, %ymm12
	vpmulld	.LC14(%rip), %ymm13, %ymm13
	vpmulld	.LC15(%rip), %ymm14, %ymm14
	vpmulld	.LC16(%rip), %ymm15, %ymm15
	vpmulld	.LC23(%rip), %xmm5, %xmm5
	vpmulld	.LC22(%rip), %xmm9, %xmm9
	vpmulld	.LC24(%rip), %xmm8, %xmm8
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC8(%rip), %ymm2, %ymm1
	vmovdqa	480(%rsp), %ymm2
	vpaddd	%xmm9, %xmm5, %xmm9
	vmovq	.LC27(%rip), %xmm5
	vpaddd	%xmm8, %xmm9, %xmm8
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC9(%rip), %ymm2, %ymm0
	vpaddd	%ymm1, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm6, %ymm6
	vpaddd	%ymm6, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm11, %ymm11
	vmovdqa	384(%rsp), %ymm3
	vpmulld	.LC17(%rip), %ymm3, %ymm0
	vmovdqa	416(%rsp), %ymm3
	vpaddd	%ymm11, %ymm12, %ymm12
	vpmulld	.LC18(%rip), %ymm3, %ymm1
	vpaddd	%ymm12, %ymm13, %ymm13
	vmovdqa	448(%rsp), %ymm3
	vpaddd	%ymm13, %ymm14, %ymm14
	vpaddd	%ymm14, %ymm15, %ymm15
	vpaddd	%ymm15, %ymm0, %ymm0
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC19(%rip), %ymm3, %ymm0
	vmovdqa	640(%rsp), %ymm3
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmulld	.LC20(%rip), %ymm3, %ymm1
	vmovdqa	704(%rsp), %ymm3
	vpaddd	%ymm0, %ymm1, %ymm1
	vpmulld	.LC21(%rip), %ymm3, %ymm0
	vmovdqa	736(%rsp), %xmm3
	vpmulld	.LC25(%rip), %xmm3, %xmm2
	vmovq	.LC26(%rip), %xmm3
	vpaddd	%ymm1, %ymm0, %ymm0
	vpaddd	%xmm2, %xmm8, %xmm2
	vpaddd	%xmm0, %xmm2, %xmm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm1, %xmm1
	vpmulld	%xmm5, %xmm7, %xmm0
	vmovq	%rcx, %xmm5
	vpmulld	%xmm3, %xmm5, %xmm2
	vmovq	.LC28(%rip), %xmm3
	vmovq	%rdx, %xmm5
	vpaddd	%xmm2, %xmm0, %xmm0
	vpmulld	%xmm3, %xmm5, %xmm2
	vmovq	.LC29(%rip), %xmm3
	vmovq	%rdi, %xmm5
	vpaddd	%xmm2, %xmm0, %xmm0
	vpmulld	%xmm3, %xmm5, %xmm2
	vpaddd	%xmm2, %xmm0, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %edx
	cmpl	156(%rax), %edx
	jne	.L60
	vpxor	928(%rsp), %ymm10, %ymm1
	vmovq	768(%rsp), %xmm3
	vmovq	%r8, %xmm5
	vpxor	896(%rsp), %ymm10, %ymm0
	vpxor	864(%rsp), %ymm10, %ymm7
	vpxor	832(%rsp), %ymm10, %ymm6
	vpxor	800(%rsp), %xmm4, %xmm4
	vpmovzxbw	%xmm1, %ymm2
	vextracti128	$0x1, %ymm1, %xmm1
	vpxor	%xmm3, %xmm5, %xmm15
	vpmovzxbw	%xmm1, %ymm1
	vpmovzxwd	%xmm2, %ymm12
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm2, %ymm5
	vpmovzxwd	%xmm1, %ymm11
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm1, %ymm2
	vpaddd	%ymm5, %ymm12, %ymm13
	vpmovzxbw	%xmm0, %ymm1
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%ymm11, %ymm13, %ymm13
	vpmovzxwd	%xmm1, %ymm9
	vpmovzxbw	%xmm0, %ymm0
	vpaddd	%ymm13, %ymm2, %ymm13
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm0, %ymm8
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm3
	vpmovzxwd	%xmm0, %ymm1
	vpaddd	%ymm9, %ymm13, %ymm0
	vpmovzxbw	%xmm7, %ymm13
	vpaddd	%ymm0, %ymm3, %ymm0
	vextracti128	$0x1, %ymm7, %xmm7
	vmovdqa	%ymm1, 704(%rsp)
	vpmovzxbw	%xmm7, %ymm14
	vpaddd	%ymm0, %ymm8, %ymm0
	vpmovzxwd	%xmm13, %ymm7
	vextracti128	$0x1, %ymm13, %xmm13
	vpaddd	%ymm1, %ymm0, %ymm0
	vpmovzxwd	%xmm13, %ymm13
	vpaddd	%ymm7, %ymm0, %ymm0
	vmovdqa	%ymm13, 864(%rsp)
	vpaddd	864(%rsp), %ymm0, %ymm0
	vpmovzxwd	%xmm14, %ymm13
	vextracti128	$0x1, %ymm14, %xmm14
	vpmovzxwd	%xmm14, %ymm14
	vmovdqa	%ymm13, 672(%rsp)
	vmovdqa	%ymm14, 640(%rsp)
	vpaddd	%ymm13, %ymm0, %ymm0
	vpmovzxbw	%xmm6, %ymm13
	vextracti128	$0x1, %ymm6, %xmm6
	vpaddd	%ymm14, %ymm0, %ymm0
	vpmovzxwd	%xmm13, %ymm14
	vextracti128	$0x1, %ymm13, %xmm13
	vpmovzxbw	%xmm6, %ymm6
	vpmovzxwd	%xmm13, %ymm13
	vpaddd	%ymm14, %ymm0, %ymm0
	vmovdqa	%ymm13, 896(%rsp)
	vpaddd	896(%rsp), %ymm0, %ymm0
	vpmovzxwd	%xmm6, %ymm13
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm6, %ymm6
	vmovdqa	%ymm6, 736(%rsp)
	vpaddd	%ymm13, %ymm0, %ymm0
	vpaddd	%ymm6, %ymm0, %ymm0
	vpmovzxbw	%xmm4, %xmm6
	vpsrldq	$8, %xmm4, %xmm4
	vpmovzxbw	%xmm4, %xmm4
	vpmovzxwd	%xmm6, %xmm1
	vpsrldq	$8, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vmovdqa	%xmm1, 928(%rsp)
	vmovdqa	%xmm6, 768(%rsp)
	vpaddd	928(%rsp), %xmm6, %xmm6
	vpmovzxwd	%xmm4, %xmm1
	vpsrldq	$8, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vmovdqa	%xmm1, 800(%rsp)
	vmovdqa	%xmm4, 832(%rsp)
	vpaddd	%xmm1, %xmm6, %xmm6
	vpaddd	%xmm4, %xmm6, %xmm6
	vpaddd	%xmm0, %xmm6, %xmm4
	vpmovzxbw	%xmm15, %xmm6
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm4, %xmm4
	vpmovzxwd	%xmm6, %xmm1
	vpsrlq	$32, %xmm15, %xmm0
	vpmovzxbw	%xmm0, %xmm0
	vmovq	%xmm1, %rdi
	vpmovzxwd	%xmm0, %xmm1
	vpsrlq	$32, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vmovq	%xmm1, %rcx
	vmovq	%rdi, %xmm1
	vpsrlq	$32, %xmm0, %xmm0
	vpmovzxwd	%xmm0, %xmm0
	vpaddd	%xmm1, %xmm6, %xmm1
	vmovq	%rcx, %xmm15
	vpaddd	%xmm15, %xmm1, %xmm1
	vpaddd	%xmm0, %xmm1, %xmm1
	vpaddd	%xmm4, %xmm1, %xmm1
	vpsrldq	$8, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm1, %xmm4
	vpsrlq	$32, %xmm4, %xmm1
	vpaddd	%xmm1, %xmm4, %xmm4
	vmovd	%xmm4, %edx
	cmpl	%edx, 320(%rax)
	jne	.L60
	vpmulld	.LC6(%rip), %ymm12, %ymm12
	vpmulld	.LC7(%rip), %ymm5, %ymm5
	vpmulld	.LC8(%rip), %ymm11, %ymm11
	vpmulld	.LC9(%rip), %ymm2, %ymm2
	vpmulld	.LC10(%rip), %ymm9, %ymm9
	vpmulld	.LC11(%rip), %ymm3, %ymm3
	vpmulld	.LC12(%rip), %ymm8, %ymm8
	vpmulld	.LC14(%rip), %ymm7, %ymm7
	vpaddd	%ymm5, %ymm12, %ymm5
	vpaddd	%ymm5, %ymm11, %ymm11
	vmovdqa	864(%rsp), %ymm5
	vpaddd	%ymm11, %ymm2, %ymm2
	vpaddd	%ymm2, %ymm9, %ymm9
	vpaddd	%ymm9, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm8, %ymm8
	vmovdqa	704(%rsp), %ymm3
	vpmulld	.LC13(%rip), %ymm3, %ymm1
	vpaddd	%ymm8, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm7, %ymm7
	vpmulld	.LC15(%rip), %ymm5, %ymm1
	vmovdqa	672(%rsp), %ymm5
	vpmulld	.LC16(%rip), %ymm5, %ymm2
	vmovdqa	640(%rsp), %ymm5
	vpaddd	%ymm7, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm2, %ymm1
	vpmulld	.LC17(%rip), %ymm5, %ymm2
	vmovdqa	896(%rsp), %ymm5
	vpaddd	%ymm1, %ymm2, %ymm2
	vpmulld	.LC18(%rip), %ymm14, %ymm1
	vpaddd	%ymm2, %ymm1, %ymm1
	vpmulld	.LC19(%rip), %ymm5, %ymm2
	vmovdqa	736(%rsp), %ymm5
	vpaddd	%ymm1, %ymm2, %ymm2
	vpmulld	.LC20(%rip), %ymm13, %ymm1
	vpaddd	%ymm2, %ymm1, %ymm1
	vpmulld	.LC21(%rip), %ymm5, %ymm2
	vmovdqa	768(%rsp), %xmm5
	vpaddd	%ymm1, %ymm2, %ymm2
	vpmulld	.LC23(%rip), %xmm5, %xmm1
	vmovdqa	928(%rsp), %xmm5
	vpmulld	.LC22(%rip), %xmm5, %xmm3
	vmovdqa	800(%rsp), %xmm5
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmulld	.LC24(%rip), %xmm5, %xmm3
	vmovdqa	832(%rsp), %xmm5
	vpaddd	%xmm3, %xmm1, %xmm1
	vpmulld	.LC25(%rip), %xmm5, %xmm3
	vmovq	.LC27(%rip), %xmm5
	vpmulld	%xmm5, %xmm6, %xmm6
	vmovq	%rdi, %xmm5
	vpaddd	%xmm3, %xmm1, %xmm1
	vmovq	.LC26(%rip), %xmm3
	vpaddd	%xmm2, %xmm1, %xmm1
	vextracti128	$0x1, %ymm2, %xmm2
	vpaddd	%xmm2, %xmm1, %xmm1
	vpmulld	%xmm3, %xmm5, %xmm2
	vmovq	.LC28(%rip), %xmm3
	vmovq	.LC29(%rip), %xmm5
	vpaddd	%xmm2, %xmm6, %xmm6
	vpmulld	%xmm3, %xmm15, %xmm2
	vpmulld	%xmm5, %xmm0, %xmm0
	vpaddd	%xmm2, %xmm6, %xmm6
	vpaddd	%xmm0, %xmm6, %xmm0
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm0, %edx
	cmpl	%edx, 324(%rax)
	jne	.L60
	jmp	.L59
.L87:
	movq	87608(%rsp), %rax
	subq	%fs:40, %rax
	jne	.L89
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
.L89:
	.cfi_restore_state
	vzeroupper
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE28:
	.size	sq2b_blind_pass.constprop.0, .-sq2b_blind_pass.constprop.0
	.section	.rodata.str1.8,"aMS",@progbits,1
	.align 8
.LC45:
	.string	"SQ2BOR O1_payload_det   %lld/%lld = %.6f  expect=1.000000 counting [A]\n"
	.align 8
.LC46:
	.string	"SQ2BOR O2_payload_rep   %lld/%lld = %.6f  expect>=0.990 measurement [A]\n"
	.align 8
.LC47:
	.string	"SQ2BOR O3_syndrome_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n"
	.align 8
.LC48:
	.string	"SQ2BOR O4_syndrome_rep  %lld/%lld = %.6f  expect=1.000000 measurement [A]\n"
	.align 8
.LC49:
	.string	"SQ2BOR O5_closure       %lld unresolved [A]  expect=0\n"
	.align 8
.LC50:
	.string	"SQ2BOR O6_apoptosis     %lld [A]  expect=0 isolated\n"
	.align 8
.LC52:
	.string	"SQ2BOR O7_blind_random  %lld/%lld detected+tombstoned (never silent)  expect=1.000000\n"
	.align 8
.LC53:
	.string	"SQ2BOR O8_blind_crafted %lld/%lld blind  expect=all-blind documented-exclusion\n"
	.align 8
.LC54:
	.string	"SQ2BOR auxB_det         %lld/%lld = %.6f  poisson tail\n"
	.align 8
.LC55:
	.string	"SQ2BOR auxB_rep         %lld/%lld = %.6f  poisson tail\n"
	.align 8
.LC56:
	.string	"SQ2BOR auxB_tombs       %lld  auxB_coh_fail %lld  auxB_slippage %lld  auxB_unresolved %lld\n"
	.align 8
.LC57:
	.string	"SQ2BOR aux_proofread_retries %lld (GTP bill, should be 0 absent injection)\n"
	.align 8
.LC58:
	.string	"SQ2BOR O9_main_cohere  %lld  expect=0 audit [A]\n"
	.section	.text.startup,"ax",@progbits
	.p2align 4
	.globl	main
	.type	main, @function
main:
.LFB23:
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
	subq	$2528, %rsp
	.cfi_escape 0x10,0x3,0x2,0x76,0x50
	movq	%fs:40, %rax
	movq	%rax, -56(%rbp)
	xorl	%eax, %eax
	movl	$1500, -2400(%rbp)
	cmpl	$1, %edi
	jle	.L91
	movq	8(%rsi), %rdi
	call	atoi@PLT
	movl	%eax, -2400(%rbp)
.L91:
	leaq	cell.2(%rip), %r14
	movl	$86336, %edx
	xorl	%esi, %esi
	xorl	%r15d, %r15d
	movq	%r14, %rdi
	call	memset@PLT
	xorl	%r9d, %r9d
	movl	$6, %edx
	movb	$0, -2288(%rbp)
	movl	$0, -2392(%rbp)
	movb	$0, -2272(%rbp)
	xorl	%r8d, %r8d
	xorl	%r10d, %r10d
	jmp	.L97
.L219:
	leal	1(%rdx), %ecx
	andl	$7, %ecx
	movl	86272(%r14,%rcx,4), %r9d
	cmpl	$31, %r9d
	jle	.L92
	leal	2(%rdx), %ecx
	andl	$7, %ecx
	movl	86272(%r14,%rcx,4), %r9d
	cmpl	$31, %r9d
	jle	.L92
	leal	3(%rdx), %ecx
	andl	$7, %ecx
	movl	86272(%r14,%rcx,4), %r9d
	cmpl	$31, %r9d
	jle	.L92
	leal	4(%rdx), %ecx
	andl	$7, %ecx
	movl	86272(%r14,%rcx,4), %r9d
	cmpl	$31, %r9d
	jle	.L92
	leal	5(%rdx), %ecx
	andl	$7, %ecx
	movl	86272(%r14,%rcx,4), %r9d
	cmpl	$31, %r9d
	jle	.L92
	leal	6(%rdx), %ecx
	andl	$7, %ecx
	movl	86272(%r14,%rcx,4), %r9d
	cmpl	$31, %r9d
	jle	.L92
	leal	7(%rdx), %ecx
	andl	$7, %ecx
	movl	86272(%r14,%rcx,4), %r9d
	cmpl	$31, %r9d
	jle	.L92
.L93:
	incl	%r10d
	cmpl	$256, %r10d
	je	.L96
.L221:
	movl	%r10d, %edx
	leaq	SQB_SCATLT(%rip), %rax
	addl	$17, %r15d
	andl	$31, %edx
	movl	(%rax,%rdx,4), %eax
	movl	86272(%r14,%rax,4), %r9d
	movq	%rax, %rdx
.L97:
	movl	$1431655765, %eax
	vmovd	%eax, %xmm14
	movl	$-1515870811, %eax
	vmovd	%eax, %xmm0
	vpbroadcastd	%xmm14, %ymm14
	vpbroadcastd	%xmm0, %ymm0
	vmovdqa	%ymm0, -2352(%rbp)
	cmpl	$31, %r9d
	jg	.L219
	movl	%edx, %ecx
.L92:
	vmovd	%r15d, %xmm2
	vmovdqa	-2352(%rbp), %ymm15
	movzbl	%r15b, %eax
	vpbroadcastb	%xmm2, %ymm2
	vpaddb	.LC33(%rip), %ymm2, %ymm8
	movb	%al, %ah
	vpxor	%ymm15, %ymm8, %ymm8
	vpmovzxbw	%xmm8, %ymm0
	vextracti128	$0x1, %ymm8, %xmm5
	vmovdqa	%ymm8, -208(%rbp)
	vpmovzxwd	%xmm0, %ymm4
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxbw	%xmm5, %ymm5
	vpmovzxwd	%xmm0, %ymm1
	vpmovzxwd	%xmm5, %ymm6
	vextracti128	$0x1, %ymm5, %xmm0
	vpaddb	.LC35(%rip), %ymm2, %ymm5
	vpaddd	%ymm1, %ymm4, %ymm9
	vpmulld	.LC7(%rip), %ymm1, %ymm1
	vpmovzxwd	%xmm0, %ymm0
	vpmulld	.LC6(%rip), %ymm4, %ymm4
	vpaddd	%ymm9, %ymm6, %ymm9
	vpaddd	%ymm9, %ymm0, %ymm9
	vpmulld	.LC9(%rip), %ymm0, %ymm0
	vpxor	%ymm15, %ymm5, %ymm5
	vmovdqa	%ymm5, -176(%rbp)
	vpaddd	%ymm1, %ymm4, %ymm4
	vpmulld	.LC8(%rip), %ymm6, %ymm1
	vpaddd	%ymm4, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm0, %ymm4
	vextracti128	$0x1, %ymm5, %xmm0
	vpmovzxbw	%xmm5, %ymm1
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm1, %ymm7
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm0, %ymm10
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm1, %ymm1
	vpmovzxwd	%xmm0, %ymm6
	vpaddd	%ymm7, %ymm9, %ymm0
	vpmulld	.LC10(%rip), %ymm7, %ymm7
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC11(%rip), %ymm1, %ymm1
	vpaddd	%ymm0, %ymm10, %ymm0
	vpaddd	%ymm0, %ymm6, %ymm0
	vpmulld	.LC13(%rip), %ymm6, %ymm6
	vpaddd	%ymm4, %ymm7, %ymm4
	vpaddd	%ymm4, %ymm1, %ymm4
	vpmulld	.LC12(%rip), %ymm10, %ymm1
	vpaddd	%ymm4, %ymm1, %ymm1
	vpaddb	.LC36(%rip), %ymm2, %ymm4
	vpaddb	.LC37(%rip), %ymm2, %ymm2
	vpaddd	%ymm1, %ymm6, %ymm6
	vpxor	%ymm15, %ymm4, %ymm4
	vpxor	%ymm15, %ymm2, %ymm2
	vpmovzxbw	%xmm4, %ymm1
	vextracti128	$0x1, %ymm4, %xmm7
	vextracti128	$0x1, %ymm2, %xmm3
	vmovdqa	%ymm2, -112(%rbp)
	vpmovzxwd	%xmm1, %ymm10
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxbw	%xmm7, %ymm7
	vpmovzxbw	%xmm3, %ymm3
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm10, %ymm0, %ymm0
	vpmulld	.LC14(%rip), %ymm10, %ymm10
	vpmovzxwd	%xmm7, %ymm9
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC15(%rip), %ymm1, %ymm1
	vextracti128	$0x1, %ymm7, %xmm7
	vmovdqa	%ymm4, -144(%rbp)
	vpmovzxwd	%xmm7, %ymm7
	vpaddd	%ymm0, %ymm9, %ymm0
	vpaddd	%ymm0, %ymm7, %ymm0
	vpmulld	.LC17(%rip), %ymm7, %ymm7
	vpaddd	%ymm6, %ymm10, %ymm6
	vpaddd	%ymm6, %ymm1, %ymm6
	vpmulld	.LC16(%rip), %ymm9, %ymm1
	vpaddd	%ymm6, %ymm1, %ymm1
	vpmovzxwd	%xmm3, %ymm6
	vextracti128	$0x1, %ymm3, %xmm3
	vpaddd	%ymm1, %ymm7, %ymm7
	vpmovzxbw	%xmm2, %ymm1
	vpmovzxwd	%xmm3, %ymm3
	vpxor	%ymm14, %ymm2, %ymm2
	vpmovzxwd	%xmm1, %ymm9
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovzxwd	%xmm1, %ymm1
	vpaddd	%ymm0, %ymm9, %ymm0
	vpmulld	.LC18(%rip), %ymm9, %ymm9
	vpaddd	%ymm0, %ymm1, %ymm0
	vpmulld	.LC19(%rip), %ymm1, %ymm1
	vpaddd	%ymm0, %ymm6, %ymm0
	vpmulld	.LC20(%rip), %ymm6, %ymm6
	vpaddd	%ymm0, %ymm3, %ymm0
	vpaddd	%ymm7, %ymm9, %ymm7
	vpaddd	%ymm7, %ymm1, %ymm1
	vpaddd	%ymm1, %ymm6, %ymm6
	vpmulld	.LC21(%rip), %ymm3, %ymm1
	vmovd	%r15d, %xmm3
	vpbroadcastb	%xmm3, %xmm3
	vpaddb	.LC38(%rip), %xmm3, %xmm3
	vpxor	%xmm15, %xmm3, %xmm3
	vpmovzxbw	%xmm3, %xmm7
	vpaddd	%ymm6, %ymm1, %ymm1
	vpsrldq	$8, %xmm3, %xmm6
	vpmovzxbw	%xmm6, %xmm6
	vpmovzxwd	%xmm7, %xmm12
	vpsrldq	$8, %xmm7, %xmm7
	vpmovzxwd	%xmm7, %xmm7
	vpmovzxwd	%xmm6, %xmm10
	vpaddd	%xmm7, %xmm12, %xmm11
	vpmulld	.LC22(%rip), %xmm12, %xmm12
	vpsrldq	$8, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vpmulld	.LC23(%rip), %xmm7, %xmm7
	vpaddd	%xmm10, %xmm11, %xmm11
	vmovdqa	%xmm3, -80(%rbp)
	vpmulld	.LC24(%rip), %xmm10, %xmm10
	vpaddd	%xmm6, %xmm11, %xmm11
	vpmulld	.LC25(%rip), %xmm6, %xmm6
	vpaddd	%xmm0, %xmm11, %xmm9
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm9, %xmm0
	vpaddd	%xmm7, %xmm12, %xmm7
	vpaddd	%xmm10, %xmm7, %xmm10
	vpaddd	%xmm6, %xmm10, %xmm6
	vpaddd	%xmm1, %xmm6, %xmm7
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%xmm1, %xmm7, %xmm1
	vmovd	%eax, %xmm7
	leaq	2(%r8), %rax
	vpshuflw	$0, %xmm7, %xmm6
	vmovq	.LC40(%rip), %xmm7
	vpaddb	%xmm6, %xmm7, %xmm7
	vmovq	.LC41(%rip), %xmm6
	vmovq	.LC26(%rip), %xmm15
	vmovdqa	%ymm2, -2064(%rbp)
	vpxor	.LC31(%rip), %xmm3, %xmm2
	movq	%rax, -2096(%rbp)
	movslq	%r9d, %rax
	vpxor	%xmm3, %xmm3, %xmm3
	imulq	$336, %rax, %rdx
	movq	%rax, -2280(%rbp)
	movl	%r9d, -2384(%rbp)
	vmovdqa	%xmm3, -2128(%rbp)
	imulq	$10752, %rcx, %rax
	movq	$0, -2264(%rbp)
	movq	%rcx, %r9
	vmovdqa	%ymm14, -2320(%rbp)
	leaq	(%rdx,%rax), %r11
	leaq	168(%rdx,%rax), %rsi
	leaq	296(%rdx,%rax), %rbx
	leaq	312(%rdx,%rax), %rax
	addq	%r14, %rax
	addq	%r14, %rsi
	addq	%r14, %rbx
	leaq	(%r14,%r11), %rdi
	vpxor	%xmm6, %xmm7, %xmm7
	movq	%rax, -2088(%rbp)
	leaq	128(%r14,%r11), %r13
	leaq	144(%r14,%r11), %r12
	vpmovzxbw	%xmm7, %xmm10
	vpsrlq	$32, %xmm7, %xmm9
	vpmovzxbw	%xmm9, %xmm9
	vmovdqa	%xmm2, -2080(%rbp)
	vpmovzxwd	%xmm10, %xmm12
	vpsrlq	$32, %xmm10, %xmm10
	vpmovzxwd	%xmm10, %xmm10
	vpmovzxwd	%xmm9, %xmm11
	vpaddd	%xmm10, %xmm12, %xmm13
	vpsrlq	$32, %xmm9, %xmm9
	vpmovzxwd	%xmm9, %xmm9
	vmovq	.LC4(%rip), %xmm2
	vmovq	%xmm7, -64(%rbp)
	vpmulld	%xmm15, %xmm12, %xmm12
	vpaddd	%xmm11, %xmm13, %xmm13
	vpaddd	%xmm9, %xmm13, %xmm13
	vpxor	%xmm2, %xmm7, %xmm7
	vpaddd	%xmm0, %xmm13, %xmm6
	vpsrldq	$8, %xmm0, %xmm0
	vpxor	%xmm13, %xmm13, %xmm13
	vpaddd	%xmm0, %xmm6, %xmm6
	vmovq	.LC27(%rip), %xmm0
	vpmulld	%xmm0, %xmm10, %xmm10
	vmovq	.LC28(%rip), %xmm0
	vpaddd	%xmm10, %xmm12, %xmm10
	vpmulld	%xmm0, %xmm11, %xmm11
	vmovq	.LC29(%rip), %xmm0
	vpaddd	%xmm11, %xmm10, %xmm10
	vpcmpeqd	%ymm11, %ymm11, %ymm11
	vpabsb	%ymm11, %ymm11
	vpmulld	%xmm0, %xmm9, %xmm9
	vpaddd	%xmm9, %xmm10, %xmm9
	vpaddd	%xmm1, %xmm9, %xmm0
	vpsrldq	$8, %xmm1, %xmm1
	vmovdqa	%ymm14, %ymm9
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrlq	$32, %xmm6, %xmm1
	vpaddd	%xmm1, %xmm6, %xmm6
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vmovd	%xmm6, -2112(%rbp)
	vmovd	%xmm0, -2104(%rbp)
	vinsertps	$16, %xmm0, %xmm6, %xmm6
	vpxor	%ymm14, %ymm8, %ymm0
	vmovdqa	%ymm0, -2160(%rbp)
	vpxor	%ymm14, %ymm5, %ymm0
	vmovdqa	%ymm0, -2192(%rbp)
	vpxor	%ymm14, %ymm4, %ymm0
	vmovdqa	%ymm0, -2224(%rbp)
	vpcmpeqd	%xmm0, %xmm0, %xmm0
	vpabsb	%xmm0, %xmm2
	vmovdqa	%xmm2, -2256(%rbp)
.L95:
	vmovdqa	-208(%rbp), %ymm0
	vmovdqa	-2160(%rbp), %ymm2
	movq	-2088(%rbp), %rax
	vmovdqu	%ymm0, (%rdi)
	vmovdqa	-176(%rbp), %ymm0
	vmovdqu	%ymm0, 32(%rdi)
	vmovdqa	-144(%rbp), %ymm0
	vmovdqu	%ymm0, 64(%rdi)
	vmovdqa	-112(%rbp), %ymm0
	vmovdqu	%ymm0, 96(%rdi)
	vmovdqu	-88(%rbp), %ymm0
	vmovdqu	%ymm0, 120(%rdi)
	vmovdqu	%ymm2, (%rsi)
	vmovdqa	-2192(%rbp), %ymm2
	vmovdqu	%ymm2, 32(%rsi)
	vmovdqa	-2224(%rbp), %ymm2
	vmovdqu	%ymm2, 64(%rsi)
	vmovdqa	-2064(%rbp), %ymm2
	vmovdqu	%ymm2, 96(%rsi)
	vmovdqa	-2080(%rbp), %xmm2
	vmovdqu	%xmm2, (%rbx)
	vmovq	%xmm7, (%rax)
	vmovdqu	(%rdi), %ymm1
	vpmovzxbw	%xmm1, %ymm2
	vextracti128	$0x1, %ymm1, %xmm0
	vpxor	(%rsi), %ymm1, %ymm1
	vpmovzxwd	%xmm2, %ymm5
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm0, %ymm0
	vpmovzxwd	%xmm0, %ymm4
	vpmovzxwd	%xmm2, %ymm2
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovzxwd	%xmm0, %ymm3
	vpaddd	%ymm2, %ymm5, %ymm0
	vpmulld	.LC6(%rip), %ymm5, %ymm5
	vpmulld	.LC7(%rip), %ymm2, %ymm2
	vpaddd	%ymm0, %ymm4, %ymm0
	vpmulld	.LC8(%rip), %ymm4, %ymm4
	vpaddd	%ymm0, %ymm3, %ymm0
	vpmulld	.LC9(%rip), %ymm3, %ymm3
	vpcmpeqb	%ymm9, %ymm1, %ymm1
	vpcmpeqb	%ymm13, %ymm1, %ymm1
	vpand	%ymm11, %ymm1, %ymm1
	vpaddd	%ymm2, %ymm5, %ymm2
	vpaddd	%ymm2, %ymm4, %ymm4
	vpmovzxbw	%xmm1, %ymm2
	vextracti128	$0x1, %ymm1, %xmm1
	vpaddd	%ymm4, %ymm3, %ymm4
	vpmovzxwd	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxbw	%xmm1, %ymm1
	vpmovzxwd	%xmm2, %ymm2
	vpor	%ymm2, %ymm3, %ymm2
	vpmovzxwd	%xmm1, %ymm3
	vextracti128	$0x1, %ymm1, %xmm1
	vpor	%ymm2, %ymm3, %ymm3
	vmovdqu	32(%rdi), %ymm2
	vpmovzxwd	%xmm1, %ymm1
	vpor	%ymm3, %ymm1, %ymm1
	vpmovzxbw	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm5
	vpmovzxwd	%xmm3, %ymm10
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm5, %ymm5
	vpaddd	%ymm10, %ymm0, %ymm0
	vpmulld	.LC10(%rip), %ymm10, %ymm10
	vpmovzxwd	%xmm3, %ymm3
	vpmovzxwd	%xmm5, %ymm8
	vpaddd	%ymm0, %ymm3, %ymm0
	vextracti128	$0x1, %ymm5, %xmm5
	vpmulld	.LC11(%rip), %ymm3, %ymm3
	vpmovzxwd	%xmm5, %ymm5
	vpaddd	%ymm0, %ymm8, %ymm0
	vpmulld	.LC12(%rip), %ymm8, %ymm8
	vpaddd	%ymm0, %ymm5, %ymm0
	vpaddd	%ymm4, %ymm10, %ymm10
	vpmulld	.LC13(%rip), %ymm5, %ymm4
	vpxor	32(%rsi), %ymm2, %ymm2
	vpaddd	%ymm10, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm8, %ymm8
	vpcmpeqb	%ymm9, %ymm2, %ymm2
	vpcmpeqb	%ymm13, %ymm2, %ymm2
	vpand	%ymm11, %ymm2, %ymm2
	vpaddd	%ymm8, %ymm4, %ymm4
	vpmovzxbw	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm3, %ymm5
	vpmovzxbw	%xmm2, %ymm2
	vpor	%ymm1, %ymm5, %ymm5
	vextracti128	$0x1, %ymm3, %xmm1
	vpmovzxwd	%xmm2, %ymm3
	vpmovzxwd	%xmm1, %ymm1
	vpor	%ymm5, %ymm1, %ymm1
	vpor	%ymm1, %ymm3, %ymm3
	vextracti128	$0x1, %ymm2, %xmm1
	vmovdqu	64(%rdi), %ymm2
	vpmovzxwd	%xmm1, %ymm1
	vpor	%ymm3, %ymm1, %ymm1
	vpmovzxbw	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm5
	vpxor	64(%rsi), %ymm2, %ymm2
	vpmovzxwd	%xmm3, %ymm10
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm5, %ymm5
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm10, %ymm0, %ymm0
	vpmulld	.LC14(%rip), %ymm10, %ymm10
	vpmovzxwd	%xmm5, %ymm8
	vpaddd	%ymm0, %ymm3, %ymm0
	vpmulld	.LC15(%rip), %ymm3, %ymm3
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%ymm0, %ymm8, %ymm0
	vpmulld	.LC16(%rip), %ymm8, %ymm8
	vpmovzxwd	%xmm5, %ymm5
	vpaddd	%ymm0, %ymm5, %ymm0
	vpcmpeqb	%ymm9, %ymm2, %ymm2
	vpcmpeqb	%ymm13, %ymm2, %ymm2
	vpand	%ymm11, %ymm2, %ymm2
	vpaddd	%ymm4, %ymm10, %ymm10
	vpmulld	.LC17(%rip), %ymm5, %ymm4
	vpaddd	%ymm10, %ymm3, %ymm3
	vpaddd	%ymm3, %ymm8, %ymm8
	vpmovzxbw	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm2
	vpmovzxwd	%xmm3, %ymm5
	vpmovzxbw	%xmm2, %ymm2
	vpor	%ymm1, %ymm5, %ymm5
	vextracti128	$0x1, %ymm3, %xmm1
	vpmovzxwd	%xmm2, %ymm3
	vpmovzxwd	%xmm1, %ymm1
	vpor	%ymm5, %ymm1, %ymm1
	vpor	%ymm1, %ymm3, %ymm3
	vextracti128	$0x1, %ymm2, %xmm1
	vmovdqu	96(%rdi), %ymm2
	vpmovzxwd	%xmm1, %ymm1
	vpor	%ymm3, %ymm1, %ymm1
	vpaddd	%ymm8, %ymm4, %ymm4
	vpmovzxbw	%xmm2, %ymm3
	vextracti128	$0x1, %ymm2, %xmm5
	vpxor	96(%rsi), %ymm2, %ymm2
	vpmovzxwd	%xmm3, %ymm10
	vextracti128	$0x1, %ymm3, %xmm3
	vpmovzxbw	%xmm5, %ymm5
	vpmovzxwd	%xmm3, %ymm3
	vpaddd	%ymm0, %ymm10, %ymm0
	vpmulld	.LC18(%rip), %ymm10, %ymm10
	vpmovzxwd	%xmm5, %ymm8
	vpaddd	%ymm0, %ymm3, %ymm0
	vpmulld	.LC19(%rip), %ymm3, %ymm3
	vextracti128	$0x1, %ymm5, %xmm5
	vpaddd	%ymm0, %ymm8, %ymm0
	vpmulld	.LC20(%rip), %ymm8, %ymm8
	vpmovzxwd	%xmm5, %ymm5
	vpaddd	%ymm0, %ymm5, %ymm0
	vpcmpeqb	%ymm9, %ymm2, %ymm2
	vpcmpeqb	%ymm13, %ymm2, %ymm2
	vpand	%ymm11, %ymm2, %ymm2
	vpaddd	%ymm4, %ymm10, %ymm10
	vpmovzxbw	%xmm2, %ymm4
	vextracti128	$0x1, %ymm2, %xmm2
	vpaddd	%ymm10, %ymm3, %ymm3
	vpmovzxbw	%xmm2, %ymm2
	vpaddd	%ymm3, %ymm8, %ymm8
	vpmulld	.LC21(%rip), %ymm5, %ymm3
	vpmovzxwd	%xmm4, %ymm5
	vpor	%ymm1, %ymm5, %ymm5
	vextracti128	$0x1, %ymm4, %xmm1
	vpmovzxwd	%xmm2, %ymm4
	vpmovzxwd	%xmm1, %ymm1
	vpor	%ymm5, %ymm1, %ymm1
	vpor	%ymm1, %ymm4, %ymm4
	vextracti128	$0x1, %ymm2, %xmm1
	vmovdqa	0(%r13), %xmm2
	vpmovzxwd	%xmm1, %ymm1
	vpor	%ymm4, %ymm1, %ymm1
	vpaddd	%ymm8, %ymm3, %ymm3
	vpmovzxbw	%xmm2, %xmm5
	vpsrldq	$8, %xmm2, %xmm4
	vpxor	(%rbx), %xmm2, %xmm2
	vpmovzxbw	%xmm4, %xmm4
	vpmovzxwd	%xmm5, %xmm12
	vpsrldq	$8, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpmovzxwd	%xmm4, %xmm8
	vpaddd	%xmm5, %xmm12, %xmm10
	vpmulld	.LC22(%rip), %xmm12, %xmm12
	vpsrldq	$8, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpmulld	.LC23(%rip), %xmm5, %xmm5
	vpaddd	%xmm8, %xmm10, %xmm10
	vpmulld	.LC24(%rip), %xmm8, %xmm8
	vpaddd	%xmm4, %xmm10, %xmm10
	vpmulld	.LC25(%rip), %xmm4, %xmm4
	vpaddd	%xmm0, %xmm10, %xmm14
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddd	%xmm0, %xmm14, %xmm0
	vpcmpeqb	.LC31(%rip), %xmm2, %xmm2
	vpcmpeqb	-2128(%rbp), %xmm2, %xmm2
	vpand	-2256(%rbp), %xmm2, %xmm2
	vpaddd	%xmm5, %xmm12, %xmm5
	vpaddd	%xmm8, %xmm5, %xmm8
	vpaddd	%xmm4, %xmm8, %xmm4
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
	vpor	%xmm1, %xmm2, %xmm2
	vextracti128	$0x1, %ymm1, %xmm1
	vpor	%xmm1, %xmm2, %xmm2
	vmovq	(%r12), %xmm1
	vpmovzxbw	%xmm1, %xmm4
	vpsrlq	$32, %xmm1, %xmm3
	vpmovzxbw	%xmm3, %xmm3
	vpxor	%xmm7, %xmm1, %xmm1
	vpmovzxwd	%xmm4, %xmm12
	vpsrlq	$32, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpmovzxwd	%xmm3, %xmm10
	vpaddd	%xmm4, %xmm12, %xmm14
	vpsrlq	$32, %xmm3, %xmm3
	vpmulld	%xmm15, %xmm12, %xmm12
	vpmovzxwd	%xmm3, %xmm3
	vpaddd	%xmm10, %xmm14, %xmm14
	vpaddd	%xmm3, %xmm14, %xmm14
	vpaddd	%xmm0, %xmm14, %xmm8
	vmovq	.LC27(%rip), %xmm14
	vpsrldq	$8, %xmm0, %xmm0
	vpaddd	%xmm0, %xmm8, %xmm0
	vpmulld	%xmm14, %xmm4, %xmm4
	vpaddd	%xmm4, %xmm12, %xmm4
	vmovq	.LC28(%rip), %xmm12
	vpmulld	%xmm12, %xmm10, %xmm10
	vpaddd	%xmm10, %xmm4, %xmm10
	vmovq	.LC29(%rip), %xmm4
	vpmulld	%xmm4, %xmm3, %xmm3
	vmovq	.LC4(%rip), %xmm4
	vpaddd	%xmm3, %xmm10, %xmm3
	vpaddd	%xmm5, %xmm3, %xmm3
	vpsrldq	$8, %xmm5, %xmm5
	vpcmpeqb	%xmm4, %xmm1, %xmm1
	vmovq	-2264(%rbp), %xmm4
	vpaddd	%xmm5, %xmm3, %xmm3
	vpcmpeqb	%xmm4, %xmm1, %xmm1
	vmovq	.LC5(%rip), %xmm4
	vpand	%xmm4, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm4
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxbw	%xmm1, %xmm1
	vpmovzxwd	%xmm4, %xmm5
	vpsrlq	$32, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpor	%xmm4, %xmm5, %xmm4
	vpmovzxwd	%xmm1, %xmm5
	vpsrlq	$32, %xmm1, %xmm1
	vpmovzxwd	%xmm1, %xmm1
	vpor	%xmm5, %xmm4, %xmm5
	vpor	%xmm1, %xmm5, %xmm1
	vpor	%xmm2, %xmm1, %xmm4
	vpsrlq	$32, %xmm3, %xmm1
	vpaddd	%xmm1, %xmm3, %xmm3
	vpsrlq	$32, %xmm0, %xmm1
	vpaddd	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm2, %xmm2
	vpor	%xmm2, %xmm4, %xmm2
	vmovd	%xmm3, %ecx
	cmpl	-2104(%rbp), %ecx
	vmovd	%xmm0, %eax
	vpsrlq	$32, %xmm2, %xmm0
	vpor	%xmm0, %xmm2, %xmm2
	vmovd	%xmm2, %edx
	sete	%cl
	cmpl	-2112(%rbp), %eax
	sete	%al
	andl	%ecx, %eax
	testl	%edx, %edx
	sete	%dl
	andb	%dl, %al
	jne	.L220
	incq	%r8
	cmpq	-2096(%rbp), %r8
	movb	$1, -2272(%rbp)
	jne	.L95
	leaq	24+cell.2(%rip), %rax
	incl	%r10d
	vmovdqa	-2320(%rbp), %ymm14
	vmovq	%xmm6, 296(%rax,%r11)
	vmovq	%xmm6, 128(%rax,%r11)
	cmpl	$256, %r10d
	jne	.L221
.L96:
	cmpb	$0, -2288(%rbp)
	vmovdqa	%ymm14, %ymm13
	je	.L98
	movl	-2392(%rbp), %eax
	movl	%eax, 86304+cell.2(%rip)
.L98:
	cmpb	$0, -2272(%rbp)
	je	.L99
	movq	%r8, 86312+cell.2(%rip)
.L99:
	vxorps	%xmm3, %xmm3, %xmm3
	vmovdqa	%ymm13, -2160(%rbp)
	movl	$86336, %edx
	movq	%r14, %rsi
	vmovaps	%xmm3, -2064(%rbp)
	leaq	clean.1(%rip), %rdi
	vzeroupper
	call	memcpy@PLT
	vpxor	%xmm0, %xmm0, %xmm0
	movl	-2400(%rbp), %r8d
	vmovdqa	%ymm0, -1936(%rbp)
	vmovdqa	%ymm0, -1808(%rbp)
	vmovdqa	%ymm0, -2000(%rbp)
	vmovdqa	%ymm0, -1968(%rbp)
	vmovdqu	%ymm0, -1912(%rbp)
	vmovdqa	%ymm0, -1872(%rbp)
	vmovdqa	%ymm0, -1840(%rbp)
	vmovdqu	%ymm0, -1784(%rbp)
	testl	%r8d, %r8d
	jle	.L168
	vmovdqa	-2160(%rbp), %ymm13
	movabsq	$-1749540032614691874, %rax
	xorl	%ebx, %ebx
	movq	$0, -2088(%rbp)
	movq	%rax, -2448(%rbp)
	movabsq	$7683277266246660415, %rax
	movq	$0, -2080(%rbp)
	movq	$0, -2096(%rbp)
	movq	%rax, -2280(%rbp)
	movabsq	$-8050056175193481693, %rax
	movq	$0, -2128(%rbp)
	movq	$0, -2224(%rbp)
	movq	%rax, -2272(%rbp)
	leaq	sqb_item_at(%rip), %rax
	movq	$0, -2104(%rbp)
	movq	$0, -2288(%rbp)
	movabsq	$1600686389938274267, %r15
	movl	$0, -2112(%rbp)
	movq	%rax, -2264(%rbp)
	movl	$91, %r13d
	vmovdqa	%ymm13, -2256(%rbp)
.L129:
	movl	-2112(%rbp), %eax
	movl	$3435973837, %edx
	xorl	%r8d, %r8d
	imulq	%rdx, %rax
	shrq	$34, %rax
	leal	(%rax,%rax,4), %edx
	movl	-2112(%rbp), %eax
	subl	%edx, %eax
	cmpl	$2, %eax
	jle	.L101
	xorl	%r8d, %r8d
	cmpl	$3, %eax
	setne	%r8b
	incl	%r8d
.L101:
	vmovdqa	%ymm0, -2384(%rbp)
	movl	%r8d, -2320(%rbp)
	movl	$86336, %edx
	leaq	clean.1(%rip), %rsi
	movq	%r14, %rdi
	vzeroupper
	call	memcpy@PLT
	movq	-2448(%rbp), %rdi
	movq	-2272(%rbp), %rsi
	movq	-2280(%rbp), %rdx
	movl	-2320(%rbp), %r8d
	vmovdqa	-2384(%rbp), %ymm0
	movq	%rdi, %r10
	leaq	(%rdi,%r15), %r12
	xorq	%rsi, %r10
	xorq	%r15, %rdx
	movq	%rsi, %rax
	salq	$17, %rsi
	movq	%r10, %rcx
	xorq	%rdx, %rsi
	rorx	$19, %r10, %r10
	xorq	%rdx, %rax
	xorq	%r15, %rcx
	movq	%rax, %r9
	movq	%rax, %rdi
	salq	$17, %rax
	xorq	%rcx, %rsi
	movq	%rcx, %rdx
	addq	%r10, %rcx
	xorq	%r10, %r9
	rorx	$47, %rcx, %rcx
	xorq	%rsi, %rdi
	xorq	%r9, %rdx
	rorx	$19, %r9, %r9
	andl	$31, %ecx
	movq	%rdi, %r10
	rorx	$47, %r12, %r12
	movl	%ecx, -2160(%rbp)
	movq	%rax, %rcx
	xorq	%r9, %r10
	movq	%rdx, %rax
	xorq	%rsi, %rcx
	movq	%rdi, %rsi
	salq	$17, %rdi
	xorq	%r10, %rax
	xorq	%rdx, %rcx
	rorx	$19, %r10, %r10
	addq	%r9, %rdx
	movq	%rax, %r9
	xorq	%rcx, %rsi
	xorq	%rcx, %rdi
	rorx	$47, %rdx, %rdx
	andl	$7, %r12d
	xorq	%rax, %rdi
	movq	%rsi, %r11
	addq	%r10, %rax
	movl	%edx, %r15d
	xorq	%r10, %r11
	rorx	$47, %rax, %r10
	movq	%rsi, %rcx
	andl	$1, %r15d
	movl	%r10d, %eax
	xorq	%rdi, %rcx
	xorq	%r11, %r9
	rorx	$19, %r11, %rdx
	shrl	$3, %eax
	movl	%r15d, -2192(%rbp)
	movq	%r9, %r15
	imulq	$452101821, %rax, %rax
	shrq	$33, %rax
	imull	$152, %eax, %r11d
	salq	$17, %rsi
	movl	%r10d, %eax
	movq	%rcx, %r10
	xorq	%rdi, %rsi
	movq	%rcx, %rdi
	salq	$17, %rcx
	xorq	%r9, %rsi
	xorq	%rdx, %rdi
	xorq	%rsi, %rcx
	xorq	%rsi, %r10
	rorx	$19, %rdi, %rsi
	xorq	%rdi, %r15
	movq	%rcx, -2280(%rbp)
	leaq	(%r9,%rdx), %rcx
	movq	%rsi, -2448(%rbp)
	movl	$2155905153, %edi
	rorx	$47, %rcx, %rcx
	subl	%r11d, %eax
	movq	%r10, -2272(%rbp)
	movl	%ecx, %esi
	imulq	%rdi, %rsi
	shrq	$39, %rsi
	testl	%r8d, %r8d
	leal	1(%rcx,%rsi), %ecx
	je	.L102
	movl	-2160(%rbp), %r9d
	movl	-2192(%rbp), %r11d
	movl	%r12d, %esi
	andl	$7, %eax
	imulq	$10752, %rsi, %rdi
	imulq	$336, %r9, %r10
	addq	%r10, %rdi
	movq	%r11, %r10
	negq	%r10
	andl	$168, %r10d
	addq	%rdi, %r10
	cmpl	$1, %r8d
	je	.L103
	leaq	160(%r10,%rax), %rax
	vmovdqa	%ymm0, -2160(%rbp)
	xorb	%cl, (%r14,%rax)
	vzeroupper
	call	sqb_sweep.constprop.1
	vmovdqa	.LC33(%rip), %ymm2
	vmovdqa	.LC60(%rip), %ymm1
	vmovdqa	.LC35(%rip), %ymm3
	vmovdqa	.LC36(%rip), %ymm4
	vmovdqa	.LC37(%rip), %ymm5
	vmovdqa	-2160(%rbp), %ymm0
	movq	86320(%r14), %rsi
	addq	%rax, -2080(%rbp)
	addq	%rsi, -2096(%rbp)
	movq	86312(%r14), %rsi
	addq	%rsi, -2088(%rbp)
.L104:
	leaq	sqb_item_at(%rip), %rax
	leaq	cell.2(%rip), %r10
	movq	%r15, -2160(%rbp)
	movq	%rax, -2264(%rbp)
	movq	%rax, %r11
	movq	%r10, %r14
	movq	%r10, %r9
.L119:
	movq	%r9, %rcx
	xorl	%esi, %esi
	.p2align 4
	.p2align 3
.L127:
	cmpb	$0, 86016(%r10,%rsi)
	je	.L122
	cmpl	$-559063315, 164(%rcx)
	je	.L125
	vmovdqu	32(%rcx), %ymm6
	movl	(%r11,%rsi,4), %edi
	vmovdqu	(%rcx), %ymm8
	movl	%edi, %eax
	sall	$4, %eax
	addl	%edi, %eax
	vmovdqa	%ymm6, -176(%rbp)
	vmovdqu	64(%rcx), %ymm6
	vmovdqa	%ymm8, -208(%rbp)
	vmovdqa	%ymm6, -144(%rbp)
	vmovdqu	96(%rcx), %ymm6
	vmovdqa	%ymm6, -112(%rbp)
	vmovdqu	120(%rcx), %ymm6
	vmovdqu	%ymm6, -88(%rbp)
	vmovd	%eax, %xmm6
	vpbroadcastb	%xmm6, %ymm6
	vpaddb	%ymm2, %ymm6, %ymm7
	vpxor	%ymm1, %ymm7, %ymm7
	vpcmpeqb	%ymm8, %ymm7, %ymm7
	vpcmpeqb	%ymm0, %ymm7, %ymm7
	vptest	%ymm7, %ymm7
	jne	.L175
	vpaddb	%ymm3, %ymm6, %ymm7
	vpxor	%ymm1, %ymm7, %ymm7
	vpcmpeqb	-176(%rbp), %ymm7, %ymm7
	vpcmpeqb	%ymm0, %ymm7, %ymm7
	vptest	%ymm7, %ymm7
	jne	.L176
	vpaddb	%ymm4, %ymm6, %ymm7
	vpxor	%ymm1, %ymm7, %ymm7
	vpcmpeqb	-144(%rbp), %ymm7, %ymm7
	vpcmpeqb	%ymm0, %ymm7, %ymm7
	vptest	%ymm7, %ymm7
	jne	.L177
	vpaddb	%ymm5, %ymm6, %ymm6
	movl	$24, %r8d
	movl	$128, %eax
	vpxor	%ymm1, %ymm6, %ymm6
	vpcmpeqb	-112(%rbp), %ymm6, %ymm6
	vpcmpeqb	%ymm0, %ymm6, %ymm6
	vptest	%ymm6, %ymm6
	jne	.L222
.L124:
	movl	%eax, %r12d
	imull	%r13d, %eax
	movl	%edi, %r15d
	sall	$4, %r15d
	leaq	-208(%rbp,%r12), %rdx
	addl	%r15d, %edi
	addl	%edi, %eax
	leal	-1(%r8), %edi
	addq	%r12, %rdi
	leaq	-207(%rbp,%rdi), %r8
	jmp	.L126
	.p2align 5
	.p2align 4
	.p2align 3
.L223:
	incq	%rdx
	addl	$91, %eax
	cmpq	%rdx, %r8
	je	.L122
.L126:
	movl	%eax, %edi
	xorl	$-91, %edi
	cmpb	%dil, (%rdx)
	je	.L223
.L125:
	incq	%rbx
.L122:
	incq	%rsi
	addq	$336, %rcx
	cmpq	$32, %rsi
	jne	.L127
	subq	$-128, %r11
	leaq	1024+sqb_item_at(%rip), %rax
	addq	$10752, %r9
	addq	$32, %r10
	cmpq	%rax, %r11
	jne	.L119
	incl	-2112(%rbp)
	movq	-2160(%rbp), %r15
	movl	-2112(%rbp), %eax
	cmpl	%eax, -2400(%rbp)
	jne	.L129
	movl	-2400(%rbp), %eax
	vmovdqa	-2256(%rbp), %ymm13
	cmpl	$2, %eax
	jle	.L179
	vmovaps	-2064(%rbp), %xmm14
	movl	$2863311531, %edx
	movq	-2448(%rbp), %r14
	xorl	%r13d, %r13d
	imulq	%rdx, %rax
	movq	$0, -2192(%rbp)
	movq	$0, -2384(%rbp)
	movq	$0, -2320(%rbp)
	movq	$0, -2256(%rbp)
	movq	$0, -2112(%rbp)
	movq	$0, -2264(%rbp)
	movq	$0, -2160(%rbp)
	movl	$0, -2392(%rbp)
	movq	$0, -2400(%rbp)
	shrq	$33, %rax
	movq	%rbx, -2408(%rbp)
	movq	%r15, -2480(%rbp)
	movq	%rax, -2512(%rbp)
.L158:
	vmovdqa	%ymm13, -2576(%rbp)
	vmovaps	%xmm14, -2528(%rbp)
	leaq	clean.1(%rip), %rsi
	leaq	cell.2(%rip), %rdi
	movl	$86336, %edx
	leaq	-1744(%rbp), %r15
	vzeroupper
	movq	%r15, %rbx
	call	memcpy@PLT
	movq	%r14, %rdi
	vmovaps	-2528(%rbp), %xmm14
	vmovdqa	-2576(%rbp), %ymm13
	vmovsd	.LC42(%rip), %xmm15
	movq	%r13, -2448(%rbp)
	movq	-2272(%rbp), %rsi
	movq	-2280(%rbp), %r8
	movq	-2480(%rbp), %r14
	jmp	.L134
.L225:
	imulq	$168, %rcx, %rcx
	movl	%eax, %r9d
	imulq	$336, %rdx, %rax
	imulq	$10752, %r9, %r9
	addq	%rcx, %rax
	leaq	cell.2(%rip), %rcx
	addq	%r9, %rax
	addq	%rcx, %rax
	xorb	%r10b, (%rax,%r11)
.L132:
	addq	$24, %rbx
	leaq	-1456(%rbp), %rax
	incq	-1872(%rbp,%r13,8)
	cmpq	%rbx, %rax
	je	.L224
.L134:
	vmovsd	.LC43(%rip), %xmm7
	movq	%rdi, %r9
	addq	%r14, %rdi
	xorq	%r14, %r8
	rorx	$47, %rdi, %rdi
	xorq	%rsi, %r9
	movq	%r8, %rdx
	movq	%r14, %rax
	shrq	$11, %rdi
	xorq	%rsi, %rdx
	xorq	%r9, %rax
	salq	$17, %rsi
	vcvtsi2sdq	%rdi, %xmm14, %xmm4
	vmulsd	%xmm15, %xmm4, %xmm4
	xorq	%r8, %rsi
	rorx	$19, %r9, %r9
	movq	%rax, %rcx
	movq	%rdx, %r8
	movq	%rdx, %r12
	movq	%rdx, %r11
	xorq	%rsi, %rcx
	xorq	%r9, %r8
	salq	$17, %r12
	movq	%rax, %r10
	xorq	%rcx, %r11
	xorq	%r8, %r10
	xorq	%r12, %rcx
	xorl	%r13d, %r13d
	vcomisd	%xmm4, %xmm7
	ja	.L130
	vmovsd	.LC44(%rip), %xmm7
	addq	%r9, %rax
	movq	%rcx, %rsi
	rorx	$19, %r8, %r9
	rorx	$47, %rax, %rax
	movq	%r11, %rdx
	movl	$2, %r13d
	shrq	$11, %rax
	vcvtsi2sdq	%rax, %xmm14, %xmm4
	vmulsd	%xmm15, %xmm4, %xmm4
	movq	%r10, %rax
	vcomisd	%xmm4, %xmm7
	jbe	.L130
	movl	$1, %r13d
.L130:
	xorq	%rax, %rsi
	movq	%rdx, %r11
	movq	%rax, %rdi
	addq	%r9, %rax
	movq	%rsi, %rcx
	xorq	%r9, %r11
	rorx	$47, %rax, %rax
	movl	%r13d, (%rbx)
	xorq	%rdx, %rcx
	salq	$17, %rdx
	xorq	%r11, %rdi
	rorx	$19, %r11, %r11
	movq	%rdx, %r9
	movq	%rcx, %r12
	movq	%rdi, %r10
	leaq	(%rdi,%r11), %rdx
	xorq	%rsi, %r9
	movq	%rcx, %rsi
	salq	$17, %rcx
	xorq	%r11, %r12
	xorq	%rdi, %r9
	movq	%rcx, %r8
	xorq	%r12, %r10
	rorx	$19, %r12, %r12
	xorq	%r9, %rsi
	xorq	%r9, %r8
	movq	%r10, %rdi
	leaq	(%r10,%r12), %rcx
	movq	%rsi, %r11
	xorq	%r10, %r8
	movq	%rsi, %r9
	salq	$17, %rsi
	xorq	%r12, %r11
	xorq	%r8, %rsi
	xorq	%r8, %r9
	rorx	$47, %rdx, %rdx
	xorq	%r11, %rdi
	rorx	$19, %r11, %r11
	movq	%r9, %r10
	movq	%r9, %r8
	xorq	%rdi, %rsi
	movq	%rdi, %r12
	addq	%r11, %rdi
	xorq	%r11, %r10
	rorx	$47, %rdi, %rdi
	rorx	$47, %rcx, %rcx
	xorq	%r10, %r12
	xorq	%rsi, %r8
	movl	%edi, %r11d
	andl	$7, %eax
	andl	$31, %edx
	andl	$1, %ecx
	shrl	$3, %r11d
	rorx	$19, %r10, %r10
	movl	%eax, 4(%rbx)
	movl	%edx, 8(%rbx)
	imulq	$452101821, %r11, %r11
	movl	%ecx, 12(%rbx)
	shrq	$33, %r11
	imull	$152, %r11d, %r14d
	movl	%edi, %r11d
	movq	%r8, %rdi
	subl	%r14d, %r11d
	salq	$17, %r9
	movq	%r12, %r14
	xorq	%r10, %rdi
	xorq	%rsi, %r9
	movq	%r8, %rsi
	salq	$17, %r8
	xorq	%rdi, %r14
	xorq	%r12, %r9
	rorx	$19, %rdi, %rdi
	xorq	%r9, %rsi
	xorq	%r9, %r8
	leaq	(%r12,%r10), %r9
	movl	$2155905153, %r12d
	rorx	$47, %r9, %r9
	movl	%r9d, %r10d
	imulq	%r12, %r10
	shrq	$39, %r10
	leal	1(%r9,%r10), %r10d
	testl	%r13d, %r13d
	je	.L225
	imulq	$336, %rdx, %rdx
	andl	$7, %r11d
	imulq	$10752, %rax, %rax
	addq	%rdx, %rax
	movl	%ecx, %edx
	negq	%rdx
	andl	$168, %edx
	addq	%rdx, %rax
	cmpl	$1, %r13d
	je	.L226
	leaq	160(%rax,%r11), %rax
	leaq	cell.2(%rip), %rcx
	xorb	%r10b, (%rcx,%rax)
	jmp	.L132
.L220:
	movq	%r9, %rcx
	leaq	24+cell.2(%rip), %rdx
	movq	-2280(%rbp), %rbx
	movl	-2384(%rbp), %r9d
	vmovq	%xmm6, 296(%rdx,%r11)
	vmovq	%xmm6, 128(%rdx,%r11)
	movq	%rcx, %rdx
	vmovdqa	-2320(%rbp), %ymm14
	salq	$5, %rdx
	movb	%al, -2288(%rbp)
	leaq	(%r14,%rdx), %rsi
	incl	-2392(%rbp)
	movb	$1, 86016(%rsi,%rbx)
	addq	%rbx, %rdx
	leaq	sqb_item_at(%rip), %rsi
	incl	%r9d
	movl	%r10d, (%rsi,%rdx,4)
	movl	%r9d, 86272(%r14,%rcx,4)
	jmp	.L93
.L175:
	xorl	%eax, %eax
.L123:
	movl	$152, %r8d
	subl	%eax, %r8d
	jmp	.L124
.L176:
	movl	$32, %eax
	jmp	.L123
.L177:
	movl	$64, %eax
	jmp	.L123
.L222:
	movl	$96, %eax
	jmp	.L123
.L226:
	leaq	152(%rax,%r11), %rax
	leaq	cell.2(%rip), %rcx
	xorb	%r10b, (%rcx,%rax)
	jmp	.L132
.L224:
	movq	%rsi, -2272(%rbp)
	vmovaps	%xmm14, -2528(%rbp)
	movq	-2448(%rbp), %r13
	movq	%r14, -2480(%rbp)
	vmovdqa	%ymm13, -2448(%rbp)
	movq	%r8, -2280(%rbp)
	movq	%rdi, %r14
	vzeroupper
	call	sqb_sweep.constprop.1
	addq	%rax, -2384(%rbp)
	leaq	cell.2(%rip), %rax
	vmovaps	-2528(%rbp), %xmm14
	movq	86320(%rax), %rsi
	vmovdqa	-2448(%rbp), %ymm13
	addq	%rsi, -2256(%rbp)
	vmovdqa	.LC37(%rip), %ymm3
	movq	86328(%rax), %rsi
	vmovdqa	.LC36(%rip), %ymm2
	movq	86312(%rax), %rax
	vmovdqa	.LC35(%rip), %ymm1
	vmovdqa	.LC33(%rip), %ymm0
	addq	%rsi, -2320(%rbp)
	addq	%rax, -2192(%rbp)
	movq	-2400(%rbp), %r12
	jmp	.L147
.L135:
	cmpl	$1, %eax
	je	.L227
.L143:
	addq	$24, %r15
	leaq	-1456(%rbp), %rax
	cmpq	%r15, %rax
	je	.L228
.L147:
	movslq	4(%r15), %rdx
	movslq	8(%r15), %rcx
	leaq	action.0(%rip), %rbx
	movl	%edx, %eax
	sall	$5, %eax
	addl	%ecx, %eax
	cltq
	movzbl	(%rbx,%rax), %esi
	movl	(%r15), %eax
	testl	%eax, %eax
	jne	.L135
	movslq	12(%r15), %rax
	cmpl	$1, %esi
	sbbq	$-1, -2160(%rbp)
	testl	%eax, %eax
	jne	.L137
	imulq	$336, %rcx, %rax
	leaq	cell.2(%rip), %rbx
	imulq	$10752, %rdx, %rsi
	addq	%rsi, %rax
	addq	%rbx, %rax
	vmovdqu	(%rax), %ymm4
	vmovdqa	%ymm4, -208(%rbp)
	vmovdqu	32(%rax), %ymm4
	vmovdqa	%ymm4, -176(%rbp)
	vmovdqu	64(%rax), %ymm4
	vmovdqa	%ymm4, -144(%rbp)
	vmovdqu	96(%rax), %ymm4
	vmovdqa	%ymm4, -112(%rbp)
	vmovdqu	120(%rax), %ymm4
	vmovdqu	%ymm4, -88(%rbp)
.L138:
	movq	%rdx, %rax
	leaq	sqb_item_at(%rip), %rbx
	vmovdqa	-2352(%rbp), %ymm7
	vpxor	%xmm6, %xmm6, %xmm6
	salq	$5, %rax
	addq	%rcx, %rax
	movl	(%rbx,%rax,4), %r8d
	movl	%r8d, %eax
	sall	$4, %eax
	addl	%r8d, %eax
	vmovd	%eax, %xmm4
	vpbroadcastb	%xmm4, %ymm4
	vpaddb	%ymm0, %ymm4, %ymm5
	vpxor	%ymm7, %ymm5, %ymm5
	vpcmpeqb	-208(%rbp), %ymm5, %ymm5
	vpcmpeqb	%ymm6, %ymm5, %ymm5
	vptest	%ymm5, %ymm5
	jne	.L182
	vpaddb	%ymm1, %ymm4, %ymm5
	vpxor	%ymm7, %ymm5, %ymm5
	vpcmpeqb	-176(%rbp), %ymm5, %ymm5
	vpcmpeqb	%ymm6, %ymm5, %ymm5
	vptest	%ymm5, %ymm5
	jne	.L183
	vpaddb	%ymm2, %ymm4, %ymm5
	vpxor	%ymm7, %ymm5, %ymm5
	vpcmpeqb	-144(%rbp), %ymm5, %ymm5
	vpcmpeqb	%ymm6, %ymm5, %ymm5
	vptest	%ymm5, %ymm5
	jne	.L184
	vpaddb	%ymm3, %ymm4, %ymm4
	movl	$24, %esi
	movl	$128, %eax
	vpxor	%ymm7, %ymm4, %ymm4
	vpcmpeqb	-112(%rbp), %ymm4, %ymm4
	vpcmpeqb	%ymm6, %ymm4, %ymm4
	vptest	%ymm4, %ymm4
	jne	.L229
.L140:
	movl	%r8d, %ecx
	movl	%eax, %edi
	sall	$4, %ecx
	leaq	-208(%rbp,%rdi), %rdx
	addl	%r8d, %ecx
	movl	$91, %r8d
	imull	%r8d, %eax
	addl	%ecx, %eax
	leal	-1(%rsi), %ecx
	addq	%rdi, %rcx
	leaq	-207(%rbp,%rcx), %rsi
	.p2align 5
	.p2align 4
	.p2align 3
.L142:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	(%rdx), %cl
	jne	.L143
	incq	%rdx
	addl	$91, %eax
	cmpq	%rdx, %rsi
	jne	.L142
	addq	$24, %r15
	leaq	-1456(%rbp), %rax
	incq	-2112(%rbp)
	cmpq	%r15, %rax
	jne	.L147
.L228:
	vmovdqa	-2352(%rbp), %ymm7
	leaq	cell.2(%rip), %r11
	movq	%r12, -2400(%rbp)
	leaq	sqb_item_at(%rip), %rbx
	movq	%r11, %r9
.L148:
	movq	%r9, %rcx
	xorl	%esi, %esi
	vpxor	%xmm6, %xmm6, %xmm6
	movl	$91, %r12d
	.p2align 4
	.p2align 3
.L156:
	cmpb	$0, 86016(%r11,%rsi)
	je	.L151
	cmpl	$-559063315, 164(%rcx)
	je	.L154
	vmovdqu	32(%rcx), %ymm4
	movl	(%rbx,%rsi,4), %edi
	vmovdqu	(%rcx), %ymm8
	movl	%edi, %eax
	sall	$4, %eax
	addl	%edi, %eax
	vmovdqa	%ymm4, -176(%rbp)
	vmovdqu	64(%rcx), %ymm4
	vmovdqa	%ymm8, -208(%rbp)
	vmovdqa	%ymm4, -144(%rbp)
	vmovdqu	96(%rcx), %ymm4
	vmovdqa	%ymm4, -112(%rbp)
	vmovdqu	120(%rcx), %ymm4
	vmovdqu	%ymm4, -88(%rbp)
	vmovd	%eax, %xmm4
	vpbroadcastb	%xmm4, %ymm4
	vpaddb	%ymm0, %ymm4, %ymm5
	vpxor	%ymm7, %ymm5, %ymm5
	vpcmpeqb	%ymm8, %ymm5, %ymm5
	vpcmpeqb	%ymm6, %ymm5, %ymm5
	vptest	%ymm5, %ymm5
	jne	.L186
	vpaddb	%ymm1, %ymm4, %ymm5
	vpxor	%ymm7, %ymm5, %ymm5
	vpcmpeqb	-176(%rbp), %ymm5, %ymm5
	vpcmpeqb	%ymm6, %ymm5, %ymm5
	vptest	%ymm5, %ymm5
	jne	.L187
	vpaddb	%ymm2, %ymm4, %ymm5
	vpxor	%ymm7, %ymm5, %ymm5
	vpcmpeqb	-144(%rbp), %ymm5, %ymm5
	vpcmpeqb	%ymm6, %ymm5, %ymm5
	vptest	%ymm5, %ymm5
	jne	.L188
	vpaddb	%ymm3, %ymm4, %ymm4
	movl	$24, %r8d
	movl	$128, %eax
	vpxor	%ymm7, %ymm4, %ymm4
	vpcmpeqb	-112(%rbp), %ymm4, %ymm4
	vpcmpeqb	%ymm6, %ymm4, %ymm4
	vptest	%ymm4, %ymm4
	jne	.L230
.L153:
	movl	%eax, %r10d
	imull	%r12d, %eax
	movl	%edi, %r15d
	sall	$4, %r15d
	leaq	-208(%rbp,%r10), %rdx
	addl	%r15d, %edi
	addl	%edi, %eax
	leal	-1(%r8), %edi
	addq	%r10, %rdi
	leaq	-207(%rbp,%rdi), %r8
	jmp	.L155
	.p2align 5
	.p2align 4
	.p2align 3
.L231:
	incq	%rdx
	addl	$91, %eax
	cmpq	%rdx, %r8
	je	.L151
.L155:
	movl	%eax, %edi
	xorl	$-91, %edi
	cmpb	%dil, (%rdx)
	je	.L231
.L154:
	incq	%r13
.L151:
	incq	%rsi
	addq	$336, %rcx
	cmpq	$32, %rsi
	jne	.L156
	subq	$-128, %rbx
	leaq	1024+sqb_item_at(%rip), %rax
	addq	$10752, %r9
	addq	$32, %r11
	cmpq	%rbx, %rax
	jne	.L148
	incl	-2392(%rbp)
	movl	-2392(%rbp), %eax
	cmpl	%eax, -2512(%rbp)
	jg	.L158
	movq	-2400(%rbp), %r14
	movq	-2408(%rbp), %rbx
.L100:
	movq	$0, -2024(%rbp)
	movq	$0, -2016(%rbp)
	movq	$0, -2008(%rbp)
	leaq	-2008(%rbp), %rdx
	leaq	-2016(%rbp), %rsi
	leaq	-2024(%rbp), %rdi
	vzeroupper
	call	sq2b_blind_pass.constprop.0
	movq	-2000(%rbp), %r12
	testq	%r12, %r12
	jne	.L159
	movq	-2288(%rbp), %rsi
	vxorpd	%xmm0, %xmm0, %xmm0
	xorl	%edx, %edx
	leaq	.LC45(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	vxorpd	%xmm0, %xmm0, %xmm0
.L160:
	movq	-2224(%rbp), %rsi
	movq	%r12, %rdx
	leaq	.LC46(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	movq	-1992(%rbp), %r12
	testq	%r12, %r12
	jne	.L161
	movq	-2104(%rbp), %rsi
	vxorpd	%xmm0, %xmm0, %xmm0
	xorl	%edx, %edx
	leaq	.LC47(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	vxorpd	%xmm0, %xmm0, %xmm0
.L162:
	movq	-2128(%rbp), %rsi
	movq	%r12, %rdx
	leaq	.LC48(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	movq	-2080(%rbp), %rsi
	leaq	.LC49(%rip), %rdi
	xorl	%eax, %eax
	call	printf@PLT
	movq	-2096(%rbp), %rsi
	leaq	.LC50(%rip), %rdi
	xorl	%eax, %eax
	call	printf@PLT
	vmovapd	-2064(%rbp), %xmm3
	movl	$2000, %edx
	leaq	.LC52(%rip), %rdi
	movq	-2024(%rbp), %rsi
	movl	$1, %eax
	vcvtsi2sdq	%rsi, %xmm3, %xmm0
	vdivsd	.LC51(%rip), %xmm0, %xmm0
	call	printf@PLT
	movq	-2008(%rbp), %rsi
	movl	$2000, %edx
	leaq	.LC53(%rip), %rdi
	xorl	%eax, %eax
	call	printf@PLT
	vmovdqa	-1872(%rbp), %xmm0
	movq	-2160(%rbp), %rsi
	addq	-2112(%rbp), %r14
	addq	-2264(%rbp), %rsi
	vpsrldq	$8, %xmm0, %xmm1
	vpaddq	%xmm1, %xmm0, %xmm0
	vmovq	%xmm0, %r12
	testq	%r12, %r12
	jne	.L163
	vxorpd	%xmm0, %xmm0, %xmm0
	xorl	%edx, %edx
	leaq	.LC54(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	vxorpd	%xmm0, %xmm0, %xmm0
.L164:
	movq	%r12, %rdx
	movq	%r14, %rsi
	leaq	.LC55(%rip), %rdi
	movl	$1, %eax
	call	printf@PLT
	movq	-2384(%rbp), %r8
	movq	%r13, %rdx
	leaq	.LC56(%rip), %rdi
	movq	-2320(%rbp), %rcx
	movq	-2256(%rbp), %rsi
	xorl	%eax, %eax
	call	printf@PLT
	movq	-2192(%rbp), %rsi
	leaq	.LC57(%rip), %rdi
	xorl	%eax, %eax
	addq	-2088(%rbp), %rsi
	call	printf@PLT
	xorl	%eax, %eax
	movq	%rbx, %rsi
	leaq	.LC58(%rip), %rdi
	call	printf@PLT
	movq	-56(%rbp), %rax
	subq	%fs:40, %rax
	jne	.L232
	addq	$2528, %rsp
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
.L227:
	.cfi_restore_state
	cmpl	$1, %esi
	movslq	12(%r15), %rsi
	sbbq	$-1, -2264(%rbp)
	testl	%esi, %esi
	jne	.L145
	imulq	$10752, %rdx, %rsi
	leaq	cell.2(%rip), %rbx
	vmovq	.LC27(%rip), %xmm11
	imulq	$336, %rcx, %rax
	addq	%rsi, %rax
	leaq	(%rbx,%rax), %rsi
	vmovdqu	(%rsi), %ymm4
	vpmovzxbw	%xmm4, %ymm5
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxwd	%xmm5, %ymm6
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxbw	%xmm4, %ymm4
	vpmovzxwd	%xmm5, %ymm5
	vpmovzxwd	%xmm4, %ymm7
	vextracti128	$0x1, %ymm4, %xmm4
	vpaddd	%ymm5, %ymm6, %ymm10
	vpmulld	.LC7(%rip), %ymm5, %ymm5
	vpmovzxwd	%xmm4, %ymm4
	vpmulld	.LC6(%rip), %ymm6, %ymm6
	vpaddd	%ymm7, %ymm10, %ymm10
	vpaddd	%ymm4, %ymm10, %ymm10
	vpmulld	.LC9(%rip), %ymm4, %ymm4
	vpaddd	%ymm5, %ymm6, %ymm6
	vpmulld	.LC8(%rip), %ymm7, %ymm5
	vpaddd	%ymm6, %ymm5, %ymm5
	vpaddd	%ymm5, %ymm4, %ymm6
	vmovdqu	32(%rsi), %ymm4
	vpmovzxbw	%xmm4, %ymm5
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxbw	%xmm4, %ymm4
	vpmovzxwd	%xmm5, %ymm9
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm4, %ymm8
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxwd	%xmm5, %ymm7
	vpmovzxwd	%xmm4, %ymm5
	vpaddd	%ymm10, %ymm9, %ymm4
	vpmulld	.LC10(%rip), %ymm9, %ymm9
	vpaddd	%ymm7, %ymm4, %ymm4
	vpaddd	%ymm4, %ymm8, %ymm4
	vpaddd	%ymm4, %ymm5, %ymm4
	vpmulld	.LC13(%rip), %ymm5, %ymm5
	vpaddd	%ymm6, %ymm9, %ymm9
	vpmulld	.LC11(%rip), %ymm7, %ymm6
	vpmulld	.LC12(%rip), %ymm8, %ymm7
	vpaddd	%ymm9, %ymm6, %ymm6
	vpaddd	%ymm6, %ymm7, %ymm7
	vpaddd	%ymm7, %ymm5, %ymm6
	vmovdqu	64(%rsi), %ymm5
	vpmovzxbw	%xmm5, %ymm7
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm7, %ymm9
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxbw	%xmm5, %ymm5
	vpaddd	%ymm4, %ymm9, %ymm4
	vpmulld	.LC14(%rip), %ymm9, %ymm9
	vpmovzxwd	%xmm7, %ymm7
	vpmovzxwd	%xmm5, %ymm8
	vpaddd	%ymm4, %ymm7, %ymm4
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm5, %ymm5
	vpaddd	%ymm4, %ymm8, %ymm4
	vpaddd	%ymm5, %ymm4, %ymm4
	vpmulld	.LC17(%rip), %ymm5, %ymm5
	vpaddd	%ymm6, %ymm9, %ymm9
	vpmulld	.LC15(%rip), %ymm7, %ymm6
	vpmulld	.LC16(%rip), %ymm8, %ymm7
	vpaddd	%ymm9, %ymm6, %ymm6
	vpaddd	%ymm6, %ymm7, %ymm7
	vpaddd	%ymm7, %ymm5, %ymm6
	vmovdqu	96(%rsi), %ymm5
	xorl	%esi, %esi
	vpmovzxbw	%xmm5, %ymm7
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm7, %ymm9
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxbw	%xmm5, %ymm5
	vpaddd	%ymm4, %ymm9, %ymm4
	vpmulld	.LC18(%rip), %ymm9, %ymm9
	vpmovzxwd	%xmm7, %ymm7
	vpmovzxwd	%xmm5, %ymm8
	vpaddd	%ymm7, %ymm4, %ymm4
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm5, %ymm5
	vpaddd	%ymm8, %ymm4, %ymm4
	vpaddd	%ymm5, %ymm4, %ymm4
	vpmulld	.LC21(%rip), %ymm5, %ymm5
	vpaddd	%ymm6, %ymm9, %ymm9
	vpmulld	.LC19(%rip), %ymm7, %ymm6
	vpmulld	.LC20(%rip), %ymm8, %ymm7
	vpaddd	%ymm9, %ymm6, %ymm6
	vpaddd	%ymm6, %ymm7, %ymm7
	vpaddd	%ymm7, %ymm5, %ymm6
	vmovdqa	128(%rax,%rbx), %xmm5
	vpmovzxbw	%xmm5, %xmm8
	vpsrldq	$8, %xmm5, %xmm5
	vpmovzxbw	%xmm5, %xmm7
	vpmovzxwd	%xmm8, %xmm10
	vpsrldq	$8, %xmm8, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpmovzxwd	%xmm7, %xmm9
	vpaddd	%xmm10, %xmm5, %xmm8
	vpmulld	.LC22(%rip), %xmm10, %xmm10
	vpsrldq	$8, %xmm7, %xmm7
	vpmovzxwd	%xmm7, %xmm7
	vpmulld	.LC23(%rip), %xmm5, %xmm5
	vpaddd	%xmm9, %xmm8, %xmm8
	vpmulld	.LC24(%rip), %xmm9, %xmm9
	vpaddd	%xmm7, %xmm8, %xmm8
	vpmulld	.LC25(%rip), %xmm7, %xmm7
	vpaddd	%xmm4, %xmm8, %xmm8
	vextracti128	$0x1, %ymm4, %xmm4
	vpaddd	%xmm4, %xmm8, %xmm8
	vpaddd	%xmm10, %xmm5, %xmm5
	vpaddd	%xmm9, %xmm5, %xmm5
	vpaddd	%xmm7, %xmm5, %xmm5
	vpaddd	%xmm6, %xmm5, %xmm5
	vextracti128	$0x1, %ymm6, %xmm6
	vpaddd	%xmm6, %xmm5, %xmm5
	vmovq	144(%rax,%rbx), %xmm6
	vpmovzxbw	%xmm6, %xmm4
	vpsrlq	$32, %xmm6, %xmm6
	vpmovzxbw	%xmm6, %xmm6
	vpmovzxwd	%xmm4, %xmm10
	vpsrlq	$32, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpmovzxwd	%xmm6, %xmm9
	vpaddd	%xmm10, %xmm4, %xmm7
	vpmulld	%xmm11, %xmm4, %xmm4
	vmovq	.LC26(%rip), %xmm11
	vpsrlq	$32, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vpaddd	%xmm9, %xmm7, %xmm7
	vpaddd	%xmm6, %xmm7, %xmm7
	vpmulld	%xmm11, %xmm10, %xmm10
	vmovq	.LC28(%rip), %xmm11
	vpaddd	%xmm8, %xmm7, %xmm7
	vpsrldq	$8, %xmm8, %xmm8
	vpaddd	%xmm10, %xmm4, %xmm4
	vpaddd	%xmm8, %xmm7, %xmm7
	vpmulld	%xmm11, %xmm9, %xmm9
	vmovq	.LC29(%rip), %xmm11
	vpaddd	%xmm9, %xmm4, %xmm4
	vpmulld	%xmm11, %xmm6, %xmm6
	vpaddd	%xmm6, %xmm4, %xmm4
	vpaddd	%xmm5, %xmm4, %xmm4
	vpsrldq	$8, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm4, %xmm4
	vpsrlq	$32, %xmm7, %xmm5
	vpaddd	%xmm5, %xmm7, %xmm7
	vpsrlq	$32, %xmm4, %xmm5
	vpaddd	%xmm5, %xmm4, %xmm4
	vmovd	%xmm7, %edi
	vmovd	%xmm4, %eax
.L146:
	imulq	$168, %rsi, %rsi
	leaq	cell.2(%rip), %rbx
	imulq	$10752, %rdx, %rdx
	imulq	$336, %rcx, %rcx
	addq	%rsi, %rdx
	addq	%rcx, %rdx
	addq	%rbx, %rdx
	cmpl	%edi, 152(%rdx)
	jne	.L143
	cmpl	%eax, 156(%rdx)
	sete	%al
	movzbl	%al, %eax
	addq	%rax, %r12
	jmp	.L143
.L145:
	imulq	$336, %rcx, %rdi
	leaq	cell.2(%rip), %rbx
	vmovq	.LC4(%rip), %xmm11
	imulq	$168, %rsi, %rax
	addq	%rdi, %rax
	imulq	$10752, %rdx, %rdi
	addq	%rdi, %rax
	leaq	(%rbx,%rax), %rdi
	vmovq	144(%rax,%rbx), %xmm8
	vpxor	128(%rax,%rbx), %xmm13, %xmm6
	vpxor	(%rdi), %ymm13, %ymm4
	vpxor	32(%rdi), %ymm13, %ymm10
	vpxor	64(%rdi), %ymm13, %ymm7
	vpxor	96(%rdi), %ymm13, %ymm5
	vpxor	%xmm11, %xmm8, %xmm11
	vpmovzxbw	%xmm4, %ymm9
	vextracti128	$0x1, %ymm4, %xmm4
	vmovq	%xmm11, %rax
	vpmovzxwd	%xmm9, %ymm12
	vpmovzxbw	%xmm4, %ymm4
	vextracti128	$0x1, %ymm9, %xmm9
	vpmovzxwd	%xmm4, %ymm11
	vpmovzxwd	%xmm9, %ymm9
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovzxwd	%xmm4, %ymm8
	vpaddd	%ymm9, %ymm12, %ymm4
	vpmulld	.LC7(%rip), %ymm9, %ymm9
	vpmulld	.LC6(%rip), %ymm12, %ymm12
	vpaddd	%ymm4, %ymm11, %ymm4
	vpmulld	.LC8(%rip), %ymm11, %ymm11
	vpaddd	%ymm4, %ymm8, %ymm4
	vpmulld	.LC9(%rip), %ymm8, %ymm8
	vpaddd	%ymm12, %ymm9, %ymm12
	vpaddd	%ymm12, %ymm11, %ymm11
	vpaddd	%ymm11, %ymm8, %ymm9
	vpmovzxbw	%xmm10, %ymm11
	vextracti128	$0x1, %ymm10, %xmm8
	vpmovzxwd	%xmm11, %ymm12
	vextracti128	$0x1, %ymm11, %xmm10
	vpmovzxbw	%xmm8, %ymm8
	vpaddd	%ymm4, %ymm12, %ymm4
	vpmulld	.LC10(%rip), %ymm12, %ymm12
	vpmovzxwd	%xmm10, %ymm10
	vpmovzxwd	%xmm8, %ymm11
	vpaddd	%ymm4, %ymm10, %ymm4
	vextracti128	$0x1, %ymm8, %xmm8
	vpmulld	.LC11(%rip), %ymm10, %ymm10
	vpmovzxwd	%xmm8, %ymm8
	vpaddd	%ymm4, %ymm11, %ymm4
	vpaddd	%ymm4, %ymm8, %ymm4
	vpmulld	.LC13(%rip), %ymm8, %ymm8
	vpaddd	%ymm9, %ymm12, %ymm12
	vpmulld	.LC12(%rip), %ymm11, %ymm9
	vpaddd	%ymm12, %ymm10, %ymm10
	vpaddd	%ymm10, %ymm9, %ymm9
	vpaddd	%ymm9, %ymm8, %ymm10
	vpmovzxbw	%xmm7, %ymm8
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxwd	%xmm8, %ymm11
	vextracti128	$0x1, %ymm8, %xmm8
	vpmovzxbw	%xmm7, %ymm7
	vpmovzxwd	%xmm8, %ymm8
	vpaddd	%ymm4, %ymm11, %ymm4
	vpmulld	.LC14(%rip), %ymm11, %ymm11
	vpmovzxwd	%xmm7, %ymm9
	vpaddd	%ymm8, %ymm4, %ymm4
	vpmulld	.LC15(%rip), %ymm8, %ymm8
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxwd	%xmm7, %ymm7
	vpaddd	%ymm4, %ymm9, %ymm4
	vpaddd	%ymm4, %ymm7, %ymm4
	vpmulld	.LC17(%rip), %ymm7, %ymm7
	vpaddd	%ymm10, %ymm11, %ymm10
	vpaddd	%ymm10, %ymm8, %ymm10
	vpmulld	.LC16(%rip), %ymm9, %ymm8
	vpaddd	%ymm10, %ymm8, %ymm8
	vpaddd	%ymm8, %ymm7, %ymm9
	vpmovzxbw	%xmm5, %ymm7
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovzxwd	%xmm7, %ymm10
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxbw	%xmm5, %ymm5
	vpmovzxwd	%xmm7, %ymm7
	vpaddd	%ymm4, %ymm10, %ymm4
	vpmulld	.LC18(%rip), %ymm10, %ymm10
	vpmovzxwd	%xmm5, %ymm8
	vpaddd	%ymm7, %ymm4, %ymm4
	vextracti128	$0x1, %ymm5, %xmm5
	vpmulld	.LC19(%rip), %ymm7, %ymm7
	vpmovzxwd	%xmm5, %ymm5
	vpaddd	%ymm8, %ymm4, %ymm4
	vpmulld	.LC20(%rip), %ymm8, %ymm8
	vpaddd	%ymm5, %ymm4, %ymm4
	vpmulld	.LC21(%rip), %ymm5, %ymm5
	vpaddd	%ymm9, %ymm10, %ymm9
	vpaddd	%ymm9, %ymm7, %ymm7
	vpaddd	%ymm7, %ymm8, %ymm8
	vpaddd	%ymm8, %ymm5, %ymm7
	vpmovzxbw	%xmm6, %xmm5
	vpsrldq	$8, %xmm6, %xmm6
	vpmovzxbw	%xmm6, %xmm6
	vpmovzxwd	%xmm5, %xmm10
	vpsrldq	$8, %xmm5, %xmm5
	vpmovzxwd	%xmm5, %xmm5
	vpmovzxwd	%xmm6, %xmm9
	vpaddd	%xmm10, %xmm5, %xmm8
	vpmulld	.LC22(%rip), %xmm10, %xmm10
	vpsrldq	$8, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vpmulld	.LC23(%rip), %xmm5, %xmm5
	vpaddd	%xmm9, %xmm8, %xmm8
	vpmulld	.LC24(%rip), %xmm9, %xmm9
	vpaddd	%xmm6, %xmm8, %xmm8
	vpmulld	.LC25(%rip), %xmm6, %xmm6
	vpaddd	%xmm4, %xmm8, %xmm8
	vextracti128	$0x1, %ymm4, %xmm4
	vpaddd	%xmm4, %xmm8, %xmm8
	vpaddd	%xmm10, %xmm5, %xmm5
	vpaddd	%xmm9, %xmm5, %xmm5
	vpaddd	%xmm6, %xmm5, %xmm5
	vpaddd	%xmm7, %xmm5, %xmm5
	vextracti128	$0x1, %ymm7, %xmm7
	vpaddd	%xmm7, %xmm5, %xmm5
	vmovq	%rax, %xmm7
	vpmovzxbw	%xmm7, %xmm4
	vpsrlq	$32, %xmm7, %xmm6
	vpmovzxbw	%xmm6, %xmm6
	vpmovzxwd	%xmm4, %xmm9
	vpsrlq	$32, %xmm4, %xmm4
	vpmovzxwd	%xmm4, %xmm4
	vpmovzxwd	%xmm6, %xmm10
	vpaddd	%xmm9, %xmm4, %xmm7
	vpsrlq	$32, %xmm6, %xmm6
	vpmovzxwd	%xmm6, %xmm6
	vpaddd	%xmm10, %xmm7, %xmm7
	vpaddd	%xmm6, %xmm7, %xmm7
	vpaddd	%xmm8, %xmm7, %xmm7
	vpsrldq	$8, %xmm8, %xmm8
	vpaddd	%xmm8, %xmm7, %xmm8
	vmovq	.LC27(%rip), %xmm7
	vpmulld	%xmm7, %xmm4, %xmm4
	vmovq	.LC26(%rip), %xmm7
	vpmulld	%xmm7, %xmm9, %xmm9
	vmovq	.LC28(%rip), %xmm7
	vpaddd	%xmm9, %xmm4, %xmm4
	vpmulld	%xmm7, %xmm10, %xmm10
	vmovq	.LC29(%rip), %xmm7
	vpaddd	%xmm10, %xmm4, %xmm4
	vpmulld	%xmm7, %xmm6, %xmm6
	vpaddd	%xmm6, %xmm4, %xmm4
	vpaddd	%xmm5, %xmm4, %xmm4
	vpsrldq	$8, %xmm5, %xmm5
	vpaddd	%xmm5, %xmm4, %xmm4
	vpsrlq	$32, %xmm8, %xmm5
	vpaddd	%xmm5, %xmm8, %xmm8
	vpsrlq	$32, %xmm4, %xmm5
	vpaddd	%xmm5, %xmm4, %xmm4
	vmovd	%xmm8, %edi
	vmovd	%xmm4, %eax
	jmp	.L146
.L186:
	xorl	%eax, %eax
.L152:
	movl	$152, %r8d
	subl	%eax, %r8d
	jmp	.L153
.L187:
	movl	$32, %eax
	jmp	.L152
.L188:
	movl	$64, %eax
	jmp	.L152
.L230:
	movl	$96, %eax
	jmp	.L152
.L137:
	imulq	$336, %rcx, %rsi
	leaq	cell.2(%rip), %rbx
	vmovq	.LC4(%rip), %xmm7
	imulq	$168, %rax, %rax
	addq	%rsi, %rax
	imulq	$10752, %rdx, %rsi
	addq	%rsi, %rax
	leaq	(%rbx,%rax), %rsi
	vpxor	(%rsi), %ymm13, %ymm5
	vmovdqa	%ymm5, -208(%rbp)
	vpxor	32(%rsi), %ymm13, %ymm5
	vmovdqa	%ymm5, -176(%rbp)
	vpxor	64(%rsi), %ymm13, %ymm5
	vmovdqa	%ymm5, -144(%rbp)
	vpxor	96(%rsi), %ymm13, %ymm4
	vmovdqa	%ymm4, -112(%rbp)
	vpxor	128(%rax,%rbx), %xmm13, %xmm4
	vmovdqa	%xmm4, -80(%rbp)
	vmovq	144(%rax,%rbx), %xmm4
	vpxor	%xmm7, %xmm4, %xmm4
	vmovq	%xmm4, -64(%rbp)
	jmp	.L138
.L102:
	movl	-2160(%rbp), %r9d
	movl	-2192(%rbp), %r8d
	movl	%r12d, %esi
	vmovdqa	%ymm0, -2512(%rbp)
	imulq	$10752, %rsi, %r10
	incq	-2000(%rbp)
	movq	%rsi, -2384(%rbp)
	imulq	$336, %r9, %rdi
	movq	%r9, -2480(%rbp)
	movq	%r10, -2320(%rbp)
	imulq	$168, %r8, %r8
	movq	%rdi, -2392(%rbp)
	addq	%rdi, %r8
	addq	%r10, %r8
	addq	%r14, %r8
	xorb	%cl, (%r8,%rax)
	vzeroupper
	call	sqb_sweep.constprop.1
	addq	%rax, -2080(%rbp)
	movl	%r12d, %eax
	sall	$5, %eax
	addl	-2160(%rbp), %eax
	leaq	action.0(%rip), %rsi
	movq	86320(%r14), %rcx
	addq	%rcx, -2096(%rbp)
	movq	86312(%r14), %rcx
	addq	%rcx, -2088(%rbp)
	vmovdqa	.LC33(%rip), %ymm2
	vmovdqa	.LC60(%rip), %ymm1
	cmpb	$1, (%rsi,%rax)
	movl	-2192(%rbp), %esi
	sbbq	$-1, -2288(%rbp)
	vmovdqa	.LC35(%rip), %ymm3
	vmovdqa	.LC36(%rip), %ymm4
	vmovdqa	.LC37(%rip), %ymm5
	vmovdqa	-2512(%rbp), %ymm0
	testl	%esi, %esi
	movq	-2320(%rbp), %r10
	movq	-2384(%rbp), %rsi
	movq	-2392(%rbp), %rdi
	movq	-2480(%rbp), %r9
	jne	.L233
	leaq	(%rdi,%r10), %rax
	addq	%r14, %rax
	vmovdqu	(%rax), %ymm6
	vmovdqa	%ymm6, -208(%rbp)
	vmovdqu	32(%rax), %ymm6
	vmovdqa	%ymm6, -176(%rbp)
	vmovdqu	64(%rax), %ymm6
	vmovdqa	%ymm6, -144(%rbp)
	vmovdqu	96(%rax), %ymm6
	vmovdqa	%ymm6, -112(%rbp)
	vmovdqu	120(%rax), %ymm6
	vmovdqu	%ymm6, -88(%rbp)
.L118:
	movq	%rsi, %rax
	movq	-2264(%rbp), %rsi
	salq	$5, %rax
	addq	%r9, %rax
	movl	(%rsi,%rax,4), %esi
	movl	%esi, %eax
	sall	$4, %eax
	addl	%esi, %eax
	vmovd	%eax, %xmm6
	vpbroadcastb	%xmm6, %ymm6
	vpaddb	%ymm2, %ymm6, %ymm7
	vpxor	%ymm1, %ymm7, %ymm7
	vpcmpeqb	-208(%rbp), %ymm7, %ymm7
	vpcmpeqb	%ymm0, %ymm7, %ymm7
	vptest	%ymm7, %ymm7
	jne	.L171
	vpaddb	%ymm3, %ymm6, %ymm7
	vpxor	%ymm1, %ymm7, %ymm7
	vpcmpeqb	-176(%rbp), %ymm7, %ymm7
	vpcmpeqb	%ymm0, %ymm7, %ymm7
	vptest	%ymm7, %ymm7
	jne	.L172
	vpaddb	%ymm4, %ymm6, %ymm7
	vpxor	%ymm1, %ymm7, %ymm7
	vpcmpeqb	-144(%rbp), %ymm7, %ymm7
	vpcmpeqb	%ymm0, %ymm7, %ymm7
	vptest	%ymm7, %ymm7
	jne	.L234
	vpaddb	%ymm5, %ymm6, %ymm6
	movl	$24, %ecx
	movl	$128, %eax
	vpxor	%ymm1, %ymm6, %ymm6
	vpcmpeqb	-112(%rbp), %ymm6, %ymm6
	vpcmpeqb	%ymm0, %ymm6, %ymm6
	vptest	%ymm6, %ymm6
	jne	.L235
.L117:
	movl	%eax, %edi
	imull	%r13d, %eax
	movl	%esi, %r8d
	decl	%ecx
	sall	$4, %r8d
	addq	%rdi, %rcx
	leaq	-208(%rbp,%rdi), %rdx
	addl	%r8d, %esi
	addl	%esi, %eax
	leaq	-207(%rbp,%rcx), %rsi
.L115:
	movl	%eax, %ecx
	xorl	$-91, %ecx
	cmpb	%cl, (%rdx)
	jne	.L104
	incq	%rdx
	addl	$91, %eax
	cmpq	%rdx, %rsi
	jne	.L115
	incq	-2224(%rbp)
	jmp	.L104
.L103:
	leaq	152(%r10,%rax), %rax
	incq	-1992(%rbp)
	vmovdqa	%ymm0, -2480(%rbp)
	movq	%r11, -2392(%rbp)
	movq	%r9, -2384(%rbp)
	movq	%rsi, -2320(%rbp)
	movq	%rdi, -2264(%rbp)
	xorb	%cl, (%r14,%rax)
	vzeroupper
	call	sqb_sweep.constprop.1
	addq	%rax, -2080(%rbp)
	movl	%r12d, %eax
	sall	$5, %eax
	addl	-2160(%rbp), %eax
	movl	-2192(%rbp), %edi
	movq	86320(%r14), %rsi
	addq	%rsi, -2096(%rbp)
	movq	86312(%r14), %rsi
	addq	%rsi, -2088(%rbp)
	leaq	action.0(%rip), %rsi
	vmovdqa	.LC33(%rip), %ymm2
	vmovdqa	.LC60(%rip), %ymm1
	cmpb	$1, (%rsi,%rax)
	sbbq	$-1, -2104(%rbp)
	testl	%edi, %edi
	vmovdqa	.LC35(%rip), %ymm3
	vmovdqa	.LC36(%rip), %ymm4
	vmovdqa	.LC37(%rip), %ymm5
	vmovdqa	-2480(%rbp), %ymm0
	movq	-2264(%rbp), %rdi
	movq	-2320(%rbp), %rsi
	movq	-2384(%rbp), %r9
	movq	-2392(%rbp), %r11
	jne	.L236
	leaq	(%r14,%rdi), %rax
	vmovq	.LC26(%rip), %xmm15
	vmovdqu	(%rax), %ymm7
	vpmovzxbw	%xmm7, %ymm6
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxwd	%xmm6, %ymm10
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxbw	%xmm7, %ymm8
	vpmovzxwd	%xmm6, %ymm7
	vpmovzxwd	%xmm8, %ymm9
	vextracti128	$0x1, %ymm8, %xmm6
	vpaddd	%ymm10, %ymm7, %ymm8
	vpmulld	.LC6(%rip), %ymm10, %ymm10
	vpmovzxwd	%xmm6, %ymm6
	vpmulld	.LC7(%rip), %ymm7, %ymm7
	vpaddd	%ymm8, %ymm9, %ymm8
	vpmulld	.LC8(%rip), %ymm9, %ymm9
	vpaddd	%ymm8, %ymm6, %ymm8
	vpmulld	.LC9(%rip), %ymm6, %ymm6
	vpaddd	%ymm10, %ymm7, %ymm7
	vpaddd	%ymm7, %ymm9, %ymm9
	vpaddd	%ymm9, %ymm6, %ymm7
	vmovdqu	32(%rax), %ymm6
	vpmovzxbw	%xmm6, %ymm9
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm9, %ymm12
	vextracti128	$0x1, %ymm9, %xmm9
	vpmovzxbw	%xmm6, %ymm6
	vpmovzxwd	%xmm9, %ymm10
	vpaddd	%ymm12, %ymm8, %ymm9
	vpmulld	.LC10(%rip), %ymm12, %ymm12
	vpmovzxwd	%xmm6, %ymm11
	vpmulld	.LC11(%rip), %ymm10, %ymm8
	vpaddd	%ymm9, %ymm10, %ymm9
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm6, %ymm6
	vpaddd	%ymm9, %ymm11, %ymm9
	vpaddd	%ymm9, %ymm6, %ymm9
	vpmulld	.LC13(%rip), %ymm6, %ymm6
	vpaddd	%ymm7, %ymm12, %ymm7
	vpaddd	%ymm7, %ymm8, %ymm8
	vpmulld	.LC12(%rip), %ymm11, %ymm7
	vpaddd	%ymm8, %ymm7, %ymm7
	vpaddd	%ymm7, %ymm6, %ymm8
	vmovdqu	64(%rax), %ymm6
	vpmovzxbw	%xmm6, %ymm7
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm7, %ymm12
	vextracti128	$0x1, %ymm7, %xmm7
	vpmovzxbw	%xmm6, %ymm6
	vpmovzxwd	%xmm7, %ymm10
	vpaddd	%ymm12, %ymm9, %ymm7
	vpmulld	.LC14(%rip), %ymm12, %ymm9
	vpmovzxwd	%xmm6, %ymm11
	vpaddd	%ymm7, %ymm10, %ymm7
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm6, %ymm6
	vpaddd	%ymm7, %ymm11, %ymm7
	vpaddd	%ymm7, %ymm6, %ymm7
	vpmulld	.LC17(%rip), %ymm6, %ymm6
	vpaddd	%ymm8, %ymm9, %ymm9
	vpmulld	.LC15(%rip), %ymm10, %ymm8
	vpaddd	%ymm9, %ymm8, %ymm8
	vpmulld	.LC16(%rip), %ymm11, %ymm9
	vpaddd	%ymm8, %ymm9, %ymm9
	vpaddd	%ymm9, %ymm6, %ymm8
	vmovdqu	96(%rax), %ymm6
	leaq	128+cell.2(%rip), %rax
	vpmovzxbw	%xmm6, %ymm9
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm9, %ymm12
	vextracti128	$0x1, %ymm9, %xmm9
	vpmovzxbw	%xmm6, %ymm6
	vpaddd	%ymm7, %ymm12, %ymm10
	vpmulld	.LC18(%rip), %ymm12, %ymm7
	vpmovzxwd	%xmm9, %ymm9
	vpmovzxwd	%xmm6, %ymm11
	vpaddd	%ymm9, %ymm10, %ymm10
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm6, %ymm6
	vpaddd	%ymm11, %ymm10, %ymm10
	vpaddd	%ymm6, %ymm10, %ymm10
	vpmulld	.LC21(%rip), %ymm6, %ymm6
	vpaddd	%ymm8, %ymm7, %ymm7
	vpmulld	.LC19(%rip), %ymm9, %ymm8
	vpaddd	%ymm7, %ymm8, %ymm8
	vpmulld	.LC20(%rip), %ymm11, %ymm7
	vpaddd	%ymm8, %ymm7, %ymm7
	vpaddd	%ymm7, %ymm6, %ymm6
	vmovdqa	(%rax,%rdi), %xmm7
	vpmovzxbw	%xmm7, %xmm9
	vpsrldq	$8, %xmm7, %xmm7
	vpmovzxbw	%xmm7, %xmm8
	vpmovzxwd	%xmm9, %xmm7
	vpsrldq	$8, %xmm9, %xmm9
	vpmovzxwd	%xmm9, %xmm12
	vpmovzxwd	%xmm8, %xmm11
	vpaddd	%xmm12, %xmm7, %xmm9
	vpmulld	.LC23(%rip), %xmm12, %xmm12
	vpsrldq	$8, %xmm8, %xmm8
	vpmovzxwd	%xmm8, %xmm8
	vpmulld	.LC22(%rip), %xmm7, %xmm7
	vpaddd	%xmm11, %xmm9, %xmm9
	vpmulld	.LC24(%rip), %xmm11, %xmm11
	vpaddd	%xmm8, %xmm9, %xmm9
	vpmulld	.LC25(%rip), %xmm8, %xmm8
	vpaddd	%xmm10, %xmm9, %xmm9
	vextracti128	$0x1, %ymm10, %xmm10
	vpaddd	%xmm10, %xmm9, %xmm9
	vpaddd	%xmm12, %xmm7, %xmm7
	vpaddd	%xmm11, %xmm7, %xmm7
	vpaddd	%xmm8, %xmm7, %xmm7
	vmovq	16(%rax,%rdi), %xmm8
	vpaddd	%xmm6, %xmm7, %xmm7
	vextracti128	$0x1, %ymm6, %xmm6
	vpaddd	%xmm6, %xmm7, %xmm7
	vpmovzxbw	%xmm8, %xmm12
	vpsrlq	$32, %xmm8, %xmm8
	vpmovzxbw	%xmm8, %xmm8
	vpmovzxwd	%xmm12, %xmm6
	vpsrlq	$32, %xmm12, %xmm12
	vpmovzxwd	%xmm12, %xmm12
	vpmovzxwd	%xmm8, %xmm11
	vpaddd	%xmm12, %xmm6, %xmm10
	vpmulld	%xmm15, %xmm6, %xmm6
	vmovq	.LC27(%rip), %xmm15
	vpsrlq	$32, %xmm8, %xmm8
	vpmovzxwd	%xmm8, %xmm8
	vpaddd	%xmm11, %xmm10, %xmm10
	vpaddd	%xmm8, %xmm10, %xmm10
	vpmulld	%xmm15, %xmm12, %xmm12
	vmovq	.LC28(%rip), %xmm15
	vpaddd	%xmm9, %xmm10, %xmm10
	vpsrldq	$8, %xmm9, %xmm9
	vpaddd	%xmm12, %xmm6, %xmm6
	vpaddd	%xmm9, %xmm10, %xmm9
	vpmulld	%xmm15, %xmm11, %xmm11
	vmovq	.LC29(%rip), %xmm15
	vpaddd	%xmm11, %xmm6, %xmm6
	vpmulld	%xmm15, %xmm8, %xmm8
	vpaddd	%xmm8, %xmm6, %xmm6
	vpaddd	%xmm7, %xmm6, %xmm6
	vpsrldq	$8, %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vpsrlq	$32, %xmm9, %xmm7
	vpaddd	%xmm7, %xmm9, %xmm9
	vpsrlq	$32, %xmm6, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vmovd	%xmm9, %edx
	vmovd	%xmm6, %eax
.L110:
	imulq	$168, %r11, %rcx
	imulq	$10752, %rsi, %rsi
	imulq	$336, %r9, %r9
	addq	%rsi, %rcx
	addq	%r9, %rcx
	addq	%r14, %rcx
	cmpl	%edx, 152(%rcx)
	jne	.L104
	cmpl	%eax, 156(%rcx)
	sete	%al
	movzbl	%al, %eax
	addq	%rax, -2128(%rbp)
	jmp	.L104
.L236:
	vmovdqa	-2256(%rbp), %ymm7
	leaq	168(%r14,%rdi), %rax
	vmovq	.LC4(%rip), %xmm15
	vpxor	96(%rax), %ymm7, %ymm12
	vpxor	(%rax), %ymm7, %ymm11
	vpxor	32(%rax), %ymm7, %ymm8
	vpxor	64(%rax), %ymm7, %ymm6
	leaq	296+cell.2(%rip), %rax
	vpxor	(%rax,%rdi), %xmm7, %xmm9
	vmovq	16(%rax,%rdi), %xmm7
	vpmovzxbw	%xmm11, %ymm10
	vextracti128	$0x1, %ymm11, %xmm11
	vpmovzxbw	%xmm11, %ymm11
	vpxor	%xmm15, %xmm7, %xmm7
	vpmovzxwd	%xmm10, %ymm15
	vextracti128	$0x1, %ymm10, %xmm10
	vpmovzxwd	%xmm11, %ymm13
	vpmovzxwd	%xmm10, %ymm14
	vextracti128	$0x1, %ymm11, %xmm10
	vpaddd	%ymm14, %ymm15, %ymm11
	vpmulld	.LC7(%rip), %ymm14, %ymm14
	vpmovzxwd	%xmm10, %ymm10
	vpmulld	.LC6(%rip), %ymm15, %ymm15
	vpaddd	%ymm11, %ymm13, %ymm11
	vpmulld	.LC8(%rip), %ymm13, %ymm13
	vpaddd	%ymm11, %ymm10, %ymm11
	vpmulld	.LC9(%rip), %ymm10, %ymm10
	vpaddd	%ymm14, %ymm15, %ymm15
	vpaddd	%ymm15, %ymm13, %ymm13
	vpaddd	%ymm13, %ymm10, %ymm10
	vpmovzxbw	%xmm8, %ymm13
	vextracti128	$0x1, %ymm8, %xmm8
	vpmovzxwd	%xmm13, %ymm15
	vextracti128	$0x1, %ymm13, %xmm13
	vpmovzxbw	%xmm8, %ymm8
	vpmovzxwd	%xmm13, %ymm13
	vpaddd	%ymm15, %ymm11, %ymm11
	vpmulld	.LC10(%rip), %ymm15, %ymm15
	vpmovzxwd	%xmm8, %ymm14
	vpaddd	%ymm11, %ymm13, %ymm11
	vpmulld	.LC11(%rip), %ymm13, %ymm13
	vextracti128	$0x1, %ymm8, %xmm8
	vpmovzxwd	%xmm8, %ymm8
	vpaddd	%ymm11, %ymm14, %ymm11
	vpaddd	%ymm11, %ymm8, %ymm11
	vpmulld	.LC13(%rip), %ymm8, %ymm8
	vpaddd	%ymm10, %ymm15, %ymm10
	vmovq	.LC26(%rip), %xmm15
	vpaddd	%ymm10, %ymm13, %ymm13
	vpmulld	.LC12(%rip), %ymm14, %ymm10
	vpaddd	%ymm13, %ymm10, %ymm10
	vpaddd	%ymm10, %ymm8, %ymm13
	vpmovzxbw	%xmm6, %ymm8
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm8, %ymm14
	vextracti128	$0x1, %ymm8, %xmm8
	vpmovzxbw	%xmm6, %ymm6
	vpmovzxwd	%xmm8, %ymm8
	vpaddd	%ymm14, %ymm11, %ymm11
	vpmulld	.LC14(%rip), %ymm14, %ymm14
	vpmovzxwd	%xmm6, %ymm10
	vpaddd	%ymm11, %ymm8, %ymm11
	vpmulld	.LC15(%rip), %ymm8, %ymm8
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm6, %ymm6
	vpaddd	%ymm11, %ymm10, %ymm11
	vpaddd	%ymm11, %ymm6, %ymm11
	vpmulld	.LC17(%rip), %ymm6, %ymm6
	vpaddd	%ymm13, %ymm14, %ymm13
	vpaddd	%ymm13, %ymm8, %ymm13
	vpmulld	.LC16(%rip), %ymm10, %ymm8
	vpaddd	%ymm13, %ymm8, %ymm8
	vpaddd	%ymm8, %ymm6, %ymm10
	vextracti128	$0x1, %ymm12, %xmm6
	vpmovzxbw	%xmm12, %ymm8
	vpmovzxbw	%xmm6, %ymm6
	vpmovzxwd	%xmm8, %ymm14
	vextracti128	$0x1, %ymm8, %xmm8
	vpmovzxwd	%xmm6, %ymm13
	vextracti128	$0x1, %ymm6, %xmm6
	vpmovzxwd	%xmm8, %ymm12
	vpmovzxwd	%xmm6, %ymm8
	vpaddd	%ymm11, %ymm14, %ymm6
	vpmulld	.LC18(%rip), %ymm14, %ymm11
	vpaddd	%ymm6, %ymm12, %ymm6
	vpaddd	%ymm6, %ymm13, %ymm6
	vpaddd	%ymm6, %ymm8, %ymm6
	vpmulld	.LC21(%rip), %ymm8, %ymm8
	vpaddd	%ymm10, %ymm11, %ymm11
	vpmulld	.LC19(%rip), %ymm12, %ymm10
	vpaddd	%ymm11, %ymm10, %ymm10
	vpmulld	.LC20(%rip), %ymm13, %ymm11
	vpaddd	%ymm10, %ymm11, %ymm11
	vpaddd	%ymm11, %ymm8, %ymm10
	vpmovzxbw	%xmm9, %xmm11
	vpsrldq	$8, %xmm9, %xmm9
	vpmovzxbw	%xmm9, %xmm9
	vpmovzxwd	%xmm11, %xmm8
	vpsrldq	$8, %xmm11, %xmm11
	vpmovzxwd	%xmm11, %xmm13
	vpmovzxwd	%xmm9, %xmm12
	vpsrldq	$8, %xmm9, %xmm9
	vpmovzxwd	%xmm9, %xmm11
	vpaddd	%xmm13, %xmm8, %xmm9
	vpmulld	.LC22(%rip), %xmm8, %xmm8
	vpmulld	.LC23(%rip), %xmm13, %xmm13
	vpaddd	%xmm12, %xmm9, %xmm9
	vpmulld	.LC24(%rip), %xmm12, %xmm12
	vpaddd	%xmm11, %xmm9, %xmm9
	vpmulld	.LC25(%rip), %xmm11, %xmm11
	vpaddd	%xmm6, %xmm9, %xmm9
	vextracti128	$0x1, %ymm6, %xmm6
	vpaddd	%xmm6, %xmm9, %xmm9
	vpaddd	%xmm13, %xmm8, %xmm8
	vpaddd	%xmm12, %xmm8, %xmm8
	vpmovzxbw	%xmm7, %xmm12
	vpsrlq	$32, %xmm7, %xmm7
	vpmovzxbw	%xmm7, %xmm7
	vpaddd	%xmm11, %xmm8, %xmm8
	vpmovzxwd	%xmm12, %xmm6
	vpsrlq	$32, %xmm12, %xmm12
	vpmovzxwd	%xmm12, %xmm12
	vpaddd	%xmm10, %xmm8, %xmm8
	vextracti128	$0x1, %ymm10, %xmm10
	vpmovzxwd	%xmm7, %xmm11
	vpsrlq	$32, %xmm7, %xmm7
	vpaddd	%xmm10, %xmm8, %xmm8
	vpaddd	%xmm12, %xmm6, %xmm10
	vpmovzxwd	%xmm7, %xmm7
	vpmulld	%xmm15, %xmm6, %xmm6
	vmovq	.LC27(%rip), %xmm15
	vpaddd	%xmm11, %xmm10, %xmm10
	vpaddd	%xmm7, %xmm10, %xmm10
	vpmulld	%xmm15, %xmm12, %xmm12
	vmovq	.LC28(%rip), %xmm15
	vpaddd	%xmm9, %xmm10, %xmm10
	vpsrldq	$8, %xmm9, %xmm9
	vpaddd	%xmm12, %xmm6, %xmm6
	vpaddd	%xmm9, %xmm10, %xmm10
	vpmulld	%xmm15, %xmm11, %xmm11
	vmovq	.LC29(%rip), %xmm15
	vpaddd	%xmm11, %xmm6, %xmm6
	vpmulld	%xmm15, %xmm7, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vpsrlq	$32, %xmm10, %xmm7
	vpaddd	%xmm7, %xmm10, %xmm10
	vpaddd	%xmm8, %xmm6, %xmm6
	vpsrldq	$8, %xmm8, %xmm8
	vmovd	%xmm10, %edx
	vpaddd	%xmm8, %xmm6, %xmm6
	vpsrlq	$32, %xmm6, %xmm7
	vpaddd	%xmm7, %xmm6, %xmm6
	vmovd	%xmm6, %eax
	jmp	.L110
.L229:
	movl	$96, %eax
.L139:
	movl	$152, %esi
	subl	%eax, %esi
	jmp	.L140
.L184:
	movl	$64, %eax
	jmp	.L139
.L183:
	movl	$32, %eax
	jmp	.L139
.L182:
	xorl	%eax, %eax
	jmp	.L139
.L163:
	vmovapd	-2064(%rbp), %xmm3
	movq	%r12, %rdx
	leaq	.LC54(%rip), %rdi
	movl	$1, %eax
	vcvtsi2sdq	%r12, %xmm3, %xmm1
	vmovapd	-2064(%rbp), %xmm3
	vmovsd	%xmm1, -2080(%rbp)
	vcvtsi2sdq	%rsi, %xmm3, %xmm0
	vdivsd	%xmm1, %xmm0, %xmm0
	call	printf@PLT
	vmovapd	-2064(%rbp), %xmm2
	vcvtsi2sdq	%r14, %xmm2, %xmm0
	vdivsd	-2080(%rbp), %xmm0, %xmm0
	jmp	.L164
.L233:
	addq	%rdi, %r10
	vmovdqa	-2256(%rbp), %ymm15
	leaq	168(%r14,%r10), %rax
	vpxor	(%rax), %ymm15, %ymm7
	vmovdqa	%ymm7, -208(%rbp)
	vpxor	32(%rax), %ymm15, %ymm7
	vmovdqa	%ymm7, -176(%rbp)
	vpxor	64(%rax), %ymm15, %ymm7
	vmovdqa	%ymm7, -144(%rbp)
	vpxor	96(%rax), %ymm15, %ymm6
	leaq	296+cell.2(%rip), %rax
	vmovq	.LC4(%rip), %xmm7
	vmovdqa	%ymm6, -112(%rbp)
	vpxor	(%rax,%r10), %xmm15, %xmm6
	vmovdqa	%xmm6, -80(%rbp)
	vmovq	16(%rax,%r10), %xmm6
	vpxor	%xmm7, %xmm6, %xmm6
	vmovq	%xmm6, -64(%rbp)
	jmp	.L118
.L161:
	vmovapd	-2064(%rbp), %xmm2
	movq	-2104(%rbp), %rsi
	movq	%r12, %rdx
	leaq	.LC47(%rip), %rdi
	movl	$1, %eax
	vcvtsi2sdq	%r12, %xmm2, %xmm1
	vmovapd	-2064(%rbp), %xmm2
	vmovsd	%xmm1, -2104(%rbp)
	vcvtsi2sdq	%rsi, %xmm2, %xmm0
	vdivsd	%xmm1, %xmm0, %xmm0
	call	printf@PLT
	vmovapd	-2064(%rbp), %xmm3
	vcvtsi2sdq	-2128(%rbp), %xmm3, %xmm0
	vdivsd	-2104(%rbp), %xmm0, %xmm0
	jmp	.L162
.L159:
	vmovapd	-2064(%rbp), %xmm2
	movq	-2288(%rbp), %rsi
	movq	%r12, %rdx
	leaq	.LC45(%rip), %rdi
	movl	$1, %eax
	vcvtsi2sdq	%r12, %xmm2, %xmm1
	vmovapd	-2064(%rbp), %xmm2
	vmovsd	%xmm1, -2352(%rbp)
	vcvtsi2sdq	%rsi, %xmm2, %xmm0
	vdivsd	%xmm1, %xmm0, %xmm0
	call	printf@PLT
	vmovapd	-2064(%rbp), %xmm3
	vcvtsi2sdq	-2224(%rbp), %xmm3, %xmm0
	vdivsd	-2352(%rbp), %xmm0, %xmm0
	jmp	.L160
.L168:
	xorl	%ecx, %ecx
	xorl	%ebx, %ebx
	movq	%rcx, -2128(%rbp)
	movq	%rcx, -2096(%rbp)
	movq	%rcx, -2080(%rbp)
	movq	%rcx, -2088(%rbp)
	movq	%rcx, -2104(%rbp)
	movq	%rcx, -2288(%rbp)
	movq	%rcx, -2224(%rbp)
.L179:
	xorl	%eax, %eax
	xorl	%edx, %edx
	xorl	%r13d, %r13d
	xorl	%r14d, %r14d
	movq	%rax, -2192(%rbp)
	movq	%rax, -2384(%rbp)
	movq	%rax, -2320(%rbp)
	movq	%rax, -2256(%rbp)
	movq	%rdx, -2112(%rbp)
	movq	%rdx, -2264(%rbp)
	movq	%rdx, -2160(%rbp)
	jmp	.L100
.L171:
	xorl	%eax, %eax
.L112:
	movl	$152, %ecx
	subl	%eax, %ecx
	jmp	.L117
.L172:
	movl	$32, %eax
	jmp	.L112
.L234:
	movl	$64, %eax
	jmp	.L112
.L235:
	movl	$96, %eax
	jmp	.L112
.L232:
	call	__stack_chk_fail@PLT
	.cfi_endproc
.LFE23:
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
.LC35:
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
.LC36:
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
.LC37:
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
.LC38:
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
.LC40:
	.byte	48
	.byte	-117
	.byte	-26
	.byte	65
	.byte	-100
	.byte	-9
	.byte	82
	.byte	-83
	.set	.LC41,.LC60
	.align 8
.LC42:
	.long	0
	.long	1017118720
	.align 8
.LC43:
	.long	858993459
	.long	1072378675
	.align 8
.LC44:
	.long	858993459
	.long	1071854387
	.align 8
.LC51:
	.long	0
	.long	1084178432
	.section	.rodata.cst32
	.align 32
.LC60:
	.long	-1515870811
	.long	-1515870811
	.long	-1515870811
	.long	-1515870811
	.long	-1515870811
	.long	-1515870811
	.long	-1515870811
	.long	-1515870811
	.ident	"GCC: (GNU) 16.1.1 20260625"
	.section	.note.GNU-stack,"",@progbits

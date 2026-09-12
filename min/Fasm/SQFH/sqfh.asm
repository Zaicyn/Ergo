; SQFH certification driver in flat assembler (FASM 1.73.x, x86-64 Linux).
; Faithful port of SQFH/sqfh_cert.c (legacy bare-sinusoid path) +
; sqfh_core.h (lock-in, lanes, overflow, spike) + the RNG. Goal:
; byte-identical stdout to sqfh_cert (O6 timing excluded, like SQ5T).
;
; The crux: libm transcendentals (sin/cos/atan2/asin/sqrt/hypot) with
; NO libc. Owned f64 implementations here (Cody-Waite reduction via
; x87-derived 2pi split, Taylor kernels, half-angle atan, sqrtsd for
; sqrt/hypot which is correctly rounded = bit-identical to libm).
; Margins: lane thresholds sit ~14 sigma from noise; %.4f bands need
; 5e-5; owned error ~1e-12. Model-M (exp) paths are NOT used by the
; cert and are not ported.
;
; Internal ABI: args in rdi,rsi,rdx,rcx,r8,r9 (SysV-like), f64 in
; xmm0/xmm1. rbx,rbp,r12-r15 callee-saved. No libc: BSS arena (2 MB
; stream+archive), raw syscalls, own %d/%.6f/%.4f/%.1f/%.2f formatting.
; Assemble: fasm sqfh.asm sqfh

format ELF64 executable 3
entry _start

SQFH_N = 64
NT = 4096

segment readable executable

; -- xorshift64: -> rax (state in rngs, nonzero file init) --
rnd64:
    mov     rax, [rngs]
    mov     rcx, rax
    shl     rcx, 13
    xor     rax, rcx
    mov     rcx, rax
    shr     rcx, 7
    xor     rax, rcx
    mov     rcx, rax
    shl     rcx, 17
    xor     rax, rcx
    mov     [rngs], rax
    ret

; -- frnd: -> xmm0 double in [0,1) --
frnd:
    call    rnd64
    shr     rax, 11
    cvtsi2sd xmm0, rax
    mulsd   xmm0, [INV_2P53]
    ret

; -- wallns: -> rax = CLOCK_MONOTONIC ns (timing only) --
wallns:
    mov     eax, 228
    mov     edi, 1
    lea     rsi, [tsbuf]
    syscall
    mov     rax, [tsbuf]
    mov     rcx, 1000000000
    mul     rcx
    add     rax, [tsbuf+8]
    ret

; -- mkconst: rdi = dst, esi = num, edx = den -> [dst] = num/den --
; Single correctly-rounded division = identical to a C decimal literal.
mkconst:
    cvtsi2sd xmm0, esi
    cvtsi2sd xmm1, edx
    divsd   xmm0, xmm1
    movsd   qword [rdi], xmm0
    ret

; -- init_math: derive PI, reduction consts, decimal consts, Taylor --
init_math:
    push    rbx
    fldpi
    fstp    qword [PI]              ; correctly rounded = M_PI
    movsd   xmm0, [PI]
    addsd   xmm0, xmm0              ; 2*PI exact
    movsd   qword [TWO_PI_HI], xmm0
    fldpi
    fadd    st0, st0                ; 2pi 80-bit
    fsub    qword [TWO_PI_HI]
    fstp    qword [TWO_PI_LO]       ; exact low part
    fld1
    fldpi
    fadd    st0, st0
    fdivp                           ; 1/(2pi) 80-bit
    fstp    qword [INV_2PI]         ; correctly rounded
    ; decimal consts (num/den)
    lea     rdi, [C_002]
    mov     esi, 2
    mov     edx, 100
    call    mkconst
    lea     rdi, [C_001]
    mov     esi, 1
    mov     edx, 100
    call    mkconst
    lea     rdi, [C_005]
    mov     esi, 5
    mov     edx, 100
    call    mkconst
    lea     rdi, [C_0098]
    mov     esi, 98
    mov     edx, 100
    call    mkconst
    lea     rdi, [C_1E12]
    mov     eax, 1
    cvtsi2sd xmm0, eax
    mov     rax, 1000000000000
    cvtsi2sd xmm1, rax
    divsd   xmm0, xmm1
    movsd   qword [rdi], xmm0
    lea     rdi, [C_08]
    mov     esi, 8
    mov     edx, 10
    call    mkconst
    lea     rdi, [C_03]
    mov     esi, 3
    mov     edx, 10
    call    mkconst
    lea     rdi, [C_27]
    mov     esi, 27
    mov     edx, 10
    call    mkconst
    lea     rdi, [C_16]
    mov     esi, 16
    mov     edx, 10
    call    mkconst
    lea     rdi, [C_004]
    mov     esi, 4
    mov     edx, 10
    call    mkconst
    lea     rdi, [C_0005]
    mov     esi, 5
    mov     edx, 1000
    call    mkconst
    lea     rdi, [C_025]
    mov     esi, 25
    mov     edx, 100
    call    mkconst
    ; TRUE_K = ((2*PI)*3)/64 ; PHI_STEP = TRUE_K*64 (C order)
    movsd   xmm0, [PI]
    addsd   xmm0, xmm0
    movsd   xmm1, [THREE]
    mulsd   xmm0, xmm1
    movsd   xmm1, [SIXTY4]
    divsd   xmm0, xmm1
    movsd   qword [TRUE_K], xmm0
    mulsd   xmm0, xmm1              ; *64 exact
    movsd   qword [PHI_STEP], xmm0
    ; PI_HALF = PI/2 ; 2DIVPI = 2/PI
    movsd   xmm0, [PI]
    movsd   xmm1, [TWO]
    divsd   xmm0, xmm1
    movsd   qword [PI_HALF], xmm0
    movsd   xmm0, [TWO]
    divsd   xmm0, [PI]
    movsd   qword [C_2DIVPI], xmm0
    ; sin Taylor coeffs: s=1; k=1..8: s = -s/((2k)*(2k+1))
    movsd   xmm0, [ONE]
    mov     r8d, 1
.scloop:
    cmp     r8d, 9
    jae     .ccoeffs
    mov     eax, r8d
    add     eax, eax                ; 2k
    lea     ecx, [rax+1]            ; 2k+1
    imul    eax, ecx                ; d
    cvtsi2sd xmm1, eax
    divsd   xmm0, xmm1
    movdqu  xmm2, dqword [SIGNBIT]   ; unaligned-safe (seg base arbitrary)
    xorpd   xmm0, xmm2
    mov     eax, r8d
    dec     eax
    movsd   qword [SIN_C+rax*8], xmm0
    inc     r8d
    jmp     .scloop
.ccoeffs:
    ; cos coeffs: c=1; k=1..8: c = -c/((2k-1)*(2k))
    movsd   xmm0, [ONE]
    mov     r8d, 1
.ccloop:
    cmp     r8d, 9
    jae     .acoeffs
    mov     eax, r8d
    add     eax, eax
    dec     eax                     ; 2k-1
    mov     ecx, r8d
    add     ecx, ecx                ; 2k
    imul    eax, ecx                ; d
    cvtsi2sd xmm1, eax
    divsd   xmm0, xmm1
    movdqu  xmm2, dqword [SIGNBIT]   ; unaligned-safe (seg base arbitrary)
    xorpd   xmm0, xmm2
    mov     eax, r8d
    dec     eax
    movsd   qword [COS_C+rax*8], xmm0
    inc     r8d
    jmp     .ccloop
.acoeffs:
    ; atan coeffs: e=-1/3; e = -e*(2n+3)/(2n+5), 9 terms
    mov     eax, 1
    cvtsi2sd xmm0, eax
    mov     eax, 3
    cvtsi2sd xmm1, eax
    divsd   xmm0, xmm1
    movdqu  xmm2, dqword [SIGNBIT]   ; unaligned-safe (seg base arbitrary)
    xorpd   xmm0, xmm2         ; -1/3
    mov     r8d, 0
.aloop:
    cmp     r8d, 9
    jae     .done
    movsd   qword [ATAN_C+r8*8], xmm0
    mov     eax, r8d
    add     eax, eax
    add     eax, 3                  ; 2n+3
    cvtsi2sd xmm1, eax
    mulsd   xmm0, xmm1
    mov     eax, r8d
    add     eax, eax
    add     eax, 5                  ; 2n+5
    cvtsi2sd xmm1, eax
    divsd   xmm0, xmm1
    movdqu  xmm2, dqword [SIGNBIT]   ; unaligned-safe (seg base arbitrary)
    xorpd   xmm0, xmm2
    inc     r8d
    jmp     .aloop
.done:
    pop     rbx
    ret

; -- my_sincos: xmm0 = x -> xmm0 = sin, xmm1 = cos (owned, ~1e-15) --
; Cody-Waite mod 2pi, then quadrant fold mod pi/2. Clobbers rax,rcx,rdx.
my_sincos:
    push    rbx
    movapd  xmm2, xmm0              ; x
    mulsd   xmm0, [INV_2PI]
    cvtsd2si rax, xmm0              ; n = rint (MXCSR nearest-even)
    cvtsi2sd xmm1, rax              ; n exact
    mulsd   xmm1, [TWO_PI_HI]       ; n*HI
    movsd   xmm0, xmm2
    subsd   xmm0, xmm1              ; x - n*HI
    cvtsi2sd xmm1, rax
    mulsd   xmm1, [TWO_PI_LO]       ; n*LO
    subsd   xmm0, xmm1              ; r in [-pi,pi] (Cody-Waite)
    ; second reduction: k = rint(r * 2/pi), s = r - k*(pi/2), |s|<=pi/4
    movapd  xmm3, xmm0              ; r
    mulsd   xmm0, [C_2DIVPI]
    cvtsd2si rax, xmm0              ; k in [-2,2]
    mov     ecx, eax
    and     ecx, 3                  ; k mod 4 (twos-complement & is exact)
    cvtsi2sd xmm0, rax              ; k exact
    mulsd   xmm0, [PI_HALF]         ; k*pi/2
    subsd   xmm3, xmm0
    movapd  xmm0, xmm3              ; s
    ; sin kernel: s*(1 + u*Horner(SIN_C)), u = s^2
    movapd  xmm2, xmm0
    mulsd   xmm2, xmm2              ; u (survives below: read-only)
    movsd   xmm4, [SIN_C+56]        ; c8
    mulsd   xmm4, xmm2
    addsd   xmm4, [SIN_C+48]
    mulsd   xmm4, xmm2
    addsd   xmm4, [SIN_C+40]
    mulsd   xmm4, xmm2
    addsd   xmm4, [SIN_C+32]
    mulsd   xmm4, xmm2
    addsd   xmm4, [SIN_C+24]
    mulsd   xmm4, xmm2
    addsd   xmm4, [SIN_C+16]
    mulsd   xmm4, xmm2
    addsd   xmm4, [SIN_C+8]
    mulsd   xmm4, xmm2
    addsd   xmm4, [SIN_C+0]
    mulsd   xmm4, xmm2
    addsd   xmm4, [ONE]
    mulsd   xmm0, xmm4              ; sin(s)
    ; cos kernel: 1 + u*Horner(COS_C)
    movapd  xmm1, xmm3              ; s
    movsd   xmm4, [COS_C+56]        ; d8
    mulsd   xmm4, xmm2
    addsd   xmm4, [COS_C+48]
    mulsd   xmm4, xmm2
    addsd   xmm4, [COS_C+40]
    mulsd   xmm4, xmm2
    addsd   xmm4, [COS_C+32]
    mulsd   xmm4, xmm2
    addsd   xmm4, [COS_C+24]
    mulsd   xmm4, xmm2
    addsd   xmm4, [COS_C+16]
    mulsd   xmm4, xmm2
    addsd   xmm4, [COS_C+8]
    mulsd   xmm4, xmm2
    addsd   xmm4, [COS_C+0]
    mulsd   xmm4, xmm2
    addsd   xmm4, [ONE]
    movapd  xmm1, xmm4              ; cos(s)
    ; quadrant select on k01: s = (k&1)? c : s ; c = (k&1)? s : c
    test    ecx, 1
    jz      .noswap
    xorpd   xmm0, xmm1
    xorpd   xmm1, xmm0
    xorpd   xmm0, xmm1
.noswap:
    mov     eax, 0x0C               ; sin neg quadrants 2,3
    bt      eax, ecx
    jnc     .spos
    movdqu  xmm2, dqword [SIGNBIT]
    xorpd   xmm0, xmm2
.spos:
    mov     eax, 0x06               ; cos neg quadrants 1,2
    bt      eax, ecx
    jnc     .cpos
    movdqu  xmm2, dqword [SIGNBIT]
    xorpd   xmm1, xmm2
.cpos:
    pop     rbx
    ret

; -- my_sin: xmm0 -> xmm0 --
my_sin:
    call    my_sincos
    ret                             ; sin in xmm0 (cos in xmm1 dropped)

; -- my_cos: xmm0 -> xmm0 --
my_cos:
    call    my_sincos
    movapd  xmm0, xmm1
    ret

; -- atan01: xmm0 = t >= 0 -> xmm0 = atan(t) --
; 2 half-angle steps + 9-term Taylor.
atan01:
    push    rbx
    movsd   xmm1, [ONE]
    ucomisd xmm0, xmm1
    jbe     .reduce                 ; t <= 1
    divsd   xmm1, xmm0              ; 1/t
    movapd  xmm0, xmm1
    call    atan01                  ; atan(1/t), terminates (arg < 1)
    movsd   xmm1, [PI_HALF]
    subsd   xmm1, xmm0
    movapd  xmm0, xmm1              ; pi/2 - atan(1/t)
    pop     rbx
    ret
.reduce:
    ; w = t/(1+sqrt(1+t^2)) twice
    movapd  xmm1, xmm0
    mulsd   xmm1, xmm1
    addsd   xmm1, [ONE]
    sqrtsd  xmm1, xmm1
    addsd   xmm1, [ONE]
    divsd   xmm0, xmm1
    movapd  xmm1, xmm0
    mulsd   xmm1, xmm1
    addsd   xmm1, [ONE]
    sqrtsd  xmm1, xmm1
    addsd   xmm1, [ONE]
    divsd   xmm0, xmm1              ; w2
    ; s = w*(1 + u*Horner(ATAN_C)), u = w^2
    movapd  xmm1, xmm0
    mulsd   xmm1, xmm1              ; u
    movsd   xmm2, [ATAN_C+64]       ; e8
    mulsd   xmm2, xmm1
    addsd   xmm2, [ATAN_C+56]
    mulsd   xmm2, xmm1
    addsd   xmm2, [ATAN_C+48]
    mulsd   xmm2, xmm1
    addsd   xmm2, [ATAN_C+40]
    mulsd   xmm2, xmm1
    addsd   xmm2, [ATAN_C+32]
    mulsd   xmm2, xmm1
    addsd   xmm2, [ATAN_C+24]
    mulsd   xmm2, xmm1
    addsd   xmm2, [ATAN_C+16]
    mulsd   xmm2, xmm1
    addsd   xmm2, [ATAN_C+8]
    mulsd   xmm2, xmm1
    addsd   xmm2, [ATAN_C+0]
    mulsd   xmm2, xmm1
    addsd   xmm2, [ONE]
    mulsd   xmm0, xmm2
    addsd   xmm0, xmm0              ; x2 (two halvings)
    addsd   xmm0, xmm0
    pop     rbx
    ret

; -- my_atan2: xmm0 = y, xmm1 = x -> xmm0 = atan2(y,x) --
my_atan2:
    push    rbx
    movq    rax, xmm0
    movq    rbx, xmm1
    shr     rax, 63                 ; sy
    shr     rbx, 63                 ; sx
    movapd  xmm2, xmm0
    movdqu  xmm4, dqword [ABS2]
    andpd   xmm2, xmm4
    movapd  xmm3, xmm1
    andpd   xmm3, xmm4              ; ay, ax
    xorpd   xmm4, xmm4
    ucomisd xmm3, xmm4              ; ax == 0?
    jne     .nonzero_x
    ucomisd xmm2, xmm4              ; ay == 0?
    jne     .xzero
    xorpd   xmm0, xmm0              ; (0,0) -> 0 (never hit on data)
    pop     rbx
    ret
.xzero:
    movsd   xmm0, [PI_HALF]
    test    rax, rax                ; sy
    jz      .xzdone
    movdqu  xmm2, dqword [SIGNBIT]   ; unaligned-safe (seg base arbitrary)
    xorpd   xmm0, xmm2
.xzdone:
    pop     rbx
    ret
.nonzero_x:
    movsd   xmm0, xmm2
    divsd   xmm0, xmm3              ; t = ay/ax
    call    atan01                  ; a
    shl     rbx, 1
    or      rbx, rax                ; q = (sx<<1)|sy
    cmp     rbx, 0
    je      .adone                  ; (+,+): +a
    cmp     rbx, 1
    je      .aneg                   ; (+,-): -a
    movsd   xmm1, [PI]
    subsd   xmm1, xmm0              ; pi - a
    movapd  xmm0, xmm1
    cmp     rbx, 2
    je      .adone                  ; (-,+): pi-a
    movdqu  xmm2, dqword [SIGNBIT]   ; unaligned-safe (seg base arbitrary)
    xorpd   xmm0, xmm2         ; (-,-): a-pi
    jmp     .adone
.aneg:
    movdqu  xmm2, dqword [SIGNBIT]   ; unaligned-safe (seg base arbitrary)
    xorpd   xmm0, xmm2
.adone:
    pop     rbx
    ret

; -- my_asin: xmm0 = r -> xmm0 = asin(r) = atan2(r, sqrt(1-r^2)) --
my_asin:
    push    rbx
    movapd  xmm2, xmm0
    mulsd   xmm2, xmm2              ; r^2
    movsd   xmm1, [ONE]
    subsd   xmm1, xmm2              ; 1-r^2
    sqrtsd  xmm1, xmm1              ; x (correctly rounded = libm)
    call    my_atan2                ; xmm0=r, xmm1=x
    pop     rbx
    ret

; -- fhypot: xmm0 = x, xmm1 = y -> xmm0 = sqrt(x^2+y^2) --
fhypot:
    mulsd   xmm0, xmm0
    mulsd   xmm1, xmm1
    addsd   xmm0, xmm1
    sqrtsd  xmm0, xmm0
    ret

segment readable

ONE dq 0x3FF0000000000000
TWO dq 0x4000000000000000
HALF dq 0x3FE0000000000000
FIFTY dq 0x4049000000000000
THREE dq 0x4008000000000000
SIXTY4 dq 0x4050000000000000
C_1E9 dq 0x41CDCD6500000000
TEN dq 0x4024000000000000
HUNDRED dq 0x4059000000000000
SIGNBIT dq 0x8000000000000000
INV_2P53 dq 0x3CA0000000000000
ABS2 dq 0x7FFFFFFFFFFFFFFF, 0x7FFFFFFFFFFFFFFF

segment readable writeable

rngs     dq 0x51F15EED1234567
PI       rq 1
TWO_PI_HI rq 1
TWO_PI_LO rq 1
INV_2PI  rq 1
TRUE_K   rq 1
PHI_STEP rq 1
C_002    rq 1
C_001    rq 1
C_005    rq 1
C_0098   rq 1
C_1E12   rq 1
C_08     rq 1
C_03     rq 1
C_27     rq 1
C_16     rq 1
C_004    rq 1
C_0005   rq 1
C_025    rq 1
C_2DIVPI rq 1
PI_HALF  rq 1
SIN_C    rq 8
COS_C    rq 8
ATAN_C   rq 9
tsbuf    rq 2

; ============ stream + handoff state ============
stream    rb 1048576               ; 4096 x 64 f32
archive   rb 1048576
lane_log  rb 4096
truth     rb 4096
slip_true rb 16384                 ; 4096 f32
cpu       rb 208
probe     rb 208
slip_rec  rq 2
th_tmp   rb 32
numbuf   rb 32
fdigits  rb 8
outbuf   rb 4096
outcur   rq 1
m_ep_open rd 1
m_ep_close rd 1
m_spike_tile rd 1
m_spike_idx rd 1
m_prev_open rq 1
m_prev_close rq 1
m_nslip rd 1
m_tns rq 1
lk_I     rq 1
lk_Q     rq 1
lk_dphi  rq 1
lk_resid rq 1
lk_E     rq 1
lk_share rq 1
lk_k     rq 1
lk_phi   rq 1
lk_scale rq 1
lk_tmp   rb 24
lk_afit  rq 1
rec_mid  rq 1
lk_cd    rq 1
lk_sd    rq 1
lk_c     rq 1
lk_s     rq 1
rec_lo   rq 1
rec_hi   rq 1
rec_M    rq 1
rec_A    rq 1

; cpu field offsets (sqfh_t layout)
O_SCALE = 0
O_A = 8
O_K = 16
O_PHI = 24
O_EPISODE = 80
O_EP_PHI0 = 88
O_EP_USED = 96
O_TILES = 104
O_LINEAR = 112
O_SLIPS = 120
O_SHEAR = 128
O_SPIKES = 136
O_OVERFLOWS = 144
O_EP_OPEN = 152
O_EP_CLOSE = 160
O_LAST_LANE = 168
O_LAST_DPHI = 176
O_LAST_SHARE = 184
O_LAST_SIDX = 192
O_LAST_EXCESS = 200

segment readable executable

; -- gen_stream: build synthetic GPU stream + truth (cert main loop 1) --
gen_stream:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    xor     r12d, r12d              ; slip_cum bits = +0.0
    xor     r13d, r13d              ; t
.tloop:
    cmp     r13d, 4096
    jae     .done
    cmp     r13d, 1000
    jne     .nslipa
    movq    xmm0, r12
    addsd   xmm0, [C_004]           ; +0.40
    movq    r12, xmm0
.nslipa:
    cmp     r13d, 2500
    jne     .nslipb
    movq    xmm0, r12
    subsd   xmm0, [C_025]           ; -0.25
    movq    r12, xmm0
.nslipb:
    movq    xmm0, r12
    cvtsd2ss xmm0, xmm0
    mov     eax, r13d
    movss   dword [slip_true+rax*4], xmm0 ; slip_true[t]
    ; shear/ovfl flags
    xor     r14d, r14d              ; shear = 0
    cmp     r13d, 1500
    jb      .noshear
    cmp     r13d, 1511
    ja      .noshear
    mov     r14d, 1
.noshear:
    xor     r15d, r15d              ; ovfl = 0
    cmp     r13d, 2000
    jb      .noovfl
    cmp     r13d, 2011
    ja      .noovfl
    mov     r15d, 1
.noovfl:
    mov     eax, r14d
    shl     eax, 1                  ; shear ? 2 : 0
    test    r15d, r15d
    jz      .truth0
    mov     eax, 4                  ; ovfl (shear impossible here: ranges disjoint)
.truth0:
    mov     ecx, r13d
    mov     [truth+rcx], al         ; truth[t]
    ; samples
    mov     r10d, r13d
    shl     r10d, 6                 ; t*64 base
    xor     r11d, r11d              ; i
.sloop:
    cmp     r11d, 64
    jae     .snext
    mov     eax, r10d
    add     eax, r11d               ; t*64+i
    cvtsi2sd xmm0, eax
    mulsd   xmm0, [TRUE_K]
    movq    xmm1, r12
    addsd   xmm0, xmm1              ; th
    movsd   qword [th_tmp], xmm0
    call    my_sin
    movsd   qword [th_tmp+8], xmm0        ; v = sin(th) (TRUE_A=1 exact no-op)
    test    r15d, r15d
    jz      .shear
    ; overflow: v = 1.6*sin(th), railed at +-1.0
    movsd   xmm0, qword [th_tmp]
    call    my_sin
    mulsd   xmm0, [C_16]
    movsd   qword [th_tmp+8], xmm0
    movsd   xmm0, qword [th_tmp+8]
    movsd   xmm1, [ONE]
    ucomisd xmm0, xmm1
    jbe     .ovlo
    movsd   qword [th_tmp+8], xmm1
    jmp     .spike
.ovlo:
    xorpd   xmm1, xmm1
    subsd   xmm1, [ONE]             ; -1.0
    movsd   xmm0, qword [th_tmp+8]
    ucomisd xmm0, xmm1
    jae     .spike
    movsd   qword [th_tmp+8], xmm1
    jmp     .spike
.shear:
    test    r14d, r14d
    jz      .spike
    ; env = sin(pi*i/64)
    cvtsi2sd xmm0, r11d
    mulsd   xmm0, [PI]
    divsd   xmm0, [SIXTY4]
    call    my_sin
    movsd   qword [th_tmp+16], xmm0       ; env
    ; termA = 0.8*sin(2.7*th+3.0*slip)*env
    movsd   xmm0, qword [th_tmp]
    mulsd   xmm0, [C_27]
    movq    xmm1, r12
    mulsd   xmm1, [THREE]
    addsd   xmm0, xmm1
    call    my_sin
    mulsd   xmm0, [C_08]
    mulsd   xmm0, qword [th_tmp+16]
    movsd   qword [th_tmp+24], xmm0       ; termA
    ; v += termA + 0.3*sin(0.5*th)*env
    movsd   xmm0, qword [th_tmp]
    mulsd   xmm0, [HALF]
    call    my_sin
    mulsd   xmm0, [C_03]
    mulsd   xmm0, qword [th_tmp+16]
    addsd   xmm0, qword [th_tmp+24]
    movsd   xmm1, qword [th_tmp+8]
    addsd   xmm1, xmm0
    movsd   qword [th_tmp+8], xmm1
.spike:
    cmp     r13d, 3000
    jne     .noise
    cmp     r11d, 17
    jne     .noise
    movsd   xmm0, qword [th_tmp+8]
    mulsd   xmm0, [FIFTY]
    movsd   qword [th_tmp+8], xmm0
.noise:
    ; n = (frnd*4 left-assoc - 2.0) * 0.005
    call    frnd
    movsd   qword [th_tmp+16], xmm0       ; reuse spill (env dead)
    call    frnd
    addsd   xmm0, qword [th_tmp+16]
    movsd   qword [th_tmp+16], xmm0
    call    frnd
    addsd   xmm0, qword [th_tmp+16]
    movsd   qword [th_tmp+16], xmm0
    call    frnd
    addsd   xmm0, qword [th_tmp+16]
    movsd   xmm1, [TWO]
    subsd   xmm0, xmm1
    mulsd   xmm0, [C_0005]
    addsd   xmm0, qword [th_tmp+8]        ; v + n
    cvtsd2ss xmm0, xmm0
    mov     eax, r10d
    add     eax, r11d               ; t*64+i
    movss   dword [stream+rax*4], xmm0
    inc     r11d
    jmp     .sloop
.snext:
    inc     r13d
    jmp     .tloop
.done:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbp
    pop     rbx
    ret

; ============ handoff core (legacy path) ============

; -- sqfh_init: rdi = cpu, xmm0 = scale, xmm1 = A, xmm2 = k, xmm3 = phi --
sqfh_init:
    push    rcx
    push    rdi
    xor     eax, eax
    mov     ecx, 26
    rep     stosq                   ; memset 208 (advances rdi: restored below)
    pop     rdi
    pop     rcx
    movsd   qword [rdi+O_SCALE], xmm0
    movsd   qword [rdi+O_A], xmm1
    movsd   qword [rdi+O_K], xmm2
    movsd   qword [rdi+O_PHI], xmm3
    ret

; -- lockin: rdi = w(f32x64), xmm0 = k, xmm1 = phi, xmm2 = scale --
; Outs to lk_* BSS. Exact C op order (separate mul/add, no FMA in build).
sqfh_lockin:
    push    rbx
    push    r12
    mov     rbx, rdi                ; w (survives trig calls)
    movsd   qword [lk_k], xmm0
    movsd   qword [lk_phi], xmm1
    movsd   qword [lk_scale], xmm2
    mulsd   xmm0, xmm2              ; k*scale
    call    my_sincos               ; xmm0=sd, xmm1=cd (one reduction)
    movsd   qword [lk_sd], xmm0
    movsd   qword [lk_cd], xmm1
    movsd   xmm0, [lk_phi]
    call    my_sincos               ; xmm0=s, xmm1=c
    movsd   qword [lk_s], xmm0
    movsd   qword [lk_c], xmm1
    movsd   xmm4, [lk_c]
    movsd   xmm5, [lk_s]
    movsd   xmm6, [lk_cd]
    movsd   xmm7, [lk_sd]
    xorpd   xmm8, xmm8              ; sI
    xorpd   xmm9, xmm9              ; sQ
    xorpd   xmm10, xmm10            ; sE
    xor     ecx, ecx                ; i
.lkloop:
    cmp     ecx, 64
    jae     .lkdone
    movss   xmm0, [rbx+rcx*4]
    cvtss2sd xmm0, xmm0             ; w[i]
    movapd  xmm1, xmm0
    mulsd   xmm1, xmm4              ; w*c
    addsd   xmm8, xmm1              ; sI
    mulsd   xmm0, xmm5              ; w*s
    addsd   xmm9, xmm0              ; sQ
    movss   xmm0, [rbx+rcx*4]
    cvtss2sd xmm0, xmm0
    mulsd   xmm0, xmm0              ; w*w
    addsd   xmm10, xmm0             ; sE
    movapd  xmm0, xmm4
    mulsd   xmm0, xmm6              ; c*cd
    movapd  xmm1, xmm5
    mulsd   xmm1, xmm7              ; s*sd
    subsd   xmm0, xmm1              ; cn
    mulsd   xmm5, xmm6              ; s*cd
    mulsd   xmm4, xmm7              ; c*sd
    addsd   xmm5, xmm4              ; s'
    movapd  xmm4, xmm0              ; c'
    inc     ecx
    jmp     .lkloop
.lkdone:
    movsd   xmm0, xmm8
    mulsd   xmm0, xmm8              ; sI^2
    movsd   xmm1, xmm9
    mulsd   xmm1, xmm9              ; sQ^2
    addsd   xmm0, xmm1
    movsd   xmm1, [TWO]
    mulsd   xmm0, xmm1              ; 2*(..)
    movsd   xmm1, [SIXTY4]
    divsd   xmm0, xmm1              ; explained
    movsd   qword [lk_tmp], xmm0          ; spill (atan2 call)
    movsd   xmm0, xmm8              ; sI
    movsd   xmm1, xmm9              ; sQ
    call    my_atan2                ; dphi
    movsd   qword [lk_dphi], xmm0
    movsd   xmm0, qword [lk_tmp]
    movsd   xmm1, xmm10             ; sE
    subsd   xmm1, xmm0              ; resid = sE - explained
    movsd   qword [lk_resid], xmm1
    movsd   qword [lk_E], xmm10
    movsd   qword [lk_I], xmm8
    movsd   qword [lk_Q], xmm9
    pop     r12
    pop     rbx
    ret

; -- spike_localize: rdi=w, xmm0=Afit, xmm1=k, xmm2=phi_eff, xmm3=scale --
; -> eax = worst idx, share to lk_share.
sqfh_spike_localize:
    push    rbx
    push    r12
    mov     rbx, rdi                ; w
    movsd   qword [lk_afit], xmm0
    movsd   qword [lk_k], xmm1
    movsd   qword [lk_phi], xmm2
    movsd   qword [lk_scale], xmm3
    mulsd   xmm1, xmm3              ; k*scale
    movsd   xmm0, xmm1
    call    my_sincos               ; xmm0=sd, xmm1=cd
    movsd   qword [lk_sd], xmm0
    movsd   qword [lk_cd], xmm1
    movsd   xmm0, [lk_phi]
    call    my_sincos               ; xmm0=s, xmm1=c
    movsd   qword [lk_s], xmm0
    movsd   qword [lk_c], xmm1
    movsd   xmm4, [lk_c]
    movsd   xmm5, [lk_s]
    movsd   xmm6, [lk_cd]
    movsd   xmm7, [lk_sd]
    movsd   xmm8, [lk_afit]         ; Afit
    xorpd   xmm9, xmm9              ; worst
    xorpd   xmm10, xmm10            ; total
    mov     r12d, -1                ; wi
    xor     ecx, ecx                ; i
.slloop:
    cmp     ecx, 64
    jae     .sldone
    movss   xmm0, [rbx+rcx*4]
    cvtss2sd xmm0, xmm0
    movsd   xmm1, xmm8
    mulsd   xmm1, xmm5              ; Afit*s
    subsd   xmm0, xmm1              ; r
    movapd  xmm1, xmm0
    mulsd   xmm1, xmm1              ; r2
    addsd   xmm10, xmm1             ; total
    ucomisd xmm1, xmm9
    jbe     .slnext                 ; r2 > worst?
    movapd  xmm9, xmm1
    mov     r12d, ecx
.slnext:
    movapd  xmm0, xmm4
    mulsd   xmm0, xmm6
    movapd  xmm1, xmm5
    mulsd   xmm1, xmm7
    subsd   xmm0, xmm1
    mulsd   xmm5, xmm6
    mulsd   xmm4, xmm7
    addsd   xmm5, xmm4
    movapd  xmm4, xmm0
    inc     ecx
    jmp     .slloop
.sldone:
    xorpd   xmm0, xmm0
    ucomisd xmm10, xmm0
    je      .slzero                 ; total == 0
    movsd   xmm0, xmm9
    divsd   xmm0, xmm10             ; worst/total
    movsd   qword [lk_share], xmm0
    mov     eax, r12d
    pop     r12
    pop     rbx
    ret
.slzero:
    movsd   qword [lk_share], xmm0
    mov     eax, r12d
    pop     r12
    pop     rbx
    ret

; -- clip_fundamental: xmm0 = A, xmm1 = A_env -> xmm0 --
sqfh_clip_fundamental:
    push    rbx
    sub     rsp, 16                 ; [rsp]=A, [rsp+8]=r
    movsd   qword [rsp], xmm0
    ucomisd xmm0, xmm1
    jbe     .cfret                  ; A <= A_env
    divsd   xmm1, xmm0              ; r = A_env/A
    movsd   qword [rsp+8], xmm1
    movsd   xmm0, xmm1
    call    my_asin                 ; asin(r)
    movsd   xmm1, [rsp+8]
    mulsd   xmm1, xmm1              ; r^2
    movsd   xmm2, [ONE]
    subsd   xmm2, xmm1              ; 1-r^2
    sqrtsd  xmm1, xmm2
    mulsd   xmm1, [rsp+8]           ; r*sqrt
    addsd   xmm0, xmm1              ; asin + r*sqrt
    movsd   xmm1, [C_2DIVPI]
    mulsd   xmm1, [rsp]             ; A*(2/pi)
    mulsd   xmm1, xmm0
    movapd  xmm0, xmm1
    add     rsp, 16
    pop     rbx
    ret
.cfret:
    movsd   xmm0, [rsp]
    add     rsp, 16
    pop     rbx
    ret

; -- recover_amplitude: xmm0 = M, xmm1 = A_env -> xmm0 = true A --
sqfh_recover_amplitude:
    push    rbx
    push    r12
    movsd   qword [rec_M], xmm0
    movsd   qword [rec_A], xmm1
    movsd   qword [rec_lo], xmm1          ; lo = A_env
    addsd   xmm1, xmm1
    movsd   qword [rec_hi], xmm1          ; hi = 2*A_env
.dbl:
    movsd   xmm0, [rec_hi]
    movsd   xmm1, [rec_A]
    call    sqfh_clip_fundamental
    ucomisd xmm0, [rec_M]
    jae     .bisect                 ; clip(hi) >= M
    movsd   xmm0, [rec_hi]
    ucomisd xmm0, [C_1E9]
    jae     .bisect                 ; hi >= 1e9
    addsd   xmm0, xmm0
    movsd   qword [rec_hi], xmm0
    jmp     .dbl
.bisect:
    xor     r12d, r12d              ; it
.bloop:
    cmp     r12d, 60
    jae     .bret
    movsd   xmm0, [rec_lo]
    addsd   xmm0, [rec_hi]
    mulsd   xmm0, [HALF]            ; mid
    movsd   qword [rec_mid], xmm0
    movsd   xmm1, [rec_A]
    call    sqfh_clip_fundamental
    ucomisd xmm0, [rec_M]
    jae     .hiwas
    movsd   xmm0, [rec_mid]
    movsd   qword [rec_lo], xmm0
    jmp     .bnext
.hiwas:
    movsd   xmm0, [rec_mid]
    movsd   qword [rec_hi], xmm0
.bnext:
    inc     r12d
    jmp     .bloop
.bret:
    movsd   xmm0, [rec_lo]
    addsd   xmm0, [rec_hi]
    mulsd   xmm0, [HALF]
    pop     r12
    pop     rbx
    ret

; -- handoff_legacy: rdi = cpu, rsi = w -> eax lane --
sqfh_handoff_legacy:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi                ; cpu
    mov     r12, rsi                ; w
    inc     qword [rbx+O_TILES]
    movsd   xmm0, [rbx+O_K]
    movsd   xmm1, [rbx+O_PHI]
    movsd   xmm2, [rbx+O_SCALE]
    mov     rdi, r12
    call    sqfh_lockin             ; outs to lk_*
    movsd   xmm0, [lk_resid]
    movsd   xmm1, [lk_E]
    xorpd   xmm2, xmm2
    ucomisd xmm1, xmm2
    je      .share0                 ; E == 0
    divsd   xmm0, xmm1              ; share = resid/E
    jmp     .sharehave
.share0:
    xorpd   xmm0, xmm0
.sharehave:
    movsd   qword [lk_tmp], xmm0          ; share
    cmp     dword [rbx+O_EPISODE], 0
    je      .nosep
    ; in episode: share < 0.02 -> close
    movsd   xmm1, [C_002]
    ucomisd xmm0, xmm1
    jae     .epcont
    mov     dword [rbx+O_EPISODE], 0
    inc     qword [rbx+O_EP_CLOSE]
    movsd   xmm0, [lk_dphi]
    movsd   [rbx+O_EP_USED], xmm0
    addsd   xmm0, [rbx+O_PHI]
    movsd   [rbx+O_PHI], xmm0
    mov     dword [rbx+O_LAST_LANE], 0
    inc     qword [rbx+O_LINEAR]
    xor     eax, eax
    jmp     .done
.epcont:
    inc     qword [rbx+O_SHEAR]
    mov     dword [rbx+O_LAST_LANE], 2
    movsd   xmm0, qword [lk_tmp]
    movsd   qword [rbx+O_LAST_SHARE], xmm0
    mov     eax, 2
    jmp     .done
.nosep:
    movsd   xmm1, [C_002]
    ucomisd xmm0, xmm1
    jbe     .slipchk                ; share <= 0.02
    ; overflow candidate: rail count
    movsd   xmm0, [rbx+O_A]
    mulsd   xmm0, [C_0098]          ; 0.98*A
    movsd   qword [lk_tmp+8], xmm0        ; rail threshold spill
    xor     r13d, r13d              ; railed
    xor     ecx, ecx
.railloop:
    cmp     ecx, 64
    jae     .raildone
    movss   xmm0, [r12+rcx*4]
    cvtss2sd xmm0, xmm0
    mov     rax, 0x7FFFFFFFFFFFFFFF
    movq    xmm1, rax
    andpd   xmm0, xmm1              ; fabs
    ucomisd xmm0, qword [lk_tmp+8]
    jb      .railnext               ; |w| < thr
    inc     r13d
.railnext:
    inc     ecx
    jmp     .railloop
.raildone:
    cvtsi2sd xmm0, r13d
    divsd   xmm0, [SIXTY4]
    ucomisd xmm0, [C_005]
    jbe     .spikeq                 ; railed/64 <= 0.05
    ; confirm: clipped-sinusoid refit
    movsd   xmm0, [lk_I]
    movsd   xmm1, [lk_Q]
    call    fhypot
    movsd   xmm1, [TWO]
    mulsd   xmm0, xmm1
    divsd   xmm0, [SIXTY4]          ; M
    movsd   qword [lk_tmp+8], xmm0        ; M spill
    movsd   xmm1, [rbx+O_A]
    call    sqfh_recover_amplitude  ; A_true
    movsd   qword [lk_tmp+16], xmm0       ; A_true spill
    movsd   xmm0, [rbx+O_K]
    mulsd   xmm0, [rbx+O_SCALE]
    call    my_sincos               ; xmm0=sd, xmm1=cd
    movsd   qword [lk_sd], xmm0
    movsd   qword [lk_cd], xmm1
    movsd   xmm0, [lk_dphi]
    addsd   xmm0, [rbx+O_PHI]       ; phi+dphi
    call    my_sincos               ; xmm0=ss, xmm1=cc
    movsd   qword [lk_s], xmm0
    movsd   qword [lk_c], xmm1            ; cc
    movsd   xmm4, [lk_c]
    movsd   xmm5, [lk_s]
    movsd   xmm6, [lk_cd]
    movsd   xmm7, [lk_sd]
    movsd   xmm8, qword [lk_tmp+16]       ; A_true
    xorpd   xmm9, xmm9              ; r2
    xor     ecx, ecx
.refitloop:
    cmp     ecx, 64
    jae     .refitdone
    movsd   xmm0, xmm8
    mulsd   xmm0, xmm5              ; A_true*ss
    movsd   xmm1, [rbx+O_A]
    ucomisd xmm0, xmm1
    jbe     .noraishi
    movapd  xmm0, xmm1              ; v = A
    jmp     .rfitdone
.noraishi:
    xorpd   xmm1, xmm1
    subsd   xmm1, [rbx+O_A]         ; -A
    ucomisd xmm0, xmm1
    jae     .rfitdone
    movapd  xmm0, xmm1
.rfitdone:
    movss   xmm1, [r12+rcx*4]
    cvtss2sd xmm1, xmm1
    subsd   xmm1, xmm0              ; d = w - v
    mulsd   xmm1, xmm1
    addsd   xmm9, xmm1              ; r2
    movapd  xmm0, xmm4
    mulsd   xmm0, xmm6
    movapd  xmm1, xmm5
    mulsd   xmm1, xmm7
    subsd   xmm0, xmm1
    mulsd   xmm5, xmm6
    mulsd   xmm4, xmm7
    addsd   xmm5, xmm4
    movapd  xmm4, xmm0
    inc     ecx
    jmp     .refitloop
.refitdone:
    movsd   xmm0, [lk_E]
    xorpd   xmm1, xmm1
    ucomisd xmm0, xmm1
    je      .spikeq                 ; E == 0
    divsd   xmm9, xmm0              ; r2/E
    ucomisd xmm9, [C_002]
    jae     .spikeq
    inc     qword [rbx+O_OVERFLOWS]
    mov     dword [rbx+O_LAST_LANE], 4
    movsd   xmm0, qword [lk_tmp+16]
    subsd   xmm0, [rbx+O_A]         ; excess = A_true - A
    movsd   qword [rbx+O_LAST_EXCESS], xmm0
    movsd   xmm0, qword [lk_tmp]
    movsd   qword [rbx+O_LAST_SHARE], xmm0
    mov     eax, 4
    jmp     .done
.spikeq:
    ; Afit + localize
    movsd   xmm0, [lk_I]
    movsd   xmm1, [lk_Q]
    call    fhypot
    movsd   xmm1, [TWO]
    mulsd   xmm0, xmm1
    divsd   xmm0, [SIXTY4]          ; Afit
    movsd   xmm1, [rbx+O_K]
    movsd   xmm2, [lk_dphi]
    addsd   xmm2, [rbx+O_PHI]       ; phi+dphi
    movsd   xmm3, [rbx+O_SCALE]
    mov     rdi, r12
    call    sqfh_spike_localize     ; eax = idx, share to lk_share
    mov     r13d, eax               ; si
    movsd   xmm0, [lk_share]
    ucomisd xmm0, [HALF]
    jbe     .shearopen              ; sshare <= 0.50
    inc     qword [rbx+O_SPIKES]
    mov     dword [rbx+O_LAST_LANE], 3
    mov     [rbx+O_LAST_SIDX], r13d
    movsd   xmm0, [lk_share]
    movsd   qword [rbx+O_LAST_SHARE], xmm0
    mov     eax, 3
    jmp     .done
.shearopen:
    mov     dword [rbx+O_EPISODE], 1
    inc     qword [rbx+O_EP_OPEN]
    movsd   xmm0, [rbx+O_PHI]
    movsd   qword [rbx+O_EP_PHI0], xmm0
    inc     qword [rbx+O_SHEAR]
    mov     dword [rbx+O_LAST_LANE], 2
    movsd   xmm0, qword [lk_tmp]
    movsd   qword [rbx+O_LAST_SHARE], xmm0
    mov     eax, 2
    jmp     .done
.slipchk:
    movsd   xmm0, [lk_dphi]
    mov     rax, 0x7FFFFFFFFFFFFFFF
    movq    xmm1, rax
    andpd   xmm0, xmm1              ; fabs(dphi)
    ucomisd xmm0, [C_001]
    jbe     .linear                 ; |dphi| <= 0.01
    inc     qword [rbx+O_SLIPS]
    movsd   xmm0, [lk_dphi]
    movsd   qword [rbx+O_LAST_DPHI], xmm0
    addsd   xmm0, [rbx+O_PHI]
    movsd   qword [rbx+O_PHI], xmm0
    mov     dword [rbx+O_LAST_LANE], 1
    mov     eax, 1
    jmp     .done
.linear:
    inc     qword [rbx+O_LINEAR]
    mov     dword [rbx+O_LAST_LANE], 0
    xor     eax, eax
.done:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- sqfh_advance: rdi = cpu --
sqfh_advance:
    movsd   xmm0, [rdi+O_K]
    mulsd   xmm0, [SIXTY4]          ; k*64 (exact scale)
    mulsd   xmm0, [rdi+O_SCALE]     ; *scale
    addsd   xmm0, [rdi+O_PHI]
    movsd   [rdi+O_PHI], xmm0
    movsd   xmm0, [SIXTY4]
    mulsd   xmm0, [rdi+O_SCALE]
    addsd   xmm0, [rdi+96]
    movsd   [rdi+96], xmm0          ; x0 += 64*scale (legacy: unused, kept)
    ret

; -- mem_eq: rdi, rsi, ecx = len -> eax 1 equal / 0 --
mem_eq:
    test    ecx, ecx
    jz      .eq
    repe    cmpsb
    sete    al
    movzx   eax, al
    ret
.eq:
    mov     eax, 1
    ret

; -- emit_str: rsi = ptr, rdx = len -> appends to outbuf --
emit_str:
    mov     rax, [outcur]
    lea     rdi, [outbuf+rax]
    mov     rcx, rdx
    rep     movsb
    mov     rax, rdi
    sub     rax, outbuf
    mov     [outcur], rax
    ret

; -- emit_u64: rax = value -> decimal --
emit_u64:
    lea     rdi, [numbuf+31]
    mov     rcx, 10
    test    rax, rax
    jnz     .dig
    dec     rdi
    mov     byte [rdi], '0'
    jmp     .out
.dig:
    xor     edx, edx
    div     rcx
    add     dl, '0'
    dec     rdi
    mov     [rdi], dl
    test    rax, rax
    jnz     .dig
.out:
    mov     rsi, rdi
    lea     rdx, [numbuf+31]
    sub     rdx, rsi
    jmp     emit_str

; -- emit_f6: xmm0 = double >= 0 -> "d.dddddd" (correctly rounded) --
emit_f6:
    push    rbx
    cvttsd2si r8, xmm0
    cvtsi2sd xmm1, r8
    subsd   xmm0, xmm1
    xor     ecx, ecx
.dig_loop:
    mulsd   xmm0, [TEN]
    cvttsd2si eax, xmm0
    mov     [fdigits+rcx], al
    cvtsi2sd xmm1, eax
    subsd   xmm0, xmm1
    inc     ecx
    cmp     ecx, 7
    jne     .dig_loop
    xor     ecx, ecx
    ucomisd xmm0, [DBL_0]
    setnz   cl
    mov     al, [fdigits+6]
    cmp     al, 5
    ja      .carry
    jb      .print
    test    ecx, ecx
    jnz     .carry
    test    byte [fdigits+5], 1
    jz      .print
.carry:
    mov     ecx, 5
.carry_loop:
    inc     byte [fdigits+rcx]
    cmp     byte [fdigits+rcx], 10
    jb      .print
    mov     byte [fdigits+rcx], 0
    dec     ecx
    jns     .carry_loop
    inc     r8
.print:
    mov     rax, r8
    call    emit_u64
    mov     rax, [outcur]
    mov     byte [outbuf+rax], '.'
    inc     qword [outcur]
    mov     rax, [outcur]
    lea     rdi, [outbuf+rax]
    xor     ecx, ecx
.copy_loop:
    mov     al, [fdigits+rcx]
    add     al, '0'
    mov     [rdi+rcx], al
    inc     ecx
    cmp     ecx, 6
    jne     .copy_loop
    add     qword [outcur], 6
    pop     rbx
    ret

; -- emit_f4: xmm0 = double (any sign) -> "[-]d.dddd" (correctly rounded) --
emit_f4:
    push    rbx
    movq    rax, xmm0
    test    rax, rax
    jns     .pos
    mov     rax, [outcur]
    mov     byte [outbuf+rax], '-'
    inc     qword [outcur]
    mov     rax, 0x7FFFFFFFFFFFFFFF
    movq    xmm1, rax
    andpd   xmm0, xmm1
.pos:
    cvttsd2si r8, xmm0
    cvtsi2sd xmm1, r8
    subsd   xmm0, xmm1
    xor     ecx, ecx
.dig_loop:
    mulsd   xmm0, [TEN]
    cvttsd2si eax, xmm0
    mov     [fdigits+rcx], al
    cvtsi2sd xmm1, eax
    subsd   xmm0, xmm1
    inc     ecx
    cmp     ecx, 5
    jne     .dig_loop
    xor     ecx, ecx
    ucomisd xmm0, [DBL_0]
    setnz   cl
    mov     al, [fdigits+4]
    cmp     al, 5
    ja      .carry
    jb      .print
    test    ecx, ecx
    jnz     .carry
    test    byte [fdigits+3], 1
    jz      .print
.carry:
    mov     ecx, 3
.carry_loop:
    inc     byte [fdigits+rcx]
    cmp     byte [fdigits+rcx], 10
    jb      .print
    mov     byte [fdigits+rcx], 0
    dec     ecx
    jns     .carry_loop
    inc     r8
.print:
    mov     rax, r8
    call    emit_u64
    mov     rax, [outcur]
    mov     byte [outbuf+rax], '.'
    inc     qword [outcur]
    mov     rax, [outcur]
    lea     rdi, [outbuf+rax]
    xor     ecx, ecx
.copy_loop:
    mov     al, [fdigits+rcx]
    add     al, '0'
    mov     [rdi+rcx], al
    inc     ecx
    cmp     ecx, 4
    jne     .copy_loop
    add     qword [outcur], 4
    pop     rbx
    ret

; -- emit_f1: xmm0 = double >= 0 -> "d.d" (timing only, round-half-up) --
emit_f1:
    push    rbx
    mulsd   xmm0, [TEN]
    cvttsd2si rax, xmm0
    xor     edx, edx
    mov     rcx, 10
    div     rcx                     ; rax = int, rdx = frac
    mov     rbx, rdx
    call    emit_u64
    mov     rax, [outcur]
    mov     byte [outbuf+rax], '.'
    inc     qword [outcur]
    mov     rax, rbx
    call    emit_u64
    pop     rbx
    ret

; -- emit_f2: xmm0 = double >= 0 -> "d.dd" (timing only) --
emit_f2:
    push    rbx
    mulsd   xmm0, [HUNDRED]
    cvttsd2si rax, xmm0
    xor     edx, edx
    mov     rcx, 100
    div     rcx
    mov     rbx, rdx
    call    emit_u64
    mov     rax, [outcur]
    mov     byte [outbuf+rax], '.'
    inc     qword [outcur]
    mov     rax, rbx
    cmp     rax, 10
    jae     .two
    push    rax
    mov     rax, [outcur]
    mov     byte [outbuf+rax], '0'
    inc     qword [outcur]
    pop     rax
.two:
    call    emit_u64
    pop     rbx
    ret

; -- ratio_f6: rax = num (signed 64), rdx = den -> xmm0 = num/den or 0.0 --
ratio_f6:
    test    rdx, rdx
    jz      .zero
    push    rbx
    mov     rbx, rdx
    cvtsi2sd xmm0, rax
    cvtsi2sd xmm1, rbx
    divsd   xmm0, xmm1
    pop     rbx
    ret
.zero:
    xorpd   xmm0, xmm0
    ret

; -- _start --
_start:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    call    init_math
    call    gen_stream
    ; init cpu: scale=1, A=1, k=TRUE_K, phi=0
    lea     rdi, [cpu]
    movsd   xmm0, [ONE]
    movsd   xmm1, [ONE]
    movsd   xmm2, [TRUE_K]
    xorpd   xmm3, xmm3
    call    sqfh_init
    mov     dword [m_nslip], 0
    mov     dword [m_ep_open], -1
    mov     dword [m_ep_close], -1
    mov     dword [m_spike_tile], -1
    mov     dword [m_spike_idx], -1
    mov     qword [m_prev_open], 0
    mov     qword [m_prev_close], 0
    xor     r15d, r15d              ; tns (integer ns total)
    xor     r14d, r14d              ; t
.tloop:
    cmp     r14d, 4096
    jae     .scoring
    mov     eax, r14d
    shl     eax, 8                  ; t*256
    lea     rsi, [stream+rax]       ; tile
    call    wallns
    mov     r13, rax                ; t0
    lea     rdi, [cpu]
    mov     eax, r14d               ; re-derive tile (wallns kills rsi)
    shl     eax, 8
    lea     rsi, [stream+rax]
    call    sqfh_handoff_legacy     ; dispatched legacy (cert path)
    mov     r12d, eax               ; lane
    call    wallns
    sub     rax, r13
    add     r15, rax                ; tns += dt
    mov     eax, r14d
    mov     [lane_log+rax], r12b
    ; archive raw (rep movsb: [rsi] -> [rdi])
    mov     eax, r14d
    shl     eax, 8
    lea     rsi, [stream+rax]
    lea     rdi, [archive+rax]
    mov     ecx, 256
    rep     movsb
    cmp     r12d, 1                 ; SLIP?
    jne     .nosliprec
    cmp     dword [m_nslip], 2
    jae     .nosliprec
    mov     eax, [m_nslip]
    movsd   xmm0, qword [cpu+O_LAST_DPHI]
    movsd   qword [slip_rec+rax*8], xmm0
    inc     dword [m_nslip]
.nosliprec:
    mov     rax, qword [cpu+O_EP_OPEN]
    cmp     rax, [m_prev_open]
    je      .noopen
    mov     [m_ep_open], r14d
    mov     [m_prev_open], rax
.noopen:
    mov     rax, qword [cpu+O_EP_CLOSE]
    cmp     rax, [m_prev_close]
    je      .noclose
    mov     [m_ep_close], r14d
    mov     [m_prev_close], rax
.noclose:
    cmp     r12d, 3                 ; SPIKE?
    jne     .advance
    mov     [m_spike_tile], r14d
    mov     eax, dword [cpu+O_LAST_SIDX]
    mov     [m_spike_idx], eax
.advance:
    lea     rdi, [cpu]
    call    sqfh_advance
    inc     r14d
    jmp     .tloop
.scoring:
    mov     qword [m_tns], r15       ; spill (scoring reuses r13-r15)
    ; clean / clean_lin / false_slip
    xor     r13d, r13d              ; clean
    xor     r14d, r14d              ; clean_lin
    xor     r15d, r15d              ; false_slip
    xor     ebx, ebx                ; t
.scloop:
    cmp     ebx, 4096
    jae     .emit
    mov     al, [truth+rbx]
    cmp     al, 2
    je      .scnext
    cmp     al, 4
    je      .scnext
    cmp     ebx, 3000
    je      .scnext
    cmp     ebx, 1000
    je      .scnext
    cmp     ebx, 2500
    je      .scnext
    inc     r13d
    mov     al, [lane_log+rbx]
    test    al, al                  ; LINEAR?
    jnz     .scslip
    inc     r14d
    jmp     .scnext
.scslip:
    cmp     al, 1                   ; SLIP?
    jne     .scnext
    inc     r15d
.scnext:
    inc     ebx
    jmp     .scloop
.emit:
    ; O1
    lea     rsi, [P1A]
    mov     rdx, P1A_LEN
    call    emit_str
    mov     eax, r14d
    call    emit_u64
    lea     rsi, [PSL]
    mov     rdx, 1
    call    emit_str
    mov     eax, r13d
    call    emit_u64
    lea     rsi, [PEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, r14
    mov     rdx, r13
    call    ratio_f6
    call    emit_f6
    lea     rsi, [P1B]
    mov     rdx, P1B_LEN
    call    emit_str
    ; O2 count
    lea     rsi, [P2A]
    mov     rdx, P2A_LEN
    call    emit_str
    mov     rax, qword [cpu+O_SLIPS]
    call    emit_u64
    lea     rsi, [P2B]
    mov     rdx, P2B_LEN
    call    emit_str
    mov     eax, r15d
    call    emit_u64
    lea     rsi, [PNL]
    mov     rdx, 1
    call    emit_str
    ; O2 recovery
    lea     rsi, [P2C]
    mov     rdx, P2C_LEN
    call    emit_str
    movsd   xmm0, [slip_rec]
    call    emit_f4
    lea     rsi, [P2D]
    mov     rdx, P2D_LEN
    call    emit_str
    movsd   xmm0, [slip_rec+8]
    call    emit_f4
    lea     rsi, [P2E]
    mov     rdx, P2E_LEN
    call    emit_str
    ; O3
    lea     rsi, [P3A]
    mov     rdx, P3A_LEN
    call    emit_str
    mov     eax, [m_ep_open]
    call    emit_u64
    lea     rsi, [P3B]
    mov     rdx, P3B_LEN
    call    emit_str
    mov     eax, [m_ep_close]
    call    emit_u64
    lea     rsi, [P3C]
    mov     rdx, P3C_LEN
    call    emit_str
    mov     rax, qword [cpu+O_EP_OPEN]
    call    emit_u64
    lea     rsi, [PSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, qword [cpu+O_EP_CLOSE]
    call    emit_u64
    lea     rsi, [PNL]
    mov     rdx, 1
    call    emit_str
    ; O4
    xor     ebx, ebx                ; raw_bad
    mov     r13d, 1500              ; t
.o4loop:
    cmp     r13d, 1512
    jae     .o4done
    mov     eax, r13d
    shl     eax, 8
    lea     rdi, [archive+rax]
    lea     rsi, [stream+rax]
    mov     ecx, 256
    call    mem_eq
    test    eax, eax
    jnz     .o4next
    inc     ebx
.o4next:
    inc     r13d
    jmp     .o4loop
.o4done:
    lea     rsi, [P4A]
    mov     rdx, P4A_LEN
    call    emit_str
    mov     eax, 12
    sub     eax, ebx
    call    emit_u64
    lea     rsi, [P4B]
    mov     rdx, P4B_LEN
    call    emit_str
    ; O5
    lea     rsi, [P5A]
    mov     rdx, P5A_LEN
    call    emit_str
    mov     eax, [m_spike_tile]
    call    emit_u64
    lea     rsi, [P5B]
    mov     rdx, P5B_LEN
    call    emit_str
    mov     eax, [m_spike_idx]
    call    emit_u64
    lea     rsi, [P5C]
    mov     rdx, P5C_LEN
    call    emit_str
    movzx   eax, byte [lane_log+3000]
    cmp     eax, 3
    je      .routed_ok
    lea     rsi, [P5W]
    mov     rdx, P5W_LEN
    call    emit_str
    jmp     .o7
.routed_ok:
    lea     rsi, [P5S]
    mov     rdx, P5S_LEN
    call    emit_str
.o7:
    ; ov_ok / ov_raw_bad over 2000..2011
    xor     ebx, ebx                ; ov_ok
    xor     r13d, r13d              ; ov_raw_bad
    mov     r14d, 2000
.o7loop:
    cmp     r14d, 2012
    jae     .o7done
    mov     eax, r14d
    movzx   ecx, byte [lane_log+rax]
    cmp     ecx, 4                  ; OVERFLOW?
    jne     .o7mem
    inc     ebx
.o7mem:
    mov     eax, r14d
    shl     eax, 8
    lea     rdi, [archive+rax]
    lea     rsi, [stream+rax]
    mov     ecx, 256
    call    mem_eq
    test    eax, eax
    jnz     .o7next
    inc     r13d
.o7next:
    inc     r14d
    jmp     .o7loop
.o7done:
    push    rbx                     ; ov_ok
    push    r13                     ; ov_raw_bad
    ; probe: init + phi + handoff tile 2000
    lea     rdi, [probe]
    movsd   xmm0, [ONE]
    movsd   xmm1, [ONE]
    movsd   xmm2, [TRUE_K]
    xorpd   xmm3, xmm3
    call    sqfh_init
    mov     eax, 2000
    cvtsi2sd xmm0, eax
    mulsd   xmm0, [SIXTY4]
    mulsd   xmm0, [TRUE_K]          ; TRUE_K*2000*64 (C order check below)
    movsd   qword [probe+O_PHI], xmm0
    mov     eax, 2000
    shl     eax, 8
    lea     rsi, [stream+rax]
    lea     rdi, [probe]
    call    sqfh_handoff_legacy
    movsd   xmm0, qword [probe+O_LAST_EXCESS]
    movsd   qword [th_tmp], xmm0          ; ex_sum spill
    pop     r13                     ; ov_raw_bad
    pop     rbx                     ; ov_ok
    lea     rsi, [P7A]
    mov     rdx, P7A_LEN
    call    emit_str
    mov     rax, rbx
    call    emit_u64
    lea     rsi, [P7B]
    mov     rdx, P7B_LEN
    call    emit_str
    mov     rax, qword [cpu+O_EP_OPEN]
    dec     rax                     ; ep = ep_open - 1
    call    emit_u64
    lea     rsi, [P7C]
    mov     rdx, P7C_LEN
    call    emit_str
    mov     eax, 12
    sub     eax, r13d
    call    emit_u64
    lea     rsi, [P7D]
    mov     rdx, P7D_LEN
    call    emit_str
    ; O8
    lea     rsi, [P8A]
    mov     rdx, P8A_LEN
    call    emit_str
    movsd   xmm0, qword [th_tmp]
    call    emit_f4
    lea     rsi, [P8B]
    mov     rdx, P8B_LEN
    call    emit_str
    ; O6 (timing excluded from diff; counts included)
    lea     rsi, [P6A]
    mov     rdx, P6A_LEN
    call    emit_str
    cvtsi2sd xmm0, qword [m_tns]
    movsd   xmm1, [C_4096]
    divsd   xmm0, xmm1              ; ns/tile
    call    emit_f1
    lea     rsi, [P6B]
    mov     rdx, P6B_LEN
    call    emit_str
    cvtsi2sd xmm0, qword [m_tns]
    divsd   xmm0, [C_4096]
    divsd   xmm0, [SIXTY4]          ; ns/sample
    call    emit_f2
    lea     rsi, [P6C]
    mov     rdx, P6C_LEN
    call    emit_str
    mov     rax, qword [cpu+O_LINEAR]
    call    emit_u64
    lea     rsi, [P6D]
    mov     rdx, P6D_LEN
    call    emit_str
    mov     rax, qword [cpu+O_SLIPS]
    call    emit_u64
    lea     rsi, [P6E]
    mov     rdx, P6E_LEN
    call    emit_str
    mov     rax, qword [cpu+O_SHEAR]
    call    emit_u64
    lea     rsi, [P6F]
    mov     rdx, P6F_LEN
    call    emit_str
    mov     rax, qword [cpu+O_SPIKES]
    call    emit_u64
    lea     rsi, [PNL]
    mov     rdx, 1
    call    emit_str
    mov     eax, 1                  ; sys_write(1, outbuf, outcur)
    mov     edi, 1
    lea     rsi, [outbuf]
    mov     rdx, [outcur]
    syscall
    mov     eax, 60
    xor     edi, edi
    syscall

segment readable

DBL_0 dq 0
C_4096 dq 0x40B0000000000000        ; 4096.0

P1A db 'SQFHOR O1_linear_purity   '
P1A_LEN = $ - P1A
P1B db '  expect>=0.990', 0x0A
P1B_LEN = $ - P1B
P2A db 'SQFHOR O2_slip_count      '
P2A_LEN = $ - P2A
P2B db ' detected (expect 2)  false_slips='
P2B_LEN = $ - P2B
P2C db 'SQFHOR O2_slip_recovery   '
P2C_LEN = $ - P2C
P2D db ' / '
P2D_LEN = $ - P2D
P2E db ' rad (true +0.40 / -0.25, expect |err|<=0.02)', 0x0A
P2E_LEN = $ - P2E
P3A db 'SQFHOR O3_episode         open@tile '
P3A_LEN = $ - P3A
P3B db ' (expect 1500+-1)  close@tile '
P3B_LEN = $ - P3B
P3C db ' (expect 1512+-1)  pairs='
P3C_LEN = $ - P3C
P4A db 'SQFHOR O4_raw_fidelity    '
P4A_LEN = $ - P4A
P4B db '/12 episode tiles byte-identical (0 clamped/corrected)', 0x0A
P4B_LEN = $ - P4B
P5A db 'SQFHOR O5_spike           tile '
P5A_LEN = $ - P5A
P5B db ' (expect 3000) sample '
P5B_LEN = $ - P5B
P5C db ' (expect 17) routed='
P5C_LEN = $ - P5C
P5S db 'SPIKE (not shear)', 0x0A
P5S_LEN = $ - P5S
P5W db 'WRONG', 0x0A
P5W_LEN = $ - P5W
P7A db 'SQFHOR O7_overflow_lane   '
P7A_LEN = $ - P7A
P7B db '/12 routed OVERFLOW (0 episodes expected: ep='
P7B_LEN = $ - P7B
P7C db ')  raw='
P7C_LEN = $ - P7C
P7D db '/12 byte-identical', 0x0A
P7D_LEN = $ - P7D
P8A db 'SQFHOR O8_excess_recovery '
P8A_LEN = $ - P8A
P8B db ' (true 0.6000, expect |err|<=0.05)', 0x0A
P8B_LEN = $ - P8B
P6A db 'SQFHOR O6_handoff_cost    '
P6A_LEN = $ - P6A
P6B db ' ns/tile ('
P6B_LEN = $ - P6B
P6C db ' ns/sample)  lanes: lin='
P6C_LEN = $ - P6C
P6D db ' slip='
P6D_LEN = $ - P6D
P6E db ' shear='
P6E_LEN = $ - P6E
P6F db ' spike='
P6F_LEN = $ - P6F
PSL db '/'
PEQ db ' = '
PNL db 0x0A


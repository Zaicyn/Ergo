; SQM certification driver in flat assembler (FASM 1.73.x, x86-64 Linux).
; Faithful port of benchmark/sqm_cert.c + sqm_core.h + xoshiro_ss RNG from
; benchmark/common.h. Goal: byte-identical stdout to sqm_cert.
;
; Deliberate scope: the SCALAR moment path only. The SSE4.1 path in
; sqm_core.h is provably identical (all sums < 2^32 at PAY=64, stored
; through uint32_t) -- the port does what the scalar fallback does.
;
; Internal ABI: args in rdi,rsi,rdx,rcx,r8,r9 (SysV-like), result in
; rax (xmm0 for doubles). rbx,rbp,r12-r15 are callee-saved everywhere.
; No libc: BSS arena, write(2)/exit(2) only. ASCII-only source
; (FASM 1.x mishandles UTF-8 comments).
;
; Cell layout (sizes from the C headers, behavior-matched):
;   pay[8][32][64] @0 (16384), root[8][32] x32B @16384 (8192),
;   half[8][32][2] x32B @24576 (16384), occ[256] @40960,
;   head[8] dwords @41216, total dword @41248,
;   counters qwords @41256: skips sec halfw fullw bread bwritten conf
;   CELL_SZ = 41312 (5164 qwords, exact)
; A moment (sqm_mom_t) is 4 qwords (32 B), s[0..3].
; Assemble: fasm sqm.asm sqm   (optional rounds arg, default 1000)

format ELF64 executable 3
entry _start

SQM_NB  = 8
SQM_NR  = 32
SQM_PAY = 64
SQM_HALF = 32
SQM_CAP = 256
SQM_CAP4 = 1024
PAY_OFF = 0
ROOT_OFF = 16384
HALF_OFF = 24576
OCC_OFF = 40960
HEAD_OFF = 41216
TOTAL_OFF = 41248
C_SKIPS = 41256
C_SEC = 41264
C_HALFW = 41272
C_FULLW = 41280
C_BREAD = 41288
C_BWRITTEN = 41296
C_CONF = 41304
CELL_SZ = 41312
CELL_QW = 5164

segment readable executable
include '../rng.inc'        ; shared xoshiro** (single source)
include '../emit.inc'       ; shared emit (single source)
mom:
    cmp     byte [use_avx], 0
    je      mom_scalar
    jmp     mom_avx2

; -- mom_scalar: rdi = buf, esi = base, edx = len, rcx = &mom --
; sqm_core.h sqm_mom fallback. All sums fit u32 at PAY=64; u64 wrap anyway.
mom_scalar:
    push    rbx
    push    r12
    push    rcx                     ; mom ptr
    mov     r12d, edx               ; len
    xor     r9, r9                  ; s0
    xor     r10, r10                ; s1
    xor     r11, r11                ; s2
    xor     ebx, ebx                ; s3
    xor     ecx, ecx                ; i
.m_loop:
    cmp     ecx, r12d
    jae     .done
    movzx   eax, byte [rdi+rcx]     ; v
    mov     r8d, esi
    add     r8, rcx
    inc     r8                      ; x = base+i+1
    add     r9, rax                 ; s0 += v
    mov     rdx, rax
    imul    rdx, r8                 ; v*x
    add     r10, rdx                ; s1
    imul    rdx, r8                 ; v*x^2
    add     r11, rdx                ; s2
    imul    rdx, r8                 ; v*x^3
    add     rbx, rdx                ; s3
    inc     ecx
    jmp     .m_loop
.done:
    pop     rcx
    mov     [rcx], r9
    mov     [rcx+8], r10
    mov     [rcx+16], r11
    mov     [rcx+24], rbx
    pop     r12
    pop     rbx
    ret

; -- mom_avx2: rdi = buf, esi = base, edx = len, rcx = &mom --
; 8 bytes/iter in u32 lanes; scalar tail; vzeroupper on exit.
mom_avx2:
    push    rbx
    push    r12
    push    rcx                     ; mom ptr
    mov     r12d, edx               ; len
    vpxor   ymm0, ymm0, ymm0        ; s0
    vpxor   ymm1, ymm1, ymm1        ; s1
    vpxor   ymm2, ymm2, ymm2        ; s2
    vpxor   ymm3, ymm3, ymm3        ; s3
    ; idx vector = [base+1 .. base+8] (MUST live in ymm5: loop reads it)
    mov     eax, esi
    inc     eax                     ; base+1
    vmovd   xmm5, eax
    vpbroadcastd ymm5, xmm5
    lea     rdx, [idx_off]
    vpaddd  ymm5, ymm5, [rdx]
    xor     r9, r9                  ; tail accumulators (main uses ymm)
    xor     r10, r10
    xor     r11, r11
    xor     ebx, ebx
    lea     rdx, [idx8]             ; +8 vector addr (rdx free in main loop)
    xor     ecx, ecx                ; i
    jmp     .acheck
.aloop:
    vpmovzxbd ymm4, qword [rdi+rcx]  ; v: 8 bytes -> 8 dwords
    vpmulld ymm6, ymm5, ymm5         ; x2
    vpmulld ymm7, ymm6, ymm5         ; x3
    vpaddd  ymm0, ymm0, ymm4         ; s0 += v
    vpmulld ymm8, ymm4, ymm5         ; v*x
    vpaddd  ymm1, ymm1, ymm8         ; s1
    vpmulld ymm8, ymm4, ymm6         ; v*x2
    vpaddd  ymm2, ymm2, ymm8         ; s2
    vpmulld ymm8, ymm4, ymm7         ; v*x3
    vpaddd  ymm3, ymm3, ymm8         ; s3
    vpaddd  ymm5, ymm5, [rdx]        ; idx += 8 (rdx = idx8 addr, set below)
    add     ecx, 8
.acheck:
    lea     eax, [rcx+8]
    cmp     eax, r12d
    jbe     .aloop
.atail:
    cmp     ecx, r12d
    jae     .adone
    movzx   eax, byte [rdi+rcx]
    mov     r8d, esi
    add     r8, rcx
    inc     r8
    add     r9, rax
    mov     rdx, rax
    imul    rdx, r8
    add     r10, rdx
    imul    rdx, r8
    add     r11, rdx
    imul    rdx, r8
    add     rbx, rdx
    inc     ecx
    jmp     .atail
.adone:
    pop     rcx                     ; mom ptr
    lea     rsi, [hstmp]            ; hsum scratch (rsi free here)
    vextracti128 xmm8, ymm0, 1
    vpaddd  xmm8, xmm8, xmm0
    vmovdqu [rsi], xmm8
    mov     eax, [hstmp]
    mov     edx, [hstmp+4]
    add     rax, rdx
    mov     edx, [hstmp+8]
    add     rax, rdx
    mov     edx, [hstmp+12]
    add     rax, rdx
    add     rax, r9
    mov     [rcx], rax              ; s0
    vextracti128 xmm8, ymm1, 1
    vpaddd  xmm8, xmm8, xmm1
    vmovdqu [rsi], xmm8
    mov     eax, [hstmp]
    mov     edx, [hstmp+4]
    add     rax, rdx
    mov     edx, [hstmp+8]
    add     rax, rdx
    mov     edx, [hstmp+12]
    add     rax, rdx
    add     rax, r10
    mov     [rcx+8], rax            ; s1
    vextracti128 xmm8, ymm2, 1
    vpaddd  xmm8, xmm8, xmm2
    vmovdqu [rsi], xmm8
    mov     eax, [hstmp]
    mov     edx, [hstmp+4]
    add     rax, rdx
    mov     edx, [hstmp+8]
    add     rax, rdx
    mov     edx, [hstmp+12]
    add     rax, rdx
    add     rax, r11
    mov     [rcx+16], rax           ; s2
    vextracti128 xmm8, ymm3, 1
    vpaddd  xmm8, xmm8, xmm3
    vmovdqu [rsi], xmm8
    mov     eax, [hstmp]
    mov     edx, [hstmp+4]
    add     rax, rdx
    mov     edx, [hstmp+8]
    add     rax, rdx
    mov     edx, [hstmp+12]
    add     rax, rdx
    add     rax, rbx
    mov     [rcx+24], rax           ; s3
    vzeroupper                      ; close AVX region before returning
    pop     r12
    pop     rbx
    ret

; -- check_avx2: -> eax 1 if AVX2 usable (OSXSAVE + XCR0 + CPUID.7:EBX[5]) --
check_avx2:
    mov     eax, 1
    cpuid
    test    ecx, 0x08000000         ; OSXSAVE?
    jz      .no
    xor     ecx, ecx
    xgetbv                          ; edx:eax = XCR0
    and     eax, 0x6                ; SSE + AVX-YMM state?
    cmp     eax, 0x6
    jne     .no
    mov     eax, 7
    xor     ecx, ecx
    cpuid
    test    ebx, 0x20               ; AVX2 bit 5
    jz      .no
    mov     eax, 1
    ret
.no:
    xor     eax, eax
    ret

; -- mom_eq: rdi = a, rsi = b (32 B each) -> eax 0/1 --
mom_eq:
    mov     rax, [rdi]
    cmp     rax, [rsi]
    jne     .no
    mov     rax, [rdi+8]
    cmp     rax, [rsi+8]
    jne     .no
    mov     rax, [rdi+16]
    cmp     rax, [rsi+16]
    jne     .no
    mov     rax, [rdi+24]
    cmp     rax, [rsi+24]
    jne     .no
    mov     eax, 1
    ret
.no:
    xor     eax, eax
    ret

; -- solve: rdi = &D, rsi = &p1, rdx = &d1, rcx = &p2, r8 = &d2 -> eax --
; sqm_core.h sqm_solve. SIGNED int64 throughout: idiv matches C
; truncation; TEST-bit matches C %2==0 for negatives. Frame holds a,b,da.
solve:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 64                 ; a,b,da @0,8,16 ; p1,d1,p2,d2 @24,32,40,48
    mov     [rsp+24], rsi           ; out-pointers spilled (regs go scratch)
    mov     [rsp+32], rdx
    mov     [rsp+40], rcx
    mov     [rsp+48], r8
    mov     r12, [rdi]              ; D0
    mov     r13, [rdi+8]            ; D1
    mov     r14, [rdi+16]           ; D2
    mov     r15, [rdi+24]           ; D3
    test    r12, r12
    jz      .fail                   ; s0 must move
    cmp     r12, 255
    jg      .two
    cmp     r12, -255
    jl      .two
    mov     rax, r13
    cqo
    idiv    r12                     ; p = D1/D0
    test    rdx, rdx
    jnz     .two
    cmp     rax, 1
    jl      .two
    cmp     rax, SQM_PAY
    jg      .two
    mov     rbx, rax                ; p
    mov     rax, r12
    imul    rax, rbx
    imul    rax, rbx                ; D0*p*p
    cmp     rax, r14
    jne     .two
    imul    rax, rbx                ; D0*p*p*p
    cmp     rax, r15
    jne     .two
    mov     rax, [rsp+24]
    mov     [rax], ebx              ; *p1 = p
    mov     rax, [rsp+32]
    mov     [rax], r12d             ; *d1 = D0 (dword)
    mov     eax, 1
    jmp     .done
.two:
    mov     rax, r12
    imul    rax, r14                ; D0*D2
    mov     rbx, r13
    imul    rbx, r13                ; D1*D1
    sub     rax, rbx
    mov     r11, rax                ; det
    test    r11, r11
    jz      .fail
    mov     rax, r12
    imul    rax, r15                ; D0*D3
    mov     rbx, r13
    imul    rbx, r14                ; D1*D2
    sub     rax, rbx
    mov     r10, rax                ; un
    mov     rax, r13
    imul    rax, r15                ; D1*D3
    mov     rbx, r14
    imul    rbx, r14                ; D2*D2
    sub     rax, rbx
    mov     r9, rax                 ; vn
    mov     rax, r10
    cqo
    idiv    r11
    test    rdx, rdx                ; un % det == 0 ?
    jnz     .fail
    mov     rax, r9
    cqo
    idiv    r11
    test    rdx, rdx                ; vn % det == 0 ?
    jnz     .fail
    mov     rax, r10                ; u = un/det
    cqo
    idiv    r11
    mov     r10, rax
    mov     rax, r9                 ; v = vn/det
    cqo
    idiv    r11
    mov     r9, rax
    mov     rax, r10
    imul    rax, r10                ; u*u
    mov     rbx, r9
    shl     rbx, 2                  ; 4*v
    sub     rax, rbx
    mov     rdi, rax                ; disc
    test    rdi, rdi
    jle     .fail
    mov     rbx, 1                  ; integer sqrt loop
.sqrt:
    mov     rax, rbx
    imul    rax, rbx
    cmp     rax, rdi
    jge     .sqrt_done
    inc     rbx
    jmp     .sqrt
.sqrt_done:
    cmp     rax, rdi
    jne     .fail
    mov     rax, r10
    add     rax, rbx                ; u+r
    test    al, 1                   ; (u+r)%2==0 ?
    jnz     .fail
    sar     rax, 1                  ; a (exact: even)
    mov     [rsp], rax
    mov     rax, r10
    sub     rax, rbx                ; u-r
    sar     rax, 1                  ; b (exact: even)
    mov     [rsp+8], rax
    cmp     qword [rsp], 1
    jl      .fail
    cmp     qword [rsp], SQM_PAY
    jg      .fail
    cmp     qword [rsp+8], 1
    jl      .fail
    cmp     qword [rsp+8], SQM_PAY
    jg      .fail
    mov     rax, [rsp]
    cmp     rax, [rsp+8]            ; a != b ?
    je      .fail
    mov     rbx, [rsp+8]            ; b
    mov     rax, r13
    mov     rcx, r12
    imul    rcx, rbx                ; D0*b
    sub     rax, rcx                ; D1-D0*b
    mov     rcx, [rsp]
    sub     rcx, rbx                ; a-b (nonzero)
    cqo
    idiv    rcx
    test    rdx, rdx                ; divisible ?
    jnz     .fail
    mov     [rsp+16], rax           ; da
    test    rax, rax                ; da != 0 ?
    jz      .fail
    cmp     rax, 255
    jg      .fail
    cmp     rax, -255
    jl      .fail
    mov     rax, r12
    sub     rax, [rsp+16]           ; db = D0-da
    mov     rbx, rax
    test    rbx, rbx
    jz      .fail
    cmp     rbx, 255
    jg      .fail
    cmp     rbx, -255
    jl      .fail
    mov     rax, [rsp+16]           ; da*a*a
    imul    rax, [rsp]
    imul    rax, [rsp]
    mov     rcx, rbx                ; db*b*b
    imul    rcx, [rsp+8]
    imul    rcx, [rsp+8]
    add     rax, rcx
    cmp     rax, r14                ; == D2 ?
    jne     .fail
    mov     rax, [rsp+16]           ; da*a*a*a
    imul    rax, [rsp]
    imul    rax, [rsp]
    imul    rax, [rsp]
    mov     rcx, rbx                ; db*b*b*b
    imul    rcx, [rsp+8]
    imul    rcx, [rsp+8]
    imul    rcx, [rsp+8]
    add     rax, rcx
    cmp     rax, r15                ; == D3 ?
    jne     .fail
    mov     rax, [rsp+24]
    mov     ecx, [rsp]              ; a
    mov     [rax], ecx              ; *p1 = a
    mov     rax, [rsp+32]
    mov     ecx, [rsp+16]           ; da
    mov     [rax], ecx              ; *d1 = da
    mov     rax, [rsp+40]
    mov     ecx, [rsp+8]            ; b
    mov     [rax], ecx              ; *p2 = b
    mov     rax, [rsp+48]
    mov     [rax], ebx              ; *d2 = db
    mov     eax, 2
    jmp     .done
.fail:
    xor     eax, eax
.done:
    add     rsp, 64
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- fill: rdi = buf[64], esi = item --
; sqm_core.h sqm_fill
fill:
    imul    r8d, esi, 17
    xor     ecx, ecx
.f_loop:
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, r8d
    xor     eax, 0xA5
    mov     [rdi+rcx], al
    inc     ecx
    cmp     ecx, SQM_PAY
    jne     .f_loop
    ret

; -- pay_ok: rdi = buf[64], esi = item -> eax 0/1 --
pay_ok:
    imul    r8d, esi, 17
    xor     ecx, ecx
.ok_loop:
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, r8d
    xor     eax, 0xA5
    cmp     [rdi+rcx], al
    jne     .fail
    inc     ecx
    cmp     ecx, SQM_PAY
    jne     .ok_loop
    mov     eax, 1
    ret
.fail:
    xor     eax, eax
    ret
mem_cpy:
    rep     movsb
    ret

; -- compute_halves: rdi = incoming[64]; reads t_mi; writes t_mh0/t_mh1 --
; The SQM_COMPUTE_HALVES macro as a helper. Pure function of incoming+mi,
; so call sites may call it unconditionally (C skips recompute for speed;
; recomputing is bit-identical). All ops mod 2^64, as in C.
compute_halves:
    push    rbx
    push    r12
    mov     rbx, rdi                ; incoming
    mov     rdi, rbx                ; mom(incoming, 0, 32, t_mh0)
    xor     esi, esi
    mov     edx, SQM_HALF
    lea     rcx, [t_mh0]
    call    mom
    mov     r12, [t_mi]             ; s0 = mi.s0 - mh0.s0
    sub     r12, [t_mh0]
    mov     rax, [t_mi+8]           ; g1 = mi.s1 - mh0.s1
    sub     rax, [t_mh0+8]
    mov     rdx, [t_mi+16]          ; g2
    sub     rdx, [t_mh0+16]
    mov     rsi, [t_mi+24]          ; g3
    sub     rsi, [t_mh0+24]
    ; s3 = g3 - 96*g2 + 3072*g1 - 32768*s0 (H=32, all mod 2^64)
    mov     r8, rsi
    mov     r9, 96
    imul    r9, rdx
    sub     r8, r9
    mov     r9, 3072
    imul    r9, rax
    add     r8, r9
    mov     r9, 32768
    imul    r9, r12
    sub     r8, r9
    mov     [t_mh1+24], r8
    ; s2 = g2 - 64*g1 + 1024*s0
    mov     r8, rdx
    mov     r9, 64
    imul    r9, rax
    sub     r8, r9
    mov     r9, 1024
    imul    r9, r12
    add     r8, r9
    mov     [t_mh1+16], r8
    ; s1 = g1 - 32*s0
    mov     r8, 32
    imul    r8, r12
    sub     rax, r8
    mov     [t_mh1+8], rax
    mov     [t_mh1], r12            ; s0
    pop     r12
    pop     rbx
    ret

; -- sqm_write: rdi = cell, esi = id, edx = item, rcx = incoming -> eax --
; sqm_core.h sqm_write. rbx=cell, r12d=id, r13d=item, r14=incoming,
; r15d=slot. Frame [rsp..+12]: p1,d1,p2,d2 ; [rsp+16]: npt spill.
sqm_write:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 24
    mov     rbx, rdi
    mov     r12d, esi
    mov     r13d, edx
    mov     r14, rcx
    cmp     esi, SQM_CAP4
    jae     .no_slot
    lea     rax, [slot_of]
    mov     eax, [rax+rsi*4]
    mov     r15d, eax
    jmp     .have_slot
.no_slot:
    mov     r15d, -1
.have_slot:
    mov     rdi, r14
    xor     esi, esi
    mov     edx, SQM_PAY
    lea     rcx, [t_mi]
    call    mom
    cmp     r15d, 0
    jl      .first
    mov     eax, r15d               ; root addr from slot
    mov     ecx, eax
    shr     ecx, 8
    and     eax, 0xFF
    shl     ecx, 5
    add     ecx, eax                ; idx
    mov     eax, ecx
    shl     rax, 5                  ; idx*32
    lea     rdi, [t_mi]
    lea     rsi, [rbx+ROOT_OFF+rax]
    call    mom_eq
    test    eax, eax
    jz      .delta
    inc     qword [rbx+C_SKIPS]     ; recognition: 0 rd, 0 wr
    xor     eax, eax
    jmp     .done
.first:
    mov     rdi, r14
    call    compute_halves
    mov     eax, r12d               ; scatter alloc
    and     eax, 31
    lea     rdx, [SCATLT]
    mov     eax, [rdx+rax*4]
    xor     edx, edx
    mov     ecx, SQM_NB
    div     ecx                     ; edx = b0
    xor     r10d, r10d              ; k
.search:
    mov     eax, edx
    add     eax, r10d
    cmp     eax, SQM_NB
    jb      .have_bin
    sub     eax, SQM_NB
.have_bin:
    cmp     dword [rbx+HEAD_OFF+rax*4], SQM_NR
    jb      .found
    inc     r10d
    cmp     r10d, SQM_NB
    jne     .search
    mov     eax, -1
    jmp     .done
.found:
    mov     r10d, eax               ; bin
    mov     r11d, [rbx+HEAD_OFF+rax*4]  ; g
    mov     eax, r10d               ; pay addr
    shl     eax, 5
    add     eax, r11d
    shl     rax, 6
    lea     rdi, [rbx+rax]
    mov     rsi, r14
    mov     ecx, SQM_PAY
    rep     movsb
    lea     rsi, [t_mi]             ; root = mi (32 B)
    mov     eax, r10d
    shl     eax, 5
    add     eax, r11d               ; idx
    mov     ecx, eax                ; keep idx
    shl     rax, 5                  ; idx*32
    lea     rdi, [rbx+ROOT_OFF+rax]
    mov     rax, [rsi]
    mov     [rdi], rax
    mov     rax, [rsi+8]
    mov     [rdi+8], rax
    mov     rax, [rsi+16]
    mov     [rdi+16], rax
    mov     rax, [rsi+24]
    mov     [rdi+24], rax
    shl     rcx, 6                  ; idx*64
    lea     rdi, [rbx+HALF_OFF+rcx] ; half[b][g][0] = mh0
    lea     rsi, [t_mh0]
    mov     rax, [rsi]
    mov     [rdi], rax
    mov     rax, [rsi+8]
    mov     [rdi+8], rax
    mov     rax, [rsi+16]
    mov     [rdi+16], rax
    mov     rax, [rsi+24]
    mov     [rdi+24], rax
    lea     rdi, [rbx+HALF_OFF+rcx+32]  ; half[b][g][1] = mh1
    lea     rsi, [t_mh1]
    mov     rax, [rsi]
    mov     [rdi], rax
    mov     rax, [rsi+8]
    mov     [rdi+8], rax
    mov     rax, [rsi+16]
    mov     [rdi+16], rax
    mov     rax, [rsi+24]
    mov     [rdi+24], rax
    mov     eax, r10d               ; idx again
    shl     eax, 5
    add     eax, r11d
    mov     byte [rbx+OCC_OFF+rax], 1
    lea     rdx, [item_at]
    mov     [rdx+rax*4], r13d       ; item_at = item
    mov     eax, r10d
    shl     eax, 8
    add     eax, r11d               ; (bin<<8)|g
    lea     rdx, [slot_of]
    mov     ecx, r12d               ; id
    mov     [rdx+rcx*4], eax
    inc     dword [rbx+HEAD_OFF+r10*4]
    inc     dword [rbx+TOTAL_OFF]
    inc     qword [rbx+C_FULLW]
    add     qword [rbx+C_BWRITTEN], SQM_PAY
    xor     eax, eax
    jmp     .done
.delta:
    mov     eax, r15d
    mov     ecx, eax
    shr     ecx, 8
    mov     r12d, ecx               ; b (id dead)
    and     eax, 0xFF
    mov     r13d, eax               ; g (item dead)
    mov     eax, r12d
    shl     eax, 5
    add     eax, r13d
    mov     r15d, eax               ; idx
    shl     rax, 5                  ; idx*32
    lea     rsi, [rbx+ROOT_OFF+rax]
    lea     rdi, [t_mi]
    mov     rax, [rdi]
    sub     rax, [rsi]
    mov     [t_D], rax
    mov     rax, [rdi+8]
    sub     rax, [rsi+8]
    mov     [t_D+8], rax
    mov     rax, [rdi+16]
    sub     rax, [rsi+16]
    mov     [t_D+16], rax
    mov     rax, [rdi+24]
    sub     rax, [rsi+24]
    mov     [t_D+24], rax
    lea     rdi, [t_D]
    lea     rsi, [rsp]
    lea     rdx, [rsp+4]
    lea     rcx, [rsp+8]
    lea     r8, [rsp+12]
    call    solve
    mov     [rsp+16], eax           ; npt
    test    eax, eax
    jz      .slice
    mov     eax, r15d               ; pay addr
    shl     rax, 6
    lea     r10, [rbx+rax]
    mov     eax, [rsp]              ; p1
    dec     eax
    mov     cl, [r10+rax]
    add     cl, [rsp+4]             ; +d1 (low byte = full-int add truncated)
    inc     qword [rbx+C_BREAD]     ; the confirm-read counts even on mismatch
    cmp     cl, [r14+rax]           ; incoming[p1-1] ?
    jne     .escalate
    cmp     dword [rsp+16], 2
    jne     .apply1
    mov     eax, [rsp+8]            ; p2
    dec     eax
    mov     cl, [r10+rax]
    add     cl, [rsp+12]
    inc     qword [rbx+C_BREAD]
    cmp     cl, [r14+rax]
    jne     .escalate
.apply1:
    mov     eax, [rsp]              ; apply p1
    dec     eax
    mov     cl, [rsp+4]
    add     [r10+rax], cl
    inc     qword [rbx+C_BWRITTEN]
    cmp     dword [rsp+16], 2
    jne     .journal
    mov     eax, [rsp+8]
    dec     eax
    mov     cl, [rsp+12]
    add     [r10+rax], cl
    inc     qword [rbx+C_BWRITTEN]
.journal:
    mov     eax, r15d               ; root = mi
    shl     rax, 5
    lea     rdi, [rbx+ROOT_OFF+rax]
    lea     rsi, [t_mi]
    mov     rax, [rsi]
    mov     [rdi], rax
    mov     rax, [rsi+8]
    mov     [rdi+8], rax
    mov     rax, [rsi+16]
    mov     [rdi+16], rax
    mov     rax, [rsi+24]
    mov     [rdi+24], rax
    mov     eax, [rsp]              ; point 1: p,d -> hj
    dec     eax
    mov     ecx, eax
    shr     ecx, 5                  ; h
    and     eax, 31
    inc     rax                     ; x
    mov     edx, r15d
    shl     edx, 1
    add     edx, ecx
    shl     rdx, 5
    lea     rdi, [rbx+HALF_OFF+rdx]
    mov     rsi, rax
    mov     edx, [rsp+4]            ; d1
    call    half_add
    cmp     dword [rsp+16], 2
    jne     .sec_done
    mov     eax, [rsp+8]            ; point 2
    dec     eax
    mov     ecx, eax
    shr     ecx, 5
    and     eax, 31
    inc     rax
    mov     edx, r15d
    shl     edx, 1
    add     edx, ecx
    shl     rdx, 5
    lea     rdi, [rbx+HALF_OFF+rdx]
    mov     rsi, rax
    mov     edx, [rsp+12]           ; d2
    call    half_add
.sec_done:
    inc     qword [rbx+C_SEC]
    xor     eax, eax
    jmp     .done
.escalate:
    inc     qword [rbx+C_CONF]
.slice:
    mov     rdi, r14
    call    compute_halves
    mov     eax, r15d
    shl     rax, 6
    lea     r10, [rbx+HALF_OFF+rax] ; half0
    lea     rdi, [t_mh0]
    mov     rsi, r10
    call    mom_eq
    xor     ecx, ecx
    test    eax, eax
    setz    cl
    mov     [rsp], ecx              ; dirty0 (p1 dead)
    mov     eax, r15d
    shl     rax, 6
    lea     r10, [rbx+HALF_OFF+rax+32]  ; half1
    lea     rdi, [t_mh1]
    mov     rsi, r10
    call    mom_eq
    xor     ecx, ecx
    test    eax, eax
    setz    cl                      ; dirty1
    cmp     ecx, [rsp]
    je      .full
    mov     eax, [rsp]              ; h = dirty0 ? 0 : 1
    test    eax, eax
    jz      .h1
    xor     r11d, r11d
    jmp     .have_h
.h1:
    mov     r11d, 1
.have_h:
    mov     eax, r15d
    shl     rax, 6
    mov     ecx, r11d
    shl     rcx, 5
    add     rax, rcx
    lea     r10, [rbx+rax]          ; sl
    lea     rsi, [r14+rcx]          ; isl = incoming + h*32
    add     qword [rbx+C_BREAD], SQM_HALF
    xor     r11d, r11d              ; nw
    xor     ecx, ecx
.cmp_loop:
    mov     al, [rsi+rcx]
    cmp     [r10+rcx], al
    je      .same
    mov     [r10+rcx], al
    inc     r11d
.same:
    inc     ecx
    cmp     ecx, SQM_HALF
    jne     .cmp_loop
    add     qword [rbx+C_BWRITTEN], r11
    inc     qword [rbx+C_HALFW]
    jmp     .store_journal
.full:
    mov     eax, r15d
    shl     rax, 6
    lea     rdi, [rbx+rax]
    mov     rsi, r14
    mov     ecx, SQM_PAY
    rep     movsb
    add     qword [rbx+C_BREAD], SQM_PAY
    add     qword [rbx+C_BWRITTEN], SQM_PAY
    inc     qword [rbx+C_FULLW]
.store_journal:
    mov     eax, r15d
    shl     rax, 5
    lea     rdi, [rbx+ROOT_OFF+rax]
    lea     rsi, [t_mi]
    mov     rax, [rsi]
    mov     [rdi], rax
    mov     rax, [rsi+8]
    mov     [rdi+8], rax
    mov     rax, [rsi+16]
    mov     [rdi+16], rax
    mov     rax, [rsi+24]
    mov     [rdi+24], rax
    mov     eax, r15d
    shl     rax, 6
    lea     rdi, [rbx+HALF_OFF+rax]
    lea     rsi, [t_mh0]
    mov     rax, [rsi]
    mov     [rdi], rax
    mov     rax, [rsi+8]
    mov     [rdi+8], rax
    mov     rax, [rsi+16]
    mov     [rdi+16], rax
    mov     rax, [rsi+24]
    mov     [rdi+24], rax
    mov     eax, r15d
    shl     rax, 6
    lea     rdi, [rbx+HALF_OFF+rax+32]
    lea     rsi, [t_mh1]
    mov     rax, [rsi]
    mov     [rdi], rax
    mov     rax, [rsi+8]
    mov     [rdi+8], rax
    mov     rax, [rsi+16]
    mov     [rdi+16], rax
    mov     rax, [rsi+24]
    mov     [rdi+24], rax
    xor     eax, eax
.done:
    add     rsp, 24
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbp
    pop     rbx
    ret

; -- half_add: rdi = &hj, rsi = x (u64), edx = d (i32, may be negative) --
; Pointwise journal update by linearity. (uint64_t)d wraps; all mod 2^64.
half_add:
    movsxd  rcx, edx                ; dc = (int64)d
    add     [rdi], rcx              ; s0
    imul    rcx, rsi                ; dc*x
    add     [rdi+8], rcx            ; s1
    mov     rax, rsi
    imul    rax, rsi                ; x^2
    movsxd  rcx, edx
    imul    rcx, rax                ; dc*x^2
    add     [rdi+16], rcx           ; s2
    imul    rax, rsi                ; x^3
    movsxd  rcx, edx
    imul    rcx, rax                ; dc*x^3
    add     [rdi+24], rcx           ; s3
    ret

; -- sweep: rdi = cell, rsi = action or 0 -> rax unresolved --
; sqm_core.h sqm_sweep. rbx=cell, r13=action, r14d=b, r15d=g, r12=unres.
; Frame [rsp..+12]: p1,d1,p2,d2.
sqm_sweep:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 24
    mov     rbx, rdi
    mov     r13, rsi
    xor     r12, r12
    xor     r14d, r14d              ; b
.b_loop:
    xor     r15d, r15d              ; g
.g_loop:
    mov     eax, r14d
    shl     eax, 5
    add     eax, r15d               ; idx
    cmp     byte [rbx+OCC_OFF+rax], 0
    je      .next
    test    r13, r13
    jz      .no_zero
    mov     byte [r13+rax], 0
.no_zero:
    shl     rax, 6                  ; idx*64
    lea     rdi, [rbx+rax]          ; pay
    xor     esi, esi
    mov     edx, SQM_PAY
    lea     rcx, [t_cur]
    call    mom
    mov     eax, r14d               ; root addr
    shl     eax, 5
    add     eax, r15d
    shl     rax, 5
    lea     rdi, [t_cur]
    lea     rsi, [rbx+ROOT_OFF+rax]
    call    mom_eq
    test    eax, eax
    jnz     .next
    test    r13, r13
    jz      .no_one
    mov     eax, r14d
    shl     eax, 5
    add     eax, r15d
    mov     byte [r13+rax], 1
.no_one:
    lea     rdi, [t_cur]            ; D = cur - root
    mov     eax, r14d
    shl     eax, 5
    add     eax, r15d
    shl     rax, 5
    lea     rsi, [rbx+ROOT_OFF+rax]
    mov     rax, [rdi]
    sub     rax, [rsi]
    mov     [t_D], rax
    mov     rax, [rdi+8]
    sub     rax, [rsi+8]
    mov     [t_D+8], rax
    mov     rax, [rdi+16]
    sub     rax, [rsi+16]
    mov     [t_D+16], rax
    mov     rax, [rdi+24]
    sub     rax, [rsi+24]
    mov     [t_D+24], rax
    lea     rdi, [t_D]
    lea     rsi, [rsp]
    lea     rdx, [rsp+4]
    lea     rcx, [rsp+8]
    lea     r8, [rsp+12]
    call    solve
    mov     [rsp+16], eax           ; npt
    test    eax, eax
    jz      .unres
    mov     eax, r14d               ; pay addr
    shl     eax, 5
    add     eax, r15d
    shl     rax, 6
    lea     r10, [rbx+rax]
    mov     ecx, [rsp]              ; p1
    dec     ecx
    mov     edx, [rsp+4]            ; d1
    sub     [r10+rcx], dl           ; pay[p1-1] -= d1 (byte wrap)
    cmp     dword [rsp+16], 2
    jne     .reverify
    mov     ecx, [rsp+8]            ; p2
    dec     ecx
    mov     edx, [rsp+12]           ; d2
    sub     [r10+rcx], dl
.reverify:
    mov     eax, r14d               ; re-verify mom
    shl     eax, 5
    add     eax, r15d
    shl     rax, 6
    lea     rdi, [rbx+rax]
    xor     esi, esi
    mov     edx, SQM_PAY
    lea     rcx, [t_cur]
    call    mom
    mov     eax, r14d
    shl     eax, 5
    add     eax, r15d
    shl     rax, 5
    lea     rdi, [t_cur]
    lea     rsi, [rbx+ROOT_OFF+rax]
    call    mom_eq
    test    eax, eax
    jz      .unres
    ; zero both halves, then recompute from the repaired payload
    mov     eax, r14d
    shl     eax, 5
    add     eax, r15d               ; idx
    shl     rax, 6
    shr     rax, 1                  ; idx*32
    lea     rdi, [rbx+HALF_OFF+rax]
    xor     eax, eax
    mov     [rdi], rax
    mov     [rdi+8], rax
    mov     [rdi+16], rax
    mov     [rdi+24], rax
    mov     [rdi+32], rax
    mov     [rdi+40], rax
    mov     [rdi+48], rax
    mov     [rdi+56], rax
    mov     eax, r14d               ; pay offset in rbp (survives mom calls)
    shl     eax, 5
    add     eax, r15d
    shl     rax, 6
    mov     rbp, rax
    lea     rdi, [rbx+rbp]          ; pay
    xor     esi, esi
    mov     edx, SQM_HALF
    shr     rbp, 1                  ; idx*32
    lea     rcx, [rbx+HALF_OFF+rbp] ; half0
    call    mom
    shl     rbp, 1                  ; idx*64
    lea     rdi, [rbx+rbp+32]       ; pay+32
    xor     esi, esi
    mov     edx, SQM_HALF
    shr     rbp, 1
    lea     rcx, [rbx+HALF_OFF+rbp+32]  ; half1
    call    mom
    jmp     .next
.unres:
    inc     r12
.next:
    inc     r15d
    cmp     r15d, SQM_NR
    jne     .g_loop
    inc     r14d
    cmp     r14d, SQM_NB
    jne     .b_loop
    mov     rax, r12
    add     rsp, 24
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbp
    pop     rbx
    ret
emit_f6w:
    mov     ecx, 6
    jmp     emit_fdec

emit_f2w:
    mov     ecx, 2
    jmp     emit_fdec
_start:
    mov     eax, [rsp]
    cmp     eax, 1
    jbe     .def
    mov     rsi, [rsp+16]
    call    atoi
    jmp     .have
.def:
    mov     eax, 1000
.have:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r12d, eax               ; rounds
    lea     rdi, [rng_main]
    mov     rsi, 0xCE27
    call    seed_rng
    call    check_avx2
    mov     [use_avx], al
    lea     rdi, [cell]             ; memset cell
    xor     eax, eax
    mov     ecx, CELL_QW
    rep     stosq
    lea     rdi, [slot_of]          ; slot_of[*] = -1
    mov     eax, -1
    mov     ecx, SQM_CAP4
    rep     stosd
    xor     r15d, r15d              ; build i = 0..255
.build:
    cmp     r15d, 256
    jae     .built
    mov     eax, r15d
    shl     rax, 6
    lea     rdi, [contents+rax]
    mov     esi, r15d
    call    fill
    mov     eax, r15d
    shl     rax, 6
    lea     rcx, [contents+rax]
    lea     rdi, [cell]
    mov     esi, r15d
    mov     edx, r15d
    call    sqm_write
    inc     r15d
    jmp     .build
.built:
    ; ---- O1: pure-skip rewrites ----
    xor     r15d, r15d              ; i
.o1:
    cmp     r15d, 256
    jae     .o1_done
    mov     rax, [cell+C_BREAD]
    mov     [t_b4r], rax
    mov     rax, [cell+C_BWRITTEN]
    mov     [t_b4w], rax
    mov     eax, r15d
    shl     rax, 6
    lea     rcx, [contents+rax]
    lea     rdi, [cell]
    mov     esi, r15d
    mov     edx, r15d
    call    sqm_write
    mov     rax, [cell+C_BREAD]
    cmp     rax, [t_b4r]
    jne     .o1_next
    mov     rax, [cell+C_BWRITTEN]
    cmp     rax, [t_b4w]
    jne     .o1_next
    lea     rdx, [slot_of]          ; pay[slot] vs contents[i]
    mov     eax, [rdx+r15*4]
    mov     ecx, eax
    shr     ecx, 8
    and     eax, 0xFF
    shl     ecx, 5
    add     ecx, eax                ; idx
    shl     rcx, 6
    lea     rdi, [cell+rcx]
    mov     eax, r15d
    shl     rax, 6
    lea     rsi, [contents+rax]
    mov     ecx, SQM_PAY
    call    mem_eq
    test    eax, eax
    jz      .o1_next
    inc     qword [ac_o1]
.o1_next:
    inc     r15d
    jmp     .o1
.o1_done:
    ; ---- O2/O3: 1-byte and 2-byte diff writes ----
    ; r13d = r, r14d = nmut, r15d = i, ebx = idx, r11d = k
    xor     r13d, r13d
.o2:
    cmp     r13d, r12d
    jae     .o2_done
    lea     rdi, [rng_main]
    call    rand_u32
    xor     edx, edx
    mov     ecx, 256
    div     ecx
    mov     r15d, edx               ; i
    mov     eax, r13d
    and     eax, 1
    inc     eax
    mov     r14d, eax               ; nmut = (r&1)?2:1
    mov     rax, [cell+C_BREAD]
    mov     [t_b4r], rax
    mov     rax, [cell+C_BWRITTEN]
    mov     [t_b4w], rax
    xor     r11d, r11d              ; k (xoshiro_ss preserves r11)
.k_loop:
    cmp     r11d, r14d
    jae     .mut_done
    lea     rdi, [rng_main]
    call    rand_u32
    xor     edx, edx
    mov     ecx, SQM_PAY
    div     ecx                     ; pos
    mov     r10d, edx
    lea     rdi, [rng_main]
    call    rand_u32
    xor     edx, edx
    mov     ecx, 255
    div     ecx
    inc     edx                     ; m
    mov     eax, r15d
    shl     rax, 6
    add     rax, r10
    xor     byte [contents+rax], dl ; contents[i][pos] ^= m
    inc     r11d
    jmp     .k_loop
.mut_done:
    mov     eax, r15d
    shl     rax, 6
    lea     rcx, [contents+rax]
    lea     rdi, [cell]
    mov     esi, r15d
    mov     edx, r15d
    call    sqm_write
    lea     rax, [slot_of]          ; b,g,idx
    mov     eax, [rax+r15*4]
    mov     ecx, eax
    shr     ecx, 8
    and     eax, 0xFF
    shl     ecx, 5
    add     ecx, eax
    mov     ebx, ecx                ; idx (callee-saved across calls)
    mov     eax, ebx
    shl     rax, 6
    lea     rdi, [cell+rax]         ; pay
    mov     eax, r15d
    shl     rax, 6
    lea     rsi, [contents+rax]
    mov     ecx, SQM_PAY
    call    mem_eq
    mov     ebp, eax                ; ok (ebp: mom uses r11, not this)
    mov     eax, ebx                ; chk = mom(pay,0,64)
    shl     rax, 6
    lea     rdi, [cell+rax]
    xor     esi, esi
    mov     edx, SQM_PAY
    lea     rcx, [t_chk]
    call    mom
    mov     eax, ebx                ; root addr
    shl     rax, 5
    lea     rdi, [t_chk]
    lea     rsi, [cell+ROOT_OFF+rax]
    call    mom_eq
    and     ebp, eax                ; ok &&= journal closure
    add     qword [ac_o2ok], rbp
    inc     qword [ac_o2n]
    mov     rax, [cell+C_BREAD]     ; deltas by nmut
    sub     rax, [t_b4r]
    mov     rdx, [cell+C_BWRITTEN]
    sub     rdx, [t_b4w]
    cmp     r14d, 1
    jne     .nmut2
    add     qword [ac_rd1], rax
    add     qword [ac_wr1], rdx
    inc     qword [ac_n1]
    jmp     .r_next
.nmut2:
    add     qword [ac_rd2], rax
    add     qword [ac_wr2], rdx
    inc     qword [ac_n2]
.r_next:
    inc     r13d
    jmp     .o2
.o2_done:
    ; ---- O4: corruption + sweep ----
    lea     rsi, [cell]             ; snap all three
    lea     rdi, [snap]
    mov     ecx, CELL_QW
    rep     movsq
    lea     rsi, [contents]
    lea     rdi, [csnap]
    mov     ecx, 2048
    rep     movsq
    lea     rsi, [slot_of]
    lea     rdi, [slot_snap]
    mov     ecx, 512
    rep     movsq
    xor     r13d, r13d              ; r
.o4:
    cmp     r13d, r12d
    jae     .o4_done
    lea     rsi, [snap]             ; restore all three
    lea     rdi, [cell]
    mov     ecx, CELL_QW
    rep     movsq
    lea     rsi, [csnap]
    lea     rdi, [contents]
    mov     ecx, 2048
    rep     movsq
    lea     rsi, [slot_snap]
    lea     rdi, [slot_of]
    mov     ecx, 512
    rep     movsq
    lea     rdi, [rng_main]         ; b = rand % 8
    call    rand_u32
    xor     edx, edx
    mov     ecx, SQM_NB
    div     ecx
    mov     r14d, edx               ; b
    lea     rdi, [rng_main]         ; g = rand % 32
    call    rand_u32
    xor     edx, edx
    mov     ecx, SQM_NR
    div     ecx
    mov     r15d, edx               ; g
    lea     rdi, [rng_main]         ; pos = rand % 64
    call    rand_u32
    xor     edx, edx
    mov     ecx, SQM_PAY
    div     ecx
    mov     r10d, edx               ; pos
    lea     rdi, [rng_main]         ; m = 1 + rand % 255
    call    rand_u32
    xor     edx, edx
    mov     ecx, 255
    div     ecx
    inc     edx
    mov     r11d, edx               ; m
    mov     eax, r14d               ; corrupt pay[b][g][pos]
    shl     eax, 5
    add     eax, r15d
    shl     rax, 6
    add     rax, r10
    lea     rdx, [cell+rax]
    xor     byte [rdx], r11b
    lea     rdi, [cell]
    lea     rsi, [action]
    call    sqm_sweep               ; rax = un
    add     qword [ac_unres], rax
    mov     eax, r14d               ; det = action[idx] != 0
    shl     eax, 5
    add     eax, r15d
    xor     ecx, ecx
    movzx   eax, byte [action+rax]
    test    eax, eax
    setnz   cl
    add     qword [ac_d4], rcx
    mov     eax, r14d               ; item = item_at[idx]
    shl     eax, 5
    add     eax, r15d
    lea     rdx, [item_at]
    mov     eax, [rdx+rax*4]
    shl     rax, 6
    lea     rsi, [csnap+rax]        ; truth
    mov     eax, r14d               ; pay addr
    shl     eax, 5
    add     eax, r15d
    shl     rax, 6
    lea     rdi, [cell+rax]
    mov     ecx, SQM_PAY
    call    mem_eq
    add     qword [ac_r4], rax
    inc     qword [ac_n4]
    inc     r13d
    jmp     .o4
.o4_done:
    lea     rsi, [snap]             ; final restore
    lea     rdi, [cell]
    mov     ecx, CELL_QW
    rep     movsq
    lea     rsi, [csnap]
    lea     rdi, [contents]
    mov     ecx, 2048
    rep     movsq
    lea     rsi, [slot_snap]
    lea     rdi, [slot_of]
    mov     ecx, 512
    rep     movsq
    ; ---- O5: blindness retreat (r13d=b, r14d=g, r15d=o, r12=pay) ----
    xor     r13d, r13d
.o5b:
    cmp     r13d, SQM_NB
    jae     .o5_done
    xor     r14d, r14d
.o5g:
    cmp     r14d, SQM_NR
    jae     .b_next
    mov     eax, r13d
    shl     eax, 5
    add     eax, r14d
    shl     rax, 6
    lea     r12, [cell+rax]         ; pay (survives mom: r12 saved)
    xor     r15d, r15d              ; o
.o5o:
    cmp     r15d, 60
    jae     .o5o_done
    mov     rax, [ac_qn]            ; quad guard
    cmp     rax, 2000
    jae     .quad_skip
    movzx   eax, byte [r12+r15]
    cmp     eax, 255
    jae     .quad_skip
    movzx   eax, byte [r12+r15+1]
    cmp     eax, 3
    jb      .quad_skip
    movzx   eax, byte [r12+r15+2]
    cmp     eax, 252
    ja      .quad_skip
    movzx   eax, byte [r12+r15+3]
    cmp     eax, 1
    jb      .quad_skip
    mov     rdi, r12                ; before = mom(pay,0,64)
    xor     esi, esi
    mov     edx, SQM_PAY
    lea     rcx, [t_before]
    call    mom
    inc     byte [r12+r15]          ; +1,-3,+3,-1
    sub     byte [r12+r15+1], 3
    add     byte [r12+r15+2], 3
    sub     byte [r12+r15+3], 1
    mov     rdi, r12                ; after
    xor     esi, esi
    mov     edx, SQM_PAY
    lea     rcx, [t_after]
    call    mom
    lea     rdi, [t_after]          ; D = after - before
    lea     rsi, [t_before]
    mov     rax, [rdi]
    sub     rax, [rsi]
    mov     [t_D], rax
    mov     rax, [rdi+8]
    sub     rax, [rsi+8]
    mov     [t_D+8], rax
    mov     rax, [rdi+16]
    sub     rax, [rsi+16]
    mov     [t_D+16], rax
    mov     rax, [rdi+24]
    sub     rax, [rsi+24]
    mov     [t_D+24], rax
    lea     rdi, [t_D]
    lea     rsi, [zero32]
    call    mom_eq
    xor     ecx, ecx                ; caught += (D != 0) = (eq == 0)
    test    eax, eax
    setz    cl
    add     qword [ac_qc], rcx
    inc     qword [ac_qn]
    dec     byte [r12+r15]          ; revert
    add     byte [r12+r15+1], 3
    sub     byte [r12+r15+2], 3
    add     byte [r12+r15+3], 1
.quad_skip:
    mov     rax, [ac_pn]            ; pent guard
    cmp     rax, 2000
    jae     .o5_next
    movzx   eax, byte [r12+r15]
    cmp     eax, 255
    jae     .o5_next
    movzx   eax, byte [r12+r15+1]
    cmp     eax, 4
    jb      .o5_next
    movzx   eax, byte [r12+r15+2]
    cmp     eax, 249
    ja      .o5_next
    movzx   eax, byte [r12+r15+3]
    cmp     eax, 4
    jb      .o5_next
    movzx   eax, byte [r12+r15+4]
    cmp     eax, 255
    jae     .o5_next
    mov     rdi, r12                ; before
    xor     esi, esi
    mov     edx, SQM_PAY
    lea     rcx, [t_before]
    call    mom
    inc     byte [r12+r15]          ; +1,-4,+6,-4,+1
    sub     byte [r12+r15+1], 4
    add     byte [r12+r15+2], 6
    sub     byte [r12+r15+3], 4
    inc     byte [r12+r15+4]
    mov     rdi, r12                ; after
    xor     esi, esi
    mov     edx, SQM_PAY
    lea     rcx, [t_after]
    call    mom
    lea     rdi, [t_before]
    lea     rsi, [t_after]
    call    mom_eq
    add     qword [ac_pb], rax      ; blind += eq
    inc     qword [ac_pn]
    dec     byte [r12+r15]          ; revert
    add     byte [r12+r15+1], 4
    sub     byte [r12+r15+2], 6
    add     byte [r12+r15+3], 4
    dec     byte [r12+r15+4]
.o5_next:
    inc     r15d
    jmp     .o5o
.o5o_done:
    inc     r14d                    ; next g
    jmp     .o5g
.b_next:
    inc     r13d                    ; next b
    jmp     .o5b
.o5_done:
    jmp     .o6_start
.o6_start:
    ; ---- O6: hot-path window (200 rounds, cell snap/restore) ----
    lea     rsi, [cell]
    lea     rdi, [snap]
    mov     ecx, CELL_QW
    rep     movsq
    xor     r13d, r13d              ; r
.o6:
    cmp     r13d, 200
    jae     .o6_done
    lea     rsi, [snap]
    lea     rdi, [cell]
    mov     ecx, CELL_QW
    rep     movsq
    lea     rdi, [rng_main]         ; i = rand % 256
    call    rand_u32
    xor     edx, edx
    mov     ecx, 256
    div     ecx
    mov     r15d, edx               ; i
    lea     rax, [slot_of]
    mov     eax, [rax+r15*4]        ; slot -> b,g
    mov     ecx, eax
    shr     ecx, 8
    mov     r14d, ecx               ; b (callee-saved across write)
    and     eax, 0xFF
    mov     ebx, eax                ; g (callee-saved across write)
    lea     rdi, [rng_main]         ; pos = rand % 64
    call    rand_u32
    xor     edx, edx
    mov     ecx, SQM_PAY
    div     ecx
    mov     r10d, edx               ; pos
    lea     rdi, [rng_main]         ; m = 1 + rand % 255
    call    rand_u32
    xor     edx, edx
    mov     ecx, 255
    div     ecx
    inc     edx                     ; m in edx
    mov     eax, r14d               ; corrupt pay[b][g][pos]
    shl     eax, 5
    add     eax, ebx
    shl     rax, 6
    add     rax, r10
    lea     rcx, [cell+rax]
    xor     byte [rcx], dl
    mov     eax, r15d               ; write(cell,i,i,contents[i])
    shl     rax, 6
    lea     rcx, [contents+rax]
    lea     rdi, [cell]
    mov     esi, r15d
    mov     edx, r15d
    call    sqm_write
    mov     eax, r14d               ; blind += (pay != contents[i])
    shl     eax, 5
    add     eax, ebx
    shl     rax, 6
    lea     rdi, [cell+rax]
    mov     eax, r15d
    shl     rax, 6
    lea     rsi, [contents+rax]
    mov     ecx, SQM_PAY
    call    mem_eq
    xor     ecx, ecx
    test    eax, eax
    setz    cl                      ; 1 when different
    add     qword [ac_o6b], rcx
    inc     qword [ac_o6n]
    inc     r13d
    jmp     .o6
.o6_done:
    lea     rsi, [snap]             ; final restore
    lea     rdi, [cell]
    mov     ecx, CELL_QW
    rep     movsq
    ; ---- emit the 9 oracle lines ----
    lea     rsi, [Q1A]
    mov     rdx, Q1A_LEN
    call    emit_str
    mov     rax, [ac_o1]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, 256
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [ac_o1]
    mov     rdx, 256
    call    ratio_fx
    call    emit_f6w
    lea     rsi, [Q1B]
    mov     rdx, Q1B_LEN
    call    emit_str
    lea     rsi, [Q2A]
    mov     rdx, Q2A_LEN
    call    emit_str
    mov     rax, [ac_o2ok]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [ac_o2n]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [ac_o2ok]
    mov     rdx, [ac_o2n]
    call    ratio_fx
    call    emit_f6w
    lea     rsi, [Q2B]
    mov     rdx, Q2B_LEN
    call    emit_str
    lea     rsi, [Q3A]
    mov     rdx, Q3A_LEN
    call    emit_str
    mov     rax, [ac_rd1]
    mov     rdx, [ac_n1]
    call    ratio_fx
    call    emit_f2w
    lea     rsi, [Q3B]
    mov     rdx, Q3B_LEN
    call    emit_str
    mov     rax, [ac_wr1]
    mov     rdx, [ac_n1]
    call    ratio_fx
    call    emit_f2w
    lea     rsi, [Q3C]
    mov     rdx, Q3C_LEN
    call    emit_str
    mov     rax, [ac_rd2]
    mov     rdx, [ac_n2]
    call    ratio_fx
    call    emit_f2w
    lea     rsi, [Q3B]
    mov     rdx, Q3B_LEN
    call    emit_str
    mov     rax, [ac_wr2]
    mov     rdx, [ac_n2]
    call    ratio_fx
    call    emit_f2w
    lea     rsi, [Q3D]
    mov     rdx, Q3D_LEN
    call    emit_str
    lea     rsi, [Q4A]
    mov     rdx, Q4A_LEN
    call    emit_str
    mov     rax, [ac_d4]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [ac_n4]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [ac_d4]
    mov     rdx, [ac_n4]
    call    ratio_fx
    call    emit_f6w
    lea     rsi, [Q4B]
    mov     rdx, Q4B_LEN
    call    emit_str
    lea     rsi, [Q5A]
    mov     rdx, Q5A_LEN
    call    emit_str
    mov     rax, [ac_r4]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [ac_n4]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [ac_r4]
    mov     rdx, [ac_n4]
    call    ratio_fx
    call    emit_f6w
    lea     rsi, [Q5B]
    mov     rdx, Q5B_LEN
    call    emit_str
    lea     rsi, [Q6A]
    mov     rdx, Q6A_LEN
    call    emit_str
    mov     rax, [ac_unres]
    call    emit_u64
    lea     rsi, [Q6B]
    mov     rdx, Q6B_LEN
    call    emit_str
    lea     rsi, [Q7A]
    mov     rdx, Q7A_LEN
    call    emit_str
    mov     rax, [ac_qc]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [ac_qn]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [ac_qc]
    mov     rdx, [ac_qn]
    call    ratio_fx
    call    emit_f6w
    lea     rsi, [Q7B]
    mov     rdx, Q7B_LEN
    call    emit_str
    lea     rsi, [Q8A]
    mov     rdx, Q8A_LEN
    call    emit_str
    mov     rax, [ac_pb]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [ac_pn]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [ac_pb]
    mov     rdx, [ac_pn]
    call    ratio_fx
    call    emit_f6w
    lea     rsi, [Q8B]
    mov     rdx, Q8B_LEN
    call    emit_str
    lea     rsi, [Q9A]
    mov     rdx, Q9A_LEN
    call    emit_str
    mov     rax, [ac_o6b]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [ac_o6n]
    call    emit_u64
    lea     rsi, [Q9B]
    mov     rdx, Q9B_LEN
    call    emit_str
    mov     eax, 1                  ; sys_write(1, outbuf, outcur)
    mov     edi, 1
    lea     rsi, [outbuf]
    mov     rdx, [outcur]
    syscall
    mov     eax, 60                 ; sys_exit(0)
    xor     edi, edi
    syscall

segment readable

SCATLT  dd  6,5,4,0,2,3,4,7,4,6,3,0,1,2,1,0,3,6,4,7,4,3,2,0,4,5,6,5,4,0,2,3
align 32
idx_off dd 0, 1, 2, 3, 4, 5, 6, 7
idx8    dd 8, 8, 8, 8, 8, 8, 8, 8
DBL_10  dq 10.0

; line literals copied verbatim from sqm_cert.c printf formats
Q1A db 'SQMOR O1_skip_exact    '
Q1A_LEN = $ - Q1A
Q1B db '  expect=1.000000 (0 rd 0 wr)', 0x0A
Q1B_LEN = $ - Q1B
Q2A db 'SQMOR O2_diff_correct  '
Q2A_LEN = $ - Q2A
Q2B db '  expect=1.000000 (content+journal closure)', 0x0A
Q2B_LEN = $ - Q2B
Q3A db 'SQMOR O3_amplification 1-byte: '
Q3A_LEN = $ - Q3A
Q3B db ' rd '
Q3B_LEN = $ - Q3B
Q3C db ' wr | 2-byte: '
Q3C_LEN = $ - Q3C
Q3D db ' wr (bytes/write)', 0x0A
Q3D_LEN = $ - Q3D
Q4A db 'SQMOR O4_sweep_det     '
Q4A_LEN = $ - Q4A
Q4B db '  expect=1.000000 counting', 0x0A
Q4B_LEN = $ - Q4B
Q5A db 'SQMOR O4_sweep_rep     '
Q5A_LEN = $ - Q5A
Q5B db '  expect>=0.990 measurement', 0x0A
Q5B_LEN = $ - Q5B
Q6A db 'SQMOR O4_unresolved    '
Q6A_LEN = $ - Q6A
Q6B db '  expect=0', 0x0A
Q6B_LEN = $ - Q6B
Q7A db 'SQMOR O5_quad_caught   '
Q7A_LEN = $ - Q7A
Q7B db '  expect=1.000000 (blind to SQ5, caught by s3)', 0x0A
Q7B_LEN = $ - Q7B
Q8A db 'SQMOR O5_pent_blind    '
Q8A_LEN = $ - Q8A
Q8B db '  expect=1.000000 documented-exclusion', 0x0A
Q8B_LEN = $ - Q8B
Q9A db 'SQMOR O6_skip_window   '
Q9A_LEN = $ - Q9A
Q9B db ' stale-after-skip  expect=all-stale documented-window (sweep closes it)', 0x0A
Q9B_LEN = $ - Q9B
QSL db '/'
QEQ db ' = '

segment readable writeable

cell      rq CELL_QW
snap      rq CELL_QW
contents  rb 16384
csnap     rb 16384
slot_of   rd SQM_CAP4
slot_snap rd SQM_CAP4
item_at   rd SQM_CAP
action    rb SQM_CAP
rng_main  rb 32
t_mi      rq 4
t_mh0     rq 4
t_mh1     rq 4
t_D       rq 4
t_cur     rq 4
t_before  rq 4
t_after   rq 4
t_chk     rq 4
zero32    rq 4
hstmp     rd 4
use_avx   rb 1
t_b4r     rq 1
t_b4w     rq 1
ac_o1     rq 1
ac_o2ok   rq 1
ac_o2n    rq 1
ac_rd1    rq 1
ac_wr1    rq 1
ac_n1     rq 1
ac_rd2    rq 1
ac_wr2    rq 1
ac_n2     rq 1
ac_d4     rq 1
ac_r4     rq 1
ac_n4     rq 1
ac_unres  rq 1
ac_qc     rq 1
ac_qn     rq 1
ac_pb     rq 1
ac_pn     rq 1
ac_o6b    rq 1
ac_o6n    rq 1
numbuf    rb 32
fdigits   rb 8
outbuf    rb 8192
outcur    rq 1
tsbuf     rq 2

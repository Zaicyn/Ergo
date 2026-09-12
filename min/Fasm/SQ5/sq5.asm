; SQ5 certification driver in flat assembler (FASM 1.73.x, x86-64 Linux).
; Faithful port of SQ5/sq5_cert.c + sq5_core.h + the RNG from SQ5/common.h
; (xoshiro256** — note: sq2b.asm's "xoshiro256++" label is wrong, its code
; is **; this file labels it correctly). Goal: byte-identical stdout to
; sq5_cert plus byte-identical sq5_audit.txt (feeds sq5_mirror.py as O8).
;
; Internal ABI: args in rdi,rsi,rdx,rcx,r8,r9 (SysV-like), result in
; rax (xmm0 for doubles). rbx,rbp,r12-r15 are callee-saved everywhere.
; No libc: BSS arena, raw syscalls (openat/read/write/close/exit,
; clock_gettime), own %lld/%.6f/%.0f/%02x formatting.
;
; Layout (from sq5_core.h; NB=8 NR=32 PAY=64 BINBYTES=2048 CAPACITY=256):
;   pay   @0      : 8*32*2*64 = 32768 B
;   stamp @32768  : 8*32*2 u32 = 2048 B
;   occ   @34816  : 8*32*2 i8 = 512 B
;   twhead@35328  : 8 int = 32 B
;   ttotal@35360  : int = 4 B
;   jr    @35364  : 8*2*12 B = 192 B   (TORUS_SZ = 35556)
; decision = flags@0 ds[6]@4 cls@28 sec_p[2]@32 tier[2]@40 unresolved@48 (52 B)
; event = cat@0 b@4 g@8 shell@12 i@16 nbytes@20 m[2]@24 (28 B)
; Assemble: fasm sq5.asm sq5   (optional roundsA arg, default 1500)

format ELF64 executable 3
entry _start

SQ5_NB = 8
SQ5_NR = 32
SQ5_PAY = 64
SQ5_BINBYTES = 2048
SQ5_CAPACITY = 256

PAY_OFF = 0
STAMP_OFF = 32768
OCC_OFF = 34816
TWHEAD_OFF = 35328
TTOTAL_OFF = 35360
JR_OFF = 35364
TORUS_SZ = 35556

segment readable executable

; -- xoshiro256** : rdi = state ptr (4 qwords) -> rax --
; SQ5/common.h:61 cmp_xoshiro256ss
xoshiro_ss:
    mov     rax, [rdi]
    add     rax, [rdi+24]
    mov     rdx, [rdi+8]
    shl     rdx, 17
    mov     rcx, [rdi]
    xor     [rdi+16], rcx
    mov     rcx, [rdi+8]
    xor     [rdi+24], rcx
    mov     rcx, [rdi+16]
    xor     [rdi+8], rcx
    mov     rcx, [rdi+24]
    xor     [rdi], rcx
    xor     [rdi+16], rdx
    mov     rcx, [rdi+24]
    mov     rdx, rcx
    shl     rcx, 45
    shr     rdx, 19
    or      rcx, rdx
    mov     [rdi+24], rcx
    mov     rdx, rax
    shl     rax, 17
    shr     rdx, 47
    or      rax, rdx
    ret

; -- seed: rdi = state, rsi = seed --
; SQ5/common.h:81 cmp_seed
seed_rng:
    push    rbx
    push    r12                     ; counter (xoshiro clobbers rcx!)
    mov     rbx, rdi
    mov     rax, rsi
    mov     rcx, 0x9E3779B97F4A7C15
    add     rax, rcx
    mov     [rbx], rax
    mov     rax, rsi
    mov     rcx, 0xBF58476D1CE4E5B9
    xor     rax, rcx
    mov     [rbx+8], rax
    mov     rax, rsi
    mov     rcx, 0x94D049BB133111EB
    add     rax, rcx
    mov     [rbx+16], rax
    mov     rax, rsi
    mov     rcx, 0xF0BA35E12960E9E7
    xor     rax, rcx
    mov     [rbx+24], rax
    mov     r12d, 10
.seed_loop:
    mov     rdi, rbx
    call    xoshiro_ss
    dec     r12d
    jnz     .seed_loop
    pop     r12
    pop     rbx
    ret

; -- rand_u32: rdi = state -> eax --
rand_u32:
    push    rdi
    call    xoshiro_ss
    pop     rdi
    ret                             ; eax = low32 (C cast truncates)

; -- rand01: rdi = state -> xmm0 double in [0,1) --
; SQ5/common.h:77 — (x>>11) * 2^-53, exact in binary
rand01:
    push    rdi
    call    xoshiro_ss
    pop     rdi
    shr     rax, 11
    cvtsi2sd xmm0, rax
    mulsd   xmm0, [INV_2P53]
    ret

; -- now_sec: -> xmm0 = CLOCK_MONOTONIC seconds (double) --
; SQ5/common.h:52 cmp_now_sec. Timing only (SQ5T excluded from diff).
now_sec:
    mov     eax, 228
    mov     edi, 1
    lea     rsi, [tsbuf]
    syscall
    cvtsi2sd xmm0, qword [tsbuf]
    cvtsi2sd xmm1, qword [tsbuf+8]
    mulsd   xmm1, [DBL_1E_9]
    addsd   xmm0, xmm1
    ret

; -- cpy_torus: rdi = dst, rsi = src (35556 B) --
cpy_torus:
    push    rcx
    mov     ecx, 4444
    rep     movsq
    mov     ecx, 1
    rep     movsd
    pop     rcx
    ret

; -- sq5_tin: rdi = torus (memset 0) --
sq5_tin:
    push    rax
    push    rcx
    xor     eax, eax
    mov     ecx, 4444
    rep     stosq
    mov     ecx, 1
    rep     stosd
    pop     rcx
    pop     rax
    ret

; -- journal_add: rdi = journal, rsi = payload64, edx = gen --
; Scalar path (sq5_core.h:109). All mod-2^32 (32-bit regs wrap).
journal_add:
    cmp     byte [use_sse41], 0
    jne     journal_add_sse41
    push    rbx
    push    r12
    push    r13
    mov     ebx, edx
    shl     ebx, 6                  ; base = gen*64
    xor     r12d, r12d              ; i
.ja:
    cmp     r12d, 64
    jae     .done
    movzx   eax, byte [rsi+r12]     ; v
    lea     ecx, [ebx+r12d+1]       ; idx
    add     [rdi], eax              ; s0 += v
    mov     edx, eax
    imul    edx, ecx                ; v*idx
    add     [rdi+4], edx            ; s1
    imul    edx, ecx                ; v*idx*idx
    add     [rdi+8], edx            ; s2
    inc     r12d
    jmp     .ja
.done:
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- check_sse41: cpuid once -> [use_sse41] (ECX bit 19) --
check_sse41:
    mov     eax, 1
    cpuid                           ; clobbers rax,rbx,rcx,rdx (nothing live)
    test    ecx, 0x80000
    setnz   al
    mov     [use_sse41], al
    ret

; -- journal_add_sse41: rdi = journal, rsi = payload64, edx = gen --
; Same sums as scalar (integer mod-2^32: order-free). C SSE4.1 path shape.
journal_add_sse41:
    push    rbx
    push    r12
    mov     ebx, edx
    shl     ebx, 6                  ; base
    lea     eax, [ebx+1]
    mov     [sse_idx], eax
    lea     eax, [ebx+2]
    mov     [sse_idx+4], eax
    lea     eax, [ebx+3]
    mov     [sse_idx+8], eax
    lea     eax, [ebx+4]
    mov     [sse_idx+12], eax
    pxor    xmm0, xmm0              ; vs0
    pxor    xmm1, xmm1              ; vs1
    pxor    xmm2, xmm2              ; vs2
    movdqu  xmm3, dqword [sse_idx]   ; idxv
    movdqu  xmm10, dqword [sse_c4]   ; [4,4,4,4]
    xor     ecx, ecx                ; i
.jb:
    cmp     ecx, 64
    jae     .hs
    movdqu  xmm4, [rsi+rcx]         ; 16 payload bytes (kept whole block)
    ; vs0 += v0+v1+v2+v3
    movdqa  xmm5, xmm4
    pmovzxbd xmm6, xmm5
    psrldq  xmm5, 4
    pmovzxbd xmm7, xmm5
    psrldq  xmm5, 4
    pmovzxbd xmm8, xmm5
    psrldq  xmm5, 4
    pmovzxbd xmm9, xmm5
    paddd   xmm6, xmm7
    paddd   xmm8, xmm9
    paddd   xmm6, xmm8
    paddd   xmm0, xmm6
    ; vs1 += v0*i0+v1*i1+v2*i2+v3*i3
    movdqa  xmm5, xmm4
    pmovzxbd xmm6, xmm5
    psrldq  xmm5, 4
    pmovzxbd xmm7, xmm5
    psrldq  xmm5, 4
    pmovzxbd xmm8, xmm5
    psrldq  xmm5, 4
    pmovzxbd xmm9, xmm5
    movdqa  xmm5, xmm3              ; i0
    movdqa  xmm11, xmm5
    paddd   xmm11, xmm10            ; i1
    movdqa  xmm12, xmm11
    paddd   xmm12, xmm10            ; i2
    movdqa  xmm15, xmm12
    paddd   xmm15, xmm10            ; i3
    pmulld  xmm6, xmm5
    pmulld  xmm7, xmm11
    pmulld  xmm8, xmm12
    pmulld  xmm9, xmm15
    paddd   xmm6, xmm7
    paddd   xmm8, xmm9
    paddd   xmm6, xmm8
    paddd   xmm1, xmm6
    ; vs2 += v0*i0*i0+... (square lanes, then products)
    movdqa  xmm5, xmm4
    pmovzxbd xmm6, xmm5
    psrldq  xmm5, 4
    pmovzxbd xmm7, xmm5
    psrldq  xmm5, 4
    pmovzxbd xmm8, xmm5
    psrldq  xmm5, 4
    pmovzxbd xmm9, xmm5
    movdqa  xmm5, xmm3
    movdqa  xmm11, xmm5
    paddd   xmm11, xmm10
    movdqa  xmm12, xmm11
    paddd   xmm12, xmm10
    movdqa  xmm15, xmm12
    paddd   xmm15, xmm10
    pmulld  xmm5, xmm5
    pmulld  xmm11, xmm11
    pmulld  xmm12, xmm12
    pmulld  xmm15, xmm15
    pmulld  xmm6, xmm5
    pmulld  xmm7, xmm11
    pmulld  xmm8, xmm12
    pmulld  xmm9, xmm15
    paddd   xmm6, xmm7
    paddd   xmm8, xmm9
    paddd   xmm6, xmm8
    paddd   xmm2, xmm6
    ; idxv += 16 via dead xmm5
    movdqa  xmm5, xmm10
    paddd   xmm5, xmm5              ; 8
    paddd   xmm5, xmm5              ; 16
    paddd   xmm3, xmm5
    add     ecx, 16
    jmp     .jb
.hs:
    movdqu  dqword [sse_hs], xmm0
    mov     eax, dword [sse_hs]
    add     eax, dword [sse_hs+4]
    add     eax, dword [sse_hs+8]
    add     eax, dword [sse_hs+12]
    add     [rdi], eax
    movdqu  dqword [sse_hs], xmm1
    mov     eax, dword [sse_hs]
    add     eax, dword [sse_hs+4]
    add     eax, dword [sse_hs+8]
    add     eax, dword [sse_hs+12]
    add     [rdi+4], eax
    movdqu  dqword [sse_hs], xmm2
    mov     eax, dword [sse_hs]
    add     eax, dword [sse_hs+4]
    add     eax, dword [sse_hs+8]
    add     eax, dword [sse_hs+12]
    add     [rdi+8], eax
    pop     r12
    pop     rbx
    ret

; -- sq5_fill: rdi = payload64, esi = item --
sq5_fill:
    push    rbx
    mov     ebx, esi
    imul    ebx, ebx, 17
    xor     ecx, ecx
.fl:
    cmp     ecx, 64
    jae     .done
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, ebx
    xor     eax, 0xA5
    mov     [rdi+rcx], al
    inc     ecx
    jmp     .fl
.done:
    pop     rbx
    ret

; -- sq5_pay_ok: rdi = payload64, esi = item -> eax 1 ok / 0 --
sq5_pay_ok:
    push    rbx
    mov     ebx, esi
    imul    ebx, ebx, 17
    xor     ecx, ecx
.ck:
    cmp     ecx, 64
    jae     .ok
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, ebx
    xor     eax, 0xA5
    cmp     al, [rdi+rcx]
    jne     .bad
    inc     ecx
    jmp     .ck
.ok:
    mov     eax, 1
    pop     rbx
    ret
.bad:
    xor     eax, eax
    pop     rbx
    ret

; -- sq5_stamp: edi = bin, esi = gen, edx = shell -> eax --
sq5_stamp:
    mov     eax, esi
    shl     eax, 1
    and     eax, 31                 ; tbits
    shl     eax, 9
    mov     ecx, edi
    and     ecx, 7
    mov     ecx, [BINGEO+rcx*4]
    shl     ecx, 24
    or      eax, ecx
    shl     edi, 16                 ; bin<<16
    or      eax, edi
    and     edx, 1
    shl     edx, 8
    or      eax, edx
    or      eax, esi                ; gen (no field overlap)
    ret

; -- journal_recompute: rdi = torus, esi = b, edx = shell --
journal_recompute:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi
    mov     r12d, esi               ; b
    mov     r13d, edx               ; shell
    mov     eax, r12d
    shl     eax, 1
    add     eax, r13d               ; b*2+shell
    imul    eax, eax, 12
    lea     r14, [rbx+JR_OFF+rax]   ; jr[b][shell]
    mov     dword [r14], 0
    mov     dword [r14+4], 0
    mov     dword [r14+8], 0
    xor     r15d, r15d              ; g
.gr:
    cmp     r15d, 32
    jae     .done
    mov     eax, r12d
    shl     eax, 5                  ; b*32
    add     eax, r15d               ; +g
    shl     eax, 1                  ; *2
    add     eax, r13d               ; +shell
    cmp     byte [rbx+OCC_OFF+rax], 0
    je      .next                   ; !occ skip
    mov     ecx, eax
    shl     ecx, 6                  ; slot*64
    lea     rsi, [rbx+rcx]          ; pay[b][g][shell] (PAY_OFF=0)
    mov     rdi, r14
    mov     edx, r15d
    call    journal_add
.next:
    inc     r15d
    jmp     .gr
.done:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- sq5_alloc: rdi = torus, esi = id, edx = item -> eax 0 / -1 --
sq5_alloc:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi
    mov     r14d, edx               ; item
    mov     eax, esi
    and     eax, 31
    mov     eax, [SCATLT+rax*4]
    xor     edx, edx
    mov     ecx, 8
    div     ecx                     ; b0 = SCATLT % 8 (edx)
    mov     r12d, edx               ; b0
    xor     r13d, r13d              ; k
.scan:
    cmp     r13d, 8
    jae     .full
    mov     eax, r12d
    add     eax, r13d
    xor     edx, edx
    mov     ecx, 8
    div     ecx                     ; b = (b0+k) % 8 (edx)
    cmp     dword [rbx+TWHEAD_OFF+rdx*4], 32
    jb      .have_bin
    inc     r13d
    jmp     .scan
.have_bin:
    mov     r15d, edx               ; bin
    mov     eax, [rbx+TWHEAD_OFF+r15*4] ; gen
    mov     r12d, eax
    mov     ecx, r15d
    shl     ecx, 5                  ; bin*32
    add     ecx, eax                ; +gen
    shl     ecx, 1                  ; *2 shell0
    ; fill pay[bin][gen][0]
    mov     edx, ecx
    shl     edx, 6                  ; slot*64
    lea     rdi, [rbx+rdx]
    mov     esi, r14d
    call    sq5_fill                ; (slot recomputed after stamp call)
    ; stamp (sq5_stamp clobbers ecx,edx: recompute slot after)
    mov     edi, r15d
    mov     esi, r12d
    xor     edx, edx
    call    sq5_stamp
    push    rax                     ; save stamp value
    mov     ecx, r15d
    shl     ecx, 5                  ; bin*32
    add     ecx, r12d               ; +gen
    shl     ecx, 1                  ; *2 shell0
    mov     edx, ecx
    shl     edx, 2                  ; slot*4
    pop     rax
    mov     [rbx+STAMP_OFF+rdx], eax
    ; occ = 1
    mov     byte [rbx+OCC_OFF+rcx], 1
    ; journal_add(jr[bin][0], pay, gen)
    mov     eax, r15d
    shl     eax, 1                  ; bin*2+0
    imul    eax, eax, 12
    lea     rdi, [rbx+JR_OFF+rax]
    mov     edx, ecx
    shl     edx, 6
    lea     rsi, [rbx+rdx]
    mov     edx, r12d
    call    journal_add
    ; item_at[bin][gen] = item
    mov     eax, r15d
    shl     eax, 5
    add     eax, r12d
    mov     [item_at+rax*4], r14d
    inc     dword [rbx+TWHEAD_OFF+r15*4]
    inc     dword [rbx+TTOTAL_OFF]
    xor     eax, eax
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
.full:
    mov     rax, -1
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- sq5_rep: rdi = torus, rsi = flux_breaks ptr -> eax copied --
sq5_rep:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi
    mov     r12, rsi                ; breaks ptr
    xor     r13d, r13d              ; copied
    xor     r14d, r14d              ; b
.rb:
    cmp     r14d, 8
    jae     .flux
    xor     r15d, r15d              ; g
.rg:
    cmp     r15d, 32
    jae     .cmpjr
    mov     eax, r14d
    shl     eax, 5
    add     eax, r15d
    shl     eax, 1                  ; slot base (shell0)
    cmp     byte [rbx+OCC_OFF+rax], 0
    je      .rg_next
    ; memcpy pay shell1 <- shell0 (rep movsb: [rsi] -> [rdi])
    mov     ecx, eax
    shl     ecx, 6
    lea     rsi, [rbx+rcx]          ; src shell0
    lea     rdi, [rbx+rcx+64]       ; dst shell1
    push    rcx
    mov     ecx, 64
    rep     movsb
    pop     rcx
    ; stamp[b][g][1]
    mov     edi, r14d
    mov     esi, r15d
    mov     edx, 1
    push    rcx
    call    sq5_stamp
    pop     rcx                     ; rcx = slot*64
    mov     edx, ecx
    shr     edx, 4                  ; slot*4 (ecx is slot*64, not slot)
    mov     [rbx+STAMP_OFF+rdx+4], eax ; shell1 stamp
    shr     ecx, 6                  ; slot for occ below
    mov     byte [rbx+OCC_OFF+rcx+1], 1
    shl     ecx, 6                  ; back to slot*64 for pay below
    ; journal_add(jr[b][1], pay shell1, g)
    mov     eax, r14d
    shl     eax, 1
    add     eax, 1
    imul    eax, eax, 12
    lea     rdi, [rbx+JR_OFF+rax]
    lea     rsi, [rbx+rcx+64]
    mov     edx, r15d
    push    rcx
    call    journal_add
    pop     rcx
    inc     r13d
.rg_next:
    inc     r15d
    jmp     .rg
.cmpjr:
    ; jr[b][0] vs jr[b][1] (12 B)
    mov     eax, r14d
    shl     eax, 1
    imul    eax, eax, 12
    lea     rsi, [rbx+JR_OFF+rax]
    mov     ecx, [rsi]
    cmp     ecx, [rsi+12]
    jne     .brk
    mov     ecx, [rsi+4]
    cmp     ecx, [rsi+16]
    jne     .brk
    mov     ecx, [rsi+8]
    cmp     ecx, [rsi+20]
    je      .rb_next
.brk:
    inc     qword [r12]
.rb_next:
    inc     r14d
    jmp     .rb
.flux:
    mov     eax, r13d
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- flux_bin: rdi = torus, esi = b, rdx = ds[2][3] -> eax flags --
; Forward shell-0 stream + backward shell-1 stream, residuals vs journals.
; Accumulators live at [rsp] (no calls made here).
flux_bin:
    push    rbx
    push    r12
    sub     rsp, 24                 ; a0 a1 a2 c0 c1 c2
    mov     rbx, rdi                ; torus
    mov     r12, rdx                ; ds
    mov     dword [rsp], 0
    mov     dword [rsp+4], 0
    mov     dword [rsp+8], 0
    mov     dword [rsp+12], 0
    mov     dword [rsp+16], 0
    mov     dword [rsp+20], 0
    xor     r9d, r9d                ; g
.fg:
    cmp     r9d, 32
    jae     .fdone
    ; forward: gf = g, shell 0
    mov     eax, esi
    shl     eax, 5
    add     eax, r9d
    shl     eax, 1                  ; slot0
    cmp     byte [rbx+OCC_OFF+rax], 0
    je      .back
    mov     ecx, eax
    shl     ecx, 6                  ; byte base
    lea     rdi, [rbx+rcx]          ; pay base (2-reg addressing below)
    mov     edx, r9d
    shl     edx, 6                  ; mbase = gf*64
    xor     r10d, r10d              ; i
.fa:
    cmp     r10d, 64
    jae     .back
    movzx   r8d, byte [rdi+r10]
    lea     r11d, [rdx+r10+1]       ; idx
    add     [rsp], r8d              ; a0
    imul    r8d, r11d
    add     [rsp+4], r8d            ; a1
    imul    r8d, r11d
    add     [rsp+8], r8d            ; a2
    inc     r10d
    jmp     .fa
.back:
    ; backward: gb = 31-g, shell 1 (same idx formula; order irrelevant)
    mov     eax, 31
    sub     eax, r9d                ; gb
    mov     edx, esi
    shl     edx, 5
    add     edx, eax
    shl     edx, 1
    add     edx, 1                  ; slot1
    cmp     byte [rbx+OCC_OFF+rdx], 0
    je      .gnext
    mov     ecx, edx
    shl     ecx, 6
    lea     rdi, [rbx+rcx]
    mov     edx, eax
    shl     edx, 6                  ; mbase = gb*64
    mov     r10d, 63                ; i
.ba:
    cmp     r10d, 0
    jl      .gnext
    movzx   r8d, byte [rdi+r10]
    lea     r11d, [rdx+r10+1]
    add     [rsp+12], r8d           ; c0
    imul    r8d, r11d
    add     [rsp+16], r8d           ; c1
    imul    r8d, r11d
    add     [rsp+20], r8d           ; c2
    dec     r10d
    jmp     .ba
.gnext:
    inc     r9d
    jmp     .fg
.fdone:
    ; jr0/jr1 bases
    mov     eax, esi
    shl     eax, 1
    imul    eax, eax, 12
    lea     r8, [rbx+JR_OFF+rax]    ; jr[b][0]
    mov     ecx, [rsp]
    sub     ecx, [r8]
    mov     [r12], ecx
    mov     ecx, [rsp+4]
    sub     ecx, [r8+4]
    mov     [r12+4], ecx
    mov     ecx, [rsp+8]
    sub     ecx, [r8+8]
    mov     [r12+8], ecx
    mov     ecx, [rsp+12]
    sub     ecx, [r8+12]
    mov     [r12+12], ecx
    mov     ecx, [rsp+16]
    sub     ecx, [r8+16]
    mov     [r12+16], ecx
    mov     ecx, [rsp+20]
    sub     ecx, [r8+20]
    mov     [r12+20], ecx
    xor     eax, eax                ; flags
    mov     ecx, [r12]
    or      ecx, [r12+4]
    or      ecx, [r12+8]
    jz      .noR0
    or      eax, 1
.noR0:
    mov     ecx, [r12+12]
    or      ecx, [r12+16]
    or      ecx, [r12+20]
    jz      .noR1
    or      eax, 2
.noR1:
    mov     ecx, [rsp]
    cmp     ecx, [rsp+12]
    jne     .rx
    mov     ecx, [rsp+4]
    cmp     ecx, [rsp+16]
    jne     .rx
    mov     ecx, [rsp+8]
    cmp     ecx, [rsp+20]
    je      .rxdone
.rx:
    or      eax, 4
.rxdone:
    add     rsp, 24
    pop     r12
    pop     rbx
    ret

; -- classify_bin: rdi = torus, esi = b, rdx = dec52, ecx = full --
sq5_classify_bin:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi
    mov     r12d, esi               ; b
    mov     r13, rdx                ; dec
    mov     r14d, ecx               ; full
    mov     rdi, r13
    xor     eax, eax
    mov     ecx, 6
    rep     stosq                   ; zero 48
    mov     dword [r13+48], 0       ; +unresolved
    mov     rdi, rbx
    mov     esi, r12d
    lea     rdx, [r13+4]            ; d->ds
    call    flux_bin                ; eax = flags
    mov     [r13], eax
    test    r14d, r14d
    jz      .legacy
    cmp     eax, 0
    je      .set0
    cmp     eax, 1
    je      .set1
    cmp     eax, 2
    je      .set2
    cmp     eax, 5                  ; R0|RX
    je      .set3
    cmp     eax, 6                  ; R1|RX
    je      .set4
    cmp     eax, 7                  ; R0|R1|RX
    je      .set5
    cmp     eax, 3                  ; R0|R1: memcmp ds equal?
    jne     .set7
    mov     eax, [r13+4]
    cmp     eax, [r13+16]
    jne     .set6
    mov     eax, [r13+8]
    cmp     eax, [r13+20]
    jne     .set6
    mov     eax, [r13+12]
    cmp     eax, [r13+24]
    jne     .set6
.set5:
    mov     dword [r13+28], 5
    jmp     .done
.set1:
    mov     dword [r13+28], 1
    jmp     .done
.set2:
    mov     dword [r13+28], 2
    jmp     .done
.set3:
    mov     dword [r13+28], 3
    jmp     .done
.set4:
    mov     dword [r13+28], 4
    jmp     .done
.set6:
    mov     dword [r13+28], 6
    jmp     .done
.set7:
    mov     dword [r13+28], 7
    jmp     .done
.set0:
    mov     dword [r13+28], 0
    jmp     .done
.legacy:
    test    eax, 1
    jz      .leg1
    mov     dword [r13+28], 3
.leg1:
    test    eax, 2
    jz      .done
    cmp     dword [r13+28], 3
    je      .legboth
    mov     dword [r13+28], 4
    jmp     .done
.legboth:
    mov     dword [r13+28], 5
.done:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- try_sec: rdi = torus, esi = b, edx = shell, rcx = ds3, r8 = used_p/0 --
; -> eax 1 repaired / 0. Signed C division semantics (idiv).
sq5_try_sec:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi                ; torus
    mov     r12d, esi               ; b
    mov     r13d, edx               ; shell
    mov     r14, rcx                ; ds
    mov     r15, r8                 ; used_p
    mov     r10d, [rcx]             ; d (signed; r10: cdq kills edx below)
    test    r10d, r10d
    jz      .fail
    cmp     r10d, 255
    jg      .fail
    cmp     r10d, -255
    jl      .fail
    mov     eax, [rcx+4]            ; ds1
    cdq
    idiv    r10d                    ; eax = p, edx = rem
    test    edx, edx
    jnz     .fail
    cmp     eax, 1
    jl      .fail
    cmp     eax, 2048
    jg      .fail
    mov     ecx, eax                ; p
    movsxd  rax, dword [r14]        ; d (64-bit)
    imul    rax, rcx
    imul    rax, rcx                ; d*p*p
    cmp     eax, [r14+8]            ; == ds[2] (low32)
    jne     .fail
    mov     eax, ecx
    dec     eax                     ; o = p-1
    mov     edx, eax
    shr     edx, 6                  ; g = o/64
    and     eax, 63                 ; i = o%64
    ; pay[b][g][shell][i] = (pay - d) & 0xFF
    mov     r10d, r12d
    shl     r10d, 5
    add     r10d, edx
    shl     r10d, 1
    add     r10d, r13d              ; slot
    mov     r11d, r10d
    shl     r11d, 6
    add     r11d, eax               ; byte offset
    movzx   r10d, byte [rbx+r11]
    mov     edx, [r14]              ; d
    sub     r10d, edx
    mov     [rbx+r11], r10b
    test    r15, r15
    jz      .ok
    mov     [r15], ecx              ; *used_p = p
.ok:
    mov     eax, 1
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
.fail:
    xor     eax, eax
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- tier2: rdi = torus, esi = b, edx = shell (copy from good=shell^1) --
sq5_tier2:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi
    mov     r12d, esi               ; b
    mov     r13d, edx               ; shell
    mov     r14d, edx
    xor     r14d, 1                 ; good
    mov     eax, r12d
    shl     eax, 1
    add     eax, r13d
    imul    eax, eax, 12
    lea     rdi, [rbx+JR_OFF+rax]   ; jr[b][shell]
    xor     eax, eax
    mov     ecx, 3
    rep     stosd                   ; zero journal (12 B)
    xor     r15d, r15d              ; g
.tg:
    cmp     r15d, 32
    jae     .done
    mov     eax, r12d
    shl     eax, 5
    add     eax, r15d
    shl     eax, 1                  ; slot base
    lea     rdi, [rbx+OCC_OFF+rax]
    cmp     byte [rdi+r14], 0
    je      .next                   ; !occ[good] skip
    ; memcpy pay shell <- good
    mov     ecx, eax
    add     ecx, r14d
    shl     ecx, 6
    lea     rsi, [rbx+rcx]          ; src good
    mov     ecx, eax
    add     ecx, r13d
    shl     ecx, 6
    lea     rdi, [rbx+rcx]          ; dst shell
    push    rax
    push    rcx
    mov     ecx, 64
    rep     movsb
    pop     rcx
    pop     rax
    ; stamp + occ
    mov     edi, r12d
    mov     esi, r15d
    mov     edx, r13d
    push    rax
    push    rcx
    call    sq5_stamp
    pop     rcx                     ; rcx = slot*64 (dst shell)
    pop     rax
    mov     edx, ecx
    shr     edx, 4                  ; slot*4 (ecx is slot*64, not slot)
    mov     [rbx+STAMP_OFF+rdx], eax
    shr     ecx, 6                  ; slot for occ below
    mov     byte [rbx+OCC_OFF+rcx], 1
    shl     ecx, 6                  ; back to slot*64 for pay below
    ; journal_add(jr[shell], pay shell, g)
    mov     edx, r12d
    shl     edx, 1
    add     edx, r13d
    imul    edx, edx, 12
    lea     rdi, [rbx+JR_OFF+rdx]
    lea     rsi, [rbx+rcx]
    mov     edx, r15d
    push    rax
    push    rcx
    call    journal_add
    pop     rcx
    pop     rax
.next:
    inc     r15d
    jmp     .tg
.done:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- apply_repair: rdi = torus, esi = b, rdx = dec52 --
sq5_apply_repair:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi
    mov     r12d, esi               ; b
    mov     r13, rdx                ; dec
    mov     eax, [rdx+28]           ; cls
    cmp     eax, 1
    je      .j0
    cmp     eax, 2
    je      .j1
    cmp     eax, 6
    je      .jpair
    cmp     eax, 3
    je      .p0
    cmp     eax, 4
    je      .p1
    cmp     eax, 5
    je      .pboth
    jmp     .closure                ; NONE/ANOMALY: nothing (closure skips too)
.j0:
    mov     rdi, rbx
    mov     esi, r12d
    xor     edx, edx
    call    journal_recompute
    mov     dword [r13+40], 3       ; tier[0]
    jmp     .closure
.j1:
    mov     rdi, rbx
    mov     esi, r12d
    mov     edx, 1
    call    journal_recompute
    mov     dword [r13+44], 3       ; tier[1]
    jmp     .closure
.jpair:
    mov     rdi, rbx
    mov     esi, r12d
    xor     edx, edx
    call    journal_recompute
    mov     rdi, rbx
    mov     esi, r12d
    mov     edx, 1
    call    journal_recompute
    mov     dword [r13+40], 3
    mov     dword [r13+44], 3
    jmp     .closure
.p0:
    mov     rdi, rbx
    mov     esi, r12d
    xor     edx, edx
    lea     rcx, [r13+4]
    lea     r8, [r13+32]            ; sec_p[0]
    call    sq5_try_sec
    test    eax, eax
    jz      .p0t2
    mov     dword [r13+40], 1
    jmp     .closure
.p0t2:
    mov     rdi, rbx
    mov     esi, r12d
    xor     edx, edx
    call    sq5_tier2
    mov     dword [r13+40], 2
    jmp     .closure
.p1:
    mov     rdi, rbx
    mov     esi, r12d
    mov     edx, 1
    lea     rcx, [r13+4+12]         ; ds[1]
    lea     r8, [r13+36]            ; sec_p[1]
    call    sq5_try_sec
    test    eax, eax
    jz      .p1t2
    mov     dword [r13+44], 1
    jmp     .closure
.p1t2:
    mov     rdi, rbx
    mov     esi, r12d
    mov     edx, 1
    call    sq5_tier2
    mov     dword [r13+44], 2
    jmp     .closure
.pboth:
    mov     rdi, rbx
    mov     esi, r12d
    xor     edx, edx
    lea     rcx, [r13+4]
    lea     r8, [r13+32]
    call    sq5_try_sec
    mov     r14d, eax               ; ok0
    mov     dword [r13+40], 0
    test    eax, eax
    jz      .pb1
    mov     dword [r13+40], 1
.pb1:
    mov     rdi, rbx
    mov     esi, r12d
    mov     edx, 1
    lea     rcx, [r13+4+12]
    lea     r8, [r13+36]
    call    sq5_try_sec
    mov     r15d, eax               ; ok1
    mov     dword [r13+44], 0
    test    eax, eax
    jz      .pbmix
    mov     dword [r13+44], 1
.pbmix:
    test    r14d, r14d
    jz      .pb_n0
    test    r15d, r15d
    jnz     .closure                ; both ok
    mov     rdi, rbx                ; ok0 only: tier2 shell1
    mov     esi, r12d
    mov     edx, 1
    call    sq5_tier2
    mov     dword [r13+44], 2
    jmp     .closure
.pb_n0:
    test    r15d, r15d
    jz      .pb_neither
    mov     rdi, rbx                ; ok1 only: tier2 shell0
    mov     esi, r12d
    xor     edx, edx
    call    sq5_tier2
    mov     dword [r13+40], 2
    jmp     .closure
.pb_neither:
    mov     dword [r13+48], 2       ; unresolved = 2
.closure:
    mov     eax, [r13+28]
    cmp     eax, 0
    je      .done
    cmp     eax, 7
    je      .done
    mov     rdi, rbx
    mov     esi, r12d
    lea     rdx, [flux_chk]
    call    flux_bin
    test    eax, eax
    jz      .done
    inc     dword [r13+48]           ; unresolved += flux != 0
.done:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- stamp_check: rdi = torus, esi = fix, rdx = badmap/0 -> rax bad --
sq5_stamp_check:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi
    mov     r12d, esi               ; fix
    mov     r13, rdx                ; badmap (0 = none)
    xor     r14d, r14d              ; b
    xor     r15d, r15d              ; bad count (64-bit)
.sb:
    cmp     r14d, 8
    jae     .done
    xor     r10d, r10d              ; g
.sg:
    cmp     r10d, 32
    jae     .sb_next
    xor     r11d, r11d              ; s
.ss:
    cmp     r11d, 2
    jae     .sg_next
    mov     eax, r14d
    shl     eax, 5
    add     eax, r10d
    shl     eax, 1
    add     eax, r11d               ; slot
    mov     ecx, eax                ; save slot
    cmp     byte [rbx+OCC_OFF+rax], 0
    je      .ss_next
    shl     ecx, 2                  ; slot*4
    mov     eax, [rbx+STAMP_OFF+rcx] ; actual
    mov     edi, r14d
    mov     esi, r10d
    mov     edx, r11d
    push    rcx
    push    r10
    push    r11
    call    sq5_stamp               ; want
    pop     r11
    pop     r10
    pop     rcx
    cmp     eax, [rbx+STAMP_OFF+rcx]
    je      .ss_next
    inc     r15
    test    r13, r13
    jz      .nofixchk
    ; slot = (b*32+g)*2+s recompute for bit ops
    mov     eax, r14d
    shl     eax, 5
    add     eax, r10d
    shl     eax, 1
    add     eax, r11d
    mov     edx, eax
    shr     edx, 6                  ; slot>>6
    and     eax, 63
    mov     ecx, eax                ; slot&63
    mov     r8, 1
    shl     r8, cl                  ; 1ULL << (slot&63)
    or      [r13+rdx*8], r8
.nofixchk:
    test    r12d, r12d
    jz      .ss_next
    mov     eax, r14d               ; recompute slot*4 (rcx died above)
    shl     eax, 5
    add     eax, r10d
    shl     eax, 1
    add     eax, r11d
    shl     eax, 2
    mov     ecx, eax
    mov     edi, r14d
    mov     esi, r10d
    mov     edx, r11d
    push    rcx
    push    r10
    push    r11
    call    sq5_stamp
    pop     r11
    pop     r10
    pop     rcx
    mov     [rbx+STAMP_OFF+rcx], eax
.ss_next:
    inc     r11d
    jmp     .ss
.sg_next:
    inc     r10d
    jmp     .sg
.sb_next:
    inc     r14d
    jmp     .sb
.done:
    mov     rax, r15
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- apply_event: rdi = torus, rsi = evt28 --
sq5_apply_event:
    push    rbx
    mov     rbx, rdi
    mov     eax, [rsi]              ; cat
    cmp     eax, 0
    je      .pay
    cmp     eax, 1
    je      .stamp
    ; JOUR: jr[b][shell] byte [i % 12] ^= m0
    mov     eax, [rsi+4]            ; b
    shl     eax, 1
    add     eax, [rsi+12]           ; +shell
    imul    eax, eax, 12
    lea     r8, [rbx+JR_OFF+rax]    ; jr byte base
    mov     eax, [rsi+16]           ; i
    xor     edx, edx
    mov     ecx, 12
    div     ecx                     ; edx = i % 12
    mov     al, [rsi+24]            ; m0
    xor     [r8+rdx], al
    pop     rbx
    ret
.pay:
    ; k = 0..nbytes-1: pay[b][g][shell][(i + k*7) % 64] ^= m[k]
    mov     eax, [rsi+4]            ; b
    shl     eax, 5
    add     eax, [rsi+8]            ; g
    shl     eax, 1
    add     eax, [rsi+12]           ; shell
    shl     eax, 6                  ; slot*64
    lea     r8, [rbx+rax]           ; pay base
    mov     r9d, [rsi+16]           ; i
    mov     r10d, [rsi+20]          ; nbytes
    xor     r11d, r11d              ; k
.payloop:
    cmp     r11d, r10d
    jae     .paydone
    mov     eax, r11d
    imul    eax, eax, 7
    add     eax, r9d                ; i + k*7
    xor     edx, edx
    mov     ecx, 64
    div     ecx                     ; edx = pos
    mov     al, [rsi+24+r11]        ; m[k]
    xor     [r8+rdx], al
    inc     r11d
    jmp     .payloop
.paydone:
    pop     rbx
    ret
.stamp:
    ; stamp[b][g][shell] byte [i & 3] ^= m0
    mov     eax, [rsi+4]
    shl     eax, 5
    add     eax, [rsi+8]
    shl     eax, 1
    add     eax, [rsi+12]
    shl     eax, 2                  ; slot*4
    lea     r8, [rbx+STAMP_OFF+rax]
    mov     eax, [rsi+16]
    and     eax, 3                  ; i & 3
    mov     cl, [rsi+24]            ; m0
    xor     [r8+rax], cl
    pop     rbx
    ret

; -- cert_round: rdi = torus, rsi = clean, rdx = rng, ecx = nev, --
;               r8d = cat_cycle, r9 = acc (scratch/dump via BSS) --
cert_round:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 8                  ; [rsp] = e counter
    mov     rbx, rdi                ; torus
    mov     rbp, rsi                ; clean
    mov     r12, rdx                ; rng
    mov     r13, r9                 ; acc
    mov     r14d, ecx               ; nev
    mov     r15d, r8d               ; cat_cycle
    mov     rdi, rbx
    mov     rsi, rbp
    call    cpy_torus               ; *torus = *clean
    mov     dword [rsp], 0          ; e = 0
.evloop:
    mov     eax, [rsp]
    cmp     eax, r14d
    jae     .classify
    imul    eax, eax, 28
    lea     r10, [evts+rax]         ; ev
    cmp     r15d, 0
    jge     .forced
    mov     rdi, r12
    call    rand01                  ; xmm0 = u
    comisd  xmm0, [DBL_070]
    jb      .catpay
    comisd  xmm0, [DBL_085]
    jb      .catstamp
    mov     eax, 2                  ; JOUR
    jmp     .havecat
.catpay:
    xor     eax, eax
    jmp     .havecat
.catstamp:
    mov     eax, 1
    jmp     .havecat
.forced:
    mov     eax, r15d
.havecat:
    mov     [r10], eax              ; ev.cat
    cmp     eax, 0
    je      .evpay
    cmp     eax, 1
    je      .evstamp
    ; JOUR fields: b, shell, i; g = 0
    mov     rdi, r12
    call    rand_u32
    xor     edx, edx
    mov     ecx, 8
    div     ecx
    mov     [r10+4], edx            ; b
    mov     dword [r10+8], 0        ; g
    mov     rdi, r12
    call    rand_u32
    and     eax, 1
    mov     [r10+12], eax           ; shell
    mov     dword [r10+20], 1       ; nbytes
    mov     rdi, r12
    call    rand_u32
    xor     edx, edx
    mov     ecx, 12
    div     ecx
    mov     [r10+16], edx           ; i
    mov     rdi, r12
    call    rand_u32
    xor     edx, edx
    mov     ecx, 255
    div     ecx
    inc     edx
    mov     [r10+24], dl            ; m0
    jmp     .applied
.evstamp:
    mov     rdi, r12
    call    rand_u32
    xor     edx, edx
    mov     ecx, 8
    div     ecx
    mov     [r10+4], edx
    mov     rdi, r12
    call    rand_u32
    xor     edx, edx
    mov     ecx, 32
    div     ecx
    mov     [r10+8], edx            ; g
    mov     rdi, r12
    call    rand_u32
    and     eax, 1
    mov     [r10+12], eax
    mov     dword [r10+20], 1
    mov     rdi, r12
    call    rand_u32
    xor     edx, edx
    mov     ecx, 4
    div     ecx
    mov     [r10+16], edx           ; i
    mov     rdi, r12
    call    rand_u32
    xor     edx, edx
    mov     ecx, 255
    div     ecx
    inc     edx
    mov     [r10+24], dl
    jmp     .applied
.evpay:
    mov     rdi, r12
    call    rand_u32
    xor     edx, edx
    mov     ecx, 8
    div     ecx
    mov     [r10+4], edx
    mov     rdi, r12
    call    rand_u32
    xor     edx, edx
    mov     ecx, 32
    div     ecx
    mov     [r10+8], edx
    mov     rdi, r12
    call    rand_u32
    and     eax, 1
    mov     [r10+12], eax
    mov     rdi, r12
    call    rand01
    comisd  xmm0, [DBL_080]
    jb      .nb1
    mov     dword [r10+20], 2
    jmp     .nbhave
.nb1:
    mov     dword [r10+20], 1
.nbhave:
    mov     rdi, r12
    call    rand_u32
    xor     edx, edx
    mov     ecx, 64
    div     ecx
    mov     [r10+16], edx           ; i
    xor     r11d, r11d              ; k
.mkloop:
    cmp     r11d, [r10+20]
    jae     .applied
    mov     rdi, r12
    push    r10
    push    r11
    call    rand_u32
    pop     r11
    pop     r10
    xor     edx, edx
    mov     ecx, 255
    div     ecx
    inc     edx
    mov     [r10+24+r11], dl        ; m[k]
    inc     r11d
    jmp     .mkloop
.applied:
    mov     rdi, rbx
    mov     rsi, r10
    push    r10
    call    sq5_apply_event
    pop     r10
    mov     eax, [r10]              ; cat
    inc     qword [r13+rax*8]       ; acc.cnt[cat]++
    inc     dword [rsp]             ; e++
    jmp     .evloop
.classify:
    ; zero badmap
    lea     rdi, [stamp_badmap]
    xor     eax, eax
    mov     ecx, 8
    rep     stosq
    call    now_sec
    movsd   [tsec0], xmm0
    mov     r15d, 0                 ; b
.cbloop:
    cmp     r15d, 8
    jae     .stamped
    mov     rdi, rbx
    mov     esi, r15d
    imul    eax, r15d, 52
    lea     rdx, [decis+rax]
    mov     ecx, 1                  ; full
    call    sq5_classify_bin
    inc     r15d
    jmp     .cbloop
.stamped:
    mov     rdi, rbx
    xor     esi, esi                ; fix = 0
    lea     rdx, [stamp_badmap]
    call    sq5_stamp_check         ; rax = sflag
    mov     [audit_sflag], rax
    add     [r13+104], rax          ; acc.stamp_flag += sflag
    call    now_sec
    movsd   [tsec1], xmm0
    mov     r15d, 0
.rploop:
    cmp     r15d, 8
    jae     .repaired
    mov     rdi, rbx
    mov     esi, r15d
    imul    eax, r15d, 52
    lea     rdx, [decis+rax]
    call    sq5_apply_repair
    inc     r15d
    jmp     .rploop
.repaired:
    mov     rdi, rbx
    mov     esi, 1                  ; fix = 1
    xor     edx, edx
    call    sq5_stamp_check
    call    now_sec
    movsd   [tsec2], xmm0
    movsd   xmm0, [tsec1]
    subsd   xmm0, [tsec0]
    movsd   xmm1, [tsec2]
    subsd   xmm1, [tsec1]
    addsd   xmm0, xmm1
    addsd   xmm0, [r13+112]         ; acc.t_full += ...
    movsd   [r13+112], xmm0
    ; legacy path on scratch (timing only)
    mov     rax, [cr_scratch]
    mov     rdi, rax
    mov     rsi, rbp
    call    cpy_torus               ; *scratch = *clean
    mov     dword [rsp], 0          ; e = 0
.legapp:
    mov     eax, [rsp]
    cmp     eax, r14d
    jae     .legtimed
    imul    eax, eax, 28
    lea     rsi, [evts+rax]
    mov     rdi, [cr_scratch]
    call    sq5_apply_event
    inc     dword [rsp]
    jmp     .legapp
.legtimed:
    call    now_sec
    movsd   [tsec3], xmm0
    mov     r15d, 0
.legloop:
    cmp     r15d, 8
    jae     .legdone
    mov     rax, [cr_scratch]
    mov     rdi, rax
    mov     esi, r15d
    imul    eax, r15d, 52
    lea     rdx, [decis0+rax]
    xor     ecx, ecx                ; full = 0
    push    rax
    call    sq5_classify_bin
    pop     rax
    mov     rdi, [cr_scratch]
    mov     esi, r15d
    lea     rdx, [decis0+rax]
    call    sq5_apply_repair
    inc     r15d
    jmp     .legloop
.legdone:
    call    now_sec
    movsd   xmm1, xmm0
    movsd   xmm0, [tsec3]
    movsd   [tsec4], xmm1
    subsd   xmm1, xmm0
    addsd   xmm1, [r13+120]         ; acc.t_simple += t4-t3
    movsd   [r13+120], xmm1
    ; audit dump on request (Phase B round 0)
    cmp     dword [cr_dump], 0
    je      .scoring
    mov     rdi, [cr_scratch]
    mov     rsi, rbp
    call    cpy_torus               ; corrupt_snap(scratch) = clean
    mov     dword [rsp], 0
.dmpapp:
    mov     eax, [rsp]
    cmp     eax, r14d
    jae     .dmpdo
    imul    eax, eax, 28
    lea     rsi, [evts+rax]
    mov     rdi, [cr_scratch]
    call    sq5_apply_event
    inc     dword [rsp]
    jmp     .dmpapp
.dmpdo:
    mov     rdi, rbp                ; clean
    mov     rsi, [cr_scratch]       ; corrupt snap
    mov     rdx, rbx                ; repaired (torus)
    lea     rcx, [evts]
    mov     r8d, r14d               ; nev
    lea     r9, [decis]
    call    audit_dump              ; (sflag via audit_sflag BSS)
.scoring:
    mov     dword [rsp], 0          ; e = 0
.scloop:
    mov     eax, [rsp]
    cmp     eax, r14d
    jae     .binscore
    imul    eax, eax, 28
    lea     r10, [evts+rax]         ; ev
    mov     eax, [r10]              ; cat
    cmp     eax, 0
    je      .scpay
    cmp     eax, 1
    je      .scstamp
    ; JOUR scoring
    mov     eax, [r10+4]            ; b
    imul    eax, eax, 52
    lea     r11, [decis+rax]          ; dd
    xor     r9d, r9d                ; d0
    mov     eax, [r11]              ; flags
    mov     ecx, [r10+12]           ; shell
    test    ecx, ecx
    jnz     .scj1
    test    eax, 1                  ; R0
    jz      .scjrep
    inc     r9d
    jmp     .scjrep
.scj1:
    test    eax, 2                  ; R1
    jz      .scjrep
    inc     r9d
.scjrep:
    ; want = recompute from content
    mov     dword [jour_want], 0
    mov     dword [jour_want+4], 0
    mov     dword [jour_want+8], 0
    mov     eax, [r10+4]            ; b
    xor     r8d, r8d                ; g2
.scjg:
    cmp     r8d, 32
    jae     .scjcmp
    mov     ecx, eax
    shl     ecx, 5
    add     ecx, r8d
    shl     ecx, 1
    add     ecx, [r10+12]           ; slot
    cmp     byte [rbx+OCC_OFF+rcx], 0
    je      .scjnext
    mov     edx, ecx
    shl     edx, 6
    lea     rsi, [rbx+rdx]
    lea     rdi, [jour_want]
    mov     edx, r8d
    push    rax
    push    r8
    push    r9
    push    r10
    push    r11
    call    journal_add
    pop     r11
    pop     r10
    pop     r9
    pop     r8
    pop     rax
.scjnext:
    inc     r8d
    jmp     .scjg
.scjcmp:
    mov     ecx, [r10+4]
    shl     ecx, 1
    add     ecx, [r10+12]
    imul    ecx, ecx, 12
    lea     rsi, [rbx+JR_OFF+rcx]   ; jr[b][shell]
    xor     r8d, r8d                ; rp
    mov     eax, dword [jour_want]
    cmp     eax, [rsi]
    jne     .scjtally
    mov     eax, dword [jour_want+4]
    cmp     eax, [rsi+4]
    jne     .scjtally
    mov     eax, dword [jour_want+8]
    cmp     eax, [rsi+8]
    jne     .scjtally
    inc     r8d
.scjtally:
    mov     eax, [r10+12]           ; shell
    test    eax, eax
    jnz     .scja1
    cmp     dword [r11+28], 1       ; JOUR0
    jne     .scjd
    inc     qword [r13+72]          ; jour_arb_ok++
    jmp     .scjd
.scja1:
    cmp     dword [r11+28], 2       ; JOUR1
    jne     .scjd
    inc     qword [r13+72]
    jmp     .scjd
.scpay:
    mov     eax, [r10+4]
    imul    eax, eax, 52
    lea     r11, [decis+rax]
    xor     r9d, r9d
    mov     eax, [r10+12]           ; shell
    mov     ecx, [r11+28]           ; cls
    test    eax, eax
    jnz     .scp1
    cmp     ecx, 3
    je      .scpd
    cmp     ecx, 5
    jne     .scprep
.scpd:
    inc     r9d
    jmp     .scprep
.scp1:
    cmp     ecx, 4
    je      .scpd
    cmp     ecx, 5
    jne     .scprep
    inc     r9d
.scprep:
    ; rp = pay_ok(pay[b][g][shell], item_at[b][g])
    mov     eax, [r10+4]
    shl     eax, 5
    add     eax, [r10+8]
    shl     eax, 1
    add     eax, [r10+12]
    mov     ecx, eax
    shl     ecx, 6
    lea     rdi, [rbx+rcx]
    mov     eax, [r10+4]
    shl     eax, 5
    add     eax, [r10+8]
    mov     esi, [item_at+rax*4]
    push    r9
    push    r10
    push    r11
    call    sq5_pay_ok              ; eax = rp
    pop     r11
    pop     r10
    mov     r8d, eax
    pop     r9
    jmp     .scjd
.scstamp:
    mov     eax, [r10+4]
    shl     eax, 5
    add     eax, [r10+8]
    shl     eax, 1
    add     eax, [r10+12]           ; slot
    mov     ecx, eax
    shr     ecx, 6                  ; slot>>6
    and     eax, 63
    mov     r8d, eax                ; bit (keep)
    mov     rax, [stamp_badmap+rcx*8]
    mov     ecx, r8d
    shr     rax, cl
    and     eax, 1
    mov     r9d, eax                ; d0
    ; rp = stamp == sq5_stamp(b,g,shell)
    mov     edi, [r10+4]
    mov     esi, [r10+8]
    mov     edx, [r10+12]
    push    r9
    push    r10
    call    sq5_stamp               ; eax = want
    pop     r10
    pop     r9
    mov     ecx, [r10+4]
    shl     ecx, 5
    add     ecx, [r10+8]
    shl     ecx, 1
    add     ecx, [r10+12]
    shl     ecx, 2
    xor     r8d, r8d
    cmp     eax, [rbx+STAMP_OFF+rcx]
    jne     .scjd
    inc     r8d
.scjd:
    mov     eax, [r10]              ; cat
    add     [r13+24+rax*8], r9      ; acc.det[cat] += d0
    add     [r13+48+rax*8], r8      ; acc.rep_ok[cat] += rp
    inc     dword [rsp]
    jmp     .scloop
.binscore:
    mov     r15d, 0                 ; b
.bsloop:
    cmp     r15d, 8
    jae     .cohsweep
    imul    eax, r15d, 52
    mov     ecx, dword [decis+rax+48] ; unresolved
    add     [r13+88], rcx           ; acc.unresolved += (64-bit add)
    cmp     dword [decis+rax+28], 7   ; ANOMALY
    jne     .bsnext
    inc     qword [r13+96]          ; anomalies++
.bsnext:
    inc     r15d
    jmp     .bsloop
.cohsweep:
    xor     r15d, r15d              ; linear slot s = b*64+g*2... use b,g,s nest
    xor     r8d, r8d                ; b
.co_b:
    cmp     r8d, 8
    jae     .rounddone
    xor     r9d, r9d                ; g
.co_g:
    cmp     r9d, 32
    jae     .co_bnext
    xor     r10d, r10d              ; s
.co_s:
    cmp     r10d, 2
    jae     .co_gnext
    mov     eax, r8d
    shl     eax, 5
    add     eax, r9d
    shl     eax, 1
    add     eax, r10d               ; slot
    cmp     byte [rbx+OCC_OFF+rax], 0
    je      .co_snext
    mov     ecx, eax
    shl     ecx, 6
    lea     rdi, [rbx+rcx]
    mov     eax, r8d
    shl     eax, 5
    add     eax, r9d
    mov     esi, [item_at+rax*4]
    push    r8
    push    r9
    push    r10
    call    sq5_pay_ok
    pop     r10
    pop     r9
    pop     r8
    test    eax, eax
    jnz     .co_snext
    inc     qword [r13+80]          ; coh_fail++
.co_snext:
    inc     r10d
    jmp     .co_s
.co_gnext:
    inc     r9d
    jmp     .co_g
.co_bnext:
    inc     r8d
    jmp     .co_b
.rounddone:
    inc     dword [r13+128]         ; acc.rounds++
    add     rsp, 8
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbp
    pop     rbx
    ret

; -- collision_pass: rdi = torus, rsi = applied ptr, rdx = quads ptr --
; -> rax blind count. [rsp]=s, [rsp+4]=o.
collision_pass:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 8
    mov     rbx, rdi                ; torus
    mov     r12, rsi                ; applied ptr
    mov     r13, rdx                ; quads ptr
    mov     qword [r12], 0
    mov     qword [r13], 0
    xor     r14d, r14d              ; blind
    xor     r15d, r15d              ; b
.cb:
    cmp     r15d, 8
    jae     .cdone
    mov     dword [rsp], 0          ; s = 0
.cs:
    cmp     dword [rsp], 2
    jae     .cb_next
    mov     dword [rsp+4], 0        ; o = 0
.co:
    cmp     dword [rsp+4], 2045
    jae     .cs_next
    mov     eax, [rsp+4]            ; o
    add     eax, 3
    shr     eax, 6                  ; (o+3)/64
    mov     ecx, r15d
    shl     ecx, 5
    add     ecx, eax
    shl     ecx, 1
    add     ecx, [rsp]              ; +s
    cmp     byte [rbx+OCC_OFF+rcx], 0
    je      .co_next                ; gate: last byte's slot occupied
    ; byte pointers p0..p3 (linear o..o+3)
    mov     eax, [rsp+4]            ; o
    mov     ecx, eax
    shr     ecx, 6                  ; o/64 (gen span handled per byte below)
    ; p0..p3 for linear o..o+3, then d = 1..8 scan
    mov     rdi, rbx
    mov     esi, r15d
    mov     edx, [rsp]              ; s
    mov     ecx, [rsp+4]            ; o
    call    col_ptrs
    mov     dword [col_d], 1
.dloop:
    cmp     dword [col_d], 9
    jae     .co_next                ; no realizable d at this offset
    mov     r8, [col_p]
    mov     r9, [col_p+8]
    mov     r10, [col_p+16]
    mov     r11, [col_p+24]
    movzx   eax, byte [r8]          ; v0
    movzx   ecx, byte [r9]          ; v1
    movzx   edx, byte [r10]         ; v2
    movzx   esi, byte [r11]         ; v3
    mov     edi, [col_d]            ; d
    add     eax, edi
    cmp     eax, 255
    ja      .dnext                  ; v0+d > 255
    lea     eax, [edi+edi*2]        ; 3d
    cmp     ecx, eax
    jb      .dnext                  ; v1 < 3d
    add     edx, eax
    cmp     edx, 255
    ja      .dnext                  ; v2+3d > 255
    cmp     esi, edi
    jb      .dnext                  ; v3 < d
    ; realizable quad found
    inc     qword [r13]             ; realizable_quads++
    mov     rax, [r12]
    cmp     rax, 2000
    jae     .co_next                ; cap hit: counted, not applied (then break)
    mov     esi, edi
    imul    esi, esi, 3             ; 3d
    add     byte [r8], dil          ; p0 += d
    sub     byte [r9], sil          ; p1 -= 3d
    add     byte [r10], sil         ; p2 += 3d
    sub     byte [r11], dil         ; p3 -= d
    inc     qword [r12]             ; applied++
    mov     rdi, rbx
    mov     esi, r15d
    lea     rdx, [flux_chk]
    call    flux_bin                ; eax = flags (clobbers r8-r11)
    test    eax, eax
    jnz     .revert
    inc     r14d                    ; blind++
.revert:
    mov     rdi, rbx                ; recompute ptrs (died in flux call)
    mov     esi, r15d
    mov     edx, [rsp]
    mov     ecx, [rsp+4]
    call    col_ptrs
    mov     edi, [col_d]
    mov     esi, edi
    imul    esi, esi, 3
    mov     r8, [col_p]
    mov     r9, [col_p+8]
    mov     r10, [col_p+16]
    mov     r11, [col_p+24]
    sub     byte [r8], dil
    add     byte [r9], sil
    sub     byte [r10], sil
    add     byte [r11], dil
    jmp     .co_next                ; break after first realizable d
.dnext:
    inc     dword [col_d]
    jmp     .dloop
.co_next:
    inc     dword [rsp+4]
    jmp     .co
.cs_next:
    inc     dword [rsp]
    jmp     .cs
.cb_next:
    inc     r15d
    jmp     .cb
.cdone:
    mov     eax, r14d
    add     rsp, 8
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbp
    pop     rbx
    ret

; -- col_ptrs: rdi = torus, esi = b, edx = s, ecx = o -> col_p[4] --
; Byte addresses of linear positions o..o+3 (caller-saved temps only).
col_ptrs:
    push    rbx
    mov     rbx, rdi
    mov     r8d, esi
    shl     r8d, 5                  ; b*32
    xor     r9d, r9d                ; k
.cp:
    cmp     r9d, 4
    jae     .done
    lea     eax, [ecx+r9d]          ; o+k
    mov     esi, eax
    shr     esi, 6                  ; gk
    and     eax, 63                 ; ik
    mov     edi, r8d
    add     edi, esi
    shl     edi, 1
    add     edi, edx                ; slot
    shl     edi, 6
    add     edi, eax
    lea     r10, [rbx+rdi]
    mov     [col_p+r9*8], r10
    inc     r9d
    jmp     .cp
.done:
    pop     rbx
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
    mulsd   xmm0, [DBL_10]
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

; -- atoi: rsi = string -> eax --
atoi:
    xor     eax, eax
    xor     ecx, ecx
.skip:
    movzx   edx, byte [rsi]
    cmp     dl, ' '
    je      .skip_next
    cmp     dl, 9
    je      .skip_next
    jmp     .sign
.skip_next:
    inc     rsi
    jmp     .skip
.sign:
    cmp     dl, '-'
    jne     .plus
    mov     ecx, 1
    inc     rsi
    jmp     .digits
.plus:
    cmp     dl, '+'
    jne     .digits
    inc     rsi
.digits:
    movzx   edx, byte [rsi]
    sub     dl, '0'
    cmp     dl, 9
    ja      .apply
    imul    eax, eax, 10
    movzx   edx, dl
    add     eax, edx
    inc     rsi
    jmp     .digits
.apply:
    test    ecx, ecx
    jz      .ret
    neg     eax
.ret:
    ret

; ============ audit dump (sq5_audit.txt, feeds sq5_mirror.py) ============
; audit_dump: rdi = clean, rsi = corrupt, rdx = repaired, rcx = evts,
;             r8d = nev, r9 = dec (sflag via audit_sflag BSS).
; Direct write() syscalls; numbers via au_numbuf; hex via au_hexchunk.
audit_dump:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi                ; clean
    mov     r12, rsi                ; corrupt
    mov     r13, rdx                ; repaired
    mov     r14, rcx                ; evts
    mov     r15d, r8d               ; nev
    push    r9                      ; dec ptr -> stack
    mov     eax, 257                ; sys_openat
    mov     edi, -100
    lea     rsi, [AUD_PATH]
    mov     edx, 577                ; O_WRONLY|O_CREAT|O_TRUNC
    mov     r10d, 420               ; 0644
    syscall
    cmp     rax, 0
    js      .fail
    mov     [audit_fd], eax
    ; HDR line
    lea     rsi, [AH_HDR]
    mov     rdx, AH_HDR_LEN
    call    au_str
    mov     rax, 8
    call    au_u64s
    mov     rax, 32
    call    au_u64s
    mov     rax, 64
    call    au_u64
    lea     rsi, [AU_NL]
    mov     rdx, 1
    call    au_str
    ; CLEAN_* hex
    lea     rsi, [AH_CO]
    mov     rdx, AH_CO_LEN
    call    au_str
    lea     rsi, [rbx+OCC_OFF]
    mov     rdx, 512
    call    au_hex
    lea     rsi, [AH_CP]
    mov     rdx, AH_CP_LEN
    call    au_str
    mov     rsi, rbx
    mov     rdx, 32768
    call    au_hex
    lea     rsi, [AH_CS]
    mov     rdx, AH_CS_LEN
    call    au_str
    lea     rsi, [rbx+STAMP_OFF]
    mov     rdx, 2048
    call    au_hex
    lea     rsi, [AH_CJ]
    mov     rdx, AH_CJ_LEN
    call    au_str
    lea     rsi, [rbx+JR_OFF]
    mov     rdx, 192
    call    au_hex
    ; EVENTS
    lea     rsi, [AH_EV]
    mov     rdx, AH_EV_LEN
    call    au_str
    mov     eax, r15d
    call    au_u64
    lea     rsi, [AU_NL]
    mov     rdx, 1
    call    au_str
    xor     eax, eax
    mov     [au_idx], eax               ; e = 0 (BSS: syscalls kill r11/rcx)
.evloop:
    mov     eax, [au_idx]
    cmp     eax, r15d
    jae     .corr
    lea     rsi, [AH_E]
    mov     rdx, AH_E_LEN
    call    au_str
    imul    eax, [au_idx], 28
    lea     r11, [r14+rax]
    mov     eax, [r11]
    call    au_u64s
    imul    eax, [au_idx], 28
    lea     r11, [r14+rax]
    mov     eax, [r11+4]
    call    au_u64s
    imul    eax, [au_idx], 28
    lea     r11, [r14+rax]
    mov     eax, [r11+8]
    call    au_u64s
    imul    eax, [au_idx], 28
    lea     r11, [r14+rax]
    mov     eax, [r11+12]
    call    au_u64s
    imul    eax, [au_idx], 28
    lea     r11, [r14+rax]
    mov     eax, [r11+16]
    call    au_u64s
    imul    eax, [au_idx], 28
    lea     r11, [r14+rax]
    mov     eax, [r11+20]
    call    au_u64s
    imul    eax, [au_idx], 28
    lea     r11, [r14+rax]
    movzx   eax, byte [r11+24]
    call    au_u64s
    imul    eax, [au_idx], 28
    lea     r11, [r14+rax]
    movzx   eax, byte [r11+25]
    call    au_u64
    lea     rsi, [AU_NL]
    mov     rdx, 1
    call    au_str
    inc     dword [au_idx]
    jmp     .evloop
.corr:
    lea     rsi, [AH_RP]
    mov     rdx, AH_RP_LEN
    call    au_str
    mov     rsi, r12
    mov     rdx, 32768
    call    au_hex
    lea     rsi, [AH_RS]
    mov     rdx, AH_RS_LEN
    call    au_str
    lea     rsi, [r12+STAMP_OFF]
    mov     rdx, 2048
    call    au_hex
    lea     rsi, [AH_RJ]
    mov     rdx, AH_RJ_LEN
    call    au_str
    lea     rsi, [r12+JR_OFF]
    mov     rdx, 192
    call    au_hex
    ; DEC lines (dec ptr reloaded from [rsp] per field: calls kill r9/r11)
    xor     eax, eax
    mov     [au_idx], eax               ; b = 0
.decloop:
    mov     eax, [au_idx]
    cmp     eax, 8
    jae     .sflag
    lea     rsi, [AH_D]
    mov     rdx, AH_D_LEN
    call    au_str
    mov     eax, [au_idx]
    call    au_u64s
    mov     r9, [rsp]
    imul    eax, [au_idx], 52
    mov     ecx, [r9+rax]
    mov     eax, ecx
    call    au_u64s
    mov     r9, [rsp]
    imul    eax, [au_idx], 52
    mov     ecx, [r9+rax+28]
    mov     eax, ecx
    call    au_u64s
    mov     r9, [rsp]
    imul    eax, [au_idx], 52
    mov     ecx, [r9+rax+32]
    mov     eax, ecx
    call    au_u64s
    mov     r9, [rsp]
    imul    eax, [au_idx], 52
    mov     ecx, [r9+rax+36]
    mov     eax, ecx
    call    au_u64s
    mov     r9, [rsp]
    imul    eax, [au_idx], 52
    mov     ecx, [r9+rax+40]
    mov     eax, ecx
    call    au_u64s
    mov     r9, [rsp]
    imul    eax, [au_idx], 52
    mov     ecx, [r9+rax+44]
    mov     eax, ecx
    call    au_u64s
    mov     r9, [rsp]
    imul    eax, [au_idx], 52
    mov     ecx, [r9+rax+48]
    mov     eax, ecx
    call    au_u64
    lea     rsi, [AU_NL]
    mov     rdx, 1
    call    au_str
    inc     dword [au_idx]
    jmp     .decloop
.sflag:
    lea     rsi, [AH_SF]
    mov     rdx, AH_SF_LEN
    call    au_str
    mov     rax, [audit_sflag]
    call    au_u64
    lea     rsi, [AU_NL]
    mov     rdx, 1
    call    au_str
    ; REP_* hex
    lea     rsi, [AH_PP]
    mov     rdx, AH_PP_LEN
    call    au_str
    mov     rsi, r13
    mov     rdx, 32768
    call    au_hex
    lea     rsi, [AH_PS]
    mov     rdx, AH_PS_LEN
    call    au_str
    lea     rsi, [r13+STAMP_OFF]
    mov     rdx, 2048
    call    au_hex
    lea     rsi, [AH_PJ]
    mov     rdx, AH_PJ_LEN
    call    au_str
    lea     rsi, [r13+JR_OFF]
    mov     rdx, 192
    call    au_hex
    mov     eax, 3                  ; sys_close
    mov     edi, [audit_fd]
    syscall
    add     rsp, 8
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
.fail:
    mov     eax, 60
    mov     edi, 2
    syscall

; -- au_str: rsi = ptr, rdx = len -> write(audit_fd) --
au_str:
    mov     eax, 1
    mov     edi, [audit_fd]
    syscall
    ret

; -- au_u64: eax = value (zero-extended) -> decimal + write --
au_u64:
    push    rbx
    mov     r10d, eax               ; save (div clobbers rax)
    lea     rdi, [au_numbuf+31]
    mov     rcx, 10
    test    r10d, r10d
    jnz     .dig
    dec     rdi
    mov     byte [rdi], '0'
    jmp     .out
.dig:
    mov     eax, r10d
    xor     edx, edx
    div     rcx                     ; 64-bit div, rax<2^32 exact
    add     dl, '0'
    dec     rdi
    mov     [rdi], dl
    mov     r10d, eax
    test    eax, eax
    jnz     .dig
.out:
    mov     rsi, rdi
    lea     rdx, [au_numbuf+31]
    sub     rdx, rsi
    mov     eax, 1
    mov     edi, [audit_fd]
    syscall
    pop     rbx
    ret

; -- au_u64s: eax = value -> decimal + space + write --
au_u64s:
    push    rax
    call    au_u64
    pop     rax
    mov     byte [au_numbuf], ' '
    mov     rsi, au_numbuf
    mov     rdx, 1
    mov     eax, 1
    mov     edi, [audit_fd]
    syscall
    ret

; -- au_hex: rsi = ptr, rdx = len -> hex chars + newline --
au_hex:
    push    rbx
    push    r12
    push    r13
    mov     rbx, rsi
    mov     r12, rdx
.hexloop:
    test    r12, r12
    jz      .nldone
    mov     rax, 1024
    cmp     r12, rax
    cmovb   rax, r12                ; chunk = min(1024, rem)
    mov     r13, rax
    xor     ecx, ecx                ; i
.hexb:
    cmp     rcx, r13
    jae     .wchunk
    movzx   eax, byte [rbx+rcx]
    mov     edx, eax
    shr     edx, 4
    mov     dl, [HEXD+rdx]
    mov     [au_hexchunk+rcx*2], dl
    and     eax, 15
    mov     al, [HEXD+rax]
    mov     [au_hexchunk+rcx*2+1], al
    inc     rcx
    jmp     .hexb
.wchunk:
    mov     rax, r13
    shl     rax, 1
    mov     rdx, rax
    lea     rsi, [au_hexchunk]
    mov     eax, 1
    mov     edi, [audit_fd]
    syscall
    add     rbx, r13
    sub     r12, r13
    jmp     .hexloop
.nldone:
    lea     rsi, [AU_NL]
    mov     rdx, 1
    mov     eax, 1
    mov     edi, [audit_fd]
    syscall
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- _start --
_start:
    mov     eax, [rsp]              ; argc
    cmp     eax, 1
    jbe     .default_rounds
    mov     rsi, [rsp+16]           ; argv[1]
    call    atoi
    jmp     .have_rounds
.default_rounds:
    mov     eax, 1500
.have_rounds:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r12d, eax               ; roundsA
    mov     eax, r12d
    xor     edx, edx
    mov     ecx, 3
    div     ecx
    mov     r13d, eax               ; roundsB
    lea     rdi, [rng_main]
    mov     rsi, 0xCE27
    call    seed_rng
    call    check_sse41             ; r12d/r13d survive cpuid
    lea     rdi, [torus]            ; tin
    call    sq5_tin
    xor     ebx, ebx                ; i = 0..255: alloc(i, i)
.alloc_loop:
    cmp     ebx, 256
    jae     .alloc_done
    lea     rdi, [torus]
    mov     esi, ebx
    mov     edx, ebx
    call    sq5_alloc
    inc     ebx
    jmp     .alloc_loop
.alloc_done:
    lea     rdi, [torus]
    lea     rsi, [rep_fb]
    call    sq5_rep
    lea     rdi, [clean]            ; clean = torus
    lea     rsi, [torus]
    call    cpy_torus
    lea     rax, [scratch]
    mov     [cr_scratch], rax
    xor     r14d, r14d              ; Phase A r = 0
    mov     dword [cr_dump], 0
.phase_a:
    cmp     r14d, r12d
    jae     .phase_b
    mov     eax, r14d
    xor     edx, edx
    mov     ecx, 5
    div     ecx                     ; edx = r % 5
    xor     r8d, r8d                ; PAY
    cmp     edx, 3
    jb      .have_cat_a
    mov     r8d, 1                  ; STAMP
    je      .have_cat_a
    mov     r8d, 2                  ; JOUR
.have_cat_a:
    lea     rdi, [torus]
    lea     rsi, [clean]
    lea     rdx, [rng_main]
    mov     ecx, 1
    lea     r9, [accA]
    call    cert_round
    inc     r14d
    jmp     .phase_a
.phase_b:
    xor     r14d, r14d
.phase_b_loop:
    cmp     r14d, r13d
    jae     .collide
    mov     dword [cr_dump], 0
    cmp     r14d, 0
    jne     .havedump
    mov     dword [cr_dump], 1
.havedump:
    lea     rdi, [torus]
    lea     rsi, [clean]
    lea     rdx, [rng_main]
    mov     ecx, 12
    mov     r8d, -1
    lea     r9, [accB]
    call    cert_round
    inc     r14d
    jmp     .phase_b_loop
.collide:
    lea     rdi, [torus]            ; torus = clean
    lea     rsi, [clean]
    call    cpy_torus
    lea     rdi, [torus]
    lea     rsi, [col_applied]
    lea     rdx, [col_quads]
    call    collision_pass          ; rax = blind
    mov     r15, rax                ; col_blind
    ; emit the oracle lines
    lea     rsi, [Q1A]
    mov     rdx, Q1A_LEN
    call    emit_str
    mov     rax, [accA+24]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+0]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+24]
    mov     rdx, [accA+0]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [Q1B]
    mov     rdx, Q1B_LEN
    call    emit_str
    lea     rsi, [Q2A]
    mov     rdx, Q2A_LEN
    call    emit_str
    mov     rax, [accA+32]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+8]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+32]
    mov     rdx, [accA+8]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [Q2B]
    mov     rdx, Q2B_LEN
    call    emit_str
    lea     rsi, [Q3A]
    mov     rdx, Q3A_LEN
    call    emit_str
    mov     rax, [accA+40]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+16]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+40]
    mov     rdx, [accA+16]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [Q3B]
    mov     rdx, Q3B_LEN
    call    emit_str
    lea     rsi, [Q4A]
    mov     rdx, Q4A_LEN
    call    emit_str
    mov     rax, [accA+48]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+0]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+48]
    mov     rdx, [accA+0]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [Q4B]
    mov     rdx, Q4B_LEN
    call    emit_str
    lea     rsi, [Q5A]
    mov     rdx, Q5A_LEN
    call    emit_str
    mov     rax, [accA+72]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+16]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+72]
    mov     rdx, [accA+16]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [Q5B]
    mov     rdx, Q5B_LEN
    call    emit_str
    lea     rsi, [Q6A]
    mov     rdx, Q6A_LEN
    call    emit_str
    mov     rax, [accA+80]
    call    emit_u64
    lea     rsi, [Q6B]
    mov     rdx, Q6B_LEN
    call    emit_str
    lea     rsi, [Q7A]
    mov     rdx, Q7A_LEN
    call    emit_str
    mov     rax, r15
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [col_applied]
    call    emit_u64
    lea     rsi, [Q7B]
    mov     rdx, Q7B_LEN
    call    emit_str
    mov     rax, [col_quads]
    call    emit_u64
    lea     rsi, [Q7C]
    mov     rdx, Q7C_LEN
    call    emit_str
    lea     rsi, [Q8A]
    mov     rdx, Q8A_LEN
    call    emit_str
    lea     rsi, [Q9A]
    mov     rdx, Q9A_LEN
    call    emit_str
    mov     rax, [accB+24]
    add     rax, [accB+32]
    add     rax, [accB+40]          ; B.det sum
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accB+0]
    add     rax, [accB+8]
    add     rax, [accB+16]          ; B.cnt sum
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accB+24]
    add     rax, [accB+32]
    add     rax, [accB+40]
    mov     rdx, [accB+0]
    add     rdx, [accB+8]
    add     rdx, [accB+16]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [Q9B]
    mov     rdx, Q9B_LEN
    call    emit_str
    lea     rsi, [Q10A]
    mov     rdx, Q10A_LEN
    call    emit_str
    mov     rax, [accB+48]
    add     rax, [accB+56]
    add     rax, [accB+64]          ; B.rep sum
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accB+0]
    add     rax, [accB+8]
    add     rax, [accB+16]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accB+48]
    add     rax, [accB+56]
    add     rax, [accB+64]
    mov     rdx, [accB+0]
    add     rdx, [accB+8]
    add     rdx, [accB+16]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [Q10B]
    mov     rdx, Q10B_LEN
    call    emit_str
    lea     rsi, [Q11A]
    mov     rdx, Q11A_LEN
    call    emit_str
    mov     rax, [accB+80]
    call    emit_u64
    lea     rsi, [Q11B]
    mov     rdx, Q11B_LEN
    call    emit_str
    mov     rax, [accB+88]
    call    emit_u64
    lea     rsi, [Q11C]
    mov     rdx, Q11C_LEN
    call    emit_str
    mov     rax, [accB+96]
    call    emit_u64
    lea     rsi, [Q11D]
    mov     rdx, Q11D_LEN
    call    emit_str
    mov     rax, [accB+104]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    ; SQ5T line (timing: format-checked, values vary — excluded from diff)
    lea     rsi, [QT0]
    mov     rdx, QT0_LEN
    call    emit_str
    movsd   xmm0, [accA+112]
    mulsd   xmm0, [DBL_1E9]
    cvtsi2sd xmm1, dword [accA+128]
    divsd   xmm0, xmm1
    cvttsd2si rax, xmm0
    call    emit_u64
    lea     rsi, [QT1]
    mov     rdx, QT1_LEN
    call    emit_str
    movsd   xmm0, [accA+120]
    mulsd   xmm0, [DBL_1E9]
    cvtsi2sd xmm1, dword [accA+128]
    divsd   xmm0, xmm1
    cvttsd2si rax, xmm0
    call    emit_u64
    lea     rsi, [QT2]
    mov     rdx, QT2_LEN
    call    emit_str
    movsd   xmm0, [accB+112]
    mulsd   xmm0, [DBL_1E9]
    cvtsi2sd xmm1, dword [accB+128]
    divsd   xmm0, xmm1
    cvttsd2si rax, xmm0
    call    emit_u64
    lea     rsi, [QT3]
    mov     rdx, QT3_LEN
    call    emit_str
    movsd   xmm0, [accB+120]
    mulsd   xmm0, [DBL_1E9]
    cvtsi2sd xmm1, dword [accB+128]
    divsd   xmm0, xmm1
    cvttsd2si rax, xmm0
    call    emit_u64
    lea     rsi, [QT4]
    mov     rdx, QT4_LEN
    call    emit_str
    mov     eax, r12d
    call    emit_u64
    lea     rsi, [QT5]
    mov     rdx, QT5_LEN
    call    emit_str
    mov     eax, r13d
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
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

INV_2P53 dq 0x3CA0000000000000      ; 2^-53
DBL_10  dq 0x4024000000000000      ; 10.0
DBL_0   dq 0
DBL_1E9 dq 0x41CDCD6500000000      ; 1e9
DBL_1E_9 dq 0x3E112E0BE826D369     ; 1e-9
DBL_070 dq 0x3FE6666666666666      ; 0.70
DBL_085 dq 0x3FEB333333333333      ; 0.85
DBL_080 dq 0x3FE999999999999A      ; 0.80
HEXD db '0123456789abcdef'

SCATLT dd 6,5,4,0,2,3,4,7,4,6,3,0,1,2,1,0
       dd 3,6,4,7,4,3,2,0,4,5,6,5,4,0,2,3
BINGEO dd 228,104,0,104,228,104,0,104
sse_c4 dd 4,4,4,4

AUD_PATH db 'sq5_audit.txt', 0
AU_NL db 0x0A
AH_HDR db 'HDR '
AH_HDR_LEN = $ - AH_HDR
AH_CO db 'CLEAN_OCC '
AH_CO_LEN = $ - AH_CO
AH_CP db 'CLEAN_PAY '
AH_CP_LEN = $ - AH_CP
AH_CS db 'CLEAN_STAMP '
AH_CS_LEN = $ - AH_CS
AH_CJ db 'CLEAN_JR '
AH_CJ_LEN = $ - AH_CJ
AH_EV db 'EVENTS '
AH_EV_LEN = $ - AH_EV
AH_E db 'EV '
AH_E_LEN = $ - AH_E
AH_RP db 'CORR_PAY '
AH_RP_LEN = $ - AH_RP
AH_RS db 'CORR_STAMP '
AH_RS_LEN = $ - AH_RS
AH_RJ db 'CORR_JR '
AH_RJ_LEN = $ - AH_RJ
AH_D db 'DEC '
AH_D_LEN = $ - AH_D
AH_SF db 'STAMP_FLAGGED '
AH_SF_LEN = $ - AH_SF
AH_PP db 'REP_PAY '
AH_PP_LEN = $ - AH_PP
AH_PS db 'REP_STAMP '
AH_PS_LEN = $ - AH_PS
AH_PJ db 'REP_JR '
AH_PJ_LEN = $ - AH_PJ

; oracle line literals (spacing verified against sq5_cert.c via diff)
Q1A db 'SQ5OR O1_payload_det  '
Q1A_LEN = $ - Q1A
Q1B db '  expect=1.000000 counting [A]', 0x0A
Q1B_LEN = $ - Q1B
Q2A db 'SQ5OR O2_stamp_det    '
Q2A_LEN = $ - Q2A
Q2B db '  expect=1.000000 counting [A]', 0x0A
Q2B_LEN = $ - Q2B
Q3A db 'SQ5OR O3_journal_det  '
Q3A_LEN = $ - Q3A
Q3B db '  expect=1.000000 counting [A]', 0x0A
Q3B_LEN = $ - Q3B
Q4A db 'SQ5OR O4_payload_rep  '
Q4A_LEN = $ - Q4A
Q4B db '  expect>=0.990000 measurement [A]', 0x0A
Q4B_LEN = $ - Q4B
Q5A db 'SQ5OR O5_arbitration  '
Q5A_LEN = $ - Q5A
Q5B db '  expect=1.000000 measurement [A isolated]', 0x0A
Q5B_LEN = $ - Q5B
Q6A db 'SQ5OR O6_coh_fail     '
Q6A_LEN = $ - Q6A
Q6B db ' slots [A]  expect=0', 0x0A
Q6B_LEN = $ - Q6B
Q7A db 'SQ5OR O7_collision    '
Q7A_LEN = $ - Q7A
Q7B db ' blind of applied; '
Q7B_LEN = $ - Q7B
Q7C db ' realizable quads mapped  expect=all-blind documented-exclusion', 0x0A
Q7C_LEN = $ - Q7C
Q8A db 'SQ5OR O8_mirror_diff  see sq5_mirror.py verdict  expect=0 construction', 0x0A
Q8A_LEN = $ - Q8A
Q9A db 'SQ5OR auxB_det        '
Q9A_LEN = $ - Q9A
Q9B db '  poisson tail, no expectation', 0x0A
Q9B_LEN = $ - Q9B
Q10A db 'SQ5OR auxB_rep        '
Q10A_LEN = $ - Q10A
Q10B db '  poisson tail (multi-hit DED limit)', 0x0A
Q10B_LEN = $ - Q10B
Q11A db 'SQ5OR auxB_coh_fail   '
Q11A_LEN = $ - Q11A
Q11B db ' slots  auxB_unresolved '
Q11B_LEN = $ - Q11B
Q11C db '  auxB_anomalies '
Q11C_LEN = $ - Q11C
Q11D db '  auxB_stamp_flagged '
Q11D_LEN = $ - Q11D
QSL db '/'
QEQ db ' = '
QNL db 0x0A
QT0 db 'SQ5T full_A='
QT0_LEN = $ - QT0
QT1 db ' legacy_A='
QT1_LEN = $ - QT1
QT2 db ' full_B='
QT2_LEN = $ - QT2
QT3 db ' legacy_B='
QT3_LEN = $ - QT3
QT4 db ' ns_per_round roundsA='
QT4_LEN = $ - QT4
QT5 db ' roundsB='
QT5_LEN = $ - QT5

segment readable writeable

torus    rb TORUS_SZ
clean    rb TORUS_SZ
scratch  rb TORUS_SZ
item_at  rd 256
evts     rb 1792
decis    rb 416
decis0     rb 416
accA     rq 17
accB     rq 17
rng_main rb 32
use_sse41 rb 1
sse_idx  rd 4
sse_hs   rb 16
stamp_badmap rq 8
jour_want rb 12
flux_chk rb 24
cr_scratch rq 1
cr_dump  rd 1
audit_sflag rq 1
tsec0    rq 1
tsec1    rq 1
tsec2    rq 1
tsec3    rq 1
tsec4    rq 1
col_p    rq 4
col_d    rd 1
rep_fb   rq 1
col_applied rq 1
col_quads rq 1
au_idx   rd 1
numbuf   rb 32
fdigits  rb 8
outbuf   rb 4096
outcur   rq 1
tsbuf    rq 2
audit_fd rd 1
au_numbuf rb 32
au_hexchunk rb 2048

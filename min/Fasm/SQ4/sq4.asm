; SQ4 alloc/integrity driver in flat assembler (FASM 1.73.x, x86-64 Linux).
; Faithful port of benchmark/bench_sq4.c EMBEDDING the overflow-probe
; fix (second pass): linear probe from the SCATLT hint, so a 256-fill
; lands 256/256 instead of 220/256. Goal: byte-identical oracle counts
; to the fixed C bench (victims cross-checked via stderr EV lines).
;
; Protocol (bench defaults at capacity): n=256, rounds=391
; (100000/256+1), error_rate=0.01 -> inj=3, churn=0, seed 0x5C4A11.
; RNG is xoshiro256** (same code as sq5.asm, correctly labeled).
;
; Layout (bench_sq4.c sq4_torus_t):
;   tinvar@0    : 32*8*2 i32 = 2048 B   [i=gen][j=bin][k=shell]
;   tocc  @2048 : 512 B
;   tfroz @2560 : 512 B
;   twhead@3072 : 8*2 int = 64 B        [j][k]
;   tlen  @3136 : 64 B
;   talloc@3200 : 64 B
;   ttotal@3264 : int (4 B)             TORUS_SZ = 3268
; Assemble: fasm sq4.asm sq4

format ELF64 executable 3
entry _start

SQ4_NBINS = 8
SQ4_NRING = 32
SQ4_N = 256
SQ4_ROUNDS = 391

TINVAR_OFF = 0
TOCC_OFF = 2048
TFROZ_OFF = 2560
TWHEAD_OFF = 3072                  ; int[8][2] below: 64 B each
TLEN_OFF = 3136
TALLOC_OFF = 3200
TTOTAL_OFF = 3264
TORUS_SZ = 3268

segment readable executable

; -- xoshiro256** : rdi = state ptr (4 qwords) -> rax --
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
seed_rng:
    push    rbx
    push    r12
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
    ret

; -- rand01: rdi = state -> xmm0 double in [0,1) --
rand01:
    push    rdi
    call    xoshiro_ss
    pop     rdi
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

; -- sq4_tin: rdi = torus (memset 0) --
sq4_tin:
    push    rax
    push    rcx
    xor     eax, eax
    mov     ecx, 408
    rep     stosq                   ; 408*8 = 3264
    mov     ecx, 1
    rep     stosd                   ; +4 = 3268 = TORUS_SZ
    pop     rcx
    pop     rax
    ret

; -- sq4_pack: edi = gen, esi = bin, edx = shell -> eax --
sq4_pack:
    mov     eax, esi
    shl     eax, 1
    and     eax, 31                 ; tbits
    shl     eax, 9
    mov     ecx, edi
    and     ecx, 7
    mov     ecx, [BINGEO+rcx*4]
    shl     ecx, 24
    or      eax, ecx
    shl     esi, 16                 ; bin<<16
    or      eax, esi
    and     edx, 1
    shl     edx, 8
    or      eax, edx
    or      eax, edi                ; gen (no field overlap)
    ret

; -- sq4_fal: rdi = torus, esi = id -> eax 0 / -1 (WITH probe fix) --
sq4_fal:
    push    rbx
    push    r12
    push    r13
    mov     rbx, rdi                ; torus
    mov     eax, esi
    and     eax, 31
    mov     r12d, [SCATLT+rax*4]    ; b0
    mov     eax, r12d
    mov     ecx, [rbx+TWHEAD_OFF+rax*8] ; twhead[bin][0]
    cmp     ecx, 32
    jb      .write                  ; hint room: eax = bin, ecx = gen
    mov     r13d, 1                 ; k = 1 (k=0 was b0, full)
.probe:
    cmp     r13d, 8
    jae     .full
    lea     eax, [r12+r13]
    and     eax, 7                  ; bin
    mov     ecx, [rbx+TWHEAD_OFF+rax*8] ; twhead[bin][0]
    cmp     ecx, 32
    jb      .write
    inc     r13d
    jmp     .probe
.write:                             ; eax = bin, ecx = gen
    mov     r12d, eax
    mov     r13d, ecx
    mov     edi, ecx                ; gen
    mov     esi, eax                ; bin
    xor     edx, edx                ; shell 0
    call    sq4_pack                ; eax = pack (r12d/r13d survive)
    mov     edx, r13d               ; gen
    shl     edx, 3                  ; gen*8
    add     edx, r12d               ; +bin
    shl     edx, 1                  ; slot (shell 0)
    mov     ecx, edx
    shl     ecx, 2                  ; slot*4
    mov     [rbx+rcx], eax          ; tinvar
    mov     byte [rbx+TOCC_OFF+rdx], 1
    mov     ecx, r12d
    shl     ecx, 3                  ; bin*8 ([bin][0] stride)
    inc     dword [rbx+TALLOC_OFF+rcx]
    mov     eax, [rbx+TALLOC_OFF+rcx]
    and     eax, 3                  ; talloc >= 0: %4
    sete    al
    movzx   eax, al
    mov     [rbx+TFROZ_OFF+rdx], al
    inc     dword [rbx+TWHEAD_OFF+rcx]
    inc     dword [rbx+TLEN_OFF+rcx]
    inc     dword [rbx+TTOTAL_OFF]
    xor     eax, eax
    pop     r13
    pop     r12
    pop     rbx
    ret
.full:
    mov     rax, -1
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- sq4_val: rdi = torus, esi = repair flag -> eax bad count --
sq4_val:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 8                  ; [rsp] = i (gen)
    mov     rbx, rdi                ; torus
    mov     r12d, esi               ; repair
    xor     r13d, r13d              ; bad
    xor     r14d, r14d              ; k = shell
.vk:
    cmp     r14d, 2
    jae     .vdone
    xor     r15d, r15d              ; j = bin
.vj:
    cmp     r15d, 8
    jae     .vknext
    mov     dword [rsp], 0          ; i = 0
.vi:
    mov     eax, [rsp]
    cmp     eax, 32
    jae     .vjnext
    mov     ecx, eax
    shl     ecx, 3                  ; gen*8
    add     ecx, r15d               ; +bin
    shl     ecx, 1
    add     ecx, r14d               ; slot
    cmp     byte [rbx+TOCC_OFF+rcx], 0
    je      .vempty
    ; occupied: pack(i,j,k) compare
    mov     edi, [rsp]              ; gen
    mov     esi, r15d               ; bin
    mov     edx, r14d               ; shell
    push    rcx
    call    sq4_pack                ; eax = want
    pop     rcx
    mov     edx, ecx
    shl     edx, 2                  ; slot*4
    cmp     eax, [rbx+rdx]
    je      .vinext
    inc     r13d                    ; bad++
    test    r12d, r12d
    jz      .vinext
    mov     [rbx+rdx], eax          ; repair: rewrite pack
    jmp     .vinext
.vempty:
    mov     edx, ecx
    shl     edx, 2
    cmp     dword [rbx+rdx], 0
    je      .vinext
    inc     r13d
    test    r12d, r12d
    jz      .vinext
    mov     dword [rbx+rdx], 0      ; repair: clear stray
.vinext:
    inc     dword [rsp]
    jmp     .vi
.vjnext:
    inc     r15d
    jmp     .vj
.vknext:
    inc     r14d
    jmp     .vk
.vdone:
    mov     eax, r13d
    add     rsp, 8
    pop     r15
    pop     r14
    pop     r13
    pop     r12
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

; -- au_str: rsi = ptr, rdx = len -> write(2) direct --
au_str:
    mov     eax, 1
    mov     edi, 2
    syscall
    ret

; -- au_u64: eax = value -> decimal + write(2) --
au_u64:
    push    rbx
    mov     r10d, eax
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
    div     rcx
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
    mov     edi, 2
    syscall
    pop     rbx
    ret

; -- au_sp: write(2) single space --
au_sp:
    mov     byte [au_numbuf], ' '
    mov     rsi, au_numbuf
    mov     rdx, 1
    mov     eax, 1
    mov     edi, 2
    syscall
    ret

; -- au_nl: write(2) newline --
au_nl:
    mov     byte [au_numbuf], 0x0A
    mov     rsi, au_numbuf
    mov     rdx, 1
    mov     eax, 1
    mov     edi, 2
    syscall
    ret

; -- _start: fixed protocol (n=256, rounds=391, err=0.01, churn=0) --
_start:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    lea     rdi, [rng_main]
    mov     rsi, 0x5C4A11
    call    seed_rng
    call    wallns
    mov     r15, rax                ; t0 (preserved: wallns keeps r15)
    xor     r14d, r14d              ; fails
    xor     r13d, r13d              ; round
.rounds:
    cmp     r13d, 391
    jae     .alloc_done
    lea     rdi, [torus]
    call    sq4_tin
    xor     r12d, r12d              ; i
.aloop:
    cmp     r12d, 256
    jae     .rnext
    lea     rdi, [torus]
    mov     esi, r12d
    call    sq4_fal
    test    eax, eax
    jz      .anext
    inc     r14d                    ; fails++
.anext:
    inc     r12d
    jmp     .aloop
.rnext:
    inc     r13d
    jmp     .rounds
.alloc_done:
    call    wallns                  ; rax = t1
    sub     rax, r15                ; t1 - t0 (r15 dead after)
    mov     [t_ns0], rax
    mov     [fails_cnt], r14d       ; spill (scan reuses r13-r15)
    lea     rdi, [torus]
    call    sq4_rep
    ; occ scan shell 1 -> occ[] (BSS rd 256)
    xor     r13d, r13d              ; n_occ
    xor     r14d, r14d              ; j = bin
.oj:
    cmp     r14d, 8
    jae     .injcalc
    xor     r15d, r15d              ; i = gen
.oi:
    cmp     r15d, 32
    jae     .ojnext
    mov     eax, r15d
    shl     eax, 3                  ; gen*8
    add     eax, r14d               ; +bin
    shl     eax, 1
    add     eax, 1                  ; slot shell1
    cmp     byte [torus+TOCC_OFF+rax], 0
    je      .oinext
    mov     ecx, r14d
    shl     ecx, 8                  ; j<<8
    or      ecx, r15d               ; |i
    mov     edx, r13d
    mov     [occ+rdx*4], ecx
    inc     r13d
.oinext:
    inc     r15d
    jmp     .oi
.ojnext:
    inc     r14d
    jmp     .oj
.injcalc:
    ; inj = (long long)(0.01 * n_occ + 0.5)
    cvtsi2sd xmm0, r13d             ; n_occ
    mov     eax, 1
    cvtsi2sd xmm1, eax
    mov     eax, 100
    cvtsi2sd xmm2, eax
    divsd   xmm1, xmm2              ; 0.01 (single rounding = literal)
    mulsd   xmm0, xmm1
    addsd   xmm0, [HALF]            ; +0.5
    cvttsd2si r14d, xmm0            ; inj (trunc, non-negative)
    mov     [inj_cnt], r14d
    ; Fisher-Yates partial shuffle over occ[0..n_occ), then inject
    xor     r12d, r12d              ; e = 0
.fyloop:
    cmp     r12d, r14d              ; e < inj?
    jae     .inject
    mov     eax, r13d
    sub     eax, r12d               ; total - e
    cvtsi2sd xmm1, eax
    lea     rdi, [rng_main]
    call    rand01                  ; xmm0 = u
    mulsd   xmm0, xmm1              ; u * (total-e)
    cvttsd2si eax, xmm0             ; (long long) trunc
    add     eax, r12d               ; j = e + ...
    cmp     eax, r13d
    jb      .jok
    mov     eax, r13d
    dec     eax                     ; j = total-1
.jok:
    mov     ecx, [occ+rax*4]
    mov     edx, [occ+r12*4]
    mov     [occ+rax*4], edx        ; swap idx[e], idx[j]
    mov     [occ+r12*4], ecx
    inc     r12d
    jmp     .fyloop
.inject:
    xor     r12d, r12d              ; c = 0
.injloop:
    cmp     r12d, r14d
    jae     .scoring
    mov     eax, [occ+r12*4]
    mov     ecx, eax
    shr     ecx, 8                  ; j
    and     eax, 0xFF               ; i
    mov     [ev_b], ecx
    mov     [ev_g], eax
    lea     rdi, [rng_main]
    call    rand_u32                ; eax = draw (rcx,rdx dead; BSS holds b/g)
    xor     edx, edx
    mov     ecx, 32
    div     ecx                     ; edx = bit
    mov     [ev_bit], edx
    ; tinvar[i][j][1] ^= 1u << bit ; slot = ((i*8+j)*2+1)
    mov     eax, [ev_g]
    shl     eax, 3                  ; i*8
    add     eax, [ev_b]             ; +j
    shl     eax, 1
    inc     eax                     ; slot shell1
    shl     eax, 2                  ; slot*4
    mov     ecx, [ev_bit]
    mov     edx, 1
    shl     edx, cl                 ; mask
    xor     dword [torus+rax], edx  ; flip
    ; stderr EV line: SQ4V ev <b> <g> <bit>
    lea     rsi, [AEV]
    mov     rdx, AEV_LEN
    call    au_str
    mov     eax, [ev_b]
    call    au_u64
    call    au_sp
    mov     eax, [ev_g]
    call    au_u64
    call    au_sp
    mov     eax, [ev_bit]
    call    au_u64
    call    au_nl
    jmp     .injnext
.injnext:
    inc     r12d
    jmp     .injloop
.scoring:
    lea     rdi, [torus]
    xor     esi, esi                ; detect
    call    sq4_val
    mov     r15d, eax               ; det (kept for O2)
    mov     r12d, eax               ; working copy
    lea     rdi, [torus]
    mov     esi, 1                  ; repair
    call    sq4_val
    lea     rdi, [torus]
    xor     esi, esi                ; re-validate
    call    sq4_val                 ; eax = remaining
    sub     r12d, eax               ; r12d = rep = det - remaining
    ; coherency walk: occupied slots carry pack(i,j,k)
    xor     r13d, r13d              ; coh_fail
    xor     r8d, r8d                ; k = shell
.cok:
    cmp     r8d, 2
    jae     .emit
    xor     r9d, r9d                ; j = bin
.coj:
    cmp     r9d, 8
    jae     .coknext
    xor     r10d, r10d              ; i = gen
.coi:
    cmp     r10d, 32
    jae     .cojnext
    mov     eax, r10d               ; gen
    shl     eax, 3                  ; gen*8
    add     eax, r9d                ; +bin
    shl     eax, 1
    add     eax, r8d                ; +shell = slot
    cmp     byte [torus+TOCC_OFF+rax], 0
    je      .coinext
    mov     edi, r10d               ; gen
    mov     esi, r9d                ; bin
    mov     edx, r8d                ; shell
    push    rax
    call    sq4_pack                ; eax = want
    pop     rcx                     ; slot
    shl     ecx, 2
    cmp     eax, dword [torus+rcx]
    je      .coinext
    inc     r13d                    ; coh_fail++
.coinext:
    inc     r10d
    jmp     .coi
.cojnext:
    inc     r9d
    jmp     .coj
.coknext:
    inc     r8d
    jmp     .cok
.emit:
    ; O1 alloc
    lea     rsi, [Q1A]
    mov     rdx, Q1A_LEN
    call    emit_str
    mov     eax, 100096
    sub     eax, [fails_cnt]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, 100096
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     eax, 100096
    sub     eax, [fails_cnt]
    mov     edx, 100096
    call    ratio_f6
    call    emit_f6
    lea     rsi, [Q1B]
    mov     rdx, Q1B_LEN
    call    emit_str
    ; O2 detect
    lea     rsi, [Q2A]
    mov     rdx, Q2A_LEN
    call    emit_str
    mov     eax, r15d               ; det
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     eax, [inj_cnt]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     eax, r15d
    mov     edx, [inj_cnt]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [Q2B]
    mov     rdx, Q2B_LEN
    call    emit_str
    ; O3 repair
    lea     rsi, [Q3A]
    mov     rdx, Q3A_LEN
    call    emit_str
    mov     eax, r12d               ; rep
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     eax, [inj_cnt]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     eax, r12d
    mov     edx, [inj_cnt]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [Q3B]
    mov     rdx, Q3B_LEN
    call    emit_str
    ; O4 coherency
    lea     rsi, [Q4A]
    mov     rdx, Q4A_LEN
    call    emit_str
    mov     eax, r13d               ; coh fails
    call    emit_u64
    lea     rsi, [Q4B]
    mov     rdx, Q4B_LEN
    call    emit_str
    ; SQ4T timing (excluded from diff)
    lea     rsi, [QT0]
    mov     rdx, QT0_LEN
    call    emit_str
    mov     rax, [t_ns0]
    call    emit_u64
    lea     rsi, [QT1]
    mov     rdx, QT1_LEN
    call    emit_str
    mov     eax, 1                  ; sys_write(1, outbuf, outcur)
    mov     edi, 1
    lea     rsi, [outbuf]
    mov     rdx, [outcur]
    syscall
    mov     eax, 60                 ; sys_exit(0)
    xor     edi, edi
    syscall

; -- sq4_rep: rdi = torus -> eax copied (shell 0 -> shell 1) --
sq4_rep:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi                ; torus
    xor     r13d, r13d              ; copied
    xor     r14d, r14d              ; j = bin
.rj:
    cmp     r14d, 8
    jae     .done
    xor     r15d, r15d              ; i = gen
.ri:
    cmp     r15d, 32
    jae     .rjnext
    mov     eax, r15d
    shl     eax, 3                  ; gen*8
    add     eax, r14d
    shl     eax, 1                  ; slot shell0
    cmp     byte [rbx+TOCC_OFF+rax], 0
    je      .rinext
    mov     edi, r15d               ; gen
    mov     esi, r14d               ; bin
    mov     edx, 1                  ; shell 1
    push    rax                     ; save slot0
    call    sq4_pack                ; eax = pack(i,j,1)
    pop     rcx                     ; slot0
    inc     ecx                     ; slot1
    mov     edx, ecx
    shl     edx, 2                  ; slot1*4
    mov     [rbx+rdx], eax          ; tinvar[i][j][1]
    mov     byte [rbx+TOCC_OFF+rcx], 1
    mov     byte [rbx+TFROZ_OFF+rcx], 0
    mov     eax, r14d
    shl     eax, 3                  ; bin*8
    add     eax, 4                  ; [bin][1]
    inc     dword [rbx+TLEN_OFF+rax]
    inc     dword [rbx+TTOTAL_OFF]
    inc     r13d                    ; copied++
    jmp     .rinext
.rjnext:
    mov     eax, [rbx+TWHEAD_OFF+r14*8]     ; twhead[j][0]
    mov     [rbx+TWHEAD_OFF+r14*8+4], eax   ; twhead[j][1] = it
    inc     r14d
    jmp     .rj
.rinext:
    inc     r15d
    jmp     .ri
.done:
    mov     eax, r13d
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

segment readable

Q1A db 'SQ4OR O1_alloc       '
Q1A_LEN = $ - Q1A
Q1B db '  expect=1.000000 counting', 0x0A
Q1B_LEN = $ - Q1B
Q2A db 'SQ4OR O2_detect      '
Q2A_LEN = $ - Q2A
Q2B db '  expect=1.000000 counting', 0x0A
Q2B_LEN = $ - Q2B
Q3A db 'SQ4OR O3_repair      '
Q3A_LEN = $ - Q3A
Q3B db '  expect=1.000000 measurement', 0x0A
Q3B_LEN = $ - Q3B
Q4A db 'SQ4OR O4_coherency   '
Q4A_LEN = $ - Q4A
Q4B db ' slots  expect=0', 0x0A
Q4B_LEN = $ - Q4B
QSL db '/'
QEQ db ' = '
QNL db 0x0A
QT0 db 'SQ4T alloc_ns='
QT0_LEN = $ - QT0
QT1 db ' rounds=391', 0x0A
QT1_LEN = $ - QT1
AEV db 'SQ4V ev '
AEV_LEN = $ - AEV

segment readable

SCATLT dd 6,5,4,0,2,3,4,7,4,6,3,0,1,2,1,0
       dd 3,6,4,7,4,3,2,0,4,5,6,5,4,0,2,3
BINGEO dd 228,104,0,104,228,104,0,104
INV_2P53 dq 0x3CA0000000000000
HALF dq 0x3FE0000000000000
DBL_10 dq 0x4024000000000000
DBL_0 dq 0

segment readable writeable

torus    rb TORUS_SZ
rng_main rb 32
occ      rd 256
numbuf   rb 32
fdigits  rb 8
outbuf   rb 4096
outcur   rq 1
tsbuf    rq 2
t_ns0    rq 1
fails_cnt rd 1
inj_cnt  rd 1
ev_b     rd 1
ev_g     rd 1
ev_bit   rd 1
au_numbuf rb 32

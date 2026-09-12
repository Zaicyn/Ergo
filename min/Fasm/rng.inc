; rng.inc -- shared xoshiro256** + seed/rand helpers (single source).
; Include after `segment readable executable` (any position there).
; Self-contained: rodata inside, no BSS needs, ends in executable.
; Users: sq2b, sqm, sqw, sq5, sq4, trit (all verified byte-identical
; sources; old `xoshiro`/`M53` names unified to xoshiro_ss/INV_2P53).
segment readable

INV_2P53 dq 0x3CA0000000000000      ; 2^-53

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


; -- rand_u32: rdi = state -> eax --
rand_u32:
    push    rdi
    call    xoshiro_ss
    pop     rdi
    ret                             ; eax = low32 (C cast truncates)

; -- rand01: rdi = state -> xmm0 double in [0,1) --
; SQ5/common.h:77 — (x>>11) * 2^-53, exact in binary


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


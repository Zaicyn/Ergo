; hash_rng.inc -- shared splitmix64-Stafford pure hash helpers (single source).
; Include after `segment readable executable` (any position there).
; Self-contained: rodata inside, no BSS needs, ends in executable.
; Pure functions of the seed (no state): H(seed) = mix(seed + GOLDEN),
; counter-mode usable -- event k recomputable without replaying 0..k-1.
; Semantics mirror Ergo HASH/RAND (top-31 / top-53 splits).
; This is a DEBUG-KIT tool: deterministic event streams for analysis
; harnesses. It does NOT replace rng.inc xoshiro streams in the ports
; (those streams are the oracles; changing them changes every number).
; Clobbers: rax, rcx (+xmm0 for hash_u01). All scalar (no AVX state).
segment readable

HASH_2M53 dq 0x3CA0000000000000      ; 2^-53

segment readable executable


; -- hash_u64: rdi = seed -> rax = Stafford-mix(seed + 0x9E3779B97F4A7C15) --
; splitmix64 finalizer (Steele/Lea/Stafford constants).
hash_u64:
    mov     rax, rdi
    mov     rcx, 0x9E3779B97F4A7C15
    add     rax, rcx
    mov     rcx, rax
    shr     rcx, 30
    xor     rax, rcx
    mov     rcx, 0xBF58476D1CE4E5B9
    imul    rax, rcx
    mov     rcx, rax
    shr     rcx, 27
    xor     rax, rcx
    mov     rcx, 0x94D049BB133111EB
    imul    rax, rcx
    mov     rcx, rax
    shr     rcx, 31
    xor     rax, rcx
    ret

; -- hash_u32: rdi = seed -> eax = H(seed) >> 33 (top 31 bits, [0,2^31)) --
; Ergo HASH semantics.
hash_u32:
    call    hash_u64
    shr     rax, 33
    ret

; -- hash_u01: rdi = seed -> xmm0 = (H(seed) >> 11) * 2^-53 in [0,1) --
; Ergo RAND semantics. Scalar SSE only (cvtsi2sd/mulsd); do not place
; between 256-bit loads and their use (pitfall 18 covers vzeroupper;
; here the reverse: SSE is fine standalone, just keep AVX regions VEX).
hash_u01:
    call    hash_u64
    shr     rax, 11                 ; top 53 bits (< 2^53, exact in f64)
    cvtsi2sd xmm0, rax
    mulsd   xmm0, [HASH_2M53]
    ret

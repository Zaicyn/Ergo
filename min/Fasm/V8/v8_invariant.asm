; V8 compute_invariant in flat assembler (FASM 1.73.x, x86-64 Linux).
; Same algorithm as Testing/V8/aizawa.cuh: XOR-fold 32 u64 words,
; then fold 32/16/8. Pattern buffer generated identically to v8_driver.c:
;   buf[i] = (uint8_t)(i * 2654435761u >> 16)
; No libc, no libm, no start files — entry is _start, output via
; write(2), exit via exit(2). Scalar-only on purpose: GCC auto-vectorized
; this loop to AVX2 (vpxor ymm); matching that by hand is the next step,
; exactly the hand-SSE story V22 already tells.
; Assemble: fasm v8_invariant.asm v8_invariant

format ELF64 executable 3
entry _start

segment readable executable

_start:
    ; --- build pattern buffer ---
    lea     rdi, [buf]
    xor     ecx, ecx            ; i = 0
.build:
    mov     eax, ecx
    imul    eax, 0x9E3779B1     ; i * 2654435761 (mod 2^32, sign irrelevant)
    shr     eax, 16
    mov     [rdi + rcx], al
    inc     ecx
    cmp     ecx, 256
    jne     .build

    ; --- XOR-fold 32 qwords ---
    xor     rax, rax            ; inv = 0
    lea     rsi, [buf]
    mov     ecx, 32
.fold:
    xor     rax, [rsi]
    add     rsi, 8
    dec     ecx
    jnz     .fold

    ; --- 32/16/8 folds ---
    mov     rdx, rax
    shr     rdx, 32
    xor     rax, rdx
    mov     rdx, rax
    shr     rdx, 16
    xor     rax, rdx
    mov     rdx, rax
    shr     rdx, 8
    xor     rax, rdx            ; rax = invariant

    ; --- hex-encode into line buffer ---
    mov     rbx, rax
    lea     rdi, [line + 10]    ; after "invariant="
    mov     ecx, 16
.hex:
    rol     rbx, 4
    mov     al, bl
    and     al, 0x0F
    add     al, '0'
    cmp     al, '9'
    jbe     .store
    add     al, 39              ; 'a'-'f' (lowercase, matches printf %x)
.store:
    mov     [rdi], al
    inc     rdi
    dec     ecx
    jnz     .hex

    ; --- write(1, line, 27) ---
    mov     eax, 1              ; sys_write
    mov     edi, 1
    lea     rsi, [line]
    mov     edx, 27
    syscall

    ; --- exit(0) ---
    mov     eax, 60             ; sys_exit
    xor     edi, edi
    syscall

segment readable writeable

buf     rb 256
line    db 'invariant=', 16 dup('?'), 0x0A

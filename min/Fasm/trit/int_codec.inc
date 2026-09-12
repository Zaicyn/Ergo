; int_codec.inc -- shared integer codec: zigzag + variable-width ints.
; Companion to trit_codec.inc (see compression_plan.md Phase A).
; Paste anywhere inside `segment readable executable` (pure code, no data,
; no BSS). Conventions: SysV-like args, rax result, only scratch regs
; (rax,rcx,rdx,rsi,rdi,r8-r11) touched unless noted.

; -- zz_enc: eax = int32 -> eax = zigzag u32. Branchless. --
; f(e) = (e<<1)^(e>>31): e>=0 -> 2e, e<0 -> -2e-1 (mod 2^32, exact).
zz_enc:
    mov     edx, eax
    sar     edx, 31                 ; sign mask: 0 / -1
    add     eax, eax                ; e<<1 (wraps mod 2^32, intended)
    xor     eax, edx
    ret

; -- zz_dec: eax = zigzag u32 -> eax = int32. Branchless. --
zz_dec:
    mov     edx, eax
    and     edx, 1
    neg     edx                     ; -(s&1): 0 / -1
    shr     eax, 1
    xor     eax, edx
    ret

; -- put_i64: rdi = out, rsi = value (int64), edx = nbytes 1..8 --
; Stores low nbytes little-endian. Caller guarantees fit (same contract
; as sparse_encode's fixed moment widths). Preserves rdi.
put_i64:
    test    edx, edx
    jz      .ret
    push    rdi
    mov     ecx, edx
    mov     rax, rsi
.pl:
    mov     [rdi], al
    shr     rax, 8
    inc     rdi
    dec     ecx
    jnz     .pl
    pop     rdi
.ret:
    ret

; -- get_i64: rdi = in, edx = nbytes 1..8 -> rax sign-extended --
; Byte loop (no over-read past the field) + shift-based sign extension.
get_i64:
    test    edx, edx
    jz      .zero
    push    rbx
    mov     ebx, edx                ; n (zero-extended, callee-saved)
    mov     r8, rdi
    add     r8, rbx                 ; &field[n]
    xor     eax, eax
    mov     ecx, ebx
.gl:
    dec     r8
    shl     rax, 8
    movzx   edx, byte [r8]
    or      rax, rdx
    dec     ecx
    jnz     .gl
    shl     ebx, 3                  ; 8n
    mov     ecx, 64
    sub     ecx, ebx                ; shift = 64-8n
    shl     rax, cl
    sar     rax, cl
    pop     rbx
    ret
.zero:
    xor     eax, eax
    ret

; -- i64width: rax = int64 value -> eax = minimal signed bytes 1..8 --
; t = v^(v>>63) (magnitude-1 for negatives); bytes = (bsr(t)+9)>>3, cap 8.
i64width:
    mov     rdx, rax
    sar     rdx, 63
    xor     rax, rdx                ; t
    test    rax, rax
    jz      .one                    ; v = 0 or v = -1 -> 1 byte
    bsr     rcx, rax
    lea     eax, [rcx+9]
    shr     eax, 3
    cmp     eax, 8
    jbe     .ret
    mov     eax, 8
    ret
.one:
    mov     eax, 1
.ret:
    ret

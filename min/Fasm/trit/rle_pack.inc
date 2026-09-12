; rle_pack.inc -- shared 2-bit pack + byte-RLE codecs (no dependencies).
; Paste this file INSIDE your `segment readable executable` section.
; It issues no segment directives, so no re-issue needed after including.
; Assemble MEMO: fasm resolves the include relative to its working
; directory -- build from the directory containing this file, or use a
; relative path from your build directory (e.g. '../trit/rle_pack.inc'
; when building from min/Fasm/Sq2B).
;
; RLE format (locked): [count:u8][value:u8] pairs, count 1..255.
; Extracted verbatim from trit/phase2.asm. Byte-identical-output check:
; a phase2 rerun must print identical sizes/fails (enc/dec MB/s vary
; run to run -- compare those lines for sanity only).

; -- pack2: rdi = 256 entries (0..3), rsi = out64 -> rax 0 / -1, rdx = bad idx
pack2:
    xor     edx, edx                ; group 0..63
.p2:
    cmp     edx, 64
    jae     .ok
    movzx   eax, byte [rdi]
    cmp     al, 4
    jae     .bad
    movzx   ecx, byte [rdi+1]
    cmp     cl, 4
    jae     .bad
    shl     ecx, 2
    or      eax, ecx
    movzx   ecx, byte [rdi+2]
    cmp     cl, 4
    jae     .bad
    shl     ecx, 4
    or      eax, ecx
    movzx   ecx, byte [rdi+3]
    cmp     cl, 4
    jae     .bad
    shl     ecx, 6
    or      eax, ecx
    mov     [rsi], al
    add     rdi, 4
    inc     rsi
    inc     edx
    jmp     .p2
.bad:
    mov     rax, -1
    ret
.ok:
    xor     eax, eax
    ret

; -- unpack2: rdi = 64 bytes, rsi = out256 (no validation: 2-bit always valid)
unpack2:
    mov     ecx, 64
.u2:
    test    ecx, ecx
    jz      .done
    movzx   eax, byte [rdi]
    mov     edx, eax
    and     edx, 3
    mov     [rsi], dl
    shr     eax, 2
    mov     edx, eax
    and     edx, 3
    mov     [rsi+1], dl
    shr     eax, 2
    mov     edx, eax
    and     edx, 3
    mov     [rsi+2], dl
    shr     eax, 2
    mov     [rsi+3], al
    add     rsi, 4
    inc     rdi
    dec     ecx
    jmp     .u2
.done:
    ret

; -- rle_enc: rdi = 256 entries (any bytes), rsi = out -> rax = enclen --
; Format: [count:u8][value:u8] pairs, count 1..255.
rle_enc:
    push    rbx
    push    r12
    mov     r12, rsi                ; out cursor
    xor     ebx, ebx                ; pos
.re:
    cmp     ebx, 256
    jae     .re_done
    movzx   eax, byte [rdi+rbx]     ; run value
    mov     ecx, 1                  ; run length
.rl:
    lea     edx, [rbx+rcx]
    cmp     edx, 256
    jae     .emit
    cmp     ecx, 255
    jae     .emit
    add     rdx, rdi
    movzx   edx, byte [rdx]
    cmp     edx, eax
    jne     .emit
    inc     ecx
    jmp     .rl
.emit:
    mov     [r12], cl
    mov     [r12+1], al
    add     r12, 2
    add     ebx, ecx
    jmp     .re
.re_done:
    mov     rax, r12
    sub     rax, rsi
    pop     r12
    pop     rbx
    ret

; -- rle_dec: rdi = pairs, rsi = out256, edx = enclen -> rax 0 ok / -1 --
rle_dec:
    push    rbx
    xor     ebx, ebx                ; out pos
    xor     ecx, ecx                ; in pos
.rd:
    cmp     ecx, edx
    jae     .rd_end
    movzx   r8d, byte [rdi+rcx]     ; count
    movzx   r9d, byte [rdi+rcx+1]   ; value
    test    r8d, r8d                ; count 0 invalid
    jz      .bad
    lea     eax, [rbx+r8]
    cmp     eax, 256
    ja      .bad                    ; overrun
.rf:
    test    r8d, r8d
    jz      .rn
    mov     [rsi+rbx], r9b
    inc     rbx
    dec     r8d
    jmp     .rf
.rn:
    add     ecx, 2
    jmp     .rd
.rd_end:
    cmp     ebx, 256
    jne     .bad
    xor     eax, eax
    pop     rbx
    ret
.bad:
    mov     rax, -1
    pop     rbx
    ret

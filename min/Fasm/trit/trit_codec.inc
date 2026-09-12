; trit_codec.inc -- shared trit codec (pack/unpack, validated bulk +
; scalar forms, assembler-generated decode table).
; Paste this file INSIDE your `segment readable executable` section:
; it ends in `segment readable` (UTBL lives there), so re-issue your
; own segment directive right after including. Assemble MEMO: fasm
; resolves the include relative to its working directory -- build
; from the directory containing this file.
segment readable executable

; -- pack_groups: rdi = trits, rsi = out, edx = ngroups --
pack_groups:
    mov     r10d, edx               ; groups remaining (scratch, no calls)
    xor     edx, edx                ; group index for diagnostics
.pg:
    test    r10d, r10d
    jz      .ok
    movzx   eax, byte [rdi+4]       ; t4
    cmp     al, 3
    jae     .bad
    movzx   ecx, byte [rdi+3]       ; t3
    cmp     cl, 3
    jae     .bad
    lea     eax, [rax+rax*2]
    add     eax, ecx
    movzx   ecx, byte [rdi+2]       ; t2
    cmp     cl, 3
    jae     .bad
    lea     eax, [rax+rax*2]
    add     eax, ecx
    movzx   ecx, byte [rdi+1]       ; t1
    cmp     cl, 3
    jae     .bad
    lea     eax, [rax+rax*2]
    add     eax, ecx
    movzx   ecx, byte [rdi]         ; t0
    cmp     cl, 3
    jae     .bad
    lea     eax, [rax+rax*2]
    add     eax, ecx
    mov     [rsi], al
    add     rdi, 5
    inc     rsi
    inc     edx
    dec     r10d
    jmp     .pg
.bad:
    mov     rax, -1
    ret
.ok:
    xor     eax, eax
    ret

; -- unpack_groups: rdi = bytes, rsi = out trits, edx = nbytes --
unpack_groups:
    mov     r10d, edx               ; remaining
    xor     edx, edx                ; byte index
.ug:
    test    r10d, r10d
    jz      .ok
    movzx   eax, byte [rdi]
    cmp     al, 242
    ja      .bad                    ; 243..255 refused loudly
    lea     ecx, [rax+rax*4]        ; v*5
    lea     r8, [UTBL]
    mov     eax, [r8+rcx]           ; 4 trits (dword)
    mov     [rsi], eax              ; unaligned dword store is fine
    mov     cl, [r8+rcx+4]          ; 5th trit
    mov     [rsi+4], cl
    inc     rdi
    add     rsi, 5
    inc     edx
    dec     r10d
    jmp     .ug
.bad:
    mov     rax, -1
    ret
.ok:
    xor     eax, eax
    ret

; -- pack5: rsi = 5 trits -> rax = byte; rdx = 0 ok else bad pos+1 --
pack5:
    xor     edx, edx
    movzx   eax, byte [rsi+4]
    cmp     al, 3
    jae     .bad4
    movzx   ecx, byte [rsi+3]
    cmp     cl, 3
    jae     .bad3
    lea     eax, [rax+rax*2]
    add     eax, ecx
    movzx   ecx, byte [rsi+2]
    cmp     cl, 3
    jae     .bad2
    lea     eax, [rax+rax*2]
    add     eax, ecx
    movzx   ecx, byte [rsi+1]
    cmp     cl, 3
    jae     .bad1
    lea     eax, [rax+rax*2]
    add     eax, ecx
    movzx   ecx, byte [rsi]
    cmp     cl, 3
    jae     .bad0
    lea     eax, [rax+rax*2]
    add     eax, ecx
    ret                             ; rdx = 0 already
.bad4:
    mov     edx, 5
    xor     eax, eax
    ret
.bad3:
    mov     edx, 4
    xor     eax, eax
    ret
.bad2:
    mov     edx, 3
    xor     eax, eax
    ret
.bad1:
    mov     edx, 2
    xor     eax, eax
    ret
.bad0:
    mov     edx, 1
    xor     eax, eax
    ret

; -- unpack5: al = byte, rdi = out5 -> rax 0 ok / -1 refused --
unpack5:
    cmp     al, 242
    ja      .bad
    movzx   ecx, al
    lea     ecx, [rcx+rcx*4]        ; v*5
    lea     rdx, [UTBL]
    mov     eax, [rdx+rcx]
    mov     [rdi], eax
    mov     cl, [rdx+rcx+4]
    mov     [rdi+4], cl
    xor     eax, eax
    ret
.bad:
    mov     rax, -1
    ret

segment readable

UTBL:
v = 0
while v < 243
  db (v) mod 3, ((v)/3) mod 3, ((v)/9) mod 3, ((v)/27) mod 3, ((v)/81) mod 3
  v = v + 1
end while

; rgba_hs.asm -- RGBA secret-color handshake, bare-metal FASM mirror.
; Two 4096 B units (4 x 1024 B RGBA channels). Secrets: color (4 bytes)
; + magnitude (lane in [0,1536)). Modified-DH standard shape over the
; toy group p=1543, g=5 (primitive). Bond S = g^ab; transient key,
; keystream, V0 keyed tag per tier. 4-tier disclosure: trust-0 sees
; slice 0 only, trust-3 sees all 4096 B.
; TSV (byte-identical with rgba_hs.c):
;   H <side> priv=<a> pub=<pa> lane=<l>
;   B bond=<S> key=<K>
;   E <dir> tag=<t> verify=<v> exact=<e>
;   T tamper=<r>
;   X bonddiff=<d> garbage=<g> tagfail=<f>
;   D 0 slice0=<s> exact=<e> locked=<l>
;   D 3 tags=<t> exact=<e>
;   R PASS | R FAIL
format ELF64 executable 3
entry _start
P_ = 1543
G_ = 5
NL_ = 1536
NU_ = 4096
NSL_ = 1024
segment readable executable
; -- sm64: rdi = state ptr -> rax. Clobbers rax,rcx,rdx. --
sm64:
    mov     rax, [rdi]
    add     rax, [st_m1]
    mov     [rdi], rax
    mov     rcx, rax
    shr     rcx, 30
    xor     rax, rcx
    mov     rcx, 0xBF58476D1CE4E5B9
    mul     rcx
    mov     rcx, rax
    shr     rcx, 27
    xor     rax, rcx
    mov     rcx, 0x94D049BB133111EB
    mul     rcx
    mov     rcx, rax
    shr     rcx, 31
    xor     rax, rcx
    ret
; -- modpow: edi = base, esi = exp -> eax. Clobbers eax,ecx,edx. --
modpow:
    push    rbx
    mov     eax, 1
    mov     ebx, edi
    test    esi, esi
    jz      .done
.lp:
    test    esi, 1
    jz      .sq
    mul     ebx
    mov     ecx, P_
    div     ecx
    mov     eax, edx
.sq:
    push    rax
    mov     eax, ebx
    mul     ebx
    mov     ecx, P_
    div     ecx
    mov     ebx, edx
    pop     rax
    shr     esi, 1
    test    esi, esi
    jnz     .lp
.done:
    pop     rbx
    ret
; -- priv_of: edi = color u32, esi = mag -> eax private scalar. --
; Clobbers rax,rcx,rdx,r8-r11. Preserves rbx,r12-r15.
priv_of:
    push    rbx
    mov     eax, esi
    xor     edx, edx
    mov     ecx, NL_
    div     ecx                    ; edx = lane
    mov     r11d, edx              ; lane
    mov     r8d, edi
    shr     r8d, 24                ; R
    mov     r9d, edi
    shr     r9d, 16
    and     r9d, 0xFF              ; Gr
    mov     r10d, edi
    shr     r10d, 8
    and     r10d, 0xFF             ; B
    and     edi, 0xFF              ; A
    mov     rax, r8
    shl     rax, 56
    mov     rcx, r9
    shl     rcx, 48
    or      rax, rcx
    mov     rcx, r10
    shl     rcx, 40
    or      rax, rcx
    mov     rcx, rdi
    shl     rcx, 32
    or      rax, rcx
    or      rax, r11
    xor     rax, [st_cA]
    mov     [st_tmp], rax
    lea     rdi, [st_tmp]
    call    sm64
    xor     edx, edx               ; 64-bit div
    mov     ecx, P_-1
    div     rcx
    mov     eax, edx
    inc     eax
    pop     rbx
    ret
; -- bond_key: edi = S, esi = pa, edx = pb, ecx = tier -> rax key. --
; Clobbers rax,rcx,rdx,r8-r11. Preserves rbx,r12-r15.
bond_key:
    push    rbx
    mov     r8d, edi
    mov     r9d, esi
    mov     r10d, edx
    mov     r11d, ecx
    mov     rax, r8
    shl     rax, 32
    or      rax, r9
    mov     rcx, r10
    imul    rcx, [st_m1]
    xor     rax, rcx
    mov     rcx, r11
    imul    rcx, [st_m2]
    xor     rax, rcx
    xor     rax, [st_cT]
    mov     [st_tmp], rax
    lea     rdi, [st_tmp]
    call    sm64
    pop     rbx
    ret
; -- keystream: rdi = K, rsi = dst, edx = n. --
; Clobbers rax,rcx,rdx. Preserves rbx,rbp,r12-r15.
keystream:
    push    rbx
    push    r12
    push    r15
    mov     r12, rsi
    mov     r15d, edx
    mov     rax, rdi
    xor     rax, [st_cS]
    mov     [st_ks], rax
    xor     ebx, ebx
.lp:
    cmp     ebx, r15d
    jae     .done
    lea     rdi, [st_ks]
    call    sm64
    mov     [r12+rbx], al
    inc     ebx
    jmp     .lp
.done:
    pop     r15
    pop     r12
    pop     rbx
    ret
; -- tag_v0: rdi = K, rsi = ptr, edx = n -> rax tag. --
; Clobbers rax,rcx,rdx. Preserves rbx,rbp,r12-r15.
tag_v0:
    push    rbx
    push    r12
    push    r15
    mov     r12, rsi
    mov     r15d, edx
    mov     rax, rdi
    xor     rax, [st_cG]
    mov     [st_tag], rax
    xor     ebx, ebx
.lp:
    cmp     ebx, r15d
    jae     .fin
    mov     rax, [st_tag]          ; h
    movzx   ecx, byte [r12+rbx]
    add     rcx, [st_m1]
    mov     rdx, rax
    shl     rdx, 6
    add     rcx, rdx
    mov     rdx, rax
    shr     rdx, 2
    add     rcx, rdx
    add     rcx, rbx
    xor     rax, rcx
    mov     [st_tag], rax
    mov     eax, ebx
    and     eax, 63
    cmp     eax, 63
    jne     .nxt
    lea     rdi, [st_tag]
    call    sm64
    mov     [st_tag], rax
.nxt:
    inc     ebx
    jmp     .lp
.fin:
    mov     rax, [st_tag]
    xor     rax, r15
    mov     [st_tag], rax
    lea     rdi, [st_tag]
    call    sm64
    pop     r15
    pop     r12
    pop     rbx
    ret
; -- build_unit: rdi = dst, esi = color u32. --
; Clobbers rax,rcx,rdx,r8-r11. Preserves rbx,rbp,r12-r15.
build_unit:
    push    rbx
    push    r12
    push    r13
    mov     r12, rdi
    mov     r13d, esi
    xor     ebx, ebx                ; c
.cl:
    cmp     ebx, 4
    jae     .done
    mov     eax, r13d
    mov     ecx, 3
    sub     ecx, ebx
    shl     ecx, 3
    shr     eax, cl
    and     eax, 0xFF              ; tint = color >> ((3-c)*8)
    mov     r8d, eax
    xor     r9d, r9d                ; i
.il:
    cmp     r9d, NSL_
    jae     .next
    mov     eax, r9d
    imul    eax, eax, 67
    add     eax, 41
    mov     ecx, ebx
    imul    ecx, ecx, 13
    add     eax, ecx
    xor     eax, r8d
    mov     ecx, r9d
    shr     ecx, 3
    xor     eax, ecx
    mov     ecx, ebx
    shl     ecx, 10
    add     ecx, r9d
    mov     [r12+rcx], al
    inc     r9d
    jmp     .il
.next:
    inc     ebx
    jmp     .cl
.done:
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- mem_eq: rdi, rsi, ecx = len -> eax 1 if equal. --
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
; -- wstr: rsi = ptr, rdx = len. Clobbers rax,rcx,r11. --
wstr:
    mov     eax, 1
    mov     edi, 1
    syscall
    ret
; -- pdec: rax = u64 -> decimal at [rsi], advances rsi. --
; Clobbers rax,rbx,rcx,rdx. Preserves rdi,r12-r15.
pdec:
    push    rbx
    mov     rbx, 10
    lea     rcx, [dbuf+20]
    cmp     rax, 0
    jne     .dl
    dec     rcx
    mov     byte [rcx], '0'
    jmp     .out
.dl:
    xor     edx, edx
    div     rbx
    dec     rcx
    add     dl, '0'
    mov     [rcx], dl
    cmp     rax, 0
    jne     .dl
.out:
    lea     rdx, [dbuf+20]
    sub     rdx, rcx
.pl:
    mov     al, byte [rcx]
    mov     [rsi], al
    inc     rcx
    inc     rsi
    dec     rdx
    jnz     .pl
    pop     rbx
    ret
; -- emit_line: rsi = linebuf-relative end ptr; writes [linebuf,end). --
emit_line:
    lea     rdx, [linebuf]
    mov     rcx, rsi
    sub     rcx, rdx
    mov     rsi, rdx
    mov     rdx, rcx
    call    wstr
    ret
_start:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     dword [fails], 0
    ; secrets: Alice E23317C4 lane 1101, Bob 4B9DF02A lane 517
    mov     edi, 0xE23317C4
    mov     esi, 1101
    call    priv_of
    mov     [va], eax
    mov     edi, 0x4B9DF02A
    mov     esi, 517
    call    priv_of
    mov     [vb], eax
    mov     edi, G_
    mov     esi, [va]
    call    modpow
    mov     [vpa], eax
    mov     edi, G_
    mov     esi, [vb]
    call    modpow
    mov     [vpb], eax
    ; H lines
    lea     rsi, [linebuf]
    mov     ax, word [LH]
    mov     [rsi], ax
    add     rsi, 2
    xor     eax, eax
    call    pdec
    mov     eax, dword [LPRIV]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LPRIV+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, dword [va]
    call    pdec
    mov     eax, dword [LPUB]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LPUB+4]
    mov     [rsi], al
    inc     rsi
    mov     eax, dword [vpa]
    call    pdec
    mov     eax, dword [LLANE]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LLANE+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, 1101
    xor     edx, edx
    mov     ecx, NL_
    div     ecx
    mov     eax, edx
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    lea     rsi, [linebuf]
    mov     ax, word [LH]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, 1
    call    pdec
    mov     eax, dword [LPRIV]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LPRIV+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, dword [vb]
    call    pdec
    mov     eax, dword [LPUB]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LPUB+4]
    mov     [rsi], al
    inc     rsi
    mov     eax, dword [vpb]
    call    pdec
    mov     eax, dword [LLANE]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LLANE+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, 517
    xor     edx, edx
    mov     ecx, NL_
    div     ecx
    mov     eax, edx
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    ; bond both sides
    mov     edi, [vpb]
    mov     esi, [va]
    call    modpow
    mov     [vSa], eax
    mov     edi, [vpa]
    mov     esi, [vb]
    call    modpow
    mov     [vSb], eax
    mov     eax, dword [vSa]
    cmp     eax, [vSb]
    je      .bondok
    inc     dword [fails]
.bondok:
    mov     edi, [vSa]
    mov     esi, [vpa]
    mov     edx, [vpb]
    xor     ecx, ecx
    call    bond_key
    mov     [vKa], rax
    mov     [vKb], rax
    ; B line
    lea     rsi, [linebuf]
    mov     ax, word [LB]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, dword [LBOND]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LBOND+4]
    mov     [rsi], al
    inc     rsi
    mov     eax, dword [vSa]
    call    pdec
    mov     eax, dword [LKEY]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LKEY+4]
    mov     [rsi], al
    inc     rsi
    mov     rax, [vKa]
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    ; dir 0: Alice unit -> Bob
    lea     rdi, [pt]
    mov     esi, 0xE23317C4
    call    build_unit
    mov     rdi, [vKa]
    lea     rsi, [ks]
    mov     edx, NU_
    call    keystream
    xor     ebx, ebx
.e0:
    cmp     ebx, NU_
    jae     .e0d
    mov     al, byte [pt+rbx]
    xor     al, [ks+rbx]
    mov     [ct+rbx], al
    inc     ebx
    jmp     .e0
.e0d:
    mov     rdi, [vKa]
    lea     rsi, [ct]
    mov     edx, NU_
    call    tag_v0
    mov     [vtag], rax
    mov     rdi, [vKb]
    lea     rsi, [ct]
    mov     edx, NU_
    call    tag_v0
    cmp     rax, [vtag]
    je      .v0ok
    inc     dword [fails]
    xor     r12d, r12d
    jmp     .v0dec
.v0ok:
    mov     r12d, 1
.v0dec:
    mov     rdi, [vKb]
    lea     rsi, [ks]
    mov     edx, NU_
    call    keystream
    xor     ebx, ebx
.d0:
    cmp     ebx, NU_
    jae     .d0d
    mov     al, byte [ct+rbx]
    xor     al, [ks+rbx]
    mov     [dcu+rbx], al
    inc     ebx
    jmp     .d0
.d0d:
    lea     rdi, [pt]
    lea     rsi, [dcu]
    mov     ecx, NU_
    call    mem_eq
    mov     r14d, eax
    test    eax, eax
    jnz     .e0line
    inc     dword [fails]
.e0line:
    lea     rsi, [linebuf]
    mov     ax, word [LE]
    mov     [rsi], ax
    add     rsi, 2
    xor     eax, eax
    call    pdec
    mov     eax, dword [LTAG]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LTAG+4]
    mov     [rsi], al
    inc     rsi
    mov     rax, [vtag]
    call    pdec
    mov     eax, dword [LVER]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, dword [LVER+4]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, r12d
    call    pdec
    mov     eax, dword [LEX]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LEX+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     al, byte [LEX+6]
    mov     [rsi], al
    inc     rsi
    mov     eax, r14d
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    mov     r15, [vtag]             ; save dir0 tag
    ; tamper: flip ct[1234], tag must differ
    mov     rdi, [vKb]
    lea     rsi, [ct]
    mov     edx, NU_
    call    tag_v0
    mov     [vtag], rax
    xor     byte [ct+1234], 0x01
    mov     rdi, [vKb]
    lea     rsi, [ct]
    mov     edx, NU_
    call    tag_v0
    cmp     rax, [vtag]
    jne     .tampok
    inc     dword [fails]
    mov     eax, 0
    jmp     .tline
.tampok:
    mov     eax, 1
.tline:
    mov     r14d, eax
    xor     byte [ct+1234], 0x01    ; restore
    lea     rsi, [linebuf]
    mov     ax, word [LT]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, dword [LTAMP]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LTAMP+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     al, byte [LTAMP+6]
    mov     [rsi], al
    inc     rsi
    mov     eax, r14d
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    ; attacker: color 0 mag 0
    xor     edi, edi
    xor     esi, esi
    call    priv_of
    mov     [vm], eax
    mov     edi, [vpa]
    mov     esi, eax
    call    modpow
    mov     [vSm], eax
    cmp     eax, [vSa]
    jne     .xdiff
    inc     dword [fails]
    xor     r12d, r12d
    jmp     .xkey
.xdiff:
    mov     r12d, 1
.xkey:
    mov     edi, [vSm]
    mov     esi, [vpa]
    mov     edx, [vpb]
    mov     ecx, 99
    call    bond_key
    mov     [vKm], rax
    mov     rdi, rax
    lea     rsi, [ks]
    mov     edx, NU_
    call    keystream
    xor     ebx, ebx
.xd:
    cmp     ebx, NU_
    jae     .xdd
    mov     al, byte [ct+rbx]
    xor     al, [ks+rbx]
    mov     [dcu+rbx], al
    inc     ebx
    jmp     .xd
.xdd:
    lea     rdi, [pt]
    lea     rsi, [dcu]
    mov     ecx, NU_
    call    mem_eq
    test    eax, eax
    jz      .xgarb
    inc     dword [fails]
    xor     r13d, r13d
    jmp     .xtag
.xgarb:
    mov     r13d, 1
.xtag:
    mov     rdi, [vKm]
    lea     rsi, [ct]
    mov     edx, NU_
    call    tag_v0
    cmp     rax, [vtag]
    jne     .xtfail
    inc     dword [fails]
    xor     r14d, r14d
    jmp     .xline
.xtfail:
    mov     r14d, 1
.xline:
    lea     rsi, [linebuf]
    mov     ax, word [LX]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, dword [LXBD]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, dword [LXBD+4]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LXBD+8]
    mov     [rsi], al
    inc     rsi
    mov     eax, r12d
    call    pdec
    mov     eax, dword [LXG]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, dword [LXG+4]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LXG+8]
    mov     [rsi], al
    inc     rsi
    mov     eax, r13d
    call    pdec
    mov     eax, dword [LXTF]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, dword [LXTF+4]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LXTF+8]
    mov     [rsi], al
    inc     rsi
    mov     eax, r14d
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    ; dir 1: Bob unit -> Alice (pt rebuilt, tag checked both keys)
    lea     rdi, [pt]
    mov     esi, 0x4B9DF02A
    call    build_unit
    mov     rdi, [vKb]
    lea     rsi, [ks]
    mov     edx, NU_
    call    keystream
    xor     ebx, ebx
.e1:
    cmp     ebx, NU_
    jae     .e1d
    mov     al, byte [pt+rbx]
    xor     al, [ks+rbx]
    mov     [ct+rbx], al
    inc     ebx
    jmp     .e1
.e1d:
    mov     rdi, [vKb]
    lea     rsi, [ct]
    mov     edx, NU_
    call    tag_v0
    mov     [vtag], rax
    mov     rdi, [vKa]
    lea     rsi, [ks]
    mov     edx, NU_
    call    keystream
    xor     ebx, ebx
.d1:
    cmp     ebx, NU_
    jae     .d1d
    mov     al, byte [ct+rbx]
    xor     al, [ks+rbx]
    mov     [dcu+rbx], al
    inc     ebx
    jmp     .d1
.d1d:
    mov     rdi, [vKa]
    lea     rsi, [ct]
    mov     edx, NU_
    call    tag_v0
    cmp     rax, [vtag]
    jne     .e1fail
    mov     r12d, 1
    jmp     .e1mem
.e1fail:
    inc     dword [fails]
    xor     r12d, r12d
.e1mem:
    lea     rdi, [pt]
    lea     rsi, [dcu]
    mov     ecx, NU_
    call    mem_eq
    mov     r14d, eax
    test    eax, eax
    jnz     .e1line
    inc     dword [fails]
.e1line:
    lea     rsi, [linebuf]
    mov     ax, word [LE]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, 1
    call    pdec
    mov     eax, dword [LTAG]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LTAG+4]
    mov     [rsi], al
    inc     rsi
    mov     rax, [vtag]
    call    pdec
    mov     eax, dword [LVER]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, dword [LVER+4]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, r12d
    call    pdec
    mov     eax, dword [LEX]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LEX+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     al, byte [LEX+6]
    mov     [rsi], al
    inc     rsi
    mov     eax, r14d
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    ; 4-tier disclosure over Alice unit
    lea     rdi, [pt]
    mov     esi, 0xE23317C4
    call    build_unit
    xor     r12d, r12d              ; slice
.tsenc:
    cmp     r12d, 4
    jae     .tsencd
    mov     edi, [vSa]
    mov     esi, [vpa]
    mov     edx, [vpb]
    mov     ecx, r12d
    call    bond_key
    mov     rbx, r12
    shl     rbx, 10
    lea     r13, [pt+rbx]           ; src
    lea     r14, [ct+rbx]           ; dst
    mov     [st_k], rax
    mov     rdi, rax
    lea     rsi, [ks]
    mov     edx, NSL_
    call    keystream
    xor     r15d, r15d
.tse:
    cmp     r15d, NSL_
    jae     .tsed
    mov     al, byte [r13+r15]
    xor     al, [ks+r15]
    mov     [r14+r15], al
    inc     r15d
    jmp     .tse
.tsed:
    mov     rdi, [st_k]
    mov     rsi, r14
    mov     edx, NSL_
    call    tag_v0
    mov     rcx, r12
    mov     [vtier+rcx*8], rax
    inc     r12d
    jmp     .tsenc
.tsencd:
    ; trust 0: slice-0 key only
    mov     edi, [vSa]
    mov     esi, [vpa]
    mov     edx, [vpb]
    xor     ecx, ecx
    call    bond_key
    mov     [st_k], rax
    mov     rdi, rax
    lea     rsi, [ct]
    mov     edx, NSL_
    call    tag_v0
    cmp     rax, [vtier]
    je      .d0sok
    inc     dword [fails]
    xor     r12d, r12d
    jmp     .d0dec
.d0sok:
    mov     r12d, 1
.d0dec:
    mov     rdi, [st_k]
    lea     rsi, [ks]
    mov     edx, NSL_
    call    keystream
    xor     ebx, ebx
.d0x:
    cmp     ebx, NSL_
    jae     .d0xd
    mov     al, byte [ct+rbx]
    xor     al, [ks+rbx]
    mov     [dcu+rbx], al
    inc     ebx
    jmp     .d0x
.d0xd:
    lea     rdi, [pt]
    lea     rsi, [dcu]
    mov     ecx, NSL_
    call    mem_eq
    mov     r13d, eax
    test    eax, eax
    jnz     .d0lock
    inc     dword [fails]
.d0lock:
    mov     edi, [vSa]
    mov     esi, [vpa]
    mov     edx, [vpb]
    mov     ecx, 99
    call    bond_key
    mov     [st_k], rax
    xor     r14d, r14d              ; locked count
    mov     ebx, 1
.d0l:
    cmp     ebx, 4
    jae     .d0line
    mov     rdi, [st_k]
    mov     rcx, rbx
    shl     rcx, 10
    lea     rsi, [ct+rcx]
    mov     edx, NSL_
    call    tag_v0
    mov     rcx, rbx
    cmp     rax, [vtier+rcx*8]
    je      .d0ln
    inc     r14d
    jmp     .d0li
.d0ln:
    inc     dword [fails]
.d0li:
    inc     ebx
    jmp     .d0l
.d0line:
    lea     rsi, [linebuf]
    mov     ax, word [LD]
    mov     [rsi], ax
    add     rsi, 2
    xor     eax, eax
    call    pdec
    mov     eax, dword [LSL0]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, dword [LSL0+4]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, r12d
    call    pdec
    mov     eax, dword [LEX]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LEX+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     al, byte [LEX+6]
    mov     [rsi], al
    inc     rsi
    mov     eax, r13d
    call    pdec
    mov     eax, dword [LDL]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, dword [LDL+4]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, r14d
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    ; trust 3: all slices
    mov     r12d, 1                 ; tags ok
    xor     ebx, ebx
.d3:
    cmp     ebx, 4
    jae     .d3d
    mov     edi, [vSa]
    mov     esi, [vpa]
    mov     edx, [vpb]
    mov     ecx, ebx
    call    bond_key
    mov     [st_k], rax
    mov     rcx, rbx
    shl     rcx, 10
    lea     r13, [ct+rcx]
    lea     r14, [dcu+rcx]
    mov     rdi, rax
    mov     rsi, r13
    mov     edx, NSL_
    call    tag_v0
    mov     rcx, rbx
    cmp     rax, [vtier+rcx*8]
    je      .d3ko
    mov     r12d, 0
    inc     dword [fails]
.d3ko:
    mov     rdi, [st_k]
    lea     rsi, [ks]
    mov     edx, NSL_
    call    keystream
    xor     r15d, r15d
.d3x:
    cmp     r15d, NSL_
    jae     .d3xd
    mov     al, byte [r13+r15]
    xor     al, [ks+r15]
    mov     [r14+r15], al
    inc     r15d
    jmp     .d3x
.d3xd:
    inc     ebx
    jmp     .d3
.d3d:
    lea     rdi, [pt]
    lea     rsi, [dcu]
    mov     ecx, NU_
    call    mem_eq
    mov     r13d, eax
    test    eax, eax
    jnz     .d3line
    inc     dword [fails]
.d3line:
    lea     rsi, [linebuf]
    mov     ax, word [LD]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, 3
    call    pdec
    mov     eax, dword [LDT]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LDT+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, r12d
    call    pdec
    mov     eax, dword [LEX]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LEX+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     al, byte [LEX+6]
    mov     [rsi], al
    inc     rsi
    mov     eax, r13d
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    ; R line
    lea     rsi, [linebuf]
    mov     ax, word [LR]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, dword [fails]
    test    eax, eax
    jz      .rpass
    mov     eax, dword [LFAIL]
    mov     [rsi], eax
    jmp     .rexit
.rpass:
    mov     eax, dword [LPASS]
    mov     [rsi], eax
.rexit:
    add     rsi, 4
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    mov     eax, 60
    xor     edi, edi
    syscall
segment readable
LH db 'H '
LPRIV db ' priv='
LPUB db ' pub='
LLANE db ' lane='
LB db 'B '
LBOND db 'bond='
LKEY db ' key='
LE db 'E '
LTAG db ' tag='
LVER db ' verify='
LEX db ' exact='
LT db 'T '
LTAMP db 'tamper='
LX db 'X '
LXBD db 'bonddiff='
LXG db ' garbage='
LXTF db ' tagfail='
LD db 'D '
LSL0 db ' slice0='
LDL db ' locked='
LDT db ' tags='
LR db 'R '
LPASS db 'PASS'
LFAIL db 'FAIL'
st_m1 dq 0x9E3779B97F4A7C15
st_m2 dq 0xBF58476D1CE4E5B9
st_cA dq 0xA53C96F182736455
st_cT dq 0x544945524B445946
st_cS dq 0x53545245414D5F5F
st_cG dq 0x5441475F4B4559
segment readable writeable
pt rb 4096
ct rb 4096
dcu rb 4096
ks rb 4096
linebuf rb 256
dbuf rb 32
st_tmp rq 1
st_ks rq 1
st_tag rq 1
st_k rq 1
st_a rq 1
st_b rq 1
st_c rq 1
st_d rq 1
va rd 1
vb rd 1
vpa rd 1
vpb rd 1
vSa rd 1
vSb rd 1
vm rd 1
vSm rd 1
vKa rq 1
vKb rq 1
vKm rq 1
vtag rq 1
vtier rq 4
fails rd 1

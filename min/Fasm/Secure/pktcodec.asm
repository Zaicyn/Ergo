; pktcodec.asm -- packet-codec core in bare-metal FASM. Interleave build,
; per-unit S0..S3 + gated SEC, GF(256) P+Q, exact erasure solve, keyed
; commitment. TSV byte-identical with pktcodec.c:
;   K secfix=<a> secref=<b> gfdiv=<c>
;   C <SP1|BUI8|LO1|LO2|MX> full=<f> tot=<t>
;   P commit=<c>
;   R PASS | R FAIL
; Contract: helpers clobber only rax,rcx,rdx,rsi,rdi,r8-r11 and push
; rbx when they use it; r12-r15 always preserved. triple4 preserves rsi.
format ELF64 executable 3
entry _start
NP_ = 8
PL_ = 512
FR_ = 4096
NTR_ = 200
segment readable executable
; -- trand: -> rax xorshift64. Clobbers rax,rcx. --
trand:
    mov     rax, [trng]
    mov     rcx, rax
    shl     rcx, 13
    xor     rax, rcx
    mov     rcx, rax
    shr     rcx, 7
    xor     rax, rcx
    mov     rcx, rax
    shl     rcx, 17
    xor     rax, rcx
    mov     [trng], rax
    ret
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
; -- triple4: rdi = ptr, esi = n -> eax,ebx,ecx,r10d. Preserves rsi. --
triple4:
    xor     eax, eax
    xor     ebx, ebx
    xor     ecx, ecx
    xor     r10d, r10d
    xor     edx, edx
.tl:
    cmp     edx, esi
    jae     .tdone
    movzx   r8d, byte [rdi+rdx]
    lea     r9d, [rdx+1]
    add     eax, r8d
    imul    r8d, r9d
    add     ebx, r8d
    imul    r8d, r9d
    add     ecx, r8d
    imul    r8d, r9d
    add     r10d, r8d
    inc     edx
    jmp     .tl
.tdone:
    ret
; -- sec_pkt: rdi = unit, rsi = ref -> eax 1 repaired-or-clean. --
sec_pkt:
    push    rbx
    push    r12
    mov     [st_ref], rsi
    mov     r12, rdi
    mov     esi, PL_
    call    triple4
    mov     rdx, [st_ref]           ; reload ref ptr (triple4 done)
    mov     r8d, eax
    sub     r8d, dword [rdx]
    mov     r9d, ebx
    sub     r9d, dword [rdx+4]
    mov     r11d, ecx
    sub     r11d, dword [rdx+8]
    sub     r10d, dword [rdx+12]
    mov     eax, r8d
    or      eax, r9d
    or      eax, r11d
    or      eax, r10d
    jz      .clean
    mov     eax, r8d
    cmp     eax, 1
    jl      .neg
    cmp     eax, 255
    jg      .fail
    jmp     .divs
.neg:
    cmp     eax, 0
    jge     .fail
    cmp     eax, -255
    jl      .fail
.divs:
    mov     eax, r9d
    cdq
    idiv    r8d
    test    edx, edx
    jnz     .fail
    cmp     eax, 1
    jl      .fail
    cmp     eax, PL_
    jg      .fail
    mov     ecx, eax
    movsxd  rax, r8d
    imul    rax, rcx
    imul    rax, rcx
    movsxd  rdx, r11d
    cmp     rax, rdx
    jne     .fail
    imul    rax, rcx
    cmp     eax, r10d
    jne     .fail
    mov     eax, r8d
    sub     byte [r12+rcx-1], al
    mov     rdi, r12
    mov     esi, PL_
    call    triple4
    mov     rdx, [st_ref]
    mov     r8d, eax
    sub     r8d, dword [rdx]
    mov     r9d, ebx
    sub     r9d, dword [rdx+4]
    mov     r11d, ecx
    sub     r11d, dword [rdx+8]
    sub     r10d, dword [rdx+12]
    mov     eax, r8d
    or      eax, r9d
    or      eax, r11d
    or      eax, r10d
    jz      .clean
.fail:
    xor     eax, eax
    jmp     .out
.clean:
    mov     eax, 1
.out:
    pop     r12
    pop     rbx
    ret
; -- gfm: dil = a, sil = b -> al. Clobbers rax,rcx,rdx (+rbx saved). --
gfm:
    push    rbx
    movzx   eax, dil
    movzx   ecx, sil
    xor     edx, edx
.gl:
    test    ecx, ecx
    jz      .gdone
    test    ecx, 1
    jz      .gskip
    xor     edx, eax
.gskip:
    mov     ebx, eax
    and     ebx, 0x80
    shl     eax, 1
    and     eax, 0xFF
    test    ebx, ebx
    jz      .gsh
    xor     eax, 0x1B
.gsh:
    shr     ecx, 1
    jmp     .gl
.gdone:
    mov     eax, edx
    pop     rbx
    ret
; -- gf_init: tables with generator 3. --
gf_init:
    push    rbx
    push    rcx
    mov     ebx, 1
    xor     ecx, ecx
.gi:
    cmp     ecx, 511
    jae     .gdone
    mov     [gexp+rcx], bl
    cmp     ecx, 255
    jae     .gskip
    movzx   eax, bl
    mov     [glog+rax], cl
.gskip:
    movzx   edi, bl
    mov     esi, 3
    push    rcx
    call    gfm
    pop     rcx
    mov     ebx, eax
    inc     ecx
    jmp     .gi
.gdone:
    mov     byte [gexp+511], 1
    pop     rcx
    pop     rbx
    ret
; -- gf_div: dil = a, sil = b -> al. Clobbers rax,rcx,rdx. --
gf_div:
    test    dil, dil
    jz      .zero
    movzx   eax, dil
    movzx   ecx, sil
    movzx   eax, byte [glog+rax]
    movzx   ecx, byte [glog+rcx]
    sub     eax, ecx
    jns     .pos
    add     eax, 255
.pos:
    mov     al, [gexp+rax]
    ret
.zero:
    xor     eax, eax
    ret
; -- ktag: rdi = K, rsi = ptr, rdx = n, rcx = dom -> rax. --
ktag:
    push    rbx
    push    r12
    mov     rax, rdi
    xor     rax, rcx
    mov     [st_tag], rax
    mov     r12, rsi
    mov     ebx, edx
    xor     r8d, r8d
.lp:
    cmp     r8d, ebx
    jae     .fin
    mov     rax, [st_tag]
    movzx   ecx, byte [r12+r8]
    add     rcx, [st_m1]
    mov     rdx, rax
    shl     rdx, 6
    add     rcx, rdx
    mov     rdx, rax
    shr     rdx, 2
    add     rcx, rdx
    add     rcx, r8
    xor     rax, rcx
    mov     [st_tag], rax
    mov     eax, r8d
    and     eax, 63
    cmp     eax, 63
    jne     .nxt
    lea     rdi, [st_tag]
    call    sm64
    mov     [st_tag], rax
.nxt:
    inc     r8d
    jmp     .lp
.fin:
    mov     rax, [st_tag]
    xor     rax, rbx
    mov     [st_tag], rax
    lea     rdi, [st_tag]
    call    sm64
    pop     r12
    pop     rbx
    ret
; -- build: bku (interleaved) + header + refs + parP/parQ. --
build:
    push    rbx
    push    r12
    push    r13
    push    r14
    xor     r12d, r12d
.blu:
    cmp     r12d, NP_
    jae     .bref
    xor     r13d, r13d
.blk:
    cmp     r13d, PL_
    jae     .bnx
    mov     eax, r13d
    shl     eax, 3
    add     eax, r12d
    mov     r14d, eax
    imul    eax, eax, 67
    add     eax, 41
    xor     eax, 0x3C
    mov     ecx, r14d
    shr     ecx, 3
    xor     eax, ecx
    mov     ecx, r12d
    shl     ecx, 9
    add     ecx, r13d
    mov     [bku+rcx], al
    inc     r13d
    jmp     .blk
.bnx:
    inc     r12d
    jmp     .blu
.bref:
    mov     byte [bku], 0x45
    mov     byte [bku+512], 0x53
    mov     byte [bku+1024], 0x46
    mov     byte [bku+1536], 0x32
    xor     r12d, r12d
.brl:
    cmp     r12d, NP_
    jae     .bpar
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [bku+rax]
    mov     esi, PL_
    call    triple4
    mov     [st_s2], ecx
    mov     ecx, r12d
    shl     ecx, 4
    mov     [refs+rcx], eax
    mov     [refs+rcx+4], ebx
    mov     eax, [st_s2]
    mov     [refs+rcx+8], eax
    mov     [refs+rcx+12], r10d
    inc     r12d
    jmp     .brl
.bpar:
    lea     rdi, [parP]
    xor     eax, eax
    mov     ecx, PL_
    rep     stosb
    lea     rdi, [parQ]
    mov     ecx, PL_
    rep     stosb
    xor     r12d, r12d
.bpu:
    cmp     r12d, NP_
    jae     .bdone
    movzx   ebx, byte [gexp+r12]
    xor     r13d, r13d
.bpi:
    cmp     r13d, PL_
    jae     .bpnx
    mov     eax, r12d
    shl     eax, 9
    add     eax, r13d
    movzx   eax, byte [bku+rax]
    xor     byte [parP+r13], al
    movzx   edi, bl
    mov     esi, eax
    call    gfm
    xor     byte [parQ+r13], al
    inc     r13d
    jmp     .bpi
.bpnx:
    inc     r12d
    jmp     .bpu
.bdone:
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- restore: fru = bku. --
reload_fr:
    lea     rsi, [bku]
    lea     rdi, [fru]
    mov     ecx, FR_
    rep     movsb
    ret
; -- bytes_ok: -> eax. --
bytes_ok:
    xor     eax, eax
    xor     ecx, ecx
.bl:
    cmp     ecx, FR_
    jae     .bdone
    movzx   edx, byte [fru+rcx]
    cmp     dl, [bku+rcx]
    jne     .bnx
    inc     eax
.bnx:
    inc     ecx
    jmp     .bl
.bdone:
    ret
; -- dmg_spread: edi = n. --
dmg_spread:
    push    rbx
    push    r12
    mov     r12d, edi
    xor     ebx, ebx
.sl:
    cmp     ebx, r12d
    jae     .sdone
    call    trand
    and     eax, 4095
    mov     ecx, eax
    and     ecx, 7
    shr     eax, 3
    shl     ecx, 9
    lea     rdx, [fru+rcx]
    add     rdx, rax
    push    rdx
.dv:
    call    trand
    movzx   ecx, al
    inc     ecx
    and     ecx, 255
    jz      .dv
    pop     rdx
    xor     byte [rdx], cl
    inc     ebx
    jmp     .sl
.sdone:
    pop     r12
    pop     rbx
    ret
; -- dmg_burst: edi = len (full-64-bit mod for start). --
dmg_burst:
    push    rbx
    push    r12
    push    r13
    mov     r12d, edi
    call    trand
    mov     ecx, FR_
    sub     ecx, r12d
    xor     edx, edx
    div     rcx                     ; rax=quotient, rdx=remainder=st
    mov     r13, rdx                ; st (pitfall #13: div leaves both)
    xor     ebx, ebx
.bl:
    cmp     ebx, r12d
    jae     .bdone
    mov     eax, ebx
    add     rax, r13
    mov     ecx, eax
    and     ecx, 7
    shr     eax, 3
    shl     ecx, 9
    lea     rdx, [fru+rcx]
    add     rdx, rax
    push    rdx
.dv:
    call    trand
    movzx   ecx, al
    inc     ecx
    and     ecx, 255
    jz      .dv
    pop     rdx
    xor     byte [rdx], cl
    inc     ebx
    jmp     .bl
.bdone:
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- dmg_loss: edi = d, rsi = lostptr -> eax n. --
dmg_loss:
    push    rbx
    push    r12
    push    r13
    mov     r12d, edi
    mov     r13, rsi
    mov     ecx, NP_
    xor     eax, eax
.zl:
    test    ecx, ecx
    jz      .zdone
    mov     [r13+rcx*4-4], eax
    dec     ecx
    jmp     .zl
.zdone:
    xor     ebx, ebx
.ll:
    cmp     ebx, r12d
    jae     .ldone
    call    trand
    and     eax, 7
    cmp     dword [r13+rax*4], 0
    jne     .ll
    mov     dword [r13+rax*4], 1
    shl     eax, 9
    lea     rdi, [fru+rax]
    xor     eax, eax
    mov     ecx, PL_
    rep     stosb
    inc     ebx
    jmp     .ll
.ldone:
    mov     eax, ebx
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- force_err: rdi = lostptr-or-0, esi = e -> eax. --
force_err:
    push    rbx
    push    r12
    push    r13
    push    r14
    mov     r14, rdi
    mov     r12d, esi
    push    rdi
    lea     rdi, [usefl]
    xor     eax, eax
    mov     ecx, FR_
    rep     stosb
    pop     rdi
    xor     ebx, ebx
.fl:
    cmp     ebx, r12d
    jae     .fdone
    call    trand
    and     eax, 4095
    mov     ecx, eax
    and     ecx, 7
    test    r14, r14
    jz      .nlck
    cmp     dword [r14+rcx*4], 0
    jne     .fl
.nlck:
    cmp     byte [usefl+rax], 0
    jne     .fl
    mov     byte [usefl+rax], 1
    shr     eax, 3
    mov     r13d, eax
    shl     ecx, 9
    lea     rdx, [fru+rcx]
    add     rdx, r13
    push    rdx
.dv:
    call    trand
    movzx   ecx, al
    inc     ecx
    and     ecx, 255
    jz      .dv
    pop     rdx
    xor     byte [rdx], cl
    inc     ebx
    jmp     .fl
.fdone:
    mov     eax, ebx
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- solve_erase: rdi = lostptr. --
solve_erase:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r15, rdi
    xor     r12d, r12d
    xor     r13d, r13d
    xor     r14d, r14d
    xor     ebx, ebx
.sl:
    cmp     ebx, NP_
    jae     .solve
    cmp     dword [r15+rbx*4], 0
    je      .snx
    cmp     r14d, 0
    jne     .sl1
    mov     r12d, ebx
    jmp     .sni
.sl1:
    mov     r13d, ebx
.sni:
    inc     r14d
.snx:
    inc     ebx
    jmp     .sl
.solve:
    cmp     r14d, 1
    je      .one
    cmp     r14d, 2
    je      .two
    jmp     .sdone
.one:
    xor     r11d, r11d
.o1:
    cmp     r11d, PL_
    jae     .sdone
    movzx   eax, byte [parP+r11]
    xor     ebx, ebx
.o1p:
    cmp     ebx, NP_
    jae     .o1s
    cmp     ebx, r12d
    je      .o1n
    mov     ecx, ebx
    shl     ecx, 9
    add     ecx, r11d
    xor     al, [fru+rcx]
.o1n:
    inc     ebx
    jmp     .o1p
.o1s:
    mov     ecx, r12d
    shl     ecx, 9
    add     ecx, r11d
    mov     [fru+rcx], al
    inc     r11d
    jmp     .o1
.two:
    movzx   eax, byte [gexp+r12]
    mov     [st_ca], al
    movzx   eax, byte [gexp+r13]
    mov     [st_cb], al
    mov     al, [st_ca]
    xor     al, [st_cb]
    mov     [st_den], al
    xor     r11d, r11d
.t2:
    cmp     r11d, PL_
    jae     .sdone
    movzx   eax, byte [parP+r11]
    mov     [st_pp], al
    movzx   eax, byte [parQ+r11]
    mov     [st_qq], al
    xor     ebx, ebx
.t2p:
    cmp     ebx, NP_
    jae     .t2s
    cmp     ebx, r12d
    je      .t2n
    cmp     ebx, r13d
    je      .t2n
    mov     ecx, ebx
    shl     ecx, 9
    add     ecx, r11d
    movzx   eax, byte [fru+rcx]
    xor     [st_pp], al
    movzx   edi, byte [gexp+rbx]
    mov     esi, eax
    call    gfm
    xor     [st_qq], al
.t2n:
    inc     ebx
    jmp     .t2p
.t2s:
    movzx   edi, byte [st_cb]
    movzx   esi, byte [st_pp]
    call    gfm
    mov     cl, al
    xor     cl, [st_qq]
    movzx   edi, cl
    movzx   esi, byte [st_den]
    call    gf_div
    mov     cl, al                  ; ua
    mov     edx, r12d
    shl     edx, 9
    add     edx, r11d
    mov     [fru+rdx], cl
    xor     cl, [st_pp]
    mov     edx, r13d
    shl     edx, 9
    add     edx, r11d
    mov     [fru+rdx], cl
    inc     r11d
    jmp     .t2
.sdone:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- run_ecc: rdi = lostptr-or-0, esi = nloss. --
run_ecc:
    push    rbx
    push    r14
    push    r15
    mov     r15, rdi
    mov     r14d, esi
    xor     ebx, ebx
.rl:
    cmp     ebx, NP_
    jae     .rsol
    test    r15, r15
    jz      .rsec
    cmp     dword [r15+rbx*4], 0
    jne     .rnx
.rsec:
    mov     eax, ebx
    shl     eax, 9
    lea     rdi, [fru+rax]
    mov     ecx, ebx
    shl     ecx, 4
    lea     rsi, [refs+rcx]
    call    sec_pkt
.rnx:
    inc     ebx
    jmp     .rl
.rsol:
    test    r15, r15
    jz      .rdone
    cmp     r14d, 1
    jl      .rdone
    cmp     r14d, 2
    jg      .rdone
    mov     rdi, r15
    call    solve_erase
    xor     ebx, ebx
.rv:
    cmp     ebx, NP_
    jae     .rdone
    cmp     dword [r15+rbx*4], 0
    je      .rvn
    mov     eax, ebx
    shl     eax, 9
    lea     rdi, [fru+rax]
    mov     ecx, ebx
    shl     ecx, 4
    lea     rsi, [refs+rcx]
    call    sec_pkt
.rvn:
    inc     ebx
    jmp     .rv
.rdone:
    pop     r15
    pop     r14
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
    mov     al, [rcx]
    mov     [rsi], al
    inc     rcx
    inc     rsi
    dec     rdx
    jnz     .pl
    pop     rbx
    ret
; -- emit_line: rsi = end ptr; writes [linebuf,end). --
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
    mov     rax, 0x123456789ABCDEF1
    mov     [trng], rax
    call    gf_init
    call    build
    ; K: secfix (unit 2, b100 ^= 0x5A, fix + memeq)
    lea     rsi, [bku+1024]
    lea     rdi, [tbuf]
    mov     ecx, PL_
    rep     movsb
    xor     byte [tbuf+100], 0x5A
    lea     rdi, [tbuf]
    lea     rsi, [refs+32]
    call    sec_pkt
    mov     r12d, eax
    lea     rdi, [tbuf]
    lea     rsi, [bku+1024]
    mov     ecx, PL_
    call    mem_eq
    and     r12d, eax
    test    r12d, r12d
    jnz     .k1ok
    inc     dword [fails]
.k1ok:
    ; K: secref (unit 5, two flips, must refuse)
    lea     rsi, [bku+2560]
    lea     rdi, [tbuf]
    mov     ecx, PL_
    rep     movsb
    xor     byte [tbuf+10], 0x11
    xor     byte [tbuf+400], 0x22
    lea     rdi, [tbuf]
    lea     rsi, [refs+80]
    call    sec_pkt
    test    eax, eax
    jz      .k2ok
    inc     dword [fails]
    xor     r13d, r13d
    jmp     .k2line
.k2ok:
    mov     r13d, 1
.k2line:
    ; K: gfdiv 4x4 roundtrips (i,j survive calls on stack)
    mov     r14d, 1
    xor     ebx, ebx
.ko:
    cmp     ebx, 4
    jae     .kodone
    xor     ecx, ecx
.ki:
    cmp     ecx, 4
    jae     .konx
    movzx   edi, byte [KA+rbx]
    movzx   esi, byte [KB+rcx]
    push    rcx
    push    rbx
    call    gfm
    mov     edi, eax
    mov     rax, [rsp+8]
    movzx   esi, byte [KB+rax]
    call    gf_div
    mov     cl, al
    mov     rax, [rsp]
    cmp     cl, [KA+rax]
    pop     rbx
    pop     rcx
    jne     .kfail
    inc     ecx
    jmp     .ki
.konx:
    inc     ebx
    jmp     .ko
.kfail:
    xor     r14d, r14d
.kodone:
    test    r14d, r14d
    jnz     .kline
    inc     dword [fails]
.kline:
    lea     rsi, [linebuf]
    mov     ax, word [LK]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, dword [LSECFIX]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LSECFIX+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     al, byte [LSECFIX+6]
    mov     [rsi], al
    inc     rsi
    mov     eax, r12d
    call    pdec
    mov     eax, dword [LSECREF]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, dword [LSECREF+4]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, r13d
    call    pdec
    mov     eax, dword [LGFDIV]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LGFDIV+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     al, byte [LGFDIV+6]
    mov     [rsi], al
    inc     rsi
    mov     eax, r14d
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    ; cells: r15d = cell 0..4
    xor     r15d, r15d
.cell:
    cmp     r15d, 5
    jae     .promise
    mov     dword [vfull], 0
    mov     qword [vtot], 0
    mov     r12d, NTR_
.tloop:
    test    r12d, r12d
    jz      .tline
    call    reload_fr
    cmp     r15d, 0
    je      .csp1
    cmp     r15d, 1
    je      .cbui
    cmp     r15d, 2
    je      .clo1
    cmp     r15d, 3
    je      .clo2
    ; MX
    lea     rsi, [lostA]
    mov     edi, 1
    call    dmg_loss
    mov     r14d, eax
    lea     rdi, [lostA]
    mov     esi, 2
    call    force_err
    lea     rdi, [lostA]
    mov     esi, r14d
    call    run_ecc
    jmp     .tacc
.csp1:
    mov     edi, 1
    call    dmg_spread
    xor     edi, edi
    xor     esi, esi
    call    run_ecc
    jmp     .tacc
.cbui:
    mov     edi, 8
    call    dmg_burst
    xor     edi, edi
    xor     esi, esi
    call    run_ecc
    jmp     .tacc
.clo1:
    lea     rsi, [lostA]
    mov     edi, 1
    call    dmg_loss
    mov     r14d, eax
    lea     rdi, [lostA]
    mov     esi, r14d
    call    run_ecc
    jmp     .tacc
.clo2:
    lea     rsi, [lostA]
    mov     edi, 2
    call    dmg_loss
    mov     r14d, eax
    lea     rdi, [lostA]
    mov     esi, r14d
    call    run_ecc
.tacc:
    call    bytes_ok
    add     [vtot], rax
    cmp     eax, FR_
    jne     .tnx
    inc     dword [vfull]
.tnx:
    dec     r12d
    jmp     .tloop
.tline:
    lea     rsi, [linebuf]
    mov     ax, word [LC]
    mov     [rsi], ax
    add     rsi, 2
    cmp     r15d, 0
    je      .nsp1
    cmp     r15d, 1
    je      .nbui
    cmp     r15d, 2
    je      .nlo1
    cmp     r15d, 3
    je      .nlo2
    mov     ax, word [NMX]
    mov     [rsi], ax
    mov     al, byte [NMX+2]
    mov     [rsi+2], al
    add     rsi, 3
    jmp     .nfull
.nsp1:
    mov     eax, dword [NSP1]
    mov     [rsi], eax
    add     rsi, 4
    jmp     .nfull
.nbui:
    mov     eax, dword [NBUI8]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [NBUI8+4]
    mov     [rsi], al
    inc     rsi
    jmp     .nfull
.nlo1:
    mov     eax, dword [NLO1]
    mov     [rsi], eax
    add     rsi, 4
    jmp     .nfull
.nlo2:
    mov     eax, dword [NLO2]
    mov     [rsi], eax
    add     rsi, 4
.nfull:
    mov     eax, dword [LFULL]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LFULL+4]
    mov     [rsi], al
    inc     rsi
    mov     eax, [vfull]
    call    pdec
    mov     eax, dword [LTOT]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LTOT+4]
    mov     [rsi], al
    inc     rsi
    mov     rax, [vtot]
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    inc     r15d
    jmp     .cell
.promise:
    ; pqt = P+Q cat; commitment; tamper b100; commit = (mismatch)
    lea     rsi, [parP]
    lea     rdi, [pqt]
    mov     ecx, PL_
    rep     movsb
    lea     rsi, [parQ]
    lea     rdi, [pqt+512]
    mov     ecx, PL_
    rep     movsb
    mov     rdi, 18050561372206496278
    lea     rsi, [pqt]
    mov     edx, 1024
    mov     rcx, 0x50524F4D495345
    call    ktag
    mov     [st_pc], rax
    xor     byte [pqt+100], 0x01
    mov     rdi, 18050561372206496278
    lea     rsi, [pqt]
    mov     edx, 1024
    mov     rcx, 0x50524F4D495345
    call    ktag
    cmp     rax, [st_pc]
    jne     .pok
    inc     dword [fails]
    xor     r12d, r12d
    jmp     .pline
.pok:
    mov     r12d, 1
.pline:
    lea     rsi, [linebuf]
    mov     ax, word [LP]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, dword [LCOMMIT]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LCOMMIT+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     al, byte [LCOMMIT+6]
    mov     [rsi], al
    inc     rsi
    mov     eax, r12d
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    lea     rsi, [linebuf]
    mov     ax, word [LR]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, [fails]
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
LK db 'K '
LSECFIX db 'secfix='
LSECREF db ' secref='
LGFDIV db ' gfdiv='
LC db 'C '
NSP1 db 'SP1 '
NBUI8 db 'BUI8 '
NLO1 db 'LO1 '
NLO2 db 'LO2 '
NMX db 'MX '
LFULL db 'full='
LTOT db ' tot='
LP db 'P '
LCOMMIT db 'commit='
LR db 'R '
LPASS db 'PASS'
LFAIL db 'FAIL'
KA db 1, 2, 0x53, 0xFF
KB db 1, 3, 0x1B, 0x80
st_m1 dq 0x9E3779B97F4A7C15
segment readable writeable
bku rb 4096
fru rb 4096
parP rb 512
parQ rb 512
refs rd 32
gexp rb 512
glog rb 256
trng rq 1
usefl rb 4096
lostA rd 8
tbuf rb 512
pqt rb 1024
linebuf rb 256
dbuf rb 32
st_tmp rq 1
st_tag rq 1
st_ref rq 1
st_s2 rd 1
st_ca db 1
st_cb db 1
st_den db 1
st_pp db 1
st_qq db 1
st_pc rq 1
fails rd 1
vfull rd 1
vtot rq 1

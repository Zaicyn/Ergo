; torusecc_d.asm -- DERIVED-shell variant (Secure stage 2b).
; No stored shell1: single 4096 B data + per-sub-bin triples (8x3) +
; global triple. Complement view recomputed live where needed (here:
; nowhere -- all repair is single-shell SEC + bounded search; the
; point of this variant is measuring what the stored shell bought).
; Same TSV shape as torusecc for direct table comparison.
; Inject samples positions in 0..4095 (shell0 only).
format ELF64 executable 3
entry _start
NBIN = 8
SBIN = 512
NTR  = 500
segment readable executable
; -- xs64: rdi = state ptr -> rax. Clobbers rax/rcx --
xs64:
    mov     rax, [rdi]
    mov     rcx, rax
    shl     rcx, 13
    xor     rax, rcx
    mov     rcx, rax
    shr     rcx, 7
    xor     rax, rcx
    mov     rcx, rax
    shl     rcx, 17
    xor     rax, rcx
    mov     [rdi], rax
    ret
; -- triple: rdi = ptr, esi = n -> eax=s0, ebx=s1, ecx=s2 (mod 2^32) --
; Clobbers rax,rbx,rcx,rdx,rsi,rdi,r8,r9.
triple:
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
; -- sec_fix: rdi = ptr, esi = n, edx=e0, ecx=e1, r8d=e2, r9d=e3 words --
; -> eax 1 fixed (applied) / 0 refused. S0/S1 solve, S2+S3 gate.
; Clobbers rax,rbx,rcx,rdx,rsi,rdi,r8-r11. Preserves r12-r15,rbp.
sec_fix:
    push    rbx
    movsxd  r10, edx                ; d
    cmp     r10d, 1
    jl      .neg
    cmp     r10d, 255
    jg      .fail
    jmp     .have_d
.neg:
    cmp     r10d, -1
    jg      .fail
    cmp     r10d, -255
    jl      .fail
.have_d:
    movsxd  r11, ecx                ; e1s
    mov     eax, r11d
    cdq
    idiv    r10d                    ; p
    test    edx, edx
    jnz     .fail
    cmp     eax, 1
    jl      .fail
    cmp     eax, esi
    jg      .fail
    movsxd  r11, r8d                ; e2s
    mov     rbx, r10                ; d
    imul    rbx, rax                ; d*p
    imul    rbx, rax                ; d*p*p
    cmp     rbx, r11
    jne     .fail
    imul    rbx, rax                ; d*p*p*p
    cmp     ebx, r9d                ; S3 gate, mod-2^32
    jne     .fail
    sub     byte [rdi+rax-1], r10b  ; apply (mod 256)
    mov     eax, 1
    pop     rbx
    ret
.fail:
    xor     eax, eax
    pop     rbx
    ret
; -- search2: rdi = ptr, esi = n; se1/se2/se3 (BSS s64). -> eax nsol(0..2).
; Unique solution in sd1/sp1/sd2/sp2. Clobbers rax,rcx,rdx,rsi,rdi,r8-r11;
; preserves rbx,r12-r15,rbp.
search2:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r15d, esi
    xor     r8d, r8d
    mov     rbx, 1
.lp1:
    cmp     rbx, r15
    jae     .sdone
    lea     r12, [rbx+1]
.lp2:
    cmp     r12, r15
    ja      .next1
    mov     r13, rbx
    sub     r13, r12
    mov     r14, [se1]
    imul    r14, r12
    mov     rax, [se2]
    sub     rax, r14
    cqo
    idiv    r13
    test    rdx, rdx
    jnz     .next2
    cmp     rax, 1
    jl      .chkneg1
    cmp     rax, 255
    jg      .next2
    jmp     .d1ok
.chkneg1:
    cmp     rax, -1
    jg      .next2
    cmp     rax, -255
    jl      .next2
.d1ok:
    mov     r14, [se1]
    sub     r14, rax
    cmp     r14, 1
    jl      .chkneg2
    cmp     r14, 255
    jg      .next2
    jmp     .d2ok
.chkneg2:
    cmp     r14, -1
    jg      .next2
    cmp     r14, -255
    jl      .next2
.d2ok:
    mov     r9, rax
    imul    r9, rbx
    imul    r9, rbx
    mov     r10, r14
    imul    r10, r12
    imul    r10, r12
    add     r9, r10
    cmp     r9, [se3]
    jne     .next2
    mov     r11, rax                ; d1
    imul    r11, rbx
    imul    r11, rbx
    imul    r11, rbx                ; d1*p1^3
    mov     r10, r14                ; d2
    imul    r10, r12
    imul    r10, r12
    imul    r10, r12                ; d2*p2^3
    add     r11, r10
    cmp     r11d, [se3b]            ; S3 gate, mod-2^32
    jne     .next2
    inc     r8d
    cmp     r8d, 1
    jg      .sdone
    mov     [sd1], eax
    mov     [sp1], ebx
    mov     [sd2], r14d
    mov     [sp2], r12d
.next2:
    inc     r12
    jmp     .lp2
.next1:
    inc     rbx
    jmp     .lp1
.sdone:
    mov     eax, r8d
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- build_refs: journal per-bin triples + global from pristine f0 --
build_refs:
    push    rbx
    push    r12
    xor     ebx, ebx                ; s
.bl:
    cmp     ebx, NBIN
    jae     .bglob
    mov     eax, ebx
    shl     eax, 9
    lea     rdi, [f0+rax]
    mov     esi, SBIN
    push    rbx
    call    triple                  ; eax,ebx,ecx + r10d=s3
    mov     r11d, r10d              ; s3 (r10d dies below)
    mov     r8d, eax
    mov     r9d, ebx
    mov     r10d, ecx
    pop     rbx
    mov     eax, ebx
    imul    eax, eax, 12
    lea     rdx, [refB+rax]
    mov     dword [rdx], r8d
    mov     dword [rdx+4], r9d
    mov     dword [rdx+8], r10d
    mov     edx, ebx
    lea     r8, [refC+rdx*4]
    mov     dword [r8], r11d        ; s3 journal
    inc     ebx
    jmp     .bl
.bglob:
    lea     rdi, [f0]
    mov     esi, 4096
    call    triple
    mov     dword [refG], eax
    mov     dword [refG+4], ebx
    mov     dword [refG+8], ecx
    mov     dword [refG3], r10d
    pop     r12
    pop     rbx
    ret
; -- inject: edi = k, esi = clustered. Positions in 0..4095. --
inject:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r13d, edi
    mov     r14d, esi
    test    r14d, r14d
    jnz     .cl
.spread:
    xor     ebx, ebx
.sploop:
    cmp     ebx, r13d
    jae     .done
    lea     rdi, [xsst]
    call    xs64
    and     eax, 4095
    mov     r12d, eax
.dloop_s:
    lea     rdi, [xsst]
    call    xs64
    and     eax, 255
    inc     eax
    and     eax, 255
    jz      .dloop_s
    xor     byte [f0+r12], al
    inc     ebx
    jmp     .sploop
.cl:
    lea     rdi, [xsst]
    call    xs64
    and     eax, 7
    mov     r15d, eax
    lea     rdi, [xsst]
    call    xs64
    and     eax, 6
    lea     r12d, [r15+rax+1]
    and     r12d, 7
    mov     eax, r13d
    shr     eax, 1
    mov     r14d, eax
    xor     ebx, ebx
.clloop:
    cmp     ebx, r13d
    jae     .done
    cmp     r13d, 4
    jg      .two
    mov     r11d, r15d
    jmp     .have_sb
.two:
    cmp     ebx, r14d
    jl      .first_half
    mov     r11d, r12d
    jmp     .have_sb
.first_half:
    mov     r11d, r15d
.have_sb:
    lea     rdi, [xsst]
    call    xs64
    and     eax, 511
    mov     edx, r11d
    shl     edx, 9
    add     eax, edx
    mov     r11d, eax
.dloop_c:
    lea     rdi, [xsst]
    call    xs64
    and     eax, 255
    inc     eax
    and     eax, 255
    jz      .dloop_c
    xor     byte [f0+r11], al
    inc     ebx
    jmp     .clloop
.done:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- resone: rdi = resbuf[12B], esi = s -> eax OR of 3 residuals --
; Preserves rbx,r12-r15,rbp.
resone:
    push    rbx
    push    r12
    push    r15
    mov     r15, rdi                ; resbuf
    mov     r12d, esi               ; s
    mov     eax, esi
    shl     eax, 9
    lea     rdi, [f0+rax]
    mov     esi, SBIN
    call    triple                  ; eax,ebx,ecx; r12,r15 intact
    mov     edx, r12d
    imul    edx, edx, 12
    lea     r8, [refB+rdx]
    mov     r9d, eax
    sub     r9d, [r8]
    mov     dword [r15], r9d
    mov     r9d, ebx
    sub     r9d, [r8+4]
    mov     dword [r15+4], r9d
    mov     r9d, ecx
    sub     r9d, [r8+8]
    mov     dword [r15+8], r9d
    mov     edx, r12d
    lea     r8, [refC+rdx*4]
    mov     r9d, r10d
    sub     r9d, [r8]
    mov     dword [r15+12], r9d
    mov     eax, [r15]
    or      eax, [r15+4]
    or      eax, [r15+8]
    or      eax, [r15+12]
    pop     r15
    pop     r12
    pop     rbx
    ret
; -- repair_frame -> eax 0 ok-so-far / 1 refused. Single shell. --
; Preserves rbx,r12-r15,rbp. Frame [rsp]: resbuf @0..8, refused @28.
repair_frame:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    push    rbp
    sub     rsp, 32
    mov     dword [rsp+28], 0
    lea     rbp, [rsp]              ; resbuf (survives calls)
    xor     r12d, r12d              ; s
.sloop:
    cmp     r12d, NBIN
    jae     .glob
    mov     rdi, rbp
    mov     esi, r12d
    call    resone
    test    eax, eax
    jz      .snext
    mov     edx, [rbp]
    mov     r8d, [rbp+8]
    mov     r9d, [rbp+12]
    mov     ecx, [rbp+4]
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [f0+rax]
    mov     esi, SBIN
    call    sec_fix                 ; result ignored; reverify decides
    mov     rdi, rbp
    mov     esi, r12d
    call    resone
    test    eax, eax
    jz      .snext
    mov     eax, [rbp]
    movsxd  r8, eax
    mov     [se1], r8
    mov     eax, [rbp+4]
    movsxd  r8, eax
    mov     [se2], r8
    mov     eax, [rbp+8]
    movsxd  r8, eax
    mov     [se3], r8
    mov     eax, [rbp+12]
    mov     dword [se3b], eax
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [f0+rax]
    mov     esi, SBIN
    call    search2
    cmp     eax, 1
    jne     .dorefuse
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [f0+rax]
    mov     eax, [sd1]
    mov     ecx, [sp1]
    sub     byte [rdi+rcx-1], al
    mov     eax, [sd2]
    mov     ecx, [sp2]
    sub     byte [rdi+rcx-1], al
    mov     rdi, rbp
    mov     esi, r12d
    call    resone
    test    eax, eax
    jnz     .dorefuse
    jmp     .snext
.dorefuse:
    mov     dword [rsp+28], 1
    jmp     .snext
.snext:
    inc     r12d
    jmp     .sloop
.glob:
    cmp     dword [rsp+28], 0
    jne     .rfail
    lea     rdi, [f0]
    mov     esi, 4096
    call    triple
    sub     eax, [refG]
    or      eax, eax
    jnz     .rfail
    mov     eax, ebx
    sub     eax, [refG+4]
    or      eax, eax
    jnz     .rfail
    mov     eax, ecx
    sub     eax, [refG+8]
    or      eax, eax
    jnz     .rfail
    sub     r10d, [refG3]
    jnz     .rfail
    xor     eax, eax
    jmp     .retdone
.rfail:
    mov     eax, 1
.retdone:
    add     rsp, 32
    pop     rbp
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- memeq4096 -> eax 1 equal / 0 differ (f0 vs bk). --
memeq4096:
    lea     rdi, [f0]
    lea     rsi, [bk]
    mov     ecx, 4096
    repe    cmpsb
    sete    al
    movzx   eax, al
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
; -- trial_cell: edi = k, esi = patidx(0 spread/1 clust). TSV line. --
trial_cell:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     [ck], edi
    mov     [cpat], esi
    mov     dword [ccorr], 0
    mov     dword [cref], 0
    mov     dword [cmisc], 0
    mov     r15d, NTR
.tloop:
    lea     rsi, [bk]
    lea     rdi, [f0]
    mov     ecx, 4096
    rep     movsb
    mov     edi, [ck]
    mov     esi, [cpat]
    call    inject
    call    repair_frame
    test    eax, eax
    jnz     .refused
    call    memeq4096
    test    eax, eax
    jz      .misc
    inc     dword [ccorr]
    jmp     .tnext
.refused:
    inc     dword [cref]
    jmp     .tnext
.misc:
    inc     dword [cmisc]
.tnext:
    dec     r15d
    jnz     .tloop
    lea     rsi, [linebuf]
    mov     eax, dword [TK]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, [ck]
    call    pdec
    cmp     dword [cpat], 0
    je      .sp
    mov     eax, dword [PCL]
    mov     [rsi], eax
    mov     ax, word [PCL+4]
    mov     [rsi+4], ax
    mov     al, byte [PCL+6]
    mov     [rsi+6], al
    add     rsi, 7
    jmp     .counts
.sp:
    mov     eax, dword [PSP]
    mov     [rsi], eax
    mov     eax, dword [PSP+4]
    mov     [rsi+4], eax
    add     rsi, 8
.counts:
    mov     eax, [ccorr]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
    mov     eax, [cref]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
    mov     eax, [cmisc]
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    lea     rdx, [linebuf]
    mov     rcx, rsi
    sub     rcx, rdx
    mov     rsi, rdx
    mov     rdx, rcx
    call    wstr
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
_start:
    push    rbx
    push    r12
    xor     ecx, ecx
.fill:
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, 17
    xor     eax, 0xA5
    mov     [f0+rcx], al
    inc     ecx
    cmp     ecx, 4096
    jne     .fill
    mov     dword [f0], 0x32465345  ; "ESF2"
    lea     rsi, [f0]
    lea     rdi, [bk]
    mov     ecx, 4096
    rep     movsb
    call    build_refs
    mov     rax, 0x123456789
    mov     [xsst], rax
    mov     edi, 1
    xor     esi, esi
    call    trial_cell
    mov     edi, 1
    mov     esi, 1
    call    trial_cell
    mov     edi, 2
    xor     esi, esi
    call    trial_cell
    mov     edi, 2
    mov     esi, 1
    call    trial_cell
    mov     edi, 3
    xor     esi, esi
    call    trial_cell
    mov     edi, 3
    mov     esi, 1
    call    trial_cell
    mov     edi, 4
    xor     esi, esi
    call    trial_cell
    mov     edi, 4
    mov     esi, 1
    call    trial_cell
    mov     edi, 6
    xor     esi, esi
    call    trial_cell
    mov     edi, 6
    mov     esi, 1
    call    trial_cell
    mov     edi, 8
    xor     esi, esi
    call    trial_cell
    mov     edi, 8
    mov     esi, 1
    call    trial_cell
    mov     eax, 60
    xor     edi, edi
    syscall
segment readable
TK db 'T k='
PSP db ' spread '
PCL db ' clust '
segment readable writeable
f0 rb 4096
bk rb 4096
refB rd 24
refC rd 8
refG rd 3
refG3 rd 1
se1 rq 1
se2 rq 1
se3 rq 1
se3b rd 1
sd1 rd 1
sp1 rd 1
sd2 rd 1
sp2 rd 1
xsst rq 1
linebuf rb 160
dbuf rb 24
ck rd 1
cpat rd 1
ccorr rd 1
cref rd 1
cmisc rd 1

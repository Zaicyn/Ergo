; torusecc.asm -- multi-bit correction demo on torus layout (Secure stage 2).
; Frame = 4096 B = 8 sub-bins x 512 B, 2 shells (shell1 = complement).
; Per sub-bin per shell: (S0,S1,S2) = (sum b, sum b*idx, sum b*idx^2)
; mod 2^32, idx 1-based within sub-bin. Plus one global frame triple.
; Repair ladder per sub-bin: clean -> single-byte SEC -> duplex 2-byte
; (1+1 algebraic across shells, else bounded search in one dirty shell)
; -> refuse (detected). Verdicts via pristine-backup memcmp: corrected
; <=> identical bytes; refused <=> ladder gave up; else miscorrected.
; All scalar (no AVX here -- avoids pitfalls 17/18 by construction).
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
    inc     edx
    jmp     .tl
.tdone:
    ret
; -- sec_fix: rdi = ptr, esi = n, edx=e0, ecx=e1, r8d=e2 (mod-2^32 words)
; -> eax 1 fixed (applied) / 0 refused. True values all < 2^31 so
; movsxd recovers them exactly. Clobbers rax,rbx,rcx,rdx,rsi,rdi,r8-r11.
sec_fix:
    push    rbx
    movsxd  r9, edx                 ; e0 signed (d candidate range)
    cmp     r9d, 1
    jl      .neg
    cmp     r9d, 255
    jg      .fail
    jmp     .have_d
.neg:
    cmp     r9d, -1
    jg      .fail
    cmp     r9d, -255
    jl      .fail
.have_d:
    movsxd  r10, ecx                ; e1 signed
    mov     eax, r10d
    cdq
    mov     r11d, r9d               ; divisor d (!=0, |d|<=255)
    idiv    r11d                    ; p = e1/d
    test    edx, edx
    jnz     .fail
    cmp     eax, 1
    jl      .fail
    cmp     eax, esi
    jg      .fail
    movsxd  r11, r8d                ; e2 signed (use r11, divisor dead)
    movsxd  rbx, r9d                ; d full 32-bit (NOT r9b: |d|>127 breaks the gate)
    mov     rsi, rbx
    imul    rsi, rax                ; d*p
    imul    rsi, rax                ; d*p*p
    cmp     rsi, r11
    jne     .fail
    sub     byte [rdi+rax-1], r9b   ; apply (mod 256)
    mov     eax, 1
    pop     rbx
    ret
.fail:
    xor     eax, eax
    pop     rbx
    ret
; -- search2: rdi = ptr, esi = n; se1/se2/se3 (BSS, signed64) residuals.
; Bounded p1<p2 search for 2-in-one-shell solve. Returns eax = number
; of solutions capped at 2; unique solution in sd1/sp1/sd2/sp2 (BSS).
; Clobbers rax,rbx,rcx,rdx,rsi,rdi,r8-r15 (saves rbx,r12-r15).
search2:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r15d, esi               ; n
    xor     r8d, r8d                ; nsol
    mov     rbx, 1                  ; p1
.lp1:
    cmp     rbx, r15
    jae     .sdone
    lea     r12, [rbx+1]            ; p2 = p1+1..
.lp2:
    cmp     r12, r15
    ja      .next1
    mov     r13, rbx
    sub     r13, r12                ; den = p1-p2 (negative, nonzero)
    mov     r14, [se1]
    imul    r14, r12                ; e1*p2
    mov     rax, [se2]
    sub     rax, r14                ; num = e2-e1*p2
    cqo
    idiv    r13                     ; d1 = num/den
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
    sub     r14, rax                ; d2 = e1-d1
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
    mov     r9, rax                 ; d1
    imul    r9, rbx
    imul    r9, rbx                 ; d1*p1*p1
    mov     r10, r14                ; d2
    imul    r10, r12
    imul    r10, r12                ; d2*p2*p2
    add     r9, r10
    cmp     r9, [se3]
    jne     .next2
    inc     r8d                     ; solution!
    cmp     r8d, 1
    jg      .sdone                  ; 2nd solution: stop, ambiguous
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
; -- build_refs: journal all triples from pristine frame --
build_refs:
    push    rbx
    push    r12
    push    r13
    xor     ebx, ebx                ; s
.bl:
    cmp     ebx, NBIN
    jae     .bglob
    xor     r12d, r12d              ; sh
.shl:
    cmp     r12d, 2
    jae     .bnext
    mov     eax, ebx
    shl     eax, 9                  ; s*512
    lea     rdi, [s0+rax]
    test    r12d, r12d
    jz      .sh0
    lea     rdi, [s1+rax]
.sh0:
    mov     esi, SBIN
    push    rbx
    push    r12
    call    triple                  ; eax=s0 ebx=s1 ecx=s2
    push    rax                     ; save s0
    mov     eax, ebx                ; s1
    pop     rdx                     ; s0 -> edx
    pop     r12                     ; sh
    pop     rbx                     ; s
    mov     r8d, ebx
    shl     r8d, 1
    add     r8d, r12d
    imul    r8d, r8d, 12            ; ((s*2+sh)*3)*4
    lea     r9, [refB+r8]
    mov     dword [r9], edx
    mov     dword [r9+4], eax
    mov     dword [r9+8], ecx
    jmp     .shnext
    ; (old .shfix recompute block removed: single exact store above)
.shnext:
    inc     r12d
    jmp     .shl
.bnext:
    inc     ebx
    jmp     .bl
.bglob:
    lea     rdi, [s0]
    mov     esi, 4096
    call    triple
    mov     [refG], eax
    mov     [refG+4], ebx
    mov     [refG+8], ecx
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- inject: edi = k, esi = clustered(0/1). Fixed xsst stream. --
; Preserves rbx,r12-r15,rbp. Shell bit kept in r10d across xs64 calls.
inject:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r13d, edi               ; k
    mov     r14d, esi               ; clustered
    test    r14d, r14d
    jnz     .cl
.spread:
    xor     ebx, ebx                ; i
.sploop:
    cmp     ebx, r13d
    jae     .done
    lea     rdi, [xsst]
    call    xs64
    and     eax, 8191               ; flat pos (shell=pos>>12)
    mov     r12d, eax
    mov     ecx, r12d
    shr     ecx, 12
    mov     r10d, ecx               ; shell (xs64-safe)
    mov     edx, r12d
    and     edx, 4095               ; off
.dloop_s:
    lea     rdi, [xsst]
    call    xs64
    and     eax, 255
    inc     eax
    and     eax, 255
    jz      .dloop_s                ; redraw zero delta
    lea     rdi, [s0+rdx]
    test    r10d, r10d
    jz      .spxor
    lea     rdi, [s1+rdx]
.spxor:
    xor     byte [rdi], al
    inc     ebx
    jmp     .sploop
.cl:
    lea     rdi, [xsst]
    call    xs64
    and     eax, 7
    mov     r15d, eax               ; sb1
    lea     rdi, [xsst]
    call    xs64
    and     eax, 6                  ; even offset -> sb2 always != sb1
    lea     r12d, [r15+rax+1]
    and     r12d, 7
    mov     eax, r13d
    shr     eax, 1
    mov     r14d, eax               ; split point (r14d: xs64-safe, loop-invariant)
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
    mov     ecx, eax
    and     ecx, 1
    mov     r10d, ecx               ; shell (xs64-safe)
    shr     eax, 1
    and     eax, 511                ; o in bin
    mov     edx, r11d
    shl     edx, 9
    add     eax, edx
    mov     r11d, eax               ; off = sb*512+o
.dloop_c:
    lea     rdi, [xsst]
    call    xs64
    and     eax, 255
    inc     eax
    and     eax, 255
    jz      .dloop_c
    lea     rdi, [s0+r11]
    test    r10d, r10d
    jz      .clxor
    lea     rdi, [s1+r11]
.clxor:
    xor     byte [rdi], al
    inc     ebx
    jmp     .clloop
.done:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- resbin: rdi = resbuf[24B], esi = s -> eax OR of 6 residuals --
; Recomputes both shells vs refs. Preserves rbx,r12-r15,rbp.
resbin:
    push    rbx
    push    r12
    push    r13
    push    r15
    mov     r15, rdi                ; resbuf
    mov     r12d, esi               ; s
    mov     eax, esi
    shl     eax, 9
    mov     r13d, eax               ; byte base
    lea     rdi, [s0+r13]
    mov     esi, SBIN
    call    triple                  ; eax,ebx,ecx
    mov     edx, r12d
    shl     edx, 1
    imul    edx, edx, 12
    lea     r8, [refB+rdx]
    mov     r9d, eax
    sub     r9d, [r8]
    mov     [r15], r9d
    mov     r9d, ebx
    sub     r9d, [r8+4]
    mov     [r15+4], r9d
    mov     r9d, ecx
    sub     r9d, [r8+8]
    mov     [r15+8], r9d
    lea     rdi, [s1+r13]
    mov     esi, SBIN
    call    triple
    mov     edx, r12d
    shl     edx, 1
    add     edx, 1
    imul    edx, edx, 12
    lea     r8, [refB+rdx]
    mov     r9d, eax
    sub     r9d, [r8]
    mov     [r15+12], r9d
    mov     r9d, ebx
    sub     r9d, [r8+4]
    mov     [r15+16], r9d
    mov     r9d, ecx
    sub     r9d, [r8+8]
    mov     [r15+20], r9d
    mov     eax, [r15]
    or      eax, [r15+4]
    or      eax, [r15+8]
    or      eax, [r15+12]
    or      eax, [r15+16]
    or      eax, [r15+20]
    pop     r15
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- repair_frame -> eax 0 ok-so-far / 1 refused. Mutates shells. --
; Preserves rbx,r12-r15,rbp. Frame [rsp]: resbuf @0..20, refused @28.
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
    call    resbin
    test    eax, eax
    jz      .snext
    xor     r14d, r14d              ; sh
.secloop:
    cmp     r14d, 2
    jae     .secver
    mov     eax, r14d
    imul    eax, eax, 12
    lea     rcx, [rbp+rax]
    mov     edx, [rcx]
    or      edx, [rcx+4]
    or      edx, [rcx+8]
    jz      .secnext                ; shell clean
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [s0+rax]
    test    r14d, r14d
    jz      .secp
    lea     rdi, [s1+rax]
.secp:
    mov     esi, SBIN
    mov     edx, [rcx]
    mov     r8d, [rcx+8]
    mov     ecx, [rcx+4]
    call    sec_fix                 ; result ignored; reverify decides
.secnext:
    inc     r14d
    jmp     .secloop
.secver:
    mov     rdi, rbp
    mov     esi, r12d
    call    resbin
    test    eax, eax
    jz      .snext
    ; dirty flags from fresh residuals
    mov     eax, [rbp]
    or      eax, [rbp+4]
    or      eax, [rbp+8]
    mov     ecx, [rbp+12]
    or      ecx, [rbp+16]
    or      ecx, [rbp+20]
    test    eax, eax
    jz      .only1
    test    ecx, ecx
    jnz     .dorefuse               ; both dirty past SEC
    mov     r14d, 0                 ; only shell0 dirty
    jmp     .dosearch
.only1:
    test    ecx, ecx
    jz      .snext                  ; unreachable (secver nonzero); be safe
    mov     r14d, 1                 ; only shell1 dirty
.dosearch:
    mov     eax, r14d
    imul    eax, eax, 12
    lea     rcx, [rbp+rax]
    mov     eax, [rcx]
    movsxd  r8, eax
    mov     [se1], r8
    mov     eax, [rcx+4]
    movsxd  r8, eax
    mov     [se2], r8
    mov     eax, [rcx+8]
    movsxd  r8, eax
    mov     [se3], r8
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [s0+rax]
    test    r14d, r14d
    jz      .sptr
    lea     rdi, [s1+rax]
.sptr:
    mov     esi, SBIN
    call    search2
    cmp     eax, 1
    jne     .dorefuse
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [s0+rax]
    test    r14d, r14d
    jz      .sptr2
    lea     rdi, [s1+rax]
.sptr2:
    mov     eax, [sd1]
    mov     ecx, [sp1]
    sub     byte [rdi+rcx-1], al
    mov     eax, [sd2]
    mov     ecx, [sp2]
    sub     byte [rdi+rcx-1], al
    mov     rdi, rbp
    mov     esi, r12d
    call    resbin
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
    lea     rdi, [s0]
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
; -- memeq832 -> eax 1 equal / 0 differ. s0..s1 contiguous 8192 = bk. --
memeq832:
    lea     rdi, [s0]
    lea     rsi, [bk]
    mov     ecx, 8192
    repe    cmpsb
    sete    al
    movzx   eax, al
    ret
; -- wstr: rsi = ptr, rdx = len (write stdout). Clobbers rax,rcx,r11. --
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
; -- trial_cell: edi = k, esi = patidx(0 spread/1 clust).
; Prints: "T k=<k> <pat> <corr> <ref> <misc>". Uses ck/cc/cr/cm BSS.
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
    ; restore pristine
    lea     rsi, [bk]
    lea     rdi, [s0]
    mov     ecx, 8192
    rep     movsb
    mov     edi, [ck]
    mov     esi, [cpat]
    call    inject
    call    repair_frame
    test    eax, eax
    jnz     .refused
    call    memeq832
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
    ; deterministic fill + complement shell + backup + refs
    xor     ecx, ecx
.fill:
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, 17
    xor     eax, 0xA5
    mov     [s0+rcx], al
    xor     al, 0x55
    mov     [s1+rcx], al
    inc     ecx
    cmp     ecx, 4096
    jne     .fill
    mov     dword [s0], 0x32465345  ; "ESF2"
    mov     eax, 0x32465345
    xor     eax, 0x55555555
    mov     dword [s1], eax         ; complement stays consistent
    lea     rsi, [s0]
    lea     rdi, [bk]
    mov     ecx, 8192
    rep     movsb
    call    build_refs
    mov     rax, 0x123456789
    mov     [xsst], rax
    ; matrix: k in {1,2,3,4,6,8} x {spread, clust}
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
TKL = $ - TK
PSP db ' spread '
PSPL = $ - PSP
PCL db ' clust '
PCLL = $ - PCL
segment readable writeable
s0 rb 4096
s1 rb 4096
bk rb 8192
refB rd 48
refG rd 3
se1 rq 1
se2 rq 1
se3 rq 1
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

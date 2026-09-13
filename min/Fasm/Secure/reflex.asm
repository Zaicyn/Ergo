; reflex.asm -- sense vs reflex vs full repair tiers (Secure stage 3).
; 9 doublets x 2 tubules (A/B = duplex) x 512 B. Same error draws run
; through all three policies per trial (snapshot/restore between).
;   sense  (9+0, no dynein): S0 residuals only, detect only, no touch.
;   reflex (9+0 + dynein): S0/S1, SEC attempt WITHOUT S2/S3 gates,
;            reverify S0/S1, tombstone (0xAA + flag) on failure.
;   full   (9+2 + central pair): S0-S3 + SEC gates + duplex 1+1 +
;            unique-2 search + refuse (torusecc ladder, 9-wide).
; Verdicts (uniform): corr = bytes identical; apop = tomb flags set;
; det = ended detected, no tomb; misc = claimed clean but bytes differ.
; TSV: "R <pol> k=<k> <pat> <corr> <apop> <det> <misc>".
format ELF64 executable 3
entry _start
NDBL = 9
DBIN = 512
FRM  = 4608
NTR  = 200
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
; -- triple4: rdi = ptr, esi = n -> eax,ebx,ecx,r10d (S0..S3 mod 2^32) --
; Clobbers rax,rbx,rcx,rdx,rsi,rdi,r8-r10. Preserves r12-r15,rbp.
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
; -- build_refs: all per-doublet per-tubule S0..S3 + globals --
build_refs:
    push    rbx
    push    r12
    xor     ebx, ebx                ; d
.bl:
    cmp     ebx, NDBL
    jae     .bglob
    xor     r12d, r12d              ; t
.shl:
    cmp     r12d, 2
    jae     .bnext
    mov     eax, ebx
    shl     eax, 9                  ; d*512
    lea     rdi, [tubA+rax]
    test    r12d, r12d
    jz      .sh0
    lea     rdi, [tubB+rax]
.sh0:
    mov     esi, DBIN
    push    rbx
    push    r12
    call    triple4                 ; eax,ebx,ecx,r10d
    mov     r8d, eax
    mov     r9d, ebx
    mov     r11d, ecx
    mov     r13d, r10d
    pop     r12
    pop     rbx
    mov     eax, ebx
    shl     eax, 1
    add     eax, r12d
    shl     eax, 4                  ; (d*2+t)*16 byte off
    lea     rdx, [refD+rax]
    mov     dword [rdx], r8d
    mov     dword [rdx+4], r9d
    mov     dword [rdx+8], r11d
    mov     dword [rdx+12], r13d
    inc     r12d
    jmp     .shl
.bnext:
    inc     ebx
    jmp     .bl
.bglob:
    lea     rdi, [tubA]
    mov     esi, FRM
    call    triple4
    mov     dword [refG], eax
    mov     dword [refG+4], ebx
    mov     dword [refG+8], ecx
    mov     dword [refG+12], r10d
    lea     rdi, [tubB]
    mov     esi, FRM
    call    triple4
    mov     dword [refG+16], eax
    mov     dword [refG+20], ebx
    mov     dword [refG+24], ecx
    mov     dword [refG+28], r10d
    pop     r12
    pop     rbx
    ret
; -- resdbl: rdi = resbuf[32B], esi = d -> eax OR of 8 residuals --
; Preserves rbx,r12-r15,rbp.
resdbl:
    push    rbx
    push    r12
    push    r15
    mov     r15, rdi
    mov     r12d, esi
    mov     eax, esi
    shl     eax, 9
    lea     rdi, [tubA+rax]
    mov     esi, DBIN
    call    triple4
    mov     edx, r12d
    shl     edx, 1
    shl     edx, 4
    lea     r8, [refD+rdx]
    mov     r9d, eax
    sub     r9d, [r8]
    mov     dword [r15], r9d
    mov     r9d, ebx
    sub     r9d, [r8+4]
    mov     dword [r15+4], r9d
    mov     r9d, ecx
    sub     r9d, [r8+8]
    mov     dword [r15+8], r9d
    mov     r9d, r10d
    sub     r9d, [r8+12]
    mov     dword [r15+12], r9d
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [tubB+rax]
    mov     esi, DBIN
    call    triple4
    mov     edx, r12d
    shl     edx, 1
    add     edx, 1
    shl     edx, 4
    lea     r8, [refD+rdx]
    mov     r9d, eax
    sub     r9d, [r8]
    mov     dword [r15+16], r9d
    mov     r9d, ebx
    sub     r9d, [r8+4]
    mov     dword [r15+20], r9d
    mov     r9d, ecx
    sub     r9d, [r8+8]
    mov     dword [r15+24], r9d
    mov     r9d, r10d
    sub     r9d, [r8+12]
    mov     dword [r15+28], r9d
    mov     eax, [r15]
    or      eax, [r15+4]
    or      eax, [r15+8]
    or      eax, [r15+12]
    or      eax, [r15+16]
    or      eax, [r15+20]
    or      eax, [r15+24]
    or      eax, [r15+28]
    pop     r15
    pop     r12
    pop     rbx
    ret
; -- sec_bare: rdi,esi,e0=edx,e1=ecx -> eax 1 applied / 0 refused --
; S0/S1 solve, NO S2/S3 gates (reflex has no central pair).
; Clobbers rax,rbx,rcx,rdx,rsi,rdi,r8-r11. Preserves r12-r15,rbp.
sec_bare:
    push    rbx
    movsxd  r10, edx
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
    movsxd  r11, ecx
    mov     eax, r11d
    cdq
    idiv    r10d
    test    edx, edx
    jnz     .fail
    cmp     eax, 1
    jl      .fail
    cmp     eax, esi
    jg      .fail
    sub     byte [rdi+rax-1], r10b
    mov     eax, 1
    pop     rbx
    ret
.fail:
    xor     eax, eax
    pop     rbx
    ret
; -- sec_gated: + e2=r8d, e3=r9d gates. Otherwise as sec_bare. --
sec_gated:
    push    rbx
    movsxd  r10, edx
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
    movsxd  r11, ecx
    mov     eax, r11d
    cdq
    idiv    r10d
    test    edx, edx
    jnz     .fail
    cmp     eax, 1
    jl      .fail
    cmp     eax, esi
    jg      .fail
    movsxd  r11, r8d
    mov     rbx, r10
    imul    rbx, rax
    imul    rbx, rax
    cmp     rbx, r11
    jne     .fail
    imul    rbx, rax
    cmp     ebx, r9d
    jne     .fail
    sub     byte [rdi+rax-1], r10b
    mov     eax, 1
    pop     rbx
    ret
.fail:
    xor     eax, eax
    pop     rbx
    ret
; -- search2: needs se1/se2/se3 (s64 BSS) + se3b (u32). -> eax nsol(0..2).
; Unique in sd1/sp1/sd2/sp2. Clobbers rax,rcx,rdx,rsi,rdi,r8-r11;
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
    mov     r11, rax
    imul    r11, rbx
    imul    r11, rbx
    imul    r11, rbx
    mov     r10, r14
    imul    r10, r12
    imul    r10, r12
    imul    r10, r12
    add     r11, r10
    cmp     r11d, [se3b]
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
; -- tombstone: edi = doublet. Poisons both tubules, sets flag. --
; Preserves rbx. Clobbers rax,rcx,rdi.
tombstone:
    push    rbx
    mov     ebx, edi
    shl     ebx, 9                  ; byte base
    lea     rdi, [tubA+rbx]
    mov     al, 0xAA
    mov     ecx, DBIN
    rep     stosb
    lea     rdi, [tubB+rbx]
    mov     al, 0xAA
    mov     ecx, DBIN
    rep     stosb
    shr     ebx, 9                  ; d
    mov     dword [tomb+rbx*4], 1
    pop     rbx
    ret
; -- inject: edi = k, esi = clustered. Positions flat 0..9215 (div). --
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
    xor     edx, edx
    mov     rcx, 9216
    div     rcx                     ; edx = pos (full 64-bit mod, matches C %)
    mov     r10d, edx
    shr     r10d, 10                ; d = pos/1024
    mov     ecx, edx
    and     ecx, 1023
    shr     ecx, 9
    mov     r11d, ecx               ; t
    and     edx, 511                ; o
    mov     ecx, r10d
    shl     ecx, 9                  ; d*512
    add     edx, ecx
    mov     r12d, edx               ; d*512+o (64-bit below)
.dloop_s:
    lea     rdi, [xsst]
    call    xs64
    and     eax, 255
    inc     eax
    and     eax, 255
    jz      .dloop_s
    lea     rdi, [tubA+r12]
    test    r11d, r11d
    jz      .spxor
    lea     rdi, [tubB+r12]
.spxor:
    xor     byte [rdi], al
    inc     ebx
    jmp     .sploop
.cl:
    lea     rdi, [xsst]
    call    xs64
    xor     edx, edx
    mov     ecx, 9
    div     rcx
    mov     r15d, edx               ; db1 (full 64-bit mod)
    lea     rdi, [xsst]
    call    xs64
    and     eax, 7
    lea     eax, [r15+rax+1]        ; db1+1+(r&7): offset 1..8
    xor     edx, edx
    mov     ecx, 9
    div     ecx
    mov     r12d, edx               ; db2 (offset never mult of 9: always != db1)
    mov     eax, r13d
    shr     eax, 1
    mov     r14d, eax               ; split
    xor     ebx, ebx
.clloop:
    cmp     ebx, r13d
    jae     .done
    cmp     r13d, 4
    jg      .two
    mov     r11d, r15d
    jmp     .have_db
.two:
    cmp     ebx, r14d
    jl      .first_half
    mov     r11d, r12d
    jmp     .have_db
.first_half:
    mov     r11d, r15d
.have_db:
    lea     rdi, [xsst]
    call    xs64
    mov     r10d, eax
    and     r10d, 1                 ; tub
    shr     eax, 1
    and     eax, 511                ; o
    mov     edx, r11d
    shl     edx, 9                  ; db*512
    add     eax, edx
    mov     r11d, eax               ; full off in tub
.dloop_c:
    lea     rdi, [xsst]
    call    xs64
    and     eax, 255
    inc     eax
    and     eax, 255
    jz      .dloop_c
    lea     rdi, [tubA+r11]
    test    r10d, r10d
    jz      .clxor
    lea     rdi, [tubB+r11]
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
; -- memeqT -> eax 1 equal / 0 differ (tubA/B vs bkA/B). --
memeqT:
    lea     rdi, [tubA]
    lea     rsi, [bkA]
    mov     ecx, FRM
    repe    cmpsb
    jne     .no
    lea     rdi, [tubB]
    lea     rsi, [bkB]
    mov     ecx, FRM
    repe    cmpsb
    jne     .no
    mov     eax, 1
    ret
.no:
    xor     eax, eax
    ret
; -- tomb_any -> eax 1 if any tomb flag set. --
tomb_any:
    xor     eax, eax
    xor     ecx, ecx
.tl:
    cmp     ecx, NDBL
    jae     .td
    or      eax, [tomb+rcx*4]
    inc     ecx
    jmp     .tl
.td:
    test    eax, eax
    setnz   al
    movzx   eax, al
    ret
; -- run_sense -> eax 1 detected / 0 clean. No mutation. --
run_sense:
    push    rbx
    push    r12
    xor     ebx, ebx
.sl:
    cmp     ebx, NDBL
    jae     .clean
    lea     rdi, [resb]
    mov     esi, ebx
    call    resdbl
    mov ecx, dword [resb]
    or      ecx, dword [resb+16]
    jnz     .det
    inc     ebx
    jmp     .sl
.clean:
    xor     eax, eax
    jmp     .out
.det:
    mov     eax, 1
.out:
    pop     r12
    pop     rbx
    ret
; -- run_reflex -> eax 1 nonclean / 0 clean-claim. May tombstone. --
run_reflex:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    lea     rdi, [tomb]
    xor     eax, eax
    mov     ecx, NDBL
    rep     stosd
    xor     ebx, ebx                ; d
.rl:
    cmp     ebx, NDBL
    jae     .rend
    lea     rdi, [resb]
    mov     esi, ebx
    call    resdbl
    mov ecx, dword [resb]
    or      ecx, dword [resb+4]
    or      ecx, dword [resb+16]
    or      ecx, dword [resb+20]
    jz      .rnext
    xor     r14d, r14d              ; t
.tubloop:
    cmp     r14d, 2
    jae     .tcheck
    mov     eax, r14d
    shl     eax, 4
    lea     rcx, [resb+rax]
    mov     edx, [rcx]
    or      edx, [rcx+4]
    jz      .tnext
    mov     eax, ebx
    shl     eax, 9
    lea     rdi, [tubA+rax]
    test    r14d, r14d
    jz      .tptr
    lea     rdi, [tubB+rax]
.tptr:
    mov     esi, DBIN
    mov     edx, [rcx]
    mov     ecx, [rcx+4]
    call    sec_bare
    test    eax, eax
    jz      .dotomb
    lea     rdi, [resb]
    mov     esi, ebx
    call    resdbl
    mov     eax, r14d
    shl     eax, 4
    lea     rcx, [resb+rax]
    mov     edx, [rcx]
    or      edx, [rcx+4]
    jz      .tnext
.dotomb:
    mov     edi, ebx
    call    tombstone
    jmp     .rnext
.tnext:
    inc     r14d
    jmp     .tubloop
.tcheck:
    jmp     .rnext
.rnext:
    inc     ebx
    jmp     .rl
.rend:
    call    tomb_any
    test    eax, eax
    jnz     .ret1
    xor     eax, eax
    jmp     .retd
.ret1:
    mov     eax, 1
.retd:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- run_full -> eax 0 ok / 1 refused. torusecc ladder, 9-wide. --
; SEC+S2/S3 gates, duplex 1+1, unique-2 search + S3, refuse. No tombs.
; Preserves rbx,r12-r15,rbp.
run_full:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     dword [reffail], 0
    xor     r12d, r12d              ; d
.dloop:
    cmp     r12d, NDBL
    jae     .glob
    lea     rdi, [resf]
    mov     esi, r12d
    call    resdbl
    test    eax, eax
    jz      .dnext
    xor     r14d, r14d              ; t
.st:
    cmp     r14d, 2
    jae     .sver
    mov     eax, r14d
    shl     eax, 4
    lea     rcx, [resf+rax]
    mov     edx, [rcx]
    or      edx, [rcx+4]
    or      edx, [rcx+8]
    or      edx, [rcx+12]
    jz      .stnext
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [tubA+rax]
    test    r14d, r14d
    jz      .sp
    lea     rdi, [tubB+rax]
.sp:
    mov     esi, DBIN
    mov     edx, [rcx]
    mov     r8d, [rcx+8]
    mov     r9d, [rcx+12]
    mov     ecx, [rcx+4]
    call    sec_gated
.stnext:
    inc     r14d
    jmp     .st
.sver:
    lea     rdi, [resf]
    mov     esi, r12d
    call    resdbl
    test    eax, eax
    jz      .dnext
    mov eax, dword [resf]
    or      eax, dword [resf+4]
    or      eax, dword [resf+8]
    or      eax, dword [resf+12]
    mov ecx, dword [resf+16]
    or      ecx, dword [resf+20]
    or      ecx, dword [resf+24]
    or      ecx, dword [resf+28]
    test    eax, eax
    jz      .only1
    test    ecx, ecx
    jnz     .dorefuse
    mov     r14d, 0
    jmp     .dosearch
.only1:
    test    ecx, ecx
    jz      .dnext
    mov     r14d, 1
.dosearch:
    mov     eax, r14d
    shl     eax, 4
    lea     rcx, [resf+rax]
    mov     eax, [rcx]
    movsxd  r8, eax
    mov     [se1], r8
    mov     eax, [rcx+4]
    movsxd  r8, eax
    mov     [se2], r8
    mov     eax, [rcx+8]
    movsxd  r8, eax
    mov     [se3], r8
    mov     eax, [rcx+12]
    mov     dword [se3b], eax
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [tubA+rax]
    test    r14d, r14d
    jz      .sptr
    lea     rdi, [tubB+rax]
.sptr:
    mov     esi, DBIN
    call    search2
    cmp     eax, 1
    jne     .dorefuse
    mov     eax, r12d
    shl     eax, 9
    lea     rdi, [tubA+rax]
    test    r14d, r14d
    jz      .sptr2
    lea     rdi, [tubB+rax]
.sptr2:
    mov     eax, [sd1]
    mov     ecx, [sp1]
    sub     byte [rdi+rcx-1], al
    mov     eax, [sd2]
    mov     ecx, [sp2]
    sub     byte [rdi+rcx-1], al
    lea     rdi, [resf]
    mov     esi, r12d
    call    resdbl
    test    eax, eax
    jnz     .dorefuse
    jmp     .dnext
.dorefuse:
    mov     dword [reffail], 1
    jmp     .dnext
.dnext:
    inc     r12d
    jmp     .dloop
.glob:
    cmp     dword [reffail], 0
    jne     .rfail
    lea     rdi, [tubA]
    mov     esi, FRM
    call    triple4
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
    sub     r10d, [refG+12]
    jnz     .rfail
    lea     rdi, [tubB]
    mov     esi, FRM
    call    triple4
    sub     eax, [refG+16]
    or      eax, eax
    jnz     .rfail
    mov     eax, ebx
    sub     eax, [refG+20]
    or      eax, eax
    jnz     .rfail
    mov     eax, ecx
    sub     eax, [refG+24]
    or      eax, eax
    jnz     .rfail
    sub     r10d, [refG+28]
    jnz     .rfail
    xor     eax, eax
    jmp     .retdone
.rfail:
    mov     eax, 1
.retdone:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
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
; -- trial_cell: edi = k, esi = pat. 3 policies per trial, same errors. --
trial_cell:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     [ck], edi
    mov     [cpat], esi
    lea     rdi, [pacc]
    xor     eax, eax
    mov     ecx, 12
    rep     stosd
    mov     r15d, NTR
.tloop:
    lea     rsi, [bkA]
    lea     rdi, [tubA]
    mov     ecx, FRM
    rep     movsb
    lea     rsi, [bkB]
    lea     rdi, [tubB]
    mov     ecx, FRM
    rep     movsb
    mov     edi, [ck]
    mov     esi, [cpat]
    call    inject
    lea     rsi, [tubA]
    lea     rdi, [snapA]
    mov     ecx, FRM
    rep     movsb
    lea     rsi, [tubB]
    lea     rdi, [snapB]
    mov     ecx, FRM
    rep     movsb
    xor     r13d, r13d              ; p = policy
.ploop:
    cmp     r13d, 3
    jae     .tnext
    lea     rsi, [snapA]
    lea     rdi, [tubA]
    mov     ecx, FRM
    rep     movsb
    lea     rsi, [snapB]
    lea     rdi, [tubB]
    mov     ecx, FRM
    rep     movsb
    lea     rdi, [tomb]
    xor     eax, eax
    mov     ecx, NDBL
    rep     stosd
    cmp     r13d, 0
    je      .psense
    cmp     r13d, 1
    je      .preflex
    call    run_full
    jmp     .verdict
.psense:
    call    run_sense
    jmp     .verdict
.preflex:
    call    run_reflex
.verdict:
    mov     r14d, eax               ; claim
    call    tomb_any
    test    eax, eax
    jz      .notomb
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx+4]           ; apop
    jmp     .pnext
.notomb:
    test    r14d, r14d
    jnz     .det
    call    memeqT
    test    eax, eax
    jz      .misc
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx]             ; corr
    jmp     .pnext
.misc:
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx+12]          ; misc
    jmp     .pnext
.det:
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx+8]           ; det
.pnext:
    inc     r13d
    jmp     .ploop
.tnext:
    dec     r15d
    jnz     .tloop
    xor     r13d, r13d
.prloop:
    cmp     r13d, 3
    jae     .pdone
    lea     rsi, [linebuf]
    mov     ax, word [HRP]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, r13d
    call    pdec
    mov     ax, word [HRK]
    mov     [rsi], ax
    mov     al, byte [HRK+2]
    mov     [rsi+2], al
    add     rsi, 3
    mov     eax, [ck]
    call    pdec
    cmp     dword [cpat], 0
    je      .prsp
    mov     eax, dword [HPCL]
    mov     [rsi], eax
    mov     ax, word [HPCL+4]
    mov     [rsi+4], ax
    mov     al, byte [HPCL+6]
    mov     [rsi+6], al
    add     rsi, 7
    jmp     .prnums
.prsp:
    mov     eax, dword [HPSP]
    mov     [rsi], eax
    mov     eax, dword [HPSP+4]
    mov     [rsi+4], eax
    add     rsi, 8
.prnums:
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    mov     eax, [rdx]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    mov     eax, [rdx+4]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    mov     eax, [rdx+8]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    mov     eax, [rdx+12]
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    lea     rdx, [linebuf]
    mov     rcx, rsi
    sub     rcx, rdx
    mov     rsi, rdx
    mov     rdx, rcx
    call    wstr
    inc     r13d
    jmp     .prloop
.pdone:
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
    mov     [tubA+rcx], al
    xor     al, 0x55
    mov     [tubB+rcx], al
    inc     ecx
    cmp     ecx, FRM
    jne     .fill
    mov     dword [tubA], 0x32465345  ; "ESF2"
    mov     eax, 0x32465345
    xor     eax, 0x55555555
    mov     dword [tubB], eax
    lea     rsi, [tubA]
    lea     rdi, [bkA]
    mov     ecx, FRM
    rep     movsb
    lea     rsi, [tubB]
    lea     rdi, [bkB]
    mov     ecx, FRM
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
HRP db 'R '
HRK db ' k='
HPSP db ' spread '
HPCL db ' clust '
segment readable writeable
tubA rb 4608
tubB rb 4608
snapA rb 4608
snapB rb 4608
bkA rb 4608
bkB rb 4608
refD rd 72
refG rd 8
tomb rd 9
se1 rq 1
se2 rq 1
se3 rq 1
se3b rd 1
sd1 rd 1
sp1 rd 1
sd2 rd 1
sp2 rd 1
xsst rq 1
linebuf rb 192
dbuf rb 24
resb rb 32
resf rb 32
reffail rd 1
pacc rd 12
ck rd 1
cpat rd 1

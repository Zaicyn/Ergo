; alignchk.asm -- overlap window for shift re-alignment (Secure stage 4).
; Two 4096 B units A, B with shared overlap B[0..W) = A[4096-W..4096).
; Trial types per W in {64,256,512}:
;   corrupt: flip k in overlap (one/both sides) -> agreement + triples.
;   shift:   B shifted left by s (drop s, zero tail) -> re-align by
;            overlap correlation, reconstruct dropped prefix from overlap,
;            verify by triple. ESF-only control (SEC, no overlap) runs
;            alongside to show shift-fragility of position-locked sums.
;   shco:    shift s + 1 corrupt byte -> re-align + SEC.
; Re-align rule: t in [0..128), t < W, length W-t >= 4; score = matches
; of A[4096-W+t..4096) vs B'[0..W-t); accept iff UNIQUE max and full
; agreement, else refuse. Verdicts via pristine memcmp + triple verify.
; TSV: "A <pol:0=esf,1=ovl> W=<W> <type> <param> <a> <b> <c> [d]".
format ELF64 executable 3
entry _start
NTR  = 200
SMAX = 512
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
; -- triple4: rdi,esi -> eax,ebx,ecx,r10d. Clobbers +r10. Preserves r12-r15.
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
; -- sec4: rdi,esi,e0=edx,e1=ecx,e2=r8d,e3=r9d -> eax 1/0. Full gates. --
sec4:
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
; -- agreeW: edx = W, esi = t -> eax = matches(A[4096-W+t .. 4096),
; Bp[0 .. W-t)). Requires 0 <= t < W. Clobbers rax,rcx,rdi,r8.
; Preserves rbx,rdx,esi,r9-r15.
agreeW:
    push    rbx
    mov     ebx, 4096
    sub     ebx, edx
    add     ebx, esi                ; A start
    lea     rdi, [unitA+rbx]
    lea     rbx, [unitB]
    mov     ecx, edx
    sub     ecx, esi                ; len = W-t
    xor     eax, eax
.agl:
    test    ecx, ecx
    jz      .adone
    mov     r8b, [rdi]
    cmp     r8b, [rbx]
    jne     .anext
    inc     eax
.anext:
    inc     rdi
    inc     rbx
    dec     ecx
    jmp     .agl
.adone:
    pop     rbx
    ret
; -- build_frame: edi = W. Fills A/B, sets overlap, backups, refs. --
build_frame:
    push    rbx
    push    r12
    push    r13
    mov     r13d, edi               ; W
    xor     ecx, ecx
.fillA:
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, 17
    xor     eax, 0xA5
    mov     edx, ecx
    shr     edx, 8
    xor     eax, edx                ; break 256-period (shift recovery needs aperiodic data)
    mov     [unitA+rcx], al
    inc     ecx
    cmp     ecx, 4096
    jne     .fillA
    mov     dword [unitA], 0x32465345
    xor     ecx, ecx
.fillB:
    mov     eax, ecx
    imul    eax, eax, 67
    add     eax, 41
    xor     eax, 0x3C
    mov     edx, ecx
    shr     edx, 8
    xor     eax, edx
    mov     [unitB+rcx], al
    inc     ecx
    cmp     ecx, 4096
    jne     .fillB
    mov     dword [unitB], 0x32465345
    ; overlap B[0..W) = A[4096-W..]
    mov     eax, 4096
    sub     eax, r13d
    lea     rsi, [unitA+rax]
    lea     rdi, [unitB]
    mov     ecx, r13d
    rep     movsb
    ; backups
    lea     rsi, [unitA]
    lea     rdi, [bkA]
    mov     ecx, 4096
    rep     movsb
    lea     rsi, [unitB]
    lea     rdi, [bkB]
    mov     ecx, 4096
    rep     movsb
    ; refs
    lea     rdi, [unitA]
    mov     esi, 4096
    call    triple4
    mov     dword [refA], eax
    mov     dword [refA+4], ebx
    mov     dword [refA+8], ecx
    mov     dword [refA+12], r10d
    lea     rdi, [unitB]
    mov     esi, 4096
    call    triple4
    mov     dword [refB], eax
    mov     dword [refB+4], ebx
    mov     dword [refB+8], ecx
    mov     dword [refB+12], r10d
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- restore_pristine / snapshot_state --
restore_pristine:
    lea     rsi, [bkA]
    lea     rdi, [unitA]
    mov     ecx, 4096
    rep     movsb
    lea     rsi, [bkB]
    lea     rdi, [unitB]
    mov     ecx, 4096
    rep     movsb
    ret
snapshot_state:
    lea     rsi, [unitA]
    lea     rdi, [snapA]
    mov     ecx, 4096
    rep     movsb
    lea     rsi, [unitB]
    lea     rdi, [snapB]
    mov     ecx, 4096
    rep     movsb
    ret
restore_snap:
    lea     rsi, [snapA]
    lea     rdi, [unitA]
    mov     ecx, 4096
    rep     movsb
    lea     rsi, [snapB]
    lea     rdi, [unitB]
    mov     ecx, 4096
    rep     movsb
    ret
; -- unit_resid: rdi = unit ptr, rsi = ref ptr -> edx,ecx,r8d,r9d = e0..e3 --
; Clobbers rax,rbx,rcx,rdx,rsi,rdi,r8-r10. Preserves r12-r15,rbp.
unit_resid:
    push    r12
    mov     r12, rsi                ; ref (preserved across triple4)
    mov     esi, 4096
    call    triple4                 ; eax,ebx,ecx,r10d
    push    rax
    push    rbx
    push    rcx
    push    r10
    mov     edx, [rsp+24]
    sub     edx, [r12]
    mov     ecx, [rsp+16]
    sub     ecx, [r12+4]
    mov     r8d, [rsp+8]
    sub     r8d, [r12+8]
    mov     r9d, [rsp]
    sub     r9d, [r12+12]
    add     rsp, 32
    pop     r12
    ret
; -- inject_corr: edi = k. Flip k bytes in overlap (sides drawn). --
; W from [cW]. Preserves rbx,r12-r15,rbp.
inject_corr:
    push    rbx
    push    r12
    push    r13
    push    r14
    mov     r13d, edi               ; k
    mov     eax, [cW]
    dec     eax
    mov     r14d, eax               ; Wmask (W pow2)
    xor     ebx, ebx                ; i
.cloop:
    cmp     ebx, r13d
    jae     .done
    lea     rdi, [xsst]
    call    xs64                    ; draw A: side + pos
    mov     r12d, eax
    and     r12d, 1                 ; side (xs64-safe reg)
    shr     eax, 1
    and     eax, r14d               ; pos = (A>>1) & (W-1)
    mov     r11d, eax               ; pos (xs64-safe)
.dloop:
    lea     rdi, [xsst]
    call    xs64                    ; draw B: delta
    and     eax, 255
    inc     eax
    and     eax, 255
    jz      .dloop
    mov     ecx, 4096
    sub     ecx, [cW]
    lea     rdi, [unitA+rcx]
    add     rdi, r11
    test    r12d, r12d
    jz      .xorx
    lea     rdi, [unitB+r11]
.xorx:
    xor     byte [rdi], al
    inc     ebx
    jmp     .cloop
.done:
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- apply_shift: edi = s. B[i] = B[i+s] (drop s), zero tail. --
apply_shift:
    push    rbx
    push    r12
    mov     r12d, edi               ; s
    lea     rsi, [unitB]
    add     rsi, r12
    lea     rdi, [unitB]
    mov     ecx, 4096
    sub     ecx, r12d
    rep     movsb                   ; forward: dst <= src always? dst=i,src=i+s: dst<src ✓ safe
    lea     rdi, [unitB+4096]
    sub     rdi, r12
    mov     al, 0
    mov     ecx, r12d
    rep     stosb
    pop     r12
    pop     rbx
    ret
; -- v_esf_corr -> eax 0 ok-claim / 1 dirty. SEC each dirty unit. --
v_esf_corr:
    push    rbx
    push    r12
    push    r13
    lea     rdi, [unitA]
    lea     rsi, [refA]
    call    unit_resid              ; edx,ecx,r8d,r9d
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jz      .chkB
    lea     rdi, [unitA]
    mov     esi, 4096
    call    sec4
    lea     rdi, [unitA]
    lea     rsi, [refA]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jnz     .dirty
.chkB:
    lea     rdi, [unitB]
    lea     rsi, [refB]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jz      .clean
    lea     rdi, [unitB]
    mov     esi, 4096
    call    sec4
    lea     rdi, [unitB]
    lea     rsi, [refB]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jnz     .dirty
.clean:
    xor     eax, eax
    jmp     .out
.dirty:
    mov     eax, 1
.out:
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- v_ovl_corr -> eax 0/1. Agreement-gated repair. --
v_ovl_corr:
    push    rbx
    push    r12
    push    r13
    mov     edx, [cW]
    xor     esi, esi
    call    agreeW
    cmp     eax, edx
    je      .agok
    call    v_esf_corr              ; repair dirty sides (same as esf here)
    test    eax, eax
    jnz     .dirty
.agok:
    mov     edx, [cW]
    xor     esi, esi
    call    agreeW
    cmp     eax, edx
    jne     .dirty
    lea     rdi, [unitA]
    lea     rsi, [refA]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jnz     .dirty
    lea     rdi, [unitB]
    lea     rsi, [refB]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jnz     .dirty
    xor     eax, eax
    jmp     .out
.dirty:
    mov     eax, 1
.out:
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- find_shift -> eax t* (0..128) or -1. Unique-max full agreement. --
find_shift:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r12d, [cW]
    mov     r13d, -1                ; best
    mov     r14d, -1                ; bestsc
    xor     r15d, r15d              ; tied
    xor     ebx, ebx                ; t
.fsloop:
    cmp     ebx, SMAX
    jae     .fdone
    cmp     ebx, r12d
    jae     .fnext                  ; t >= W: length <= 0, skip
    mov     eax, r12d
    sub     eax, ebx
    cmp     eax, 4
    jb      .fnext                  ; length < 4: refuse zone
    mov     edx, r12d
    mov     esi, ebx
    push    rbx
    push    r12
    call    agreeW
    pop     r12
    pop     rbx
    cmp     eax, r14d
    jg      .newbest
    je      .tie
    jmp     .fnext
.newbest:
    mov     r13d, ebx
    mov     r14d, eax
    xor     r15d, r15d
    jmp     .fnext
.tie:
    mov     r15d, 1
.fnext:
    inc     ebx
    jmp     .fsloop
.fdone:
    test    r15d, r15d
    jnz     .refuse
    cmp     r13d, 0
    jl      .refuse
    mov     eax, r12d
    sub     eax, r13d               ; len = W-best
    cmp     r14d, eax               ; full agreement?
    jne     .refuse
    mov     eax, r13d
    jmp     .fret
.refuse:
    mov     eax, -1
.fret:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- v_esf_shift -> eax 0/1. SEC-only attempt on B. --
v_esf_shift:
    push    rbx
    push    r12
    push    r13
    lea     rdi, [unitB]
    lea     rsi, [refB]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jz      .clean
    lea     rdi, [unitB]
    mov     esi, 4096
    call    sec4
    lea     rdi, [unitB]
    lea     rsi, [refB]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jnz     .dirty
.clean:
    xor     eax, eax
    jmp     .out
.dirty:
    mov     eax, 1
.out:
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- v_ovl_shift -> eax t* or -1. Re-align + reconstruct + verify. --
v_ovl_shift:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    call    find_shift
    cmp     eax, -1
    je      .refuse
    mov     r14d, eax               ; t*
    mov     r12d, [cW]
    ; reconstruct B[0..t) from A-overlap
    mov     eax, 4096
    sub     eax, r12d
    lea     rsi, [unitA+rax]
    lea     rdi, [unitB]
    mov     ecx, r14d
    rep     movsb
    ; shift back: B[t+i] = snapB[i]
    lea     rsi, [snapB]
    lea     rdi, [unitB]
    add     rdi, r14
    mov     ecx, 4096
    sub     ecx, r14d
    rep     movsb
    ; verify triple vs refB
    lea     rdi, [unitB]
    lea     rsi, [refB]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jnz     .refuse
    mov     eax, r14d
    jmp     .fret
.refuse:
    mov     eax, -1
.fret:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- v_ovl_shco and v_esf_shco share v_ovl_shift + SEC tail inline in driver --
; -- corr_core -> eax 0 clean-claim / 1 dirty. SEC dirty units, re-check. --
corr_core:
    push    rbx
    push    r12
    push    r13
    lea     rdi, [unitA]
    lea     rsi, [refA]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jz      .chkB
    lea     rdi, [unitA]
    mov     esi, 4096
    call    sec4
.chkB:
    lea     rdi, [unitB]
    lea     rsi, [refB]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jz      .rechk
    lea     rdi, [unitB]
    mov     esi, 4096
    call    sec4
.rechk:
    mov     edx, [cW]
    xor     esi, esi
    call    agreeW
    cmp     eax, edx
    jne     .dirty
    lea     rdi, [unitA]
    lea     rsi, [refA]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jnz     .dirty
    lea     rdi, [unitB]
    lea     rsi, [refB]
    call    unit_resid
    mov     r13d, edx
    or      r13d, ecx
    or      r13d, r8d
    or      r13d, r9d
    jnz     .dirty
    xor     eax, eax
    jmp     .out
.dirty:
    mov     eax, 1
.out:
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- v_shco -> eax 0 fullok-claim / 1 part / 2 fail. --
v_shco:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    call    find_shift
    cmp     eax, -1
    je      .fail
    mov     r14d, eax               ; t*
    mov     r12d, [cW]
    mov     eax, 4096
    sub     eax, r12d
    lea     rsi, [unitA+rax]
    lea     rdi, [unitB]
    mov     ecx, r14d
    rep     movsb
    lea     rsi, [snapB]
    lea     rdi, [unitB]
    add     rdi, r14
    mov     ecx, 4096
    sub     ecx, r14d
    rep     movsb
    call    corr_core
    test    eax, eax
    jnz     .part
    xor     eax, eax                ; fullok-claim
    jmp     .out
.part:
    mov     eax, 1
    jmp     .out
.fail:
    mov     eax, 2
.out:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- memeqAB -> eax 1 both pristine / 0 differ. --
memeqAB:
    lea     rdi, [unitA]
    lea     rsi, [bkA]
    mov     ecx, 4096
    repe    cmpsb
    jne     .no
    lea     rdi, [unitB]
    lea     rsi, [bkB]
    mov     ecx, 4096
    repe    cmpsb
    jne     .no
    mov     eax, 1
    ret
.no:
    xor     eax, eax
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
; -- corr_cell: edi = W, esi = k. Two policies, TSV C lines. --
corr_cell:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     [cW], edi
    mov     [ck], esi
    lea     rdi, [pacc]
    xor     eax, eax
    mov     ecx, 12
    rep     stosd
    mov     r15d, NTR
.tloop:
    call    restore_pristine
    mov     edi, [ck]
    call    inject_corr
    call    snapshot_state
    xor     r13d, r13d              ; pol
.ploop:
    cmp     r13d, 2
    jae     .tnext
    call    restore_snap
    cmp     r13d, 0
    je      .pesf
    call    v_ovl_corr
    jmp     .verd
.pesf:
    call    v_esf_corr
.verd:
    mov     r14d, eax
    test    eax, eax
    jnz     .det
    call    memeqAB
    test    eax, eax
    jz      .misc
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx]             ; ok
    jmp     .pnext
.misc:
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx+8]           ; misc
    jmp     .pnext
.det:
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx+4]           ; det
.pnext:
    inc     r13d
    jmp     .ploop
.tnext:
    dec     r15d
    jnz     .tloop
    xor     r13d, r13d
.prloop:
    cmp     r13d, 2
    jae     .pdone
    lea     rsi, [linebuf]
    mov     ax, word [LC]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, r13d
    call    pdec
    mov     ax, word [LW]
    mov     [rsi], ax
    mov     al, byte [LW+2]
    mov     [rsi+2], al
    add     rsi, 3
    mov     eax, [cW]
    call    pdec
    mov     ax, word [LK]
    mov     [rsi], ax
    mov     al, byte [LK+2]
    mov     [rsi+2], al
    add     rsi, 3
    mov     eax, [ck]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
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
; -- shift_cell: edi = W, esi = s. TSV S lines (realign/det/false). --
shift_cell:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     [cW], edi
    mov     [cpar], esi
    lea     rdi, [pacc]
    xor     eax, eax
    mov     ecx, 12
    rep     stosd
    mov     r15d, NTR
.tloop:
    call    restore_pristine
    mov     edi, [cpar]
    call    apply_shift
    call    snapshot_state
    xor     r13d, r13d
.ploop:
    cmp     r13d, 2
    jae     .tnext
    call    restore_snap
    cmp     r13d, 0
    je      .pesf
    call    v_ovl_shift
    mov     r14d, eax               ; t* or -1
    cmp     eax, -1
    je      .det
    call    memeqAB
    test    eax, eax
    jz      .false
    cmp     r14d, [cpar]
    je      .realign
    jmp     .false
.pesf:
    call    v_esf_shift
    test    eax, eax
    jnz     .det
    call    memeqAB
    test    eax, eax
    jz      .false
    jmp     .det                    ; s>=1: can't match; claim-0 here is wrong
.det:
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx+4]           ; det
    jmp     .pnext
.false:
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx+8]           ; false
    jmp     .pnext
.realign:
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx]             ; realign
.pnext:
    inc     r13d
    jmp     .ploop
.tnext:
    dec     r15d
    jnz     .tloop
    xor     r13d, r13d
.prloop:
    cmp     r13d, 2
    jae     .pdone
    lea     rsi, [linebuf]
    mov     ax, word [LS]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, r13d
    call    pdec
    mov     ax, word [LW]
    mov     [rsi], ax
    mov     al, byte [LW+2]
    mov     [rsi+2], al
    add     rsi, 3
    mov     eax, [cW]
    call    pdec
    mov     ax, word [LSV]
    mov     [rsi], ax
    mov     al, byte [LSV+2]
    mov     [rsi+2], al
    add     rsi, 3
    mov     eax, [cpar]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
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
; -- shco_cell: edi = W, esi = s. Shift + 1 overlap flip. TSV M lines. --
shco_cell:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     [cW], edi
    mov     [cpar], esi
    lea     rdi, [pacc]
    xor     eax, eax
    mov     ecx, 12
    rep     stosd
    mov     r15d, NTR
.tloop:
    call    restore_pristine
    mov     edi, [cpar]
    call    apply_shift
    mov     edi, 1
    call    inject_corr
    call    snapshot_state
    xor     r13d, r13d
.ploop:
    cmp     r13d, 2
    jae     .tnext
    call    restore_snap
    cmp     r13d, 0
    je      .pesf
    call    v_shco
    cmp     eax, 2
    je      .fail
    test    eax, eax
    jnz     .fail2
    call    memeqAB
    test    eax, eax
    jz      .fail
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx]             ; fullok
    jmp     .pnext
.fail2:
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx+4]           ; part
    jmp     .pnext
.pesf:
    call    v_esf_shift
    test    eax, eax
    jnz     .fail
    call    memeqAB
    test    eax, eax
    jz      .fail
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx]             ; fullok (unreachable in practice)
    jmp     .pnext
.fail:
    mov     eax, r13d
    shl     eax, 4
    lea     rdx, [pacc+rax]
    inc     dword [rdx+8]           ; fail
.pnext:
    inc     r13d
    jmp     .ploop
.tnext:
    dec     r15d
    jnz     .tloop
    xor     r13d, r13d
.prloop:
    cmp     r13d, 2
    jae     .pdone
    lea     rsi, [linebuf]
    mov     ax, word [LM]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, r13d
    call    pdec
    mov     ax, word [LW]
    mov     [rsi], ax
    mov     al, byte [LW+2]
    mov     [rsi+2], al
    add     rsi, 3
    mov     eax, [cW]
    call    pdec
    mov     ax, word [LSV]
    mov     [rsi], ax
    mov     al, byte [LSV+2]
    mov     [rsi+2], al
    add     rsi, 3
    mov     eax, [cpar]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
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
    mov     rax, 0x123456789
    mov     [xsst], rax
    mov     edi, 64
    mov     [cW], edi
    call    build_frame
    mov     edi, 64
    mov     esi, 1
    call    corr_cell
    mov     edi, 64
    mov     esi, 2
    call    corr_cell
    mov     edi, 64
    mov     esi, 1
    call    shift_cell
    mov     edi, 64
    mov     esi, 2
    call    shift_cell
    mov     edi, 64
    mov     esi, 4
    call    shift_cell
    mov     edi, 64
    mov     esi, 8
    call    shift_cell
    mov     edi, 64
    mov     esi, 16
    call    shift_cell
    mov     edi, 64
    mov     esi, 32
    call    shift_cell
    mov     edi, 64
    mov     esi, 64
    call    shift_cell
    mov     edi, 64
    mov     esi, 128
    call    shift_cell
    mov     edi, 64
    mov     esi, 4
    call    shco_cell
    mov     edi, 64
    mov     esi, 16
    call    shco_cell
    mov     edi, 256
    mov     [cW], edi
    call    build_frame
    mov     edi, 256
    mov     esi, 1
    call    corr_cell
    mov     edi, 256
    mov     esi, 2
    call    corr_cell
    mov     edi, 256
    mov     esi, 1
    call    shift_cell
    mov     edi, 256
    mov     esi, 2
    call    shift_cell
    mov     edi, 256
    mov     esi, 4
    call    shift_cell
    mov     edi, 256
    mov     esi, 8
    call    shift_cell
    mov     edi, 256
    mov     esi, 16
    call    shift_cell
    mov     edi, 256
    mov     esi, 32
    call    shift_cell
    mov     edi, 256
    mov     esi, 64
    call    shift_cell
    mov     edi, 256
    mov     esi, 128
    call    shift_cell
    mov     edi, 256
    mov     esi, 200
    call    shift_cell
    mov     edi, 256
    mov     esi, 4
    call    shco_cell
    mov     edi, 256
    mov     esi, 16
    call    shco_cell
    mov     edi, 512
    mov     [cW], edi
    call    build_frame
    mov     edi, 512
    mov     esi, 1
    call    corr_cell
    mov     edi, 512
    mov     esi, 2
    call    corr_cell
    mov     edi, 512
    mov     esi, 1
    call    shift_cell
    mov     edi, 512
    mov     esi, 2
    call    shift_cell
    mov     edi, 512
    mov     esi, 4
    call    shift_cell
    mov     edi, 512
    mov     esi, 8
    call    shift_cell
    mov     edi, 512
    mov     esi, 16
    call    shift_cell
    mov     edi, 512
    mov     esi, 32
    call    shift_cell
    mov     edi, 512
    mov     esi, 64
    call    shift_cell
    mov     edi, 512
    mov     esi, 128
    call    shift_cell
    mov     edi, 512
    mov     esi, 200
    call    shift_cell
    mov     edi, 512
    mov     esi, 256
    call    shift_cell
    mov     edi, 512
    mov     esi, 400
    call    shift_cell
    mov     edi, 512
    mov     esi, 500
    call    shift_cell
    mov     edi, 512
    mov     esi, 4
    call    shco_cell
    mov     edi, 512
    mov     esi, 16
    call    shco_cell
    mov     eax, 60
    xor     edi, edi
    syscall
segment readable
LC db 'C '
LS db 'S '
LM db 'M '
LW db ' W='
LK db ' k='
LSV db ' s='
segment readable writeable
unitA rb 4096
unitB rb 4096
snapA rb 4096
snapB rb 4096
bkA rb 4096
bkB rb 4096
refA rd 4
refB rd 4
xsst rq 1
linebuf rb 192
dbuf rb 24
cW rd 1
ck rd 1
cpar rd 1
pacc rd 12

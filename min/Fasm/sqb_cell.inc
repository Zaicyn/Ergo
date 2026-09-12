; sqb_cell.inc -- shared Squaragon duplex (bio) cell.
;
; Extracted verbatim from min/Fasm/Sq2B/sq2b.asm (oracle-proven there),
; plus sqb_fill (new here, proven by the sqw oracle when it lands).
; Serves sq2b.asm today, sqw.asm next (its recognition layer sits on the
; full cell API), SQ5-adjacent work later.
;
; Paste this file INSIDE your `segment readable executable` section:
; it ends in `segment readable` (LUTs live there), so re-issue your own
; segment directive right after including. Assemble MEMO: fasm resolves
; the include relative to its working directory -- from min/Fasm/Sq2B/
; use:  include '../sqb_cell.inc'
;
; REQUIRED driver BSS (cell instances differ per program; declare these):
;   decbuf  rb 152     ; scratch for excise/commit/transcribe paths
;   hstmp   rb 16      ; AVX syndrome horizontal-sum scratch
;   tmp_s0  rd 1       ; strand_ok temporaries
;   tmp_s1  rd 1
;   item_at rd 256     ; bench bookkeeping set by proofread_commit
;   use_avx2 rb 1      ; AVX2 dispatch flag -- DRIVER MUST INIT via
;                      ; check_avx2 in _start (0 = scalar fallback)
;
; Scalar + AVX2 + dispatch travel together; check_avx2 lives here too.
segment readable executable

SQB_NB  = 8
SQB_NR  = 32
SQB_PAY = 152
CODON_SZ = 168
OCC_OFF = 86016
HEAD_OFF = 86272
TOTAL_OFF = 86304
RETR_OFF = 86312
TOMB_OFF = 86320
SLIP_OFF = 86328
CELL_SZ = 86336
TOMB_MAGIC = 0xDEAD5EED
COMPLEMENT = 0x55

; -- codon_ptr: rdi = cell, esi = b, edx = g, ecx = strand → rax --
; clobbers rax only
codon_ptr:
    mov     eax, esi
    shl     eax, 5
    add     eax, edx
    shl     eax, 1
    add     eax, ecx
    imul    rax, rax, CODON_SZ
    add     rax, rdi
    ret

; -- syn: dispatched (AVX2 when available). Args untouched. --
syn:
    cmp     byte [use_avx2], 0
    je      syn_scalar
    jmp     syn_avx2

; -- syn_scalar: rdi = decoded[152], rsi = &s0, rdx = &s1 --
; bio.h:93 sqb_syn (mod-2^32 wrap is natural in 32-bit regs)
syn_scalar:
    xor     eax, eax
    xor     ecx, ecx
    xor     r8d, r8d
.syn_loop:
    movzx   r9d, byte [rdi+rcx]
    add     eax, r9d
    lea     r10d, [rcx+1]
    imul    r10d, r9d
    add     r8d, r10d
    inc     ecx
    cmp     ecx, SQB_PAY
    jne     .syn_loop
    mov     [rsi], eax
    mov     [rdx], r8d
    ret

syn_avx2:
    vpxor   ymm0, ymm0, ymm0        ; s0
    vpxor   ymm1, ymm1, ymm1        ; s1
    lea     rax, [idx17]
    vmovdqa ymm5, [rax]             ; idx [1..8]
    lea     rax, [idx8]
    mov     ecx, 19
.vlp:
    vpmovzxbd ymm4, qword [rdi]     ; v
    vpaddd  ymm0, ymm0, ymm4         ; s0 += v
    vpmulld ymm6, ymm4, ymm5         ; v*idx
    vpaddd  ymm1, ymm1, ymm6         ; s1 += v*idx
    vpaddd  ymm5, ymm5, [rax]        ; idx += 8
    add     rdi, 8
    dec     ecx
    jnz     .vlp
    lea     rax, [hstmp]
    vextracti128 xmm6, ymm0, 1
    vpaddd  xmm6, xmm6, xmm0
    vmovdqu [rax], xmm6
    mov     ecx, [rax]
    add     ecx, [rax+4]
    add     ecx, [rax+8]
    add     ecx, [rax+12]
    mov     [rsi], ecx              ; s0
    vextracti128 xmm6, ymm1, 1
    vpaddd  xmm6, xmm6, xmm1
    vmovdqu [rax], xmm6
    mov     ecx, [rax]
    add     ecx, [rax+4]
    add     ecx, [rax+8]
    add     ecx, [rax+12]
    mov     [rdx], ecx              ; s1
    vzeroupper
    ret

; -- strand_ok: rdi = codon, esi = strand → eax 0/1 --
; bio.h:102
strand_ok:
    push    rbx
    mov     rbx, rdi
    test    esi, esi
    jnz     .dec1
    lea     rsi, [tmp_s0]
    lea     rdx, [tmp_s1]
    call    syn
    jmp     .cmp
.dec1:
    lea     rdi, [decbuf]
    cmp     byte [use_avx2], 0
    je      .dec_scalar
    ; AVX2 152B complement (VEX-only; verified 27x over scalar, bitwise
    ; identical). rbx = codon (address base only), rdi = decbuf.
    vmovdqa ymm0, yword [C55]       ; 32 x 0x55 (align-32 in rodata)
    vpxor   ymm1, ymm0, [rbx]
    vmovdqu [rdi], ymm1
    vpxor   ymm1, ymm0, [rbx+32]
    vmovdqu [rdi+32], ymm1
    vpxor   ymm1, ymm0, [rbx+64]
    vmovdqu [rdi+64], ymm1
    vpxor   ymm1, ymm0, [rbx+96]
    vmovdqu [rdi+96], ymm1
    vmovdqa xmm2, dqword [C55]      ; low 16 (aligned)
    vpxor   xmm1, xmm2, [rbx+128]
    vmovdqu [rdi+128], xmm1
    mov     rax, [rbx+144]
    xor     rax, qword [C55]        ; low 8 = 0x5555...
    mov     [rdi+144], rax
    vzeroupper
    jmp     .dec_done
.dec_scalar:
    xor     ecx, ecx
.xor_loop:
    mov     al, [rbx+rcx]
    xor     al, COMPLEMENT
    mov     [rdi+rcx], al
    inc     rcx
    cmp     ecx, SQB_PAY
    jne     .xor_loop
.dec_done:
    lea     rsi, [tmp_s0]
    lea     rdx, [tmp_s1]
    call    syn
.cmp:
    mov     eax, [tmp_s0]
    cmp     eax, [rbx+152]
    jne     .fail
    mov     eax, [tmp_s1]
    cmp     eax, [rbx+156]
    jne     .fail
    mov     eax, 1
    pop     rbx
    ret
.fail:
    xor     eax, eax
    pop     rbx
    ret

; -- duplex_mismatch: dispatched (AVX2+POPCNT when available). Args untouched. --
duplex_mismatch:
    cmp     byte [use_avx2], 0
    je      duplex_mismatch_scalar
    jmp     duplex_mismatch_avx2

; -- duplex_mismatch_scalar: rdi = c0, rsi = c1 -> eax count --
; bio.h:115
duplex_mismatch_scalar:
    xor     eax, eax
    xor     ecx, ecx
.mm_loop:
    mov     dl, [rdi+rcx]
    xor     dl, [rsi+rcx]
    xor     dl, COMPLEMENT
    test    dl, dl
    setnz   dl
    movzx   edx, dl
    add     eax, edx
    inc     ecx
    cmp     ecx, SQB_PAY
    jne     .mm_loop
    ret

; -- duplex_mismatch_avx2: rdi = c0, rsi = c1 -> eax (AVX2+POPCNT) --
duplex_mismatch_avx2:
    lea     rdx, [C55]
    vmovdqa ymm7, [rdx]
    xor     eax, eax
    xor     ecx, ecx                ; offset 0,32,64,96
.vlp:
    vmovdqu ymm8, [rdi+rcx]
    vmovdqu ymm9, [rsi+rcx]
    vpxor   ymm8, ymm8, ymm9
    vpcmpeqb ymm8, ymm8, ymm7
    vpmovmskb edx, ymm8             ; 1 = match
    not     edx                     ; 1 = mismatch
    popcnt  edx, edx
    add     eax, edx
    add     ecx, 32
    cmp     ecx, 128
    jb      .vlp
    mov     ecx, 128                ; scalar tail 128..151
.tlp:
    cmp     ecx, 152
    jae     .done
    mov     dl, [rdi+rcx]
    xor     dl, [rsi+rcx]
    xor     dl, 0x55
    test    dl, dl
    setnz   dl
    movzx   edx, dl
    add     eax, edx
    inc     ecx
    jmp     .tlp
.done:
    vzeroupper
    ret

; -- check_avx2: AVX2 + POPCNT + OSXSAVE/XCR0 -> eax 1/0 --
check_avx2:
    mov     eax, 1
    cpuid
    test    ecx, 0x08000000         ; OSXSAVE?
    jz      .no
    test    ecx, 0x00800000         ; POPCNT (bit 23)?
    jz      .no
    xor     ecx, ecx
    xgetbv
    and     eax, 0x6
    cmp     eax, 0x6
    jne     .no
    mov     eax, 7
    xor     ecx, ecx
    cpuid
    test    ebx, 0x20               ; AVX2
    jz      .no
    mov     eax, 1
    ret
.no:
    xor     eax, eax
    ret

; -- strand_write: rdi = codon, rsi = decoded, edx = strand --
; bio.h:127
strand_write:
    push    rbx
    mov     rbx, rdi
    push    rsi
    test    edx, edx
    jnz     .s1
    mov     ecx, SQB_PAY
    rep     movsb
    jmp     .syndrome
.s1:
    xor     ecx, ecx
.xor_loop:
    mov     al, [rsi+rcx]
    xor     al, COMPLEMENT
    mov     [rbx+rcx], al
    inc     rcx
    cmp     ecx, SQB_PAY
    jne     .xor_loop
.syndrome:
    pop     rsi
    mov     rdi, rsi
    lea     rsi, [rbx+152]
    lea     rdx, [rbx+156]
    call    syn
    mov     dword [rbx+160], 0
    mov     dword [rbx+164], 0
    pop     rbx
    ret

; -- excise: rdi = dst, rsi = src, edx = dst_strand --
; bio.h:139
excise:
    cmp     rdi, rsi
    je      .ret
    push    rbx
    push    r12
    mov     rbx, rdi
    mov     r12d, edx
    test    edx, edx
    jz      .src1
    mov     ecx, SQB_PAY
    lea     rdi, [decbuf]
    rep     movsb                   ; src is strand 0: direct copy
    jmp     .age
.src1:
    lea     rdi, [decbuf]           ; src is strand 1: decode
    xor     ecx, ecx
.dec_loop:
    mov     al, [rsi+rcx]
    xor     al, COMPLEMENT
    mov     [rdi+rcx], al
    inc     rcx
    cmp     ecx, SQB_PAY
    jne     .dec_loop
.age:
    mov     eax, [rbx+160]
    push    rax
    mov     rdi, rbx
    lea     rsi, [decbuf]
    mov     edx, r12d
    call    strand_write
    pop     rax
    mov     [rbx+160], eax
    pop     r12
    pop     rbx
.ret:
    ret

; -- proofread_commit: rdi = cell, esi = b, edx = g, ecx = item → eax --
; bio.h:158. Frame: [rsp] = b,g,item,cell after sub; 3 pushes (odd = aligned)
proofread_commit:
    sub     rsp, 32
    mov     [rsp], esi
    mov     [rsp+4], edx
    mov     [rsp+8], ecx
    mov     [rsp+16], rdi
    push    rbx
    push    r12
    push    r13
    lea     rdi, [decbuf]
    mov     r8d, [rsp+24+8]         ; item
    imul    r8d, r8d, 17            ; item*17
    xor     r10d, r10d              ; a
    xor     r11d, r11d              ; s1
    xor     ecx, ecx                ; i
.build:
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, r8d
    xor     eax, 0xA5
    mov     [rdi+rcx], al
    movzx   eax, al
    add     r10d, eax
    lea     edx, [rcx+1]
    imul    edx, eax
    add     r11d, edx
    inc     ecx
    cmp     ecx, SQB_PAY
    jne     .build
    mov     r9d, 2                  ; attempts
.attempt:
    mov     rdi, [rsp+24+16]        ; cell
    mov     esi, [rsp+24]           ; b
    mov     edx, [rsp+24+4]         ; g
    xor     ecx, ecx
    call    codon_ptr
    mov     rbx, rax                ; c0
    mov     rdi, [rsp+24+16]
    mov     esi, [rsp+24]
    mov     edx, [rsp+24+4]
    mov     ecx, 1
    call    codon_ptr
    mov     r12, rax                ; c1
    lea     rsi, [decbuf]
    mov     rdi, rbx
    mov     ecx, SQB_PAY
    rep     movsb
    mov     [rbx+152], r10d
    mov     [rbx+156], r11d
    mov     dword [rbx+160], 0
    mov     dword [rbx+164], 0
    xor     ecx, ecx
.c1_loop:
    mov     al, [decbuf+rcx]
    xor     al, COMPLEMENT
    mov     [r12+rcx], al
    inc     rcx
    cmp     ecx, SQB_PAY
    jne     .c1_loop
    mov     [r12+152], r10d
    mov     [r12+156], r11d
    mov     dword [r12+160], 0
    mov     dword [r12+164], 0
    xor     r8d, r8d                ; mm
    xor     edx, edx                ; va
    xor     r13d, r13d              ; vs
    xor     ecx, ecx
.verify:
    movzx   eax, byte [rbx+rcx]     ; c0 byte
    movzx   edi, byte [r12+rcx]     ; c1 byte
    xor     edi, eax
    xor     edi, COMPLEMENT
    test    edi, edi
    setnz   dil
    or      r8b, dil                ; mm |= ...
    add     edx, eax                ; va += c0
    lea     edi, [rcx+1]
    imul    edi, eax
    add     r13d, edi               ; vs += c0*(i+1)
    inc     ecx
    cmp     ecx, SQB_PAY
    jne     .verify
    test    r8d, r8d
    jnz     .retry
    cmp     edx, r10d
    jne     .retry
    cmp     r13d, r11d
    jne     .retry
    ; success: occupy
    mov     rdi, [rsp+24+16]
    mov     eax, [rsp+24]
    shl     eax, 5
    add     eax, [rsp+24+4]
    mov     byte [rdi+OCC_OFF+rax], 1
    mov     ecx, [rsp+24+8]
    mov     [item_at+rax*4], ecx
    xor     eax, eax
    jmp     .done
.retry:
    mov     rdi, [rsp+24+16]
    inc     qword [rdi+RETR_OFF]
    dec     r9d
    jnz     .attempt
    mov     eax, -1
.done:
    pop     r13
    pop     r12
    pop     rbx
    add     rsp, 32
    ret

; -- alloc_slot: rdi = cell, esi = id, edx = item --
;               rcx = out_b or 0, r8 = out_g or 0 → eax 0/-1 --
; bio.h:194
alloc_slot:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15                     ; 5 pushes, stack stays aligned
    mov     r15, rdi                ; cell
    mov     r12d, edx               ; item
    mov     r14, rcx                ; out_b
    sub     rsp, 32
    mov     [rsp], r8               ; out_g spill (aligned: 5 pushes + 32)
    mov     eax, esi
    and     eax, 31
    mov     eax, [SCATLT+rax*4]
    xor     edx, edx
    mov     ecx, SQB_NB
    div     ecx                     ; edx = b0
    xor     ebx, ebx                ; k
.search:
    mov     eax, edx
    add     eax, ebx
    cmp     eax, SQB_NB
    jb      .have_bin
    sub     eax, SQB_NB
.have_bin:
    mov     r13d, eax               ; bin
    cmp     dword [r15+HEAD_OFF+rax*4], SQB_NR
    jb      .found
    inc     ebx
    cmp     ebx, SQB_NB
    jne     .search
    mov     eax, -1
    jmp     .ret
.found:
    mov     ebx, [r15+HEAD_OFF+r13*4]   ; g = head[bin]
    mov     rdi, r15
    mov     esi, r13d
    mov     edx, ebx
    mov     ecx, r12d
    call    proofread_commit
    test    eax, eax
    jnz     .ret                    ; -1 propagates, returns -1
    inc     dword [r15+HEAD_OFF+r13*4]
    inc     dword [r15+TOTAL_OFF]
    test    r14, r14
    jz      .no_ob
    mov     [r14], r13d
.no_ob:
    mov     rax, [rsp]
    test    rax, rax
    jz      .no_og
    mov     [rax], ebx
.no_og:
    xor     eax, eax
.ret:
    add     rsp, 32
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- transcribe: rdi = cell, esi = b, edx = g, rcx = out → eax --
; bio.h:218
transcribe:
    push    rbx
    mov     rbx, rcx                ; out
    xor     ecx, ecx
    call    codon_ptr               ; rax = c0
    cmp     dword [rax+164], TOMB_MAGIC
    je      .dead
    mov     rdi, rbx
    mov     rsi, rax
    mov     ecx, SQB_PAY
    rep     movsb
    xor     eax, eax
    pop     rbx
    ret
.dead:
    mov     eax, 1
    pop     rbx
    ret

; -- sweep: rdi = cell, rsi = action or 0 → rax unresolved --
; bio.h:231. rbx = b, r12d = g, rbp = c0, r13 = cell, r14 = action,
; r15 = unresolved. mm/ok0 spilled to frame (must survive calls).
sweep:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 24                 ; frame: [rsp]=mm, [rsp+4]=ok0
    mov     r13, rdi                ; cell
    mov     r14, rsi                ; action
    xor     r15, r15                ; unresolved
    xor     ebx, ebx                ; b
.b_loop:
    xor     r12d, r12d              ; g
.g_loop:
    mov     eax, ebx
    shl     eax, 5
    add     eax, r12d               ; idx = b*32+g
    cmp     byte [r13+OCC_OFF+rax], 0
    je      .next
    imul    rax, rax, 336           ; idx * (2 codons * 168 B)
    lea     rbp, [r13+rax]          ; c0 (c1 = c0+168)
    test    r14, r14
    jz      .no_zero
    mov     eax, ebx
    shl     eax, 5
    add     eax, r12d
    mov     byte [r14+rax], 0
.no_zero:
    cmp     dword [rbp+164], TOMB_MAGIC
    je      .next                   ; already dead
    mov     rdi, rbp
    lea     rsi, [rbp+CODON_SZ]
    call    duplex_mismatch
    mov     [rsp], eax              ; spill mm
    mov     rdi, rbp
    xor     esi, esi
    call    strand_ok
    mov     [rsp+4], eax            ; spill ok0
    lea     rdi, [rbp+CODON_SZ]
    mov     esi, 1
    call    strand_ok               ; eax = ok1
    mov     r10d, [rsp]             ; mm
    mov     r11d, [rsp+4]           ; ok0
    test    r10d, r10d
    jnz     .damaged
    test    r11d, r11d
    jz      .damaged
    test    eax, eax
    jz      .damaged
    inc     dword [rbp+160]         ; methylation clock
    lea     rdi, [rbp+CODON_SZ]
    inc     dword [rdi+160]
    jmp     .next
.damaged:
    test    r14, r14
    jz      .branch
    mov     ecx, ebx
    shl     ecx, 5
    add     ecx, r12d
    mov     byte [r14+rcx], 1
.branch:
    test    r11d, r11d
    jz      .q0
    test    eax, eax
    jz      .fix1                   ; ok0 && !ok1
    inc     qword [r13+SLIP_OFF]    ; ok0 && ok1, duplex disagrees
    lea     rdi, [rbp+CODON_SZ]     ; excise(c1, c0, 1)
    mov     rsi, rbp
    mov     edx, 1
    call    excise
    jmp     .closure
.q0:
    test    eax, eax
    jz      .both_dead              ; !ok0 && !ok1
    mov     rdi, rbp                ; !ok0 && ok1: excise(c0, c1, 0)
    lea     rsi, [rbp+CODON_SZ]
    xor     edx, edx
    call    excise
    jmp     .closure
.fix1:                              ; ok0 && !ok1: excise(c1, c0, 1)
    lea     rdi, [rbp+CODON_SZ]
    mov     rsi, rbp
    mov     edx, 1
    call    excise
    jmp     .closure
.both_dead:
    mov     dword [rbp+164], TOMB_MAGIC
    lea     rdi, [rbp+CODON_SZ]
    mov     dword [rdi+164], TOMB_MAGIC
    inc     qword [r13+TOMB_OFF]
    test    r14, r14
    jz      .closure
    mov     ecx, ebx
    shl     ecx, 5
    add     ecx, r12d
    mov     byte [r14+rcx], 2
.closure:
    cmp     dword [rbp+164], TOMB_MAGIC
    je      .next
    mov     rdi, rbp
    lea     rsi, [rbp+CODON_SZ]
    call    duplex_mismatch
    test    eax, eax
    jnz     .unres
    mov     rdi, rbp
    xor     esi, esi
    call    strand_ok
    test    eax, eax
    jz      .unres
    lea     rdi, [rbp+CODON_SZ]
    mov     esi, 1
    call    strand_ok
    test    eax, eax
    jnz     .next
.unres:
    inc     r15
.next:
    inc     r12d
    cmp     r12d, SQB_NR
    jne     .g_loop
    inc     ebx
    cmp     ebx, SQB_NB
    jne     .b_loop
    mov     rax, r15
    add     rsp, 24
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbp
    pop     rbx
    ret


; -- sqb_fill: rdi = out[152], esi = item (deterministic payload) --
; bio.h:82. NEW in this file (sq2b builds payloads inline in commit);
; will be proven by the sqw oracle. Leaf, scratch only.
sqb_fill:
    imul    r8d, esi, 17
    xor     ecx, ecx
.f_loop:
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, r8d
    xor     eax, 0xA5
    mov     [rdi+rcx], al
    inc     ecx
    cmp     ecx, SQB_PAY
    jne     .f_loop
    ret

; -- pay_ok: rdi = payload[152], esi = item → eax 0/1 --
; bio.h:86
pay_ok:
    imul    r8d, esi, 17
    xor     ecx, ecx
.ok_loop:
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, r8d
    xor     eax, 0xA5
    cmp     [rdi+rcx], al
    jne     .fail
    inc     ecx
    cmp     ecx, SQB_PAY
    jne     .ok_loop
    mov     eax, 1
    ret
.fail:
    xor     eax, eax
    ret

segment readable

SCATLT  dd  6,5,4,0,2,3,4,7,4,6,3,0,1,2,1,0,3,6,4,7,4,3,2,0,4,5,6,5,4,0,2,3
align 32
C55 dd 0x55555555, 0x55555555, 0x55555555, 0x55555555, 0x55555555, 0x55555555, 0x55555555, 0x55555555
align 32
idx17   dd 1, 2, 3, 4, 5, 6, 7, 8
idx8    dd 8, 8, 8, 8, 8, 8, 8, 8

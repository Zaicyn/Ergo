; SQW certification driver in flat assembler (FASM 1.73.x, x86-64 Linux).
; Faithful port of benchmark/sqw_cert.c + sqw_core.h. The duplex cell
; itself comes from ../sqb_cell.inc (shared, single source); this file
; holds the recognition layer (hash / cache / refcounts / audit) and the
; cert driver. Goal: byte-identical stdout to sqw_cert.
;
; Internal ABI: args rdi,rsi,rdx,rcx,r8,r9; rbx,rbp,r12-r15 callee-saved.
; No libc: BSS arena, write(2)/exit(2) only. ASCII-only source.
;
; sqw_cell_t layout (from sqw_core.h, behavior-matched):
;   cell @0 (86336), idx[4096] x16B @86336 (65536),
;   ref[8][32] dwords @151872 (1024),
;   refs_total/skips/phys_allocs qwords @152896/152904/152912
;   SQW_SZ = 152920 (19115 qwords, exact)
; Entry: h qword @0, b @8, g @9, used @10.
; Assemble (from this directory): fasm sqw.asm sqw (default 1500 rounds)

format ELF64 executable 3
entry _start

SQW_IDX = 4096
SQW_CAP = 256
SQW_CELL = 86336
SQW_IDB = 86336
SQW_ENT = 16
SQW_RFB = 151872
SQW_RFT = 152896
SQW_SKP = 152904
SQW_PHA = 152912
SQW_SZ = 152920
SQW_QW = 19115
CERT_N = 256

segment readable executable

include '../sqb_cell.inc'   ; shared duplex cell (code + consts + LUTs)

segment readable executable

; -- xoshiro256++ : rdi = state ptr (4 qwords) -> rax --
xoshiro:
    mov     rax, [rdi]
    add     rax, [rdi+24]
    mov     rdx, [rdi+8]
    shl     rdx, 17
    mov     rcx, [rdi]
    xor     [rdi+16], rcx
    mov     rcx, [rdi+8]
    xor     [rdi+24], rcx
    mov     rcx, [rdi+16]
    xor     [rdi+8], rcx
    mov     rcx, [rdi+24]
    xor     [rdi], rcx
    xor     [rdi+16], rdx
    mov     rcx, [rdi+24]
    mov     rdx, rcx
    shl     rcx, 45
    shr     rdx, 19
    or      rcx, rdx
    mov     [rdi+24], rcx
    mov     rdx, rax
    shl     rax, 17
    shr     rdx, 47
    or      rax, rdx
    ret

; -- seed: rdi = state, rsi = seed (10 warmups, callee-saved counter) --
seed_rng:
    push    rbx
    push    r12
    mov     rbx, rdi
    mov     rax, rsi
    mov     rcx, 0x9E3779B97F4A7C15
    add     rax, rcx
    mov     [rbx], rax
    mov     rax, rsi
    mov     rcx, 0xBF58476D1CE4E5B9
    xor     rax, rcx
    mov     [rbx+8], rax
    mov     rax, rsi
    mov     rcx, 0x94D049BB133111EB
    add     rax, rcx
    mov     [rbx+16], rax
    mov     rax, rsi
    mov     rcx, 0xF0BA35E12960E9E7
    xor     rax, rcx
    mov     [rbx+24], rax
    mov     r12d, 10
.seed_loop:
    mov     rdi, rbx
    call    xoshiro
    dec     r12d
    jnz     .seed_loop
    pop     r12
    pop     rbx
    ret

; -- rand_u32: rdi = state -> eax --
rand_u32:
    push    rdi
    call    xoshiro
    pop     rdi
    ret

; -- rand01: rdi = state -> xmm0 double in [0,1) --
rand01:
    push    rdi
    call    xoshiro
    pop     rdi
    shr     rax, 11
    cvtsi2sd xmm0, rax
    mulsd   xmm0, [M53]
    ret

; -- emit_str: rsi = ptr, rdx = len --
emit_str:
    mov     rax, [ocur]
    lea     rdi, [outbuf+rax]
    mov     rcx, rdx
    rep     movsb
    mov     rax, rdi
    sub     rax, outbuf
    mov     [ocur], rax
    ret

; -- emit_u64: rax -> decimal --
emit_u64:
    lea     rdi, [numbuf+31]
    mov     rcx, 10
    test    rax, rax
    jnz     .dig
    dec     rdi
    mov     byte [rdi], '0'
    jmp     .out
.dig:
    xor     edx, edx
    div     rcx
    add     dl, '0'
    dec     rdi
    mov     [rdi], dl
    test    rax, rax
    jnz     .dig
.out:
    mov     rsi, rdi
    lea     rdx, [numbuf+31]
    sub     rdx, rsi
    jmp     emit_str

; -- emit_fdec: xmm0 = double >= 0, ecx = decimals (2 or 6) --
emit_fdec:
    push    rbx
    mov     r8d, ecx
    cvttsd2si r9, xmm0
    cvtsi2sd xmm1, r9
    subsd   xmm0, xmm1
    xor     ecx, ecx
.dig_loop:
    mulsd   xmm0, [DBL_10]
    cvttsd2si eax, xmm0
    mov     [fdigits+rcx], al
    cvtsi2sd xmm1, eax
    subsd   xmm0, xmm1
    inc     ecx
    cmp     ecx, r8d
    jbe     .dig_loop
    xor     ecx, ecx
    ucomisd xmm0, [DBL_0]
    setnz   cl
    mov     eax, r8d
    mov     dl, [fdigits+rax]
    cmp     dl, 5
    ja      .carry
    jb      .print
    test    ecx, ecx
    jnz     .carry
    dec     eax
    test    byte [fdigits+rax], 1
    jz      .print
.carry:
    mov     ecx, r8d
    dec     ecx
.carry_loop:
    inc     byte [fdigits+rcx]
    cmp     byte [fdigits+rcx], 10
    jb      .print
    mov     byte [fdigits+rcx], 0
    dec     ecx
    jns     .carry_loop
    inc     r9
.print:
    mov     rax, r9
    call    emit_u64
    mov     rax, [ocur]
    mov     byte [outbuf+rax], '.'
    inc     qword [ocur]
    mov     rax, [ocur]
    lea     rdi, [outbuf+rax]
    xor     ecx, ecx
.copy_loop:
    cmp     ecx, r8d
    jae     .copied
    mov     al, [fdigits+rcx]
    add     al, '0'
    mov     [rdi+rcx], al
    inc     ecx
    jmp     .copy_loop
.copied:
    movsxd  rax, r8d
    add     [ocur], rax
    pop     rbx
    ret

emit_f6:
    mov     ecx, 6
    jmp     emit_fdec

emit_f2:
    mov     ecx, 2
    jmp     emit_fdec

; -- ratio_fx: rax = num, rdx = den -> xmm0 = num/den or 0.0 --
ratio_fx:
    test    rdx, rdx
    jz      .zero
    push    rbx
    mov     rbx, rdx
    cvtsi2sd xmm0, rax
    cvtsi2sd xmm1, rbx
    divsd   xmm0, xmm1
    pop     rbx
    ret
.zero:
    xorpd   xmm0, xmm0
    ret

; -- atoi: rsi = string -> eax --
atoi:
    xor     eax, eax
    xor     ecx, ecx
.skip:
    movzx   edx, byte [rsi]
    cmp     dl, ' '
    je      .skip_next
    cmp     dl, 9
    je      .skip_next
    jmp     .sign
.skip_next:
    inc     rsi
    jmp     .skip
.sign:
    cmp     dl, '-'
    jne     .plus
    mov     ecx, 1
    inc     rsi
    jmp     .digits
.plus:
    cmp     dl, '+'
    jne     .digits
    inc     rsi
.digits:
    movzx   edx, byte [rsi]
    sub     dl, '0'
    cmp     dl, 9
    ja      .apply
    imul    eax, eax, 10
    movzx   edx, dl
    add     eax, edx
    inc     rsi
    jmp     .digits
.apply:
    test    ecx, ecx
    jz      .ret
    neg     eax
.ret:
    ret

; ================= SQW recognition layer (new; proves itself here) =========

; -- sqw_hash: rdi = payload[152] -> rax u64 (FNV-1a 19 words + finalizer) --
sqw_hash:
    mov     rax, 0x9E3779B97F4A7C15
    xor     ecx, ecx                ; word 0..18
.h_loop:
    cmp     ecx, 19
    jae     .fin
    mov     rdx, [rdi+rcx*8]
    xor     rax, rdx
    mov     rdx, 0x100000001b3
    mul     rdx                     ; low 64 stays in rax (mod 2^64, as C)
    inc     ecx
    jmp     .h_loop
.fin:
    mov     rdx, rax
    shr     rdx, 29
    xor     rax, rdx                ; h ^= h >> 29
    mov     rdx, 0xBF58476D1CE4E5B9
    mul     rdx                     ; h *= ...
    mov     rdx, rax
    shr     rdx, 32
    xor     rax, rdx                ; h ^= h >> 32
    ret

; -- ref_ok: edi = ref word -> eax 1/0 ((lo + hi) == 0xFFFF) --
ref_ok:
    mov     eax, edi
    and     eax, 0xFFFF
    mov     ecx, edi
    shr     ecx, 16
    add     eax, ecx
    cmp     eax, 0xFFFF
    sete    al
    movzx   eax, al
    ret

; -- ref_inc: edi = ref word -> eax (paired ++) --
ref_inc:
    mov     eax, edi
    and     eax, 0xFFFF
    inc     eax                     ; lo+1 (mod 2^16? C: (r&0xFFFF)+1, then
    mov     ecx, eax                ; paired; overflow wraps naturally below)
    not     ecx
    and     ecx, 0xFFFF
    shl     ecx, 16
    and     eax, 0xFFFF
    or      eax, ecx
    ret

; -- ref_one: -> eax = fresh refcount (1 | ~1<<16) --
ref_one:
    mov     eax, 0xFFFE0001
    ret

; -- sqw_init: rdi = w (152920 B zero) --
sqw_init:
    push    rdi
    xor     eax, eax
    mov     ecx, SQW_SZ / 8         ; 19115 qwords exact
    rep     stosq
    pop     rdi
    ret

; -- sqw_alloc: rdi = w, esi = id, edx = item -> eax 0 / -1 --
; Uses decbuf (152 B scratch, free: commit rebuilds from item, not dec).
sqw_alloc:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rbx, rdi                ; w
    mov     r12d, esi               ; id
    mov     r13d, edx               ; item
    lea     rdi, [decbuf]
    mov     esi, r13d
    call    sqb_fill                ; dec = fill(item)
    lea     rdi, [decbuf]
    call    sqw_hash                ; rax = h
    mov     r14, rax                ; h (callee-saved across codon_ptr? codon
                                    ;  clobbers rax only -- but keep in r14)
    and     eax, SQW_IDX - 1        ; h & 4095
    shl     rax, 4                  ; *16
    lea     r15, [rbx+SQW_IDB+rax]  ; e
    cmp     byte [r15+10], 0        ; e->used ?
    je      .miss
    mov     rax, [r15]              ; e->h
    cmp     rax, r14
    jne     .miss
    movzx   r10d, byte [r15+8]      ; b (scratch: codon_ptr/memcmp keep it)
    movzx   r11d, byte [r15+9]      ; g
    mov     rdi, rbx                ; c0 = cell.c[b][g][0] (cell @ w+0)
    mov     esi, r10d
    mov     edx, r11d
    xor     ecx, ecx
    call    codon_ptr               ; rax = c0 (clobbers rax only)
    cmp     dword [rax+164], TOMB_MAGIC
    je      .miss
    mov     rdi, rax
    lea     rsi, [decbuf]
    mov     ecx, SQB_PAY
    repe    cmpsb                   ; byte-exact verify (fail-safe gate)
    jne     .miss
    ; HIT: refcount++, done -- no write, no journal, no proofread
    mov     eax, r10d
    shl     eax, 5
    add     eax, r11d               ; idx
    lea     rdx, [rbx+SQW_RFB]
    mov     edi, [rdx+rax*4]        ; ref[b][g]
    call    ref_inc                 ; eax = new (rdx/r10d/r11d survive: leaf)
    mov     ecx, r10d               ; recompute idx (rax clobbered by call)
    shl     ecx, 5
    add     ecx, r11d
    mov     [rdx+rcx*4], eax
    inc     qword [rbx+SQW_RFT]
    inc     qword [rbx+SQW_SKP]
    lea     rax, [sqw_item_slot_b]
    mov     ecx, r13d
    mov     [rax+rcx*4], r10d
    lea     rax, [sqw_item_slot_g]
    mov     [rax+rcx*4], r11d
    xor     eax, eax
    jmp     .done
.miss:
    mov     rax, r14                ; e = idx + (h&4095)*16
    and     rax, SQW_IDX - 1
    shl     rax, 4
    lea     r15, [rbx+SQW_IDB+rax]  ; e (recomputed; r15 dead since probe)
    sub     rsp, 16                 ; out_b/out_g slots (aligned)
    mov     rdi, rbx
    mov     esi, r12d               ; id
    mov     edx, r13d               ; item
    lea     rcx, [rsp]
    lea     r8, [rsp+8]
    call    alloc_slot
    mov     r10d, [rsp]             ; b
    mov     r11d, [rsp+8]           ; g
    add     rsp, 16
    test    eax, eax
    jnz     .failret
    call    ref_one
    mov     ecx, r10d               ; ref[b][g] = fresh
    shl     ecx, 5
    add     ecx, r11d
    lea     rdx, [rbx+SQW_RFB]
    mov     [rdx+rcx*4], eax
    inc     qword [rbx+SQW_RFT]
    inc     qword [rbx+SQW_PHA]
    mov     [r15], r14              ; e->h
    mov     [r15+8], r10b           ; e->b
    mov     [r15+9], r11b           ; e->g
    mov     byte [r15+10], 1        ; e->used
    lea     rax, [sqw_item_slot_b]
    mov     ecx, r13d
    mov     [rax+rcx*4], r10d
    lea     rax, [sqw_item_slot_g]
    mov     [rax+rcx*4], r11d
    xor     eax, eax
    jmp     .done
.failret:
    mov     eax, -1
.done:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; -- ref_audit: rdi = w, rsi = &sum_ok(int) -> rax = bad slots --
; All cross-call values in callee-saved; addresses recomputed after calls.
ref_audit:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 8                  ; align (6 pushes)
    mov     rbx, rdi                ; w
    mov     rbp, rsi                ; sum_ok
    xor     r14, r14                ; bad
    xor     r12, r12                ; sum
    xor     r13d, r13d              ; b
.b_loop:
    xor     r15d, r15d              ; g
.g_loop:
    mov     eax, r13d
    shl     eax, 5
    add     eax, r15d               ; idx
    cmp     byte [rbx+OCC_OFF+rax], 0
    je      .next
    lea     rdx, [rbx+SQW_RFB]
    mov     edi, [rdx+rax*4]        ; ref[b][g]
    call    ref_ok                  ; eax (clobbers rax,rcx,rdi only)
    test    eax, eax
    jz      .badslot
    mov     eax, r13d               ; recompute (regs above are Call-dead)
    shl     eax, 5
    add     eax, r15d
    lea     rdx, [rbx+SQW_RFB]
    mov     eax, [rdx+rax*4]
    and     eax, 0xFFFF
    add     r12, rax                ; sum += lo
    jmp     .next
.badslot:
    inc     r14
.next:
    inc     r15d
    cmp     r15d, SQB_NR
    jne     .g_loop
    inc     r13d
    cmp     r13d, SQB_NB
    jne     .b_loop
    mov     rax, r12
    cmp     rax, [rbx+SQW_RFT]
    sete    al
    movzx   eax, al
    mov     [rbp], eax              ; *sum_ok
    mov     rax, r14
    add     rsp, 8
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbp
    pop     rbx
    ret

; -- verify_all_items: rdi = w, rsi = stream, edx = n -> rax = ok count --
verify_all_items:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 8
    mov     rbx, rdi                ; w
    mov     r12, rsi                ; stream
    mov     r13d, edx               ; n
    xor     r14d, r14d              ; i
    xor     ebp, ebp                ; ok
.vi:
    cmp     r14d, r13d
    jae     .vdone
    mov     eax, [r12+r14*4]        ; item
    mov     r15d, eax               ; item (callee-saved across calls)
    lea     rdx, [sqw_item_slot_b]
    mov     esi, [rdx+rax*4]        ; b
    lea     rdx, [sqw_item_slot_g]
    mov     edx, [rdx+rax*4]        ; g
    mov     rdi, rbx                ; cell @ w+0
    xor     ecx, ecx                ; strand 0
    call    codon_ptr               ; rax = c0 (clobbers rax only)
    cmp     dword [rax+164], TOMB_MAGIC
    je      .vnext
    mov     rdi, rax                ; c0->g @ +0
    mov     esi, r15d
    call    pay_ok                  ; leaf: keeps callee-saved
    test    eax, eax
    jz      .vnext
    inc     ebp
.vnext:
    inc     r14d
    jmp     .vi
.vdone:
    mov     eax, ebp
    add     rsp, 8
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbp
    pop     rbx
    ret

; -- sqw_apply_event: rdi = w, rsi = evt{cat,b,g,strand,i,m} --
sqw_apply_event:
    push    rbx
    mov     rbx, rdi                ; w
    mov     eax, [rsi]              ; cat
    cmp     eax, 0
    je      .pay
    cmp     eax, 1
    je      .syn
    cmp     eax, 2
    je      .ref
    jmp     .idx
.pay:
    mov     r10d, [rsi+4]           ; b
    mov     r11d, [rsi+8]           ; g
    mov     ecx, [rsi+12]           ; strand
    mov     r8d, [rsi+16]           ; i
    movzx   r9d, byte [rsi+20]      ; m
    push    rcx                     ; strand (div needs ecx)
    mov     eax, r8d
    xor     edx, edx
    mov     ecx, 152
    div     ecx                     ; edx = i%152
    mov     r8d, edx
    pop     rcx                     ; strand
    mov     esi, r10d
    mov     edx, r11d
    mov     rdi, rbx
    call    codon_ptr               ; rax = codon
    xor     byte [rax+r8], r9b
    pop     rbx
    ret
.syn:
    mov     r10d, [rsi+4]
    mov     r11d, [rsi+8]
    mov     ecx, [rsi+12]
    mov     r8d, [rsi+16]
    movzx   r9d, byte [rsi+20]
    push    rcx
    mov     eax, r8d
    xor     edx, edx
    mov     ecx, 8
    div     ecx                     ; edx = i%8
    mov     r8d, edx
    pop     rcx
    mov     esi, r10d
    mov     edx, r11d
    mov     rdi, rbx
    call    codon_ptr
    xor     byte [rax+152+r8], r9b  ; syn0/syn1 bytes
    pop     rbx
    ret
.ref:
    mov     eax, [rsi+4]            ; b
    shl     eax, 5
    add     eax, [rsi+8]            ; g -> idx
    shl     rax, 2                  ; *4
    lea     rdx, [rbx+SQW_RFB+rax]  ; &ref[b][g]
    mov     ecx, [rsi+16]
    and     ecx, 3                  ; i&3 (C bitwise, exact)
    movzx   eax, byte [rsi+20]      ; m
    xor     byte [rdx+rcx], al
    pop     rbx
    ret
.idx:
    mov     eax, [rsi+16]
    and     eax, SQW_IDX - 1        ; i&4095
    shl     rax, 4                  ; *16
    lea     rdx, [rbx+SQW_IDB+rax]  ; ent
    mov     eax, [rsi+8]            ; g
    and     eax, 15                 ; g%16 (C %16 on non-negative)
    movzx   ecx, byte [rsi+20]      ; m
    xor     byte [rdx+rax], cl
    pop     rbx
    ret

; -- cert_round: rdi=w, rsi=clean, rdx=stream, ecx=nev, r8d=forced, r9=acc --
; RNG via rng_main BSS (single global stream). acc offsets: cnt0..3 @0,
; det @32, rep @64, recog 96..120, tombs 128, tomb_refs 136, unres 144,
; cohf 152, rounds 160.
cert_round:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 8
    mov     rbx, rdi                ; w
    mov     r12, rdx                ; stream
    mov     r14d, ecx               ; nev
    mov     r13, r9                 ; acc
    mov     ebp, r8d                ; forced (rsi=clean intact for copy below)
    mov     ecx, SQW_QW
    rep     movsq                   ; *w = *clean (rdi=w, rsi=clean)
    ; occ_list of occupied codons
    xor     r10d, r10d              ; n_occ (no calls in build loop)
    xor     r11d, r11d              ; b
.ob:
    xor     r15d, r15d              ; g
.og:
    mov     eax, r11d
    shl     eax, 5
    add     eax, r15d               ; idx
    cmp     byte [rbx+OCC_OFF+rax], 0
    je      .ono
    mov     ecx, r11d
    shl     ecx, 8
    add     ecx, r15d               ; (b<<8)|g
    mov     [occ_list+r10*4], ecx
    inc     r10d
.ono:
    inc     r15d
    cmp     r15d, SQB_NR
    jne     .og
    inc     r11d
    cmp     r11d, SQB_NB
    jne     .ob
    mov     [t_nocc], r10d
    xor     r15d, r15d              ; e
.ev:
    cmp     r15d, r14d
    jae     .sweep_it
    mov     eax, ebp                ; forced
    cmp     eax, 0
    jge     .have_cat
    lea     rdi, [rng_main]
    call    rand01                  ; xmm0
    comisd  xmm0, [DBL_070]
    jae     .not_pay
    xor     eax, eax                ; PAY
    jmp     .have_cat
.not_pay:
    lea     rdi, [rng_main]
    call    rand01
    comisd  xmm0, [DBL_050]
    jae     .not_syn
    mov     eax, 1                  ; SYN
    jmp     .have_cat
.not_syn:
    lea     rdi, [rng_main]
    call    rand01
    comisd  xmm0, [DBL_067]
    jae     .is_idx
    mov     eax, 2                  ; REF
    jmp     .have_cat
.is_idx:
    mov     eax, 3                  ; IDX
.have_cat:
    imul    ecx, r15d, 24
    lea     rdi, [evtbuf+rcx]       ; evt[e] (rdi dead after stores below)
    mov     [rdi], eax              ; cat
    mov     r10d, eax               ; cat (r10 free: no calls until apply)
    inc     qword [r13+rax*8]       ; acc.cnt[cat]
    lea     rdi, [rng_main]         ; slot = occ_list[rand % n_occ]
    call    xoshiro
    xor     edx, edx
    mov     ecx, [t_nocc]
    div     ecx
    mov     eax, [occ_list+rdx*4]   ; slot
    mov     r10d, eax
    shr     r10d, 8                 ; b (r10 survives xoshiro calls: untouched)
    and     eax, 0xFF
    mov     r11d, eax               ; g (same)
    imul    ecx, r15d, 24
    lea     rdi, [evtbuf+rcx]
    mov     [rdi+4], r10d           ; b
    mov     [rdi+8], r11d           ; g
    lea     rdi, [rng_main]         ; strand = rand & 1
    call    xoshiro
    and     eax, 1
    imul    ecx, r15d, 24
    mov     [evtbuf+rcx+12], eax
    lea     rdi, [rng_main]         ; i = rand % 152
    call    xoshiro
    xor     edx, edx
    mov     ecx, 152
    div     ecx
    imul    ecx, r15d, 24
    mov     [evtbuf+rcx+16], edx
    lea     rdi, [rng_main]         ; m = 1 + rand % 255
    call    xoshiro
    xor     edx, edx
    mov     ecx, 255
    div     ecx
    inc     edx
    imul    ecx, r15d, 24
    mov     byte [evtbuf+rcx+20], dl
    imul    ecx, r15d, 24           ; apply
    lea     rsi, [evtbuf+rcx]
    mov     rdi, rbx
    call    sqw_apply_event
    inc     r15d
    jmp     .ev
.sweep_it:
    mov     rdi, rbx
    lea     rsi, [action]
    call    sweep                   ; rax = unresolved
    add     qword [r13+144], rax    ; acc.unresolved
    mov     rdi, rbx
    lea     rsi, [t_sumok]
    call    ref_audit               ; (result ignored here; scored per-event)
    xor     r15d, r15d              ; scoring e = 0
.score:
    cmp     r15d, r14d
    jae     .tomb
    imul    eax, r15d, 24
    lea     rsi, [evtbuf+rax]
    mov     ecx, [rsi]              ; cat
    mov     edx, [rsi+4]            ; b
    mov     r8d, [rsi+8]            ; g
    mov     r9d, [rsi+12]           ; strand
    mov     r10d, [rsi+16]          ; i
    mov     r11d, [rsi+20]          ; m (dword load; low byte used)
    mov     [t_evt], ecx
    mov     [t_evt+4], edx
    mov     [t_evt+8], r8d
    mov     [t_evt+12], r9d
    mov     [t_evt+16], r10d
    mov     [t_evt+20], r11d
    cmp     ecx, 0
    je      .sc_pay
    cmp     ecx, 1
    je      .sc_syn
    cmp     ecx, 2
    je      .sc_ref
    jmp     .sc_idx
.sc_pay:
    mov     eax, [t_evt+4]          ; idx = b*32+g
    shl     eax, 5
    add     eax, [t_evt+8]
    xor     ecx, ecx
    mov     cl, [action+rax]
    test    ecx, ecx
    jz      .no_d0
    inc     qword [r13+32]          ; det[0]
.no_d0:
    mov     esi, [t_evt+4]          ; codon(cell,b,g,strand)
    mov     edx, [t_evt+8]
    mov     ecx, [t_evt+12]
    mov     rdi, rbx
    call    codon_ptr               ; rax = codon
    cmp     dword [t_evt+12], 0
    jne     .dec1
    mov     rsi, rax
    lea     rdi, [decbuf]
    mov     ecx, SQB_PAY
    rep     movsb
    jmp     .payok
.dec1:
    lea     rdi, [decbuf]
    xor     ecx, ecx
.d1l:
    mov     dl, [rax+rcx]           ; dl not al (al would clobber rax pointer!)
    xor     dl, COMPLEMENT
    mov     [rdi+rcx], dl
    inc     ecx
    cmp     ecx, SQB_PAY
    jne     .d1l
.payok:
    mov     eax, [t_evt+4]
    shl     eax, 5
    add     eax, [t_evt+8]
    lea     rdx, [item_at]
    mov     esi, [rdx+rax*4]
    lea     rdi, [decbuf]
    call    pay_ok
    add     qword [r13+64], rax     ; rep[0]
    jmp     .sc_next
.sc_syn:
    mov     eax, [t_evt+4]
    shl     eax, 5
    add     eax, [t_evt+8]
    xor     ecx, ecx
    mov     cl, [action+rax]
    test    ecx, ecx
    jz      .no_d1
    inc     qword [r13+40]          ; det[1]
.no_d1:
    mov     esi, [t_evt+4]
    mov     edx, [t_evt+8]
    mov     ecx, [t_evt+12]
    mov     rdi, rbx
    call    codon_ptr
    mov     rdi, rax
    mov     esi, [t_evt+12]
    call    strand_ok
    add     qword [r13+72], rax     ; rep[1]
    jmp     .sc_next
.sc_ref:
    mov     eax, [t_evt+4]
    shl     eax, 5
    add     eax, [t_evt+8]
    lea     rdx, [rbx+SQW_RFB]
    mov     edi, [rdx+rax*4]
    call    ref_ok                  ; eax
    xor     ecx, ecx                ; det[2] += !ok
    test    eax, eax
    setz    cl
    add     qword [r13+48], rcx
    jmp     .sc_next
.sc_idx:
    inc     qword [r13+120]         ; idx_poison_total
    mov     rdi, rbx
    mov     rsi, r12                ; stream
    mov     edx, CERT_N
    call    verify_all_items
    cmp     rax, CERT_N
    jne     .sc_next
    inc     qword [r13+112]         ; idx_poison_ok
.sc_next:
    inc     r15d
    jmp     .score
.tomb:
    mov     rax, [rbx+TOMB_OFF]
    test    rax, rax
    jz      .cohere
    add     qword [r13+128], rax    ; tombs
    xor     r14d, r14d              ; b (nev dead)
.tb:
    xor     r15d, r15d              ; g
.tg:
    mov     eax, r14d
    shl     eax, 5
    add     eax, r15d               ; idx
    imul    rax, rax, 336           ; *2 codons *168 B
    lea     rdx, [rbx+rax]          ; c[b][g][0]
    cmp     dword [rdx+164], TOMB_MAGIC
    jne     .tn
    mov     eax, r14d               ; ref addr
    shl     eax, 5
    add     eax, r15d
    lea     rcx, [rbx+SQW_RFB]
    mov     edi, [rcx+rax*4]
    call    ref_ok
    test    eax, eax
    jz      .tn
    mov     eax, r14d               ; recompute (call clobbered regs)
    shl     eax, 5
    add     eax, r15d
    lea     rdx, [rbx+SQW_RFB]
    mov     eax, [rdx+rax*4]
    and     eax, 0xFFFF
    add     [r13+136], rax          ; tomb_refs += lo
.tn:
    inc     r15d
    cmp     r15d, SQB_NR
    jne     .tg
    inc     r14d
    cmp     r14d, SQB_NB
    jne     .tb
.cohere:
    mov     rdi, rbx
    mov     rsi, r12                ; stream
    mov     edx, CERT_N
    call    verify_all_items        ; rax = ok
    mov     ecx, CERT_N
    sub     ecx, eax
    add     [r13+152], rcx          ; coh_fail
    inc     qword [r13+160]         ; rounds
    add     rsp, 8
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbp
    pop     rbx
    ret

_start:
    mov     eax, [rsp]              ; argc
    cmp     eax, 1
    jbe     .def
    mov     rsi, [rsp+16]           ; argv[1]
    call    atoi
    jmp     .have
.def:
    mov     eax, 1500
.have:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r12d, eax               ; roundsA
    mov     eax, r12d
    xor     edx, edx
    mov     ecx, 3
    div     ecx
    mov     r13d, eax               ; roundsB
    lea     rdi, [rng_main]
    mov     rsi, 0xCE27
    call    seed_rng
    call    check_avx2
    mov     [use_avx2], al
    ; stream: 0..127 shuffled, then random 0..127 (50% duplication)
    xor     r15d, r15d
.sfill:
    cmp     r15d, 128
    jae     .fy
    mov     [stream+r15*4], r15d
    inc     r15d
    jmp     .sfill
.fy:
    mov     r15d, 127               ; Fisher-Yates i = U-1..1
.fyl:
    cmp     r15d, 1
    jb      .fy_done
    lea     rdi, [rng_main]
    call    rand_u32
    mov     ecx, r15d
    inc     ecx                     ; i+1
    xor     edx, edx
    div     ecx                     ; edx = j
    mov     eax, [stream+r15*4]     ; swap stream[i], stream[j]
    mov     ecx, [stream+rdx*4]
    mov     [stream+r15*4], ecx
    mov     [stream+rdx*4], eax
    dec     r15d
    jmp     .fyl
.fy_done:
    mov     r15d, 128
.sfill2:
    cmp     r15d, 256
    jae     .built
    lea     rdi, [rng_main]
    call    rand_u32
    xor     edx, edx
    mov     ecx, 128
    div     ecx
    mov     [stream+r15*4], edx
    inc     r15d
    jmp     .sfill2
.built:
    lea     rdi, [w]
    call    sqw_init
    xor     r15d, r15d              ; alloc i = 0..255
.al:
    cmp     r15d, 256
    jae     .al_done
    lea     rax, [stream]
    mov     edx, [rax+r15*4]        ; item
    lea     rdi, [w]
    mov     esi, r15d               ; id
    call    sqw_alloc
    inc     r15d
    jmp     .al
.al_done:
    lea     rsi, [w]                ; clean = w
    lea     rdi, [clean]
    mov     ecx, SQW_QW
    rep     movsq
    lea     rdi, [clean]            ; O1 recognition on clean fill
    lea     rsi, [stream]
    mov     edx, CERT_N
    call    verify_all_items
    mov     rbx, rax                ; recog_ok (survives: callees keep rbx)
    lea     rdi, [accA]             ; zero accs (168 B = 21 qw)
    xor     eax, eax
    mov     ecx, 21
    rep     stosq
    lea     rdi, [accB]
    mov     ecx, 21
    rep     stosq
    xor     r14d, r14d              ; Phase A
.phase_a:
    cmp     r14d, r12d
    jae     .phase_b
    mov     eax, r14d
    xor     edx, edx
    mov     ecx, 7
    div     ecx                     ; edx = r % 7
    xor     esi, esi                ; PAY
    cmp     edx, 3
    jb      .have_cat_a             ; r%7 < 3 -> PAY
    je      .syn_a                  ; == 3 -> SYN (consume flags NOW)
    cmp     edx, 4
    je      .ref_a                  ; == 4 -> REF
    mov     esi, 3                  ; else IDX
    jmp     .have_cat_a
.syn_a:
    mov     esi, 1
    jmp     .have_cat_a
.ref_a:
    mov     esi, 2
.have_cat_a:
    mov     r8d, esi                ; cat -> forced (BEFORE leas reuse rsi)
    lea     rdi, [w]
    lea     rsi, [clean]
    lea     rdx, [stream]
    mov     ecx, 1
    lea     r9, [accA]
    call    cert_round
    inc     r14d
    jmp     .phase_a
.phase_b:
    xor     r14d, r14d
.phase_b_loop:
    cmp     r14d, r13d
    jae     .emit_all
    lea     rdi, [w]
    lea     rsi, [clean]
    lea     rdx, [stream]
    mov     ecx, 12
    mov     r8d, -1
    lea     r9, [accB]
    call    cert_round
    inc     r14d
    jmp     .phase_b_loop
.emit_all:
    lea     rsi, [Q1A]
    mov     rdx, Q1A_LEN
    call    emit_str
    mov     rax, rbx                ; recog_ok
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, CERT_N
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, rbx
    mov     rdx, CERT_N
    call    ratio_fx
    call    emit_f6
    lea     rsi, [Q1B]
    mov     rdx, Q1B_LEN
    call    emit_str
    lea     rsi, [Q2A]
    mov     rdx, Q2A_LEN
    call    emit_str
    mov     rax, [accA+48]          ; A.det[2]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+16]          ; A.cnt[2]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+48]
    mov     rdx, [accA+16]
    call    ratio_fx
    call    emit_f6
    lea     rsi, [Q2B]
    mov     rdx, Q2B_LEN
    call    emit_str
    lea     rsi, [Q3A]
    mov     rdx, Q3A_LEN
    call    emit_str
    mov     rax, [accA+32]          ; det[0]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+0]           ; cnt[0]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+32]
    mov     rdx, [accA+0]
    call    ratio_fx
    call    emit_f6
    lea     rsi, [Q3B]
    mov     rdx, Q3B_LEN
    call    emit_str
    lea     rsi, [Q4A]
    mov     rdx, Q4A_LEN
    call    emit_str
    mov     rax, [accA+64]          ; rep[0]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+0]           ; cnt[0]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+64]
    mov     rdx, [accA+0]
    call    ratio_fx
    call    emit_f6
    lea     rsi, [Q4B]
    mov     rdx, Q4B_LEN
    call    emit_str
    lea     rsi, [Q5A]
    mov     rdx, Q5A_LEN
    call    emit_str
    mov     rax, [accA+40]          ; det[1]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+8]           ; cnt[1]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+40]
    mov     rdx, [accA+8]
    call    ratio_fx
    call    emit_f6
    lea     rsi, [Q5B]
    mov     rdx, Q5B_LEN
    call    emit_str
    lea     rsi, [Q6A]
    mov     rdx, Q6A_LEN
    call    emit_str
    mov     rax, [accA+72]          ; rep[1]
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+8]
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+72]
    mov     rdx, [accA+8]
    call    ratio_fx
    call    emit_f6
    lea     rsi, [Q6B]
    mov     rdx, Q6B_LEN
    call    emit_str
    lea     rsi, [Q7A]
    mov     rdx, Q7A_LEN
    call    emit_str
    mov     rax, [accA+144]         ; unresolved
    call    emit_u64
    lea     rsi, [Q7B]
    mov     rdx, Q7B_LEN
    call    emit_str
    lea     rsi, [Q8A]
    mov     rdx, Q8A_LEN
    call    emit_str
    mov     rax, [accA+128]         ; tombs
    call    emit_u64
    lea     rsi, [Q8B]
    mov     rdx, Q8B_LEN
    call    emit_str
    lea     rsi, [Q9A]
    mov     rdx, Q9A_LEN
    call    emit_str
    mov     rax, [accA+112]         ; idx_poison_ok
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+120]         ; idx_poison_total
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+112]
    mov     rdx, [accA+120]
    call    ratio_fx
    call    emit_f6
    lea     rsi, [Q9B]
    mov     rdx, Q9B_LEN
    call    emit_str
    lea     rsi, [Q10A]
    mov     rdx, Q10A_LEN
    call    emit_str
    mov     rax, [accB+32]
    add     rax, [accB+40]          ; det01
    mov     r14, rax                ; (phases done: r14/r15 free)
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accB+0]
    add     rax, [accB+8]           ; cnt01
    mov     r15, rax
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, r14
    mov     rdx, r15
    call    ratio_fx
    call    emit_f6
    lea     rsi, [Q10B]
    mov     rdx, Q10B_LEN
    call    emit_str
    lea     rsi, [Q11A]
    mov     rdx, Q11A_LEN
    call    emit_str
    mov     rax, [accB+64]
    add     rax, [accB+72]          ; rep01
    mov     r14, rax
    call    emit_u64
    lea     rsi, [QSL]
    mov     rdx, 1
    call    emit_str
    mov     rax, r15                ; cnt01 (r15 intact: emits keep it)
    call    emit_u64
    lea     rsi, [QEQ]
    mov     rdx, 3
    call    emit_str
    mov     rax, r14
    mov     rdx, r15
    call    ratio_fx
    call    emit_f6
    lea     rsi, [Q11B]
    mov     rdx, Q11B_LEN
    call    emit_str
    lea     rsi, [Q12A]
    mov     rdx, Q12A_LEN
    call    emit_str
    mov     rax, [accB+128]         ; tombs
    call    emit_u64
    lea     rsi, [Q12B]
    mov     rdx, Q12B_LEN
    call    emit_str
    mov     rax, [accB+136]         ; tomb_refs
    call    emit_u64
    lea     rsi, [Q12C]
    mov     rdx, Q12C_LEN
    call    emit_str
    mov     rax, [accB+136]
    mov     rdx, [accB+128]
    call    ratio_fx
    call    emit_f2
    lea     rsi, [Q12D]
    mov     rdx, Q12D_LEN
    call    emit_str
    mov     rax, [accB+152]         ; coh_fail
    call    emit_u64
    lea     rsi, [Q12E]
    mov     rdx, Q12E_LEN
    call    emit_str
    mov     rax, [accB+144]         ; unresolved
    call    emit_u64
    lea     rsi, [Q12F]
    mov     rdx, Q12F_LEN
    call    emit_str
    mov     eax, 1                  ; sys_write(1, outbuf, outcur)
    mov     edi, 1
    lea     rsi, [outbuf]
    mov     rdx, [ocur]
    syscall
    mov     eax, 60                 ; sys_exit(0)
    xor     edi, edi
    syscall
.efail:
    lea     rsi, [LEF]
    mov     rdx, LEF_LEN
    call    emit_str
    mov     eax, 1
    mov     edi, 1
    lea     rsi, [outbuf]
    mov     rdx, [ocur]
    syscall
    mov     eax, 60
    mov     edi, 1
    syscall
.fail:
    lea     rsi, [LFF]
    mov     rdx, LFF_LEN
    call    emit_str
    mov     eax, 1
    mov     edi, 1
    lea     rsi, [outbuf]
    mov     rdx, [ocur]
    syscall
    mov     eax, 60
    mov     edi, 1
    syscall

segment readable

M53 dq 0x3CA0000000000000          ; 2^-53
DBL_10  dq 10.0
DBL_0   dq 0.0
DBL_070 dq 0.70
DBL_050 dq 0.50
DBL_067 dq 0.67
Q1A db 'SQWOR O1_recognition  '
Q1A_LEN = $ - Q1A
Q1B db '  expect=1.000000 counting (memoization exactness)', 0x0A
Q1B_LEN = $ - Q1B
Q2A db 'SQWOR O2_refpair_det  '
Q2A_LEN = $ - Q2A
Q2B db '  expect=1.000000 counting [A]', 0x0A
Q2B_LEN = $ - Q2B
Q3A db 'SQWOR O3_payload_det  '
Q3A_LEN = $ - Q3A
Q3B db '  expect=1.000000 counting [A]', 0x0A
Q3B_LEN = $ - Q3B
Q4A db 'SQWOR O3_payload_rep  '
Q4A_LEN = $ - Q4A
Q4B db '  expect>=0.990 measurement [A]', 0x0A
Q4B_LEN = $ - Q4B
Q5A db 'SQWOR O4_syndrome_det '
Q5A_LEN = $ - Q5A
Q5B db '  expect=1.000000 counting [A]', 0x0A
Q5B_LEN = $ - Q5B
Q6A db 'SQWOR O4_syndrome_rep '
Q6A_LEN = $ - Q6A
Q6B db '  expect=1.000000 measurement [A]', 0x0A
Q6B_LEN = $ - Q6B
Q7A db 'SQWOR O5_closure      '
Q7A_LEN = $ - Q7A
Q7B db ' unresolved [A]  expect=0', 0x0A
Q7B_LEN = $ - Q7B
Q8A db 'SQWOR O6_apoptosis    '
Q8A_LEN = $ - Q8A
Q8B db ' [A]  expect=0 isolated', 0x0A
Q8B_LEN = $ - Q8B
Q9A db 'SQWOR O7_idx_failsafe '
Q9A_LEN = $ - Q9A
Q9B db '  expect=1.000000 (poisoned cache never serves wrong content) [A isolated]', 0x0A
Q9B_LEN = $ - Q9B
Q10A db 'SQWOR auxB_det        '
Q10A_LEN = $ - Q10A
Q10B db '  poisson tail (content classes)', 0x0A
Q10B_LEN = $ - Q10B
Q11A db 'SQWOR auxB_rep        '
Q11A_LEN = $ - Q11A
Q11B db '  poisson tail', 0x0A
Q11B_LEN = $ - Q11B
Q12A db 'SQWOR auxB_tombs      '
Q12A_LEN = $ - Q12A
Q12B db '  tomb_refs '
Q12B_LEN = $ - Q12B
Q12C db ' (amplification: '
Q12C_LEN = $ - Q12C
Q12D db ' logical items lost per tombstone)  auxB_coh_fail '
Q12D_LEN = $ - Q12D
Q12E db '  auxB_unresolved '
Q12E_LEN = $ - Q12E
Q12F db 0x0A
Q12F_LEN = $ - Q12F
QSL db '/'
QEQ db ' = '
LEF db 'sqw encoder refused', 0x0A
LEF_LEN = $ - LEF
LFF db 'sqw fatal', 0x0A
LFF_LEN = $ - LFF

segment readable writeable

w         rb SQW_SZ
clean     rb SQW_SZ
stream    rd CERT_N
sqw_item_slot_b rd 1024          ; SQB_CAPACITY*4
sqw_item_slot_g rd 1024
evtbuf    rd 384                  ; 64 x 24 B events
occ_list  rd 256                  ; SQB_CAPACITY
action    rb 256
accA      rq 21                   ; 168 B
accB      rq 21
rng_main  rb 32
decbuf    rb SQB_PAY
hstmp     rb 16
tmp_s0    rd 1
tmp_s1    rd 1
item_at   rd 256
use_avx2  rb 1
t_sumok   rd 1
t_nocc    rd 1
t_evt     rd 6                    ; evt copy (6 dwords)
numbuf    rb 32
outbuf    rb 8192
ocur      rq 1
fdigits   rb 8

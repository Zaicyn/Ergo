; SQ2B certification driver in flat assembler (FASM 1.73.x, x86-64 Linux).
; Faithful port of benchmark/sq2b_cert.c + squaragon_v2_bio.h + the RNG
; from benchmark/common.h. Goal: byte-identical stdout to sq2b_cert.
;
; Internal ABI: args in rdi,rsi,rdx,rcx,r8,r9 (SysV-like), result in
; rax (xmm0 for doubles). rbx,rbp,r12-r15 are callee-saved everywhere.
; codon_ptr clobbers rax only. No libc: BSS arena, write(2)/exit(2).
;
; Layout (struct sizes derived from the C headers, behavior-matched):
;   codon = 168 B : g[152] @0, syn0 @152, syn1 @156, age @160, tomb @164
;   cell  = c[8][32][2] @0 (86016), occ[256] @86016, head[8] @86272,
;           total @86304, retries @86312, tombstones @86320, slippage @86328
; acc   = cnt[3], det[3], rep[3], tombs, slip, unres, retr, cohf, rounds
;         (9 + 1 qwords @ 8-byte strides, 120 B)
; Assemble: fasm sq2b.asm sq2b   (optional rounds arg, default 1500)

format ELF64 executable 3
entry _start


segment readable executable
include '../sqb_cell.inc'   ; shared cell (code + consts + LUTs)

segment readable executable
include '../rng.inc'        ; shared xoshiro** (single source)
include '../emit.inc'       ; shared emit (single source)
apply_event:
    push    rbx
    mov     ebx, [rsi]              ; cat (callee-saved across codon_ptr)
    mov     r8d, [rsi+16]           ; i
    mov     r9d, [rsi+20]           ; m
    mov     ecx, [rsi+12]           ; strand
    mov     edx, [rsi+8]            ; g
    mov     esi, [rsi+4]            ; b (last use of evt pointer)
    call    codon_ptr               ; rax = codon (clobbers rax only)
    cmp     ebx, 0
    je      .pay
    cmp     ebx, 1
    je      .synm
    lea     rdx, [rax+160]          ; META: age/tomb bytes
    jmp     .xorm
.synm:
    lea     rdx, [rax+152]          ; SYN: syn0/syn1 bytes
    jmp     .xorm
.pay:
    lea     rdx, [rax+r8]           ; PAY: g[i]
    xor     byte [rdx], r9b
    pop     rbx
    ret
.xorm:
    mov     ecx, r8d
    and     ecx, 7
    xor     byte [rdx+rcx], r9b
    pop     rbx
    ret

; -- cert_round: rdi = cell, rsi = clean, rdx = rng, ecx = nev, --
;               r8d = forced_cat, r9 = acc → (acc updated) --
; sq2b_cert.c:35. rbx=cell, rbp=clean, r12=rng, r13=acc, r14d=nev,
; r15d=e. forced spilled to frame. events in evtbuf (64 x 24 B).
cert_round:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 8
    mov     [rsp], r8d              ; forced spill
    mov     rbx, rdi
    mov     rbp, rsi
    mov     r12, rdx
    mov     r13, r9
    mov     r14d, ecx
    ; *cell = *clean
    mov     rcx, CELL_SZ/8
    rep     movsq                   ; rdi=cell dst, rsi=clean src
    xor     r15d, r15d              ; e
.ev_loop:
    cmp     r15d, r14d
    jae     .sweep_it
    imul    eax, r15d, 24
    lea     rbp, [evtbuf+rax]       ; evt[e] (clean no longer needed)
    mov     eax, [rsp]              ; forced
    cmp     eax, 0
    jge     .have_cat
    mov     rdi, r12
    call    rand01                  ; xmm0
    comisd  xmm0, [DBL_085]
    jae     .not_pay
    xor     eax, eax                ; PAY
    jmp     .have_cat
.not_pay:
    mov     rdi, r12
    call    rand01
    comisd  xmm0, [DBL_060]
    jae     .is_meta
    mov     eax, 1                  ; SYN
    jmp     .have_cat
.is_meta:
    mov     eax, 2                  ; META
.have_cat:
    mov     [rbp], eax              ; evt.cat
    inc     qword [r13+rax*8]       ; acc.cnt[cat]++
    mov     rdi, r12
    call    xoshiro_ss
    xor     edx, edx
    mov     ecx, SQB_NB
    div     ecx
    mov     [rbp+4], edx            ; b
    mov     rdi, r12
    call    xoshiro_ss
    xor     edx, edx
    mov     ecx, SQB_NR
    div     ecx
    mov     [rbp+8], edx            ; g
    mov     rdi, r12
    call    xoshiro_ss
    and     eax, 1
    mov     [rbp+12], eax           ; strand
    mov     rdi, r12
    call    xoshiro_ss
    xor     edx, edx
    mov     ecx, SQB_PAY
    div     ecx
    mov     [rbp+16], edx           ; i
    mov     rdi, r12
    call    xoshiro_ss
    xor     edx, edx
    mov     ecx, 255
    div     ecx
    inc     edx
    mov     [rbp+20], edx           ; m = 1 + rand%255
    mov     rdi, rbx
    mov     rsi, rbp
    call    apply_event
    inc     r15d
    jmp     .ev_loop
.sweep_it:
    mov     rdi, rbx
    lea     rsi, [action]
    call    sweep                   ; rax = unresolved
    add     qword [r13+88], rax
    mov     rax, [rbx+TOMB_OFF]
    add     qword [r13+72], rax     ; tombs
    mov     rax, [rbx+SLIP_OFF]
    add     qword [r13+80], rax     ; slippage
    mov     rax, [rbx+RETR_OFF]
    add     qword [r13+96], rax     ; retries
    xor     r15d, r15d              ; scoring loop e = 0
.score:
    cmp     r15d, r14d
    jae     .cohere
    imul    eax, r15d, 24
    lea     rbp, [evtbuf+rax]       ; evt
    mov     eax, [rbp]              ; cat
    mov     ecx, [rbp+4]            ; b
    mov     edx, [rbp+8]            ; g
    mov     r10d, ecx
    shl     r10d, 5
    add     r10d, edx               ; idx
    movzx   r11d, byte [action+r10] ; act
    cmp     eax, 0
    je      .sc_pay
    cmp     eax, 1
    je      .sc_syn
    jmp     .sc_next                ; META scores nothing
.sc_pay:
    test    r11b, r11b
    jz      .no_det0
    inc     qword [r13+24]          ; det[0]
.no_det0:
    mov     rdi, rbx
    mov     esi, [rbp+4]
    mov     edx, [rbp+8]
    mov     ecx, [rbp+12]
    call    codon_ptr               ; rax = codon (ecx = strand kept)
    test    ecx, ecx
    jnz     .dec1
    mov     rsi, rax
    lea     rdi, [decbuf]
    mov     ecx, SQB_PAY
    rep     movsb
    jmp     .payok
.dec1:
    lea     rdi, [decbuf]
    xor     ecx, ecx
.d1l:
    mov     dl, [rax+rcx]           ; NOTE: dl, not al — al would clobber
    xor     dl, COMPLEMENT          ; the low byte of the rax pointer itself
    mov     [rdi+rcx], dl
    inc     rcx
    cmp     ecx, SQB_PAY
    jne     .d1l
.payok:
    lea     rdi, [decbuf]
    mov     ecx, [rbp+4]
    shl     ecx, 5
    add     ecx, [rbp+8]
    mov     esi, [item_at+rcx*4]
    call    pay_ok
    add     qword [r13+48], rax     ; rep[0]
    jmp     .sc_next
.sc_syn:
    test    r11b, r11b
    jz      .no_det1
    inc     qword [r13+32]          ; det[1]
.no_det1:
    mov     rdi, rbx
    mov     esi, [rbp+4]
    mov     edx, [rbp+8]
    mov     ecx, [rbp+12]
    call    codon_ptr
    mov     rdi, rax
    mov     esi, [rbp+12]
    call    strand_ok
    add     qword [r13+56], rax     ; rep[1]
.sc_next:
    inc     r15d
    jmp     .score
.cohere:
    xor     r14d, r14d              ; b (nev no longer needed)
    ; cohere: fused single-pass check (no transcribe/decbuf/calls).
    ; Constants loaded once AFTER vzeroupper (upper halves are live data!
    ; vzeroupper after a load wipes them -> pitfall #18). Per-slot base via
    ; m32 broadcast (no SSE movd -> no transition penalty in the loop).
    vzeroupper
    vmovdqu ymm5, yword [POK91]
    vmovdqu ymm6, yword [POKA5]
    vmovdqu ymm8, yword [POK08]
    vmovdqu ymm9, yword [POKFF]
.cb_loop:
    xor     r15d, r15d              ; g
.cg_loop:
    mov     eax, r14d
    shl     eax, 5
    add     eax, r15d               ; idx
    cmp     byte [rbx+OCC_OFF+rax], 0
    je      .cnext
    lea     ecx, [eax*2]            ; slot0 = idx*2+0
    imul    rcx, rcx, CODON_SZ
    lea     rsi, [rbx+rcx]          ; c0 (codon_ptr inline)
    cmp     dword [rsi+164], TOMB_MAGIC
    je      .cohfail
    mov     edi, [item_at+rax*4]
    imul    edi, edi, 17
    mov     [cohbase], edi
    vpbroadcastd ymm4, dword [cohbase]
    vmovdqu ymm7, yword [POK07]
    mov     ecx, 19
.ckloop:
    vmovdqa ymm0, ymm7
    vpmulld ymm0, ymm0, ymm5
    vpaddd  ymm0, ymm0, ymm4
    vpxor   ymm0, ymm0, ymm6
    vpand   ymm0, ymm0, ymm9
    vpmovzxbd ymm1, qword [rsi]
    vpcmpeqd ymm1, ymm1, ymm0
    vpmovmskb eax, ymm1
    cmp     eax, -1
    jne     .cohfail
    add     rsi, 8
    vpaddd  ymm7, ymm7, ymm8
    dec     ecx
    jnz     .ckloop
    jmp     .cnext
.cohfail:
    inc     qword [r13+104]         ; coh_fail
.cnext:
    inc     r15d
    cmp     r15d, SQB_NR
    jne     .cg_loop
    inc     r14d
    cmp     r14d, SQB_NB
    jne     .cb_loop
    vzeroupper                      ; hygiene: cohere leaves upper ymm live
    inc     qword [r13+112]         ; rounds
    add     rsp, 8
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbp
    pop     rbx
    ret

; -- blind_pass: rdi = clean, rsi = &crd, rdx = &crt, rcx = &cfb --
; sq2b_cert.c:96. 2000 trials, own RNG seeded 0xB11D.
; Frame (sub 24 after 6 pushes = aligned): b,g,i,m dwords @ [rsp..+12].
blind_pass:
    push    rbx
    push    rbp
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 24
    mov     rbx, rdi                ; clean
    mov     r12, rsi                ; &crd
    mov     r13, rdx                ; &crt
    mov     r14, rcx                ; &cfb
    lea     rdi, [rng_blind]
    mov     rsi, 0xB11D
    call    seed_rng
    xor     r15d, r15d              ; t
.trial:
    cmp     r15d, 2000
    jae     .done
    mov     rsi, rbx                ; copy clean -> tmpcell
    lea     rdi, [tmpcell]
    mov     ecx, CELL_SZ
    rep     movsb
    lea     rdi, [rng_blind]        ; b = rand % 8
    call    xoshiro_ss
    xor     edx, edx
    mov     ecx, SQB_NB
    div     ecx
    mov     [rsp], edx
    lea     rdi, [rng_blind]        ; g = rand % 32
    call    xoshiro_ss
    xor     edx, edx
    mov     ecx, SQB_NR
    div     ecx
    mov     [rsp+4], edx
    lea     rdi, [rng_blind]        ; i = rand % 152
    call    xoshiro_ss
    xor     edx, edx
    mov     ecx, SQB_PAY
    div     ecx
    mov     [rsp+8], edx
    lea     rdi, [rng_blind]        ; m = 1 + rand % 255
    call    xoshiro_ss
    xor     edx, edx
    mov     ecx, 255
    div     ecx
    inc     edx
    mov     [rsp+12], edx
    ; (a) random coordinated dual-strand hit
    lea     rdi, [tmpcell]
    mov     esi, [rsp]
    mov     edx, [rsp+4]
    xor     ecx, ecx
    call    codon_ptr
    mov     r8d, [rsp+8]
    mov     r9d, [rsp+12]
    xor     byte [rax+r8], r9b
    lea     rdi, [tmpcell]
    mov     esi, [rsp]
    mov     edx, [rsp+4]
    mov     ecx, 1
    call    codon_ptr
    xor     byte [rax+r8], r9b
    lea     rdi, [tmpcell]
    xor     esi, esi
    call    sweep
    lea     rdi, [tmpcell]
    mov     esi, [rsp]
    mov     edx, [rsp+4]
    xor     ecx, ecx
    call    codon_ptr
    cmp     dword [rax+164], TOMB_MAGIC
    jne     .part_b
    inc     qword [r12]             ; crd
    inc     qword [r13]             ; crt
.part_b:
    ; (b) crafted fully-consistent hit
    mov     rsi, rbx
    lea     rdi, [tmpcell]
    mov     ecx, CELL_SZ
    rep     movsb
    lea     rdi, [tmpcell]
    mov     esi, [rsp]
    mov     edx, [rsp+4]
    xor     ecx, ecx
    call    codon_ptr
    mov     rbp, rax                ; c0
    mov     r8d, [rsp+8]
    mov     r9d, [rsp+12]
    xor     byte [rax+r8], r9b
    lea     rdi, [tmpcell]
    mov     esi, [rsp]
    mov     edx, [rsp+4]
    mov     ecx, 1
    call    codon_ptr               ; c1
    xor     byte [rax+r8], r9b
    mov     rsi, rbp                ; dec = memcpy(c0.g)
    lea     rdi, [decbuf]
    mov     ecx, SQB_PAY
    rep     movsb
    lea     rdi, [decbuf]
    lea     rsi, [tmp_s0]
    lea     rdx, [tmp_s1]
    call    syn
    mov     eax, [tmp_s0]
    mov     [rbp+152], eax
    mov     eax, [tmp_s1]
    mov     [rbp+156], eax
    lea     rdi, [tmpcell]
    mov     esi, [rsp]
    mov     edx, [rsp+4]
    mov     ecx, 1
    call    codon_ptr               ; c1 again
    mov     ecx, [tmp_s0]
    mov     [rax+152], ecx
    mov     ecx, [tmp_s1]
    mov     [rax+156], ecx
    lea     rdi, [tmpcell]
    xor     esi, esi
    call    sweep                   ; rax = unresolved
    test    rax, rax
    jnz     .next_trial
    lea     rdi, [tmpcell]
    mov     esi, [rsp]
    mov     edx, [rsp+4]
    xor     ecx, ecx
    call    codon_ptr
    cmp     dword [rax+164], TOMB_MAGIC
    je      .next_trial
    inc     qword [r14]             ; cfb
.next_trial:
    inc     r15d
    jmp     .trial
.done:
    add     rsp, 24
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
    jbe     .default_rounds
    mov     rsi, [rsp+16]           ; argv[1]
    call    atoi
    jmp     .have_rounds
.default_rounds:
    mov     eax, 1500
.have_rounds:
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
    lea     rdi, [cell]             ; sqb_init: memset 0
    xor     eax, eax
    mov     ecx, CELL_SZ/8
    rep     stosq
    xor     ebx, ebx                ; i = 0..255: alloc(i, i)
.alloc_loop:
    cmp     ebx, 256
    jae     .alloc_done
    lea     rdi, [cell]
    mov     esi, ebx
    mov     edx, ebx
    xor     ecx, ecx
    xor     r8d, r8d
    call    alloc_slot
    inc     ebx
    jmp     .alloc_loop
.alloc_done:
    lea     rsi, [cell]             ; clean = cell
    lea     rdi, [clean]
    mov     ecx, CELL_SZ/8
    rep     movsq
    lea     rdi, [accA]             ; zero accs
    xor     eax, eax
    mov     ecx, 15
    rep     stosq
    lea     rdi, [accB]
    mov     ecx, 15
    rep     stosq
    xor     r14d, r14d              ; Phase A
.phase_a:
    cmp     r14d, r12d
    jae     .phase_b
    mov     eax, r14d
    xor     edx, edx
    mov     ecx, 5
    div     ecx                     ; edx = r % 5
    xor     esi, esi                ; PAY
    cmp     edx, 3
    jb      .have_cat_a
    mov     esi, 1                  ; SYN
    je      .have_cat_a
    mov     esi, 2                  ; META
.have_cat_a:
    mov     r8d, esi                ; forced cat (before rsi is reused)
    lea     rdi, [cell]
    lea     rsi, [clean]
    lea     rdx, [rng_main]
    mov     ecx, 1
    lea     r9, [accA]
    call    cert_round
    inc     r14d
    jmp     .phase_a
.phase_b:
    xor     r14d, r14d
.phase_b_loop:
    cmp     r14d, r13d
    jae     .blind
    lea     rdi, [cell]
    lea     rsi, [clean]
    lea     rdx, [rng_main]
    mov     ecx, 12
    mov     r8d, -1
    lea     r9, [accB]
    call    cert_round
    inc     r14d
    jmp     .phase_b_loop
.blind:
    lea     rdi, [clean]
    lea     rsi, [crd]
    lea     rdx, [crt]
    lea     rcx, [cfb]
    call    blind_pass
    ; emit the 12 oracle lines
    lea     rsi, [P1A]
    mov     rdx, P1A_LEN
    call    emit_str
    mov     rax, [accA+24]
    call    emit_u64
    lea     rsi, [SLASH]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+0]
    call    emit_u64
    lea     rsi, [EQSTR]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+24]
    mov     rdx, [accA+0]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [P1B]
    mov     rdx, P1B_LEN
    call    emit_str
    lea     rsi, [P2A]
    mov     rdx, P2A_LEN
    call    emit_str
    mov     rax, [accA+48]
    call    emit_u64
    lea     rsi, [SLASH]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+0]
    call    emit_u64
    lea     rsi, [EQSTR]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+48]
    mov     rdx, [accA+0]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [P2B]
    mov     rdx, P2B_LEN
    call    emit_str
    lea     rsi, [P3A]
    mov     rdx, P3A_LEN
    call    emit_str
    mov     rax, [accA+32]
    call    emit_u64
    lea     rsi, [SLASH]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+8]
    call    emit_u64
    lea     rsi, [EQSTR]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+32]
    mov     rdx, [accA+8]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [P3B]
    mov     rdx, P3B_LEN
    call    emit_str
    lea     rsi, [P4A]
    mov     rdx, P4A_LEN
    call    emit_str
    mov     rax, [accA+56]
    call    emit_u64
    lea     rsi, [SLASH]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accA+8]
    call    emit_u64
    lea     rsi, [EQSTR]
    mov     rdx, 3
    call    emit_str
    mov     rax, [accA+56]
    mov     rdx, [accA+8]
    call    ratio_f6
    call    emit_f6
    lea     rsi, [P4B]
    mov     rdx, P4B_LEN
    call    emit_str
    lea     rsi, [P5A]
    mov     rdx, P5A_LEN
    call    emit_str
    mov     rax, [accA+88]
    call    emit_u64
    lea     rsi, [P5B]
    mov     rdx, P5B_LEN
    call    emit_str
    lea     rsi, [P6A]
    mov     rdx, P6A_LEN
    call    emit_str
    mov     rax, [accA+72]
    call    emit_u64
    lea     rsi, [P6B]
    mov     rdx, P6B_LEN
    call    emit_str
    lea     rsi, [P7A]
    mov     rdx, P7A_LEN
    call    emit_str
    mov     rax, [crd]
    call    emit_u64
    lea     rsi, [SLASH]
    mov     rdx, 1
    call    emit_str
    mov     rax, 2000
    call    emit_u64
    lea     rsi, [P7B]
    mov     rdx, P7B_LEN
    call    emit_str
    lea     rsi, [P8A]
    mov     rdx, P8A_LEN
    call    emit_str
    mov     rax, [cfb]
    call    emit_u64
    lea     rsi, [SLASH]
    mov     rdx, 1
    call    emit_str
    mov     rax, 2000
    call    emit_u64
    lea     rsi, [P8B]
    mov     rdx, P8B_LEN
    call    emit_str
    lea     rsi, [P9A]
    mov     rdx, P9A_LEN
    call    emit_str
    mov     rax, [accB+24]
    add     rax, [accB+32]
    mov     r14, rax
    call    emit_u64
    lea     rsi, [SLASH]
    mov     rdx, 1
    call    emit_str
    mov     rax, [accB+0]
    add     rax, [accB+8]
    mov     r15, rax
    call    emit_u64
    lea     rsi, [EQSTR]
    mov     rdx, 3
    call    emit_str
    mov     rax, r14
    mov     rdx, r15
    call    ratio_f6
    call    emit_f6
    lea     rsi, [P9B]
    mov     rdx, P9B_LEN
    call    emit_str
    lea     rsi, [P10A]
    mov     rdx, P10A_LEN
    call    emit_str
    mov     rax, [accB+48]
    add     rax, [accB+56]
    mov     r14, rax
    call    emit_u64
    lea     rsi, [SLASH]
    mov     rdx, 1
    call    emit_str
    mov     rax, r15
    call    emit_u64
    lea     rsi, [EQSTR]
    mov     rdx, 3
    call    emit_str
    mov     rax, r14
    mov     rdx, r15
    call    ratio_f6
    call    emit_f6
    lea     rsi, [P10B]
    mov     rdx, P10B_LEN
    call    emit_str
    lea     rsi, [P11A]
    mov     rdx, P11A_LEN
    call    emit_str
    mov     rax, [accB+72]
    call    emit_u64
    lea     rsi, [P11B]
    mov     rdx, P11B_LEN
    call    emit_str
    mov     rax, [accB+104]
    call    emit_u64
    lea     rsi, [P11C]
    mov     rdx, P11C_LEN
    call    emit_str
    mov     rax, [accB+80]
    call    emit_u64
    lea     rsi, [P11D]
    mov     rdx, P11D_LEN
    call    emit_str
    mov     rax, [accB+88]
    call    emit_u64
    lea     rsi, [P11E]
    mov     rdx, P11E_LEN
    call    emit_str
    lea     rsi, [P12A]
    mov     rdx, P12A_LEN
    call    emit_str
    mov     rax, [accA+96]
    add     rax, [accB+96]
    call    emit_u64
    lea     rsi, [P12B]
    mov     rdx, P12B_LEN
    call    emit_str
    lea     rsi, [P13A]
    mov     rdx, P13A_LEN
    call    emit_str
    mov     rax, [accA+104]
    call    emit_u64
    lea     rsi, [P13B]
    mov     rdx, P13B_LEN
    call    emit_str
    mov     eax, 1                  ; sys_write(1, outbuf, outcur)
    mov     edi, 1
    lea     rsi, [outbuf]
    mov     rdx, [outcur]
    syscall
    mov     eax, 60                 ; sys_exit(0)
    xor     edi, edi
    syscall

segment readable

DBL_10  dq 10.0
DBL_085 dq 0.85
DBL_060 dq 0.60

; line literals copied verbatim from sq2b_cert.c printf formats
P1A db 'SQ2BOR O1_payload_det   '
P1A_LEN = $ - P1A
P1B db '  expect=1.000000 counting [A]', 0x0A
P1B_LEN = $ - P1B
P2A db 'SQ2BOR O2_payload_rep   '
P2A_LEN = $ - P2A
P2B db '  expect>=0.990 measurement [A]', 0x0A
P2B_LEN = $ - P2B
P3A db 'SQ2BOR O3_syndrome_det  '
P3A_LEN = $ - P3A
P3B db '  expect=1.000000 counting [A]', 0x0A
P3B_LEN = $ - P3B
P4A db 'SQ2BOR O4_syndrome_rep  '
P4A_LEN = $ - P4A
P4B db '  expect=1.000000 measurement [A]', 0x0A
P4B_LEN = $ - P4B
P5A db 'SQ2BOR O5_closure       '
P5A_LEN = $ - P5A
P5B db ' unresolved [A]  expect=0', 0x0A
P5B_LEN = $ - P5B
P6A db 'SQ2BOR O6_apoptosis     '
P6A_LEN = $ - P6A
P6B db ' [A]  expect=0 isolated', 0x0A
P6B_LEN = $ - P6B
P7A db 'SQ2BOR O7_blind_random  '
P7A_LEN = $ - P7A
P7B db ' detected+tombstoned (never silent)  expect=1.000000', 0x0A
P7B_LEN = $ - P7B
P8A db 'SQ2BOR O8_blind_crafted '
P8A_LEN = $ - P8A
P8B db ' blind  expect=all-blind documented-exclusion', 0x0A
P8B_LEN = $ - P8B
P9A db 'SQ2BOR auxB_det         '
P9A_LEN = $ - P9A
P9B db '  poisson tail', 0x0A
P9B_LEN = $ - P9B
P10A db 'SQ2BOR auxB_rep         '
P10A_LEN = $ - P10A
P10B db '  poisson tail', 0x0A
P10B_LEN = $ - P10B
P11A db 'SQ2BOR auxB_tombs       '
P11A_LEN = $ - P11A
P11B db '  auxB_coh_fail '
P11B_LEN = $ - P11B
P11C db '  auxB_slippage '
P11C_LEN = $ - P11C
P11D db '  auxB_unresolved '
P11D_LEN = $ - P11D
P11E db 0x0A
P11E_LEN = $ - P11E
P12A db 'SQ2BOR aux_proofread_retries '
P12A_LEN = $ - P12A
P12B db ' (GTP bill, should be 0 absent injection)', 0x0A
P12B_LEN = $ - P12B
P13A db 'SQ2BOR O9_main_cohere  '
P13A_LEN = $ - P13A
P13B db '  expect=0 audit [A]', 0x0A
P13B_LEN = $ - P13B
SLASH db '/'
EQSTR db ' = '

segment readable writeable

cell    rb CELL_SZ
clean   rb CELL_SZ
tmpcell rb CELL_SZ
item_at rd SQB_NB * SQB_NR
action  rb SQB_NB * SQB_NR
evtbuf  rb 64 * 24
accA    rq 15                     ; cnt[3] det[3] rep[3] tombs slip unres retr cohf rounds
accB    rq 15
rng_main rb 32
rng_blind rb 32
decbuf  rb SQB_PAY
cohbase rd 1                        ; fused-cohere per-slot base temp
hstmp   rb 16
tmp_s0  rd 1
tmp_s1  rd 1
numbuf  rb 32
fdigits rb 8
crd     rq 1
crt     rq 1
cfb     rq 1
outbuf  rb 4096
outcur  rq 1
tsbuf   rq 2
use_avx2 rb 1

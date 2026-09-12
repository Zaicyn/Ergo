; Phase 2: action-log encoding shootout on REAL sweep data
; (2000 rounds x 256 ternary outcomes from sq2b cert runs).
; Compares: raw bytes vs 2-bit pack vs trit pack (pad-noted) vs byte RLE.
; Sizes on real data + best-of-3 encode/decode speeds + round-trip verify.
; Shared bulk codec comes from trit_codec.inc (single source of truth).
; Assemble (from this directory): fasm phase2.asm phase2
; Needs /tmp/opencode/sq2b_actions.bin (see min/Fasm/Sq2B capture notes).

format ELF64 executable 3
entry _start

NROUNDS = 2000
ROUND = 256
RAW_SZ = NROUNDS * ROUND            ; 512000

NROUNDS = 2000
ROUND = 256
RAW_SZ = NROUNDS * ROUND            ; 512000
BIT2_SZ = NROUNDS * 64              ; 128000
TRIT_SZ = NROUNDS * 52              ; 104000 (51 groups + 1 padded)
RLE_MAX = NROUNDS * 512

segment readable executable

include 'trit_codec.inc'   ; pack_groups/unpack_groups/pack5/unpack5 + UTBL

segment readable executable

include 'rle_pack.inc'   ; pack2/unpack2/rle_enc/rle_dec (no deps)
include '../emit.inc'      ; shared emit (single source)

; -- round codecs (src/dst round pointers set by caller) --
; raw: plain 256 B copy both directions
cpy256:
    mov     ecx, 256
    rep     movsb
    ret

; er_trit: rdi = 256 trits -> rsi (52 B: 51 groups + padded pack5)
; dr_trit: rdi = 52 B -> rsi (256 trits, pad trit restored to [255])
er_trit:
    push    rbx
    push    r12
    mov     rbx, rdi                ; src (preserved: pack calls clobber rdi)
    mov     r12, rsi                ; dst
    mov     edx, 51
    call    pack_groups
    test    rax, rax
    jnz     .fail
    movzx   eax, byte [rbx+255]
    mov     [pad5], al
    lea     rsi, [pad5]
    call    pack5                   ; rax = pad byte
    test    rdx, rdx
    jnz     .fail
    mov     [r12+51], al
    xor     eax, eax
    pop     r12
    pop     rbx
    ret
.fail:
    mov     rax, -1
    pop     r12
    pop     rbx
    ret

dr_trit:
    push    rbx
    push    r12
    mov     rbx, rsi                ; dst
    mov     r12, rdi                ; src (calls advance rdi/rsi)
    mov     rdi, r12
    mov     rsi, rbx
    mov     edx, 51
    call    unpack_groups           ; 255 trits -> dst
    test    rax, rax
    jnz     .fail
    mov     al, [r12+51]            ; pad byte -> trit 255
    lea     rdi, [t5x]
    call    unpack5
    test    rax, rax
    jnz     .fail
    mov     al, [t5x]
    mov     [rbx+255], al
    xor     eax, eax
    pop     r12
    pop     rbx
    ret
.fail:
    mov     rax, -1
    pop     r12
    pop     rbx
    ret
_start:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    ; open actions file
    mov     eax, 257                ; sys_openat
    mov     edi, -100               ; AT_FDCWD
    lea     rsi, [FPATH]
    xor     edx, edx                ; O_RDONLY
    syscall
    cmp     rax, 0
    js      .fail
    mov     r15d, eax               ; fd
    xor     r14d, r14d              ; total
.frd:
    mov     eax, 0                  ; sys_read
    mov     edi, r15d
    mov     edx, RAW_SZ
    sub     edx, r14d
    lea     rsi, [filebuf+r14]
    syscall
    test    rax, rax
    jle     .frd_end
    add     r14, rax
    cmp     r14d, RAW_SZ
    jb      .frd
.frd_end:
    mov     eax, 3                  ; sys_close
    mov     edi, r15d
    syscall
    cmp     r14d, RAW_SZ
    jne     .fail
    ; ---- encode + verify, all methods ----
    ; r12d = fails, r13d = round, rbx = rle off_accum
    xor     r12d, r12d
    xor     ebx, ebx
    xor     r13d, r13d
.round:
    cmp     r13d, NROUNDS
    jae     .rounds_done
    mov     eax, r13d
    shl     rax, 8                  ; r*256
    lea     r14, [filebuf+rax]      ; src (r14 scratch? NO calls yet -- but
                                    ; encode calls follow; r14 dies. recompute
                                    ; per method instead: use fresh math below)
    ; RAW
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [e_raw+rax]        ; dst (rep movsb: [rsi] -> [rdi])
    lea     rsi, [filebuf+rax]      ; src
    mov     ecx, ROUND
    rep     movsb
    add     qword [t_raw], ROUND
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [e_raw+rax]
    lea     rsi, [filebuf+rax]
    mov     ecx, ROUND
    call    mem_eq
    xor     ecx, ecx
    test    eax, eax
    setz    cl                      ; 1 when differ
    add     [fails], rcx
    ; 2BIT
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [filebuf+rax]
    mov     eax, r13d
    shl     rax, 6                  ; r*64
    lea     rsi, [e_2bit+rax]
    call    pack2
    test    rax, rax
    jnz     .efail
    add     qword [t_2bit], 64
    mov     eax, r13d
    shl     rax, 6
    lea     rdi, [e_2bit+rax]
    lea     rsi, [chk]
    call    unpack2
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [chk]
    lea     rsi, [filebuf+rax]
    mov     ecx, ROUND
    call    mem_eq
    xor     ecx, ecx
    test    eax, eax
    setz    cl
    add     [fails], rcx
    ; TRIT
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [filebuf+rax]      ; src
    imul    rax, r13, 52            ; r*52
    lea     rsi, [e_trit+rax]
    call    er_trit
    test    rax, rax
    jnz     .efail
    add     qword [t_trit], 52
    imul    rax, r13, 52
    lea     rdi, [e_trit+rax]
    lea     rsi, [chk]
    call    dr_trit
    test    rax, rax
    jnz     .efail
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [chk]
    lea     rsi, [filebuf+rax]
    mov     ecx, ROUND
    call    mem_eq
    xor     ecx, ecx
    test    eax, eax
    setz    cl
    add     [fails], rcx
    ; RLE
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [filebuf+rax]      ; src
    lea     rsi, [e_rle+rbx]        ; dst at off_accum
    call    rle_enc                 ; rax = len
    mov     rcx, r13
    shl     rcx, 4                  ; r*16 (entry = 2 qwords)
    lea     rdx, [offs+rcx]
    mov     [rdx], rbx              ; offs[2r] = start
    add     rbx, rax
    mov     [rdx+8], rbx            ; offs[2r+1] = end
    add     [t_rle], rax
    mov     rax, [rdx+8]            ; len = end - start
    sub     rax, [rdx]
    mov     rdx, [rdx]              ; start
    lea     rdi, [e_rle+rdx]
    mov     edx, eax                ; len
    lea     rsi, [chk]
    call    rle_dec
    test    rax, rax
    jnz     .efail
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [chk]
    lea     rsi, [filebuf+rax]
    mov     ecx, ROUND
    call    mem_eq
    xor     ecx, ecx
    test    eax, eax
    setz    cl
    add     [fails], rcx
    inc     r13d
    jmp     .round
.rounds_done:
    mov     rcx, NROUNDS
    shl     rcx, 4
    mov     rax, rbx
    mov     [offs+rcx], rax         ; sentinel offs[2N]
    ; ---- speed: best-of-3 encode-all + decode-all per method ----
    ; macro-free explicit loops; t_sCy/t_sNs hold starts (cpuid-safe)
    ; ENC RAW
    mov     qword [bestCy], -1
    mov     qword [bestNs], -1
    mov     r15d, 3
.ber:
    call    cycles
    mov     [t_sCy], rax
    call    wallns
    mov     [t_sNs], rax
    xor     r13d, r13d
.berl:
    cmp     r13d, NROUNDS
    jae     .berd
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [e_raw+rax]        ; dst (rep movsb: [rsi] -> [rdi])
    lea     rsi, [filebuf+rax]      ; src
    mov     ecx, ROUND
    rep     movsb
    inc     r13d
    jmp     .berl
.berd:
    call    wallns
    sub     rax, [t_sNs]
    mov     [t_eNs], rax
    call    cycles
    sub     rax, [t_sCy]
    cmp     rax, [bestCy]
    jae     .ber2
    mov     [bestCy], rax
    mov     rax, [t_eNs]
    mov     [bestNs], rax
.ber2:
    dec     r15d
    jnz     .ber
    mov     rax, 512000000
    xor     edx, edx
    div     qword [bestNs]
    mov     [mEncRaw], rax
    ; DEC RAW
    mov     qword [bestCy], -1
    mov     qword [bestNs], -1
    mov     r15d, 3
.bdr:
    call    cycles
    mov     [t_sCy], rax
    call    wallns
    mov     [t_sNs], rax
    xor     r13d, r13d
.bdrl:
    cmp     r13d, NROUNDS
    jae     .bdrd
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [chk]              ; dst scratch
    lea     rsi, [e_raw+rax]        ; src
    mov     ecx, ROUND
    rep     movsb
    inc     r13d
    jmp     .bdrl
.bdrd:
    call    wallns
    sub     rax, [t_sNs]
    mov     [t_eNs], rax
    call    cycles
    sub     rax, [t_sCy]
    cmp     rax, [bestCy]
    jae     .bdr2
    mov     [bestCy], rax
    mov     rax, [t_eNs]
    mov     [bestNs], rax
.bdr2:
    dec     r15d
    jnz     .bdr
    mov     rax, 512000000
    xor     edx, edx
    div     qword [bestNs]
    mov     [mDecRaw], rax
    ; ENC 2BIT
    mov     qword [bestCy], -1
    mov     qword [bestNs], -1
    mov     r15d, 3
.be2:
    call    cycles
    mov     [t_sCy], rax
    call    wallns
    mov     [t_sNs], rax
    xor     r13d, r13d
.be2l:
    cmp     r13d, NROUNDS
    jae     .be2d
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [filebuf+rax]
    mov     eax, r13d
    shl     rax, 6
    lea     rsi, [e_2bit+rax]
    call    pack2
    inc     r13d
    jmp     .be2l
.be2d:
    call    wallns
    sub     rax, [t_sNs]
    mov     [t_eNs], rax
    call    cycles
    sub     rax, [t_sCy]
    cmp     rax, [bestCy]
    jae     .be22
    mov     [bestCy], rax
    mov     rax, [t_eNs]
    mov     [bestNs], rax
.be22:
    dec     r15d
    jnz     .be2
    mov     rax, 512000000
    xor     edx, edx
    div     qword [bestNs]
    mov     [mEnc2b], rax
    ; DEC 2BIT
    mov     qword [bestCy], -1
    mov     qword [bestNs], -1
    mov     r15d, 3
.bd2:
    call    cycles
    mov     [t_sCy], rax
    call    wallns
    mov     [t_sNs], rax
    xor     r13d, r13d
.bd2l:
    cmp     r13d, NROUNDS
    jae     .bd2d
    mov     eax, r13d
    shl     rax, 6
    lea     rdi, [e_2bit+rax]
    lea     rsi, [chk]
    call    unpack2
    inc     r13d
    jmp     .bd2l
.bd2d:
    call    wallns
    sub     rax, [t_sNs]
    mov     [t_eNs], rax
    call    cycles
    sub     rax, [t_sCy]
    cmp     rax, [bestCy]
    jae     .bd22
    mov     [bestCy], rax
    mov     rax, [t_eNs]
    mov     [bestNs], rax
.bd22:
    dec     r15d
    jnz     .bd2
    mov     rax, 512000000
    xor     edx, edx
    div     qword [bestNs]
    mov     [mDec2b], rax
    ; ENC TRIT
    mov     qword [bestCy], -1
    mov     qword [bestNs], -1
    mov     r15d, 3
.bet:
    call    cycles
    mov     [t_sCy], rax
    call    wallns
    mov     [t_sNs], rax
    xor     r13d, r13d
.betl:
    cmp     r13d, NROUNDS
    jae     .betd
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [filebuf+rax]
    imul    rax, r13, 52
    lea     rsi, [e_trit+rax]
    call    er_trit
    inc     r13d
    jmp     .betl
.betd:
    call    wallns
    sub     rax, [t_sNs]
    mov     [t_eNs], rax
    call    cycles
    sub     rax, [t_sCy]
    cmp     rax, [bestCy]
    jae     .bet2
    mov     [bestCy], rax
    mov     rax, [t_eNs]
    mov     [bestNs], rax
.bet2:
    dec     r15d
    jnz     .bet
    mov     rax, 512000000
    xor     edx, edx
    div     qword [bestNs]
    mov     [mEncTr], rax
    ; DEC TRIT
    mov     qword [bestCy], -1
    mov     qword [bestNs], -1
    mov     r15d, 3
.bdt:
    call    cycles
    mov     [t_sCy], rax
    call    wallns
    mov     [t_sNs], rax
    xor     r13d, r13d
.bdtl:
    cmp     r13d, NROUNDS
    jae     .bdtd
    imul    rax, r13, 52
    lea     rdi, [e_trit+rax]
    lea     rsi, [chk]
    call    dr_trit
    inc     r13d
    jmp     .bdtl
.bdtd:
    call    wallns
    sub     rax, [t_sNs]
    mov     [t_eNs], rax
    call    cycles
    sub     rax, [t_sCy]
    cmp     rax, [bestCy]
    jae     .bdt2
    mov     [bestCy], rax
    mov     rax, [t_eNs]
    mov     [bestNs], rax
.bdt2:
    dec     r15d
    jnz     .bdt
    mov     rax, 512000000
    xor     edx, edx
    div     qword [bestNs]
    mov     [mDecTr], rax
    ; ENC RLE
    mov     qword [bestCy], -1
    mov     qword [bestNs], -1
    mov     r15d, 3
.berl2:
    call    cycles
    mov     [t_sCy], rax
    call    wallns
    mov     [t_sNs], rax
    xor     r13d, r13d
    xor     ebx, ebx
.berl2l:
    cmp     r13d, NROUNDS
    jae     .berl2d
    mov     eax, r13d
    shl     rax, 8
    lea     rdi, [filebuf+rax]
    lea     rsi, [e_rle+rbx]
    call    rle_enc
    add     rbx, rax
    inc     r13d
    jmp     .berl2l
.berl2d:
    call    wallns
    sub     rax, [t_sNs]
    mov     [t_eNs], rax
    call    cycles
    sub     rax, [t_sCy]
    cmp     rax, [bestCy]
    jae     .ber22
    mov     [bestCy], rax
    mov     rax, [t_eNs]
    mov     [bestNs], rax
.ber22:
    dec     r15d
    jnz     .berl2
    mov     rax, 512000000
    xor     edx, edx
    div     qword [bestNs]
    mov     [mEncRl], rax
    ; DEC RLE (uses offs from verify pass)
    mov     qword [bestCy], -1
    mov     qword [bestNs], -1
    mov     r15d, 3
.bdl:
    call    cycles
    mov     [t_sCy], rax
    call    wallns
    mov     [t_sNs], rax
    xor     r13d, r13d
.bdll:
    cmp     r13d, NROUNDS
    jae     .bdld
    mov     eax, r13d
    shl     rax, 4                  ; r*16
    lea     rdx, [offs+rax]         ; &offs[2r]
    mov     rdi, [rdx]              ; start
    lea     rdi, [e_rle+rdi]
    mov     eax, [rdx+8]            ; end
    sub     rax, [rdx]              ; len
    mov     edx, eax
    lea     rsi, [chk]
    call    rle_dec
    inc     r13d
    jmp     .bdll
.bdld:
    call    wallns
    sub     rax, [t_sNs]
    mov     [t_eNs], rax
    call    cycles
    sub     rax, [t_sCy]
    cmp     rax, [bestCy]
    jae     .bdl2
    mov     [bestCy], rax
    mov     rax, [t_eNs]
    mov     [bestNs], rax
.bdl2:
    dec     r15d
    jnz     .bdl
    mov     rax, 512000000
    xor     edx, edx
    div     qword [bestNs]
    mov     [mDecRl], rax
.emit_all:
    lea     rsi, [QNR]
    mov     rdx, QNR_LEN
    call    emit_str
    mov     rax, NROUNDS
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QRB]
    mov     rdx, QRB_LEN
    call    emit_str
    mov     rax, [t_raw]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [Q2B]
    mov     rdx, Q2B_LEN
    call    emit_str
    mov     rax, [t_2bit]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QTR]
    mov     rdx, QTR_LEN
    call    emit_str
    mov     rax, [t_trit]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QRL]
    mov     rdx, QRL_LEN
    call    emit_str
    mov     rax, [t_rle]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QFL]
    mov     rdx, QFL_LEN
    call    emit_str
    mov     rax, [fails]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QER]
    mov     rdx, QER_LEN
    call    emit_str
    mov     rax, [mEncRaw]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QE2]
    mov     rdx, QE2_LEN
    call    emit_str
    mov     rax, [mEnc2b]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QET]
    mov     rdx, QET_LEN
    call    emit_str
    mov     rax, [mEncTr]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QEL]
    mov     rdx, QEL_LEN
    call    emit_str
    mov     rax, [mEncRl]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QDR]
    mov     rdx, QDR_LEN
    call    emit_str
    mov     rax, [mDecRaw]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QD2]
    mov     rdx, QD2_LEN
    call    emit_str
    mov     rax, [mDec2b]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QDT]
    mov     rdx, QDT_LEN
    call    emit_str
    mov     rax, [mDecTr]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [QDL]
    mov     rdx, QDL_LEN
    call    emit_str
    mov     rax, [mDecRl]
    call    emit_u64
    lea     rsi, [QNL]
    mov     rdx, 1
    call    emit_str
    mov     eax, 1                  ; sys_write(1, outbuf, outcur)
    mov     edi, 1
    lea     rsi, [outbuf]
    mov     rdx, [outcur]
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
    mov     rdx, [outcur]
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
    mov     rdx, [outcur]
    syscall
    mov     eax, 60
    mov     edi, 1
    syscall

segment readable

FPATH db '/tmp/opencode/sq2b_actions.bin', 0
QNR db 'phase2 rounds: '
QNR_LEN = $ - QNR
QNL db 0x0A
QRB db 'raw bytes: '
QRB_LEN = $ - QRB
Q2B db 'twobit bytes: '
Q2B_LEN = $ - Q2B
QTR db 'trit bytes: '
QTR_LEN = $ - QTR
QRL db 'rle bytes: '
QRL_LEN = $ - QRL
QFL db 'roundtrip fails: '
QFL_LEN = $ - QFL
QER db 'enc MB/s raw: '
QER_LEN = $ - QER
QE2 db 'enc MB/s 2bit: '
QE2_LEN = $ - QE2
QET db 'enc MB/s trit: '
QET_LEN = $ - QET
QEL db 'enc MB/s rle: '
QEL_LEN = $ - QEL
QDR db 'dec MB/s raw: '
QDR_LEN = $ - QDR
QD2 db 'dec MB/s 2bit: '
QD2_LEN = $ - QD2
QDT db 'dec MB/s trit: '
QDT_LEN = $ - QDT
QDL db 'dec MB/s rle: '
QDL_LEN = $ - QDL
LEF db 'phase2 encoder refused', 0x0A
LEF_LEN = $ - LEF
LFF db 'phase2 fatal (file)', 0x0A
LFF_LEN = $ - LFF

segment readable writeable

filebuf   rb 524288
e_raw     rb 512000
e_2bit    rb 131072
e_trit    rb 106496
e_rle     rb 1048576
chk       rb 256
pad5      rb 8
t5x       rb 8
offs      rq 4001
t_raw     rq 1
t_2bit    rq 1
t_trit    rq 1
t_rle     rq 1
fails     rq 1
numbuf    rb 32
fdigits   rb 8
outbuf    rb 8192
outcur      rq 1
tsbuf     rq 2
t_sCy     rq 1
t_sNs     rq 1
t_eNs     rq 1
bestCy    rq 1
bestNs    rq 1
mEncRaw   rq 1
mDecRaw   rq 1
mEnc2b    rq 1
mDec2b    rq 1
mEncTr    rq 1
mDecTr    rq 1
mEncRl    rq 1
mDecRl    rq 1

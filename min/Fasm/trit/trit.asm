; Trit codec toolset (FASM 1.73.x, x86-64 Linux) — Phase 1 of trit_meta.md.
; Base-3, little-trit-first: v = t0+3*t1+9*t2+27*t3+81*t4.
; Five trits per byte (3^5 = 243); codes 243..255 are framing markers and
; are REFUSED loudly on decode. Decode table generated at build time by
; the assembler itself (verified arithmetically in the self-test, so a
; table typo cannot hide).
;
; API (bulk, checked):
;   pack_groups   rdi = trits, rsi = out bytes, edx = ngroups
;                 -> rax 0 ok / -1 bad trit, rdx = bad group index
;   unpack_groups rdi = bytes, rsi = out trits, edx = nbytes
;                 -> rax 0 ok / -1 bad byte, rdx = bad byte index
;   pack5   rsi = 5 trits -> rax = byte / rdx = 0 ok, else bad pos+1
;   unpack5 al = byte, rdi = out5 -> rax 0 ok / -1 refused
; No libc: BSS arena, clock_gettime/rdtsc for bench, write/exit.
; Assemble: fasm trit.asm trit

format ELF64 executable 3
entry _start

NTRITS = 1000000
NGROUP = NTRITS / 5
NPACK = NTRITS / 5

segment readable executable

include 'trit_codec.inc'   ; shared codec (code + UTBL)

segment readable executable


; -- xoshiro256++ : rdi = state -> rax --
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

; -- emit_str: rsi = ptr, rdx = len --
emit_str:
    mov     rax, [ocur]
    lea     rdi, [obuf+rax]
    mov     rcx, rdx
    rep     movsb
    mov     rax, rdi
    sub     rax, obuf
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

; -- emit_hex16: rbx -> 16 hex chars --
emit_hex16:
    mov     rax, [ocur]
    lea     rdi, [obuf+rax]
    mov     rcx, 16
.hh:
    rol     rbx, 4
    mov     al, bl
    and     al, 0x0F
    add     al, '0'
    cmp     al, '9'
    jbe     .hs
    add     al, 39
.hs:
    mov     [rdi], al
    inc     rdi
    dec     ecx
    jnz     .hh
    mov     rax, rdi
    sub     rax, obuf
    mov     [ocur], rax
    ret

; -- wallns: -> rax = CLOCK_MONOTONIC ns (clobbers rcx,rdx,rsi,rdi,r11) --
wallns:
    mov     eax, 228                ; sys_clock_gettime
    mov     edi, 1                  ; MONOTONIC
    lea     rsi, [tsbuf]
    syscall
    mov     rax, [tsbuf]            ; sec
    mov     rcx, 1000000000
    mul     rcx                     ; rdx:rax = sec*1e9 (sec small, rdx=0)
    add     rax, [tsbuf+8]          ; + nsec
    ret

; -- cycles: -> rax = serialized rdtsc (clobbers rax,rbx,rcx,rdx) --
cycles:
    xor     eax, eax
    cpuid
    rdtsc
    shl     rdx, 32
    or      rax, rdx
    ret

_start:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    ; ---- exhaustive self-test: all 243 codes round-trip ----
    xor     r12d, r12d              ; fails
    xor     ebx, ebx                ; total
    xor     r13d, r13d              ; v = 0..242
.rt:
    cmp     r13d, 243
    jae     .rt_done
    mov     eax, r13d
    lea     rdi, [t5buf]
    call    unpack5                 ; al=v -> trits
    test    rax, rax
    jnz     .rt_fail
    lea     rsi, [t5buf]
    call    pack5                   ; -> rax byte
    test    rdx, rdx
    jnz     .rt_fail
    cmp     eax, r13d
    jne     .rt_fail
    jmp     .rt_next
.rt_fail:
    inc     r12d
.rt_next:
    inc     ebx
    inc     r13d
    jmp     .rt
.rt_done:
    ; ---- refusal: bytes 243..255 ----
    mov     r13d, 243
.rj:
    cmp     r13d, 256
    jae     .rj_done
    mov     eax, r13d
    lea     rdi, [t5buf]
    call    unpack5
    cmp     rax, -1                 ; must refuse
    je      .rj_next
    inc     r12d
.rj_next:
    inc     ebx
    inc     r13d
    jmp     .rj
.rj_done:
    ; ---- refusal: trit value 3 at each position ----
    xor     r13d, r13d              ; pos
.rp:
    cmp     r13d, 5
    jae     .rp_done
    lea     rdi, [t5buf]
    xor     eax, eax
    mov     [rdi], eax              ; zero 4 low trits (dword)
    mov     byte [rdi+4], 0
    mov     eax, r13d
    mov     byte [rdi+rax], 3       ; poison one position
    lea     rsi, [t5buf]
    call    pack5
    test    rdx, rdx                ; rdx != 0 means refused
    jnz     .rp_next
    inc     r12d
.rp_next:
    inc     ebx
    inc     r13d
    jmp     .rp
.rp_done:
    lea     rsi, [Lst]
    mov     rdx, LST_LEN
    call    emit_str
    mov     eax, r12d
    call    emit_u64
    lea     rsi, [Lslash]
    mov     rdx, 1
    call    emit_str
    mov     eax, ebx
    call    emit_u64
    lea     rsi, [Lnl]
    mov     rdx, 1
    call    emit_str
    test    r12d, r12d
    jnz     .fail_exit
    ; ---- fill 1M trits via xoshiro(seed 0x2026) % 3 ----
    lea     rdi, [rngst]
    mov     rsi, 0x2026
    mov     rax, rsi
    mov     rcx, 0x9E3779B97F4A7C15
    add     rax, rcx
    mov     [rdi], rax
    mov     rax, rsi
    mov     rcx, 0xBF58476D1CE4E5B9
    xor     rax, rcx
    mov     [rdi+8], rax
    mov     rax, rsi
    mov     rcx, 0x94D049BB133111EB
    add     rax, rcx
    mov     [rdi+16], rax
    mov     rax, rsi
    mov     rcx, 0xF0BA35E12960E9E7
    xor     rax, rcx
    mov     [rdi+24], rax
    mov     r12d, 10
.seed_warm:
    push    r12
    lea     rdi, [rngst]
    call    xoshiro
    pop     r12
    dec     r12d
    jnz     .seed_warm
    lea     rbx, [trits]
    mov     r15d, NTRITS
.fill:
    push    rbx
    push    r15
    lea     rdi, [rngst]
    call    xoshiro
    pop     r15
    pop     rbx
    xor     edx, edx
    mov     ecx, 3
    div     ecx
    mov     [rbx], dl
    inc     rbx
    dec     r15d
    jnz     .fill
    ; ---- bulk round-trip: pack -> unpack -> compare ----
    lea     rdi, [trits]
    lea     rsi, [packed]
    mov     edx, NGROUP
    call    pack_groups
    test    rax, rax
    jnz     .fail_exit
    lea     rdi, [packed]
    lea     rsi, [unpacked]
    mov     edx, NPACK
    call    unpack_groups
    test    rax, rax
    jnz     .fail_exit
    lea     rdi, [trits]
    lea     rsi, [unpacked]
    mov     ecx, NTRITS
    repe    cmpsb
    jne     .fail_exit
    ; ---- digest packed buffer (FNV-1a, for C cross-check) ----
    mov     rax, 0xcbf29ce484222325
    mov     rbx, rax
    lea     rsi, [packed]
    mov     ecx, NPACK
.dig:
    xor     bl, [rsi]
    mov     rdx, 0x100000001b3
    mov     rax, rbx
    mul     rdx
    mov     rbx, rax
    inc     rsi
    dec     ecx
    jnz     .dig
    mov     [digest], rbx
    lea     rsi, [Ldg]
    mov     rdx, LDG_LEN
    call    emit_str
    call    emit_hex16
    lea     rsi, [Lnl]
    mov     rdx, 1
    call    emit_str
    ; ---- bench pack best-of-5 (cycles + wall) ----
    mov     qword [bestCy], -1
    mov     qword [bestNs], -1
    mov     r15d, 5
.bp:
    call    cycles
    mov     r14, rax
    call    wallns
    mov     r13, rax
    lea     rdi, [trits]
    lea     rsi, [packed]
    mov     edx, NGROUP
    call    pack_groups
    call    wallns
    mov     [t_endns], rax
    call    cycles
    mov     r12, rax
    mov     rbx, [t_endns]
    sub     r12, r14                ; cycles
    sub     rbx, r13                ; ns
    cmp     r12, [bestCy]
    jae     .bp2
    mov     [bestCy], r12
.bp2:
    cmp     rbx, [bestNs]
    jae     .bp3
    mov     [bestNs], rbx
.bp3:
    dec     r15d
    jnz     .bp
    mov     rax, [bestCy]           ; cycles/Ktrit = cy*1000/1M = cy/1000
    xor     edx, edx
    mov     ecx, 1000
    div     rcx
    mov     [mPackCy], rax
    mov     rax, [bestNs]           ; out MB/s = 200000*1000/ns
    mov     rbx, rax
    mov     rax, 200000000
    xor     edx, edx
    div     rbx
    mov     [mPackMB], rax
    ; ---- bench unpack best-of-5 ----
    mov     qword [bestCy], -1
    mov     qword [bestNs], -1
    mov     r15d, 5
.bu:
    call    cycles
    mov     r14, rax
    call    wallns
    mov     r13, rax
    lea     rdi, [packed]
    lea     rsi, [unpacked]
    mov     edx, NPACK
    call    unpack_groups
    call    wallns
    mov     [t_endns], rax
    call    cycles
    mov     r12, rax
    mov     rbx, [t_endns]
    sub     r12, r14
    sub     rbx, r13
    cmp     r12, [bestCy]
    jae     .bu2
    mov     [bestCy], r12
.bu2:
    cmp     rbx, [bestNs]
    jae     .bu3
    mov     [bestNs], rbx
.bu3:
    dec     r15d
    jnz     .bu
    mov     rax, [bestCy]
    xor     edx, edx
    mov     ecx, 1000
    div     rcx
    mov     [mUnpCy], rax
    mov     rax, [bestNs]
    mov     rbx, rax
    mov     rax, 200000000
    xor     edx, edx
    div     rbx
    mov     [mUnpMB], rax
    ; ---- print metrics ----
    lea     rsi, [Lpc]
    mov     rdx, LPC_LEN
    call    emit_str
    mov     rax, [mPackCy]
    call    emit_u64
    lea     rsi, [Lnl]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [Luc]
    mov     rdx, LUC_LEN
    call    emit_str
    mov     rax, [mUnpCy]
    call    emit_u64
    lea     rsi, [Lnl]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [Lpm]
    mov     rdx, LPM_LEN
    call    emit_str
    mov     rax, [mPackMB]
    call    emit_u64
    lea     rsi, [Lnl]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [Lum]
    mov     rdx, LUM_LEN
    call    emit_str
    mov     rax, [mUnpMB]
    call    emit_u64
    lea     rsi, [Lnl]
    mov     rdx, 1
    call    emit_str
    mov     eax, 1
    mov     edi, 1
    lea     rsi, [obuf]
    mov     rdx, [ocur]
    syscall
    mov     eax, 60
    xor     edi, edi
    syscall
.fail_exit:
    mov     eax, 1
    mov     edi, 1
    lea     rsi, [obuf]
    mov     rdx, [ocur]
    syscall
    mov     eax, 60
    mov     edi, 1
    syscall

segment readable


Lst db 'trit selftest fails/total: '
LST_LEN = $ - Lst
Lslash db '/'
Lnl db 0x0A
Ldg db 'digest: '
LDG_LEN = $ - Ldg
Lpc db 'pack cycles/Ktrit: '
LPC_LEN = $ - Lpc
Luc db 'unpack cycles/Ktrit: '
LUC_LEN = $ - Luc
Lpm db 'pack out MB/s: '
LPM_LEN = $ - Lpm
Lum db 'unpack in MB/s: '
LUM_LEN = $ - Lum

segment readable writeable

trits     rb NTRITS
packed    rb NPACK
unpacked  rb NTRITS
t5buf     rb 8
rngst     rq 4
tsbuf     rq 2
t_endns   rq 1
digest    rq 1
bestCy    rq 1
bestNs    rq 1
mPackCy   rq 1
mUnpCy    rq 1
mPackMB   rq 1
mUnpMB    rq 1
numbuf    rb 32
obuf      rb 2048
ocur      rq 1

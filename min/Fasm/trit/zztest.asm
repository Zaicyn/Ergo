; zztest: self-test + speed for int_codec.inc (Phase A gate).
; Exhaustive int8 round-trip + width table boundaries + put/get per width.
; Assemble (from this directory): fasm zztest.asm zztest

format ELF64 executable 3
entry _start

NBUF = 65536

segment readable executable

include 'int_codec.inc'   ; zz_enc/zz_dec/put_i64/get_i64/i64width

segment readable executable

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

; -- cycles: -> rax = serialized rdtsc --
cycles:
    xor     eax, eax
    cpuid
    rdtsc
    shl     rdx, 32
    or      rax, rdx
    ret

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

_start:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    xor     r12d, r12d              ; fails
    xor     ebx, ebx                ; total
    ; ---- exhaustive int8 ----
    mov     r13d, -128
.i8:
    mov     eax, r13d
    call    zz_enc
    call    zz_dec
    cmp     eax, r13d
    jne     .i8f
    jmp     .i8w
.i8f:
    inc     r12d
.i8w:
    inc     ebx
    movsxd  rax, r13d
    call    i64width
    cmp     eax, 1
    jne     .i8f2
    jmp     .i8n
.i8f2:
    inc     r12d
.i8n:
    inc     ebx
    inc     r13d
    cmp     r13d, 128
    jne     .i8
    ; ---- width table (32 entries) ----
    xor     r13d, r13d              ; entry 0..31
.wt:
    cmp     r13d, 32
    jae     .wt_done
    mov     eax, r13d
    shl     rax, 4                  ; 16 B entries
    lea     r14, [wtab+rax]         ; entry (survives calls: callee-saved)
    mov     rax, [r14]              ; value
    call    i64width
    cmp     eax, [r14+8]            ; want
    jne     .wtf
    jmp     .wtp
.wtf:
    inc     r12d
.wtp:
    inc     ebx
    mov     rax, [r14]              ; put(value, want)
    mov     rsi, rax
    lea     rdi, [wbuf]
    mov     edx, [r14+8]
    call    put_i64
    lea     rdi, [wbuf]
    mov     edx, [r14+8]
    call    get_i64                 ; rax back
    cmp     rax, [r14]
    jne     .wtf2
    jmp     .wtp2
.wtf2:
    inc     r12d
.wtp2:
    inc     ebx
    inc     r13d
    jmp     .wt
.wt_done:
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
    ; ---- fill buf with LCG pattern ----
    xor     ecx, ecx
.fill:
    mov     eax, ecx
    imul    eax, eax, 0x9E3779B1
    mov     [buf+rcx*4], eax
    inc     ecx
    cmp     ecx, NBUF
    jne     .fill
    ; ---- codec digest over buf (LCG values): FNV(zz(v)), FNV(width(v)) ----
    mov     rbx, 0xcbf29ce484222325
    xor     r15d, r15d
.dl:
    cmp     r15d, NBUF
    jae     .dd
    mov     eax, [buf+r15*4]
    call    zz_enc
    mov     r14d, eax               ; zig (r14 survives: callees keep it)
    mov     ecx, 4
.fl:
    xor     bl, r14b
    mov     rdx, 0x100000001b3
    mov     rax, rbx
    mul     rdx
    mov     rbx, rax
    shr     r14d, 8
    dec     ecx
    jnz     .fl
    mov     eax, [buf+r15*4]
    movsxd  rax, eax                ; int32 -> int64
    call    i64width                ; eax = width
    xor     bl, al
    mov     rdx, 0x100000001b3
    mov     rax, rbx
    mul     rdx
    mov     rbx, rax
    inc     r15d
    jmp     .dl
.dd:
    mov     [digest], rbx
    lea     rsi, [Ldg]
    mov     rdx, LDG_LEN
    call    emit_str
    mov     rbx, [digest]
    call    emit_hex16
    lea     rsi, [Lnl]
    mov     rdx, 1
    call    emit_str
    ; ---- zz bench best-of-3 ----
    mov     r14, -1
    mov     r13d, 3
.bzz:
    call    cycles
    mov     [t_start], rax          ; start (BSS: cpuid clobbers rbx)
    xor     r15d, r15d
.bzzl:
    cmp     r15d, NBUF
    jae     .bzzd
    mov     eax, [buf+r15*4]
    call    zz_enc
    call    zz_dec
    mov     [buf+r15*4], eax
    inc     r15d
    jmp     .bzzl
.bzzd:
    call    cycles
    sub     rax, [t_start]
    cmp     rax, r14
    jae     .bzz2
    mov     r14, rax
.bzz2:
    dec     r13d
    jnz     .bzz
    mov     rax, r14                ; cycles/Kop = best*1000/NBUF
    mov     rcx, 1000
    mul     rcx                     ; rdx:rax (fits: best ~1M cy -> 1e9)
    mov     ecx, NBUF
    div     rcx
    mov     [mZz], rax
    ; ---- putget bench best-of-3 (width 4) ----
    mov     r14, -1
    mov     r13d, 3
.bpg:
    call    cycles
    mov     [t_start], rax
    xor     r15d, r15d
.bpgl:
    cmp     r15d, NBUF
    jae     .bpgd
    mov     esi, [buf+r15*4]
    lea     rdi, [buf2+r15*4]
    mov     edx, 4
    call    put_i64
    lea     rdi, [buf2+r15*4]
    mov     edx, 4
    call    get_i64
    mov     [buf+r15*4], eax
    inc     r15d
    jmp     .bpgl
.bpgd:
    call    cycles
    sub     rax, [t_start]
    cmp     rax, r14
    jae     .bpg2
    mov     r14, rax
.bpg2:
    dec     r13d
    jnz     .bpg
    mov     rax, r14
    mov     rcx, 1000
    mul     rcx
    mov     ecx, NBUF
    div     rcx
    mov     [mPg], rax
    ; ---- print speeds ----
    lea     rsi, [Lzz]
    mov     rdx, LZZ_LEN
    call    emit_str
    mov     rax, [mZz]
    call    emit_u64
    lea     rsi, [Lnl]
    mov     rdx, 1
    call    emit_str
    lea     rsi, [Lpg]
    mov     rdx, LPG_LEN
    call    emit_str
    mov     rax, [mPg]
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

wtab:
    dq -128
    dd 1, 0
    dq 127
    dd 1, 0
    dq 0
    dd 1, 0
    dq -1
    dd 1, 0
    dq -129
    dd 2, 0
    dq 128
    dd 2, 0
    dq -32768
    dd 2, 0
    dq 32767
    dd 2, 0
    dq -32769
    dd 3, 0
    dq 32768
    dd 3, 0
    dq -8388608
    dd 3, 0
    dq 8388607
    dd 3, 0
    dq -8388609
    dd 4, 0
    dq 8388608
    dd 4, 0
    dq -2147483648
    dd 4, 0
    dq 2147483647
    dd 4, 0
    dq -2147483649
    dd 5, 0
    dq 2147483649
    dd 5, 0
    dq -549755813888
    dd 5, 0
    dq 549755813887
    dd 5, 0
    dq -549755813889
    dd 6, 0
    dq 549755813889
    dd 6, 0
    dq -140737488355328
    dd 6, 0
    dq 140737488355327
    dd 6, 0
    dq -140737488355329
    dd 7, 0
    dq 140737488355329
    dd 7, 0
    dq -36028797018963968
    dd 7, 0
    dq 36028797018963967
    dd 7, 0
    dq -36028797018963969
    dd 8, 0
    dq 36028797018963969
    dd 8, 0
    dq 0x8000000000000000
    dd 8, 0
    dq 9223372036854775807
    dd 8, 0
Lst db 'zz selftest fails/total: '
LST_LEN = $ - Lst
Lslash db '/'
Lnl db 0x0A
Lzz db 'zz cycles/Kop: '
LZZ_LEN = $ - Lzz
Lpg db 'putget cycles/Kop: '
LPG_LEN = $ - Lpg
Ldg db 'codec digest: '
LDG_LEN = $ - Ldg

segment readable writeable

buf     rd NBUF
buf2    rd NBUF
wbuf    rb 8
digest  rq 1
t_start rq 1
mZz     rq 1
mPg     rq 1
numbuf  rb 32
obuf    rb 512
ocur    rq 1

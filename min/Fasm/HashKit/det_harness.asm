; det_harness.asm -- deterministic-analysis debug-kit tool (counter-mode RNG).
; Uses ../hash_rng.inc (splitmix64-Stafford pure hashes). Does NOT touch
; the ports' xoshiro streams. Two jobs:
;   1. KAT stream digest: FNV-1a over hash_u64/u32/u01 outputs (C mirror
;      in det_harness.c must print the same digests).
;   2. Counter-mode event demo: 20000 allocator-flavored events
;      (b,g,item) derived per-index, then RANDOM-ACCESS recompute of 5
;      spread indices with no replay -- the property that makes this a
;      complement to sequential xoshiro streams for failure analysis.
format ELF64 executable 3
entry _start

include '../hash_rng.inc'

SEED    = 0x0123456789ABCDEF
N_STREAM = 100000
N_EVENTS = 20000

segment readable executable

; -- fnv_fold: rax = value, r13 = state in/out (rbx = prime, preserved) --
fnv_fold:
    mov     ecx, 8
.fb:
    xor     r13b, al
    imul    r13, rbx
    shr     rax, 8
    dec     ecx
    jnz     .fb
    ret

; -- print_hex64: rax = value -> 16 hex chars + \n on stdout --
print_hex64:
    push    rbx
    push    rcx
    push    rdx
    mov     rcx, 16
    lea     rdx, [hexbuf+16]
.ph:
    mov     rbx, rax
    and     rbx, 0xF
    mov     bl, [hextab+rbx]
    dec     rdx
    mov     [rdx], bl
    shr     rax, 4
    dec     rcx
    jnz     .ph
    mov     byte [hexbuf+16], 10
    mov     eax, 1
    mov     edi, 1
    lea     rsi, [hexbuf]
    mov     edx, 17
    syscall
    pop     rdx
    pop     rcx
    pop     rbx
    ret

; -- print_str: rsi = ptr, rdx = len --
print_str:
    mov     eax, 1
    mov     edi, 1
    syscall
    ret

_start:
    mov     rbx, 0x100000001B3       ; FNV prime (survives hash calls)
    mov     r13, 0xCBF29CE484222325 ; FNV offset
    xor     r12d, r12d              ; i
.stream:
    mov     rdi, SEED
    add     rdi, r12
    call    hash_u64
    call    fnv_fold
    mov     rdi, SEED
    add     rdi, r12
    call    hash_u32
    call    fnv_fold
    mov     rdi, SEED
    add     rdi, r12
    call    hash_u01
    movq    rax, xmm0
    call    fnv_fold
    inc     r12
    cmp     r12, N_STREAM
    jne     .stream
    lea     rsi, [S_STREAM]
    mov     rdx, S_STREAM_LEN
    call    print_str
    mov     rax, r13
    call    print_hex64

    ; -- counter-mode events: (b,g,item) per index k --
    mov     r13, 0xCBF29CE484222325
    xor     r12d, r12d              ; k
.events:
    mov     rdi, SEED
    lea     rax, [r12*4]
    xor     rdi, rax
    call    hash_u32
    and     eax, 15
    mov     r10d, eax               ; b
    mov     rdi, SEED
    lea     rax, [r12*4+1]
    xor     rdi, rax
    call    hash_u32
    and     eax, 31
    mov     r11d, eax               ; g
    mov     rdi, SEED
    lea     rax, [r12*4+2]
    xor     rdi, rax
    call    hash_u32
    and     eax, 255
    mov     r9d, eax                ; item (saved before fold)
    ; fold triple
    shl     rax, 16
    or      rax, r11
    shl     rax, 8
    or      rax, r10
    call    fnv_fold
    ; stash spread indices for spot check
    cmp     r12d, 0
    je      .stash0
    cmp     r12d, 1
    je      .stash1
    cmp     r12d, 2
    je      .stash2
    cmp     r12d, 9999
    je      .stash3
    cmp     r12d, 19999
    je      .stash4
.next_ev:
    inc     r12
    cmp     r12, N_EVENTS
    jne     .events
    lea     rsi, [S_EVENTS]
    mov     rdx, S_EVENTS_LEN
    call    print_str
    mov     rax, r13
    call    print_hex64

    ; -- random-access spot check: recompute stashed indices directly --
    xor     r14d, r14d              ; passes
    xor     r12d, r12d              ; slot 0..4
.spot:
    lea     rdx, [r12*4]
    lea     rdx, [rdx+r12*8]        ; slot byte offset = slot*12
    lea     r8, [spotv+rdx]         ; stashed triple ptr (r8 survives calls)
    mov     eax, [spotk+r12*4]      ; k
    mov     r15d, eax               ; save k
    mov     rdi, SEED
    lea     rdx, [rax*4]
    xor     rdi, rdx
    call    hash_u32
    and     eax, 15
    cmp     eax, [r8+0]
    jne     .spot_next
    mov     rdi, SEED
    mov     eax, r15d
    lea     rdx, [rax*4+1]
    xor     rdi, rdx
    call    hash_u32
    and     eax, 31
    cmp     eax, [r8+4]
    jne     .spot_next
    mov     rdi, SEED
    mov     eax, r15d
    lea     rdx, [rax*4+2]
    xor     rdi, rdx
    call    hash_u32
    and     eax, 255
    cmp     eax, [r8+8]
    jne     .spot_next
    inc     r14d
.spot_next:
    inc     r12d
    cmp     r12d, 5
    jne     .spot
    lea     rsi, [S_SPOT]
    mov     rdx, S_SPOT_LEN
    call    print_str
    mov     eax, r14d
    add     al, '0'
    mov     [hexbuf], al
    mov     byte [hexbuf+1], '/'
    mov     byte [hexbuf+2], '5'
    mov     byte [hexbuf+3], 10
    mov     eax, 1
    mov     edi, 1
    lea     rsi, [hexbuf]
    mov     edx, 4
    syscall
    mov     eax, 60
    xor     edi, edi
    syscall

.stash0:
    mov     [spotv+0], r10d
    mov     [spotv+4], r11d
    mov     [spotv+8], r9d
    jmp     .next_ev
.stash1:
    mov     [spotv+12], r10d
    mov     [spotv+16], r11d
    mov     [spotv+20], r9d
    jmp     .next_ev
.stash2:
    mov     [spotv+24], r10d
    mov     [spotv+28], r11d
    mov     [spotv+32], r9d
    jmp     .next_ev
.stash3:
    mov     [spotv+36], r10d
    mov     [spotv+40], r11d
    mov     [spotv+44], r9d
    jmp     .next_ev
.stash4:
    mov     [spotv+48], r10d
    mov     [spotv+52], r11d
    mov     [spotv+56], r9d
    jmp     .next_ev

segment readable

hextab db '0123456789abcdef'
S_STREAM db 'H stream '
S_STREAM_LEN = $ - S_STREAM
S_EVENTS db 'H events '
S_EVENTS_LEN = $ - S_EVENTS
S_SPOT db 'H spot '
S_SPOT_LEN = $ - S_SPOT
spotk dd 0, 1, 2, 9999, 19999

segment readable writeable

spotv   rd 15                       ; 5 x (b, g, item)
hexbuf  rb 24

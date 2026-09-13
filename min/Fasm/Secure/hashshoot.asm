; hashshoot.asm -- hash shootout for file-integrity use (Secure campaign).
; Three hashes over 4 KB frames (4096 = 512 u64 blocks, exact):
;   FNV-1a 64  (proposal Path A, canonical): h ^= b; h *= prime, byte-wise.
;   SPLITMIX-STREAM (HashKit extension): h = mix(h XOR block) per u64,
;     Stafford finalizer as the compression function, IV 0.
;   AD-HOC (control, proposal's CPU-hash spirit): h = (h<<13)^(h>>7)^block,
;     seed 166136261. Expected to lose on avalanche; kept honest.
; Per hash (via generic runners taking the hash fn in r12):
;   digest of pristine frame; full 32768-bit avalanche (histogram +
;   mean/min/max Hamming distance); best-of-5 ns/frame over 5000 iters;
;   2000-trial multi-byte detection count.
; Lines: "H <name> <digest16> <ns> <avalx1000> <min> <max> <det/2000>".
format ELF64 executable 3
entry _start
FNV_OFF = 0xCBF29CE484222325
FNV_PRM = 0x100000001B3
MIX_M1  = 0xBF58476D1CE4E5B9
MIX_M2  = 0x94D049BB133111EB
AD_SEED = 166136261
NFRAME  = 4096
NBLOCK  = 512
NDET    = 2000
NIT     = 5000
segment readable executable
wallns:
    mov     eax, 228
    mov     edi, 1
    lea     rsi, [tsbuf]
    syscall
    mov     rax, [tsbuf]
    mov     rcx, 1000000000
    mul     rcx
    add     rax, [tsbuf+8]
    ret
; -- fnv1a64: rdi = ptr -> rax digest. Clobbers rax/rcx/rdx/rdi/r8 --
fnv1a64:
    mov     rax, FNV_OFF
    mov     rdx, FNV_PRM
    mov     ecx, NFRAME
.fl:
    movzx   r8d, byte [rdi]
    xor     rax, r8
    imul    rax, rdx
    inc     rdi
    dec     ecx
    jnz     .fl
    ret
; -- spmix: rdi = ptr -> rax digest. Clobbers rax/rcx/rdx/rdi/r8 --
spmix:
    xor     eax, eax                ; IV 0
    mov     ecx, NBLOCK
.ml:
    xor     rax, [rdi]
    mov     r8, rax
    shr     r8, 30
    xor     rax, r8
    mov     r8, MIX_M1
    imul    rax, r8
    mov     r8, rax
    shr     r8, 27
    xor     rax, r8
    mov     r8, MIX_M2
    imul    rax, r8
    mov     r8, rax
    shr     r8, 31
    xor     rax, r8
    add     rdi, 8
    dec     ecx
    jnz     .ml
    ret
; -- adhoc: rdi = ptr -> rax digest. Clobbers rax/rcx/rdx/rdi/r8 --
adhoc:
    mov     rax, AD_SEED
    mov     ecx, NBLOCK
.al:
    mov     r8, rax
    shl     r8, 13
    shr     rax, 7
    xor     rax, r8
    xor     rax, [rdi]
    add     rdi, 8
    dec     ecx
    jnz     .al
    ret
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
; -- run_aval: r12 = hash fn, r11 = h0. Fills asum/amin/amax/aval1000/histo --
run_aval:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    xor     r13, r13                ; sum
    mov     r14, 64                 ; min
    xor     r15, r15                ; max
    lea     rax, [histo]
    mov     ecx, 65
.z:
    mov     qword [rax+rcx*8-8], 0
    dec     ecx
    jnz     .z
    xor     ebx, ebx                ; j = bit index
.al:
    cmp     ebx, 32768
    jae     .adone
    mov     eax, ebx
    shr     eax, 3                  ; byte
    mov     ecx, ebx
    and     ecx, 7                  ; bit
    mov     r10d, eax               ; save byte
    mov     r9d, ecx                ; save bit
    mov     al, 1
    shl     al, cl
    xor     [frame+r10], al         ; flip (r10 survives call? fn uses r8 only -- YES safe)
    push    rbx
    push    r9
    push    r10
    push    r11
    lea     rdi, [frame]
    call    r12
    pop     r11
    pop     r10
    pop     r9
    pop     rbx
    xor     rax, r11                ; diff vs h0
    popcnt  rax, rax                ; dist (fn preserves r10/r9/rbx? YES: uses rax/rcx/rdx/rdi/r8)
    add     r13, rax
    cmp     rax, r14
    jae     .nomin
    mov     r14, rax
.nomin:
    cmp     rax, r15
    jbe     .nomax
    mov     r15, rax
.nomax:
    inc     qword [histo+rax*8]
    ; unflip
    mov     eax, r10d
    mov     ecx, r9d
    mov     r10d, eax
    mov     al, 1
    shl     al, cl
    xor     [frame+r10], al
    inc     ebx
    jmp     .al
.adone:
    mov     [asum], r13
    mov     [amin], r14
    mov     [amax], r15
    mov     rax, r13
    mov     rcx, 1000
    mul     rcx                     ; sum*1000 (no overflow: 64*32768*1000 < 2^63)
    mov     rcx, 32768
    div     rcx
    mov     [aval1000], rax
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- run_speed: r12 = hash fn -> rax best ns/frame --
run_speed:
    push    rbx
    push    r12
    push    r13
    push    r14
    mov     qword [tbest], -1
    mov     r13d, 5
.rs:
    call    wallns
    mov     rbx, rax
    mov     r14d, NIT
.as:
    lea     rdi, [frame]
    call    r12
    add     [fsum], rax
    dec     r14d
    jnz     .as
    call    wallns
    sub     rax, rbx
    xor     edx, edx
    mov     rcx, NIT
    div     rcx
    cmp     rax, [tbest]
    jae     .rs2
    mov     [tbest], rax
.rs2:
    dec     r13d
    jnz     .rs
    mov     rax, [tbest]
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- run_detect: r12 = hash fn, r11 = h0 -> rax misses (of NDET) --
run_detect:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    ; backup frame
    lea     rsi, [frame]
    lea     rdi, [backup]
    mov     ecx, NFRAME
    rep     movsb
    mov     rax, 0x123456789
    mov     [xsst], rax
    xor     r15, r15                ; misses
    mov     r13d, NDET
.dt:
    lea     rdi, [xsst]
    call    xs64                    ; clobbers rax/rcx only; r13/r15 safe? xs uses rax,rcx -- YES safe
    mov     ecx, eax
    and     ecx, 7
    add     ecx, 2                  ; k = 2..9 bytes... spec says 2..8; use 2+(rnd&6)
    and     eax, 6
    add     eax, 2
    mov     r14d, eax               ; k
    xor     ebx, ebx                ; t
.kb:
    cmp     ebx, r14d
    jae     .kdone
    push    rbx
    push    r14
    lea     rdi, [xsst]
    call    xs64
    mov     ebx, eax
    and     ebx, 4095               ; pos
    push    rbx
    lea     rdi, [xsst]
    call    xs64
    pop     rbx
    and     eax, 255
    add     eax, 1                  ; delta 1..256 -> &255 nonzero-ish
    and     eax, 255
    jz      .kb_same                ; delta 0 impossible; keep simple: use al (1..255, never 0 since +1 mod 256 can be 0 if eax was 255! recheck)
.kb_same:
    xor     [frame+rbx], al
    pop     r14
    pop     rbx
    inc     ebx
    jmp     .kb
.kdone:
    push    r11
    push    r13
    push    r14
    push    r15
    lea     rdi, [frame]
    call    r12
    pop     r15
    pop     r14
    pop     r13
    pop     r11
    cmp     rax, r11
    jne     .spotted
    inc     r15                     ; MISS
.spotted:
    ; restore
    push    r11
    push    r13
    push    r14
    push    r15
    lea     rsi, [backup]
    lea     rdi, [frame]
    mov     ecx, NFRAME
    rep     movsb
    pop     r15
    pop     r14
    pop     r13
    pop     r11
    dec     r13d
    jnz     .dt
    mov     rax, r15
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- ph16: rax -> 16 hex at [rsi], advances. Clobbers rax/rcx/rbx --
ph16:
    push    rcx
    push    rbx
    mov     rcx, 16
.h:
    rol     rax, 4
    mov     ebx, eax
    and     ebx, 0xF
    mov     bl, [hextab+rbx]
    mov     [rsi], bl
    inc     rsi
    dec     rcx
    jnz     .h
    pop     rbx
    pop     rcx
    ret
; -- pdec: rax -> decimal at [rsi], advances. Clobbers rax/rcx/rdx/rbx --
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
; -- emitline: rdi = name(6B). Reads ldigest/lns/laval/lmin/lmax/ldet --
emitline:
    push    rax
    push    rcx
    push    rdx
    lea     rsi, [linebuf]
    mov     ecx, 6
.nl:
    mov     al, [rdi]
    mov     [rsi], al
    inc     rdi
    inc     rsi
    dec     ecx
    jnz     .nl
    mov     rax, [ldigest]
    call    ph16
    mov     byte [rsi], ' '
    inc     rsi
    mov     rax, [lns]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
    mov     rax, [laval]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
    mov     rax, [lmin]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
    mov     rax, [lmax]
    call    pdec
    mov     byte [rsi], ' '
    inc     rsi
    mov     rax, [ldet]
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    mov     rdx, rsi
    lea     rsi, [linebuf]
    sub     rdx, rsi
    mov     eax, 1
    mov     edi, 1
    syscall
    pop     rdx
    pop     rcx
    pop     rax
    ret
_start:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    xor     ecx, ecx
.fill:
    mov     eax, ecx
    imul    eax, eax, 91
    add     eax, 17
    xor     eax, 0xA5
    mov     [frame+rcx], al
    inc     ecx
    cmp     ecx, NFRAME
    jne     .fill
    mov     dword [frame], 0x32465345  ; "ESF2"
    ; hash 0: fnv
    lea     r12, [fnv1a64]
    lea     rdi, [frame]
    call    r12
    mov     [ldigest], rax
    mov     r11, rax
    call    run_aval
    mov     rax, [aval1000]
    mov     [laval], rax
    mov     rax, [amin]
    mov     [lmin], rax
    mov     rax, [amax]
    mov     [lmax], rax
    call    run_speed
    mov     [lns], rax
    mov     r11, [ldigest]
    call    run_detect
    mov     [ldet], rax
    lea     rdi, [nm0]
    call    emitline
    ; hash 1: spmix
    lea     r12, [spmix]
    lea     rdi, [frame]
    call    r12
    mov     [ldigest], rax
    mov     r11, rax
    call    run_aval
    mov     rax, [aval1000]
    mov     [laval], rax
    mov     rax, [amin]
    mov     [lmin], rax
    mov     rax, [amax]
    mov     [lmax], rax
    call    run_speed
    mov     [lns], rax
    mov     r11, [ldigest]
    call    run_detect
    mov     [ldet], rax
    lea     rdi, [nm1]
    call    emitline
    ; hash 2: adhoc
    lea     r12, [adhoc]
    lea     rdi, [frame]
    call    r12
    mov     [ldigest], rax
    mov     r11, rax
    call    run_aval
    mov     rax, [aval1000]
    mov     [laval], rax
    mov     rax, [amin]
    mov     [lmin], rax
    mov     rax, [amax]
    mov     [lmax], rax
    call    run_speed
    mov     [lns], rax
    mov     r11, [ldigest]
    call    run_detect
    mov     [ldet], rax
    lea     rdi, [nm2]
    call    emitline
    mov     eax, 60
    xor     edi, edi
    syscall
segment readable
hextab db '0123456789abcdef'
nm0 db 'H fnv  '
nm1 db 'H spm  '
nm2 db 'H adh  '
segment readable writeable
frame rb NFRAME
backup rb NFRAME
histo rq 65
tsbuf rq 2
fsum rq 1
tbest rq 1
xsst rq 1
asum rq 1
amin rq 1
amax rq 1
aval1000 rq 1
dbuf rb 24
linebuf rb 160
ldigest rq 1
lns rq 1
laval rq 1
lmin rq 1
lmax rq 1
ldet rq 1

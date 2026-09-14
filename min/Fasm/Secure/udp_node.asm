; udp_node.asm -- UDP transport shell on pktcore.inc. Role via argv[1]:
;   udp_node send   build frame, emit 8 units + meta to the proxy (PS),
;                   then serve fetches on PF until idle/cap, print S line.
;   udp_node recv   collect on PR, repair, fetch iff 1-2 units missing,
;                   commitment-check, print V line.
; Datagram: [seq u16][kind u8][idx u8][len u16][00] + payload.
; kinds: 0=unit 1=meta 2=parP 3=parQ 4=fetch-req. Fixed seq 7.
; No RNG here: damage happens at the proxy; draws never cross languages.
format ELF64 executable 3
entry _start
PS_ = 41001
PR_ = 41002
PF_ = 41003
SEQ_ = 7
segment readable executable
include 'pktcore.inc'
segment readable executable           ; inc ends in readable (st_m1)
; -- mkloop: rdi = dst16, esi = port -> sockaddr_in 127.0.0.1. --
mkloop:
    mov     word [rdi], 2
    mov     eax, esi
    xchg    al, ah
    mov     word [rdi+2], ax
    mov     dword [rdi+4], 0x0100007F
    mov     qword [rdi+8], 0
    ret
; -- udp_sock: -> eax fd. --
udp_sock:
    mov     eax, 41
    mov     edi, 2
    mov     esi, 2
    xor     edx, edx
    syscall
    ret
; -- selwait: edi = fd, esi = ms -> eax 1 ready / 0 timeout. --
selwait:
    push    rbx
    mov     ebx, edi
    mov     qword [selset], 0
    mov     qword [selset+8], 0
    mov     eax, ebx
    bts     qword [selset], rax
    mov     eax, esi
    mov     ecx, 1000
    xor     edx, edx
    div     ecx                     ; eax=sec, edx=ms-rem
    mov     [seltv], rax
    imul    edx, edx, 1000
    mov     [seltv+8], rdx
    mov     eax, 23
    lea     esi, [selset]
    xor     edx, edx
    xor     r10d, r10d
    lea     r8, [seltv]
    mov     edi, ebx
    inc     edi
    syscall                         ; rax = ready count
    test    eax, eax
    jz      .to
    mov     eax, 1
    jmp     .out
.to:
    xor     eax, eax
.out:
    pop     rbx
    ret
; -- send_main. --
send_main:
    push    rbx
    push    r12
    push    r13
    mov     rax, 0x123456789ABCDEF1
    mov     [trng], rax
    call    gf_init
    call    build
    ; meta: syndromes LE + commitment + auth
    xor     r12d, r12d
.sm:
    cmp     r12d, NP_
    jae     .smdone
    mov     ecx, r12d
    shl     ecx, 4
    xor     ebx, ebx
.smw:
    cmp     ebx, 4
    jae     .smnx
    mov     eax, [refs+rcx+rbx*4]
    mov     r13d, r12d
    shl     r13d, 4
    add     r13d, ebx
    shl     r13d, 2
    mov     dword [metbuf+r13], eax
    inc     ebx
    jmp     .smw
.smnx:
    inc     r12d
    jmp     .sm
.smdone:
    lea     rsi, [parP]
    lea     rdi, [pqcat]
    mov     ecx, PL_
    rep     movsb
    lea     rsi, [parQ]
    lea     rdi, [pqcat+512]
    mov     ecx, PL_
    rep     movsb
    mov     rdi, 18050561372206496278
    lea     rsi, [pqcat]
    mov     edx, 1024
    mov     rcx, 0x50524F4D495345
    call    ktag
    mov     qword [metbuf+128], rax
    mov     rdi, 18050561372206496278
    lea     rsi, [metbuf]
    mov     edx, 136
    mov     rcx, 0x53545245414D4155
    call    ktag
    mov     qword [metbuf+136], rax
    ; socket + emit 9 datagrams to proxy
    call    udp_sock
    mov     r12d, eax                ; ssnd
    lea     rdi, [proxyaddr]
    mov     esi, PS_
    call    mkloop
    xor     r13d, r13d               ; u
.snd:
    cmp     r13d, NP_
    jae     .sndm
    mov     eax, r13d
    shl     eax, 9
    lea     rsi, [bku+rax]
    mov     word [sbuf+8+0], SEQ_
    mov     byte [sbuf+8+2], 0
    mov     byte [sbuf+8+3], r13b   ; idx=u (al here is low(u*512)=0!)
    mov     word [sbuf+8+4], PL_
    mov     byte [sbuf+8+6], 0
    mov     byte [sbuf+8+7], 0
    lea     rdi, [sbuf+8+8]
    mov     ecx, PL_
    push    r13
    rep     movsb
    pop     r13
    mov     eax, 44
    mov     edi, r12d
    lea     rsi, [sbuf+8]
    mov     edx, PL_+8
    xor     r10d, r10d
    lea     r8, [proxyaddr]
    mov     r9d, 16
    syscall
    inc     r13d
    jmp     .snd
.sndm:
    mov     word [sbuf+8+0], SEQ_
    mov     byte [sbuf+8+2], 1
    mov     byte [sbuf+8+3], 0
    mov     word [sbuf+8+4], 256
    mov     byte [sbuf+8+6], 0
    mov     byte [sbuf+8+7], 0
    lea     rsi, [metbuf]
    lea     rdi, [sbuf+8+8]
    mov     ecx, 256
    rep     movsb
    mov     eax, 44
    mov     edi, r12d
    lea     rsi, [sbuf+8]
    mov     edx, 256+8
    xor     r10d, r10d
    lea     r8, [proxyaddr]
    mov     r9d, 16
    syscall
    ; bind fetch socket, serve until idle (1000 ms) or 8 served
    call    udp_sock
    mov     r13d, eax                ; sfs
    lea     rdi, [fetchaddr]
    mov     esi, PF_
    call    mkloop
    mov     eax, 49
    mov     edi, r13d
    lea     rsi, [fetchaddr]
    mov     edx, 16
    syscall
    xor     r12d, r12d               ; served
.serve:
    cmp     r12d, 8
    jae     .sdone
    mov     edi, r13d
    mov     esi, 1000
    call    selwait
    test    eax, eax
    jz      .sdone
    mov     dword [peerlen], 16
    mov     eax, 45
    mov     edi, r13d
    lea     rsi, [rbuf]
    mov     edx, 2048
    xor     r10d, r10d
    lea     r8, [peeraddr]
    lea     r9, [peerlen]
    syscall
    cmp     rax, 8
    jl      .serve
    cmp     byte [rbuf+2], 4
    jne     .serve
    mov     byte [sbuf+8+2], 2
    mov     byte [sbuf+8+3], 0
    mov     word [sbuf+8+4], PL_
    lea     rsi, [parP]
    lea     rdi, [sbuf+8+8]
    mov     ecx, PL_
    rep     movsb
    mov     eax, 44
    mov     edi, r13d
    lea     rsi, [sbuf+8]
    mov     edx, PL_+8
    xor     r10d, r10d
    lea     r8, [peeraddr]
    mov     r9d, 16
    syscall
    mov     byte [sbuf+8+2], 3
    lea     rsi, [parQ]
    lea     rdi, [sbuf+8+8]
    mov     ecx, PL_
    rep     movsb
    mov     eax, 44
    mov     edi, r13d
    lea     rsi, [sbuf+8]
    mov     edx, PL_+8
    xor     r10d, r10d
    lea     r8, [peeraddr]
    mov     r9d, 16
    syscall
    inc     r12d
    jmp     .serve
.sdone:
    lea     rsi, [linebuf]
    mov     ax, word [LS]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, dword [LSENT]
    mov     [rsi], eax
    add     rsi, 4
    mov     al, byte [LSENT+4]
    mov     [rsi], al
    inc     rsi
    mov     eax, 9
    call    pdec
    mov     eax, dword [LSERV]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, dword [LSERV+4]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, r12d
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- recv_main. --
recv_main:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    call    gf_init
    call    build ; known-answer scoring oracle only (repair never reads bku)
    call    udp_sock
    mov     r12d, eax                ; srcv
    lea     rdi, [bindaddr]
    mov     esi, PR_
    call    mkloop
    mov     eax, 49
    mov     edi, r12d
    lea     rsi, [bindaddr]
    mov     edx, 16
    syscall
    xor     eax, eax
    mov     ecx, NP_
    lea     rdi, [haveu]
    rep     stosb
    mov     byte [havem], 0
    xor     r13d, r13d               ; got
    xor     r14d, r14d               ; iters guard
.coll:
    cmp     r13d, 9
    jae     .cdone
    cmp     r14d, 40
    jae     .cdone
    inc     r14d
    mov     edi, r12d
    mov     esi, 500
    call    selwait
    test    eax, eax
    jz      .cdone
    mov     eax, 45
    mov     edi, r12d
    lea     rsi, [rbuf]
    mov     edx, 2048
    xor     r10d, r10d
    xor     r8d, r8d
    xor     r9d, r9d
    syscall
    cmp     rax, 8
    jl      .coll
    movzx   eax, byte [rbuf+2]       ; kind
    movzx   ebx, byte [rbuf+3]       ; idx
    movzx   ecx, word [rbuf+4]       ; len
    cmp     eax, 0
    je      .cu
    cmp     eax, 1
    je      .cm
    jmp     .coll
.cu:
    cmp     ebx, NP_
    jae     .coll
    cmp     byte [haveu+rbx], 0
    jne     .coll
    cmp     ecx, PL_
    jne     .coll
    lea     rsi, [rbuf+8]
    mov     eax, ebx
    shl     eax, 9
    lea     rdi, [fru+rax]
    push    rcx
    mov     ecx, PL_
    rep     movsb
    pop     rcx
    mov     byte [haveu+rbx], 1
    inc     r13d
    jmp     .coll
.cm:
    cmp     byte [havem], 0
    jne     .coll
    cmp     ecx, 256
    jne     .coll
    lea     rsi, [rbuf+8]
    lea     rdi, [metbuf]
    mov     ecx, 256
    rep     movsb
    mov     byte [havem], 1
    inc     r13d
    jmp     .coll
.cdone:
    mov     r15d, r13d               ; got
    xor     ebx, ebx                 ; nl
    xor     ecx, ecx
.cl:
    cmp     ecx, NP_
    jae     .cld
    cmp     byte [haveu+rcx], 0
    jne     .cln
    mov     dword [lostN+rcx*4], 1
    inc     ebx
    jmp     .clc
.cln:
    mov     dword [lostN+rcx*4], 0
.clc:
    inc     ecx
    jmp     .cl
.cld:
    mov     r14d, ebx                ; nl
    ; refs from meta (if present)
    cmp     byte [havem], 0
    je      .rep
    lea     rsi, [metbuf]
    lea     rdi, [refs]
    mov     ecx, 128
    rep     movsb
.rep:
    xor     ebx, ebx
.rl:
    cmp     ebx, NP_
    jae     .rdone
    cmp     dword [lostN+rbx*4], 0
    jne     .rnx
    mov     eax, ebx
    shl     eax, 9
    lea     rdi, [fru+rax]
    mov     ecx, ebx
    shl     ecx, 4
    lea     rsi, [refs+rcx]
    call    sec_pkt
.rnx:
    inc     ebx
    jmp     .rl
.rdone:
    call    bytes_ok
    cmp     eax, FR_
    je      .isfull
    xor     r12d, r12d               ; full=0
    xor     r13d, r13d               ; fetch=0
    cmp     byte [havem], 0
    je      .vout
    cmp     r14d, 1
    jl      .vout
    cmp     r14d, 2
    jg      .vout
    mov     r13d, 1                  ; fetch=1 (ebx=fd keeps r12d=full)
    call    udp_sock
    mov     ebx, eax
    lea     rdi, [fetchaddr]
    mov     esi, PF_
    call    mkloop
    mov     eax, 42
    mov     edi, ebx
    lea     rsi, [fetchaddr]
    mov     edx, 16
    syscall
    mov     byte [sbuf+8+2], 4
    mov     byte [sbuf+8+3], 0
    mov     word [sbuf+8+4], 1
    mov     byte [sbuf+8+8], 0
    mov     eax, 44
    mov     edi, ebx
    lea     rsi, [sbuf+8]
    mov     edx, 9
    xor     r10d, r10d
    xor     r8d, r8d
    xor     r9d, r9d
    syscall
    mov     edi, ebx
    mov     esi, 500
    call    selwait
    test    eax, eax
    jz      .vout
    mov     eax, 45
    mov     edi, ebx
    lea     rsi, [rbuf]
    mov     edx, 2048
    xor     r10d, r10d
    xor     r8d, r8d
    xor     r9d, r9d
    syscall
    cmp     rax, 8
    jl      .vout
    cmp     byte [rbuf+2], 2
    jne     .vout
    lea     rsi, [rbuf+8]
    lea     rdi, [fPb]
    mov     ecx, PL_
    rep     movsb
    mov     edi, ebx
    mov     esi, 500
    call    selwait
    test    eax, eax
    jz      .vout
    mov     eax, 45
    mov     edi, ebx
    lea     rsi, [rbuf]
    mov     edx, 2048
    xor     r10d, r10d
    xor     r8d, r8d
    xor     r9d, r9d
    syscall
    cmp     rax, 8
    jl      .vout
    cmp     byte [rbuf+2], 3
    jne     .vout
    lea     rsi, [rbuf+8]
    lea     rdi, [fQb]
    mov     ecx, PL_
    rep     movsb
    lea     rsi, [fPb]
    lea     rdi, [pqcat]
    mov     ecx, PL_
    rep     movsb
    lea     rsi, [fQb]
    lea     rdi, [pqcat+512]
    mov     ecx, PL_
    rep     movsb
    mov     rdi, 18050561372206496278
    lea     rsi, [pqcat]
    mov     edx, 1024
    mov     rcx, 0x50524F4D495345
    call    ktag
    cmp     rax, qword [metbuf+128]
    jne     .vout
    lea     rsi, [fPb]
    lea     rdi, [parP]
    mov     ecx, PL_
    rep     movsb
    lea     rsi, [fQb]
    lea     rdi, [parQ]
    mov     ecx, PL_
    rep     movsb
    lea     rdi, [lostN]
    mov     esi, r14d
    call    run_ecc
    call    bytes_ok
    cmp     eax, FR_
    jne     .vout
    mov     r12d, 1
    jmp     .vout
.isfull:
    mov     r12d, 1
    xor     r13d, r13d
.vout:
    lea     rsi, [linebuf]
    mov     ax, word [LV]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, dword [LGOT]
    mov     [rsi], eax
    add     rsi, 4
    mov     eax, r15d
    call    pdec
    mov     eax, dword [LLOST]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LLOST+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, r14d
    call    pdec
    mov     eax, dword [LFETCH]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LFETCH+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     al, byte [LFETCH+6]
    mov     [rsi], al
    inc     rsi
    mov     eax, r13d
    call    pdec
    mov     eax, dword [LFULL]
    mov     [rsi], eax
    add     rsi, 4
    mov     ax, word [LFULL+4]
    mov     [rsi], ax
    add     rsi, 2
    mov     eax, r12d
    call    pdec
    mov     byte [rsi], 10
    inc     rsi
    call    emit_line
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
_start:
    pop     rax                      ; argc
    cmp     rax, 2
    jl      .usage
    mov     rax, [rsp+8]             ; argv[1]
    mov     ecx, [rax]
    cmp     ecx, 'send'
    je      .send
    cmp     ecx, 'recv'
    je      .recv
.usage:
    lea     rsi, [USEMSG]
    mov     rdx, USELEN
    call    wstr
    mov     eax, 60
    mov     edi, 1
    syscall
.send:
    call    send_main
    jmp     .exit
.recv:
    call    recv_main
.exit:
    mov     eax, 60
    xor     edi, edi
    syscall
segment readable
LS db 'S '
LSENT db 'sent='
LSERV db ' served='
LV db 'V '
LGOT db 'got='
LLOST db ' lost='
LFETCH db ' fetch='
LFULL db ' full='
USEMSG db 'usage: udp_node send|recv', 10
USELEN = 26
segment readable writeable
bku rb 4096
fru rb 4096
parP rb 512
parQ rb 512
refs rd 32
gexp rb 512
glog rb 256
trng rq 1
usefl rb 4096
linebuf rb 256
dbuf rb 32
st_tag rq 1
st_ref rq 1
st_s2 rd 1
st_ca db 1
st_cb db 1
st_den db 1
st_pp db 1
st_qq db 1
sbuf rb 528
rbuf rb 2048
metbuf rb 256
pqcat rb 1024
fPb rb 512
fQb rb 512
haveu rb 8
havem db 1
proxyaddr rb 16
fetchaddr rb 16
bindaddr rb 16
peeraddr rb 16
peerlen rd 1
selset rb 16
seltv rq 2
lostN rd 8

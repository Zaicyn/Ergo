; tcp_node.asm -- TCP transport shell on pktcore.inc. Role via argv[1].
; Same datagrams as UDP, each sent as [len u16 LE][hdr8][payload].
; Topology: sender connects to proxy (PS); proxy connects to receiver
; listen (PR); fetch is a separate receiver->sender connection (PF).
; TCP_NODELAY on everything; verdict lines identical to udp_node.
format ELF64 executable 3
entry _start
PS_ = 41001
PR_ = 41002
PF_ = 41003
SEQ_ = 7
segment readable executable
include 'pktcore.inc'
segment readable executable           ; inc ends in readable (st_m1)
; -- mkloop: rdi = dst16, esi = port. --
mkloop:
    mov     word [rdi], 2
    mov     eax, esi
    xchg    al, ah
    mov     word [rdi+2], ax
    mov     dword [rdi+4], 0x0100007F
    mov     qword [rdi+8], 0
    ret
; -- tcp_sock: -> eax fd (STREAM). --
tcp_sock:
    mov     eax, 41
    mov     edi, 2
    mov     esi, 1
    xor     edx, edx
    syscall
    ret
; -- nodelay: edi = fd. --
nodelay:
    push    rbx
    mov     ebx, edi
    mov     dword [seltv], 1
    mov     eax, 54
    mov     edi, ebx
    mov     esi, 6
    mov     edx, 1
    lea     r10, [seltv]
    mov     r8d, 4
    syscall
    pop     rbx
    ret
; -- reuse: edi = fd (SO_REUSEADDR, for rapid reruns under TIME_WAIT). --
reuse:
    push    rbx
    mov     ebx, edi
    mov     dword [seltv], 1
    mov     eax, 54
    mov     edi, ebx
    mov     esi, 1
    mov     edx, 2
    lea     r10, [seltv]
    mov     r8d, 4
    syscall
    pop     rbx
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
    div     ecx
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
    syscall
    test    eax, eax
    jz      .to
    mov     eax, 1
    jmp     .out
.to:
    xor     eax, eax
.out:
    pop     rbx
    ret
; -- sendall: rdi = fd, rsi = buf, rdx = len. --
sendall:
    push    rbx
    push    r12
    mov     r12, rsi
    mov     rbx, rdx
.snd:
    test    rbx, rbx
    jz      .done
    mov     eax, 44
    mov     rsi, r12
    mov     rdx, rbx
    xor     r10d, r10d
    xor     r8d, r8d
    xor     r9d, r9d
    syscall
    cmp     rax, 0
    jle     .done
    add     r12, rax
    sub     rbx, rax
    jmp     .snd
.done:
    pop     r12
    pop     rbx
    ret
; -- txmsg: rdi = fd, rsi = payload, edx = paylen, cl = kind, r8b = idx.
; Framed: [len16][hdr8][payload]. Clobbers caller-saved + rbx/r12 via calls.
txmsg:
    push    rbx
    push    r12
    push    r13
    mov     r12d, edx
    mov     r13b, cl
    mov     bl, r8b
    mov     eax, r12d
    add     eax, 8
    mov     word [sbuf], ax
    mov     word [sbuf+2], SEQ_
    mov     byte [sbuf+4], r13b
    mov     byte [sbuf+5], bl
    mov     ax, r12w
    mov     word [sbuf+6], ax
    mov     byte [sbuf+8], 0
    mov     byte [sbuf+9], 0
    push    rdi
    push    rsi
    lea     rdi, [sbuf+10]
    mov     ecx, r12d
    rep     movsb
    pop     rsi
    pop     rdi
    push    rdi
    lea     rsi, [sbuf]
    mov     eax, r12d
    add     eax, 10
    mov     edx, eax
    call    sendall
    pop     rdi
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- rxmsg: rdi = fd, esi = ms -> eax paylen (0 timeout/error).
; Message lands in rbuf: hdr at [rbuf], payload at [rbuf+8].
rxmsg:
    push    rbx
    push    r12
    push    r13
    push    r14
    mov     r14d, edi
    mov     r12d, esi
    lea     r13, [rbuf]
    mov     edi, r14d
    mov     esi, r12d
    call    selwait
    test    eax, eax
    jz      .fail
    mov     edi, r14d
    lea     rsi, [rbuf+2040]
    mov     edx, 2
    call    readex
    test    eax, eax
    jz      .fail
    movzx   ebx, word [rbuf+2040]
    cmp     ebx, 8
    jl      .fail
    cmp     ebx, 520
    jg      .fail
    mov     edi, r14d
    lea     rsi, [rbuf]
    mov     edx, ebx
    call    readex
    test    eax, eax
    jz      .fail
    mov     eax, ebx
    sub     eax, 8
    jmp     .out
.fail:
    xor     eax, eax
.out:
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- readex: rdi = fd, rsi = dst, edx = len -> eax 1 ok / 0 timeout|err.
readex:
    push    rbx
    push    r12
    push    r13
    mov     r12, rsi
    mov     r13d, edx
    mov     ebx, edi
.rd:
    test    r13d, r13d
    jz      .ok
    mov     edi, ebx
    mov     esi, 500
    call    selwait
    test    eax, eax
    jz      .fail
    mov     eax, 45
    mov     edi, ebx
    mov     rsi, r12
    movsxd  rdx, r13d
    xor     r10d, r10d
    xor     r8d, r8d
    xor     r9d, r9d
    syscall
    cmp     rax, 0
    jle     .fail
    add     r12, rax
    sub     r13d, eax
    jmp     .rd
.ok:
    mov     eax, 1
    jmp     .out
.fail:
    xor     eax, eax
.out:
    pop     r13
    pop     r12
    pop     rbx
    ret
; -- send_main. --
send_main:
    push    rbx
    push    r12
    push    r13
    push    r14
    mov     rax, 0x123456789ABCDEF1
    mov     [trng], rax
    call    gf_init
    call    build
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
    mov     eax, dword [refs+rcx+rbx*4]
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
    call    tcp_sock
    mov     r12d, eax
    mov     edi, r12d
    call    nodelay
    lea     rdi, [proxyaddr]
    mov     esi, PS_
    call    mkloop
    mov     eax, 42
    mov     edi, r12d
    lea     rsi, [proxyaddr]
    mov     edx, 16
    syscall
    xor     r13d, r13d
.snd:
    cmp     r13d, NP_
    jae     .sndm
    mov     eax, r13d
    shl     eax, 9
    lea     rsi, [bku+rax]
    mov     edi, r12d
    mov     edx, PL_
    mov     cl, 0
    mov     r8b, r13b
    call    txmsg
    inc     r13d
    jmp     .snd
.sndm:
    mov     edi, r12d
    lea     rsi, [metbuf]
    mov     edx, 256
    mov     cl, 1
    xor     r8b, r8b
    call    txmsg
    ; fetch listen on PF
    call    tcp_sock
    mov     r13d, eax
    mov     edi, r13d
    call    nodelay
    mov     edi, r13d
    call    reuse
    lea     rdi, [fetchaddr]
    mov     esi, PF_
    call    mkloop
    mov     eax, 49
    mov     edi, r13d
    lea     rsi, [fetchaddr]
    mov     edx, 16
    syscall
    mov     eax, 50
    mov     edi, r13d
    mov     esi, 4
    syscall
    xor     r12d, r12d               ; served (init BEFORE select:
    mov     edi, r13d                ; timeout path must see 0, not ssnd fd)
    mov     esi, 2000
    call    selwait
    test    eax, eax
    jz      .sdone
    mov     dword [peerlen], 16
    mov     eax, 43
    mov     edi, r13d
    lea     rsi, [peeraddr]
    lea     rdx, [peerlen]
    syscall
    mov     r13d, eax                ; sfs
    mov     edi, r13d
    call    nodelay
.serve:
    cmp     r12d, 8
    jae     .sdone
    mov     edi, r13d
    mov     esi, 1000
    call    rxmsg                    ; whole req message, 1s budget
    test    eax, eax
    jz      .sdone
    cmp     byte [rbuf+2], 4
    jne     .serve
    mov     edi, r13d
    lea     rsi, [parP]
    mov     edx, PL_
    mov     cl, 2
    xor     r8b, r8b
    call    txmsg
    mov     edi, r13d
    lea     rsi, [parQ]
    mov     edx, PL_
    mov     cl, 3
    xor     r8b, r8b
    call    txmsg
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
    pop     r14
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
    call    build
    call    tcp_sock
    mov     r12d, eax                ; listen
    mov     edi, r12d
    call    nodelay
    mov     edi, r12d
    call    reuse
    lea     rdi, [bindaddr]
    mov     esi, PR_
    call    mkloop
    mov     eax, 49
    mov     edi, r12d
    lea     rsi, [bindaddr]
    mov     edx, 16
    syscall
    mov     eax, 50
    mov     edi, r12d
    mov     esi, 4
    syscall
    mov     edi, r12d
    mov     esi, 5000
    call    selwait
    test    eax, eax
    jz      .nobody
    mov     eax, 43
    mov     edi, r12d
    xor     esi, esi
    xor     edx, edx
    syscall
    mov     r12d, eax                ; conn
    mov     edi, r12d
    call    nodelay
    jmp     .coll0
.nobody:
    xor     r13d, r13d               ; got=0
    jmp     .cdone
.coll0:
    xor     eax, eax
    mov     ecx, NP_
    lea     rdi, [haveu]
    rep     stosb
    mov     byte [havem], 0
    xor     r13d, r13d               ; got
    xor     r14d, r14d               ; iters
.coll:
    cmp     r13d, 9
    jae     .cdone
    cmp     r14d, 40
    jae     .cdone
    inc     r14d
    mov     edi, r12d
    mov     esi, 500
    call    rxmsg
    test    eax, eax
    jz      .coll
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
    mov     ecx, PL_
    rep     movsb
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
    xor     ebx, ebx
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
    xor     r12d, r12d
    xor     r13d, r13d
    cmp     byte [havem], 0
    je      .vout
    cmp     r14d, 1
    jl      .vout
    cmp     r14d, 2
    jg      .vout
    mov     r13d, 1
    call    tcp_sock
    mov     ebx, eax
    mov     edi, ebx
    call    nodelay
    lea     rdi, [fetchaddr]
    mov     esi, PF_
    call    mkloop
    mov     eax, 42
    mov     edi, ebx
    lea     rsi, [fetchaddr]
    mov     edx, 16
    syscall
    mov     edi, ebx
    lea     rsi, [freqb]
    mov     edx, 1
    mov     cl, 4
    xor     r8b, r8b
    call    txmsg
    mov     edi, ebx
    mov     esi, 500
    call    rxmsg
    test    eax, eax
    jz      .vout
    cmp     byte [rbuf+2], 2
    jne     .vout
    lea     rsi, [rbuf+8]
    lea     rdi, [fPb]
    mov     ecx, PL_
    rep     movsb
    mov     edi, ebx
    mov     esi, 500
    call    rxmsg
    test    eax, eax
    jz      .vout
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
    sub     rsp, 32                 ; sigaction struct
    mov     qword [rsp], 1          ; SIG_IGN
    mov     qword [rsp+8], 0
    mov     qword [rsp+16], 0
    mov     qword [rsp+24], 0
    mov     eax, 13                 ; rt_sigaction
    mov     edi, 13                 ; SIGPIPE
    mov     rsi, rsp
    xor     edx, edx
    mov     r10d, 8
    syscall
    add     rsp, 32
    pop     rax
    cmp     rax, 2
    jl      .usage
    mov     rax, [rsp+8]
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
USEMSG db 'usage: tcp_node send|recv', 10
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
sbuf rb 530
rbuf rb 2048
metbuf rb 256
pqcat rb 1024
fPb rb 512
fQb rb 512
freqb rb 1
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

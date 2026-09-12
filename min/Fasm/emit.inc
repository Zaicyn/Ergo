; emit.inc -- shared decimal/format/emit + misc helpers (single source).
; Include after `segment readable executable` (any position there).
; Self-contained except BSS contract (driver provides, exact names;
; sizes fit the driver's own output volume):
;   outbuf rb N, outcur rq 1, numbuf rb 32,
;   fdigits rb 8, tsbuf rq 2.  Ends in executable.
; Users: sq2b, sqm, sqw, sq5, sq4, sqfh, phase2, trit (all verified
; byte-identical sources; sqw/phase2/trit `ocur` unified to outcur).
segment readable

TEN10 dq 0x4024000000000000       ; 10.0 exact
DBL_0 dq 0                         ; +0.0

segment readable executable


; -- emit_str: rsi = ptr, rdx = len → appends to outbuf --
emit_str:
    mov     rax, [outcur]
    lea     rdi, [outbuf+rax]
    mov     rcx, rdx
    rep     movsb
    mov     rax, rdi
    sub     rax, outbuf
    mov     [outcur], rax
    ret

; -- emit_u64: rax = value → decimal --


; -- emit_u64: rax = value → decimal --
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
    div     rcx                     ; rdx:rax / 10
    add     dl, '0'
    dec     rdi
    mov     [rdi], dl
    test    rax, rax
    jnz     .dig
.out:
    mov     rsi, rdi
    lea     rdx, [numbuf+31]
    sub     rdx, rsi
    jmp     emit_str                ; tail call

; -- emit_f6: xmm0 = double >= 0 → "d.dddddd" (correctly rounded) --
; Digit extraction is exact for the magnitudes printed here
; (ratios in [0,10)); one guard digit + sticky, round-half-even.


; -- emit_f6: xmm0 = double >= 0 → "d.dddddd" (correctly rounded) --
; Digit extraction is exact for the magnitudes printed here
; (ratios in [0,10)); one guard digit + sticky, round-half-even.
emit_f6:
    push    rbx
    cvttsd2si r8, xmm0              ; int part
    cvtsi2sd xmm1, r8
    subsd   xmm0, xmm1              ; frac
    xor     ecx, ecx                ; digit index 0..6
.dig_loop:
    mulsd   xmm0, [TEN10]
    cvttsd2si eax, xmm0
    mov     [fdigits+rcx], al
    cvtsi2sd xmm1, eax
    subsd   xmm0, xmm1
    inc     ecx
    cmp     ecx, 7
    jne     .dig_loop
    xor     ecx, ecx
    ucomisd xmm0, [DBL_0]
    setnz   cl                      ; sticky
    mov     al, [fdigits+6]         ; guard digit
    cmp     al, 5
    ja      .carry
    jb      .print
    test    ecx, ecx
    jnz     .carry
    test    byte [fdigits+5], 1     ; half-even
    jz      .print
.carry:
    mov     ecx, 5
.carry_loop:
    inc     byte [fdigits+rcx]
    cmp     byte [fdigits+rcx], 10
    jb      .print
    mov     byte [fdigits+rcx], 0
    dec     ecx
    jns     .carry_loop
    inc     r8                      ; carried past d1
.print:
    mov     rax, r8
    call    emit_u64
    mov     rax, [outcur]
    mov     byte [outbuf+rax], '.'
    inc     qword [outcur]
    mov     rax, [outcur]
    lea     rdi, [outbuf+rax]
    xor     ecx, ecx
.copy_loop:
    mov     al, [fdigits+rcx]
    add     al, '0'
    mov     [rdi+rcx], al
    inc     ecx
    cmp     ecx, 6
    jne     .copy_loop
    add     qword [outcur], 6
    pop     rbx
    ret

; -- ratio_f6: rax = num (signed 64), rdx = den → xmm0 = num/den or 0.0 --


; -- emit_fdec: xmm0 = double >= 0, ecx = decimals (2 or 6) --
; Correctly-rounded decimal output: N+1 guard digits + sticky,
; round-half-even. Exact for the benign ratios printed here.
emit_fdec:
    push    rbx
    mov     r8d, ecx                ; N
    cvttsd2si r9, xmm0              ; int part
    cvtsi2sd xmm1, r9
    subsd   xmm0, xmm1              ; frac
    xor     ecx, ecx
.dig_loop:
    mulsd   xmm0, [TEN10]
    cvttsd2si eax, xmm0
    mov     [fdigits+rcx], al
    cvtsi2sd xmm1, eax
    subsd   xmm0, xmm1
    inc     ecx
    cmp     ecx, r8d
    jbe     .dig_loop               ; digits 0..N
    xor     ecx, ecx
    ucomisd xmm0, [DBL_0]
    setnz   cl                      ; sticky
    mov     eax, r8d                ; guard = d[N]
    mov     dl, [fdigits+rax]
    cmp     dl, 5
    ja      .carry
    jb      .print
    test    ecx, ecx
    jnz     .carry
    dec     eax                     ; d[N-1] odd ?
    test    byte [fdigits+rax], 1
    jz      .print
.carry:
    mov     ecx, r8d
    dec     ecx                     ; start at d[N-1]
.carry_loop:
    inc     byte [fdigits+rcx]
    cmp     byte [fdigits+rcx], 10
    jb      .print
    mov     byte [fdigits+rcx], 0
    dec     ecx
    jns     .carry_loop
    inc     r9                      ; carried past d0
.print:
    mov     rax, r9
    call    emit_u64
    mov     rax, [outcur]
    mov     byte [outbuf+rax], '.'
    inc     qword [outcur]
    mov     rax, [outcur]
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
    add     [outcur], rax
    pop     rbx
    ret


; -- ratio_f6: rax = num (signed 64), rdx = den → xmm0 = num/den or 0.0 --
ratio_f6:
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

; -- atoi: rsi = string → eax (C atoi semantics, no overflow concern) --


; -- ratio_fx: rax = num (signed 64), rdx = den -> xmm0 = num/den or 0.0 --
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


; -- atoi: rsi = string → eax (C atoi semantics, no overflow concern) --
atoi:
    xor     eax, eax
    xor     ecx, ecx                ; sign 0/1
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

; -- _start --


; -- wallns: -> rax = CLOCK_MONOTONIC ns (timing only) --
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

; -- mkconst: rdi = dst, esi = num, edx = den -> [dst] = num/den --
; Single correctly-rounded division = identical to a C decimal literal.


; -- cycles: -> rax = serialized rdtsc --
cycles:
    xor     eax, eax
    cpuid
    rdtsc
    shl     rdx, 32
    or      rax, rdx
    ret


; -- mem_eq: rdi, rsi, ecx = len -> eax 0/1 (== memcmp(...)==0) --
mem_eq:
    test    ecx, ecx
    jz      .eq
    repe    cmpsb
    sete    al
    movzx   eax, al
    ret
.eq:
    mov     eax, 1
    ret

; -- mem_cpy: rdi = dst, rsi = src, ecx = len --


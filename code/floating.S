.global _start
.text
_start:
 fmov d0, #1.0
 fmov d1, #1.0
 fmov d2, #1.0
 fmov d3, #1.0
 fmov d4, #1.0
 fmov d5, #1.0
 fmov d6, #1.0
 fmov d7, #1.0
 fmov d16, #0.5
 mov x20, #1000
loop:
 fadd d0, d0, d16
 fadd d1, d1, d16
 fadd d2, d2, d16
 fadd d3, d3, d16
 fadd d4, d4, d16
 fadd d5, d5, d16
 fadd d6, d6, d16
 fadd d7, d7, d16
 fadd d0, d0, d16
 fadd d1, d1, d16
 fadd d2, d2, d16
 fadd d3, d3, d16
 fadd d4, d4, d16
 fadd d5, d5, d16
 fadd d6, d6, d16
 fadd d7, d7, d16
 fadd d0, d0, d16
 fadd d1, d1, d16
 fadd d2, d2, d16
 fadd d3, d3, d16
 fadd d4, d4, d16
 fadd d5, d5, d16
 fadd d6, d6, d16
 fadd d7, d7, d16
 fadd d0, d0, d16
 fadd d1, d1, d16
 fadd d2, d2, d16
 fadd d3, d3, d16
 fadd d4, d4, d16
 fadd d5, d5, d16
 fadd d6, d6, d16
 fadd d7, d7, d16
 subs x20, x20, #1
 b.ne loop

 mov x0, #0
 mov x8, #93
 svc #0

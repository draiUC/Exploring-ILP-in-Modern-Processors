.global _start
.text
_start:
 mov x1, #0
 mov x20, #1000
loop:
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 add x1, x1, #1
 subs x20, x20, #1
 b.ne loop

 mov x0, #0
 mov x8, #93
 svc #0

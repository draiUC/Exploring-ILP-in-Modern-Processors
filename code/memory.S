.global _start
.text
_start:
 adr x10, data
 mov x1, #0
 mov x20, #1000
loop:
 ldr x1, [x10, #0]
 ldr x2, [x10, #64]
 ldr x3, [x10, #128]
 ldr x4, [x10, #192]
 ldr x5, [x10, #256]
 ldr x6, [x10, #320]
 ldr x7, [x10, #384]
 ldr x8, [x10, #448]
 ldr x1, [x10, #0]
 ldr x2, [x10, #64]
 ldr x3, [x10, #128]
 ldr x4, [x10, #192]
 ldr x5, [x10, #256]
 ldr x6, [x10, #320]
 ldr x7, [x10, #384]
 ldr x8, [x10, #448]
 ldr x1, [x10, #0]
 ldr x2, [x10, #64]
 ldr x3, [x10, #128]
 ldr x4, [x10, #192]
 ldr x5, [x10, #256]
 ldr x6, [x10, #320]
 ldr x7, [x10, #384]
 ldr x8, [x10, #448]
 ldr x1, [x10, #0]
 ldr x2, [x10, #64]
 ldr x3, [x10, #128]
 ldr x4, [x10, #192]
 ldr x5, [x10, #256]
 ldr x6, [x10, #320]
 ldr x7, [x10, #384]
 ldr x8, [x10, #448]
 subs x20, x20, #1
 b.ne loop

 mov x0, #0
 mov x8, #93
 svc #0

.data
.balign 64
data:
.rept 64
 .quad 1
.endr

.global _start
.text
_start:
 mov x1, #1
 mov x2, #0
 mov x3, #0
 mov x20, #1000
loop:
 eor x1, x1, x1, lsl #13
 eor x1, x1, x1, lsr #7
 eor x1, x1, x1, lsl #17
 tbz x1, #0, skip0
 add x2, x2, #1
 b done0
skip0:
 add x3, x3, #1
done0:
 eor x1, x1, x1, lsl #13
 eor x1, x1, x1, lsr #7
 eor x1, x1, x1, lsl #17
 tbz x1, #0, skip1
 add x2, x2, #1
 b done1
skip1:
 add x3, x3, #1
done1:
 eor x1, x1, x1, lsl #13
 eor x1, x1, x1, lsr #7
 eor x1, x1, x1, lsl #17
 tbz x1, #0, skip2
 add x2, x2, #1
 b done2
skip2:
 add x3, x3, #1
done2:
 eor x1, x1, x1, lsl #13
 eor x1, x1, x1, lsr #7
 eor x1, x1, x1, lsl #17
 tbz x1, #0, skip3
 add x2, x2, #1
 b done3
skip3:
 add x3, x3, #1
done3:
 subs x20, x20, #1
 b.ne loop

 mov x0, #0
 mov x8, #93
 svc #0

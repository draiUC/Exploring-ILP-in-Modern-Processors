.global _start
.text
_start:
 adr x10, node0
 mov x20, #1000
loop:
 ldr x10, [x10]
 ldr x10, [x10]
 ldr x10, [x10]
 ldr x10, [x10]
 subs x20, x20, #1
 b.ne loop

 mov x0, #0
 mov x8, #93
 svc #0

.data
.balign 4096
node0:
 .quad node1
 .space 4088
node1:
 .quad node2
 .space 4088
node2:
 .quad node3
 .space 4088
node3:
 .quad node4
 .space 4088
node4:
 .quad node5
 .space 4088
node5:
 .quad node6
 .space 4088
node6:
 .quad node7
 .space 4088
node7:
 .quad node8
 .space 4088
node8:
 .quad node9
 .space 4088
node9:
 .quad node10
 .space 4088
node10:
 .quad node11
 .space 4088
node11:
 .quad node12
 .space 4088
node12:
 .quad node13
 .space 4088
node13:
 .quad node14
 .space 4088
node14:
 .quad node15
 .space 4088
node15:
 .quad node16
 .space 4088
node16:
 .quad node17
 .space 4088
node17:
 .quad node18
 .space 4088
node18:
 .quad node19
 .space 4088
node19:
 .quad node20
 .space 4088
node20:
 .quad node21
 .space 4088
node21:
 .quad node22
 .space 4088
node22:
 .quad node23
 .space 4088
node23:
 .quad node24
 .space 4088
node24:
 .quad node25
 .space 4088
node25:
 .quad node26
 .space 4088
node26:
 .quad node27
 .space 4088
node27:
 .quad node28
 .space 4088
node28:
 .quad node29
 .space 4088
node29:
 .quad node30
 .space 4088
node30:
 .quad node31
 .space 4088
node31:
 .quad node32
 .space 4088
node32:
 .quad node33
 .space 4088
node33:
 .quad node34
 .space 4088
node34:
 .quad node35
 .space 4088
node35:
 .quad node36
 .space 4088
node36:
 .quad node37
 .space 4088
node37:
 .quad node38
 .space 4088
node38:
 .quad node39
 .space 4088
node39:
 .quad node40
 .space 4088
node40:
 .quad node41
 .space 4088
node41:
 .quad node42
 .space 4088
node42:
 .quad node43
 .space 4088
node43:
 .quad node44
 .space 4088
node44:
 .quad node45
 .space 4088
node45:
 .quad node46
 .space 4088
node46:
 .quad node47
 .space 4088
node47:
 .quad node48
 .space 4088
node48:
 .quad node49
 .space 4088
node49:
 .quad node50
 .space 4088
node50:
 .quad node51
 .space 4088
node51:
 .quad node52
 .space 4088
node52:
 .quad node53
 .space 4088
node53:
 .quad node54
 .space 4088
node54:
 .quad node55
 .space 4088
node55:
 .quad node56
 .space 4088
node56:
 .quad node57
 .space 4088
node57:
 .quad node58
 .space 4088
node58:
 .quad node59
 .space 4088
node59:
 .quad node60
 .space 4088
node60:
 .quad node61
 .space 4088
node61:
 .quad node62
 .space 4088
node62:
 .quad node63
 .space 4088
node63:
 .quad node64
 .space 4088
node64:
 .quad node65
 .space 4088
node65:
 .quad node66
 .space 4088
node66:
 .quad node67
 .space 4088
node67:
 .quad node68
 .space 4088
node68:
 .quad node69
 .space 4088
node69:
 .quad node70
 .space 4088
node70:
 .quad node71
 .space 4088
node71:
 .quad node72
 .space 4088
node72:
 .quad node73
 .space 4088
node73:
 .quad node74
 .space 4088
node74:
 .quad node75
 .space 4088
node75:
 .quad node76
 .space 4088
node76:
 .quad node77
 .space 4088
node77:
 .quad node78
 .space 4088
node78:
 .quad node79
 .space 4088
node79:
 .quad node80
 .space 4088
node80:
 .quad node81
 .space 4088
node81:
 .quad node82
 .space 4088
node82:
 .quad node83
 .space 4088
node83:
 .quad node84
 .space 4088
node84:
 .quad node85
 .space 4088
node85:
 .quad node86
 .space 4088
node86:
 .quad node87
 .space 4088
node87:
 .quad node88
 .space 4088
node88:
 .quad node89
 .space 4088
node89:
 .quad node90
 .space 4088
node90:
 .quad node91
 .space 4088
node91:
 .quad node92
 .space 4088
node92:
 .quad node93
 .space 4088
node93:
 .quad node94
 .space 4088
node94:
 .quad node95
 .space 4088
node95:
 .quad node96
 .space 4088
node96:
 .quad node97
 .space 4088
node97:
 .quad node98
 .space 4088
node98:
 .quad node99
 .space 4088
node99:
 .quad node100
 .space 4088
node100:
 .quad node101
 .space 4088
node101:
 .quad node102
 .space 4088
node102:
 .quad node103
 .space 4088
node103:
 .quad node104
 .space 4088
node104:
 .quad node105
 .space 4088
node105:
 .quad node106
 .space 4088
node106:
 .quad node107
 .space 4088
node107:
 .quad node108
 .space 4088
node108:
 .quad node109
 .space 4088
node109:
 .quad node110
 .space 4088
node110:
 .quad node111
 .space 4088
node111:
 .quad node112
 .space 4088
node112:
 .quad node113
 .space 4088
node113:
 .quad node114
 .space 4088
node114:
 .quad node115
 .space 4088
node115:
 .quad node116
 .space 4088
node116:
 .quad node117
 .space 4088
node117:
 .quad node118
 .space 4088
node118:
 .quad node119
 .space 4088
node119:
 .quad node120
 .space 4088
node120:
 .quad node121
 .space 4088
node121:
 .quad node122
 .space 4088
node122:
 .quad node123
 .space 4088
node123:
 .quad node124
 .space 4088
node124:
 .quad node125
 .space 4088
node125:
 .quad node126
 .space 4088
node126:
 .quad node127
 .space 4088
node127:
 .quad node0
 .space 4088
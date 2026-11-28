# Fixed benign guest media probe; GNU as --32, ld -m elf_i386 -Ttext 0x7c00 --oformat binary.
# The Python fixture adds a second sector containing 0x1234 and zero padding.
.code16
.section .text
.global _start
_start:
 cli
 xor %ax,%ax
 mov %ax,%ds
 mov %ax,%es
 mov %ax,%ss
 mov $0x7c00,%sp
 sti
 cld
 mov %dl,drive
 call read_sector
 jc fail
 cmpw $0x1234,0x0600
 jne fail
 movw $0x5678,0x0600
 mov $0x0301,%ax
 call disk
 jnc fail
 call read_sector
 jc fail
 cmpw $0x1234,0x0600
 jne fail
 mov $success,%si
 jmp emit
fail:
 mov $failure,%si
emit:
 lodsb
 test %al,%al
 jz halt
 out %al,$0xe9
 jmp emit
halt:
 cli
 hlt
 jmp halt
read_sector:
 mov $0x0201,%ax
disk:
 mov $0x0600,%bx
 mov $0x0002,%cx
 xor %dx,%dx
 mov drive,%dl
 int $0x13
 ret
drive: .byte 0
success: .asciz "DTT_VM_READ_OK_WRITE_DENIED\n"
failure: .asciz "DTT_VM_PROBE_FAILED\n"
.org 510
.word 0xaa55

from gbemu.cpu import CPU
from gbemu.mmu import MMU

if __name__ == "__main__":
    cpu = CPU(MMU())
    # ("BC", "A", 0x1234, 0x2),  # LD [BC], A
    opcode = 0x2
    value = 0x1234
    dest = "BC"

    cpu = CPU(MMU())
    top = (value >> 8) & 0xFF
    bottom = value & 0xFF
    cpu.insert_instruction(bytearray([opcode, bottom, top]))
    cpu.cycle()

    print(cpu.reg[dest], value, hex(cpu.reg[dest]), hex(value))

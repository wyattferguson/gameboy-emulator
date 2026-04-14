from gbemu.cpu import CPU
from gbemu.mmu import MMU

if __name__ == "__main__":
    cpu = CPU(MMU())
    # ("BC", "A", 0x1234, 0x2),  # LD [BC], A
    # opcode = 0x2
    value = 0x11
    # dest = "BC"
    # cpu = CPU(MMU())
    # top = (value >> 8) & 0xFF
    # bottom = value & 0xFF
    # cpu.insert_instruction(bytearray([opcode, bottom, top]))
    # cpu.cycle()

    # print(cpu.reg[dest], value, hex(cpu.reg[dest]), hex(value))
    print(f"Value: {value}, {bin(value)}, {hex(value)}")

    carry: int = (value >> 7) & 0x1
    x = ((value << 1) | carry) & 0xFF
    print(f"Result: {x}, {bin(x)}, {hex(x)}, Carry: {carry}")

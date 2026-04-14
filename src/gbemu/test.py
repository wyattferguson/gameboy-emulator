from gbemu.cpu import CPU
from gbemu.mmu import MMU

if __name__ == "__main__":
    cpu = CPU(MMU())
    opcode = 0x3
    value = 0x00FF
    cpu.reg["BC"] = value
    print(hex(cpu.reg["BC"]), hex(cpu.reg["B"]), hex(cpu.reg["C"]))
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()
    print(hex(cpu.reg["BC"]), hex(cpu.reg["B"]), hex(cpu.reg["C"]))

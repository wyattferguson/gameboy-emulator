from gbemu.cpu import CPU
from gbemu.mmu import MMU

if __name__ == "__main__":
    cpu = CPU(MMU())
    opcode = 0x1
    value = 0x1234
    bottom = (value >> 8) & 0xFF
    top = value & 0xFF
    cpu.insert_instruction(bytearray([opcode, top, bottom]))
    cpu.cycle()
    top = cpu.pc + 3
    # print(
    #     cpu.mmu[cpu.pc : top],
    #     f": {[hex(b) for b in instruction]} at {hex(cpu.pc)}",
    # )

    print(hex(cpu.reg["BC"]), hex(cpu.reg["B"]), hex(cpu.reg["C"]))

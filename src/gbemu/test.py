from gbemu.cpu import CPU
from gbemu.mmu import MMU

if __name__ == "__main__":
    cpu = CPU(MMU())
    cpu.reg["H"] = 0x34
    cpu.reg["L"] = 0x56

    print(hex(cpu.reg["HL"]), hex(cpu.reg["H"]), hex(cpu.reg["L"]))

    cpu.reg["HL"] = 0x12CD
    print(hex(cpu.reg["HL"]), hex(cpu.reg["H"]), hex(cpu.reg["L"]))

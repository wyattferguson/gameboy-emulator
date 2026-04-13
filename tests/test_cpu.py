from gbemu.cpu import CPU
from gbemu.mmu import MMU


def test_cpu_register_access() -> None:
    cpu = CPU(MMU())

    cpu.reg["A"] = 0x12
    cpu.reg["H"] = 0x34
    cpu.reg["L"] = 0x56

    assert cpu.reg["A"] == 0x12
    assert cpu.reg["HL"] == 0x3456
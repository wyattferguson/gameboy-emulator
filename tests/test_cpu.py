from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.opcodes import OPCODES


def test_cpu_register_access() -> None:
    cpu = CPU(MMU())

    cpu.reg["A"] = 0x12
    cpu.reg["H"] = 0x34
    cpu.reg["L"] = 0x56

    assert cpu.reg["A"] == 0x12
    assert cpu.reg["HL"] == 0x3456


def test_decode_does_not_mutate_shared_opcode_args() -> None:
    opcode = OPCODES["0x36"]
    cpu = CPU(MMU())
    cpu.reg["HL"] = 0x1234
    cpu.insert_instruction(bytearray([0x36, 0x12]))

    cpu.fetch()
    cpu.decode()

    assert opcode.args == ["HL"]
    assert cpu.args == ["HL", 0x12]

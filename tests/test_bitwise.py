import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.opcodes import OPCODES


@pytest.mark.parametrize(
    (
        "a_value",
        "register",
        "value",
        "z_flag",
        "h_flag",
        "result",
        "opcode",
    ),
    [
        (0x12, "B", 0x34, 0, 1, 0x10, 0xA0),  # AND A -> B
        (0x00, "B", 0xDD, 1, 1, 0x00, 0xA0),
        (0xFF, "B", 0xDD, 0, 1, 0xDD, 0xA0),
        (0x0F, "HL", 0xF0, 1, 1, 0x00, 0xA6),  # AND A -> [HL]
        (0x12, "B", 0x34, 0, 0, 0x26, 0xA8),  # XOR A -> B
        (0xCC, "B", 0xCC, 1, 0, 0x00, 0xA8),
        (0xFF, "HL", 0xDD, 0, 0, 0x22, 0xAE),  # XOR A -> [HL]
        (0x12, "B", 0x34, 0, 0, 0x36, 0xB0),  # OR A -> B
        (0xCC, "B", 0xCC, 0, 0, 0xCC, 0xB0),
        (0xBC, "B", 0x00, 0, 0, 0xBC, 0xB0),
        (0xFF, "HL", 0xDD, 0, 0, 0xFF, 0xB6),  # OR A -> [HL]
        (0x3D, "HL", 0x05, 0, 0, 0x3D, 0xB6),
    ],
)
def test_bitwise(
    a_value: int,
    register: str,
    value: int,
    z_flag: int,
    h_flag: int,
    result: int,
    opcode: int,
) -> None:
    cpu = CPU(MMU())
    cpu.reg["A"] = a_value
    if register == "HL":
        cpu.mmu[cpu.reg["HL"]] = value
    else:
        cpu.reg[register] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg["A"] == result
    assert cpu.flags["Z"] == z_flag
    assert cpu.flags["N"] == 0
    assert cpu.flags["H"] == h_flag
    assert cpu.flags["C"] == 0

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
        "c_flag",
        "opcode",
    ),
    [
        (0x12, "B", 0x34, 0, 1, 1, 0xB8),  # CP A -> B
        (0xDE, "C", 0xDE, 1, 0, 0, 0xB9),  # CP A -> C
        (0x21, "D", 0x20, 0, 0, 0, 0xBA),  # CP A -> D
        (0x01, "E", 0xFF, 0, 1, 1, 0xBB),  # CP A -> E
        (0xFF, "H", 0xFF, 1, 0, 0, 0xBC),  # CP A -> H
        (0x00, "L", 0x00, 1, 0, 0, 0xBD),  # CP A -> L
        (0x7E, "HL", 0x7F, 0, 1, 1, 0xBE),  # CP A -> [HL]
        (0x80, "HL", 0x7F, 0, 1, 0, 0xBE),  # CP A -> [HL] with borrow
        (0x7F, "HL", 0x80, 0, 0, 1, 0xBE),  # CP A -> [HL] with carry
        (0x80, "HL", 0x80, 1, 0, 0, 0xBE),  # CP A -> [HL] with zero result
    ],
)
def test_cp(
    a_value: int,
    register: str,
    value: int,
    z_flag: int,
    h_flag: int,
    c_flag: int,
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

    assert cpu.flags["Z"] == z_flag
    assert cpu.flags["N"] == 1
    assert cpu.flags["H"] == h_flag
    assert cpu.flags["C"] == c_flag

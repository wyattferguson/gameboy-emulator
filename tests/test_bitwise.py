import pytest

from gbemu.cpu import CPU
from gbemu.opcodes import OPCODES, OpCode
from tests.conftest import RAM


@pytest.mark.parametrize(
    (
        "a_value",
        "register",
        "value",
        "z_flag",
        "result",
        "opcode",
    ),
    [
        (0x12, "B", 0x34, 0, 0x10, 0xA0),  # AND A -> B
        (0x00, "B", 0xDD, 1, 0x00, 0xA0),
        (0xFF, "B", 0xDD, 0, 0xDD, 0xA0),
        (0x0F, "HL", 0xF0, 1, 0x00, 0xA6),
    ],
)
def test_and(
    a_value: int,
    register: str,
    value: int,
    z_flag: int,
    result: int,
    opcode: int,
) -> None:
    cpu = CPU(RAM())
    cpu.reg["A"] = a_value
    if register == "HL":
        cpu.ram[cpu.hl] = value
    else:
        cpu.reg[register] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.instruction == OPCODES[f"0x{opcode:x}"]
    assert cpu.reg["A"] == result
    assert cpu.flags["Z"] == z_flag
    assert cpu.flags["N"] == 0
    assert cpu.flags["H"] == 1
    assert cpu.flags["C"] == 0

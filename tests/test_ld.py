import pytest

from gbemu.config import PC_START, SP_START
from gbemu.cpu import CPU
from gbemu.opcodes import OPCODES, OpCode
from tests.conftest import RAM


def test_ld_a_d8() -> None:
    cpu = CPU(RAM())
    cpu.insert_instruction(bytearray([0x3E, 0x42]))  # LD A, d8; d8 = 0x42
    cpu.cycle()

    assert cpu.instruction == OPCODES["0x3e"]
    assert cpu.reg["A"] == 0x42


@pytest.mark.parametrize(
    ("dest", "src", "value", "opcode"),
    [
        ("B", "B", 0x32, 0x40),
        ("B", "C", 0x35, 0x41),
        ("B", "D", 0x37, 0x42),
        ("B", "E", 0x39, 0x43),
        ("B", "H", 0x3B, 0x44),
        ("B", "L", 0x3D, 0x45),
        ("B", "A", 0x3F, 0x47),
        ("C", "B", 0x42, 0x48),
        ("C", "C", 0x45, 0x49),
        ("C", "D", 0x47, 0x4A),
        ("C", "E", 0x49, 0x4B),
        ("C", "H", 0x4B, 0x4C),
        ("C", "L", 0x12, 0x4D),
        ("C", "A", 0x13, 0x4F),
        ("D", "B", 0x15, 0x50),
        ("D", "C", 0x17, 0x51),
        ("D", "D", 0x19, 0x52),
        ("D", "E", 0x1B, 0x53),
        ("D", "H", 0x1D, 0x54),
        ("D", "L", 0x1F, 0x55),
        ("D", "A", 0x21, 0x57),
        ("E", "B", 0x23, 0x58),
        ("E", "C", 0x25, 0x59),
        ("E", "D", 0x27, 0x5A),
        ("E", "E", 0x29, 0x5B),
        ("E", "H", 0x2B, 0x5C),
        ("E", "L", 0x2D, 0x5D),
        ("E", "A", 0x2F, 0x5F),
        ("H", "B", 0x31, 0x60),
        ("H", "C", 0x33, 0x61),
        ("H", "D", 0x35, 0x62),
        ("H", "E", 0x37, 0x63),
        ("H", "H", 0x39, 0x64),
        ("H", "L", 0x3B, 0x65),
        ("H", "A", 0x3D, 0x67),
        ("L", "B", 0x3F, 0x68),
        ("L", "C", 0x41, 0x69),
        ("L", "D", 0x43, 0x6A),
        ("L", "E", 0x45, 0x6B),
        ("L", "H", 0x47, 0x6C),
        ("L", "L", 0x49, 0x6D),
        ("L", "A", 0x4B, 0x6F),
        ("A", "B", 0x23, 0x78),
        ("A", "C", 0x25, 0x79),
        ("A", "D", 0x27, 0x7A),
        ("A", "E", 0x29, 0x7B),
        ("A", "H", 0x2B, 0x7C),
        ("A", "L", 0x2D, 0x7D),
        ("A", "A", 0x2F, 0x7F),
    ],
)
def test_ld_reg(dest: str, src: str, value: int, opcode: int) -> None:
    cpu = CPU(RAM())
    cpu.reg[src] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg[dest] == value


@pytest.mark.parametrize(
    ("dest", "h", "l", "value", "opcode"),
    [
        ("B", 0x12, 0x34, 86, 0x46),
        ("C", 0x12, 0x34, 34, 0x4E),
        ("D", 0x12, 0x34, 56, 0x56),
        ("E", 0x12, 0x34, 11, 0x5E),
        ("H", 0x12, 0x34, 22, 0x66),
        ("L", 0x12, 0x34, 33, 0x6E),
        ("A", 0x22, 0x34, 33, 0x7E),
    ],
)
def test_ld_hl(dest: str, h: int, l: int, value: int, opcode: int) -> None:
    cpu = CPU(RAM())
    hl = (h << 8) + l
    cpu.ram[hl] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.reg["H"] = h
    cpu.reg["L"] = l
    cpu.cycle()

    assert cpu.reg[dest] == value


@pytest.mark.parametrize(
    ("dest", "h", "l", "value", "opcode"),
    [
        ("B", 0x12, 0x34, 86, 0x70),
        ("C", 0x44, 0x22, 34, 0x71),
        ("D", 0x15, 0x12, 56, 0x72),
        ("E", 0x16, 0x34, 11, 0x73),
        ("H", 0x47, 0x18, 22, 0x74),
        ("L", 0x12, 0x34, 33, 0x75),
        ("A", 0x24, 0x35, 33, 0x77),
    ],
)
def test_ld_hl_r(dest: str, h: int, l: int, value: int, opcode: int) -> None:
    cpu = CPU(RAM())
    cpu.reg["H"] = h
    cpu.reg["L"] = l
    cpu.insert_instruction(bytearray([opcode]))
    cpu.reg[dest] = value
    cpu.cycle()

    assert cpu.ram[cpu.hl] == value

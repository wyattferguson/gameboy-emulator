import pytest

from gbemu.config import MEMORY_SIZE, PC_START, SP_START
from gbemu.cpu import CPU
from gbemu.opcodes import OPCODES, OpCode


class RAM:
    def __init__(self) -> None:
        self._memory = [0] * MEMORY_SIZE

    def __getitem__(self, address: int) -> int:
        return self._memory[address]

    def __setitem__(self, address: int, value: int) -> None:
        self._memory[address] = value


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
    ],
)
def test_ld_reg(dest: str, src: str, value: int, opcode: int) -> None:
    cpu = CPU(RAM())
    cpu.reg[src] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.instruction == OPCODES[f"0x{opcode:x}"]
    assert cpu.reg[dest] == value


@pytest.mark.parametrize(
    ("dest", "h", "l", "value", "opcode"),
    [
        ("B", 0x12, 0x34, 86, 0x46),
        ("C", 0x12, 0x34, 34, 0x4E),
    ],
)
def test_ld_hl(dest: str, h: int, l: int, value: int, opcode: int) -> None:
    cpu = CPU(RAM())
    hl = (h << 8) + l
    cpu.ram[hl] = value
    cpu.insert_instruction(bytearray([opcode]))  # LD B, [HL]
    cpu.reg["H"] = h
    cpu.reg["L"] = l
    cpu.cycle()

    assert cpu.instruction == OPCODES[f"0x{opcode:x}"]
    assert cpu.reg[dest] == value

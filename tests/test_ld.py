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
    ],
)
def test_ld_reg(dest: str, src: str, value: int, opcode: int) -> None:
    cpu = CPU(RAM())
    cpu.reg[src] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.instruction == OPCODES[f"0x{opcode:x}"]
    assert cpu.reg[dest] == value

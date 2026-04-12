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

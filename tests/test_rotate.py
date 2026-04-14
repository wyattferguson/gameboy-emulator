import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.opcodes import OPCODES, OpCode
from tests.helper import verify_flags


@pytest.mark.parametrize(
    ("dest", "value", "c_flag", "result", "opcode"),
    [
        ("A", 0x11, 0, 0x22, 0x7),  # RLCA
        ("A", 0xFF, 1, 0xFF, 0x7),  # RLCA with carry
    ],
)
def test_rot(dest: str, value: int, c_flag: int, result: int, opcode: int) -> None:
    cpu = CPU(MMU())
    cpu.reg[dest] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg[dest] == result
    verify_flags(cpu, c_flag=c_flag)

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
        ("A", 0x11, 1, 0x88, 0xF),  # RRCA
        ("A", 0xFE, 0, 0x7F, 0xF),  # RRCA without carry
    ],
)
def test_rot_circular(dest: str, value: int, c_flag: int, result: int, opcode: int) -> None:
    cpu = CPU(MMU())
    cpu.reg[dest] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg[dest] == result
    verify_flags(cpu, c_flag=c_flag)


@pytest.mark.parametrize(
    ("dest", "value", "start_c_flag", "c_flag", "result", "opcode"),
    [
        ("A", 0x11, 0, 0, 0x22, 0x17),  # RLA
        ("A", 0xFF, 1, 1, 0xFF, 0x17),  # RLA start carry 1
        ("A", 0x56, 0, 0, 0xAC, 0x17),  # RLA start carry 0
        ("A", 0x78, 1, 0, 0xF1, 0x17),  # RLA no carry
        ("A", 0x11, 0, 1, 0x08, 0x1F),  # RRA start carry 0
        ("A", 0xFF, 1, 1, 0xFF, 0x1F),  # RRA start carry 1
        ("A", 0x56, 0, 0, 0x2B, 0x1F),  # RRA without carry-in
        ("A", 0x78, 1, 0, 0xBC, 0x1F),  # RRA with carry-in
    ],
)
def test_rot_carry(
    dest: str,
    value: int,
    start_c_flag: int,
    c_flag: int,
    result: int,
    opcode: int,
) -> None:
    cpu = CPU(MMU())
    cpu.reg[dest] = value
    cpu.flags["C"] = start_c_flag
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg[dest] == result
    verify_flags(cpu, c_flag=c_flag)

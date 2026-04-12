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


@pytest.mark.parametrize(
    (
        "dest",
        "src",
        "dest_val",
        "src_val",
        "carry",
        "z_flag",
        "n_flag",
        "h_flag",
        "c_flag",
        "result",
        "opcode",
    ),
    [
        ("A", "B", 0x12, 0x34, 0, 0, 0, 0, 0, 0x46, 0x80),
        ("A", "B", 0x0, 0x0, 0, 1, 0, 0, 0, 0x0, 0x80),
        ("A", "B", 0x1D, 0x11, 0, 0, 0, 0, 0, 0x2E, 0x80),
        ("A", "B", 0x4F, 0x15, 0, 0, 0, 1, 0, 0x64, 0x80),
        ("A", "B", 0xFF, 0xFF, 0, 0, 0, 1, 1, 0xFE, 0x80),
        ("A", "A", 0x11, 0x11, 0, 0, 0, 0, 0, 0x22, 0x87),
        ("A", "B", 0xFF, 0xFF, 0, 0, 0, 1, 1, 0xFE, 0x88),  # ADC A, B with carry
        ("A", "B", 0xFF, 0xFF, 1, 0, 0, 1, 1, 0xFF, 0x88),  # ADC A, B with carry
    ],
)
def test_add(
    dest: int,
    src: int,
    dest_val: int,
    src_val: int,
    carry: int,
    z_flag: int,
    n_flag: int,
    h_flag: int,
    c_flag: int,
    result: int,
    opcode: int,
) -> None:
    cpu = CPU(RAM())
    cpu.reg[dest] = dest_val
    cpu.reg[src] = src_val
    cpu.flags["C"] = carry
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.instruction == OPCODES[f"0x{opcode:x}"]
    assert cpu.reg[dest] == result
    assert cpu.flags["Z"] == z_flag
    assert cpu.flags["N"] == n_flag
    assert cpu.flags["H"] == h_flag
    assert cpu.flags["C"] == c_flag


@pytest.mark.parametrize(
    (
        "dest",
        "dest_val",
        "h",
        "l",
        "value",
        "carry",
        "z_flag",
        "n_flag",
        "h_flag",
        "c_flag",
        "result",
        "opcode",
    ),
    [
        ("A", 0x01, 0x12, 0x34, 0x02, 0, 0, 0, 0, 0, 0x03, 0x86),
        ("A", 0x1F, 0x12, 0x34, 0x1C, 0, 0, 0, 1, 0, 0x3B, 0x86),
        ("A", 0xFF, 0x12, 0x34, 0x0F, 0, 0, 0, 1, 1, 0x0E, 0x86),
        ("A", 0xFF, 0x12, 0x34, 0x0F, 1, 0, 0, 1, 1, 0x0F, 0x8E),  # ADC A, [HL] with carry
        ("A", 0x3F, 0x12, 0x34, 0x0F, 1, 0, 0, 1, 0, 0x4F, 0x8E),  # ADC A, [HL] with carry
    ],
)
def test_add_hl(
    dest: str,
    dest_val: int,
    h: int,
    l: int,
    value: int,
    carry: int,
    z_flag: int,
    n_flag: int,
    h_flag: int,
    c_flag: int,
    result: int,
    opcode: int,
) -> None:
    cpu = CPU(RAM())
    cpu.reg[dest] = dest_val
    cpu.reg["H"] = h
    cpu.reg["L"] = l
    cpu.flags["C"] = carry
    cpu.ram[(h << 8) + l] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.instruction == OPCODES[f"0x{opcode:x}"]
    assert cpu.reg[dest] == result
    assert cpu.flags["Z"] == z_flag
    assert cpu.flags["N"] == n_flag
    assert cpu.flags["H"] == h_flag
    assert cpu.flags["C"] == c_flag

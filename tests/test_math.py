import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.opcodes import OPCODES, OpCode


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
        ("A", "B", 0x12, 0x34, 0, 0, 0, 0, 0, 0x46, 0x80),  # ADD A -> B
        ("A", "B", 0x0, 0x0, 0, 1, 0, 0, 0, 0x0, 0x80),
        ("A", "B", 0x1D, 0x11, 0, 0, 0, 0, 0, 0x2E, 0x80),
        ("A", "B", 0x4F, 0x15, 0, 0, 0, 1, 0, 0x64, 0x80),
        ("A", "B", 0xFF, 0xFF, 0, 0, 0, 1, 1, 0xFE, 0x80),
        ("A", "A", 0x11, 0x11, 0, 0, 0, 0, 0, 0x22, 0x87),
        ("A", "B", 0xFF, 0xFF, 0, 0, 0, 1, 1, 0xFE, 0x88),  # ADC A, B with carry
        ("A", "B", 0xFF, 0xFF, 1, 0, 0, 1, 1, 0xFF, 0x88),
        ("A", "B", 0x34, 0x12, 0, 0, 1, 0, 0, 0x22, 0x90),  # SUB A -> B
        ("A", "B", 0x12, 0x34, 0, 0, 1, 1, 1, 0xDE, 0x90),
    ],
)
def test_reg_to_reg(
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
    cpu = CPU(MMU())
    cpu.reg[dest] = dest_val
    cpu.reg[src] = src_val
    cpu.flags["C"] = carry
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

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
        ("A", 0x01, 0x12, 0x34, 0x02, 0, 0, 0, 0, 0, 0x03, 0x86),  # ADD A, [HL]
        ("A", 0x1F, 0x12, 0x34, 0x1C, 0, 0, 0, 1, 0, 0x3B, 0x86),
        ("A", 0xFF, 0x12, 0x34, 0x0F, 0, 0, 0, 1, 1, 0x0E, 0x86),
        ("A", 0xFF, 0x12, 0x34, 0x0F, 1, 0, 0, 1, 1, 0x0F, 0x8E),  # ADC A, [HL] with carry
        ("A", 0x3F, 0x12, 0x34, 0x0F, 1, 0, 0, 1, 0, 0x4F, 0x8E),
        ("A", 0x01, 0x12, 0x34, 0x02, 0, 0, 1, 1, 1, 0xFF, 0x94),  # SUB A, [HL]
        ("A", 0x1F, 0x12, 0x34, 0x1C, 0, 0, 1, 0, 0, 0x03, 0x9C),  # SBC A, [HL] with carry
        ("A", 0x10, 0x12, 0x34, 0x0F, 1, 1, 1, 1, 0, 0x00, 0x9C),
        ("A", 0x65, 0x12, 0x34, 0x23, 1, 0, 1, 0, 0, 0x41, 0x9C),
    ],
)
def test_hl_to_reg(
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
    cpu = CPU(MMU())
    cpu.reg[dest] = dest_val
    cpu.reg["H"] = h
    cpu.reg["L"] = l
    cpu.flags["C"] = carry
    cpu.mmu[(h << 8) + l] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg[dest] == result
    assert cpu.flags["Z"] == z_flag
    assert cpu.flags["N"] == n_flag
    assert cpu.flags["H"] == h_flag
    assert cpu.flags["C"] == c_flag

import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.opcodes import OPCODES
from tests.utils import verify_flags


@pytest.mark.parametrize(
    (
        "a_value",
        "register",
        "value",
        "z_flag",
        "h_flag",
        "result",
        "opcode",
    ),
    [
        (0x12, "B", 0x34, 0, 1, 0x10, 0xA0),  # AND A -> B
        (0x00, "B", 0xDD, 1, 1, 0x00, 0xA0),
        (0xFF, "B", 0xDD, 0, 1, 0xDD, 0xA0),
        (0x0F, "HL", 0xF0, 1, 1, 0x00, 0xA6),  # AND A -> [HL]
        (0x12, "B", 0x34, 0, 0, 0x26, 0xA8),  # XOR A -> B
        (0xCC, "B", 0xCC, 1, 0, 0x00, 0xA8),
        (0xFF, "HL", 0xDD, 0, 0, 0x22, 0xAE),  # XOR A -> [HL]
        (0x12, "B", 0x34, 0, 0, 0x36, 0xB0),  # OR A -> B
        (0xCC, "B", 0xCC, 0, 0, 0xCC, 0xB0),
        (0xBC, "B", 0x00, 0, 0, 0xBC, 0xB0),
        (0xFF, "HL", 0xDD, 0, 0, 0xFF, 0xB6),  # OR A -> [HL]
        (0x3D, "HL", 0x05, 0, 0, 0x3D, 0xB6),
    ],
)
def test_bitwise(
    a_value: int,
    register: str,
    value: int,
    z_flag: int,
    h_flag: int,
    result: int,
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

    assert cpu.reg["A"] == result
    verify_flags(cpu, z_flag, 0, h_flag, 0)


@pytest.mark.parametrize(
    (
        "value",
        "result",
        "opcode",
    ),
    [
        (0x00, 0xFF, 0x2F),  # CPL A
        (0xFF, 0x00, 0x2F),  # CPL A
        (0xAA, 0x55, 0x2F),  # CPL A
        (0x55, 0xAA, 0x2F),  # CPL A
        (0x12, 0xED, 0x2F),  # CPL A
    ],
)
def test_cpl(
    value: int,
    result: int,
    opcode: int,
) -> None:
    cpu = CPU(MMU())
    cpu.reg["A"] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg["A"] == result
    verify_flags(cpu, n_flag=1, h_flag=1)


@pytest.mark.parametrize(
    (
        "c_flag_before",
        "c_flag_after",
        "opcode",
    ),
    [
        (0, 1, 0x3F),  # CCF
        (1, 0, 0x3F),  # CCF
        (0, 1, 0x37),  # SCF
        (1, 1, 0x37),  # SCF
    ],
)
def test_ccf(
    c_flag_before: int,
    c_flag_after: int,
    opcode: int,
) -> None:
    cpu = CPU(MMU())
    cpu.flags["C"] = c_flag_before
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()
    verify_flags(cpu, n_flag=0, h_flag=0, c_flag=c_flag_after)


@pytest.mark.parametrize(
    (
        "a_value",
        "immediate",
        "z_flag",
        "result",
    ),
    [
        (0x12, 0x34, 0, 0x10),  # AND A, d8
        (0x00, 0xDD, 1, 0x00),  # AND A, d8 with zero result
        (0xFF, 0xDD, 0, 0xDD),  # AND A, d8 with all bits
        (0x0F, 0xF0, 1, 0x00),  # AND A, d8 no overlap
        (0xFF, 0xFF, 0, 0xFF),  # AND A, d8 identity
        (0xAA, 0x55, 1, 0x00),  # AND A, d8 alternating bits
        (0xF0, 0x0F, 1, 0x00),  # AND A, d8 no overlap
        (0xF0, 0xF0, 0, 0xF0),  # AND A, d8 same bits
    ],
)
def test_and_immediate(
    a_value: int,
    immediate: int,
    z_flag: int,
    result: int,
) -> None:
    """Test AND A, d8 instruction."""
    cpu = CPU(MMU())
    cpu.reg["A"] = a_value
    cpu.insert_instruction(bytearray([0xE6, immediate]))
    cpu.cycle()

    assert cpu.reg["A"] == result
    verify_flags(cpu, z_flag=z_flag, n_flag=0, h_flag=1, c_flag=0)

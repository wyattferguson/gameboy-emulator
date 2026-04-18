import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.opcodes import OPCODES, OpCode
from tests.utils import set_hl_value, verify_flags


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
        ("A", "B", 0x0, 0x0, 0, 1, 0, 0, 0, 0x0, 0x80),  # ADD A -> B with zero result
        ("A", "B", 0x1D, 0x11, 0, 0, 0, 0, 0, 0x2E, 0x80),  # ADD A -> B with half-carry
        ("A", "B", 0x4F, 0x15, 0, 0, 0, 1, 0, 0x64, 0x80),  # ADD A -> B with carry
        ("A", "B", 0xFF, 0xFF, 0, 0, 0, 1, 1, 0xFE, 0x80),  # ADD A -> B with carry and zero result
        ("A", "A", 0x11, 0x11, 0, 0, 0, 0, 0, 0x22, 0x87),  # ADC A -> A
        ("A", "B", 0xFF, 0xFF, 0, 0, 0, 1, 1, 0xFE, 0x88),  # ADC A, B with carry
        ("A", "B", 0xFF, 0xFF, 1, 0, 0, 1, 1, 0xFF, 0x88),  # ADC A, B with carry
        ("A", "B", 0x34, 0x12, 0, 0, 1, 0, 0, 0x22, 0x90),  # SUB A -> B
        ("A", "B", 0x12, 0x34, 0, 0, 1, 1, 1, 0xDE, 0x90),  # SUB A -> B with borrow
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
    verify_flags(cpu, z_flag, n_flag, h_flag, c_flag)


@pytest.mark.parametrize(
    (
        "dest",
        "dest_val",
        "hl",
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
        ("A", 0x01, 0x1234, 0x02, 0, 0, 0, 0, 0, 0x03, 0x86),  # ADD A, [HL]
        ("A", 0x1F, 0x1234, 0x1C, 0, 0, 0, 1, 0, 0x3B, 0x86),  # ADD A, [HL]
        ("A", 0xFF, 0x1234, 0x0F, 0, 0, 0, 1, 1, 0x0E, 0x86),  # ADD A, [HL]
        ("A", 0xFF, 0x1234, 0x0F, 1, 0, 0, 1, 1, 0x0F, 0x8E),  # ADC A, [HL] w/ carry
        ("A", 0x3F, 0x1234, 0x0F, 1, 0, 0, 1, 0, 0x4F, 0x8E),  # ADC A, [HL] w/ carry
        ("A", 0x01, 0x1234, 0x02, 0, 0, 1, 1, 1, 0xFF, 0x94),  # SUB A, [HL]
        ("A", 0x1F, 0x1234, 0x1C, 0, 0, 1, 0, 0, 0x03, 0x9C),  # SBC A, [HL] w/ carry
        ("A", 0x10, 0x1234, 0x0F, 1, 1, 1, 1, 0, 0x00, 0x9C),
        ("A", 0x65, 0x1234, 0x23, 1, 0, 1, 0, 0, 0x41, 0x9C),
    ],
)
def test_hl_to_reg(
    dest: str,
    dest_val: int,
    hl: int,
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
    cpu.reg["HL"] = hl
    cpu.flags["C"] = carry
    cpu.mmu[hl] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg[dest] == result
    verify_flags(cpu, z_flag, n_flag, h_flag, c_flag)


@pytest.mark.parametrize(
    (
        "dest",
        "value",
        "result",
        "opcode",
    ),
    [
        ("BC", 0x1234, 0x1235, 0x03),  # INC BC
        ("DE", 0xFFFF, 0x0000, 0x13),  # INC DE
        ("HL", 0x00FF, 0x0100, 0x23),  # INC HL
        ("SP", 0xDD11, 0xDD12, 0x33),  # INC SP
    ],
)
def test_inc_16(
    dest: str,
    value: int,
    result: int,
    opcode: int,
) -> None:
    cpu = CPU(MMU())
    cpu.reg[dest] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg[dest] == result


@pytest.mark.parametrize(
    (
        "dest",
        "value",
        "result",
        "z_flag",
        "h_flag",
        "n_flag",
        "opcode",
    ),
    [
        ("B", 0x12, 0x11, 0, 0, 1, 0x05),  # DEC B
        ("B", 0xFF, 0xFE, 0, 0, 1, 0x05),  # DEC B
        ("D", 0x56, 0x55, 0, 0, 1, 0x15),  # DEC D
        ("H", 0x01, 0x00, 1, 1, 1, 0x25),  # DEC H with carry and zero
        ("B", 0x12, 0x13, 0, 0, 0, 0x04),  # INC B
        ("B", 0x1F, 0x20, 0, 1, 0, 0x04),  # INC B with carry
        ("D", 0x56, 0x57, 0, 0, 0, 0x14),  # INC D
        ("H", 0xFF, 0x00, 1, 1, 0, 0x24),  # INC H with carry and zero
        ("BC", 0x1234, 0x1233, 0, 0, 0, 0xB),  # DEC BC
        ("DE", 0x1230, 0x122F, 0, 0, 0, 0x1B),  # DEC DE
        ("HL", 0x1234, 0x1233, 0, 0, 0, 0x2B),  # DEC HL
        ("SP", 0x1234, 0x1233, 0, 0, 0, 0x3B),  # DEC SP
        ("C", 0x56, 0x57, 0, 0, 0, 0xC),  # INC C
        ("E", 0x00, 0x1, 0, 0, 0, 0x1C),  # INC E
        ("L", 0xFF, 0x00, 1, 1, 0, 0x2C),  # INC L with carry and zero
        ("A", 0xFF, 0x00, 1, 1, 0, 0x3C),  # INC A with carry and zero
        ("C", 0x12, 0x11, 0, 0, 1, 0x0D),  # DEC C
        ("E", 0x00, 0xFF, 0, 0, 1, 0x1D),  # DEC E
        ("L", 0x56, 0x55, 0, 0, 1, 0x2D),  # DEC L
        ("A", 0x01, 0x00, 1, 1, 1, 0x3D),  # DEC A with carry and zero
    ],
)
def test_dec_inc_mixed(
    dest: str,
    value: int,
    result: int,
    z_flag: int,
    h_flag: int,
    n_flag: int,
    opcode: int,
) -> None:
    cpu = CPU(MMU())
    cpu.reg[dest] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg[dest] == result
    verify_flags(cpu, z_flag, n_flag, h_flag)


@pytest.mark.parametrize(
    (
        "dest",
        "value",
        "result",
        "z_flag",
        "n_flag",
        "h_flag",
        "opcode",
    ),
    [
        ("HL", 0x11, 0x12, 0, 0, 0, 0x34),  # INC [HL]
        ("HL", 0x0F, 0x10, 0, 0, 1, 0x34),  # INC [HL] with half-carry
        ("HL", 0xFF, 0x00, 1, 0, 1, 0x34),  # INC [HL] with carry and zero
        ("HL", 0xD, 0xC, 0, 1, 0, 0x35),  # DEC [HL]
        ("HL", 0x10, 0x0F, 0, 1, 1, 0x35),  # DEC [HL] with half-borrow
        ("HL", 0x01, 0x00, 1, 1, 0, 0x35),  # DEC [HL] with zero
    ],
)
def test_dec_inc_mem(
    dest: str,
    value: int,
    result: int,
    z_flag: int,
    n_flag: int,
    h_flag: int,
    opcode: int,
) -> None:
    cpu = CPU(MMU())
    set_hl_value(cpu, value)
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.mmu[cpu.reg[dest]] == result
    verify_flags(cpu, z_flag, n_flag, h_flag)


@pytest.mark.parametrize(
    (
        "dest",
        "src",
        "dest_val",
        "src_val",
        "carry",
        "result",
        "opcode",
    ),
    [
        ("HL", "BC", 0x1234, 0x1234, 0, 0x2468, 0x9),  # ADD HL, BC
        ("HL", "BC", 0x1234, 0xF234, 1, 0x468, 0x9),  # ADD HL, BC check carry
        ("HL", "DE", 0x2, 0x1, 0, 0x3, 0x19),  # ADD HL, DE
        ("HL", "HL", 0x0100, 0x0100, 0, 0x0200, 0x29),  # ADD HL, HL
        ("HL", "SP", 0xDD11, 0xDD12, 1, 0xBA23, 0x39),  # ADD HL, SP check carry
    ],
)
def test_add16(
    dest: str,
    src: str,
    dest_val: int,
    src_val: int,
    carry: int,
    result: int,
    opcode: int,
) -> None:
    cpu = CPU(MMU())
    cpu.reg[dest] = dest_val
    cpu.reg[src] = src_val
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg[dest] == result
    verify_flags(cpu, c_flag=carry, n_flag=0)


@pytest.mark.parametrize(
    (
        "a_start",
        "n_start",
        "c_start",
        "result",
        "z_flag",
        "n_flag",
        "c_flag",
    ),
    [
        (0x3C, 0, 0, 0x42, 0, 0, 0),  # lower nibble adjust (+0x06)
        (0x9A, 0, 0, 0x00, 1, 0, 1),  # lower+upper adjust (+0x66)
        (0x15, 0, 1, 0x75, 0, 0, 1),  # carry-in forces upper adjust (+0x60)
        (0x73, 1, 1, 0x13, 0, 1, 1),  # subtraction mode with carry adjust (-0x60)
        (0x1F, 1, 0, 0x19, 0, 1, 0),  # subtraction mode lower nibble adjust (-0x06)
    ],
)
def test_daa(
    a_start: int,
    n_start: int,
    c_start: int,
    result: int,
    z_flag: int,
    n_flag: int,
    c_flag: int,
) -> None:
    cpu = CPU(MMU())
    cpu.reg["A"] = a_start
    cpu.flags["N"] = n_start
    cpu.flags["C"] = c_start
    cpu.insert_instruction(bytearray([0x27]))

    cpu.cycle()

    assert cpu.reg["A"] == result
    verify_flags(cpu, z_flag=z_flag, n_flag=n_flag, h_flag=0, c_flag=c_flag)


@pytest.mark.parametrize(
    (
        "a_val",
        "immediate",
        "carry",
        "z_flag",
        "n_flag",
        "h_flag",
        "c_flag",
        "result",
        "opcode",
    ),
    [
        (0x12, 0x34, 0, 0, 0, 0, 0, 0x46, 0xC6),  # ADD A, d8
        (0x00, 0x00, 0, 1, 0, 0, 0, 0x00, 0xC6),  # ADD A, d8 with zero result
        (0x1D, 0x11, 0, 0, 0, 0, 0, 0x2E, 0xC6),  # ADD A, d8 with no carry
        (0x4F, 0x15, 0, 0, 0, 1, 0, 0x64, 0xC6),  # ADD A, d8 with half-carry
        (0xFF, 0xFF, 0, 0, 0, 1, 1, 0xFE, 0xC6),  # ADD A, d8 with carry
        (0x0F, 0x01, 0, 0, 0, 1, 0, 0x10, 0xC6),  # ADD A, d8 half-carry
        (0x0F, 0xFF, 0, 0, 0, 1, 1, 0x0E, 0xC6),  # ADD A, d8 carry and half-carry
        (0xFF, 0x0F, 1, 0, 0, 1, 1, 0x0F, 0xCE),  # ADC A, d8 with carry
        (0x3F, 0x0F, 1, 0, 0, 1, 0, 0x4F, 0xCE),  # ADC A, d8 with carry
        (0xFF, 0xFF, 0, 0, 0, 1, 1, 0xFE, 0xCE),  # ADC A, d8 no carry input
        (0x34, 0x12, 0, 0, 1, 0, 0, 0x22, 0xD6),  # SUB A, d8
        (0x12, 0x34, 0, 0, 1, 1, 1, 0xDE, 0xD6),  # SUB A, d8 with borrow
        (0x00, 0x00, 0, 1, 1, 0, 0, 0x00, 0xD6),  # SUB A, d8 with zero result
        (0x1F, 0x1C, 0, 0, 1, 0, 0, 0x03, 0xDE),  # SBC A, d8 with carry
        (0x10, 0x0F, 1, 1, 1, 1, 0, 0x00, 0xDE),  # SBC A, d8 with carry and zero
        (0x65, 0x23, 1, 0, 1, 0, 0, 0x41, 0xDE),  # SBC A, d8 with carry
    ],
)
def test_immediate_arithmetic(
    a_val: int,
    immediate: int,
    carry: int,
    z_flag: int,
    n_flag: int,
    h_flag: int,
    c_flag: int,
    result: int,
    opcode: int,
) -> None:
    """Test ADD A, d8, ADC A, d8, SUB A, d8, SBC A, d8 instructions."""
    cpu = CPU(MMU())
    cpu.reg["A"] = a_val
    cpu.flags["C"] = carry
    # Instruction: opcode (1 byte) + immediate (1 byte)
    cpu.insert_instruction(bytearray([opcode, immediate]))
    cpu.cycle()

    assert cpu.reg["A"] == result
    verify_flags(cpu, z_flag=z_flag, n_flag=n_flag, h_flag=h_flag, c_flag=c_flag)

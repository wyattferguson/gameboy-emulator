import pytest

from gbemu.config import M_JOYPAD
from tests.utils import make_cpu, verify_flags


@pytest.mark.parametrize(
    ("dest", "src", "value", "opcode"),
    [
        ("B", "B", 0x32, 0x40),  # LD B, B
        ("B", "C", 0x35, 0x41),  # LD B, C
        ("B", "D", 0x37, 0x42),  # LD B, D
        ("B", "A", 0x3F, 0x47),  # LD B, A
        ("C", "B", 0x42, 0x48),  # LD C, B
        ("C", "C", 0x45, 0x49),  # LD C, C
        ("C", "D", 0x47, 0x4A),  # LD C, D
        ("D", "L", 0x1F, 0x55),  # LD D, L
        ("D", "A", 0x21, 0x57),  # LD D, A
        ("E", "B", 0x23, 0x58),  # LD E, B
        ("E", "D", 0x27, 0x5A),  # LD E, D
        ("E", "E", 0x29, 0x5B),  # LD E, E
        ("E", "H", 0x2B, 0x5C),  # LD E, H
        ("E", "L", 0x2D, 0x5D),  # LD E, L
        ("E", "A", 0x2F, 0x5F),  # LD E, A
        ("H", "B", 0x31, 0x60),  # LD H, B
        ("H", "C", 0x33, 0x61),  # LD H, C
        ("H", "D", 0x35, 0x62),  # LD H, D
        ("H", "E", 0x37, 0x63),  # LD H, E
        ("H", "H", 0x39, 0x64),  # LD H, H
        ("L", "E", 0x45, 0x6B),  # LD L, E
        ("L", "H", 0x47, 0x6C),  # LD L, H
        ("L", "L", 0x49, 0x6D),  # LD L, L
        ("L", "A", 0x4B, 0x6F),  # LD L, A
        ("A", "B", 0x23, 0x78),  # LD A, B
        ("A", "H", 0x2B, 0x7C),  # LD A, H
        ("A", "L", 0x2D, 0x7D),  # LD A, L
        ("A", "A", 0x2F, 0x7F),  # LD A, A
    ],
)
def test_ld(dest: str, src: str, value: int, opcode: int) -> None:
    cpu = make_cpu()
    cpu.reg[src] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg[dest] == value


@pytest.mark.parametrize(
    ("reg", "pair_reg", "address", "value", "opcode"),
    [
        ("B", "HL", 0x1234, 86, 0x46),  # LD B, [HL]
        ("C", "HL", 0x1234, 34, 0x4E),  # LD C, [HL]
        ("D", "HL", 0x1234, 56, 0x56),  # LD D, [HL]
        ("E", "HL", 0x1234, 11, 0x5E),  # LD E, [HL]
        ("H", "HL", 0x1234, 22, 0x66),  # LD H, [HL]
        ("L", "HL", 0x1234, 33, 0x6E),  # LD L, [HL]
        ("A", "HL", 0x1234, 33, 0x7E),  # LD A, [HL]
        ("A", "BC", 0x1234, 0xCD, 0xA),  # LD A, [BC]
        ("A", "BC", 0x00F0, 0x12, 0xA),  # LD A, [BC]
        ("A", "DE", 0x1234, 0xFF, 0x1A),  # LD A, [DE]
        ("A", "DE", 0x00F0, 0x55, 0x1A),  # LD A, [DE]
    ],
)
def test_ld_hl(reg: str, pair_reg: str, address: int, value: int, opcode: int) -> None:
    cpu = make_cpu()
    cpu.mmu[address] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.reg[pair_reg] = address
    cpu.cycle()

    assert cpu.reg[reg] == value


@pytest.mark.parametrize(
    ("dest", "hl", "value", "opcode"),
    [
        ("B", 0x1234, 86, 0x70),  # LD [HL], B
        ("C", 0x4422, 34, 0x71),  # LD [HL], C
        ("D", 0x1512, 56, 0x72),  # LD [HL], D
        ("E", 0x1634, 11, 0x73),  # LD [HL], E
        ("H", 0x4718, 22, 0x74),  # LD [HL], H
        ("L", 0x1234, 33, 0x75),  # LD [HL], L
        ("A", 0x2435, 33, 0x77),  # LD [HL], A
    ],
)
def test_ld_hl_r(dest: str, hl: int, value: int, opcode: int) -> None:
    cpu = make_cpu()
    cpu.reg["HL"] = hl
    cpu.insert_instruction(bytearray([opcode]))
    cpu.reg[dest] = value
    cpu.cycle()

    assert cpu.mmu[cpu.reg["HL"]] == value


@pytest.mark.parametrize(
    ("dest", "value", "opcode"),
    [
        ("BC", 0x1234, 0x1),  # LD BC, d16
        ("DE", 0x5678, 0x11),  # LD DE, d16
        ("HL", 0x9ABC, 0x21),  # LD HL, d16
        ("SP", 0xDDC6, 0x31),  # LD SP, d16
    ],
)
def test_ld_16(dest: str, value: int, opcode: int) -> None:
    cpu = make_cpu()
    top = (value >> 8) & 0xFF
    bottom = value & 0xFF
    cpu.insert_instruction(bytearray([opcode, bottom, top]))
    cpu.cycle()

    if dest != "SP":
        assert cpu.reg[dest[0]] == top
        assert cpu.reg[dest[1]] == bottom
    assert cpu.reg[dest] == value


@pytest.mark.parametrize(
    ("dest", "src", "value", "opcode"),
    [
        ("BC", "A", 0xCD, 0x2),  # LD [BC], A
        ("DE", "A", 0x12, 0x12),  # LD [DE], A
    ],
)
def test_ld_16_reg(dest: str, src: str, value: int, opcode: int) -> None:
    cpu = make_cpu()
    cpu.reg[src] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.mmu[cpu.reg[dest]] == value


@pytest.mark.parametrize(
    ("dest", "value", "opcode"),
    [
        ("B", 0x12, 0x6),  # LD B, d8
        ("D", 0xDF, 0x16),  # LD D, d8
        ("H", 0xF, 0x26),  # LD H, d8
        ("C", 0xAB, 0xE),  # LD C, d8
        ("E", 0x45, 0x1E),  # LD E, d8
        ("L", 0x78, 0x2E),  # LD L, d8
        ("A", 0xCD, 0x3E),  # LD A, d8
    ],
)
def test_ld_8(dest: str, value: int, opcode: int) -> None:
    """Test LD r, d8 instruction. Load 8-bit value into register."""
    cpu = make_cpu()
    cpu.insert_instruction(bytearray([opcode, value]))
    cpu.cycle()
    assert cpu.reg[dest] == value


@pytest.mark.parametrize(
    ("dest", "address", "value", "opcode"),
    [
        ("HL", 0x1234, 0x12, 0x36),  # LD [HL], d8
        ("HL", 0xDF11, 0xFF, 0x36),  # LD [HL], d8
        ("HL", 0xF, 0xAB, 0x36),  # LD [HL], d8
    ],
)
def test_ld_mem_8(dest: str, address: int, value: int, opcode: int) -> None:
    """Test LD [HL], d8 instruction. Load 8-bit value into memory at address in HL."""
    cpu = make_cpu()
    cpu.reg[dest] = address
    cpu.insert_instruction(bytearray([opcode, value]))
    cpu.cycle()
    assert cpu.mmu[cpu.reg[dest]] == value


@pytest.mark.parametrize(
    ("opcode", "msb", "lsb", "sp_value"),
    [
        (0x8, 0x12, 0x34, 0xCCCC),  # LD [16a], SP
    ],
)
def test_ld_mem_imm(opcode: int, msb: int, lsb: int, sp_value: int) -> None:
    """Test LD [16a], SP instruction. Load SP into memory at 16-bit address."""
    cpu = make_cpu()
    cpu.reg["SP"] = sp_value
    cpu.insert_instruction(bytearray([opcode, lsb, msb]))
    cpu.cycle()
    address = (msb << 8) | lsb
    assert cpu.mmu[address] == (sp_value & 0xFF)
    assert cpu.mmu[address + 1] == ((sp_value >> 8) & 0xFF)


@pytest.mark.parametrize(
    ("address", "value", "hl_mod", "opcode"),
    [
        (0x1234, 0xCD, 1, 0x2A),  # LD A, [HL+]
        (0x00F0, 0x12, 1, 0x2A),  # LD A, [HL+]
        (0x1234, 0xCD, -1, 0x3A),  # LD A, [HL-]
        (0x00F0, 0x12, -1, 0x3A),  # LD A, [HL-]
    ],
)
def test_ld_a_hl_mod_register(address: int, value: int, hl_mod: int, opcode: int) -> None:
    cpu = make_cpu()
    cpu.reg["HL"] = address
    cpu.mmu[address] = value
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.reg["A"] == value
    assert cpu.reg["HL"] == address + hl_mod


@pytest.mark.parametrize(
    ("address", "value", "hl_mod", "opcode"),
    [
        (0x1234, 0xCD, 1, 0x22),  # LD [HL+], A
        (0x00F0, 0x12, 1, 0x22),  # LD [HL+], A
        (0x1234, 0xCD, -1, 0x32),  # LD [HL-], A
        (0x00F0, 0x12, -1, 0x32),  # LD [HL-], A
    ],
)
def test_ld_a_hl_mod_memory(address: int, value: int, hl_mod: int, opcode: int) -> None:
    cpu = make_cpu()
    cpu.reg["A"] = value
    cpu.reg["HL"] = address
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    assert cpu.mmu[address] == value
    assert cpu.reg["HL"] == address + hl_mod


@pytest.mark.parametrize(
    ("address", "value"),
    [
        (0x1234, 0xCD),
        (0x00F0, 0x12),
        (0xC123, 0xFF),
    ],
)
def test_ld_a16_from_a_opcode_ea(address: int, value: int) -> None:
    """Test LD [a16], A (0xEA)."""
    cpu = make_cpu()
    cpu.reg["A"] = value
    low = address & 0xFF
    high = (address >> 8) & 0xFF
    cpu.insert_instruction(bytearray([0xEA, low, high]))
    cpu.cycle()

    assert cpu.mmu[address] == value


@pytest.mark.parametrize(
    ("address", "value"),
    [
        (0x1234, 0xCD),
        (0x00F0, 0x12),
        (0xC123, 0xFF),
    ],
)
def test_ld_a_from_a16_opcode_fa(address: int, value: int) -> None:
    """Test LD A, [a16] (0xFA)."""
    cpu = make_cpu()
    cpu.mmu[address] = value
    low = address & 0xFF
    high = (address >> 8) & 0xFF
    cpu.insert_instruction(bytearray([0xFA, low, high]))
    cpu.cycle()

    assert cpu.reg["A"] == value


@pytest.mark.parametrize(
    ("offset", "value"),
    [
        (0x01, 0x12),
        (0x42, 0xCD),
        (0xFF, 0x7E),
    ],
)
def test_ldh_mem_a_opcode_e0(offset: int, value: int) -> None:
    """Test LDH [a8], A (0xE0)."""
    cpu = make_cpu()
    cpu.reg["A"] = value
    cpu.insert_instruction(bytearray([0xE0, offset]))
    cpu.cycle()

    assert cpu.mmu[0xFF00 + offset] == value


@pytest.mark.parametrize(
    ("offset", "value"),
    [
        (0x01, 0x3C),
        (0x42, 0xAA),
        (0xFF, 0x01),
    ],
)
def test_ldh_a_mem_opcode_f0(offset: int, value: int) -> None:
    """Test LDH A, [a8] (0xF0)."""
    cpu = make_cpu()
    cpu.mmu[0xFF00 + offset] = value
    cpu.insert_instruction(bytearray([0xF0, offset]))
    cpu.cycle()

    assert cpu.reg["A"] == value


@pytest.mark.parametrize(
    ("c_value", "a_value"),
    [
        (0x01, 0x9A),
        (0x4C, 0x11),
        (0xFF, 0xE7),
    ],
)
def test_ldh_mem_c_a_opcode_e2(c_value: int, a_value: int) -> None:
    """Test LDH [C], A (0xE2)."""
    cpu = make_cpu()
    cpu.reg["C"] = c_value
    cpu.reg["A"] = a_value
    cpu.insert_instruction(bytearray([0xE2]))
    cpu.cycle()

    assert cpu.mmu[0xFF00 + c_value] == a_value


@pytest.mark.parametrize(
    ("c_value", "mem_value"),
    [
        (0x01, 0x66),
        (0x4C, 0xB2),
        (0xFF, 0x19),
    ],
)
def test_ldh_a_mem_c_opcode_f2(c_value: int, mem_value: int) -> None:
    """Test LDH A, [C] (0xF2)."""
    cpu = make_cpu()
    cpu.reg["C"] = c_value
    cpu.mmu[0xFF00 + c_value] = mem_value
    cpu.insert_instruction(bytearray([0xF2]))
    cpu.cycle()

    assert cpu.reg["A"] == mem_value


def test_ldh_mem_a_opcode_e0_updates_joypad_selection() -> None:
    """Test LDH [0x00], A against JOYP's select-line semantics."""
    cpu = make_cpu()
    cpu.reg["A"] = 0x10
    cpu.insert_instruction(bytearray([0xE0, 0x00]))
    cpu.cycle()

    assert cpu.mmu[M_JOYPAD] == 0xDF


def test_ldh_a_mem_opcode_f0_reads_joypad_state() -> None:
    """Test LDH A, [0x00] against JOYP's selected active-low lines."""
    cpu = make_cpu()
    cpu.mmu[M_JOYPAD] = 0x20
    cpu.mmu.set_joypad_pressed(0b0100, dpad=True, pressed=True)
    cpu.insert_instruction(bytearray([0xF0, 0x00]))
    cpu.cycle()

    assert cpu.reg["A"] == 0xEB


@pytest.mark.parametrize(
    ("sp", "offset", "result", "h_flag", "c_flag"),
    [
        (0x0001, 0x01, 0x0002, 0, 0),
        (0x000F, 0x01, 0x0010, 1, 0),
        (0x00FF, 0x01, 0x0100, 1, 1),
        (0x0000, 0xFF, 0xFFFF, 0, 1),
    ],
)
def test_add_sp_e8_opcode_e8(sp: int, offset: int, result: int, h_flag: int, c_flag: int) -> None:
    """Test ADD SP, e8 (0xE8)."""
    cpu = make_cpu()
    cpu.reg["SP"] = sp
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 1
    cpu.insert_instruction(bytearray([0xE8, offset]))
    cpu.cycle()

    assert cpu.reg["SP"] == result
    verify_flags(cpu, z_flag=0, n_flag=0, h_flag=h_flag, c_flag=c_flag)


@pytest.mark.parametrize(
    ("sp", "offset", "result", "h_flag", "c_flag"),
    [
        (0x0100, 0x01, 0x0101, 0, 0),
        (0x00FF, 0x01, 0x0100, 1, 1),
        (0x0000, 0xFF, 0xFFFF, 0, 1),
    ],
)
def test_ld_hl_sp_plus_e8_opcode_f8(
    sp: int,
    offset: int,
    result: int,
    h_flag: int,
    c_flag: int,
) -> None:
    """Test LD HL, SP + e8 (0xF8)."""
    cpu = make_cpu()
    cpu.reg["SP"] = sp
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 1
    cpu.insert_instruction(bytearray([0xF8, offset]))
    cpu.cycle()

    assert cpu.reg["HL"] == result
    assert cpu.reg["SP"] == sp
    verify_flags(cpu, z_flag=0, n_flag=0, h_flag=h_flag, c_flag=c_flag)


@pytest.mark.parametrize("hl", [0x0000, 0x1234, 0xFFFF])
def test_ld_sp_hl_opcode_f9(hl: int) -> None:
    """Test LD SP, HL (0xF9)."""
    cpu = make_cpu()
    cpu.reg["HL"] = hl
    cpu.reg["SP"] = 0
    cpu.insert_instruction(bytearray([0xF9]))
    cpu.cycle()

    assert cpu.reg["SP"] == hl

import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from tests.utils import verify_flags


@pytest.mark.parametrize(
    ("bit_num", "value", "z_flag", "opcode"),
    [
        (0, 0x01, 0, 0x40),  # BIT 0, B - bit set
        (0, 0x02, 1, 0x40),  # BIT 0, B - bit clear
        (0, 0xFF, 0, 0x40),  # BIT 0, B - all bits set
        (0, 0x00, 1, 0x40),  # BIT 0, B - no bits set
        (1, 0x02, 0, 0x48),  # BIT 1, B - bit set
        (1, 0x01, 1, 0x48),  # BIT 1, B - bit clear
        (1, 0xFF, 0, 0x48),  # BIT 1, B - all bits set
        (1, 0x00, 1, 0x48),  # BIT 1, B - no bits set
        (2, 0x04, 0, 0x50),  # BIT 2, B - bit set
        (2, 0x03, 1, 0x50),  # BIT 2, B - bit clear
        (3, 0x08, 0, 0x58),  # BIT 3, B - bit set
        (3, 0x07, 1, 0x58),  # BIT 3, B - bit clear
        (4, 0x10, 0, 0x60),  # BIT 4, B - bit set
        (4, 0x0F, 1, 0x60),  # BIT 4, B - bit clear
        (5, 0x20, 0, 0x68),  # BIT 5, B - bit set
        (5, 0x1F, 1, 0x68),  # BIT 5, B - bit clear
        (6, 0x40, 0, 0x70),  # BIT 6, B - bit set
        (6, 0x3F, 1, 0x70),  # BIT 6, B - bit clear
        (7, 0x80, 0, 0x78),  # BIT 7, B - bit set
        (7, 0x7F, 1, 0x78),  # BIT 7, B - bit clear
    ],
)
def test_cb_bit_b(bit_num: int, value: int, z_flag: int, opcode: int) -> None:
    """Test BIT B register (bit positions 0-7)."""
    cpu = CPU(MMU())
    assert opcode == (0x40 + (bit_num * 8))
    cpu.reg["B"] = value
    cpu.insert_instruction(bytearray([0xCB, opcode]))
    cpu.cycle()

    # BIT doesn't modify the register
    assert cpu.reg["B"] == value
    verify_flags(cpu, z_flag=z_flag, n_flag=0, h_flag=1)


@pytest.mark.parametrize(
    ("bit_num", "dest", "value", "z_flag", "opcode"),
    [
        (0, "C", 0x01, 0, 0x41),  # BIT 0, C
        (0, "D", 0x02, 1, 0x42),  # BIT 0, D
        (0, "E", 0xFF, 0, 0x43),  # BIT 0, E
        (0, "H", 0x00, 1, 0x44),  # BIT 0, H
        (0, "L", 0x01, 0, 0x45),  # BIT 0, L
        (0, "A", 0x02, 1, 0x47),  # BIT 0, A
        (1, "C", 0x02, 0, 0x49),  # BIT 1, C
        (1, "D", 0x01, 1, 0x4A),  # BIT 1, D
        (2, "E", 0x04, 0, 0x53),  # BIT 2, E
        (2, "H", 0x03, 1, 0x54),  # BIT 2, H
        (3, "L", 0x08, 0, 0x5D),  # BIT 3, L
        (3, "A", 0x07, 1, 0x5F),  # BIT 3, A
        (4, "C", 0x10, 0, 0x61),  # BIT 4, C
        (4, "D", 0x0F, 1, 0x62),  # BIT 4, D
        (5, "E", 0x20, 0, 0x6B),  # BIT 5, E
        (5, "H", 0x1F, 1, 0x6C),  # BIT 5, H
        (6, "L", 0x40, 0, 0x75),  # BIT 6, L
        (6, "A", 0x3F, 1, 0x77),  # BIT 6, A
        (7, "C", 0x80, 0, 0x79),  # BIT 7, C
        (7, "D", 0x7F, 1, 0x7A),  # BIT 7, D
    ],
)
def test_cb_bit_registers(
    bit_num: int,
    dest: str,
    value: int,
    z_flag: int,
    opcode: int,
) -> None:
    """Test BIT on various registers (C through A)."""
    cpu = CPU(MMU())
    register_index = {"B": 0, "C": 1, "D": 2, "E": 3, "H": 4, "L": 5, "A": 7}[dest]
    assert opcode == (0x40 + (bit_num * 8) + register_index)
    cpu.reg[dest] = value
    cpu.insert_instruction(bytearray([0xCB, opcode]))
    cpu.cycle()

    # BIT doesn't modify the register
    assert cpu.reg[dest] == value
    verify_flags(cpu, z_flag=z_flag, n_flag=0, h_flag=1)


@pytest.mark.parametrize(
    ("value", "z_flag", "opcode"),
    [
        (0x01, 0, 0x46),  # BIT 0, [HL] - bit set
        (0x00, 1, 0x46),  # BIT 0, [HL] - bit clear
        (0xFF, 0, 0x46),  # BIT 0, [HL] - all bits set
        (0x02, 0, 0x4E),  # BIT 1, [HL] - bit set
        (0x01, 1, 0x4E),  # BIT 1, [HL] - bit clear
        (0x04, 0, 0x56),  # BIT 2, [HL] - bit set
        (0x03, 1, 0x56),  # BIT 2, [HL] - bit clear
        (0x08, 0, 0x5E),  # BIT 3, [HL] - bit set
        (0x07, 1, 0x5E),  # BIT 3, [HL] - bit clear
        (0x10, 0, 0x66),  # BIT 4, [HL] - bit set
        (0x0F, 1, 0x66),  # BIT 4, [HL] - bit clear
        (0x20, 0, 0x6E),  # BIT 5, [HL] - bit set
        (0x1F, 1, 0x6E),  # BIT 5, [HL] - bit clear
        (0x40, 0, 0x76),  # BIT 6, [HL] - bit set
        (0x3F, 1, 0x76),  # BIT 6, [HL] - bit clear
        (0x80, 0, 0x7E),  # BIT 7, [HL] - bit set
        (0x7F, 1, 0x7E),  # BIT 7, [HL] - bit clear
    ],
)
def test_cb_bit_hl(value: int, z_flag: int, opcode: int) -> None:
    """Test BIT on memory location [HL]."""
    mmu = MMU()
    cpu = CPU(mmu)
    addr = 0xC000
    cpu.reg["H"] = addr >> 8
    cpu.reg["L"] = addr & 0xFF
    mmu[addr] = value
    cpu.insert_instruction(bytearray([0xCB, opcode]))
    cpu.cycle()

    # BIT doesn't modify memory
    assert mmu[addr] == value
    verify_flags(cpu, z_flag=z_flag, n_flag=0, h_flag=1)


def test_cb_bit_all_bits_register() -> None:
    """Test BIT on all bit positions (0-7) for a single register."""
    cpu = CPU(MMU())
    value = 0xAA  # 10101010 - alternating bits set

    for bit_num in range(8):
        cpu.reg["B"] = value
        expected_z = 0 if (value >> bit_num) & 0x1 else 1
        # Calculate opcode: 0x40 + (bit_num * 8)
        opcode = 0x40 + (bit_num * 8)
        cpu.insert_instruction(bytearray([0xCB, opcode]))
        cpu.cycle()

        assert cpu.reg["B"] == value
        verify_flags(cpu, z_flag=expected_z, n_flag=0, h_flag=1)

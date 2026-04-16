import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.utils import hex_to_signed


@pytest.mark.parametrize(
    (
        "offset",
        "opcode",
    ),
    [
        (0x12, 0x18),  # JR d8
        (0xFF, 0x18),  # JR d8
        (0x00, 0x18),  # JR d8
        (0xFE, 0x18),  # JR d8 (negative offset)
    ],
)
def test_jr(
    offset: int,
    opcode: int,
) -> None:
    """Test JR instruction. Jump to address relative to current PC."""
    cpu = CPU(MMU())
    result_pc = cpu.pc + hex_to_signed(offset, 8)
    cpu.insert_instruction(bytearray([opcode, offset]))
    cpu.cycle()

    assert cpu.pc == result_pc


@pytest.mark.parametrize(
    (
        "opcode",
        "flag",
        "flag_value",
        "offset",
        "should_jump",
    ),
    [
        (0x20, "Z", 0, 0x12, True),  # JR NZ, r8 w/ Z = 0 (jump taken)
        (0x20, "Z", 0, 0xFE, True),  # JR NZ, r8 w/ Z = 0 (jump taken, negative offset)
        (0x20, "Z", 1, 0x12, False),  # JR NZ, r8 w/ Z = 1 (jump not taken)
        (0x20, "Z", 1, 0xFE, False),  # JR NZ, r8 w/ Z = 1 (jump not taken, negative offset)
        (0x28, "Z", 1, 0x12, True),  # JR Z, r8 w/ Z = 1 (jump taken)
        (0x28, "Z", 1, 0xFE, True),  # JR Z, r8 w/ Z = 1 (jump taken, negative offset)
        (0x28, "Z", 0, 0x12, False),  # JR Z, r8 w/ Z = 0 (jump not taken)
        (0x28, "Z", 0, 0xFE, False),  # JR Z, r8 w/ Z = 0 (jump not taken, negative offset)
        (0x30, "C", 0, 0x12, True),  # JR NC, r8 w/ C = 0 (jump taken)
        (0x30, "C", 0, 0xFE, True),  # JR NC, r8 w/ C = 0 (jump taken, negative offset)
        (0x30, "C", 1, 0x12, False),  # JR NC, r8 w/ C = 1 (jump not taken)
        (0x30, "C", 1, 0xFE, False),  # JR NC, r8 w/ C = 1 (jump not taken, negative offset)
        (0x38, "C", 1, 0x12, True),  # JR C, r8 w/ C = 1 (jump taken)
        (0x38, "C", 1, 0xFE, True),  # JR C, r8 w/ C = 1 (jump taken, negative offset)
        (0x38, "C", 0, 0x12, False),  # JR C, r8 w/ C = 0 (jump not taken)
        (0x38, "C", 0, 0xFE, False),  # JR C, r8 w/ C = 0 (jump not taken, negative offset)
    ],
)
def test_jrc(
    opcode: int,
    flag: str,
    flag_value: int,
    offset: int,
    should_jump: bool,
) -> None:
    """Test conditional JR."""
    cpu = CPU(MMU())
    result_pc = cpu.pc + (hex_to_signed(offset, 8) if should_jump else 0)
    cpu.flags[flag] = flag_value
    cpu.insert_instruction(bytearray([opcode, offset]))

    cpu.cycle()

    assert cpu.pc == result_pc


@pytest.mark.parametrize(
    "addr",
    [
        0x1234,  # JP a16
        0x8000,  # JP a16 high address
        0x0000,  # JP a16 low address
        0xFFFF,  # JP a16 max address
    ],
)
def test_jp(
    addr: int,
) -> None:
    """Test JP instruction. Jump to absolute address."""
    cpu = CPU(MMU())
    # Instruction: opcode (1 byte) + address (2 bytes, little-endian)
    addr_low = addr & 0xFF
    addr_high = (addr >> 8) & 0xFF
    cpu.insert_instruction(bytearray([0xC3, addr_low, addr_high]))
    cpu.cycle()

    assert cpu.pc == addr


@pytest.mark.parametrize(
    (
        "opcode",
        "flag",
        "flag_value",
        "addr",
        "should_jump",
    ),
    [
        (0xC2, "Z", 0, 0x1234, True),  # JP NZ, a16 w/ Z = 0 (jump taken)
        (0xC2, "Z", 1, 0x1234, False),  # JP NZ, a16 w/ Z = 1 (jump not taken)
        (0xCA, "Z", 1, 0x5678, True),  # JP Z, a16 w/ Z = 1 (jump taken)
        (0xCA, "Z", 0, 0x5678, False),  # JP Z, a16 w/ Z = 0 (jump not taken)
        (0xD2, "C", 0, 0x8000, True),  # JP NC, a16 w/ C = 0 (jump taken)
        (0xD2, "C", 1, 0x8000, False),  # JP NC, a16 w/ C = 1 (jump not taken)
        (0xDA, "C", 1, 0xABCD, True),  # JP C, a16 w/ C = 1 (jump taken)
        (0xDA, "C", 0, 0xABCD, False),  # JP C, a16 w/ C = 0 (jump not taken)
    ],
)
def test_jpc(
    opcode: int,
    flag: str,
    flag_value: int,
    addr: int,
    should_jump: bool,
) -> None:
    """Test conditional JP."""
    cpu = CPU(MMU())
    initial_pc = cpu.pc
    result_pc = addr if should_jump else (initial_pc + 3)
    cpu.flags[flag] = flag_value
    addr_low = addr & 0xFF
    addr_high = (addr >> 8) & 0xFF
    cpu.insert_instruction(bytearray([opcode, addr_low, addr_high]))

    cpu.cycle()

    assert cpu.pc == result_pc


def test_jp_hl() -> None:
    """Test JP HL. Jump to address stored in HL register."""
    cpu = CPU(MMU())
    target_addr = 0x4321
    cpu.reg["H"] = (target_addr >> 8) & 0xFF
    cpu.reg["L"] = target_addr & 0xFF
    cpu.insert_instruction(bytearray([0xE9]))
    cpu.cycle()

    assert cpu.pc == target_addr

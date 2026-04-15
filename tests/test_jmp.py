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
    result_pc = cpu.pc + (hex_to_signed(offset, 8) if should_jump else 2)
    cpu.flags[flag] = flag_value
    cpu.insert_instruction(bytearray([opcode, offset]))

    cpu.cycle()

    assert cpu.pc == result_pc

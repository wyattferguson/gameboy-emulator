import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.opcodes import OPCODES


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
    result_pc = cpu.pc + cpu.hex_to_signed(offset, 8)
    cpu.insert_instruction(bytearray([opcode, offset]))
    cpu.cycle()

    assert cpu.pc == result_pc

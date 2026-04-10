import pytest

from gbemu.config import PC_START, SP_START
from gbemu.cpu import CPU
from gbemu.opcodes import OpCode
from gbemu.ram import RAM


class DummyRAM:
    def __getitem__(self, address: int) -> int:
        return 0

    def __setitem__(self, address: int, value: int) -> None:
        return None


@pytest.mark.parametrize(
    ("start_pc", "offset", "expected_pc"),
    [
        (0x100, 0x10, 0x112),
        (0x120, -0x08, 0x11A),
    ],
)
def test_jr_updates_program_counter_relative_to_current_instruction(
    start_pc: int,
    offset: int,
    expected_pc: int,
) -> None:
    cpu = CPU(DummyRAM())
    cpu.PC = start_pc
    cpu.instruction = OpCode("JR i8", 2, 8, "jr")

    cpu.jr(offset)

    assert expected_pc == cpu.PC

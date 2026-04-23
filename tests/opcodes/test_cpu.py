import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.opcodes import CB_PREFIXED_TABLE
from gbemu.utils import hex_to_signed


@pytest.mark.parametrize(
    ("value", "bits", "expected"),
    [
        (0x00, 8, 0),
        (0x7F, 8, 127),
        (0x80, 8, -128),
        (0xFF, 8, -1),
        (0x8000, 16, -32768),
        (0xFFFF, 16, -1),
    ],
)
def test_hex_to_signed(value: int, bits: int, expected: int) -> None:
    assert hex_to_signed(value, bits) == expected


def test_cycle_wraps_pc_after_instruction_increment() -> None:
    mmu = MMU()
    cpu = CPU(mmu)

    # Place NOP at 0xFFFF and ensure PC wraps to 0x0000 after execution.
    mmu.memory[0xFFFF] = 0x00
    cpu.pc = 0xFFFF

    cpu.cycle()

    assert cpu.pc == 0x0000


def test_fetch_wraps_cb_prefixed_opcode_across_address_boundary() -> None:
    mmu = MMU()
    cpu = CPU(mmu)

    mmu.memory[0xFFFF] = 0xCB
    mmu.memory[0x0000] = 0x11
    cpu.pc = 0xFFFF

    cpu.fetch()

    assert cpu.cb_prefixed is True
    assert cpu.instruction == CB_PREFIXED_TABLE[0x11]


def test_decode_wraps_immediate_operand_across_address_boundary() -> None:
    mmu = MMU()
    cpu = CPU(mmu)

    mmu.memory[0xFFFF] = 0x06
    mmu.memory[0x0000] = 0x42
    cpu.pc = 0xFFFF

    cpu.fetch()
    cpu.decode()

    assert cpu.args == ["B", 0x42]

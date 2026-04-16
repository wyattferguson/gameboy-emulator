import pytest

from gbemu.config import PC_START
from gbemu.cpu import CPU
from gbemu.mmu import MMU


@pytest.mark.parametrize(
    ("opcode", "target_addr"),
    [
        (0xC7, 0x00),  # RST $00
        (0xCF, 0x08),  # RST $08
        (0xD7, 0x10),  # RST $10
        (0xDF, 0x18),  # RST $18
        (0xE7, 0x20),  # RST $20
        (0xEF, 0x28),  # RST $28
        (0xF7, 0x30),  # RST $30
        (0xFF, 0x38),  # RST $38
    ],
)
def test_rst_vectors(opcode: int, target_addr: int) -> None:
    """RST should push PC and jump to its fixed vector address."""
    cpu = CPU(MMU())
    initial_pc = cpu.pc
    initial_sp = cpu.reg["SP"]

    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()

    # pc_inc=False on all RST opcodes, so PC is exactly the target vector.
    assert cpu.pc == target_addr

    # Emulator stack model increments SP by 2 on push.
    assert cpu.reg["SP"] == (initial_sp + 2) & 0xFFFF

    # MMU stores one byte at SP: low byte of pushed PC.
    assert cpu.mmu[cpu.reg["SP"]] == (initial_pc & 0xFF)


def test_rst_uses_current_pc_value() -> None:
    """RST should push the current PC low byte, not a fixed constant."""
    cpu = CPU(MMU())
    cpu.pc = 0x1234
    initial_sp = cpu.reg["SP"]

    cpu.insert_instruction(bytearray([0xFF]))  # RST $38
    cpu.cycle()

    assert cpu.pc == 0x38
    assert cpu.reg["SP"] == (initial_sp + 2) & 0xFFFF
    assert cpu.mmu[cpu.reg["SP"]] == 0x34


def test_rst_from_default_pc_start() -> None:
    """Sanity check default start PC is pushed as low byte on RST."""
    cpu = CPU(MMU())
    assert cpu.pc == PC_START

    cpu.insert_instruction(bytearray([0xC7]))  # RST $00
    cpu.cycle()

    assert cpu.pc == 0x00
    assert cpu.mmu[cpu.reg["SP"]] == (PC_START & 0xFF)

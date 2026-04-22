import pytest

from gbemu.constants import SP_START
from tests.utils import cycle_instruction, make_cpu


@pytest.mark.parametrize(
    ("opcode", "reg_high", "reg_low", "high", "low"),
    [
        (0xC5, "B", "C", 0x12, 0x34),
        (0xD5, "D", "E", 0x56, 0x78),
        (0xE5, "H", "L", 0x9A, 0xBC),
        (0xF5, "A", "F", 0x3C, 0xF0),
    ],
)
def test_push(opcode: int, reg_high: str, reg_low: str, high: int, low: int) -> None:
    """PUSH stores 16-bit value on stack and decrements SP by 2."""
    cpu = make_cpu()
    initial_sp = cpu.reg["SP"]
    cpu.reg[reg_high] = high

    expected_low = low
    if reg_low == "F":
        cpu.flags["Z"] = 1 if (low & 0x80) else 0
        cpu.flags["N"] = 1 if (low & 0x40) else 0
        cpu.flags["H"] = 1 if (low & 0x20) else 0
        cpu.flags["C"] = 1 if (low & 0x10) else 0
        expected_low = low & 0xF0
    else:
        cpu.reg[reg_low] = low

    cycle_instruction(cpu, opcode)

    assert cpu.reg["SP"] == (initial_sp - 2) & 0xFFFF
    assert cpu.mmu[cpu.reg["SP"]] == expected_low
    assert cpu.mmu[(cpu.reg["SP"] + 1) & 0xFFFF] == high


@pytest.mark.parametrize(
    ("opcode", "reg_pair", "initial_sp", "low", "high"),
    [
        (0xC1, "BC", 0x8000, 0x42, 0x99),
        (0xD1, "DE", 0x9000, 0xAB, 0xCD),
        (0xE1, "HL", 0xA000, 0x11, 0x22),
    ],
)
def test_pop(opcode: int, reg_pair: str, initial_sp: int, low: int, high: int) -> None:
    """POP loads register-pair from stack and increments SP by 2."""
    cpu = make_cpu()
    cpu.reg["SP"] = initial_sp
    cpu.mmu[initial_sp] = low
    cpu.mmu[(initial_sp + 1) & 0xFFFF] = high
    cycle_instruction(cpu, opcode)

    assert cpu.reg[reg_pair] == ((high << 8) | low)
    assert cpu.reg["SP"] == (initial_sp + 2) & 0xFFFF


def test_push_bc_then_pop_bc_round_trip() -> None:
    """PUSH BC then POP BC should preserve register value."""
    cpu = make_cpu()
    start_sp = cpu.reg["SP"]
    cpu.reg["B"] = 0xBE
    cpu.reg["C"] = 0xEF

    cycle_instruction(cpu, 0xC5, 0xC1)
    cpu.cycle()

    assert cpu.reg["BC"] == 0xBEEF
    assert cpu.reg["SP"] == start_sp


def test_pop_af_sets_flags_and_masks_low_nibble() -> None:
    """POP AF should update flags from upper nibble and clear F low nibble."""
    cpu = make_cpu()
    cpu.reg["SP"] = 0x8000
    cpu.mmu[0x8000] = 0xF7  # F low byte; low nibble should be masked away
    cpu.mmu[0x8001] = 0x12  # A high byte

    cycle_instruction(cpu, 0xF1)

    assert cpu.reg["AF"] == 0x12F0
    assert cpu.flags["Z"] == 1
    assert cpu.flags["N"] == 1
    assert cpu.flags["H"] == 1
    assert cpu.flags["C"] == 1


def test_push_pop_increment_pc_by_one() -> None:
    """PUSH and POP should both advance PC by 1."""
    cpu = make_cpu()
    cpu.reg["BC"] = 0x1234
    cycle_instruction(cpu, 0xC5, 0xC1)
    assert cpu.pc == 1
    cpu.cycle()
    assert cpu.pc == 2


def test_push_boundary_sp_wraps_downward() -> None:
    """PUSH should wrap SP downward at memory boundary."""
    cpu = make_cpu()
    cpu.reg["SP"] = 0x0001
    cpu.reg["B"] = 0x42
    cpu.reg["C"] = 0x24

    cycle_instruction(cpu, 0xC5)

    assert cpu.reg["SP"] == 0xFFFF
    assert cpu.mmu[0xFFFF] == 0x24
    assert cpu.mmu[0x0000] == 0x42


def test_default_sp_start() -> None:
    """Sanity check CPU stack pointer start value."""
    cpu = make_cpu()
    assert cpu.reg["SP"] == SP_START

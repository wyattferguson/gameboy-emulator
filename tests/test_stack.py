import pytest

from gbemu.config import PC_START, SP_START
from gbemu.cpu import CPU
from gbemu.mmu import MMU


@pytest.mark.parametrize(
    "opcode,reg_high,reg_low,high,low",
    [
        (0xC5, "B", "C", 0x12, 0x34),  # PUSH BC
        (0xC5, "B", "C", 0xFF, 0xFF),  # PUSH BC max value
        (0xC5, "B", "C", 0x00, 0x00),  # PUSH BC min value
        (0xD5, "D", "E", 0x56, 0x78),  # PUSH DE
        (0xD5, "D", "E", 0xAB, 0xCD),  # PUSH DE max value
        (0xE5, "H", "L", 0x9A, 0xBC),  # PUSH HL
        (0xE5, "H", "L", 0x11, 0x11),  # PUSH HL min value
        (0xE5, "H", "L", 0x99, 0xFF),  # PUSH HL high value
        (0xF5, "A", "F", 0x3C, 0xF0),  # PUSH AF
        (0xF5, "A", "F", 0xFF, 0x10),  # PUSH AF alt value
    ],
)
def test_push(opcode: int, reg_high: str, reg_low: str, high: int, low: int) -> None:
    """Test PUSH increments SP by 2 and stores low byte."""
    cpu = CPU(MMU())
    initial_sp = cpu.reg["SP"]
    cpu.reg[reg_high] = high
    cpu.reg[reg_low] = low
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()
    assert cpu.reg["SP"] == (initial_sp + 2) & 0xFFFF
    assert cpu.mmu[cpu.reg["SP"]] == low


@pytest.mark.parametrize(
    "opcode,reg_pair,address",
    [
        (0xC1, "BC", 0x0080),  # POP BC
        (0xC1, "BC", 0xC000),  # POP BC different address
        (0xC1, "BC", 0x8000),  # POP BC high address
        (0xD1, "DE", 0x9000),  # POP DE
        (0xD1, "DE", 0xA000),  # POP DE different address
        (0xD1, "DE", 0x8000),  # POP DE high address
        (0xE1, "HL", 0xB000),  # POP HL
        (0xE1, "HL", 0x7000),  # POP HL different address
        (0xE1, "HL", 0x8000),  # POP HL high address
    ],
)
def test_pop(opcode: int, reg_pair: str, address: int) -> None:
    """Test POP decrements target register by 2."""
    cpu = CPU(MMU())
    cpu.reg[reg_pair] = address
    initial_reg_val = cpu.reg[reg_pair]
    cpu.mmu[address] = 0x42
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()
    assert cpu.reg[reg_pair] == (initial_reg_val - 2) & 0xFFFF


def test_push_bc_then_pop_bc() -> None:
    """Test PUSH BC stores only low byte at the new SP address."""
    cpu = CPU(MMU())
    initial_sp = cpu.reg["SP"]
    cpu.reg["B"] = 0xBE
    cpu.reg["C"] = 0xEF
    cpu.insert_instruction(bytearray([0xC5]))  # PUSH BC
    cpu.cycle()
    pushed_sp = cpu.reg["SP"]
    assert pushed_sp == (initial_sp + 2) & 0xFFFF
    assert cpu.mmu[pushed_sp] == 0xEF


def test_pop_af_sets_flags() -> None:
    """Test POP AF updates AF and decodes upper-nibble flags from stack value."""
    cpu = CPU(MMU())
    cpu.reg["AF"] = 0x8000
    cpu.mmu[0x8000] = 0xB0  # Z=1, N=0, H=1, C=1

    cpu.insert_instruction(bytearray([0xF1]))  # POP AF
    cpu.cycle()

    assert cpu.reg["AF"] == 0x7FFE
    assert cpu.flags["Z"] == 1
    assert cpu.flags["N"] == 0
    assert cpu.flags["H"] == 1
    assert cpu.flags["C"] == 1


def test_push_affects_sp_only() -> None:
    """Test that PUSH only modifies SP, not other registers."""
    cpu = CPU(MMU())
    initial_sp = cpu.reg["SP"]

    bc_high, bc_low = 0x12, 0x34
    de_high, de_low = 0x56, 0x78
    hl_high, hl_low = 0x9A, 0xBC

    # Set registers to specific values
    cpu.reg["B"] = bc_high
    cpu.reg["C"] = bc_low
    cpu.reg["D"] = de_high
    cpu.reg["E"] = de_low
    cpu.reg["H"] = hl_high
    cpu.reg["L"] = hl_low

    # PUSH BC
    cpu.insert_instruction(bytearray([0xC5]))
    cpu.cycle()

    # Other registers should be unchanged
    assert cpu.reg["B"] == bc_high
    assert cpu.reg["C"] == bc_low
    assert cpu.reg["D"] == de_high
    assert cpu.reg["E"] == de_low
    assert cpu.reg["H"] == hl_high
    assert cpu.reg["L"] == hl_low
    assert cpu.reg["SP"] == (initial_sp + 2) & 0xFFFF


@pytest.mark.parametrize(
    "opcode,setup_reg,setup_val,mem_addr",
    [
        (0xC5, None, None, None),  # PUSH BC
        (0xC1, "BC", 0x8000, 0x8000),  # POP BC
    ],
)
def test_pc_increment(
    opcode: int,
    setup_reg: str | None,
    setup_val: int | None,
    mem_addr: int | None,
) -> None:
    """Test that PUSH and POP each increment PC by 1."""
    cpu = CPU(MMU())
    initial_pc = cpu.pc
    if setup_reg:
        cpu.reg[setup_reg] = setup_val
        cpu.mmu[mem_addr] = 0x42
    else:
        cpu.reg["BC"] = 0x1234
    cpu.insert_instruction(bytearray([opcode]))
    cpu.cycle()
    assert cpu.pc == initial_pc + 1


def test_push_boundary_sp_value() -> None:
    """Test PUSH with SP near boundary."""
    cpu = CPU(MMU())

    # Set SP to high memory value
    cpu.reg["SP"] = 0xFFFE
    cpu.reg["B"] = 0x42
    cpu.reg["C"] = 0x42

    cpu.insert_instruction(bytearray([0xC5]))
    cpu.cycle()

    # SP should wrap around (0xFFFE + 2 = 0x10000, masked to 0x0000)
    assert cpu.reg["SP"] == 0x0000
    # Value should be stored at wrapped location
    assert cpu.mmu[0x0000] == 0x42

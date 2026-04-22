import pytest

from tests.utils import cycle_instruction, make_cpu


def test_nop() -> None:
    """Test NOP instruction. Should do nothing except advance PC."""
    cpu = make_cpu()
    initial_pc = cpu.pc
    cycle_instruction(cpu, 0x00)

    # PC should be incremented by 1 (instruction length)
    assert cpu.pc == (initial_pc + 1) & 0xFFFF


def test_halt() -> None:
    """Test HALT instruction. Enter low-power mode until interrupt."""
    cpu = make_cpu()
    initial_pc = cpu.pc
    cycle_instruction(cpu, 0x76)

    # PC should be incremented by 1 (instruction length)
    assert cpu.pc == (initial_pc + 1) & 0xFFFF


def test_di() -> None:
    """Test DI instruction. Disable interrupts."""
    cpu = make_cpu()
    # Start with interrupts enabled
    cpu.interrupts = True
    initial_pc = cpu.pc
    cycle_instruction(cpu, 0xF3)

    # Interrupts should be disabled
    assert cpu.interrupts is False
    # PC should be incremented by 1 (instruction length)
    assert cpu.pc == (initial_pc + 1) & 0xFFFF


def test_ei() -> None:
    """Test EI instruction. IME is enabled after the following instruction."""
    cpu = make_cpu()
    # Start with interrupts disabled
    cpu.interrupts = False
    initial_pc = cpu.pc
    cycle_instruction(cpu, 0xFB, 0x00)

    # EI delays IME by one instruction.
    assert cpu.interrupts is False
    cpu.cycle()
    assert cpu.interrupts is True
    # PC should be incremented by 1 (instruction length)
    assert cpu.pc == (initial_pc + 2) & 0xFFFF


@pytest.mark.parametrize(
    "initial_state",
    [
        True,  # Already enabled
        False,  # Disabled
    ],
)
def test_di_multiple(
    initial_state: bool,
) -> None:
    """Test DI instruction multiple times."""
    cpu = make_cpu()
    cpu.interrupts = initial_state

    cycle_instruction(cpu, 0xF3)
    assert cpu.interrupts is False

    # Call DI again while already disabled
    cycle_instruction(cpu, 0xF3)
    assert cpu.interrupts is False


@pytest.mark.parametrize(
    "initial_state",
    [
        True,  # Already enabled
        False,  # Disabled
    ],
)
def test_ei_multiple(
    initial_state: bool,
) -> None:
    """Test EI instruction multiple times with delayed IME behavior."""
    cpu = make_cpu()
    cpu.interrupts = initial_state

    cpu.insert_instruction(bytearray([0xFB, 0x00, 0xFB, 0x00]))  # EI;NOP;EI;NOP
    cpu.cycle()
    if initial_state:
        assert cpu.interrupts is True
    else:
        assert cpu.interrupts is False
    cpu.cycle()
    assert cpu.interrupts is True

    # Call EI again while enabled: still delayed and remains enabled after NOP.
    cpu.cycle()
    assert cpu.interrupts is True
    cpu.cycle()
    assert cpu.interrupts is True


def test_di_ei_sequence() -> None:
    """Test DI followed by EI sequence."""
    cpu = make_cpu()
    cpu.interrupts = True

    # Disable interrupts
    cycle_instruction(cpu, 0xF3)
    assert cpu.interrupts is False

    # Enable interrupts
    cycle_instruction(cpu, 0xFB, 0x00)
    assert cpu.interrupts is False
    cpu.cycle()
    assert cpu.interrupts is True


def test_halt_waits_until_interrupt_pending() -> None:
    """HALT should stop instruction fetch until an interrupt is pending."""
    cpu = make_cpu()
    cycle_instruction(cpu, 0x76, 0x00)
    assert cpu.halted is True
    pc_after_halt = cpu.pc

    # No pending interrupt: CPU should remain halted and not advance PC.
    cpu.cycle()
    assert cpu.halted is True
    assert cpu.pc == pc_after_halt

    # Pending interrupt wakes CPU from HALT.
    cpu.mmu[0xFFFF] = 0x01  # IE: VBlank enabled
    cpu.mmu[0xFF0F] = 0x01  # IF: VBlank requested
    cpu.cycle()
    assert cpu.halted is False
    assert cpu.pc == (pc_after_halt + 1) & 0xFFFF


def test_interrupt_service_pushes_pc_and_jumps_vector() -> None:
    """When IME is set, pending interrupt should jump to vector and clear IF bit."""
    cpu = make_cpu()
    cpu.interrupts = True
    cpu.pc = 0x1234
    cpu.reg["SP"] = 0xFFFE
    cpu.mmu[0xFFFF] = 0x01  # IE bit 0 (VBlank)
    cpu.mmu[0xFF0F] = 0x01  # IF bit 0 pending

    cycles = cpu.cycle()

    assert cycles == 20
    assert cpu.pc == 0x40
    assert cpu.interrupts is False
    assert (cpu.mmu[0xFF0F] & 0x01) == 0
    assert cpu.reg["SP"] == 0xFFFC
    assert cpu.mmu[0xFFFC] == 0x34
    assert cpu.mmu[0xFFFD] == 0x12


def test_interrupt_priority_services_lowest_vector_first() -> None:
    """When multiple interrupts are pending, service priority order bit0..bit4."""
    cpu = make_cpu()
    cpu.interrupts = True
    cpu.pc = 0x4000
    cpu.reg["SP"] = 0xFFFE

    # VBlank(bit0) and Timer(bit2) both enabled+pending.
    cpu.mmu[0xFFFF] = 0x05
    cpu.mmu[0xFF0F] = 0x05

    cycles = cpu.cycle()

    assert cycles == 20
    assert cpu.pc == 0x40
    assert (cpu.mmu[0xFF0F] & 0x01) == 0
    assert (cpu.mmu[0xFF0F] & 0x04) == 0x04


def test_ei_does_not_service_interrupt_until_following_cycle() -> None:
    """EI enables IME after next instruction; pending IRQ services on cycle after that."""
    cpu = make_cpu()
    cpu.interrupts = False
    cpu.pc = 0x200
    cpu.reg["SP"] = 0xFFFE
    cpu.insert_instruction(bytearray([0xFB, 0x00]))  # EI ; NOP

    cpu.mmu[0xFFFF] = 0x01
    cpu.mmu[0xFF0F] = 0x01

    c1 = cpu.cycle()
    assert c1 == 4
    assert cpu.pc == 0x201
    assert cpu.interrupts is False

    c2 = cpu.cycle()
    assert c2 == 4
    assert cpu.pc == 0x202
    assert cpu.interrupts is True

    c3 = cpu.cycle()
    assert c3 == 20
    assert cpu.pc == 0x40

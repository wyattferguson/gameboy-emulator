import pytest

from tests.utils import make_cpu


def test_nop() -> None:
    """Test NOP instruction. Should do nothing except advance PC."""
    cpu = make_cpu()
    initial_pc = cpu.pc
    cpu.insert_instruction(bytearray([0x00]))  # NOP
    cpu.cycle()

    # PC should be incremented by 1 (instruction length)
    assert cpu.pc == (initial_pc + 1) & 0xFFFF


def test_halt() -> None:
    """Test HALT instruction. Enter low-power mode until interrupt."""
    cpu = make_cpu()
    initial_pc = cpu.pc
    cpu.insert_instruction(bytearray([0x76]))  # HALT
    cpu.cycle()

    # PC should be incremented by 1 (instruction length)
    assert cpu.pc == (initial_pc + 1) & 0xFFFF


def test_di() -> None:
    """Test DI instruction. Disable interrupts."""
    cpu = make_cpu()
    # Start with interrupts enabled
    cpu.interrupts = True
    initial_pc = cpu.pc
    cpu.insert_instruction(bytearray([0xF3]))  # DI
    cpu.cycle()

    # Interrupts should be disabled
    assert cpu.interrupts is False
    # PC should be incremented by 1 (instruction length)
    assert cpu.pc == (initial_pc + 1) & 0xFFFF


def test_ei() -> None:
    """Test EI instruction. Enable interrupts."""
    cpu = make_cpu()
    # Start with interrupts disabled
    cpu.interrupts = False
    initial_pc = cpu.pc
    cpu.insert_instruction(bytearray([0xFB]))  # EI
    cpu.cycle()

    # Interrupts should be enabled
    assert cpu.interrupts is True
    # PC should be incremented by 1 (instruction length)
    assert cpu.pc == (initial_pc + 1) & 0xFFFF


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

    cpu.insert_instruction(bytearray([0xF3]))  # DI
    cpu.cycle()
    assert cpu.interrupts is False

    # Call DI again while already disabled
    cpu.insert_instruction(bytearray([0xF3]))  # DI
    cpu.cycle()
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
    """Test EI instruction multiple times."""
    cpu = make_cpu()
    cpu.interrupts = initial_state

    cpu.insert_instruction(bytearray([0xFB]))  # EI
    cpu.cycle()
    assert cpu.interrupts is True

    # Call EI again while already enabled
    cpu.insert_instruction(bytearray([0xFB]))  # EI
    cpu.cycle()
    assert cpu.interrupts is True


def test_di_ei_sequence() -> None:
    """Test DI followed by EI sequence."""
    cpu = make_cpu()
    cpu.interrupts = True

    # Disable interrupts
    cpu.insert_instruction(bytearray([0xF3]))  # DI
    cpu.cycle()
    assert cpu.interrupts is False

    # Enable interrupts
    cpu.insert_instruction(bytearray([0xFB]))  # EI
    cpu.cycle()
    assert cpu.interrupts is True

import pytest

from gbemu.config import (
    M_DIVIDER,
    M_INTERRUPT_FLAG,
    M_TIMER_CONTROL,
    M_TIMER_COUNTER,
    M_TIMER_MODULO,
    MEMORY_SIZE,
)
from gbemu.timer import Timer


def make_memory() -> list[int]:
    return [0] * MEMORY_SIZE


def test_timer_tick_ignores_non_positive_cycles() -> None:
    timer = Timer()
    memory = make_memory()
    memory[M_DIVIDER] = 0x12
    memory[M_TIMER_COUNTER] = 0x34

    timer.tick(memory, 0)
    timer.tick(memory, -4)

    assert memory[M_DIVIDER] == 0x12
    assert memory[M_TIMER_COUNTER] == 0x34


def test_timer_divider_increments_every_256_cycles() -> None:
    timer = Timer()
    memory = make_memory()

    timer.tick(memory, 255)
    assert memory[M_DIVIDER] == 0x00

    timer.tick(memory, 1)
    assert memory[M_DIVIDER] == 0x01

    timer.tick(memory, 512)
    assert memory[M_DIVIDER] == 0x03


def test_timer_divider_wraps_at_8_bits() -> None:
    timer = Timer()
    memory = make_memory()
    memory[M_DIVIDER] = 0xFF

    timer.tick(memory, 256)

    assert memory[M_DIVIDER] == 0x00


def test_timer_disabled_does_not_increment_tima() -> None:
    timer = Timer()
    memory = make_memory()
    memory[M_TIMER_COUNTER] = 0x7A
    memory[M_TIMER_CONTROL] = 0x00

    timer.tick(memory, 4096)

    assert memory[M_TIMER_COUNTER] == 0x7A
    assert (memory[M_INTERRUPT_FLAG] & 0x04) == 0


@pytest.mark.parametrize(
    ("tac_bits", "period"),
    [
        (0x00, 1024),
        (0x01, 16),
        (0x02, 64),
        (0x03, 256),
    ],
)
def test_timer_frequency_selection_controls_increment_period(
    tac_bits: int,
    period: int,
) -> None:
    timer = Timer()
    memory = make_memory()
    memory[M_TIMER_CONTROL] = 0x04 | tac_bits

    timer.tick(memory, period - 1)
    assert memory[M_TIMER_COUNTER] == 0x00

    timer.tick(memory, 1)
    assert memory[M_TIMER_COUNTER] == 0x01


def test_timer_accumulates_cycles_across_multiple_ticks() -> None:
    timer = Timer()
    memory = make_memory()
    memory[M_TIMER_CONTROL] = 0x05

    for _ in range(3):
        timer.tick(memory, 5)

    assert memory[M_TIMER_COUNTER] == 0x00

    timer.tick(memory, 1)

    assert memory[M_TIMER_COUNTER] == 0x01


def test_timer_can_increment_multiple_times_in_single_tick() -> None:
    timer = Timer()
    memory = make_memory()
    memory[M_TIMER_CONTROL] = 0x05

    timer.tick(memory, 48)

    assert memory[M_TIMER_COUNTER] == 0x03


def test_timer_overflow_reloads_tma_and_requests_interrupt() -> None:
    timer = Timer()
    memory = make_memory()
    memory[M_TIMER_CONTROL] = 0x05
    memory[M_TIMER_COUNTER] = 0xFF
    memory[M_TIMER_MODULO] = 0xAB

    timer.tick(memory, 16)

    assert memory[M_TIMER_COUNTER] == 0xAB
    assert (memory[M_INTERRUPT_FLAG] & 0x04) == 0x04


def test_timer_overflow_then_continues_incrementing_in_same_tick() -> None:
    timer = Timer()
    memory = make_memory()
    memory[M_TIMER_CONTROL] = 0x05
    memory[M_TIMER_COUNTER] = 0xFF
    memory[M_TIMER_MODULO] = 0x20

    timer.tick(memory, 32)

    assert memory[M_TIMER_COUNTER] == 0x21
    assert (memory[M_INTERRUPT_FLAG] & 0x04) == 0x04


def test_timer_preserves_pending_interrupt_flag_bits() -> None:
    timer = Timer()
    memory = make_memory()
    memory[M_TIMER_CONTROL] = 0x05
    memory[M_TIMER_COUNTER] = 0xFF
    memory[M_TIMER_MODULO] = 0x77
    memory[M_INTERRUPT_FLAG] = 0x01

    timer.tick(memory, 16)

    assert memory[M_INTERRUPT_FLAG] == 0x05

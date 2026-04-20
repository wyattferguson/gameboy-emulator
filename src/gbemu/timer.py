"""

This module emulates DIV/TIMA/TMA/TAC timing and timer interrupt generation.

Step-by-step:
1. Accumulate elapsed CPU cycles each instruction.
2. Advance DIV on its fixed 256-cycle cadence.
3. Check TAC enable/frequency bits for TIMA progression.
4. Increment TIMA or reload from TMA on overflow.
5. Request timer interrupt when overflow reload occurs.
"""

from gbemu.config import (
    M_DIVIDER,
    M_INTERRUPT_FLAG,
    M_TIMER_CONTROL,
    M_TIMER_COUNTER,
    M_TIMER_MODULO,
    TIMER_PERIODS,
)


class Timer:
    """DMG timer unit (DIV/TIMA/TMA/TAC)."""

    def __init__(self) -> None:
        """Initialize internal cycle accumulators for DIV and TIMA clocks."""
        self._div_cycle_accumulator: int = 0
        self._timer_cycle_accumulator: int = 0

    def tick(self, memory: list[int], elapsed_cycles: int) -> None:
        """Advance DIV/TIMA according to elapsed CPU cycles."""
        if elapsed_cycles <= 0:
            return

        self._tick_div(memory, elapsed_cycles)
        self._tick_tima(memory, elapsed_cycles)

    def _tick_div(self, memory: list[int], elapsed_cycles: int) -> None:
        """Accumulate cycles and update DIV at its fixed 256-cycle cadence."""
        # DIV increments at 16384 Hz -> every 256 CPU cycles.
        self._div_cycle_accumulator += elapsed_cycles
        div_increments = self._div_cycle_accumulator // 256
        if div_increments:
            self._div_cycle_accumulator %= 256
            memory[M_DIVIDER] = (memory[M_DIVIDER] + div_increments) & 0xFF

    def _tick_tima(self, memory: list[int], elapsed_cycles: int) -> None:
        """Advance TIMA according to TAC frequency and request timer interrupt on overflow."""
        timer_control = memory[M_TIMER_CONTROL]
        if (timer_control & 0x04) == 0:
            return

        timer_period = TIMER_PERIODS[timer_control & 0x03]

        self._timer_cycle_accumulator += elapsed_cycles
        while self._timer_cycle_accumulator >= timer_period:
            self._timer_cycle_accumulator -= timer_period
            if memory[M_TIMER_COUNTER] == 0xFF:
                memory[M_TIMER_COUNTER] = memory[M_TIMER_MODULO]
                memory[M_INTERRUPT_FLAG] |= 0x04
            else:
                memory[M_TIMER_COUNTER] = (memory[M_TIMER_COUNTER] + 1) & 0xFF

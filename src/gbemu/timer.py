from gbemu.constants import (
    M_DIVIDER,
    M_INTERRUPT_FLAG,
    M_TIMER_CONTROL,
    M_TIMER_COUNTER,
    M_TIMER_MODULO,
    TIMER_PERIODS,
)

# DIV register runs on a fixed 256-cycle period (16384 Hz at 4 MHz).
_DIV_PERIOD = 256

# TAC bit 2 is the timer-enable flag.
_TAC_ENABLE_BIT = 0x04

# TAC bits 0-1 select the TIMA clock frequency index into TIMER_PERIODS.
_TAC_CLOCK_MASK = 0x03


class Timer:
    """DMG timer unit (DIV / TIMA / TMA / TAC)."""

    def __init__(self) -> None:
        """Initialise sub-cycle accumulators for DIV and TIMA clocks."""
        self._div_cycle_accumulator: int = 0
        self._timer_cycle_accumulator: int = 0

    def tick(self, memory: list[int], elapsed_cycles: int) -> None:
        """Advance both the DIV and TIMA clocks by elapsed_cycles."""
        if elapsed_cycles <= 0:
            return
        self._tick_div(memory, elapsed_cycles)
        self._tick_tima(memory, elapsed_cycles)

    def _tick_div(self, memory: list[int], elapsed_cycles: int) -> None:
        """Increment DIV for every full 256-cycle period in elapsed_cycles."""
        self._div_cycle_accumulator += elapsed_cycles
        increments, self._div_cycle_accumulator = divmod(self._div_cycle_accumulator, _DIV_PERIOD)
        if increments:
            memory[M_DIVIDER] = (memory[M_DIVIDER] + increments) & 0xFF

    def _tick_tima(self, memory: list[int], elapsed_cycles: int) -> None:
        """Increment TIMA at the TAC-selected rate, reloading from TMA on overflow."""
        tac = memory[M_TIMER_CONTROL]
        if not (tac & _TAC_ENABLE_BIT):
            return

        period = TIMER_PERIODS[tac & _TAC_CLOCK_MASK]
        self._timer_cycle_accumulator += elapsed_cycles

        # Step TIMA one tick at a time so each overflow correctly reloads TMA.
        while self._timer_cycle_accumulator >= period:
            self._timer_cycle_accumulator -= period
            if memory[M_TIMER_COUNTER] == 0xFF:
                # Overflow: reload from TMA and request timer interrupt.
                memory[M_TIMER_COUNTER] = memory[M_TIMER_MODULO]
                memory[M_INTERRUPT_FLAG] |= 0x04
            else:
                memory[M_TIMER_COUNTER] += 1

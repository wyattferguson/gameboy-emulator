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
        self._div_cycle_accumulator: int = 0
        self._timer_cycle_accumulator: int = 0

    def tick(self, memory: list[int], elapsed_cycles: int) -> None:
        """Advance DIV/TIMA according to elapsed CPU cycles."""
        if elapsed_cycles <= 0:
            return

        # DIV increments at 16384 Hz -> every 256 CPU cycles.
        self._div_cycle_accumulator += elapsed_cycles
        while self._div_cycle_accumulator >= 256:
            self._div_cycle_accumulator -= 256
            memory[M_DIVIDER] = (memory[M_DIVIDER] + 1) & 0xFF

        timer_control = memory[M_TIMER_CONTROL]
        timer_enabled = bool(timer_control & 0x04)
        if not timer_enabled:
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

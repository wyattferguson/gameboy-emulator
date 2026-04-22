"""

This module translates host keyboard events into DMG joypad register state changes.

Step-by-step:
1. Bind controller logic to the MMU joypad interface.
2. Poll pygame events each frame.
3. Detect quit/escape events for clean emulator shutdown.
4. Map key transitions to dpad/button bit masks.
5. Update JOYP and request joypad interrupts through MMU logic.
"""

import sys

import pygame as pg

from gbemu.config import KEYMAP
from gbemu.constants import M_INTERRUPT_FLAG, M_JOYPAD
from gbemu.mmu import MMU


class Controller:
    """Gameboy Controller."""

    def __init__(self, mmu: MMU) -> None:
        """Bind MMU input lines and initialize JOYP select state."""
        self.mmu = mmu
        self._buttons = 0x0F
        self._dpad = 0x0F
        self.mmu.register_joypad_refresh_hook(self._sync_joypad_register)
        self.mmu[M_JOYPAD] = 0x30

    def _sync_joypad_register(self) -> None:
        """Compose FF00 from select bits and controller latched key states."""
        select = self.mmu.memory[M_JOYPAD] & 0x30
        joypad = 0xCF | select
        if (select & 0x10) == 0:
            joypad &= 0xF0 | self._dpad
        if (select & 0x20) == 0:
            joypad &= 0xF0 | self._buttons
        self.mmu.memory[M_JOYPAD] = joypad & 0xFF

    @staticmethod
    def _is_exit_event(event: pg.event.Event) -> bool:
        """Return True when an event should terminate emulation."""
        return event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE)

    def set_key_state(self, bits: int, *, dpad: bool, pressed: bool) -> None:
        """Update pressed state for one joypad line."""
        target = self._dpad if dpad else self._buttons
        previous = target
        if pressed:
            target &= (~bits) & 0x0F
        else:
            target |= bits & 0x0F

        if dpad:
            self._dpad = target
        else:
            self._buttons = target

        if previous != target and pressed:
            self.mmu.memory[M_INTERRUPT_FLAG] |= 0x10

        self._sync_joypad_register()

    def _handle_input_event(self, event: pg.event.Event) -> None:
        """Map keyboard key transitions into JOYP line updates."""
        if event.type not in (pg.KEYDOWN, pg.KEYUP):
            return

        keybind = KEYMAP.get(event.key)
        if keybind is None:
            return

        bits, dpad = keybind
        self.set_key_state(bits, dpad=dpad, pressed=event.type == pg.KEYDOWN)

    def update(self) -> None:
        """Check for key presses and update JOYPAD state."""
        for event in pg.event.get():
            # Press ESCAPE to quit emulator
            if self._is_exit_event(event):
                pg.quit()
                sys.exit()
            self._handle_input_event(event)

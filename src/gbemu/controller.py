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

from gbemu.config import KEYMAP, M_JOYPAD
from gbemu.mmu import MMU


class Controller:
    """Gameboy Controller."""

    def __init__(self, mmu: MMU) -> None:
        """Bind MMU input lines and initialize JOYP select state."""
        self.mmu = mmu
        self.mmu[M_JOYPAD] = 0x30

    @staticmethod
    def _is_exit_event(event: pg.event.Event) -> bool:
        """Return True when an event should terminate emulation."""
        return event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE)

    def set_key_state(self, bits: int, *, dpad: bool, pressed: bool) -> None:
        """Update pressed state for one joypad line."""
        self.mmu.set_joypad_pressed(bits, dpad=dpad, pressed=pressed)

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

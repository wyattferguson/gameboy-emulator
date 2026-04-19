import sys

import pygame as pg

from gbemu.config import M_JOYPAD
from gbemu.mmu import MMU

KEYMAP: dict[int, tuple[int, bool]] = {
    pg.K_UP: (0b0100, True),
    pg.K_w: (0b0100, True),
    pg.K_DOWN: (0b1000, True),
    pg.K_s: (0b1000, True),
    pg.K_LEFT: (0b0010, True),
    pg.K_RIGHT: (0b0001, True),
    pg.K_d: (0b0001, True),
    pg.K_a: (0b0001, False),
    pg.K_j: (0b0001, False),
    pg.K_b: (0b0010, False),
    pg.K_k: (0b0010, False),
    pg.K_RETURN: (0b1000, False),
    pg.K_LSHIFT: (0x0100, False),
    pg.K_RSHIFT: (0x0100, False),
}


class Controller:
    """Gameboy Controller."""

    def __init__(self, mmu: MMU) -> None:
        self.mmu = mmu
        self.mmu[M_JOYPAD] = 0xFF  # Set all buttons to not pressed
        self.dpad_pressed = False

    def flip(self, bits: int, dpad: bool = False) -> None:
        """Set pressed buttons."""
        # Reset dpad / button flags
        if self.dpad_pressed != dpad:
            self.mmu[M_JOYPAD] = 0xEF if dpad else 0xDF
            self.dpad_pressed = dpad
        # Flip the bits of the pressed buttons
        self.mmu[M_JOYPAD] ^= bits

    def update(self) -> None:
        """Check for key presses and update JOYPAD state."""
        for event in pg.event.get():
            # Press ESCAPE to quit emulator
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            if event.type not in (pg.KEYDOWN, pg.KEYUP):
                continue

            keybind = KEYMAP.get(event.key)
            if keybind is None:
                continue

            bits, dpad = keybind
            self.flip(bits, dpad)

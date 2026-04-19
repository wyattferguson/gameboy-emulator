import sys

import pygame as pg

from gbemu.config import M_JOYPAD
from gbemu.mmu import MMU


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
            elif event.type in (pg.KEYDOWN, pg.KEYUP):
                match event.key:
                    case pg.K_UP:
                        self.flip(0b0100, True)
                    case pg.K_DOWN:
                        self.flip(0b1000, True)
                    case pg.K_LEFT:
                        self.flip(0b0010, True)
                    case pg.K_RIGHT:
                        self.flip(0b0001, True)
                    case pg.K_a:
                        self.flip(0b0001)
                    case pg.K_b:
                        self.flip(0b0010)
                    case pg.K_RETURN:
                        self.flip(0b1000)
                    case pg.K_LSHIFT:
                        self.flip(0x0100)
                    case _:
                        pass

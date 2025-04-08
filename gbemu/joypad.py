import pygame as pg

from ._config import JOYPAD_MEM
from .ram import RAM


class Joypad:
    def __init__(self, ram: RAM):
        self.ram = ram
        self.ram[JOYPAD_MEM] = 0xFF  # Set all buttons to not pressed

    def flip(self, bits: int, dpad: bool = False) -> None:
        """Set pressed buttons."""
        # Reset dpad / button flags
        self.ram[JOYPAD_MEM] = (self.ram[JOYPAD_MEM] | 0xF0) ^ 0x10 if dpad else 0x20
        # Flip the bits of the pressed buttons
        self.ram[JOYPAD_MEM] ^= bits

    def update(self) -> None:
        for event in pg.event.get():
            # Press ESCAPE to quit emulator
            if event.type == pg.QUIT or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                exit()
            elif event.type == pg.KEYDOWN or event.type == pg.KEYUP:
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

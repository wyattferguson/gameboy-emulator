import pygame as pg

from ._config import M_JOYPAD
from .ram import RAM


class Joypad:
    def __init__(self, ram: RAM):
        self.ram = ram
        self.ram[M_JOYPAD] = 0xFF  # Set all buttons to not pressed
        self.dpad_pressed = False

    def flip(self, bits: int, dpad: bool = False) -> None:
        """Set pressed buttons."""
        # Reset dpad / button flags
        if self.dpad_pressed != dpad:
            self.ram[M_JOYPAD] = 0xEF if dpad else 0xDF
            self.dpad_pressed = dpad
        # Flip the bits of the pressed buttons
        self.ram[M_JOYPAD] ^= bits

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

    def __str__(self) -> str:
        return (
            f"Joypad State:\n"
            f"JOYPAD: {self.ram[M_JOYPAD]}\n"
            f"Up/Select : {(self.ram[M_JOYPAD] & 0b0100) == 0}\n"
            f"Down/Start: {(self.ram[M_JOYPAD] & 0b1000) == 0}\n"
            f"Right/A: {(self.ram[M_JOYPAD] & 0b0001) == 0}\n"
            f"Left/B: {(self.ram[M_JOYPAD] & 0b0010) == 0}\n"
            f"{'D-Pad' if self.dpad_pressed else 'Button'} Pressed\n"
        )

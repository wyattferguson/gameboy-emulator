import pygame as pg

from gbemu.config import DISPLAY_SCALER, SCREEN_HEIGHT, SCREEN_WIDTH


class Screen:
    def __init__(self) -> None:
        pg.init()
        pg.display.set_caption("Gameboy Emulator")
        self.screen_size = (SCREEN_WIDTH * DISPLAY_SCALER, SCREEN_HEIGHT * DISPLAY_SCALER)
        self.screen = pg.display.set_mode(self.screen_size)

    def update(self) -> None:
        pg.display.update()

    def clear_screen(self) -> None:
        """Black out entire screen"""
        self.screen.fill((0, 0, 0))

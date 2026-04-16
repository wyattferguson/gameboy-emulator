import pygame as pg

from gbemu.config import BG_COLOR, DISPLAY_SCALER, SCREEN_HEIGHT, SCREEN_WIDTH


class Screen:
    """GB Screen."""

    def __init__(self, scaler: int = DISPLAY_SCALER) -> None:
        pg.init()
        pg.display.set_caption("Gameboy Emulator")
        self.scaler = scaler
        self.screen_size = (SCREEN_WIDTH * scaler, SCREEN_HEIGHT * scaler)
        self.screen = pg.display.set_mode(self.screen_size)
        self.clear_screen()

    def update(self) -> None:
        """Update the display."""
        pg.display.update()

    def clear_screen(self) -> None:
        """Black out entire screen."""
        self.screen.fill(BG_COLOR)

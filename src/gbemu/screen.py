from time import sleep

import pygame as pg

from gbemu.config import BG_COLOR, DISPLAY_SCALER, ERROR_COLOR, PALLETE, SCREEN_HEIGHT, SCREEN_WIDTH
from gbemu.ctypes import Color


class Screen:
    """GB Screen."""

    def __init__(self, scaler: int = DISPLAY_SCALER) -> None:
        self.pg = pg
        self.pg.init()
        self.pg.display.set_caption("Gameboy Emulator")
        self.scaler = scaler
        self.palette = PALLETE
        self.screen_size = (SCREEN_WIDTH * scaler, SCREEN_HEIGHT * scaler)
        self.screen = self.pg.display.set_mode(self.screen_size)
        self.clear_screen()

    def update(self) -> None:
        """Update the display."""
        # # fmt: off
        # logo = [[0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B, 0x03, 0x73, 0x00, 0x83, 0x00, 0x0C, 0x00, 0x0D],
        #         [0x00, 0x08, 0x11, 0x1F, 0x88, 0x89, 0x00, 0x0E, 0xDC, 0xCC, 0x6E, 0xE6, 0xDD, 0xDD, 0xD9, 0x99],
        #         [0xBB, 0xBB, 0x67, 0x63, 0x6E, 0x0E, 0xEC, 0xCC, 0xDD, 0xDC, 0x99, 0x9F, 0xBB, 0xB9, 0x33, 0x3E]]
        # # fmt: on
        # # logo = [[0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B]]
        # for tile in range(len(logo)):
        #     self.ds(logo[tile], 0, tile + 1)
        # # sleep(60)
        self.pg.display.update()

    def draw_buffer(self, buffer: list[list[int]]) -> None:
        """Draw entire buffer to screen."""
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                color_id: int = buffer[y][x]
                color: Color = self.color_from_id(color_id)
                self.draw_pixel(x, y, color)

    def color_from_id(self, color_id: int) -> Color:
        """Convert a color ID to an RGB color."""
        return self.palette[color_id] if color_id < len(self.palette) else ERROR_COLOR

    def draw_pixel(self, x: int, y: int, color: Color) -> None:
        """Draw a pixel on the screen."""
        rect = self.pg.Rect(x * self.scaler, y * self.scaler, self.scaler, self.scaler)
        self.pg.draw.rect(self.screen, color, rect)

    def clear_screen(self) -> None:
        """Wipe entire screen."""
        self.screen.fill(BG_COLOR)

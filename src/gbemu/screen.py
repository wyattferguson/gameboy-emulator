import pygame as pg

from gbemu.config import BG_COLOR, DISPLAY_SCALER, ERROR_COLOR, PALLETE, SCREEN_HEIGHT, SCREEN_WIDTH
from gbemu.ctypes import Color


class Screen:
    """GB Screen."""

    def __init__(self, scaler: int = DISPLAY_SCALER) -> None:
        pg.init()
        pg.display.set_caption("Gameboy Emulator")
        self.scaler = scaler
        self.palette = PALLETE
        self.screen_size = (SCREEN_WIDTH * scaler, SCREEN_HEIGHT * scaler)
        self.screen = pg.display.set_mode(self.screen_size)
        self.clear_screen()

    def update(self) -> None:
        """Update the display."""
        pg.display.flip()

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
        rect = pg.Rect(x * self.scaler, y * self.scaler, self.scaler, self.scaler)
        pg.draw.rect(self.screen, color, rect)

    def draw_tile(self, tile_data: list[int], x: int, y: int) -> None:
        """Draw a tile on the screen."""
        for i in range(8):
            byte1 = tile_data[i * 2]
            byte2 = tile_data[i * 2 + 1]
            for j in range(8):
                color_id = ((byte2 >> (7 - j)) & 1) << 1 | ((byte1 >> (7 - j)) & 1)
                color: Color = self.color_from_id(color_id)
                self.draw_pixel(x + j, y + i, color)

    # def draw_background(self, bg_data: list[int]) -> None:
    #     """Draw the background on the screen."""
    #     for i in range(32):
    #         for j in range(32):
    #             tile_index = bg_data[i * 32 + j]
    #             tile_data = self.get_tile_data(tile_index)
    #             self.draw_tile(tile_data, j * 8, i * 8)

    # def draw_window(self, window_data: list[int], x: int, y: int) -> None:
    #     """Draw the window on the screen."""
    #     for i in range(32):
    #         for j in range(32):
    #             tile_index = window_data[i * 32 + j]
    #             tile_data = self.get_tile_data(tile_index)
    #             self.draw_tile(tile_data, x + j * 8, y + i * 8)

    def clear_screen(self) -> None:
        """Wipe entire screen."""
        self.screen.fill(BG_COLOR)

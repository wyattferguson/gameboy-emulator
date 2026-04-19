import pygame as pg

from gbemu.config import BG_COLOR, DISPLAY_SCALER, ERROR_COLOR, PALLETE, SCREEN_HEIGHT, SCREEN_WIDTH
from gbemu.ctypes import Color


class Screen:
    """GB Screen."""

    def __init__(self, scaler: int = DISPLAY_SCALER) -> None:
        self.pg = pg
        # Initialize the display backend and window surface.
        self.pg.init()
        self.pg.display.set_caption("Gameboy Emulator")
        self.scaler = scaler
        self.palette = PALLETE
        self.screen_size = (SCREEN_WIDTH * scaler, SCREEN_HEIGHT * scaler)
        self.screen = self.pg.display.set_mode(self.screen_size)
        self._pixel_buffer = bytearray(SCREEN_WIDTH * SCREEN_HEIGHT * 3)
        self._frame_surface = self.pg.image.frombuffer(
            self._pixel_buffer,
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            "RGB",
        )
        self._bg_frame = bytes(BG_COLOR) * (SCREEN_WIDTH * SCREEN_HEIGHT)
        self.clear_screen()

    def update(self) -> None:
        """Update the display."""
        scaled_surface = self.pg.transform.scale(self._frame_surface, self.screen_size)
        self.screen.blit(scaled_surface, (0, 0))
        self.pg.display.update()

    def draw_buffer(self, buffer: list[list[int]]) -> None:
        """Draw a buffer of color IDs to the screen."""
        # Frame-level helper: route each row through the scanline renderer.
        for y, row in enumerate(buffer):
            self.draw_scanline(row, y)

    def draw_scanline(self, color_ids: list[int], y: int) -> None:
        """Draw one scanline of color IDs at a given y coordinate."""
        if y < 0 or y >= SCREEN_HEIGHT:
            return

        row_offset = y * SCREEN_WIDTH * 3
        for x, color_id in enumerate(color_ids[:SCREEN_WIDTH]):
            red, green, blue = self.color_from_id(color_id)
            pixel_offset = row_offset + (x * 3)
            self._pixel_buffer[pixel_offset] = red
            self._pixel_buffer[pixel_offset + 1] = green
            self._pixel_buffer[pixel_offset + 2] = blue

    def color_from_id(self, color_id: int) -> Color:
        """Convert a color ID to an RGB color."""
        return self.palette[color_id] if color_id < len(self.palette) else ERROR_COLOR

    def draw_pixel(self, x: int, y: int, color: Color) -> None:
        """Draw a pixel on the screen."""
        pixel_offset = (y * SCREEN_WIDTH + x) * 3
        self._pixel_buffer[pixel_offset] = color[0]
        self._pixel_buffer[pixel_offset + 1] = color[1]
        self._pixel_buffer[pixel_offset + 2] = color[2]
        rect = self.pg.Rect(x * self.scaler, y * self.scaler, self.scaler, self.scaler)
        self.pg.draw.rect(self.screen, color, rect)

    def clear_screen(self) -> None:
        """Wipe entire screen."""
        self._pixel_buffer[:] = self._bg_frame
        self.screen.fill(BG_COLOR)

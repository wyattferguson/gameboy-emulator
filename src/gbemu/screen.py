import pygame as pg

from gbemu.config import BG_COLOR, DISPLAY_SCALER, ERROR_COLOR, PALLETE, SCREEN_HEIGHT, SCREEN_WIDTH
from gbemu.ctypes import Color


class Screen:
    """Hardware-like front buffer for DMG color IDs."""

    def __init__(self, scaler: int = DISPLAY_SCALER) -> None:
        self.pg = pg
        self.pg.init()
        self.pg.display.set_caption("Gameboy Emulator")

        self.scaler = scaler
        self.palette = PALLETE
        self.screen_size = (SCREEN_WIDTH * scaler, SCREEN_HEIGHT * scaler)
        self.screen = self.pg.display.set_mode(self.screen_size)

        # One byte per pixel stores DMG palette slot (0..3).
        self._color_ids = bytearray(SCREEN_WIDTH * SCREEN_HEIGHT)
        # RGB front buffer used for display upload.
        self._pixel_rgb = bytearray(SCREEN_WIDTH * SCREEN_HEIGHT * 3)
        self._frame_surface = self.pg.image.frombuffer(
            self._pixel_rgb,
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            "RGB",
        )
        self._clear_rgb = bytes(BG_COLOR) * (SCREEN_WIDTH * SCREEN_HEIGHT)

        self.clear_screen()

    def update(self) -> None:
        """Present the current frame buffer to the pygame window."""
        scaled = self.pg.transform.scale(self._frame_surface, self.screen_size)
        self.screen.blit(scaled, (0, 0))
        self.pg.display.update()

    def draw_buffer(self, buffer: list[list[int]]) -> None:
        """Draw a full frame represented as scanlines of palette IDs."""
        for y, row in enumerate(buffer[:SCREEN_HEIGHT]):
            self.draw_scanline(row, y)

    def draw_scanline(self, color_ids: list[int], y: int) -> None:
        """Draw one scanline of DMG palette slots into the RGB back buffer."""
        if y < 0 or y >= SCREEN_HEIGHT:
            return

        y_offset_ids = y * SCREEN_WIDTH
        y_offset_rgb = y * SCREEN_WIDTH * 3

        for x, color_id in enumerate(color_ids[:SCREEN_WIDTH]):
            palette_slot = color_id & 0x03
            self._color_ids[y_offset_ids + x] = palette_slot
            red, green, blue = self.color_from_id(palette_slot)

            pixel_offset = y_offset_rgb + x * 3
            self._pixel_rgb[pixel_offset] = red
            self._pixel_rgb[pixel_offset + 1] = green
            self._pixel_rgb[pixel_offset + 2] = blue

    def color_from_id(self, color_id: int) -> Color:
        """Translate a DMG palette slot to an RGB tuple."""
        if 0 <= color_id < len(self.palette):
            return self.palette[color_id]
        return ERROR_COLOR

    def draw_pixel(self, x: int, y: int, color: Color) -> None:
        """Plot one pixel directly to both software and pygame frame targets."""
        if x < 0 or x >= SCREEN_WIDTH or y < 0 or y >= SCREEN_HEIGHT:
            return

        pixel_offset = (y * SCREEN_WIDTH + x) * 3
        self._pixel_rgb[pixel_offset] = color[0]
        self._pixel_rgb[pixel_offset + 1] = color[1]
        self._pixel_rgb[pixel_offset + 2] = color[2]

        rect = self.pg.Rect(x * self.scaler, y * self.scaler, self.scaler, self.scaler)
        self.pg.draw.rect(self.screen, color, rect)

    def clear_screen(self) -> None:
        """Reset frame buffers and fill the output surface with BG color."""
        self._color_ids[:] = bytes([0]) * (SCREEN_WIDTH * SCREEN_HEIGHT)
        self._pixel_rgb[:] = self._clear_rgb
        self.screen.fill(BG_COLOR)

"""

This module manages framebuffer composition and pygame presentation for DMG palette output.

Step-by-step:
1. Initialize software buffers and pygame display surfaces.
2. Accept scanline or pixel writes as DMG color IDs/RGB values.
3. Translate palette slots into RGB bytes in the frame buffer.
4. Scale and blit the frame surface to the output window.
5. Optionally render FPS overlay diagnostics each presented frame.
"""

import itertools

import pygame as pg

from gbemu.config import (
    BG_COLOR,
    DISPLAY_SCALER,
    FPS_BG_COLOR,
    FPS_COLOR,
    PALLETE,
    SCREEN_AREA,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHOW_FPS_OVERLAY,
)
from gbemu.ctypes import Color


class Screen:
    """GB Display Screen."""

    def __init__(
        self,
        scaler: int = DISPLAY_SCALER,
        show_fps_overlay: bool = SHOW_FPS_OVERLAY,
    ) -> None:
        """Initialize pygame surfaces and software frame buffers."""
        self.pg = pg
        self.pg.init()
        self.pg.display.set_caption("Gameboy Emulator")

        self.scaler = scaler
        self.palette = PALLETE
        self.show_fps_overlay = show_fps_overlay
        self._fps_value: float = 0.0
        self.screen_size = (SCREEN_WIDTH * scaler, SCREEN_HEIGHT * scaler)
        self.screen = self.pg.display.set_mode(self.screen_size)

        # Each pixel's color ID (0-3) is stored as one byte in this buffer.
        self._color_ids = bytearray(SCREEN_AREA)

        # Each pixel is 3 bytes (RGB) in the frame buffer.
        self._screen_buffer = bytearray(SCREEN_AREA * 3)
        self._frame_surface = self.pg.image.frombuffer(
            self._screen_buffer,
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            "RGB",
        )
        frame_bitsize = self._frame_surface.get_bitsize()
        frame_masks = self._frame_surface.get_masks()
        self._scaled_surface = self.pg.Surface(
            self.screen_size,
            depth=frame_bitsize,
            masks=frame_masks,
        )
        self._fps_font = self.pg.font.Font(None, 24)
        self._clear_rgb = bytes(BG_COLOR) * SCREEN_AREA

        # Pre-compute 3-byte RGB entries for each of the 4 palette slots.
        self._palette_bytes: list[bytes] = [bytes(color) for color in self.palette]

        self.clear_screen()

    def update(self) -> None:
        """Draw frame buffer and FPS overlay."""
        self.pg.transform.scale(self._frame_surface, self.screen_size, self._scaled_surface)
        self.screen.blit(self._scaled_surface, (0, 0))
        self._draw_fps_overlay()
        self.pg.display.flip()

    def set_fps(self, fps: float) -> None:
        """Update the FPS value used by the overlay."""
        self._fps_value = fps

    def toggle_fps_overlay(self) -> None:
        """Toggle the FPS overlay on or off."""
        self.show_fps_overlay = not self.show_fps_overlay

    def _draw_fps_overlay(self) -> None:
        """Render the FPS counter text in the top-right corner."""
        if not self.show_fps_overlay:
            return

        overlay = self._fps_font.render(
            f"{self._fps_value:5.0f} FPS",
            True,
            FPS_COLOR,
            FPS_BG_COLOR,
        )
        x = self.screen_size[0] - overlay.get_width()
        self.screen.blit(overlay, (x, 0))

    def draw_buffer(self, buffer: list[list[int]]) -> None:
        """Draw a full frame represented as scanlines of palette IDs."""
        # chain.from_iterable + islice avoids per-row slice copies.
        slots = bytearray(
            cid & 0x03
            for cid in itertools.chain.from_iterable(
                itertools.islice(row, SCREEN_WIDTH)
                for row in itertools.islice(buffer, SCREEN_HEIGHT)
            )
        )
        self._color_ids[: len(slots)] = slots
        self._screen_buffer[: len(slots) * 3] = b"".join(self._palette_bytes[s] for s in slots)

    def draw_scanline(self, color_ids: list[int], y: int) -> None:
        """Draw one scanline of DMG palette slots into the RGB back buffer."""
        n = min(len(color_ids), SCREEN_WIDTH)
        y_offset_ids = y * SCREEN_WIDTH
        y_offset_rgb = y * SCREEN_WIDTH * 3

        # islice avoids a list copy; iterate values directly instead of by index.
        slots = bytearray(c & 0x03 for c in itertools.islice(color_ids, n))
        self._color_ids[y_offset_ids : y_offset_ids + n] = slots
        self._screen_buffer[y_offset_rgb : y_offset_rgb + n * 3] = b"".join(
            self._palette_bytes[s] for s in slots
        )

    def _set_pixel_at_offset(self, pixel_offset: int, color: Color) -> None:
        """Write one RGB triple into the screen buffer."""
        self._screen_buffer[pixel_offset : pixel_offset + 3] = color

    def draw_pixel(self, x: int, y: int, color: Color) -> None:
        """Draw pixel to both software and pygame."""
        pixel_offset = (y * SCREEN_WIDTH + x) * 3
        self._set_pixel_at_offset(pixel_offset, color)

        rect = self.pg.Rect(x * self.scaler, y * self.scaler, self.scaler, self.scaler)
        self.pg.draw.rect(self.screen, color, rect)

    def clear_screen(self) -> None:
        """Reset frame buffers and fill the output surface with BG color."""
        self._color_ids[:] = bytes(SCREEN_AREA)
        self._screen_buffer[:] = self._clear_rgb
        self.screen.fill(BG_COLOR)

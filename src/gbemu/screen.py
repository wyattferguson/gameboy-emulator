import pygame as pg

from gbemu.config import (
    BG_COLOR,
    DISPLAY_SCALER,
    ERROR_COLOR,
    FPS_OVERLAY_COLOR,
    FPS_OVERLAY_MARGIN,
    PALLETE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHOW_FPS_OVERLAY,
)
from gbemu.ctypes import Color


class Screen:
    """Hardware-like front buffer for DMG color IDs."""

    def __init__(
        self,
        scaler: int = DISPLAY_SCALER,
        show_fps_overlay: bool = SHOW_FPS_OVERLAY,
    ) -> None:
        self.pg = pg
        self.pg.init()
        self.pg.display.set_caption("Gameboy Emulator")

        self.scaler = scaler
        self.palette = PALLETE
        self.show_fps_overlay = show_fps_overlay
        self._fps_value: float | None = None
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
        frame_bitsize = self._frame_surface.get_bitsize()
        frame_masks = self._frame_surface.get_masks()
        self._scaled_surface = self.pg.Surface(
            self.screen_size,
            depth=frame_bitsize,
            masks=frame_masks,
        )
        self._fps_font = self.pg.font.Font(None, 18) if self.show_fps_overlay else None
        self._clear_rgb = bytes(BG_COLOR) * (SCREEN_WIDTH * SCREEN_HEIGHT)

        self.clear_screen()

    def update(self) -> None:
        """Present the current frame buffer to the pygame window."""
        self.pg.transform.scale(self._frame_surface, self.screen_size, self._scaled_surface)
        self.screen.blit(self._scaled_surface, (0, 0))
        self._draw_fps_overlay()
        self.pg.display.update()

    def set_fps(self, fps: float) -> None:
        """Update the FPS value used by the optional overlay."""
        if fps > 0:
            self._fps_value = fps

    def _draw_fps_overlay(self) -> None:
        if not self.show_fps_overlay or self._fps_font is None:
            return

        fps_text = f"{self._fps_value:5.1f} FPS" if self._fps_value is not None else " --.- FPS"
        overlay = self._fps_font.render(fps_text, True, FPS_OVERLAY_COLOR)
        shadow = self._fps_font.render(fps_text, True, (0, 0, 0))
        x = self.screen_size[0] - overlay.get_width() - FPS_OVERLAY_MARGIN
        y = FPS_OVERLAY_MARGIN
        self.screen.blit(shadow, (x + 1, y + 1))
        self.screen.blit(overlay, (x, y))

    def draw_buffer(self, buffer: list[list[int]]) -> None:
        """Draw a full frame represented as scanlines of palette IDs."""
        for y, row in enumerate(buffer):
            if y >= SCREEN_HEIGHT:
                break
            self.draw_scanline(row, y)

    def draw_scanline(self, color_ids: list[int], y: int) -> None:
        """Draw one scanline of DMG palette slots into the RGB back buffer."""
        if y < 0 or y >= SCREEN_HEIGHT:
            return

        palette = self.palette
        palette_len = len(palette)
        y_offset_ids = y * SCREEN_WIDTH
        y_offset_rgb = y * SCREEN_WIDTH * 3

        for x in range(min(len(color_ids), SCREEN_WIDTH)):
            color_id = color_ids[x]
            palette_slot = color_id & 0x03
            self._color_ids[y_offset_ids + x] = palette_slot

            if 0 <= palette_slot < palette_len:
                red, green, blue = palette[palette_slot]
            else:
                red, green, blue = ERROR_COLOR

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
        self._color_ids[:] = bytes(SCREEN_WIDTH * SCREEN_HEIGHT)
        self._pixel_rgb[:] = self._clear_rgb
        self.screen.fill(BG_COLOR)

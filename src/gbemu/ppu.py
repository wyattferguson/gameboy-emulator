"""
Step-by-step guide for the DMG PPU flow.

1. CPU drives timing:
    CPU calls ``PPU.update(cpu_cycles)`` after each executed instruction.

2. LCDC is refreshed:
    ``update`` checks LCD enable state and decodes LCDC fields when they change.
    If LCD is disabled, PPU state is reset via ``_disable_lcd_state``.

3. Cycles are accumulated:
    ``mode_cycles`` grows by ``cpu_cycles`` and ``process_timing`` advances as
    many full mode windows as available.

4. Mode machine advances in ``_step_mode``:
    - Mode 2 (OAM scan): collect up to 10 visible sprites for current scanline.
    - Mode 3 (pixel transfer): render one scanline (BG/window + sprites).
    - Mode 0 (HBlank): finish line timing, increment LY, transition to next mode.
    - Mode 1 (VBlank): advance LY by full scanline windows until frame wraps.

5. Rendering path:
    ``render_scanline`` builds BG/window pixels first, then overlays objects.
    Final palette IDs are pushed to ``Screen.draw_scanline``.

6. Register side effects and interrupts:
    ``_set_mode`` updates STAT mode bits and raises STAT interrupts when enabled.
    ``enter_vblank`` requests VBlank interrupt. ``_sync_lyc_status`` keeps
    STAT coincidence bit and LYC interrupt behavior in sync.

7. Frame boundary:
    ``advance_scanline`` wraps LY at 154 lines, increments frame counter, and
    presents frame output via ``Screen.update`` when a frame completes.
"""

from enum import IntEnum

from gbemu.config import SCREEN_HEIGHT, SCREEN_WIDTH
from gbemu.constants import (
    CYCLES_PER_SCANLINE,
    M_BG_PALETTE_DATA,
    M_BG_TILE_MAP_VRAM,
    M_INTERRUPT_FLAG,
    M_LCD_CONTROL,
    M_LCD_STATUS,
    M_LCD_Y_COORDINATE,
    M_LY_COMPARE,
    M_OAM_END,
    M_OAM_START,
    M_OBJ_PALETTE_0_DATA,
    M_OBJ_PALETTE_1_DATA,
    M_VIEWPORT_X,
    M_VIEWPORT_Y,
    M_WIN_MAP_VRAM,
    M_WINDOW_X_PLUS_7,
    M_WINDOW_Y,
    PPU_MODE0_CYCLES,
    PPU_MODE2_CYCLES,
    PPU_MODE3_CYCLES,
    SCAN_LINES,
)
from gbemu.ctypes import ColorExt, Tile, TileSize
from gbemu.mmu import MMU
from gbemu.screen import Screen
from gbemu.utils import bit


class PPUMode(IntEnum):
    """DMG LCD controller mode values mirrored in STAT bits 0-1."""

    HBLANK = 0
    VBLANK = 1
    OAM = 2
    PIXEL_TRANSFER = 3


class PPU:
    """DMG PPU timing and scanline renderer."""

    def __init__(self, mmu: MMU, headless: bool = False) -> None:
        self.mmu = mmu
        self.screen: Screen | None = None if headless else Screen()

        self._line_sprites: list[Tile] = []
        self.scan_line = 0
        self.frame = 0
        self.mode = PPUMode.OAM
        self.mode_cycles = 0
        self.window_line = 0

        # Decoded LCDC flags.
        self.lcd_enabled = 0
        self.window_tile_map = 0
        self.window_enabled = 0
        self.bg_tile_idx = 0
        self.bg_tile_map = 0
        self.obj_size = 0
        self.obj_enabled = 0
        self.bg_window_enabled = 0
        self.bg_priority = 0

        self._cached_lcdc: int | None = None
        self._window_line_latched_for_scanline = False

        self.refresh_lcd_control(self.mmu.memory[M_LCD_CONTROL])
        self._set_mode(PPUMode.OAM)
        self._sync_lyc_status()

    def update(self, cpu_cycles: int = 4) -> None:
        """Advance the PPU by the CPU cycles consumed by one instruction."""
        lcdc = self.mmu.memory[M_LCD_CONTROL]
        was_enabled = bool(self.lcd_enabled)

        if lcdc != self._cached_lcdc:
            self.refresh_lcd_control(lcdc)

        if not self.lcd_enabled:
            if was_enabled:
                self._disable_lcd_state()
            return

        self.mode_cycles += cpu_cycles
        self.process_timing()

    def process_timing(self) -> None:
        """Consume complete PPU mode windows while enough cycles are buffered."""
        while self._step_mode():
            pass

    def _step_mode(self) -> bool:
        """Advance one timing window for the active PPU mode, if possible."""
        if self.mode == PPUMode.OAM:
            return self._step_oam_mode()
        if self.mode == PPUMode.PIXEL_TRANSFER:
            return self._step_pixel_transfer_mode()
        if self.mode == PPUMode.HBLANK:
            return self._step_hblank_mode()
        return self._step_vblank_mode()

    def _step_oam_mode(self) -> bool:
        """Handle mode 2 timing and transition to pixel transfer."""
        if self.mode_cycles < PPU_MODE2_CYCLES:
            return False

        self.mode_cycles -= PPU_MODE2_CYCLES
        self._window_line_latched_for_scanline = False
        self._line_sprites = self._scan_oam_for_scanline()
        self._set_mode(PPUMode.PIXEL_TRANSFER)
        return True

    def _step_pixel_transfer_mode(self) -> bool:
        """Handle mode 3 timing, render line, and enter HBlank."""
        if self.mode_cycles < PPU_MODE3_CYCLES:
            return False

        self.mode_cycles -= PPU_MODE3_CYCLES
        self.render_scanline()
        self._set_mode(PPUMode.HBLANK)
        self.enter_hblank()
        return True

    def _step_hblank_mode(self) -> bool:
        """Handle mode 0 timing and select next scanline mode."""
        if self.mode_cycles < PPU_MODE0_CYCLES:
            return False

        self.mode_cycles -= PPU_MODE0_CYCLES
        self.advance_scanline()
        if self.scan_line >= SCREEN_HEIGHT:
            self._set_mode(PPUMode.VBLANK)
            self.enter_vblank()
        else:
            self._set_mode(PPUMode.OAM)
        return True

    def _step_vblank_mode(self) -> bool:
        """Handle mode 1 timing until LY wraps and mode 2 resumes."""
        if self.mode_cycles < CYCLES_PER_SCANLINE:
            return False

        self.mode_cycles -= CYCLES_PER_SCANLINE
        self.advance_scanline()
        if self.scan_line == 0:
            self._set_mode(PPUMode.OAM)
        return True

    def _disable_lcd_state(self) -> None:
        """Reset PPU scan state and bus visibility when LCD is turned off."""
        self.mode_cycles = 0
        self.scan_line = 0
        self.window_line = 0
        self._window_line_latched_for_scanline = False
        self._set_mode(PPUMode.OAM)
        self.mmu.set_ppu_bus_access(oam_locked=False, vram_locked=False)
        self.mmu.memory[M_LCD_Y_COORDINATE] = 0
        self._sync_lyc_status()
        if self.screen:
            self.screen.clear_screen()

    def advance_scanline(self) -> None:
        """Advance LY and handle frame-end wrap at LY 153->0."""
        self.scan_line += 1
        if self.scan_line >= SCAN_LINES:
            self.scan_line = 0
            self.window_line = 0
            self.frame += 1
            if self.screen:
                self.screen.update()

        self.mmu.memory[M_LCD_Y_COORDINATE] = self.scan_line
        self._sync_lyc_status()

    def _scan_oam_for_scanline(self) -> list[Tile]:
        """Collect up to 10 visible sprites in DMG draw order for the current scanline."""
        ordered_sprites: list[tuple[int, Tile]] = []
        sprite_count = 0
        sprite_height = TileSize.LARGE if self.obj_size else TileSize.SMALL
        memory = self.mmu.memory

        for addr in range(M_OAM_START, M_OAM_END + 1, 4):
            y = memory[addr] - 16
            if not (y <= self.scan_line < y + int(sprite_height)):
                continue

            attributes = memory[addr + 3]
            sprite = Tile(
                index=memory[addr + 2],
                data=[],
                height=sprite_height,
                x=memory[addr + 1] - 8,
                y=y,
                x_flipped=bool((attributes >> 5) & 0x01),
                y_flipped=bool((attributes >> 6) & 0x01),
                dmg_palette=(attributes >> 4) & 0x01,
                priority=bool((attributes >> 7) & 0x01),
            )

            # Maintain draw order incrementally to avoid per-scanline sorting later.
            # We draw low-priority sprites first: larger X first; for equal X, later OAM first.
            sprite_idx = sprite_count
            sprite_count += 1
            insert_at = len(ordered_sprites)
            while insert_at > 0:
                prev_idx, prev = ordered_sprites[insert_at - 1]
                if (prev.x, prev_idx) >= (sprite.x, sprite_idx):
                    break
                insert_at -= 1
            ordered_sprites.insert(insert_at, (sprite_idx, sprite))

            if sprite_count == 10:
                break

        return [sprite for _, sprite in ordered_sprites]

    def render_scanline(self) -> None:
        """Compose a full scanline from BG/window and OBJ layers."""
        if self.bg_window_enabled:
            base_line, bg_ids = self.render_bg_window_line_with_ids()
        else:
            base_line = [self.apply_bg_palette(0)] * SCREEN_WIDTH
            bg_ids = [0] * SCREEN_WIDTH

        if self.obj_enabled:
            self.render_object_line(base_line, bg_ids)

        if self.screen:
            self.screen.draw_scanline(base_line, self.scan_line)

    def enter_hblank(self) -> None:
        """HBlank transition hook reserved for future DMA/stat extensions."""
        return

    def _set_bus_access_for_mode(self, mode: PPUMode) -> None:
        """Apply DMG bus-lock rules for CPU-visible VRAM/OAM access by mode."""
        # CPU bus access rules by mode:
        # mode 2: OAM blocked, VRAM open
        # mode 3: OAM+VRAM blocked
        # mode 0/1 or LCD off: both open
        if not self.lcd_enabled:
            self.mmu.set_ppu_bus_access(oam_locked=False, vram_locked=False)
        elif mode == PPUMode.OAM:
            self.mmu.set_ppu_bus_access(oam_locked=True, vram_locked=False)
        elif mode == PPUMode.PIXEL_TRANSFER:
            self.mmu.set_ppu_bus_access(oam_locked=True, vram_locked=True)
        else:
            self.mmu.set_ppu_bus_access(oam_locked=False, vram_locked=False)

    def enter_vblank(self) -> None:
        """Raise VBlank interrupt on entry to mode 1."""
        self._request_interrupt(0)

    def _request_interrupt(self, bit_index: int) -> None:
        """Request an interrupt by setting a bit in IF."""
        self.mmu.memory[M_INTERRUPT_FLAG] |= 1 << bit_index

    def _set_mode(self, mode: PPUMode) -> None:
        """Update STAT mode bits, bus access, and optional STAT interrupt request."""
        self.mode = mode
        self._set_bus_access_for_mode(mode)

        stat = self.mmu.memory[M_LCD_STATUS]
        stat = (stat & 0xFC) | int(mode)
        self.mmu.memory[M_LCD_STATUS] = stat

        if (
            (mode == PPUMode.HBLANK and ((stat >> 3) & 0x01))
            or (mode == PPUMode.VBLANK and ((stat >> 4) & 0x01))
            or (mode == PPUMode.OAM and ((stat >> 5) & 0x01))
        ):
            self._request_interrupt(1)

    def _sync_lyc_status(self) -> None:
        """Synchronize STAT coincidence bit and trigger LYC interrupt if enabled."""
        ly: int = self.mmu.memory[M_LCD_Y_COORDINATE]
        lyc: int = self.mmu.memory[M_LY_COMPARE]
        stat: int = self.mmu.memory[M_LCD_STATUS]

        if ly == lyc:
            stat |= 0x04
            if (stat >> 6) & 0x01:
                self._request_interrupt(1)
        else:
            stat &= 0xFB

        self.mmu.memory[M_LCD_STATUS] = stat

    def _decode_dmg_palette(self, palette_reg: int) -> ColorExt:
        """Expand a DMG palette register into a 4-entry color lookup tuple."""
        return (
            palette_reg & 0x03,
            (palette_reg >> 2) & 0x03,
            (palette_reg >> 4) & 0x03,
            (palette_reg >> 6) & 0x03,
        )

    def _tile_row_addr(self, tile_number: int, tile_row: int) -> int:
        """Resolve the tile-row address using LCDC tile-data addressing mode."""
        if self.bg_tile_idx:
            return 0x8000 + tile_number * 16 + tile_row * 2

        signed_id = tile_number if tile_number < 128 else tile_number - 256
        return 0x9000 + signed_id * 16 + tile_row * 2

    def _render_tilemap_segment(
        self,
        map_base: int,
        tile_y: int,
        tile_row: int,
        x_start: int,
        x_stop: int,
        map_x_offset: int,
        wrap_map_x: bool,
        palette_lut: ColorExt,
        palette_ids: list[int],
        raw_color_ids: list[int],
    ) -> None:
        """Render a horizontal tilemap segment into palette/raw scanline buffers."""
        memory = self.mmu.memory
        row_index_base = map_base + tile_y * 32
        last_tile_number = -1
        last_low = 0
        last_high = 0

        for x in range(x_start, x_stop):
            map_x = ((x + map_x_offset) & 0xFF) if wrap_map_x else (x - map_x_offset)
            tile_number = memory[row_index_base + (map_x >> 3)]
            if tile_number != last_tile_number:
                row_addr = self._tile_row_addr(tile_number, tile_row)
                last_low = memory[row_addr]
                last_high = memory[row_addr + 1]
                last_tile_number = tile_number

            bit_index = 7 - (map_x & 0x07)
            color_id = ((last_high >> bit_index) & 1) << 1 | (last_low >> bit_index) & 1
            raw_color_ids[x] = color_id
            palette_ids[x] = palette_lut[color_id]

    def render_bg_window_line_with_ids(self) -> tuple[list[int], list[int]]:
        """Render BG/window pixels and return (palette_ids, raw_2bpp_ids)."""
        scx: int = self.mmu.memory[M_VIEWPORT_X]
        scy: int = self.mmu.memory[M_VIEWPORT_Y]
        wy: int = self.mmu.memory[M_WINDOW_Y]
        wx: int = self.mmu.memory[M_WINDOW_X_PLUS_7] - 7
        bg_pal = self._decode_dmg_palette(self.mmu.memory[M_BG_PALETTE_DATA])

        palette_ids = [0] * SCREEN_WIDTH
        raw_color_ids = [0] * SCREEN_WIDTH

        window_active = bool(self.window_enabled and self.scan_line >= wy and wx < SCREEN_WIDTH)
        window_row = self.window_line
        if window_active and not self._window_line_latched_for_scanline:
            self.window_line += 1
            self._window_line_latched_for_scanline = True

        # WX values below 7 are hardware-quirky; clamp start to x=0 for stable DMG behavior.
        window_start_x: int = max(wx, 0) if window_active else SCREEN_WIDTH

        # Render BG first, then window, so each segment can use a branch-free inner loop.
        bg_limit = min(window_start_x, SCREEN_WIDTH)
        if bg_limit > 0:
            bg_map_y = (self.scan_line + scy) & 0xFF
            self._render_tilemap_segment(
                map_base=M_BG_TILE_MAP_VRAM[self.bg_tile_map][0],
                tile_y=bg_map_y >> 3,
                tile_row=bg_map_y & 0x07,
                x_start=0,
                x_stop=bg_limit,
                map_x_offset=scx,
                wrap_map_x=True,
                palette_lut=bg_pal,
                palette_ids=palette_ids,
                raw_color_ids=raw_color_ids,
            )

        if window_active and window_start_x < SCREEN_WIDTH:
            self._render_tilemap_segment(
                map_base=M_WIN_MAP_VRAM[self.window_tile_map][0],
                tile_y=window_row >> 3,
                tile_row=window_row & 0x07,
                x_start=window_start_x,
                x_stop=SCREEN_WIDTH,
                map_x_offset=window_start_x,
                wrap_map_x=False,
                palette_lut=bg_pal,
                palette_ids=palette_ids,
                raw_color_ids=raw_color_ids,
            )

        return palette_ids, raw_color_ids

    def render_object_line(self, bg_line: list[int], bg_color_ids: list[int]) -> None:
        """Overlay sprite pixels onto bg_line in-place (no copy)."""
        memory: list[int] = self.mmu.memory

        # Draw in precomputed low->high priority order from OAM scan.
        for sprite in self._line_sprites:
            row: int = self.scan_line - sprite.y
            if sprite.y_flipped:
                row: int = int(sprite.height) - 1 - row

            tile_index = sprite.index
            if sprite.height == TileSize.LARGE:
                tile_index &= 0xFE
                if row >= 8:
                    tile_index += 1
                    row -= 8

            tile_addr: int = 0x8000 + tile_index * 16 + row * 2
            low: int = memory[tile_addr]
            high: int = memory[tile_addr + 1]
            palette_reg: int = memory[
                M_OBJ_PALETTE_1_DATA if sprite.dmg_palette else M_OBJ_PALETTE_0_DATA
            ]
            pal: ColorExt = self._decode_dmg_palette(palette_reg)
            # Hoist sprite fields to locals to reduce attribute lookups in inner loop.
            sx: int = sprite.x
            x_flipped: bool = sprite.x_flipped
            priority: bool = sprite.priority

            for col in range(8):
                x = sx + col
                if x < 0 or x >= SCREEN_WIDTH:
                    continue

                bit_idx = col if x_flipped else 7 - col
                color_id: int = ((high >> bit_idx) & 1) << 1 | (low >> bit_idx) & 1
                if color_id == 0:
                    continue

                if priority and bg_color_ids[x] != 0:
                    continue

                bg_line[x] = pal[color_id]

    def resolve_tile_data_addr(self, tile_id: int) -> int:
        """Resolve a tile index to its base address using LCDC bit 4 mode."""
        if self.bg_tile_idx:
            return 0x8000 + tile_id * 16

        signed_id = tile_id if tile_id < 128 else tile_id - 256
        return 0x9000 + signed_id * 16

    def apply_bg_palette(self, color_id: int) -> int:
        """Map a raw 2bpp color index through the BGP register."""
        palette = self.mmu.memory[M_BG_PALETTE_DATA]
        return (palette >> (color_id * 2)) & 0x03

    def refresh_lcd_control(self, lcd_control: int | None = None) -> None:
        """Decode LCDC into cached boolean fields."""
        if lcd_control is None:
            lcd_control: int = self.mmu.memory[M_LCD_CONTROL]

        self._cached_lcdc = lcd_control
        self.lcd_enabled = bit(lcd_control, 7)
        self.window_tile_map = bit(lcd_control, 6)
        self.window_enabled = bit(lcd_control, 5)
        self.bg_tile_idx = bit(lcd_control, 4)
        self.bg_tile_map = bit(lcd_control, 3)
        self.obj_size = bit(lcd_control, 2)
        self.obj_enabled = bit(lcd_control, 1)
        self.bg_window_enabled = bit(lcd_control, 0)
        self.bg_priority = self.bg_window_enabled

"""Step-by-step guide for the DMG PPU flow in this module.

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

from gbemu.config import (
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
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from gbemu.ctypes import Tile, TileSize
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
        self.headless = headless
        self.screen: Screen | None = None if headless else Screen()

        # Legacy/public state used by tests and other modules.
        self.tiles: list[Tile] = []
        self.line_sprites: list[Tile] = []
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

        self.mmu.memory[M_LCD_Y_COORDINATE] = 0
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
        advanced = False

        if self.mode == PPUMode.OAM:
            if self.mode_cycles >= PPU_MODE2_CYCLES:
                self.mode_cycles -= PPU_MODE2_CYCLES
                self._window_line_latched_for_scanline = False
                self.scan_oam_for_scanline()
                self._set_mode(PPUMode.PIXEL_TRANSFER)
                advanced = True
        elif self.mode == PPUMode.PIXEL_TRANSFER:
            if self.mode_cycles >= PPU_MODE3_CYCLES:
                self.mode_cycles -= PPU_MODE3_CYCLES
                self.render_scanline()
                self._set_mode(PPUMode.HBLANK)
                self.enter_hblank()
                advanced = True
        elif self.mode == PPUMode.HBLANK:
            if self.mode_cycles >= PPU_MODE0_CYCLES:
                self.mode_cycles -= PPU_MODE0_CYCLES
                self.advance_scanline()
                if self.scan_line >= SCREEN_HEIGHT:
                    self._set_mode(PPUMode.VBLANK)
                    self.enter_vblank()
                else:
                    self._set_mode(PPUMode.OAM)
                advanced = True
        elif self.mode_cycles >= CYCLES_PER_SCANLINE:
            self.mode_cycles -= CYCLES_PER_SCANLINE
            self.advance_scanline()
            if self.scan_line == 0:
                self._set_mode(PPUMode.OAM)
            advanced = True

        return advanced

    def _disable_lcd_state(self) -> None:
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

    def scan_oam_for_scanline(self) -> None:
        """Build the list of up to 10 sprites visible on the current scanline."""
        self.line_sprites = []
        sprite_height = TileSize.LARGE if self.obj_size else TileSize.SMALL
        memory = self.mmu.memory

        for addr in range(M_OAM_START, M_OAM_END + 1, 4):
            y = memory[addr] - 16
            if not (y <= self.scan_line < y + int(sprite_height)):
                continue

            attributes = memory[addr + 3]
            self.line_sprites.append(
                Tile(
                    index=memory[addr + 2],
                    data=[],
                    height=sprite_height,
                    x=memory[addr + 1] - 8,
                    y=y,
                    x_flipped=bool(bit(attributes, 5)),
                    y_flipped=bool(bit(attributes, 6)),
                    dmg_palette=bit(attributes, 4),
                    priority=bool(bit(attributes, 7)),
                ),
            )

            if len(self.line_sprites) == 10:
                break

    def render_scanline(self) -> None:
        """Compose a full scanline from BG/window and OBJ layers."""
        base_line = [self.apply_bg_palette(0)] * SCREEN_WIDTH
        bg_ids = [0] * SCREEN_WIDTH

        if self.bg_window_enabled:
            base_line, bg_ids = self.render_bg_window_line_with_ids()

        if self.obj_enabled:
            base_line = self.render_object_line(base_line, bg_ids)

        if self.screen:
            self.screen.draw_scanline(base_line, self.scan_line)

    def enter_hblank(self) -> None:
        """HBlank transition hook reserved for future DMA/stat extensions."""
        return

    def _set_bus_access_for_mode(self, mode: PPUMode) -> None:
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
        self.mmu.memory[M_INTERRUPT_FLAG] |= 1 << bit_index

    def _set_mode(self, mode: PPUMode) -> None:
        self.mode = mode
        self._set_bus_access_for_mode(mode)

        stat = self.mmu.memory[M_LCD_STATUS]
        stat = (stat & 0xFC) | int(mode)
        self.mmu.memory[M_LCD_STATUS] = stat

        if (
            (mode == PPUMode.HBLANK and bit(stat, 3))
            or (mode == PPUMode.VBLANK and bit(stat, 4))
            or (mode == PPUMode.OAM and bit(stat, 5))
        ):
            self._request_interrupt(1)

    def _sync_lyc_status(self) -> None:
        ly = self.mmu.memory[M_LCD_Y_COORDINATE]
        lyc = self.mmu.memory[M_LY_COMPARE]
        stat = self.mmu.memory[M_LCD_STATUS]

        if ly == lyc:
            stat |= 0x04
            if bit(stat, 6):
                self._request_interrupt(1)
        else:
            stat &= 0xFB

        self.mmu.memory[M_LCD_STATUS] = stat

    def render_bg_window_line_with_ids(self) -> tuple[list[int], list[int]]:
        """Render BG/window pixels and return (palette_ids, raw_2bpp_ids)."""
        memory = self.mmu.memory
        scx = memory[M_VIEWPORT_X]
        scy = memory[M_VIEWPORT_Y]
        wy = memory[M_WINDOW_Y]
        wx = memory[M_WINDOW_X_PLUS_7] - 7

        palette_ids = [0] * SCREEN_WIDTH
        raw_color_ids = [0] * SCREEN_WIDTH

        window_active = bool(self.window_enabled and self.scan_line >= wy and wx < SCREEN_WIDTH)
        window_row = self.window_line
        if window_active and not self._window_line_latched_for_scanline:
            self.window_line += 1
            self._window_line_latched_for_scanline = True

        # WX values below 7 are hardware-quirky; clamp start to x=0 for stable DMG behavior.
        window_start_x = max(wx, 0)

        for x in range(SCREEN_WIDTH):
            use_window = bool(window_active and x >= window_start_x)
            if use_window:
                map_x = x - window_start_x
                map_y = window_row
                tile_map_base = M_WIN_MAP_VRAM[self.window_tile_map][0]
            else:
                map_x = (x + scx) & 0xFF
                map_y = (self.scan_line + scy) & 0xFF
                tile_map_base = M_BG_TILE_MAP_VRAM[self.bg_tile_map][0]

            tile_x = map_x >> 3
            tile_y = map_y >> 3
            tile_number = memory[tile_map_base + tile_y * 32 + tile_x]
            tile_row = map_y & 0x07
            color_id = self._read_tile_color(tile_number, tile_row, map_x & 0x07)

            raw_color_ids[x] = color_id
            palette_ids[x] = self.apply_bg_palette(color_id)

        return palette_ids, raw_color_ids

    def render_bg_window_line(self) -> list[int]:
        """Render only palette IDs for a line, used by software logo tests."""
        line, _ = self.render_bg_window_line_with_ids()
        return line

    def render_object_line(self, bg_line: list[int], bg_color_ids: list[int]) -> list[int]:
        """Overlay sprite pixels onto an existing BG/window scanline."""
        out = list(bg_line)
        memory = self.mmu.memory

        # DMG overlap priority: smaller X wins; for equal X, lower OAM index wins.
        # Draw lowest-priority sprites first so highest-priority pixels remain on top.
        ordered_sprites = sorted(
            enumerate(self.line_sprites),
            key=lambda item: (item[1].x, item[0]),
            reverse=True,
        )
        for _, sprite in ordered_sprites:
            row = self.scan_line - sprite.y
            if sprite.y_flipped:
                row = int(sprite.height) - 1 - row

            tile_index = sprite.index
            if sprite.height == TileSize.LARGE:
                tile_index &= 0xFE
                if row >= 8:
                    tile_index += 1
                    row -= 8

            tile_addr = 0x8000 + tile_index * 16 + row * 2
            low = memory[tile_addr]
            high = memory[tile_addr + 1]
            palette = memory[M_OBJ_PALETTE_1_DATA if sprite.dmg_palette else M_OBJ_PALETTE_0_DATA]

            for col in range(8):
                x = sprite.x + col
                if x < 0 or x >= SCREEN_WIDTH:
                    continue

                bit_idx = col if sprite.x_flipped else 7 - col
                color_id = ((high >> bit_idx) & 0x01) << 1 | ((low >> bit_idx) & 0x01)
                if color_id == 0:
                    continue

                if sprite.priority and bg_color_ids[x] != 0:
                    continue

                out[x] = (palette >> (color_id * 2)) & 0x03

        return out

    def _read_tile_color(self, tile_id: int, row: int, col: int) -> int:
        row_addr = self.resolve_tile_data_addr(tile_id) + row * 2
        low = self.mmu.memory[row_addr]
        high = self.mmu.memory[row_addr + 1]
        bit_index = 7 - col
        lo = (low >> bit_index) & 0x01
        hi = (high >> bit_index) & 0x01
        return (hi << 1) | lo

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
        """Decode LCDC into cached boolean fields used by renderer and timing."""
        if lcd_control is None:
            lcd_control = self.mmu.memory[M_LCD_CONTROL]

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

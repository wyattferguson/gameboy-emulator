from enum import IntEnum

from gbemu.config import (
    CYCLES_PER_SCANLINE,
    M_BG_PALETTE_DATA,
    M_BG_TILE_DATA_VRAM,
    M_BG_TILE_MAP_VRAM,
    M_LCD_CONTROL,
    M_LCD_Y_COORDINATE,
    M_OAM_END,
    M_OAM_START,
    M_VIEWPORT_X,
    M_VIEWPORT_Y,
    M_WIN_MAP_VRAM,
    M_WINDOW_X_PLUS_7,
    M_WINDOW_Y,
    SCAN_LINES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from gbemu.ctypes import Tile, TileSize
from gbemu.mmu import MMU
from gbemu.screen import Screen
from gbemu.utils import bit


class PPUMode(IntEnum):
    """PPU modes in scanline order."""

    HBLANK = 0
    VBLANK = 1
    OAM = 2
    PIXEL_TRANSFER = 3


class PPU:
    """Picture Processing Unit (PPU) for the Gameboy."""

    def __init__(self, mmu: MMU, headless: bool = False) -> None:
        self.mmu: MMU = mmu
        self.headless = headless
        self.screen: Screen | None = Screen() if not headless else None

        # High-level frame/line state.
        self.tiles: list[Tile] = []
        self.scan_line: int = 0
        self.frame: int = 0
        self.line_sprites: list[Tile] = []
        self.mode: PPUMode = PPUMode.OAM
        self.mode_cycles: int = 0

        # Cached LCDC fields (refreshed each update).
        self.lcd_enabled: int = 0
        self.window_tile_map: int = 0
        self.window_enabled: int = 0
        self.bg_tile_idx: int = 0
        self.bg_tile_map: int = 0
        self.obj_size: int = 0
        self.obj_enabled: int = 0
        self.bg_priority: int = 0
        self._lcd_control_cache: int | None = None
        self.headless = headless

    def update(self, cpu_cycles: int = 4) -> None:
        """Advance PPU timing using CPU cycles for this instruction."""
        # Keep LCDC-derived flags in sync with MMU before rendering.
        previous_lcd_enabled = self.lcd_enabled
        lcd_control = self.mmu.memory[M_LCD_CONTROL]
        if lcd_control != self._lcd_control_cache:
            self.refresh_lcd_control(lcd_control)
        if not self.lcd_enabled:
            if previous_lcd_enabled:
                self._reset_when_lcd_disabled()
            return

        # Accumulate elapsed cycles and consume complete PPU mode slices.
        self.mode_cycles += cpu_cycles
        self.process_timing()

    def process_timing(self) -> None:
        """Consume PPU mode windows as cycles accumulate."""
        # DMG line timing model (t-cycles): OAM 80 + transfer 172 + HBlank 204 = 456.
        while True:
            if self.mode == PPUMode.OAM:
                if self.mode_cycles < 80:
                    return
                self.mode_cycles -= 80
                self.scan_oam_for_scanline()
                self.mode = PPUMode.PIXEL_TRANSFER

            elif self.mode == PPUMode.PIXEL_TRANSFER:
                if self.mode_cycles < 172:
                    return
                self.mode_cycles -= 172
                self.render_scanline()
                self.mode = PPUMode.HBLANK
                self.enter_hblank()

            elif self.mode == PPUMode.HBLANK:
                if self.mode_cycles < 204:
                    return
                self.mode_cycles -= 204
                self.advance_scanline()
                self.mode = PPUMode.VBLANK if self.scan_line >= SCREEN_HEIGHT else PPUMode.OAM

            else:  # PPUMode.VBLANK
                if self.mode_cycles < CYCLES_PER_SCANLINE:
                    return
                self.mode_cycles -= CYCLES_PER_SCANLINE
                self.advance_scanline()
                if self.scan_line == 0:
                    # New frame starts at LY 0 with OAM scan.
                    self.mode = PPUMode.OAM

    def _reset_when_lcd_disabled(self) -> None:
        """Resetting LY and mode state."""
        self.mode = PPUMode.OAM
        self.mode_cycles = 0
        self.scan_line = 0
        self.mmu.memory[M_LCD_Y_COORDINATE] = 0
        if self.screen:
            self.screen.clear_screen()

    def advance_scanline(self) -> None:
        """Increment LY and wrap to the next frame after VBlank lines."""
        self.scan_line += 1
        if self.scan_line >= SCAN_LINES:
            self.scan_line = 0
            self.frame += 1
            # Present the composed frame once per full LY sweep.
            if self.screen:
                self.screen.update()
        self.mmu.memory[M_LCD_Y_COORDINATE] = self.scan_line

    def scan_oam_for_scanline(self) -> None:
        """Collect up to 10 sprites visible on the current scanline."""
        self.line_sprites = []
        sprite_height = TileSize.LARGE if self.obj_size else TileSize.SMALL
        memory = self.mmu.memory

        for addr in range(M_OAM_START, M_OAM_END + 1, 4):
            y = memory[addr] - 16
            x = memory[addr + 1] - 8
            tile_index = memory[addr + 2]
            attributes = memory[addr + 3]

            if not (y <= self.scan_line < y + sprite_height):
                continue

            self.line_sprites.append(
                Tile(
                    index=tile_index,
                    data=[],
                    height=sprite_height,
                    x=x,
                    y=y,
                    x_flipped=bool(bit(attributes, 5)),
                    y_flipped=bool(bit(attributes, 6)),
                    dmg_palette=bit(attributes, 4),
                    priority=bool(bit(attributes, 7)),
                ),
            )

            if len(self.line_sprites) >= 10:
                # Hardware limit: only 10 sprites may be selected per scanline.
                break

    def render_scanline(self) -> None:
        """Compose BG/window first, then objects, and send one line to the screen."""
        # Color IDs in this line are DMG palette slots (0..3).
        line = [0] * SCREEN_WIDTH

        if self.bg_priority:
            line = self.render_bg_window_line()

        if self.obj_enabled:
            line = self.render_object_line(line)

        if self.screen:
            self.screen.draw_scanline(line, self.scan_line)

    def enter_hblank(self) -> None:
        """HBlank hook for future STAT/HDMA behavior."""

    def enter_vblank(self) -> None:
        """VBlank hook for future interrupt/stat behavior."""

    def render_bg_window_line(self) -> list[int]:
        """Render one BG/window scanline as palette IDs (0..3)."""
        # Scroll/window registers define which 256x256 map pixel is sampled.
        memory = self.mmu.memory
        scx = memory[M_VIEWPORT_X]
        scy = memory[M_VIEWPORT_Y]
        wy = memory[M_WINDOW_Y]
        wx = memory[M_WINDOW_X_PLUS_7] - 7
        bg_palette = memory[M_BG_PALETTE_DATA]
        line = [0] * SCREEN_WIDTH

        for x in range(SCREEN_WIDTH):
            use_window = bool(self.window_enabled and self.scan_line >= wy and x >= wx)

            if use_window:
                map_x = x - wx
                map_y = self.scan_line - wy
                tile_map = M_WIN_MAP_VRAM[self.window_tile_map]
            else:
                map_x = (x + scx) & 0xFF
                map_y = (self.scan_line + scy) & 0xFF
                tile_map = M_BG_TILE_MAP_VRAM[self.bg_tile_map]

            tile_x = map_x // 8
            tile_y = map_y // 8
            tile_map_start = tile_map[0]
            tile_num_addr = tile_map_start + (tile_y * 32) + tile_x
            tile_id = memory[tile_num_addr]

            # Tile data rows are encoded as two bitplanes.
            # Even byte (offset 0): contains bit 0 (low) of each pixel's 2-bit color.
            # Odd byte (offset 1): contains bit 1 (high) of each pixel's 2-bit color.
            tile_data_addr = self.resolve_tile_data_addr(tile_id)
            row_in_tile = map_y % 8
            row_addr = tile_data_addr + (row_in_tile * 2)
            bit_plane_0 = memory[row_addr]
            bit_plane_1 = memory[row_addr + 1]
            bit_idx = 7 - (map_x % 8)
            color_id = ((bit_plane_1 >> bit_idx) & 0x01) << 1 | ((bit_plane_0 >> bit_idx) & 0x01)

            line[x] = (bg_palette >> (color_id * 2)) & 0x03

        return line

    def render_object_line(self, bg_line: list[int]) -> list[int]:
        """Object blending outline. Full sprite priority is TODO."""
        return bg_line

    def resolve_tile_data_addr(self, tile_id: int) -> int:
        """Resolve tile data base address for LCDC tile-data mode."""
        # LCDC bit 4 selects unsigned (0x8000) vs signed (0x8800/0x9000 base) indexing.
        if self.bg_tile_idx:
            tile_data_start = M_BG_TILE_DATA_VRAM[1][0]
            return tile_data_start + (tile_id * 16)

        signed_tile_id = tile_id if tile_id < 128 else tile_id - 256
        return 0x9000 + (signed_tile_id * 16)

    def apply_bg_palette(self, color_id: int) -> int:
        """Map a 2bpp color index through BGP to a palette slot."""
        palette = self.mmu.memory[M_BG_PALETTE_DATA]
        return (palette >> (color_id * 2)) & 0x03

    def refresh_lcd_control(self, lcd_control: int | None = None) -> None:
        """Refresh the PPU status based on the LCD control register."""
        if lcd_control is None:
            lcd_control = self.mmu.memory[M_LCD_CONTROL]
        self._lcd_control_cache = lcd_control
        self.lcd_enabled = bit(lcd_control, 7)
        self.window_tile_map = bit(lcd_control, 6)
        self.window_enabled = bit(lcd_control, 5)
        self.bg_tile_idx = bit(lcd_control, 4)
        self.bg_tile_map = bit(lcd_control, 3)
        self.obj_size = bit(lcd_control, 2)
        self.obj_enabled = bit(lcd_control, 1)
        self.bg_priority = bit(lcd_control, 0)

from gbemu.cart import Cart
from gbemu.config import (
    M_BG_PALETTE_DATA,
    M_LCD_CONTROL,
    M_LCD_Y_COORDINATE,
    M_VIEWPORT_X,
    M_VIEWPORT_Y,
    M_WINDOW_X_PLUS_7,
    M_WINDOW_Y,
    SCREEN_WIDTH,
)
from gbemu.cpu import CPU
from gbemu.ctypes import TileSize
from gbemu.mmu import MMU
from gbemu.ppu import PPU, PPUMode


def test_ppu_mode_timing_oam() -> None:
    """Test that PPU correctly spends 80 cycles in OAM mode."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80  # LCD on

    ppu.refresh_lcd_control()
    ppu.scan_line = 0
    ppu.mode = PPUMode.OAM
    ppu.mode_cycles = 0

    # Feed 79 cycles - should stay in OAM
    ppu.update(79)
    assert ppu.mode == PPUMode.OAM, "Should remain in OAM after 79 cycles"

    # Feed 1 more cycle to complete OAM window
    ppu.update(1)
    assert ppu.mode == PPUMode.PIXEL_TRANSFER, "Should transition to PIXEL_TRANSFER after 80 cycles"


def test_ppu_mode_timing_pixel_transfer() -> None:
    """Test that PPU correctly spends 172 cycles in PIXEL_TRANSFER mode."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    ppu.refresh_lcd_control()
    ppu.scan_line = 0
    ppu.mode = PPUMode.PIXEL_TRANSFER
    ppu.mode_cycles = 0

    ppu.update(171)
    assert ppu.mode == PPUMode.PIXEL_TRANSFER, "Should remain in PIXEL_TRANSFER after 171 cycles"

    ppu.update(1)
    assert ppu.mode == PPUMode.HBLANK, "Should transition to HBLANK after 172 cycles"


def test_ppu_mode_timing_hblank() -> None:
    """Test that PPU correctly spends 204 cycles in HBLANK mode."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    ppu.refresh_lcd_control()
    ppu.scan_line = 0
    ppu.mode = PPUMode.HBLANK
    ppu.mode_cycles = 0

    ppu.update(203)
    assert ppu.mode == PPUMode.HBLANK, "Should remain in HBLANK after 203 cycles"

    ppu.update(1)
    assert ppu.mode == PPUMode.OAM, (
        "Should transition to OAM after 204 cycles (within visible area)"
    )


def test_ppu_scanline_advancement() -> None:
    """Test that LY increments correctly through full frame."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    ppu.refresh_lcd_control()
    ppu.scan_line = 0
    ppu.mode = PPUMode.OAM
    ppu.mode_cycles = 0

    # Advance through one complete scanline (456 cycles)
    ppu.update(456)

    assert ppu.scan_line == 1, "LY should advance to 1 after one scanline"
    assert mmu[M_LCD_Y_COORDINATE] == 1, "MMU LY register should mirror scan_line"


def test_ppu_frame_wrap() -> None:
    """Test that LY wraps from 153 to 0 and frame increments."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    ppu.refresh_lcd_control()
    ppu.scan_line = 153
    ppu.frame = 5
    ppu.mode = PPUMode.HBLANK
    ppu.mode_cycles = 0

    # Advance through HBLANK
    ppu.update(204)

    assert ppu.scan_line == 0, "LY should wrap to 0 after line 153"
    assert ppu.frame == 6, "Frame should increment on wrap"
    assert mmu[M_LCD_Y_COORDINATE] == 0, "MMU LY should be 0"


def test_ppu_lcd_disabled_resets_state() -> None:
    """Test that disabling LCD resets PPU state."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    ppu.refresh_lcd_control()
    ppu.scan_line = 42
    ppu.mode = PPUMode.PIXEL_TRANSFER
    ppu.mode_cycles = 100

    # Disable LCD
    mmu[M_LCD_CONTROL] = 0x00
    ppu.update(4)

    assert ppu.scan_line == 0, "LY should reset to 0 when LCD disabled"
    assert ppu.mode == PPUMode.OAM, "Mode should reset to OAM when LCD disabled"
    assert ppu.mode_cycles == 0, "Mode cycles should reset when LCD disabled"
    assert mmu[M_LCD_Y_COORDINATE] == 0, "MMU LY should be 0 when LCD disabled"


def test_ppu_lcdc_register_parsing() -> None:
    """Test that LCDC bits are correctly parsed."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)

    # Set all LCDC bits
    mmu[M_LCD_CONTROL] = 0xFF

    ppu.refresh_lcd_control()

    assert ppu.lcd_enabled == 1, "Bit 7 should set lcd_enabled"
    assert ppu.window_tile_map == 1, "Bit 6 should set window_tile_map"
    assert ppu.window_enabled == 1, "Bit 5 should set window_enabled"
    assert ppu.bg_tile_idx == 1, "Bit 4 should set bg_tile_idx"
    assert ppu.bg_tile_map == 1, "Bit 3 should set bg_tile_map"
    assert ppu.obj_size == 1, "Bit 2 should set obj_size"
    assert ppu.obj_enabled == 1, "Bit 1 should set obj_enabled"
    assert ppu.bg_priority == 1, "Bit 0 should set bg_priority"


def test_ppu_lcdc_register_all_disabled() -> None:
    """Test that LCDC bits are all zero when cleared."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)

    mmu[M_LCD_CONTROL] = 0x00
    ppu.refresh_lcd_control()

    assert ppu.lcd_enabled == 0
    assert ppu.window_tile_map == 0
    assert ppu.window_enabled == 0
    assert ppu.bg_tile_idx == 0
    assert ppu.bg_tile_map == 0
    assert ppu.obj_size == 0
    assert ppu.obj_enabled == 0
    assert ppu.bg_priority == 0


def test_ppu_apply_bg_palette_identity() -> None:
    """Test palette application with 0xE4 (identity mapping)."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)

    # 0xE4 = 11100100 => maps 0→0, 1→1, 2→2, 3→3 (identity)
    mmu[M_BG_PALETTE_DATA] = 0xE4
    ppu.refresh_lcd_control()

    assert ppu.apply_bg_palette(0) == 0
    assert ppu.apply_bg_palette(1) == 1
    assert ppu.apply_bg_palette(2) == 2
    assert ppu.apply_bg_palette(3) == 3


def test_ppu_apply_bg_palette_inverted() -> None:
    """Test palette application with 0x1B (inverted mapping)."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)

    # 0x1B = 00011011 => maps 0→3, 1→2, 2→1, 3→0 (inverted)
    mmu[M_BG_PALETTE_DATA] = 0x1B
    ppu.refresh_lcd_control()

    assert ppu.apply_bg_palette(0) == 3
    assert ppu.apply_bg_palette(1) == 2
    assert ppu.apply_bg_palette(2) == 1
    assert ppu.apply_bg_palette(3) == 0


def test_ppu_apply_bg_palette_monochrome() -> None:
    """Test palette application with 0xFC (monochrome)."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)

    # 0xFC = 11111100 => maps 0→0, 1-3→3
    mmu[M_BG_PALETTE_DATA] = 0xFC
    ppu.refresh_lcd_control()

    assert ppu.apply_bg_palette(0) == 0
    assert ppu.apply_bg_palette(1) == 3
    assert ppu.apply_bg_palette(2) == 3
    assert ppu.apply_bg_palette(3) == 3


def test_ppu_render_bg_window_line_palette_ids() -> None:
    """Test that render_bg_window_line returns valid palette IDs."""
    mmu = MMU(Cart("roms/hello.gb"))
    cpu = CPU(mmu)
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    for _ in range(8000):
        c = cpu.cycle()
        ppu.update(c)

    ppu.refresh_lcd_control()
    mmu[M_VIEWPORT_X] = 0
    mmu[M_VIEWPORT_Y] = 0

    line = ppu.render_bg_window_line()

    assert len(line) == SCREEN_WIDTH, "Line should be SCREEN_WIDTH pixels"
    assert all(0 <= pid <= 3 for pid in line), "All palette IDs should be 0-3"


def test_ppu_resolve_tile_data_addr_unsigned() -> None:
    """Test tile data address resolution in unsigned mode."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)

    # LCDC bit 4 = 1 => unsigned mode (0x8000 base)
    mmu[M_LCD_CONTROL] = 0x90
    ppu.refresh_lcd_control()

    addr = ppu.resolve_tile_data_addr(0)
    assert addr == 0x8000, "Tile 0 in unsigned mode should be at 0x8000"

    addr = ppu.resolve_tile_data_addr(127)
    assert addr == 0x8000 + (127 * 16), "Tile 127 in unsigned mode should be at 0x8000 + 127*16"

    addr = ppu.resolve_tile_data_addr(255)
    assert addr == 0x8000 + (255 * 16), "Tile 255 in unsigned mode should be at 0x8000 + 255*16"


def test_ppu_resolve_tile_data_addr_signed() -> None:
    """Test tile data address resolution in signed mode."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)

    # LCDC bit 4 = 0 => signed mode (0x9000 base)
    mmu[M_LCD_CONTROL] = 0x80
    ppu.refresh_lcd_control()

    addr = ppu.resolve_tile_data_addr(0)
    assert addr == 0x9000, "Tile 0 in signed mode should be at 0x9000"

    addr = ppu.resolve_tile_data_addr(127)
    assert addr == 0x9000 + (127 * 16), "Tile 127 in signed mode should be at 0x9000 + 127*16"

    # Tiles 128-255 are negative (-128 to -1)
    addr = ppu.resolve_tile_data_addr(128)
    assert addr == 0x9000 + (-128 * 16), "Tile 128 in signed mode is -128 (0x9000 - 128*16)"

    addr = ppu.resolve_tile_data_addr(255)
    assert addr == 0x9000 + (-1 * 16), "Tile 255 in signed mode is -1 (0x9000 - 16)"


def test_ppu_scan_oam_for_scanline_basic() -> None:
    """Test OAM scanning collects sprites intersecting scanline."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    ppu.refresh_lcd_control()
    ppu.scan_line = 16
    ppu.obj_size = 0  # 8x8 sprites

    # Place sprite 0: y=16, x=10, tile=0x01
    mmu[0xFE00] = 16 + 16
    mmu[0xFE01] = 10 + 8
    mmu[0xFE02] = 0x01
    mmu[0xFE03] = 0x00

    ppu.scan_oam_for_scanline()

    assert len(ppu.line_sprites) == 1, "Should find 1 sprite intersecting scanline 16"
    assert ppu.line_sprites[0].index == 0x01
    assert ppu.line_sprites[0].x == 10
    assert ppu.line_sprites[0].y == 16


def test_ppu_scan_oam_for_scanline_multiple() -> None:
    """Test OAM scanning with multiple sprites on same scanline."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    ppu.refresh_lcd_control()
    ppu.scan_line = 20
    ppu.obj_size = 0  # 8x8 sprites

    # Place 3 sprites at scanline 20
    for i in range(3):
        base = 0xFE00 + (i * 4)
        mmu[base] = 20 + 16
        mmu[base + 1] = (i * 10) + 8
        mmu[base + 2] = 0x10 + i
        mmu[base + 3] = 0x00

    ppu.scan_oam_for_scanline()

    assert len(ppu.line_sprites) == 3, "Should find 3 sprites at scanline 20"
    for i in range(3):
        assert ppu.line_sprites[i].index == 0x10 + i


def test_ppu_scan_oam_for_scanline_sprite_height_8x8() -> None:
    """Test sprite height selection for 8x8 sprites."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    ppu.refresh_lcd_control()
    ppu.obj_size = 0  # 8x8
    ppu.scan_line = 20

    mmu[0xFE00] = 20 + 16  # y=20
    mmu[0xFE01] = 10 + 8
    mmu[0xFE02] = 0x01
    mmu[0xFE03] = 0x00

    ppu.scan_oam_for_scanline()

    assert len(ppu.line_sprites) == 1
    assert ppu.line_sprites[0].height == TileSize.SMALL


def test_ppu_scan_oam_for_scanline_sprite_height_8x16() -> None:
    """Test sprite height selection for 8x16 sprites."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x84  # LCD on + obj_size (bit 2)

    ppu.refresh_lcd_control()
    assert ppu.obj_size == 1, "Bit 2 should be set for obj_size"
    ppu.scan_line = 20

    mmu[0xFE00] = 20 + 16  # y=20
    mmu[0xFE01] = 10 + 8
    mmu[0xFE02] = 0x01
    mmu[0xFE03] = 0x00

    ppu.scan_oam_for_scanline()

    assert len(ppu.line_sprites) == 1
    assert ppu.line_sprites[0].height == TileSize.LARGE


def test_ppu_scan_oam_for_scanline_limit_10() -> None:
    """Test that at most 10 sprites are scanned per scanline."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    ppu.refresh_lcd_control()
    ppu.scan_line = 20
    ppu.obj_size = 0

    # Place 15 sprites, all at scanline 20
    for i in range(15):
        base = 0xFE00 + (i * 4)
        mmu[base] = 20 + 16
        mmu[base + 1] = (i * 5) + 8
        mmu[base + 2] = i
        mmu[base + 3] = 0x00

    ppu.scan_oam_for_scanline()

    assert len(ppu.line_sprites) == 10, "Should collect at most 10 sprites per scanline"


def test_ppu_scan_oam_for_scanline_sprite_attributes() -> None:
    """Test that sprite attributes are correctly parsed."""
    mmu = MMU(Cart("roms/hello.gb"))
    ppu = PPU(mmu, headless=True)
    mmu[M_LCD_CONTROL] = 0x80

    ppu.refresh_lcd_control()
    ppu.scan_line = 20
    ppu.obj_size = 0

    # Sprite with attributes: x_flipped=1, y_flipped=1, dmg_palette=1, priority=1
    mmu[0xFE00] = 20 + 16
    mmu[0xFE01] = 10 + 8
    mmu[0xFE02] = 0x42
    mmu[0xFE03] = 0xF0  # All attribute bits set

    ppu.scan_oam_for_scanline()

    assert len(ppu.line_sprites) == 1
    sprite = ppu.line_sprites[0]
    assert sprite.x_flipped == True, "Bit 5 should set x_flipped"
    assert sprite.y_flipped == True, "Bit 6 should set y_flipped"
    assert sprite.dmg_palette == 1, "Bit 4 should set dmg_palette"
    assert sprite.priority == True, "Bit 7 should set priority"

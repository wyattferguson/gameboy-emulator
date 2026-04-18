from enum import IntEnum

from loguru import logger

from gbemu.config import (
    CYCLES_PER_SCANLINE,
    M_BG_TILE_DATA_VRAM,
    M_BG_TILE_MAP_VRAM,
    M_LCD_CONTROL,
    M_OAM_END,
    M_OAM_START,
    M_VRAM_END,
    M_VRAM_START,
    M_WIN_MAP_VRAM,
    SCAN_LINES,
    TILE_BITS,
)
from gbemu.ctypes import Tile
from gbemu.mmu import MMU
from gbemu.screen import Screen
from gbemu.utils import bit


class PPUMode(IntEnum):
    """PPU modes w/ cycle counts."""

    HBLANK = 20
    VBLANK = 114
    OAM = 80
    PIXEL_TRANSFER = 43


class PPU:
    """Picture Processing Unit (PPU) for the Gameboy."""

    def __init__(self, mmu: MMU, headless: bool = False) -> None:
        self.mmu: MMU = mmu
        self.screen: Screen = Screen()
        # self.index_methods = {
        #     [127, 255, 0],
        #     [127, 255, 0],
        #     [0, 255, 127],
        # }
        self.tiles: list[Tile] = []
        self.background: list[int] = []
        self.window: list[int] = []
        self.scan_line: int = 0
        self.frame: int = 0
        self.mode: PPUMode = PPUMode.OAM
        self.lcd_enabled: int = 0
        self.window_tile_map: int = 0
        self.window_enabled: int = 0
        self.bg_tiles: int = 0
        self.bg_tile_map: int = 0
        self.obj_size: int = 0
        self.obj_enabled: int = 0
        self.bg_priority: int = 0

    def update(self) -> None:
        """Update the screen."""
        # for address in range(M_VRAM_START, M_VRAM_END + 1):
        #     value = self.mmu[address]
        #     # logger.debug(f"PPU: Read value {value:02x} from VRAM address {address:04x}")
        # for line in range(SCAN_LINES):
        #     self.update_scanline(line)
        # logger.debug(f"PPU: Updated scanline to {self.scan_line}")

        self.refresh_lcd_control()

        self.frame += 1
        self.screen.update()

    def refresh_lcd_control(self) -> None:
        """Refresh the PPU status based on the LCD control register."""
        lcd_control = self.mmu[M_LCD_CONTROL]
        self.lcd_enabled = bit(lcd_control, 7)
        self.window_tile_map = bit(lcd_control, 6)
        self.window_enabled = bit(lcd_control, 5)
        self.bg_tiles = bit(lcd_control, 4)
        self.bg_tile_map = bit(lcd_control, 3)
        self.obj_size = bit(lcd_control, 2)
        self.obj_enabled = bit(lcd_control, 1)
        self.bg_priority = bit(lcd_control, 0)
        # print(
        #     f"""PPU: LCD Control -
        #     Register:  {lcd_control:02x}
        #     LCD Enabled: {self.lcd_enabled}
        #     Window Tile Map: {self.window_tile_map}
        #     Window Enabled: {self.window_enabled}
        #     BG Tiles: {self.bg_tiles}
        #     BG Tile Map: {self.bg_tile_map}
        #     OBJ Size: {self.obj_size}
        #     OBJ Enabled: {self.obj_enabled}
        #     BG Priority: {self.bg_priority}""",
        # )
        # print(
        #     f"BG_TILE_MAP_VRAM: {M_BG_TILE_MAP_VRAM[self.bg_tile_map][0]:04x} - {M_BG_TILE_MAP_VRAM[self.bg_tile_map][1]:04x}",
        # )
        # print(
        #     f"BG_TILE_DATA_VRAM: {M_BG_TILE_DATA_VRAM[self.bg_tiles][0]:04x} - {M_BG_TILE_DATA_VRAM[self.bg_tiles][1]:04x}",
        # )
        # print(
        #     f"WIN_MAP_VRAM: {M_WIN_MAP_VRAM[self.window_tile_map][0]:04x} - {M_WIN_MAP_VRAM[self.window_tile_map][1]:04x}",
        # )
        # tile_data = []
        # for tile_map_offset in range(8):
        #     tile_data = self.read_bg_tile_map(tile_map_offset)
        #     self.screen.draw_tile(tile_data, tile_map_offset * 8, tile_map_offset % 8)
        # self.read_bg_tile_map(0)
        # print(tile_data)
        # self.mmu.dump(M_BG_TILE_DATA_VRAM[self.bg_tiles][0], M_BG_TILE_DATA_VRAM[self.bg_tiles][1])
        # self.mmu.dump(M_BG_MAP_VRAM[self.bg_tile_map][0], M_BG_MAP_VRAM[self.bg_tile_map][1])

    def read_tile(self, tile_index: int) -> list[int]:
        """Read a tile from VRAM."""
        tile_data = []
        for i in range(TILE_BITS):
            tile_data.append(self.mmu[0x104 + tile_index * TILE_BITS + i])
        return tile_data

    def read_bg_tile_map(self, tile_index: int) -> list[list[int]]:
        """Read one tile's pixel bytes using the selected background map/data mode."""
        # map_base = M_BG_TILE_MAP_VRAM[self.bg_tile_map][0]
        map_base = 0x0104
        # for y in range(8):
        for x in range(8):
            addr = map_base + (x)
            tile_number = self.mmu[addr]
            tile2 = self.mmu[addr + 1]

            print(hex(tile_number), bin(tile_number), hex(addr))
            print(hex(tile2), bin(tile2), hex(addr + 1))

            self.screen.ds([tile_number, tile2], 0, x)
        # if self.bg_tiles == 0:
        #     # 0x8800 addressing uses signed tile numbers with 0x9000 as index 0.
        #     signed_tile_number = tile_number if tile_number < 0x80 else tile_number - 0x100
        #     data_base = 0x9000 + signed_tile_number * TILE_BITS
        # else:
        #     data_base = M_BG_TILE_DATA_VRAM[self.bg_tiles][0] + tile_number * TILE_BITS

        # return [list(self.mmu[data_base : data_base + TILE_BITS])]

    def parse_oam(self) -> None:
        """Parse OAM data into sprite objects."""
        for address in range(M_OAM_START, M_OAM_END + 1, 4):
            y_pos = self.mmu[address]
            x_pos = self.mmu[address + 1]
            tile_index = self.mmu[address + 2]
            attributes = self.mmu[address + 3]
            logger.debug(
                f"PPU: Parsed OAM entry at {address:04x} - Y: {y_pos}, X: {x_pos}, Tile: {tile_index}, Attr: {attributes:02x}",
            )

    def transfer_pixel_data(self) -> None:
        """Transfer pixel data from OAM to the screen."""

    def cycle(self) -> None:
        """Advance the PPU by one cycle."""
        if self.mode == PPUMode.OAM:
            self.mode = PPUMode.PIXEL_TRANSFER
        elif self.mode == PPUMode.PIXEL_TRANSFER:
            self.mode = PPUMode.HBLANK
        elif self.mode == PPUMode.HBLANK:
            self.mode = PPUMode.VBLANK
        elif self.mode == PPUMode.VBLANK:
            self.mode = PPUMode.OAM
            # self.frame += 1
            logger.debug(f"PPU: Starting frame {self.frame}")

    def update_scanline(self, cur_line: int) -> None:
        """Update the current scanline."""
        self.scan_line: int = (cur_line + 1) % SCAN_LINES

    def vram(self, offset: int) -> int:
        """Get value from VRAM."""
        return self.mmu[M_VRAM_START + offset]

    def tile_id(self, tile_index: int) -> int:
        """Get the tile ID for a given tile index."""
        return self.vram(tile_index * TILE_BITS)

from enum import IntEnum

from loguru import logger

from gbemu.config import (
    CYCLES_PER_SCANLINE,
    M_LCD_CONTROL,
    M_TILE_MAP_VRAM,
    M_VRAM_END,
    M_VRAM_START,
    SCAN_LINES,
    TILE_BITS,
)
from gbemu.ctypes import Tile
from gbemu.mmu import MMU
from gbemu.screen import Screen


class PPUMode(IntEnum):
    """PPU modes w/ cycle counts."""

    HBLANK = 20
    VBLANK = 114
    OAM = 80
    PIXEL_TRANSFER = 43


class PPU:
    """Picture Processing Unit (PPU) for the Gameboy."""

    def __init__(self, mmu: MMU) -> None:
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

    def update(self) -> None:
        """Update the screen."""
        # for address in range(M_VRAM_START, M_VRAM_END + 1):
        #     value = self.mmu[address]
        #     # logger.debug(f"PPU: Read value {value:02x} from VRAM address {address:04x}")
        print("\n################### PPU: Dumping Cart Ram ##################\n")
        self.dump_ram(0, 128)

        # print("\n################### PPU: Bank 1 VRAM ##################\n")
        # self.dump_ram(0x9800, 128)
        for line in range(SCAN_LINES):
            self.update_scanline(line)
            # logger.debug(f"PPU: Updated scanline to {self.scan_line}")
        self.screen.update()

    def dump_ram(self, address_start: int, size: int) -> None:
        """Dump a range of RAM for debugging."""
        for x in range(size):
            addr = address_start + (x * 16)
            row = self.mmu[addr : addr + 16]
            bytes_str = " ".join(f"{byte:02x}" for byte in row)
            line = f"{addr:04x}"
            print(f"{line}: {bytes_str}")

    def read_tile(self, tile_index: int) -> list[int]:
        """Read a tile from VRAM."""
        tile_data = []
        for i in range(TILE_BITS):
            tile_data.append(self.mmu[M_VRAM_START + tile_index * TILE_BITS + i])
        return tile_data

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

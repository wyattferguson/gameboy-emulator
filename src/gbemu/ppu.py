from loguru import logger

from gbemu.config import M_LCD_CONTROL, VRAM_END, VRAM_START
from gbemu.mmu import MMU
from gbemu.screen import Screen


class PPU:
    """Picture Processing Unit (PPU) for the Gameboy."""

    def __init__(self, mmu: MMU) -> None:
        self.mmu = mmu
        self.screen = Screen()
        self.index_methods = {
            [127, 255, 0],
            [127, 255, 0],
            [0, 255, 127],
        }
        self.tiles = []
        self.background = []
        self.window = []

    def update(self) -> None:
        """Update the screen."""
        for address in range(VRAM_START, VRAM_END + 1):
            value = self.mmu[address]
            # logger.debug(f"PPU: Read value {value:02x} from VRAM address {address:04x}")
        self.screen.update()

    def read_tile(self, tile_index: int) -> list[int]:
        """Read a tile from VRAM."""
        tile_data = []
        for i in range(16):
            tile_data.append(self.mmu[VRAM_START + tile_index * 16 + i])
        return tile_data

    def vram(self, address: int) -> int:
        """Get value from VRAM."""
        return self.mmu[VRAM_START + address]

    def tile_id(self, tile_index: int) -> int:
        """Get the tile ID for a given tile index."""
        return self.vram(tile_index * 16)

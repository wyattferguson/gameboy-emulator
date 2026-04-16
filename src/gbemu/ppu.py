from loguru import logger

from gbemu.mmu import MMU
from gbemu.screen import Screen


class PPU:
    """Picture Processing Unit (PPU) for the Gameboy."""

    def __init__(self, mmu: MMU, screen: Screen) -> None:
        self.mmu = mmu
        self.screen = screen

    def tile_id(self, tile_index: int) -> int:
        """Get the tile ID for a given tile index."""
        return self.mmu[0x8000 + tile_index * 16]

from loguru import logger

from gbemu.mmu import MMU
from gbemu.screen import Screen


class PPU:
    """Picture Processing Unit (PPU) for the Gameboy."""

    def __init__(self, mmu: MMU, screen: Screen) -> None:
        self.mmu = mmu
        self.screen = screen

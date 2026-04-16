from time import sleep

from loguru import logger

from gbemu.audio import Audio
from gbemu.cart import Cart
from gbemu.config import DEBUG, DEFAULT_ROM
from gbemu.controller import Controller
from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.ppu import PPU
from gbemu.screen import Screen


class Gbemu:
    """Gameboy Emulator."""

    def __init__(self, rom: str = DEFAULT_ROM, debug: bool = DEBUG) -> None:
        self.debug = debug
        self.rom = rom
        self.cart = Cart(self.rom)
        self.mmu = MMU(self.cart)
        self.controller = Controller(self.mmu)
        self.screen = Screen()
        self.audio = Audio()
        self.ppu = PPU(self.mmu, self.screen)
        self.cpu = CPU(self.mmu)

    def run(self) -> None:
        """Run the emulator."""
        while True:
            self.cpu.cycle()
            self.screen.update()
            self.audio.update()
            sleep(0.05)  # sleep to prevent 100% CPU usage
            self.controller.update()

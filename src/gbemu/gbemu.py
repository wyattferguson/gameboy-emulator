from time import sleep

from loguru import logger

from gbemu.apu import APU
from gbemu.cart import Cart
from gbemu.config import DEBUG, DEFAULT_ROM
from gbemu.controller import Controller
from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.ppu import PPU


class Gbemu:
    """Gameboy Emulator."""

    def __init__(self, rom: str = DEFAULT_ROM, debug: bool = DEBUG) -> None:
        self.debug = debug
        self.rom = rom
        self.cart = Cart(self.rom)
        self.mmu = MMU(self.cart)
        self.controller = Controller(self.mmu)
        self.audio = APU()
        self.ppu = PPU(self.mmu)
        self.cpu = CPU(self.mmu)

    def run(self) -> None:
        """Run the emulator."""
        while True:
            self.controller.update()
            self.cpu.cycle()
            self.audio.update()
            self.ppu.update()
            sleep(0.05)  # sleep to prevent 100% CPU usage

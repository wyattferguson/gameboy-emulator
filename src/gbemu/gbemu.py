import sys
from time import sleep

from loguru import logger

from gbemu.apu import APU
from gbemu.cart import Cart
from gbemu.config import DEBUG, DEFAULT_ROM, HEADLESS, M_VRAM_END, M_VRAM_START
from gbemu.controller import Controller
from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.ppu import PPU


class Gbemu:
    """Gameboy Emulator."""

    def __init__(
        self,
        rom: str = DEFAULT_ROM,
        debug: bool = DEBUG,
        headless: bool = HEADLESS,
    ) -> None:
        self.debug = debug
        self.rom = rom
        self.cart = Cart(self.rom)
        self.mmu = MMU(self.cart)
        self.controller = Controller(self.mmu)
        self.audio = APU()
        self.ppu = PPU(self.mmu, headless)
        self.cpu = CPU(self.mmu)

    def run(self) -> None:
        """Run the emulator."""
        while True:
            self.controller.update()
            self.cpu.cycle()
            self.ppu.update()
            # print(self.cpu.pc, hex(self.cpu.pc))
            # if self.cpu.pc == 0x64:
            #     # ppu_status_after = self.mmu[0xFF41]
            #     self.mmu.dump(0x8010, 0x8030)
            #     # self.mmu.dump(0x9800, 0x9FFF)
            #     self.mmu.dump(0xFF40, 0xFF4F)
            #     self.mmu.dump(0x0104, 0x0133)
            #     # self.mmu.dump(0xFE00, 0xFE9F)

            #     # self.ppu.parse_oam()
            #     self.ppu.refresh_lcd_control()
            #     # print(f"PPU status before: {ppu_status_before:02x}, after: {ppu_status_after:02x}")
            #     logger.debug("BIOS execution complete. PC reached 0x100.")
            # sys.exit()
            self.audio.update()
            self.ppu.update()
            sleep(0.00001)  # sleep to prevent 100% CPU usage

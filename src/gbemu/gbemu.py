import sys
from time import perf_counter, sleep

from loguru import logger

from gbemu.apu import APU
from gbemu.cart import Cart
from gbemu.config import (
    CYCLES_PER_FRAME,
    DEBUG,
    DEFAULT_ROM,
    HEADLESS,
    M_VRAM_END,
    M_VRAM_START,
    TARGET_FPS,
)
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
        """Run the GB emulator."""
        # Target wall-clock seconds per frame (1 / ~59.73).
        frame_duration = 1.0 / TARGET_FPS

        while True:
            frame_start = perf_counter()

            # Process one full frame of CPU+PPU cycles before presenting.
            frame_cycles = 0
            while frame_cycles < CYCLES_PER_FRAME:
                # Handle input once per instruction (cheap polling).
                self.controller.update()
                # CPU executes one instruction; PPU advances using the same cycle budget.
                cpu_cycles = self.cpu.cycle()
                self.ppu.update(cpu_cycles)
                self.audio.update()
                frame_cycles += cpu_cycles

            # Pace to real-time: sleep the remainder of the frame budget if we ran fast.
            elapsed = perf_counter() - frame_start
            spare = frame_duration - elapsed
            if spare > 0:
                sleep(spare)

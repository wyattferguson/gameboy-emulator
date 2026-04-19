from time import perf_counter, sleep

from gbemu.apu import APU
from gbemu.cart import Cart
from gbemu.config import (
    CYCLES_PER_FRAME,
    DEBUG,
    DEFAULT_ROM,
    HEADLESS,
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
        smoothed_fps: float | None = None

        while True:
            frame_start = perf_counter()

            self._run_frame()
            self._pace_frame(frame_start, frame_duration)

            frame_elapsed = perf_counter() - frame_start
            if frame_elapsed > 0:
                instant_fps = 1.0 / frame_elapsed
                smoothed_fps = (
                    instant_fps
                    if smoothed_fps is None
                    else (smoothed_fps * 0.9) + (instant_fps * 0.1)
                )
                if self.ppu.screen:
                    self.ppu.screen.set_fps(smoothed_fps)

    def _run_frame(self) -> None:
        # Poll input once per frame; per-instruction event pumping is too expensive.
        self.controller.update()

        # Process one full frame of CPU+PPU cycles before presenting.
        frame_cycles = 0
        while frame_cycles < CYCLES_PER_FRAME:
            # CPU executes one instruction; PPU advances using the same cycle budget.
            cpu_cycles = self.cpu.cycle()
            self.ppu.update(cpu_cycles)
            self.audio.update()
            frame_cycles += cpu_cycles

    @staticmethod
    def _pace_frame(frame_start: float, frame_duration: float) -> None:
        # Pace to real-time: sleep the remainder of the frame budget if we ran fast.
        spare = frame_duration - (perf_counter() - frame_start)
        if spare > 0:
            sleep(spare)

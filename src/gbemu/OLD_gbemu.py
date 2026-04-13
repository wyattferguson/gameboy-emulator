from gbemu.audio import Audio
from gbemu.cart import Cart
from gbemu.config import DEFAULT_ROM
from gbemu.cpu import CPU
from gbemu.joypad import Joypad
from gbemu.mmu import MMU
from gbemu.screen import Screen


class Gbemu:
    def __init__(self, rom: str = DEFAULT_ROM, debug: bool = False) -> None:
        self.debug = debug
        self.rom = rom
        self.cart = Cart(self.rom)
        self.mmu = MMU(self.cart)
        # self.joypad = Joypad(self.mmu)
        # self.screen = Screen()
        # self.audio = Audio()
        self.cpu = CPU(self.mmu, self.debug)

    def run(self) -> None:
        """Run the emulator."""
        print(self.cart)
        # print(self.mmu)
        print("MEMORY:")
        print(self.mmu)
        print("GAME CYCLE:")
        while True:
            self.cpu.cycle()
            # self.joypad.update()

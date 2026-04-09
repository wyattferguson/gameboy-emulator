from gbemu.audio import Audio
from gbemu.cart import Cart
from gbemu.config import DEFAULT_ROM
from gbemu.cpu import CPU
from gbemu.joypad import Joypad
from gbemu.ram import RAM
from gbemu.screen import Screen


class Gbemu:
    def __init__(self, rom: str = DEFAULT_ROM, debug: bool = False) -> None:
        self.debug = debug
        self.rom = rom
        self.cart = Cart(self.rom)
        self.ram = RAM(self.cart)
        # self.joypad = Joypad(self.ram)
        # self.screen = Screen()
        # self.audio = Audio()
        self.cpu = CPU(self.ram, self.debug)

    def run(self) -> None:
        """Run the emulator."""
        print(self.cart)
        # print(self.ram)
        print("MEMORY:")
        print(self.ram)
        print("GAME CYCLE:")
        while True:
            self.cpu.cycle()
            # self.joypad.update()

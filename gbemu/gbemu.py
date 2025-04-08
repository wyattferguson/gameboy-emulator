from ._config import DEFAULT_ROM
from .cart import Cart
from .cpu import CPU
from .joypad import Joypad
from .ram import RAM
from .screen import Screen


class Gbemu:
    def __init__(self, rom: str = DEFAULT_ROM, debug: bool = False) -> None:
        self.debug = debug
        self.rom = rom
        self.cart = Cart(self.rom)
        self.ram = RAM(self.cart)
        # self.joypad = Joypad(self.ram)
        # self.screen = Screen()
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

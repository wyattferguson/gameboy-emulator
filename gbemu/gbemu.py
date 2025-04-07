from ._config import DEFAULT_ROM
from .cart import Cart
from .cpu import CPU
from .ram import RAM
from .screen import Screen


class Gbemu:
    def __init__(self, rom: str = DEFAULT_ROM, debug: bool = False) -> None:
        self.debug = debug
        self.rom = rom
        self.cart = Cart(self.rom)
        self.ram = RAM(self.cart)
        # self.screen = Screen()
        self.cpu = CPU(self.ram, self.debug)  # CPU instance will be created in the run method

    def run(self) -> None:
        """Run the emulator."""
        print("Running GBEmu...")
        print(self.cart)

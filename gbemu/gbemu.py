from ._config import DEFAULT_ROM
from .cart import Cart
from .cpu import CPU
from .screen import Screen


class Gbemu:
    def __init__(self, rom: str = DEFAULT_ROM, debug: bool = False) -> None:
        self.debug = debug
        self.rom = rom
        self.cart = Cart(self.rom)
        # self.screen = Screen()
        # self.cpu = CPU(self.debug)  # CPU instance will be created in the run method

    def run(self) -> None:
        """Run the emulator."""
        # self.cpu.load_rom(self.rom)
        print("Running GBEmu...")
        print(self.cart)
        # self.cart.load()

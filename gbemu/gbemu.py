from ._config import MEMORY, PROGRAM_START
from .cpu import CPU
from .screen import Screen


class gbemu:
    def __init__(self, rom: str = None, debug: bool = False) -> None:
        self.debug = debug
        self.rom = rom
        self.screen = Screen()
        self.cpu = CPU()  # CPU instance will be created in the run method

    def run(self) -> None:
        """Run the emulator."""
        self.load_rom(self.rom)

    def load_rom(self, rom_file: str) -> None:
        """Load .GB ROM into memory"""
        print(f"Loading Rom - {rom_file}")

        with open(rom_file, "rb") as rom_ptr:
            # read the rom file and convert to list of bytes
            rom = bytearray(rom_ptr.read())
            # convert to list of integers
        self.PC = PROGRAM_START  # program start in memory
        self.mem[self.PC : len(rom)] = rom  # copy rom to ram

        # for x in range(100):
        #     addr = self.PC + x
        #     code = self.mem[addr]
        #     print(addr, hex(addr), code)
        #     OPCODE_TABLE[hex(code)]
        # exit()

from ._config import BIOS, MEMORY_SIZE, PROGRAM_START
from ._exceptions import RamError
from .cart import Cart


class RAM:
    def __init__(self, cart: Cart, size: int = MEMORY_SIZE) -> None:
        """Initialize RAM with a given size."""
        self.size = size
        self._memory = [0] * self.size
        # self._memory[0 : len(BIOS)] = BIOS  # load system bios
        # copy rom into memory for now
        self._memory[0 : len(cart.rom)] = cart.rom
        self._cart = cart

    def __getitem__(self, address: int) -> hex:
        if address < 0 or address >= self.size:
            raise RamError(f"Address {address} is out of bounds.")
        return self._memory[address]

    def __setitem__(self, address: int, value: int) -> None:
        if address < 0 or address >= self.size:
            raise RamError(f"Address {address} is out of bounds.")
        self._memory[address] = value

    def __str__(self):
        # print memory in 16 byte chunks
        chunk_size: int = 16
        print_rows: int = 4
        return "\n".join(
            " ".join(f"{byte:02x}" for byte in self._memory[i : i + chunk_size])
            for i in range(PROGRAM_START, PROGRAM_START + (chunk_size * print_rows), chunk_size)
        )

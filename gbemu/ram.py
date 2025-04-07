from ._config import BIOS, MEMORY_SIZE, PROGRAM_START
from ._exceptions import RamError
from .cart import Cart


class RAM:
    def __init__(self, cart: Cart, size: int = MEMORY_SIZE) -> None:
        """Initialize RAM with a given size."""
        self.size = size
        self._memory = bytearray(self.size)
        self._memory[0 : len(BIOS)] = BIOS  # load system bios
        # copy rom into memory for now
        self._memory[PROGRAM_START : PROGRAM_START + len(cart.rom)] = cart.rom
        self._cart = cart

    @property
    def memory(self) -> bytearray:
        return self._memory

    @memory.setter
    def memory(self, address: int, value: bytearray) -> None:
        # if not isinstance(value, bytearray):
        #     raise TypeError("Memory must be a bytearray.")
        # if len(value) > self.size:
        #     raise RamError(
        #         f"Write Error: Address {address} out of bounds for RAM size {self.size}."
        #     )
        self._memory[address] = value

    # def read(self, address: int | list[int, int]) -> int:
    #     """Read a byte from RAM at the specified address."""
    #     if isinstance(address, list):
    #         return [self._memory[a] for a in address if 0 <= a < self.size]
    #     if address < 0 or address >= self.size:
    #         raise RamError(f"Read Error: Address {address} out of bounds for RAM size {self.size}.")
    #     return self._memory[address]

    # def write(self, address: int, value: int) -> None:
    #     """Write a byte to RAM at the specified address."""
    #     if address < 0 or address >= self.size:
    #         raise RamError(
    #             f"Write Error: Address {address} out of bounds for RAM size {self.size}."
    #         )
    #     self._memory[address] = value

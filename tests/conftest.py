from gbemu.config import MEMORY_SIZE
from gbemu.exceptions import RamError


class RAM:
    """Simple RAM stub used by CPU unit tests."""

    def __init__(self) -> None:
        self._memory = [0] * MEMORY_SIZE

    @property
    def size(self) -> int:
        return MEMORY_SIZE

    def __getitem__(self, address: int) -> int:
        if address < 0 or address >= self.size:
            raise RamError(f"Address {address} is out of bounds.")
        return self._memory[address]

    def __setitem__(self, address: int, value: int) -> None:
        if address < 0 or address >= self.size:
            raise RamError(f"Address {address} is out of bounds.")
        self._memory[address] = value

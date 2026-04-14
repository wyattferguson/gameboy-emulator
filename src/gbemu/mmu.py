from gbemu.cart import Cart
from gbemu.config import BIOS, MEMORY_SIZE, PC_START
from gbemu.exceptions import RamError


class MMU:
    """Unified system memory."""

    def __init__(self, cart: Cart | None = None, size: int = MEMORY_SIZE) -> None:
        self.size = size
        self._memory = [0] * self.size
        # self._memory[0 : len(BIOS)] = BIOS  # load system bios
        self._cart = cart
        if cart:
            # FIX: Load max 32kb of ROM and bank switching for larger ROMs
            self._memory[0 : len(cart.rom)] = cart.rom

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, address: int | slice) -> int | list[int]:
        if isinstance(address, slice):
            return self._memory[address]
        if address < 0 or address >= len(self):
            raise RamError(f"Address {address} is out of bounds.")
        return self._memory[address]

    def __setitem__(self, address: int, value: int) -> None:
        if address < 0 or address >= len(self):
            raise RamError(f"Address {address} is out of bounds.")
        self._memory[address] = value

    def __str__(self) -> str:
        """Return memory in 16 byte chunks."""
        chunk_size: int = 16
        print_rows: int = 4
        return "\n".join(
            " ".join(f"{byte:02x}" for byte in self._memory[i : i + chunk_size])
            for i in range(PC_START, PC_START + (chunk_size * print_rows), chunk_size)
        )

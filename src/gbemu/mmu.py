from typing import overload

from gbemu.cart import Cart
from gbemu.config import BIOS, M_BOOT_ROM_MAPPING_CONTROL, MEMORY_SIZE


class MMU:
    """Unified system memory."""

    def __init__(self, cart: Cart | None = None, size: int = MEMORY_SIZE) -> None:
        self.size = size
        self._memory = [0] * self.size
        self._boot_rom_mapped = True
        if cart:
            # FIX: Load max 32kb of ROM and bank switching for larger ROMs
            self._memory[0 : len(cart.rom)] = cart.rom
        self._memory[0 : len(BIOS)] = BIOS  # load system bios
        self._cart = cart

    def __len__(self) -> int:
        return self.size

    @property
    def memory(self) -> list[int]:
        """Expose raw memory for performance-sensitive subsystems."""
        return self._memory

    @overload
    def __getitem__(self, address: int) -> int: ...

    @overload
    def __getitem__(self, address: slice) -> list[int]: ...

    def __getitem__(self, address: int | slice) -> int | list[int]:
        return self.memory[address]

    def __setitem__(self, address: int, value: int) -> None:
        # Direct assignment with 8-bit masking
        value &= 0xFF
        self._memory[address] = value

        if (
            address == M_BOOT_ROM_MAPPING_CONTROL
            and value != 0
            and self._boot_rom_mapped
            and self._cart is not None
        ):
            self._memory[0 : len(BIOS)] = self._cart.rom[0 : len(BIOS)]
            self._boot_rom_mapped = False

    def dump(self, start: int = 0, end: int = 0xFFFF) -> None:
        """Print memory slice in formatted rows."""
        chunk_size: int = 16
        print(f"\n################## MMU: {start:04x}-{end:04x}  ##################\n")
        for i in range(start, end + 1, chunk_size):
            chunk = self._memory[i : i + chunk_size]
            print(f"{i:04x}: " + " ".join(f"{byte:02x}" for byte in chunk))
        print("\n#####################################################\n")

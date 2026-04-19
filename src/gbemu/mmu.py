from typing import overload

from gbemu.cart import Cart
from gbemu.config import (
    BIOS,
    M_BOOT_ROM_MAPPING_CONTROL,
    M_DIVIDER,
    M_LCD_STATUS,
    M_OAM_DMA_SOURCE_START,
    MEMORY_SIZE,
)


class MMU:
    """Unified system memory."""

    def __init__(self, cart: Cart | None = None, size: int = MEMORY_SIZE) -> None:
        self.size = size
        self._memory = [0] * self.size
        self._boot_rom_mapped = True
        self._cart = cart if (cart is not None and cart.rom is not None) else None
        if self._cart is not None:
            # FIX: Load max 32kb of ROM and bank switching for larger ROMs
            self._memory[0 : len(self._cart.rom)] = self._cart.rom
        self._memory[0 : len(BIOS)] = BIOS  # load system bios
        self._oam_locked = False
        self._vram_locked = False

    def set_ppu_bus_access(self, *, oam_locked: bool, vram_locked: bool) -> None:
        """Set CPU-visible OAM/VRAM bus lock state based on active PPU mode."""
        self._oam_locked = oam_locked
        self._vram_locked = vram_locked

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
        if isinstance(address, int):
            # FEA0-FEFF is unusable memory area and reads as 0xFF.
            if 0xFEA0 <= address <= 0xFEFF:
                return 0xFF

            # During mode 2/3, CPU cannot access OAM.
            if self._oam_locked and 0xFE00 <= address <= 0xFE9F:
                return 0xFF

            # During mode 3, CPU cannot access VRAM.
            if self._vram_locked and 0x8000 <= address <= 0x9FFF:
                return 0xFF
        return self.memory[address]

    def __setitem__(self, address: int, value: int) -> None:
        value &= 0xFF

        # FF04 DIV resets to 0 on any write.
        if address == M_DIVIDER:
            self._memory[address] = 0
            return

        # FF41 STAT mode/coincidence bits (0-2) are read-only.
        if address == M_LCD_STATUS:
            self._memory[address] = (self._memory[address] & 0x07) | (value & 0xF8)
            return

        # FF50 controls one-way boot ROM unmap and is always writable as IO state.
        if address == M_BOOT_ROM_MAPPING_CONTROL:
            self._memory[address] = value
            if value != 0 and self._boot_rom_mapped and self._cart is not None:
                self._memory[0 : len(BIOS)] = self._cart.rom[0 : len(BIOS)]
                self._boot_rom_mapped = False
            return

        # OAM DMA: writing a page number triggers an instant 160-byte copy to OAM.
        # On hardware, writing to 0xFF46 copies 160 bytes from (value * 0x100) to OAM.
        if address == M_OAM_DMA_SOURCE_START:
            self._memory[address] = value
            src = value * 0x100
            self._memory[0xFE00:0xFEA0] = self._memory[src : src + 160]
            return

        # Cartridge ROM region is not directly writable on hardware.
        # Writes here are mapper control on MBC carts; for ROM-only carts they are ignored.
        if self._cart is not None and 0x0000 <= address <= 0x7FFF:
            return

        # C000-DDFF work RAM is mirrored at E000-FDFF (echo RAM).
        if 0xC000 <= address <= 0xDDFF:
            self._memory[address] = value
            self._memory[address + 0x2000] = value
            return

        if 0xE000 <= address <= 0xFDFF:
            self._memory[address] = value
            self._memory[address - 0x2000] = value
            return

        # FEA0-FEFF is unusable memory area; writes are ignored.
        if 0xFEA0 <= address <= 0xFEFF:
            return

        # During mode 2/3, CPU writes to OAM are ignored.
        if self._oam_locked and 0xFE00 <= address <= 0xFE9F:
            return

        # During mode 3, CPU writes to VRAM are ignored.
        if self._vram_locked and 0x8000 <= address <= 0x9FFF:
            return

        self._memory[address] = value

    def dump(self, start: int = 0, end: int = 0xFFFF) -> None:
        """Print memory slice in formatted rows."""
        chunk_size: int = 16
        print(f"\n################## MMU: {start:04x}-{end:04x}  ##################\n")
        for i in range(start, end + 1, chunk_size):
            chunk = self._memory[i : i + chunk_size]
            print(f"{i:04x}: " + " ".join(f"{byte:02x}" for byte in chunk))
        print("\n#####################################################\n")

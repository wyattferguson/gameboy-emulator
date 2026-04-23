"""

This module implements the memory management unit with DMG-mapped read/write behavior.

Step-by-step:
1. Allocate the 64KB memory space and map boot/cartridge data.
2. Apply special register semantics for JOYP, DIV, STAT, DMA, and boot unmap.
3. Enforce address-space rules for ROM, WRAM echo, and unusable ranges.
4. Gate OAM/VRAM access based on active PPU bus lock state.
5. Provide byte/slice interfaces used by CPU and peripherals.
"""

from collections.abc import Callable
from typing import overload

from gbemu.cart import Cart
from gbemu.constants import (
    BIOS,
    M_BOOT_ROM_MAPPING_CONTROL,
    M_DIVIDER,
    M_JOYPAD,
    M_LCD_STATUS,
    M_OAM_DMA_SOURCE_START,
    M_OAM_END,
    M_OAM_START,
    M_VRAM_END,
    M_VRAM_START,
    MEMORY_SIZE,
    MMU_ECHO_END,
    MMU_ECHO_START,
    MMU_ROM_BANK_SIZE,
    MMU_ROM_END,
    MMU_UNUSABLE_END,
    MMU_UNUSABLE_START,
    MMU_WRAM_END,
    MMU_WRAM_START,
)
from gbemu.mappers import MemoryMapper, create_mapper


class MMU:
    """Unified system memory."""

    _ECHO_OFFSET = 0x2000
    _DMA_LENGTH = 160

    def __init__(self, cart: Cart | None = None, size: int = MEMORY_SIZE) -> None:
        self.size = size
        self._memory = [0] * self.size
        self._boot_rom_mapped = True
        self._cart = cart if (cart is not None and cart.rom is not None) else None

        if self._cart and self._cart.rom is not None:
            # Map the full 0000-7FFF cartridge ROM region on startup.
            self._memory[0 : MMU_ROM_END + 1] = self._cart.rom[0 : MMU_ROM_END + 1]

        self._memory[0 : len(BIOS)] = BIOS  # load system bios
        self._oam_locked = False
        self._vram_locked = False
        self._joypad_refresh_hook: Callable[[], None] | None = None
        self._mapper: MemoryMapper | None = create_mapper(self._cart)

        # JOYP powers up as all high (no selection, no keys pressed).
        self._memory[M_JOYPAD] = 0xFF

        if self._mapper is not None:
            self._mapper.initialize(self._memory)

        self._overlay_boot_rom()

    def _overlay_boot_rom(self) -> None:
        """Keep the BIOS visible while the boot ROM is still mapped."""
        if self._boot_rom_mapped:
            self._memory[0 : len(BIOS)] = BIOS

    def load_bank(self, value: int = 0) -> None:
        """Force a ROM bank remap through the active mapper."""
        if self._mapper is None:
            return
        self._mapper.load_bank(value, self._memory)
        self._overlay_boot_rom()

    def register_joypad_refresh_hook(self, hook: Callable[[], None]) -> None:
        """Register a callback invoked when JOYP select lines are written."""
        self._joypad_refresh_hook = hook

    def set_ppu_bus_access(self, *, oam_locked: bool, vram_locked: bool) -> None:
        """Set CPU-visible OAM/VRAM bus lock state based on active PPU mode."""
        self._oam_locked = oam_locked
        self._vram_locked = vram_locked

    @property
    def memory(self) -> list[int]:
        """Expose raw memory for performance-sensitive subsystems."""
        return self._memory

    @overload
    def __getitem__(self, address: int) -> int: ...

    @overload
    def __getitem__(self, address: slice) -> list[int]: ...

    def __getitem__(self, address: int | slice) -> int | list[int]:
        """Read one byte or a byte slice from memory with hardware read rules."""
        memory = self._memory
        if isinstance(address, int):
            # Keep this path inline (instead of helper dispatch) because CPU fetches
            # go through here for nearly every instruction.

            # FEA0-FEFF is unusable memory area and reads as 0xFF.
            if MMU_UNUSABLE_START <= address <= MMU_UNUSABLE_END:
                return 0xFF

            # During mode 2/3, CPU cannot access OAM.
            if self._oam_locked and M_OAM_START <= address <= M_OAM_END:
                return 0xFF

            # During mode 3, CPU cannot access VRAM.
            if self._vram_locked and M_VRAM_START <= address <= M_VRAM_END:
                return 0xFF

            return memory[address]
        return memory[address]

    def _unmap_boot_rom_if_needed(self, value: int) -> None:
        """Apply one-way FF50 boot-ROM unmap behavior when a cartridge is present."""
        if value == 0 or not self._boot_rom_mapped or self._cart is None:
            return

        self._boot_rom_mapped = False
        rom = self._cart.rom
        if rom is not None:
            self._memory[0 : len(BIOS)] = rom[0 : len(BIOS)]
        if self._mapper is not None:
            self._mapper.initialize(self._memory)

    def __setitem__(self, address: int, value: int) -> None:
        """Write one byte, applying IO semantics and mapped-region rules."""
        value &= 0xFF

        # Bank switching request
        if address < 0x8000:
            if self._mapper is not None:
                self._mapper.handle_write(address, value, self._memory)
                self._overlay_boot_rom()
                return
            # No cartridge loaded: allow direct writes (test/debug support).

        # Try IO register handlers first (cheapest branch for common path)
        if self._handle_io_write(address, value):
            return

        # Check protected regions
        if self._is_write_protected(address):
            return

        # Handle mirrored WRAM/echo regions
        if self._handle_wram_echo_write(address, value):
            return

        # Check PPU bus locks
        if self._is_ppu_locked(address):
            return

        self._memory[address] = value

    def _handle_io_write(self, address: int, value: int) -> bool:
        """Handle IO register writes. Return True if handled."""
        memory = self._memory

        if address == M_DIVIDER:
            memory[address] = 0
            return True
        if address == M_JOYPAD:
            memory[address] = (memory[address] & 0xCF) | (value & 0x30)
            if self._joypad_refresh_hook:
                self._joypad_refresh_hook()
            return True
        if address == M_LCD_STATUS:
            memory[address] = (memory[address] & 0x07) | (value & 0xF8)
            return True
        if address == M_BOOT_ROM_MAPPING_CONTROL:
            memory[address] = value
            self._unmap_boot_rom_if_needed(value)
            return True
        if address == M_OAM_DMA_SOURCE_START:
            memory[address] = value
            src = value * 0x100
            memory[M_OAM_START : M_OAM_END + 1] = memory[src : src + self._DMA_LENGTH]
            return True
        return False

    def _is_write_protected(self, address: int) -> bool:
        """Check if address is in a write-protected region."""
        return MMU_UNUSABLE_START <= address <= MMU_UNUSABLE_END or (
            self._cart is not None and address <= MMU_ROM_END
        )

    def _handle_wram_echo_write(self, address: int, value: int) -> bool:
        """Handle WRAM/echo mirroring. Return True if handled."""
        if MMU_WRAM_START <= address <= MMU_WRAM_END:
            self._memory[address] = value
            self._memory[address + self._ECHO_OFFSET] = value
            return True
        if MMU_ECHO_START <= address <= MMU_ECHO_END:
            self._memory[address] = value
            self._memory[address - self._ECHO_OFFSET] = value
            return True
        return False

    def _is_ppu_locked(self, address: int) -> bool:
        """Check if PPU bus locks prevent this write."""
        return (self._oam_locked and M_OAM_START <= address <= M_OAM_END) or (
            self._vram_locked and M_VRAM_START <= address <= M_VRAM_END
        )

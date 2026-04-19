from typing import overload

from gbemu.cart import Cart
from gbemu.config import (
    BIOS,
    M_BOOT_ROM_MAPPING_CONTROL,
    M_DIVIDER,
    M_INTERRUPT_FLAG,
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
    MMU_ROM_END,
    MMU_ROM_START,
    MMU_UNUSABLE_END,
    MMU_UNUSABLE_START,
    MMU_WRAM_END,
    MMU_WRAM_START,
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
            rom = self._cart.rom
            if rom is not None:
                self._memory[0 : len(rom)] = rom
        self._memory[0 : len(BIOS)] = BIOS  # load system bios
        self._oam_locked = False
        self._vram_locked = False
        self._joyp_select = 0x30
        self._joyp_buttons = 0x0F
        self._joyp_dpad = 0x0F
        self._sync_joypad_register()

    def _sync_joypad_register(self) -> None:
        joypad = 0xCF | self._joyp_select
        if (self._joyp_select & 0x10) == 0:
            joypad &= 0xF0 | self._joyp_dpad
        if (self._joyp_select & 0x20) == 0:
            joypad &= 0xF0 | self._joyp_buttons
        self._memory[M_JOYPAD] = joypad & 0xFF

    @staticmethod
    def _in_range(address: int, start: int, end: int) -> bool:
        return start <= address <= end

    def _is_unusable(self, address: int) -> bool:
        return self._in_range(address, MMU_UNUSABLE_START, MMU_UNUSABLE_END)

    def _is_oam(self, address: int) -> bool:
        return self._in_range(address, M_OAM_START, M_OAM_END)

    def _is_vram(self, address: int) -> bool:
        return self._in_range(address, M_VRAM_START, M_VRAM_END)

    def _is_cart_rom(self, address: int) -> bool:
        return self._cart is not None and self._in_range(address, MMU_ROM_START, MMU_ROM_END)

    def _is_wram(self, address: int) -> bool:
        return self._in_range(address, MMU_WRAM_START, MMU_WRAM_END)

    def _is_echo_ram(self, address: int) -> bool:
        return self._in_range(address, MMU_ECHO_START, MMU_ECHO_END)

    def set_joypad_pressed(self, mask: int, *, dpad: bool, pressed: bool) -> None:
        """Update latched JOYP pressed-state bits and request interrupt on key press."""
        target = self._joyp_dpad if dpad else self._joyp_buttons
        previous = target
        if pressed:
            target &= (~mask) & 0x0F
        else:
            target |= mask & 0x0F

        if dpad:
            self._joyp_dpad = target
        else:
            self._joyp_buttons = target

        if previous != target and pressed:
            self._memory[M_INTERRUPT_FLAG] |= 0x10
        self._sync_joypad_register()

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
            if address == M_JOYPAD:
                self._sync_joypad_register()
                return self._memory[address]

            # FEA0-FEFF is unusable memory area and reads as 0xFF.
            if self._is_unusable(address):
                return 0xFF

            # During mode 2/3, CPU cannot access OAM.
            if self._oam_locked and self._is_oam(address):
                return 0xFF

            # During mode 3, CPU cannot access VRAM.
            if self._vram_locked and self._is_vram(address):
                return 0xFF
        return self.memory[address]

    def _handle_io_write(self, address: int, value: int) -> bool:
        # FF04 DIV resets to 0 on any write.
        if address == M_DIVIDER:
            self._memory[address] = 0
            return True

        # FF00 JOYP only exposes writable select bits 4-5.
        if address == M_JOYPAD:
            self._joyp_select = value & 0x30
            self._sync_joypad_register()
            return True

        # FF41 STAT mode/coincidence bits (0-2) are read-only.
        if address == M_LCD_STATUS:
            self._memory[address] = (self._memory[address] & 0x07) | (value & 0xF8)
            return True

        # FF50 controls one-way boot ROM unmap and is always writable as IO state.
        if address == M_BOOT_ROM_MAPPING_CONTROL:
            self._memory[address] = value
            if value != 0 and self._boot_rom_mapped and self._cart is not None:
                rom = self._cart.rom
                if rom is not None:
                    self._memory[0 : len(BIOS)] = rom[0 : len(BIOS)]
                self._boot_rom_mapped = False
            return True

        # OAM DMA: writing a page number triggers an instant 160-byte copy to OAM.
        # On hardware, writing to 0xFF46 copies 160 bytes from (value * 0x100) to OAM.
        if address == M_OAM_DMA_SOURCE_START:
            self._memory[address] = value
            src = value * 0x100
            self._memory[M_OAM_START : M_OAM_END + 1] = self._memory[src : src + 160]
            return True

        return False

    def _handle_memory_write(self, address: int, value: int) -> bool:
        # Cartridge ROM region is not directly writable on hardware.
        # Writes here are mapper control on MBC carts; for ROM-only carts they are ignored.
        if self._is_cart_rom(address):
            return True

        # C000-DDFF work RAM is mirrored at E000-FDFF (echo RAM).
        if self._is_wram(address):
            self._memory[address] = value
            self._memory[address + 0x2000] = value
            return True

        if self._is_echo_ram(address):
            self._memory[address] = value
            self._memory[address - 0x2000] = value
            return True

        # FEA0-FEFF is unusable memory area; writes are ignored.
        if self._is_unusable(address):
            return True

        # During mode 2/3, CPU writes to OAM are ignored.
        if self._oam_locked and self._is_oam(address):
            return True

        # During mode 3, CPU writes to VRAM are ignored.
        return bool(self._vram_locked and self._is_vram(address))

    def __setitem__(self, address: int, value: int) -> None:
        value &= 0xFF

        if self._handle_io_write(address, value):
            return
        if self._handle_memory_write(address, value):
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

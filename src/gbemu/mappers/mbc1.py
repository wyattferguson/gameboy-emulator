from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gbemu.cart import Cart
from gbemu.constants import MMU_ROM_BANK_SIZE


class MBC1Mapper:
    """MBC1 mapper supporting ROM bank switching and mode control."""

    _BANK0_START = 0x0000
    _BANK1_START = 0x4000

    def __init__(self, cart: "Cart") -> None:
        self._cart = cart
        self._rom_bank_low5 = 1
        self._rom_bank_high2 = 0
        self._mode = 0

    def initialize(self, memory: list[int]) -> None:
        self._apply_mapping(memory)

    def handle_write(self, address: int, value: int, memory: list[int]) -> None:
        if address < 0x2000:
            # RAM enable register (external RAM not modeled yet).
            return
        if address < 0x4000:
            self._rom_bank_low5 = value & 0x1F
        elif address < 0x6000:
            self._rom_bank_high2 = value & 0x03
        else:
            self._mode = value & 0x01
        self._apply_mapping(memory)

    def load_bank(self, value: int, memory: list[int]) -> None:
        self._rom_bank_low5 = value & 0x1F
        self._apply_mapping(memory)

    def _apply_mapping(self, memory: list[int]) -> None:
        low5 = (self._rom_bank_low5 & 0x1F) or 1
        high2 = self._rom_bank_high2 & 0x03
        switch_bank = (high2 << 5) | low5
        fixed_bank = 0 if self._mode == 0 else high2 << 5

        self._map_rom_bank(memory, self._BANK0_START, fixed_bank)
        self._map_rom_bank(memory, self._BANK1_START, switch_bank)

    def _map_rom_bank(self, memory: list[int], dst_start: int, bank_num: int) -> None:
        rom = self._cart.rom
        if rom is None:
            return

        bank_count = len(rom) // MMU_ROM_BANK_SIZE
        if bank_count == 0:
            return

        bank_num %= bank_count
        src_start = bank_num * MMU_ROM_BANK_SIZE
        src_end = src_start + MMU_ROM_BANK_SIZE
        chunk = rom[src_start:src_end]
        if len(chunk) != MMU_ROM_BANK_SIZE:
            return
        memory[dst_start : dst_start + MMU_ROM_BANK_SIZE] = chunk

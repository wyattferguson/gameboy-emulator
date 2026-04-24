"""Cartridge memory mapper implementations selected by Cart."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from gbemu.cart import Cart
from gbemu.mappers.mbc1 import MBC1Mapper
from gbemu.mappers.rom_only import RomOnlyMapper


class MemoryMapper(Protocol):
    """Mapper interface for ROM control writes and bank remapping."""

    def initialize(self, memory: list[int]) -> None:
        """Apply initial mapper state to MMU memory windows."""

    def handle_write(self, address: int, value: int, memory: list[int]) -> None:
        """Handle writes in 0000-7FFF cartridge control region."""

    def load_bank(self, value: int, memory: list[int]) -> None:
        """Compatibility helper to force a ROM bank selection."""


def get_mapper(cart: "Cart | None") -> MemoryMapper:
    """Get mapper matching cartridge metadata."""
    if cart is None or cart.rom is None:
        return RomOnlyMapper()

    if cart.cart_type.startswith("MBC1"):
        return MBC1Mapper(cart)

    return RomOnlyMapper()

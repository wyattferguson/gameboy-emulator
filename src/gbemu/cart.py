from pathlib import Path
from typing import TYPE_CHECKING

from gbemu.config import (
    CART_TYPE,
    CGB_FLAG,
    DEFAULT_ROM,
    DESTINATION_CODE,
    NEW_LICENSEE,
    OLD_LICENSEE,
)
from gbemu.constants import (
    H_CART_TYPE,
    H_CGB_FLAG,
    H_DESTINATION,
    H_HEADER_CHECKSUM,
    H_MANUFACTURER_END,
    H_MANUFACTURER_START,
    H_NEW_LICENSEE_END,
    H_NEW_LICENSEE_START,
    H_OLD_LICENSEE,
    H_ROM_SIZE,
    H_SGB_FLAG,
    H_TITLE_END,
    H_TITLE_START,
    H_VERSION,
    MMU_ROM_BANK_SIZE,
)
from gbemu.mappers.mappers import get_mapper

if TYPE_CHECKING:
    from gbemu.mappers.mappers import MemoryMapper


class Cart:
    """GB Cartridge."""

    def __init__(self, filename: str = DEFAULT_ROM) -> None:
        self.filename = filename
        self.rom: bytearray | None = self.load()
        self.manufacturer_code = ""
        self.title = ""
        self.cgb_flag = "Unknown"
        self.sgb_flag = 0
        self.cart_type = "Unknown"
        self.rom_size = 0
        self.banks = 0
        self.destination = "Unknown"
        self.version = 0
        self.licensee = "Unknown"
        self.mapper: MemoryMapper | None = None

        if self.rom is None:
            return

        self._decode_header(self.rom)

        self.mapper = get_mapper(self)

    def _decode_header(self, rom: bytearray) -> None:
        """Decode cartridge metadata fields from ROM header bytes."""
        try:
            self.manufacturer_code = self._decode_text(
                rom,
                H_MANUFACTURER_START,
                H_MANUFACTURER_END,
            )
            self.title = self._decode_text(rom, H_TITLE_START, H_TITLE_END, encoding="ASCII")
            self.cgb_flag = CGB_FLAG.get(f"{rom[H_CGB_FLAG] & 0xF0:02X}", "Unknown")
            self.sgb_flag = rom[H_SGB_FLAG]
            self.cart_type = CART_TYPE.get(rom[H_CART_TYPE], "Unknown")
            self.rom_size = 32 * (1 << rom[H_ROM_SIZE])
            self.banks = max(1, len(rom) // MMU_ROM_BANK_SIZE)
            self.destination = DESTINATION_CODE.get(rom[H_DESTINATION], "Unknown")
            self.version = rom[H_VERSION]
            self.licensee = (
                NEW_LICENSEE.get(
                    rom[H_NEW_LICENSEE_START:H_NEW_LICENSEE_END].decode(errors="replace"),
                    "Unknown",
                )
                if rom[H_OLD_LICENSEE] == 33
                else OLD_LICENSEE.get(f"{rom[H_OLD_LICENSEE]:X}", "Unknown")
            )
        except Exception:
            raise ValueError("Failed to decode cartridge header metadata.")

    @staticmethod
    def _decode_text(rom: bytearray, start: int, end: int, encoding: str = "utf-8") -> str:
        """Decode a null-padded text span from header bytes."""
        return rom[start:end].strip(b"\x00").decode(encoding, errors="replace")

    def load(self) -> bytearray | None:
        """Load ROM file into memory and verify checksum."""
        try:
            with Path(self.filename).open("rb") as f:
                return bytearray(f.read())
        except Exception:
            return None

    def initialize_mapping(self, memory: list[int]) -> None:
        """Apply mapper state to MMU windows when a ROM is present."""
        if self.mapper is None or self.rom is None:
            return
        self.mapper.initialize(memory)

    def handle_mapper_write(self, address: int, value: int, memory: list[int]) -> bool:
        """Handle MBC control writes for 0000-7FFF when cartridge ROM exists."""
        if self.mapper is None or self.rom is None:
            return False
        self.mapper.handle_write(address, value, memory)
        return True

    def load_bank(self, value: int, memory: list[int]) -> None:
        """Force a mapper bank selection when cartridge ROM exists."""
        if self.mapper is None or self.rom is None:
            return
        self.mapper.load_bank(value, memory)

    def _verify_checksum(self, rom: bytearray) -> bool:
        """Calculate and verify the ROM checksum."""
        header_checksum = rom[H_HEADER_CHECKSUM]

        # calculate ROM checksum
        checksum = 0
        for address in range(H_TITLE_START, H_HEADER_CHECKSUM):
            checksum = checksum - rom[address] - 1

        # compare header checksum with lower 8 bits of calculated checksum
        return header_checksum == (checksum & 0xFF)

    def read(self, address: int = 0x0) -> int:
        """Read a byte from the cartridge at the specified address."""
        if self.rom is None:
            return 0xFF
        if not (0 <= address < len(self.rom)):
            return 0xFF

        return self.rom[address]

    def write(self, address: int = 0x0, value: int = 0) -> None:
        """Write a byte to the cartridge at the specified address."""
        if self.rom is None:
            return
        if not (0 <= address < len(self.rom)):
            return

        self.rom[address] = value & 0xFF

    def __str__(self) -> str:
        """Render formatted cartridge metadata for logs/debug output."""
        return (
            "Cartridge Info:\n"
            f"Filename: {self.filename}\n"
            f"Title: {self.title}\n"
            f"Manufacturer Code: {self.manufacturer_code}\n"
            f"Licensee: {self.licensee}\n"
            f"CGB Flag: {self.cgb_flag}\n"
            f"ROM Size: {self.rom_size} KB\n"
            f"Banks: {self.banks}\n"
            f"Cart Type: {self.cart_type}\n"
            f"Version: {self.version}\n"
            f"Destination Code: {self.destination}\n"
        )

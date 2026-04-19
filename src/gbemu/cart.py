from pathlib import Path

from loguru import logger

from gbemu.config import (
    CART_TYPE,
    CGB_FLAG,
    DEFAULT_ROM,
    DESTINATION_CODE,
    H_CART_TYPE,
    H_CGB_FLAG,
    H_DESTINATION,
    H_HEADER_CHECKSUM,
    H_MANUFACTURER_END,
    H_MANUFACTURER_START,
    H_NEW_LICENSEE_END,
    H_NEW_LICENSEE_START,
    H_OLD_LICENSEE,
    H_RAM_SIZE,
    H_ROM_SIZE,
    H_SGB_FLAG,
    H_TITLE_END,
    H_TITLE_START,
    H_VERSION,
    MMU_SIZE,
    NEW_LICENSEE,
    OLD_LICENSEE,
)


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
        self.mmu_size = "Unknown"
        self.destination = "Unknown"
        self.version = 0
        self.licensee = "Unknown"

        if self.rom is None:
            return

        self._decode_header(self.rom)

    def _decode_header(self, rom: bytearray) -> None:
        try:
            self.manufacturer_code = (
                rom[H_MANUFACTURER_START:H_MANUFACTURER_END]
                .strip(
                    b"\x00",
                )
                .decode(errors="replace")
            )
            self.title = (
                rom[H_TITLE_START:H_TITLE_END]
                .strip(b"\x00")
                .decode(
                    "ASCII",
                    errors="replace",
                )
            )
            self.cgb_flag = CGB_FLAG.get(f"{rom[H_CGB_FLAG] & 0xF0:02X}", "Unknown")
            self.sgb_flag = rom[H_SGB_FLAG]
            self.cart_type = CART_TYPE.get(rom[H_CART_TYPE], "Unknown")
            self.rom_size = 32 * (1 << rom[H_ROM_SIZE])
            self.mmu_size = MMU_SIZE.get(rom[H_RAM_SIZE], "Unknown")
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
        except Exception as e:
            logger.exception(f"Error decoding cartridge header: {self.filename} - {e}")

    def load(self) -> bytearray | None:
        """Load ROM file into memory and verify checksum."""
        try:
            with Path(self.filename).open("rb") as f:
                rom = bytearray(f.read())
                if not self._verify_checksum(rom):
                    logger.error(f"ROM checksum failed for {self.filename}")
                return rom
        except Exception as e:
            logger.exception(f"Error loading ROM: {self.filename} - {e}")
            return None

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
            logger.error(f"Attempted to read from unloaded cart: {self.filename}")
            return 0xFF
        if not (0 <= address < len(self.rom)):
            logger.error(f"Attempted to read out of bounds. Address: {address}")
            return 0xFF

        return self.rom[address]

    def write(self, address: int = 0x0, value: int = 0) -> None:
        """Write a byte to the cartridge at the specified address."""
        if self.rom is None:
            logger.error(f"Attempted to write to unloaded cart: {self.filename}")
            return
        if not (0 <= address < len(self.rom)):
            logger.error(f"Attempted to write out of bounds. Address: {address}, Value: {value}")
            return

        self.rom[address] = value & 0xFF

    def __str__(self) -> str:
        return (
            "Cartridge Info:\n"
            f"Filename: {self.filename}\n"
            f"Title: {self.title}\n"
            f"Manufacturer Code: {self.manufacturer_code}\n"
            f"Licensee: {self.licensee}\n"
            f"CGB Flag: {self.cgb_flag}\n"
            f"ROM Size: {self.rom_size} KB\n"
            f"MMU Size: {self.mmu_size}\n"
            f"Cart Type: {self.cart_type}\n"
            f"Version: {self.version}\n"
            f"Destination Code: {self.destination}\n"
        )

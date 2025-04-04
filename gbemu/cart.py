from ._config import CART_TYPE, DEFAULT_ROM, NINTENDO_LOGO
from ._exceptions import CartError, RomError


class Cart:
    def __init__(self, filename: str = DEFAULT_ROM) -> None:
        self.filename = filename
        self.rom = bytearray()
        self.load()
        self.manufacturer_code = self.rom[0x13F:0x142].strip(b"\x00").decode()
        self.copyright_logo = self.rom[0x104:0x134]
        self.title = self.rom[0x134:0x143].strip(b"\x00").decode("ASCII")
        self.cgb_flag = self.rom[0x143]
        self.sgb_flag = self.rom[0x146]
        self.license_code = self.rom[0x144:0x146]
        self.cart_type = CART_TYPE[self.rom[0x147]]
        self.rom_size = 32 * (1 << self.rom[0x148])
        self.ram_size = self.rom[0x149]
        self.destination_code = self.rom[0x14A]
        self.old_license_code = self.rom[0x14B]
        self.version = self.rom[0x14C]

        # logo copyright check
        if self.copyright_logo != NINTENDO_LOGO:
            raise RomError(f"Invalid ROM copyright: {self.filename}")

    def load(self) -> None:
        """Load ROM file into memory and verify checksum."""
        try:
            with open(self.filename, "rb") as f:
                self.rom = bytearray(f.read())
                header_checksum = self.rom[0x14D]

                # calculate ROM checksum
                checksum = 0
                for address in range(0x134, 0x14D):
                    checksum = checksum - self.rom[address] - 1

                # compare header checksum with lower 8 bits of calculated checksum
                if header_checksum != (checksum & 0x00FF):
                    raise RomError(f"Header checksum mismatch for ROM: {self.filename}")
        except Exception as e:
            raise RomError(f"Error loading ROM: {self.filename} - {e}") from e

    def read(self, address: int = 0x0):
        """Read a byte from the cartridge at the specified address."""
        if address < 0 or address >= len(self.rom):
            raise CartError(f"Attempted to read out of bounds. Address: {address}")

        return self.rom[address]

    def write(self, address: int = 0x0, value: int = 0):
        """Write a byte to the cartridge at the specified address."""
        if address < 0 or address >= len(self.rom):
            raise CartError(f"Attempted to write out of bounds. Address: {address}, Value: {value}")

        self.rom[address] = value

    def __str__(self):
        return (
            "Cartridge Info:\n"
            f"Title: {self.title}\n"
            f"Manufacturer Code: {self.manufacturer_code}\n"
            f"License Code: {self.license_code}\n"
            f"ROM Size: {self.rom_size} KB\n"
            f"RAM Size: {self.ram_size} KB\n"
            f"Cart Type: {self.cart_type}\n"
            f"Version: {self.version}\n"
        )

from ._cart_tables import CART_TYPE, CGB_FLAG, DESINATION_CODE, NEW_LICENSEE, OLD_LICENSEE, RAM_SIZE
from ._config import DEFAULT_ROM
from ._exceptions import CartError, RomError


class Cart:
    def __init__(self, filename: str = DEFAULT_ROM) -> None:
        self.filename = filename
        self.rom = self.load()

        try:
            self.manufacturer_code = self.rom[0x13F:0x142].strip(b"\x00").decode()
            self.title = self.rom[0x134:0x143].strip(b"\x00").decode("ASCII")
            self.cgb_flag = CGB_FLAG.get(f"{self.rom[0x143] & 0xF0}", "Unknown")
            self.sgb_flag = self.rom[0x146]
            self.cart_type = CART_TYPE[self.rom[0x147]]
            self.rom_size = 32 * (1 << self.rom[0x148])
            self.ram_size = RAM_SIZE[self.rom[0x149]]
            self.destination = DESINATION_CODE[self.rom[0x14A]]
            self.version = self.rom[0x14C]
            self.licensee = (
                NEW_LICENSEE[f"{self.rom[0x144:0x146].decode()}"]
                if self.rom[0x14B] == "33"
                else OLD_LICENSEE[f"{self.rom[0x14B]}"]
            )
        except Exception as e:
            raise CartError(f"Error decoding cartridge header: {self.filename} - {e}") from e

    def load(self) -> bytearray:
        """Load ROM file into memory and verify checksum."""
        try:
            with open(self.filename, "rb") as f:
                rom = bytearray(f.read())
                header_checksum = rom[0x14D]

                # calculate ROM checksum
                checksum = 0
                for address in range(0x134, 0x14D):
                    checksum = checksum - rom[address] - 1

                # compare header checksum with lower 8 bits of calculated checksum
                if header_checksum != (checksum & 0xFF):
                    raise RomError(f"Header checksum mismatch for ROM: {self.filename}")
                return rom
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
            f"Filenamne: {self.filename}\n"
            f"Title: {self.title}\n"
            f"Manufacturer Code: {self.manufacturer_code}\n"
            f"Licensee: {self.licensee}\n"
            f"CGB Flag: {self.cgb_flag}\n"
            f"ROM Size: {self.rom_size} KB\n"
            f"RAM Size: {self.ram_size}\n"
            f"Cart Type: {self.cart_type}\n"
            f"Version: {self.version}\n"
            f"Desination Code: {self.destination}\n"
        )

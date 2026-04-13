from pathlib import Path

from loguru import logger

from gbemu.config import DEFAULT_ROM
from gbemu.exceptions import CartError, RomError


class Cart:
    """GB Cartridge."""

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
            self.mmu_size = MMU_SIZE[self.rom[0x149]]
            self.destination = DESINATION_CODE[self.rom[0x14A]]
            self.version = self.rom[0x14C]
            self.licensee = (
                NEW_LICENSEE[f"{self.rom[0x144:0x146].decode()}"]
                if self.rom[0x14B] == 33
                else OLD_LICENSEE[f"{self.rom[0x14B]}"]
            )
        except Exception as e:
            raise CartError(f"Error decoding cartridge header: {self.filename} - {e}") from e

    def load(self) -> bytearray:
        """Load ROM file into memory and verify checksum."""
        try:
            with Path(self.filename).open("rb") as f:
                rom = bytearray(f.read())
                if not self._verify_checksum(rom):
                    logger.error(f"ROM checksum failed for {self.filename}")
                return rom
        except Exception as e:
            raise RomError(f"Error loading ROM: {self.filename} - {e}") from e

    def _verify_checksum(self, rom: bytearray) -> bool:
        """Calculate and verify the ROM checksum."""
        header_checksum = rom[0x14D]

        # calculate ROM checksum
        checksum = 0
        for address in range(0x134, 0x14D):
            checksum = checksum - rom[address] - 1

        # compare header checksum with lower 8 bits of calculated checksum
        return header_checksum == (checksum & 0xFF)

    def read(self, address: int = 0x0) -> int:
        """Read a byte from the cartridge at the specified address."""
        if address < 0 or address >= len(self.rom):
            raise CartError(f"Attempted to read out of bounds. Address: {address}")

        return self.rom[address]

    def write(self, address: int = 0x0, value: int = 0) -> None:
        """Write a byte to the cartridge at the specified address."""
        if address < 0 or address >= len(self.rom):
            raise CartError(f"Attempted to write out of bounds. Address: {address}, Value: {value}")

        self.rom[address] = value

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
            f"Desination Code: {self.destination}\n"
        )


CART_TYPE: dict[int, str] = {
    0x00: "ROM ONLY",
    0x01: "MBC1",
    0x02: "MBC1+RAM",
    0x03: "MBC1+RAM+BATTERY",
    0x05: "MBC2",
    0x06: "MBC2+BATTERY",
    0x08: "ROM+RAM",
    0x09: "ROM+RAM+BATTERY",
    0x0B: "MMM01",
    0x0C: "MMM01+RAM",
    0x0D: "MMM01+RAM+BATTERY",
    0x0F: "MBC3+TIMER+BATTERY",
    0x10: "MBC3+TIMER+RAM+BATTERY",
    0x11: "MBC3",
    0x12: "MBC3+RAM",
    0x13: "MBC3+RAM+BATTERY",
    0x19: "MBC5",
    0x1A: "MBC5+RAM",
    0x1B: "MBC5+RAM+BATTERY",
    0x1C: "MBC5+RUMBLE",
    0x1D: "MBC5+RUMBLE+RAM",
    0x1E: "MBC5+RUMBLE+RAM+BATTERY",
    0x20: "MBC6",
    0x22: "MBC7+SENSOR+RUMBLE+RAM+BATTERY",
    0xFC: "POCKET CAMERA",
    0xFD: "BANDAI TAMA5",
    0xFE: "HuC3",
    0xFF: "HuC1+RAM+BATTERY",
}

CGB_FLAG: dict[str, str] = {
    "0": "GB",
    "80": "CGB",
    "C0": "CGB+DMG",
}

MMU_SIZE: dict[int, str] = {
    0x00: "None",
    0x01: "Unused",
    0x02: "8 KB",
    0x03: "32 KB",
    0x04: "128 KB",
    0x05: "64 KB",
}

DESINATION_CODE: dict[int, str] = {
    0x00: "Japan & Overseas",
    0x01: "Non-Japan",
}

NEW_LICENSEE: dict[str, str] = {
    "0": "None",
    "1": "Nintendo Research & Development 1",
    "8": "Capcom",
    "13": "EA (Electronic Arts)",
    "18": "Hudson Soft",
    "19": "B-AI",
    "20": "KSS",
    "22": "Planning Office WADA",
    "24": "PCM Complete",
    "25": "San-X",
    "28": "Kemco",
    "29": "SETA Corporation",
    "30": "Viacom",
    "31": "Nintendo",
    "32": "Bandai",
    "33": "Ocean Software/Acclaim Entertainment",
    "34": "Konami",
    "35": "HectorSoft",
    "37": "Taito",
    "38": "Hudson Soft",
    "39": "Banpresto",
    "41": "Ubi Soft",
    "42": "Atlus",
    "44": "Malibu Interactive",
    "46": "Angel",
    "47": "Bullet-Proof Software",
    "49": "Irem",
    "50": "Absolute",
    "51": "Acclaim Entertainment",
    "52": "Activision",
    "53": "Sammy USA Corporation",
    "54": "Konami",
    "55": "Hi Tech Expressions",
    "56": "LJN",
    "57": "Matchbox",
    "58": "Mattel",
    "59": "Milton Bradley Company",
    "60": "Titus Interactive",
    "61": "Virgin Games Ltd.",
    "64": "Lucasfilm Games",
    "67": "Ocean Software",
    "69": "EA (Electronic Arts)",
    "70": "Infogrames",
    "71": "Interplay Entertainment",
    "72": "Broderbund",
    "73": "Sculptured Software",
    "75": "The Sales Curve Limited",
    "78": "THQ",
    "79": "Accolade",
    "80": "Misawa Entertainment",
    "83": "lozc",
    "86": "Tokuma Shoten",
    "87": "Tsukuda Original",
    "91": "Chunsoft Co.",
    "92": "Video System",
    "93": "Ocean Software/Acclaim Entertainment",
    "95": "Varie",
    "96": "Yonezawa",
    "97": "Kaneko",
    "99": "Pack-In-Video",
    "9H": "Bottom Up",
    "A4": "Konami (Yu-Gi-Oh!)",
    "BL": "MTO",
    "DK": "Kodansha",
}

OLD_LICENSEE: dict[str, str] = {
    "0": "None",
    "1": "Nintendo",
    "8": "Capcom",
    "9": "HOT-B",
    "A": "Jaleco",
    "B": "Coconuts Japan",
    "C": "Elite Systems",
    "13": "EA (Electronic Arts)",
    "18": "Hudson Soft",
    "19": "ITC Entertainment",
    "1A": "Yanoman",
    "1D": "Japan Clary",
    "1F": "Virgin Games Ltd.",
    "24": "PCM Complete",
    "25": "San-X",
    "28": "Kemco",
    "29": "SETA Corporation",
    "30": "Infogrames",
    "31": "Nintendo",
    "32": "Bandai",
    "33": "NEW_LICENSEE",
    "34": "Konami",
    "35": "HectorSoft",
    "38": "Capcom",
    "39": "Banpresto",
    "3C": "Entertainment Interactive (stub)",
    "3E": "Gremlin",
    "41": "Ubi Soft",
    "42": "Atlus",
    "44": "Malibu Interactive",
    "46": "Angel",
    "47": "Spectrum HoloByte",
    "49": "Irem",
    "4A": "Virgin Games Ltd.",
    "4D": "Malibu Interactive",
    "4F": "U.S. Gold",
    "50": "Absolute",
    "51": "Acclaim Entertainment",
    "52": "Activision",
    "53": "Sammy USA Corporation",
    "54": "GameTek",
    "55": "Park Place",
    "56": "LJN",
    "57": "Matchbox",
    "59": "Milton Bradley Company",
    "5A": "Mindscape",
    "5B": "Romstar",
    "5C": "Naxat Soft",
    "5D": "Tradewest",
    "60": "Titus Interactive",
    "61": "Virgin Games Ltd.",
    "67": "Ocean Software",
    "69": "EA (Electronic Arts)",
    "6E": "Elite Systems",
    "6F": "Electro Brain",
    "70": "Infogrames",
    "71": "Interplay Entertainment",
    "72": "Broderbund",
    "73": "Sculptured Software",
    "75": "The Sales Curve Limited",
    "78": "THQ",
    "79": "Accolade",
    "7A": "Triffix Entertainment",
    "7C": "MicroProse",
    "7F": "Kemco",
    "80": "Misawa Entertainment",
    "83": "LOZC G.",
    "86": "Tokuma Shoten",
    "8B": "Bullet-Proof Software",
    "8C": "Vic Tokai Corp.",
    "8E": "Ape Inc.",
    "8F": "I'Max",
    "91": "Chunsoft Co.",
    "92": "Video System",
    "93": "Tsubaraya Productions",
    "95": "Varie",
    "96": "Yonezawa/S'Pal",
    "97": "Kemco",
    "99": "Arc",
    "9A": "Nihon Bussan",
    "9B": "Tecmo",
    "9C": "Imagineer",
    "9D": "Banpresto",
    "9F": "Nova",
    "A1": "Hori Electric",
    "A2": "Bandai",
    "A4": "Konami",
    "A6": "Kawada",
    "A7": "Takara",
    "A9": "Technos Japan",
    "AA": "Broderbund",
    "AC": "Toei Animation",
    "AD": "Toho",
    "AF": "Namco",
    "B0": "Acclaim Entertainment",
    "B1": "ASCII Corporation or Nexsoft",
    "B2": "Bandai",
    "B4": "Square Enix",
    "B6": "HAL Laboratory",
    "B7": "SNK",
    "B9": "Pony Canyon",
    "BA": "Culture Brain",
    "BB": "Sunsoft",
    "BD": "Sony Imagesoft",
    "BF": "Sammy Corporation",
    "C0": "Taito",
    "C2": "Kemco",
    "C3": "Square",
    "C4": "Tokuma Shoten",
    "C5": "Data East",
    "C6": "Tonkin House",
    "C8": "Koei",
    "C9": "UFL",
    "CA": "Ultra Games",
    "CB": "VAP, Inc.",
    "CC": "Use Corporation",
    "CD": "Meldac",
    "CE": "Pony Canyon",
    "CF": "Angel",
    "D0": "Taito",
    "D1": "SOFEL (Software Engineering Lab)",
    "D2": "Quest",
    "D3": "Sigma Enterprises",
    "D4": "ASK Kodansha Co.",
    "D6": "Naxat Soft",
    "D7": "Copya System",
    "D9": "Banpresto",
    "DA": "Tomy",
    "DB": "LJN",
    "DD": "Nippon Computer Systems",
    "DE": "Human Ent.",
    "DF": "Altron",
    "E0": "Jaleco",
    "E1": "Towa Chiki",
    "E2": "Yutaka",
    "E3": "Varie",
    "E5": "Epoch",
    "E7": "Athena",
    "E8": "Asmik Ace Entertainment",
    "E9": "Natsume",
    "EA": "King Records",
    "EB": "Atlus",
    "EC": "Epic/Sony Records",
    "EE": "IGS",
    "F0": "A Wave",
    "F3": "Extreme Entertainment",
    "FF": "LJN",
}

import pygame as pg

from gbemu.ctypes import Color

DEFAULT_ROM = "./roms/puzzle.gb"
MEMORY_SIZE: int = 65536  # 64kb of totally memory (ROM + RAM + IO)
SP_START: int = 0xFFFE  # stack pointer start location
DEBUG = False
HEADLESS = False

# fmt: off
BIOS: list[int] = [
    0x31, 0xFE, 0xFF, 0xAF, 0x21, 0xFF, 0x9F, 0x32, 0xCB, 0x7C, 0x20, 0xFB,
    0x21, 0x26, 0xFF, 0x0E, 0x11, 0x3E, 0x80, 0x32, 0xE2, 0x0C, 0x3E, 0xF3,
    0xE2, 0x32, 0x3E, 0x77, 0x77, 0x3E, 0xFC, 0xE0, 0x47, 0x11, 0x04, 0x01,
    0x21, 0x10, 0x80, 0x1A, 0xCD, 0x95, 0x00, 0xCD, 0x96, 0x00, 0x13, 0x7B,
    0xFE, 0x34, 0x20, 0xF3, 0x11, 0xD8, 0x00, 0x06, 0x08, 0x1A, 0x13, 0x22,
    0x23, 0x05, 0x20, 0xF9, 0x3E, 0x19, 0xEA, 0x10, 0x99, 0x21, 0x2F, 0x99,
    0x0E, 0x0C, 0x3D, 0x28, 0x08, 0x32, 0x0D, 0x20, 0xF9, 0x2E, 0x0F, 0x18,
    0xF3, 0x67, 0x3E, 0x64, 0x57, 0xE0, 0x42, 0x3E, 0x91, 0xE0, 0x40, 0x04,
    0x1E, 0x02, 0x0E, 0x0C, 0xF0, 0x44, 0xFE, 0x90, 0x20, 0xFA, 0x0D, 0x20,
    0xF7, 0x1D, 0x20, 0xF2, 0x0E, 0x13, 0x24, 0x7C, 0x1E, 0x83, 0xFE, 0x62,
    0x28, 0x06, 0x1E, 0xC1, 0xFE, 0x64, 0x20, 0x06, 0x7B, 0xE2, 0x0C, 0x3E,
    0x87, 0xF2, 0xF0, 0x42, 0x90, 0xE0, 0x42, 0x15, 0x20, 0xD2, 0x05, 0x20,
    0x4F, 0x16, 0x20, 0x18, 0xCB, 0x4F, 0x06, 0x04, 0xC5, 0xCB, 0x11, 0x17,
    0xC1, 0xCB, 0x11, 0x17, 0x05, 0x20, 0xF5, 0x22, 0x23, 0x22, 0x23, 0xC9,
    0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B, 0x03, 0x73, 0x00, 0x83,
    0x00, 0x0C, 0x00, 0x0D, 0x00, 0x08, 0x11, 0x1F, 0x88, 0x89, 0x00, 0x0E,
    0xDC, 0xCC, 0x6E, 0xE6, 0xDD, 0xDD, 0xD9, 0x99, 0xBB, 0xBB, 0x67, 0x63,
    0x6E, 0x0E, 0xEC, 0xCC, 0xDD, 0xDC, 0x99, 0x9F, 0xBB, 0xB9, 0x33, 0x3E,
    0x3C, 0x42, 0xB9, 0xA5, 0xB9, 0xA5, 0x42, 0x4C, 0x21, 0x04, 0x01, 0x11,
    0xA8, 0x00, 0x1A, 0x13, 0xBE, 0x20, 0xFE, 0x23, 0x7D, 0xFE, 0x34, 0x20,
    0xF5, 0x06, 0x19, 0x78, 0x86, 0x23, 0x05, 0x20, 0xFB, 0x86, 0x20, 0xFE,
    0x3E, 0x01, 0xE0, 0x50,
]
# fmt: on

# screen/ppu config
DISPLAY_SCALER: int = 5
SCREEN_WIDTH: int = 160
SCREEN_HEIGHT: int = 144

BG_COLOR: Color = (202, 220, 159)
ERROR_COLOR: Color = (219, 18, 18)
PALLETE: list[Color] = [
    (155, 188, 15),
    (139, 172, 15),
    (48, 98, 48),
    (15, 56, 15),
]
TILE_WIDTH: int = 8
TILE_BITS: int = 16
SCAN_LINES: int = 154
CYCLES_PER_SCANLINE: int = 456
# Total t-cycles for one full frame: 154 scanlines x 456 dots each.
CYCLES_PER_FRAME: int = SCAN_LINES * CYCLES_PER_SCANLINE  # 70224
CPU_CLOCK_HZ: int = 4_194_304
TARGET_FPS: float = CPU_CLOCK_HZ / CYCLES_PER_FRAME  # ~59.73 fps
SHOW_FPS_OVERLAY: bool = True
FPS_OVERLAY_MARGIN: int = 6
FPS_OVERLAY_COLOR: Color = (15, 56, 15)

# Hardware Registers
M_JOYPAD: int = 0xFF00
M_SERIAL_DATA: int = 0xFF01
M_SERIAL_CONTROL: int = 0xFF02
M_DIVIDER: int = 0xFF04
M_TIMER_COUNTER: int = 0xFF05
M_TIMER_MODULO: int = 0xFF06
M_TIMER_CONTROL: int = 0xFF07
M_INTERRUPT_FLAG: int = 0xFF0F
M_INFRARED_PORT: int = 0xFF56

# Audio registers
M_SND_CH1_SWEEP: int = 0xFF10
M_SND_CH1_LENGTH_DUTY: int = 0xFF11
M_SND_CH1_VOLUME_ENVELOPE: int = 0xFF12
M_SND_CH1_PERIOD_LOW: int = 0xFF13
M_SND_CH1_PERIOD_HIGH_CONTROL: int = 0xFF14
M_SND_CH2_LENGTH_DUTY: int = 0xFF16
M_SND_CH2_VOLUME_ENVELOPE: int = 0xFF17
M_SND_CH2_PERIOD_LOW: int = 0xFF18
M_SND_CH2_PERIOD_HIGH_CONTROL: int = 0xFF19
M_SND_CH3_DAC_ENABLE: int = 0xFF1A
M_SND_CH3_LENGTH_TIMER: int = 0xFF1B
M_SND_CH3_OUTPUT_LEVEL: int = 0xFF1C
M_SND_CH3_PERIOD_LOW: int = 0xFF1D
M_SND_CH3_PERIOD_HIGH_CONTROL: int = 0xFF1E
M_SND_CH4_LENGTH_TIMER: int = 0xFF20
M_SND_CH4_VOLUME_ENVELOPE: int = 0xFF21
M_SND_CH4_FREQUENCY_RANDOMNESS: int = 0xFF22
M_SND_CH4_CONTROL: int = 0xFF23
M_MASTER_VOLUME_VIN_PANNING: int = 0xFF24
M_SND_PANNING: int = 0xFF25
M_SND_ON_OFF: int = 0xFF26
M_WAVE_RAM_START: int = 0xFF30
M_WAVE_RAM_END: int = 0xFF3F
M_AUDIO_DIGITAL_OUTPUTS_1_2: int = 0xFF76
M_AUDIO_DIGITAL_OUTPUTS_3_4: int = 0xFF77

# LCD registers
M_LCD_CONTROL: int = 0xFF40
M_LCD_STATUS: int = 0xFF41
M_VIEWPORT_Y: int = 0xFF42
M_VIEWPORT_X: int = 0xFF43
M_LCD_Y_COORDINATE: int = 0xFF44
M_LY_COMPARE: int = 0xFF45
M_OAM_DMA_SOURCE_START: int = 0xFF46
M_BG_PALETTE_DATA: int = 0xFF47
M_OBJ_PALETTE_0_DATA: int = 0xFF48
M_OBJ_PALETTE_1_DATA: int = 0xFF49
M_WINDOW_Y: int = 0xFF4A
M_WINDOW_X_PLUS_7: int = 0xFF4B
M_CPU_MODE_SELECT: int = 0xFF4C
M_PREPARE_SPEED_SWITCH: int = 0xFF4D
M_VRAM_BANK: int = 0xFF4F
M_BOOT_ROM_MAPPING_CONTROL: int = 0xFF50

# Video registers
M_VRAM_START: int = 0x8000
M_VRAM_END: int = 0x9FFF
M_OAM_START: int = 0xFE00
M_OAM_END: int = 0xFE9F
M_WIN_MAP_VRAM: list[list[int]] = [[0x9800, 0x9BFF], [0x9C00, 0x9FFF]]
M_BG_TILE_MAP_VRAM: list[list[int]] = [[0x9800, 0x9BFF], [0x9C00, 0x9FFF]]
M_VRAM_DMA_SOURCE_HIGH: int = 0xFF51
M_VRAM_DMA_SOURCE_LOW: int = 0xFF52
M_VRAM_DMA_DESTINATION_HIGH: int = 0xFF53
M_VRAM_DMA_DESTINATION_LOW: int = 0xFF54
M_VRAM_DMA_LENGTH_MODE_START: int = 0xFF55

# CGB registers
M_BG_COLOR_PALETTE_SPECIFICATION: int = 0xFF68
M_BG_COLOR_PALETTE_DATA: int = 0xFF69
M_OBJ_COLOR_PALETTE_SPECIFICATION: int = 0xFF6A
M_OBJ_COLOR_PALETTE_DATA: int = 0xFF6B
M_OBJECT_PRIORITY_MODE: int = 0xFF6C
M_WRAM_BANK: int = 0xFF70

# Interrupt registers
M_INTERRUPT_ENABLE: int = 0xFFFF

# MMU memory map ranges
MMU_ROM_START = 0x0000
MMU_ROM_END = 0x7FFF
MMU_WRAM_START = 0xC000
MMU_WRAM_END = 0xDDFF
MMU_ECHO_START = 0xE000
MMU_ECHO_END = 0xFDFF
MMU_UNUSABLE_START = 0xFEA0
MMU_UNUSABLE_END = 0xFEFF

# PPU mode timing windows (in CPU cycles)
PPU_MODE2_CYCLES = 80
PPU_MODE3_CYCLES = 172
PPU_MODE0_CYCLES = CYCLES_PER_SCANLINE - PPU_MODE2_CYCLES - PPU_MODE3_CYCLES

# Timer periods by TAC clock-select bits
TIMER_PERIODS: dict[int, int] = {
    0x00: 1024,  # 4096 Hz
    0x01: 16,  # 262144 Hz
    0x02: 64,  # 65536 Hz
    0x03: 256,  # 16384 Hz
}

# Opcodes documented as invalid on LR35902 (no defined instruction semantics)
CPU_INVALID_UNPREFIXED_OPCODES = {
    0xD3,
    0xDB,
    0xDD,
    0xE3,
    0xE4,
    0xEB,
    0xEC,
    0xED,
    0xF4,
    0xFC,
    0xFD,
}

# Keyboard mapping to joypad bit mask and line-select (dpad=True, buttons=False)
KEYMAP: dict[int, tuple[int, bool]] = {
    pg.K_UP: (0b0100, True),
    pg.K_w: (0b0100, True),
    pg.K_DOWN: (0b1000, True),
    pg.K_s: (0b1000, True),
    pg.K_LEFT: (0b0010, True),
    pg.K_RIGHT: (0b0001, True),
    pg.K_d: (0b0001, True),
    pg.K_a: (0b0001, False),
    pg.K_j: (0b0001, False),
    pg.K_b: (0b0010, False),
    pg.K_k: (0b0010, False),
    pg.K_RETURN: (0b1000, False),
    pg.K_LSHIFT: (0b0100, False),
    pg.K_RSHIFT: (0b0100, False),
}

# Cartridge header offsets
H_MANUFACTURER_START = 0x13F
H_MANUFACTURER_END = 0x142
H_TITLE_START = 0x134
H_TITLE_END = 0x143
H_CGB_FLAG = 0x143
H_NEW_LICENSEE_START = 0x144
H_NEW_LICENSEE_END = 0x146
H_SGB_FLAG = 0x146
H_CART_TYPE = 0x147
H_ROM_SIZE = 0x148
H_RAM_SIZE = 0x149
H_DESTINATION = 0x14A
H_OLD_LICENSEE = 0x14B
H_VERSION = 0x14C
H_HEADER_CHECKSUM = 0x14D

# Cartridge metadata mappings
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
    "00": "GB",
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

DESTINATION_CODE: dict[int, str] = {
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

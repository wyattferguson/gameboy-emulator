from dataclasses import dataclass, field
from enum import IntEnum, StrEnum

Color = tuple[int, int, int]
ColorExt = tuple[int, int, int, int]


class RegisterDict(dict):
    """Handle 8bit or 16bit registers seamlessly."""

    def __getitem__(self, key: str) -> int:
        if len(key) == 1 or key == "SP":
            return super().__getitem__(key)

        return self._get_register_pair(key)

    def __setitem__(self, key: str, value: int) -> None:
        if len(key) == 1:
            super().__setitem__(key, value & 0xFF)
            return

        if key == "SP":
            super().__setitem__("SP", value & 0xFFFF)
            return

        self._set_register_pair(key, value)

    def _get_register_pair(self, pair: str) -> int:
        """Combine two 8-bit register entries into a single 16-bit value."""
        high: int = super().__getitem__(pair[0])
        low: int = super().__getitem__(pair[1])
        return (high << 8) | low

    def _set_register_pair(self, pair: str, value: int) -> None:
        """Split a 16-bit value into high/low 8-bit register entries."""
        super().__setitem__(pair[0], (value >> 8) & 0xFF)
        super().__setitem__(pair[1], value & 0xFF)


class Bitwise(StrEnum):
    """Bitwise operations."""

    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    NOT = "NOT"


@dataclass(frozen=True)
class OpCode:
    """GB CPU instruction."""

    label: str  # mnemonic name
    length: int  # length of instruction in bytes
    cycles: int  # number of cpu cycles
    call: str | None = None  # CPU method name to call
    args: list[str | bool | int | Bitwise] = field(
        default_factory=list,
    )  # args to send to CPU method
    flags: dict[str, int] | None = None  # set CPU flags after execution
    pc_inc: bool = True  # whether to increment PC after execution

    def __str__(self) -> str:
        return f"{self.label} {self.length} - {self.args} - {self.flags}"


class TileSize(IntEnum):
    """Tile sizes."""

    SMALL = 8  # 8x8 pixels
    LARGE = 16  # 8x16 pixels


@dataclass()
class Tile:
    """GB tile + attributes."""

    index: int
    data: list[int]
    height: TileSize = TileSize.SMALL
    x: int = 0
    y: int = 0
    x_flipped: bool = False
    y_flipped: bool = False
    bank: int = 0
    dmg_palette: int = 0
    cgb_palette: int = 0
    priority: bool = False

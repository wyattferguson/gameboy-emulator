from dataclasses import dataclass
from enum import IntEnum, StrEnum

type Color = tuple[int, int, int]


class CallableDict(dict):
    """Run callable values when accessed."""

    def __getitem__(self, key: str) -> int:
        val = super().__getitem__(key)
        if callable(val):
            return val()
        return val

    def __setitem__(self, key: str, value: int) -> None:
        existing_value = super().get(key)
        if callable(existing_value):
            self._set_register_pair(key, value)
        elif key == "SP":
            super().__setitem__("SP", value & 0xFFFF)
        else:
            super().__setitem__(key, value & 0xFF)

    def _set_register_pair(self, pair: str, value: int) -> None:
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
    cycles: int  # number of cpu cyles
    call: str | None = None  # CPU method name to call
    args: list[str | bool | int | Bitwise] | None = None  # give arguments to send to CPU method
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

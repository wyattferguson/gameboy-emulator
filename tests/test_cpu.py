import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.opcodes import OPCODES
from gbemu.utils import hex_to_signed


@pytest.mark.parametrize(
    ("value", "bits", "expected"),
    [
        (0x00, 8, 0),
        (0x7F, 8, 127),
        (0x80, 8, -128),
        (0xFF, 8, -1),
        (0x8000, 16, -32768),
        (0xFFFF, 16, -1),
    ],
)
def test_hex_to_signed(value: int, bits: int, expected: int) -> None:
    assert hex_to_signed(value, bits) == expected

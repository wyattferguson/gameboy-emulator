from gbemu.cart import Cart
from gbemu.constants import BIOS


def test_cart_loads_known_rom() -> None:
    cart = Cart("roms/hello.gb")

    assert len(cart.rom) > 0x150


def test_cart_header_logo_matches_bios_logo() -> None:
    cart = Cart("roms/hello.gb")

    assert list(cart.rom[0x0104:0x0134]) == BIOS[0x00A8 : 0x00A8 + 48]


def test_cart_checksum_verification_passes_for_known_rom() -> None:
    cart = Cart("roms/hello.gb")

    assert cart._verify_checksum(cart.rom) is True


def test_cart_read_and_write_roundtrip() -> None:
    cart = Cart("roms/hello.gb")
    original = cart.read(0x100)

    cart.write(0x100, 0x42)

    assert cart.read(0x100) == 0x42

    # Restore original byte so the in-memory image remains unchanged for this test process.
    cart.write(0x100, original)

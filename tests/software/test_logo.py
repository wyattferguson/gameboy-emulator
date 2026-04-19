from gbemu.cart import Cart
from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.ppu import PPU


def _render_logo_signature() -> list[str]:
    """Render the BIOS logo region and return a compact textual signature."""
    mmu = MMU(Cart("roms/hello.gb"))
    cpu = CPU(mmu)
    ppu = PPU(mmu, headless=True)

    for _ in range(120000):
        cycles = cpu.cycle()
        ppu.update(cycles)
        if cpu.pc == 0x64:
            break

    mmu[0xFF42] = 64
    ppu.refresh_lcd_control()

    signature: list[str] = []
    for scan_line in range(8, 16):
        ppu.scan_line = scan_line
        line = ppu.render_bg_window_line()[24:104]
        signature.append("".join("." if pixel == 0 else str(pixel) for pixel in line))

    return signature


def test_logo_signature_is_stable() -> None:
    """Nintendo logo rendering should keep this stable known-good signature."""
    expected = [
        "........3333..33..3333..3333..333333..3333..3333..3333....3333..333333..3333..33",
        "........3333..33..3333..3333..333333..3333..3333..3333....3333..333333..3333..33",
        "........3333....333333..3333..3333....3333..3333..333333333333..3333....3333..33",
        "........3333....333333..3333..3333....3333..3333..333333333333..3333....3333..33",
        "........3333....333333..3333..3333....3333..3333..3333..........3333....3333..33",
        "........3333....333333..3333..3333....3333..3333..3333..........3333....3333..33",
        "........3333......3333..3333..3333....3333..3333....3333333333..3333....3333....",
        "........3333......3333..3333..3333....3333..3333....3333333333..3333....3333....",
    ]

    assert _render_logo_signature() == expected


def test_logo_signature_has_foreground_and_background() -> None:
    """Logo region should contain both background and non-background palette IDs."""
    signature = _render_logo_signature()

    assert all("." in line for line in signature)
    assert all("3" in line for line in signature)

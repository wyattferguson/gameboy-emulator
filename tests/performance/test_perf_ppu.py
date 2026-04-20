import os
from time import perf_counter

import pytest

from gbemu.config import M_LCD_CONTROL
from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.ppu import PPU

RUN_PERF_TESTS = os.getenv("GBEMU_RUN_PERF_TESTS") == "1"

pytestmark = [
    pytest.mark.performance,
    pytest.mark.skipif(
        not RUN_PERF_TESTS,
        reason="Set GBEMU_RUN_PERF_TESTS=1 to run performance tests.",
    ),
]

_THRESHOLD_SECONDS = 5.0

# LCDC = 0x91: LCD on, BG on, tile data at 0x8000, BG map at 0x9800.
_LCDC_ON = 0x91


def _make_ppu() -> tuple[MMU, PPU]:
    """Set up a headless PPU with deterministic tile and map data."""
    mmu = MMU()
    mmu.memory[M_LCD_CONTROL] = _LCDC_ON
    # Fill BG map with tile index 0.
    mmu.memory[0x9800 : 0x9800 + 32 * 32] = [0] * (32 * 32)
    # Solid tile — all pixels set to color ID 3.
    mmu.memory[0x8000 : 0x8000 + 16] = [0xFF, 0xFF] * 8
    ppu = PPU(mmu, headless=True)
    ppu.refresh_lcd_control(mmu.memory[M_LCD_CONTROL])
    return mmu, ppu


def _print_metrics(label: str, iterations: int, elapsed: float) -> None:
    """Print human-readable throughput metrics to stdout."""
    ops_per_sec = iterations / elapsed
    us_per_op = (elapsed / iterations) * 1_000_000
    print(
        f"\n[PPU] {label}\n"
        f"  iterations : {iterations:>10,}\n"
        f"  total time : {elapsed:>10.4f} s\n"
        f"  throughput : {ops_per_sec:>10,.0f} ops/s\n"
        f"  per op     : {us_per_op:>10.3f} µs",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_ppu_bg_scanline_render() -> None:
    """Measure background scanline render throughput with solid tiles."""
    _, ppu = _make_ppu()
    iterations = 1_000

    t0 = perf_counter()
    for i in range(iterations):
        ppu.scan_line = i % 144
        ppu.render_bg_window_line_with_ids()
    elapsed = perf_counter() - t0

    _print_metrics("BG scanline render (1 000 lines)", iterations, elapsed)
    assert elapsed < _THRESHOLD_SECONDS


def test_ppu_oam_scan() -> None:
    """Measure OAM sprite scan speed with 40 sprites in OAM."""
    mmu, ppu = _make_ppu()

    # Fill all 40 OAM slots with Y=16 (on-screen for scanline 0), X=8, tile 0, attrs 0.
    oam_base = 0xFE00
    for i in range(40):
        base = oam_base + i * 4
        mmu.memory[base] = 16  # Y (on screen at scan_line=0)
        mmu.memory[base + 1] = 8  # X
        mmu.memory[base + 2] = 0  # tile index
        mmu.memory[base + 3] = 0  # attributes

    iterations = 5_000
    t0 = perf_counter()
    for _ in range(iterations):
        ppu.scan_line = 0
        ppu.scan_oam_for_scanline()
    elapsed = perf_counter() - t0

    _print_metrics("OAM scan 40 sprites (5 000 scans)", iterations, elapsed)
    assert elapsed < _THRESHOLD_SECONDS


def test_ppu_full_frame_update() -> None:
    """Measure full-frame PPU update driven by CPU cycle ticks."""
    mmu = MMU()
    cpu = CPU(mmu)
    ppu = PPU(mmu, headless=True)
    mmu.memory[M_LCD_CONTROL] = _LCDC_ON
    mmu.memory[0x9800 : 0x9800 + 32 * 32] = [0] * (32 * 32)
    mmu.memory[0x8000 : 0x8000 + 16] = [0xFF, 0xFF] * 8
    ppu.refresh_lcd_control(mmu.memory[M_LCD_CONTROL])

    # Run a NOP stream so the CPU produces valid cycles.
    start = 0xC000
    count = 10_000
    mmu.memory[start : start + count] = [0x00] * count
    cpu.pc = start

    frames_before = ppu.frame
    t0 = perf_counter()
    for _ in range(count):
        cycles = cpu.cycle()
        ppu.update(cycles)
    elapsed = perf_counter() - t0

    frames_rendered = ppu.frame - frames_before
    fps = frames_rendered / elapsed if elapsed > 0 else 0
    print(
        f"\n[PPU] Full frame update (10 000 CPU steps)\n"
        f"  frames rendered : {frames_rendered:>10,}\n"
        f"  total time      : {elapsed:>10.4f} s\n"
        f"  effective FPS   : {fps:>10.1f}",
    )
    assert elapsed < _THRESHOLD_SECONDS


def test_ppu_sprite_overlay() -> None:
    """Measure sprite overlay cost when 10 sprites are visible on a scanline."""
    mmu, ppu = _make_ppu()

    # Place 10 sprites on scan_line 0.
    oam_base = 0xFE00
    for i in range(10):
        base = oam_base + i * 4
        mmu.memory[base] = 16
        mmu.memory[base + 1] = 8 + i * 8
        mmu.memory[base + 2] = 0
        mmu.memory[base + 3] = 0

    iterations = 2_000
    t0 = perf_counter()
    for _ in range(iterations):
        ppu.scan_line = 0
        ppu.scan_oam_for_scanline()
        bg_line, bg_ids = ppu.render_bg_window_line_with_ids()
        ppu.render_object_line(bg_line, bg_ids)
    elapsed = perf_counter() - t0

    _print_metrics("Sprite overlay 10 sprites/line (2 000 lines)", iterations, elapsed)
    assert elapsed < _THRESHOLD_SECONDS

import os
from time import perf_counter

import pytest

from gbemu.config import M_LCD_CONTROL
from gbemu.cpu import CPU
from gbemu.mmu import MMU
from gbemu.ppu import PPU
from gbemu.timer import Timer

RUN_PERF_TESTS = os.getenv("GBEMU_RUN_PERF_TESTS") == "1"

pytestmark = [
    pytest.mark.performance,
    pytest.mark.skipif(
        not RUN_PERF_TESTS,
        reason="Set GBEMU_RUN_PERF_TESTS=1 to run performance tests.",
    ),
]


def test_cpu_cycle_throughput_nop_stream() -> None:
    mmu = MMU()
    cpu = CPU(mmu)
    start = 0xC000
    count = 4_000

    mmu.memory[start : start + count] = [0x00] * count
    cpu.pc = start

    t0 = perf_counter()
    for _ in range(count):
        cpu.cycle()
    elapsed = perf_counter() - t0

    assert cpu.pc == (start + count) & 0xFFFF
    # Loose guardrail to catch severe regressions only.
    assert elapsed < 6.0


def test_mmu_read_write_hotpath() -> None:
    mmu = MMU()
    iterations = 300_000
    base = 0xC000

    t0 = perf_counter()
    for i in range(iterations):
        address = base + (i & 0x7FF)
        mmu[address] = i & 0xFF
        _ = mmu[address]
    elapsed = perf_counter() - t0

    assert elapsed < 5.0


def test_ppu_scanline_render_hotpath() -> None:
    mmu = MMU()
    ppu = PPU(mmu, headless=True)

    # LCD on, BG on, tile data at 0x8000, BG map 0x9800.
    mmu.memory[M_LCD_CONTROL] = 0x91
    ppu.refresh_lcd_control(mmu.memory[M_LCD_CONTROL])

    # Deterministic tile/map data to keep rendering path active.
    mmu.memory[0x9800 : 0x9800 + 32 * 32] = [0] * (32 * 32)
    mmu.memory[0x8000 : 0x8000 + 16] = [0xFF, 0x00] * 8

    iterations = 1_000
    t0 = perf_counter()
    for i in range(iterations):
        ppu.scan_line = i % 144
        ppu.render_bg_window_line_with_ids()
    elapsed = perf_counter() - t0

    assert elapsed < 5.0


def test_timer_tick_hotpath() -> None:
    mmu = MMU()
    timer = Timer()

    # Enable timer; clock select=01 (fast period) for active loop behavior.
    mmu.memory[0xFF07] = 0x05

    iterations = 200_000
    t0 = perf_counter()
    for _ in range(iterations):
        timer.tick(mmu.memory, 4)
    elapsed = perf_counter() - t0

    assert elapsed < 4.0

import os
from time import perf_counter

import pytest

from gbemu.config import SCREEN_HEIGHT, SCREEN_WIDTH
from gbemu.screen import Screen

RUN_PERF_TESTS = os.getenv("GBEMU_RUN_PERF_TESTS") == "1"

pytestmark = [
    pytest.mark.performance,
    pytest.mark.skipif(
        not RUN_PERF_TESTS,
        reason="Set GBEMU_RUN_PERF_TESTS=1 to run performance tests.",
    ),
]

_THRESHOLD_SECONDS = 5.0


def _make_screen() -> Screen:
    """Create a Screen instance without a visible window (scaler=1)."""
    return Screen(scaler=1, show_fps_overlay=False)


def _print_metrics(label: str, iterations: int, elapsed: float) -> None:
    """Print human-readable throughput metrics to stdout."""
    ops_per_sec = iterations / elapsed
    us_per_op = (elapsed / iterations) * 1_000_000
    print(
        f"\n[Screen] {label}\n"
        f"  iterations : {iterations:>10,}\n"
        f"  total time : {elapsed:>10.4f} s\n"
        f"  throughput : {ops_per_sec:>10,.0f} ops/s\n"
        f"  per op     : {us_per_op:>10.3f} µs",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_screen_draw_scanline_solid() -> None:
    """Measure throughput when writing a full solid-color scanline."""
    screen = _make_screen()
    line = [3] * SCREEN_WIDTH  # all pixels → palette slot 3 (darkest)
    iterations = 10_000

    t0 = perf_counter()
    for i in range(iterations):
        screen.draw_scanline(line, i % SCREEN_HEIGHT)
    elapsed = perf_counter() - t0

    _print_metrics(
        f"draw_scanline solid ({SCREEN_WIDTH}px × {iterations:,} lines)",
        iterations,
        elapsed,
    )
    assert elapsed < _THRESHOLD_SECONDS


def test_screen_draw_scanline_varied() -> None:
    """Measure throughput when writing scanlines with varying palette IDs."""
    screen = _make_screen()
    line = [i % 4 for i in range(SCREEN_WIDTH)]
    iterations = 10_000

    t0 = perf_counter()
    for i in range(iterations):
        screen.draw_scanline(line, i % SCREEN_HEIGHT)
    elapsed = perf_counter() - t0

    _print_metrics(
        f"draw_scanline varied ({SCREEN_WIDTH}px × {iterations:,} lines)",
        iterations,
        elapsed,
    )
    assert elapsed < _THRESHOLD_SECONDS


def test_screen_full_frame_buffer_write() -> None:
    """Measure throughput for writing a complete 160×144 frame."""
    screen = _make_screen()
    frame = [[i % 4 for i in range(SCREEN_WIDTH)] for _ in range(SCREEN_HEIGHT)]
    iterations = 500

    t0 = perf_counter()
    for _ in range(iterations):
        screen.draw_buffer(frame)
    elapsed = perf_counter() - t0

    pixels_per_frame = SCREEN_WIDTH * SCREEN_HEIGHT
    total_pixels = pixels_per_frame * iterations
    mpps = (total_pixels / elapsed) / 1_000_000
    print(
        f"\n[Screen] Full frame write ({SCREEN_WIDTH}×{SCREEN_HEIGHT} × {iterations} frames)\n"
        f"  total frames : {iterations:>10,}\n"
        f"  total time   : {elapsed:>10.4f} s\n"
        f"  throughput   : {mpps:>10.2f} Mpx/s\n"
        f"  per frame    : {(elapsed / iterations) * 1000:>10.3f} ms",
    )
    assert elapsed < _THRESHOLD_SECONDS


def test_screen_pixel_rgb_write_hotpath() -> None:
    """Measure throughput for direct RGB pixel writes via draw_pixel."""
    screen = _make_screen()
    iterations = 100_000
    colors = screen.palette  # list of Color tuples, length 4

    t0 = perf_counter()
    for i in range(iterations):
        x = i % SCREEN_WIDTH
        y = (i // SCREEN_WIDTH) % SCREEN_HEIGHT
        screen.draw_pixel(x, y, colors[i % 4])
    elapsed = perf_counter() - t0

    _print_metrics(f"draw_pixel RGB ({iterations:,} pixels)", iterations, elapsed)
    assert elapsed < _THRESHOLD_SECONDS

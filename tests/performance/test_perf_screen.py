import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from time import perf_counter

import pytest

from gbemu.config import SCREEN_HEIGHT, SCREEN_WIDTH
from gbemu.screen import Screen

from .perfconfig import BUFFER_ITERATIONS, SCANLINE_ITERATIONS

pytestmark = [pytest.mark.performance]


@pytest.fixture(scope="module")
def screen() -> Screen:
    """Shared Screen instance for all screen perf tests."""
    return Screen(scaler=1, show_fps_overlay=False)


@pytest.fixture(scope="module")
def scanline() -> list[int]:
    """Repeating palette-ID scanline."""
    return [i % 4 for i in range(SCREEN_WIDTH)]


@pytest.fixture(scope="module")
def full_buffer(scanline: list[int]) -> list[list[int]]:
    """Full-frame buffer of palette IDs."""
    return [scanline[:] for _ in range(SCREEN_HEIGHT)]


def test_perf_draw_scanline(screen: Screen, scanline: list[int]) -> None:
    """Measure draw_scanline throughput (one scanline per call)."""
    iterations = SCANLINE_ITERATIONS

    t0 = perf_counter()
    for _ in range(iterations):
        screen.draw_scanline(scanline, 0)
    elapsed = perf_counter() - t0

    calls_per_sec = iterations / elapsed
    ms_per_call = elapsed * 1000 / iterations
    print(
        f"\n[SCREEN draw_scanline]\n"
        f"  iterations : {iterations:>10,}\n"
        f"  total time : {elapsed:>10.4f} s\n"
        f"  ms/call    : {ms_per_call:>10.4f} ms\n"
        f"  throughput : {calls_per_sec:>10,.0f} calls/s",
    )
    assert elapsed < 5.0


def test_perf_draw_buffer(screen: Screen, full_buffer: list[list[int]]) -> None:
    """Measure draw_buffer throughput (full 160x144 frame per call)."""
    iterations = BUFFER_ITERATIONS

    t0 = perf_counter()
    for _ in range(iterations):
        screen.draw_buffer(full_buffer)
    elapsed = perf_counter() - t0

    frames_per_sec = iterations / elapsed
    ms_per_frame = elapsed * 1000 / iterations
    print(
        f"\n[SCREEN draw_buffer]\n"
        f"  iterations : {iterations:>10,}\n"
        f"  total time : {elapsed:>10.4f} s\n"
        f"  ms/frame   : {ms_per_frame:>10.4f} ms\n"
        f"  throughput : {frames_per_sec:>10,.1f} fps theoretical",
    )
    assert elapsed < 10.0

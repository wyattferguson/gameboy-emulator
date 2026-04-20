import os
from time import perf_counter

import pytest

from gbemu.cart import Cart
from gbemu.mmu import MMU

RUN_PERF_TESTS = os.getenv("GBEMU_RUN_PERF_TESTS") == "1"

pytestmark = [
    pytest.mark.performance,
    pytest.mark.skipif(
        not RUN_PERF_TESTS,
        reason="Set GBEMU_RUN_PERF_TESTS=1 to run performance tests.",
    ),
]

_WRAM_BASE = 0xC000
_THRESHOLD_SECONDS = 5.0


def _print_metrics(label: str, iterations: int, elapsed: float) -> None:
    """Print human-readable throughput metrics to stdout."""
    ops_per_sec = iterations / elapsed
    ns_per_op = (elapsed / iterations) * 1_000_000_000
    print(
        f"\n[MMU] {label}\n"
        f"  iterations : {iterations:>10,}\n"
        f"  total time : {elapsed:>10.4f} s\n"
        f"  throughput : {ops_per_sec:>10,.0f} ops/s\n"
        f"  per op     : {ns_per_op:>10.1f} ns",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_mmu_wram_read_write() -> None:
    """Sequential read/write cycle through WRAM (C000-DFFF)."""
    mmu = MMU()
    iterations = 300_000

    t0 = perf_counter()
    for i in range(iterations):
        addr = _WRAM_BASE + (i & 0x7FF)
        mmu[addr] = i & 0xFF
        _ = mmu[addr]
    elapsed = perf_counter() - t0

    _print_metrics("WRAM sequential read/write (300 000 pairs)", iterations, elapsed)
    assert elapsed < _THRESHOLD_SECONDS


def test_mmu_io_register_read_write() -> None:
    """Read/write to I/O register range (FF00-FF7F) — hits special-case paths."""
    mmu = MMU()
    # Use safe I/O addresses: palette, scroll, window registers (no side effects).
    io_addrs = [0xFF47, 0xFF42, 0xFF43, 0xFF4A, 0xFF4B]
    iterations = 200_000

    t0 = perf_counter()
    for i in range(iterations):
        addr = io_addrs[i % len(io_addrs)]
        mmu[addr] = i & 0xFF
        _ = mmu[addr]
    elapsed = perf_counter() - t0

    _print_metrics("I/O register read/write (200 000 pairs)", iterations, elapsed)
    assert elapsed < _THRESHOLD_SECONDS


def test_mmu_slice_read() -> None:
    """Slice read of 16-byte blocks from WRAM — exercises __getitem__ slice path."""
    mmu = MMU()
    iterations = 100_000

    t0 = perf_counter()
    for i in range(iterations):
        base = _WRAM_BASE + (i & 0x7F0)
        _ = mmu[base : base + 16]
    elapsed = perf_counter() - t0

    _print_metrics("WRAM slice read 16 B (100 000 slices)", iterations, elapsed)
    assert elapsed < _THRESHOLD_SECONDS


def test_mmu_rom_read_with_cart() -> None:
    """Read across ROM space (0000-7FFF) with a real cartridge mapped."""
    mmu = MMU(Cart("roms/hello.gb"))
    iterations = 200_000

    t0 = perf_counter()
    for i in range(iterations):
        addr = i & 0x7FFF
        _ = mmu[addr]
    elapsed = perf_counter() - t0

    _print_metrics("ROM read with cart (200 000 reads)", iterations, elapsed)
    assert elapsed < _THRESHOLD_SECONDS


def test_mmu_hram_read_write() -> None:
    """Read/write HRAM (FF80-FFFE) — the fast scratch region used during DMA."""
    mmu = MMU()
    iterations = 300_000

    t0 = perf_counter()
    for i in range(iterations):
        addr = 0xFF80 + (i & 0x7E)
        mmu[addr] = i & 0xFF
        _ = mmu[addr]
    elapsed = perf_counter() - t0

    _print_metrics("HRAM read/write (300 000 pairs)", iterations, elapsed)
    assert elapsed < _THRESHOLD_SECONDS

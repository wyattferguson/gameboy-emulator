import os
from time import perf_counter

import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU

RUN_PERF_TESTS = os.getenv("GBEMU_RUN_PERF_TESTS") == "1"

pytestmark = [
    pytest.mark.performance,
    pytest.mark.skipif(
        not RUN_PERF_TESTS,
        reason="Set GBEMU_RUN_PERF_TESTS=1 to run performance tests.",
    ),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_THRESHOLD_SECONDS = 6.0


def _print_metrics(label: str, iterations: int, elapsed: float) -> None:
    """Print human-readable throughput metrics to stdout."""
    ops_per_sec = iterations / elapsed
    us_per_op = (elapsed / iterations) * 1_000_000
    print(
        f"\n[CPU] {label}\n"
        f"  iterations : {iterations:>10,}\n"
        f"  total time : {elapsed:>10.4f} s\n"
        f"  throughput : {ops_per_sec:>10,.0f} ops/s\n"
        f"  per op     : {us_per_op:>10.3f} µs",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_cpu_nop_stream() -> None:
    """Measure raw instruction dispatch throughput on a dense NOP stream."""
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

    _print_metrics("NOP stream (4 000 instructions)", count, elapsed)
    assert elapsed < _THRESHOLD_SECONDS


def test_cpu_mixed_alu_stream() -> None:
    """Measure throughput on a mixed ALU workload (INC, DEC, ADD, XOR, LD)."""
    # INC A=0x3C, DEC B=0x05, ADD A,B=0x80, XOR A=0xAF, LD A,d8=0x3E+0x00
    pattern = [0x3C, 0x05, 0x80, 0xAF, 0x3E, 0x00]
    mmu = MMU()
    cpu = CPU(mmu)
    start = 0xC000
    repeats = 500
    code = (pattern * repeats)[:2_000]

    mmu.memory[start : start + len(code)] = code
    cpu.pc = start

    t0 = perf_counter()
    steps = 0
    while cpu.pc < start + len(code):
        cpu.cycle()
        steps += 1
    elapsed = perf_counter() - t0

    _print_metrics(f"Mixed ALU stream ({steps} instructions)", steps, elapsed)
    assert elapsed < _THRESHOLD_SECONDS


def test_cpu_branch_heavy_stream() -> None:
    """Measure throughput for a tight branch loop: JR NZ, $FE (spin until Z=1)."""
    mmu = MMU()
    cpu = CPU(mmu)

    # Place: LD B, 50 (0x06 0x32) then DJNZ-equivalent: DEC B / JR NZ, -3 / NOP
    # DEC B = 0x05, JR NZ = 0x20 rel, rel = 0xFD (-3 in two's complement)
    start = 0xC000
    code = [
        0x06,
        50,  # LD B, 50
    ]
    # 50 iterations of: DEC B (0x05) + JR NZ, -3 (0x20, 0xFD)
    code += [0x05, 0x20, 0xFD] * 50
    code += [0x00]  # NOP at the end

    mmu.memory[start : start + len(code)] = code
    cpu.pc = start

    t0 = perf_counter()
    steps = 0
    end = start + len(code) - 1
    for _ in range(10_000):
        cpu.cycle()
        steps += 1
        if cpu.pc >= end:
            break
    elapsed = perf_counter() - t0

    _print_metrics(f"Branch-heavy stream ({steps} instructions)", steps, elapsed)
    assert elapsed < _THRESHOLD_SECONDS


def test_cpu_interrupt_service_overhead() -> None:
    """Measure overhead when interrupts fire repeatedly via NOP + forced IF."""
    mmu = MMU()
    cpu = CPU(mmu)
    start = 0xC000
    count = 2_000

    mmu.memory[start : start + count] = [0x00] * count
    cpu.pc = start
    cpu.interrupts = True

    # Point VBlank vector (0x40) to a RETI (0xD9) so interrupt returns immediately.
    mmu.memory[0x40] = 0xD9

    t0 = perf_counter()
    for _ in range(count):
        mmu.memory[0xFF0F] = 0x01  # request VBlank interrupt
        mmu.memory[0xFFFF] = 0x01  # enable VBlank interrupt
        cpu.cycle()
    elapsed = perf_counter() - t0

    _print_metrics(f"Interrupt service overhead ({count} cycles)", count, elapsed)
    assert elapsed < _THRESHOLD_SECONDS

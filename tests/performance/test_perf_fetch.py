from time import perf_counter

import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU

from .perfconfig import ITERATIONS

pytestmark = [pytest.mark.performance]


def test_cpu_fetch_mixed_opcode_stream() -> None:
    """Measure CPU.fetch throughput on a mixed CB/non-CB opcode stream."""
    mmu = MMU()
    cpu = CPU(mmu)

    base = 0xC000
    stream = [
        0x00,  # NOP
        0x7C,  # LD A,H
        0x3E,  # LD A,d8 (fetch only)
        0xAF,  # XOR A
        0xCB,
        0x11,  # RL C
        0xCB,
        0x7C,  # BIT 7,H
        0xCB,
        0x37,  # SWAP A
    ]
    mmu.memory[base : base + len(stream)] = stream

    iterations = ITERATIONS
    stream_len = len(stream)

    t0 = perf_counter()
    for i in range(iterations):
        cpu.pc = base + (i % stream_len)
        cpu.fetch()
    elapsed = perf_counter() - t0

    fetches_per_sec = iterations / elapsed
    print(
        f"\n[FETCH PERFORMANCE]\n"
        f"  iterations : {iterations:>10,}\n"
        f"  total time : {elapsed:>10.4f} s\n"
        f"  throughput : {fetches_per_sec:>10,.0f} fetches/s",
    )
    assert elapsed < 10.0

from time import perf_counter

import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU

from .perfconfig import ITERATIONS

pytestmark = [pytest.mark.performance]


def test_cpu_decode_mixed_instruction_stream() -> None:
    """Measure CPU.decode throughput with mixed 1/2/3-byte instructions."""
    mmu = MMU()
    cpu = CPU(mmu)

    base = 0xC000
    stream = [
        0x00,  # NOP (1-byte)
        0x3E,
        0x12,  # LD A,d8 (2-byte)
        0x21,
        0x34,
        0x12,  # LD HL,d16 (3-byte)
        0x7C,  # LD A,H (1-byte)
        0xCB,
        0x11,  # RL C (CB-prefixed)
    ]
    mmu.memory[base : base + len(stream)] = stream

    iterations = ITERATIONS
    stream_len = len(stream)

    t0 = perf_counter()
    for i in range(iterations):
        cpu.pc = base + (i % stream_len)
        cpu.fetch()
        cpu.decode()
    elapsed = perf_counter() - t0

    decodes_per_sec = iterations / elapsed
    print(
        f"\n[DECODE PERFORMANCE]\n"
        f"  iterations : {iterations:>10,}\n"
        f"  total time : {elapsed:>10.4f} s\n"
        f"  throughput : {decodes_per_sec:>10,.0f} decodes/s",
    )
    assert elapsed < 10.0

from time import perf_counter

import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU

from .perfconfig import ITERATIONS

pytestmark = [pytest.mark.performance]


def test_cpu_execute_mixed_hot_operations() -> None:
    """Measure CPU.execute throughput over a mixed operation stream."""
    mmu = MMU()
    cpu = CPU(mmu)

    # Seed deterministic register/memory state used by handlers.
    cpu.reg["A"] = 0x42
    cpu.reg["B"] = 0x11
    cpu.reg["C"] = 0x22
    cpu.reg["H"] = 0xC0
    cpu.reg["L"] = 0x10
    mmu[0xC010] = 0x77

    base = 0xC200
    stream = [
        0x00,  # NOP
        0x3C,  # INC A
        0x05,  # DEC B
        0x80,  # ADD A,B
        0xA9,  # XOR A,C
        0x7E,  # LD A,[HL]
        0x77,  # LD [HL],A
        0xCB,
        0x11,  # RL C
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
        cpu.decode()
        cpu.execute()
    elapsed = perf_counter() - t0

    executes_per_sec = iterations / elapsed
    print(
        f"\n[EXECUTE PERFORMANCE]\n"
        f"  iterations : {iterations:>10,}\n"
        f"  total time : {elapsed:>10.4f} s\n"
        f"  throughput : {executes_per_sec:>10,.0f} executes/s",
    )
    assert elapsed < 10.0

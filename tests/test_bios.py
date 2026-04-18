import pytest

from gbemu.cart import Cart
from gbemu.cpu import CPU
from gbemu.mmu import MMU


def test_cpu_runs_initial_bios_sequence() -> None:
    """Run BIOS from reset through the first call-site and verify side effects."""
    cpu = CPU(MMU())

    target_pc = 0x28  # Stop before executing the first CALL instruction in BIOS.
    max_steps = 30000

    for _ in range(max_steps):
        if cpu.pc == target_pc:
            break
        cpu.cycle()
    else:
        pytest.fail("CPU did not reach first BIOS call site within step budget")

    assert cpu.pc == target_pc

    # BIOS boot sequence writes expected I/O values before first CALL.
    assert cpu.mmu[0xFF26] == 0x80
    assert cpu.mmu[0xFF25] == 0xF3
    assert cpu.mmu[0xFF24] == 0x77
    assert cpu.mmu[0xFF11] == 0x80
    assert cpu.mmu[0xFF12] == 0xF3
    assert cpu.mmu[0xFF47] == 0xFC


def test_cpu_runs_full_bios_sequence() -> None:
    """Run boot ROM until it unmaps itself by writing 0x01 to 0xFF50."""
    cpu = CPU(MMU(Cart()))
    max_steps = 500000

    for _ in range(max_steps):
        # Stabilize LY to allow BIOS wait loop to progress without a PPU implementation.
        cpu.mmu[0xFF44] = 0x90
        cpu.cycle()
        if cpu.mmu[0xFF50] == 0x01:
            break
    else:
        pytest.fail("CPU did not finish BIOS boot sequence within step budget")

    assert cpu.mmu[0xFF50] == 0x01
    assert cpu.pc == 0x100

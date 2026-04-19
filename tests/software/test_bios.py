from collections.abc import Callable

import pytest

from gbemu.cart import Cart
from gbemu.cpu import CPU
from gbemu.mmu import MMU
from tests.utils import make_cpu


def _run_until_pc(
    cpu: CPU,
    target_pc: int,
    max_steps: int,
    stabilize_ly: bool = False,
) -> None:
    """Execute CPU cycles until a target PC is reached."""
    for _ in range(max_steps):
        if cpu.pc == target_pc:
            return
        if stabilize_ly:
            # Allow BIOS LY wait-loop to progress without full PPU timing.
            cpu.mmu[0xFF44] = 0x90
        cpu.cycle()
    pytest.fail(f"CPU did not reach PC {hex(target_pc)} within step budget")


def _run_until(
    cpu: CPU,
    condition: Callable[[], bool],
    max_steps: int,
    stabilize_ly: bool = False,
) -> None:
    """Execute CPU cycles until a condition becomes true."""
    for _ in range(max_steps):
        if condition():
            return
        if stabilize_ly:
            cpu.mmu[0xFF44] = 0x90
        cpu.cycle()
    pytest.fail("CPU did not satisfy BIOS completion condition within step budget")


def test_bios_starts_vram_clear_process() -> None:
    """BIOS startup should begin clearing VRAM at the top of tile memory."""
    cpu = make_cpu()

    # Seed representative addresses to ensure the clear loop actually writes zeros.
    cpu.mmu[0x8000] = 0xAA
    cpu.mmu[0x9000] = 0xBB
    cpu.mmu[0x9FFF] = 0xCC

    _run_until_pc(cpu, target_pc=0x0C, max_steps=50000)

    assert cpu.reg["SP"] == 0xFFFE
    assert cpu.reg["A"] == 0x00
    # At this checkpoint the first clear write has occurred and HL moved down.
    assert cpu.reg["HL"] == 0x9FFE
    assert cpu.mmu[0x9FFF] == 0x00


def test_bios_initializes_audio_and_palette_io() -> None:
    """BIOS should initialize core audio registers and BG palette in the IO area."""
    cpu = make_cpu()

    _run_until_pc(cpu, target_pc=0x21, max_steps=50000)

    assert cpu.mmu[0xFF26] == 0x80
    assert cpu.mmu[0xFF25] == 0xF3
    assert cpu.mmu[0xFF24] == 0x77
    assert cpu.mmu[0xFF11] == 0x80
    assert cpu.mmu[0xFF12] == 0xF3
    assert cpu.mmu[0xFF47] == 0xFC


def test_bios_processes_logo_and_sets_display_state() -> None:
    """BIOS should process logo/tile setup and prime display control registers."""
    cpu = CPU(MMU(Cart()))

    # 0x64 is the start of the LY polling loop.
    _run_until_pc(cpu, target_pc=0x64, max_steps=250000)

    assert cpu.mmu[0x9910] == 0x19
    assert cpu.mmu[0xFF42] == 0x64
    assert cpu.mmu[0xFF40] == 0x91

    # Logo/tile decode should populate tile data region with non-zero bytes.
    assert any(cpu.mmu[0x8010:0x8030])


def test_cpu_runs_initial_bios_sequence() -> None:
    """Run BIOS from reset through the first call-site and verify side effects."""
    cpu = make_cpu()

    # Stop before executing the first CALL instruction in BIOS.
    _run_until_pc(cpu, target_pc=0x28, max_steps=50000)

    assert cpu.pc == 0x28

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

    _run_until(
        cpu,
        condition=lambda: cpu.mmu[0xFF50] == 0x01,
        max_steps=500000,
        stabilize_ly=True,
    )

    assert cpu.mmu[0xFF50] == 0x01
    assert cpu.pc == 0x100
    assert cpu.reg["A"] == 0x01

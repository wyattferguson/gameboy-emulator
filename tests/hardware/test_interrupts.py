import pytest

from gbemu.config import M_INTERRUPT_ENABLE, M_INTERRUPT_FLAG
from tests.utils import make_cpu

PENDING_INTERRUPTS_ATTR = "_pending" + "_interrupts"
SERVICE_INTERRUPT_ATTR = "_service" + "_interrupt"
IME_DELAY_ATTR = "_ime" + "_delay"


def pending_interrupts(cpu: object) -> int:
    return getattr(cpu, PENDING_INTERRUPTS_ATTR)()


def service_interrupt(cpu: object) -> bool:
    return getattr(cpu, SERVICE_INTERRUPT_ATTR)()


def get_ime_delay(cpu: object) -> int:
    return getattr(cpu, IME_DELAY_ATTR)


def set_ime_delay(cpu: object, value: int) -> None:
    setattr(cpu, IME_DELAY_ATTR, value)


def test_pending_interrupts_masks_to_enabled_low_five_bits() -> None:
    cpu = make_cpu()
    cpu.mmu[M_INTERRUPT_ENABLE] = 0xFF
    cpu.mmu[M_INTERRUPT_FLAG] = 0xFF

    assert pending_interrupts(cpu) == 0x1F


def test_pending_interrupts_respects_enable_mask() -> None:
    cpu = make_cpu()
    cpu.mmu[M_INTERRUPT_ENABLE] = 0x14
    cpu.mmu[M_INTERRUPT_FLAG] = 0x17

    assert pending_interrupts(cpu) == 0x14


def test_service_interrupt_returns_false_when_ime_disabled() -> None:
    cpu = make_cpu()
    cpu.interrupts = False
    cpu.pc = 0x3456
    cpu.reg["SP"] = 0xFFFE
    cpu.mmu[M_INTERRUPT_ENABLE] = 0x01
    cpu.mmu[M_INTERRUPT_FLAG] = 0x01

    assert service_interrupt(cpu) is False
    assert cpu.pc == 0x3456
    assert cpu.reg["SP"] == 0xFFFE
    assert (cpu.mmu[M_INTERRUPT_FLAG] & 0x01) == 0x01


@pytest.mark.parametrize(
    ("mask", "vector"),
    [
        (0x01, 0x40),
        (0x02, 0x48),
        (0x04, 0x50),
        (0x08, 0x58),
        (0x10, 0x60),
    ],
)
def test_service_interrupt_jumps_to_correct_vector(mask: int, vector: int) -> None:
    cpu = make_cpu()
    cpu.interrupts = True
    cpu.pc = 0x2468
    cpu.reg["SP"] = 0xFFFE
    cpu.mmu[M_INTERRUPT_ENABLE] = mask
    cpu.mmu[M_INTERRUPT_FLAG] = mask

    assert service_interrupt(cpu) is True
    assert cpu.pc == vector
    assert cpu.interrupts is False
    assert get_ime_delay(cpu) == 0
    assert cpu.reg["SP"] == 0xFFFC
    assert cpu.mmu[0xFFFC] == 0x68
    assert cpu.mmu[0xFFFD] == 0x24
    assert (cpu.mmu[M_INTERRUPT_FLAG] & mask) == 0


def test_service_interrupt_uses_priority_order_with_multiple_pending() -> None:
    cpu = make_cpu()
    cpu.interrupts = True
    cpu.pc = 0x4000
    cpu.reg["SP"] = 0xFFFE
    cpu.mmu[M_INTERRUPT_ENABLE] = 0x1F
    cpu.mmu[M_INTERRUPT_FLAG] = 0x1C

    assert service_interrupt(cpu) is True
    assert cpu.pc == 0x50
    assert cpu.mmu[M_INTERRUPT_FLAG] == 0x18


def test_service_interrupt_clears_ime_delay_when_taken() -> None:
    cpu = make_cpu()
    cpu.interrupts = True
    set_ime_delay(cpu, 1)
    cpu.mmu[M_INTERRUPT_ENABLE] = 0x01
    cpu.mmu[M_INTERRUPT_FLAG] = 0x01

    assert service_interrupt(cpu) is True
    assert get_ime_delay(cpu) == 0


def test_halt_with_pending_interrupt_and_ime_disabled_resumes_without_servicing() -> None:
    cpu = make_cpu()
    cpu.halted = True
    cpu.interrupts = False
    cpu.pc = 0x200
    cpu.insert_instruction(bytearray([0x00]))
    cpu.mmu[M_INTERRUPT_ENABLE] = 0x01
    cpu.mmu[M_INTERRUPT_FLAG] = 0x01

    cycles = cpu.cycle()

    assert cycles == 4
    assert cpu.halted is False
    assert cpu.pc == 0x201
    assert (cpu.mmu[M_INTERRUPT_FLAG] & 0x01) == 0x01


def test_cycle_services_interrupt_before_fetching_next_opcode() -> None:
    cpu = make_cpu()
    cpu.interrupts = True
    cpu.pc = 0x300
    cpu.reg["SP"] = 0xFFFE
    cpu.insert_instruction(bytearray([0x00]))
    cpu.mmu[M_INTERRUPT_ENABLE] = 0x02
    cpu.mmu[M_INTERRUPT_FLAG] = 0x02

    cycles = cpu.cycle()

    assert cycles == 20
    assert cpu.pc == 0x48
    assert cpu.reg["SP"] == 0xFFFC
    assert cpu.mmu[0xFFFC] == 0x00
    assert cpu.mmu[0xFFFD] == 0x03


def test_reti_restores_pc_and_reenables_ime() -> None:
    cpu = make_cpu()
    cpu.reg["SP"] = 0xFFFC
    cpu.mmu[0xFFFC] = 0x34
    cpu.mmu[0xFFFD] = 0x12
    cpu.interrupts = False
    set_ime_delay(cpu, 2)

    cpu.reti()

    assert cpu.pc == 0x1234
    assert cpu.reg["SP"] == 0xFFFE
    assert cpu.interrupts is True
    assert get_ime_delay(cpu) == 0


def test_di_clears_ime_and_pending_enable_delay() -> None:
    cpu = make_cpu()
    cpu.interrupts = True
    set_ime_delay(cpu, 2)

    cpu.di()

    assert cpu.interrupts is False
    assert get_ime_delay(cpu) == 0


def test_ei_sets_enable_delay_without_immediate_ime() -> None:
    cpu = make_cpu()
    cpu.interrupts = False

    cpu.ei()

    assert cpu.interrupts is False
    assert get_ime_delay(cpu) == 2

import pytest

from gbemu.config import PC_START, SP_START
from gbemu.cpu import CPU
from gbemu.mmu import MMU


@pytest.mark.parametrize(
    "target_addr",
    [
        0x1234,  # CALL a16
        0x8000,  # CALL a16 high address
        0x0000,  # CALL a16 low address
        0x0100,  # CALL a16 typical ROM address
    ],
)
def test_call(
    target_addr: int,
) -> None:
    """Test CALL instruction. Push PC to stack and jump to address."""
    cpu = CPU(MMU())
    initial_sp = cpu.reg["SP"]

    # Instruction: opcode (1 byte) + address (2 bytes, little-endian)
    addr_low = target_addr & 0xFF
    addr_high = (target_addr >> 8) & 0xFF
    cpu.insert_instruction(bytearray([0xCD, addr_low, addr_high]))

    cpu.cycle()
    assert cpu.pc == target_addr
    assert cpu.reg["SP"] == (initial_sp - 2) & 0xFFFF


@pytest.mark.parametrize(
    (
        "opcode",
        "flag",
        "flag_value",
        "target_addr",
        "should_call",
    ),
    [
        (0xC4, "Z", 0, 0x1234, True),  # CALL NZ, a16 w/ Z = 0 (call taken)
        (0xC4, "Z", 1, 0x1234, False),  # CALL NZ, a16 w/ Z = 1 (call not taken)
        (0xCC, "Z", 1, 0x5678, True),  # CALL Z, a16 w/ Z = 1 (call taken)
        (0xCC, "Z", 0, 0x5678, False),  # CALL Z, a16 w/ Z = 0 (call not taken)
        (0xD4, "C", 0, 0x8000, True),  # CALL NC, a16 w/ C = 0 (call taken)
        (0xD4, "C", 1, 0x8000, False),  # CALL NC, a16 w/ C = 1 (call not taken)
        (0xDC, "C", 1, 0xABCD, True),  # CALL C, a16 w/ C = 1 (call taken)
        (0xDC, "C", 0, 0xABCD, False),  # CALL C, a16 w/ C = 0 (call not taken)
    ],
)
def test_callc(
    opcode: int,
    flag: str,
    flag_value: int,
    target_addr: int,
    should_call: bool,
) -> None:
    """Test conditional CALL instructions."""
    cpu = CPU(MMU())
    initial_pc = cpu.pc
    initial_sp = cpu.reg["SP"]

    cpu.flags[flag] = flag_value
    addr_low = target_addr & 0xFF
    addr_high = (target_addr >> 8) & 0xFF
    cpu.insert_instruction(bytearray([opcode, addr_low, addr_high]))

    cpu.cycle()

    if should_call:
        assert cpu.pc == target_addr
        assert cpu.reg["SP"] == (initial_sp - 2) & 0xFFFF
    else:
        assert cpu.pc == (initial_pc + 3) & 0xFFFF
        assert cpu.reg["SP"] == initial_sp


@pytest.mark.parametrize(
    (
        "flag",
        "flag_value",
    ),
    [
        ("Z", 0),  # RET NZ w/ Z = 0 (return taken)
        ("Z", 1),  # RET NZ w/ Z = 1 (return not taken)
    ],
)
def test_ret_nz(
    flag: str,
    flag_value: int,
) -> None:
    """Test RET NZ instruction. Return from subroutine if Z flag is 0."""
    cpu = CPU(MMU())
    return_addr = 0x1234
    initial_pc = cpu.pc

    cpu.reg["SP"] = 0x8000
    cpu.mmu[cpu.reg["SP"]] = return_addr & 0xFF  # low byte at SP
    cpu.mmu[cpu.reg["SP"] + 1] = (return_addr >> 8) & 0xFF  # high byte at SP+1

    cpu.flags[flag] = flag_value
    cpu.insert_instruction(bytearray([0xC0]))

    cpu.cycle()

    if flag_value == 0:
        assert cpu.pc == return_addr
        assert cpu.reg["SP"] == (0x8000 + 2) & 0xFFFF
    else:
        assert cpu.pc == (initial_pc + 1) & 0xFFFF
        assert cpu.reg["SP"] == 0x8000

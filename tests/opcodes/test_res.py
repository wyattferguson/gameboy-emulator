import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from tests.utils import verify_flags

REGISTER_ORDER = ["B", "C", "D", "E", "H", "L", "HL", "A"]


@pytest.mark.parametrize(
    ("bit_num", "target_index"),
    [(bit_num, target_index) for bit_num in range(8) for target_index in range(8)],
)
def test_cb_res_all_targets(bit_num: int, target_index: int) -> None:
    """Test all CB-prefixed RES opcodes for registers and [HL]."""
    mmu = MMU()
    cpu = CPU(mmu)
    target = REGISTER_ORDER[target_index]
    opcode = 0x80 + (bit_num * 8) + target_index
    initial_value = 0xFF
    expected_value = initial_value & ~(1 << bit_num)

    cpu.flags["Z"] = 1
    cpu.flags["N"] = 0
    cpu.flags["H"] = 1
    cpu.flags["C"] = 0

    if target == "HL":
        addr = 0xC000
        cpu.reg["H"] = addr >> 8
        cpu.reg["L"] = addr & 0xFF
        mmu[addr] = initial_value
    else:
        cpu.reg[target] = initial_value

    cpu.insert_instruction(bytearray([0xCB, opcode]))
    cpu.cycle()

    if target == "HL":
        assert mmu[addr] == expected_value
    else:
        assert cpu.reg[target] == expected_value

    verify_flags(cpu, z_flag=1, n_flag=0, h_flag=1, c_flag=0)


@pytest.mark.parametrize(
    ("bit_num", "opcode", "value", "expected_value"),
    [
        (0, 0x80, 0xAA, 0xAA),
        (3, 0x9B, 0xFF, 0xF7),
        (6, 0xB5, 0x00, 0x00),
        (7, 0xBE, 0x7F, 0x7F),
    ],
)
def test_cb_res_preserves_unrelated_bits(
    bit_num: int,
    opcode: int,
    value: int,
    expected_value: int,
) -> None:
    """Test RES only clears the selected bit and leaves all others unchanged."""
    mmu = MMU()
    cpu = CPU(mmu)
    target = REGISTER_ORDER[opcode % 8]

    if target == "HL":
        addr = 0xC100
        cpu.reg["H"] = addr >> 8
        cpu.reg["L"] = addr & 0xFF
        mmu[addr] = value
    else:
        cpu.reg[target] = value

    cpu.insert_instruction(bytearray([0xCB, opcode]))
    cpu.cycle()

    if target == "HL":
        assert mmu[addr] == expected_value
    else:
        assert cpu.reg[target] == expected_value

    assert ((expected_value >> bit_num) & 0x1) == 0

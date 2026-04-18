import pytest

from gbemu.cpu import CPU
from gbemu.mmu import MMU
from tests.utils import verify_flags

REGISTER_ORDER = ["B", "C", "D", "E", "H", "L", "HL", "A"]


@pytest.mark.parametrize(
    ("bit_num", "target_index"),
    [(bit_num, target_index) for bit_num in range(8) for target_index in range(8)],
)
def test_cb_set_all_targets(bit_num: int, target_index: int) -> None:
    """Test all CB-prefixed SET opcodes for registers and [HL]."""
    mmu = MMU()
    cpu = CPU(mmu)
    target = REGISTER_ORDER[target_index]
    opcode = 0xC0 + (bit_num * 8) + target_index
    initial_value = 0x00
    expected_value = initial_value | (1 << bit_num)

    cpu.flags["Z"] = 0
    cpu.flags["N"] = 1
    cpu.flags["H"] = 0
    cpu.flags["C"] = 1

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

    verify_flags(cpu, z_flag=0, n_flag=1, h_flag=0, c_flag=1)


@pytest.mark.parametrize(
    ("bit_num", "opcode", "value", "expected_value"),
    [
        (0, 0xC0, 0xAA, 0xAB),
        (3, 0xDB, 0x00, 0x08),
        (6, 0xF5, 0x40, 0x40),
        (7, 0xFE, 0x7F, 0xFF),
    ],
)
def test_cb_set_preserves_unrelated_bits(
    bit_num: int,
    opcode: int,
    value: int,
    expected_value: int,
) -> None:
    """Test SET only sets the selected bit and leaves all others unchanged."""
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

    assert ((expected_value >> bit_num) & 0x1) == 1

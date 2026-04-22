import pytest

from tests.utils import SAFE_HL_ADDRESS, cycle_instruction, make_cpu, set_hl_value, verify_flags


@pytest.mark.parametrize(
    ("dest", "value", "c_flag", "result", "opcode"),
    [
        ("A", 0x11, 0, 0x22, 0x7),  # RLCA
        ("A", 0xFF, 1, 0xFF, 0x7),  # RLCA with carry
        ("A", 0x11, 1, 0x88, 0xF),  # RRCA
        ("A", 0xFE, 0, 0x7F, 0xF),  # RRCA without carry
    ],
)
def test_rot_circular(dest: str, value: int, c_flag: int, result: int, opcode: int) -> None:
    cpu = make_cpu()
    cpu.reg[dest] = value
    cycle_instruction(cpu, opcode)

    assert cpu.reg[dest] == result
    verify_flags(cpu, c_flag=c_flag)


@pytest.mark.parametrize(
    ("dest", "value", "start_c_flag", "c_flag", "result", "opcode"),
    [
        ("A", 0x11, 0, 0, 0x22, 0x17),  # RLA
        ("A", 0xFF, 1, 1, 0xFF, 0x17),  # RLA start carry 1
        ("A", 0x56, 0, 0, 0xAC, 0x17),  # RLA start carry 0
        ("A", 0x78, 1, 0, 0xF1, 0x17),  # RLA no carry
        ("A", 0x11, 0, 1, 0x08, 0x1F),  # RRA start carry 0
        ("A", 0xFF, 1, 1, 0xFF, 0x1F),  # RRA start carry 1
        ("A", 0x56, 0, 0, 0x2B, 0x1F),  # RRA without carry-in
        ("A", 0x78, 1, 0, 0xBC, 0x1F),  # RRA with carry-in
    ],
)
def test_rot_carry(
    dest: str,
    value: int,
    start_c_flag: int,
    c_flag: int,
    result: int,
    opcode: int,
) -> None:
    cpu = make_cpu()
    cpu.reg[dest] = value
    cpu.flags["C"] = start_c_flag
    cycle_instruction(cpu, opcode)

    assert cpu.reg[dest] == result
    verify_flags(cpu, c_flag=c_flag)


@pytest.mark.parametrize(
    ("dest", "value", "start_c_flag", "c_flag", "result", "opcode"),
    [
        ("B", 0x11, 0, 0, 0x22, 0x0),  # RLC B
        ("B", 0xFF, 1, 1, 0xFF, 0x0),  # RLC B w/ carry
        ("C", 0x11, 0, 0, 0x22, 0x1),  # RLC C
        ("D", 0x56, 0, 0, 0xAC, 0x2),  # RLC D
        ("D", 0x78, 1, 0, 0xF0, 0x2),  # RLC D with start carry 1
        ("E", 0x11, 0, 0, 0x22, 0x3),  # RLC E
        ("H", 0xFF, 1, 1, 0xFF, 0x4),  # RLC H
        ("L", 0x56, 0, 0, 0xAC, 0x5),  # RLC L
        ("L", 0x78, 1, 0, 0xF0, 0x5),  # RLC L with start carry 1
    ],
)
def test_cb_rot(
    dest: str,
    value: int,
    start_c_flag: int,
    c_flag: int,
    result: int,
    opcode: int,
) -> None:
    cpu = make_cpu()
    cpu.reg[dest] = value
    cpu.flags["C"] = start_c_flag
    cycle_instruction(cpu, 0xCB, opcode)

    assert cpu.reg[dest] == result
    verify_flags(cpu, c_flag=c_flag)


@pytest.mark.parametrize(
    ("value", "start_c_flag", "c_flag", "result"),
    [
        (0x11, 0, 0, 0x22),  # RLC [HL] no carry
        (0xFF, 1, 1, 0xFF),  # RLC [HL] all ones
        (0x80, 0, 1, 0x01),  # RLC [HL] bit 7 wraps to bit 0
        (0x78, 1, 0, 0xF0),  # RLC [HL] start carry ignored
    ],
)
def test_cb_rot_hl(value: int, start_c_flag: int, c_flag: int, result: int) -> None:
    cpu = make_cpu()
    set_hl_value(cpu, value)
    cpu.flags["C"] = start_c_flag
    cycle_instruction(cpu, 0xCB, 0x6)

    assert cpu.mmu[SAFE_HL_ADDRESS] == result
    verify_flags(cpu, c_flag=c_flag)


@pytest.mark.parametrize(
    ("dest", "value", "start_c_flag", "c_flag", "result", "opcode"),
    [
        ("A", 0x85, 0, 1, 0x0B, 0x7),  # RLC A
        ("B", 0x01, 0, 1, 0x80, 0x8),  # RRC B
        ("C", 0x01, 0, 1, 0x80, 0x9),  # RRC C
        ("D", 0x01, 0, 1, 0x80, 0xA),  # RRC D
        ("E", 0x01, 0, 1, 0x80, 0xB),  # RRC E
        ("H", 0x01, 0, 1, 0x80, 0xC),  # RRC H
        ("L", 0x01, 0, 1, 0x80, 0xD),  # RRC L
        ("A", 0x01, 0, 1, 0x80, 0xF),  # RRC A
        ("B", 0x80, 1, 1, 0x01, 0x10),  # RL B
        ("C", 0x80, 1, 1, 0x01, 0x11),  # RL C
        ("D", 0x80, 1, 1, 0x01, 0x12),  # RL D
        ("E", 0x80, 1, 1, 0x01, 0x13),  # RL E
        ("H", 0x80, 1, 1, 0x01, 0x14),  # RL H
        ("L", 0x80, 1, 1, 0x01, 0x15),  # RL L
        ("A", 0x80, 1, 1, 0x01, 0x17),  # RL A
        ("B", 0x01, 1, 1, 0x80, 0x18),  # RR B
        ("C", 0x01, 1, 1, 0x80, 0x19),  # RR C
        ("D", 0x01, 1, 1, 0x80, 0x1A),  # RR D
        ("E", 0x01, 1, 1, 0x80, 0x1B),  # RR E
        ("H", 0x01, 1, 1, 0x80, 0x1C),  # RR H
        ("L", 0x01, 1, 1, 0x80, 0x1D),  # RR L
        ("A", 0x01, 1, 1, 0x80, 0x1F),  # RR A
    ],
)
def test_cb_rot_remaining_registers(
    dest: str,
    value: int,
    start_c_flag: int,
    c_flag: int,
    result: int,
    opcode: int,
) -> None:
    cpu = make_cpu()
    cpu.reg[dest] = value
    cpu.flags["C"] = start_c_flag
    cycle_instruction(cpu, 0xCB, opcode)

    assert cpu.reg[dest] == result
    verify_flags(cpu, c_flag=c_flag)


@pytest.mark.parametrize(
    ("opcode", "value", "start_c_flag", "c_flag", "result"),
    [
        (0xE, 0x01, 0, 1, 0x80),  # RRC [HL]
        (0x16, 0x80, 1, 1, 0x01),  # RL [HL]
        (0x1E, 0x01, 1, 1, 0x80),  # RR [HL]
    ],
)
def test_cb_rot_remaining_hl(
    opcode: int,
    value: int,
    start_c_flag: int,
    c_flag: int,
    result: int,
) -> None:
    cpu = make_cpu()
    set_hl_value(cpu, value)
    cpu.flags["C"] = start_c_flag
    cycle_instruction(cpu, 0xCB, opcode)

    assert cpu.mmu[SAFE_HL_ADDRESS] == result
    verify_flags(cpu, c_flag=c_flag)


@pytest.mark.parametrize(
    ("dest", "value", "c_flag", "result", "opcode"),
    [
        ("B", 0x81, 1, 0x02, 0x20),  # SLA B
        ("C", 0x80, 1, 0x00, 0x21),  # SLA C
        ("D", 0x40, 0, 0x80, 0x22),  # SLA D
        ("E", 0x7F, 0, 0xFE, 0x23),  # SLA E
        ("H", 0x01, 0, 0x02, 0x24),  # SLA H
        ("L", 0xFF, 1, 0xFE, 0x25),  # SLA L
        ("A", 0x55, 0, 0xAA, 0x27),  # SLA A
        ("B", 0x81, 1, 0xC0, 0x28),  # SRA B
        ("C", 0x7F, 1, 0x3F, 0x29),  # SRA C
        ("D", 0x80, 0, 0xC0, 0x2A),  # SRA D
        ("E", 0x01, 1, 0x00, 0x2B),  # SRA E
        ("H", 0xFF, 1, 0xFF, 0x2C),  # SRA H
        ("L", 0x02, 0, 0x01, 0x2D),  # SRA L
        ("A", 0x85, 1, 0xC2, 0x2F),  # SRA A
    ],
)
def test_cb_shift_selected_registers(
    dest: str,
    value: int,
    c_flag: int,
    result: int,
    opcode: int,
) -> None:
    cpu = make_cpu()
    cpu.reg[dest] = value
    cycle_instruction(cpu, 0xCB, opcode)

    assert cpu.reg[dest] == result
    verify_flags(cpu, c_flag=c_flag)


@pytest.mark.parametrize(
    ("opcode", "value", "c_flag", "result"),
    [
        (0x26, 0x81, 1, 0x02),  # SLA [HL]
        (0x2E, 0x81, 1, 0xC0),  # SRA [HL]
    ],
)
def test_cb_shift_selected_hl(opcode: int, value: int, c_flag: int, result: int) -> None:
    cpu = make_cpu()
    set_hl_value(cpu, value)
    cycle_instruction(cpu, 0xCB, opcode)

    assert cpu.mmu[SAFE_HL_ADDRESS] == result
    verify_flags(cpu, c_flag=c_flag)


def test_cb_prefixed_instruction_advances_pc_by_two() -> None:
    cpu = make_cpu()
    initial_pc = cpu.pc
    cycle_instruction(cpu, 0xCB, 0x11)

    assert cpu.pc == (initial_pc + 2) & 0xFFFF


@pytest.mark.parametrize(
    ("dest", "value", "z_flag", "result", "opcode"),
    [
        ("B", 0xAB, 0, 0xBA, 0x30),  # SWAP B
        ("C", 0x12, 0, 0x21, 0x31),  # SWAP C
        ("D", 0xF0, 0, 0x0F, 0x32),  # SWAP D
        ("E", 0x0F, 0, 0xF0, 0x33),  # SWAP E
        ("H", 0x00, 1, 0x00, 0x34),  # SWAP H zero
        ("L", 0x5A, 0, 0xA5, 0x35),  # SWAP L
        ("A", 0x37, 0, 0x73, 0x37),  # SWAP A
    ],
)
def test_cb_swap_registers(dest: str, value: int, z_flag: int, result: int, opcode: int) -> None:
    cpu = make_cpu()
    cpu.reg[dest] = value
    cycle_instruction(cpu, 0xCB, opcode)

    assert cpu.reg[dest] == result
    verify_flags(cpu, z_flag=z_flag, n_flag=0, h_flag=0, c_flag=0)


@pytest.mark.parametrize(
    ("value", "z_flag", "result"),
    [
        (0xAB, 0, 0xBA),  # SWAP [HL]
        (0x00, 1, 0x00),  # SWAP [HL] zero
        (0xF0, 0, 0x0F),  # SWAP [HL] upper nibble
    ],
)
def test_cb_swap_hl(value: int, z_flag: int, result: int) -> None:
    cpu = make_cpu()
    set_hl_value(cpu, value)
    cycle_instruction(cpu, 0xCB, 0x36)

    assert cpu.mmu[SAFE_HL_ADDRESS] == result
    verify_flags(cpu, z_flag=z_flag, n_flag=0, h_flag=0, c_flag=0)

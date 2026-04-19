from gbemu.cpu import INVALID_UNPREFIXED_OPCODES
from gbemu.opcodes import CB_PREFIXED, OPCODES
from tests.utils import make_cpu


def test_unprefixed_opcode_table_covers_defined_instruction_space() -> None:
    """All 256 bytes are either implemented opcodes or documented invalid ones."""
    missing = []
    for opcode in range(0x100):
        key = hex(opcode)
        if opcode == 0xCB:
            # 0xCB is the prefix for the separate CB-prefixed instruction space.
            continue
        if key in OPCODES:
            continue
        if opcode in INVALID_UNPREFIXED_OPCODES:
            continue
        missing.append(key)

    assert not missing, f"Missing unprefixed opcode definitions: {missing}"


def test_cb_prefixed_opcode_table_is_complete() -> None:
    """CB-prefixed decode table should contain all 256 entries."""
    missing = [hex(opcode) for opcode in range(0x100) if hex(opcode) not in CB_PREFIXED]
    assert not missing, f"Missing CB-prefixed opcode definitions: {missing}"


def test_invalid_unprefixed_opcodes_fallback_without_crashing() -> None:
    """Invalid unprefixed opcodes should execute as deterministic fallback NOPs."""
    for opcode in INVALID_UNPREFIXED_OPCODES:
        cpu = make_cpu()
        cpu.pc = 0x0200
        cpu.insert_instruction(bytearray([opcode]))

        elapsed = cpu.cycle()

        assert cpu.pc == 0x0201
        assert elapsed == 4
        assert cpu.instruction.label.startswith("ILLEGAL")

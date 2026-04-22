from gbemu.cpu import CPU
from gbemu.mmu import MMU

SAFE_HL_ADDRESS = 0xC000
REGISTER_ORDER = ("B", "C", "D", "E", "H", "L", "HL", "A")


def make_cpu() -> CPU:
    """Create a CPU with a fresh MMU for tests."""
    return CPU(MMU())


def cycle_instruction(cpu: CPU, *instruction: int) -> int:
    """Load instruction bytes at the current PC and execute one CPU cycle."""
    cpu.insert_instruction(bytearray(instruction))
    return cpu.cycle()


def set_hl_value(cpu: CPU, value: int, address: int = SAFE_HL_ADDRESS) -> None:
    """Set HL to a safe RAM address and write a byte at [HL]."""
    cpu.reg["HL"] = address
    cpu.mmu[address] = value


def set_target_value(
    cpu: CPU,
    target: str,
    value: int,
    address: int = SAFE_HL_ADDRESS,
) -> int:
    """Write a test value to a register target or [HL] and return the backing address."""
    if target == "HL":
        set_hl_value(cpu, value, address)
        return address

    cpu.reg[target] = value
    return address


def get_target_value(cpu: CPU, target: str, address: int = SAFE_HL_ADDRESS) -> int:
    """Read back a register target or the byte stored at [HL]."""
    if target == "HL":
        return cpu.mmu[address]

    return cpu.reg[target]


def verify_flags(cpu: CPU, **expected_flags: int) -> None:
    """Assert only the flags explicitly passed by name."""
    flag_names = {
        "z_flag": "Z",
        "n_flag": "N",
        "h_flag": "H",
        "c_flag": "C",
    }
    unexpected_flags = set(expected_flags) - set(flag_names)
    assert not unexpected_flags, f"Unexpected flag names: {sorted(unexpected_flags)}"

    for expected_name, expected_value in expected_flags.items():
        assert cpu.flags[flag_names[expected_name]] == expected_value

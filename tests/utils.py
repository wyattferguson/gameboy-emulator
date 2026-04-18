from gbemu.cpu import CPU
from gbemu.mmu import MMU

SAFE_HL_ADDRESS = 0xC000


def make_cpu() -> CPU:
    """Create a CPU with a fresh MMU for tests."""
    return CPU(MMU())


def set_hl_value(cpu: CPU, value: int, address: int = SAFE_HL_ADDRESS) -> None:
    """Set HL to a safe RAM address and write a byte at [HL]."""
    cpu.reg["HL"] = address
    cpu.mmu[address] = value


def verify_flags(
    cpu: CPU,
    z_flag: int | None = None,
    n_flag: int | None = None,
    h_flag: int | None = None,
    c_flag: int | None = None,
) -> None:
    if z_flag is not None:
        assert cpu.flags["Z"] == z_flag
    if n_flag is not None:
        assert cpu.flags["N"] == n_flag
    if h_flag is not None:
        assert cpu.flags["H"] == h_flag
    if c_flag is not None:
        assert cpu.flags["C"] == c_flag

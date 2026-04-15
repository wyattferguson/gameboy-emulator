from src.gbemu.cpu import CPU


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

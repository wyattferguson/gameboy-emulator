def hex_to_signed(value: int, bits: int = 8) -> int:
    """Convert an unsigned hex value to its signed representation."""
    mask = (1 << bits) - 1
    value &= mask
    sign_bit = 1 << (bits - 1)
    return value - (1 << bits) if value & sign_bit else value

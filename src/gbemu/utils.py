def hex_to_signed(value: int, bits: int = 8) -> int:
    """Convert an unsigned hex value to its signed representation."""
    mask = (1 << bits) - 1
    value &= mask
    sign_bit = 1 << (bits - 1)
    return value - (1 << bits) if value & sign_bit else value


def to_u16(msb: int, lsb: int) -> int:
    """Build a 16-bit value from MSB and low-byte/address."""
    return ((msb & 0xFF) << 8) | (lsb & 0xFF)


def bit(value: int, bit_index: int) -> int:
    """Get the value of a specific bit in a byte."""
    return (value >> bit_index) & 1

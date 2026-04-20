"""

This module provides small bit/number helpers reused across CPU and rendering logic.

Step-by-step:
1. Convert unsigned immediates to signed two's-complement values.
2. Compose 16-bit words from high/low byte inputs.
3. Extract individual bit values from packed bytes.
4. Keep helper behavior pure and side-effect free.
5. Support concise arithmetic and decoding in core modules.
"""


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

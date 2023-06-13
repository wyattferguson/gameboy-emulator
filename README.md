# :joystick: Gameboy Emulator

# Specifications

## Memory Map

    0000 3FFF 16 KiB ROM bank 00 From cartridge, usually a fixed bank
    4000 7FFF 16 KiB ROM Bank 01~NN From cartridge, switchable bank via mapper(if any)
    8000 9FFF 8 KiB Video RAM(VRAM) In CGB mode, switchable bank 0/1
    A000 BFFF 8 KiB External RAM From cartridge, switchable bank if any
    C000 CFFF 4 KiB Work RAM(WRAM)
    D000 DFFF 4 KiB Work RAM(WRAM) In CGB mode, switchable bank 1~7
    E000 FDFF Mirror of C000~DDFF(ECHO RAM) Nintendo says use of this area is prohibited.
    FE00 FE9F Sprite attribute table(OAM)
    FEA0 FEFF Not Usable Nintendo says use of this area is prohibited
    FF00 FF7F I/O Registers
    FF80 FFFE High RAM(HRAM)
    FFFF FFFF Interrupt Enable register(IE)

## Registers

    A,B,C,D,E,F,H,L - 8bit General Purpose Registers
    AF, BC, HL, DE - 16bit Pair Registers
    SP - Stack Pointer
    PC - Program Counter
    Flags
        Z - Zero
        N - Subtract
        H - Half-carry
        C - Carry

## Register Instructions

    ADDHL (add to HL) - just like ADD except that the target is added to the HL register
    ADC (add with carry) - just like ADD except that the value of the carry flag is also added to the number
    SUB (subtract) - subtract the value stored in a specific register with the value in the A register
    SBC (subtract with carry) - just like ADD except that the value of the carry flag is also subtracted from the number
    AND (logical and) - do a bitwise and on the value in a specific register and the value in the A register
    OR (logical or) - do a bitwise or on the value in a specific register and the value in the A register
    XOR (logical xor) - do a bitwise xor on the value in a specific register and the value in the A register
    CP (compare) - just like SUB except the result of the subtraction is not stored back into A
    INC (increment) - increment the value in a specific register by 1
    DEC (decrement) - decrement the value in a specific register by 1
    CCF (complement carry flag) - toggle the value of the carry flag
    SCF (set carry flag) - set the carry flag to true
    RRA (rotate right A register) - bit rotate A register right through the carry flag
    RLA (rotate left A register) - bit rotate A register left through the carry flag
    RRCA (rotate right A register) - bit rotate A register right (not through the carry flag)
    RRLA (rotate left A register) - bit rotate A register left (not through the carry flag)
    CPL (complement) - toggle every bit of the A register
    BIT (bit test) - test to see if a specific bit of a specific register is set
    RESET (bit reset) - set a specific bit of a specific register to 0
    SET (bit set) - set a specific bit of a specific register to 1
    SRL (shift right logical) - bit shift a specific register right by 1
    RR (rotate right) - bit rotate a specific register right by 1 through the carry flag
    RL (rotate left) - bit rotate a specific register left by 1 through the carry flag
    RRC (rorate right) - bit rotate a specific register right by 1 (not through the carry flag)
    RLC (rorate left) - bit rotate a specific register left by 1 (not through the carry flag)
    SRA (shift right arithmetic) - arithmetic shift a specific register right by 1
    SLA (shift left arithmetic) - arithmetic shift a specific register left by 1
    SWAP (swap nibbles) - switch upper and lower nibble of a specific register

## References

- [CPU opcode referencee - https://rgbds.gbdev.io/docs/v0.6.1/gbz80.7](https://rgbds.gbdev.io/docs/v0.6.1/gbz80.7)
- [Game Boy CPU (SM83) instruction set charts - https://gbdev.io/gb-opcodes/optables/](https://gbdev.io/gb-opcodes/optables/)

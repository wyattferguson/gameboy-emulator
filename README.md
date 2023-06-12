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

## References

- [CPU opcode referencee - https://rgbds.gbdev.io/docs/v0.6.1/gbz80.7](https://rgbds.gbdev.io/docs/v0.6.1/gbz80.7)
- [Game Boy CPU (SM83) instruction set charts - https://gbdev.io/gb-opcodes/optables/](https://gbdev.io/gb-opcodes/optables/)

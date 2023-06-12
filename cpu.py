
from dataclasses import dataclass

from config import BIOS, MEMORY, PROGRAM_START


@dataclass(frozen=True)
class OpCode:
    label: str
    length: bytes
    cycles: int
    flags: tuple
    call: callable
    args: list

    def __str__(self) -> str:
        return f"{self.label} - {self.length} - {self.args}"


class CPU(object):
    def __init__(self, screen):
        self.PC = 0x0  # program counter
        self.SP = 0xFFFE  # stack pointer
        self.mem = bytearray([0] * MEMORY)  # 64kb of memory
        self.mem[0:len(BIOS)] = BIOS  # load system bios

        # 8bit registers
        self.reg = {
            'a': 0,
            'b': 0,
            'c': 0,
            'd': 0,
            'e': 0,
            'f': 0,
            'h': 0,
            'l': 0,
        }

        # Boolean flag registers
        self.flags = {
            'zero': 0,
            'subtract': 0,
            'half_carry': 0,
            'carry': 0
        }

        self.instruction = False

        self.cycles = 0
        self.screen = screen

        self.opcodes = {
            '0xff': OpCode("RST 38H", 1, 16, False, self.RST, [0x38])
        }

    def load_rom(self, rom_file: str):
        '''Load .GB ROM into memory'''
        print(f"Loading Rom - {rom_file}")

        rom_ptr = open(rom_file, 'rb')
        rom = rom_ptr.read()

        self.PC = PROGRAM_START  # program start in memory
        self.mem[self.PC:len(rom)] = rom  # copy rom to ram

        rom_ptr.close()

    def decode(self):
        # All instructions are 2 bytes long and are stored most-significant-byte first
        self.op_code = hex(self.mem[self.PC])
        print(hex(self.PC), self.op_code)
        try:
            self.instruction = self.opcodes[self.op_code]
            print(self.instruction)
            self.instruction.call(*self.instruction.args)
        except Exception as e:
            # stop on op code error
            print("NEW CODE:", e)
            exit()

    def cycle(self):
        '''Execute next CPU cycle'''
        self.decode()
        # self.debug()
        self.PC += 2  # move program counter to next instruction

    def RST(self, addr: int):
        '''Call address vec. This is a shorter and faster equivalent to CALL for suitable values of vec.'''
        print("Cool ADDRE", addr)

    def CALL(self):
        pass

    def LD(self):
        '''Store value'''
        pass

    def HALT(self):
        '''Enter CPU low-power consumption mode until an interrupt occurs. '''
        pass

    def INC(self):
        '''Increment Value'''
        pass

    def DEC(self):
        '''Decrement Value'''
        pass

    def JMP(self):
        '''Jump to Address'''
        pass

    def POP(self):
        pass

    def PUSH(self):
        pass

    def SWAP(self):
        pass

    def RET(self):
        '''Return from subroutine'''
        pass

    def ROTR(self):
        '''Rotate byte'''
        pass

    def SHIFT(self):
        '''Logical bit shift'''
        pass

    def STOP(self):
        '''Enter CPU very low power mode. Also used to switch between double and normal speed CPU modes in GBC.'''
        pass

    def SET(self):
        pass

    def SBC(self):
        '''Subtract and carry'''
        pass

    def SCF(self):
        '''Set Carry Flag.'''
        pass

    def CP(self):
        '''Subtract Values'''
        pass

    def ADD(self):
        pass

    def AND(self):
        '''Bitwise AND'''
        pass

    def OR(self):
        pass

    def XOR(self):
        pass


if __name__ == "__main__":
    cpu = CPU(False)
    cpu.load_rom("./roms/2048.gb")
    cpu.cycle()

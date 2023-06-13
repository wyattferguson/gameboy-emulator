
from config import BIOS, MEMORY, PROGRAM_START
from opcodes import OPCODE_TABLE, OpCode


class CPU(object):
    def __init__(self):
        self.PC: int = 0x0  # program counter
        # self.SP: int = 0xFFFE  # stack pointer
        self.mem = bytearray([0] * MEMORY)  # 64kb of memory
        self.mem[0:len(BIOS)] = BIOS  # load system bios

        # 8bit registers
        self.reg = {
            'A': 0,
            'B': 0,
            'C': 0,
            'D': 0,
            'E': 0,
            'F': 0,
            'H': 0,
            'L': 0,
            'SP': 0xFFFE,  # stack pointer
            'AF': 0,
            'BC': 0,
            'HL': 0,
            'DE': 0,

        }

        # Flag registers
        self.flag = {
            'Z': 0,  # zero
            'N': 0,  # subtract
            'H': 0,  # half-carry
            'C': 0   # carry
        }

        self.instruction: OpCode = False
        self.cycles: int = 0

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
        op_code = hex(self.mem[self.PC])
        try:
            self.instruction = OPCODE_TABLE[op_code]

            print(hex(self.PC), "-", self.instruction)
            getattr(self, self.instruction.call)(*self.instruction.args)
            # self.instruction.call(*self.instruction.args)
        except Exception as e:
            # stop on op code error
            print("NEW CODE:", e)
            exit()

    def cycle(self):
        '''Execute next CPU cycle'''
        self.decode()
        # self.debug()
        self.PC += self.instruction.length  # move program counter to next instruction

    def RST(self, addr: int):
        '''Store PC, move to addr'''
        self.mem[self.reg['SP']] = self.PC
        self.PC = addr - 1

    def CALL(self):
        pass

    def LD(self, register: str, constant: int):
        '''Store value in register'''
        self.reg[register] = constant

    def HALT(self):
        '''Enter CPU low-power consumption mode until an interrupt occurs. '''
        pass

    def INC(self, register: str):
        '''Increment Value'''
        self.reg[register] += 1

    def DEC(self, register):
        '''Decrement Value'''
        self.reg[register] -= 1

    def JMP(self):
        '''Jump to Address'''
        pass

    def POP(self):
        pass

    def PUSH(self):
        pass

    def SWAP(self, reg):
        '''Swap the upper 4 and the lower 4 bits'''
        pass

    def RET(self):
        '''Return from subroutine'''
        self.PC = self.mem[self.SP]
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

    def __str__(self):
        status = (f"\nSP: {hex(self.SP)}({self.SP})   PC: {hex(self.PC)}({self.PC})\n"
                  f"REGS: {self.reg}\n"
                  f"FLAGS: {self.flag}\n"
                  f"CYCLES: {self.cycles}\n"
                  f"INST: {self.instruction}\n"
                  )
        return status


if __name__ == "__main__":
    cpu = CPU()
    cpu.load_rom("./roms/2048.gb")
    while True:
        cpu.cycle()

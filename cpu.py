
from config import BIOS, MEMORY, PROGRAM_START
from opcodes import OPCODE_TABLE, OpCode


class CPU(object):
    def __init__(self):
        self.PC = 0x0  # program counter
        # self.SP = 0xFFFE  # stack pointer
        self.mem = [0] * MEMORY  # 64kb of memory
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
            'AF': 0,
            'BC': 0,
            'HL': 0,
            'DE': 0,
            'SP': 0xFFFE  # stack pointer
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
        self.args: list = []

    def load_rom(self, rom_file: str):
        '''Load .GB ROM into memory'''
        print(f"Loading Rom - {rom_file}")

        rom_ptr = open(rom_file, 'rb')
        rom = rom_ptr.read()

        self.PC = PROGRAM_START  # program start in memory
        self.mem[self.PC:len(rom)] = rom  # copy rom to ram

        # for x in range(100):
        #     addr = self.PC + x
        #     code = self.mem[addr]
        #     print(addr, hex(addr), code)
        #     OPCODE_TABLE[hex(code)]
        # exit()
        rom_ptr.close()

    def fetch(self):
        op_code = hex(self.mem[self.PC])
        try:
            self.instruction = OPCODE_TABLE[op_code]
            print(hex(self.PC), self.PC, "-", self.instruction, "-", op_code)
        except Exception as e:
            print("FETCH:", e)
            exit()

    def decode(self):
        try:
            self.args = self.instruction.args if self.instruction.args else self.instruction.flags
            # if self.instruction.length > 1:
            #     self.args += [self.mem[self.PC + i]
            #                   for i in range(1, self.instruction.length)]
            #     print("ARGS:", self.args)

        except Exception as e:
            print("DECODE:", e)
            exit()

    def execute(self):
        try:
            # print(self.args)
            if self.args:
                getattr(self, self.instruction.call)(*self.args)
            else:
                getattr(self, self.instruction.call)

        except Exception as e:
            print("EXECUTE:", e)
            exit()

    def cycle(self):
        '''Execute next CPU cycle'''
        self.fetch()
        self.decode()
        self.execute()
        # self.debug()

        # move program counter to next instruction
        self.PC += self.instruction.length

    def RST(self, addr: int):
        '''Store PC, move to addr'''
        self.mem[self.reg['SP']] = self.PC
        self.reg['SP'] -= 2
        self.PC = addr

    def NOP(self):
        '''No Operation'''
        pass

    def JR(self, flag: str = False, flag_val: int = False):
        '''Relative Jump to address'''
        if not flag or self.flag[flag] == flag_val:
            offset = self.mem[self.PC + 1]
            self.PC += offset

    def SET(self):
        pass

    def ROT(self):
        '''Rotate byte'''
        pass

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

    def JMP(self, addr: int):
        '''Jump to Address'''
        self.PC = addr

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

    def SHIFT(self):
        '''Logical bit shift'''
        pass

    def STOP(self):
        '''Halt CPU/LCD display until button pressed'''
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
        status = (f"\nSP: {hex(self.reg['SP'])}({self.reg['SP']})   PC: {hex(self.PC)}({self.PC})\n"
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

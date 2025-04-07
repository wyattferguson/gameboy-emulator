from ._config import PROGRAM_START
from ._exceptions import DecodeError, ExecuteError, FetchError
from .opcodes import OPCODE_TABLE, OpCode
from .ram import RAM


class CPU:
    def __init__(self, ram: RAM, debug: bool = False) -> None:
        self.debug = debug
        self.PC = PROGRAM_START  # program counter
        self.SP = 0xFFFE  # stack pointer
        # self.SP = 0xFFFE  # stack pointer
        self.ram = ram

        self.registers = {
            # 8bit registers
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0,
            "E": 0,
            "F": 0,
            "H": 0,
            "L": 0,
            # combined 16bit registers
            "AF": 0,
            "BC": 0,
            "HL": 0,
            "DE": 0,
        }

        # Flag registers
        self.flags = {
            "Z": 0,  # zero
            "N": 0,  # subtract
            "H": 0,  # half-carry
            "C": 0,  # carry
        }

        self.instruction: OpCode = False
        self.cycles: int = 0
        self.args: list = []

    def fetch(self):
        op_code = hex(self.mem[self.PC])
        try:
            self.instruction = OPCODE_TABLE[op_code]
            print(hex(self.PC), self.PC, "-", self.instruction, "-", op_code)
        except Exception as e:
            raise FetchError(
                f"Error fetching instruction: PC = {self.PC} OPCODE = {op_code} - {e}"
            ) from e

    def decode(self):
        try:
            self.args = self.instruction.args if self.instruction.args else self.instruction.flags
            # if self.instruction.length > 1:
            #     self.args += [self.mem[self.PC + i]
            #                   for i in range(1, self.instruction.length)]
            #     print("ARGS:", self.args)

        except Exception as e:
            raise DecodeError(
                f"Error decoding instr: PC={self.PC} SP={self.SP} INSTR={self.instruction} - {e}"
            ) from e

    def execute(self):
        try:
            # print(self.args)
            if self.args:
                getattr(self, self.instruction.call)(*self.args)
            else:
                getattr(self, self.instruction.call)

        except Exception as e:
            raise ExecuteError(f"Error executing: {self.instruction} - {e}") from e

    def cycle(self):
        """Execute next CPU cycle"""
        self.fetch()
        self.decode()
        self.execute()
        # self.debug()

        # move program counter to next instruction
        self.PC += self.instruction.length

    def RST(self, addr: int):
        """Store PC, move to addr"""
        self.mem[self.SP] = self.PC
        self.SP -= 2
        self.PC = addr

    def NOP(self):
        """No Operation"""
        pass

    def JR(self, flag: str = False, flag_val: int = False):
        """Relative Jump to address"""
        if not flag or self.flags[flag] == flag_val:
            offset = self.mem[self.PC + 1]
            self.PC += offset

    def SET(self):
        pass

    def ROT(self):
        """Rotate byte"""
        pass

    def CALL(self):
        pass

    def LD(self, register: str, constant: int):
        """Store value in register"""
        self.registers[register] = constant

    def HALT(self):
        """Enter CPU low-power consumption mode until an interrupt occurs."""
        pass

    def INC(self, register: str):
        """Increment Value"""
        self.registers[register] += 1

    def DEC(self, register):
        """Decrement Value"""
        self.registers[register] -= 1

    def JMP(self, addr: int):
        """Jump to Address"""
        self.PC = addr

    def POP(self):
        pass

    def PUSH(self):
        pass

    def SWAP(self, register: str):
        """Swap the upper 4 and the lower 4 bits"""
        pass

    def RET(self):
        """Return from subroutine"""
        self.PC = self.mem[self.SP]
        pass

    def SHIFT(self):
        """Logical bit shift"""
        pass

    def STOP(self):
        """Halt CPU/LCD display until button pressed"""
        pass

    def SBC(self):
        """Subtract and carry"""
        pass

    def SCF(self):
        """Set Carry Flag."""
        pass

    def CP(self):
        """Subtract Values"""
        pass

    def ADD(self):
        pass

    def AND(self):
        """Bitwise AND"""
        pass

    def OR(self):
        pass

    def XOR(self):
        pass

    def __str__(self):
        return (
            "CPU State:\n"
            f"PC: {hex(self.PC)}({self.PC})\n"
            f"SP: {hex(self.SP)}({self.SP})\n"
            f"REGS: {self.registers}\n"
            f"FLAGS: {self.flags}\n"
            f"CYCLES: {self.cycles}\n"
            f"INST: {self.instruction}\n"
        )

from ._config import PROGRAM_START
from ._exceptions import DecodeError, ExecuteError, FetchError
from .opcodes import OPCODES, OpCode
from .ram import RAM


class CPU:
    def __init__(self, ram: RAM, debug: bool = False) -> None:
        self.debug = debug
        self.PC = PROGRAM_START  # program counter
        self.SP = 0xFFFE  # stack pointer
        self.ram = ram

        self.registers = {
            # 8bit registers
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0,
            "E": 0,
            "F": 0,
            "HL": 0,
        }

        # Flag registers
        self.flags = {
            "Z": 0,  # zero
            "N": 0,  # subtract
            "H": 0,  # half-carry
            "C": 0,  # carry
        }

        self.instruction: OpCode | None = None
        self.cycles: int = 0
        self.args: list | None = None

    def fetch(self):
        op_code = hex(self.ram[self.PC])
        try:
            self.instruction = OPCODES[op_code]
            print("\nFetch: ", hex(self.PC), "-", self.instruction, "-", op_code)
        except Exception:
            # raise FetchError(
            #     f"Error fetching instruction: PC = {self.PC} OPCODE = {op_code} - {e}"
            # ) from e
            print("\nNot Found: ", hex(self.PC), "-", op_code)
            exit()

    def decode(self):
        try:
            self.args = self.instruction.args if self.instruction.args else []
            if self.instruction.length > 1:
                b = bytes([self.ram[self.PC + i] for i in range(1, self.instruction.length)])
                self.args.append(int.from_bytes(b, byteorder="little"))

            print(f"Decoded: {self.instruction}")
        except Exception as e:
            # raise DecodeError(
            #     f"Error decoding instr: PC={self.PC} SP={self.SP} INSTR={self.instruction} - {e}"
            # ) from e
            print("Decode Error: ", e)
            exit()

    def execute(self):
        try:
            print("Execute: ", self.instruction.call)
            if self.args:
                getattr(self, self.instruction.call)(*self.args)
            else:
                getattr(self, self.instruction.call)()

        except Exception as e:
            # raise ExecuteError(f"Error executing: {self.instruction} - {e}") from e
            print("Execute Error: ", e)
            exit()

    def cycle(self):
        """Execute next CPU cycle"""
        self.fetch()
        self.decode()
        self.execute()
        self.cycles += self.instruction.cycles

    def RST(self, addr: int):
        """Store PC, move to addr"""
        self.ram[self.SP] = self.PC
        self.SP -= 2
        self.PC = addr

    def NOP(self):
        """No Operation"""
        self.PC += 1

    def JR(self, offset: int = 0):
        """Relative Jump to address"""
        # if not flag or self.flags[flag] == flag_val:
        self.PC += offset
        self.PC += self.instruction.length

    def SET(self):
        pass

    def ROT(self):
        """Rotate byte"""
        pass

    def CALL(self):
        pass

    def LD_HR(self, register: str):
        """Load H register with value from register"""
        new_hl = (self.registers["HL"] & 0x00FF) | (self.registers[register] << 8)
        self.LD("HL", new_hl)

    def LD_HM(self, register: str):
        """Load H register with value from register"""
        self.LD("HL", register)
        self.registers["HL"] -= 1

    def LD(self, register: str, value: int | str):
        """Store value in register"""
        if isinstance(value, str):
            value = self.registers[value]

        print(f"LD {register} {value}")
        self.registers[register] = value
        self.PC += self.instruction.length

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
        print(f"POP SP: {hex(self.SP)}")
        if len(self.ram) < self.SP:
            self.SP += 2
            self.PC = self.ram[self.SP]
        else:
            raise Exception("Stack underflow")

    def PUSH(self):
        pass

    def SWAP(self, register: str):
        """Swap the upper 4 and the lower 4 bits"""
        pass

    def RET(self):
        """Return from subroutine"""
        self.PC = self.ram[self.SP]

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

    def XOR(self, register_a: int, register_b: int):
        """Bitwise XOR"""
        z = self.registers[register_a] ^ self.registers[register_b]
        self.flags["Z"] = 1 if z == 0 else 0
        self.PC += self.instruction.length

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

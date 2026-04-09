from gbemu.config import PC_START, SP_START
from gbemu.exceptions import DecodeError, ExecuteError, FetchError
from gbemu.opcodes import OPCODES, OpCode
from gbemu.ram import RAM


class CPU:
    def __init__(self, ram: RAM, debug: bool = False) -> None:
        self.debug = debug
        self.PC = PC_START  # program counter
        self.SP = SP_START  # stack pointer
        self.ram = ram

        self.reg = {
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0,
            "E": 0,
            "F": 0,
            "HL": 0,
        }

        self.flags = {
            "Z": 0,  # zero
            "N": 0,  # subtract
            "H": 0,  # half-carry
            "C": 0,  # carry
        }

        self.instruction: OpCode
        self.cycles: int = 0
        self.args: list[int] = []

    def fetch(self) -> None:
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

    def decode(self) -> None:
        try:
            self.args = self.instruction.args or []
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

    def execute(self) -> None:
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

    def cycle(self) -> None:
        """Execute next CPU cycle"""
        self.fetch()
        self.decode()
        self.execute()
        self.cycles += self.instruction.cycles

    def rst(self, addr: int) -> None:
        """Store PC, move to addr"""
        self.ram[self.SP] = self.PC
        self.SP -= 2
        self.PC = addr

    def nop(self) -> None:
        """No Operation"""
        self.PC += 1

    def jr(self, offset: int = 0) -> None:
        """Relative Jump to address"""
        # if not flag or self.flags[flag] == flag_val:
        self.PC += offset
        self.PC += self.instruction.length

    def set(self) -> None:
        pass

    def rot(self) -> None:
        """Rotate byte"""

    def call(self) -> None:
        pass

    def ld_hr(self, register: str) -> None:
        """Load H register with value from register"""
        new_hl = (self.reg["HL"] & 0x00FF) | (self.reg[register] << 8)
        self.ld("HL", new_hl)

    def ld_hm(self, register: str) -> None:
        """Load H register with value from register"""
        self.ld("HL", register)
        self.reg["HL"] -= 1

    def ld(self, register: str, value: int | str) -> None:
        """Store value in register"""
        if isinstance(value, str):
            value = self.reg[value]

        print(f"LD {register} {value}")
        self.reg[register] = value
        self.PC += self.instruction.length

    def halt(self) -> None:
        """Enter CPU low-power consumption mode until an interrupt occurs."""

    def inc(self, register: str) -> None:
        """Increment Value"""
        self.reg[register] += 1

    def dec(self, register) -> None:
        """Decrement Value"""
        self.reg[register] -= 1

    def jmp(self, addr: int) -> None:
        """Jump to Address"""
        self.PC = addr

    def pop(self) -> None:
        print(f"POP SP: {hex(self.SP)}")
        if len(self.ram) < self.SP:
            self.SP += 2
            self.PC = self.ram[self.SP]
        else:
            raise Exception("Stack underflow")

    def push(self) -> None:
        pass

    def swap(self, register: str) -> None:
        """Swap the upper 4 and the lower 4 bits"""

    def ret(self) -> None:
        """Return from subroutine"""
        self.PC = self.ram[self.SP]

    def shift(self) -> None:
        """Logical bit shift"""

    def stop(self) -> None:
        """Halt CPU/LCD display until button pressed"""

    def sbc(self) -> None:
        """Subtract and carry"""

    def scf(self) -> None:
        """Set Carry Flag."""

    def cp(self) -> None:
        """Subtract Values"""

    def add(self) -> None:
        pass

    def and_(self) -> None:
        """Bitwise AND"""

    def or_(self) -> None:
        pass

    def xor(self, register_a: int, register_b: int) -> None:
        """Bitwise XOR"""
        z = self.reg[register_a] ^ self.reg[register_b]
        self.flags["Z"] = 1 if z == 0 else 0
        self.PC += self.instruction.length

    def __str__(self) -> str:
        return (
            "CPU State:\n"
            f"PC: {hex(self.PC)}({self.PC})\n"
            f"SP: {hex(self.SP)}({self.SP})\n"
            f"REGS: {self.reg}\n"
            f"FLAGS: {self.flags}\n"
            f"CYCLES: {self.cycles}\n"
            f"INST: {self.instruction}\n"
        )

import sys

from loguru import logger

from gbemu.config import DEBUG, PC_START, SP_START
from gbemu.exceptions import DecodeError, ExecuteError, FetchError
from gbemu.opcodes import OPCODES, OpCode
from gbemu.ram import RAM


class CPU:
    def __init__(self, ram: RAM) -> None:
        self.debug = DEBUG
        self.pc = PC_START  # program counter
        self.sp = SP_START  # stack pointer
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
        """Fetch instruction from memory at PC."""
        op_code = hex(self.ram[self.pc])
        try:
            self.instruction = OPCODES[op_code]
            logger.debug(f"Fetch: {hex(self.pc)} - {self.instruction}")
        except Exception:
            # raise FetchError(
            #     f"Error fetching instruction: PC = {self.pc} OPCODE = {op_code} - {e}"
            # ) from e
            logger.debug(f"Not Found: {hex(self.pc)} - {op_code}")
            sys.exit()

    def decode(self) -> None:
        """Decode instruction and its arguments."""
        try:
            self.args = self.instruction.args or []
            if self.instruction.length > 1:
                b = bytes([self.ram[self.pc + i] for i in range(1, self.instruction.length)])
                self.args.append(int.from_bytes(b, byteorder="little"))

            logger.debug(f"Decoded: {self.instruction}, {self.args}")
        except Exception as e:
            # raise DecodeError(
            #     f"Error decoding instr: PC={self.pc} SP={self.sp} INSTR={self.instruction} - {e}"
            # ) from e
            logger.debug(f"Decode Error: {e}")
            sys.exit()

    def execute(self) -> None:
        """Run instruction and update PC, SP, registers, and flags."""
        try:
            logger.debug(f"Execute: {self.instruction.call}, {self.args}")
            if self.args:
                getattr(self, self.instruction.call)(*self.args)
            else:
                getattr(self, self.instruction.call)()

        except Exception as e:
            # raise ExecuteError(f"Error executing: {self.instruction} - {e}") from e
            logger.debug(f"Execute Error: {e}")
            sys.exit()

    def insert_instruction(self, instruction: bytearray) -> None:
        """Insert instruction into RAM at current PC."""
        for i, byte in enumerate(instruction):
            self.ram[self.pc + i] = byte

    def cycle(self) -> None:
        """Execute next CPU cycle."""
        self.fetch()
        self.decode()
        self.execute()
        # self.cycles += self.instruction.cycles

    def rst(self, addr: int) -> None:
        """Store PC, move to addr."""
        self.ram[self.sp] = self.pc
        self.sp -= 2
        self.pc = addr

    def nop(self) -> None:
        """No Operation."""
        self.pc += 1

    def jr(self, offset: int = 0) -> None:
        """Relative Jump to address."""
        # if not flag or self.flags[flag] == flag_val:
        self.pc += offset
        self.pc += self.instruction.length

    def set(self) -> None:
        pass

    def rot(self) -> None:
        """Rotate byte."""

    def call(self) -> None:
        pass

    def ld_hr(self, register: str) -> None:
        """Load H register with value from register."""
        new_hl = (self.reg["HL"] & 0x00FF) | (self.reg[register] << 8)
        self.ld("HL", new_hl)

    def ld_hm(self, register: str) -> None:
        """Load H register with value from register."""
        self.ld("HL", register)
        self.reg["HL"] -= 1

    def ld(self, register: str, value: int | str) -> None:
        """Store value in register."""
        if isinstance(value, str):
            value = self.reg[value]

        logger.debug(f"LD {register} {hex(value)}({value})")
        self.reg[register] = value
        self.pc += self.instruction.length

    def halt(self) -> None:
        """Enter CPU low-power consumption mode until an interrupt occurs."""

    def inc(self, register: str) -> None:
        """Increment Value."""
        self.reg[register] += 1

    def dec(self, register) -> None:
        """Decrement Value."""
        self.reg[register] -= 1

    def jmp(self, addr: int) -> None:
        """Jump to Address."""
        self.pc = addr

    def pop(self) -> None:
        logger.debug(f"POP SP: {hex(self.sp)}({self.sp})")
        if len(self.ram) < self.sp:
            self.sp += 2
            self.pc = self.ram[self.sp]
        else:
            raise Exception("Stack underflow")

    def push(self) -> None:
        pass

    def swap(self, register: str) -> None:
        """Swap the upper 4 and the lower 4 bits."""

    def ret(self) -> None:
        """Return from subroutine."""
        self.pc = self.ram[self.sp]

    def shift(self) -> None:
        """Logical bit shift."""

    def stop(self) -> None:
        """Halt CPU/LCD display until button pressed."""

    def sbc(self) -> None:
        """Subtract and carry."""

    def scf(self) -> None:
        """Set Carry Flag."""

    def cp(self) -> None:
        """Subtract Values."""

    def add(self) -> None:
        pass

    def and_(self) -> None:
        """Bitwise AND."""

    def or_(self) -> None:
        pass

    def xor(self, register_a: int, register_b: int) -> None:
        """Bitwise XOR."""
        z = self.reg[register_a] ^ self.reg[register_b]
        self.flags["Z"] = 1 if z == 0 else 0
        self.pc += self.instruction.length

    def __str__(self) -> str:
        return (
            "CPU State:\n"
            f"PC: {hex(self.pc)}({self.pc})\n"
            f"SP: {hex(self.sp)}({self.sp})\n"
            f"REGS: {self.reg}\n"
            f"FLAGS: {self.flags}\n"
            f"CYCLES: {self.cycles}\n"
            f"INST: {self.instruction}\n"
        )

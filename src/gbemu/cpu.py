import re
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
            "H": 0,
            "L": 0,
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

    def hl(self) -> int:
        """Get value of HL register pair."""
        return (self.reg["H"] << 8) + self.reg["L"]

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
        self.pc += self.instruction.length

    def nop(self) -> None:
        """No Operation."""
        self.pc += self.instruction.length

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

    def ld_hl(self, reg: str) -> None:
        """Load value from memory at address in HL into register."""
        self.ld(reg, self.ram[self.hl()])

    def ld_hl_r(self, reg: str) -> None:
        """Load value from register into memory at address in HL."""
        self.ram[self.hl()] = self.reg[reg]

    def halt(self) -> None:
        """Enter CPU low-power consumption mode until an interrupt occurs."""

    def add_reg(self, register_a: str, register_b: str, with_carry: bool = False) -> None:
        self.add(register_a, self.reg[register_b], with_carry=with_carry)

    def add_hl(self, register: str, with_carry: bool = False) -> None:
        self.add(register, self.ram[self.hl()], with_carry=with_carry)

    def add(self, dest: str, value: int, with_carry: bool = False) -> None:
        carry = self.flags["C"] if with_carry else 0
        total = self.reg[dest] + value + carry
        self.flags["Z"] = 1 if (total & 0xFF) == 0 else 0
        self.flags["N"] = 0
        self.flags["H"] = 1 if (self.reg[dest] & 0xF) + (value & 0xF) + carry > 0xF else 0
        self.flags["C"] = 1 if total > 0xFF else 0
        self.reg[dest] = total & 0xFF

    def sub_reg(self, register_a: str, register_b: str, with_carry: bool = False) -> None:
        self.sub(register_a, self.reg[register_b], with_carry=with_carry)

    def sub_hl(self, register: str, with_carry: bool = False) -> None:
        self.sub(register, self.ram[self.hl()], with_carry=with_carry)

    def sub(self, dest: str, value: int, with_carry: bool = False) -> None:
        carry = self.flags["C"] if with_carry else 0
        total = self.reg[dest] - value - carry
        self.flags["Z"] = 1 if (total & 0xFF) == 0 else 0
        self.flags["N"] = 1
        self.flags["H"] = 1 if (self.reg[dest] & 0xF) - (value & 0xF) - carry < 0 else 0
        self.flags["C"] = 1 if total < 0 else 0
        self.reg[dest] = total & 0xFF

    # def inc(self, register: str) -> None:
    #     """Increment Value."""
    #     self.reg[register] += 1

    # def dec(self, register: str) -> None:
    #     """Decrement Value."""
    #     self.reg[register] -= 1

    # def jmp(self, addr: int) -> None:
    #     """Jump to Address."""
    #     self.pc = addr

    # def pop(self) -> None:
    #     logger.debug(f"POP SP: {hex(self.sp)}({self.sp})")
    #     if len(self.ram) < self.sp:
    #         self.sp += 2
    #         self.pc = self.ram[self.sp]
    #     else:
    #         raise Exception("Stack underflow")

    # def xor(self, register_a: int, register_b: int) -> None:
    #     """Bitwise XOR."""
    #     z = self.reg[register_a] ^ self.reg[register_b]
    #     self.flags["Z"] = 1 if z == 0 else 0
    #     self.pc += self.instruction.length

    # def rst(self, addr: int) -> None:
    #     """Store PC, move to addr."""
    #     self.ram[self.sp] = self.pc
    #     self.sp -= 2
    #     self.pc = addr

    # def jr(self, offset: int = 0) -> None:
    #     """Relative Jump to address."""
    #     # if not flag or self.flags[flag] == flag_val:
    #     self.pc += offset
    #     self.pc += self.instruction.length

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

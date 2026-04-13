import sys

from loguru import logger

from gbemu.config import DEBUG, PC_START, SP_START
from gbemu.exceptions import DecodeError, ExecuteError, FetchError
from gbemu.mmu import MMU
from gbemu.opcodes import OPCODES, OpCode


class CPU:
    def __init__(self, mmu: MMU) -> None:
        self.debug = DEBUG
        self.pc = PC_START  # program counter
        self.sp = SP_START  # stack pointer
        self.mmu = mmu

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
            "Z": 0,
            "N": 0,  # subtract
            "H": 0,  # half-carry
            "C": 0,  # carry
        }

        self.instruction: OpCode
        self.cycles: int = 0
        self.args: list[int] = []

    @property
    def hl(self) -> int:
        """Get value of HL register pair."""
        return (self.reg["H"] << 8) + self.reg["L"]

    @hl.setter
    def hl(self, value: int) -> None:
        """Set value of HL register pair."""
        self.reg["H"] = (value >> 8) & 0xFF
        self.reg["L"] = value & 0xFF

    def fetch(self) -> None:
        """Fetch instruction from memory at PC."""
        op_code = hex(self.mmu[self.pc])
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
                b = bytes([self.mmu[self.pc + i] for i in range(1, self.instruction.length)])
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
            if self.instruction.flags:
                for flag, value in self.instruction.flags.items():
                    self.flags[flag] = value
            if self.args:
                getattr(self, self.instruction.call)(*self.args)
            else:
                getattr(self, self.instruction.call)()

        except Exception as e:
            # raise ExecuteError(f"Error executing: {self.instruction} - {e}") from e
            logger.debug(f"Execute Error: {e}")
            sys.exit()

    def insert_instruction(self, instruction: bytearray) -> None:
        """Insert instruction into MMU at current PC. Used for Testing."""
        for i, byte in enumerate(instruction):
            self.mmu[self.pc + i] = byte

    def cycle(self) -> None:
        """Execute next CPU cycle."""
        self.fetch()
        self.decode()
        self.execute()
        self.pc += self.instruction.length

    def nop(self) -> None:
        """No Operation."""
        self.pc += self.instruction.length

    def ld(self, register_a: str, register_b: int | str) -> None:
        """Store value in register."""
        if isinstance(register_b, str):
            register_b = self.reg[register_b]

        self.reg[register_a] = register_b

    def ld_hl(self, reg: str) -> None:
        """Load value from memory at address in HL into register."""
        self.ld(reg, self.mmu[self.hl])

    def ld_hl_reg(self, reg: str) -> None:
        """Load value from register into memory at address in HL."""
        self.mmu[self.hl] = self.reg[reg]

    def halt(self) -> None:
        """Enter CPU low-power consumption mode until an interrupt occurs."""

    def add(self, dest: str, source: str, with_carry: bool = False) -> None:
        """Add value from source to dest, optionally with carry."""
        carry: int = self.flags["C"] if with_carry else 0
        value: int = self.mmu[self.hl] if source == "HL" else self.reg[source]
        total: int = self.reg[dest] + value + carry
        self.flags["Z"] = 1 if (total & 0xFF) == 0 else 0
        self.flags["H"] = 1 if (self.reg[dest] & 0xF) + (value & 0xF) + carry > 0xF else 0
        self.flags["C"] = 1 if total > 0xFF else 0
        self.reg[dest] = total & 0xFF

    def sub(self, register_a: str, register_b: str, with_carry: bool = False) -> None:
        """Subtract value from source to dest, optionally with carry."""
        carry: int = self.flags["C"] if with_carry else 0
        value: int = self.mmu[self.hl] if register_b == "HL" else self.reg[register_b]
        result: int = self.reg[register_a] - value - carry
        self._set_sub_flags(result, self.reg[register_a], value, carry)
        self.reg[register_a] = result & 0xFF

    def bitwise(self, operation: str, register_a: str, register_b: str) -> None:
        """Perform bitwise operation (AND, XOR, OR)."""
        value: int = self.mmu[self.hl] if register_b == "HL" else self.reg[register_b]

        if operation == "AND":
            self.reg[register_a] &= value
        elif operation == "XOR":
            self.reg[register_a] ^= value
        elif operation == "OR":
            self.reg[register_a] |= value

        self.flags["Z"] = 1 if self.reg[register_a] == 0 else 0

    def cp(self, register_a: str, register_b: str) -> None:
        """Compare registers."""
        value: int = self.mmu[self.hl] if register_b == "HL" else self.reg[register_b]
        result: int = self.reg[register_a] - value
        self._set_sub_flags(result, self.reg[register_a], value)

    def _set_sub_flags(self, result: int, a: int, b: int, carry: int = 0) -> None:
        """Set flags for subtraction operations."""
        self.flags["Z"] = 1 if (result & 0xFF) == 0 else 0
        self.flags["H"] = 1 if (a & 0xF) - (b & 0xF) - carry < 0 else 0
        self.flags["C"] = 1 if result < 0 else 0

    def inc(self, register: str) -> None:
        """Increment Value."""
        self.reg[register] += 1

    def dec(self, register: str) -> None:
        """Decrement Value."""
        self.reg[register] -= 1

    def jmp(self, addr: int) -> None:
        """Jump to Address."""
        self.pc = addr

    def pop(self) -> None:
        logger.debug(f"POP SP: {hex(self.sp)}({self.sp})")
        if len(self.mmu) < self.sp:
            self.sp += 2
            self.pc = self.mmu[self.sp]
        else:
            raise Exception("Stack underflow")

    # def rst(self, addr: int) -> None:
    #     """Store PC, move to addr."""
    #     self.mmu[self.sp] = self.pc
    #     self.sp -= 2
    #     self.pc = addr

    def jr(self, offset: int = 0) -> None:
        """Relative Jump to address."""
        # if not flag or self.flags[flag] == flag_val:
        self.pc += offset
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

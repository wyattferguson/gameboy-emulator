import sys

from loguru import logger

from gbemu.config import DEBUG, PC_START, SP_START
from gbemu.ctypes import Bitwise, CallableDict
from gbemu.exceptions import DecodeError, ExecuteError, FetchError
from gbemu.mmu import MMU
from gbemu.opcodes import OPCODES, OpCode
from gbemu.utils import hex_to_signed


class CPU:
    """GB CPU."""

    def __init__(self, mmu: MMU) -> None:
        self.debug: bool = DEBUG
        self.pc: int = PC_START  # program counter
        self.mmu: MMU = mmu

        self.reg = CallableDict(
            {
                "A": 0,
                "B": 0,
                "C": 0,
                "D": 0,
                "E": 0,
                "F": 0,
                "H": 0,
                "L": 0,
                "HL": lambda: self.get_reg16("H", "L"),
                "BC": lambda: self.get_reg16("B", "C"),
                "DE": lambda: self.get_reg16("D", "E"),
                "AF": lambda: self.get_reg16("A", "F"),
                "SP": SP_START,  # stack pointer
            },
        )

        self.flags = {
            "Z": 0,  # zero
            "N": 0,  # subtract
            "H": 0,  # half-carry
            "C": 0,  # carry
        }

        self.instruction: OpCode
        self.cycles: int = 0
        self.args: list[int]

    def fetch(self) -> None:
        """Fetch instruction from memory at PC."""
        op_code = hex(self.mmu[self.pc])  # ty:ignore[invalid-argument-type]
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
            self.args = list(self.instruction.args or [])  # ty:ignore[invalid-assignment]
            if self.instruction.length > 1:
                b = bytes([self.mmu[self.pc + i] for i in range(1, self.instruction.length)])  # ty:ignore[invalid-argument-type]
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

            # Set flags with static values from instruction definition
            if self.instruction.flags:
                for flag, value in self.instruction.flags.items():
                    self.flags[flag] = value

            # Execute instruction logic
            if self.instruction.call:
                getattr(self, self.instruction.call)(*self.args)

        except Exception as e:
            # raise ExecuteError(f"Error executing: {self.instruction} - {e}") from e
            logger.debug(f"Execute Error: {e}")
            sys.exit()

    def insert_instruction(self, instruction: bytearray) -> None:
        """Insert instruction into MMU at current PC. Used for Testing."""
        for i, byte in enumerate(instruction):
            self.mmu[self.pc + i] = byte

    def get_reg16(self, register_a: str, register_b: str) -> int:
        """Get value of 16-bit register pair."""
        return (self.reg[register_a] << 8) + self.reg[register_b]

    def cycle(self) -> None:
        """Execute next CPU cycle."""
        self.fetch()
        self.decode()
        self.execute()
        if self.instruction.pc_inc:
            self.pc += self.instruction.length

    def nop(self) -> None:
        """No Operation."""

    def ld(self, register: str, src_location: int | str) -> None:
        """Load value in register."""
        if isinstance(src_location, str):
            src_location: int = self.reg[src_location]

        self.reg[register] = src_location

    def ld_reg16(self, reg: str, src_register: str) -> None:
        """Load value from memory from 16bit address into register."""
        self.ld(reg, self.mmu[self.reg[src_register]])  # ty:ignore[invalid-argument-type]

    def ld_mem(self, dest_register: str, src: str | int) -> None:
        """Load value into memory."""
        if isinstance(src, str):
            src: int = self.reg[src]
        self.mmu[self.reg[dest_register]] = src

    def ld_a_hl_mod(self, mod: int = 1, from_register: bool = False) -> None:
        """Load value into memory at HL or reg A, then increment or decrement HL."""
        if from_register:
            self.mmu[self.reg["HL"]] = self.reg["A"]
        else:
            self.reg["A"] = self.get_stored_value("HL")
        self.reg["HL"] += mod

    def ld_mem_sp(self, address: int) -> None:
        """Load SP into memory at immediate 16-bit address (little-endian)."""
        self.mmu[address] = self.reg["SP"] & 0xFF
        self.mmu[address + 1] = (self.reg["SP"] >> 8) & 0xFF

    def halt(self) -> None:
        """Enter CPU low-power consumption mode until an interrupt occurs."""

    def stop(self) -> None:
        """Halt CPU and LCD until button pressed. Used for power saving."""

    def add(self, dest_register: str, src_register: str, with_carry: bool = False) -> None:
        """Add value from source to dest, optionally with carry."""
        carry: int = self.flags["C"] if with_carry else 0
        value: int = self.get_stored_value(src_register)
        total: int = self.reg[dest_register] + value + carry
        self.flags["Z"] = 1 if (total & 0xFF) == 0 else 0
        self.flags["H"] = 1 if (self.reg[dest_register] & 0xF) + (value & 0xF) + carry > 0xF else 0
        self.flags["C"] = 1 if total > 0xFF else 0
        self.reg[dest_register] = total & 0xFF

    def add16(self, dest_register: str, src_register: str) -> None:
        """Add 16-bit pair registers."""
        value: int = self.reg[src_register]
        total: int = self.reg[dest_register] + value
        self.flags["H"] = 1 if (self.reg[dest_register] & 0xFFF) + (value & 0xFFF) > 0xFFF else 0
        self.flags["C"] = 1 if total > 0xFFFF else 0
        self.reg[dest_register] = total & 0xFFFF

    def sub(self, dest_register: str, src_register: str, with_carry: bool = False) -> None:
        """Subtract value from source to dest, optionally with carry."""
        carry: int = self.flags["C"] if with_carry else 0
        value: int = self.get_stored_value(src_register)
        result: int = self.reg[dest_register] - value - carry
        self._set_sub_flags(result, self.reg[dest_register], value, carry)
        self.reg[dest_register] = result & 0xFF

    def bitwise(self, operation: Bitwise, dest_register: str, src_register: str) -> None:
        """Perform bitwise operation (AND, XOR, OR)."""
        value: int = self.get_stored_value(src_register)

        if operation == Bitwise.AND:
            self.reg[dest_register] &= value
        elif operation == Bitwise.XOR:
            self.reg[dest_register] ^= value
        elif operation == Bitwise.OR:
            self.reg[dest_register] |= value

        self.flags["Z"] = 1 if self.reg[dest_register] == 0 else 0

    def cp(self, dest_register: str, src_register: str) -> None:
        """Compare registers."""
        value: int = self.get_stored_value(src_register)
        result: int = self.reg[dest_register] - value
        self._set_sub_flags(result, self.reg[dest_register], value)

    def get_stored_value(self, register: str, from_memory: bool = False) -> int:
        """Get value stored in register or memory."""
        if register == "HL" or from_memory:
            return self.mmu[self.reg[register]]  # ty:ignore[invalid-return-type]
        return self.reg[register]

    def _set_sub_flags(self, result: int, a: int, b: int, carry: int = 0) -> None:
        """Set flags for subtraction operations."""
        self.flags["Z"] = 1 if (result & 0xFF) == 0 else 0
        self.flags["H"] = 1 if (a & 0xF) - (b & 0xF) - carry < 0 else 0
        self.flags["C"] = 1 if result < 0 else 0

    def inc(self, register: str) -> None:
        """Increment register."""
        self.reg[register] += 1

        # Only set flags for 8-bit registers
        if len(register) == 1:
            self._set_inc_dec_flags(self.reg[register], self.reg[register])

    def inc_mem(self, register: str) -> None:
        """Increment value at address in HL."""
        addr: int = self.reg[register]
        self.mmu[addr] += 1
        self._set_inc_dec_flags(self.mmu[addr], self.mmu[addr])  # ty:ignore[invalid-argument-type]

    def dec_mem(self, register: str) -> None:
        """Decrement value at address in HL."""
        addr: int = self.reg[register]
        value: int = self.mmu[addr]  # ty:ignore[invalid-assignment]
        self.mmu[addr] = value - 1
        self._set_inc_dec_flags(self.mmu[addr], value)  # ty:ignore[invalid-argument-type]

    def dec(self, register: str) -> None:
        """Decrement register or HL address."""
        self.reg[register] -= 1

        # Only set flags for 8-bit registers
        if len(register) == 1:
            self._set_inc_dec_flags(self.reg[register], self.reg[register])

    def _set_inc_dec_flags(self, result: int, value: int) -> None:
        """Set flags for INC and DEC operations."""
        self.flags["Z"] = 1 if result == 0 else 0
        self.flags["H"] = 1 if (value & 0xF) == 0 else 0

    def rotate(
        self,
        register: str,
        left: bool,
        circular: bool = False,
        insert_carry: bool = False,
    ) -> None:
        """Rotate bits in register left or right."""
        value: int = self.reg[register]
        old_carry: int = self.flags["C"]
        new_carry: int = (value >> 7) & 0x1 if left else value & 0x1

        shifted: int = new_carry if left else new_carry << 7
        if insert_carry:
            shifted = old_carry if left else old_carry << 7
        elif not circular:
            shifted = 0

        if left:
            self.reg[register] = ((value << 1) | shifted) & 0xFF
        else:
            self.reg[register] = (value >> 1) | shifted

        self.flags["C"] = new_carry

    def jmp(self, addr: int) -> None:
        """Jump to Address."""
        self.pc = addr

    def pop(self) -> int:
        """Pop value from stack."""
        value: int = self.mmu[self.reg["SP"]]  # ty:ignore[invalid-assignment]
        self.reg["SP"] -= 1
        return value

    def push(self, value: int) -> None:
        """Push value onto stack."""
        self.reg["SP"] += 1
        self.mmu[self.reg["SP"]] = value

    # def rst(self, addr: int) -> None:
    #     """Store PC, move to addr."""
    #     self.mmu[self.sp] = self.pc
    #     self.sp -= 2
    #     self.pc = addr

    def cpl(self, register: str) -> None:
        """Complement A register."""
        self.reg[register] ^= 0xFF

    def ccf(self) -> None:
        """Complement Carry Flag."""
        self.flags["C"] ^= 1

    def daa(self) -> None:
        """Decimal Adjust Accumulator. Modify A register to BCD representation."""
        a: int = self.reg["A"]
        adjust: int = 0

        # Adjust lower nibble if H flag is set or if value is > 9
        if self.flags["H"] or (a & 0xF) > 9:
            adjust |= 0x6

        # Adjust upper nibble if C flag is set or if value is > 0x99
        if self.flags["C"] or a > 0x99:
            adjust |= 0x60

        a: int = a - adjust & 0xFF if self.flags["N"] else a + adjust & 0xFF

        self.reg["A"] = a
        self.flags["Z"] = 1 if a == 0 else 0
        if adjust >= 0x60:
            self.flags["C"] = 1

    def jrc(self, flag: str, condition: int, offset: int) -> None:
        """Relative Jump to address if condition is met."""
        if self.flags[flag] == condition:
            self.jr(offset)

    def jr(self, offset: int = 0) -> None:
        """Relative Jump to address."""
        signed_offset: int = hex_to_signed(offset, 8)
        self.pc += signed_offset

    def ret(self, condition_flag: str | None = None, condition_value: int | None = None) -> None:
        """Return from subroutine, optionally if condition is met."""
        if condition_flag is None or self.flags[condition_flag] == condition_value:
            self.pc = self.pop()

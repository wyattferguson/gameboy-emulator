from typing import Any

from gbemu.config import (
    CPU_INVALID_UNPREFIXED_OPCODES,
    DEBUG,
    M_INTERRUPT_ENABLE,
    M_INTERRUPT_FLAG,
    SP_START,
)
from gbemu.ctypes import Bitwise, CallableDict
from gbemu.logger import logger
from gbemu.mmu import MMU
from gbemu.opcodes import CB_PREFIXED, OPCODES, OpCode
from gbemu.timer import Timer
from gbemu.utils import hex_to_signed, to_u16

OPCODES_BY_BYTE = {int(key, 16): value for key, value in OPCODES.items()}
CB_PREFIXED_BY_BYTE = {int(key, 16): value for key, value in CB_PREFIXED.items()}


class CPU:
    """GB CPU."""

    def __init__(self, mmu: MMU) -> None:
        self.debug: bool = DEBUG
        self.pc = 0x0000
        self.mmu: MMU = mmu
        self.interrupts: bool = False
        self._ime_delay: int = 0
        self.halted: bool = False
        self.cb_prefixed: bool = False
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
                "HL": lambda: self.reg16("H", "L"),
                "BC": lambda: self.reg16("B", "C"),
                "DE": lambda: self.reg16("D", "E"),
                "AF": lambda: self.reg16("A", "F"),
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
        self._cycle_adjust: int = 0
        self.args: list[int]
        self._illegal_opcode_log_once: set[tuple[int, int]] = set()
        self._call_cache: dict[str, Any] = {}
        self._timer = Timer()

    def fetch(self) -> None:
        """Fetch instruction from memory at PC."""
        op_value = self.mmu[self.pc]

        if op_value == 0xCB:
            cb_opcode = self.fetch_cb_prefixed()
            instruction = CB_PREFIXED_BY_BYTE.get(cb_opcode)
            self.instruction = (
                instruction
                if instruction is not None
                else self._illegal_opcode(cb_opcode, cb_prefixed=True)
            )
            self.cb_prefixed = True
        else:
            instruction = OPCODES_BY_BYTE.get(op_value)
            self.instruction = (
                instruction
                if instruction is not None
                else self._illegal_opcode(op_value, cb_prefixed=False)
            )

        if self.debug:
            logger.debug(f"Fetch: {hex(self.pc)} - {self.instruction}")

    def _illegal_opcode(self, op_code: int, cb_prefixed: bool = False) -> OpCode:
        """Provide a deterministic fallback for opcodes missing from decode tables."""
        prefix = "CB " if cb_prefixed else ""
        op_hex = f"0x{op_code:02x}"
        instruction = OpCode(f"ILLEGAL {prefix}{op_hex}", 1, 4, "nop")

        key = (self.pc, op_code)
        if key not in self._illegal_opcode_log_once:
            self._illegal_opcode_log_once.add(key)
            level = "warning" if op_code in CPU_INVALID_UNPREFIXED_OPCODES else "error"
            log = logger.warning if level == "warning" else logger.error
            log(f"Illegal opcode {prefix}{op_hex} at PC {hex(self.pc)}; falling back to NOP")

        return instruction

    def fetch_cb_prefixed(self) -> int:
        """Fetch CB-prefixed instruction."""
        return self.mmu[(self.pc + 1) & 0xFFFF]

    def decode(self) -> None:
        """Decode instruction and its arguments."""
        try:
            base_args = self.instruction.args
            self.args = list(base_args or [])  # ty:ignore[invalid-assignment]
            if self.instruction.length > 1 and not self.cb_prefixed:
                if self.instruction.length == 2:
                    immediate = self.mmu[(self.pc + 1) & 0xFFFF]
                elif self.instruction.length == 3:
                    low = self.mmu[(self.pc + 1) & 0xFFFF]
                    high = self.mmu[(self.pc + 2) & 0xFFFF]
                    immediate = (high << 8) | low
                else:
                    b = bytes(
                        self.mmu[(self.pc + i) & 0xFFFF] for i in range(1, self.instruction.length)
                    )
                    immediate = int.from_bytes(b, byteorder="little")
                self.args.append(immediate)

            if self.debug:
                logger.debug(f"Decoded: {self.instruction}, {self.args}")
        except Exception as e:
            logger.exception(
                f"Decode - PC: {self.pc}({hex(self.pc)}) OP: {hex(self.mmu[self.pc])}",
                f"INSTR: {self.instruction} - {e}",
            )

    def execute(self) -> None:
        """Run instruction and update PC, SP, registers, and flags."""
        try:
            if self.debug:
                logger.debug(f"Execute: {self.instruction.call}, {self.args}")

            # Set flags with static values from instruction definition
            if self.instruction.flags:
                for flag, value in self.instruction.flags.items():
                    self.flags[flag] = value

            # Execute instruction logic
            if self.instruction.call:
                call_name = self.instruction.call
                method_obj: Any = self._call_cache.get(call_name)
                if method_obj is None:
                    method_obj = getattr(self, call_name)
                    self._call_cache[call_name] = method_obj
                method_obj(*self.args)

        except Exception as e:
            logger.exception(
                f"Execute - PC: {self.pc}({hex(self.pc)}) MEM: {hex(self.mmu[self.pc])}",
                f"INSTR: {self.instruction} - {e}",
            )

    def insert_instruction(self, instruction: bytearray) -> None:
        """Insert instruction into MMU at current PC. Used for Testing."""
        for i, byte in enumerate(instruction):
            self.mmu[self.pc + i] = byte

    def reg16(self, register_a: str, register_b: str) -> int:
        """Get value of 16-bit register pair."""
        low = self.reg[register_b]
        if register_b == "F":
            low = (
                ((self.flags["Z"] & 0x1) << 7)
                | ((self.flags["N"] & 0x1) << 6)
                | ((self.flags["H"] & 0x1) << 5)
                | ((self.flags["C"] & 0x1) << 4)
            )
        return to_u16(self.reg[register_a], low)

    def cycle(self) -> int:
        """Execute one instruction and return elapsed CPU cycles."""
        pending_interrupts = self._pending_interrupts()

        # HALT keeps CPU idle until an interrupt becomes pending.
        if self.halted and pending_interrupts == 0:
            return self._commit_cycles(4)
        if self.halted and pending_interrupts != 0:
            self.halted = False

        if self._service_interrupt():
            return self._commit_cycles(20)

        self.fetch()
        self.decode()
        self._cycle_adjust = 0
        self.execute()
        self.cb_prefixed = False
        if self.instruction.pc_inc:
            self.pc = (self.pc + self.instruction.length) & 0xFFFF

        if self._ime_delay > 0:
            self._ime_delay -= 1
            if self._ime_delay == 0:
                self.interrupts = True

        # Keep a running total and return this instruction's timing to drive other hardware.
        elapsed = self.instruction.cycles + self._cycle_adjust
        return self._commit_cycles(elapsed)

    def _commit_cycles(self, elapsed: int) -> int:
        """Tick timer and aggregate elapsed cycles for one CPU step."""
        self._timer.tick(self.mmu.memory, elapsed)
        self.cycles += elapsed
        return elapsed

    def _pending_interrupts(self) -> int:
        """Return bitmask of currently pending and enabled interrupts (bits 0..4)."""
        return self.mmu[M_INTERRUPT_FLAG] & self.mmu[M_INTERRUPT_ENABLE] & 0x1F

    def _service_interrupt(self) -> bool:
        """Service highest-priority interrupt when IME is set."""
        pending = self._pending_interrupts()
        if pending == 0 or not self.interrupts:
            return False

        # IME is cleared when jumping to ISR.
        self.interrupts = False
        self._ime_delay = 0

        vectors = [0x40, 0x48, 0x50, 0x58, 0x60]
        for bit_index, vector in enumerate(vectors):
            mask = 1 << bit_index
            if pending & mask:
                self.mmu[M_INTERRUPT_FLAG] &= (~mask) & 0xFF
                self.push(self.pc)
                self.pc = vector
                return True
        return False

    def nop(self) -> None:
        """No Operation."""

    def get_reg(self, register: str | int) -> int:
        """Get value of 8-bit register."""
        return self.reg[register] if isinstance(register, str) else register

    def ld(self, register: str, src: int | str) -> None:
        """Load value in register."""
        self.reg[register] = self.get_reg(src)

    def ld_reg16(self, reg: str, src_register: str | int) -> None:
        """Load value from memory from a register-pair address or immediate address."""
        address = self.reg[src_register] if isinstance(src_register, str) else src_register
        self.ld(reg, self.mmu[address])

    def ld_mem(self, dest_register: str, src: str | int) -> None:
        """Load value into memory."""
        self.mmu[self.reg[dest_register]] = self.get_reg(src)

    def ldh_reg(self, register: str, offset: int | str) -> None:
        """Load value into register from memory at address 0xFF00 + offset."""
        offset = self.get_reg(offset)
        self.reg[register] = self.mmu[0xFF00 + offset]

    def ldh_mem(self, register: str, offset: int | str) -> None:
        """Load value from register into memory at address 0xFF00 + offset."""
        offset = self.get_reg(offset)
        self.mmu[0xFF00 + offset] = self.reg[register]

    def ld_mem16(self, register: str, src: int) -> None:
        """Load register value into memory at 16-bit address."""
        self.mmu[src] = self.reg[register]

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

    def _push_u16(self, value: int) -> None:
        """Push a 16-bit value onto the stack (stack grows downward)."""
        value &= 0xFFFF
        self.reg["SP"] = (self.reg["SP"] - 1) & 0xFFFF
        self.mmu[self.reg["SP"]] = (value >> 8) & 0xFF
        self.reg["SP"] = (self.reg["SP"] - 1) & 0xFFFF
        self.mmu[self.reg["SP"]] = value & 0xFF

    def _pop_u16(self) -> int:
        """Pop a 16-bit value from the stack (little-endian)."""
        low = self.mmu[self.reg["SP"]]
        self.reg["SP"] = (self.reg["SP"] + 1) & 0xFFFF
        high = self.mmu[self.reg["SP"]]
        self.reg["SP"] = (self.reg["SP"] + 1) & 0xFFFF
        return to_u16(high, low)

    def halt(self) -> None:
        """Enter CPU low-power consumption mode until an interrupt occurs."""
        self.halted = True

    def stop(self, d8: int = 0) -> None:
        """Halt CPU and LCD until button pressed. Used for power saving."""
        _ = d8
        self.stopped = True

    def add(
        self,
        dest_register: str,
        register: str | bool,
        with_carry: bool | int = False,
    ) -> None:
        """Add value from source to dest, optionally with carry."""
        with_carry_flag, value = self._resolve_operand(register, with_carry)
        carry: int = self.flags["C"] if with_carry_flag else 0
        total: int = self.reg[dest_register] + value + carry
        self._set_add_flags(total, self.reg[dest_register], value, carry)
        self.reg[dest_register] = total & 0xFF

    def add16(self, dest_register: str, src_register: str) -> None:
        """Add 16-bit pair registers."""
        value: int = self.reg[src_register]
        total: int = self.reg[dest_register] + value
        self.flags["H"] = 1 if (self.reg[dest_register] & 0xFFF) + (value & 0xFFF) > 0xFFF else 0
        self.flags["C"] = 1 if total > 0xFFFF else 0
        self.reg[dest_register] = total & 0xFFFF

    def add_sp_e8(self, offset: int) -> None:
        """Add signed immediate to SP, updating H/C from low-byte carry behavior."""
        self._set_sp_offset_result("SP", offset)

    def ld_hl_sp_e8(self, offset: int) -> None:
        """Store SP + signed immediate into HL, with ADD SP,e8 flag semantics."""
        self._set_sp_offset_result("HL", offset)

    def _set_sp_offset_result(self, target: str, offset: int) -> None:
        """Apply SP + signed offset and set flags using ADD SP,e8 semantics."""
        sp = self.reg["SP"]
        signed_offset = hex_to_signed(offset, 8)
        result = (sp + signed_offset) & 0xFFFF
        self.flags["Z"] = 0
        self.flags["N"] = 0
        self.flags["H"] = 1 if ((sp ^ offset ^ result) & 0x10) != 0 else 0
        self.flags["C"] = 1 if ((sp ^ offset ^ result) & 0x100) != 0 else 0
        self.reg[target] = result

    def sub(
        self,
        dest_register: str,
        register: str | bool,
        with_carry: bool | int = False,
    ) -> None:
        """Subtract value from source to dest, optionally with carry."""
        with_carry_flag, value = self._resolve_operand(register, with_carry)
        carry: int = self.flags["C"] if with_carry_flag else 0
        result: int = self.reg[dest_register] - value - carry
        self._set_sub_flags(result, self.reg[dest_register], value, carry)
        self.reg[dest_register] = result & 0xFF

    def bitwise(self, operation: Bitwise, dest_register: str, source: str | int) -> None:
        """Perform bitwise operation (AND, XOR, OR)."""
        value: int = self.get_stored_value(source) if isinstance(source, str) else source

        if operation == Bitwise.AND:
            self.reg[dest_register] &= value
        elif operation == Bitwise.XOR:
            self.reg[dest_register] ^= value
        elif operation == Bitwise.OR:
            self.reg[dest_register] |= value

        self.flags["Z"] = 1 if self.reg[dest_register] == 0 else 0

    def cp(self, dest_register: str, src_register: str | int) -> None:
        """Compare registers."""
        value: int = (
            self.get_stored_value(src_register) if isinstance(src_register, str) else src_register
        )
        result: int = self.reg[dest_register] - value
        self._set_sub_flags(result, self.reg[dest_register], value)

    def get_stored_value(self, register: str) -> int:
        """Get value stored in register or memory."""
        if register == "HL":
            return self.mmu[self.reg[register]]
        return self.reg[register]

    def _resolve_operand(
        self,
        register: str | bool,
        with_carry: bool | int,
    ) -> tuple[bool, int]:
        """Resolve operand for add/sub operations."""
        if isinstance(register, bool):
            # Immediate mode: register parameter is actually the with_carry flag
            with_carry_flag = register
            value = with_carry if isinstance(with_carry, int) else 0
        else:
            # Register mode: normal register operation
            with_carry_flag = with_carry if isinstance(with_carry, bool) else False
            value = self.get_stored_value(register)
        return with_carry_flag, value

    def _set_add_flags(self, total: int, a: int, b: int, carry: int = 0) -> None:
        """Set flags for addition operations."""
        self.flags["Z"] = 1 if (total & 0xFF) == 0 else 0
        self.flags["H"] = 1 if (a & 0xF) + (b & 0xF) + carry > 0xF else 0
        self.flags["C"] = 1 if total > 0xFF else 0

    def _set_sub_flags(self, result: int, a: int, b: int, carry: int = 0) -> None:
        """Set flags for subtraction operations."""
        self.flags["Z"] = 1 if (result & 0xFF) == 0 else 0
        self.flags["H"] = 1 if (a & 0xF) - (b & 0xF) - carry < 0 else 0
        self.flags["C"] = 1 if result < 0 else 0

    def inc(self, register: str) -> None:
        """Increment register."""
        previous = self.reg[register]
        self.reg[register] += 1

        # Only set flags for 8-bit registers
        if len(register) == 1:
            self._set_inc_dec_flags(self.reg[register], previous)

    def inc_mem(self, register: str) -> None:
        """Increment value at address in HL."""
        self._adjust_mem(register, 1)

    def dec_mem(self, register: str) -> None:
        """Decrement value at address in HL."""
        self._adjust_mem(register, -1)

    def _adjust_mem(self, register: str, delta: int) -> None:
        addr = self.reg[register]
        previous = self.mmu[addr]
        updated = (previous + delta) & 0xFF
        self.mmu[addr] = updated
        self._set_inc_dec_flags(updated, previous)

    def dec(self, register: str) -> None:
        """Decrement register or HL address."""
        previous = self.reg[register]
        self.reg[register] -= 1

        # Only set flags for 8-bit registers
        if len(register) == 1:
            self._set_inc_dec_flags(self.reg[register], previous)

    def _set_inc_dec_flags(self, result: int, value: int) -> None:
        """Set flags for INC and DEC operations."""
        self.flags["Z"] = 1 if (result & 0xFF) == 0 else 0
        if self.flags["N"] == 0:
            # INC: half-carry when low nibble overflows (e.g. 0x0F -> 0x10).
            self.flags["H"] = 1 if (value & 0x0F) == 0x0F else 0
        else:
            # DEC: half-borrow when low nibble underflows (e.g. 0x10 -> 0x0F).
            self.flags["H"] = 1 if (value & 0x0F) == 0x00 else 0

    def rot(
        self,
        register: str,
        left: bool = False,
        circular: bool = False,
        insert_carry: bool = False,
    ) -> None:
        """Rotate bits left or right."""
        value: int = self.get_stored_value(register)
        old_carry: int = self.flags["C"]
        new_carry: int = (value >> 7) & 0x1 if left else value & 0x1

        shifted: int = new_carry if left else new_carry << 7
        if insert_carry:
            shifted: int = old_carry if left else old_carry << 7
        elif not circular:
            shifted = (value & 0x80) if not left else 0

        result: int = (value << 1 | shifted) & 0xFF if left else value >> 1 | shifted

        if register == "HL":
            self.mmu[self.reg["HL"]] = result
        else:
            self.reg[register] = result

        # CB-prefixed rotate ops update Z from result;
        # unprefixed A rotates force Z=0 via opcode flags.
        if self.cb_prefixed:
            self.flags["Z"] = 1 if result == 0 else 0
        self.flags["C"] = new_carry

    def shift(self, register: str, left: bool = False, arithmetic: bool = False) -> None:
        """Shift bits left or right."""
        value: int = self.get_stored_value(register)
        new_carry: int = (value >> 7) & 0x1 if left else value & 0x1

        if left:
            result: int = (value << 1) & 0xFF
        else:
            msb: int = value & 0x80 if arithmetic else 0
            result: int = (value >> 1) | msb

        if register == "HL":
            self.mmu[self.reg["HL"]] = result
        else:
            self.reg[register] = result

        # Shift opcodes are CB-prefixed and set Z from result.
        self.flags["Z"] = 1 if result == 0 else 0
        self.flags["C"] = new_carry

    def jpc(self, flag: str, condition: int, addr: int) -> None:
        """Jump to address if condition is met."""
        if self.flags[flag] == condition:
            self.jp(addr)
        else:
            self.pc = (self.pc + 3) & 0xFFFF
            # JP cc base timing is 16 cycles; not-taken timing is 12.
            self._cycle_adjust = -4

    def jp(self, addr: int | str) -> None:
        """Jump to Address."""
        if isinstance(addr, str):
            addr = self.reg[addr]
        self.pc = addr

    def pop(self, register: str) -> int:
        """Pop 16-bit value from stack into register-pair."""
        value = self._pop_u16()
        if register == "AF":
            value &= 0xFFF0
            self.flags["Z"] = (value >> 7) & 0x1
            self.flags["N"] = (value >> 6) & 0x1
            self.flags["H"] = (value >> 5) & 0x1
            self.flags["C"] = (value >> 4) & 0x1
        self.reg[register] = value
        return value

    def push(self, register: str | int) -> None:
        """Push value onto stack."""
        value = self.reg[register] if isinstance(register, str) else register
        self._push_u16(value)

    def rst(self, addr: int, msb: int = 0) -> None:
        """Call to the absolute fixed address."""
        value: int = to_u16(msb, addr)
        self.push((self.pc + 1) & 0xFFFF)
        self.pc = value

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
        else:
            self.pc = (self.pc + 2) & 0xFFFF
            # JR cc base timing is 12 cycles; not-taken timing is 8.
            self._cycle_adjust = -4

    def jr(self, offset: int = 0) -> None:
        """Relative Jump to address."""
        signed_offset: int = hex_to_signed(offset, 8)
        self.pc = (self.pc + 2 + signed_offset) & 0xFFFF

    def callc(self, flag: str, condition: int, addr: int) -> None:
        """Call subroutine at address if condition is met."""
        if self.flags[flag] == condition:
            self.call(addr)
        else:
            self.pc = (self.pc + 3) & 0xFFFF
            # CALL cc base timing is 24 cycles; not-taken timing is 12.
            self._cycle_adjust = -12

    def call(self, addr: int) -> None:
        """Call subroutine at address."""
        self.push((self.pc + 3) & 0xFFFF)
        self.pc = addr

    def ret(self, condition_flag: str | None = None, condition_value: int | None = None) -> None:
        """Return from subroutine, optionally if condition is met."""
        if condition_flag is None or self.flags[condition_flag] == condition_value:
            self.pc = self._pop_u16()
        else:
            self.pc = (self.pc + 1) & 0xFFFF
            # RET cc base timing is 20 cycles; not-taken timing is 8.
            self._cycle_adjust = -12

    def reti(self) -> None:
        """Return from interrupt and enable interrupts."""
        self.pc = self._pop_u16()
        self.interrupts = True
        self._ime_delay = 0

    def bit(self, bit_num: int, register: str) -> None:
        """Test if bit is set in register or memory."""
        value: int = self.get_stored_value(register)
        self.flags["Z"] = 0 if (value >> bit_num) & 0x1 else 1

    def di(self) -> None:
        """Disable interrupts."""
        self.interrupts = False
        self._ime_delay = 0

    def ei(self) -> None:
        """Enable interrupts after the following instruction (DMG behavior)."""
        self._ime_delay = 2

    def set_stored_value(self, register: str, value: int) -> None:
        """Set value in register or memory."""
        if register == "HL":
            self.mmu[self.reg[register]] = value
        else:
            self.reg[register] = value

    def swap(self, register: str) -> None:
        """Swap upper and lower nibbles."""
        value: int = self.get_stored_value(register)
        result: int = ((value & 0xF) << 4) | ((value & 0xF0) >> 4)

        self.set_stored_value(register, result)
        self.flags["Z"] = 1 if result == 0 else 0

    def res(self, bit_num: int, register: str) -> None:
        """Reset bit in register or memory."""
        value: int = self.get_stored_value(register)
        result: int = value & ~(1 << bit_num)
        self.set_stored_value(register, result)

    def set(self, bit_num: int, register: str) -> None:
        """Set bit in register or memory."""
        value: int = self.get_stored_value(register)
        result: int = value | (1 << bit_num)
        self.set_stored_value(register, result)

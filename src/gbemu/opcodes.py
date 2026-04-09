from dataclasses import dataclass


@dataclass(frozen=True)
class OpCode:
    label: str  # mnemonic name
    length: int  # lengh of instuction in bytes
    cycles: int  # number of cpu cyles
    call: str  # CPU method name to call
    args: list[str] | None = None  # give arguments to send to CPU method
    flags: list[str] | None = None  # set CPU flags after execution

    def __str__(self) -> str:
        return f"{self.label} - {self.length} - {self.args} - {self.flags}"


OPCODES: dict[str, OpCode] = {
    "0x0": OpCode("NOP", 1, 4, "nop"),
    "0x1f": OpCode("RRA", 1, 4, "rra", flags=["C"]),  # STOPPED HERE
    "0x6": OpCode("LD H, B", 1, 4, "ld_hr", args=["B"]),
    "0x5": OpCode("LD D, B", 1, 4, "ld", args=["D", "B"]),
    "0xe": OpCode("LDH [a8], A", 2, 12, "ld", args=["A"]),
    "0x20": OpCode("JR NZ, i8", 2, 8, "jr"),  # FIX: 8/12 Timing(?)
    "0x21": OpCode("LD HL, a16", 3, 12, "ld", args=["HL"]),
    "0x32": OpCode("LD [HL-], A", 1, 8, "ld_hm", args=["A"]),
    "0xc3": OpCode("JMP a16", 3, 16, "jmp"),
    "0xe1": OpCode("POP HL", 1, 12, "pop"),
    "0xaf": OpCode("XOR A, A", 1, 4, "xor", args=["A", "A"], flags=["Z"]),
}

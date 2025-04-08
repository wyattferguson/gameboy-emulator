from dataclasses import dataclass


@dataclass(frozen=True)
class OpCode:
    label: str  # mnemonic name
    length: int  # lengh of instuction in bytes
    cycles: int  # number of cpu cyles
    call: str  # CPU method name to call
    args: list | None = None  # give arguments to send to CPU method
    flags: tuple | None = None  # set CPU flags after execution

    def __str__(self) -> str:
        return f"{self.label} - {self.length} - {self.args} - {self.flags}"


OPCODES: dict[hex, OpCode] = {
    "0x0": OpCode("NOP", 1, 4, "NOP"),
    "0x1f": OpCode("RRA", 1, 4, "RRA", flags=("C")),  # STOPPED HERE
    "0x6": OpCode("LD H, B", 1, 4, "LD_HR", args=["B"]),
    "0x5": OpCode("LD D, B", 1, 4, "LD", args=["D", "B"]),
    "0xe": OpCode("LDH [a8], A", 2, 12, "LD", args=["A"]),
    "0x20": OpCode("JR NZ, i8", 2, 8, "JR"),  # FIX: 8/12 Timing(?)
    "0x21": OpCode("LD HL, a16", 3, 12, "LD", args=["HL"]),
    "0x32": OpCode("LD [HL-], A", 1, 8, "LD_HM", args=["A"]),
    "0xc3": OpCode("JMP a16", 3, 16, "JMP"),
    "0xe1": OpCode("POP HL", 1, 12, "POP"),
    "0xaf": OpCode("XOR A, A", 1, 4, "XOR", args=["A", "A"], flags=("Z")),
}

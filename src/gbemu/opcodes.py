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
        return f"{self.label} {self.length} - {self.args} - {self.flags}"


OPCODES: dict[str, OpCode] = {
    "0x0": OpCode("NOP", 1, 4, "nop"),
    # "0x1f": OpCode("RRA", 1, 4, "rra", flags=["C"]),
    "0x3e": OpCode("LD A, d8", 2, 8, "ld", args=["A"]),
    "0x40": OpCode("LD B, B", 1, 4, "ld", args=["B", "B"]),
    "0x41": OpCode("LD B, C", 1, 4, "ld", args=["B", "C"]),
    "0x42": OpCode("LD B, D", 1, 4, "ld", args=["B", "D"]),
    "0x43": OpCode("LD B, E", 1, 4, "ld", args=["B", "E"]),
    "0x44": OpCode("LD B, H", 1, 4, "ld", args=["B", "H"]),
    "0x45": OpCode("LD B, L", 1, 4, "ld", args=["B", "L"]),
    "0x46": OpCode("LD B, [HL]", 1, 8, "ld_hl", args=["B"]),
    "0x47": OpCode("LD B, A", 1, 4, "ld", args=["B", "A"]),
    "0x48": OpCode("LD C, B", 1, 4, "ld", args=["C", "B"]),
    "0x49": OpCode("LD C, C", 1, 4, "ld", args=["C", "C"]),
    "0x4a": OpCode("LD C, D", 1, 4, "ld", args=["C", "D"]),
    "0x4b": OpCode("LD C, E", 1, 4, "ld", args=["C", "E"]),
    "0x4c": OpCode("LD C, H", 1, 4, "ld", args=["C", "H"]),
    "0x4d": OpCode("LD C, L", 1, 4, "ld", args=["C", "L"]),
    "0x4e": OpCode("LD C, [HL]", 1, 8, "ld_hl", args=["C"]),
    "0x4f": OpCode("LD C, A", 1, 4, "ld", args=["C", "A"]),
}

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
    "0x50": OpCode("LD D, B", 1, 4, "ld", args=["D", "B"]),
    "0x51": OpCode("LD D, C", 1, 4, "ld", args=["D", "C"]),
    "0x52": OpCode("LD D, D", 1, 4, "ld", args=["D", "D"]),
    "0x53": OpCode("LD D, E", 1, 4, "ld", args=["D", "E"]),
    "0x54": OpCode("LD D, H", 1, 4, "ld", args=["D", "H"]),
    "0x55": OpCode("LD D, L", 1, 4, "ld", args=["D", "L"]),
    "0x56": OpCode("LD D, [HL]", 1, 8, "ld_hl", args=["D"]),
    "0x57": OpCode("LD D, A", 1, 4, "ld", args=["D", "A"]),
    "0x58": OpCode("LD E, B", 1, 4, "ld", args=["E", "B"]),
    "0x59": OpCode("LD E, C", 1, 4, "ld", args=["E", "C"]),
    "0x5a": OpCode("LD E, D", 1, 4, "ld", args=["E", "D"]),
    "0x5b": OpCode("LD E, E", 1, 4, "ld", args=["E", "E"]),
    "0x5c": OpCode("LD E, H", 1, 4, "ld", args=["E", "H"]),
    "0x5d": OpCode("LD E, L", 1, 4, "ld", args=["E", "L"]),
    "0x5e": OpCode("LD E, [HL]", 1, 8, "ld_hl", args=["E"]),
    "0x5f": OpCode("LD E, A", 1, 4, "ld", args=["E", "A"]),
    "0x60": OpCode("LD H, B", 1, 4, "ld", args=["H", "B"]),
    "0x61": OpCode("LD H, C", 1, 4, "ld", args=["H", "C"]),
    "0x62": OpCode("LD H, D", 1, 4, "ld", args=["H", "D"]),
    "0x63": OpCode("LD H, E", 1, 4, "ld", args=["H", "E"]),
    "0x64": OpCode("LD H, H", 1, 4, "ld", args=["H", "H"]),
    "0x65": OpCode("LD H, L", 1, 4, "ld", args=["H", "L"]),
    "0x66": OpCode("LD H, [HL]", 1, 8, "ld_hl", args=["H"]),
    "0x67": OpCode("LD H, A", 1, 4, "ld", args=["H", "A"]),
    "0x68": OpCode("LD L, B", 1, 4, "ld", args=["L", "B"]),
    "0x69": OpCode("LD L, C", 1, 4, "ld", args=["L", "C"]),
    "0x6a": OpCode("LD L, D", 1, 4, "ld", args=["L", "D"]),
    "0x6b": OpCode("LD L, E", 1, 4, "ld", args=["L", "E"]),
    "0x6c": OpCode("LD L, H", 1, 4, "ld", args=["L", "H"]),
    "0x6d": OpCode("LD L, L", 1, 4, "ld", args=["L", "L"]),
    "0x6e": OpCode("LD L, [HL]", 1, 8, "ld_hl", args=["L"]),
    "0x6f": OpCode("LD L, A", 1, 4, "ld", args=["L", "A"]),
    "0x70": OpCode("LD [HL], B", 1, 8, "ld_hl_r", args=["B"]),
    "0x71": OpCode("LD [HL], C", 1, 8, "ld_hl_r", args=["C"]),
    "0x72": OpCode("LD [HL], D", 1, 8, "ld_hl_r", args=["D"]),
    "0x73": OpCode("LD [HL], E", 1, 8, "ld_hl_r", args=["E"]),
    "0x74": OpCode("LD [HL], H", 1, 8, "ld_hl_r", args=["H"]),
    "0x75": OpCode("LD [HL], L", 1, 8, "ld_hl_r", args=["L"]),
    "0x76": OpCode("HALT", 1, 4, "halt"),  # NEEDS INTERRUPT HANDLING / TESTING
    "0x77": OpCode("LD [HL], A", 1, 8, "ld_hl_r", args=["A"]),
    "0x78": OpCode("LD A, B", 1, 4, "ld", args=["A", "B"]),
    "0x79": OpCode("LD A, C", 1, 4, "ld", args=["A", "C"]),
    "0x7a": OpCode("LD A, D", 1, 4, "ld", args=["A", "D"]),
    "0x7b": OpCode("LD A, E", 1, 4, "ld", args=["A", "E"]),
    "0x7c": OpCode("LD A, H", 1, 4, "ld", args=["A", "H"]),
    "0x7d": OpCode("LD A, L", 1, 4, "ld", args=["A", "L"]),
    "0x7e": OpCode("LD A, [HL]", 1, 8, "ld_hl", args=["A"]),
    "0x7f": OpCode("LD A, A", 1, 4, "ld", args=["A", "A"]),
    "0x80": OpCode("ADD A, B", 1, 4, "add", args=["A", "B"], flags=["Z", "N", "H", "C"]),
    "0x81": OpCode("ADD A, C", 1, 4, "add", args=["A", "C"], flags=["Z", "N", "H", "C"]),
    "0x82": OpCode("ADD A, D", 1, 4, "add", args=["A", "D"], flags=["Z", "N", "H", "C"]),
    "0x83": OpCode("ADD A, E", 1, 4, "add", args=["A", "E"], flags=["Z", "N", "H", "C"]),
    "0x84": OpCode("ADD A, H", 1, 4, "add", args=["A", "H"], flags=["Z", "N", "H", "C"]),
    "0x85": OpCode("ADD A, L", 1, 4, "add", args=["A", "L"], flags=["Z", "N", "H", "C"]),
    "0x86": OpCode("ADD A, [HL]", 1, 8, "add_hl", args=["A"], flags=["Z", "N", "H", "C"]),
    "0x87": OpCode("ADD A, A", 1, 4, "add", args=["A", "A"], flags=["Z", "N", "H", "C"]),
}

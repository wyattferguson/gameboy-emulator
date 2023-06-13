from dataclasses import dataclass


@dataclass(frozen=True)
class OpCode:
    label: str   # mnemonic name
    length: int  # lengh of instuction in bytes
    cycles: int  # number of cpu cyles
    call: str    # CPU method name to call
    args: list = None   # give arguments to send to CPU method
    flags: tuple = None

    def __str__(self) -> str:
        return f"{self.label} - {self.length} - {self.args}"


# Opcodes whose argument should be added with 0xff00
prefix_opcodes = (0xcb, 0x10)

# Extended opcodes. Use this table after the opcode 0xcb has been encountered
# from the preceding table. BYte lengths here are EXCLUSIVE the preceding
# prefix opcode.

OPCODE_TABLE = {
    # '0x10': OpCode("STOP", 2, 4, "STOP", None),  # TBD
    # '0x31': OpCode("LD SP, n16", 3, 12, "LD", ["SP"]),
    # # '0x32': OpCode("LD [HL-], A", 1, 8, "LD", ["HL", "A"]),
    # '0x38': OpCode("JR C, e8", 2, 12, "JR", None, ("C", 1)),
    # '0xc9': OpCode("RET", 1, 4, "RET", None),
    '0x0': OpCode("NOP", 1, 1, "NOP"),
    '0x03': OpCode("INC BC", 1, 8, "INC", ['BC']),
    '0x13': OpCode("INC DE", 1, 8, "INC", ['DE']),
    '0x18': OpCode("JR e8", 2, 8, "JR"),
    '0x20': OpCode("JR NZ, e8", 2, 8, "JR", None, ("Z", 0)),
    '0x22': OpCode("LD [HL+], A", 1, 8, "LD", ["HL", "A"]),  # TODO
    '0x1a': OpCode("SDFSDF", 1, 8, "SLKDJF", ['DE']),  # TODO
    '0x23': OpCode("INC HL", 1, 8, "INC", ['HL']),
    '0x28': OpCode("JR N, e8", 2, 8, "JR", None, ("Z", 1)),
    '0x30': OpCode("JR NC, e8", 2, 8, "JR", None, ("C", 0)),
    '0x33': OpCode("INC SP", 1, 8, "INC", ['SP']),
    '0x38': OpCode("JR C, e8", 2, 12, "JR", None, ("C", 1)),
    '0xff': OpCode("RST 38H", 1, 16, "RST", [0x38]),
}

EXT_OPCODE_TABLE = {
    '0xff': OpCode("SET 7 A", 1, 8, "SET", None),
}

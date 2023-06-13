from dataclasses import dataclass


@dataclass(frozen=True)
class OpCode:
    label: str   # mnemonic name
    length: int  # lengh of instuction in bytes
    cycles: int  # number of cpu cyles
    call: str    # CPU method name to call
    args: list   # give arguments to send to CPU method

    def __str__(self) -> str:
        return f"{self.label} - {self.length} - {self.args}"


@dataclass
class Register:
    label: str
    value: any
    address: int

    def __repr__(self) -> str:
        return self.value


@dataclass
class PairRegister:
    label: str
    high: Register
    low: Register
    #  return (self.get(register_name[0]) << 8) + self.get(register_name[1])

    def __repr__(self) -> str:
        return (self.high << 8) + self.low


OPCODE_TABLE = {

    '0x31': OpCode("LD SP, n16", 3, 12, "LD", ["SP"]),
    '0x32': OpCode("LD [HL-], A", 1, 8, "LD", ["HL", "A"]),
    '0xc9': OpCode("RET", 1, 4, "RET", []),
    '0xff': OpCode("RST 38H", 1, 16, "RST", [0x38]),
}

from dataclasses import dataclass


@dataclass(frozen=True)
class OpCode:
    label: str
    length: bytes
    cycles: int
    flags: tuple
    call: str
    args: list

    def __str__(self) -> str:
        return f"{self.label} - {self.length} - {self.args}"


opcode_table = {
    '0xff': OpCode("RST 38H", 1, 16, False, "RST", [0x38])
}

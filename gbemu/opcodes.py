from dataclasses import dataclass


@dataclass(frozen=True)
class OpCode:
    label: str   # mnemonic name
    length: int  # lengh of instuction in bytes
    cycles: int  # number of cpu cyles
    call: str    # CPU method name to call
    args: list | None = None   # give arguments to send to CPU method
    flags: tuple | None = None

    def __str__(self) -> str:
        return f"{self.label} - {self.length} - {self.args}"


# Opcodes whose argument should be added with 0xff00
prefix_opcodes = (0xcb, 0x10)

# Extended opcodes. Use this table after the opcode 0xcb has been encountered
# from the preceding table. BYte lengths here are EXCLUSIVE the preceding
# prefix opcode.

OPCODE_TABLE = {
    '0x0': OpCode("NOP", 1, 1, "NOP"),
}

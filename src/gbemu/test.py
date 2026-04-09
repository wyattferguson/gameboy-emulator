from gbemu.config import MEMORY_SIZE

if __name__ == "__main__":
    # a = 0b1111_1111
    # b = 0b0000_0100
    # print(f"A: {bin(a)}, B: {bin(b)}")

    # print(f"A & B: {bin(a & b)}")
    # print(f"A | B: {bin(a | b)}")

    # for n in range(4):
    #     a = a ^ b
    #     print(f"A = {bin(a)}")

    a = 0b1101_1111
    b = 0b0011_00000
    print(f"A: {bin(a)}, B: {bin(b)}")
    print(MEMORY_SIZE)

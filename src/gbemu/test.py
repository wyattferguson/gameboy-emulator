from gbemu.config import MEMORY_SIZE

"""
0001 0010
0011 0100
0010 0000




"""
if __name__ == "__main__":
    a = 0x12
    b = 0x34
    result = a & b
    print(bin(a))
    print(bin(b))
    print(bin(result))
    print(f"{a} & {b} = {result}")

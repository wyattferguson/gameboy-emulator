from gbemu.config import MEMORY_SIZE

if __name__ == "__main__":
    a = 0xFF
    b = 0xFF
    c = 1
    print(f"a: {a}/{bin(a)} b: {b}/{bin(b)} c: {c}/{bin(c)}")
    print(f"a & 0xF: {a & 0xF}/{bin(a & 0xF)} b & 0xF: {b & 0xF}/{bin(b & 0xF)} c: {c}/{bin(c)}")
    total = a + b + c
    print(f"total: {total}/{bin(total)}/{hex(total)}")

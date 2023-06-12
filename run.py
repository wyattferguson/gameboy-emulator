from pygame import time

from config import DELAY
from cpu import CPU
from screen import Screen


def run():
    rom = "./roms/2048.gb"
    screen = Screen()
    cpu = CPU(screen)
    cpu.load_rom(rom)

    while True:
        time.wait(DELAY)
        cpu.cycle()
        screen.update()


if __name__ == "__main__":
    run()

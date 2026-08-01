<div align="center">
<img src="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzR1NnA0aHZzcWFvY2w1OGJzdnRiY243cnl1MjFzN291aDk2Z2VkZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/VHFIfibSOqdIAnEkyd/giphy.gif" alt="animated" /><br>
  <h1>:joystick:  GBemu</h1>
  <p><strong>Python Gameboy Emulator.</strong></p>

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>


This is my workin' progress gameboy emulator created in pure python. The emulator is mostly functional with a smattering of edge case bugs listed in the `TODO.md`. The big missing feature is audio, but emulating the APU is something Im not all that concered with right now. Most early gameboy games run with the 2 mappers I have so far my goal is to complete the MBC3 because that would give support for a good chunk of all games.

Right now the if you run it using the standard python interepter you hit a performance bottleneck pretty quick on any lower spec PC's, so I've used pypy as the default to get out a good performance gain. Idealy in the future once I rework the MMU it would just be a cython build.

## Installation

This project uses `uv` with PyPy as the default interpreter for best performance, but it should work with CPython as well. To set up the virtual environment and install dependencies, run:

```powershell
uv venv
uv sync
```

## How to use

By default the emulator will attempt to load `./roms/2048.gb` on startup, but you can specify any rom path with the `-r` flag.

Run the emulator:

```powershell
task run

task run -r path/to/rom.gb
```

Run the test suite:

```powershell
task tests
```

Run performance tests:

```powershell
task perf
```

## Included Roms

- `2048.gb` - A 2048 clone I made, full source is availible in the [Github Repo](https://github.com/wyattferguson/2048-gb)
- `gameoflife.gb` - A port of Game of Life I made, full source is availible in the [Github Repo](https://github.com/wyattferguson/gameoflife-gb)
- `hello.gb` - A very simple rom that just boots and displays a sprite hello message.

## Controls

Mapped controls can be changed in `src/gbemu/config.py`. Default mappings are:

- D-Pad: W, A, S, D
- A: J
- B: K
- Start: Enter
- Select: Right Shift

## References

- [GBDev CPU Instuction Set(https://gbdev.gg8.se/wiki/articles/CPU_Instruction_Set)](https://gbdev.gg8.se/wiki/articles/CPU_Instruction_Set)
- [Gameboy Test Roms (https://github.com/retrio/gb-test-roms)](https://github.com/retrio/gb-test-roms)
- [GB ASM Tutorial (https://gbdev.io/gb-asm-tutorial)](https://gbdev.io/gb-asm-tutorial)
- [GB Opcode Table (https://gbdev.io/gb-opcodes/optables/)](https://gbdev.io/gb-opcodes/optables/)
- [Pan Docs (https://gbdev.io/pandocs/Specifications.html)](https://gbdev.io/pandocs/Specifications.html)
- [Game Boy: Complete Technical Reference (https://gekkio.fi/files/gb-docs/gbctr.pdf)](https://gekkio.fi/files/gb-docs/gbctr.pdf)

## License

[MIT license](https://github.com/wyattferguson/gbemu/blob/master/LICENSE)

## Contact + Support

Created by [Wyatt Ferguson](https://github.com/wyattferguson)

For any questions or comments heres how you can reach me:

**:octopus: Follow me on [Github @wyattferguson](https://github.com/wyattferguson)**

**:mailbox_with_mail: Email me at [wyattxdev@duck.com](wyattxdev@duck.com)**

**:tropical_drink: Follow on [BlueSky @wyattf](https://wyattf.bsky.social)**

If you find this useful and want to tip me a little coffee money:

**:coffee: [Buy Me A Coffee](https://www.buymeacoffee.com/wyattferguson)**

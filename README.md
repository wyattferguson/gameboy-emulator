# :video_game: gbemu - Python Gameboy Emulator

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

### :octocat: Follow me on [Github @wyattferguson](https://github.com/wyattferguson)

### :mailbox_with_mail: Email me at [wyattxdev@duck.com](wyattxdev@duck.com)

### :tropical_drink: Follow on [BlueSky @wyattf](https://wyattf.bsky.social)

If you find this useful and want to tip me a little coffee money:

### :coffee: [Buy Me A Coffee](https://www.buymeacoffee.com/wyattferguson)

# :video_game: gbemu - Python Gameboy Emulator

## Installation

This project uses `uv` with PyPy as the default interpreter.

```powershell
uv venv
uv sync
```

`uv venv` will create `.venv` with PyPy automatically via the project's `.python-version` file.

## How to use

Run the emulator:

```powershell
task run
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
- `hello.gb` - A very simple rom that just boots and display a sprite hello message.
- `roms/tests/` a collection of roms with different specific bugs, these are run during testing with pytest.
- `roms/verification/` a collection of roms to verify the accuracy of all the systems instructions and timings.

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

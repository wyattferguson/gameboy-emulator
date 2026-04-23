# gbemu — TODO

Itemized list of everything needed to complete the Game Boy (DMG) emulator.
Items are grouped by subsystem and ordered roughly by impact on compatibility.

---

## 1. MBC / Bank Switching

**Status:** Only ROM-only (type `0x00`) cartridges are supported. The MMU loads a maximum of 32 KB of ROM data into the flat memory array and ignores everything beyond that.

- [ ] **MBC1** — Most common mapper. Implement ROM bank register (bits 0-4), RAM bank register (bits 5-6), banking mode select, and external RAM enable/disable. Needed for Tetris variants, Kirby, Link's Awakening, and dozens of other titles.
- [ ] **MBC2** — Built-in 512×4-bit RAM, simpler bank register. Needed for a small set of titles (Tennis, Baseball).
- [ ] **MBC3** — Adds a Real-Time Clock (RTC) on top of MBC1-style banking. Needed for Pokémon Red/Blue/Yellow/Gold/Silver.
- [ ] **MBC5** — Extends ROM addressing to 64 banks and RAM to 16 banks. Used by most late-era DMG/CGB games (Pokémon Crystal, DK 64, etc.).
- [ ] **Cart RAM (SRAM) persistence** — Save external RAM to a `.sav` file on write and reload it on startup so battery-backed saves survive across sessions.
- [ ] **ROM-size validation** — Detect actual mapper type from header byte `0x0147` and refuse or warn rather than silently truncating unsupported ROMs.

---

## 2. APU (Audio)

**Status:** `apu.py` is entirely stubbed — `update()` does nothing and no audio is produced.

- [ ] **Channel 1 — Pulse + Sweep** — Implement frequency sweep (`NR10`), duty cycle (`NR11`), envelope (`NR12`), frequency low/high (`NR13`/`NR14`), and length counter. Output a square wave to the left/right mixer.
- [ ] **Channel 2 — Pulse** — Same as Channel 1 without the sweep unit (`NR21`–`NR24`).
- [ ] **Channel 3 — Wave** — Arbitrary 32-nibble waveform read from Wave RAM (`FF30`–`FF3F`). Registers `NR30`–`NR34` control enable, length, output level, and frequency.
- [ ] **Channel 4 — Noise** — Linear-feedback shift register (LFSR) with programmable clock divider and width (`NR41`–`NR44`).
- [ ] **Master volume / mixer** — Implement `NR50` (master volume L/R) and `NR51` (channel-to-terminal routing).
- [ ] **Frame sequencer** — 512 Hz clock that drives length counters (256 Hz), volume envelopes (64 Hz), and frequency sweep (128 Hz).
- [ ] **Pygame audio output** — Open a pygame mixer stream and push synthesized samples each frame. Sync sample rate to emulator timing to avoid underruns.
- [ ] **NR52 power control** — Writing 0 to bit 7 of `NR52` should reset all channel registers.

---

## 3. PPU Accuracy

**Status:** Scanline renderer is functional but uses simplified fixed-cycle mode timings and a direct scanline approach rather than a pixel FIFO.

- [ ] **Pixel FIFO renderer** — Replace the current direct scanline renderer with a two-FIFO (BG FIFO + OBJ FIFO) design. Required for accurate per-pixel mixing and mid-scanline scroll effects.
- [ ] **Mode 3 variable timing** — Mode 3 duration varies between 172–289 dots depending on sprite count, SCX alignment, and window activation. Currently fixed at `PPU_MODE3_CYCLES`. Adjust Mode 0 duration to compensate so each scanline still totals 456 dots.
- [ ] **Window X=0 quirk** — Window triggered at WX=0 skips the first pixel; needs special handling in the render path.
- [ ] **Sprite priority edge cases** — When two sprites overlap, the one with the lower OAM index wins. Verify the current OAM scan order matches hardware priority rules.
- [ ] **SCX sub-tile scrolling** — Fine horizontal scroll (SCX mod 8) should discard the leftmost pixels from the BG FIFO, not shift the tile base.
- [ ] **LY=LYC coincidence flag on disable/enable** — When LCD is re-enabled, LY is reset to 0 and the coincidence check should fire immediately if LYC is also 0.
- [ ] **STAT interrupt blocking** — The STAT interrupt line is open-drain; simultaneous source enables can prevent a rising edge. Implement the STAT interrupt blocking behavior.

---

## 4. OAM DMA

**Status:** OAM DMA (`FF46` write) is instant — it copies 160 bytes immediately without locking the CPU bus.

- [ ] **DMA bus lock** — During DMA transfer the CPU may only access `FF80`–`FFFE` (HRAM). Lock all other reads/writes for 160 machine cycles (640 T-cycles) after `FF46` is written.
- [ ] **DMA source validation** — DMA source addresses above `DF00` produce undefined behavior on hardware; add a warning for out-of-range sources.

---

## 5. HALT / STOP Behavior

**Status:** `halt` sets `self.halted = True` and `stop` sets `self.stopped = True` but neither is fully accurate.

- [ ] **HALT bug** — When `HALT` is executed with `IME=0` and a pending interrupt, the CPU fails to increment PC after the next fetch. Implement the HALT bug so the following byte is executed twice.
- [ ] **HALT wake-up** — Exiting HALT should resume execution at the instruction after HALT and service the interrupt if IME was enabled.
- [ ] **STOP behavior** — `STOP` should halt both the CPU and LCD, clear the DIV register, and wait for a joypad button press before resuming. Currently it only sets a flag.

---

## 6. Timer Edge Cases

**Status:** DIV and TIMA timers are implemented but several hardware quirks are missing.

- [ ] **DIV reset side effect** — Writing any value to `FF03` (DIV) resets the internal 16-bit counter to 0. If the falling edge of the TIMA multiplexer bit occurs at the same moment, TIMA should increment once.
- [ ] **TIMA overflow delay** — After TIMA overflows, there is a 4-cycle window before TMA is reloaded and the interrupt is requested. Writing TIMA during this window cancels the reload.
- [ ] **TAC multiplexer bits** — TIMA should tick on the falling edge of the internal counter bit selected by TAC (bits 9, 3, 5, 7 for speeds 0–3), not by counting CPU cycles directly.

---

## 7. Serial Link / SGB

**Status:** Not implemented. Serial registers (`FF01`/`FF02`) are plain memory.

- [ ] **Serial transfer stub** — Implement basic internal clock serial transfer: after 8 bits are shifted out (512 T-cycles), set bit 3 of `IF` to request the serial interrupt. Needed for some games that spin on serial completion.
- [ ] **Link cable (optional)** — Full two-instance TCP/socket link cable emulation for multiplayer games.
- [ ] **Super Game Boy (optional)** — `SGB_FLAG` is decoded from the header but no SGB border, palettes, or packet commands are processed.

---

## 8. Game Boy Color (CGB) Support

**Status:** `CGB_FLAG` is decoded from the cartridge header but all CGB features are ignored.

- [ ] **Double-speed mode** — Writing bit 0 of `FF4D` (KEY1) and executing `STOP` doubles CPU clock to 8.39 MHz. Halve cycle counts reported to PPU/timer when active.
- [ ] **VRAM bank 1** — Add a second 8 KB VRAM bank selected by `FF4F`. BG and OBJ tile data can reside in either bank.
- [ ] **CGB BG palette RAM** — 64 bytes of BG palette memory at `FF69`/`FF68` (index/data), replacing the single DMG palette register.
- [ ] **CGB OBJ palette RAM** — 64 bytes of OBJ palette memory at `FF6B`/`FF6A`.
- [ ] **WRAM banking** — Add 7 extra switchable WRAM banks (total 32 KB) selected by `FF70`.
- [ ] **HDMA / GDMA** — Implement general-purpose DMA (`FF55`) for CGB ROM loading and H-Blank DMA for per-scanline transfers.
- [ ] **CGB-only opcodes** — `LD [HL+], A` / `LD A, [HL+]` addressing is shared with DMG, but verify no CGB-only undocumented behavior is missing.

---

## 9. Cartridge / ROM Loading

- [ ] **Checksum validation** — Verify the header checksum (`014D`) and global checksum (`014E`–`014F`) on load; warn if they fail.
- [ ] **File drag-and-drop** — Accept a ROM path dropped onto the pygame window in addition to the CLI argument.
- [ ] **Recent ROMs menu (optional)** — Track recently opened ROMs in a config file and expose them via a simple in-window menu.

---

## 10. Save States

**Status:** Not implemented. No mechanism to snapshot or restore emulator state.

- [ ] **Save state serialization** — Serialize CPU registers, MMU memory, PPU state, timer counters, and all hardware register values to a file (e.g., JSON or `pickle`).
- [ ] **Save state restore** — Deserialize and reload all state to return the emulator to a prior point.
- [ ] **Slot system (optional)** — Support multiple numbered slots (e.g., F5–F8 to save, F1–F4 to load).

---

## 11. Input

**Status:** KEYMAP is a static dict in `config.py`; no runtime remapping is possible.

- [ ] **Runtime key remapping** — Allow users to rebind keys at launch (e.g., via CLI flags or a config file) rather than hard-coding them in `KEYMAP`.
- [ ] **Gamepad / controller support** — Use `pygame.joystick` to map a physical controller's axes and buttons to DMG inputs.
- [ ] **Turbo / fast-forward** — Hold a key (e.g., Tab) to run the emulator at 2×–8× speed without audio.

---

## 12. Debugging Tools

**Status:** Debug flag exists but only enables opcode logging. No interactive tooling.

- [ ] **Step debugger** — Pause execution and step one instruction at a time via keyboard shortcut. Display current registers, flags, and PC.
- [ ] **Memory inspector** — Print or render a hex dump of any 64 KB region on demand.
- [ ] **VRAM viewer** — Render the tile data, BG map, and OAM table to a secondary pygame surface for visual debugging.
- [ ] **Breakpoints** — Allow setting a PC breakpoint so the emulator pauses automatically when it reaches a given address.
- [ ] **Instruction trace log** — Optionally write a full disassembly trace (PC, opcode mnemonic, register state) to a file.

---

## 13. Test ROM Validation

**Status:** Tests cover individual opcodes and hardware modules but no external compliance test ROMs are run.

- [ ] **Blargg's cpu_instrs** — Run all 11 sub-tests from `cpu_instrs.gb` and assert the serial output matches expected pass strings.
- [ ] **Blargg's instr_timing** — Validate per-instruction cycle counts against Blargg's timing ROM output.
- [ ] **Blargg's mem_timing** — Validate memory access timing for read/write cycles.
- [ ] **Mooneye-GB test suite** — Run acceptance tests covering HALT bug, timer quirks, OAM DMA, MBC behavior, and PPU mode timing.
- [ ] **dmg-acid2** — Render the dmg-acid2 PPU test ROM and compare pixel output to the reference image to verify rendering accuracy.

---

## 14. Performance

**Status:** PyPy is now the default runtime. DMG performance is improved, but there is still limited headroom for CGB double-speed or heavier test suites.

- [ ] **Profile hot paths** — Run `cProfile` on `cpu.cycle()`, `ppu.update()`, and `mmu.__getitem__` to find the biggest bottlenecks.
- [ ] **MMU access optimization** — The current `__getitem__` / `__setitem__` path has many branching checks. Consider caching read/write handlers per address range.
- [ ] **Cython or mypyc compilation (optional)** — Compile the CPU and MMU modules to C extensions for a significant speed boost without changing Python source.
- [ ] **PyPy JIT tuning** — Profile hot loops under PyPy and adjust object layout or dispatch patterns that block JIT optimization.

---

## 15. Documentation & Project Health

- [ ] **README** — Fill in the Installation, How to Use, and Included ROMs sections which are currently empty placeholders.
- [ ] **Changelog** — Add a `CHANGELOG.md` tracking version history and feature additions.
- [ ] **CI pipeline** — Add a GitHub Actions workflow that runs `pytest`, `ruff`, and `ty` on every push and pull request.
- [ ] **Coverage reporting** — Add `pytest-cov` and enforce a minimum coverage threshold in CI.
- [ ] **Package release** — Configure `pyproject.toml` build metadata and publish a versioned release to PyPI or GitHub Releases.

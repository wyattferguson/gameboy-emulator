# gbemu — TODO

---

## 1. MBC / Bank Switching

- **MBC3** — Adds a Real-Time Clock (RTC) on top of MBC1-style banking. Needed for Pokémon Red/Blue/Yellow/Gold/Silver.
- **MBC5** — Extends ROM addressing to 64 banks and RAM to 16 banks. Used by most late-era games.
- **Cart RAM (SRAM) persistence** — Save external RAM to a `.sav` file on write and reload it on startup so battery-backed saves survive across sessions.

---

## 2. APU (Audio)

- **Channel 1 — Pulse + Sweep** — Implement frequency sweep (`NR10`), duty cycle (`NR11`), envelope (`NR12`), frequency low/high (`NR13`/`NR14`), and length counter. Output a square wave to the left/right mixer.
- **Channel 2 — Pulse** — Same as Channel 1 without the sweep unit (`NR21`–`NR24`).
- **Channel 3 — Wave** — Arbitrary 32-nibble waveform read from Wave RAM (`FF30`–`FF3F`). Registers `NR30`–`NR34` control enable, length, output level, and frequency.
- **Channel 4 — Noise** — Linear-feedback shift register (LFSR) with programmable clock divider and width (`NR41`–`NR44`).
- **Master volume / mixer** — Implement `NR50` (master volume L/R) and `NR51` (channel-to-terminal routing).
- **Frame sequencer** — 512 Hz clock that drives length counters (256 Hz), volume envelopes (64 Hz), and frequency sweep (128 Hz).
- **Pygame audio output** — Open a pygame mixer stream and push synthesized samples each frame. Sync sample rate to emulator timing to avoid underruns.
- **NR52 power control** — Writing 0 to bit 7 of `NR52` should reset all channel registers.

---

## 3. PPU Accuracy

**Status:** Scanline renderer is functional but uses simplified fixed-cycle mode timings and a direct scanline approach rather than a pixel FIFO.

- **Pixel FIFO renderer** — Replace the current direct scanline renderer with a two-FIFO (BG FIFO + OBJ FIFO) design. Required for accurate per-pixel mixing and mid-scanline scroll effects.
- **Mode 3 variable timing** — Mode 3 duration varies between 172–289 dots depending on sprite count, SCX alignment, and window activation. Currently fixed at `PPU_MODE3_CYCLES`. Adjust Mode 0 duration to compensate so each scanline still totals 456 dots.
- **Window X=0 quirk** — Window triggered at WX=0 skips the first pixel; needs special handling in the render path.
- **Sprite priority edge cases** — When two sprites overlap, the one with the lower OAM index wins. Verify the current OAM scan order matches hardware priority rules.
- **SCX sub-tile scrolling** — Fine horizontal scroll (SCX mod 8) should discard the leftmost pixels from the BG FIFO, not shift the tile base.
- **LY=LYC coincidence flag on disable/enable** — When LCD is re-enabled, LY is reset to 0 and the coincidence check should fire immediately if LYC is also 0.
- **STAT interrupt blocking** — The STAT interrupt line is open-drain; simultaneous source enables can prevent a rising edge. Implement the STAT interrupt blocking behavior.

---

## 4. OAM DMA

**Status:** OAM DMA (`FF46` write) is instant — it copies 160 bytes immediately without locking the CPU bus.

- **DMA bus lock** — During DMA transfer the CPU may only access `FF80`–`FFFE` (HRAM). Lock all other reads/writes for 160 machine cycles (640 T-cycles) after `FF46` is written.
- **DMA source validation** — DMA source addresses above `DF00` produce undefined behavior on hardware; add a warning for out-of-range sources.

---

## 5. HALT / STOP Behavior

**Status:** `halt` sets `self.halted = True` and `stop` sets `self.stopped = True` but neither is fully accurate.

- **HALT bug** — When `HALT` is executed with `IME=0` and a pending interrupt, the CPU fails to increment PC after the next fetch. Implement the HALT bug so the following byte is executed twice.
- **HALT wake-up** — Exiting HALT should resume execution at the instruction after HALT and service the interrupt if IME was enabled.
- **STOP behavior** — `STOP` should halt both the CPU and LCD, clear the DIV register, and wait for a joypad button press before resuming. Currently it only sets a flag.

---

## 6. Timer Edge Cases

**Status:** DIV and TIMA timers are implemented but several hardware quirks are missing.

- **DIV reset side effect** — Writing any value to `FF03` (DIV) resets the internal 16-bit counter to 0. If the falling edge of the TIMA multiplexer bit occurs at the same moment, TIMA should increment once.
- **TIMA overflow delay** — After TIMA overflows, there is a 4-cycle window before TMA is reloaded and the interrupt is requested. Writing TIMA during this window cancels the reload.
- **TAC multiplexer bits** — TIMA should tick on the falling edge of the internal counter bit selected by TAC (bits 9, 3, 5, 7 for speeds 0–3), not by counting CPU cycles directly.

---

## 9. Cartridge

- **Checksum validation** — Verify the header checksum (`014D`) and global checksum (`014E`–`014F`) on load; warn if they fail.

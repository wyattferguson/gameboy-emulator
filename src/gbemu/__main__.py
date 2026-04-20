"""

This module is the command-line entry point used to launch the emulator process.

Step-by-step:
1. Define CLI flags for ROM path and debug behavior.
2. Parse arguments through Click decorators.
3. Construct a configured emulator instance.
4. Enter the main emulation loop.
5. Let process termination propagate through normal runtime exits.
"""

import click

from gbemu.config import DEFAULT_ROM
from gbemu.gbemu import Gbemu


@click.command()
@click.option(
    "--rom",
    "-r",
    type=str,
    default=DEFAULT_ROM,
    help="File to load the ROM from.",
)
@click.option(
    "--debug",
    "-d",
    default=False,
    is_flag=True,
    help="Enable debug mode. Used only for development.",
)
def run(rom: str = DEFAULT_ROM, debug: bool = False) -> None:
    """Run the emulator."""
    Gbemu(rom=rom, debug=debug).run()


if __name__ == "__main__":
    run()

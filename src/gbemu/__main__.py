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

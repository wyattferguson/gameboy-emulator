import click

from gbemu import gbemu

from ._config import DEFAULT_ROM


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
    """Run the Kanban application."""
    gb = gbemu(rom=rom, debug=debug)

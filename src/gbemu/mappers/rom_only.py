class RomOnlyMapper:
    """No-op mapper for plain ROM cartridges."""

    def initialize(self, memory: list[int]) -> None:  # noqa: ARG002
        return

    def handle_write(self, address: int, value: int, memory: list[int]) -> None:  # noqa: ARG002
        # ROM-only cartridges ignore writes in 0000-7FFF.
        return

    def load_bank(self, value: int, memory: list[int]) -> None:  # noqa: ARG002
        return

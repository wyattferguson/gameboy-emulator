from loguru import logger


class APU:
    """Audio Processing Unit (APU)."""

    def __init__(self) -> None:
        self.volume: int = 100

    def update(self) -> None:
        pass

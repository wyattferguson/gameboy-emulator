# http://gbdev.gg8.se/wiki/articles/Sound_Controller
# http://gbdev.gg8.se/wiki/articles/Gameboy_sound_hardware
# http://www.devrs.com/gb/files/hosted/GBSOUND.txt


class APU:
    """Audio Processing Unit (APU)."""

    def __init__(self) -> None:
        """Initialize placeholder APU state."""
        self.volume: int = 100

    def update(self) -> None:
        """Advance APU state for the current CPU step (stub)."""

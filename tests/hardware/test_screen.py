from random import randint

from gbemu.config import PALLETE, SCREEN_HEIGHT, SCREEN_WIDTH
from gbemu.screen import Screen


def test_pixel_drawing() -> None:
    """Test that drawing pixels on the screen works."""
    screen = Screen(scaler=1)
    expected_colors: dict[tuple[int, int], tuple[int, int, int]] = {}

    # Fill screen with random colors and track expected colors
    for y in range(SCREEN_HEIGHT):
        for x in range(SCREEN_WIDTH):
            color_id = randint(0, len(PALLETE) - 1)
            color = PALLETE[color_id]
            screen.draw_pixel(x, y, color)
            expected_colors[(x, y)] = color

    assert len(expected_colors) == SCREEN_HEIGHT * SCREEN_WIDTH

    # verify drawn pixels match expected colors
    for y in range(SCREEN_HEIGHT):
        for x in range(SCREEN_WIDTH):
            pixel = screen.screen.get_at((x * screen.scaler, y * screen.scaler))
            assert tuple(pixel[:3]) == expected_colors[(x, y)]

from types import SimpleNamespace

import pygame as pg
import pytest

from gbemu.constants import M_JOYPAD
from gbemu.controller import Controller
from gbemu.mmu import MMU


@pytest.mark.parametrize(
    ("keys", "select", "expected_pressed", "expected_released"),
    [
        ([pg.K_j], 0x10, 0xDE, 0xDF),           # A button
        ([pg.K_k], 0x10, 0xDD, 0xDF),           # B button
        ([pg.K_RETURN], 0x10, 0xD7, 0xDF),      # Start
        ([pg.K_RSHIFT], 0x10, 0xDB, 0xDF),      # Select
        ([pg.K_w], 0x20, 0xEB, 0xEF),           # Up
        ([pg.K_s], 0x20, 0xE7, 0xEF),           # Down
        ([pg.K_a], 0x20, 0xED, 0xEF),           # Left
        ([pg.K_d], 0x20, 0xEE, 0xEF),           # Right
        ([pg.K_j, pg.K_k], 0x10, 0xDC, 0xDF),  # A+B
        ([pg.K_w, pg.K_d], 0x20, 0xEA, 0xEF),  # Up+Right
    ],
)
def test_controller_input(
    monkeypatch: pytest.MonkeyPatch,
    keys: list[int],
    select: int,
    expected_pressed: int,
    expected_released: int,
) -> None:
    controller = Controller(MMU())
    controller.mmu[M_JOYPAD] = select

    monkeypatch.setattr(
        pg.event,
        "get",
        lambda: [SimpleNamespace(type=pg.KEYDOWN, key=key) for key in keys],
    )
    controller.update()
    assert controller.mmu[M_JOYPAD] == expected_pressed

    monkeypatch.setattr(
        pg.event,
        "get",
        lambda: [SimpleNamespace(type=pg.KEYUP, key=key) for key in keys],
    )
    controller.update()
    assert controller.mmu[M_JOYPAD] == expected_released


def test_controller_press_does_not_change_unselected_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = Controller(MMU())

    monkeypatch.setattr(
        pg.event,
        "get",
        lambda: [SimpleNamespace(type=pg.KEYDOWN, key=pg.K_a)],
    )
    controller.update()

    assert controller.mmu[M_JOYPAD] == 0xFF

from types import SimpleNamespace

import pygame as pg
import pytest

from gbemu.config import M_JOYPAD
from gbemu.controller import Controller
from gbemu.mmu import MMU


@pytest.mark.parametrize(
    ("keys", "expected_pressed", "expected_released"),
    [
        ([pg.K_a], 0xFE, 0xFF),
        ([pg.K_b], 0xFD, 0xFF),
        ([pg.K_RETURN], 0xF7, 0xFF),
        ([pg.K_LSHIFT], 0xFF, 0xFF),
        ([pg.K_UP], 0xEB, 0xEF),
        ([pg.K_DOWN], 0xE7, 0xEF),
        ([pg.K_LEFT], 0xED, 0xEF),
        ([pg.K_RIGHT], 0xEE, 0xEF),
        ([pg.K_a, pg.K_b], 0xFC, 0xFF),
        ([pg.K_UP, pg.K_RIGHT], 0xEA, 0xEF),
    ],
)
def test_controller_input(
    monkeypatch: pytest.MonkeyPatch,
    keys: list[int],
    expected_pressed: int,
    expected_released: int,
) -> None:
    controller = Controller(MMU())

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

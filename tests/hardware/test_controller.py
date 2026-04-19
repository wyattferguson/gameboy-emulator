from types import SimpleNamespace

import pygame as pg
import pytest

from gbemu.config import M_JOYPAD
from gbemu.controller import Controller
from gbemu.mmu import MMU


@pytest.mark.parametrize(
    ("keys", "select", "expected_pressed", "expected_released"),
    [
        ([pg.K_a], 0x10, 0xDE, 0xDF),
        ([pg.K_b], 0x10, 0xDD, 0xDF),
        ([pg.K_RETURN], 0x10, 0xD7, 0xDF),
        ([pg.K_LSHIFT], 0x10, 0xDB, 0xDF),
        ([pg.K_UP], 0x20, 0xEB, 0xEF),
        ([pg.K_DOWN], 0x20, 0xE7, 0xEF),
        ([pg.K_LEFT], 0x20, 0xED, 0xEF),
        ([pg.K_RIGHT], 0x20, 0xEE, 0xEF),
        ([pg.K_a, pg.K_b], 0x10, 0xDC, 0xDF),
        ([pg.K_UP, pg.K_RIGHT], 0x20, 0xEA, 0xEF),
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

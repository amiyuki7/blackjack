from __future__ import annotations
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from ..app import App

from ..app import State
import pygame as pg


class Round(State):
    def __init__(self, ctx: App) -> None:
        super().__init__(ctx)

    def update(self) -> None:
        return super().update()

    def render(self) -> None:
        return super().render()

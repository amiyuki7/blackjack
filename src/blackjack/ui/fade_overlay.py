from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..app import App

from .lib import UIState, UIObject
import pygame as pg


class FadeOverlay(UIObject):
    def __init__(self, ctx: App, target_state: UIState) -> None:
        self.rect = pg.rect.Rect(0, 0, ctx.display.get_width(), ctx.display.get_height())
        s = pg.Surface((self.rect.width, self.rect.height), pg.SRCALPHA)
        s.fill((0, 0, 0, 200))
        self.surface = s

        super().__init__(ctx, target_state)

    def update(self) -> None:
        pass

    def render(self) -> None:
        self.ctx.display.blit(self.surface, self.rect)

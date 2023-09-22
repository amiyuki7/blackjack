from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple, Type

if TYPE_CHECKING:
    from ..app import App

from ..app import State
from .round import Round

# importlib resources docs: https://docs.python.org/3.11/library/importlib.resources.html
from importlib import resources as impresources

import pygame as pg
import os
from math import floor


class AssetLoader:
    def __init__(self) -> None:
        all_assets = self.all_assets()

        self.to_load = iter(all_assets)
        self.expected_files = len(all_assets)

    @staticmethod
    def all_assets() -> List[str]:
        """Returns the absolute path of all assets"""
        return [
            str(resource)
            for resource in impresources.files("blackjack").joinpath("cards_png").iterdir()
            if resource.is_file() and resource.name.endswith(".png")
        ]

    def load_next(self) -> Tuple[str, pg.Surface] | None:
        path = next(self.to_load, None)

        if path is None:
            return

        filename = os.path.basename(path)
        key = os.path.splitext(filename)[0]

        return key, pg.image.load(path)


class Loading(State):
    def __init__(self, ctx: App) -> None:
        self.loader = AssetLoader()

        super().__init__(ctx)

    def update(self) -> None:
        if (t := self.loader.load_next()) is not None:
            key, surface = t
            self.ctx.images[key] = surface

    def render(self) -> None:
        loaded = len(self.ctx.images) / self.loader.expected_files

        screen_w, screen_h = self.ctx.display.get_width(), self.ctx.display.get_height()
        rect_w, rect_h = (screen_w // 2.5), screen_h // 30
        x, y = (screen_w - rect_w) // 2, (screen_h - rect_h) // 2

        progress_rect = pg.Rect(x, y, rect_w * loaded, rect_h)
        pg.draw.rect(self.ctx.display, (80, 230, 80), progress_rect, border_radius=45)

        font = pg.font.Font(
            str(impresources.files("blackjack").joinpath("fonts/KozGoPro-Bold.otf")), 30
        )
        text = font.render(f"{floor(loaded * 100)}%", True, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.right = progress_rect.right
        text_rect.y = progress_rect.y + floor(text_rect.height * 1.8)

        self.ctx.display.blit(text, text_rect)

        if loaded == 1:
            self.pend(Round)

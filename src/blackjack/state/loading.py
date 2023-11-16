from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from ..app import App

from ..app import State
from ..util import get_evenly_spaced_points
from .table import Table

# importlib resources docs: https://docs.python.org/3.11/library/importlib.resources.html
from importlib import resources as impresources

import pygame as pg
import os
from math import floor
from loguru import logger


class AssetLoader:
    def __init__(self) -> None:
        all_assets = self.all_assets()

        self.to_load = iter(all_assets)
        self.expected_files = len(all_assets)

    @staticmethod
    def all_assets() -> List[str]:
        """Returns the absolute path of all assets"""
        cards = [
            str(resource)
            for resource in impresources.files("blackjack").joinpath("cards_png").iterdir()
            if resource.is_file() and resource.name.endswith(".png")
        ]

        other_assets = [
            str(resource)
            for resource in impresources.files("blackjack").joinpath("assets").iterdir()
            if resource.is_file() and resource.name.endswith(".png")
        ]

        # Flattened list of all asset paths
        return [res for sub in [cards, other_assets] for res in sub]

    def load_next(self) -> Tuple[str, pg.Surface] | None:
        path = next(self.to_load, None)

        if path is None:
            return None

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

        if len(self.ctx.zones) == 0:
            # Load all zone positions
            screen_w, screen_h = self.ctx.display.get_width(), self.ctx.display.get_height()
            card = pg.image.load(str(impresources.files("blackjack").joinpath("assets/0cardfront.png")))
            card = pg.transform.scale(card, (card.get_width() * 0.14, card.get_height() * 0.14))
            padding = card.get_width() // 4

            self.ctx.zones["deck"] = pg.rect.Rect(
                screen_w - card.get_width() - padding, padding, card.get_width(), card.get_height()
            )
            self.ctx.zones["burn"] = pg.rect.Rect(padding, padding, card.get_width(), card.get_height())

            n_zones = 4
            zone_width = screen_w / 4.5
            for idx, point in enumerate(get_evenly_spaced_points(screen_w, zone_width, n_zones)):
                zone_rect = pg.rect.Rect(point, screen_h - 1.5 * zone_width, zone_width, zone_width)

                # Partition the zone into 4 subzones for each hand
                zone_tl = pg.rect.Rect(zone_rect.x, zone_rect.top, zone_width // 2, zone_width // 2)
                zone_tr = pg.rect.Rect(zone_tl.right, zone_rect.top, zone_width // 2, zone_width // 2)
                zone_bl = pg.rect.Rect(zone_rect.x, zone_tl.bottom, zone_width // 2, zone_width // 2)
                zone_br = pg.rect.Rect(zone_bl.right, zone_tr.bottom, zone_width // 2, zone_width // 2)
                stat_rect = pg.rect.Rect(zone_rect.x, zone_rect.bottom, zone_width, zone_width // 2 * 3 / 5)
                bet_rect = pg.rect.Rect(zone_rect.x, stat_rect.bottom, zone_width, zone_width // 2 * 2 / 5)

                self.ctx.zones[f"tl_{idx}"] = zone_tl
                self.ctx.zones[f"tr_{idx}"] = zone_tr
                self.ctx.zones[f"bl_{idx}"] = zone_bl
                self.ctx.zones[f"br_{idx}"] = zone_br
                self.ctx.zones[f"stat_{idx}"] = stat_rect
                self.ctx.zones[f"bet_{idx}"] = bet_rect

    def render(self) -> None:
        loaded = len(self.ctx.images) / self.loader.expected_files

        screen_w, screen_h = self.ctx.display.get_width(), self.ctx.display.get_height()
        rect_w, rect_h = (screen_w // 2.5), screen_h // 30
        x, y = (screen_w - rect_w) // 2, (screen_h - rect_h) // 2

        progress_rect = pg.Rect(x, y, rect_w * loaded, rect_h)
        pg.draw.rect(self.ctx.display, (80, 230, 80), progress_rect, border_radius=45)

        font = pg.font.Font(str(impresources.files("blackjack").joinpath("fonts/KozGoPro-Bold.otf")), 30)
        text = font.render(f"{floor(loaded * 100)}%", True, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.right = progress_rect.right
        text_rect.y = progress_rect.y + floor(text_rect.height * 1.8)

        self.ctx.display.blit(text, text_rect)

        if loaded == 1:
            self.pend(Table)

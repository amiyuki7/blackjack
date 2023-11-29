from __future__ import annotations
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from ..app import App

from .lib import UIState, UIObject
from importlib import resources as impresources
import pygame as pg


class BetBox(UIObject):
    def __init__(self, ctx: App, target_state: UIState) -> None:
        # Ratio of the rectangle
        width = ctx.display.get_width() / 5
        height = width / 5

        self.rect = pg.rect.Rect(0, 0, width, height)
        self.rect.centerx, self.rect.centery = ctx.display.get_rect().center
        self.rect.y -= ctx.display.get_height() // 5

        s = pg.Surface((self.rect.width, self.rect.height), pg.SRCALPHA)
        s.fill((0, 0, 0, 100))
        self.inp_surface = s

        self.min_bet, self.max_bet = 100, 10000
        self.bet_val: str = ""
        self.bet_font = pg.font.Font(
            str(impresources.files("blackjack").joinpath("fonts/KozGoPro-Bold.otf")), self.rect.height // 2
        )
        self.sub_font = pg.font.Font(
            str(impresources.files("blackjack").joinpath("fonts/KozGoPro-Light.otf")), self.rect.height // 4
        )
        self.text = self.bet_font.render("", True, (255, 255, 255))

        self.min_bet_text = self.sub_font.render(f"Min bet: {self.min_bet}", True, (200, 200, 200))
        self.max_bet_text = self.sub_font.render(f"Max bet: {self.max_bet}", True, (200, 200, 200))

        super().__init__(ctx, target_state)

    def handle_key_update(self, event: pg.event.Event) -> None:
        if (key := event.key) in (codes := [pg.K_1, pg.K_2, pg.K_3, pg.K_4, pg.K_5, pg.K_6, pg.K_7, pg.K_8, pg.K_9]):
            self.bet_val += str(codes.index(key) + 1)

        if event.key == pg.K_0:
            if len(self.bet_val) > 0:
                self.bet_val += "0"

        if event.key == pg.K_BACKSPACE:
            self.bet_val = self.bet_val[0:-1]

        if event.key == pg.K_RETURN:
            if len(self.bet_val) > 0:
                if self.min_bet <= int(self.bet_val) <= self.max_bet:
                    from blackjack.state.table import Table, Player

                    assert type(self.ctx.state) == Table
                    player = self.ctx.state.filter_players(lambda player: type(player) == Player)[0]
                    player.round_bet = int(self.bet_val)

        # Max bet check
        if len(self.bet_val) > 0:
            if int(self.bet_val) > self.max_bet:
                self.bet_val = self.bet_val[0:-1]

    def get_bet_text_colour(self) -> Tuple[int, int, int]:
        # Red if doesn't pass the minimum bet
        if len(self.bet_val) == 0:
            return (0, 0, 0)

        assert int(self.bet_val)
        if int(self.bet_val) < self.min_bet:
            return (255, 0, 0)
        else:
            return (0, 255, 0)

    def update(self) -> None:
        self.text = self.bet_font.render(" " + self.bet_val, True, self.get_bet_text_colour())

    def render(self) -> None:
        self.ctx.display.blit(self.inp_surface, self.rect)
        self.ctx.display.blit(self.text, (self.rect.x, self.rect.y + self.rect.height * 0.25))
        self.ctx.display.blit(self.min_bet_text, (self.rect.x, self.rect.top - self.min_bet_text.get_height()))
        self.ctx.display.blit(
            self.max_bet_text,
            (self.rect.right - self.max_bet_text.get_width(), self.rect.top - self.max_bet_text.get_height()),
        )

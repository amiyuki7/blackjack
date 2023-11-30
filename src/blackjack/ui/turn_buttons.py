from __future__ import annotations
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from ..app import App

from enum import Enum, auto
from .lib import UIState, UIObject
from ..util import in_radial_distance
import pygame as pg
from loguru import logger
from importlib import resources as impresources


class ActionType(Enum):
    Hit = auto()
    Stand = auto()
    Split = auto()
    Double = auto()

    @staticmethod
    def get_colour(action_type: ActionType) -> Tuple[int, int, int]:
        match action_type:
            case ActionType.Hit:
                return (50, 193, 44)  # 32c12c
            case ActionType.Stand:
                return (212, 12, 96)  # d40c60
            case ActionType.Split:
                return (82, 110, 255)  # 526eff
            case ActionType.Double:
                return (255, 207, 72)  # ffcf48

    @staticmethod
    def get_left_offset(action_type: ActionType, button_radius: int) -> int:
        match action_type:
            case ActionType.Hit:
                return button_radius * 10
            case ActionType.Stand:
                return button_radius * 8
            case ActionType.Split:
                return button_radius * 6
            case ActionType.Double:
                return button_radius * 4


class TurnButton(UIObject):
    def __init__(self, ctx: App, action_type: ActionType, target_state: UIState) -> None:
        self.is_disabled = False
        self.is_hovered = False
        self.is_clicked = False
        self.action_type = action_type

        self.radius = ctx.display.get_width() // 24

        self.rect = pg.rect.Rect(0, 0, self.radius * 2, self.radius * 2)
        # These values are aligned with the dealer zone
        self.rect.center = ctx.display.get_rect().center
        self.rect.centery -= ctx.display.get_rect().height // 5

        self.colour = ActionType.get_colour(action_type)
        self.rect.x -= ActionType.get_left_offset(action_type, self.radius)

        self.text_font = pg.font.Font(
            str(impresources.files("blackjack").joinpath("fonts/KozGoPro-Bold.otf")), self.rect.height // 5
        )

        super().__init__(ctx, target_state)

    def handle_mouse_hover(self, event: pg.event.Event) -> None:
        if not self.is_disabled:
            self.colour = (
                (255, 255, 255)
                if in_radial_distance(self.rect.center, self.radius, event.pos)
                else ActionType.get_colour(self.action_type)
            )

    def handle_mouse_click(self, event: pg.event.Event) -> None:
        if self.colour == (255, 255, 255):
            # Is hovered
            self.is_clicked = True

    def update(self) -> None:
        from blackjack.state.table import Table

        assert type(self.ctx.state) == Table

        if self.is_disabled:
            self.colour = (100, 100, 100)

        player_id, hand_idx = self.ctx.state.current_turn
        player = self.ctx.state.filter_players(lambda player: player.id == player_id)[0]
        target_hand = player.hands[hand_idx]

        # Enable all buttons after Movables have finished moving, but...
        # If the action associated with the button is invalid, then disable the button
        if len(self.ctx.state.movables) == 0:
            self.is_disabled = False
            if self.action_type == ActionType.Split:
                self.is_disabled = not (player.allowed_to_potentially_split() and target_hand.allowed_to_split())
            elif self.action_type == ActionType.Double:
                self.is_disabled = not target_hand.allowed_to_double()

    def render(self) -> None:
        pg.draw.circle(self.ctx.display, self.colour, self.rect.center, self.rect.width / 2.25)
        text = self.text_font.render(self.action_type.name, True, (0, 0, 0))
        self.ctx.display.blit(
            text, (self.rect.centerx - text.get_width() // 2, self.rect.centery - text.get_height() // 2)
        )

    def onclick(self) -> None:
        pass

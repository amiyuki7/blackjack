from __future__ import annotations
from typing import Dict, List, Optional, Type

import os, sys, pygame as pg

from abc import ABC, abstractmethod

from loguru import logger

from blackjack.ui.turn_buttons import ActionType

from .util import Vec2
from .ui import UIState, UIObject, FadeOverlay, BetBox, TurnButton

# Setup logging
ENABLE_LOGGING = os.environ.get("BLACKJACK_ENABLE_LOGGING", "no")

if ENABLE_LOGGING == "yes":
    logger.remove(0)
    logger.add(
        "log/{time:YYYY-MMM-D@H:mm:ss}.log",
        format="{time:HH:mm:ss} | {level} | {file}:{function}:{line} -> {message}",
        level="TRACE",
    )
else:
    logger.disable("blackjack")


pg.init()


class Drawable(ABC):
    pos: Vec2
    image_key: str

    def draw(self, ctx: App) -> None:
        """"""
        image = ctx.images[self.image_key]
        blit_rect = pg.rect.Rect(self.pos.x, self.pos.y, image.get_width(), image.get_height())
        ctx.display.blit(image, blit_rect)


class State(ABC):
    def __init__(self, ctx: App) -> None:
        self.ctx = ctx
        self.pend_state = Optional[Type[State]]

    @abstractmethod
    def update(self) -> None:
        """"""

    @abstractmethod
    def render(self) -> None:
        """"""

    def pend(self, state: Type[State]) -> None:
        """"""
        self.ctx.state = state(self.ctx)

        logger.debug(f"[DEBUG] State transitioned to {type(self.ctx.state).__name__}")


class App:
    def __init__(self, state: Type[State]) -> None:
        self.state = state(self)
        self.ui_state = UIState.Normal
        self.clock = pg.time.Clock()
        self.dt: float

        self.display = pg.display.set_mode((1920, 1080), pg.FULLSCREEN)
        pg.display.set_caption("Blackjack")

        self.images: Dict[str, pg.Surface] = {}
        self.zones: Dict[str, pg.Rect] = {}
        """
        <d> = 0|1|2|3
        keys: ["deck", "burn", "hand_bl_<d>", "hand_br_<d>", "hand_tl_<d>", "hand_tr_<d>", "stat_<d>", "bet_<d>"]
        """

        self.ui_objects: List[UIObject] = []
        self.ui_objects.append(FadeOverlay(self, UIState.Bet))
        self.ui_objects.append(BetBox(self, UIState.Bet))

        for action_type in ActionType:
            self.ui_objects.append(b := TurnButton(self, action_type, UIState.Turn))
            logger.debug(f"Appended {action_type} Button {repr(b)}")

    def update(self) -> None:
        self.state.update()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                match self.ui_state:
                    case UIState.Normal:
                        pass
                    case UIState.Bet:
                        # Filter out the bet box object
                        [u for u in self.ui_objects if type(u) == BetBox][0].handle_key_update(event)
            if event.type == pg.MOUSEMOTION:
                match self.ui_state:
                    case UIState.Turn:
                        [u.handle_mouse_hover(event) for u in self.ui_objects if type(u) == TurnButton]
            if event.type == pg.MOUSEBUTTONDOWN:
                match self.ui_state:
                    case UIState.Turn:
                        [u.handle_mouse_click(event) for u in self.ui_objects if type(u) == TurnButton]

        # Only update UI Objects during the correct UI State
        for obj in self.ui_objects:
            if obj.target_state == self.ui_state:
                obj.update()

    def render(self) -> None:
        self.display.fill((0, 0, 0))
        self.state.render()

        # Overlayed UI renders
        for obj in self.ui_objects:
            if obj.target_state == self.ui_state:
                obj.render()

    def run(self) -> None:
        while 1:
            self.update()
            self.render()

            self.dt = self.clock.tick(60) / 1000
            pg.display.flip()

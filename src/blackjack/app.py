from __future__ import annotations
from typing import Dict, List, Optional, Sized, Type

import enum, os, sys, math, pygame as pg

from pygame.locals import *
from abc import ABC, abstractmethod

from loguru import logger
from .util import Vec2

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


# class Suit(enum.Enum):
#     Diamond = enum.auto()
#     Club = enum.auto()
#     Heart = enum.auto()
#     Spade = enum.auto()
#
#
# class Card:
#     def __init__(self, value: Optional[int], suit: Suit) -> None:
#         self.texture = ""
#         self.value = value
#         self.suit = suit
#         # check if value is none then decide
#         self.is_ace: bool = False
#
#
# class Hand:
#     def __init__(self) -> None:
#         self.cards: List[Card] = []
#
#     def calculate_value(self) -> int:
#         return 0
#
#
# class Player:
#     def __init__(self) -> None:
#         self.hand = Hand()
#
#
# class Dealer(Player):
#     pass


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
        self.clock = pg.time.Clock()
        self.dt: float

        self.display = pg.display.set_mode((1920, 1080), pg.FULLSCREEN)
        pg.display.set_caption("Blackjack")

        self.images: Dict[str, pg.Surface] = {}
        self.zones: Dict[str, pg.Rect] = {}

    def update(self) -> None:
        self.state.update()

        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_w:
                    logger.info("yay")

    def render(self) -> None:
        self.display.fill((0, 0, 0))
        self.state.render()

    def run(self) -> None:
        while 1:
            self.update()
            self.render()

            self.dt = self.clock.tick(60) / 1000
            pg.display.flip()

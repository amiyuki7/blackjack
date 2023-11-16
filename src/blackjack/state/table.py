from __future__ import annotations
from os import stat, walk, write
from typing import TYPE_CHECKING, List, Dict, Tuple
from typing_extensions import override

from pygame.transform import scale, set_smoothscale_backend

if TYPE_CHECKING:
    from ..app import App

from ..app import Drawable, State
from ..util import Vec2, get_evenly_spaced_points

from enum import Enum, auto
from importlib import resources as impresources
import pygame as pg
import itertools
import random
from queue import LifoQueue
from loguru import logger


class Player:
    def __init__(self, id: int) -> None:
        self.hands: List[Hand] = []
        self.id = id


class Bot(Player):
    def __init__(self, id: int) -> None:
        super().__init__(id)


class Dealer(Player):
    def __init__(self, id: int) -> None:
        super().__init__(id)


class Card(Drawable):
    def __init__(self, value: int, suit: str, image_key: str) -> None:
        self.value = value
        self.suit = suit
        self.image_key = image_key
        """
        Usage within a State class:

        ```
        self.ctx.images[card.image_key]
        ```
        """
        self.is_ace = value == -1

    @override
    def draw(self, ctx: App) -> None:
        card_front = ctx.images["0cardfront"]
        card_front = pg.transform.scale(card_front, (card_front.get_width() * 0.14, card_front.get_height() * 0.14))

        card = pg.Surface(card_front.get_size(), pg.SRCALPHA)
        card.blit(card_front, (0, 0))
        scaled_face = pg.transform.scale(ctx.images[self.image_key], (card.get_width() * 0.7, card.get_height() * 0.7))

        card.blit(
            scaled_face,
            ((card.get_width() - scaled_face.get_width()) // 2, (card.get_height() - scaled_face.get_height()) // 2),
        )

        blit_rect = pg.rect.Rect(self.pos.x, self.pos.y, card.get_width(), card.get_height())
        ctx.display.blit(card, blit_rect)


class Hand:
    def __init__(self, cards: List[Card]) -> None:
        self.cards = cards


class Deck:
    def __init__(self, n_decks: int) -> None:
        self.__card_queue: LifoQueue[str] = LifoQueue()
        self.n_decks = n_decks

    def new_shuffled_deck(self) -> None:
        cards = [
            [
                "_of_".join(card)
                for card in itertools.product(
                    ["2", "3", "4", "5", "6", "7", "8", "9", "10", "ace", "jack", "queen", "king"],
                    ["diamonds", "clubs", "hearts", "spades"],
                )
            ]
            for _ in range(0, self.n_decks)
        ]
        flattened = list(itertools.chain(*cards))
        random.shuffle(flattened)
        self.__card_queue.queue = flattened

    def poptop(self) -> Card:
        top = self.__card_queue.get()
        # String format is "<value>_of_<suit>"
        value, suit = (parts := top.split("_"))[0], parts[-1]

        match value:
            case s if s in ["jack", "queen", "king"]:
                val = 10
            case "ace":
                val = -1
            case _:
                val = int(value)

        return Card(val, suit, top)

    def is_exhausted(self) -> bool:
        return self.__card_queue.empty()


class GamePhase(Enum):
    Initial = auto()
    Deal = auto()
    Play = auto()
    EndRound = auto()


class Movable:
    def __init__(self, obj: Drawable, dest: Vec2, speed: int) -> None:
        """speed | how long (ms) the object should take to reach its destination"""
        self.obj = obj
        self.dest = dest
        self.speed = speed

        self.is_headed_right = self.obj.pos.x < self.dest.x
        self.is_headed_down = self.obj.pos.y < self.dest.y

    def move(self, dt: float) -> None:
        """
        Returns
            - True  | The object has reached its destination
            - False | It has not
        """
        direction = (self.dest - self.obj.pos).unit()
        scaled_direction = direction * self.speed * dt

        # If the distance between the destination and position is less than the to be added vector, then we're done!
        # This check is necessary for locking the object to the destination because of adding non-constant floats
        if (self.dest - self.obj.pos).magn() < scaled_direction.magn():
            self.obj.pos = self.dest
        else:
            self.obj.pos += Vec2(direction.x * self.speed * dt, direction.y * self.speed * dt)

    def is_done(self) -> bool:
        """Check if the object has arrived at its destination"""
        return self.obj.pos.x == self.dest.x and self.obj.pos.y == self.dest.y


class Table(State):
    def __init__(self, ctx: App) -> None:
        # Dealer will always have the id 0, and the player will always have the id 1
        self.players = [Dealer(0), Player(1), Bot(2), Bot(3), Bot(4)]
        self.deck = Deck(n_decks=6)
        self.deck.new_shuffled_deck()
        self.game_phase: GamePhase = GamePhase.Initial
        self.movables: List[Movable] = []
        self.game_objects: List[Drawable] = []

        super().__init__(ctx)

    def update(self) -> None:
        match self.game_phase:
            case GamePhase.Initial:
                # Dummy phase for now, but implemented like this so it's easier to write any events
                # that could happen before the deal phase in the future
                top_card = self.deck.poptop()
                top_card.pos = Vec2(500, 100)

                self.movables.append(Movable(top_card, dest=Vec2(50, 600), speed=1000))
                self.game_phase = GamePhase.Deal
                pass
            case GamePhase.Deal:
                pass
            case _:
                pass

        for movable in self.movables:
            movable.move(self.ctx.dt)
            if movable.is_done():
                self.game_objects.append(movable.obj)
                self.movables.remove(movable)

    def render(self) -> None:
        self.ctx.display.fill((255, 0, 0))
        screen_w, screen_h = self.ctx.display.get_width(), self.ctx.display.get_height()

        # Draw the deck of cards
        card_front = pg.image.load(str(impresources.files("blackjack").joinpath("assets/0cardfront.png")))
        card_front = pg.transform.scale(card_front, (card_front.get_width() * 0.14, card_front.get_height() * 0.14))

        padding = card_front.get_width() // 4

        deck_pos = pg.rect.Rect(
            screen_w - card_front.get_width() - padding, padding, card_front.get_width(), card_front.get_height()
        )
        self.ctx.display.blit(card_front, deck_pos)

        # Draw the burned pile
        burned_pos = pg.rect.Rect(padding, padding, card_front.get_width(), card_front.get_height())
        self.ctx.display.blit(card_front, burned_pos)

        # Draw rectangles for every zone
        n_zones = 4
        zone_width = screen_w / 4.5

        for point in get_evenly_spaced_points(screen_w, zone_width, n_zones):
            zone_rect = pg.rect.Rect(point, screen_h - 1.5 * zone_width, zone_width, zone_width)
            # pg.draw.rect(self.ctx.display, (0, 255, 0), zone_rect)

            # Draw four partitions of the zone for four possible hands
            zone_tl = pg.rect.Rect(zone_rect.x, zone_rect.top, zone_width // 2, zone_width // 2)
            zone_tr = pg.rect.Rect(zone_tl.right, zone_rect.top, zone_width // 2, zone_width // 2)
            zone_bl = pg.rect.Rect(zone_rect.x, zone_tl.bottom, zone_width // 2, zone_width // 2)
            zone_br = pg.rect.Rect(zone_bl.right, zone_tr.bottom, zone_width // 2, zone_width // 2)
            pg.draw.rect(self.ctx.display, (50, 50, 50), zone_tl)
            pg.draw.rect(self.ctx.display, (100, 100, 100), zone_tr)
            pg.draw.rect(self.ctx.display, (150, 150, 150), zone_bl)
            pg.draw.rect(self.ctx.display, (0, 0, 255), zone_br)

            stat_rect = pg.rect.Rect(zone_rect.x, zone_rect.bottom, zone_width, zone_width // 2 * 3 / 5)
            pg.draw.rect(self.ctx.display, (0, 130, 0), stat_rect)

            bet_rect = pg.rect.Rect(zone_rect.x, stat_rect.bottom, zone_width, zone_width // 2 * 2 / 5)
            pg.draw.rect(self.ctx.display, (0, 50, 0), bet_rect)

        # Draw the stack of cards in each hand to each corresponding zone / partitioned zone
        # Generalise the spacing for a diagonal vector

        # Draw all game objects
        for movable in self.movables:
            movable.obj.draw(self.ctx)

        for game_object in self.game_objects:
            game_object.draw(self.ctx)

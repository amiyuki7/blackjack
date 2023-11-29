from __future__ import annotations
from typing import TYPE_CHECKING, Callable, List
from typing_extensions import override

if TYPE_CHECKING:
    from ..app import App

from ..app import Drawable, State
from ..ui import UIState
from ..util import Vec2

from enum import Enum, auto
from importlib import resources as impresources
import pygame as pg
import itertools
import random
from queue import LifoQueue


class Player:
    def __init__(self, id: int) -> None:
        self.hands: List[Hand] = [Hand()]
        self.id = id
        self.balance = 100000

        self.round_bet = 0

        self.current_hand = 0

    def add_card(self, card: Card) -> None:
        self.hands[self.current_hand].cards.append(card)


class Bot(Player):
    def __init__(self, id: int) -> None:
        super().__init__(id)

    def decide_bet(self) -> None:
        # Not going to add heuristics for betting - just random value
        # Check blackjack.ui.bet_box for min/max bet values
        min_bet, max_bet = 100, 5000
        self.round_bet = random.randrange(min_bet, max_bet + 1)


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
        self.is_facedown = False

    @override
    def draw(self, ctx: App) -> None:
        if self.is_facedown or self.image_key == "0cardback":
            card = ctx.images["0cardback"]
            card = pg.transform.scale(card, (card.get_width() * 0.14, card.get_height() * 0.14))
            blit_rect = pg.rect.Rect(self.pos.x, self.pos.y, card.get_width(), card.get_height())
            ctx.display.blit(card, blit_rect)
            return

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
    def __init__(self) -> None:
        self.cards: List[Card] = []

        self.is_doubled = False

    def calculate_value(self) -> int:
        cum = 0
        non_aces = [card for card in self.cards if not card.is_ace]

        for card in non_aces:
            cum += card.value

        aces = set(self.cards) - set(non_aces)
        no_aces = len(aces)
        # If there are more than 1 ace, then you can at most have ONE ace that is valued at 11. Thus, if we have n > 1
        # aces, we add n-1 to the cumulative value and then check whether the last ace can be valued at 11.
        if no_aces > 0:
            if no_aces > 1:
                cum += no_aces - 1

            try_plus_11 = cum + 11

            if try_plus_11 > 21:
                cum += 1
            else:
                cum += 11

        return cum


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
    Bet = auto()
    Deal = auto()
    Play = auto()
    EndRound = auto()


class Movable:
    def __init__(self, obj: Drawable, dest: Vec2, speed: int) -> None:
        """speed | how long (ms) the object should take to reach its destination"""
        self.obj = obj
        self.dest = dest
        self.speed = speed

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
        self.players: List[Player] = [Dealer(-1), Player(0), Bot(1), Bot(2), Bot(3)]
        self.deck = Deck(n_decks=6)
        self.deck.new_shuffled_deck()
        self.game_phase: GamePhase = GamePhase.Initial
        self.movables: List[Movable] = []
        self.game_objects: List[Drawable] = []

        self.deal_counter: int = 0

        self.stats_font = pg.font.Font(
            str(impresources.files("blackjack").joinpath("fonts/KozGoPro-Light.otf")), ctx.zones["bet_0"].height // 2
        )

        self.DEBUG_FORCE_DEALER_BLACKJACK = False

        super().__init__(ctx)

    def filter_players(self, condition: Callable[[Player], bool]) -> List[Player]:
        return [player for player in self.players if condition(player)]

    def update(self) -> None:
        match self.game_phase:
            case GamePhase.Initial:
                # Dummy phase for now, but implemented like this so it's easier to write any events
                # that could happen before the deal phase in the future
                deck_zone = self.ctx.zones["deck"].topleft

                burn_card = self.deck.poptop()
                burn_card.pos = Vec2(deck_zone[0], deck_zone[1])
                burn_card.image_key = "0cardback"
                burn_zone = self.ctx.zones["burn"].topleft
                self.movables.append(Movable(burn_card, dest=Vec2(burn_zone[0], burn_zone[1]), speed=2000))

                self.game_phase = GamePhase.Bet
            case GamePhase.Bet:
                self.ctx.ui_state = UIState.Bet

                player = self.filter_players(lambda player: type(player) == Player)[0]
                if player.round_bet != 0:
                    self.game_phase = GamePhase.Deal
                    self.ctx.ui_state = UIState.Normal

                    # This will only run once
                    [x.decide_bet() for x in self.players if type(x) == Bot]

            case GamePhase.Deal:
                if self.deal_counter < 2 and len(self.movables) == 0:
                    for i in range(-1, 4):
                        target = self.filter_players(lambda player: player.id == i)[0]

                        if i == -1 and self.DEBUG_FORCE_DEALER_BLACKJACK:
                            if self.deal_counter == 0:
                                top_card = Card(10, suit="spades", image_key="queen_of_spades")
                            else:
                                top_card = Card(-1, suit="hearts", image_key="ace_of_hearts")
                        else:
                            top_card = self.deck.poptop()

                        top_card.pos = Vec2(*self.ctx.zones["deck"].topleft)

                        # Second card for the dealer is face down
                        if self.deal_counter == 1 and i == -1:
                            top_card.is_facedown = True

                        target.add_card(top_card)

                        zone = self.ctx.zones[f"hand_{'dealer' if i == -1 else f'bl_{i}'}"].topleft
                        zone = (zone[0] + self.deal_counter * 25, zone[1] + self.deal_counter * 25)
                        self.movables.append(Movable(top_card, dest=Vec2(zone[0], zone[1]), speed=2000))

                    self.deal_counter += 1

                if self.deal_counter >= 2 and len(self.movables) == 0:
                    self.game_phase = GamePhase.Play

            case GamePhase.Play:
                dealer = self.filter_players(lambda player: type(player) == Dealer)[0]
                if dealer.hands[0].calculate_value() == 21:
                    for card in dealer.hands[0].cards:
                        card.is_facedown = False

                    self.game_phase = GamePhase.EndRound
            case GamePhase.EndRound:
                # Reset bets to 0
                for player in self.players:
                    player.round_bet = 0
            case _:
                pass

        for movable in self.movables:
            movable.move(self.ctx.dt)
            if movable.is_done():
                self.game_objects.append(movable.obj)
                self.movables.remove(movable)

    def render(self) -> None:
        self.ctx.display.fill((255, 0, 0))

        for zone_name, rect in self.ctx.zones.items():
            if "hand" in zone_name:
                pg.draw.rect(self.ctx.display, (80, 140, 60), rect)
            if "stat" in zone_name:
                pg.draw.rect(self.ctx.display, (80, 80, 80), rect)
            if "bet" in zone_name:
                pg.draw.rect(self.ctx.display, (30, 30, 30), rect)
            if zone_name == "deck":
                card = pg.image.load(str(impresources.files("blackjack").joinpath("assets/0cardback.png")))
                card = pg.transform.scale(card, (card.get_width() * 0.14, card.get_height() * 0.14))
                self.ctx.display.blit(card, rect)

        # Draw the stack of cards in each hand to each corresponding zone / partitioned zone
        # Generalise the spacing for a diagonal vector

        # Draw all game objects
        for movable in self.movables:
            movable.obj.draw(self.ctx)

        for game_object in self.game_objects:
            game_object.draw(self.ctx)

        if self.game_phase in [GamePhase.Bet, GamePhase.Deal, GamePhase.Play]:
            # Draw the bet text
            for player in self.players:
                id = player.id
                if id == -1:
                    # Dealer
                    continue

                bet_text = self.stats_font.render(f"Bet: ${player.round_bet}", True, (255, 255, 255))
                rect = self.ctx.zones[f"bet_{id}"]
                self.ctx.display.blit(bet_text, (rect.left + rect.height // 4, rect.top + rect.height // 4))

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..app import App

from abc import ABC, abstractmethod
from enum import Enum, auto
import pygame as pg


class UIState(Enum):
    Normal = auto()
    Bet = auto()


class UIObject(ABC):
    def __init__(self, ctx: App, target_state: UIState) -> None:
        self.rect: pg.rect.Rect
        self.ctx = ctx
        self.target_state = target_state

    @abstractmethod
    def update(self) -> None:
        """"""

    @abstractmethod
    def render(self) -> None:
        """"""

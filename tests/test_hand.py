import pytest
from typing import List
from blackjack.state.table import Hand, Card

from . import FromFixture


@pytest.fixture
def hand() -> Hand:
    return Hand()


def ValCard(value: int) -> Card:
    """Returns a card which only focuses on the value"""
    return Card(value, "", "")


@pytest.mark.parametrize(
    "cards, expected_value",
    [
        ([ValCard(5), ValCard(10), ValCard(3)], 18),
        ([ValCard(10), ValCard(10)], 20),
        ([ValCard(-1), ValCard(10)], 21),
        ([ValCard(-1), ValCard(3), ValCard(5), ValCard(10)], 19),
        ([ValCard(-1), ValCard(-1), ValCard(5), ValCard(10), ValCard(8)], 25),
        ([ValCard(6), ValCard(-1), ValCard(4)], 21),
    ],
)
def test_expected_value(hand: FromFixture[Hand], cards: List[Card], expected_value: int):
    hand.cards.extend(cards)
    assert hand.calculate_value() == expected_value

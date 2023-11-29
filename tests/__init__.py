import pytest
import typing

T = typing.TypeVar("T")
FromFixture = typing.Annotated[T, pytest.fixture]

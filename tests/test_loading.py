import pytest
from blackjack.state.loading import AssetLoader


def test_asset_loader():
    asset_loader = AssetLoader()
    assert asset_loader.expected_files == 56

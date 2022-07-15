from serde.toml import from_toml

from sbatcher.config import Options


def test_value_array() -> None:
    toml = r"""
    account = "me"
    array = {values=[1, 2, 3], max_parallel=4}
    """

    options = from_toml(Options, toml)
    assert options.account == "me"
    assert options.array is not None
    assert options.array.values == [1, 2, 3]
    assert options.array.max_parallel == 4


def test_range_array() -> None:
    toml = r"""
    account = "you"
    array = {range=[1, 100, 20], max_parallel=4}
    """

    options = from_toml(Options, toml)
    assert options.account == "you"
    assert options.array is not None
    assert options.array.range_ == [1, 100, 20]

import pytest
from serde import SerdeError
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


def test_cluster_constraint() -> None:
    t1 = r"""
    cluster_constraint = {features = ["foo"]}
    """
    cluter_constraint = from_toml(Options, t1).cluster_constraint
    assert cluter_constraint.features == ["foo"]

    t2 = r"""
    cluster_constraint = {exclude = true, features = ["foo", "bar"]}
    """
    cluter_constraint = from_toml(Options, t2).cluster_constraint
    assert cluter_constraint.exclude
    assert cluter_constraint.features == ["foo", "bar"]

    t3 = r"""
    cluster_constraint = {exclude = true}
    """
    with pytest.raises(SerdeError):
        from_toml(Options, t3)


def test_cpu_freq() -> None:
    t1 = r"""
    cpu_freq = {p1 = "low"}
    """

    cpu_freq = from_toml(Options, t1).cpu_freq
    assert cpu_freq.p1 == "low"

    t2 = r"""
    cpu_freq = {p1 = "low", p2 = "medium"}
    """

    cpu_freq = from_toml(Options, t2).cpu_freq
    assert cpu_freq.p1 == "low" and cpu_freq.p2 == "medium"

    t3 = r"""
    cpu_freq = {p1 = 1, p2 = "medium", p3 = "Conservative"}
    """

    cpu_freq = from_toml(Options, t3).cpu_freq
    assert cpu_freq.p1 == 1 and (
        cpu_freq.p2 == "medium" and cpu_freq.p3 == "Conservative"
    )

    t4 = r"""
    cpu_freq = {p1 = 1, p3 = "Conservative"}
    """

    with pytest.raises(ValueError):
        from_toml(Options, t4)


def test_distribution() -> None:
    t1 = r"""
    distribution = {first = "block"}
    """

    distribution = from_toml(Options, t1).distribution
    assert distribution.first == "block"

    t2 = r"""
    distribution = {first = "block", second = "cyclic"}
    """

    distribution = from_toml(Options, t2).distribution
    assert distribution.first == "block" and distribution.second == "cyclic"

    t3 = r"""
    distribution = {first = "block", second = "cyclic", third = "fcyclic"}
    """

    distribution = from_toml(Options, t3).distribution
    assert distribution.first == "block" and (
        distribution.second == "cyclic" and distribution.third == "fcyclic"
    )

    t4 = r"""
    distribution = {first = "block", third = "fcyclic"}
    """

    with pytest.raises(ValueError):
        from_toml(Options, t4)


def test_extra_node_info() -> None:
    toml = r"""
    extra_node_info = ["*", 3, "*"]
    """
    assert from_toml(Options, toml).extra_node_info == ("*", 3, "*")


def test_mem() -> None:
    toml = r"""
    mem = {size = 128, unit = "G"}
    """
    mem = from_toml(Options, toml).mem
    assert mem.size == 128 and mem.unit == "G"


def test_signal() -> None:
    t1 = r"""
    signal = {num = 100}
    """
    signal = from_toml(Options, t1).signal
    assert signal.num == 100

    t2 = r"""
    signal = {num = "USR1", option = "R"}
    """
    signal = from_toml(Options, t2).signal
    assert signal.num == "USR1" and signal.option == "R"

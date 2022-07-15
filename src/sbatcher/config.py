from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path

from serde import deserialize, field


@deserialize
@dataclass
class Array:
    values: list[int] = field(default_factory=list)
    range_: list[int] = field(default_factory=list, rename="range")
    max_parallel: int = 1


@deserialize
@dataclass
class Options:
    """sbatch options"""

    account: str | None = None
    array: Array | None = None
    batch: str | None = None
    bb: str | None = None
    bbf: Path | None = None
    begin: datetime | time | None = None
    chdir: Path | None = None
    clusters: list[str] = field(default_factory=list)
    comment: str | None = None
    constraint: str | None = None
    container: Path | None = None
    contiguous: bool = False
    core_spec: int | None = None
    cores_per_socket: int | None = None

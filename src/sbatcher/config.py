from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Literal

from serde import deserialize, field


@deserialize
@dataclass
class Array:
    values: list[int] = field(default_factory=list)
    range_: list[int] = field(default_factory=list, rename="range")
    max_parallel: int | None = None


@deserialize
@dataclass
class Distribution:
    first: Literal["block"] | Literal["cyclic"] | Literal["arbitary"] | int
    second: Literal["block"] | Literal["cyclic"] | Literal["fcyclic"]
    third: Literal["block"] | Literal["cyclic"] | Literal["fcyclic"]
    pack: bool = False


@deserialize
@dataclass
class GpuBind:
    timeout: int | None = None
    mode: Literal["S"] | Literal["L"] | None = None


@deserialize
@dataclass
class Options:
    """sbatch options"""

    account: str = ""
    array: Array | None = None
    batch: str = ""
    bb: str = ""
    bbf: Path | None = None
    begin: datetime | time | None = None
    chdir: Path | None = None
    clusters: list[str] = field(default_factory=list)
    comment: str = ""
    constraint: str = ""
    container: Path | None = None
    contiguous: bool = False
    core_spec: int | None = None
    cores_per_socket: int | None = None
    cpu_freq: str = ""
    cpus_per_gpu: int | None = None
    cpus_per_task: int | None = None
    deadline: datetime | time | None = None
    delay_boot: int | None = None
    dependency: str = ""
    distribution: Distribution | None = None
    error_file: str = "{{ SBATCHER_CONFIG_FILE }}.err"
    exclusive: Literal["mcs", "user"] | None = None
    export: Literal["ALL", "NONE"] | list[str] | None = None
    export_file: Path | None = None
    extra_node_info: tuple[
        int | Literal["*"], int | Literal["*"], int | Literal["*"]
    ] | None = None
    get_user_env: str = ""
    gid: int | str = ""
    # gpu_bind:

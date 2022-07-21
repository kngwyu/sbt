from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Literal

from serde import deserialize, field


@deserialize
@dataclass
class AcctgFreq:
    datatype: Literal["task", "energy", "network", "filesystem"]
    interval: int


@deserialize
@dataclass
class Array:
    values: list[int] = field(default_factory=list)
    range_: list[int] = field(default_factory=list, rename="range")
    max_parallel: int | None = None


@deserialize
@dataclass
class ClusterConstraint:
    features: list[str]
    exclude: bool = False


@deserialize
@dataclass
class CpuFreq:
    p1: int | Literal["low", "medium", "high", "highm1"]
    p2: int | Literal["medium", "high", "highm1"] | None = None
    p3: Literal[
        "Conservative", "OnDemand", "Performance", "PowerSave", "SchedUtil", "UserSpace"
    ] | None = None


@deserialize
@dataclass
class Distribution:
    first: Literal["block", "cycle", "arbitary"] | int
    second: Literal["block", "cyclic", "fcyclic"] | None = None
    third: Literal["block", "cyclic", "fcyclic"] | None = None
    pack: bool = False


@deserialize
@dataclass
class GpuBind:
    type_: Literal[
        "closest", "map_gpu", "mask_gpu", "none", "per_task", "single"
    ] = field(rename="type")
    value: int | list[str] | None = None
    verbose: bool = False


@deserialize
@dataclass
class GpuFreq:
    value: int | Literal["low", "medium", "high", "highm1"]
    memory: int | Literal["low", "medium", "high", "highm1"] | None = None
    verbose: bool = False


@deserialize
@dataclass
class License:
    name: str
    db: str = ""
    count: int | None = None


@deserialize
@dataclass
class Options:
    """sbatch options"""

    account: str = ""
    acctg_freq: list[AcctgFreq] = field(default_factory=list)
    array: Array | None = None
    batch: str = ""
    bb: str = ""
    bbf: Path | None = None
    begin: datetime | time | None = None
    chdir: Path | None = None
    cluster_constraint: ClusterConstraint | None = None
    clusters: list[str] = field(default_factory=list)
    comment: str = ""
    constraint: str = ""
    container: Path | None = None
    contiguous: bool = False
    core_spec: int | None = None
    cores_per_socket: int | None = None
    cpu_freq: CpuFreq | None = None
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
    gpu_bind: GpuBind | None = None
    gpu_freq: GpuFreq | None = None
    gpus: list[int | tuple[str, int]] = field(default_factory=list)
    gpus_per_node: list[int | tuple[str, int]] = field(default_factory=list)
    gpus_per_task: list[int | tuple[str, int]] = field(default_factory=list)
    gres: list[tuple[str, int] | tuple[str, str, int]] = field(default_factory=list)
    gres_flags: Literal["disable-binding", "enforce-binding"] | None = None
    hint: Literal[
        "compute_bound", "memory_bound", "multithread", "nomultithread"
    ] | None = None
    hold: bool = False
    input_: Path | None = field(default=None)
    jobname: str = ""
    kill_on_invalid_dep: Literal["yes", "no"] | None = None
    licenses: list[License] = field(default_factory=list)
    mail_type: list[
        Literal[
            "NONE",
            "BEGIN",
            "END",
            "FAIL",
            "REQUEUE",
            "ALL",
            "INVALID_DEPEND",
            "REQUEUE",
            "STAGE_OUT",
            "TIME_LIMIT",
            "TIME_LIMIT_90",
            "TIME_LIMIT_80",
            "TIME_LIMIT_50",
            "ARRAY_TASKS",
        ]
    ] = field(default_factory=list)
    mail_user: str = ""
    mcs_label: str = ""

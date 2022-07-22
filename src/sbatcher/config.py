from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Literal, Protocol

from serde import deserialize, field


class SbatchStr(Protocol):
    def as_sbatch_str(self) -> str:
        ...


@deserialize
@dataclass
class AcctgFreq:
    datatype: Literal["task", "energy", "network", "filesystem"]
    interval: int

    def as_sbatch_str(self) -> str:
        return f"{self.datatype}={self.interval}"


@deserialize
@dataclass
class Array:
    values: list[int] = field(default_factory=list)
    range_: list[int] = field(default_factory=list, rename="range")
    max_parallel: int | None = None

    def as_sbatch_str(self) -> str:
        vlen, rlen = len(self.values), len(self.range_)
        if vlen == 0 and rlen == 0:
            raise ValueError(
                "One of values of range must be available in array = {...}"
            )
        elif vlen > 0 and rlen > 0:
            raise ValueError("Both of values of range are given in array = {...}")
        elif rlen == 0:
            ret = ",".join([str(value) for value in self.values])
        elif rlen == 1 or rlen > 3:
            raise ValueError(
                "array = { range = [...]} expects an array with length 2 or 3"
            )
        else:
            a, b = self.range_[:2]
            ret = f"{a}-{b}"
            if rlen == 3:
                ret += f":{self.range_[2]}"
        if self.max_parallel is not None:
            ret += f"%{self.max_parallel}"
        return ret


@deserialize
@dataclass
class ClusterConstraint:
    features: list[str]
    exclude: bool = False

    def as_sbatch_str(self) -> str:
        ret = ",".join(self.features)
        if self.exclude:
            return f"!{ret}"
        else:
            return ret


@deserialize
@dataclass
class CpuFreq:
    p1: int | Literal["low", "medium", "high", "highm1"]
    p2: int | Literal["medium", "high", "highm1"] | None = None
    p3: Literal[
        "Conservative", "OnDemand", "Performance", "PowerSave", "SchedUtil", "UserSpace"
    ] | None = None

    def as_sbatch_str(self) -> str:
        ret = str(self.p1)
        if self.p2 is not None:
            ret += f"-{self.p2}"
            if self.p3 is not None:
                ret += f":{self.p3}"
        else:
            assert self.p3 is None, "Invalid cpu freq: p3 is specified without p2"

        return ret


@deserialize
@dataclass
class Distribution:
    first: Literal["block", "cycle", "arbitary"] | int
    second: Literal["block", "cyclic", "fcyclic"] | None = None
    third: Literal["block", "cyclic", "fcyclic"] | None = None
    pack: bool = False

    def as_sbatch_str(self) -> str:
        ret = str(self.first)
        if self.second is not None:
            ret += f":{self.second}"
            if self.third is not None:
                ret += f":{self.third}"
        else:
            assert (
                self.third is None
            ), "Invalid distribution: third is specified without second"

        if self.pack:
            ret += ",{Pack}"
        return ret


@deserialize
@dataclass
class GpuBind:
    type_: Literal[
        "closest", "map_gpu", "mask_gpu", "none", "per_task", "single"
    ] = field(rename="type")
    value: int | list[str] | None = None
    verbose: bool = False

    def as_sbatch_str(self) -> str:
        ret = str(self.type_)
        if self.value is not None:
            if isinstance(self.value, list):
                ret += ":" + ",".join(self.value)
            else:
                ret += f":{self.value}"
        if self.verbose:
            ret = f"verbose,{ret}"
        return ret


@deserialize
@dataclass
class GpuFreq:
    value: int | Literal["low", "medium", "high", "highm1"]
    memory: int | Literal["low", "medium", "high", "highm1"] | None = None
    verbose: bool = False

    def as_sbatch_str(self) -> str:
        ret = str(self.value)
        if self.memory is not None:
            ret += f",memory={self.memory}"
        if self.verbose:
            ret += ",verbose"
        return ret


@deserialize
@dataclass
class License:
    name: str
    db: str = ""
    count: int | None = None

    def as_sbatch_str(self) -> str:
        ret = self.name
        if len(self.db) > 0:
            ret += f"@{self.db}"
        if self.count is not None:
            ret += f":{self.count}"
        return ret


@deserialize
@dataclass
class Mem:
    size: int
    unit: Literal["K", "M", "G", "T"]

    def as_sbatch_str(self) -> str:
        return f"{self.size}{self.unit}"


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
    error: Path = Path("{{ SBATCHER_CONFIG_FILE }}.err")
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
    mem: Mem | None = None
    mem_bind: Literal["local", "none"] | None = None
    mem_per_cpu: Mem | None = None
    mincpus: int | None = None
    network: Literal["system", "blade"] | None = None
    nice: int | None = None
    no_kill: bool = False
    no_requeue: bool = False
    node_file: Path | None = None
    nodelist: list[str] = field(default_factory=list)
    nodes: int | tuple[int, int] | None = None
    ntasks: int | None = None
    ntasks_per_core: int | None = None
    ntasks_per_gpu: int | None = None
    ntasks_per_node: int | None = None
    ntasks_per_socket: int | None = None
    open_mode: Literal["append", "truncate"] | None = None
    output: Path = Path("{{ SBATCHER_CONFIG_FILE }}.out")
    overcommit: bool = False
    oversubscribe: bool = False
    parsable: bool = False
    partition: str | list[str] = ""
    power: list[str] = field(default_factory=list)

"""Implement a collection of sbatch options."""

from __future__ import annotations

import datetime as dt
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from serde.compat import dataclasses

if sys.version_info[:2] == (3, 7):
    from typing_extensions import Literal
else:
    from typing import Literal

from serde import deserialize, field

from sbatcher.render_helper import is_empty, render_optional


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

    def __post_init__(self) -> None:
        vlen, rlen = len(self.values), len(self.range_)
        if vlen == 0 and rlen == 0:
            raise ValueError(
                "One of values of range must be available in array = {...}"
            )
        elif vlen > 0 and rlen > 0:
            raise ValueError("Both of values of range are given in array = {...}")
        elif rlen == 1 or rlen > 3:
            raise ValueError(
                "array = { range = [...]} expects an array with length 2 or 3"
            )

    def as_sbatch_str(self) -> str:
        rlen = len(self.range_)
        if rlen == 0:
            ret = ",".join([str(value) for value in self.values])
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
        "Conservative",
        "OnDemand",
        "Performance",
        "PowerSave",
        "SchedUtil",
        "UserSpace",
    ] | None = None

    def __post_init__(self) -> None:
        if self.p2 is None and self.p3 is not None:
            raise ValueError("Invalid cpu freq: p3 is specified without p2")

    def as_sbatch_str(self) -> str:
        return (
            str(self.p1)
            + render_optional(self.p2, prefix="-")
            + render_optional(self.p3, prefix=":")
        )


@deserialize
@dataclass
class Distribution:
    first: Literal["block", "cycle", "arbitary"] | int
    second: Literal["block", "cyclic", "fcyclic"] | None = None
    third: Literal["block", "cyclic", "fcyclic"] | None = None
    pack: bool = False

    def __post_init__(self) -> None:
        if self.second is None and self.third is not None:
            raise ValueError("Invalid distribution: third is specified without second")

    def as_sbatch_str(self) -> str:
        return (
            str(self.first)
            + render_optional(self.second, prefix=":")
            + render_optional(self.third, prefix=":")
            + {True: ",{Pack}", False: ""}[self.pack]
        )


@deserialize
@dataclass
class Duration:
    days: int = 0
    hours: int = 0
    minutes: int = 0

    def __post_init__(self) -> None:
        if self.days == 0 and self.hours == 0 and self.minutes == 0:
            raise ValueError("Zero duration")

    def as_sbatch_str(self) -> str:
        if self.days == 0:
            return f"{self.hours}:{self.minutes}"
        else:
            return f"{self.days}-{self.hours}:{self.minutes}"


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
        ret = str(self.value) + render_optional(self.memory, prefix=",memory=")
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
        return (
            self.name
            + render_optional(self.db, prefix="@")
            + render_optional(self.count, prefix="")
        )


@deserialize
@dataclass
class Mem:
    size: int
    unit: Literal["K", "M", "G", "T"] = "M"

    def as_sbatch_str(self) -> str:
        return f"{self.size}{self.unit}"


@deserialize
@dataclass
class Signal:
    num: str | int
    time: int = 60
    option: Literal["R", "B"] | None = None

    def as_sbatch_str(self) -> str:
        return render_optional(self.option, suffix=":") + f"{self.num}@{self.time}"


@deserialize
@dataclass
class Switches:
    count: int
    max_time: Duration | None = None

    def as_sbatch_str(self):
        if self.max_time is None:
            return str(self.count)
        else:
            return f"{self.count}@{self.max_time.as_sbatch_str()}"


@deserialize
@dataclass
class Options:
    """
    Sbatch options.
    Some options(--help, --test-only, --version, and --usage) are only available in CLI.
    """

    account: str = ""
    acctg_freq: list[AcctgFreq] = field(default_factory=list)
    array: Array | None = None
    batch: str = ""
    bb: str = ""
    bbf: Path | None = None
    # TODO: This does not work now because of an upstream bug
    begin: dt.datetime | None = None
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
    deadline: dt.datetime | None = None
    delay_boot: int | None = None
    dependency: str = ""
    distribution: Distribution | None = None
    exclusive: Literal["mcs", "user"] | None = None
    export: Literal["ALL", "NONE"] | list[str] | None = None
    export_file: Path | None = None
    extra_node_info: tuple[
        int | Literal["*"],
        int | Literal["*"],
        int | Literal["*"],
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
        "compute_bound",
        "memory_bound",
        "multithread",
        "nomultithread",
    ] | None = None
    hold: bool = False
    input_: Path | None = field(default=None)
    job_name: str = ""
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
    no_kill: bool | Literal["off"] = False
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
    overcommit: bool = False
    oversubscribe: bool = False
    parsable: bool = False
    partition: str | list[str] = ""
    power: list[str] = field(default_factory=list)
    prefer: list[str] = field(default_factory=list)
    priority: int | Literal["TOP"] | None = None
    profile: Literal["All", "None"] | list[
        Literal["Energy", "Task", "Lustre", "Network"]
    ] = field(default_factory=list)
    propagate: list[
        Literal[
            "ALL",
            "NONE",
            "AS",
            "CORE",
            "CPU",
            "DATA",
            "FSIZE",
            "MEMLOCK",
            "NOFILE",
            "NPROC",
            "RSS",
            "STACK",
        ]
    ] = field(default_factory=list)
    qos: int | None = None
    quiet: bool = False
    requeue: bool = False
    reservation: list[str] = field(default_factory=list)
    signal: Signal | None = None
    sockets_per_node: int | None = None
    spread_job: bool = False
    switches: Switches | None = None
    thread_spec: int | None = None
    threads_per_core: int | None = None
    time: Duration | None = None
    time_min: Duration | None = None
    tmp: Mem | None = None
    uid: int | str = ""
    use_min_nodes: bool = False
    verbose: bool = False
    wait_all_nodes: bool = False
    wckey: str = ""


def _render_gpus(gpus: list[int | tuple[str, int]]) -> str:
    def to_s(value: int | tuple[str, int]) -> str:
        if isinstance(value, tuple):
            return f"{value[0]}:{value[1]}"
        else:
            return str(value)

    return "=" + ",".join([to_s(elem) for elem in gpus])


def _render_gres(gres: list[tuple[str, int] | tuple[str, str, int]]) -> str:
    def to_s(value: tuple[str, int] | tuple[str, str, int]) -> str:
        return ":".join([str(elem) for elem in value])

    return "=" + ",".join([to_s(elem) for elem in gres])


def _render_no_kill(no_kill: bool | Literal["off"]) -> str:
    if no_kill == "off":
        return "=off"
    else:
        return ""


def _render_nodes(nodes: int | tuple[int, int]) -> str:
    if isinstance(nodes, tuple):
        return "=" + f"{nodes[0]}-{nodes[1]}"
    else:
        return "=" + str(nodes)


_CUSTOM_RENDER_FUNCTIONS = {
    "extra_node_info": (lambda value: ":".join([str(elem) for elem in value])),
    "gpus": _render_gpus,
    "gpus_per_node": _render_gpus,
    "gpus_per_task": _render_gpus,
    "gres": _render_gres,
    "no_kill": _render_no_kill,
    "nodes": _render_nodes,
    "wait_all_nodes": (lambda value: str(int(value))),
}


def _render_key(key: str) -> str:
    return "--" + key.replace("_", "-")


def _render_value(key: str, value: Any) -> str:
    if key in _CUSTOM_RENDER_FUNCTIONS:
        return _CUSTOM_RENDER_FUNCTIONS[key](value)
    elif hasattr(value, "as_sbatch_str"):
        return "=" + value.as_sbatch_str()
    elif isinstance(value, (list, tuple)):
        values = [
            v.as_sbatch_str() if hasattr(v, "as_sbatch_str") else str(v) for v in value
        ]
        return "=" + ",".join(values)
    elif isinstance(value, bool):
        return ""
    else:
        return f"={value}"


def render(options: Options) -> str:
    res = []
    for field in dataclasses.fields(options):
        key = field.name
        value = getattr(options, key)
        if not is_empty(value):
            res.append("#SBATCH " + _render_key(key) + _render_value(key, value))
    rendered = "\n".join(res)
    if len(res) != 0:
        rendered = "\n" + rendered + "\n"
    return rendered

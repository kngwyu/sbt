"""Implement a collection of sbatch options."""
from __future__ import annotations

import datetime as dt
import operator
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Tuple, Union

from serde.compat import dataclasses

if sys.version_info[:2] == (3, 7):
    from typing_extensions import Literal
else:
    from typing import Literal

from serde import deserialize, field

from sbt.render_helper import is_empty, render_optional


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
    values: List[int] = field(default_factory=list)
    range_: List[int] = field(default_factory=list, rename="range")
    max_parallel: Union[int, None] = None

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
    features: List[str]
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
    p1: Union[int, Literal["low", "medium", "high", "highm1"]]
    p2: Union[int, Literal["medium", "high", "highm1"], None] = None
    p3: Union[
        Literal[
            "Conservative",
            "OnDemand",
            "Performance",
            "PowerSave",
            "SchedUtil",
            "UserSpace",
        ],
        None,
    ] = None

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
    first: Union[Literal["block", "cycle", "arbitary"], int]
    second: Union[Literal["block", "cyclic", "fcyclic"], None] = None
    third: Union[Literal["block", "cyclic", "fcyclic"], None] = None
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
        "closest",
        "map_gpu",
        "mask_gpu",
        "none",
        "per_task",
        "single",
    ] = field(rename="type")
    value: Union[int, List[str], None] = None
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
    value: Union[int, Literal["low", "medium", "high", "highm1"]]
    memory: Union[int, Literal["low", "medium", "high", "highm1"], None] = None
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
    count: Union[int, None] = None

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
    num: Union[str, int]
    time: int = 60
    option: Union[Literal["R", "B"], None] = None

    def as_sbatch_str(self) -> str:
        return render_optional(self.option, suffix=":") + f"{self.num}@{self.time}"


@deserialize
@dataclass
class Switches:
    count: int
    max_time: Union[Duration, None] = None

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
    Note that
      - --help, --version, and --usage are not supported.
      - --test-only is supported by sbt --dry-run.
    """

    account: str = ""
    acctg_freq: List[AcctgFreq] = field(default_factory=list)
    array: Union[Array, None] = None
    batch: str = ""
    bb: str = ""
    bbf: Union[Path, None] = None
    # TODO: This does not work now because of an upstream bug
    begin: Union[dt.datetime, None] = None
    chdir: Union[Path, None] = None
    cluster_constraint: Union[ClusterConstraint, None] = None
    clusters: List[str] = field(default_factory=list)
    comment: str = ""
    constraint: str = ""
    container: Union[Path, None] = None
    contiguous: bool = False
    core_spec: Union[int, None] = None
    cores_per_socket: Union[int, None] = None
    cpu_freq: Union[CpuFreq, None] = None
    cpus_per_gpu: Union[int, None] = None
    cpus_per_task: Union[int, None] = None
    deadline: Union[dt.datetime, None] = None
    delay_boot: Union[int, None] = None
    dependency: str = ""
    distribution: Union[Distribution, None] = None
    error: str = "{{ SBT_LOGFILE_NAME }}.err"
    exclusive: Union[Literal["mcs", "user"], None] = None
    export: Union[Literal["ALL", "NONE"], List[str], None] = None
    export_file: Union[Path, None] = None
    extra_node_info: Union[
        Tuple[
            Union[int, Literal["*"]],
            Union[int, Literal["*"]],
            Union[int, Literal["*"]],
        ],
        None,
    ] = None
    get_user_env: str = ""
    gid: Union[int, str] = ""
    gpu_bind: Union[GpuBind, None] = None
    gpu_freq: Union[GpuFreq, None] = None
    gpus: List[Union[int, Tuple[str, int]]] = field(default_factory=list)
    gpus_per_node: List[Union[int, Tuple[str, int]]] = field(default_factory=list)
    gpus_per_task: List[Union[int, Tuple[str, int]]] = field(default_factory=list)
    gres: List[Union[Tuple[str, int], Tuple[str, str, int]]] = field(
        default_factory=list
    )
    gres_flags: Union[Literal["disable-binding", "enforce-binding"], None] = None
    hint: Union[
        Literal[
            "compute_bound",
            "memory_bound",
            "multithread",
            "nomultithread",
        ],
        None,
    ] = None
    hold: bool = False
    input_: Union[Path, None] = field(default=None)
    job_name: str = "{{ SBT_JOB_NAME }}"
    kill_on_invalid_dep: Union[Literal["yes", "no"], None] = None
    licenses: List[License] = field(default_factory=list)
    mail_type: List[
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
    mem: Union[Mem, None] = None
    mem_bind: Union[Literal["local", "none"], None] = None
    mem_per_cpu: Union[Mem, None] = None
    mincpus: Union[int, None] = None
    network: Union[Literal["system", "blade"], None] = None
    nice: Union[int, None] = None
    no_kill: Union[bool, Literal["off"]] = False
    no_requeue: bool = False
    node_file: Union[Path, None] = None
    nodelist: List[str] = field(default_factory=list)
    nodes: Union[int, Tuple[int, int], None] = None
    ntasks: Union[int, None] = None
    ntasks_per_core: Union[int, None] = None
    ntasks_per_gpu: Union[int, None] = None
    ntasks_per_node: Union[int, None] = None
    ntasks_per_socket: Union[int, None] = None
    output: str = "{{ SBT_LOGFILE_NAME }}.out"
    open_mode: Union[Literal["append", "truncate"], None] = None
    overcommit: bool = False
    oversubscribe: bool = False
    parsable: bool = False
    partition: Union[str, List[str]] = ""
    power: List[str] = field(default_factory=list)
    prefer: List[str] = field(default_factory=list)
    priority: Union[int, Literal["TOP"], None] = None
    profile: Union[
        Literal["All", "None"],
        List[Literal["Energy", "Task", "Lustre", "Network"]],
    ] = field(default_factory=list)
    propagate: List[
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
    qos: Union[int, None] = None
    quiet: bool = False
    requeue: bool = False
    reservation: List[str] = field(default_factory=list)
    signal: Union[Signal, None] = None
    sockets_per_node: Union[int, None] = None
    spread_job: bool = False
    switches: Union[Switches, None] = None
    thread_spec: Union[int, None] = None
    threads_per_core: Union[int, None] = None
    time: Union[Duration, None] = None
    time_min: Union[Duration, None] = None
    tmp: Union[Mem, None] = None
    uid: Union[int, str] = ""
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


def render_options(options: Options) -> str:
    res = []
    for key in map(operator.attrgetter("name"), dataclasses.fields(options)):
        value = getattr(options, key)
        if not is_empty(value):
            res.append("#SBATCH " + _render_key(key) + _render_value(key, value))
    rendered = "\n".join(res)
    if len(res) != 0:
        rendered = "\n" + rendered + "\n"
    return rendered

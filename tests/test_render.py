from __future__ import annotations

from pathlib import Path

import pytest
from serde.toml import from_toml

from sbt.config import Config, render
from sbt.options import Duration, Mem, Options, render_options


def test_render_options() -> None:
    options = Options(
        cpus_per_task=1,
        gres=[("gpu", 1)],
        mail_type=["END", "FAIL"],
        mail_user="yuji.kanagawa@oist.jp",
        mem_per_cpu=Mem(16, "G"),
        nodes=1,
        ntasks=1,
        ntasks_per_node=1,
        partition="gpu",
        time=Duration(1),
    )
    rendered = render_options(options)
    expected = r"""
#SBATCH --cpus-per-task=1
#SBATCH --error={{ SBT_LOGFILE_NAME }}.err
#SBATCH --gres=gpu:1
#SBATCH --job-name={{ SBT_JOB_NAME }}
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=yuji.kanagawa@oist.jp
#SBATCH --mem-per-cpu=16G
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --output={{ SBT_LOGFILE_NAME }}.out
#SBATCH --partition=gpu
#SBATCH --time=1-00:00:00
"""
    assert rendered == expected


@pytest.mark.parametrize("var", ("Yay", 10))
def test_render_config(var: str | int) -> None:
    toml = r"""
logdir = "/tmp/log"

template =  "echo {{ var }}"

[slurm_options]
cpus_per_task = 1
gres = [["gpu", 1]]
mail_type = ["END", "FAIL"]
mail_user = "yuji.kanagawa@oist.jp"
mem_per_cpu = { size = 16, unit = "G" }
nodes = 1
ntasks = 1
ntasks_per_node = 1
partition = "gpu"
time = { hours = 12 }

[default_values]
var = 1
"""
    config = from_toml(Config, toml)
    name = "myjob"
    rendered, jobname = next(
        iter(
            render(
                Path("myjob.toml"),
                config,
                {"var": var},
                no_timestamp=True,
            )
        )
    )
    expected = f"""#!/bin/bash -l
#SBATCH --cpus-per-task=1
#SBATCH --error=/tmp/log/{name}-var-{var}.err
#SBATCH --gres=gpu:1
#SBATCH --job-name={name}-var-{var}
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=yuji.kanagawa@oist.jp
#SBATCH --mem-per-cpu=16G
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --output=/tmp/log/{name}-var-{var}.out
#SBATCH --partition=gpu
#SBATCH --time=12:00:00
echo {var}"""
    assert rendered == expected, rendered
    assert jobname == f"{name}-var-{var}"


def test_render_matrix() -> None:
    toml = r"""
logdir = "/tmp/log"

template =  "echo {{ foo }} && echo {{ bar }}"

[slurm_options]
cpus_per_task = 1
gres = [["gpu", 1]]
mail_type = ["END", "FAIL"]
mail_user = "yuji.kanagawa@oist.jp"
mem_per_cpu = { size = 16, unit = "G" }
nodes = 1
ntasks = 1
ntasks_per_node = 1
partition = "gpu"
time = { hours = 12 }

[default-values]
foo = "fooooooo"

[matrix]
foo = ["yay", "me"]
bar = ["oh", "no"]
"""
    config = from_toml(Config, toml)
    name = "myjob"
    foobar_correct = [
        ("yay", "oh"),
        ("yay", "no"),
        ("me", "oh"),
        ("me", "no"),
    ]
    for foobar, (rendered, jobname) in zip(
        foobar_correct,
        render(
            Path("myjob.toml"),
            config,
            {},
            no_timestamp=True,
        ),
    ):
        foo, bar = foobar
        expected = f"""#!/bin/bash -l
#SBATCH --cpus-per-task=1
#SBATCH --error=/tmp/log/{name}-foo-{foo}-bar-{bar}.err
#SBATCH --gres=gpu:1
#SBATCH --job-name={name}-foo-{foo}-bar-{bar}
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=yuji.kanagawa@oist.jp
#SBATCH --mem-per-cpu=16G
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --output=/tmp/log/{name}-foo-{foo}-bar-{bar}.out
#SBATCH --partition=gpu
#SBATCH --time=12:00:00
echo {foo} && echo {bar}"""
        assert rendered == expected, rendered
        assert jobname == f"{name}-foo-{foo}-bar-{bar}"

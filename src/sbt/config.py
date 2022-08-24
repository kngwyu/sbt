from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import jinja2
import jinja2.meta
from serde import deserialize, field

from sbt.options import Options, render_options


@deserialize
@dataclass
class Config:
    logdir: Path = field(default_factory=lambda: Path("."))
    slurm_options: Options = field(default_factory=Options)
    shebang: str = "#!/bin/bash -l"
    template: Optional[str] = None
    template_path: Optional[Path] = None
    default_values: Dict[str, Any] = field(default_factory=dict)
    matrix: Dict[str, List[Any]] = field(default_factory=dict)
    env_vars: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.template is None and self.template_path is None:
            raise ValueError("Either of [template] and [template_path] is necessary")

        if self.template is not None and self.template_path is not None:
            raise ValueError(
                "You can specify only one of [template] and [template_path]"
            )

    def is_overriden_key(self, key: str) -> bool:
        return key in self.matrix or key not in self.default_values

    def get_environment(
        self,
        header: str,
        basedir: Path,
    ) -> tuple[str, jinja2.Environment]:
        if self.template_path is not None:
            if self.template_path.is_absolute():
                template = self.template_path.read_text()
            else:
                template = basedir.joinpath(self.template_path).read_text()
        else:
            assert self.template is not None
            template = self.template
        script = header + template
        loader = jinja2.DictLoader({"script": script})
        return script, jinja2.Environment(loader=loader)

    def variables_iter(self, overrides: dict[str, Any]) -> Iterable[dict[str, Any]]:
        iterated = {k: v for k, v in self.matrix.items() if k not in overrides}
        if len(iterated) == 0:
            yield {**self.default_values, **overrides}
        else:
            for matrix_vars in itertools.product(*iterated.values()):
                variables = {**self.default_values, **overrides}
                for key, value in zip(iterated, matrix_vars):
                    variables[key] = value
                yield variables


def _render_kv(k: str, v: Any) -> str:
    return re.sub(r"[^A-Za-z0-9|_-]", "-", f"{k}-{v}")


def _override_name(overrides: dict[str, Any]) -> str:
    if len(overrides) == 0:
        return "default"
    else:
        return "-".join([_render_kv(*kv) for kv in overrides.items()])


def _prompt(env: jinja2.Environment, script: str, variables: Iterable[str]) -> bool:
    from rich import markup
    from rich import print as rich_print
    from rich.prompt import Confirm
    from rich.text import Text

    def variables_text(diff: set[str]) -> Text:
        diff_list = list(diff)
        if len(diff_list) == 1:
            return markup.render(f"Variable [r]{diff_list[0]}[/r]")
        elif len(diff_list) == 2:
            return markup.render(f"Variables [r]{diff_list[0]} and {diff_list[1]}[/r]")
        else:
            variables = (
                ",".join(diff_list[:-2]) + f", {diff_list[-2]}, and {diff_list[-1]}"
            )
            return markup.render(f"Variables [r]{variables}[/r] ")

    template_variables = jinja2.meta.find_undeclared_variables(env.parse(script))
    given_variables = set(variables)
    diff_t_g = template_variables.difference(given_variables)
    diff_g_t = given_variables.difference(template_variables)
    if len(diff_t_g) > 0:
        ask_text = variables_text(diff_t_g)
        ask_text.append(" are available in templates but not given in config or CLI.")
    elif len(diff_g_t) > 0:
        ask_text = variables_text(diff_g_t)
        ask_text.append(" are given but not available in templates.")
    else:
        rich_print("All variables are specified :tada:")
        ask_text = None

    if ask_text is not None:
        ask_text.append("\nProceed?")
        return Confirm.ask(ask_text)

    return True


def render(
    self_path: Path,
    config: Config,
    cli_options: dict[str, Any],
    show_prompt: bool = False,
    no_timestamp: bool = False,  # Only for testing
) -> Iterable[tuple[str, str]]:
    # Render sbatch header
    options = render_options(config.slurm_options)
    script = config.shebang + options
    # Timestamp
    if not no_timestamp:
        script += f"# timestamp: {datetime.now().isoformat()}\n"
    script, env = config.get_environment(script, self_path.parent)
    for variables in config.variables_iter(cli_options):
        # Make a unique job name and out/err file names
        overrides = {k: v for k, v in variables.items() if config.is_overriden_key(k)}
        job_name = self_path.stem + "-" + _override_name(overrides=overrides)
        logdir = config.logdir.absolute()
        variables.update(
            {
                "SBT_JOB_NAME": job_name,
                "SBT_LOGFILE_NAME": logdir.joinpath(job_name).as_posix(),
            }
        )

        if show_prompt and not _prompt(env, script, variables.keys()):
            exit(0)

        # Render variables in the script
        yield env.get_template("script").render(variables), job_name

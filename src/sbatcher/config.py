from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import jinja2
import jinja2.meta
from serde import deserialize, field
from serde.se import copy

from sbatcher.options import Options, render_options


@deserialize
@dataclass
class Config:
    logdir: Path = field(default_factory=lambda: Path("."))
    slurm_options: Options = field(default_factory=Options)
    shebang: str = "#!/bin/bash -l"
    template: str | None = None
    template_path: Path | None = None
    template_vars: dict[str, Any] = field(default_factory=dict)
    env_vars: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.template is None and self.template_path is None:
            raise ValueError("Either of [template] and [template_path] is necessary")

        if self.template is not None and self.template_path is not None:
            raise ValueError(
                "You can specify only one of [template] and [template_path]"
            )

    def get_environment(self, header: str) -> tuple[str, jinja2.Environment]:
        if self.template_path is not None:
            template = self.template_path.read_text()
        else:
            assert self.template is not None
            template = self.template
        loader = jinja2.DictLoader({"script": header + template})
        return template, jinja2.Environment(loader=loader)


def _override_name(logdir: Path, overrides: dict[str, Any]) -> str:
    if len(overrides) == 0:
        return "default"
    else:
        return "-".join([f"{kv[0]}-{kv[1]}" for kv in overrides.items()])


def render(
    name: str,
    config: Config,
    cli_options: dict[str, Any],
    show_prompt: bool = False,
    no_timestamp: bool = False,  # Only for testing
) -> tuple[str, str]:
    # Render sbatch header
    options = render_options(config.slurm_options)
    script = config.shebang + options
    # Timestamp
    if not no_timestamp:
        script += f"# timestamp: {datetime.now().isoformat()}\n"
    template_str, env = config.get_environment(script)
    # Make a unique job name and out/err file names
    job_name = name + "-" + _override_name(config.logdir, overrides=cli_options)
    # Setup variables
    variables = copy.deepcopy(config.template_vars)
    variables.update(cli_options)

    # Show unused variables
    if show_prompt:
        from rich import markup
        from rich.prompt import Confirm
        from rich.text import Text

        def variables_text(diff: set[str]) -> Text:
            text = Text("Variables")
            diff_list = list(diff)
            if len(diff_list) == 1:
                return markup.render(f"Variable [r]{diff_list[0]}[/r]")
            elif len(diff_list) == 2:
                return markup.render(
                    f"Variables [r]{diff_list[0]} and {diff_list[1]}[/r]"
                )
            else:
                variables = (
                    ",".join(diff_list[:-2]) + f", {diff_list[-2]}, and {diff_list[-1]}"
                )
                return markup.render(f"Variables [r] {variables} [/r]")

        template_variables = jinja2.meta.find_undeclared_variables(
            env.parse(template_str)
        )
        n_template_vars = len(template_variables)
        given_variables = set(variables.keys())
        diff_t_g = template_variables.difference(given_variables)
        diff_g_t = given_variables.difference(template_variables)
        if len(diff_t_g) > 0:
            ask_text = variables_text(diff_t_g)
            ask_text.append(
                " are available in templates but not given in config or CLI."
            )
        elif len(diff_g_t) > 0:
            ask_text = variables_text(diff_g_t)
            ask_text.append(" are given but not available in templates.")
        else:
            ask_text = Text("are replaced. ")
        ask_text.append("\nProceed?")
        if not Confirm.ask(ask_text):
            exit(0)

    logdir = config.logdir.absolute()
    variables.update(
        {
            "SBATCHER_JOB_NAME": job_name,
            "SBATCHER_LOGFILE_NAME": logdir.joinpath(job_name).as_posix(),
        }
    )
    # Render variables in the script
    return env.get_template("script").render(variables), job_name

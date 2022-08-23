"""Entry point. Save a script file and submit it. """

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

from rich import markup
from rich.console import Console
from rich.prompt import Confirm
from rich.syntax import Syntax
from serde.toml import from_toml

from sbt.config import Config, render


def _nth_script(basedir: Path, script_name: str) -> int:
    max_value = 0
    for script in basedir.glob(f"{script_name}*.bash"):
        name = script.name
        pos = name.find("--")
        if pos > 0:
            max_value = max(max_value, int(name[pos + 2 :]))
    return max_value


def _save_script(
    script: str,
    script_name: str,
    logdir: Path,
    show_prompt: bool,
    overwrite: bool,
) -> Path:
    script_path = logdir.joinpath(f"{script_name}.bash")
    if script_path.exists():
        if overwrite and show_prompt:
            answer = Confirm.ask(
                markup.render(f"{script_path.as_posix()} already exists. Overwrite it?")
            )
        elif show_prompt:
            nth = _nth_script(logdir, script_name)
            old_path = script_path
            script_path = logdir.joinpath(f"{script_name}--{nth + 1}.bash")
            answer = Confirm.ask(
                markup.render(
                    f"{old_path.as_posix()} already exists. Create {script_path.as_posix()}?"
                )
            )
        else:
            answer = True

        if not answer:
            exit(0)

    if show_prompt:
        console = Console()
        syntax = Syntax(script, "bash")
        console.print(syntax)
        if not Confirm.ask(
            f"The above script is written to {script_path.as_posix()}. Proceed?"
        ):
            exit(0)

    logdir.mkdir(parents=True, exist_ok=True)
    script_path.touch()
    script_path.write_text(script)
    return script_path


def save_script(
    config_file_name: str,
    cli_options: dict[str, str],
    show_prompt: bool = False,
    overwrite: bool = False,
) -> Iterable[Path]:
    config_path = Path(config_file_name).absolute()
    config_toml = config_path.read_text()
    config = from_toml(Config, config_toml)
    for script, script_name in render(
        self_path=config_path,
        config=config,
        cli_options=cli_options,
        show_prompt=show_prompt,
    ):
        yield _save_script(
            script,
            script_name,
            config.logdir.absolute(),
            overwrite,
            show_prompt,
        )


def run_sbatch(script_path: Path, dry_run: bool) -> int:
    args = ["sbatch", script_path.as_posix()]
    if dry_run:
        args.append("--test-only")
    return subprocess.run(args).returncode

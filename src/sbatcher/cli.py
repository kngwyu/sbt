"""CLI interface of sbatcher """
from __future__ import annotations

import click

from sbatcher.submit import run_sbatch, save_script


def _parse_arg(arg: str) -> tuple[str, str]:
    if not arg.startswith("--"):
        raise ValueError("Only '--key=value' is acceptable as an additional argument")
    splitted = arg[2:].split("=")
    if len(splitted) != 2:
        raise ValueError("Only '--key=value' is acceptable as an additional argument")
    key, value = map(lambda s: s.replace("-", "_"), splitted)
    return key, value


@click.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("config_path", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Only generate and check a batch script")
@click.option("-y", "--yes", is_flag=True, help="Skip all questions")
@click.option("--overwrite", is_flag=True, help="Allow overwrite the script")
@click.pass_context
def cli(
    context: click.Context,
    config_path: str,
    dry_run: bool,
    yes: bool,
    overwrite: bool,
) -> None:
    additional_args = {kv[0]: kv[1] for kv in map(_parse_arg, context.args)}
    script_path = save_script(
        config_file_name=config_path,
        cli_options=additional_args,
        show_prompt=not yes,
        overwrite=overwrite,
    )
    exit(run_sbatch(script_path, dry_run))

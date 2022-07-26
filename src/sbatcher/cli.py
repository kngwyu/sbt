"""CLI interface of sbatcher """

import click


@click.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("config_path", type=click.Path(exists=True), help="Path to config file")
@click.option("--dry-run", is_flag=True, help="Only generate and check a batch script")
@click.option("-y", "--yes", is_flag=True, help="Skip all questions")
@click.pass_context
def cli(context: click.Context, config_path: str, dry_run: bool, yes: bool) -> None:
    pass

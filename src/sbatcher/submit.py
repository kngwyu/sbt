"""Entry point. Save a script file and submit it. """

from __future__ import annotations

from pathlib import Path

from serde.toml import from_toml

from sbatcher.config import Config, render


def submit(
    config_file_name: str,
    cli_options: dict[str, str],
    show_prompt: bool = False,
) -> int:
    config_path = Path(config_file_name).absolute()
    config_name = config_path.name
    config_toml = config_path.read_text()
    config = from_toml(Config, config_toml)
    script = render(
        name=config_name,
        config=config,
        cli_options=cli_options,
        show_prompt=show_prompt,
    )

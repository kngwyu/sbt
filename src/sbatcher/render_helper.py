from typing import Any, Sized


def is_empty(value: Any) -> bool:
    return isinstance(value, Sized) and len(value) == 0


def render_optional(value: Any, prefix: str = "", suffix: str = "") -> str:
    if value is None or is_empty(value):
        return ""
    else:
        return f"{prefix}{value}{suffix}"

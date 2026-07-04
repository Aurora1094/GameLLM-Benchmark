from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT_DIR / "prompts"
MAIN_TEMPLATE = PROMPTS_DIR / "main.md"
SPECS_DIR = PROMPTS_DIR / "specs"

PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
CHECKPOINT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
VALID_DIFFICULTIES = {"easy", "medium", "hard"}

REQUIRED_PLACEHOLDERS = {
    "game_name",
    "window_size",
    "player_color",
    "round_time_sec",
    "game_description",
    "checkpoints_rendered",
}


class PromptBuildError(ValueError):
    """Raised when the structured prompt contract cannot be satisfied."""


def build_prompt(main_path_or_difficulty: str | Path, spec_path_or_game: str | Path) -> str:
    """Render a final prompt.

    Supports both the explicit contract:
        build_prompt("prompts/main.md", "prompts/specs/easy/pong.md")

    and the existing pipeline style:
        build_prompt("easy", "pong")
    """
    main_path, spec_path = _resolve_build_paths(main_path_or_difficulty, spec_path_or_game)
    template = _strip_maintainer_comments(_read_required_text(main_path))
    spec = load_spec(spec_path)
    values = _build_placeholder_values(spec)

    placeholders = PLACEHOLDER_PATTERN.findall(template)
    _validate_template_placeholders(main_path, placeholders, values)

    prompt = PLACEHOLDER_PATTERN.sub(lambda match: str(values[match.group(1)]), template)
    _validate_rendered_prompt(prompt, spec_path)
    return prompt.rstrip() + "\n"


def load_checkpoints(spec_path_or_difficulty: str | Path, game: str | Path | None = None) -> list[dict[str, Any]]:
    """Load D2 checkpoint targets from the same spec used to build a prompt."""
    spec_path = _resolve_spec_path(spec_path_or_difficulty, game)
    spec = load_spec(spec_path)
    return [dict(item) for item in spec["checkpoints"]]


def load_spec(spec_path: str | Path) -> dict[str, Any]:
    """Parse and validate one YAML-frontmatter game spec."""
    path = Path(spec_path)
    text = _read_required_text(path)
    meta, body = _split_frontmatter(text, path)
    if not isinstance(meta, dict):
        raise PromptBuildError(f"{path} frontmatter must be a mapping")

    spec = dict(meta)
    spec["body"] = body.strip()
    _validate_spec(spec, path)
    return spec


def generated_prompt_path(difficulty: str, game: str) -> Path:
    return PROMPTS_DIR / difficulty / game / "prompt.txt"


def write_prompt_snapshot(prompt: str, run_dir: str | Path, game_slug: str) -> Path:
    """Persist the exact prompt used for a run."""
    out_dir = Path(run_dir) / "prompts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{game_slug}.txt"
    out_path.write_text(prompt, encoding="utf-8")
    return out_path


def _resolve_build_paths(
    main_path_or_difficulty: str | Path,
    spec_path_or_game: str | Path,
) -> tuple[Path, Path]:
    first = Path(main_path_or_difficulty)
    second = Path(spec_path_or_game)
    if first.suffix or first.exists() or second.suffix:
        return first, second
    return MAIN_TEMPLATE, SPECS_DIR / str(main_path_or_difficulty) / f"{spec_path_or_game}.md"


def _resolve_spec_path(spec_path_or_difficulty: str | Path, game: str | Path | None) -> Path:
    first = Path(spec_path_or_difficulty)
    if game is None:
        return first
    return SPECS_DIR / str(spec_path_or_difficulty) / f"{game}.md"


def _read_required_text(path: Path) -> str:
    if not path.exists():
        raise PromptBuildError(f"missing file: {path}")
    if not path.is_file():
        raise PromptBuildError(f"expected file, got directory: {path}")
    return path.read_text(encoding="utf-8-sig")


def _strip_maintainer_comments(text: str) -> str:
    return HTML_COMMENT_PATTERN.sub("", text).lstrip()


def _split_frontmatter(text: str, path: Path) -> tuple[dict[str, Any], str]:
    normalized = text.lstrip("\ufeff")
    if not normalized.startswith("---"):
        raise PromptBuildError(f"{path} must start with YAML frontmatter")

    lines = normalized.splitlines()
    if not lines or lines[0].strip() != "---":
        raise PromptBuildError(f"{path} must start with a standalone --- line")

    closing_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        raise PromptBuildError(f"{path} frontmatter is missing closing ---")

    raw_yaml = "\n".join(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1 :])
    try:
        meta = yaml.safe_load(raw_yaml) or {}
    except yaml.YAMLError as exc:
        raise PromptBuildError(f"{path} frontmatter YAML is invalid: {exc}") from exc
    return meta, body


def _validate_spec(spec: dict[str, Any], path: Path) -> None:
    _require_nonempty_string(spec, "game_name", path)

    difficulty = spec.get("difficulty")
    if difficulty not in VALID_DIFFICULTIES:
        raise PromptBuildError(
            f"{path} field `difficulty` must be one of {sorted(VALID_DIFFICULTIES)}"
        )

    params = spec.get("params")
    if not isinstance(params, dict):
        raise PromptBuildError(f"{path} field `params` must be a mapping")

    _validate_window_size(params.get("window_size"), path)
    _validate_color(params.get("player_color"), path)
    _validate_positive_int(params.get("round_time_sec"), f"{path} params.round_time_sec")
    _validate_checkpoints(spec.get("checkpoints"), path)


def _require_nonempty_string(mapping: dict[str, Any], key: str, path: Path) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PromptBuildError(f"{path} field `{key}` must be a non-empty string")
    return value.strip()


def _validate_window_size(value: Any, path: Path) -> None:
    if not isinstance(value, list) or len(value) != 2:
        raise PromptBuildError(f"{path} params.window_size must be [W, H]")
    for item in value:
        _validate_positive_int(item, f"{path} params.window_size")


def _validate_color(value: Any, path: Path) -> None:
    if not isinstance(value, str) or not COLOR_PATTERN.fullmatch(value):
        raise PromptBuildError(f"{path} params.player_color must be #RRGGBB")


def _validate_positive_int(value: Any, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PromptBuildError(f"{label} must be a positive integer")


def _validate_checkpoints(value: Any, path: Path) -> None:
    if not isinstance(value, list) or not value:
        raise PromptBuildError(f"{path} field `checkpoints` must be a non-empty list")

    seen: set[str] = set()
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise PromptBuildError(f"{path} checkpoint #{index} must be a mapping")

        checkpoint_id = item.get("id")
        if not isinstance(checkpoint_id, str) or not CHECKPOINT_ID_PATTERN.fullmatch(checkpoint_id):
            raise PromptBuildError(f"{path} checkpoint #{index} id must be snake_case")
        if checkpoint_id in seen:
            raise PromptBuildError(f"{path} checkpoint id is duplicated: {checkpoint_id}")
        seen.add(checkpoint_id)

        desc = item.get("desc")
        if not isinstance(desc, str) or not desc.strip():
            raise PromptBuildError(f"{path} checkpoint {checkpoint_id} desc must be non-empty")

        weight = item.get("weight", 1)
        _validate_positive_int(weight, f"{path} checkpoint {checkpoint_id} weight")
        item["weight"] = weight


def _build_placeholder_values(spec: dict[str, Any]) -> dict[str, str]:
    params = spec["params"]
    width, height = params["window_size"]
    rendered = "\n".join(
        f"{index}. {checkpoint['desc'].strip()}"
        for index, checkpoint in enumerate(spec["checkpoints"], start=1)
    )

    return {
        "game_name": spec["game_name"].strip(),
        "window_size": f"{width}x{height}",
        "player_color": params["player_color"].strip(),
        "round_time_sec": str(params["round_time_sec"]),
        "game_description": spec.get("body", "").strip(),
        "checkpoints_rendered": rendered,
    }


def _validate_template_placeholders(
    scaffold_path: Path,
    placeholders: list[str],
    values: dict[str, str],
) -> None:
    seen = set(placeholders)
    unknown = sorted(seen - set(values))
    if unknown:
        raise PromptBuildError(
            f"{scaffold_path} contains unknown placeholder(s): {', '.join('{' + item + '}' for item in unknown)}"
        )

    missing = sorted(REQUIRED_PLACEHOLDERS - seen)
    if missing:
        raise PromptBuildError(
            f"{scaffold_path} is missing required placeholder(s): {', '.join('{' + item + '}' for item in missing)}"
        )

    empty = sorted(key for key in seen if key != "game_description" and not str(values.get(key, "")).strip())
    if empty:
        raise PromptBuildError(
            f"empty value for placeholder(s): {', '.join('{' + item + '}' for item in empty)}"
        )


def _validate_rendered_prompt(prompt: str, spec_path: str | Path) -> None:
    leftovers = sorted(set(PLACEHOLDER_PATTERN.findall(prompt)))
    if leftovers:
        raise PromptBuildError(
            f"{spec_path} rendered prompt has unresolved placeholder(s): "
            + ", ".join("{" + item + "}" for item in leftovers)
        )

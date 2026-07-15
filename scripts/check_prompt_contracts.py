from __future__ import annotations

import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluator.dimension2_functionality.profiles import GAME_PROFILES
from prompt_builder import MAIN_TEMPLATE, SPECS_DIR, build_prompt, load_checkpoints


GAMES_CONFIG = REPO_ROOT / "config" / "games.yaml"


def validate_prompt(spec_path: Path) -> list[str]:
    prompt = build_prompt(MAIN_TEMPLATE, spec_path)
    checkpoints = load_checkpoints(spec_path)
    checkpoint_ids = [item["id"] for item in checkpoints]

    leaked_ids = [checkpoint_id for checkpoint_id in checkpoint_ids if checkpoint_id in prompt]
    if leaked_ids:
        raise ValueError(f"{spec_path} leaks checkpoint id(s): {', '.join(leaked_ids)}")
    if "weight:" in prompt or "id:" in prompt:
        raise ValueError(f"{spec_path} leaks internal checkpoint fields")
    return checkpoint_ids


def validate_active_d2_contracts(config: dict, ids_by_spec: dict[Path, list[str]]) -> None:
    for difficulty, games in config["games"].items():
        for game in games:
            spec_path = SPECS_DIR / difficulty / f"{game}.md"
            profile_id = f"{difficulty}_{game}"
            profile = GAME_PROFILES.get(profile_id)
            if profile is None:
                raise ValueError(f"active game {profile_id} has no D2 detection profile")

            checkpoint_ids = ids_by_spec[spec_path]
            recipe_ids = [port.port_id for port in profile.test_ports]
            missing = [item for item in checkpoint_ids if item not in recipe_ids]
            if missing:
                raise ValueError(
                    f"active game {profile_id} has no recipe for checkpoint(s): {', '.join(missing)}"
                )


def main() -> int:
    config = yaml.safe_load(GAMES_CONFIG.read_text(encoding="utf-8-sig"))
    specs = sorted(SPECS_DIR.glob("*/*.md"))
    if not specs:
        raise ValueError(f"no game specs found under {SPECS_DIR}")

    ids_by_spec = {spec_path: validate_prompt(spec_path) for spec_path in specs}
    validate_active_d2_contracts(config, ids_by_spec)
    active_count = sum(len(games) for games in config["games"].values())
    print(f"PASS: rendered {len(specs)} specs; validated {active_count} active D2 contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

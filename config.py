from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
GAMES_DIR = ROOT_DIR / "games"
PROMPTS_DIR = ROOT_DIR / "prompts"
EVALUATION_RULES_DIR = ROOT_DIR / "evaluation"
RESULTS_RAW_DIR = ROOT_DIR / "results" / "raw"
RESULTS_PROCESSED_DIR = ROOT_DIR / "results" / "processed"

DEFAULT_SCORE_POLICY = ROOT_DIR / "config" / "scoring_policy_minimal.yaml"
DEFAULT_WEIGHTS = ROOT_DIR / "config" / "weights.yaml"

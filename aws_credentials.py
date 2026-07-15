"""Load local AWS credentials without exposing or persisting their values elsewhere."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_CREDENTIALS_CSV = ROOT_DIR / "aws_credentials.csv"
ACCESS_KEY_COLUMN = "Access key ID"
SECRET_KEY_COLUMN = "Secret access key"


def load_aws_credentials(
    csv_path: str | Path = DEFAULT_CREDENTIALS_CSV,
    region: str = "us-east-1",
) -> dict[str, Any]:
    """Populate missing AWS environment variables from a local AWS CSV file."""
    existing_access = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    existing_secret = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
    path = Path(csv_path).expanduser().resolve()

    source = "environment"
    if not (existing_access and existing_secret):
        if not path.is_file():
            return {
                "loaded": False,
                "source": "missing",
                "csv_path": str(path),
                "region": os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or region,
            }

        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = set(reader.fieldnames or [])
            required = {ACCESS_KEY_COLUMN, SECRET_KEY_COLUMN}
            if not required.issubset(fieldnames):
                missing = ", ".join(sorted(required - fieldnames))
                raise ValueError(f"AWS credentials CSV is missing columns: {missing}")
            row = next(reader, None)

        if not row:
            raise ValueError(f"AWS credentials CSV has no credential row: {path}")

        csv_access = str(row.get(ACCESS_KEY_COLUMN, "")).strip()
        csv_secret = str(row.get(SECRET_KEY_COLUMN, "")).strip()
        if not csv_access or not csv_secret:
            raise ValueError(f"AWS credentials CSV contains an empty key value: {path}")

        os.environ["AWS_ACCESS_KEY_ID"] = csv_access
        os.environ["AWS_SECRET_ACCESS_KEY"] = csv_secret
        source = "csv"

    os.environ.setdefault("AWS_REGION", region)
    return {
        "loaded": True,
        "source": source,
        "csv_path": str(path) if source == "csv" else None,
        "region": os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or region,
    }

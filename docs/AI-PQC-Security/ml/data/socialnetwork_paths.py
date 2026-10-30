"""Canonical project-local source for the 2024 SocialNetwork release."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOCIALNETWORK_RAW = PROJECT_ROOT / "ml/data/raw/microservice-ids-2024/socialnetwork"
ARCHIVES = ("SocialNetwork-training-data.zip", "SocialNetwork-validation-data.zip", "SocialNetwork-attack-data.zip")


def source_directory(value=None):
    path = Path(value).resolve() if value is not None else SOCIALNETWORK_RAW
    missing = [name for name in (*ARCHIVES, "README.md") if not (path / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing verified dataset files in {path}: {missing}; run scripts/import-socialnetwork-dataset.ps1")
    return path

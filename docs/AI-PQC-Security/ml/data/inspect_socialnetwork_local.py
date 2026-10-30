"""Default project-local entry point; historical explicit-source scripts stay intact."""
import argparse
import json
from pathlib import Path

from socialnetwork_paths import source_directory, ARCHIVES, PROJECT_ROOT
from inspect_socialnetwork_archives import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "ml/artifacts/socialnetwork-local-inspection-v1.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Inspection evidence exists; choose a fresh output")
    source = source_directory(args.source)
    report = {"schema": "socialnetwork-local-inspection-v1", "source": str(source),
              "attack_traces_decoded": False,
              "archives": [inspect(source / name, probe=name == "SocialNetwork-validation-data.zip") for name in ARCHIVES]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(f"Project-local dataset inspection saved: {args.output}")


if __name__ == "__main__":
    main()

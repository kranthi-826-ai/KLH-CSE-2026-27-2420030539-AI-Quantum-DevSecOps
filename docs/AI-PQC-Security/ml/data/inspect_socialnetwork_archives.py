"""Read-only, bounded archive inspection; never extract or infer attack labels."""
import argparse
import gzip
import io
import json
from pathlib import Path
import tarfile
import zipfile


class BudgetExceeded(Exception):
    pass


class LimitedReader(io.RawIOBase):
    def __init__(self, source, limit):
        self.source, self.remaining = source, limit

    def readable(self):
        return True

    def read(self, size=-1):
        if self.remaining <= 0:
            raise BudgetExceeded()
        size = min(self.remaining, size if size >= 0 else self.remaining)
        data = self.source.read(size)
        self.remaining -= len(data)
        return data


def inspect(path, probe=False, budget=128 * 1024 * 1024):
    result = {"archive": path.name, "bytes": path.stat().st_size, "members": []}
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            result["members"].append({"name": member.filename, "bytes": member.file_size})
        # Only validation is eligible for content probing, not held-out attack data.
        if probe:
            if path.name != "SocialNetwork-validation-data.zip":
                raise ValueError("Content probing is restricted to validation data")
            member = next(m for m in archive.infolist() if m.filename.endswith(".tar.gz"))
            details = {"member": member.filename, "headers": [], "samples": [], "bounded": False}
            result["probe"] = details
            with archive.open(member) as compressed, gzip.GzipFile(fileobj=compressed) as decompressed:
                reader = LimitedReader(decompressed, budget)
                try:
                    with tarfile.open(fileobj=reader, mode="r|") as nested:
                        for item in nested:
                            details["headers"].append({"name": item.name, "bytes": item.size})
                            if item.isfile() and len(details["samples"]) < 4:
                                if item.name.endswith(".zip") and item.size <= 96 * 1024 * 1024:
                                    # One bounded inner ZIP enables central-directory inspection.
                                    content = nested.extractfile(item).read(item.size)
                                    with zipfile.ZipFile(io.BytesIO(content)) as inner:
                                        entry = next(e for e in inner.infolist() if not e.is_dir())
                                        with inner.open(entry) as trace:
                                            lines = [trace.readline(2048).decode("utf-8", errors="replace") for _ in range(8)]
                                        details["samples"].append({"name": item.name, "inner_name": entry.filename,
                                                                  "uncompressed_bytes": entry.file_size, "lines": lines})
                                    # A schema probe must not scan the rest of the huge trace collection.
                                    details["bounded"] = True
                                    break
                                elif item.name.endswith((".zip", ".gz")):
                                    details["samples"].append({"name": item.name, "kind": "binary_not_decoded"})
                                else:
                                    content = nested.extractfile(item).read(min(item.size, 4096))
                                    details["samples"].append({"name": item.name, "prefix": content.decode("utf-8", errors="replace")})
                            if len(details["headers"]) >= 40:
                                details["bounded"] = True
                                break
                except BudgetExceeded:
                    details["bounded"] = True
    return result


def collection_metadata(path, allow_attack_metadata=False):
    """Inventory archives without decoding trace ZIPs; attack metadata is opt-in."""
    allowed = {"SocialNetwork-validation-data.zip", "SocialNetwork-training-data.zip"}
    if allow_attack_metadata:
        allowed.add("SocialNetwork-attack-data.zip")
    if path.name not in allowed:
        raise ValueError("Metadata scanning is restricted to training/validation")
    limit = 32 * 1024**3 if "training" in path.name else (4 * 1024**3 if "attack" in path.name else 512 * 1024**2)
    records = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            if not member.filename.endswith(".tar.gz"):
                continue
            record = {"archive": member.filename, "headers": [], "small_text": []}
            with archive.open(member) as compressed, gzip.GzipFile(fileobj=compressed) as source:
                try:
                    with tarfile.open(fileobj=LimitedReader(source, limit), mode="r|") as nested:
                        for item in nested:
                            record["headers"].append({"name": item.name, "bytes": item.size})
                            if item.isfile() and item.size <= 16384 and item.name.endswith((".txt", ".log", ".csv", ".json", ".md")):
                                record["small_text"].append({"name": item.name, "text": nested.extractfile(item).read().decode("utf-8", errors="replace")})
                except BudgetExceeded:
                    record["incomplete_budget_limit"] = True
            records.append(record)
    return records


def validation_metadata(path):
    if path.name != "SocialNetwork-validation-data.zip":
        raise ValueError("Metadata scanning is restricted to validation")
    return collection_metadata(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--metadata", action="store_true")
    parser.add_argument("--training-metadata", action="store_true")
    parser.add_argument("--attack-metadata", action="store_true", help="Read annotations, never decode attack traces")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite inspection evidence")
    paths = sorted(args.source.glob("SocialNetwork-*-data.zip"))
    if len(paths) != 3:
        raise ValueError("Expected exactly three SocialNetwork archives")
    report = {"schema": "socialnetwork-inspection-v1", "not_training": True,
              "archives": [inspect(p, p.name == "SocialNetwork-validation-data.zip") for p in paths]}
    if args.metadata:
        report["validation_metadata"] = validation_metadata(args.source / "SocialNetwork-validation-data.zip")
    if args.training_metadata:
        report["training_metadata"] = collection_metadata(args.source / "SocialNetwork-training-data.zip")
    if args.attack_metadata:
        report["attack_metadata"] = collection_metadata(args.source / "SocialNetwork-attack-data.zip", allow_attack_metadata=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(f"Saved bounded inspection: {args.output}")


if __name__ == "__main__":
    main()

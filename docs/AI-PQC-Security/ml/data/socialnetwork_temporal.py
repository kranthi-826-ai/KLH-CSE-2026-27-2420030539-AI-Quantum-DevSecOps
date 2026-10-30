"""Causal previous-five-second features from continuously observed syscall windows."""
from collections import defaultdict, deque
from socialnetwork_rich_syscalls import RICH_COLUMNS, SENSITIVE

TEMPORAL_COLUMNS = RICH_COLUMNS + tuple(f"prior5_{name}" for name in SENSITIVE) + (
    "prior5_mean_events", "prior5_max_events", "prior5_observed_windows", "events_to_prior5_mean")


def add_history(rows, first_full_window):
    """Missing rows mean no OBSERVED syscalls only within verified continuous coverage."""
    history = defaultdict(deque)
    result = []
    for row in sorted(rows, key=lambda r: (r["window"], r["container_group"])):
        window = row["window"]
        key = (row.get("recording", ""), row["container_group"])
        prior = history[key]
        while prior and prior[0]["window"] < window - 5:
            prior.popleft()
        if prior and prior[-1]["window"] >= window:
            raise ValueError("Duplicate or noncausal window")
        features = dict(row["features"])
        for name in SENSITIVE:
            features[f"prior5_{name}"] = sum(r["features"][f"sensitive_entry_{name}"] for r in prior)
        mean = sum(r["features"]["events"] for r in prior) / 5
        features.update({"prior5_mean_events": mean,
                         "prior5_max_events": max((r["features"]["events"] for r in prior), default=0),
                         "prior5_observed_windows": len(prior),
                         "events_to_prior5_mean": (row["features"]["events"] + 1) / (mean + 1)})
        result.append({**row, "features": features, "history_complete": window - 5 >= first_full_window})
        prior.append(row)
    return result

"""Versioned syscall detail, preserving base features and excluding identities/arguments."""
import hashlib
from collections import Counter

from socialnetwork_syscalls import COLUMNS, aggregate, bucket

SENSITIVE = ("execve", "execveat", "clone", "clone3", "fork", "vfork", "unshare", "setns",
             "mount", "umount", "umount2", "pivot_root", "chroot", "bpf", "ptrace", "setuid",
             "setgid", "setresuid", "setresgid", "capset", "open", "openat", "write", "mprotect",
             "socket", "setsockopt", "connect", "kill", "init_module", "finit_module", "chmod", "chown")
RICH_COLUMNS = tuple(COLUMNS) + tuple(f"entry_syscall_{i}" for i in range(128)) + tuple(
    f"entry_category_{i}" for i in range(16)) + tuple(f"sensitive_entry_{name}" for name in SENSITIVE) + tuple(
    f"thread_transition_{i}" for i in range(64))


def rich_aggregate(lines):
    states = {}

    def observe():
        for line in lines:
            fields = line.split(maxsplit=6)
            if len(fields) >= 6 and fields[3] == ">":
                try:
                    timestamp = int(fields[0])
                except ValueError:
                    timestamp = -1
                if timestamp >= 0:
                    key = (timestamp // 1_000_000_000, hashlib.sha256(fields[1].encode()).hexdigest())
                    state = states.setdefault(key, {"calls": Counter(), "categories": Counter(), "transitions": Counter(), "last": {}})
                    syscall = fields[5]
                    state["calls"][syscall] += 1
                    state["categories"][fields[4]] += 1
                    previous = state["last"].get(fields[2])
                    if previous is not None:
                        state["transitions"][previous + "->" + syscall] += 1
                    state["last"][fields[2]] = syscall
            yield line

    rows, audit = aggregate(observe())
    for row in rows:
        state = states.get((row["window"], row["container_group"]), {"calls": {}, "categories": {}, "transitions": {}})
        count = max(1, sum(state["calls"].values()))
        calls, categories, transitions = [0.] * 128, [0.] * 16, [0.] * 64
        for name, value in state["calls"].items():
            calls[bucket(name, 128)] += value / count
        for name, value in state["categories"].items():
            categories[bucket(name, 16)] += value / count
        transition_count = max(1, sum(state["transitions"].values()))
        for name, value in state["transitions"].items():
            transitions[bucket(name, 64)] += value / transition_count
        values = calls + categories + [state["calls"].get(name, 0) for name in SENSITIVE] + transitions
        row["features"].update(dict(zip(RICH_COLUMNS[len(COLUMNS):], values)))
    return rows, audit

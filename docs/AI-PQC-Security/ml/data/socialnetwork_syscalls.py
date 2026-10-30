"""Bounded syscall-prefix features for a separate, experimental host IDS."""
import hashlib
import struct
import zlib
from collections import Counter

WINDOW_NS = 1_000_000_000
COLUMNS = ("events", "exit_fraction", "negative_exit_fraction", "unique_syscalls", "unique_threads") + tuple(
    f"syscall_bin_{i}" for i in range(16)) + tuple(f"category_bin_{i}" for i in range(8))


def bucket(value, width):
    return int.from_bytes(hashlib.sha256(value.encode()).digest()[:4], "little") % width


def first_zip_lines(source, max_lines=500_000, max_bytes=128 * 1024**2):
    """Stream first local ZIP entry; no seeking/extraction; prefixes are not CRC-verified."""
    header = source.read(30)
    if len(header) != 30:
        raise ValueError("Truncated inner ZIP header")
    fields = struct.unpack("<4s5H3I2H", header)
    if fields[0] != b"PK\x03\x04" or fields[2] & 1 or fields[3] != 8:
        raise ValueError("Expected unencrypted deflated first ZIP entry")
    skip = fields[9] + fields[10]
    if len(source.read(skip)) != skip:
        raise ValueError("Truncated ZIP name/extra")
    inflater = zlib.decompressobj(-15)
    buffer = b""
    total = count = 0
    while total < max_bytes and count < max_lines:
        chunk = inflater.unconsumed_tail or source.read(65536)
        if not chunk:
            if not inflater.eof:
                raise ValueError("Truncated ZIP deflate stream")
            break
        output = inflater.decompress(chunk, min(65536, max_bytes - total))
        total += len(output)
        buffer += output
        while b"\n" in buffer and count < max_lines:
            line, buffer = buffer.split(b"\n", 1)
            if len(line) > 65536:
                raise ValueError("Oversized syscall line")
            count += 1
            yield line.decode("utf-8", errors="strict")
        if len(buffer) > 65536:
            raise ValueError("Oversized syscall line")
        if inflater.eof:
            break


def aggregate(lines):
    """Nonoverlapping one-second windows; boundary windows excluded, IDs metadata only."""
    groups = {}
    first = last = None
    parsed = rejected = 0
    for line in lines:
        fields = line.split(maxsplit=6)
        if len(fields) < 6 or fields[3] not in {"<", ">"}:
            rejected += 1
            continue
        try:
            timestamp = int(fields[0])
        except ValueError:
            rejected += 1
            continue
        if timestamp < 0:
            rejected += 1
            continue
        window = timestamp // WINDOW_NS
        first = window if first is None else min(first, window)
        last = window if last is None else max(last, window)
        key = (window, fields[1])
        state = groups.setdefault(key, {"count": 0, "exit": 0, "negative": 0,
                                       "syscalls": Counter(), "threads": set(), "categories": Counter()})
        state["count"] += 1
        state["exit"] += fields[3] == "<"
        arguments = fields[6] if len(fields) == 7 else ""
        state["negative"] += fields[3] == "<" and any(v.startswith("res=-") for v in arguments.split())
        state["syscalls"][fields[5]] += 1
        state["categories"][fields[4]] += 1
        state["threads"].add(fields[2])
        parsed += 1
    rows = []
    for (window, container), state in sorted(groups.items()):
        if window in {first, last}:
            continue
        count = state["count"]
        sysbins, catbins = [0] * 16, [0] * 8
        for syscall, value in state["syscalls"].items():
            sysbins[bucket(syscall, 16)] += value / count
        for category, value in state["categories"].items():
            catbins[bucket(category, 8)] += value / count
        values = [count, state["exit"] / count, state["negative"] / max(1, state["exit"]),
                  len(state["syscalls"]), len(state["threads"])] + sysbins + catbins
        rows.append({"window": window, "container_group": hashlib.sha256(container.encode()).hexdigest(),
                     "features": dict(zip(COLUMNS, values))})
    return rows, {"parsed_events": parsed, "rejected_events": rejected, "first_window": first,
                  "last_window": last, "boundary_windows_excluded": True}

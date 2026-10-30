"""Generic syscall return-error features; no argument payloads or annotation inputs."""
from collections import Counter
import hashlib
import re

from socialnetwork_syscalls import aggregate, bucket, COLUMNS

ERRNOS = (1, 2, 3, 4, 5, 9, 11, 12, 13, 14, 16, 17, 22, 24, 110, 115)
ERROR_COLUMNS = ('reported_error_count', 'reported_error_exit_fraction') + tuple(
    f'reported_errno_{code}' for code in ERRNOS) + tuple(f'error_pair_{i}' for i in range(32))
COLUMNS_WITH_ERRORS = tuple(COLUMNS) + ERROR_COLUMNS


def reported_error(arguments):
    # Only the actual leading result/descriptor field, not a "res=" string
    # embedded in a command, file path, payload or other arbitrary argument.
    first = arguments.split(maxsplit=1)[0] if arguments.strip() else ''
    match = re.fullmatch(r'(?:res|fd)=-(\d+)(?:\([^\s]*\))?', first)
    return int(match[1]) if match and int(match[1]) > 0 else None


def aggregate_errors(lines):
    states = {}
    def observe():
        for line in lines:
            fields = line.split(maxsplit=6)
            if len(fields) >= 6 and fields[3] == '<':
                timestamp = int(fields[0])
                group = hashlib.sha256(fields[1].encode()).hexdigest()
                state = states.setdefault((timestamp // 1_000_000_000, group),
                                          {'exits':0, 'errors':Counter(), 'pairs':Counter()})
                state['exits'] += 1
                error = reported_error(fields[6] if len(fields) == 7 else '')
                if error is not None:
                    state['errors'][error] += 1
                    state['pairs'][fields[5] + ':' + str(error)] += 1
            yield line
    rows, audit = aggregate(observe())
    for row in rows:
        state = states.get((row['window'], row['container_group']), {'exits':0, 'errors':{}, 'pairs':{}})
        count = sum(state['errors'].values())
        pairs = [0.] * 32
        for name, value in state['pairs'].items():
            pairs[bucket(name, 32)] += value / max(1, count)
        values = [count, count / max(1, state['exits'])] + [state['errors'].get(code, 0) / max(1, count) for code in ERRNOS] + pairs
        row['features'].update(dict(zip(ERROR_COLUMNS, values)))
    return rows, audit

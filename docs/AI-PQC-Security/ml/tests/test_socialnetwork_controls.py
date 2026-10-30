import io
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from evaluate_socialnetwork_controls import control_lines


def test_control_slice_is_pre_attack_and_matches_exact_pod():
    case = {"start_ns": 1700237693000000000, "pod": "nginx-ab-12"}
    start = case["start_ns"]
    lines = [f"{start + offset * 1000000000} k8s_nginx_nginx-ab-12_default_uid_0 1 < NET read res=0\n"
             for offset in (-65, -55, -20, -5, 2)]
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("events.txt", "".join(lines))
    audit = {"scanned_events": 0, "max_timestamp_ns": 0}
    hashes = set()
    selected = list(control_lines(io.BytesIO(stream.getvalue()), case, audit, hashes))
    assert len(selected) == 2
    assert all(int(line.split()[0]) < start - 10000000000 for line in selected)
    assert len(hashes) == 1

import io
from pathlib import Path
import sys
import zipfile
import hashlib

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from map_socialnetwork_roles import service_role, map_trace


def test_role_is_container_type_not_replica_identity():
    assert service_role("k8s_nginx-thrift_nginx-thrift-abc-12_default_uid_0") == "nginx-thrift"
    assert service_role("k8s_nginx-thrift_nginx-thrift-def-99_default_other_0") == "nginx-thrift"
    with pytest.raises(ValueError):
        service_role("untrusted-header")


def test_mapping_requires_every_requested_group():
    container = "k8s_nginx-thrift_nginx-thrift-abc-12_default_uid_0"
    source = io.BytesIO()
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("trace", f"1700000000000000000 {container} 1 < NET read res=0\n")
    group = hashlib.sha256(container.encode()).hexdigest()
    mapping = {}
    map_trace(io.BytesIO(source.getvalue()), {group}, mapping)
    assert mapping[group] == "nginx-thrift"
    with pytest.raises(ValueError, match="every cached group"):
        map_trace(io.BytesIO(source.getvalue()), {"unknown"}, {})

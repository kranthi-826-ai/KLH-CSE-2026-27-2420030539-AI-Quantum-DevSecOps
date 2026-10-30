"""Read-only post-run cross-check of frozen matrix receipts against actual MySQL audit joins."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from verify_adaptive_matrix import CASES, MODEL_SHA, ROOT, prototype
from verify_database_recovery import Mysql, read_password


def validate_receipt(receipt):
    if receipt.get('passed') is not True or receipt.get('model_sha256')!=MODEL_SHA:
        raise ValueError('Require a completed receipt for the frozen model')
    expected={(case[0],repeat):case for case in CASES for repeat in range(2)}
    rows=receipt.get('rows',[])
    if len(rows)!=32 or {(row.get('case'),row.get('repeat')) for row in rows}!=set(expected):
        raise ValueError('Missing or duplicate frozen scenarios')
    correlations=set();identities=set();run_ids=set()
    for row in rows:
        case=expected[(row['case'],row['repeat'])]
        if (row.get('passed') is not True or row.get('actual_http')!=case[-1] or
            row.get('expected_mode')!=case[-2] or row.get('expected_effective_risk')!=case[-3]
            or row.get('selection_threshold_ms')!=case[4]):
            raise ValueError('Scenario receipt differs from frozen expected result')
        correlation=row.get('correlation_id','')
        match=re.fullmatch(r'matrix-([0-9a-f]{32})-([01])-([a-z_]+)',correlation)
        if not match or int(match[2])!=row['repeat'] or match[3]!=row['case'] or len(correlation)>80:
            raise ValueError('Invalid synthetic correlation')
        run_ids.add(match[1]);correlations.add(correlation)
        for key in ('execution_id','decision_id'):
            value=row.get(key,'')
            if not re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',value):
                raise ValueError('Invalid recorded identity')
            if value in identities:raise ValueError('Reused execution/decision identity')
            identities.add(value)
    if len(correlations)!=32 or len(run_ids)!=1:raise ValueError('Mixed run identities')
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    folder=args.directory.resolve()
    if folder.parent!=(ROOT/'ml/artifacts').resolve():raise ValueError('Require an immediate artifact child')
    output=folder/'adaptive-audits-recheck.json'
    if output.exists():raise ValueError('Refusing to overwrite a prior audit check')
    path=folder/'adaptive-matrix.json'
    receipt=json.loads(path.read_text(encoding='utf-8'))
    rows=validate_receipt(receipt)
    db=Mysql(read_password())
    payload_hash=hashlib.sha256(prototype()['data'].encode()).hexdigest()
    # All interpolated values passed the fixed ASCII identity/correlation guards above.
    cases=' UNION ALL '.join(f"SELECT '{row['correlation_id']}' AS correlation_id,'{row['execution_id']}' AS execution_id,'{row['decision_id']}' AS decision_id" for row in rows)
    query="SELECT JSON_OBJECT('executions',COUNT(DISTINCT b.execution_id),'decisions',COUNT(DISTINCT p.decision_id),"\
        "'events',COUNT(DISTINCT e.event_id),'verified',SUM(b.outcome='SUCCESS' AND CAST(b.round_trip_verified AS UNSIGNED)=1),"\
        "'denied',SUM(b.outcome='FAILED' AND CAST(b.round_trip_verified AS UNSIGNED)=0 AND b.risk_level='HIGH' AND b.selected_mode='CLASSICAL'),"\
        "'consistent',SUM(b.selected_mode=p.selected_mode AND b.risk_level=p.effective_risk_level AND p.input_risk_level='MEDIUM' "\
        "AND b.model_version=p.model_version AND b.model_version='"+MODEL_SHA[:16]+"' AND b.policy_version=p.policy_version "\
        "AND b.policy_version='1.1.0' AND b.payload_sha256='"+payload_hash+"' "\
        "AND ((b.outcome='SUCCESS' AND e.outcome='SUCCESS') OR (b.outcome='FAILED' AND e.outcome='FAILURE')))) "\
        "FROM ("+cases+") fixture JOIN pqc_business_db.crypto_executions b ON b.execution_id=fixture.execution_id AND b.correlation_id=fixture.correlation_id "\
        "JOIN pqc_policy_db.policy_decisions p ON p.decision_id=fixture.decision_id AND p.decision_id=b.decision_id AND p.correlation_id=b.correlation_id "\
        "JOIN pqc_monitoring_db.security_events e ON e.correlation_id=b.correlation_id AND e.username=b.username "\
        "AND e.request_path='/api/v1/business/adaptive-secure-data';"
    actual=json.loads(db.sql(query))
    expected={'executions':32,'decisions':32,'events':32,'verified':24,'denied':8,'consistent':32}
    if actual!=expected:raise RuntimeError('Post-run MySQL audit joins differ from frozen expectations')
    result={'schema':'adaptive-audit-postcheck-v1','passed':True,'read_only':True,
        'matrix_receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'database_join_counts':actual,
        'scope':'Actual MySQL execution/policy/event identities,versions,payload fingerprints and outcomes; no inference rerun'}
    with output.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

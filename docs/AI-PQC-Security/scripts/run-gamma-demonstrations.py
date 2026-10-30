"""Run labelled presentation fixtures through real APIs; never export credentials."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tests/live'))
from verify_stack import request

account = json.loads((root/'ml/artifacts/gamma-capture-20261029/demo-account.json').read_text())
status, login = request('/api/v1/auth/login', body=account)
assert status == 200
token = login['token']
raw = (root/'tests/e2e/bruno/AI-PQC-Security/Adaptive_Secure_Data.bru').read_text()
prototype, _ = json.JSONDecoder().raw_decode(raw.split('body:json {', 1)[1].lstrip())
results = []
for mode, sensitivity, pqc, hybrid in [('CLASSICAL','PUBLIC',False,False), ('HYBRID','RESTRICTED',False,True), ('PQC','RESTRICTED',True,True)]:
    status, result = request('/api/v1/business/adaptive-secure-data', token=token,
        correlation=f'presentation-20261029-{mode.lower()}',
        body={**prototype,'data':'Labelled presentation demonstration payload', 'dataSensitivity':sensitivity,'pqcSupported':pqc,'hybridSupported':hybrid})
    assert status == 200 and result['selectedMode'] == mode and result['roundTripVerified']
    results.append({k:result[k] for k in ('executionId','decisionId','correlationId','selectedMode','algorithmProfile','riskLevel','riskScore','roundTripVerified','policyLatencyMillis','cryptoLatencyMillis','totalLatencyMillis')})
status, _ = request('/api/v1/business/adaptive-secure-data',token=token,correlation='presentation-20261029-denied-downgrade',
                    body={**prototype,'dataSensitivity':'RESTRICTED','pqcSupported':False,'hybridSupported':False})
assert status == 422
out = root/'output/gamma-presentation'
out.mkdir(parents=True,exist_ok=True)
(out/'live-demo-results.json').write_text(json.dumps({'scope':'Controlled presentation fixtures, not new ML evaluation','verified_executions':results,'unsafe_downgrade_http_status':status},indent=2))
print('Three real API profiles verified; unsafe downgrade rejected with HTTP 422. No credentials exported.')

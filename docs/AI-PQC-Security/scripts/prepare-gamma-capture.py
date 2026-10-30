"""Create a dedicated local demonstration account without logging its credentials."""
import json
import secrets
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'ml/artifacts/gamma-capture-20261029'
out.mkdir(parents=True, exist_ok=True)
account = {'username': 'presentation_' + secrets.token_hex(4), 'password': secrets.token_urlsafe(24)}
req = urllib.request.Request('http://127.0.0.1:8080/api/v1/auth/register',
                             data=json.dumps(account).encode(), headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req, timeout=20) as response:
    assert response.status == 201
(out / 'demo-account.json').write_text(json.dumps(account), encoding='utf-8')
print('Dedicated local demonstration account created. Credentials remain in ignored local artifacts.')

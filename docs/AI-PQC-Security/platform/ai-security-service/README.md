# AI Security Service

FastAPI inference service for the current UNSW-NB15 Random Forest candidate.
It accepts the exact network-flow feature schema used during training and
returns a probability, risk level, model identity, and explanation.

It intentionally does not reinterpret authentication/API audit events as
UNSW-NB15 flows. A separately trained system-event model will be required for
that schema after enough de-identified project events are collected.

Run from the repository root:

```powershell
ml/.venv/Scripts/python.exe -m pip install -r platform/ai-security-service/requirements.txt
$env:PYTHONPATH="platform/ai-security-service"
$env:MONITORING_API_KEY="use-the-same-local-key-as-the-policy-engine"
ml/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8090
```

Open `http://localhost:8090/docs` for the local OpenAPI interface. Prediction
requests must include `X-Internal-API-Key`; health and model metadata remain
available for local readiness checks.

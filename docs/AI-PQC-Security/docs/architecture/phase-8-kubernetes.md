# Phase 8 Kubernetes Foundation

The manifests under `infrastructure/kubernetes` reproduce the verified Compose
topology in the `ai-pqc-security` namespace. They use resource limits sized for
a 16 GB development laptop, persistent database and model volumes, non-public
internal services, health probes, and default-deny network isolation.

Secrets are deliberately absent from Git. Create them locally before applying
the manifests:

```text
kubectl create namespace ai-pqc-security
kubectl -n ai-pqc-security create secret generic ai-pqc-secrets \
  --from-literal=DB_PASSWORD=<strong-password> \
  --from-literal=JWT_SECRET=<at-least-32-random-characters> \
  --from-literal=MONITORING_API_KEY=<random-internal-key>
```

The 106 MB promoted model is also excluded from Git and container images. Apply
`storage.yaml`, wait for `model-loader`, copy the promoted artifact, and then
apply the full kustomization:

```text
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/storage.yaml
kubectl -n ai-pqc-security wait --for=condition=Ready pod/model-loader --timeout=120s
kubectl -n ai-pqc-security cp ml/models/promoted/model.joblib model-loader:/models/model.joblib
kubectl apply -k infrastructure/kubernetes
```

For Docker Desktop Kubernetes, build the Compose images first so the local
cluster can reuse them with `imagePullPolicy: IfNotPresent`. The dashboard and
gateway are exposed on NodePorts `30088` and `30080`; every other application
service remains cluster-internal. Delete `model-loader` after the model copy.

The model PVC supports later controlled promotion and rollback without baking a
large research artifact into an application image. Production clusters should
replace local image names with immutable registry digests and use an external
secret manager and managed database.

# Optional operator email alerts

The selected operational channels are dashboard + email. Dashboard access remains
administrator-only. SMTP is optional and disabled until deliberately configured;
the project must not claim that a real operator received an email yet.

## Private configuration

Copy `infrastructure/monitoring/email.env.example` to root `.env.email` and edit
that private file locally. Both `.env.email` and `.runtime/` are Git-ignored.
Supply the SMTP hostname, port, sender, username, provider-specific app password
and a single recipient. Do not paste passwords into chat, commands or research
evidence. Providers requiring OAuth rather than SMTP app passwords need a
separate integration; this implementation does not claim OAuth support.

Run `ml/.venv/Scripts/python.exe scripts/configure_email_alerts.py` to validate
without writing or connecting. Add `--apply` to generate restricted runtime
files. The generated configuration references a separate password file, requires
TLS with normal certificate checks, and explicitly selects implicit TLS for
port465. It never prints credentials or sends email during preparation.
Windows output-directory ACLs are restricted to the current user before writing.

Production notification grouping waits30 seconds, groups updates over5 minutes,
repeats persistent incidents every4 hours and sends recovery notifications.
These intervals do not replace the unchanged Prometheus rule holds.
The sender/recipient fields are addresses, not user-supplied template code.

## Deployment acceptance is still pending

`docker-compose.email.yml` is an **unverified deployment candidate**, not a
one-click production release. Compose syntax validates without starting Docker.
It adds a loopback-bound Alertmanager and a generated Prometheus alert target.
No Docker daemon or external SMTP provider was started during local testing.

Before enabling it, verify bind-mount permissions from inside the intended
non-root container. Generated host files are0600: a Linux container UID65534
will not normally read a file owned by another host UID. Use a reviewed secret
mount/ownership strategy for the actual host; do not make passwords world-readable
or run the service as root to bypass the issue. Windows Docker Desktop mount
behavior is also unverified. Verify storage access, image policy, networking,
sender authentication, TLS negotiation, actual inbox receipt and outage/recovery
on that deployment before calling email operational. Existing base-stack ports
and metrics still need production ingress/access-control hardening.

## Reproducible synthetic transport tests

Prepare the publisher-checksummed pinned tools with
`scripts/prepare-alertmanager-tools.ps1`. The binary is retained only under
ignored `ml/artifacts/tools/`. No email account is needed.

`tests/live/verify_email_transport.py --output-directory ml/artifacts/NEW_RUN`
starts owned loopback-only Alertmanager and SMTP sink processes. The sink
accepts only fixed `example.test` envelopes and cannot relay. It rejects the
first message temporarily, then checks firing delivery, retry, suppression of
three identical updates, and recovery delivery. It stops its owned servers.
The fixture deliberately disables SMTP TLS **only for fixed127.0.0.1**; this is
not provider TLS/authentication evidence. No production credentials are read.

Add `--rule-engine` to test actual Prometheus production rules through
Alertmanager to that sink. Synthetic DEAD metrics drive the unchanged1-minute
hold; the firing fixture remains active8 additional seconds for local transport
retry, then recovers. A separate sibling engine artifact preserves the state
trace. This proves only the measured local chain, not a deployed cluster,
guaranteed notification latency, remote provider delivery or email acknowledgement.

Primary configuration reference:
[Alertmanager configuration](https://prometheus.io/docs/alerting/latest/configuration/).

# ADR 0004 — Identity-scoped audit and execution reads

Date: 2026-10-20. Status: implemented; verification results recorded separately.

## Gap and decision

The authenticated list endpoints previously returned the latest 100 global rows
to every user. This exposed other users' operational metadata. Both endpoints
now apply access scope in the repository query, before ordering/limiting:

- A verified JWT with exact `ROLE_ADMIN` authority may read the global latest 100.
- Other authenticated principals may read only rows matching their signed subject.
- Unattributed events are visible only in the administrative global view.
- Anonymous requests remain 401. Query parameters and caller role/username
  headers cannot expand access. No client-selected username is used for scope.

Public registration continues to assign ROLE_USER server-side. There is no
public role-promotion endpoint. Operator provisioning must be an explicit trusted
administrative operation, not a dashboard toggle or a registration body field.
Do not put the JWT secret in the frontend or mint admin tokens in a browser.

## Verification plan

Real HTTP tests in each service use signed user/admin JWTs and persisted H2 rows,
checking two users, an empty third identity, anonymous access, forged role headers,
username/role query parameters and an unattributed event. Live MySQL verification
adds user isolation, attempted registration escalation and short-lived signed
operator fixtures using only the isolated runner's ephemeral key. These fixture
tokens stay in memory and do not create/promote a real administrator account.

## Limitations

This is user-record isolation, not organization/tenant RBAC or complete incident
authorization. A failed-login event's username is the attempted account, not
proof of who sent the request. Roles remain JWT snapshots until expiry; changing
a database role does not revoke an existing token. Shared signing-secret trust,
operator provisioning/revocation, TLS, least-privilege DB access and protected
service ingress remain deployment requirements. The ordinary user's dashboard
now represents that user's records, not global system activity.

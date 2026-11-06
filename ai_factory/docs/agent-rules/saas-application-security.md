---
name: saas-application-security
description: Security rules for CarbonTally's API, authentication, transport and storage boundaries. Use for authorisation, session handling, CORS/CSP/headers, input handling, signed URLs, secret handling, or any change to an endpoint that reads or writes tenant data. Supabase Auth owns credentials and sessions; RLS is the primary isolation layer.
---

# Application Security — Authorisation, Sessions, Transport, Storage

**Tier 2.** Defers to [carbontally-agent-governance.md](carbontally-agent-governance.md).

## 1. When to activate

Any endpoint or dependency that reads/writes tenant data; any auth, session, CORS, CSP or
header change; any storage/signed-URL path; any use of the service-role key.

## 2. The control order (do not invert it)

1. **RLS** — the primary isolation layer. Deny by default.
2. **Server-side authorisation** — explicit checks per route, tenant taken from the
   authenticated principal, never from the request body.
3. **Framework validation** — Pydantic models with `extra="forbid"`; parameterised SQL.
4. **UI** — presentation only. Never the boundary.

## 3. Hard rules

1. **The tenant comes from the principal.** Never trust an `organization_id` in a body or
   query without verifying membership.
2. **Cross-tenant reads return 404, not 403** — do not confirm the existence of another
   tenant's resource.
3. **Never disable or widen RLS**; never grant `service_role` to a request path that can be
   reached by a customer. If elevated access is required, keep explicit application-level
   authorisation and document why.
4. **Sessions belong to the auth provider.** Supabase Auth manages the browser session; do not
   move tokens into your own cookie scheme as a "fix". Compensating controls instead: strict
   CSP for `script-src`, no `dangerouslySetInnerHTML`, short token lifetime, server-side
   revocation, RLS. Any change to the session model is a PO decision.
5. **CSP**: `style-src 'unsafe-inline'` is required by MUI/Emotion and is permitted **only**
   for styles. Never relax `script-src`.
6. **Parameterise on write, escape on render.** Do not "sanitise" values before insertion —
   it corrupts legitimate data.
7. **Signed URLs are credentials.** Issue only after authorisation; never log, never include
   in an error body, never assume the path is authorisation.
8. **Storage policies are enforced by the provider.** `storage.objects` policies are an
   operator step, not a migration. A read-only role must not write; verify it per environment.
9. **No password hashing in application code** — Supabase Auth owns it. Audit for credential
   handling that bypasses the provider.
10. **Evidence over assertion**: any security change ships with ALLOW **and** DENY tests.

## 4. Anti-patterns

- **The Body-Tenant** — authorising from `request.organization_id`.
- **The Helpful 403** — confirming that another tenant's record exists.
- **The Service-Role Shortcut** — bypassing RLS to make a query work.
- **The Disabled Control** — treating a hidden button as authorisation.
- **The Logged Signed URL** — a credential in a log line.
- **The Cookie Rewrite** — replacing the provider's session model to satisfy a generic rule.

## 5. Self-check

- [ ] Is the tenant derived from the principal?
- [ ] Does a cross-tenant attempt return 404 (or a non-disclosing refusal)?
- [ ] Are there ALLOW and DENY tests for the new path?
- [ ] Did I touch RLS, a policy, or the service-role surface? (if yes, why, and what tests?)
- [ ] Are secrets, tokens and signed URLs absent from logs and responses?
- [ ] Does the change rely on the UI for authorisation anywhere?

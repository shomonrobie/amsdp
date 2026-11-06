---
name: saas-ai-provider-registry
description: Rules for CarbonTally's AI provider/model registry, eligibility gate, lifecycle and credential custody. Use when registering or activating a provider or model, changing pricing data, routing a document to a model, changing eligibility rules, or touching provider credentials. Registration is inert; approval, attestation and activation are separate operations.
---

# AI Provider & Model Registry — Lifecycle, Eligibility, Credentials

**Tier 2.** Defers to [carbontally-agent-governance.md](carbontally-agent-governance.md).
Provider choice is **PO-authorised** (V-3): a provider may be approved for development/testing
only, pending an IDTA/TRA. Read the current state; never assume.

## 1. When to activate

Any change to `ai_providers`, `ai_models`, `ai_model_prices`, `ai_registry_audit`, the
eligibility resolver, the vision escalation ladder, model routing, or credential handling.

## 2. Two lifecycle machines — never one

| Object | States |
|---|---|
| Provider | `registered → active → suspended → retired` |
| Model | `registered → tested → active → suspended → retired` |

- **Approval is a separate boolean** (`provider_approved`), not a state.
- **Residency attestation is a dated field that expires.** An expired attestation makes the
  provider ineligible.
- **`ineligible` is derived, never stored.** Do not add an `ineligible` status value.
- Do not invent a model state (`approved`, `attested`) that nothing reads — a silent no-op
  looks like a working gate.

## 3. Registration is inert

Registering a provider or model grants no routing eligibility. Nothing may be routed until it
is activated, approved, attested and priced.

## 4. The eligibility gate is six checks, fail-closed

A model may be used only when **all** hold:

1. platform AI is enabled;
2. the model is vision-capable (for vision routing);
3. the model is manually activated;
4. the provider is `active` **and** `provider_approved`;
5. the residency attestation is current;
6. the tokenisation/pricing basis is complete.

Evaluate **per document / per call**, not once at startup — a suspension must take effect
immediately. Return named outcomes (`no_eligible_model`, `VISION_UNAVAILABLE`,
`attestation_expired`); never a generic failure.

## 5. Credentials — ciphertext at rest, never echoed

- Keys live encrypted (`pgp_sym_encrypt` with a transaction-local key) plus a one-way
  fingerprint for rotation. There is **no plaintext column**.
- Never log, return or error-echo a credential. A response may reduce a credential-shaped
  value to `...` + last 4; that masking is defence in depth, not authorisation.
- Credential writes are audited (`ai_registry_audit`): actor, action, target, previous/new
  state, timestamp.

## 6. Hard rules

1. **No routing without activation.** A retired or suspended provider receives nothing.
2. **Never hard-code a provider blocklist.** Evaluate eligibility rules; a blocklist is the
   **Blocklist Fallacy** and was explicitly superseded.
3. **Never invent a provider priority ranking.** Routing order is configured, not guessed.
4. **Prices are data, not code.** Per-1M pricing lives in `ai_model_prices`; unknown cost is
   written as SQL `NULL`, never `0`.
5. **Do not silently retry into a different provider** to make a request succeed. An escalation
   is a recorded decision with its outcome.
6. **The customer UI never displays the provider name in production** (V-3).

## 7. Anti-patterns

- **The Boolean Activation** — replacing the lifecycle with an on/off flag.
- **The Stored Ineligible** — persisting a derived state that then drifts.
- **The Blocklist Fallacy** — banned-provider list instead of eligibility rules.
- **The Env-Var Key** — a provider secret in the process environment when the registry owns it.
- **The Silent Substitution** — falling back to another model without recording it.

## 8. Self-check

- [ ] Did I keep approval, attestation and activation separate?
- [ ] Is `ineligible` still derived?
- [ ] Does the gate check all six conditions, per call?
- [ ] Is the credential never logged/echoed, and is custody unchanged?
- [ ] Is provider activation a PO-authorised state I read rather than assumed?
- [ ] Is the cost of an unknown basis `NULL`, not zero?

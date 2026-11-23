# QUE-006 W5 — Remote Voice Catalogue Installation (implementation report)

**Assignment ID:** `AMSDP-QUE-006-W5-REMOTE-INSTALLATION`
**Date:** 2026-11-21
**Status:** **PARTIALLY IMPLEMENTED.** The facility-side agent is implemented and verified against a stub
distribution endpoint and a real temporary directory: verified download, atomic install, previous-version
retention, rollback, crash recovery and offline use. The **server-side distribution API does not exist**
(it depends on W3's pack identity, which this host cannot run) and no facility PC was used.

---

## 1. What is implemented

| File | Status | Purpose |
|---|---|---|
| `scripts/que-006-agent/lib/installer.mjs` | new, 349 lines | Bundle fetch, per-file SHA-256 verification, safe paths, staging, atomic swap, rollback, recovery, status file |
| `scripts/que-006-agent/agent.mjs` | new, 116 lines | CLI: `--status`, `--once`, `--interval`, `--rollback <packId>`; configuration from environment only |
| `scripts/que-006-agent/tests/installer.test.mjs` | new, 10 tests | Every guarantee below, against a real HTTP stub server and a temp install root |

### 1.1 The architecture, exactly as approved (assignment §3.5)

| Approved element | Implementation |
|---|---|
| A local agent runs on the facility's PC | `agent.mjs` — runnable by `node`, no dependency, no listener |
| Polls over a secure outbound connection | fetches `packs/<packId>/bundle.json` and each file; the bearer token is attached once, in `createAgent` |
| Downloads and verifies approved catalogues | every file is verified by SHA-256 of the received bytes **before** it is written; the bundle must name `pack.json` |
| Installs updates atomically | the tree is built in `staging-<version>` and swapped by `rename`; nothing partial becomes `current` |
| Retains the previous catalogue for rollback | `current` → `previous` on every successful update; `rollback()` restores it |
| Reports installation and update status | `state.json` (write-then-rename) + `status()`; the CLI prints it |
| Keeps working offline | `activeRoot()` is a local filesystem read; a failed poll never touches `current` |
| No inbound access to facility PCs | no server, no socket, no listener anywhere in the agent |

### 1.2 Security properties that are actually enforced

- **Checksum, not extension.** A tampered file is refused (`checksum_mismatch`) and the install fails with
  nothing changed.
- **Path traversal refused.** `safeRelativePath()` rejects `..`, absolute paths, Windows drive letters and
  backslashes; a bundle that tries it fails with `invalid_path` and writes nothing outside the pack
  directory (the test asserts the outside path does not exist).
- **Pack id is a directory name**, so it is validated as a plain token (`safePackId`).
- **Manifest identity is checked**: the downloaded `pack.json` must declare the same id and version as the
  bundle, so a mislabelled package cannot be installed under another pack.
- **The token is never printed**, never a CLI argument (so it cannot leak through a process list), and only
  travels outbound.

## 2. Test evidence

`node --test scripts/que-006-agent/tests/installer.test.mjs` — **10/10 pass**:

1. a first install verifies, writes and reports its version
2. an unchanged version is up-to-date and downloads nothing
3. a checksum mismatch installs nothing and leaves no staging tree
4. a failed update leaves the working catalogue untouched
5. an update keeps the previous version and rollback restores it
6. a path that escapes the pack directory is refused
7. recovery removes a stale staging tree and promotes the previous catalogue
8. offline: the active catalogue is readable with no server at all
9. the agent refuses to run without a server or a pack list
10. the agent installs every entitled pack over an outbound call only

## 3. Status per assignment §W5 requirement

| # | Requirement | Status |
|---|---|---|
| 1 | Local agent on facility PC | **IMPLEMENTED AND VERIFIED** (as a Node CLI) |
| 2 | Secure outbound polling | **IMPLEMENTED AND VERIFIED** (bearer token attached once, outbound only) |
| 3 | Catalogue/version discovery | **IMPLEMENTED AND VERIFIED** (`bundle.json` index; `up-to-date` short-circuit) |
| 4 | Authenticated package download | **IMPLEMENTED** (token attached) — the **server** that authenticates it is **NOT IMPLEMENTED** |
| 5 | Integrity and checksum verification | **IMPLEMENTED AND VERIFIED** |
| 6 | Voice-pack compatibility checks | **PARTIALLY IMPLEMENTED** — manifest id/version identity is checked; language/format compatibility is **not** (needs W3's compatibility metadata) |
| 7 | Safe staging | **IMPLEMENTED AND VERIFIED** |
| 8 | Atomic installation | **IMPLEMENTED AND VERIFIED** (rename swap, restore on failure) |
| 9 | Previous catalogue retention | **IMPLEMENTED AND VERIFIED** |
| 10 | Rollback | **IMPLEMENTED AND VERIFIED** |
| 11 | Installation status reporting | **IMPLEMENTED AND VERIFIED** (`state.json`, `status()`) |
| 12 | Recovery from interrupted downloads | **IMPLEMENTED AND VERIFIED** (staging removed on failure; `recover()` at every start) |
| 13 | Recovery from interrupted installation | **IMPLEMENTED AND VERIFIED** (`recover()` promotes `previous` when `current` is missing) |
| 14 | Offline operation on the last valid catalogue | **IMPLEMENTED AND VERIFIED** (local read; playback never fetches) |
| 15 | Safe switching between pack versions | **IMPLEMENTED AND VERIFIED** (install v2 keeps v1; rollback returns to it) |

### 3.1 Distribution API — NOT IMPLEMENTED

The agent expects `GET <server>/packs/<packId>/bundle.json` and one URL per file. Nothing serves that today:

- the server routes belong to W3 (`/api/v1/voice-packs/...`), which is not implemented;
- entitlement ("this organisation may download these packs") must be server-side, and no such check exists
  yet — the agent's `AMSDP_VOICE_PACKS` list is a client-side hint, **not** an access control. This is the
  most important gap: assignment §W5 requires that one organisation cannot download another's private
  packs, and only the server can enforce that.

## 4. What is **not** verified

- No real HTTPS server, no CDN, no facility PC.
- No Windows service / scheduled-task wrapper and no installer — the agent is a CLI today.
- No bandwidth, resume-after-disconnect or disk-full behaviour (a partial download is discarded).
- No compatibility refusal of an incompatible pack (requirement 6).

## 5. Governance and skill compliance (`.clinerules` §6)

- **Domains (§4):** Deployment/infrastructure + multi-tenant data. Applied: no inbound exposure; tenant
  isolation left to the server where it belongs — and flagged as missing rather than faked; no credentials
  in code; no destructive filesystem operation outside the configured install root.
- **Skills:** none installed (§5) — none claimed; Node standard library only, no new dependency.
- **Non-negotiables (§3):** no secrets logged or exposed; the agent never writes outside its root; failures
  are recorded in `state.json` instead of being swallowed.
- **Evidence:** 10 named tests passing in this tree, plus the quoted command.

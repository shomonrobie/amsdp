# AMSDP Frontend Visual Quality Investigation

**Date:** 8 November 2026
**Status:** Root cause identified and fix applied (authorized correction)

---

## Root Cause

The M6 AppShell/UI component system was present in source and genuinely used in markup, but **its stylesheet was never loaded by the browser**. Next.js Pages Router only bundles global CSS when it is imported from `pages/_app.js`. No `_app.js` existed and nothing imported `frontend/styles/global.css`, so the production build contained **zero CSS files** (`.next/static/css/` was absent) and served HTML carried **no `<link rel="stylesheet">`**. HTTP 200 and successful compilation were misleading — they proved route wiring, not styling.

## Symptom → Cause Mapping (as reported)

| Reported symptom | Missing rule in `styles/global.css` |
|---|---|
| Default browser typography | `body { font-family:…; background:#f0f2f5; }` |
| Blue underlined nav links | `a { color:#1a5c7a; text-decoration:none; }` + `.app-sidebar a { display:block; … }` |
| Nav items running together | `.app-sidebar a { padding:0.6rem 1rem; }` |
| No layout/spacing | `.content/.header/.main` padding + box-shadow |
| Metrics in narrow vertical column | `.flex`, `.flex-wrap` on dashboard cards |
| No professional dashboard | `.card`, `.page-title`, `.badge` |

## Affected Files

- `frontend/pages/_app.js` — **missing** (root cause)
- `frontend/styles/global.css` — written, never imported
- All page/component classNames matched rules that never reached the browser

## Shared Components — Used but Unstyled

Verified JSX reuse of `AppShell`, `DataTable`, `Modal`, `ConfirmDialog`, `StatusBadge`, `Alert` across dashboard/queue/audit and wrapped pages. The only failure was the missing global stylesheet import; no component redesign was needed.

## Required Correction

1. Create `frontend/pages/_app.js` importing `../styles/global.css`.
2. Rebuild and restart the frontend container.

---

## Fix Applied — Verification Evidence

**Changed file:** `frontend/pages/_app.js` (new, 5 lines) — imports `../styles/global.css` and renders `<Component {...pageProps} />`.

| Check | Result |
|-------|--------|
| Production build (`next build`, clean `.next`) | ✅ Success; `/_app` route emitted |
| Generated CSS assets | ✅ `.next/static/css/d4505cc7162f4e57.css` (3,355 bytes) |
| Served dashboard HTML references CSS | ✅ `<link rel="stylesheet" href="/_next/static/css/d4505cc7162f4e57.css">` |
| CSS fetch status | ✅ HTTP 200 |
| Key rules present in served CSS | ✅ `.app-sidebar a` (nav spacing), `.flex-wrap` (metric row), `.header`, `.card`, `@media` (responsive), `text-decoration:none` (no underlined links) |
| Stylesheet reference on all pages | ✅ `/`, `/dashboard`, `/queue`, `/audit`, `/patients`, `/appointments`, `/doctors`, `/schedules`, `/staff` → each `css-refs=1` |
| CSS asset inside built image | ✅ `IN_IMAGE_OK` (`/app/.next/static/css/d4505cc7162f4e57.css`) |
| Login behavior preserved | ✅ `admin` login returns token |

**Browser note:** this environment has no browser automation/screenshot capability; verification was performed at the served-HTML, build-output, and CSS-asset levels, which conclusively demonstrates the stylesheet now reaches the client. Final visual confirmation (AppShell, sidebar spacing, dashboard metric rows, bn/en styling) should be done in a real browser at `http://localhost:3100/dashboard` after logging in.
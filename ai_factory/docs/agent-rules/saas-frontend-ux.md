---
name: saas-frontend-ux
description: Frontend quality rules for CarbonTally's React application. Use for UI components, pages, layouts, tables, forms, dialogs, responsive behaviour, accessibility, design tokens, or any visual change. This platform is CRA (react-scripts) + React 18 + MUI/Emotion + react-router 7 with D21 semantic tokens — not Next.js and not Tailwind.
---

# Frontend UX — React (CRA), MUI, D21 Tokens

**Tier 2.** Defers to [carbontally-agent-governance.md](carbontally-agent-governance.md).
D19 (workbench) and D21 (design system) are frozen: a change to either needs PO review.

## 1. When to activate

Any change under `frontend/src/`, any new page/section, any table, form, dialog, navigation,
empty/loading/error state, or accessibility fix.

## 2. Never introduce a second design system

- Styling: existing `frontend/src/v3/tokens.css` variables + MUI/Emotion. **No Tailwind, no
  `tailwind.config.js`, no per-page one-off visual language.**
- Components: use the existing component tree (`components/`, `v3/{customer,ops,pe,consultant,admin,evidence,messaging,portal,reports}`). Do not scaffold `app/(routes)`, `page.tsx` or `next/image` — this is not Next.js.

## 3. What every operational screen must answer

1. Where am I? 2. Which organisation/client/entity am I working on? 3. What needs attention?
4. What can I do? 5. What happened? 6. What happens next? 7. How do I go back?

If a user must infer these from raw UUIDs, status codes or logs, the screen is wrong.

## 4. Business state over implementation detail

- Prefer `2,661.55 kg CO₂e` to `240 KB`; `Awaiting customer approval` to `status_code=7`;
  `Birmingham Head Office` to a facility UUID.
- Never display a raw UUID where a human-readable relationship exists.
- Percentages and statuses must be derived from persisted state — never an animation.

## 5. Tables and queues

- Large operational tables need pagination, sorting, filtering/search, record counts and
  meaningful columns. Tiny static tables do not need every control — judge by expected scale.
- A row must carry the business context needed to act on it: organisation, client, consultant,
  processing entity, batch, status, assigned party.
- Prefer **queue → open workspace → focused route → back to queue** over one enormous scroll.

## 6. States — all four, always

- **Loading** is not *working*. Show real persisted state (`queued`, `extracting`, `blocked`,
  `failed`, `retrying`) with timestamps where available.
- **Empty**: say what is empty, why it may be, and what to do next. No blank tables, no
  endless spinner.
- **Error**: a human sentence plus a recovery action. Never a raw exception, PostgREST message
  or `orgs.map is not a function`.
- **Unauthorised**: a clear refusal, not a blank screen.

## 7. Accessibility — WCAG 2.2 AA is the bar

Semantic HTML; no clickable `<div>`; keyboard reachable; visible focus; labels on every input;
semantic headings; alt text; AA contrast; dialogs trap and restore focus; tables use real
table semantics. Automated axe sweep is not a substitute for keyboard testing.

## 8. Responsive — eight viewports, not three

1920×1080, 1440×900, 1280×800, 1024×768, 768×1024, 430×932, 390×844, 375×812.

Watch for horizontal overflow, clipped tables, broken forms, unusable dialogs, broken
navigation. Mobile-first, but verify all eight.

## 9. Security in the UI

The UI is **never** the boundary. Hiding a button or disabling a control is presentation, not
authorisation; the server must enforce. Never log tokens or signed URLs to the console.

## 10. Anti-patterns

- **The Tailwind Import** — adding a utility framework to a MUI/token codebase.
- **The Monolith** — a 500-line page component. Split by responsibility; D19 workbench panes
  are the exception by design, not a licence for everything.
- **The Decorative Progress Bar** — progress that does not read persisted state.
- **The Guessable Empty State** — an empty white table with no explanation.
- **The UUID Table** — IDs where names belong.

## 11. Self-check

- [ ] Tokens/MUI only; no new styling system
- [ ] Works at 375px and 1920px; no horizontal overflow
- [ ] Keyboard-only path works; focus visible
- [ ] Loading/empty/error/denied states all present and truthful
- [ ] Business context shown, no raw UUIDs
- [ ] No authorisation logic relied on in the client

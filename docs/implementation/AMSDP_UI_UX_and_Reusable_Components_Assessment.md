# AMSDP UI/UX and Reusable Components Assessment

**Date:** 8 November 2026
**Status:** Read-only assessment (no code changed)
**Scope:** Current frontend state after M1–M5

---

## 1. Current Design System

| Item | Status | Notes |
|------|--------|-------|
| Framework | Next.js 14 + React 18 (JS, no TypeScript) | Per original stack; TS not yet adopted |
| Styling | `styles/global.css` CSS utility/component classes | No Tailwind/shadcn/ui (not in stack) |
| Color | `#1a5c7a` primary on `#f0f2f5` background | Consistent |
| Typography | Helvetica/Arial, small (0.85rem default) | Consistent |
| Styled components | `.btn*`, `.card`, `.error/.success/.loading/.empty`, `.modal*`, `.form-*`, `.page-title`, `.flex*`, `.mb-*`, `.badge*` | Usage varies per page |
| Layout | Fixed 200px sidebar + `marginLeft:200px`, hand-copied on every page | No shared layout component |

## 2. Shared Component Inventory (current)

There are **no shared React components**. Each page defines its own primitives inline. The de-facto "shared" layer is the `global.css` class set.

| Page | File | Key duplicated code |
|------|------|---------------------|
| Login | `index.js` | `T()` helper, locale toggle |
| Dashboard | `dashboard.js` | Sidebar + header shell (reference shell) |
| Orgs | `orgs.js` | `L/T` dict, `usr()`, login guard, list+modal |
| Branches | `branches.js` | Same |
| Staff | `staff.js` | Same + role select |
| Patients | `patients.js` | Same + search + duplicate warning |
| Doctors | `doctors.js` | Same + branch checkboxes |
| Schedules | `schedules.js` | Same + slots table |
| Appointments | `appointments.js` | Same + status action buttons |
| Queue | `queue.js` | Same + reorder actions + two modals |

## 3. Page-Specific Duplicated Components

| Duplicated concern | # copies | Recommended shared component |
|--------------------|---------|-------------------------------|
| `L={bn,en}` + `T(k)` | 10 | `lib/i18n.js` — locale dict + `t()` |
| `usr()` / `tok()` / auth header | 8 | `lib/auth.js` — `useAuth()` + `apiFetch()` |
| Login-required guard block | 8 | `RequireLogin` wrapper |
| Sidebar+header shell | 1 full (dashboard); 9 rely on fixed left margin | `AppShell` layout |
| List loading/empty/error/table | 8 | `DataTable` |
| Modal + header + form actions | 8 | `Modal` / `FormDialog` |
| Status badge | 6 | `StatusBadge` |
| Locale toggle | 8 | part of `AppShell` header |
| Success/error alerts | 6 | `Alert` |
| Confirm-with-reason dialog | 2 | `ConfirmDialog` |
## 4. UI/UX Consistency

- **Good:** consistent primary color, table styling, button styles, cards, and Bangla/English toggle presence on all pages.
- **Inconsistent:**
  - Mixed inline styles vs CSS classes (dashboard login block, queue table widths).
  - Action-button patterns differ between queue and appointments.
  - **Sidebar only exists in dashboard.js.** Sub-pages render content with a 200px left margin but *no sidebar*, so users cannot navigate away from a sub-page without editing the URL. This is the largest UX gap.
  - No breadcrumbs anywhere.
  - Branch/org context indicator present only on dashboard header.

## 5. Responsive Design

- Desktop: acceptable.
- **Mobile/tablet: not addressed** — fixed sidebar, no collapsible drawer, tables lack horizontal-scroll wrapper, forms not mobile-optimized. Blueprint's mobile-first requirement unmet.

## 6. Accessibility

- No ARIA attributes, no modal focus management/trap, no `aria-live` alerts, no form-error announcement.
- Color-only status indication lacks accompanying text alternatives.
- Native `<label>` and real `<button>` usage is good.
- No automated a11y testing.

## 7. Bangla/English Consistency

- All pages have `L.bn`/`L.en` and a toggle.
- **Inconsistencies:** locale is `sessionStorage`-only; several strings remain English in modals ("Policy", "Loading", "Select...", "Cancel", "Save", "Required"); dates/numbers not localized via `Intl`; default locale differs between login (`bn`) and identity defaults (`en`).

## 8. Available Cline Skills and Project Instructions

- **Project instructions:** `.clinerules` (repo root) is the only governance file: LLM routing (local `qwen2.5-coder:1.5b` for simple/isolated edits; Frontier escalation for multi-file/complex work), write-code-only boundary, task triage (≤2 files on local model), no destructive git, no secrets.
- **Tools available to the agent:** repository read/search, web fetch, shell, editor, memory tools — used across M1–M5.
- **No skill-library directory exists** in the repo (searched; none found — no `.cline/skills` or plugin dirs).

## 9. Evidence of Which Skills Were Actually Used

- M1–M5 completed by the coding agent directly (multi-file frontend+backend), consistent with Frontier-escalation behavior in `.clinerules`.
- **No evidence** the local `qwen2.5-coder:1.5b` model was invoked during completed milestones (all work is in the tree; no local-model traces). Documented-but-unused routing option.
- Editor, shell, search, read were the workhorses; memory tools unused for project knowledge.

## 10. Recommended Shared Component Improvements (M6-ready)

1. **`components/AppShell.js`** — role-aware sidebar (from dashboard), header with user/org/branch context + locale toggle + logout, breadcrumbs, responsive drawer. Wrap all pages.
2. **`lib/i18n.js`** — central dictionary registry; complete Bangla/English; move stray English strings in.
3. **`lib/auth.js`** — `useAuth()`, `apiFetch()`, `RequireLogin`, `Permission` wrappers.
4. **`components/ui/*`** — `DataTable`, `Modal`, `ConfirmDialog` (optional reason), `StatusBadge`, `Alert`, `FormDialog`, `Field`.
5. **Styles** — absorb inline styles into classes; add `.table-wrap` (horizontal scroll) and responsive `@media` rules.
6. **Accessibility pass** — modal focus trap, `role=dialog`, aria labels, `aria-live` alerts, keyboard-operable reorder controls.
7. **Localization** — persist locale preference; adopt `Intl.DateTimeFormat` for dates/times/counts.

## 11. Outstanding Recommendations (parked for M6)

- Role-aware dashboard surfaces (receptionist vs doctor) on the shared shell.
- Reusable statistic/period-filter components for scheduled vs walk-in vs checked-in counts.
- No fabricated metrics — every dashboard number must come from a real API.
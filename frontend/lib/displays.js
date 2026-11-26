/* Display administration policy — MP-39 / MD-11.
 *
 * The rules that decide *what may be saved* and *what a screen's URL is* live
 * here rather than inside the page, for the same reason `lib/staff-policy.js`
 * exists: the page stays a view, and a rule can be tested without a DOM.
 *
 * The server is still the boundary.  `backend/queuing/displays.py` re-validates
 * every field, re-checks `queue.display.manage`, and refuses a foreign branch,
 * room, department or doctor with a non-disclosing 404 or a 422.  These helpers
 * only spare the operator a round trip and keep the form's messages in the
 * screen's own language.
 */

export const SCOPE_TYPES = ['branch', 'doctors', 'department', 'room'];
export const LANGUAGES = ['bn', 'en'];
export const STATUSES = ['active', 'disabled'];

export const SCOPE_LABEL_KEYS = {
  branch: 'dispScopeBranch',
  doctors: 'dispScopeDoctors',
  department: 'dispScopeDepartment',
  room: 'dispScopeRoom',
};

export const EMPTY_DISPLAY = {
  name: '', code: '', language: 'bn', scope_type: 'branch',
  department_id: '', room_id: '', doctor_ids: [], footer_text: '',
  show_room: true, show_estimated_wait: true, show_waiting_count: true,
  status: 'active',
};

/** Normalise a free-text code to the public handle the server will accept. */
export function normaliseCode(value) {
  return String(value || '').trim().toLowerCase();
}

/** `true` when *code* is a legal `?display=` handle (lower-case a-z 0-9 hyphen). */
export function codeLooksValid(value) {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(normaliseCode(value))
    && normaliseCode(value).length <= 40;
}

/**
 * Validate a draft before it is sent.  Returns `{ ok, error }` where *error* is
 * an **i18n key**, never an English sentence — the caller translates it.
 */
export function validateDisplayDraft(draft) {
  if (!draft) return { ok: false, error: 'fillRequired' };
  if (!String(draft.name || '').trim()) return { ok: false, error: 'nameRequired' };
  if (!codeLooksValid(draft.code)) return { ok: false, error: 'dispCodeHint' };
  if (LANGUAGES.indexOf(draft.language) < 0) return { ok: false, error: 'dispLanguage' };
  if (SCOPE_TYPES.indexOf(draft.scope_type) < 0) return { ok: false, error: 'dispScope' };
  if (draft.scope_type === 'department' && !draft.department_id) {
    return { ok: false, error: 'dispDepartmentRequired' };
  }
  if (draft.scope_type === 'room' && !draft.room_id) {
    return { ok: false, error: 'dispRoomRequired' };
  }
  if (draft.scope_type === 'doctors' && !(draft.doctor_ids || []).length) {
    return { ok: false, error: 'dispSelectDoctors' };
  }
  return { ok: true, error: '' };
}

/**
 * The body for `POST /api/v1/queue/displays`.
 *
 * `branch_id` is the branch the operator chose; it is not an authority claim —
 * the server resolves the organization from the token and refuses a branch that
 * is not the caller's.
 */
export function createPayload(draft, branchId) {
  const scope = draft.scope_type;
  return {
    branch_id: branchId,
    name: String(draft.name || '').trim(),
    code: normaliseCode(draft.code),
    language: draft.language,
    scope_type: scope,
    // A target that does not apply to the chosen scope is never sent: the server
    // would refuse it, and an empty string is not "no value" to a CHECK
    // constraint on a foreign key.
    department_id: scope === 'department' ? (draft.department_id || null) : null,
    room_id: scope === 'room' ? (draft.room_id || null) : null,
    doctor_ids: scope === 'doctors' ? (draft.doctor_ids || []) : [],
    footer_text: String(draft.footer_text || '').trim(),
    show_room: !!draft.show_room,
    show_estimated_wait: !!draft.show_estimated_wait,
    show_waiting_count: !!draft.show_waiting_count,
  };
}

/**
 * The body for `PATCH /api/v1/queue/displays/{id}` — only what changed.
 *
 * An unchanged field is omitted so the audit row is written for a real change
 * and a no-op save leaves no trace claiming otherwise.
 */
export function patchPayload(draft, original) {
  const fresh = createPayload(draft, (original || {}).branch_id || '');
  const before = original || {};
  const patch = {};
  for (const key of ['name', 'code', 'language', 'scope_type', 'department_id',
    'room_id', 'footer_text', 'status']) {
    const next = key === 'status' ? (draft.status || 'active') : fresh[key];
    const prev = key === 'status' ? (before.status || 'active') : (before[key] || '');
    if (String(next || '') !== String(prev || '')) patch[key] = next;
  }
  for (const key of ['show_room', 'show_estimated_wait', 'show_waiting_count']) {
    const next = !!draft[key];
    const prev = before[key] !== false;
    if (next !== prev) patch[key] = next;
  }
  if ((draft.doctor_ids || []).slice().sort().join(',')
    !== (before.doctor_ids || []).slice().sort().join(',')) {
    patch.doctor_ids = draft.doctor_ids || [];
  }
  return patch;
}

/** The address an operator copies onto the television. */
export function displayUrl(orgCode, branchCode, code) {
  const base = '/queue-display/' + encodeURIComponent(orgCode || '')
    + '/' + encodeURIComponent(branchCode || '');
  return code ? base + '?display=' + encodeURIComponent(normaliseCode(code)) : base;
}

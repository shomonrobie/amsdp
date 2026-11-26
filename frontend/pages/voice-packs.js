/* Voice-pack administration — MP-04 (Product Owner decision, PO-05 superseded).
 *
 * W3's operator surface. Before this page, publishing a voice pack meant
 * `curl`-ing eight endpoints in the right order and trusting that the order was
 * right. Here the lifecycle is visible, but **nothing is decided in the browser**:
 * every refusal still comes from `organization/voice_pack_policy.py`, and this
 * screen shows the server's answer unchanged.
 *
 * Three deliberate properties:
 *
 *  * **No fallback toggle.** The policy's fallback constant is `False`; there is
 *    no switch here that could pretend otherwise, and the page never calls the
 *    browser's speech API.
 *  * **No guessing at authority.** A button the policy would refuse is either
 *    not rendered (`actionsFor` filters on role and ownership) or rendered
 *    disabled with the reason the API would give (`403` vs `409`).
 *  * **No silent configuration loss.** `configPayload` omits untouched languages;
 *    only an explicit "inherit" selection sends `null`, because `null` means
 *    *clear the override* and a stray one would drop a facility's chosen voice.
 */
import React from 'react';
import AppShell from '../components/AppShell';
import {
  RequireLogin, PermissionDenied, ErrorAlert, SuccessAlert, LoadingState,
} from '../components/ui/Alert';
import Button from '../components/ui/Button';
import { Field } from '../components/ui/Field';
import { Input, Select } from '../components/ui/Input';
import { getUser, apiFetch, can } from '../lib/auth';
import { t } from '../lib/i18n';
import {
  ACTIONS, ACTION_LABELS, BUCKET_KEYS, FILTER_STATUSES, INHERIT, PACK_LANGUAGES,
  PLATFORM_ROLES, ROLLBACK_LANGUAGES, actionsFor, configPayload,
  configPayloadIsEmpty, groupPacks, hasOrgOverride, isManageable, isPlatformPack,
  mayReadLibrary, packLabel, refusalKey, roleOf, rollbackBody, selectablePacks,
  statusLabelKey,
} from '../lib/voice-pack-admin';

/** Turn a fetch failure into something an operator can act on. */
function failure(e) {
  const status = e && e.status;
  const body = e && e.body;
  const detail = typeof body === 'string' ? body
    : (body && (body.message || body.detail)) || (e && e.message) || '';
  const problems = body && body.problems;
  if (status === 403) return t('vpPlatformOnly');
  if (status === 404) return t('vpNotFound');
  const key = refusalKey(detail);
  if (key) return t(key);
  if (problems && problems.length) return problems.join('; ');
  return String(detail || t('saveFailed'));
}

function ActionButtons({ pack, user, busy, onRun }) {
  /* Availability has its own switch in the detail panel — it needs a target
     value (`available: true|false`), which a plain "run action" button cannot
     supply.  Offering it twice would also risk one button saying "release"
     while the other said "withhold". */
  const actions = actionsFor(pack, user).filter((a) => a.action !== 'availability');
  if (!actions.length) return null;
  return (
    <div className="flex flex-wrap gap-2" data-testid="vp-actions">
      {actions.map((a) => (
        <span key={a.action} className="flex flex-col gap-1">
          <Button variant="ghost" size="sm"
            data-testid={'vp-action-' + a.action}
            disabled={!a.allowed || busy === a.action}
            title={a.reason ? t(a.reason) : ''}
            onClick={() => onRun(pack, a.action)}>
            {t(ACTION_LABELS[a.action])}
          </Button>
          {!a.allowed && a.reason
            ? <span className="text-xs text-muted-foreground">{t(a.reason)}</span>
            : null}
        </span>
      ))}
    </div>
  );
}

export default function VoicePacks() {
  const user = getUser() || {};
  const mayRead = mayReadLibrary(user) && can('org.read');
  const isPlatformAdmin = PLATFORM_ROLES.indexOf(roleOf(user)) >= 0;

  const [tab, setTab] = React.useState('library');
  const [packs, setPacks] = React.useState([]);
  const [language, setLanguage] = React.useState('');
  const [status, setStatus] = React.useState('');
  const [selectedId, setSelectedId] = React.useState('');
  const [preview, setPreview] = React.useState(null);
  const [note, setNote] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const [busy, setBusy] = React.useState('');
  const [err, setErr] = React.useState('');
  const [notice, setNotice] = React.useState('');

  const loadPacks = React.useCallback(async () => {
    if (!mayRead) { setLoading(false); return; }
    setLoading(true);
    try {
      const qs = [];
      if (language) qs.push('language=' + encodeURIComponent(language));
      if (status) qs.push('status=' + encodeURIComponent(status));
      const data = await apiFetch('/api/v1/voice-packs'
        + (qs.length ? '?' + qs.join('&') : ''));
      setPacks((data && data.packs) || []);
      setErr('');
    } catch (e) {
      setErr(failure(e));
      setPacks([]);
    } finally {
      setLoading(false);
    }
  }, [mayRead, language, status]);

  React.useEffect(() => { loadPacks(); }, [loadPacks]);

  const selected = packs.find((p) => p.id === selectedId) || null;

  /* Preview is a read-only audition: it writes nothing and changes no status. */
  const openPreview = async (pack) => {
    setSelectedId(pack.id);
    setPreview(null);
    setErr('');
    setBusy('preview');
    try {
      setPreview(await apiFetch('/api/v1/voice-packs/'
        + encodeURIComponent(pack.id) + '/preview'));
    } catch (e) {
      setErr(failure(e));
    } finally {
      setBusy('');
    }
  };

  const runAction = async (pack, action) => {
    setBusy(action);
    setErr('');
    setNotice('');
    try {
      const opts = { method: 'POST' };
      if (action === 'availability') {
        /* The route takes an explicit target, not a toggle: send the value we
           want, never "whatever it is now". */
        opts.body = JSON.stringify({ available: !pack.available_to_organizations });
      } else if (ACTIONS[action] && ACTIONS[action].note) {
        opts.body = JSON.stringify({ note: note.trim() });
      }
      await apiFetch('/api/v1/voice-packs/' + encodeURIComponent(pack.id)
        + '/' + action, opts);
      setNotice(t('vpActionDone'));
      setNote('');
      await loadPacks();
      if (selectedId === pack.id) await openPreview(pack);
    } catch (e) {
      setErr(failure(e));
    } finally {
      setBusy('');
    }
  };

  if (!user.id) return null;

  return (
    <AppShell>
      <RequireLogin>
        {!mayRead
          ? <PermissionDenied msg={t('vpNoAccess')} />
          : (
            <div className="flex flex-col gap-4">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <h1 className="text-xl font-bold text-foreground" data-testid="vp-heading">
                    {t('vpTitle')}
                  </h1>
                  <p className="text-sm text-muted-foreground">{t('vpHint')}</p>
                </div>
                <div className="flex gap-2" role="tablist">
                  <Button variant={tab === 'library' ? 'primary' : 'ghost'} size="sm"
                    data-testid="vp-tab-library" onClick={() => setTab('library')}>
                    {t('vpLibrary')}
                  </Button>
                  <Button variant={tab === 'config' ? 'primary' : 'ghost'} size="sm"
                    data-testid="vp-tab-config" onClick={() => setTab('config')}>
                    {t('vpConfig')}
                  </Button>
                </div>
              </div>

              {err ? <ErrorAlert>{err}</ErrorAlert> : null}
              {notice ? <SuccessAlert>{notice}</SuccessAlert> : null}

              {tab === 'library'
                ? (
                  <div className="flex flex-col gap-3">
                    <LibraryPanel packs={packs} loading={loading} busy={busy}
                      language={language} status={status}
                      setLanguage={setLanguage} setStatus={setStatus}
                      user={user} onPreview={openPreview} />
                    <PackDetail selected={selected} preview={preview} note={note}
                      setNote={setNote} user={user} busy={busy} onRun={runAction} />
                  </div>
                )
                : <ConfigPanel user={user} orgId={user.organization_id || ''}
                    isPlatformAdmin={isPlatformAdmin} />}
            </div>
          )}
      </RequireLogin>
    </AppShell>
  );
}


function LibraryPanel(props) {
  const {
    packs, loading, busy, language, status, setLanguage, setStatus,
    selected, preview, note, setNote, user, onPreview, onRun,
  } = props;
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-end gap-2">
        <Field label={t('vpLanguage')}>
          <Select value={language} data-testid="vp-filter-language"
            onChange={(e) => setLanguage(e.target.value)}>
            <option value="">{t('vpAll')}</option>
            {PACK_LANGUAGES.map((l) => (
              <option key={l} value={l}>{l === 'bn' ? 'বাংলা' : 'English'}</option>
            ))}
          </Select>
        </Field>
        <Field label={t('vpStatus')}>
          <Select value={status} data-testid="vp-filter-status"
            onChange={(e) => setStatus(e.target.value)}>
            {FILTER_STATUSES.map((s) => (
              <option key={s || 'all'} value={s}>
                {s ? t(statusLabelKey(s)) : t('vpAll')}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      {loading
        ? <LoadingState msg={t('loading')} />
        : (packs.length === 0
          ? (
            <p className="text-sm text-muted-foreground" data-testid="vp-empty">
              {t('vpEmpty')}
            </p>
          )
          : (
            <div className="flex flex-col gap-4" data-testid="vp-list">
              {groupPacks(packs).map((group) => (
                <section key={group.key} data-testid={'vp-group-' + group.key}>
                  <h2 className="text-sm font-semibold text-foreground">
                    {t(BUCKET_KEYS[group.key])}
                  </h2>
                  <ul className="mt-1 flex flex-col gap-2">
                    {group.items.map((pack) => (
                      <li key={pack.id}
                        className="rounded border border-input bg-card p-3"
                        data-testid={'vp-row-' + pack.id}>
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div>
                            <div className="font-semibold text-foreground">
                              {packLabel(pack)}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {t(statusLabelKey(pack.status))}
                              {' · '}
                              {isPlatformPack(pack) ? t('vpScopePlatform') : t('vpScopeOrg')}
                              {' · '}
                              {pack.validation_status === 'pass'
                                ? t('vpValidated') : t('vpNotValidated')}
                              {isPlatformPack(pack) && pack.available_to_organizations
                                ? ' · ' + t('vpReleased') : null}
                            </div>
                          </div>
                          <Button variant="ghost" size="sm"
                            data-testid={'vp-preview-' + pack.id}
                            disabled={busy === 'preview'}
                            onClick={() => onPreview(pack)}>
                            {t('vpPreview')}
                          </Button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          ))}
    </div>
  );
}


function PackDetail({ selected, preview, note, setNote, user, busy, onRun }) {
  if (!selected) return null;
  const noteAction = actionsFor(selected, user).find((a) => a.note);
  const noteKey = noteAction ? noteAction.note : '';
  return (
    <div className="rounded border border-input bg-card p-3" data-testid="vp-detail">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="font-semibold text-foreground">{packLabel(selected)}</div>
          <div className="text-xs text-muted-foreground">
            {t(statusLabelKey(selected.status))}{' · '}{selected.id}
          </div>
        </div>
        <ActionButtons pack={selected} user={user} busy={busy} onRun={onRun} />
      </div>

      {preview ? (
        <div className="mt-3 flex flex-col gap-2">
          <div className="text-sm">
            <strong>{t('vpSelectable')}:</strong>{' '}
            {preview.selectable ? t('vpYes') : t('vpNo')}
          </div>
          <div className="text-sm" data-testid="vp-problems">
            <strong>{t('vpProblems')}:</strong>{' '}
            {(preview.problems || []).length === 0
              ? t('vpNoProblems')
              : (
                <ul className="mt-1 list-disc pl-5">
                  {(preview.problems || []).map((p) => <li key={p}>{p}</li>)}
                </ul>
              )}
          </div>
          {preview.descriptor ? (
            <div className="text-xs text-muted-foreground">
              {t('vpManifest')}:{' '}
              <code data-testid="vp-descriptor">
                {preview.descriptor.language} v{preview.descriptor.version}
                {' · '}{preview.descriptor.scope}
                {' · '}{(preview.descriptor.assets || []).length} {t('vpAssets')}
              </code>
            </div>
          ) : null}
        </div>
      ) : (busy === 'preview' ? <LoadingState msg={t('loading')} /> : null)}

      {noteKey ? (
        <Field label={t(noteKey)} hint={t('vpNoteHint')}>
          <Input value={note} data-testid="vp-note"
            onChange={(e) => setNote(e.target.value)} />
        </Field>
      ) : null}

      {selected.status === 'published' && isPlatformPack(selected)
        && isManageable(selected, user) ? (
        <div className="mt-2 flex items-center gap-2">
          <Button variant="ghost" size="sm" data-testid="vp-availability"
            disabled={busy === 'availability'}
            onClick={() => onRun(selected, 'availability')}>
            {selected.available_to_organizations ? t('vpWithhold') : t('vpRelease')}
          </Button>
          <span className="text-xs text-muted-foreground">
            {selected.available_to_organizations ? t('vpReleased') : t('vpWithheld')}
          </span>
        </div>
      ) : null}
    </div>
  );
}


/* Configuration: what is *in force* for this facility, and how to change it.
 *
 * The precedence (organisation override -> platform default -> nothing) is
 * resolved by the server and shown here as `resolved`; the page never recomputes
 * it, so the screen cannot promise a voice the runtime would not use.
 */
function ConfigPanel({ user, orgId, isPlatformAdmin }) {
  const writable = can('org.manage');
  const [scope, setScope] = React.useState('organization');
  const [view, setView] = React.useState(null);
  const [draft, setDraft] = React.useState(null);
  const [base, setBase] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState('');
  const [notice, setNotice] = React.useState('');

  const url = scope === 'platform'
    ? '/api/v1/platform/announcement-config'
    : '/api/v1/orgs/' + encodeURIComponent(orgId) + '/announcement-config';

  const seed = React.useCallback((data) => {
    const stored = scope === 'platform'
      ? (data.voice_packs || {})
      : ((data.organization && data.organization.voice_packs) || {});
    const lang = scope === 'platform'
      ? (data.language || '')
      : ((data.organization && data.organization.language) || '');
    return { language: lang, bn: stored.bn || '', en: stored.en || '' };
  }, [scope]);

  const load = React.useCallback(async () => {
    if (scope === 'organization' && !orgId) { setLoading(false); return; }
    setLoading(true);
    setErr('');
    try {
      const data = await apiFetch(url);
      setView(data);
      const next = seed(data);
      setDraft(next);
      setBase(next);
    } catch (e) {
      setErr(failure(e));
      setView(null);
      setDraft(null);
    } finally {
      setLoading(false);
    }
  }, [url, scope, orgId, seed]);

  React.useEffect(() => { load(); }, [load]);

  const set = (key, value) => setDraft((cur) => (cur ? { ...cur, [key]: value } : cur));

  const optionsFor = (lang) => {
    const rows = (view && view.available_packs) || [];
    if (scope === 'platform') return selectablePacks(rows, user, lang);
    /* The organisation view already answers `selectable` per pack; a released
       platform pack is included only when the server says it may be chosen. */
    return rows.filter((r) => r.language === lang && r.selectable === true);
  };

  const save = async () => {
    if (!draft || !base) return;
    const packs = {};
    PACK_LANGUAGES.forEach((l) => {
      if (draft[l] !== base[l]) packs[l] = draft[l] === '' ? INHERIT : draft[l];
    });
    const payload = configPayload({
      language: draft.language !== base.language ? draft.language : '',
      voice_packs: packs,
    });
    if (configPayloadIsEmpty(payload)) {
      setNotice(t('vpNothingChanged'));
      return;
    }
    setBusy(true);
    setErr('');
    setNotice('');
    try {
      await apiFetch(url, { method: 'PUT', body: JSON.stringify(payload) });
      setNotice(t('vpSaved'));
      await load();
    } catch (e) {
      setErr(failure(e));
    } finally {
      setBusy(false);
    }
  };

  /* Rollback restores the previous *published* version for one language.  The
     server chooses the target (`policy.rollback_target`); the screen only names
     the language, so it can never pick a draft or another tenant's pack.  A 409
     ("no earlier published … pack is available") is shown verbatim. */
  const rollback = async (lang) => {
    setBusy(true);
    setErr('');
    setNotice('');
    try {
      await apiFetch(url + '/rollback',
        { method: 'POST', body: JSON.stringify(rollbackBody(lang)) });
      setNotice(t('vpRolledBack'));
      await load();
    } catch (e) {
      setErr(failure(e));
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingState msg={t('loading')} />;
  if (!view || !draft) return err ? <ErrorAlert>{err}</ErrorAlert> : null;

  const resolved = view.resolved || {};
  /* The platform view sends `inherited`; the organisation view sends only the
     override block, so "inheriting" is the absence of any override. */
  const inherited = scope === 'platform'
    ? !!view.inherited
    : !hasOrgOverride(view.organization);
  const warnings = resolved.warnings || [];


  return (
    <div className="flex flex-col gap-3" data-testid="vp-config">
      {isPlatformAdmin ? (
        <div className="flex gap-2">
          <Button variant={scope === 'organization' ? 'primary' : 'ghost'} size="sm"
            data-testid="vp-scope-org" onClick={() => setScope('organization')}>
            {t('vpScopeOrg')}
          </Button>
          <Button variant={scope === 'platform' ? 'primary' : 'ghost'} size="sm"
            data-testid="vp-scope-platform" onClick={() => setScope('platform')}>
            {t('vpPlatformDefaults')}
          </Button>
        </div>
      ) : null}

      {err ? <ErrorAlert>{err}</ErrorAlert> : null}
      {notice ? <SuccessAlert>{notice}</SuccessAlert> : null}
      {!writable ? <p className="text-sm text-muted-foreground">{t('vpReadOnly')}</p> : null}

      <div className="text-sm">
        <strong>{t('vpInForce')}:</strong>{' '}
        {resolved.language ? (resolved.language === 'bn' ? 'বাংলা' : 'English') : t('vpNone')}
        {PACK_LANGUAGES.map((l) => (
          <span key={l} className="ml-2 text-xs text-muted-foreground">
            {l}: {(resolved.voice_packs || {})[l] || t('vpNone')}
            {' ('}{(resolved.sources || {})[l] || 'none'}{')'}
          </span>
        ))}
        {inherited ? <span className="ml-2 text-xs">{t('vpInherited')}</span> : null}
      </div>

      {warnings.length ? (
        <ul className="text-xs text-muted-foreground" data-testid="vp-warnings">
          {warnings.map((w) => (
            <li key={w.language + ':' + w.source + ':' + w.reason}>
              {w.language} · {w.source} · {w.reason}
            </li>
          ))}
        </ul>
      ) : null}

      <div className="flex flex-wrap items-end gap-2">
        <Field label={t('vpLanguage')}>
          <Select value={draft.language} data-testid="vp-config-language"
            disabled={!writable} onChange={(e) => set('language', e.target.value)}>
            {PACK_LANGUAGES.map((l) => (
              <option key={l} value={l}>{l === 'bn' ? 'বাংলা' : 'English'}</option>
            ))}
          </Select>
        </Field>
        {PACK_LANGUAGES.map((l) => (
          <Field key={l} label={l === 'bn' ? 'বাংলা' : 'English'}>
            <Select value={draft[l]} data-testid={'vp-config-pack-' + l}
              disabled={!writable} onChange={(e) => set(l, e.target.value)}>
              <option value={INHERIT}>{t('vpInherit')}</option>
              {optionsFor(l).map((p) => (
                <option key={p.id} value={p.id}>
                  {(p.voice_name || p.id) + ' v' + (p.version || 1)}
                </option>
              ))}
            </Select>
          </Field>
        ))}
        <Button data-testid="vp-save-config" disabled={!writable || busy} onClick={save}>
          {busy ? t('saving') : t('save')}
        </Button>
      </div>

      {scope === 'organization' ? (
        <div className="flex flex-col gap-1" data-testid="vp-rollback">
          <span className="text-sm">{t('vpRollbackTitle')}</span>
          <div className="flex flex-wrap gap-2">
            {ROLLBACK_LANGUAGES.map((l) => (
              <Button key={l} variant="ghost" size="sm"
                data-testid={'vp-rollback-' + l}
                disabled={!writable || busy}
                onClick={() => rollback(l)}>
                {t('vpRollback') + ' · ' + (l === 'bn' ? 'বাংলা' : 'English')}
              </Button>
            ))}
          </div>
          <span className="text-xs text-muted-foreground">{t('vpRollbackHint')}</span>
        </div>
      ) : null}

      <p className="text-xs text-muted-foreground">{t('vpConfigHint')}</p>
    </div>
  );
}


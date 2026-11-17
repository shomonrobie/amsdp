export async function getServerSideProps() { return { props: {} }; }
/* Doctor Management — directory, profile, chambers and BMDC verification.
 * AMSDP-FACILITY-DOCTOR-01 / AMSDP-FRONTEND-UX-DEMO-01.
 *
 * The page is a directory first: every doctor is reachable by name, mobile or
 * BMDC number, and the record shows the mobile in the canonical `01XXXXXXXXX`
 * form the API stores, the specialities as structured links, every branch with
 * its chamber, the consultation fee and the verification state.
 *
 * Two presentations of the same rows live here: a card grid (scanning — "who is
 * on duty in this branch?") and a dense table (management).  Both are built from
 * the same data and the same actions, so nothing exists in one and not the other.
 *
 * All rules live elsewhere and are only *applied* here:
 *  * `lib/phone.js`    — mirrors `backend/common/phone.py`, so a malformed
 *                        number is refused before the request is sent;
 *  * `lib/facility.js` — chamber labels, BMDC labels and the permitted
 *                        verification transitions;
 *  * `lib/status.js`   — one status vocabulary, so a retired doctor reads the
 *                        same here as on every other screen;
 *  * `lib/auth.js`     — `can()` mirrors `backend/common/permissions.py`.
 * The server still decides; the UI never offers what the API would refuse, and a
 * refused call is shown with the API's own message.
 *
 * Presentational sub-components are declared at *module* scope on purpose: a
 * component created inside `Doctors()` is a new type on every render, so React
 * unmounts and remounts it — which is how focus used to be pulled out of the
 * very inputs a receptionist was typing into.
 */
import React from 'react';
import { LayoutGrid, List, Pencil, ShieldCheck, UserPlus, UserRound } from 'lucide-react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
import Dialog from '../components/ui/Dialog';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import StatusBadge from '../components/ui/StatusBadge';
import EmptyState from '../components/ui/EmptyState';
import PageHeader from '../components/ui/PageHeader';
import Toolbar, { Filter } from '../components/ui/Toolbar';
import SearchInput from '../components/ui/SearchInput';
import { Field, FormRow } from '../components/ui/Field';
import { Input, Select } from '../components/ui/Input';
import DoctorAvatar from '../components/shared/DoctorAvatar';
import BranchSelect from '../components/shared/BranchSelect';
import { getUser, apiFetch, can } from '../lib/auth';
import { t, getLocale } from '../lib/i18n';
import { validateMobile, formatMobile } from '../lib/phone';
import { money } from '../lib/utils';
import {
  bmdcLabel, bmdcTransitions, specialityName, roomOptions, chamberText, activeOnly,
} from '../lib/facility';

/** A blank profile form; `branches` holds one entry per assigned branch. */
const EMPTY_FORM = {
  id: '', name: '', mobile: '', registration_number: '', qualification: '',
  consultation_fee: '', specialty_ids: [], branches: [], photoSrc: '',
};

const EMPTY_FILTERS = { q: '', branch_id: '', specialty_id: '', status: '' };

/** BMDC state → badge tone.  `pending_verification` is amber, never green. */
const BMDC_TONE = {
  verified: 'success',
  rejected: 'danger',
  pending_verification: 'warning',
  unverified: 'warning',
};

/** Chamber of one assignment, preferring the loaded facility over the snapshot. */
function assignmentChamber(assignment, rooms) {
  const room = assignment.room_id
    ? (rooms || []).find((r) => r.id === assignment.room_id) : null;
  return room ? chamberText(room) : (assignment.room_name || '');
}

function BmdcBadge({ status, locale, size }) {
  return (
    <Badge tone={BMDC_TONE[status] || 'neutral'} size={size}>
      {bmdcLabel(status, locale)}
    </Badge>
  );
}

/** Specialities as chips; the overflow keeps a long list one line tall. */
function SpecialityChips({ specialties, locale, max = 3 }) {
  const list = specialties || [];
  if (!list.length) return <span className="text-muted-foreground">{t('unassigned')}</span>;
  const shown = list.slice(0, max);
  const extra = list.length - shown.length;
  return (
    <span className="flex flex-wrap items-center gap-1">
      {shown.map((s) => (
        <Badge key={s.id || s.name_en} tone="primary" size="sm">
          {specialityName(s, locale)}
        </Badge>
      ))}
      {extra > 0 && <Badge tone="outline" size="sm">+{extra}</Badge>}
    </span>
  );
}

/** Every active chamber of a doctor, one line each. */
function ChamberList({ doctor, roomsByBranch }) {
  const chambers = activeOnly(doctor.branches || []);
  if (!chambers.length) {
    return <span className="text-sm text-muted-foreground">{t('noChamber')}</span>;
  }
  return (
    <ul className="m-0 flex list-none flex-col gap-0.5 p-0">
      {chambers.map((a) => (
        <li key={a.id || a.branch_id} className="flex flex-wrap items-center gap-1 text-xs">
          <span className="font-semibold text-foreground">{a.branch_name}</span>
          <span aria-hidden="true" className="text-muted-foreground">·</span>
          <span className="text-muted-foreground">
            {assignmentChamber(a, roomsByBranch[a.branch_id]) || t('noChamber')}
          </span>
          {a.is_primary && <Badge tone="info" size="sm">{t('primary')}</Badge>}
        </li>
      ))}
    </ul>
  );
}

/** One doctor as a card — the scanning view. */
function DoctorCard({ doctor, roomsByBranch, locale, mayManage, onProfile, onEdit, onVerify }) {
  const inactive = (doctor.status || 'active') !== 'active';
  return (
    <article className="flex min-w-0 flex-col gap-2 rounded-lg border border-border bg-card p-3 shadow-sm">
      <div className="flex min-w-0 items-start gap-2.5">
        <DoctorAvatar name={doctor.name} size="lg" />
        <div className="min-w-0 flex-1">
          <h2 className="m-0 truncate text-lg font-bold leading-tight text-foreground">{doctor.name}</h2>
          <p className="m-0 truncate text-xs text-muted-foreground">
            {doctor.qualification || t('unassigned')}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-1">
            {inactive && <StatusBadge status="inactive" size="sm" />}
            <BmdcBadge status={doctor.bmdc_verification_status} locale={locale} size="sm" />
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-sm font-bold text-primary">{money(doctor.consultation_fee, locale)}</div>
          <div className="text-[0.62rem] uppercase tracking-wide text-muted-foreground">{t('fee')}</div>
        </div>
      </div>

      <dl className="m-0 grid grid-cols-1 gap-1.5 border-t border-border pt-2 text-xs">
        <div className="flex min-w-0 items-baseline gap-2">
          <dt className="w-16 shrink-0 font-semibold text-muted-foreground">{t('mobile')}</dt>
          <dd className="m-0 min-w-0 font-mono text-foreground">
            {formatMobile(doctor.mobile) || '—'}
          </dd>
        </div>
        <div className="flex min-w-0 items-baseline gap-2">
          <dt className="w-16 shrink-0 font-semibold text-muted-foreground">{t('specialities')}</dt>
          <dd className="m-0 min-w-0">
            <SpecialityChips specialties={doctor.specialties} locale={locale} />
          </dd>
        </div>
        <div className="flex min-w-0 items-baseline gap-2">
          <dt className="w-16 shrink-0 font-semibold text-muted-foreground">{t('chamber')}</dt>
          <dd className="m-0 min-w-0"><ChamberList doctor={doctor} roomsByBranch={roomsByBranch} /></dd>
        </div>
      </dl>

      <footer className="mt-auto flex flex-wrap items-center gap-1 border-t border-border pt-2">
        <Button size="sm" variant="outline" onClick={() => onProfile(doctor)}>
          <UserRound aria-hidden="true" size={13} />
          {t('profile')}
        </Button>
        {mayManage && (
          <Button size="sm" variant="ghost" onClick={() => onEdit(doctor)}>
            <Pencil aria-hidden="true" size={13} />
            {t('edit')}
          </Button>
        )}
        {mayManage && (
          <Button size="sm" variant="ghost" onClick={() => onVerify(doctor)}>
            <ShieldCheck aria-hidden="true" size={13} />
            {t('verify')}
          </Button>
        )}
      </footer>
    </article>
  );
}

/** The same doctor as a table row — the management view. */
function DoctorRow({ doctor, roomsByBranch, locale, mayManage, onProfile, onEdit, onVerify }) {
  const inactive = (doctor.status || 'active') !== 'active';
  return (
    <tr>
      <td className="px-2 py-2 align-top">
        <div className="flex min-w-0 items-center gap-2">
          <DoctorAvatar name={doctor.name} size="md" />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-1">
              <strong className="text-foreground">{doctor.name}</strong>
              {inactive && <StatusBadge status="inactive" size="sm" />}
            </div>
            <div className="truncate text-xs text-muted-foreground">
              {[doctor.qualification, doctor.registration_number].filter(Boolean).join(' · ') || '—'}
            </div>
          </div>
        </div>
      </td>
      <td className="px-2 py-2 align-top font-mono text-xs">
        {formatMobile(doctor.mobile) || '—'}
      </td>
      <td className="px-2 py-2 align-top">
        <SpecialityChips specialties={doctor.specialties} locale={locale} />
      </td>
      <td className="px-2 py-2 align-top">
        <ChamberList doctor={doctor} roomsByBranch={roomsByBranch} />
      </td>
      <td className="px-2 py-2 align-top text-sm font-semibold">
        {money(doctor.consultation_fee, locale)}
      </td>
      <td className="px-2 py-2 align-top">
        <BmdcBadge status={doctor.bmdc_verification_status} locale={locale} size="sm" />
      </td>
      <td className="px-2 py-2 align-top">
        <div className="flex flex-wrap items-center gap-1">
          <Button size="sm" variant="outline" onClick={() => onProfile(doctor)}>
            <UserRound aria-hidden="true" size={13} />
            {t('profile')}
          </Button>
          {mayManage && (
            <>
              <Button size="sm" variant="ghost" onClick={() => onEdit(doctor)}>
                <Pencil aria-hidden="true" size={13} />
                {t('edit')}
              </Button>
              <Button size="sm" variant="ghost" onClick={() => onVerify(doctor)}>
                <ShieldCheck aria-hidden="true" size={13} />
                {t('verify')}
              </Button>
            </>
          )}
        </div>
      </td>
    </tr>
  );
}

/** One labelled fact in the profile dialog. */
function ProfileRow({ label, children }) {
  return (
    <div className="flex flex-col gap-0.5 border-b border-border py-1.5 last:border-b-0 sm:flex-row sm:gap-3">
      <dt className="w-40 shrink-0 text-xs font-semibold text-muted-foreground">{label}</dt>
      <dd className="m-0 min-w-0 text-base text-foreground">{children}</dd>
    </div>
  );
}

function ProfileSection({ title, children }) {
  return (
    <section className="mt-3">
      <h3 className="m-0 mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h3>
      {children}
    </section>
  );
}

/** The read-only profile: identity, contact, professional facts, chambers. */
function DoctorProfile({ doctor, roomsByBranch, locale }) {
  const chambers = activeOnly(doctor.branches || []);
  return (
    <div>
      <div className="flex flex-wrap items-start gap-3 border-b border-border pb-3">
        <DoctorAvatar name={doctor.name} size="lg" />
        <div className="min-w-0 flex-1">
          <h2 className="m-0 text-xl font-bold leading-tight text-foreground">{doctor.name}</h2>
          <p className="m-0 text-sm text-muted-foreground">{doctor.qualification || '—'}</p>
          <div className="mt-1 flex flex-wrap items-center gap-1">
            <StatusBadge status={doctor.status || 'active'} />
            <BmdcBadge status={doctor.bmdc_verification_status} locale={locale} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-x-6 md:grid-cols-2">
        <ProfileSection title={t('contact')}>
          <dl className="m-0">
            <ProfileRow label={t('mobile')}>
              <a href={'tel:' + (doctor.mobile || '')} className="text-primary">
                {formatMobile(doctor.mobile) || '—'}
              </a>
            </ProfileRow>
            <ProfileRow label={t('registrationNumber')}>
              {doctor.registration_number || '—'}
            </ProfileRow>
          </dl>
        </ProfileSection>

        <ProfileSection title={t('professional')}>
          <dl className="m-0">
            <ProfileRow label={t('specialities')}>
              <SpecialityChips specialties={doctor.specialties} locale={locale} max={8} />
            </ProfileRow>
            <ProfileRow label={t('consultationFee')}>
              {money(doctor.consultation_fee, locale)}
            </ProfileRow>
            <ProfileRow label={t('bmdcStatus')}>
              {bmdcLabel(doctor.bmdc_verification_status, locale)}
            </ProfileRow>
          </dl>
        </ProfileSection>
      </div>

      <ProfileSection title={t('assignBranches') + ' (' + chambers.length + ')'}>
        {chambers.length === 0 ? (
          <EmptyState compact title={t('noChamber')} />
        ) : (
          <ul className="m-0 flex list-none flex-col gap-1.5 p-0">
            {chambers.map((a) => (
              <li
                key={a.id || a.branch_id}
                className="flex flex-wrap items-center justify-between gap-2 rounded border border-border bg-muted px-2 py-1.5"
              >
                <div className="flex min-w-0 flex-wrap items-center gap-1">
                  <strong className="text-base text-foreground">{a.branch_name}</strong>
                  <span aria-hidden="true" className="text-muted-foreground">·</span>
                  <span className="text-sm text-muted-foreground">
                    {assignmentChamber(a, roomsByBranch[a.branch_id]) || t('noChamber')}
                  </span>
                </div>
                {a.is_primary && <Badge tone="info" size="sm">{t('primary')}</Badge>}
              </li>
            ))}
          </ul>
        )}
      </ProfileSection>
    </div>
  );
}

/** Skeleton tiles while the first page of doctors is in flight. */
function LoadingCards() {
  return (
    <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3" aria-busy="true">
      <span className="sr-only" role="status">{t('loading')}</span>
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="h-40 animate-pulse rounded-lg border border-border bg-card" />
      ))}
    </div>
  );
}

export default function Doctors() {
  const user = getUser();
  const orgId = user.organization_id;
  const locale = getLocale();
  const mayManage = can('doctor.create') || can('doctor.manage');

  const [items, setItems] = React.useState(null);
  const [specialities, setSpecialities] = React.useState([]);
  const [branches, setBranches] = React.useState([]);
  const [roomsByBranch, setRoomsByBranch] = React.useState({});
  const [filters, setFilters] = React.useState(EMPTY_FILTERS);
  const [view, setView] = React.useState('cards');
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState('');
  const [notice, setNotice] = React.useState('');
  const [form, setForm] = React.useState(null);
  const [formErrors, setFormErrors] = React.useState({});
  const [profile, setProfile] = React.useState(null);
  const [verify, setVerify] = React.useState(null);
  const [saving, setSaving] = React.useState(false);

  const doctorsUrl = React.useCallback((f) => {
    const p = new URLSearchParams();
    if ((f.q || '').trim()) p.set('q', f.q.trim());
    if (f.branch_id) p.set('branch_id', f.branch_id);
    if (f.specialty_id) p.set('specialty_id', f.specialty_id);
    if (f.status) p.set('status', f.status);
    const qs = p.toString();
    return '/api/v1/doctors' + (qs ? '?' + qs : '');
  }, []);

  const loadDoctors = React.useCallback(async (f) => {
    setBusy(true);
    try {
      const data = await apiFetch(doctorsUrl(f));
      setItems(Array.isArray(data) ? data : (data.items || []));
      setErr('');
    } catch (e) {
      setErr(String(e.message || e));
      // A failed *refresh* keeps the last good rows on screen; a failed first
      // load has nothing to keep, so the list becomes an explicit empty state.
      setItems((cur) => (cur === null ? [] : cur));
    } finally {
      setBusy(false);
    }
  }, [doctorsUrl]);

  // One loader for typing and for the selects: a 250 ms debounce keeps a
  // receptionist's keystrokes from firing a request each.  It also performs the
  // first load, so there is no second "initial" fetch that could race this one.
  React.useEffect(() => {
    if (!user.id) return undefined;
    const timer = setTimeout(() => { loadDoctors(filters); }, 250);
    return () => clearTimeout(timer);
  }, [filters, user.id, loadDoctors]);

  React.useEffect(() => {
    if (!orgId) return;
    apiFetch('/api/v1/orgs/' + orgId + '/specialties')
      .then((d) => setSpecialities(activeOnly(Array.isArray(d) ? d : (d.items || []))))
      .catch(() => setSpecialities([]));
    apiFetch('/api/v1/orgs/' + orgId + '/branches')
      .then(async (d) => {
        const list = Array.isArray(d) ? d : (d.items || []);
        setBranches(list);
        // One facility read per branch: the branch API has no room list that
        // also carries the floor and department names a chamber label needs.
        const pairs = await Promise.all(list.map(async (b) => {
          try {
            const tree = await apiFetch('/api/v1/branches/' + b.id + '/facility');
            return [b.id, tree.rooms || []];
          } catch (e) { return [b.id, []]; }
        }));
        setRoomsByBranch(Object.fromEntries(pairs));
      })
      .catch(() => setBranches([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  if (!user.id) return null;

  const list = items || [];
  const activeCount = list.filter((d) => (d.status || 'active') === 'active').length;
  const verifiedCount = list.filter((d) => d.bmdc_verification_status === 'verified').length;
  const filtersDirty = Object.keys(EMPTY_FILTERS).some((k) => filters[k]);

  const setFilter = (key) => (value) => setFilters((cur) => ({ ...cur, [key]: value }));
  const clearFilters = () => setFilters({ ...EMPTY_FILTERS });

  // ---------------------------------------------------------------------
  // Form state
  // ---------------------------------------------------------------------

  const openCreate = () => {
    setErr('');
    setNotice('');
    setFormErrors({});
    setForm({ ...EMPTY_FORM });
  };

  const openEdit = async (doctor) => {
    setErr('');
    setNotice('');
    setFormErrors({});
    const assigned = activeOnly(doctor.branches || []).map((a) => ({
      assignment_id: a.id,
      branch_id: a.branch_id,
      branch_name: a.branch_name,
      room_id: a.room_id || '',
      is_primary: !!a.is_primary,
    }));
    setForm({
      id: doctor.id,
      name: doctor.name || '',
      mobile: doctor.mobile || '',
      registration_number: doctor.registration_number || '',
      qualification: doctor.qualification || '',
      consultation_fee: doctor.consultation_fee === null || doctor.consultation_fee === undefined
        ? '' : String(doctor.consultation_fee),
      specialty_ids: (doctor.specialty_ids || []).slice(),
      branches: assigned,
      photoSrc: '',
    });
    if (doctor.has_photo) {
      try {
        const p = await apiFetch('/api/v1/doctors/' + doctor.id + '/photo');
        setForm((cur) => (cur && cur.id === doctor.id
          ? { ...cur, photoSrc: 'data:' + (p.mime_type || 'image/jpeg') + ';base64,' + p.photo_base64 }
          : cur));
      } catch (e) { /* a photo that fails to load must not block the form */ }
    }
  };

  /** Update one form key and clear its error; focus stays where the user put it. */
  const field = (key) => (e) => {
    const value = e.target.value;
    setForm((cur) => (cur ? { ...cur, [key]: value } : cur));
    setFormErrors((cur) => (cur[key] ? { ...cur, [key]: '' } : cur));
  };

  const toggleSpecialty = (id) => setForm((cur) => {
    if (!cur) return cur;
    const has = cur.specialty_ids.includes(id);
    return {
      ...cur,
      specialty_ids: has
        ? cur.specialty_ids.filter((s) => s !== id)
        : cur.specialty_ids.concat(id),
    };
  });

  /** Add or remove a branch; the first branch added becomes the primary one. */
  const toggleBranch = (branchId) => setForm((cur) => {
    if (!cur) return cur;
    if (cur.branches.some((b) => b.branch_id === branchId)) {
      const left = cur.branches.filter((b) => b.branch_id !== branchId);
      // Same outcome as the server's promote_primary(): never leave the doctor
      // without a primary branch while one assignment remains.
      if (left.length && !left.some((b) => b.is_primary)) {
        left[0] = { ...left[0], is_primary: true };
      }
      return { ...cur, branches: left };
    }
    const branch = branches.find((b) => b.id === branchId);
    return {
      ...cur,
      branches: cur.branches.concat([{
        assignment_id: '',
        branch_id: branchId,
        branch_name: branch ? branch.name : '',
        room_id: '',
        is_primary: cur.branches.length === 0,
      }]),
    };
  });

  const setPrimary = (branchId) => setForm((cur) => (cur ? {
    ...cur,
    branches: cur.branches.map((b) => ({ ...b, is_primary: b.branch_id === branchId })),
  } : cur));

  const setRoom = (branchId, roomId) => setForm((cur) => (cur ? {
    ...cur,
    branches: cur.branches.map((b) => (b.branch_id === branchId ? { ...b, room_id: roomId } : b)),
  } : cur));

  // ---------------------------------------------------------------------
  // Persistence
  // ---------------------------------------------------------------------

  const save = async () => {
    if (!form) return;
    setErr('');
    setNotice('');
    const problems = {};
    if (!form.name.trim()) problems.name = t('nameRequired');
    const mobile = validateMobile(form.mobile, {
      empty: t('mobileRequired'), invalid: t('invalidMobile'),
    });
    if (!mobile.ok) problems.mobile = mobile.error;
    setFormErrors(problems);
    if (Object.keys(problems).length) return;

    const primary = form.branches.find((b) => b.is_primary);
    const payload = {
      name: form.name.trim(),
      mobile: mobile.value,
      registration_number: form.registration_number.trim(),
      qualification: form.qualification.trim(),
      consultation_fee: form.consultation_fee === '' ? null : Number(form.consultation_fee),
      specialty_ids: form.specialty_ids,
      branch_ids: form.branches.map((b) => b.branch_id),
      primary_branch_id: primary ? primary.branch_id : null,
    };
    setSaving(true);
    const editing = !!form.id;
    try {
      const saved = editing
        ? await apiFetch('/api/v1/doctors/' + form.id, {
          method: 'PATCH', body: JSON.stringify(payload),
        })
        : await apiFetch('/api/v1/doctors', {
          method: 'POST', body: JSON.stringify(payload),
        });
      // A chamber belongs to the *assignment*, not the doctor, so it is
      // reconciled per branch once the record exists.  An empty string clears
      // the chamber — the API's way of telling "clear" from "unchanged".
      await Promise.all((saved.branches || []).map(async (a) => {
        const want = form.branches.find((b) => b.branch_id === a.branch_id);
        if (!want) return;
        const desired = want.room_id || '';
        if ((a.room_id || '') === desired) return;
        await apiFetch('/api/v1/doctors/' + saved.id + '/branches/' + a.id, {
          method: 'PATCH',
          body: JSON.stringify({ room_id: desired }),
        });
      }));
      setForm(null);
      setNotice(editing ? t('savedOk') : t('createdOk'));
      await loadDoctors(filters);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setSaving(false);
    }
  };

  const openVerify = (doctor) => {
    setErr('');
    setNotice('');
    // `bmdcTransitions` returns the current state plus every permitted target;
    // the current state is dropped because re-recording it changes nothing.
    const options = bmdcTransitions(doctor.bmdc_verification_status)
      .filter((s) => s !== doctor.bmdc_verification_status);
    setVerify({
      doctor,
      options,
      status: options[0] || 'pending_verification',
      note: '',
    });
  };

  const submitVerify = async () => {
    if (!verify) return;
    setErr('');
    setSaving(true);
    try {
      await apiFetch('/api/v1/doctors/' + verify.doctor.id + '/verification', {
        method: 'POST',
        body: JSON.stringify({ status: verify.status, note: verify.note }),
      });
      setVerify(null);
      setNotice(t('savedOk'));
      await loadDoctors(filters);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setSaving(false);
    }
  };

  const uploadPhoto = (event) => {
    const input = event.target;
    const file = input.files && input.files[0];
    if (!file || !form || !form.id) return;
    setErr('');
    const reader = new FileReader();
    reader.onload = async () => {
      const dataUrl = String(reader.result || '');
      const comma = dataUrl.indexOf(',');
      if (comma < 0) return;
      const meta = dataUrl.slice(5, comma);            // image/png;base64
      const base64 = dataUrl.slice(comma + 1);
      try {
        await apiFetch('/api/v1/doctors/' + form.id + '/photo', {
          method: 'POST',
          body: JSON.stringify({
            photo_base64: base64,
            mime_type: meta.split(';')[0] || 'image/jpeg',
          }),
        });
        setForm((cur) => (cur ? { ...cur, photoSrc: dataUrl } : cur));
        setNotice(t('savedOk'));
        await loadDoctors(filters);
      } catch (e) {
        setErr(String(e.message || e));
      } finally {
        // Let the same file be picked again after a failure.
        input.value = '';
      }
    };
    reader.readAsDataURL(file);
  };

  const removePhoto = async () => {
    if (!form || !form.id) return;
    setErr('');
    try {
      await apiFetch('/api/v1/doctors/' + form.id + '/photo', { method: 'DELETE' });
      setForm((cur) => (cur ? { ...cur, photoSrc: '' } : cur));
      setNotice(t('savedOk'));
      await loadDoctors(filters);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  const viewToggle = (
    <div role="group" aria-label={t('view')} className="flex items-center gap-1">
      <Button
        size="sm"
        variant={view === 'cards' ? 'primary' : 'outline'}
        aria-pressed={view === 'cards'}
        onClick={() => setView('cards')}
      >
        <LayoutGrid aria-hidden="true" size={13} />
        {t('viewCards')}
      </Button>
      <Button
        size="sm"
        variant={view === 'table' ? 'primary' : 'outline'}
        aria-pressed={view === 'table'}
        onClick={() => setView('table')}
      >
        <List aria-hidden="true" size={13} />
        {t('viewTable')}
      </Button>
    </div>
  );

  return (
    <RequireLogin>
      <AppShell active="/doctors" breadcrumbs={[{ label: t('doctors') }]}>
        <PageHeader
          title={t('doctors')}
          subtitle={t('doctorDirectoryHint')}
          meta={(
            <>
              <span>{t('total')}: <strong>{items === null ? '…' : list.length}</strong></span>
              <span>{t('active')}: <strong>{activeCount}</strong></span>
              <span>{t('verified')}: <strong>{verifiedCount}</strong></span>
              {busy && <span role="status">{t('loading')}</span>}
            </>
          )}
          actions={mayManage ? (
            <Button variant="primary" onClick={openCreate}>
              <UserPlus aria-hidden="true" size={15} />
              {t('addDoctor')}
            </Button>
          ) : null}
        />

        <Toolbar label={t('searchDoctors')} end={viewToggle}>
          <SearchInput
            id="doctors-search"
            value={filters.q}
            onChange={setFilter('q')}
            placeholder={t('searchDoctors')}
            label={t('searchDoctors')}
            className="w-full sm:w-72"
          />
          <Filter label={t('branch')} htmlFor="doctors-branch">
            <BranchSelect
              id="doctors-branch"
              branches={branches}
              value={filters.branch_id}
              onChange={setFilter('branch_id')}
              allowAll
              allLabel={t('allBranches')}
              label={t('branch')}
              className="w-40"
            />
          </Filter>
          <Filter label={t('speciality')} htmlFor="doctors-speciality">
            <Select
              id="doctors-speciality"
              value={filters.specialty_id}
              onChange={(e) => setFilter('specialty_id')(e.target.value)}
              className="w-40"
            >
              <option value="">{t('allSpecialities')}</option>
              {specialities.map((s) => (
                <option key={s.id} value={s.id}>{specialityName(s, locale)}</option>
              ))}
            </Select>
          </Filter>
          <Filter label={t('status')} htmlFor="doctors-status">
            <Select
              id="doctors-status"
              value={filters.status}
              onChange={(e) => setFilter('status')(e.target.value)}
              className="w-32"
            >
              <option value="">{t('allStatus')}</option>
              <option value="active">{t('active')}</option>
              <option value="inactive">{t('inactive')}</option>
            </Select>
          </Filter>
          {filtersDirty && (
            <Button variant="ghost" size="sm" onClick={clearFilters} className="self-end">
              {t('clearFilters')}
            </Button>
          )}
        </Toolbar>

        {err && (
          <div
            role="alert"
            className="mb-2 rounded border border-destructive bg-[hsl(var(--danger-soft))] px-3 py-2 text-sm font-semibold text-destructive"
          >
            {err}
          </div>
        )}
        {notice && (
          <div
            role="status"
            className="mb-2 rounded border border-[hsl(var(--success)/0.35)] bg-success-soft px-3 py-2 text-sm font-semibold text-success"
          >
            {notice}
          </div>
        )}
        {!mayManage && <p className="mb-2 mt-0 text-sm text-muted-foreground">{t('manageOnly')}</p>}

        {items === null ? (
          <LoadingCards />
        ) : list.length === 0 ? (
          <EmptyState
            icon={UserRound}
            title={filtersDirty ? t('noResults') : t('empty')}
            hint={filtersDirty ? t('noResultsHint') : undefined}
            action={filtersDirty ? (
              <Button variant="outline" onClick={clearFilters}>{t('clearFilters')}</Button>
            ) : (mayManage ? (
              <Button variant="primary" onClick={openCreate}>{t('addDoctor')}</Button>
            ) : null)}
          />
        ) : view === 'cards' ? (
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
            {list.map((d) => (
              <DoctorCard
                key={d.id}
                doctor={d}
                roomsByBranch={roomsByBranch}
                locale={locale}
                mayManage={mayManage}
                onProfile={setProfile}
                onEdit={openEdit}
                onVerify={openVerify}
              />
            ))}
          </div>
        ) : (

          <div className="overflow-x-auto rounded border border-border bg-card shadow-sm">
            <table className="w-full border-collapse text-base">
              <thead>
                <tr className="border-b border-border bg-muted text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th scope="col" className="px-2 py-1.5 font-semibold">{t('doctor')}</th>
                  <th scope="col" className="px-2 py-1.5 font-semibold">{t('mobile')}</th>
                  <th scope="col" className="px-2 py-1.5 font-semibold">{t('specialities')}</th>
                  <th scope="col" className="px-2 py-1.5 font-semibold">{t('chamber')}</th>
                  <th scope="col" className="px-2 py-1.5 font-semibold">{t('fee')}</th>
                  <th scope="col" className="px-2 py-1.5 font-semibold">{t('bmdc')}</th>
                  <th scope="col" className="px-2 py-1.5 font-semibold">{t('actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {list.map((d) => (
                  <DoctorRow
                    key={d.id}
                    doctor={d}
                    roomsByBranch={roomsByBranch}
                    locale={locale}
                    mayManage={mayManage}
                    onProfile={setProfile}
                    onEdit={openEdit}
                    onVerify={openVerify}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}


        {profile && (
          <Dialog
            open
            onClose={() => setProfile(null)}
            title={t('doctorProfile')}
            description={profile.name}
            size="lg"
            footer={<Button variant="secondary" onClick={() => setProfile(null)}>{t('close')}</Button>}
          >
            <DoctorProfile doctor={profile} roomsByBranch={roomsByBranch} locale={locale} />
          </Dialog>
        )}

        {form && (
          <Dialog
            open
            onClose={() => setForm(null)}
            title={form.id ? t('edit') + ' — ' + form.name : t('addDoctor')}
            description={t('doctorDirectoryHint')}
            size="lg"
            footer={(
              <>
                <Button variant="outline" onClick={() => setForm(null)} disabled={saving}>
                  {t('cancel')}
                </Button>
                <Button variant="primary" onClick={save} loading={saving}>
                  {t('save')}
                </Button>
              </>
            )}
          >
            <FormRow>
              <Field label={t('name')} error={formErrors.name} required>
                <Input name="name" value={form.name} onChange={field('name')} autoComplete="off" />
              </Field>
              <Field label={t('mobile')} error={formErrors.mobile} hint={t('invalidMobile')} required>
                <Input
                  name="mobile"
                  value={form.mobile}
                  onChange={field('mobile')}
                  inputMode="tel"
                  placeholder="01XXXXXXXXX"
                  autoComplete="off"
                />
              </Field>
              <Field label={t('registrationNumber')}>
                <Input
                  name="registration_number"
                  value={form.registration_number}
                  onChange={field('registration_number')}
                  placeholder="A-12345"
                  autoComplete="off"
                />
              </Field>
              <Field label={t('qualification')}>
                <Input
                  name="qualification"
                  value={form.qualification}
                  onChange={field('qualification')}
                  placeholder="MBBS, FCPS"
                  autoComplete="off"
                />
              </Field>
              <Field label={t('consultationFee')} hint={locale === 'en' ? 'BDT (Tk)' : '৳ টাকা'}>
                <Input
                  name="consultation_fee"
                  type="number"
                  min="0"
                  value={form.consultation_fee}
                  onChange={field('consultation_fee')}
                />
              </Field>
            </FormRow>


            <fieldset className="mt-3 border-0 p-0">
              <legend className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {t('specialities')}
              </legend>
              {specialities.length === 0 ? (
                <p className="m-0 text-sm text-muted-foreground">{t('empty')}</p>
              ) : (
                <div className="flex flex-wrap gap-1">
                  {specialities.map((s) => {
                    const checked = form.specialty_ids.includes(s.id);
                    return (
                      <label
                        key={s.id}
                        className={
                          'inline-flex cursor-pointer items-center gap-1.5 rounded-pill border px-2 py-1 text-sm '
                          + (checked
                            ? 'border-primary bg-accent font-semibold text-primary'
                            : 'border-border bg-card text-foreground')
                        }
                      >
                        <input
                          type="checkbox"
                          className="h-3.5 w-3.5"
                          checked={checked}
                          onChange={() => toggleSpecialty(s.id)}
                        />
                        {specialityName(s, locale)}
                      </label>
                    );
                  })}
                </div>
              )}
            </fieldset>

            {form.id && (
              <div className="mt-3 flex flex-wrap items-center gap-3 rounded border border-border bg-muted px-2.5 py-2">
                <DoctorAvatar name={form.name} src={form.photoSrc} size="lg" />
                <div className="flex min-w-0 flex-col gap-1">
                  <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {t('photo')}
                  </span>
                  <div className="flex flex-wrap items-center gap-1">
                    <label className="inline-flex h-8 cursor-pointer items-center rounded-sm border border-border bg-card px-2.5 text-sm font-medium text-foreground hover:bg-accent">
                      {t('uploadPhoto')}
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        className="sr-only"
                        onChange={uploadPhoto}
                      />
                    </label>
                    {form.photoSrc && (
                      <Button size="sm" variant="ghost" onClick={removePhoto}>
                        {t('removePhoto')}
                      </Button>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground">{t('photoHint')}</span>
                </div>
              </div>
            )}


            <fieldset className="mt-3 w-full min-w-0 border-0 p-0">
              <legend className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {t('assignBranches')}
              </legend>
              {branches.length === 0 ? (
                <p className="m-0 text-sm text-muted-foreground">{t('facilityEmpty')}</p>
              ) : (
                <div className="flex flex-col gap-1.5">
                  {branches.map((b) => {
                    const row = form.branches.find((x) => x.branch_id === b.id);
                    const options = roomOptions(roomsByBranch[b.id] || []);
                    return (
                      <div
                        key={b.id}
                        className={
                          'rounded border px-2 py-1.5 '
                          + (row ? 'border-border bg-card' : 'border-dashed border-border bg-transparent')
                        }
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <label className="inline-flex cursor-pointer items-center gap-1.5 text-base">
                            <input
                              type="checkbox"
                              className="h-4 w-4"
                              checked={!!row}
                              onChange={() => toggleBranch(b.id)}
                            />
                            <strong className={row ? 'text-foreground' : 'text-muted-foreground'}>
                              {b.name}
                            </strong>
                          </label>
                          {row && (
                            <>
                              <label className="inline-flex cursor-pointer items-center gap-1 text-sm text-muted-foreground">
                                <input
                                  type="radio"
                                  name="primary-branch"
                                  checked={!!row.is_primary}
                                  onChange={() => setPrimary(b.id)}
                                />
                                {t('primaryBranch')}
                              </label>
                              <Select
                                aria-label={t('chamber')}
                                value={row.room_id}
                                onChange={(e) => setRoom(b.id, e.target.value)}
                                className="w-56"
                              >
                                <option value="">{t('noChamber')}</option>
                                {options.map((o) => (
                                  <option key={o.value} value={o.value}>{o.label}</option>
                                ))}
                              </Select>
                              {options.length === 0 && (
                                <span className="text-xs text-muted-foreground">{t('noRooms')}</span>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </fieldset>
          </Dialog>
        )}


        {verify && (
          <Dialog
            open
            onClose={() => setVerify(null)}
            title={t('verifyTitle')}
            description={verify.doctor.name}
            size="sm"
            footer={(
              <>
                <Button variant="outline" onClick={() => setVerify(null)} disabled={saving}>
                  {t('cancel')}
                </Button>
                <Button
                  variant="primary"
                  onClick={submitVerify}
                  loading={saving}
                  disabled={verify.options.length === 0}
                >
                  {t('save')}
                </Button>
              </>
            )}
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <strong className="text-base text-foreground">{verify.doctor.name}</strong>
              <BmdcBadge status={verify.doctor.bmdc_verification_status} locale={locale} />
            </div>
            <dl className="m-0">
              <ProfileRow label={t('registrationNumber')}>
                {verify.doctor.registration_number || '—'}
              </ProfileRow>
            </dl>
            {verify.options.length === 0 ? (
              <p className="mt-2 mb-0 text-sm text-muted-foreground">{t('bmdcStatus')}</p>
            ) : (
              <div className="mt-2 flex flex-col gap-3">
                <Field label={t('bmdcStatus')}>
                  <Select
                    value={verify.status}
                    onChange={(e) => setVerify({ ...verify, status: e.target.value })}
                  >
                    {verify.options.map((s) => (
                      <option key={s} value={s}>{bmdcLabel(s, locale)}</option>
                    ))}
                  </Select>
                </Field>
                <Field label={t('bmdcNote')}>
                  <Input
                    value={verify.note}
                    onChange={(e) => setVerify({ ...verify, note: e.target.value })}
                    placeholder={t('bmdcNote')}
                  />
                </Field>
              </div>
            )}
          </Dialog>
        )}
      </AppShell>
    </RequireLogin>
  );
}


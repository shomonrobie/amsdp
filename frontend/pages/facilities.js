export async function getServerSideProps() { return { props: {} }; }
/* Facilities — the branch tree, and the organization's speciality catalogue.
 * AMSDP-FACILITY-DOCTOR-01 / AMSDP-FRONTEND-UX-DEMO-01.
 *
 * One branch at a time, because the facility hierarchy *is* branch
 * configuration.  The tree comes from `GET /api/v1/branches/{id}/facility`
 * (floors, departments and rooms in one round trip) and is placed on the page
 * with `groupRoomsByFloor`, which keeps a room with no floor visible under an
 * "unassigned" heading instead of silently dropping it.
 *
 * Nothing here deletes: retiring sets `status="inactive"`, so a session or an
 * appointment that already names the room keeps resolving it.  Retired records
 * are hidden by default and can be revealed and restored, which is the only way
 * back from a mistaken retirement without touching the database.
 *
 * The page reads as the structure a person actually walks through —
 * তলা → বিভাগ → কক্ষ — so a room is always shown inside its floor, with its
 * department, its capacity and how many clinic sessions currently use it.
 * Every sub-component is declared at module scope: an inline component is a new
 * type on each render, which remounts its inputs and steals focus mid-typing.
 */
import React from 'react';
import {
  Building2, DoorOpen, Layers, Pencil, Plus, Undo2, Ban, Search,
} from 'lucide-react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
import Dialog from '../components/ui/Dialog';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import StatusBadge from '../components/ui/StatusBadge';
import EmptyState from '../components/ui/EmptyState';
import PageHeader from '../components/ui/PageHeader';
import Toolbar, { Filter } from '../components/ui/Toolbar';
import SearchInput from '../components/ui/SearchInput';
import { Field, FormRow } from '../components/ui/Field';
import { Input, Select, Textarea } from '../components/ui/Input';
import BranchSelect from '../components/shared/BranchSelect';
import { getUser, apiFetch, can, getActiveBranch } from '../lib/auth';
import { t, getLocale } from '../lib/i18n';
import {
  ROOM_TYPES, groupRoomsByFloor, roomUsage, facilityCounts,
  activeOnly, specialityName,
} from '../lib/facility';

const EMPTY_EDITOR = {
  kind: '', id: '', name: '', code: '', level: '', description: '',
  floor_id: '', department_id: '', room_type: 'consultation', capacity: '',
  name_en: '', name_bn: '', sort_order: '',
};

/** Copy a facility row into the editor shape. */
function toEditor(kind, row) {
  if (!row) return { ...EMPTY_EDITOR, kind };
  if (kind === 'specialty') {
    return {
      ...EMPTY_EDITOR,
      kind,
      id: row.id,
      code: row.code || '',
      name_en: row.name_en || '',
      name_bn: row.name_bn || '',
      sort_order: row.sort_order === null || row.sort_order === undefined ? '' : String(row.sort_order),
    };
  }
  return {
    ...EMPTY_EDITOR,
    kind,
    id: row.id,
    name: row.name || '',
    code: row.code || '',
    level: row.level === null || row.level === undefined ? '' : String(row.level),
    description: row.description || '',
    floor_id: row.floor_id || '',
    department_id: row.department_id || '',
    room_type: row.room_type || 'consultation',
    capacity: row.capacity === null || row.capacity === undefined ? '' : String(row.capacity),
  };
}

/** Add / edit title for the four editable resource kinds. */
function editorTitle(editor) {
  if (!editor) return '';
  const map = {
    floor: ['addFloor', 'editFloor'],
    department: ['addDepartment', 'editDepartment'],
    room: ['addRoom', 'editRoom'],
    specialty: ['add', 'edit'],
  };
  const pair = map[editor.kind] || map.room;
  return t(editor.id ? pair[1] : pair[0]);
}

/** A titled panel — the unit every section of this page is built from. */
function SectionCard({ icon: Icon, title, hint, actions, children, className }) {
  return (
    <section className={'rounded border border-border bg-card shadow-sm ' + (className || '')}>
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-3 py-2">
        <div className="flex min-w-0 items-center gap-2">
          {Icon && (
            <span aria-hidden="true" className="inline-flex h-7 w-7 items-center justify-center rounded-pill bg-secondary text-primary">
              <Icon size={15} />
            </span>
          )}
          <div className="min-w-0">
            <h2 className="m-0 text-base font-bold leading-tight text-foreground">{title}</h2>
            {hint && <p className="m-0 text-xs text-muted-foreground">{hint}</p>}
          </div>
        </div>
        {actions && <div className="flex flex-wrap items-center gap-1">{actions}</div>}
      </header>
      <div className="px-3 py-2">{children}</div>
    </section>
  );
}

/** Edit / retire / restore — the same three actions for every facility kind. */
function RowActions({ row, kind, mayManage, onEdit, onRetire, onRestore }) {
  if (!mayManage) return <span className="text-muted-foreground">—</span>;
  const retired = (row.status || 'active') !== 'active';
  return (
    <div className="flex flex-wrap items-center gap-1">
      <Button size="sm" variant="ghost" onClick={() => onEdit(kind, row)}>
        <Pencil aria-hidden="true" size={12} />
        {t('edit')}
      </Button>
      {retired ? (
        <Button size="sm" variant="ghost" onClick={() => onRestore(kind, row)}>
          <Undo2 aria-hidden="true" size={12} />
          {t('restore')}
        </Button>
      ) : (
        <Button size="sm" variant="ghost" onClick={() => onRetire(kind, row)}>
          <Ban aria-hidden="true" size={12} />
          {t('retire')}
        </Button>
      )}
    </div>
  );
}

/** One floor and the rooms that sit on it (a floor-less room is its own card). */
function FloorCard({ group, occupancy, mayManage, onEdit, onRetire, onRestore, onAddRoom }) {
  const floor = group.floor;
  const rooms = group.rooms;
  return (
    <SectionCard
      icon={floor ? Layers : DoorOpen}
      title={(floor ? floor.name : t('unassigned')) + ' — ' + rooms.length + ' ' + t('rooms')}
      hint={floor
        ? [floor.code, floor.level === null || floor.level === undefined
          ? '' : t('level') + ' ' + floor.level].filter(Boolean).join(' · ')
        : undefined}
      actions={(
        <>
          {floor && (
            <RowActions
              row={floor}
              kind="floor"
              mayManage={mayManage}
              onEdit={onEdit}
              onRetire={onRetire}
              onRestore={onRestore}
            />
          )}
          {mayManage && (
            <Button size="sm" variant="outline" onClick={() => onAddRoom(floor)}>
              <Plus aria-hidden="true" size={12} />
              {t('addRoomHere')}
            </Button>
          )}
        </>
      )}
    >
      {rooms.length === 0 ? (
        <EmptyState compact title={t('noRooms')} hint={t('facilityEmpty')} />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-base">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('room')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('department')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('roomType')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('capacity')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('usedBySessions')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('status')}</th>
                <th scope="col" className="py-1.5 font-semibold">{t('actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rooms.map((r) => (
                <tr key={r.id} className={(r.status || 'active') !== 'active' ? 'text-muted-foreground' : ''}>
                  <td className="py-1.5 pr-2 align-top">
                    <strong className="text-foreground">{r.name}</strong>
                    {r.code && <span className="ml-1 font-mono text-xs text-muted-foreground">{r.code}</span>}
                  </td>
                  <td className="py-1.5 pr-2 align-top">
                    {r.department_name || <span className="text-muted-foreground">{t('unassigned')}</span>}
                  </td>
                  <td className="py-1.5 pr-2 align-top text-sm">
                    <Badge tone="outline" size="sm">{r.room_type}</Badge>
                  </td>
                  <td className="py-1.5 pr-2 align-top">
                    {r.capacity === null || r.capacity === undefined
                      ? <span className="text-muted-foreground">—</span> : r.capacity}
                  </td>
                  <td className="py-1.5 pr-2 align-top">
                    {occupancy[r.id]
                      ? <Badge tone="info" size="sm">{occupancy[r.id]}</Badge>
                      : <span className="text-muted-foreground">0</span>}
                  </td>
                  <td className="py-1.5 pr-2 align-top">
                    <StatusBadge status={r.status || 'active'} size="sm" />
                  </td>
                  <td className="py-1.5 align-top">
                    <RowActions
                      row={r}
                      kind="room"
                      mayManage={mayManage}
                      onEdit={onEdit}
                      onRetire={onRetire}
                      onRestore={onRestore}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionCard>
  );
}

/** Departments — cross-cutting, so they are listed flat and counted by rooms. */
function DepartmentTable({ departments, rooms, mayManage, onAdd, onEdit, onRetire, onRestore }) {
  const roomCount = (id) => (rooms || []).filter((r) => (r.department_id || '') === id).length;
  return (
    <SectionCard
      icon={Building2}
      title={t('departments')}
      hint={departments.length ? departments.length + ' ' + t('departments') : undefined}
      actions={mayManage && (
        <Button size="sm" variant="outline" onClick={onAdd}>
          <Plus aria-hidden="true" size={12} />
          {t('addDepartment')}
        </Button>
      )}
    >
      {departments.length === 0 ? (
        <EmptyState compact title={t('facilityEmpty')} hint={t('structureHint')} />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-base">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('name')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('code')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('rooms')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('status')}</th>
                <th scope="col" className="py-1.5 font-semibold">{t('actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {departments.map((d) => (
                <tr key={d.id}>
                  <td className="py-1.5 pr-2 align-top font-semibold text-foreground">{d.name}</td>
                  <td className="py-1.5 pr-2 align-top font-mono text-sm text-muted-foreground">{d.code || '—'}</td>
                  <td className="py-1.5 pr-2 align-top">{roomCount(d.id)}</td>
                  <td className="py-1.5 pr-2 align-top"><StatusBadge status={d.status || 'active'} size="sm" /></td>
                  <td className="py-1.5 align-top">
                    <RowActions
                      row={d}
                      kind="department"
                      mayManage={mayManage}
                      onEdit={onEdit}
                      onRetire={onRetire}
                      onRestore={onRestore}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionCard>
  );
}
/** The organization-wide speciality catalogue (one list, both languages). */
function CatalogueTable({
  rows, query, onQuery, mayManage, onAdd, onEdit, onRetire, onRestore, locale,
}) {
  const needle = query.trim().toLowerCase();
  const shown = needle
    ? rows.filter((s) => [s.name_en, s.name_bn, s.code]
      .some((v) => String(v || '').toLowerCase().includes(needle)))
    : rows;
  return (
    <SectionCard
      title={t('catalogue')}
      hint={rows.length ? rows.length + ' ' + t('specialities') : undefined}
      actions={(
        <>
          <SearchInput
            id="facility-speciality-search"
            value={query}
            onChange={(v) => onQuery(v || '')}
            placeholder={t('searchSpecialities')}
            label={t('searchSpecialities')}
            className="w-56"
          />
          {mayManage && (
            <Button size="sm" variant="outline" onClick={onAdd}>
              <Plus aria-hidden="true" size={12} />
              {t('add')}
            </Button>
          )}
        </>
      )}
    >
      {shown.length === 0 ? (
        <EmptyState
          compact
          icon={Search}
          title={rows.length ? t('noMatch') : t('empty')}
          hint={t('searchSpecialities')}
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-base">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('name')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('code')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('order')}</th>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('status')}</th>
                <th scope="col" className="py-1.5 font-semibold">{t('actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {shown.map((s) => (
                <tr key={s.id}>
                  <td className="py-1.5 pr-2 align-top">
                    <strong className="text-foreground">{specialityName(s, locale)}</strong>
                    <div className="text-xs text-muted-foreground">
                      {locale === 'en' ? s.name_bn : s.name_en}
                    </div>
                  </td>
                  <td className="py-1.5 pr-2 align-top font-mono text-sm text-muted-foreground">
                    {s.code || '—'}
                  </td>
                  <td className="py-1.5 pr-2 align-top">
                    {s.sort_order === null || s.sort_order === undefined
                      ? <span className="text-muted-foreground">—</span> : s.sort_order}
                  </td>
                  <td className="py-1.5 pr-2 align-top">
                    <StatusBadge status={s.status || 'active'} size="sm" />
                  </td>
                  <td className="py-1.5 align-top">
                    <RowActions
                      row={s}
                      kind="specialty"
                      mayManage={mayManage}
                      onEdit={onEdit}
                      onRetire={onRetire}
                      onRestore={onRestore}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionCard>
  );
}
/** Placeholder cards while the tree loads — no layout jump when it arrives. */
function StructureSkeleton() {
  return (
    <div className="flex flex-col gap-2" aria-busy="true" aria-live="polite">
      <span className="sr-only">{t('loading')}</span>
      {[0, 1].map((n) => (
        <div key={n} className="animate-pulse rounded border border-border bg-card p-3">
          <div className="mb-2 h-4 w-40 rounded bg-muted" />
          <div className="h-3 w-full rounded bg-muted" />
          <div className="mt-2 h-3 w-3/4 rounded bg-muted" />
        </div>
      ))}
    </div>
  );
}

export default function Facilities() {
  const user = getUser();
  const orgId = user.organization_id;
  const locale = getLocale();
  const mayManage = can('facility.manage');

  const [branches, setBranches] = React.useState([]);
  const [branchId, setBranchId] = React.useState('');
  const [tree, setTree] = React.useState({ floors: [], departments: [], rooms: [] });
  const [sessions, setSessions] = React.useState([]);
  const [specialities, setSpecialities] = React.useState([]);
  const [showRetired, setShowRetired] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState('');
  const [notice, setNotice] = React.useState('');
  const [editor, setEditor] = React.useState(null);
  const [retiring, setRetiring] = React.useState(null);
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    if (!orgId) return;
    apiFetch('/api/v1/orgs/' + orgId + '/branches')
      .then((d) => {
        const list = Array.isArray(d) ? d : (d.items || []);
        setBranches(list);
        const saved = getActiveBranch();
        const first = list.find((b) => b.id === saved) || list[0];
        if (first) setBranchId(first.id);
        else setLoading(false);
      })
      .catch((e) => { setErr(String(e.message || e)); setLoading(false); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  /* Specialities are organization-wide, so retired ones are always fetched —
   * hiding them would make a retired entry unrecoverable from this screen. */
  const loadSpecialities = React.useCallback(() => {
    if (!orgId) return;
    apiFetch('/api/v1/orgs/' + orgId + '/specialties?include_inactive=true')
      .then((d) => setSpecialities(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setSpecialities([]));
  }, [orgId]);

  const loadBranch = React.useCallback(async (id, includeRetired) => {
    if (!id) return;
    setLoading(true);
    setErr('');
    try {
      const suffix = includeRetired ? '?include_inactive=true' : '';
      const [facility, rows] = await Promise.all([
        apiFetch('/api/v1/branches/' + id + '/facility' + suffix),
        apiFetch('/api/v1/branches/' + id + '/sessions'),
      ]);
      setTree({
        floors: facility.floors || [],
        departments: facility.departments || [],
        rooms: facility.rooms || [],
      });
      setSessions(Array.isArray(rows) ? rows : (rows.items || []));
    } catch (e) {
      setErr(String(e.message || e));
      setTree({ floors: [], departments: [], rooms: [] });
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => { loadBranch(branchId, showRetired); }, [branchId, showRetired, loadBranch]);
  React.useEffect(() => { loadSpecialities(); }, [loadSpecialities]);

  if (!user.id) return null;

  const occupancy = roomUsage(sessions);
  const counts = facilityCounts(tree);
  const groups = groupRoomsByFloor(tree.rooms, tree.floors);

  const openEditor = (kind, row, preset) => {
    setErr('');
    setNotice('');
    setEditor({ ...toEditor(kind, row), ...(preset || {}) });
  };

  const openRoomOnFloor = (floor) => openEditor('room', null, { floor_id: floor ? floor.id : '' });

  const field = (key) => (event) => {
    const value = event.target.value;
    setEditor((cur) => (cur ? { ...cur, [key]: value } : cur));
  };

  /* One save routine for four resources: the endpoint and the payload differ,
   * the operator flow does not. */
  const endpoint = (kind, id) => {
    if (kind === 'floor') {
      return id ? '/api/v1/floors/' + id : '/api/v1/branches/' + branchId + '/floors';
    }
    if (kind === 'department') {
      return id ? '/api/v1/departments/' + id : '/api/v1/branches/' + branchId + '/departments';
    }
    if (kind === 'room') {
      return id ? '/api/v1/rooms/' + id : '/api/v1/branches/' + branchId + '/rooms';
    }
    return id ? '/api/v1/specialties/' + id : '/api/v1/orgs/' + orgId + '/specialties';
  };

  const save = async () => {
    if (!editor) return;
    setErr('');
    setNotice('');
    const { kind, id } = editor;
    let body;
    if (kind === 'specialty') {
      if (!editor.name_en.trim()) { setErr(t('nameRequired')); return; }
      body = {
        name_en: editor.name_en.trim(),
        name_bn: editor.name_bn.trim(),
        code: editor.code.trim() || null,
        sort_order: editor.sort_order === '' ? 0 : Number(editor.sort_order),
      };
    } else if (kind === 'room') {
      if (!editor.name.trim()) { setErr(t('nameRequired')); return; }
      body = {
        name: editor.name.trim(),
        code: editor.code.trim() || null,
        floor_id: editor.floor_id || null,
        department_id: editor.department_id || null,
        room_type: editor.room_type,
        capacity: editor.capacity === '' ? null : Number(editor.capacity),
        description: editor.description.trim(),
      };
    } else {
      if (!editor.name.trim()) { setErr(t('nameRequired')); return; }
      body = {
        name: editor.name.trim(),
        code: editor.code.trim() || null,
        description: editor.description.trim(),
      };
      // `level` belongs to floors only; a department has no building level.
      if (kind === 'floor') body.level = editor.level === '' ? null : Number(editor.level);
    }
    setSaving(true);
    try {
      await apiFetch(endpoint(kind, id), {
        method: id ? 'PATCH' : 'POST',
        body: JSON.stringify(body),
      });
      setEditor(null);
      setNotice(id ? t('savedOk') : t('createdOk'));
      if (kind === 'specialty') loadSpecialities();
      else await loadBranch(branchId, showRetired);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setSaving(false);
    }
  };

  const retire = async () => {
    if (!retiring) return;
    setErr('');
    setNotice('');
    try {
      await apiFetch(endpoint(retiring.kind, retiring.row.id), { method: 'DELETE' });
      setRetiring(null);
      setNotice(t('savedOk'));
      if (retiring.kind === 'specialty') loadSpecialities();
      else await loadBranch(branchId, showRetired);
    } catch (e) {
      setRetiring(null);
      setErr(String(e.message || e));
    }
  };

  /* Re-activation is a status change, never a re-creation: the row keeps its
   * id, so every session and appointment that already points at it heals. */
  const restore = async (kind, row) => {
    setErr('');
    setNotice('');
    try {
      await apiFetch(endpoint(kind, row.id), {
        method: 'PATCH',
        body: JSON.stringify({ status: 'active' }),
      });
      setNotice(t('savedOk'));
      if (kind === 'specialty') loadSpecialities();
      else await loadBranch(branchId, showRetired);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  const retireTitle = (kind) => {
    if (kind === 'floor') return t('retireFloor');
    if (kind === 'department') return t('retireDepartment');
    if (kind === 'room') return t('retireRoom');
    return t('retireSpecialty');
  };

  const selectedBranch = branches.find((b) => b.id === branchId);

  return (
    <RequireLogin>
      <AppShell active="/facilities" breadcrumbs={[{ label: t('facilities') }]}>
        <PageHeader
          title={t('facilities')}
          subtitle={t('structureHint')}
          meta={(
            <>
              {selectedBranch && (
                <span className="font-semibold text-foreground">{selectedBranch.name}</span>
              )}
              <span>{counts.floors} {t('floors')}</span>
              <span>{counts.departments} {t('departments')}</span>
              <span>{counts.rooms} {t('rooms')}</span>
              <span>{sessions.length} {t('sessions')}</span>
            </>
          )}
          actions={mayManage ? (
            <>
              <Button variant="outline" onClick={() => openEditor('floor')}>
                <Layers aria-hidden="true" size={14} />
                {t('addFloor')}
              </Button>
              <Button variant="outline" onClick={() => openEditor('department')}>
                <Building2 aria-hidden="true" size={14} />
                {t('addDepartment')}
              </Button>
              <Button variant="primary" onClick={() => openEditor('room')}>
                <Plus aria-hidden="true" size={14} />
                {t('addRoom')}
              </Button>
            </>
          ) : null}
        />

        <Toolbar
          label={t('structure')}
          end={!mayManage && <span className="text-xs text-muted-foreground">{t('manageOnly')}</span>}
        >
          <Filter label={t('branch')} htmlFor="facility-branch">
            <BranchSelect
              id="facility-branch"
              branches={branches}
              value={branchId}
              onChange={setBranchId}
              label={t('branch')}
            />
          </Filter>
          <label className="mt-3 flex items-center gap-2 text-sm text-foreground" htmlFor="facility-show-retired">
            <input
              id="facility-show-retired"
              type="checkbox"
              className="h-4 w-4"
              checked={showRetired}
              onChange={(event) => setShowRetired(event.target.checked)}
            />
            {t('showRetired')}
          </label>
        </Toolbar>

        {err && (
          <div
            role="alert"
            className="mb-2 rounded border border-[hsl(var(--destructive)/0.35)] bg-[hsl(var(--danger-soft))] px-3 py-2 text-sm font-semibold text-destructive"
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

        {loading ? (
          <StructureSkeleton />
        ) : (
          <div className="flex flex-col gap-2">
            {groups.length === 0 ? (
              <EmptyState
                icon={Building2}
                title={t('facilityEmpty')}
                hint={t('structureHint')}
                action={mayManage && (
                  <Button variant="primary" onClick={() => openEditor('floor')}>
                    <Plus aria-hidden="true" size={14} />
                    {t('addFloor')}
                  </Button>
                )}
              />
            ) : groups.map((group) => (
              <FloorCard
                key={group.floor ? group.floor.id : 'unassigned'}
                group={group}
                occupancy={occupancy}
                mayManage={mayManage}
                onEdit={openEditor}
                onRetire={(kind, row) => setRetiring({ kind, row })}
                onRestore={restore}
                onAddRoom={openRoomOnFloor}
              />
            ))}

            <DepartmentTable
              departments={tree.departments}
              rooms={tree.rooms}
              mayManage={mayManage}
              onAdd={() => openEditor('department')}
              onEdit={openEditor}
              onRetire={(kind, row) => setRetiring({ kind, row })}
              onRestore={restore}
            />

            <CatalogueTable
              rows={specialities}
              query={query}
              onQuery={setQuery}
              mayManage={mayManage}
              onAdd={() => openEditor('specialty')}
              onEdit={openEditor}
              onRetire={(kind, row) => setRetiring({ kind, row })}
              onRestore={restore}
              locale={locale}
            />
          </div>
        )}

        {editor && (
          <Dialog
            open
            title={editorTitle(editor)}
            description={editor.id ? t('structureHint') : undefined}
            onClose={() => setEditor(null)}
            size="md"
            footer={(
              <>
                <Button variant="outline" onClick={() => setEditor(null)} disabled={saving}>
                  {t('cancel')}
                </Button>
                <Button variant="primary" loading={saving} onClick={save}>
                  {t('save')}
                </Button>
              </>
            )}
          >
            {editor.kind === 'specialty' ? (
              <FormRow>
                <Field label={t('speciality') + ' — English'} required>
                  <Input name="name_en" value={editor.name_en} onChange={field('name_en')} />
                </Field>
                <Field label={t('speciality') + ' — বাংলা'}>
                  <Input name="name_bn" value={editor.name_bn} onChange={field('name_bn')} />
                </Field>
                <Field label={t('code')}>
                  <Input name="code" value={editor.code} onChange={field('code')} />
                </Field>
                <Field label={t('order')}>
                  <Input
                    name="sort_order"
                    type="number"
                    value={editor.sort_order}
                    onChange={field('sort_order')}
                  />
                </Field>
              </FormRow>
            ) : (
              <FormRow>
                <Field label={t('name')} required>
                  <Input name="name" value={editor.name} onChange={field('name')} />
                </Field>
                <Field label={t('code')}>
                  <Input name="code" value={editor.code} onChange={field('code')} />
                </Field>
                {editor.kind === 'floor' && (
                  <Field label={t('level')} hint={t('floors') + ' — 0, 1, 2 …'}>
                    <Input
                      name="level"
                      type="number"
                      value={editor.level}
                      onChange={field('level')}
                    />
                  </Field>
                )}

                {editor.kind === 'room' && (
                  <>
                    <Field label={t('floors')}>
                      <Select name="floor_id" value={editor.floor_id} onChange={field('floor_id')}>
                        <option value="">{t('unassigned')}</option>
                        {activeOnly(tree.floors).map((f) => (
                          <option key={f.id} value={f.id}>{f.name}</option>
                        ))}
                      </Select>
                    </Field>
                    <Field label={t('department')}>
                      <Select
                        name="department_id"
                        value={editor.department_id}
                        onChange={field('department_id')}
                      >
                        <option value="">{t('unassigned')}</option>
                        {activeOnly(tree.departments).map((d) => (
                          <option key={d.id} value={d.id}>{d.name}</option>
                        ))}
                      </Select>
                    </Field>
                    <Field label={t('roomType')}>
                      <Select name="room_type" value={editor.room_type} onChange={field('room_type')}>
                        {ROOM_TYPES.map((type) => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </Select>
                    </Field>
                    <Field label={t('capacity')}>
                      <Input
                        name="capacity"
                        type="number"
                        min="0"
                        value={editor.capacity}
                        onChange={field('capacity')}
                      />
                    </Field>
                  </>
                )}

                <Field label={t('description')} className="md:col-span-2">
                  <Textarea
                    name="description"
                    rows={2}
                    value={editor.description}
                    onChange={field('description')}
                  />
                </Field>
              </FormRow>
            )}
          </Dialog>
        )}

        {retiring && (
          <ConfirmDialog
            title={retireTitle(retiring.kind)}
            message={(retiring.row.name || retiring.row.name_en || '') + ' — ' + t('retireMsg')}
            confirmLabel={t('retire')}
            busy={saving}
            onConfirm={retire}
            onClose={() => setRetiring(null)}
          />
        )}
      </AppShell>
    </RequireLogin>
  );
}




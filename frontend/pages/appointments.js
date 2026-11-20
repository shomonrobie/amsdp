export async function getServerSideProps(){return{props:{}}}
/* Appointments — calendar-first booking.
 *
 * The week/day grid is the primary surface: a receptionist clicks an empty slot
 * and books into it, or clicks a card to act on that appointment. The table is
 * kept as the "তালিকা" view, now paged, searchable and sortable *on the server*
 * (GET /api/v1/appointments/list) so one appointment can be found among
 * thousands — walk-in, cancel-with-reason and check-in keep their original API
 * calls, and no scheduling or lifecycle rule lives on this page.
 *
 * All calendar arithmetic lives in lib/calendar/grid.js and all list-query
 * arithmetic in lib/calendar/list.js (both unit-tested); this page only fetches,
 * holds state and renders.
 */
import React from 'react';
import { Search as SearchIcon } from 'lucide-react';
import AppShell from '../components/AppShell';
import AppointmentCalendar from '../components/AppointmentCalendar';
import { RequireLogin } from '../components/ui/Alert';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import PageHeader from '../components/ui/PageHeader';
import SearchInput from '../components/ui/SearchInput';
import StatusBadge from '../components/ui/StatusBadge';
import Toolbar, { Filter } from '../components/ui/Toolbar';
import { Select } from '../components/ui/Input';
import BranchSelect from '../components/shared/BranchSelect';
import Modal from '../components/ui/Modal';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import SymptomPicker, { OnsetField } from '../components/SymptomPicker';
import { getUser, apiFetch, getActiveBranch } from '../lib/auth';
import { statusLabel } from '../lib/status';
import {
  rangeFor, shiftAnchor, formatRange, formatDayLong, todayIso, slotsForDate,
  slotOf, ACTIVE_STATUSES,
} from '../lib/calendar/grid';
import {
  LIST_PAGE_SIZES, emptyQuery, isFiltered, clearFilters, setFilter, setPage, setLimit,
  toggleSort, ariaSort, buildFilterParams, buildListParams, parseEnvelope, pageWindow,
} from '../lib/calendar/list';
import {
  MATCHES_PATH, buildMatchParams, parseMatchIndex, matchSummary, nearestMatchDate,
  matchesBannerKey,
} from '../lib/calendar/matches';
/* F-18/F-19 — the booking dialog's two explanations: how full a slot is, said in
   words, and what a refusal means, said in the receptionist's language. */
import {
  seatsWord, refusalCode, REFUSAL_KEYS, bookingMode, typeLabelKey, typeBadgeKey,
  overrideProblem,
} from '../lib/calendar/booking';

const L = {
  bn: { t:'অ্যাপয়েন্টমেন্ট', p:'রোগী', d:'ডাক্তার', dt:'তারিখ', tm:'সময়', st:'অবস্থা',
    tk:'টোকেন', na:'এই দৃশ্যে কোনো অ্যাপয়েন্টমেন্ট নেই', bk:'বুকিং', wi:'ওয়াক-ইন',
    cc:'বাতিল', ci:'চেক-ইন', week:'সপ্তাহ', day:'দিন', list:'তালিকা', view:'দৃশ্য',
    today:'আজ', prev:'আগের', next:'পরের', allDoctors:'সব ডাক্তার', full:'পূর্ণ',
    closed:'শিডিউল নেই', past:'শেষ', loading:'লোড হচ্ছে…', actions:'কর্ম',
    searchPatient:'নাম বা মোবাইল দিয়ে রোগী খুঁজুন', notFound:'রোগী পাওয়া যায়নি',
    selectPatient:'রোগী নির্বাচন করুন', change:'পরিবর্তন', chooseSlot:'সময় নির্বাচন করুন',
    noSlots:'এই দিনে কোনো সেশন নেই', notes:'নোট', save:'সংরক্ষণ',
    saving:'সংরক্ষণ হচ্ছে…', bookedOk:'বুকিং সম্পন্ন হয়েছে', needPatient:'রোগী নির্বাচন করুন',
    needDoctor:'ডাক্তার নির্বাচন করুন', needDate:'তারিখ দিন', needTime:'সময় নির্বাচন করুন',
    bookErr:'বুকিং ব্যর্থ', actionErr:'কাজটি সম্পন্ন হয়নি',
    /* F-18 — the free-text fallback is not equivalent to a slot, and says so. */
    noSlotsHint:'এই ডাক্তার এই দিনে কোনো সময়সূচি দেননি — এখানে লেখা সময় কোনো স্লট বা সেশনের '
      + 'মধ্যে পড়ে না, এবং একসঙ্গে একজন রোগীকেই ধরা হয়',
    /* AMSDP-APPT-OWNER-DECISIONS-01 (Q1) — scheduled, walk-in and unscheduled are
       three different things, and the screen says which one it is booking. */
    typeScheduled:'নির্ধারিত', typeWalkIn:'ওয়াক-ইন', typeUnscheduled:'সময়সূচির বাইরে',
    typeWalkInShort:'ওয়াক-ইন', typeUnscheduledShort:'বাইরে',
    typeLabel:'ধরন', overrideReason:'কারণ (আবশ্যক)', overrideReasonLabel:'গ্রহণের কারণ',
    overrideHint:'এই সময় ডাক্তারের প্রকাশিত সেশনের বাইরে — কারণ লিখে রোগী গ্রহণ করুন। '
      + 'এটি নির্ধারিত স্লট নয়।',
    overrideReasonPlaceholder:'যেমন: জরুরি ভিজিট, সময়সূচি ছাড়া এসেছেন',
    walkInReason:'কারণ (সেশন না থাকলে আবশ্যক)',
    walkInHint:'রোগী এখন চেম্বারে আছেন — সেশন চললে সরাসরি ওয়াক-ইন, না চললে কারণ লিখে গ্রহণ।',
    allFullHint:'এই দিনের সব স্লট পূর্ণ — অন্য সময় বা দিন বেছে নিন',
    errNeedsOverride:'এই সময় প্রকাশিত সেশনে নেই — ওয়াক-ইন বা সময়সূচির বাইরে হিসেবে কারণসহ গ্রহণ করুন',
    errOverrideLimit:'এই ডাক্তারের জন্য আজ সময়সূচির বাইরে গ্রহণের সীমা শেষ',
    errOverrideDisabled:'এই প্রতিষ্ঠান সময়সূচির বাইরে রোগী গ্রহণ করে না',
    errUseWalkIn:'ওয়াক-ইন ওয়ার্কফ্লো দিয়ে রোগী যোগ করুন',
    /* F-19 — a slot's remaining room in words, and every refusal with a next step. */
    seatsLeft:'আরও {n}টি খালি', seatLast:'শেষ আসন', slotFull:'পূর্ণ',
    errSlotFull:'এই সময়টি পূর্ণ — অন্য সময় বেছে নিন',
    errNoSlot:'এই সময় ডাক্তারের ঠিক করা স্লটের মধ্যে নেই — তালিকা থেকে সময় বেছে নিন',
    errOutsideSession:'এই সময় ডাক্তারের সেশনের বাইরে — সেশনের ভিতরের সময় দিন',
    errBadDate:'তারিখটি ঠিক নেই — আবার বেছে নিন',
    errBadTime:'সময়ের বিন্যাস ঠিক নেই — ঘণ্টা:মিনিট আকারে দিন',
    errBadTransition:'এই অবস্থা থেকে এই পরিবর্তন করা যায় না — তালিকা হালনাগাদ করুন',
    errPatient:'রোগীটি পাওয়া যায়নি — আবার খুঁজুন',
    errDoctor:'ডাক্তারটি পাওয়া যায়নি — আবার বেছে নিন',
    errBranch:'শাখাটি পাওয়া যায়নি — অন্য শাখা বেছে নিন',
    errNotFound:'তথ্যটি পাওয়া গেল না — তালিকা হালনাগাদ করুন',
    errNeedReason:'কারণ আবশ্যক', errForbidden:'এই কাজটি আপনার অনুমতির বাইরে',
    errUnknown:'সার্ভার কারণ জানায়নি — আবার চেষ্টা করুন',
    loadErr:'অ্যাপয়েন্টমেন্ট লোড করা যায়নি',
    detail:'অ্যাপয়েন্টমেন্ট', reason:'বাতিলের কারণ', cancelTitle:'অ্যাপয়েন্টমেন্ট বাতিল',
    cancelMsg:'এই অ্যাপয়েন্টমেন্ট বাতিল করতে চান? কারণ আবশ্যক।',
    confirmCancel:'বাতিল নিশ্চিত করুন', back:'ফিরে যান', source:'উৎস',
    weekTotal:'এই সপ্তাহে মোট', dayTotal:'এই দিনে মোট', capacity:'ধারণক্ষমতা',
    booked:'বুক হয়েছে', walkOk:'ওয়াক-ইন যোগ হয়েছে', search:'খুঁজুন',
    /* AMSDP-APPT-LIST-UX — the toolbar, the list view and its paging. */
    subtitle:'ফাঁকা স্লটে ক্লিক করে বুক করুন, কার্ডে ক্লিক করে কাজ করুন',
    searchAppt:'রোগীর নাম, মোবাইল বা টোকেন', filters:'ফিল্টার', allStatus:'সব অবস্থা',
    branch:'শাখা', allBranches:'সব শাখা', clearFilters:'ফিল্টার মুছুন',
    noResults:'কোনো অ্যাপয়েন্টমেন্ট মেলেনি', noResultsHint:'তারিখ বা ফিল্টার বদলে আবার দেখুন',
    showing:'দেখানো হচ্ছে', pages:'পৃষ্ঠা', prevPage:'আগের পৃষ্ঠা', nextPage:'পরের পৃষ্ঠা',
    pageSize:'প্রতি পৃষ্ঠা', loc:'কক্ষ', more:'আরও {n}', sortBy:'সাজান', total:'মোট',
    /* AMSDP-CALENDAR-FILTER-01 (D-2) — the search matched beyond these dates. */
    weekMatches:'এই সপ্তাহে মিলেছে', dayMatches:'এই দিনে মিলেছে',
    otherDates:'এই তারিখগুলোর বাইরে আরও {n}টি মিল আছে — {d}টি তারিখে',
    /* Bangla does not inflect its counters, so all three English variants are
       the same sentence here; the keys still exist so `T()` never falls back. */
    otherDatesOne:'এই তারিখগুলোর বাইরে আরও {n}টি মিল আছে — {d}টি তারিখে',
    otherDatesOneDate:'এই তারিখগুলোর বাইরে আরও {n}টি মিল আছে — {d}টি তারিখে',
    otherDatesTruncated:'(আরও তারিখ আছে — তালিকায় সব দেখুন)',
    gotoNearest:'কাছের তারিখে যান', seeAllMatches:'তালিকায় সব দেখুন',
    searchingOtherDates:'অন্য তারিখেও খোঁজা হচ্ছে…',
    /* AMSDP-SYMPTOM-01 — the two optional questions the receptionist asks. */
    sy:'উপসর্গ', syNone:'কোনো উপসর্গ দেওয়া হয়নি', onset:'কখন থেকে',
    syPrompt:'আপনার কী কী সমস্যা হচ্ছে?',
    syPlaceholder:'উপসর্গ খুঁজুন — বাংলা বা ইংরেজি', syOptional:'ঐচ্ছিক',
    sySelected:'নির্বাচিত উপসর্গ', syRemove:'সরান', syFreeText:'নিজের ভাষায়',
    syAddFree:'নিজের ভাষায় লিখে যোগ করুন',
    syAlready:'এই উপসর্গটি আগেই নির্বাচন করা হয়েছে', syFull:'আরও উপসর্গ যোগ করা যাবে না',
    syHint:'ঐচ্ছিক — রোগী যা বলছেন তাই লিখুন। এটি রোগনির্ণয় নয়।',
    syList:'উপসর্গের প্রস্তাব', onsetPrompt:'কখন থেকে সমস্যা হচ্ছে?',
    onsetNotAsked:'জিজ্ঞাসা করা হয়নি', onsetNote:'সংক্ষিপ্ত বিবরণ',
    onsetNotePlaceholder:'যেমন: প্রায় চার দিন ধরে, সকালে বেশি' },
  en: { t:'Appointments', p:'Patient', d:'Doctor', dt:'Date', tm:'Time', st:'Status',
    tk:'Token', na:'No appointments in this view', bk:'Book', wi:'Walk-in',
    cc:'Cancel', ci:'Check-in', week:'Week', day:'Day', list:'List', view:'View',
    today:'Today', prev:'Previous', next:'Next', allDoctors:'All Doctors', full:'Full',
    closed:'No clinic', past:'Past', loading:'Loading…', actions:'Actions',
    searchPatient:'Search a patient by name or mobile', notFound:'No patient found',
    selectPatient:'Select patient', change:'Change', chooseSlot:'Choose a time',
    noSlots:'No clinic on this day', notes:'Notes', save:'Save',
    saving:'Saving…', bookedOk:'Appointment booked', needPatient:'Select a patient',
    needDoctor:'Select a doctor', needDate:'Pick a date', needTime:'Pick a time',
    bookErr:'Booking failed', actionErr:'That action did not complete',
    /* F-18 — the free-text fallback is not equivalent to a slot, and says so. */
    noSlotsHint:'This doctor publishes no session on this day — a time entered here falls outside '
      + 'every slot and session, and is counted one patient at a time',
    /* AMSDP-APPT-OWNER-DECISIONS-01 (Q1) — the three persisted types. */
    typeScheduled:'Scheduled', typeWalkIn:'Walk-in', typeUnscheduled:'Outside hours',
    typeWalkInShort:'Walk-in', typeUnscheduledShort:'Outside',
    typeLabel:'Type', overrideReason:'Reason (required)', overrideReasonLabel:'Acceptance reason',
    overrideHint:'This time is outside the doctor\u2019s published sessions — record '
      + 'why the patient is accepted. This is not a confirmed slot.',
    overrideReasonPlaceholder:'e.g. urgent visit, arrived without an appointment',
    walkInReason:'Reason (required outside a session)',
    walkInHint:'The patient is here now — inside a session this is a walk-in, '
      + 'otherwise record the reason and accept them.',
    allFullHint:'Every slot this day is full — choose another time or day',
    errNeedsOverride:'That time is outside the published sessions — register a '
      + 'walk-in, or accept an outside-hours visit with a reason',
    errOverrideLimit:'This doctor has reached today\u2019s outside-hours limit',
    errOverrideDisabled:'This organization does not accept patients outside its sessions',
    errUseWalkIn:'Register the patient through the walk-in workflow',
    /* F-19 — a slot's remaining room in words, and every refusal with a next step. */
    seatsLeft:'{n} left', seatLast:'last seat', slotFull:'Full',
    errSlotFull:'That time is fully booked — choose another slot',
    errNoSlot:'That time is not one of the doctor\'s published slots — pick one of the listed times',
    errOutsideSession:'That time is outside the doctor\'s session — pick a time inside it',
    errBadDate:'That date is not valid — pick it again',
    errBadTime:'That time is not valid — use hours:minutes',
    errBadTransition:'This appointment cannot change that way — refresh the list',
    errPatient:'That patient was not found — search again',
    errDoctor:'That doctor was not found — choose again',
    errBranch:'That branch was not found — choose another',
    errNotFound:'That record was not found — refresh the list',
    errNeedReason:'A reason is required', errForbidden:'This action is outside your permission',
    errUnknown:'The server gave no reason — try again',
    loadErr:'Could not load appointments',
    detail:'Appointment', reason:'Cancellation reason', cancelTitle:'Cancel appointment',
    cancelMsg:'Cancel this appointment? A reason is required.',
    confirmCancel:'Confirm cancel', back:'Back', source:'Source',
    weekTotal:'This week', dayTotal:'This day', capacity:'Capacity',
    booked:'booked', walkOk:'Walk-in registered', search:'Search',
    /* AMSDP-APPT-LIST-UX — the toolbar, the list view and its paging. */
    subtitle:'Click an empty slot to book, a card to act on it',
    searchAppt:'Patient name, mobile or token', filters:'Filters', allStatus:'All statuses',
    branch:'Branch', allBranches:'All branches', clearFilters:'Clear filters',
    noResults:'No appointments match', noResultsHint:'Try another date or filter',
    showing:'Showing', pages:'Pages', prevPage:'Previous page', nextPage:'Next page',
    pageSize:'Per page', loc:'Chamber', more:'{n} more', sortBy:'Sort by', total:'Total',
    /* AMSDP-CALENDAR-FILTER-01 (D-2) — the search matched beyond these dates. */
    weekMatches:'Matched this week', dayMatches:'Matched this day',
    otherDates:'{n} more matches on {d} other dates',
    /* AMSDP-CALENDAR-FILTER-01 — English inflects both numbers; `matchesBannerKey`
       picks the sentence so the banner never reads "1 more matches on 1 other
       dates" (browser verification S02). */
    otherDatesOne:'1 more match on 1 other date',
    otherDatesOneDate:'{n} more matches on 1 other date',
    otherDatesTruncated:'(more dates than can be listed — open the list)',
    gotoNearest:'Go to nearest date', seeAllMatches:'See all in the list',
    searchingOtherDates:'Searching other dates…',
    /* AMSDP-SYMPTOM-01 — the two optional questions the receptionist asks. */
    sy:'Symptoms', syNone:'No symptom recorded', onset:'Problem started',
    syPrompt:'What problems are you having?',
    syPlaceholder:'Search a symptom — Bangla or English', syOptional:'optional',
    sySelected:'Selected symptoms', syRemove:'Remove', syFreeText:'as described',
    syAddFree:'Add this exactly as described',
    syAlready:'That symptom is already selected', syFull:'No further symptoms can be added',
    syHint:'Optional — record what the patient reports. This is not a diagnosis.',
    syList:'Symptom suggestions', onsetPrompt:'When did the problem start?',
    onsetNotAsked:'Not asked', onsetNote:'Short description',
    onsetNotePlaceholder:'e.g. about four days, worse in the morning' },
};

/** Bangla is the default locale and the AppShell toggle writes this key. */
function locale() {
  if (typeof window === 'undefined') return 'bn';
  return sessionStorage.getItem('locale') || 'bn';
}
function T(key) {
  const table = L[locale()] || L.bn;
  return table[key] || L.bn[key] || key;
}

/**
 * Fill a `{token}` template, emphasising the values it substitutes.
 *
 * The same convention `labels.more` uses (`'আরও {n}'`), so a translated sentence
 * keeps its number next to the words around it rather than at a fixed offset.
 * The substituted values get `<strong>` because they are the fact being
 * reported — how many matches, on how many dates.
 */
function withNumbers(template, values) {
  return String(template).split(/(\{\w+\})/).map((part, i) => {
    const token = /^\{\w+\}$/.test(part) ? part.slice(1, -1) : '';
    if (token && token in values) return <strong key={i}>{values[token]}</strong>;
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

/** Fill a `{token}` template as plain text — button labels and tooltips. */
function fill(template, values) {
  return String(template).replace(/\{(\w+)\}/g,
    (whole, key) => (key in values ? String(values[key]) : whole));
}

/**
 * F-19 — the server's refusal, said in the reader's language.
 *
 * The dialog used to append `String(e.message || e)`, which put an English
 * sentence from `backend/appointment/main.py` inside a Bangla screen and named
 * concepts (a "session window") the dialog never showed.  `refusalCode` maps the
 * refusal to a caption that carries a next step, and an unrecognised answer is
 * reported as unrecognised rather than pasted verbatim.
 */
function refusalText(err) {
  return T(REFUSAL_KEYS[refusalCode(err)] || 'errUnknown');
}

/* The lifecycle order the status filter offers. Labels and tones come from
   lib/status, so the filter, the badge and the calendar card cannot drift. */
const LIFECYCLE = ['BOOKED', 'AWAITING_CONFIRMATION', 'CONFIRMED', 'CHECKED_IN',
  'IN_QUEUE', 'IN_CONSULTATION', 'COMPLETED', 'CANCELLED', 'NO_SHOW', 'RESCHEDULED'];
const ACTIONS = { BOOKED:['CONFIRMED','CANCELLED'], CONFIRMED:['CHECKED_IN','CANCELLED'],
  CHECKED_IN:['IN_QUEUE'], IN_QUEUE:['IN_CONSULTATION','CANCELLED'],
  IN_CONSULTATION:['COMPLETED'] };
const CAN_BOOK = ['super_admin', 'org_admin', 'branch_admin', 'receptionist'];

/** Column-header styling, shared by the plain and the sortable headers.
 *  The colour of a header cell comes from `global.css` (`th`), which paints the
 *  app's existing table header; only the metrics are set here. */
const TH = 'whitespace-nowrap px-2 py-1.5 text-left text-[0.68rem] font-semibold '
  + 'uppercase tracking-wide';

/** A column that cannot be sorted (token, time, actions). */
function Th({ label }) {
  return <th scope='col' className={TH}>{label}</th>;
}

/**
 * A sortable column header.
 *
 * `aria-sort` lives on the <th> and the button carries the action, so a screen
 * reader announces both the current order and what pressing it will do. The ▲/▼
 * is decorative: the order is already stated by `aria-sort`. `border-0
 * bg-transparent p-0` is required: Tailwind's preflight is deliberately off in
 * this app (see `tailwind.config.js`), so a bare <button> would otherwise paint
 * the browser's own chrome inside the header cell.
 */
function SortTh({ column, label, query, onSort }) {
  const active = query.sort === column;
  return (
    <th scope='col' aria-sort={ariaSort(query, column)} className={TH}>
      <button type='button' onClick={() => onSort(column)}
        aria-label={label + ' — ' + T('sortBy')}
        className={'inline-flex items-center gap-1 border-0 bg-transparent p-0 uppercase '
          + 'tracking-wide hover:opacity-80 ' + (active ? 'font-bold' : '')}>
        {label}
        {active ? <span aria-hidden='true'>{query.order === 'asc' ? '▲' : '▼'}</span> : null}
      </button>
    </th>
  );
}

/** Patient type-ahead — the same search endpoint the patients page uses. */
function PatientSearch({ selected, onPick, onClear }) {
  const [query, setQuery] = React.useState('');
  const [rows, setRows] = React.useState([]);
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    const text = query.trim();
    if (selected || text.length < 2) { setRows([]); return undefined; }
    let alive = true;
    setBusy(true);
    const timer = setTimeout(() => {
      apiFetch('/api/v1/patients?q=' + encodeURIComponent(text) + '&page=1&limit=20')
        .then((d) => { if (alive) { setRows((d && d.items) || []); setBusy(false); } })
        .catch(() => { if (alive) { setRows([]); setBusy(false); } });
    }, 250);
    return () => { alive = false; clearTimeout(timer); };
  }, [query, selected]);

  if (selected) {
    return (
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center',
        border:'1px solid #cfe0e9', background:'#eef4f8', borderRadius:4, padding:'0.45rem 0.6rem' }}>
        <span><strong>{selected.name}</strong>{selected.mobile ? ' · ' + selected.mobile : ''}</span>
        <button type='button' className='btn btn-sm btn-outline' onClick={onClear}>{T('change')}</button>
      </div>
    );
  }
  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)}
        placeholder={T('searchPatient')} aria-label={T('searchPatient')} />
      {busy && <div className='loading' style={{ padding:'0.4rem' }}>…</div>}
      {rows.length > 0 && (
        <ul className='bns-list' style={{ position:'static', marginTop:4, maxHeight:180 }}>
          {rows.map((p) => (
            <li key={p.id}>
              <button type='button' className='bns-option'
                style={{ width:'100%', border:'none', background:'transparent', textAlign:'left' }}
                onClick={() => onPick(p)}>
                <span className='bns-name'>{p.name}</span>
                <span className='bns-alias'>{p.mobile}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {!busy && query.trim().length >= 2 && rows.length === 0 && (
        <div className='empty' style={{ padding:'0.4rem' }}>{T('notFound')}</div>
      )}
    </div>
  );
}

/** Slot buttons for the chosen doctor + date, with the live booked count. */
function slotsForBooking({ schedules, doctorId, date, dayRows }) {
  if (!date) return [];
  const doctorSchedules = (schedules || []).filter((s) => s.doctor_id === doctorId);
  const counts = {};
  (dayRows || []).forEach((a) => {
    if (!ACTIVE_STATUSES.includes(a.status)) return;
    const key = slotOf(a);
    counts[key] = (counts[key] || 0) + 1;
  });
  return slotsForDate(doctorSchedules, date).map((slot) => {
    const booked = counts[slot.start] || 0;
    return { ...slot, booked, full: booked >= slot.capacity };
  });
}

export default function Appointments() {
  const user = getUser();
  const [view, setView] = React.useState('week');
  const [anchor, setAnchor] = React.useState(() => todayIso());
  const [doctorId, setDoctorId] = React.useState('');
  const [appointments, setAppointments] = React.useState([]);
  const [schedules, setSchedules] = React.useState([]);
  const [doctors, setDoctors] = React.useState([]);
  const [names, setNames] = React.useState({});
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [notice, setNotice] = React.useState('');
  const [detail, setDetail] = React.useState(null);
  const [cancelTarget, setCancelTarget] = React.useState(null);
  const [book, setBook] = React.useState(null);
  const [dayRows, setDayRows] = React.useState([]);
  const [bookError, setBookError] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [walk, setWalk] = React.useState(null);
  /* AMSDP-SYMPTOM-01 — the bilingual catalogue, fetched once for the session
     and searched in memory (see components/SymptomPicker.js).  An empty
     payload is a legitimate state: the form then offers free text only. */
  const [catalogue, setCatalogue] = React.useState(
    { items: [], onset_options: [], max_symptoms: 20 });
  /* AMSDP-APPT-LIST-UX — the list view's query, its answer and its own busy
     state.  `query` is the single source of the search, the filters, the sort
     and the page; `list.items === null` means "not fetched yet". */
  const [query, setQuery] = React.useState(emptyQuery);
  const [searchText, setSearchText] = React.useState('');
  const [list, setList] = React.useState(
    { items: null, total: 0, page: 1, limit: LIST_PAGE_SIZES[0], pages: 0 });
  const [listBusy, setListBusy] = React.useState(false);
  const [listError, setListError] = React.useState('');
  /* Bumped after every booking/status change so the list refetches without the
     page having to know which of its two data sources changed. */
  const [listTick, setListTick] = React.useState(0);
  /* AMSDP-CALENDAR-FILTER-01 (D-2) — where the current search matched *outside*
     the dates on screen.  Counts only, `null` while nothing narrows the
     calendar; a failed request leaves it `null` rather than inventing a number. */
  const [matches, setMatches] = React.useState(null);
  const [matchesBusy, setMatchesBusy] = React.useState(false);
  const [branches, setBranches] = React.useState([]);

  const today = todayIso();
  const gridView = view === 'list' ? 'week' : view;
  const range = React.useMemo(() => rangeFor(gridView, anchor), [gridView, anchor]);
  const canBook = CAN_BOOK.includes(user.role);

  /* One request per visible range *and* per filter change: the grid reads
     exactly what the list reads.  `buildFilterParams` is the same builder the
     paged list uses, so the search box, the status filter, the doctor filter and
     the branch picker cannot apply to one view and not the other
     (AMSDP-CALENDAR-FILTER-01, F-1/F-2). */
  const gridParams = React.useMemo(
    () => new URLSearchParams(
      buildFilterParams(query, { from: range.from, to: range.to })).toString(),
    [query, range.from, range.to],
  );
  const load = React.useCallback(async () => {
    setLoading(true); setError('');
    try {
      const data = await apiFetch('/api/v1/appointments?' + gridParams);
      setAppointments(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(T('loadErr') + ': ' + String(e.message || e));
    } finally {
      setLoading(false);
    }
  }, [gridParams]);

  React.useEffect(() => { if (user.id) load(); }, [load, user.id]);

  /* Refresh both data sources together: a booking or a status change must be
     visible in the grid *and* in the paged list. */
  const refresh = React.useCallback(async () => {
    await load();
    setListTick((n) => n + 1);
  }, [load]);

  /* The branches this token may switch to (`/me/branches` is already scoped to
     it, so the picker can never offer an out-of-scope id).  One branch means no
     choice to offer — the control stays away rather than showing one option. */
  React.useEffect(() => {
    if (!user.id) return undefined;
    let alive = true;
    apiFetch('/api/v1/me/branches')
      .then((d) => {
        if (!alive) return;
        const items = Array.isArray(d) ? d : (d && d.items) || [];
        setBranches(items.filter((b) => b && b.id));
      })
      .catch(() => { if (alive) setBranches([]); });
    return () => { alive = false; };
  }, [user.id]);

  /* Typing is debounced before it becomes a request; the input itself stays
     synchronous, so the caret never jumps while the receptionist types. */
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setQuery((q) => (q.q === searchText ? q : setFilter(q, 'q', searchText)));
    }, 300);
    return () => clearTimeout(timer);
  }, [searchText]);

  /* One request per query change, and only while the list is on screen.  The
     request is rebuilt from `lib/calendar/list.js`, so the server does the
     search, the filtering, the sorting and the paging. */
  const listParams = React.useMemo(
    () => new URLSearchParams(buildListParams(query, { from: range.from, to: range.to })).toString(),
    [query, range.from, range.to],
  );
  React.useEffect(() => {
    if (!user.id || view !== 'list') return undefined;
    let alive = true;
    const params = new URLSearchParams(listParams);
    const limit = Number(params.get('limit')) || LIST_PAGE_SIZES[0];
    setListBusy(true); setListError('');
    apiFetch('/api/v1/appointments/list?' + listParams)
      .then((d) => { if (alive) { setList(parseEnvelope(d)); setListBusy(false); } })
      .catch((e) => {
        if (!alive) return;
        setListError(T('loadErr') + ': ' + String(e.message || e));
        setList({ items: [], total: 0, page: 1, limit, pages: 0 });
        setListBusy(false);
      });
    return () => { alive = false; };
  }, [user.id, view, listParams, listTick]);

  /* D-2 — a search reaches every date the token may read, so the Week/Day grid
     has to say where the matches it cannot show are.  The index is asked for
     counts only, with the same filters as the grid but *without* the date
     window; the banner then states a number and offers the nearest other date.
     Only the index's own vocabulary counts as "a search" here: a date bound on
     its own is not a query whose other dates mean anything, so it never starts
     one. */
  const searchActive = isFiltered(query);
  const matchFilters = React.useMemo(() => buildMatchParams(query), [query]);
  const matchIndexWanted = Object.keys(matchFilters).length > 0;
  const matchesParams = React.useMemo(() => {
    if (view === 'list' || !matchIndexWanted) return '';
    return new URLSearchParams({ ...matchFilters, near: anchor }).toString();
  }, [view, matchIndexWanted, matchFilters, anchor]);
  React.useEffect(() => {
    if (!user.id || !matchesParams) {
      setMatches(null); setMatchesBusy(false); return undefined;
    }
    let alive = true;
    setMatchesBusy(true);
    apiFetch(MATCHES_PATH + '?' + matchesParams)
      .then((d) => { if (alive) { setMatches(parseMatchIndex(d)); setMatchesBusy(false); } })
      .catch(() => { if (alive) { setMatches(null); setMatchesBusy(false); } });
    return () => { alive = false; };
  }, [user.id, matchesParams, listTick]);
  const matchesSummary = React.useMemo(
    () => (matches ? matchSummary(matches, { from: range.from, to: range.to }) : null),
    [matches, range.from, range.to],
  );
  const nearestOther = matchesSummary ? nearestMatchDate(matchesSummary, anchor) : '';

  React.useEffect(() => {
    if (!user.id) return;
    const branch = getActiveBranch();
    const url = '/api/v1/doctors' + (branch ? '?branch_id=' + encodeURIComponent(branch) : '');
    apiFetch(url)
      .then((d) => {
        const items = (d && d.items) || [];
        if (items.length || !branch) return setDoctors(items);
        // Branch context may not map to a doctor record; never hide the calendar for it.
        return apiFetch('/api/v1/doctors').then((all) => setDoctors((all && all.items) || []));
      })
      .catch(() => setDoctors([]));
    apiFetch('/api/v1/schedules')
      .then((d) => setSchedules(Array.isArray(d) ? d : []))
      .catch(() => setSchedules([]));
  }, [user.id]);

  /* The symptom catalogue: one request, no request per keystroke.  A failure
     is not fatal — booking, and free-text symptom recording, still work. */
  React.useEffect(() => {
    if (!user.id) return undefined;
    let alive = true;
    apiFetch('/api/v1/symptoms')
      .then((d) => {
        if (!alive || !d) return;
        setCatalogue({
          items: Array.isArray(d.items) ? d.items : [],
          onset_options: Array.isArray(d.onset_options) ? d.onset_options : [],
          max_symptoms: Number.isInteger(d.max_symptoms) ? d.max_symptoms : 20,
        });
      })
      .catch(() => { if (alive) setCatalogue({ items: [], onset_options: [], max_symptoms: 20 }); });
    return () => { alive = false; };
  }, [user.id]);

  /* Chip names: only the rows whose patient name did not come with the
     appointment need a lookup — normally none of them. */
  React.useEffect(() => {
    if (!user.id) return undefined;
    const missing = [...new Set(appointments
      .filter((a) => a && a.patient_id && !a.patient_name && !names[a.patient_id])
      .map((a) => a.patient_id))];
    if (!missing.length) return undefined;
    let alive = true;
    Promise.all(missing.map(async (id) => {
      try {
        const p = await apiFetch('/api/v1/patients/' + encodeURIComponent(id));
        return [id, (p && p.name) || '#' + id.slice(0, 6)];
      } catch (e) {
        return [id, '#' + id.slice(0, 6)];
      }
    })).then((pairs) => {
      if (!alive) return;
      setNames((prev) => {
        const next = { ...prev };
        pairs.forEach(([id, name]) => { next[id] = name; });
        return next;
      });
    });
    return () => { alive = false; };
  }, [appointments, names, user.id]);

  /* The slot picker needs the chosen day's bookings even outside the range. */
  const bookDate = book && book.date;
  const bookDoctor = book && book.doctorId;
  React.useEffect(() => {
    if (!bookDate) return undefined;
    let alive = true;
    const params = new URLSearchParams({ date: bookDate });
    if (bookDoctor) params.set('doctor_id', bookDoctor);
    apiFetch('/api/v1/appointments?' + params.toString())
      .then((d) => { if (alive) setDayRows(Array.isArray(d) ? d : []); })
      .catch(() => { if (alive) setDayRows([]); });
    return () => { alive = false; };
  }, [bookDate, bookDoctor]);

  const openBooking = (opts = {}) => {
    setBookError(''); setDayRows([]);
    const date = opts.date || (view === 'day' ? anchor : today);
    const time = opts.time || '';
    setBook({
      date,
      time,
      doctorId: opts.doctorId || preferredDoctor(date, time),
      patient: null,
      notes: '',
      // AMSDP-SYMPTOM-01 — the two optional questions start empty, always.  No
      // symptom is pre-selected, and the booking is complete without them.
      symptoms: { ids: [], texts: [] },
      onset: '',
      onsetNote: '',
      // AMSDP-APPT-OWNER-DECISIONS-01 (Q1) — the override reason, empty until
      // the dialog decides the requested time falls outside published sessions.
      overrideReason: '',
    });
  };

  const saveBooking = async () => {
    if (!book) return;
    if (!book.patient) { setBookError(T('needPatient')); return; }
    if (!book.doctorId) { setBookError(T('needDoctor')); return; }
    if (!book.date) { setBookError(T('needDate')); return; }
    /* Q1: with no published slot the booking is an explicit outside-hours
       acceptance, so it carries the type and a reason.  A typed time is still
       recorded (it places the card on the day), but it is no longer presented or
       sent as a confirmed slot. */
    const mode = bookingMode(slotChoices).mode;
    const unscheduled = mode === 'unscheduled';
    if (unscheduled) {
      const problem = overrideProblem({ reason: book.overrideReason });
      if (problem) { setBookError(T(problem)); return; }
    }
    const time = (book.time || '').slice(0, 5);
    if (!time && !unscheduled) { setBookError(T('needTime')); return; }
    setSaving(true); setBookError('');
    try {
      const created = await apiFetch('/api/v1/appointments', {
        method: 'POST',
        body: JSON.stringify({
          patient_id: book.patient.id,
          doctor_id: book.doctorId,
          appointment_date: book.date,
          start_time: time || null,
          appointment_type: unscheduled ? 'unscheduled' : 'scheduled',
          override_reason: unscheduled ? String(book.overrideReason).trim() : '',
          notes: book.notes || '',
          booking_source: 'reception',
          // Empty lists are the normal case, not a special one.
          symptom_ids: (book.symptoms && book.symptoms.ids) || [],
          symptom_texts: (book.symptoms && book.symptoms.texts) || [],
          symptom_onset: book.onset || null,
          symptom_onset_note: book.onsetNote || '',
        }),
      });
      const token = created && created.token_number;
      setNotice(T('bookedOk') + (token ? ' — ' + T('tk') + ': ' + token : ''));
      setBook(null);
      await refresh();
    } catch (e) {
      setBookError(T('bookErr') + ': ' + refusalText(e));
    } finally {
      setSaving(false);
    }
  };

  const changeStatus = async (appt, status, reason = '') => {
    try {
      await apiFetch('/api/v1/appointments/' + appt.id + '/status',
        { method: 'PATCH', body: JSON.stringify({ status, reason }) });
      setDetail(null);
      await refresh();
    } catch (e) {
      setError(T('actionErr') + ': ' + refusalText(e));
    }
  };

  const checkIn = async (appt) => {
    try {
      await apiFetch('/api/v1/appointments/' + appt.id + '/check-in',
        { method: 'POST', body: JSON.stringify({ status: 'CHECKED_IN', reason: '' }) });
      setDetail(null);
      await refresh();
    } catch (e) {
      setError(T('actionErr') + ': ' + refusalText(e));
    }
  };

  const registerWalkIn = async () => {
    if (!walk) return;
    if (!walk.patient) { setBookError(T('needPatient')); return; }
    if (!walk.doctorId) { setBookError(T('needDoctor')); return; }
    setSaving(true); setBookError('');
    try {
      await apiFetch('/api/v1/appointments/walk-in', {
        method: 'POST',
        body: JSON.stringify({
          patient_id: walk.patient.id,
          doctor_id: walk.doctorId,
          notes: walk.notes || '',
          /* Q1: the server decides whether this arrival is inside a published
             session.  A reason is required when it is not, and is recorded with
             the appointment; it is simply ignored when a session covers it. */
          reason: (walk.reason || '').trim(),
          symptom_ids: (walk.symptoms && walk.symptoms.ids) || [],
          symptom_texts: (walk.symptoms && walk.symptoms.texts) || [],
          symptom_onset: walk.onset || null,
          symptom_onset_note: walk.onsetNote || '',
        }),
      });
      setWalk(null); setNotice(T('walkOk'));
      await refresh();
    } catch (e) {
      setBookError(T('bookErr') + ': ' + refusalText(e));
    } finally {
      setSaving(false);
    }
  };

  const doctorName = (id) => (doctors.find((d) => d.id === id) || {}).name
    || '#' + String(id || '').slice(0, 6);

  /**
   * Which doctor a click on an empty cell should book into.
   *
   * With a doctor filter the answer is that doctor. In the combined "all
   * doctors" timetable the cell is the union of every doctor's hours, so pick a
   * doctor who still has capacity in that slot; failing that, one who publishes
   * the slot at all, so the booking dialog can show it as full rather than
   * silently offering a time nobody works.
   */
  function preferredDoctor(date, time) {
    if (doctorId) return doctorId;
    const ids = [...new Set(schedules.map((s) => s.doctor_id).filter(Boolean))];
    if (!date || !time || !ids.length) return ids[0] || (doctors[0] && doctors[0].id) || '';
    const counts = {};
    appointments.forEach((a) => {
      if (!ACTIVE_STATUSES.includes(a.status)) return;
      if (a.appointment_date !== date || slotOf(a) !== time) return;
      counts[a.doctor_id] = (counts[a.doctor_id] || 0) + 1;
    });
    const slotOfDoctor = (id) => slotsForDate(schedules.filter((s) => s.doctor_id === id), date)
      .find((s) => s.start === time);
    const withRoom = ids.find((id) => {
      const slot = slotOfDoctor(id);
      return slot && (counts[id] || 0) < slot.capacity;
    });
    return withRoom || ids.find((id) => Boolean(slotOfDoctor(id))) || ids[0];
  }

  /* The grid rows carry the patient's name now (the read joins it), so the
     calendar no longer issues one patient request per name on screen.  The
     lookup map stays as the fallback for a row whose patient record is gone,
     which must still read as something rather than a blank card. */
  const patientName = (a) => a.patient_name || names[a.patient_id]
    || '#' + String(a.patient_id || '').slice(0, 6);

  /* AMSDP-SYMPTOM-01 — labels and rendering helpers for the two optional
     questions.  The catalogue supplies its own bilingual wording for the
     symptoms and onset options; these are only the surrounding captions, which
     follow the page's existing `T()` convention. */
  const symptomLabels = {
    title: T('sy'), optional: T('syOptional'), prompt: T('syPrompt'),
    placeholder: T('syPlaceholder'), selected: T('sySelected'), none: T('syNone'),
    remove: T('syRemove'), freeText: T('syFreeText'), addFree: T('syAddFree'),
    alreadySelected: T('syAlready'), full: T('syFull'), hint: T('syHint'),
    listLabel: T('syList'), onsetTitle: T('onsetPrompt'),
    onsetNotAsked: T('onsetNotAsked'), onsetNote: T('onsetNote'),
    onsetNotePlaceholder: T('onsetNotePlaceholder'),
  };

  /**
   * The selected doctor's speciality codes — the *only* booking context the
   * symptom search sees.  It reorders equally good text matches and nothing
   * else: no symptom is added, hidden or suggested because of it, and neither
   * the patient's age nor sex is passed at all.
   */
  const specialtyCodesFor = (selectedDoctorId) => {
    const doc = doctors.find((d) => d.id === selectedDoctorId);
    if (!doc) return [];
    const codes = (doc.specialties || []).map((s) => s.code).filter(Boolean);
    if (!codes.length && doc.speciality) {
      codes.push(String(doc.speciality).toLowerCase().replace(/[^a-z]+/g, ' ').trim());
    }
    return codes;
  };

  const symptomLine = (a) => {
    const list = (a && a.symptoms) || [];
    if (!list.length) return '-';
    return list.map((s) => (s.kind === 'catalogue'
      ? (locale() === 'en' ? (s.name_en || s.name_bn) : (s.name_bn || s.name_en))
      : s.text + ' (' + T('syFreeText') + ')')).join(', ');
  };

  const onsetLine = (a) => {
    if (!a || !a.symptom_onset) return '-';
    const option = (catalogue.onset_options || [])
      .find((o) => o.code === a.symptom_onset);
    const label = option
      ? (locale() === 'en' ? option.name_en : option.name_bn)
      : a.symptom_onset;
    return a.symptom_onset_note ? label + ' — ' + a.symptom_onset_note : label;
  };

  const scopedSchedules = doctorId ? schedules.filter((s) => s.doctor_id === doctorId) : schedules;
  const slotChoices = book
    ? slotsForBooking({ schedules, doctorId: book.doctorId, date: book.date, dayRows })
    : [];
  /* One vocabulary for every status on this page: the badge, the filter options
     and the action buttons all read lib/status. */
  const actionLabel = (act) => (act === 'CANCELLED' ? T('cc')
    : act === 'CHECKED_IN' ? T('ci') : statusLabel(act, locale()));

  /* --- the list view's derived handles ------------------------------------ */
  /** The list payload already carries the patient's name; no lookup needed. */
  const listPatientName = (a) => a.patient_name || patientName(a);
  /** The doctor filter drives the grid *and* the list; keep them one state. */
  const setDoctor = (value) => {
    setDoctorId(value);
    setQuery((q) => setFilter(q, 'doctor_id', value));
  };
  const sortBy = (key) => setQuery((q) => toggleSort(q, key));
  const resetFilters = () => {
    setDoctorId('');
    setSearchText('');
    setQuery((q) => clearFilters(q));
  };
  const pageItems = list.items || [];
  const pageWin = pageWindow(list.page, list.pages);
  const firstRow = list.total ? (list.page - 1) * list.limit + 1 : 0;
  const lastRow = list.total ? Math.min(list.total, firstRow + pageItems.length - 1) : 0;

  if (!user.id) return null;

  return (
    <RequireLogin>
      <AppShell active='/appointments' breadcrumbs={[{ label: T('t') }]}>
        <div>
          <PageHeader
            title={T('t')}
            subtitle={T('subtitle')}
            meta={<>
              <span>{T('view')}: <strong>{T(view)}</strong></span>
              <span>{gridView === 'day'
                ? formatDayLong(anchor, locale())
                : formatRange(range.from, range.to, locale())}</span>
              {/* Each view reports its own data: the grid's count describes the
                  cards on screen, the list states its own total next to the
                  pager.  Printing both at once invites comparing two numbers
                  that are scoped differently (see report §11, open item).
                  When a filter is on, the label says so — "this week" alone
                  would describe a total the grid is no longer showing. */}
              {view !== 'list' && (
                <span>{(gridView === 'day'
                  ? (searchActive ? T('dayMatches') : T('dayTotal'))
                  : (searchActive ? T('weekMatches') : T('weekTotal')))}{' '}
                  {appointments.length}</span>
              )}
            </>}
            actions={<>
              <Button variant='outline' size='sm' aria-label={T('prev')}
                onClick={() => setAnchor(shiftAnchor(gridView, anchor, -1))}>‹</Button>
              <Button variant='outline' size='sm'
                onClick={() => setAnchor(today)}>{T('today')}</Button>
              <Button variant='outline' size='sm' aria-label={T('next')}
                onClick={() => setAnchor(shiftAnchor(gridView, anchor, 1))}>›</Button>
              <div role='group' aria-label={T('view')} className='flex'>
                {['week', 'day', 'list'].map((v) => (
                  <Button key={v} size='sm' aria-pressed={view === v}
                    variant={view === v ? 'primary' : 'outline'}
                    onClick={() => setView(v)}>{T(v)}</Button>
                ))}
              </div>
              {canBook && <Button size='sm' onClick={() => openBooking()}>{T('bk')}</Button>}
              {canBook && (
                <Button size='sm' variant='outline'
                  onClick={() => {
                    setBookError('');
                    setWalk({ patient: null, doctorId: doctorId || (doctors[0] && doctors[0].id) || '', notes: '',
                      /* Q1: empty until the arrival turns out to be outside every
                         published session — then the server requires it. */
                      reason: '',
                      symptoms: { ids: [], texts: [] }, onset: '', onsetNote: '' });
                  }}>{T('wi')}</Button>
              )}
            </>}
          />

          <Toolbar label={T('filters')} end={<>
            {isFiltered(query) && (
              <Button size='sm' variant='ghost' onClick={resetFilters}>{T('clearFilters')}</Button>
            )}
            {view === 'list' && (
              <Filter label={T('pageSize')} htmlFor='appt-page-size' className='w-24'>
                <Select id='appt-page-size' value={query.limit}
                  onChange={(e) => setQuery((q) => setLimit(q, Number(e.target.value)))}>
                  {LIST_PAGE_SIZES.map((n) => <option key={n} value={n}>{n}</option>)}
                </Select>
              </Filter>
            )}
          </>}>
            <SearchInput id='appt-search' value={searchText} onChange={setSearchText}
              placeholder={T('searchAppt')} label={T('searchAppt')}
              className='w-full sm:w-72' />
            <Filter label={T('d')} htmlFor='appt-doctor' className='w-44'>
              <Select id='appt-doctor' value={doctorId}
                onChange={(e) => setDoctor(e.target.value)}>
                <option value=''>{T('allDoctors')}</option>
                {doctors.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </Select>
            </Filter>
            <Filter label={T('st')} htmlFor='appt-status' className='w-44'>
              <Select id='appt-status' value={query.status}
                onChange={(e) => setQuery((q) => setFilter(q, 'status', e.target.value))}>
                <option value=''>{T('allStatus')}</option>
                {LIFECYCLE.map((s) => (
                  <option key={s} value={s}>{statusLabel(s, locale())}</option>
                ))}
              </Select>
            </Filter>
            {branches.length > 1 && (
              <Filter label={T('branch')} htmlFor='appt-branch' className='w-44'>
                <BranchSelect id='appt-branch' branches={branches} value={query.branch_id}
                  onChange={(v) => setQuery((q) => setFilter(q, 'branch_id', v))}
                  allowAll allLabel={T('allBranches')} label={T('branch')} />
              </Filter>
            )}
          </Toolbar>

          {/* D-2 — the search reached past the dates on screen.  The calendar
              says how many and where, and offers one click to the nearest other
              date; the List view is offered too, because "show me all of them"
              is a legitimate next move.  Counts only: no name ever appears here
              that the calendar has not been authorised to fetch. */}
          {view !== 'list' && matchesSummary && matchesSummary.outOfRange > 0 && (
            <div className='appt-matches' role='status' aria-live='polite'>
              <span>{withNumbers(T(matchesBannerKey(matchesSummary)),
                { n: matchesSummary.outOfRange, d: matchesSummary.otherDateCount })}</span>
              {matchesSummary.truncated && <span>{T('otherDatesTruncated')}</span>}
              {nearestOther && (
                <Button size='sm' variant='outline'
                  onClick={() => setAnchor(nearestOther)}>
                  {T('gotoNearest')} — {formatDayLong(nearestOther, locale())}
                </Button>
              )}
              <Button size='sm' variant='ghost' onClick={() => setView('list')}>
                {T('seeAllMatches')}
              </Button>
            </div>
          )}
          {view !== 'list' && matchesBusy && (
            <div className='sr-only' role='status' aria-live='polite'>{T('searchingOtherDates')}</div>
          )}

          {notice && <div className='success'>{notice}</div>}
          {error && <div className='error'>{error}</div>}

          {view === 'list' ? (
            <div>
              {listError && <div className='error' role='alert'>{listError}</div>}
              {list.items === null && listBusy ? (
                <div className='loading'>{T('loading')}</div>
              ) : listError && pageItems.length === 0 ? null : list.total === 0 ? (
                <EmptyState icon={SearchIcon} title={T('noResults')} hint={T('noResultsHint')}
                  action={isFiltered(query) ? (
                    <Button size='sm' variant='outline'
                      onClick={resetFilters}>{T('clearFilters')}</Button>
                  ) : undefined} />
              ) : (
                <>
                  <div className='overflow-x-auto'>
                    <table className='w-full border-collapse text-sm'>
                      <thead>
                        <tr className='border-b border-border'>
                          <Th label={T('tk')} />
                          <SortTh column='patient' label={T('p')} query={query} onSort={sortBy} />
                          <SortTh column='doctor' label={T('d')} query={query} onSort={sortBy} />
                          <SortTh column='date' label={T('dt')} query={query} onSort={sortBy} />
                          <Th label={T('tm')} />
                          <SortTh column='status' label={T('st')} query={query} onSort={sortBy} />
                          <Th label={T('actions')} />
                        </tr>
                      </thead>
                      <tbody>
                        {pageItems.map((a) => {
                          const bad = a.status === 'CANCELLED' || a.status === 'NO_SHOW';
                          return (
                            <tr key={a.id}
                              className={'border-b border-border last:border-0'
                                + (bad ? ' text-muted-foreground' : '')}>
                              <td className='px-2 py-1.5 font-mono text-xs'>{a.token_number || '-'}</td>
                              <td className='px-2 py-1.5'>
                                <button type='button' onClick={() => setDetail(a)}
                                  className='border-0 bg-transparent p-0 text-left font-medium hover:underline'>
                                  {listPatientName(a)}
                                </button>
                                {a.patient_mobile ? (
                                  <span className='block text-xs text-muted-foreground'>
                                    {a.patient_mobile}
                                  </span>
                                ) : null}
                              </td>
                              <td className='px-2 py-1.5'>{a.doctor_name || doctorName(a.doctor_id)}</td>
                              <td className='whitespace-nowrap px-2 py-1.5'>{a.appointment_date}</td>
                              <td className='whitespace-nowrap px-2 py-1.5'>{a.start_time || '-'}</td>
                              <td className='px-2 py-1.5'><StatusBadge status={a.status} size='sm' /></td>
                              <td className='px-2 py-1.5'>
                                <div className='flex flex-wrap gap-1'>
                                  {(ACTIONS[a.status] || []).map((act) => (
                                    <Button key={act} size='sm'
                                      variant={act === 'CANCELLED' ? 'danger' : 'secondary'}
                                      onClick={() => (act === 'CANCELLED'
                                        ? setCancelTarget(a) : changeStatus(a, act, ''))}>
                                      {actionLabel(act)}
                                    </Button>
                                  ))}
                                  {/* Check-in is offered on every row (the desk may
                                      need it whatever the status), but never twice:
                                      a transition list that already contains
                                      CHECKED_IN supplies the button above. */}
                                  {!(ACTIONS[a.status] || []).includes('CHECKED_IN') && (
                                    <Button size='sm' variant='outline'
                                      onClick={() => checkIn(a)}>{T('ci')}</Button>
                                  )}
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div className='mt-2 flex flex-wrap items-center justify-between gap-2 text-sm text-muted-foreground'>
                    <span role='status' aria-live='polite'>
                      {T('showing')} {firstRow}–{lastRow} · {T('total')}{' '}
                      <strong>{list.total}</strong>
                    </span>
                    <nav aria-label={T('pages')} className='flex items-center gap-1'>
                      <Button size='sm' variant='outline' disabled={list.page <= 1}
                        aria-label={T('prevPage')}
                        onClick={() => setQuery((q) => setPage(q, list.page - 1))}>‹</Button>
                      {pageWin.truncatedStart ? <span aria-hidden='true' className='px-1'>…</span> : null}
                      {pageWin.numbers.map((n) => (
                        <Button key={n} size='sm'
                          variant={n === list.page ? 'primary' : 'outline'}
                          aria-current={n === list.page ? 'page' : undefined}
                          aria-label={T('pages') + ' ' + n}
                          onClick={() => setQuery((q) => setPage(q, n))}>{n}</Button>
                      ))}
                      {pageWin.truncatedEnd ? <span aria-hidden='true' className='px-1'>…</span> : null}
                      <Button size='sm' variant='outline' disabled={list.page >= list.pages}
                        aria-label={T('nextPage')}
                        onClick={() => setQuery((q) => setPage(q, list.page + 1))}>›</Button>
                    </nav>
                  </div>
                </>
              )}
            </div>
          ) : loading ? (
            <div className='loading'>{T('loading')}</div>
          ) : (
            <AppointmentCalendar
              dates={range.dates}
              appointments={appointments}
              schedules={scopedSchedules}
              today={today}
              lang={locale()}
              labels={{ time: T('tm'), full: T('full'), closed: T('closed'),
                past: T('past'), bookAt: T('bk'), grid: T('t'), more: T('more'),
                /* Q1: a walk-in or outside-hours card says so on its face, so it
                   can never be read as an ordinary confirmed slot. */
                typeWalkIn: T(typeBadgeKey('walk_in')),
                typeUnscheduled: T(typeBadgeKey('unscheduled')) }}
              patientName={patientName}
              doctorName={(a) => a.doctor_name || doctorName(a.doctor_id)}
              /* The committed search term, not the keystroke buffer: what is
                 marked is what the server was asked for. */
              highlightTerm={query.q}
              showDoctor={!doctorId}
              showCapacity={Boolean(doctorId)}
              onSlotClick={(date, time) => openBooking({ date, time })}
              onEventClick={(appt) => setDetail(appt)}
              onDayClick={(iso) => { setAnchor(iso); setView('day'); }}
            />
          )}

          {book && (
            <Modal title={T('bk')} onClose={() => setBook(null)}
              footer={<>
                <button type='button' className='btn-outline'
                  onClick={() => setBook(null)}>{T('back')}</button>
                <button type='button' className='btn' disabled={saving}
                  onClick={saveBooking}>{saving ? T('saving') : T('save')}</button>
              </>}>
              {bookError && <div className='error'>{bookError}</div>}
              <div className='form-group'>
                <label>{T('p')}</label>
                <PatientSearch selected={book.patient}
                  onPick={(p) => setBook({ ...book, patient: p })}
                  onClear={() => setBook({ ...book, patient: null })} />
              </div>
              <div className='form-group'>
                <label>{T('d')}</label>
                <select value={book.doctorId} aria-label={T('d')}
                  onChange={(e) => setBook({ ...book, doctorId: e.target.value, time: '' })}>
                  <option value=''>—</option>
                  {doctors.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div className='form-group'>
                <label>{T('dt')}</label>
                <input type='date' value={book.date} aria-label={T('dt')}
                  onChange={(e) => setBook({ ...book, date: e.target.value, time: '' })} />
              </div>
              <div className='form-group'>
                <label>{T('chooseSlot')}</label>
                {slotChoices.length === 0 ? (
                  <>
                    <div style={{ fontSize:'0.8rem', color:'#8a6d00', marginBottom:4 }}>
                      {T('noSlots')}
                    </div>
                    {/* F-18 — the free-text field is a walk-in fallback, not a
                        slot, and the dialog says what the booking will then be.
                        Keeping the field is the documented current behaviour
                        (owner decision Q1 on outside-session bookings is still
                        open); presenting it as equivalent to a slot is not. */}
                    <input type='time' value={book.time} aria-label={T('tm')}
                      onChange={(e) => setBook({ ...book, time: e.target.value })} />
                    <div style={{ fontSize:'0.75rem', color:'#8a6d00', marginTop:4 }}>
                      {T('noSlotsHint')}
                    </div>
                  </>
                ) : (
                  <div className='flex flex-wrap' role='radiogroup' aria-label={T('chooseSlot')}
                    style={{ maxHeight: 190, overflowY: 'auto' }}>
                    {slotChoices.map((s) => {
                      /* F-19 — a full or nearly full slot says so in words; the
                         arithmetic alone read the same at 3/4 and 4/4. */
                      const word = seatsWord(s);
                      const seats = word
                        ? fill(T(word.key), { n: word.n })
                        : s.booked + '/' + s.capacity;
                      return (
                        <button key={s.start} type='button' role='radio'
                          aria-checked={book.time === s.start} disabled={s.full}
                          className={'btn btn-sm' + (book.time === s.start ? '' : ' btn-outline')}
                          style={{ opacity: s.full ? 0.45 : 1, margin: 1 }}
                          title={T('capacity') + ': ' + s.capacity + ' · ' + seats}
                          onClick={() => setBook({ ...book, time: s.start })}>
                          {s.start}{' '}
                          <span style={{ fontSize: '0.68rem' }}>{seats}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
              {/* Q1 — when nothing is published for this doctor/day the only honest
                  path is an outside-hours acceptance, which carries a reason.  The
                  field is asked for here, before the round trip, instead of letting
                  the server refuse a booking the dialog already knew was special. */}
              {bookingMode(slotChoices).requiresReason ? (
                <div className='form-group'>
                  <label htmlFor='book-override-reason'>{T('overrideReason')}</label>
                  <input id='book-override-reason' value={book.overrideReason || ''}
                    aria-label={T('overrideReason')}
                    placeholder={T('overrideReasonPlaceholder')}
                    aria-describedby='book-override-hint'
                    onChange={(e) => setBook({ ...book, overrideReason: e.target.value })} />
                  <small id='book-override-hint' className='muted'>{T('overrideHint')}</small>
                </div>
              ) : null}
              {/* F-19 — a day whose slots are all full is stated, not left to a row
                  of equally grey buttons. */}
              {bookingMode(slotChoices).mode === 'allFull' ? (
                <div style={{ fontSize: '0.78rem', color: '#8a6d00' }}>
                  {T('allFullHint')}
                </div>
              ) : null}
              {/* AMSDP-SYMPTOM-01 — optional, empty by default, and the
                  booking completes with nothing recorded here. */}
              <SymptomPicker
                id='book-symptoms'
                catalogue={catalogue.items}
                value={book.symptoms}
                maxSymptoms={catalogue.max_symptoms}
                lang={locale()}
                contextSpecialtyCodes={specialtyCodesFor(book.doctorId)}
                labels={symptomLabels}
                onChange={(next) => setBook({ ...book, symptoms: next })} />
              <OnsetField
                id='book-onset'
                value={book.onset}
                note={book.onsetNote}
                options={catalogue.onset_options}
                labels={symptomLabels}
                onChange={(code) => setBook({ ...book, onset: code, onsetNote: code ? book.onsetNote : '' })}
                onNoteChange={(text) => setBook({ ...book, onsetNote: text })} />
              <div className='form-group'>
                <label>{T('notes')}</label>
                <input value={book.notes} aria-label={T('notes')}
                  onChange={(e) => setBook({ ...book, notes: e.target.value })} />
              </div>
            </Modal>
          )}

          {detail && (
            <Modal title={T('detail')} onClose={() => setDetail(null)}
              footer={<>
                {(ACTIONS[detail.status] || []).map((act) => (
                  <button key={act} type='button'
                    className={'btn' + (act === 'CANCELLED' ? ' btn-danger' : '')}
                    onClick={() => (act === 'CANCELLED'
                      ? setCancelTarget(detail) : changeStatus(detail, act, ''))}>
                    {actionLabel(act)}
                  </button>
                ))}
                {!(ACTIONS[detail.status] || []).includes('CHECKED_IN') && (
                  <button type='button' className='btn btn-outline'
                    onClick={() => checkIn(detail)}>{T('ci')}</button>
                )}
                <button type='button' className='btn-outline'
                  onClick={() => setDetail(null)}>{T('back')}</button>
              </>}>
              <table style={{ boxShadow: 'none' }}>
                <tbody>
                  {[[T('p'), patientName(detail)], [T('d'), doctorName(detail.doctor_id)],
                    [T('dt'), detail.appointment_date], [T('tm'), detail.start_time || '-'],
                    [T('tk'), detail.token_number || '-'],
                    [T('st'), <StatusBadge key='st' status={detail.status} size='sm' />],
                    // Q1: the persisted type is always stated, and an outside-hours
                    // acceptance always shows the reason it was recorded with.
                    [T('typeLabel'), T(typeLabelKey(detail.appointment_type))],
                    [T('overrideReasonLabel'), detail.override_reason || '-'],
                    [T('loc'), detail.location_label || '-'],
                    [T('source'), detail.booking_source || '-'],
                    [T('sy'), symptomLine(detail)],
                    [T('onset'), onsetLine(detail)],
                    [T('notes'), detail.notes || '-']].map(([label, value]) => (
                    <tr key={label}>
                      <td style={{ fontWeight: 600, background: '#f6f9fc', width: '38%' }}>{label}</td>
                      <td>{value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Modal>
          )}

          {cancelTarget && (
            <ConfirmDialog title={T('cancelTitle')} message={T('cancelMsg')} requireReason
              onConfirm={(reason) => {
                const target = cancelTarget;
                setCancelTarget(null);
                changeStatus(target, 'CANCELLED', reason);
              }}
              onClose={() => setCancelTarget(null)} />
          )}

          {walk && (
            <Modal title={T('wi')} onClose={() => setWalk(null)}
              footer={<>
                <button type='button' className='btn-outline'
                  onClick={() => setWalk(null)}>{T('back')}</button>
                <button type='button' className='btn' disabled={saving}
                  onClick={registerWalkIn}>{saving ? T('saving') : T('save')}</button>
              </>}>
              {bookError && <div className='error'>{bookError}</div>}
              <div className='form-group'>
                <label>{T('p')}</label>
                <PatientSearch selected={walk.patient}
                  onPick={(p) => setWalk({ ...walk, patient: p })}
                  onClear={() => setWalk({ ...walk, patient: null })} />
              </div>
              <div className='form-group'>
                <label>{T('d')}</label>
                <select value={walk.doctorId} aria-label={T('d')}
                  onChange={(e) => setWalk({ ...walk, doctorId: e.target.value })}>
                  <option value=''>—</option>
                  {doctors.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <SymptomPicker
                id='walk-symptoms'
                catalogue={catalogue.items}
                value={walk.symptoms}
                maxSymptoms={catalogue.max_symptoms}
                lang={locale()}
                contextSpecialtyCodes={specialtyCodesFor(walk.doctorId)}
                labels={symptomLabels}
                onChange={(next) => setWalk({ ...walk, symptoms: next })} />
              <OnsetField
                id='walk-onset'
                value={walk.onset}
                note={walk.onsetNote}
                options={catalogue.onset_options}
                labels={symptomLabels}
                onChange={(code) => setWalk({ ...walk, onset: code, onsetNote: code ? walk.onsetNote : '' })}
                onNoteChange={(text) => setWalk({ ...walk, onsetNote: text })} />
              <div className='form-group'>
                <label htmlFor='walk-reason'>{T('walkInReason')}</label>
                <input id='walk-reason' value={walk.reason || ''}
                  aria-label={T('walkInReason')}
                  placeholder={T('overrideReasonPlaceholder')}
                  aria-describedby='walk-reason-hint'
                  onChange={(e) => setWalk({ ...walk, reason: e.target.value })} />
                {/* Q1: why the field exists, said before the refusal happens. */}
                <small id='walk-reason-hint' className='muted'>{T('walkInHint')}</small>
              </div>
              <div className='form-group'>
                <label>{T('notes')}</label>
                <input value={walk.notes} aria-label={T('notes')}
                  onChange={(e) => setWalk({ ...walk, notes: e.target.value })} />
              </div>
            </Modal>
          )}
        </div>
      </AppShell>
    </RequireLogin>
  );
}




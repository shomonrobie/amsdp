/* AppointmentCalendar — week/day booking grid.
 *
 * A thin rendering shell: every decision about which days, which times, whether
 * a cell is bookable, how many patients already occupy it and how many cards fit
 * comes from `lib/calendar/grid.js`, which `tests/calendar-grid.test.mjs`
 * covers. This file only turns that model into rows, cards and "+" buttons.
 *
 * Layout notes
 *  - CSS grid with a sticky time column, so it scrolls horizontally on a narrow
 *    receptionist screen instead of collapsing into unreadable columns.
 *  - A chip is a <button> and reads as a small card: patient name first, then
 *    `time · doctor`, then the status in words and colour, then the chamber.
 *    Opening an appointment is a real control, reachable by keyboard, never a
 *    click handler on a <div>.
 *  - A week cell is about three cards tall. Anything past that becomes a
 *    "+N more" control that opens the day view, so no appointment is ever
 *    silently clipped out of view.
 *  - When a search narrows the calendar, the chip marks the substring that
 *    matched (`lib/calendar/highlight.js`), so the card visibly answers the
 *    question it appeared for without hiding the rest of the name.
 */
import React from 'react';
import {
  bucketAppointments, cellState, chipLayout, gridTimes, dayLabel, moreLabel, todayIso,
} from '../lib/calendar/grid';
import { highlightSegments } from '../lib/calendar/highlight';
import { statusLabel } from '../lib/status';

/** Status → colour. Reads the same tokens as StatusBadge, so the calendar and
 *  the tables never drift apart. The value is a CSS colour: `hsl(var(--x))`,
 *  because tokens.css stores bare HSL channels. */
const TONE = {
  BOOKED: 'hsl(var(--status-scheduled))',
  AWAITING_CONFIRMATION: 'hsl(var(--warning))',
  CONFIRMED: 'hsl(var(--status-confirmed))',
  CHECKED_IN: 'hsl(var(--status-checked-in))',
  IN_QUEUE: 'hsl(var(--status-waiting))',
  IN_CONSULTATION: 'hsl(var(--status-in-consultation))',
  COMPLETED: 'hsl(var(--status-completed))',
  CANCELLED: 'hsl(var(--status-cancelled))',
  NO_SHOW: 'hsl(var(--status-no-show))',
  RESCHEDULED: 'hsl(var(--status-rescheduled))',
};

/** Friday and Saturday — the weekend a Bangladeshi chamber actually closes on. */
const WEEKEND_DAYS = [5, 6];
const isWeekend = (iso) => WEEKEND_DAYS.includes(new Date(`${iso}T00:00:00`).getDay());


const S = {
  // 15-minute slots across a whole week are tall; the grid scrolls inside its own
  // box with the day header and the time gutter pinned, like any booking calendar.
  wrap: { overflow: 'auto', maxHeight: '68vh', background: 'hsl(var(--card))', borderRadius: 6,
    boxShadow: '0 1px 3px rgba(0,0,0,0.08)', overscrollBehavior: 'contain',
    scrollbarGutter: 'stable' },
  grid: { display: 'grid', minWidth: 88 },
  corner: { position: 'sticky', left: 0, top: 0, zIndex: 5,
    background: 'hsl(var(--primary))', color: 'hsl(var(--primary-foreground))',
    padding: '0.5rem 0.4rem', fontSize: '0.75rem', display: 'flex',
    alignItems: 'flex-end', justifyContent: 'center' },
  head: { position: 'sticky', top: 0, zIndex: 4, background: 'hsl(var(--primary))',
    color: 'hsl(var(--primary-foreground))',
    border: 'none', borderLeft: '1px solid hsl(var(--primary-hover))',
    padding: '0.4rem 0.3rem', font: 'inherit', cursor: 'pointer', textAlign: 'center',
    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, minWidth: 0 },
  headToday: { background: 'hsl(var(--info))', boxShadow: 'inset 0 -3px 0 hsl(var(--warning))' },
  headDay: { fontSize: '0.95rem', fontWeight: 700, lineHeight: 1.1 },
  headWd: { fontSize: '0.7rem', opacity: 0.9 },
  headCount: { fontSize: '0.65rem', background: 'hsl(var(--primary-foreground) / 0.22)',
    borderRadius: 8, padding: '0 0.35rem' },
  timeCell: { position: 'sticky', left: 0, zIndex: 2, background: 'hsl(var(--muted))',
    color: 'hsl(var(--muted-foreground))',
    fontSize: '0.72rem', padding: '0.35rem 0.3rem', textAlign: 'right',
    borderTop: '1px solid hsl(var(--border))', display: 'flex', alignItems: 'flex-start',
    justifyContent: 'flex-end', fontVariantNumeric: 'tabular-nums' },
  cell: { borderTop: '1px solid hsl(var(--border))', borderLeft: '1px solid hsl(var(--border))',
    padding: 3, minHeight: 54, display: 'flex', flexDirection: 'column', gap: 3,
    position: 'relative' },
  cellOpen: { background: 'hsl(var(--card))' },
  cellClosed: { background: 'hsl(var(--muted))' },
  // Weekends and today never rely on colour alone: the closed/past tags still
  // spell out why a cell is unusable.
  cellWeekend: { background: 'hsl(var(--secondary))' },
  cellToday: { background: 'hsl(var(--accent))' },
  cellHour: { borderTop: '2px solid hsl(var(--border))' },
  /* A chip is a small card, patient first: the name is what the receptionist
     scans for, the time and doctor explain which clinic it belongs to, the
     status is spelled out in words as well as colour, and the chamber line says
     where to send the patient.  Everything wraps to one line each, so a long
     Bangla name never pushes the status out of the cell. */
  card: { display: 'flex', flexDirection: 'column', gap: 1, width: '100%', textAlign: 'left',
    border: 'none', borderLeft: '3px solid', borderRadius: 4, padding: '0.22rem 0.35rem',
    font: 'inherit', fontSize: '0.72rem', color: 'hsl(var(--foreground))', cursor: 'pointer',
    lineHeight: 1.25, background: 'hsl(var(--secondary))', minWidth: 0, fontFamily: 'inherit' },
  cardTop: { display: 'flex', alignItems: 'center', gap: 4, minWidth: 0 },
  cardName: { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
    flex: 1, fontWeight: 600 },
  cardToken: { flexShrink: 0, fontSize: '0.62rem',
    color: 'hsl(var(--muted-foreground))', background: 'hsl(var(--card))', borderRadius: 3,
    padding: '0 0.2rem' },
  cardMeta: { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
    fontSize: '0.65rem', color: 'hsl(var(--muted-foreground))' },
  cardStatus: { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
    fontSize: '0.62rem', fontWeight: 700 },
  cardWhere: { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
    fontSize: '0.62rem', color: 'hsl(var(--muted-foreground))' },
  dot: { width: 6, height: 6, borderRadius: '50%', flexShrink: 0 },
  /* "+N more" — a real control when the grid can open the day, a plain summary
     when it cannot.  Either way it states how many rows it stands for. */
  more: { width: '100%', border: '1px dashed hsl(var(--border))', borderRadius: 4,
    background: 'transparent', color: 'hsl(var(--primary))', fontSize: '0.62rem',
    lineHeight: 1.2, padding: '0.1rem 0.2rem', cursor: 'pointer', textAlign: 'center' },
  moreStatic: { width: '100%', border: 'none', background: 'transparent',
    color: 'hsl(var(--muted-foreground))', fontSize: '0.62rem', lineHeight: 1.2,
    padding: '0.1rem 0.2rem', textAlign: 'center' },
  dot: { width: 6, height: 6, borderRadius: '50%', flexShrink: 0 },
  add: { width: '100%', minHeight: 22, border: '1px dashed hsl(var(--border))', borderRadius: 4,
    background: 'hsl(var(--card))', color: 'hsl(var(--primary))', fontSize: '0.85rem', lineHeight: 1,
    cursor: 'pointer' },
  tag: { fontSize: '0.62rem', color: 'hsl(var(--muted-foreground))', textAlign: 'center' },
  capTag: { position: 'absolute', top: 2, right: 3, fontSize: '0.6rem',
    color: 'hsl(var(--muted-foreground))' },
};


/**
 * `text` with the part the search matched marked.
 *
 * The segments come from `lib/calendar/highlight.js` (substring match, never a
 * RegExp, never HTML), so a patient whose name contains `<` or `*` is rendered
 * as the text it is.  `<mark>` carries the semantic meaning; the stylesheet adds
 * the underline as a second, non-colour cue, and the chip's accessible name
 * stays the plain name so a screen reader hears it once.
 */
function Highlighted({ text, term }) {
  if (!term) return text;
  return (
    <>
      {highlightSegments(text, term).map((segment, i) => (segment.match
        ? <mark key={i} className="appt-cal-hit">{segment.text}</mark>
        : <React.Fragment key={i}>{segment.text}</React.Fragment>))}
    </>
  );
}

function Chip({ appt, color, patient, doctor, showDoctor, lang, onOpen, highlightTerm }) {
  const time = (appt.start_time || '').slice(0, 5);
  const cancelled = appt.status === 'CANCELLED' || appt.status === 'NO_SHOW';
  const status = statusLabel(appt.status, lang);
  const where = appt.location_label || '';
  // The tooltip keeps the machine status; the card states it in words, so the
  // chip reads correctly in Bangla and screenshot-diffs stay stable.
  const title = `${time} · ${patient}${appt.token_number ? ' · ' + appt.token_number : ''} · ${appt.status}`;
  return (
    <button type="button" className="appt-cal-chip"
      style={{ ...S.card, borderLeft: `3px solid ${color}`,
        background: cancelled ? 'hsl(var(--danger-soft))' : 'hsl(var(--secondary))',
        textDecoration: cancelled ? 'line-through' : 'none' }}
      title={title}
      aria-label={`${patient} · ${time}${showDoctor && doctor ? ' · ' + doctor : ''} · ${status}`}
      onClick={() => onOpen && onOpen(appt)}>
      <span style={S.cardTop}>
        <span style={{ ...S.dot, background: color }} aria-hidden="true" />
        <span style={S.cardName}><Highlighted text={patient} term={highlightTerm} /></span>
        {appt.token_number
          ? <span style={S.cardToken}><Highlighted text={appt.token_number} term={highlightTerm} /></span>
          : null}
      </span>
      <span style={S.cardMeta}>{showDoctor && doctor ? time + ' · ' + doctor : time}</span>
      <span style={{ ...S.cardStatus, color }}>{status}</span>
      {where ? <span style={S.cardWhere} title={where}>{where}</span> : null}
    </button>
  );
}

/** "+N more" — counts the rows the cell could not show, names them on hover. */
function MoreChip({ names, label, onOpen }) {
  if (!onOpen) {
    return <span style={S.moreStatic} title={names}>{label}</span>;
  }
  return (
    <button type="button" className="appt-cal-more" style={S.more}
      title={names} aria-label={`${label} — ${names}`} onClick={onOpen}>
      {label}
    </button>
  );
}

export default function AppointmentCalendar({
  dates, appointments = [], schedules = [], today, lang = 'bn', labels = {},
  onSlotClick, onEventClick, onDayClick, patientName, doctorName, showDoctor = false,
  showCapacity = true, chipLimit = 3, highlightTerm = '',
}) {
  const todayDate = today || todayIso();
  const byDate = React.useMemo(() => bucketAppointments(appointments), [appointments]);
  const times = React.useMemo(
    () => gridTimes({ schedules, dates, appointments }), [schedules, dates, appointments],
  );
  const resolvePatient = patientName || ((a) => (a.patient_name || a.patient_id || '').slice(0, 12));
  const resolveDoctor = doctorName || ((a) => a.doctor_id || '');

  return (
    <div style={S.wrap} className="appt-cal-wrap">
      <div role="grid" aria-label={labels.grid || labels.title || 'calendar'}
        style={{ ...S.grid, gridTemplateColumns: `88px repeat(${dates.length}, minmax(150px, 1fr))` }}>
        <div style={S.corner}>{labels.time}</div>
        {dates.map((iso) => {
          const dayTotal = byDate[iso] ? Object.values(byDate[iso]).reduce((n, l) => n + l.length, 0) : 0;
          const label = dayLabel(iso, lang);
          const [weekday, day] = label.split(' ');
          return (
            <button type="button" key={iso} onClick={onDayClick ? () => onDayClick(iso) : undefined}
              style={{ ...S.head, ...(iso === todayDate ? S.headToday : {}) }}
              aria-current={iso === todayDate ? 'date' : undefined}
              title={`${label} · ${dayTotal}`}>
              <span style={S.headWd}>{weekday}</span>
              <span style={S.headDay}>{day}</span>
              {dayTotal > 0 && <span style={S.headCount}>{dayTotal}</span>}
            </button>
          );
        })}

        {times.map((time) => (
          <React.Fragment key={time}>
            <div style={S.timeCell}>{time}</div>
            {dates.map((iso) => {
              const state = cellState({ iso, time, schedules, byDate, today: todayDate });
              const caption = state.booked + '/' + state.capacity;
              const isToday = iso === todayDate;
              // Closed wins over the ambient tints: a shut day must look shut.
              const tone = state.closed
                ? S.cellClosed
                : isToday
                  ? S.cellToday
                  : isWeekend(iso)
                    ? S.cellWeekend
                    : S.cellOpen;
              return (
                <div key={iso + time} role="gridcell"
                  className={'appt-cal-cell' + (state.closed ? ' is-closed' : '')}
                  style={{ ...S.cell, ...(time.endsWith(':00') ? S.cellHour : null), ...tone }}
                  aria-label={`${dayLabel(iso, lang)} ${time} — ${caption}`}>
                  {showCapacity && state.capacity > 1 && state.booked > 0 && (
                    <span style={S.capTag}>{caption}</span>
                  )}
                  {(() => {
                    // In the week view a cell is ~3 cards tall, so the rest is
                    // summarised rather than clipped.  The day view has the whole
                    // column, so it shows every card.
                    const layout = chipLayout(state.items,
                      { max: dates.length > 1 ? chipLimit : Infinity });
                    const hidden = state.items.slice(layout.shown.length);
                    return (
                      <>
                        {layout.shown.map((appt) => (
                          <Chip key={appt.id} appt={appt} color={TONE[appt.status] || '#607d8b'}
                            patient={resolvePatient(appt)} doctor={resolveDoctor(appt)}
                            showDoctor={showDoctor} lang={lang} onOpen={onEventClick}
                            highlightTerm={highlightTerm} />
                        ))}
                        {layout.overflow && (
                          <MoreChip
                            label={moreLabel(labels.more, layout.hidden)}
                            names={hidden.map(resolvePatient).join(', ')}
                            onOpen={onDayClick ? () => onDayClick(iso) : undefined} />
                        )}
                      </>
                    );
                  })()}
                  {state.bookable && (
                    <button type="button" className="appt-cal-add" style={S.add}
                      aria-label={`${labels.bookAt || 'Book'} ${dayLabel(iso, lang)} ${time}`}
                      onClick={() => onSlotClick && onSlotClick(iso, time)}>+</button>
                  )}
                  {!state.bookable && state.full && state.items.length === 0 && (
                    <span style={S.tag}>{labels.full}</span>
                  )}
                  {state.closed && state.items.length === 0 && (
                    <span style={S.tag}>{labels.closed}</span>
                  )}
                  {state.past && !state.closed && state.items.length === 0 && (
                    <span style={S.tag}>{labels.past}</span>
                  )}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}


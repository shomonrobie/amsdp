/* Status badge — consistent status coloring with text. */
export default function StatusBadge({ status, label }) {
  const active = ['active', 'waiting', 'in_consultation', 'CONFIRMED', 'CHECKED_IN', 'IN_QUEUE', 'BOOKED'].includes(status);
  const terminal = ['cancelled', 'no_show', 'CANCELLED', 'NO_SHOW'].includes(status);
  const cls = active ? 'badge badge-active' : terminal ? 'badge badge-inactive' : 'badge';
  return <span className={cls}>{label || status}</span>;
}
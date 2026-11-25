/* DataTable — loading/empty/error states + consistent table rendering. */
import { LoadingState, EmptyState, ErrorAlert } from './Alert';

/* `render(row, index)` and `rowProps(row, index)` exist because the index is the
 * row's position in the list being rendered: MP-29 found the queue's reorder
 * arrows calling `move(undefined, ±1)` — the cell renderer was only ever handed
 * the row, so the swap wrote `undefined` into the id payload and the server
 * refused it. Passing the index is what makes reorder — pointer or keyboard —
 * reference a real position.
 */
export default function DataTable({ columns, rows, loading, empty, error, rowKey = 'id', onRowClick, rowProps }) {
  if (loading) return <LoadingState />;
  if (error) return <ErrorAlert>{error}</ErrorAlert>;
  if (!rows || rows.length === 0) return <EmptyState msg={empty} />;
  return (
    <table>
      <thead>
        <tr>{columns.map((c, i) => <th key={i}>{typeof c === 'string' ? c : c.label}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((row, ri) => (
          <tr key={row[rowKey] || ri} onClick={onRowClick ? () => onRowClick(row) : undefined}
              style={onRowClick ? { cursor: 'pointer' } : undefined}
              {...(rowProps ? rowProps(row, ri) : null)}>
            {columns.map((c, i) => <td key={i}>{typeof c === 'string' ? row[c] : (c.render ? c.render(row, ri) : row[c.key])}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
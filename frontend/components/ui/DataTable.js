/* DataTable — loading/empty/error states + consistent table rendering. */
import { LoadingState, EmptyState, ErrorAlert } from './Alert';

export default function DataTable({ columns, rows, loading, empty, error, rowKey = 'id', onRowClick }) {
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
              style={onRowClick ? { cursor: 'pointer' } : undefined}>
            {columns.map((c, i) => <td key={i}>{typeof c === 'string' ? row[c] : (c.render ? c.render(row) : row[c.key])}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
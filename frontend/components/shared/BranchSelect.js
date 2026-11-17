/* BranchSelect — the branch picker every cross-branch screen uses.
 *
 * Branch choice is a *filter*, never an authorisation decision: the API scopes
 * results to the caller's token, and an out-of-scope id returns 404.  This
 * control only decides what to ask for.
 */
import React from 'react';
import { cn } from '../../lib/utils';

export default function BranchSelect({
  branches = [],
  value,
  onChange,
  label,
  id = 'amsdp-branch',
  allLabel,
  allowAll = false,
  disabled = false,
  className,
}) {
  return (
    <select
      id={id}
      aria-label={label}
      value={value}
      disabled={disabled}
      onChange={(event) => onChange && onChange(event.target.value)}
      className={cn(
        'h-9 rounded border border-input bg-card px-2 pr-6 text-base text-foreground',
        'focus-visible:border-ring',
        className,
      )}
    >
      {allowAll && <option value="">{allLabel || '—'}</option>}
      {branches.map((branch) => (
        <option key={branch.id} value={branch.id}>
          {branch.name}
        </option>
      ))}
    </select>
  );
}

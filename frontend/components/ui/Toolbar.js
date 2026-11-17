/* Toolbar — the filter row above a list.
 *
 * A labelled `role="toolbar"` container so keyboard and screen-reader users are
 * told that these controls act on the list below, not on the whole page.
 */
import React from 'react';
import { cn } from '../../lib/utils';

export default function Toolbar({ label, children, className, end }) {
  return (
    <div
      role="toolbar"
      aria-label={label}
      className={cn(
        'mb-2 flex flex-wrap items-center gap-2 rounded border border-border bg-card px-2.5 py-2 shadow-sm',
        className,
      )}
    >
      {children}
      {end && <div className="ml-auto flex flex-wrap items-center gap-2">{end}</div>}
    </div>
  );
}

/** A labelled inline filter: caption above the control, compact on a toolbar. */
export function Filter({ label, children, className, htmlFor }) {
  return (
    <label htmlFor={htmlFor} className={cn('flex min-w-0 flex-col gap-0.5', className)}>
      <span className="text-[0.68rem] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      {children}
    </label>
  );
}

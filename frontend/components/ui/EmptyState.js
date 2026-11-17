/* EmptyState — the "there is nothing here, and here is why" panel.
 *
 * An empty list is a normal, explainable state (no search results, branch not
 * configured, no sessions yet), never a blank white area.  `hint` says what to
 * do next; `action` offers the way to do it.
 */
import React from 'react';
import { cn } from '../../lib/utils';

export default function EmptyState({ icon: Icon, title, hint, action, className, compact = false }) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-2 rounded border border-dashed border-border bg-card text-center',
        compact ? 'px-3 py-4' : 'px-4 py-8',
        className,
      )}
    >
      {Icon && (
        <span aria-hidden="true" className="inline-flex h-9 w-9 items-center justify-center rounded-pill bg-secondary text-muted-foreground">
          <Icon size={17} />
        </span>
      )}
      <p className="m-0 text-base font-semibold text-foreground">{title}</p>
      {hint && <p className="m-0 max-w-prose text-sm text-muted-foreground">{hint}</p>}
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}

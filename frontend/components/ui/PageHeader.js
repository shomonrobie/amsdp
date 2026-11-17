/* PageHeader — title, one-line purpose, live meta and the screen's actions.
 *
 * Every operational page opens the same way, so a supervisor moving between
 * queue, doctors and facilities does not have to re-learn where the primary
 * action is.  `meta` holds counts/status that describe the data on screen.
 */
import React from 'react';
import { cn } from '../../lib/utils';

export default function PageHeader({ title, subtitle, meta, actions, className, children }) {
  return (
    <div className={cn('mb-3 flex flex-wrap items-end justify-between gap-3', className)}>
      <div className="min-w-0">
        <h1 className="m-0 text-2xl font-bold leading-tight text-foreground">{title}</h1>
        {subtitle && <p className="mt-0.5 mb-0 text-sm text-muted-foreground">{subtitle}</p>}
        {meta && <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">{meta}</div>}
        {children}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

/* Form controls — Input, Textarea, Select.
 *
 * Shared characteristics that matter at a reception desk:
 *  - 36 px minimum height (comfortable pointer target), 14 px text.
 *  - `invalid` drives a red border AND `aria-invalid`, so the state is not
 *    carried by colour alone.
 *  - `w-full` by default: forms are grid-laid-out by `Field`, never by guessing
 *    widths inline.
 *
 * Select is deliberately the *native* element.  It keeps the OS picker on
 * Android tablets, works without JavaScript focus management and is already
 * keyboard- and screen-reader-correct.  Radix Select would add a portal and a
 * custom keyboard model for no operational gain here.
 */
import React from 'react';
import { cn } from '../../lib/utils';

const base =
  'w-full rounded border border-input bg-card text-foreground placeholder:text-muted-foreground ' +
  'transition-colors box-border focus-visible:border-ring';

export const Input = React.forwardRef(function Input(
  { className, invalid = false, type = 'text', ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      type={type}
      aria-invalid={invalid || undefined}
      className={cn(base, 'h-9 px-2.5 text-base', invalid && 'border-destructive', className)}
      {...props}
    />
  );
});

export const Textarea = React.forwardRef(function Textarea(
  { className, invalid = false, rows = 3, ...props },
  ref,
) {
  return (
    <textarea
      ref={ref}
      rows={rows}
      aria-invalid={invalid || undefined}
      className={cn(base, 'px-2.5 py-2 text-base leading-normal', invalid && 'border-destructive', className)}
      {...props}
    />
  );
});

export const Select = React.forwardRef(function Select(
  { className, invalid = false, children, ...props },
  ref,
) {
  return (
    <select
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(base, 'h-9 px-2 text-base pr-6', invalid && 'border-destructive', className)}
      {...props}
    >
      {children}
    </select>
  );
});

export default Input;

/* Field / FormRow — label, hint, error, required marker and the aria wiring
 * between them.  Every form in AMSDP composes these so a label is never a bare
 * <label> without `htmlFor`, a hint is never just grey text, and an error is
 * announced (`role="alert"`) instead of only turning a border red.
 *
 * `Field` clones its single child to inject `id`, `aria-describedby` and
 * `invalid`, so call sites stay readable:
 *
 *   <Field label={t('fullName')} hint="…" error={err} required>
 *     <Input value={name} onChange={…} />
 *   </Field>
 */
import React from 'react';
import { cn } from '../../lib/utils';
import { fieldId } from '../../lib/utils';

export function Field({
  label, hint, error, required = false, children, htmlFor, id, className, hintId,
}) {
  const child = React.Children.only(children);
  const controlId = htmlFor || id || child.props.id || fieldId(child.props.name || label);
  const hintDomId = hint || error ? controlId + '-hint' : undefined;

  const control = React.cloneElement(child, {
    id: controlId,
    'aria-describedby': hintDomId,
    invalid: error ? true : child.props.invalid,
    'aria-required': required || child.props['aria-required'],
  });

  return (
    <div className={cn('flex min-w-0 flex-col items-start gap-1 text-left', className)}>
      <label htmlFor={controlId} className="text-left text-sm font-semibold text-foreground">
        {label}
        {required && <span aria-hidden="true" className="text-destructive"> *</span>}
        {required && <span className="sr-only"> (required)</span>}
      </label>
      {control}
      {hint && !error && (
        <span id={hintDomId} className="text-xs text-muted-foreground">
          {hint}
        </span>
      )}
      {error && (
        <span id={hintDomId} role="alert" className="text-xs font-semibold text-destructive">
          {error}
        </span>
      )}
      {!hint && !error && hintId && (
        // Reserved space keeps a two-column form from jumping when validation
        // messages appear.
        <span id={hintDomId} className="text-xs text-transparent select-none">&nbsp;</span>
      )}
    </div>
  );
}

/** A responsive form grid: 1 column on a phone, 2 on tablet, `cols` on desktop. */
export function FormRow({ children, cols = 2, className }) {
  const desktop = cols === 1 ? 'xl:grid-cols-1' : cols === 3 ? 'xl:grid-cols-3' : 'xl:grid-cols-2';
  return (
    <div className={cn('grid grid-cols-1 gap-x-4 gap-y-3 md:grid-cols-2', desktop, className)}>
      {children}
    </div>
  );
}

export default Field;

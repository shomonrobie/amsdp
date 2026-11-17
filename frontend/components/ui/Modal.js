/* Modal — compatibility wrapper over `Dialog`.
 *
 * Kept because several pages already import it (`doctors`, `facilities`,
 * `schedules`, `appointments`, `queue`, `ConfirmDialog`, …).  The API is
 * unchanged; the implementation is now the Radix-based `Dialog`, which removes
 * the focus-loss defect this component used to cause:
 *
 *   // before — re-ran on every keystroke because callers pass an inline arrow
 *   useEffect(() => { el.focus(); … }, [onClose]);
 *
 * A dialog that steals focus back to its container after the first character is
 * worse than no dialog at all: a receptionist cannot type a patient's name.
 * Radix traps focus inside the panel, focuses the first field on open, and
 * restores focus to the trigger on close — with no dependency on prop identity.
 *
 * New code should import `components/ui/Dialog` directly (it also supports
 * `size`, `description` and `initialFocusRef`).
 */
import React from 'react';
import Dialog from './Dialog';

export default function Modal({ title, onClose, children, footer, size = 'md', description, className, initialFocusRef }) {
  return (
    <Dialog
      open
      title={title}
      description={description}
      onClose={onClose}
      footer={footer}
      size={size}
      className={className}
      initialFocusRef={initialFocusRef}
    >
      {children}
    </Dialog>
  );
}
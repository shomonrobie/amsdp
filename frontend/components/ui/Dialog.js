/* Dialog — the accessible modal for AMSDP, built on Radix Dialog.
 *
 * Why Radix rather than another hand-rolled overlay: this is the shadcn/ui
 * foundation, and the previous local modal (`components/ui/Modal.js`, still
 * exported as a thin wrapper) had a focus defect that made every form inside it
 * unusable: its focus effect depended on the `onClose` prop, callers pass an
 * inline arrow, so every keystroke re-rendered the parent, re-ran the effect and
 * pulled the caret out of the input onto the dialog container.
 *
 * Radix supplies the behaviours that are easy to get wrong and expensive to
 * test: a real focus trap, focus restoration to the trigger on close, Escape and
 * overlay dismissal, `aria-modal`/`role="dialog"` wiring, `aria-labelledby` and
 * `aria-describedby`, and a scroll lock.  A description is always rendered
 * (visually hidden when the caller gives none) so the dialog is never announced
 * as an unnamed panel.
 */
import React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';

const SIZES = {
  sm: 'max-w-md',
  md: 'max-w-2xl',
  lg: 'max-w-4xl',
  xl: 'max-w-6xl',
  full: 'max-w-[96rem]',
};

/**
 * @param {object} props
 * @param {boolean} props.open
 * @param {() => void} props.onClose          called for Escape, overlay click, the X or any close request
 * @param {string} props.title                the dialog's accessible name
 * @param {string} [props.description]        optional supporting line
 * @param {React.ReactNode} props.children    body
 * @param {React.ReactNode} [props.footer]    action row, right-aligned
 * @param {'sm'|'md'|'lg'|'xl'|'full'} [props.size]
 * @param {React.RefObject} [props.initialFocusRef] element to focus instead of the first tabbable one
 * @param {string} [props.closeLabel]         accessible label for the X button
 */
export default function Dialog({
  open = true,
  onClose,
  title,
  description,
  children,
  footer,
  size = 'md',
  className,
  bodyClassName,
  initialFocusRef,
  closeLabel = 'Close',
  testId,
}) {
  const handleOpenChange = (next) => {
    if (!next) onClose && onClose();
  };

  return (
    <DialogPrimitive.Root open={!!open} onOpenChange={handleOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay
          data-testid="dialog-overlay"
          className="fixed inset-0 z-40 bg-[rgba(12,32,44,0.55)] animate-amsdp-in"
        />
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto p-3 sm:p-6 pointer-events-none">
          <DialogPrimitive.Content
            data-testid={testId}
            className={cn(
              'pointer-events-auto relative my-auto flex w-full flex-col rounded-lg border border-border',
              'bg-card text-card-foreground shadow-lg animate-amsdp-pop focus:outline-none',
              SIZES[size] || SIZES.md,
              className,
            )}
            onOpenAutoFocus={(event) => {
              if (initialFocusRef && initialFocusRef.current) {
                event.preventDefault();
                initialFocusRef.current.focus();
              }
            }}
          >
            <header className="flex items-start justify-between gap-4 border-b border-border px-4 py-3">
              <div className="min-w-0">
                <DialogPrimitive.Title className="text-xl font-bold leading-tight text-foreground">
                  {title}
                </DialogPrimitive.Title>
                <DialogPrimitive.Description
                  className={cn(
                    'mt-0.5 text-sm text-muted-foreground',
                    !description && 'sr-only',
                  )}
                >
                  {description || title}
                </DialogPrimitive.Description>
              </div>
              <DialogPrimitive.Close asChild>
                <button
                  type="button"
                  aria-label={closeLabel}
                  className="-mr-1 -mt-1 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  <X aria-hidden="true" size={16} />
                </button>
              </DialogPrimitive.Close>
            </header>

            <div className={cn('min-h-0 flex-1 px-4 py-3', bodyClassName)}>{children}</div>

            {footer && (
              <footer className="flex flex-wrap items-center justify-end gap-2 border-t border-border bg-muted px-4 py-3">
                {footer}
              </footer>
            )}
          </DialogPrimitive.Content>
        </div>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}

export { DialogPrimitive };

/* ConfirmDialog — confirmation, with a mandatory reason where the domain needs
 * one (cancel appointment, retire a chamber, record a missed turn).
 *
 * Built on the shared `Dialog`/`Button`/`Field` primitives so it inherits the
 * focus trap, the Escape/overlay dismissal and the typed `danger` action — and
 * so the reason field is a labelled, described, described-by-error control
 * instead of a bare `<input>` under a plain `<label>`.
 *
 * The reason field receives focus on open: the only thing the user can usefully
 * type is the reason, not the close button.
 */
import { useRef, useState } from 'react';
import Modal from './Modal';
import Button from './Button';
import { Field } from './Field';
import { Input } from './Input';
import { t } from '../../lib/i18n';

export default function ConfirmDialog({
  title,
  message,
  requireReason = false,
  onConfirm,
  onClose,
  confirmLabel,
  busy = false,
}) {
  const [reason, setReason] = useState('');
  const reasonRef = useRef(null);
  const canConfirm = !requireReason || reason.trim().length > 0;

  return (
    <Modal
      title={title}
      onClose={onClose}
      size="sm"
      initialFocusRef={requireReason ? reasonRef : undefined}
      footer={
        <>
          <Button variant="outline" onClick={onClose} disabled={busy}>
            {t('cancel')}
          </Button>
          <Button
            variant="danger"
            loading={busy}
            disabled={!canConfirm}
            onClick={() => onConfirm && onConfirm(requireReason ? reason.trim() : '')}
          >
            {confirmLabel || t('confirm')}
          </Button>
        </>
      }
    >
      <p className="m-0 text-base text-foreground">{message}</p>
      {requireReason && (
        <div className="mt-3">
          <Field label={t('reason')} required>
            <Input
              ref={reasonRef}
              name="reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder={t('reason')}
            />
          </Field>
        </div>
      )}
    </Modal>
  );
}

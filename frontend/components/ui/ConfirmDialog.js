/* ConfirmDialog — confirmation with optional reason. */
import { useState } from 'react';
import Modal from './Modal';
import { t } from '../../lib/i18n';

export default function ConfirmDialog({ title, message, requireReason, onConfirm, onClose }) {
  const [reason, setReason] = useState('');
  const canConfirm = !requireReason || reason.trim().length > 0;
  return (
    <Modal title={title} onClose={onClose}
      footer={
        <>
          <button className="btn-outline" onClick={onClose}>{t('cancel')}</button>
          <button className="btn btn-danger" disabled={!canConfirm}
            onClick={() => onConfirm(requireReason ? reason.trim() : '')}>
            {t('confirm')}
          </button>
        </>
      }>
      <p>{message}</p>
      {requireReason && (
        <div className="form-group mt-1">
          <label>Reason *</label>
          <input value={reason} onChange={(e) => setReason(e.target.value)}
                 placeholder={t('queue') + ' reason'} autoFocus />
        </div>
      )}
    </Modal>
  );
}
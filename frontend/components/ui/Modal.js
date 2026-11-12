/* Modal — accessible overlay dialog. */
import { useEffect, useRef } from 'react';
import { t } from '../../lib/i18n';

export default function Modal({ title, onClose, children, footer }) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (el) el.focus();
    const onKey = (e) => { if (e.key === 'Escape') onClose && onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={ref} className="modal" role="dialog" aria-modal="true" aria-label={title}
           tabIndex={-1} onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        <div>{children}</div>
        {footer && <div className="form-actions">{footer}</div>}
      </div>
    </div>
  );
}
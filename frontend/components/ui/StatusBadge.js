/* StatusBadge — a status pill with a label that is always readable.
 *
 * The old version carried its own two lists ("active" / "terminal") and printed
 * the raw enum when no label was supplied, so `IN_CONSULTATION` reached the
 * screen in SCREAMING_SNAKE.  It now resolves through `lib/status`, which owns
 * the whole vocabulary, tone and Bangla/English label.
 *
 * The `label` prop is still honoured: a page may add context ("আজ বাতিল").
 */
import React from 'react';
import Badge from './Badge';
import { statusMeta } from '../../lib/status';
import { getLocale } from '../../lib/i18n';

export default function StatusBadge({ status, label, size, className, locale }) {
  const lang = locale || getLocale();
  const meta = statusMeta(status, lang);
  return (
    <Badge tone={meta.tone} size={size} className={className} title={status || undefined}>
      {label || meta.label}
    </Badge>
  );
}
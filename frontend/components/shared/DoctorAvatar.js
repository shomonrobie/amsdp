/* DoctorAvatar — photograph when there is one, initials when there is not.
 *
 * A missing photo is normal (most chambers do not supply one), so the fallback
 * is a designed state, not a broken image: initials in a tinted circle with the
 * name as the accessible text.  `initials()` strips Bangla/English honorifics
 * ("ডা.", "Dr.") so "ডা. রহিম উদ্দিন" reads "রউ", not "ডা".
 */
import React from 'react';
import { initials } from '../../lib/facility';
import { cn } from '../../lib/utils';

const SIZES = {
  sm: 'h-7 w-7 text-[0.68rem]',
  md: 'h-9 w-9 text-sm',
  lg: 'h-14 w-14 text-lg',
};

export default function DoctorAvatar({ name, src, size = 'md', className }) {
  const box = cn(
    'inline-flex shrink-0 items-center justify-center rounded-pill bg-secondary font-bold text-primary',
    SIZES[size] || SIZES.md,
    className,
  );
  if (src) {
    return (
      <img
        src={src}
        alt={name ? `Photo of ${name}` : 'Doctor photo'}
        className={cn(box, 'object-cover')}
      />
    );
  }
  return (
    <span className={box} aria-hidden="true" title={name || undefined}>
      {initials(name)}
    </span>
  );
}

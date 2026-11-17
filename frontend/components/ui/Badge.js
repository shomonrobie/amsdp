/* Badge — one pill, every tone, always text + colour (never colour alone).
 *
 * Tones map 1:1 onto the semantic tokens in `styles/tokens.css`, so a status
 * means the same thing on the dashboard, the calendar, the queue and the
 * doctor profile.
 */
import React from 'react';
import { cva } from 'class-variance-authority';
import { cn } from '../../lib/utils';

export const badgeVariants = cva(
  'inline-flex items-center gap-1 whitespace-nowrap rounded-pill border px-2 py-0.5 ' +
    'text-xs font-semibold leading-tight',
  {
    variants: {
      tone: {
        neutral: 'border-border bg-neutral-soft text-neutral',
        info: 'border-[hsl(var(--info)/0.35)] bg-info-soft text-info',
        primary: 'border-[hsl(var(--primary)/0.35)] bg-accent text-primary',
        success: 'border-[hsl(var(--success)/0.35)] bg-success-soft text-success',
        warning: 'border-[hsl(var(--warning)/0.35)] bg-warning-soft text-warning',
        danger: 'border-[hsl(var(--destructive)/0.35)] bg-[hsl(var(--danger-soft))] text-destructive',
        outline: 'border-border bg-transparent text-muted-foreground',
        purple: 'border-[hsl(282_65%_35%/0.35)] bg-[hsl(282_60%_96%)] text-[hsl(282_65%_32%)]',
        teal: 'border-[hsl(174_100%_20%/0.35)] bg-[hsl(174_60%_94%)] text-[hsl(174_100%_18%)]',
        orange: 'border-[hsl(27_100%_47%/0.35)] bg-[hsl(27_100%_95%)] text-[hsl(27_100%_34%)]',
        slate: 'border-[hsl(200_11%_33%/0.35)] bg-[hsl(200_11%_94%)] text-[hsl(200_11%_30%)]',
        brown: 'border-[hsl(15_25%_33%/0.35)] bg-[hsl(15_25%_94%)] text-[hsl(15_25%_28%)]',
      },
      size: {
        sm: 'text-[0.68rem] px-1.5 py-0',
        md: '',
      },
    },
    defaultVariants: { tone: 'neutral', size: 'md' },
  },
);

export default function Badge({ tone, size, className, children, ...props }) {
  return (
    <span className={cn(badgeVariants({ tone, size }), className)} {...props}>
      {children}
    </span>
  );
}

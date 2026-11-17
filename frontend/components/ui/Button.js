/* Button — the shadcn/ui button for AMSDP.
 *
 * One visual language for every action in the product: `primary` for the single
 * committing action of a screen, `secondary` for the default, `outline`/`ghost`
 * for low-emphasis and toolbar actions, `danger` for destructive ones.
 *
 * `loading` keeps the label in place (no width jump) and sets `aria-busy`, so a
 * receptionist can see that the click registered even on a slow link.
 */
import React from 'react';
import { cva } from 'class-variance-authority';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium ' +
    'transition-colors select-none disabled:pointer-events-none disabled:opacity-55',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground shadow-sm hover:bg-primary-hover',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-accent',
        outline: 'border border-border bg-card text-foreground hover:bg-accent',
        ghost: 'bg-transparent text-foreground hover:bg-accent',
        danger: 'bg-destructive text-destructive-foreground shadow-sm hover:opacity-90',
        link: 'bg-transparent text-primary underline-offset-4 hover:underline px-0',
      },
      size: {
        sm: 'h-8 px-2.5 text-sm rounded-sm',
        md: 'h-9 px-3.5 text-base rounded',
        lg: 'h-10 px-5 text-lg rounded',
        icon: 'h-8 w-8 rounded',
      },
      block: { true: 'w-full' },
    },
    defaultVariants: { variant: 'secondary', size: 'md' },
  },
);

const Button = React.forwardRef(function Button(
  { variant, size, block, loading = false, className, children, type = 'button', disabled, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(buttonVariants({ variant, size, block }), className)}
      {...props}
    >
      {loading && <Loader2 aria-hidden="true" size={14} className="animate-spin" />}
      {children}
    </button>
  );
});

export default Button;

/* SearchInput — the one search box for every list in AMSDP.
 *
 * Controlled and synchronous: the parent owns the string, and filtering is done
 * locally or through an already-debounced fetch.  Nothing here re-creates the
 * input on each keystroke (the input is a single stable element), which is the
 * property a receptionist notices first.
 */
import React from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '../../lib/utils';

export default function SearchInput({
  value = '',
  onChange,
  placeholder = '',
  label,
  id = 'amsdp-search',
  className,
  disabled = false,
}) {
  return (
    <div className={cn('relative flex items-center', className)}>
      <Search
        aria-hidden="true"
        size={14}
        className="pointer-events-none absolute left-2.5 text-muted-foreground"
      />
      <input
        id={id}
        type="search"
        role="searchbox"
        aria-label={label || placeholder || 'Search'}
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(event) => onChange && onChange(event.target.value)}
        className={cn(
          'h-9 w-full rounded border border-input bg-card pl-8 pr-8 text-base text-foreground',
          'placeholder:text-muted-foreground focus-visible:border-ring',
        )}
      />
      {value ? (
        <button
          type="button"
          aria-label="Clear search"
          onClick={() => onChange && onChange('')}
          className="absolute right-1.5 inline-flex h-6 w-6 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <X aria-hidden="true" size={13} />
        </button>
      ) : null}
    </div>
  );
}

import { useCallback, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ChevronDown, Search } from 'lucide-react';

import { Input } from '@/components/Input';
import type { AuthorRead } from '@/services/bookApi';
import { classNames } from '@/services/string';

const norm = (s: string) =>
  s
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .trim();

const inputShellClass =
  'h-11 w-full rounded-xl border border-input bg-background pl-10 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50';

type MenuPos = { top: number; left: number; width: number };

type AuthorSearchSelectProps = {
  id: string;
  authors: AuthorRead[];
  value: number;
  onChange: (authorId: number) => void;
  /** Ex.: enquanto a lista de autores é carregada. */
  loading?: boolean;
  disabled?: boolean;
  allowEmpty?: boolean;
  placeholder?: string;
  emptyHint?: string;
  'aria-invalid'?: boolean;
};

const AuthorSearchSelect = ({
  id,
  authors,
  value,
  onChange,
  loading = false,
  disabled = false,
  allowEmpty = false,
  placeholder = 'Buscar por nome do autor…',
  emptyHint = 'Cadastre um autor em “Gerenciar autores”.',
  'aria-invalid': ariaInvalid,
}: AuthorSearchSelectProps) => {
  const listId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [highlight, setHighlight] = useState(0);
  const [menuPos, setMenuPos] = useState<MenuPos | null>(null);

  const selected = useMemo(() => authors.find((a) => a.id === value) ?? null, [authors, value]);

  const syncQueryFromValue = useCallback(() => {
    setQuery(selected ? selected.name : '');
  }, [selected]);

  useEffect(() => {
    if (!open) {
      syncQueryFromValue();
    }
  }, [open, syncQueryFromValue, value, authors]);

  const filtered = useMemo(() => {
    const q = norm(query);
    if (!q) return authors;
    return authors.filter((a) => norm(a.name).includes(q));
  }, [authors, query]);

  useEffect(() => {
    setHighlight((h) => (filtered.length === 0 ? 0 : Math.min(h, filtered.length - 1)));
  }, [filtered.length]);

  const fieldLocked = disabled || loading;
  const showList = open && !fieldLocked && authors.length > 0;
  const catalogEmpty = !loading && authors.length === 0;
  const readOnlyMessage = loading ? 'Carregando autores…' : catalogEmpty ? emptyHint : null;

  const updateMenuPosition = useCallback(() => {
    if (!rootRef.current) return;
    const r = rootRef.current.getBoundingClientRect();
    setMenuPos({ top: r.bottom + 4, left: r.left, width: r.width });
  }, []);

  useLayoutEffect(() => {
    if (!showList) {
      setMenuPos(null);
      return;
    }
    updateMenuPosition();
  }, [showList, updateMenuPosition, query, filtered.length]);

  useEffect(() => {
    if (!showList) return;
    updateMenuPosition();
    const onScrollOrResize = () => updateMenuPosition();
    window.addEventListener('scroll', onScrollOrResize, true);
    window.addEventListener('resize', onScrollOrResize);
    return () => {
      window.removeEventListener('scroll', onScrollOrResize, true);
      window.removeEventListener('resize', onScrollOrResize);
    };
  }, [showList, updateMenuPosition]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (ev: MouseEvent) => {
      const t = ev.target as Node;
      if (rootRef.current?.contains(t)) return;
      if (listRef.current?.contains(t)) return;
      setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  const pick = (a: AuthorRead) => {
    onChange(a.id);
    setQuery(a.name);
    setOpen(false);
    inputRef.current?.blur();
  };

  const listContent =
    showList && menuPos ? (
      <ul
        ref={listRef}
        id={listId}
        role='listbox'
        style={{
          position: 'fixed',
          top: menuPos.top,
          left: menuPos.left,
          width: menuPos.width,
          zIndex: 10000,
        }}
        className='max-h-60 overflow-auto rounded-xl border border-border bg-card py-1 shadow-book'
      >
        {filtered.length === 0 ? (
          <li className='px-3 py-2 text-sm text-muted-foreground'>Nenhum autor corresponde à busca.</li>
        ) : (
          filtered.map((a, i) => (
            <li
              key={a.id}
              id={`${id}-opt-${a.id}`}
              role='option'
              aria-selected={a.id === value}
              className={classNames(
                'px-3 py-2.5 text-sm cursor-pointer border-l-2 border-transparent',
                i === highlight ? 'bg-secondary text-ink border-l-coral' : 'text-foreground hover:bg-secondary/80',
              )}
              onMouseEnter={() => setHighlight(i)}
              onMouseDown={(e) => {
                e.preventDefault();
                pick(a);
              }}
            >
              <span className='font-medium'>{a.name}</span>
            </li>
          ))
        )}
      </ul>
    ) : null;

  return (
    <div ref={rootRef} className='relative'>
      <Search className='pointer-events-none absolute left-3 top-1/2 z-[1] -translate-y-1/2 w-4 h-4 text-muted-foreground' aria-hidden />
      <Input
        ref={inputRef}
        id={id}
        role='combobox'
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete='list'
        aria-activedescendant={showList && filtered[highlight] ? `${id}-opt-${filtered[highlight].id}` : undefined}
        aria-invalid={ariaInvalid}
        disabled={fieldLocked || catalogEmpty}
        value={readOnlyMessage ?? query}
        readOnly={readOnlyMessage != null}
        placeholder={placeholder}
        onChange={(ev) => {
          const v = ev.target.value;
          setQuery(v);
          setOpen(true);
          if (allowEmpty && v.trim() === '') {
            onChange(0);
          }
        }}
        onFocus={() => {
          if (fieldLocked || catalogEmpty) return;
          setOpen(true);
          if (selected) {
            setQuery(selected.name);
          }
        }}
        onKeyDown={(ev) => {
          if (fieldLocked || catalogEmpty) return;
          if (!showList) {
            if (ev.key === 'ArrowDown' || ev.key === 'Enter') {
              ev.preventDefault();
              setOpen(true);
            }
            return;
          }
          if (ev.key === 'Escape') {
            ev.preventDefault();
            setOpen(false);
            syncQueryFromValue();
            return;
          }
          if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            setHighlight((h) => (filtered.length === 0 ? 0 : (h + 1) % filtered.length));
            return;
          }
          if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            setHighlight((h) => (filtered.length === 0 ? 0 : (h - 1 + filtered.length) % filtered.length));
            return;
          }
          if (ev.key === 'Enter' && filtered[highlight]) {
            ev.preventDefault();
            pick(filtered[highlight]);
          }
        }}
        className={classNames(inputShellClass, readOnlyMessage && 'text-muted-foreground')}
      />
      <ChevronDown
        className={classNames(
          'pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground transition-transform',
          showList && 'rotate-180',
        )}
        aria-hidden
      />

      {typeof document !== 'undefined' && listContent ? createPortal(listContent, document.body) : null}
    </div>
  );
};

export default AuthorSearchSelect;

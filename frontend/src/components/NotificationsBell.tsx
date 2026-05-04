import { Bell } from 'lucide-react';

import Button from '@/components/Button';
import { useNotificationsPanel } from '@/hooks/useNotificationsPanel';
import { formatNotificationWhen } from '@/lib/localeDateFormat';

const NotificationsBell = () => {
  const { token, wrapRef, open, setOpen, items, unread, loading, onMarkAllRead, onClearAll } =
    useNotificationsPanel();

  if (!token) return null;

  return (
    <div className='relative' ref={wrapRef}>
      <button
        type='button'
        className='relative w-12 h-12 rounded-full bg-card border border-border flex items-center justify-center hover:bg-secondary'
        title='Notificações'
        aria-expanded={open}
        aria-haspopup='dialog'
        onClick={() => setOpen((o) => !o)}
      >
        <Bell className='w-5 h-5 text-ink' />
        {unread > 0 && (
          <span className='absolute -top-0.5 -right-0.5 min-w-[1.125rem] h-[1.125rem] px-1 rounded-full bg-coral text-cream text-[10px] font-semibold flex items-center justify-center'>
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          className='absolute right-0 top-full mt-2 w-[min(100vw-2rem,22rem)] max-h-[min(70vh,24rem)] overflow-hidden rounded-2xl border border-border bg-card shadow-lg z-50 flex flex-col'
          role='dialog'
          aria-label='Notificações'
        >
          <div className='flex items-center justify-between gap-2 px-4 py-3 border-b border-border'>
            <span className='text-sm font-medium text-ink'>Notificações</span>
            <div className='flex items-center gap-1.5 shrink-0'>
              {items.some((x) => !x.read_at) && (
                <Button
                  type='button'
                  colorSchema='secondary'
                  className='text-xs h-8 px-3 rounded-lg'
                  onClick={() => void onMarkAllRead()}
                >
                  Marcar lidas
                </Button>
              )}
              {items.length > 0 && (
                <Button
                  type='button'
                  colorSchema='secondary'
                  className='text-xs h-8 px-3 rounded-lg text-coral border-coral/40 hover:bg-coral/10'
                  onClick={() => void onClearAll()}
                >
                  Limpar tudo
                </Button>
              )}
            </div>
          </div>
          <div className='overflow-y-auto flex-1'>
            {loading && <p className='text-sm text-muted-foreground px-4 py-6'>Carregando…</p>}
            {!loading && items.length === 0 && (
              <p className='text-sm text-muted-foreground px-4 py-6'>Nenhuma notificação ainda.</p>
            )}
            {!loading &&
              items.map((n) => (
                <div
                  key={n.id}
                  className={
                    n.read_at
                      ? 'px-4 py-3 border-b border-border/60 text-muted-foreground'
                      : 'px-4 py-3 border-b border-border/60 bg-secondary/40'
                  }
                >
                  <p className='text-sm font-medium text-ink'>{n.title}</p>
                  <p className='text-xs text-muted-foreground mt-0.5'>{formatNotificationWhen(n.created_at)}</p>
                  <p className='text-sm mt-2 leading-snug whitespace-pre-wrap'>{n.body}</p>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationsBell;

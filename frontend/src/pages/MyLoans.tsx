import { Link } from 'react-router-dom';
import { ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react';

import AdminFeedbackModal from '@/components/AdminFeedbackModal';
import Button from '@/components/Button';
import { useMyLoansPage } from '@/hooks/useMyLoansPage';
import { formatDateShortPtBr } from '@/lib/localeDateFormat';

const MyLoans = () => {
  const {
    filter,
    setFilter,
    page,
    setPage,
    items,
    pages,
    loading,
    error,
    loanActionId,
    resCancelId,
    feedback,
    setFeedback,
    reservations,
    resLoading,
    onReturn,
    onRenew,
    onCancelReservation,
    formatLoanTimeline,
    renewalExtraDays,
  } = useMyLoansPage();

  const canPrev = page > 1;
  const canNext = page < pages;

  return (
    <div className='p-6 lg:p-10 max-w-3xl w-full mx-auto'>
      <Link
        to='/home'
        className='inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-ink mb-8'
      >
        <ArrowLeft className='w-4 h-4' />
        Voltar
      </Link>
      <h1 className='font-serif text-4xl text-ink mb-2'>Seus empréstimos</h1>
      <p className='text-muted-foreground mb-6'>Livros com você agora e histórico.</p>

      <div className='flex flex-wrap gap-2 mb-8'>
        <Button
          type='button'
          colorSchema={filter === 'active' ? 'primary' : 'secondary'}
          className='rounded-full'
          onClick={() => setFilter('active')}
        >
          Em andamento
        </Button>
        <Button
          type='button'
          colorSchema={filter === 'all' ? 'primary' : 'secondary'}
          className='rounded-full'
          onClick={() => setFilter('all')}
        >
          Todos
        </Button>
      </div>

      {error && (
        <p className='text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-xl px-4 py-3 mb-6'>
          {error}
        </p>
      )}

      {loading ? (
        <p className='text-muted-foreground'>Carregando…</p>
      ) : items.length === 0 ? (
        <p className='text-muted-foreground'>
          {filter === 'active' ? 'Nenhum empréstimo ativo no momento.' : 'Nenhum empréstimo registrado.'}
        </p>
      ) : (
        <ul className='space-y-4'>
          {items.map((loan) => {
            const title = loan.book_title ?? `Livro #${loan.book_id}`;
            const author = loan.author_name;
            const timeline = formatLoanTimeline(loan.due_at, loan.returned_at, loan.is_overdue);
            const busy = loanActionId === loan.id;
            const canRenew =
              loan.is_active && !loan.is_overdue && loan.renewal_count < 1 && !loan.returned_at;

            return (
              <li
                key={loan.id}
                className='bg-card border border-border rounded-2xl p-5 flex flex-col gap-4'
              >
                <div className='flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3'>
                  <div className='min-w-0'>
                    <Link
                      to={`/livro/${loan.book_id}`}
                      className='font-serif text-lg text-ink hover:text-coral transition-colors'
                    >
                      {title}
                    </Link>
                    {author && <p className='text-sm text-coral mt-0.5'>{author}</p>}
                    <p className='text-sm text-muted-foreground mt-2'>
                      Retirada {formatDateShortPtBr(loan.borrowed_at)} · Devolução prevista {formatDateShortPtBr(loan.due_at)}
                    </p>
                    {loan.returned_at && (
                      <p className='text-xs text-muted-foreground mt-1'>Devolvido em {formatDateShortPtBr(loan.returned_at)}</p>
                    )}
                    {loan.is_active &&
                      loan.projected_fine_brl != null &&
                      Number.parseFloat(String(loan.projected_fine_brl)) > 0 && (
                        <p className='text-sm font-medium text-amber-900 mt-2'>
                          Multa se devolver hoje: R${' '}
                          {Number.parseFloat(String(loan.projected_fine_brl)).toLocaleString('pt-BR', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}{' '}
                          <span className='text-xs text-muted-foreground font-normal'>(R$ 2,00/dia civil)</span>
                        </p>
                      )}
                    {loan.returned_at &&
                      loan.fine_amount != null &&
                      Number.parseFloat(String(loan.fine_amount)) > 0 && (
                        <p className='text-sm font-medium text-coral mt-2'>
                          Multa por atraso: R${' '}
                          {Number.parseFloat(String(loan.fine_amount)).toLocaleString('pt-BR', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </p>
                      )}
                    <p
                      className={
                        loan.is_active && loan.is_overdue
                          ? 'text-sm font-medium text-coral mt-2'
                          : 'text-sm text-ink/80 mt-2'
                      }
                    >
                      {timeline}
                    </p>
                  </div>
                  <div className='flex flex-wrap gap-2 shrink-0'>
                    {loan.is_active && (
                      <span className='text-xs font-medium px-2 py-1 rounded-full bg-teal/15 text-teal'>Ativo</span>
                    )}
                    {!loan.is_active && (
                      <span className='text-xs font-medium px-2 py-1 rounded-full bg-secondary text-muted-foreground'>
                        Devolvido
                      </span>
                    )}
                    {loan.is_overdue && loan.is_active && (
                      <span className='text-xs font-medium px-2 py-1 rounded-full bg-coral/15 text-coral'>Atrasado</span>
                    )}
                  </div>
                </div>
                {loan.is_active && (
                  <div className='flex flex-wrap gap-2 pt-1 border-t border-border/60'>
                    <Button
                      type='button'
                      colorSchema='primary'
                      className='rounded-xl'
                      loading={busy}
                      onClick={() => void onReturn(loan)}
                    >
                      Devolver
                    </Button>
                    {canRenew && (
                      <Button
                        type='button'
                        colorSchema='secondary'
                        className='rounded-xl'
                        loading={busy}
                        disabled={busy}
                        onClick={() => void onRenew(loan)}
                      >
                        Renovar (+{renewalExtraDays} dias)
                      </Button>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {!loading && !error && pages > 1 && (
        <nav className='flex flex-wrap items-center justify-center gap-3 pt-8' aria-label='Paginação'>
          <Button
            type='button'
            colorSchema='secondary'
            className='gap-1 rounded-xl'
            disabled={!canPrev}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            <ChevronLeft className='w-4 h-4' /> Anterior
          </Button>
          <span className='text-sm text-muted-foreground px-2'>
            {page} / {pages}
          </span>
          <Button
            type='button'
            colorSchema='secondary'
            className='gap-1 rounded-xl'
            disabled={!canNext}
            onClick={() => setPage((p) => p + 1)}
          >
            Próxima <ChevronRight className='w-4 h-4' />
          </Button>
        </nav>
      )}

      <section className='mt-14 pt-10 border-t border-border'>
        <h2 className='font-serif text-2xl text-ink mb-2'>Reservas na fila</h2>
        <p className='text-sm text-muted-foreground mb-4'>
          Livros emprestados em que você entrou na fila de espera. Quando for sua vez, empreste a partir da página do
          livro; se estiver com hold por limite de empréstimos, devolva um exemplar e o empréstimo entra
          automaticamente.
        </p>
        {resLoading && <p className='text-sm text-muted-foreground'>Carregando reservas…</p>}
        {!resLoading && reservations.length === 0 && (
          <p className='text-sm text-muted-foreground'>Nenhuma reserva pendente.</p>
        )}
        {!resLoading && reservations.length > 0 && (
          <ul className='space-y-3'>
            {reservations.map((r) => {
              const rTitle = r.book_title ?? `Livro #${r.book_id}`;
              return (
                <li
                  key={r.id}
                  className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-2xl border border-border bg-card px-4 py-3'
                >
                  <div>
                    <Link
                      to={`/livro/${r.book_id}`}
                      className='font-serif text-lg text-ink hover:text-coral transition-colors'
                    >
                      {rTitle}
                    </Link>
                    {r.author_name && <p className='text-sm text-coral mt-0.5'>{r.author_name}</p>}
                    <p className='text-xs text-muted-foreground mt-1'>
                      Na fila desde {formatDateShortPtBr(r.created_at)}
                      {r.queue_position != null && r.status !== 'hold' && (
                        <>
                          {' · '}
                          <span className='text-ink/90'>Posição na fila: {r.queue_position}º</span>
                        </>
                      )}
                      {r.status === 'hold' && r.hold_until && (
                        <span className='block mt-1 text-amber-900'>
                          Libere um empréstimo e pegue o livro até{' '}
                          {new Date(r.hold_until).toLocaleString('pt-BR', {
                            day: '2-digit',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      )}
                    </p>
                  </div>
                  <Button
                    type='button'
                    colorSchema='secondary'
                    className='rounded-xl shrink-0 text-destructive border-destructive/25 hover:bg-destructive/10'
                    loading={resCancelId === r.id}
                    disabled={resCancelId != null && resCancelId !== r.id}
                    onClick={() => void onCancelReservation(r)}
                  >
                    Cancelar reserva
                  </Button>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <AdminFeedbackModal feedback={feedback} onDismiss={() => setFeedback(null)} idPrefix='my-loans-feedback' />
    </div>
  );
};

export default MyLoans;

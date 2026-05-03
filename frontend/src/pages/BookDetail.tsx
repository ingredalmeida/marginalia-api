import { ArrowLeft, BookMarked, CalendarClock, CheckCircle2, Loader2 } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import AdminFeedbackModal from '@/components/AdminFeedbackModal';
import BookHandCover from '@/components/BookHandCover';
import Button from '@/components/Button';
import { ACERVO_CHIP } from '@/data/homeBrowse';
import { useBookDetail } from '@/hooks/useBookDetail';
import { classNames } from '@/services/string';

const BookDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const bookId = id ? Number.parseInt(id, 10) : NaN;

  const {
    userId,
    book,
    loading,
    error,
    myLoan,
    myReservation,
    queuePosition,
    queueTotal,
    ctxLoading,
    actionBusy,
    feedback,
    setFeedback,
    onBorrow,
    onReserve,
    onCancelReserve,
    onReturn,
    onRenew,
    canTryRenew,
    loanUi,
  } = useBookDetail(bookId);

  const chip = ACERVO_CHIP;
  const { LOAN_DEFAULT_DAYS, MAX_ACTIVE_LOANS_PER_USER, MAX_PENDING_RESERVATIONS_PER_USER, RENEWAL_EXTRA_DAYS } =
    loanUi;

  return (
    <main className='p-6 lg:p-10 max-w-6xl mx-auto'>
      <div className='mb-8'>
        <Button
          type='button'
          colorSchema='secondary'
          className='gap-2 border-0 bg-transparent shadow-none text-muted-foreground hover:text-ink -ml-2'
          onClick={() => navigate(-1)}
        >
          <ArrowLeft className='w-4 h-4' /> Voltar
        </Button>
      </div>

      {loading && (
        <p className='text-muted-foreground flex items-center gap-2'>
          <Loader2 className='w-4 h-4 animate-spin' /> Carregando…
        </p>
      )}
      {error && (
        <p className='text-coral mb-4'>
          {error}{' '}
          <Link to='/home' className='underline text-ink'>
            Ir para a home
          </Link>
        </p>
      )}

      {book && (
        <article className='space-y-10 animate-fade-up'>
          <div className='grid gap-8 md:grid-cols-[minmax(200px,280px)_1fr] md:gap-12 items-start'>
            <div className='relative aspect-[3/4] w-full max-w-[280px] mx-auto md:mx-0 rounded-2xl overflow-hidden shadow-book md:sticky md:top-24'>
              <BookHandCover bookId={book.id} title={book.title} chip={chip} emphasis />
            </div>

            <div className='space-y-6 text-ink min-w-0'>
              <header>
                <p className='text-xs tracking-[0.25em] text-muted-foreground mb-1'>{chip}</p>
                <h1 className='font-serif text-4xl sm:text-5xl text-balance leading-tight'>{book.title}</h1>
                <p className='text-lg text-coral mt-3 font-medium'>{book.author.name}</p>
              </header>

              <div className='flex flex-wrap gap-2'>
                <span
                  className={classNames(
                    'text-xs font-medium px-3 py-1 rounded-full border',
                    book.available
                      ? 'bg-teal/10 text-teal border-teal/25'
                      : 'bg-amber/10 text-amber-800 border-amber/25',
                  )}
                >
                  {book.available ? 'Disponível para empréstimo' : 'Exemplar emprestado'}
                </span>
                {book.isbn && (
                  <span className='text-xs px-3 py-1 rounded-full bg-card border border-border text-muted-foreground'>
                    ISBN {book.isbn}
                  </span>
                )}
                {book.publication_year != null && (
                  <span className='text-xs px-3 py-1 rounded-full bg-card border border-border text-muted-foreground'>
                    {book.publication_year}
                  </span>
                )}
              </div>

              <dl className='grid gap-4 sm:grid-cols-2 text-sm'>
                {book.publisher && (
                  <div>
                    <dt className='text-muted-foreground text-xs tracking-wider uppercase mb-1'>Editora</dt>
                    <dd>{book.publisher}</dd>
                  </div>
                )}
                <div className='sm:col-span-2 flex items-start gap-2 text-muted-foreground'>
                  <CalendarClock className='w-4 h-4 shrink-0 mt-0.5' />
                  <span>
                    Empréstimo padrão de <strong className='text-ink'>{LOAN_DEFAULT_DAYS} dias</strong>. Até{' '}
                    {MAX_ACTIVE_LOANS_PER_USER} livros ativos e até {MAX_PENDING_RESERVATIONS_PER_USER} reservas na fila
                    por pessoa. Renovação de +{RENEWAL_EXTRA_DAYS} dias, uma vez, nas regras do sistema.
                  </span>
                </div>
              </dl>

              {book.description && (
                <div>
                  <h2 className='text-xs tracking-[0.25em] text-muted-foreground mb-2'>Sobre</h2>
                  <p className='text-muted-foreground leading-relaxed whitespace-pre-wrap'>{book.description}</p>
                </div>
              )}
            </div>
          </div>

          <section className='pt-8 border-t border-border'>
            <div className='flex items-center gap-2 mb-4'>
              <BookMarked className='w-5 h-5 text-coral' />
              <h2 className='font-serif text-2xl text-ink'>Reserva e empréstimo</h2>
            </div>
            <p className='text-sm text-muted-foreground mb-6 max-w-2xl'>
              Quando o livro está com alguém, use a fila de reserva. Quando estiver disponível, você pode emprestar
              direto (se for a sua vez na fila, o sistema libera o empréstimo).
            </p>

            {ctxLoading && (
              <p className='text-sm text-muted-foreground flex items-center gap-2'>
                <Loader2 className='w-4 h-4 animate-spin' /> Atualizando situação do exemplar…
              </p>
            )}

            {!ctxLoading && userId != null && (
              <div className='flex flex-col gap-3 max-w-xl'>
                {myLoan?.is_active && (
                  <div className='rounded-2xl border border-border bg-card p-4 space-y-3'>
                    <p className='text-sm font-medium text-ink flex items-center gap-2'>
                      <CheckCircle2 className='w-4 h-4 text-teal' /> Você está com este exemplar.
                    </p>
                    <div className='flex flex-wrap gap-2'>
                      <Button
                        type='button'
                        colorSchema='primary'
                        className='rounded-xl'
                        loading={actionBusy}
                        onClick={() => void onReturn()}
                      >
                        Registrar devolução
                      </Button>
                      {canTryRenew && (
                        <Button
                          type='button'
                          colorSchema='secondary'
                          className='rounded-xl'
                          loading={actionBusy}
                          disabled={actionBusy}
                          onClick={() => void onRenew()}
                        >
                          Renovar (+{RENEWAL_EXTRA_DAYS} dias)
                        </Button>
                      )}
                    </div>
                    <Link to='/emprestimos' className='text-sm text-coral underline hover:text-ink'>
                      Ver em Meus empréstimos
                    </Link>
                  </div>
                )}

                {!myLoan?.is_active && book.available && (
                  <Button
                    type='button'
                    colorSchema='primary'
                    className='rounded-xl h-12 w-full sm:w-auto'
                    loading={actionBusy}
                    onClick={() => void onBorrow()}
                  >
                    Emprestar agora
                  </Button>
                )}

                {!myLoan?.is_active && !book.available && !myReservation && (
                  <Button
                    type='button'
                    colorSchema='secondary'
                    className='rounded-xl h-12 w-full sm:w-auto border-coral/30'
                    loading={actionBusy}
                    onClick={() => void onReserve()}
                  >
                    Entrar na fila de reserva
                  </Button>
                )}

                {!myLoan?.is_active && !book.available && myReservation && (
                  <div className='rounded-2xl border border-border bg-card p-4 space-y-3'>
                    <p className='text-sm text-ink'>
                      {myReservation.status === 'hold' ? (
                        <>
                          Você é o próximo na fila, mas precisa liberar um lugar na estante (máx. 3 empréstimos).
                          {myReservation.hold_until && (
                            <>
                              {' '}
                              <span className='text-amber-800'>
                                Prazo até{' '}
                                {new Date(myReservation.hold_until).toLocaleString('pt-BR', {
                                  day: '2-digit',
                                  month: 'short',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })}
                              </span>
                            </>
                          )}
                          {' '}
                          Devolva um dos seus empréstimos para liberar vaga: o título em hold será emprestado
                          automaticamente, ou use o botão abaixo quando já houver vaga.
                        </>
                      ) : (
                        <>
                          Você está na fila de reserva
                          {queuePosition != null && queueTotal != null
                            ? ` (posição ${queuePosition} de ${queueTotal})`
                            : '.'}
                        </>
                      )}
                    </p>
                    <div className='flex flex-wrap gap-2'>
                      {myReservation.status === 'hold' && (
                        <Button
                          type='button'
                          colorSchema='primary'
                          className='rounded-xl'
                          loading={actionBusy}
                          onClick={() => void onBorrow()}
                        >
                          Emprestar com a reserva
                        </Button>
                      )}
                      <Button
                        type='button'
                        colorSchema='secondary'
                        className='rounded-xl text-destructive border-destructive/30 hover:bg-destructive/10'
                        loading={actionBusy}
                        onClick={() => void onCancelReserve()}
                      >
                        Cancelar minha reserva
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {userId == null && (
              <p className='text-sm text-muted-foreground'>Faça login para reservar ou emprestar.</p>
            )}
          </section>
        </article>
      )}

      <AdminFeedbackModal feedback={feedback} onDismiss={() => setFeedback(null)} idPrefix='book-detail-feedback' />
    </main>
  );
};

export default BookDetail;

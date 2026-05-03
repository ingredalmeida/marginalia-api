import { ChevronLeft, ChevronRight, Search, Trash2 } from 'lucide-react';

import AdminFeedbackModal from '@/components/AdminFeedbackModal';
import AuthorSearchSelect from '@/components/AuthorSearchSelect';
import Button from '@/components/Button';
import { Input } from '@/components/Input';
import { Label } from '@/components/Label';
import { useAdminBooks } from '@/hooks/useAdminBooks';
import { adminTextareaClass } from '@/lib/adminFormStyles';
import { PAGE_SIZE } from '@/lib/pagination';
import { classNames } from '@/services/string';

const AdminBooks = () => {
  const {
    mainTab,
    setMainTab,
    authors,
    authorsLoading,
    bookTitle,
    setBookTitle,
    bookAuthorId,
    setBookAuthorId,
    bookDescription,
    setBookDescription,
    bookPublisher,
    setBookPublisher,
    bookIsbn,
    setBookIsbn,
    bookYear,
    setBookYear,
    bookSaving,
    page,
    setPage,
    searchInput,
    setSearchInput,
    data,
    error,
    loading,
    editBook,
    setEditBook,
    editBookTitle,
    setEditBookTitle,
    editBookAuthorId,
    setEditBookAuthorId,
    editBookDescription,
    setEditBookDescription,
    editBookPublisher,
    setEditBookPublisher,
    editBookIsbn,
    setEditBookIsbn,
    editBookYear,
    setEditBookYear,
    feedback,
    dismissFeedback,
    onCreateBook,
    openEdit,
    saveEdit,
    onDelete,
    pages,
    canPrev,
    canNext,
    q,
  } = useAdminBooks();

  return (
    <main className='p-6 lg:p-10 max-w-[1400px] mx-auto'>
      <header className='mb-8'>
        <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>ADMINISTRAÇÃO</p>
        <h1 className='font-serif text-4xl lg:text-5xl text-ink'>Gerenciar livros</h1>
        <p className='text-muted-foreground mt-2 max-w-2xl'>
          Cadastre novos títulos ou busque por nome do livro ou do autor para editar ou excluir.
        </p>
      </header>

      <div className='inline-flex bg-secondary rounded-full p-1 mb-8'>
        {(['cadastro', 'gerenciar'] as const).map((t) => (
          <button
            key={t}
            type='button'
            onClick={() => setMainTab(t)}
            className={classNames(
              'px-5 py-2 text-sm rounded-full transition-all',
              mainTab === t ? 'bg-ink text-cream shadow-soft' : 'text-muted-foreground',
            )}
          >
            {t === 'cadastro' ? 'Cadastro' : 'Gerenciar'}
          </button>
        ))}
      </div>

      {mainTab === 'cadastro' && (
        <section className='max-w-2xl animate-fade-up'>
          <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>NOVO LIVRO</p>
          <h2 className='font-serif text-2xl text-ink mb-6'>Cadastrar livro</h2>
          <form onSubmit={(e) => void onCreateBook(e)} className='bg-card border border-border rounded-2xl p-6 space-y-4'>
            <div className='space-y-2'>
              <Label htmlFor='bk-title'>Título</Label>
              <Input
                id='bk-title'
                value={bookTitle}
                onChange={(ev) => setBookTitle(ev.target.value)}
                className='h-11 rounded-xl'
                required
                minLength={1}
              />
            </div>
            <div className='space-y-2'>
              <Label htmlFor='bk-author'>Autor</Label>
              <AuthorSearchSelect
                id='bk-author'
                authors={authors}
                value={bookAuthorId}
                onChange={setBookAuthorId}
                loading={authorsLoading}
                allowEmpty
                placeholder='Buscar ou selecione um autor…'
              />
            </div>
            <div className='space-y-2'>
              <Label htmlFor='bk-desc'>Descrição (opcional)</Label>
              <textarea
                id='bk-desc'
                value={bookDescription}
                onChange={(ev) => setBookDescription(ev.target.value)}
                className={adminTextareaClass}
                rows={4}
              />
            </div>
            <div className='grid sm:grid-cols-2 gap-4'>
              <div className='space-y-2'>
                <Label htmlFor='bk-pub'>Editora (opcional)</Label>
                <Input id='bk-pub' value={bookPublisher} onChange={(ev) => setBookPublisher(ev.target.value)} className='h-11 rounded-xl' />
              </div>
              <div className='space-y-2'>
                <Label htmlFor='bk-isbn'>ISBN (opcional)</Label>
                <Input id='bk-isbn' value={bookIsbn} onChange={(ev) => setBookIsbn(ev.target.value)} className='h-11 rounded-xl' />
              </div>
              <div className='space-y-2 sm:col-span-2'>
                <Label htmlFor='bk-year'>Ano (opcional)</Label>
                <Input
                  id='bk-year'
                  inputMode='numeric'
                  value={bookYear}
                  onChange={(ev) => setBookYear(ev.target.value)}
                  className='h-11 rounded-xl max-w-xs'
                  placeholder='ex. 1977'
                />
              </div>
            </div>
            <Button
              type='submit'
              loading={bookSaving}
              disabled={bookSaving || authorsLoading || authors.length === 0 || bookAuthorId < 1}
              className='rounded-xl'
            >
              Cadastrar livro
            </Button>
          </form>
        </section>
      )}

      {mainTab === 'gerenciar' && (
        <section className='animate-fade-up space-y-8'>
          <div>
            <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>BUSCAR</p>
            <h2 className='font-serif text-2xl text-ink mb-4'>Filtrar livros</h2>
            <div className='relative max-w-xl'>
              <Search className='absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground' />
              <Input
                value={searchInput}
                onChange={(ev) => setSearchInput(ev.target.value)}
                placeholder='Título ou nome do autor…'
                className='h-12 pl-12 rounded-xl bg-card border-border'
                aria-label='Buscar livro'
              />
            </div>
            <p className='text-xs text-muted-foreground mt-2'>
              Deixe em branco para ver todos (com paginação). Com texto, a busca atualiza após um breve intervalo.
            </p>
          </div>

          {error && (
            <p className='text-sm text-coral mb-6 bg-coral/5 border border-coral/20 rounded-xl px-4 py-3'>{error}</p>
          )}

          {loading && <p className='text-sm text-muted-foreground mb-6'>Carregando…</p>}

          {data && !loading && (
            <>
              <div className='space-y-3 mb-8'>
                {data.items.map((b) => (
                  <div
                    key={b.id}
                    className='bg-card border border-border rounded-2xl p-5 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4'
                  >
                    <button type='button' onClick={() => openEdit(b)} className='min-w-0 flex-1 text-left'>
                      <p className='font-serif text-lg text-ink'>{b.title}</p>
                      <p className='text-sm text-coral mt-0.5'>{b.author.name}</p>
                      <p className='text-xs text-muted-foreground mt-2'>
                        ID {b.id}
                        {b.isbn ? ` · ISBN ${b.isbn}` : ''}
                        {b.publication_year != null ? ` · ${b.publication_year}` : ''}
                      </p>
                    </button>
                    <Button type='button' colorSchema='secondary' className='shrink-0 rounded-xl' onClick={() => openEdit(b)}>
                      Editar
                    </Button>
                  </div>
                ))}
              </div>

              {data.items.length === 0 && (
                <p className='text-muted-foreground mb-8'>Nenhum livro encontrado com esse filtro.</p>
              )}

              {!q && pages > 1 && (
                <nav className='flex flex-wrap items-center justify-center gap-3 pb-8' aria-label='Paginação'>
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

              {q && data.total > data.items.length && (
                <p className='text-xs text-muted-foreground pb-6'>Mostrando os primeiros {PAGE_SIZE} resultados. Refine a busca se precisar.</p>
              )}
            </>
          )}
        </section>
      )}

      {editBook && (
        <div className='fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/40 overflow-y-auto'>
          <div className='bg-card border border-border rounded-2xl shadow-book max-w-lg w-full p-6 space-y-4 my-8 animate-fade-up'>
            <h2 className='font-serif text-2xl text-ink'>Editar livro</h2>
            <div className='space-y-2'>
              <Label htmlFor='eb-title'>Título</Label>
              <Input id='eb-title' value={editBookTitle} onChange={(ev) => setEditBookTitle(ev.target.value)} className='h-11 rounded-xl' />
            </div>
            <div className='space-y-2'>
              <Label htmlFor='eb-author'>Autor</Label>
              <AuthorSearchSelect
                id='eb-author'
                authors={authors}
                value={editBookAuthorId}
                onChange={setEditBookAuthorId}
                loading={authorsLoading}
                placeholder='Buscar ou trocar autor…'
              />
            </div>
            <div className='space-y-2'>
              <Label htmlFor='eb-desc'>Descrição</Label>
              <textarea id='eb-desc' value={editBookDescription} onChange={(ev) => setEditBookDescription(ev.target.value)} className={adminTextareaClass} rows={4} />
            </div>
            <div className='grid sm:grid-cols-2 gap-4'>
              <div className='space-y-2'>
                <Label htmlFor='eb-pub'>Editora</Label>
                <Input id='eb-pub' value={editBookPublisher} onChange={(ev) => setEditBookPublisher(ev.target.value)} className='h-11 rounded-xl' />
              </div>
              <div className='space-y-2'>
                <Label htmlFor='eb-isbn'>ISBN</Label>
                <Input id='eb-isbn' value={editBookIsbn} onChange={(ev) => setEditBookIsbn(ev.target.value)} className='h-11 rounded-xl' />
              </div>
              <div className='space-y-2 sm:col-span-2'>
                <Label htmlFor='eb-year'>Ano</Label>
                <Input id='eb-year' value={editBookYear} onChange={(ev) => setEditBookYear(ev.target.value)} className='h-11 rounded-xl max-w-xs' />
              </div>
            </div>
            <div className='flex flex-col sm:flex-row gap-2 pt-2'>
              <Button type='button' colorSchema='primary' className='flex-1 rounded-xl' loading={bookSaving} onClick={() => void saveEdit()}>
                Salvar
              </Button>
              <Button
                type='button'
                colorSchema='secondary'
                className='flex-1 rounded-xl gap-2 text-destructive border-destructive/30 hover:bg-destructive/10'
                disabled={bookSaving}
                onClick={() => void onDelete(editBook.id)}
              >
                <Trash2 className='w-4 h-4' />
                Excluir
              </Button>
              <Button type='button' colorSchema='secondary' className='flex-1 rounded-xl' disabled={bookSaving} onClick={() => setEditBook(null)}>
                Fechar
              </Button>
            </div>
          </div>
        </div>
      )}

      <AdminFeedbackModal feedback={feedback} onDismiss={dismissFeedback} idPrefix='admin-books-feedback' />
    </main>
  );
};

export default AdminBooks;

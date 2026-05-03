import { ChevronLeft, ChevronRight, Search, Trash2 } from 'lucide-react';

import AdminFeedbackModal from '@/components/AdminFeedbackModal';
import Button from '@/components/Button';
import { Input } from '@/components/Input';
import { Label } from '@/components/Label';
import { useAdminAuthors } from '@/hooks/useAdminAuthors';
import { adminTextareaClass } from '@/lib/adminFormStyles';
import { PAGE_SIZE } from '@/lib/pagination';
import { classNames } from '@/services/string';

const AdminAuthors = () => {
  const {
    mainTab,
    setMainTab,
    newAuthorName,
    setNewAuthorName,
    newAuthorBio,
    setNewAuthorBio,
    authorSaving,
    page,
    setPage,
    searchInput,
    setSearchInput,
    data,
    error,
    loading,
    editAuthor,
    setEditAuthor,
    editAuthorName,
    setEditAuthorName,
    editAuthorBio,
    setEditAuthorBio,
    feedback,
    dismissFeedback,
    onCreateAuthor,
    openEdit,
    saveEdit,
    onDelete,
    pages,
    canPrev,
    canNext,
    q,
  } = useAdminAuthors();

  return (
    <main className='p-6 lg:p-10 max-w-[1400px] mx-auto'>
      <header className='mb-8'>
        <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>ADMINISTRAÇÃO</p>
        <h1 className='font-serif text-4xl lg:text-5xl text-ink'>Gerenciar autores</h1>
        <p className='text-muted-foreground mt-2 max-w-2xl'>
          Cadastre novos autores ou busque um existente para editar ou excluir.
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
          <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>NOVO AUTOR</p>
          <h2 className='font-serif text-2xl text-ink mb-6'>Cadastrar autor</h2>
          <form onSubmit={(e) => void onCreateAuthor(e)} className='bg-card border border-border rounded-2xl p-6 space-y-4'>
            <div className='space-y-2'>
              <Label htmlFor='admin-a-name'>Nome</Label>
              <Input
                id='admin-a-name'
                value={newAuthorName}
                onChange={(ev) => setNewAuthorName(ev.target.value)}
                className='h-11 rounded-xl'
                required
                minLength={1}
              />
            </div>
            <div className='space-y-2'>
              <Label htmlFor='admin-a-bio'>Biografia (opcional)</Label>
              <textarea
                id='admin-a-bio'
                value={newAuthorBio}
                onChange={(ev) => setNewAuthorBio(ev.target.value)}
                className={adminTextareaClass}
                rows={4}
              />
            </div>
            <Button type='submit' loading={authorSaving} disabled={authorSaving} className='rounded-xl'>
              Cadastrar autor
            </Button>
          </form>
        </section>
      )}

      {mainTab === 'gerenciar' && (
        <section className='animate-fade-up space-y-8'>
          <div>
            <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>BUSCAR</p>
            <h2 className='font-serif text-2xl text-ink mb-4'>Filtrar autores</h2>
            <div className='relative max-w-xl'>
              <Search className='absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground' />
              <Input
                value={searchInput}
                onChange={(ev) => setSearchInput(ev.target.value)}
                placeholder='Nome ou trecho da biografia…'
                className='h-12 pl-12 rounded-xl bg-card border-border'
                aria-label='Buscar autor'
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
                {data.items.map((a) => (
                  <div
                    key={a.id}
                    className='bg-card border border-border rounded-2xl p-5 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4'
                  >
                    <button type='button' onClick={() => openEdit(a)} className='min-w-0 flex-1 text-left'>
                      <p className='font-serif text-lg text-ink'>{a.name}</p>
                      {a.bio && <p className='text-sm text-muted-foreground line-clamp-2 mt-1'>{a.bio}</p>}
                      <p className='text-xs text-muted-foreground mt-2'>ID {a.id}</p>
                    </button>
                    <Button type='button' colorSchema='secondary' className='shrink-0 rounded-xl' onClick={() => openEdit(a)}>
                      Editar
                    </Button>
                  </div>
                ))}
              </div>

              {data.items.length === 0 && (
                <p className='text-muted-foreground mb-8'>Nenhum autor encontrado com esse filtro.</p>
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

      {editAuthor && (
        <div className='fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/40'>
          <div className='bg-card border border-border rounded-2xl shadow-book max-w-md w-full p-6 space-y-4 animate-fade-up'>
            <h2 className='font-serif text-2xl text-ink'>Editar autor</h2>
            <div className='space-y-2'>
              <Label htmlFor='edit-a-name'>Nome</Label>
              <Input
                id='edit-a-name'
                value={editAuthorName}
                onChange={(ev) => setEditAuthorName(ev.target.value)}
                className='h-11 rounded-xl'
              />
            </div>
            <div className='space-y-2'>
              <Label htmlFor='edit-a-bio'>Biografia</Label>
              <textarea
                id='edit-a-bio'
                value={editAuthorBio}
                onChange={(ev) => setEditAuthorBio(ev.target.value)}
                className={adminTextareaClass}
                rows={4}
              />
            </div>
            <div className='flex flex-col sm:flex-row gap-2 pt-2'>
              <Button type='button' colorSchema='primary' className='flex-1 rounded-xl' loading={authorSaving} onClick={() => void saveEdit()}>
                Salvar
              </Button>
              <Button
                type='button'
                colorSchema='secondary'
                className='flex-1 rounded-xl gap-2 text-destructive border-destructive/30 hover:bg-destructive/10'
                disabled={authorSaving}
                onClick={() => void onDelete(editAuthor.id)}
              >
                <Trash2 className='w-4 h-4' />
                Excluir
              </Button>
              <Button type='button' colorSchema='secondary' className='flex-1 rounded-xl' disabled={authorSaving} onClick={() => setEditAuthor(null)}>
                Fechar
              </Button>
            </div>
          </div>
        </div>
      )}

      <AdminFeedbackModal feedback={feedback} onDismiss={dismissFeedback} idPrefix='admin-authors-feedback' />
    </main>
  );
};

export default AdminAuthors;

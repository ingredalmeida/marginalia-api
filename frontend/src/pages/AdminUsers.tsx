import { ChevronLeft, ChevronRight, Pencil, Search, Trash2 } from 'lucide-react';

import AdminFeedbackModal from '@/components/AdminFeedbackModal';
import Button from '@/components/Button';
import { Input } from '@/components/Input';
import { Label } from '@/components/Label';
import { useAdminUsers } from '@/hooks/useAdminUsers';
import { PAGE_SIZE } from '@/lib/pagination';
import { classNames } from '@/services/string';

const AdminUsers = () => {
  const {
    userId,
    page,
    setPage,
    searchInput,
    setSearchInput,
    debouncedSearch,
    data,
    error,
    loading,
    editId,
    editName,
    setEditName,
    editEmail,
    setEditEmail,
    editPassword,
    setEditPassword,
    saving,
    feedback,
    dismissFeedback,
    startEdit,
    cancelEdit,
    saveEdit,
    onDelete,
    pages,
    canPrev,
    canNext,
  } = useAdminUsers();

  return (
    <main className='p-6 lg:p-10 max-w-[1400px] mx-auto'>
      <header className='mb-8'>
        <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>ADMINISTRAÇÃO</p>
        <h1 className='font-serif text-4xl lg:text-5xl text-ink'>Gerenciar usuários</h1>
        <p className='text-muted-foreground mt-2 max-w-2xl'>
          Busque por nome ou e-mail, edite dados ou remova contas sem empréstimos vinculados.
        </p>
      </header>

      <section className='mb-8'>
        <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>BUSCAR</p>
        <h2 className='font-serif text-2xl text-ink mb-4'>Filtrar usuários</h2>
        <div className='relative max-w-xl'>
          <Search className='absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground' />
          <Input
            value={searchInput}
            onChange={(ev) => setSearchInput(ev.target.value)}
            placeholder='Nome ou e-mail…'
            className='h-12 pl-12 rounded-xl bg-card border-border'
            aria-label='Buscar usuário'
          />
        </div>
        <p className='text-xs text-muted-foreground mt-2'>
          Deixe em branco para ver todos (com paginação). Com texto, a busca atualiza após um breve intervalo.
        </p>
      </section>

      {error && (
        <p className='text-sm text-coral mb-6 bg-coral/5 border border-coral/20 rounded-xl px-4 py-3'>{error}</p>
      )}

      {loading && <p className='text-sm text-muted-foreground mb-6'>Carregando…</p>}

      {data && !loading && (
        <>
          <div className='space-y-3 mb-8'>
            {data.items.map((u) => (
              <div
                key={u.id}
                className='bg-card border border-border rounded-2xl p-5 flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4'
              >
                <div className='min-w-0 flex-1'>
                  <div className='flex flex-wrap items-center gap-2 mb-1'>
                    <p className='font-serif text-lg text-ink'>{u.name}</p>
                    {u.is_admin && (
                      <span className='text-[10px] tracking-wider uppercase px-2 py-0.5 rounded-full bg-ink text-cream'>
                        Admin
                      </span>
                    )}
                  </div>
                  <p className='text-sm text-muted-foreground break-all'>{u.email}</p>
                  <p className='text-xs text-muted-foreground mt-2'>ID {u.id}</p>
                </div>
                <div className='flex flex-wrap gap-2 shrink-0'>
                  <Button
                    type='button'
                    colorSchema='secondary'
                    className='gap-2 rounded-xl'
                    onClick={() => startEdit(u.id, u.name, u.email)}
                    disabled={editId != null}
                  >
                    <Pencil className='w-4 h-4' />
                    Editar
                  </Button>
                  <Button
                    type='button'
                    colorSchema='secondary'
                    className={classNames(
                      'gap-2 rounded-xl',
                      u.id === userId && 'opacity-40 cursor-not-allowed',
                    )}
                    disabled={u.id === userId}
                    onClick={() => void onDelete(u.id)}
                    title={u.id === userId ? 'Você não pode excluir a própria conta aqui.' : undefined}
                  >
                    <Trash2 className='w-4 h-4' />
                    Excluir
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {data.items.length === 0 && (
            <p className='text-muted-foreground mb-8'>Nenhum usuário encontrado com esse filtro.</p>
          )}

          {editId != null && (
            <div className='fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/40'>
              <div className='bg-card border border-border rounded-2xl shadow-book max-w-md w-full p-6 space-y-4 animate-fade-up'>
                <h2 className='font-serif text-2xl text-ink'>Editar usuário</h2>
                <div className='space-y-2'>
                  <Label htmlFor='admin-user-name'>Nome</Label>
                  <Input
                    id='admin-user-name'
                    value={editName}
                    onChange={(ev) => setEditName(ev.target.value)}
                    className='h-11 rounded-xl'
                  />
                </div>
                <div className='space-y-2'>
                  <Label htmlFor='admin-user-email'>E-mail</Label>
                  <Input
                    id='admin-user-email'
                    type='email'
                    value={editEmail}
                    onChange={(ev) => setEditEmail(ev.target.value)}
                    className='h-11 rounded-xl'
                  />
                </div>
                <div className='space-y-2'>
                  <Label htmlFor='admin-user-pass'>Nova senha (opcional)</Label>
                  <Input
                    id='admin-user-pass'
                    type='password'
                    value={editPassword}
                    onChange={(ev) => setEditPassword(ev.target.value)}
                    placeholder='Mín. 8 caracteres se preencher'
                    className='h-11 rounded-xl'
                    minLength={editPassword ? 8 : undefined}
                    maxLength={128}
                  />
                </div>
                <div className='flex gap-2 pt-2'>
                  <Button type='button' colorSchema='primary' className='flex-1 rounded-xl' loading={saving} onClick={() => void saveEdit()}>
                    Salvar
                  </Button>
                  <Button type='button' colorSchema='secondary' className='flex-1 rounded-xl' disabled={saving} onClick={cancelEdit}>
                    Cancelar
                  </Button>
                </div>
              </div>
            </div>
          )}

          {!debouncedSearch.trim() && pages > 1 && (
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

          {debouncedSearch.trim() && data.total > data.items.length && (
            <p className='text-xs text-muted-foreground pb-6'>Mostrando os primeiros {PAGE_SIZE} resultados. Refine a busca se precisar.</p>
          )}
        </>
      )}

      <AdminFeedbackModal feedback={feedback} onDismiss={dismissFeedback} idPrefix='admin-users-feedback' />
    </main>
  );
};

export default AdminUsers;

import { ChevronLeft, ChevronRight } from 'lucide-react';

import BookTile from '@/components/BookTile';
import Button from '@/components/Button';
import LibraryPageHeader from '@/components/LibraryPageHeader';
import { useExplorePage } from '@/hooks/useExplorePage';
import { EMPTY_SEARCH_MESSAGE } from '@/lib/catalogCopy';

const Explore = () => {
  const { q, page, setPage, data, error, loading, pages, canPrev, canNext } = useExplorePage();

  return (
    <main className='p-6 lg:p-10 max-w-[1400px] mx-auto'>
      <LibraryPageHeader />

      <section className='mb-8'>
        <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>ACERVO</p>
        <h1 className='font-serif text-4xl lg:text-5xl text-ink'>Explorar biblioteca</h1>
        {data && (
          <p className='text-muted-foreground mt-2'>
            {q ? (
              <>
                Busca por <span className='text-ink font-medium'>“{q}”</span> · {data.total}{' '}
                {data.total === 1 ? 'resultado' : 'resultados'}
              </>
            ) : (
              <>
                {data.total} {data.total === 1 ? 'título' : 'títulos'}
              </>
            )}
            {pages > 0 && (
              <>
                {' '}
                · página {page} de {pages}
              </>
            )}
          </p>
        )}
        {error && <p className='text-sm text-coral mt-2'>{error}</p>}
        {loading && <p className='text-sm text-muted-foreground mt-2'>Carregando…</p>}
      </section>

      {data && data.items.length > 0 && (
        <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-12'>
          {data.items.map((b, i) => (
            <BookTile key={b.id} book={b} animIndex={i} />
          ))}
        </div>
      )}

      {data && !loading && data.items.length === 0 && !error && (
        <p className='text-muted-foreground max-w-xl leading-relaxed'>
          {q ? EMPTY_SEARCH_MESSAGE : 'Nenhum livro cadastrado no acervo ainda.'}
        </p>
      )}

      {data && pages > 1 && (
        <nav className='flex flex-wrap items-center justify-center gap-3 pb-8' aria-label='Paginação'>
          <Button
            type='button'
            colorSchema='secondary'
            className='gap-1 rounded-xl'
            disabled={!canPrev || loading}
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
            disabled={!canNext || loading}
            onClick={() => setPage((p) => p + 1)}
          >
            Próxima <ChevronRight className='w-4 h-4' />
          </Button>
        </nav>
      )}
    </main>
  );
};

export default Explore;

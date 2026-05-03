import { ChevronLeft, ChevronRight } from 'lucide-react';

import BookTile from '@/components/BookTile';
import Button from '@/components/Button';
import LibraryPageHeader from '@/components/LibraryPageHeader';
import SpotlightSection from '@/components/SpotlightSection';
import { useHomePage } from '@/hooks/useHomePage';
import { EMPTY_SEARCH_MESSAGE } from '@/lib/catalogCopy';

const Home = () => {
  const {
    firstName,
    q,
    spotlight,
    listError,
    listLoading,
    emptyCatalog,
    searchPage,
    setSearchPage,
    searchData,
    searchLoading,
    searchError,
    searchPages,
    canPrev,
    canNext,
  } = useHomePage();

  return (
    <main className='p-6 lg:p-10 max-w-[1400px] mx-auto'>
      <LibraryPageHeader />

      <section className='mb-12 animate-fade-up'>
        <p className='text-sm tracking-[0.3em] text-muted-foreground mb-3'>BIBLIOTECA · MARGINÁLIA</p>
        <h1 className='font-serif text-5xl lg:text-6xl text-ink text-balance max-w-3xl'>
          Olá, {firstName}. Explore a estante e descubra o que há de <em className='text-coral not-italic'>novo</em> para
          você.
        </h1>
      </section>

      {q ? (
        <section className='animate-fade-up mb-14'>
          <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>RESULTADOS</p>
          <h2 className='font-serif text-3xl text-ink mb-2'>Busca no acervo</h2>
          <p className='text-muted-foreground mb-6'>
            Termo: <span className='text-ink font-medium'>“{q}”</span>
            {searchData != null && (
              <>
                {' '}
                · {searchData.total} {searchData.total === 1 ? 'resultado' : 'resultados'}
                {searchPages > 0 && (
                  <>
                    {' '}
                    · página {searchPage} de {searchPages}
                  </>
                )}
              </>
            )}
          </p>
          {searchError && <p className='text-sm text-coral mb-4'>{searchError}</p>}
          {searchLoading && <p className='text-sm text-muted-foreground mb-6'>Buscando…</p>}
          {searchData && !searchLoading && searchData.items.length > 0 && (
            <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-10'>
              {searchData.items.map((b, i) => (
                <BookTile key={b.id} book={b} animIndex={i} />
              ))}
            </div>
          )}
          {searchData && !searchLoading && searchData.total === 0 && !searchError && (
            <p className='text-muted-foreground max-w-xl leading-relaxed'>{EMPTY_SEARCH_MESSAGE}</p>
          )}
          {searchData && searchPages > 1 && !searchLoading && (
            <nav className='flex flex-wrap items-center justify-center gap-3 pb-8' aria-label='Paginação da busca'>
              <Button
                type='button'
                colorSchema='secondary'
                className='gap-1 rounded-xl'
                disabled={!canPrev}
                onClick={() => setSearchPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft className='w-4 h-4' /> Anterior
              </Button>
              <span className='text-sm text-muted-foreground px-2'>
                {searchPage} / {searchPages}
              </span>
              <Button
                type='button'
                colorSchema='secondary'
                className='gap-1 rounded-xl'
                disabled={!canNext}
                onClick={() => setSearchPage((p) => p + 1)}
              >
                Próxima <ChevronRight className='w-4 h-4' />
              </Button>
            </nav>
          )}
        </section>
      ) : (
        <SpotlightSection
          books={spotlight}
          listError={listError}
          listLoading={listLoading}
          showEmptyHint={emptyCatalog}
        />
      )}
    </main>
  );
};

export default Home;

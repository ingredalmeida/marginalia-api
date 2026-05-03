import { useNavigate } from 'react-router-dom';

import BookHandCover from '@/components/BookHandCover';
import type { BookRead } from '@/services/bookApi';

type SpotlightSectionProps = {
  books: BookRead[];
  listError: string | null;
  listLoading: boolean;
  showEmptyHint: boolean;
};

const SpotlightSection = ({ books, listError, listLoading, showEmptyHint }: SpotlightSectionProps) => {
  const navigate = useNavigate();

  return (
    <section className='mb-14'>
      <div className='mb-8'>
        <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>EM DESTAQUE</p>
        <h2 className='font-serif text-4xl text-ink'>Indicações desta semana</h2>
        {listError && <p className='text-sm text-coral mt-2'>{listError}</p>}
        {listLoading && <p className='text-sm text-muted-foreground mt-2'>Carregando estante…</p>}
        {showEmptyHint && (
          <p className='text-sm text-muted-foreground mt-3 max-w-lg'>
            Ainda não há livros cadastrados no acervo.
          </p>
        )}
      </div>

      {books.length > 0 && (
        <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6'>
          {books.map((b, i) => {
            const authorLine = b.author.name;
            return (
              <article
                key={b.id}
                role='button'
                tabIndex={0}
                onClick={() => navigate(`/livro/${b.id}`)}
                onKeyDown={(ev) => {
                  if (ev.key === 'Enter' || ev.key === ' ') {
                    ev.preventDefault();
                    navigate(`/livro/${b.id}`);
                  }
                }}
                className='group cursor-pointer animate-fade-up'
                style={{ animationDelay: `${i * 40}ms` }}
              >
                <div className='relative aspect-[3/4] rounded-2xl overflow-hidden shadow-book group-hover:-translate-y-2 transition-all duration-500'>
                  <BookHandCover bookId={b.id} title={b.title} />
                </div>
                <div className='mt-4'>
                  <h4 className='font-serif text-lg text-ink line-clamp-2'>{b.title}</h4>
                  <p className='text-sm text-coral line-clamp-2'>{authorLine}</p>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
};

export default SpotlightSection;

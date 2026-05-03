import { useNavigate } from 'react-router-dom';

import BookHandCover from '@/components/BookHandCover';
import type { BookRead } from '@/services/bookApi';

type BookTileProps = {
  book: BookRead;
  animIndex?: number;
};

const BookTile = ({ book, animIndex = 0 }: BookTileProps) => {
  const navigate = useNavigate();
  const authorLine = book.author.name;

  return (
    <article
      role='button'
      tabIndex={0}
      onClick={() => navigate(`/livro/${book.id}`)}
      onKeyDown={(ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') {
          ev.preventDefault();
          navigate(`/livro/${book.id}`);
        }
      }}
      className='group cursor-pointer animate-fade-up'
      style={{ animationDelay: `${animIndex * 40}ms` }}
    >
      <div className='relative aspect-[3/4] rounded-2xl overflow-hidden shadow-book group-hover:-translate-y-2 transition-all duration-500'>
        <BookHandCover bookId={book.id} title={book.title} />
      </div>
      <div className='mt-4'>
        <h4 className='font-serif text-lg text-ink line-clamp-2'>{book.title}</h4>
        <p className='text-sm text-coral line-clamp-2'>{authorLine}</p>
      </div>
    </article>
  );
};

export default BookTile;

import { ACERVO_CHIP, coverVisualForBookId } from '@/data/homeBrowse';

export type BookHandCoverProps = {
  bookId: number;
  title: string;
  chip?: string;
  /** Larger padding and title for the book detail hero */
  emphasis?: boolean;
};

const BookHandCover = ({ bookId, title, chip = ACERVO_CHIP, emphasis = false }: BookHandCoverProps) => {
  const visual = coverVisualForBookId(bookId);
  const pad = emphasis ? 'p-6' : 'p-5';
  const titleClass = emphasis
    ? 'font-serif text-2xl sm:text-3xl leading-tight'
    : 'font-serif text-2xl leading-tight';

  return (
    <>
      <div className={`absolute inset-0 bg-gradient-to-br ${visual.gradient}`} />
      <div className={`absolute inset-0 flex flex-col justify-between ${pad} text-cream`}>
        <span className='text-[10px] tracking-[0.3em] opacity-80'>MARGINÁLIA</span>
        <div>
          <p className='text-[10px] tracking-[0.25em] opacity-80 mb-2'>{chip}</p>
          {/* Card grids use h3; detail hero mirrors typography without a second page h1 */}
          {emphasis ? (
            <p className={`${titleClass} m-0`}>{title}</p>
          ) : (
            <h3 className={titleClass}>{title}</h3>
          )}
        </div>
      </div>
      <div
        className={`absolute top-0 right-5 w-6 h-10 ${visual.spine} brightness-75`}
        style={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 50% 75%, 0 100%)' }}
      />
    </>
  );
};

export default BookHandCover;

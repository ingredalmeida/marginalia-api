export const ACERVO_CHIP = 'ACERVO';

/** Gradientes + lombada (classes Tailwind literais para o JIT). */
export const BOOK_COVER_VISUALS = [
  { gradient: 'from-coral to-pink', spine: 'bg-coral' },
  { gradient: 'from-teal to-coral', spine: 'bg-teal' },
  { gradient: 'from-terracotta to-coral', spine: 'bg-terracotta' },
  { gradient: 'from-mustard to-pink', spine: 'bg-mustard' },
  { gradient: 'from-teal to-pink', spine: 'bg-teal' },
  { gradient: 'from-ink to-teal', spine: 'bg-ink' },
  { gradient: 'from-coral to-mustard', spine: 'bg-coral' },
  { gradient: 'from-terracotta to-teal', spine: 'bg-terracotta' },
  { gradient: 'from-teal to-mustard', spine: 'bg-teal' },
  { gradient: 'from-coral to-terracotta', spine: 'bg-coral' },
] as const;

export type BookCoverVisual = (typeof BOOK_COVER_VISUALS)[number];

export function coverVisualForBookId(bookId: number): BookCoverVisual {
  const id = Number.isFinite(bookId) && bookId >= 1 ? Math.floor(bookId) : 1;
  return BOOK_COVER_VISUALS[(id - 1) % BOOK_COVER_VISUALS.length];
}

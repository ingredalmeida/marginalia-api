import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { useAuth } from '@/hooks/useAuth';
import { PAGE_SIZE } from '@/lib/pagination';
import { fetchBooksPage, type BookRead } from '@/services/bookApi';

export function useExplorePage() {
  const { token } = useAuth();
  const [searchParams] = useSearchParams();
  const q = (searchParams.get('q') ?? '').trim();

  const [page, setPage] = useState(1);
  const [data, setData] = useState<{ items: BookRead[]; total: number; pages: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setPage(1);
  }, [q]);

  const load = useCallback(
    async (p: number) => {
      if (!token) {
        setLoading(false);
        setData(null);
        setError('Sessão inválida. Faça login novamente.');
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const res = await fetchBooksPage(token, {
          page: p,
          page_size: PAGE_SIZE,
          ...(q ? { q } : {}),
        });
        setData({ items: res.items, total: res.total, pages: res.pages });
      } catch (e) {
        setData(null);
        setError(e instanceof Error ? e.message : 'Não foi possível carregar os livros.');
      } finally {
        setLoading(false);
      }
    },
    [token, q],
  );

  useEffect(() => {
    void load(page);
  }, [page, load]);

  const pages = data?.pages ?? 0;
  const canPrev = page > 1;
  const canNext = page < pages;

  return {
    q,
    page,
    setPage,
    data,
    error,
    loading,
    pages,
    canPrev,
    canNext,
  };
}

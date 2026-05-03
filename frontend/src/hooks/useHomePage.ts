import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { useAuth } from '@/hooks/useAuth';
import { PAGE_SIZE } from '@/lib/pagination';
import { randomSample } from '@/lib/randomSample';
import { fetchBooksPage, type BookRead } from '@/services/bookApi';

export function useHomePage() {
  const { profile, token } = useAuth();
  const [searchParams] = useSearchParams();
  const q = (searchParams.get('q') ?? '').trim();

  const firstName = profile?.name?.split(/\s+/)[0] ?? 'leitora';

  const [spotlight, setSpotlight] = useState<BookRead[]>([]);
  const [totalInCatalog, setTotalInCatalog] = useState<number | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [listLoading, setListLoading] = useState(true);

  const [searchPage, setSearchPage] = useState(1);
  const [searchData, setSearchData] = useState<{
    items: BookRead[];
    total: number;
    pages: number;
  } | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    setSearchPage(1);
  }, [q]);

  const loadSpotlight = useCallback(async () => {
    if (!token) {
      setListLoading(false);
      return;
    }
    setListLoading(true);
    setListError(null);
    try {
      const pool: BookRead[] = [];
      let firstTotal: number | null = null;
      let pages = 1;
      for (let p = 1; p <= 5; p += 1) {
        const chunk = await fetchBooksPage(token, { page: p, page_size: PAGE_SIZE });
        if (firstTotal === null) firstTotal = chunk.total;
        pages = chunk.pages;
        pool.push(...chunk.items);
        if (p >= pages || chunk.items.length === 0) break;
      }
      setTotalInCatalog(firstTotal ?? 0);
      setSpotlight(randomSample(pool, Math.min(5, pool.length)));
    } catch (e) {
      setSpotlight([]);
      setTotalInCatalog(null);
      setListError(e instanceof Error ? e.message : 'Não foi possível carregar os livros.');
    } finally {
      setListLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (q) return;
    void loadSpotlight();
  }, [q, loadSpotlight]);

  useEffect(() => {
    if (!token || !q) {
      setSearchData(null);
      setSearchError(null);
      setSearchLoading(false);
      return;
    }
    let cancelled = false;
    setSearchLoading(true);
    setSearchError(null);
    void (async () => {
      try {
        const res = await fetchBooksPage(token, {
          page: searchPage,
          page_size: PAGE_SIZE,
          q,
        });
        if (!cancelled) {
          setSearchData({ items: res.items, total: res.total, pages: res.pages });
        }
      } catch (e) {
        if (!cancelled) {
          setSearchData(null);
          setSearchError(e instanceof Error ? e.message : 'Não foi possível buscar.');
        }
      } finally {
        if (!cancelled) setSearchLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, q, searchPage]);

  const emptyCatalog = !listLoading && !listError && totalInCatalog === 0;
  const searchPages = searchData?.pages ?? 0;
  const canPrev = searchPage > 1;
  const canNext = searchPage < searchPages;

  return {
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
  };
}

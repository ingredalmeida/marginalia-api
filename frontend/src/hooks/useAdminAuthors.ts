import { useCallback, useEffect, useState } from 'react';

import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { useAdminFeedback } from '@/hooks/useAdminFeedback';
import { useAuth } from '@/hooks/useAuth';
import { PAGE_SIZE } from '@/lib/pagination';
import {
  createAuthor,
  deleteAuthor,
  fetchAuthorsPage,
  updateAuthor,
  type AuthorCreateBody,
} from '@/services/authorApi';
import type { AuthorRead, Page } from '@/services/bookApi';

export type AdminAuthorsMainTab = 'cadastro' | 'gerenciar';

export function useAdminAuthors() {
  const { token } = useAuth();
  const { feedback, setFeedback, dismissFeedback } = useAdminFeedback();

  const [mainTab, setMainTab] = useState<AdminAuthorsMainTab>('cadastro');

  const [newAuthorName, setNewAuthorName] = useState('');
  const [newAuthorBio, setNewAuthorBio] = useState('');
  const [authorSaving, setAuthorSaving] = useState(false);

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearch = useDebouncedValue(searchInput, 350);
  const [data, setData] = useState<Page<AuthorRead> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [editAuthor, setEditAuthor] = useState<AuthorRead | null>(null);
  const [editAuthorName, setEditAuthorName] = useState('');
  const [editAuthorBio, setEditAuthorBio] = useState('');

  const load = useCallback(async () => {
    if (!token || mainTab !== 'gerenciar') return;
    setLoading(true);
    setError(null);
    const q = debouncedSearch.trim();
    try {
      const res = await fetchAuthorsPage(token, {
        page: q ? 1 : page,
        page_size: PAGE_SIZE,
        ...(q ? { q } : {}),
      });
      setData(res);
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : 'Não foi possível carregar os autores.');
    } finally {
      setLoading(false);
    }
  }, [token, mainTab, page, debouncedSearch]);

  useEffect(() => {
    void load();
  }, [load]);

  const onCreateAuthor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !newAuthorName.trim()) return;
    setAuthorSaving(true);
    try {
      const body: AuthorCreateBody = { name: newAuthorName.trim(), bio: newAuthorBio.trim() || null };
      await createAuthor(token, body);
      setNewAuthorName('');
      setNewAuthorBio('');
      setFeedback({ type: 'success', message: 'Autor cadastrado com sucesso.' });
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err instanceof Error ? err.message : 'Não foi possível criar o autor.',
      });
    } finally {
      setAuthorSaving(false);
    }
  };

  const openEdit = (a: AuthorRead) => {
    setEditAuthor(a);
    setEditAuthorName(a.name);
    setEditAuthorBio(a.bio ?? '');
    setFeedback(null);
  };

  const saveEdit = async () => {
    if (!token || !editAuthor) return;
    setAuthorSaving(true);
    try {
      await updateAuthor(token, editAuthor.id, {
        name: editAuthorName.trim(),
        bio: editAuthorBio.trim() || null,
      });
      setEditAuthor(null);
      await load();
      setFeedback({ type: 'success', message: 'Autor atualizado.' });
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err instanceof Error ? err.message : 'Não foi possível atualizar.',
      });
    } finally {
      setAuthorSaving(false);
    }
  };

  const onDelete = async (id: number) => {
    if (!token) return;
    try {
      await deleteAuthor(token, id);
      setEditAuthor(null);
      await load();
      setFeedback({ type: 'success', message: 'Autor removido.' });
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err instanceof Error ? err.message : 'Não foi possível excluir.',
      });
    }
  };

  const pages = data?.pages ?? 0;
  const canPrev = page > 1;
  const canNext = page < pages;
  const q = debouncedSearch.trim();

  const setMainTabClearFeedback = (t: AdminAuthorsMainTab) => {
    setMainTab(t);
    setFeedback(null);
  };

  return {
    token,
    mainTab,
    setMainTab: setMainTabClearFeedback,
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
  };
}

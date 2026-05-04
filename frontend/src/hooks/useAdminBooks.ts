import { useCallback, useEffect, useState } from 'react';

import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { useAdminFeedback } from '@/hooks/useAdminFeedback';
import { useAuth } from '@/hooks/useAuth';
import { PAGE_SIZE } from '@/lib/pagination';
import {
  createBook,
  deleteBook,
  fetchBooksPage,
  updateBook,
  type AuthorRead,
  type BookCreateBody,
  type BookRead,
  type BookUpdateBody,
  type Page,
} from '@/services/bookApi';
import { fetchAllAuthors } from '@/services/catalogHelpers';

export type AdminBooksMainTab = 'cadastro' | 'gerenciar';

export function useAdminBooks() {
  const { token } = useAuth();
  const { feedback, setFeedback, dismissFeedback } = useAdminFeedback();

  const [mainTab, setMainTab] = useState<AdminBooksMainTab>('cadastro');

  const [authors, setAuthors] = useState<AuthorRead[]>([]);
  const [authorsLoading, setAuthorsLoading] = useState(false);

  const [bookTitle, setBookTitle] = useState('');
  const [bookAuthorId, setBookAuthorId] = useState(0);
  const [bookDescription, setBookDescription] = useState('');
  const [bookPublisher, setBookPublisher] = useState('');
  const [bookIsbn, setBookIsbn] = useState('');
  const [bookYear, setBookYear] = useState('');
  const [bookSaving, setBookSaving] = useState(false);

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearch = useDebouncedValue(searchInput, 350);
  const [data, setData] = useState<Page<BookRead> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [editBook, setEditBook] = useState<BookRead | null>(null);
  const [editBookTitle, setEditBookTitle] = useState('');
  const [editBookAuthorId, setEditBookAuthorId] = useState(0);
  const [editBookDescription, setEditBookDescription] = useState('');
  const [editBookPublisher, setEditBookPublisher] = useState('');
  const [editBookIsbn, setEditBookIsbn] = useState('');
  const [editBookYear, setEditBookYear] = useState('');

  const refreshAuthorList = useCallback(async () => {
    if (!token) return;
    setAuthorsLoading(true);
    try {
      const list = await fetchAllAuthors(token);
      setAuthors(list);
    } catch {
      setAuthors([]);
    } finally {
      setAuthorsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      void refreshAuthorList();
    }
  }, [token, refreshAuthorList]);

  const load = useCallback(async () => {
    if (!token || mainTab !== 'gerenciar') return;
    setLoading(true);
    setError(null);
    const q = debouncedSearch.trim();
    try {
      const res = await fetchBooksPage(token, {
        page: q ? 1 : page,
        page_size: PAGE_SIZE,
        ...(q ? { q } : {}),
      });
      setData(res);
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : 'Não foi possível carregar os livros.');
    } finally {
      setLoading(false);
    }
  }, [token, mainTab, page, debouncedSearch]);

  useEffect(() => {
    void load();
  }, [load]);

  const onCreateBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !bookTitle.trim()) return;
    if (bookAuthorId < 1) {
      setFeedback({ type: 'error', message: 'Selecione um autor.' });
      return;
    }
    setBookSaving(true);
    try {
      const body: BookCreateBody = {
        title: bookTitle.trim(),
        author_id: bookAuthorId,
        description: bookDescription.trim() || null,
        publisher: bookPublisher.trim() || null,
        isbn: bookIsbn.trim() || null,
        publication_year: bookYear.trim() ? Number.parseInt(bookYear, 10) : null,
      };
      if (body.publication_year != null && !Number.isFinite(body.publication_year)) {
        throw new Error('Ano de publicação inválido.');
      }
      await createBook(token, body);
      setBookTitle('');
      setBookAuthorId(0);
      setBookDescription('');
      setBookPublisher('');
      setBookIsbn('');
      setBookYear('');
      setFeedback({ type: 'success', message: 'Livro cadastrado com sucesso.' });
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err instanceof Error ? err.message : 'Não foi possível cadastrar o livro.',
      });
    } finally {
      setBookSaving(false);
    }
  };

  const openEdit = (b: BookRead) => {
    setEditBook(b);
    setEditBookTitle(b.title);
    setEditBookAuthorId(b.author_id);
    setEditBookDescription(b.description ?? '');
    setEditBookPublisher(b.publisher ?? '');
    setEditBookIsbn(b.isbn ?? '');
    setEditBookYear(b.publication_year != null ? String(b.publication_year) : '');
    setFeedback(null);
  };

  const saveEdit = async () => {
    if (!token || !editBook) return;
    setBookSaving(true);
    try {
      const body: BookUpdateBody = {
        title: editBookTitle.trim(),
        author_id: editBookAuthorId,
        description: editBookDescription.trim() || null,
        publisher: editBookPublisher.trim() || null,
        isbn: editBookIsbn.trim() || null,
        publication_year: editBookYear.trim() ? Number.parseInt(editBookYear, 10) : null,
      };
      if (body.publication_year != null && !Number.isFinite(body.publication_year)) {
        throw new Error('Ano de publicação inválido.');
      }
      await updateBook(token, editBook.id, body);
      setEditBook(null);
      await refreshAuthorList();
      await load();
      setFeedback({ type: 'success', message: 'Livro atualizado.' });
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err instanceof Error ? err.message : 'Não foi possível atualizar.',
      });
    } finally {
      setBookSaving(false);
    }
  };

  const onDelete = async (id: number) => {
    if (!token) return;
    try {
      await deleteBook(token, id);
      setEditBook(null);
      await load();
      setFeedback({ type: 'success', message: 'Livro removido.' });
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

  const setMainTabClearFeedback = (t: AdminBooksMainTab) => {
    setMainTab(t);
    setFeedback(null);
  };

  return {
    token,
    mainTab,
    setMainTab: setMainTabClearFeedback,
    authors,
    authorsLoading,
    bookTitle,
    setBookTitle,
    bookAuthorId,
    setBookAuthorId,
    bookDescription,
    setBookDescription,
    bookPublisher,
    setBookPublisher,
    bookIsbn,
    setBookIsbn,
    bookYear,
    setBookYear,
    bookSaving,
    page,
    setPage,
    searchInput,
    setSearchInput,
    data,
    error,
    loading,
    editBook,
    setEditBook,
    editBookTitle,
    setEditBookTitle,
    editBookAuthorId,
    setEditBookAuthorId,
    editBookDescription,
    setEditBookDescription,
    editBookPublisher,
    setEditBookPublisher,
    editBookIsbn,
    setEditBookIsbn,
    editBookYear,
    setEditBookYear,
    feedback,
    dismissFeedback,
    onCreateBook,
    openEdit,
    saveEdit,
    onDelete,
    pages,
    canPrev,
    canNext,
    q,
  };
}

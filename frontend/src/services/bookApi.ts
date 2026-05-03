import { apiUrl } from '@/lib/api';
import { PAGE_SIZE } from '@/lib/pagination';
import { authHeader, jsonAuthHeader } from '@/lib/authFetch';
import { parseApiError } from '@/services/parseApiError';

export type AuthorRead = {
  id: number;
  name: string;
  bio: string | null;
};

export type BookRead = {
  id: number;
  title: string;
  description: string | null;
  publisher: string | null;
  isbn: string | null;
  publication_year: number | null;
  author_id: number;
  author: AuthorRead;
  created_at: string;
  available: boolean;
};

export type BookCreateBody = {
  title: string;
  author_id: number;
  description?: string | null;
  publisher?: string | null;
  isbn?: string | null;
  publication_year?: number | null;
};

export type BookUpdateBody = Partial<BookCreateBody>;

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export async function fetchBooksPage(
  token: string,
  params: {
    page?: number;
    page_size?: number;
    q?: string;
  },
): Promise<Page<BookRead>> {
  const q = new URLSearchParams();
  q.set('page', String(params.page ?? 1));
  q.set('page_size', String(params.page_size ?? PAGE_SIZE));
  if (params.q?.trim()) {
    q.set('q', params.q.trim());
  }
  const res = await fetch(apiUrl(`/api/v1/books?${q}`), { headers: authHeader(token) });
  if (res.status === 401) {
    throw new Error('Sessão inválida ou expirada. Faça login novamente.');
  }
  if (!res.ok) {
    throw new Error(`Não foi possível carregar o acervo (${res.status}).`);
  }
  return res.json() as Promise<Page<BookRead>>;
}

export async function fetchBook(token: string, id: number): Promise<BookRead> {
  const res = await fetch(apiUrl(`/api/v1/books/${id}`), { headers: authHeader(token) });
  if (res.status === 401) {
    throw new Error('Sessão inválida ou expirada. Faça login novamente.');
  }
  if (res.status === 404) {
    throw new Error('Livro não encontrado.');
  }
  if (!res.ok) {
    throw new Error(`Não foi possível carregar o livro (${res.status}).`);
  }
  return res.json() as Promise<BookRead>;
}

export async function createBook(token: string, body: BookCreateBody): Promise<BookRead> {
  const res = await fetch(apiUrl('/api/v1/books'), {
    method: 'POST',
    headers: jsonAuthHeader(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<BookRead>;
}

export async function updateBook(token: string, id: number, body: BookUpdateBody): Promise<BookRead> {
  const res = await fetch(apiUrl(`/api/v1/books/${id}`), {
    method: 'PATCH',
    headers: jsonAuthHeader(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<BookRead>;
}

export async function deleteBook(token: string, id: number): Promise<void> {
  const res = await fetch(apiUrl(`/api/v1/books/${id}`), {
    method: 'DELETE',
    headers: authHeader(token),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
}

import { apiUrl } from '@/lib/api';
import { PAGE_SIZE } from '@/lib/pagination';
import { authHeader, jsonAuthHeader } from '@/lib/authFetch';
import type { AuthorRead, Page } from '@/services/bookApi';
import { parseApiError } from '@/services/parseApiError';

export type AuthorCreateBody = {
  name: string;
  bio?: string | null;
};

export type AuthorUpdateBody = {
  name?: string;
  bio?: string | null;
};

export async function fetchAuthorsPage(
  token: string,
  params: { page?: number; page_size?: number; q?: string },
): Promise<Page<AuthorRead>> {
  const q = new URLSearchParams();
  q.set('page', String(params.page ?? 1));
  q.set('page_size', String(params.page_size ?? PAGE_SIZE));
  if (params.q?.trim()) {
    q.set('q', params.q.trim());
  }
  const res = await fetch(apiUrl(`/api/v1/authors?${q}`), { headers: authHeader(token) });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<Page<AuthorRead>>;
}

export async function createAuthor(token: string, body: AuthorCreateBody): Promise<AuthorRead> {
  const res = await fetch(apiUrl('/api/v1/authors'), {
    method: 'POST',
    headers: jsonAuthHeader(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<AuthorRead>;
}

export async function updateAuthor(token: string, id: number, body: AuthorUpdateBody): Promise<AuthorRead> {
  const res = await fetch(apiUrl(`/api/v1/authors/${id}`), {
    method: 'PATCH',
    headers: jsonAuthHeader(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<AuthorRead>;
}

export async function deleteAuthor(token: string, id: number): Promise<void> {
  const res = await fetch(apiUrl(`/api/v1/authors/${id}`), {
    method: 'DELETE',
    headers: authHeader(token),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
}

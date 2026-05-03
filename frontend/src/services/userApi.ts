import { apiUrl } from '@/lib/api';
import { PAGE_SIZE } from '@/lib/pagination';
import { authHeader, jsonAuthHeader } from '@/lib/authFetch';
import type { UserRead } from '@/services/authApi';
import { parseApiError } from '@/services/parseApiError';

export type PageUsers = {
  items: UserRead[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type UserUpdateBody = {
  name?: string;
  email?: string;
  password?: string;
};

export async function fetchUser(token: string, userId: number): Promise<UserRead> {
  const res = await fetch(apiUrl(`/api/v1/users/${userId}`), {
    headers: authHeader(token),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<UserRead>;
}

export async function patchUser(token: string, userId: number, body: UserUpdateBody): Promise<UserRead> {
  const res = await fetch(apiUrl(`/api/v1/users/${userId}`), {
    method: 'PATCH',
    headers: jsonAuthHeader(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<UserRead>;
}

export async function fetchUsersPage(
  token: string,
  params: { page?: number; page_size?: number; q?: string },
): Promise<PageUsers> {
  const qs = new URLSearchParams();
  qs.set('page', String(params.page ?? 1));
  qs.set('page_size', String(params.page_size ?? PAGE_SIZE));
  if (params.q?.trim()) {
    qs.set('q', params.q.trim());
  }
  const res = await fetch(apiUrl(`/api/v1/users?${qs}`), { headers: authHeader(token) });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<PageUsers>;
}

export async function deleteUser(token: string, userId: number): Promise<void> {
  const res = await fetch(apiUrl(`/api/v1/users/${userId}`), {
    method: 'DELETE',
    headers: authHeader(token),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
}

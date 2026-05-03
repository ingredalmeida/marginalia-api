import { apiUrl } from '@/lib/api';
import { PAGE_SIZE } from '@/lib/pagination';
import { authHeader, jsonAuthHeader } from '@/lib/authFetch';
import type { Page } from '@/services/bookApi';
import { parseApiError } from '@/services/parseApiError';

export type ReservationRead = {
  id: number;
  user_id: number;
  book_id: number;
  status: string;
  created_at: string;
  hold_until?: string | null;
  book_title?: string | null;
  author_name?: string | null;
  queue_position?: number | null;
};

export async function createReservation(
  token: string,
  body: { user_id: number; book_id: number },
): Promise<ReservationRead> {
  const res = await fetch(apiUrl('/api/v1/reservations'), {
    method: 'POST',
    headers: jsonAuthHeader(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<ReservationRead>;
}

export async function cancelReservation(token: string, reservationId: number): Promise<void> {
  const res = await fetch(apiUrl(`/api/v1/reservations/${reservationId}`), {
    method: 'DELETE',
    headers: authHeader(token),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
}

export async function fetchReservationsForBook(
  token: string,
  bookId: number,
  params: { page?: number; page_size?: number } = {},
): Promise<Page<ReservationRead>> {
  const q = new URLSearchParams();
  q.set('book_id', String(bookId));
  q.set('page', String(params.page ?? 1));
  q.set('page_size', String(params.page_size ?? PAGE_SIZE));
  const res = await fetch(apiUrl(`/api/v1/reservations?${q}`), { headers: authHeader(token) });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<Page<ReservationRead>>;
}

export async function fetchMyPendingReservations(
  token: string,
  params: { page?: number; page_size?: number } = {},
): Promise<Page<ReservationRead>> {
  const q = new URLSearchParams();
  q.set('page', String(params.page ?? 1));
  q.set('page_size', String(params.page_size ?? PAGE_SIZE));
  const res = await fetch(apiUrl(`/api/v1/reservations?${q}`), { headers: authHeader(token) });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<Page<ReservationRead>>;
}

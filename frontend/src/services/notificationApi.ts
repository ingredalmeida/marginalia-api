import { apiUrl } from '@/lib/api';
import { authHeader } from '@/lib/authFetch';
import { parseApiError } from '@/services/parseApiError';

export type NotificationRead = {
  id: number;
  title: string;
  body: string;
  kind: string;
  ref_reservation_id?: number | null;
  read_at: string | null;
  created_at: string;
};

export async function fetchNotifications(token: string, limit = 30): Promise<NotificationRead[]> {
  const q = new URLSearchParams({ limit: String(limit) });
  const res = await fetch(apiUrl(`/api/v1/notifications?${q}`), { headers: authHeader(token) });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<NotificationRead[]>;
}

export async function fetchUnreadNotificationCount(token: string): Promise<number> {
  const res = await fetch(apiUrl('/api/v1/notifications/unread-count'), { headers: authHeader(token) });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  const data = (await res.json()) as { count: number };
  return data.count;
}

export async function markAllNotificationsRead(token: string): Promise<void> {
  const res = await fetch(apiUrl('/api/v1/notifications/read-all'), {
    method: 'POST',
    headers: authHeader(token),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
}

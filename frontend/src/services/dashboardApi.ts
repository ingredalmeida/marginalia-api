import { apiUrl } from '@/lib/api';
import { authHeader } from '@/lib/authFetch';
import { parseApiError } from '@/services/parseApiError';

export type TopBookItem = {
  book_id: number;
  title: string;
  author_name: string;
  loan_count: number;
};

export type DashboardSummary = {
  date_from: string;
  date_to: string;
  book_titles_total: number;
  users_total: number;
  active_loans: number;
  overdue_loans: number;
  loans_started_in_period: number;
  total_fines_brl: string;
  available_titles: number;
  on_loan_titles: number;
  reservations_pending: number;
  reservations_hold: number;
  top_books: TopBookItem[];
};

export async function fetchDashboardSummary(
  token: string,
  dateFrom: string,
  dateTo: string,
): Promise<DashboardSummary> {
  const q = new URLSearchParams({ date_from: dateFrom, date_to: dateTo });
  const res = await fetch(apiUrl(`/api/v1/admin/dashboard?${q}`), { headers: authHeader(token) });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<DashboardSummary>;
}

/** Baixa CSV/PDF dos relatórios admin (mesmo período do painel quando aplicável). */
export async function downloadReportFile(token: string, pathWithQuery: string): Promise<void> {
  const res = await fetch(apiUrl(pathWithQuery), { headers: authHeader(token) });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  const blob = await res.blob();
  const dispo = res.headers.get('Content-Disposition');
  let filename = 'relatorio';
  const m = dispo && /filename="([^"]+)"/.exec(dispo);
  if (m) filename = m[1];
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

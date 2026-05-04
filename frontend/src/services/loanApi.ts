import { apiUrl } from '@/lib/api';
import { PAGE_SIZE } from '@/lib/pagination';
import { authHeader, jsonAuthHeader } from '@/lib/authFetch';
import { parseApiError } from '@/services/parseApiError';

export type LoanRead = {
  id: number;
  user_id: number;
  book_id: number;
  renewal_count: number;
  borrowed_at: string;
  due_at: string;
  returned_at: string | null;
  fine_amount: string | null;
  /** Ativo: multa estimada se devolver agora; devolvido: null (use fine_amount). */
  projected_fine_brl: string | null;
  created_at: string;
  is_active: boolean;
  is_overdue: boolean;
  book_title?: string | null;
  author_name?: string | null;
};

export type PageLoans = {
  items: LoanRead[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

function firstNonEmptyString(...vals: (string | null | undefined)[]): string | null {
  for (const v of vals) {
    if (typeof v === 'string' && v.trim()) return v.trim();
  }
  return null;
}

function normalizeLoanFromApi(raw: Record<string, unknown>): LoanRead {
  const base = raw as unknown as LoanRead;
  return {
    ...base,
    projected_fine_brl: base.projected_fine_brl ?? null,
    book_title: firstNonEmptyString(
      base.book_title,
      raw.book_title as string | undefined,
      raw.bookTitle as string | undefined,
    ),
    author_name: firstNonEmptyString(
      base.author_name,
      raw.author_name as string | undefined,
      raw.authorName as string | undefined,
    ),
  };
}

export type LoanReturnResult = {
  loan: LoanRead;
  fine_amount: string;
};

export async function fetchUserLoans(
  token: string,
  userId: number,
  status: 'active' | 'returned' | 'overdue' | 'all' = 'active',
  page = 1,
  page_size = PAGE_SIZE,
): Promise<PageLoans> {
  const q = new URLSearchParams({ status, page: String(page), page_size: String(page_size) });
  const res = await fetch(apiUrl(`/api/v1/users/${userId}/loans?${q}`), {
    headers: authHeader(token),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  const data = (await res.json()) as PageLoans & { items: Record<string, unknown>[] };
  return {
    ...data,
    items: data.items.map((row) => normalizeLoanFromApi(row)),
  };
}

export async function createLoan(
  token: string,
  body: { user_id: number; book_id: number },
): Promise<LoanRead> {
  const res = await fetch(apiUrl('/api/v1/loans'), {
    method: 'POST',
    headers: jsonAuthHeader(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<LoanRead>;
}

export async function returnLoan(token: string, loanId: number): Promise<LoanReturnResult> {
  const res = await fetch(apiUrl(`/api/v1/loans/${loanId}/return`), {
    method: 'POST',
    headers: authHeader(token),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<LoanReturnResult>;
}

export async function renewLoan(token: string, loanId: number): Promise<LoanRead> {
  const res = await fetch(apiUrl(`/api/v1/loans/${loanId}/renew`), {
    method: 'POST',
    headers: authHeader(token),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<LoanRead>;
}

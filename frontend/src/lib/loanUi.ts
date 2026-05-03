/** Prazo inicial de empréstimo (dias), alinhado ao backend `LOAN_DEFAULT_DAYS`. */
export const LOAN_DEFAULT_DAYS = 14;
/** Dias adicionados em uma renovação (`RENEWAL_EXTRA_DAYS`). */
export const RENEWAL_EXTRA_DAYS = 4;
export const MAX_ACTIVE_LOANS_PER_USER = 3;
export const MAX_PENDING_RESERVATIONS_PER_USER = 3;

/** Texto amigável até a devolução ou atraso. */
export function formatLoanTimeline(dueAt: string, returnedAt: string | null, isOverdue: boolean): string {
  if (returnedAt) {
    return 'Empréstimo encerrado.';
  }
  const due = new Date(dueAt);
  const now = new Date();
  const startOfDue = new Date(due.getFullYear(), due.getMonth(), due.getDate()).getTime();
  const startOfNow = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const dayMs = 86400000;
  const diffDays = Math.round((startOfDue - startOfNow) / dayMs);
  if (isOverdue || diffDays < 0) {
    const late = Math.abs(diffDays);
    return late === 0 ? 'Atrasado: vence hoje.' : `Atrasado há ${late} dia(s).`;
  }
  if (diffDays === 0) return 'Vence hoje.';
  if (diffDays === 1) return 'Falta 1 dia para devolver.';
  return `Faltam ${diffDays} dias para devolver.`;
}

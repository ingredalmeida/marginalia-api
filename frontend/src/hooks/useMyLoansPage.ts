import { useCallback, useEffect, useState } from 'react';

import type { AdminFeedback } from '@/components/AdminFeedbackModal';
import { useAuth } from '@/hooks/useAuth';
import { formatLoanTimeline, RENEWAL_EXTRA_DAYS } from '@/lib/loanUi';
import { PAGE_SIZE } from '@/lib/pagination';
import { fetchUserLoans, renewLoan, returnLoan, type LoanRead } from '@/services/loanApi';
import { cancelReservation, fetchMyPendingReservations, type ReservationRead } from '@/services/reservationApi';

export function useMyLoansPage() {
  const { token, userId } = useAuth();
  const [filter, setFilter] = useState<'active' | 'all'>('active');
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<LoanRead[]>([]);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loanActionId, setLoanActionId] = useState<number | null>(null);
  const [resCancelId, setResCancelId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<AdminFeedback | null>(null);
  const [reservations, setReservations] = useState<ReservationRead[]>([]);
  const [resLoading, setResLoading] = useState(false);

  useEffect(() => {
    setPage(1);
  }, [filter]);

  const loadLoans = useCallback(async () => {
    if (!token || userId == null) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const status = filter === 'active' ? 'active' : 'all';
      const res = await fetchUserLoans(token, userId, status, page, PAGE_SIZE);
      setItems(res.items);
      setPages(res.pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível carregar.');
      setItems([]);
      setPages(1);
    } finally {
      setLoading(false);
    }
  }, [token, userId, filter, page]);

  useEffect(() => {
    void loadLoans();
  }, [loadLoans]);

  const loadReservations = useCallback(async () => {
    if (!token || userId == null) {
      setReservations([]);
      return;
    }
    setResLoading(true);
    try {
      const acc: ReservationRead[] = [];
      let p = 1;
      while (p <= 10) {
        const r = await fetchMyPendingReservations(token, { page: p, page_size: PAGE_SIZE });
        acc.push(...r.items);
        if (p >= r.pages || r.items.length === 0) break;
        p += 1;
      }
      setReservations(acc);
    } catch {
      setReservations([]);
    } finally {
      setResLoading(false);
    }
  }, [token, userId]);

  useEffect(() => {
    void loadReservations();
  }, [loadReservations]);

  const refreshAfterLoanAction = useCallback(async () => {
    await loadLoans();
    await loadReservations();
  }, [loadLoans, loadReservations]);

  const onReturn = useCallback(
    async (loan: LoanRead) => {
      if (!token) return;
      setLoanActionId(loan.id);
      try {
        const res = await returnLoan(token, loan.id);
        const fine = parseFloat(res.fine_amount);
        setFeedback({
          type: 'success',
          message:
            fine > 0
              ? `Devolução registrada. Multa: R$ ${fine.toFixed(2).replace('.', ',')}.`
              : 'Devolução registrada.',
        });
        await refreshAfterLoanAction();
      } catch (e) {
        setFeedback({
          type: 'error',
          message: e instanceof Error ? e.message : 'Não foi possível devolver.',
        });
      } finally {
        setLoanActionId(null);
      }
    },
    [token, refreshAfterLoanAction],
  );

  const onRenew = useCallback(
    async (loan: LoanRead) => {
      if (!token) return;
      setLoanActionId(loan.id);
      try {
        await renewLoan(token, loan.id);
        setFeedback({
          type: 'success',
          message: `Prazo de devolução estendido em ${RENEWAL_EXTRA_DAYS} dias.`,
        });
        await loadLoans();
      } catch (e) {
        setFeedback({
          type: 'error',
          message: e instanceof Error ? e.message : 'Não foi possível renovar.',
        });
      } finally {
        setLoanActionId(null);
      }
    },
    [token, loadLoans],
  );

  const onCancelReservation = useCallback(
    async (r: ReservationRead) => {
      if (!token) return;
      setResCancelId(r.id);
      try {
        await cancelReservation(token, r.id);
        setFeedback({ type: 'success', message: 'Reserva cancelada.' });
        await loadReservations();
      } catch (e) {
        setFeedback({
          type: 'error',
          message: e instanceof Error ? e.message : 'Não foi possível cancelar a reserva.',
        });
      } finally {
        setResCancelId(null);
      }
    },
    [token, loadReservations],
  );

  return {
    filter,
    setFilter,
    page,
    setPage,
    items,
    pages,
    loading,
    error,
    loanActionId,
    resCancelId,
    feedback,
    setFeedback,
    reservations,
    resLoading,
    onReturn,
    onRenew,
    onCancelReservation,
    formatLoanTimeline,
    renewalExtraDays: RENEWAL_EXTRA_DAYS,
  };
}

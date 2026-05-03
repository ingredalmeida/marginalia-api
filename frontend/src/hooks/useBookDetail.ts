import { useCallback, useEffect, useMemo, useState } from 'react';

import type { AdminFeedback } from '@/components/AdminFeedbackModal';
import { useAuth } from '@/hooks/useAuth';
import { PAGE_SIZE } from '@/lib/pagination';
import {
  LOAN_DEFAULT_DAYS,
  MAX_ACTIVE_LOANS_PER_USER,
  MAX_PENDING_RESERVATIONS_PER_USER,
  RENEWAL_EXTRA_DAYS,
} from '@/lib/loanUi';
import { fetchBook, type BookRead } from '@/services/bookApi';
import { createLoan, fetchUserLoans, renewLoan, returnLoan, type LoanRead } from '@/services/loanApi';
import {
  cancelReservation,
  createReservation,
  fetchMyPendingReservations,
  fetchReservationsForBook,
  type ReservationRead,
} from '@/services/reservationApi';

export function useBookDetail(bookId: number) {
  const { token, userId } = useAuth();

  const [book, setBook] = useState<BookRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [myLoan, setMyLoan] = useState<LoanRead | null>(null);
  const [myReservation, setMyReservation] = useState<ReservationRead | null>(null);
  const [queuePosition, setQueuePosition] = useState<number | null>(null);
  const [queueTotal, setQueueTotal] = useState<number | null>(null);
  const [ctxLoading, setCtxLoading] = useState(false);

  const [actionBusy, setActionBusy] = useState(false);
  const [feedback, setFeedback] = useState<AdminFeedback | null>(null);

  const reloadBook = useCallback(async () => {
    if (!token || !Number.isFinite(bookId) || bookId < 1) return;
    const b = await fetchBook(token, bookId);
    setBook(b);
  }, [token, bookId]);

  const reloadContext = useCallback(async () => {
    if (!token || userId == null || !Number.isFinite(bookId) || bookId < 1) {
      setMyLoan(null);
      setMyReservation(null);
      setQueuePosition(null);
      setQueueTotal(null);
      return;
    }
    setCtxLoading(true);
    try {
      const activePage = await fetchUserLoans(token, userId, 'active', 1, 50);
      const loan = activePage.items.find((l) => l.book_id === bookId && l.is_active) ?? null;
      setMyLoan(loan);

      const mine = await fetchMyPendingReservations(token, { page: 1, page_size: 50 });
      const res =
        mine.items.find(
          (r) => r.book_id === bookId && (r.status === 'pending' || r.status === 'hold'),
        ) ?? null;
      setMyReservation(res);

      if (!res) {
        setQueuePosition(null);
        setQueueTotal(null);
        return;
      }
      setQueuePosition(res.queue_position ?? null);
      const qPage = await fetchReservationsForBook(token, bookId, { page: 1, page_size: PAGE_SIZE });
      setQueueTotal(qPage.total);
    } catch {
      setMyLoan(null);
      setMyReservation(null);
      setQueuePosition(null);
      setQueueTotal(null);
    } finally {
      setCtxLoading(false);
    }
  }, [token, userId, bookId]);

  useEffect(() => {
    if (!Number.isFinite(bookId) || bookId < 1) {
      setError('ID inválido.');
      setLoading(false);
      return;
    }
    if (!token) {
      setError('Sessão inválida. Faça login novamente.');
      setLoading(false);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const b = await fetchBook(token, bookId);
        if (!cancelled) {
          setBook(b);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setBook(null);
          setError(e instanceof Error ? e.message : 'Erro ao carregar.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [bookId, token]);

  useEffect(() => {
    if (!book || !token || userId == null) return;
    void reloadContext();
  }, [book, token, userId, reloadContext]);

  const refreshAll = useCallback(async () => {
    await reloadBook();
    await reloadContext();
  }, [reloadBook, reloadContext]);

  const onBorrow = useCallback(async () => {
    if (!token || userId == null || !book) return;
    setActionBusy(true);
    try {
      await createLoan(token, { user_id: userId, book_id: book.id });
      setFeedback({
        type: 'success',
        message: `Empréstimo registrado. Você tem ${LOAN_DEFAULT_DAYS} dias para devolver.`,
      });
      await refreshAll();
    } catch (e) {
      setFeedback({
        type: 'error',
        message: e instanceof Error ? e.message : 'Não foi possível emprestar.',
      });
    } finally {
      setActionBusy(false);
    }
  }, [token, userId, book, refreshAll]);

  const onReserve = useCallback(async () => {
    if (!token || userId == null || !book) return;
    setActionBusy(true);
    try {
      await createReservation(token, { user_id: userId, book_id: book.id });
      setFeedback({
        type: 'success',
        message:
          'Você entrou na fila de reserva. Quando o exemplar for devolvido, avisaremos na ordem da fila.',
      });
      await refreshAll();
    } catch (e) {
      setFeedback({
        type: 'error',
        message: e instanceof Error ? e.message : 'Não foi possível reservar.',
      });
    } finally {
      setActionBusy(false);
    }
  }, [token, userId, book, refreshAll]);

  const onCancelReserve = useCallback(async () => {
    if (!token || !myReservation) return;
    setActionBusy(true);
    try {
      await cancelReservation(token, myReservation.id);
      setFeedback({ type: 'success', message: 'Reserva cancelada.' });
      await refreshAll();
    } catch (e) {
      setFeedback({
        type: 'error',
        message: e instanceof Error ? e.message : 'Não foi possível cancelar.',
      });
    } finally {
      setActionBusy(false);
    }
  }, [token, myReservation, refreshAll]);

  const onReturn = useCallback(async () => {
    if (!token || !myLoan) return;
    setActionBusy(true);
    try {
      const res = await returnLoan(token, myLoan.id);
      const fine = parseFloat(res.fine_amount);
      setFeedback({
        type: 'success',
        message:
          fine > 0
            ? `Devolução registrada. Multa por atraso: R$ ${fine.toFixed(2).replace('.', ',')}.`
            : 'Devolução registrada. Obrigada por devolver no prazo.',
      });
      await refreshAll();
    } catch (e) {
      setFeedback({
        type: 'error',
        message: e instanceof Error ? e.message : 'Não foi possível devolver.',
      });
    } finally {
      setActionBusy(false);
    }
  }, [token, myLoan, refreshAll]);

  const onRenew = useCallback(async () => {
    if (!token || !myLoan) return;
    setActionBusy(true);
    try {
      await renewLoan(token, myLoan.id);
      setFeedback({
        type: 'success',
        message: `Prazo estendido em mais ${RENEWAL_EXTRA_DAYS} dias. Confira a nova data de devolução.`,
      });
      await refreshAll();
    } catch (e) {
      setFeedback({
        type: 'error',
        message: e instanceof Error ? e.message : 'Não foi possível renovar.',
      });
    } finally {
      setActionBusy(false);
    }
  }, [token, myLoan, refreshAll]);

  const canTryRenew = useMemo(
    () =>
      Boolean(myLoan && myLoan.is_active && !myLoan.is_overdue && myLoan.renewal_count < 1),
    [myLoan],
  );

  return {
    token,
    userId,
    book,
    loading,
    error,
    myLoan,
    myReservation,
    queuePosition,
    queueTotal,
    ctxLoading,
    actionBusy,
    feedback,
    setFeedback,
    onBorrow,
    onReserve,
    onCancelReserve,
    onReturn,
    onRenew,
    canTryRenew,
    loanUi: {
      LOAN_DEFAULT_DAYS,
      MAX_ACTIVE_LOANS_PER_USER,
      MAX_PENDING_RESERVATIONS_PER_USER,
      RENEWAL_EXTRA_DAYS,
    },
  };
}

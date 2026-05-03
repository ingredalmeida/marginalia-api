import { useCallback, useEffect, useState } from 'react';

import { useAuth } from '@/hooks/useAuth';
import { fetchDashboardSummary, type DashboardSummary } from '@/services/dashboardApi';

function toYMD(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function defaultRange(): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(from.getDate() - 30);
  return { from: toYMD(from), to: toYMD(to) };
}

export function useAdminDashboard() {
  const { token } = useAuth();
  const [{ from: dateFrom, to: dateTo }, setRange] = useState(defaultRange);
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) {
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDashboardSummary(token, dateFrom, dateTo);
      setData(res);
    } catch {
      setData(null);
      setError('Não foi possível carregar os dados agora. Tente de novo em instantes.');
    } finally {
      setLoading(false);
    }
  }, [token, dateFrom, dateTo]);

  useEffect(() => {
    void load();
  }, [load]);

  const setDateFrom = (v: string) => setRange((r) => ({ ...r, from: v }));
  const setDateTo = (v: string) => setRange((r) => ({ ...r, to: v }));

  return {
    token,
    dateFrom,
    dateTo,
    setDateFrom,
    setDateTo,
    data,
    loading,
    error,
    reload: load,
  };
}

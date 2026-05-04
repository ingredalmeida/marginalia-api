import { useCallback, useEffect, useState } from 'react';

import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { useAdminFeedback } from '@/hooks/useAdminFeedback';
import { useAuth } from '@/hooks/useAuth';
import { PAGE_SIZE } from '@/lib/pagination';
import { deleteUser, fetchUsersPage, patchUser, type PageUsers } from '@/services/userApi';

export function useAdminUsers() {
  const { token, userId, refreshProfile } = useAuth();
  const { feedback, setFeedback, dismissFeedback } = useAdminFeedback();

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearch = useDebouncedValue(searchInput, 350);

  const [data, setData] = useState<PageUsers | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [editId, setEditId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editPassword, setEditPassword] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    const q = debouncedSearch.trim();
    try {
      const res = await fetchUsersPage(token, {
        page: q ? 1 : page,
        page_size: PAGE_SIZE,
        ...(q ? { q } : {}),
      });
      setData(res);
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : 'Não foi possível carregar os usuários.');
    } finally {
      setLoading(false);
    }
  }, [token, page, debouncedSearch]);

  useEffect(() => {
    void load();
  }, [load]);

  const startEdit = (id: number, name: string, email: string) => {
    setEditId(id);
    setEditName(name);
    setEditEmail(email);
    setEditPassword('');
  };

  const cancelEdit = () => {
    setEditId(null);
  };

  const saveEdit = async () => {
    if (!token || editId == null) return;
    setSaving(true);
    try {
      const body: { name?: string; email?: string; password?: string } = {};
      const row = data?.items.find((u) => u.id === editId);
      if (row && editName.trim() !== row.name) body.name = editName.trim();
      if (row && editEmail.trim().toLowerCase() !== row.email.toLowerCase()) {
        body.email = editEmail.trim().toLowerCase();
      }
      if (editPassword.length > 0) body.password = editPassword;
      if (Object.keys(body).length === 0) {
        cancelEdit();
        setFeedback({ type: 'success', message: 'Nenhuma alteração para salvar.' });
        return;
      }
      await patchUser(token, editId, body);
      if (editId === userId) {
        await refreshProfile();
      }
      cancelEdit();
      await load();
      setFeedback({ type: 'success', message: 'Dados do usuário atualizados.' });
    } catch (e) {
      setFeedback({
        type: 'error',
        message: e instanceof Error ? e.message : 'Não foi possível salvar.',
      });
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (id: number) => {
    if (!token || id === userId) return;
    try {
      await deleteUser(token, id);
      await load();
      setFeedback({ type: 'success', message: 'Usuário removido do sistema.' });
    } catch (e) {
      setFeedback({
        type: 'error',
        message: e instanceof Error ? e.message : 'Não foi possível excluir.',
      });
    }
  };

  const pages = data?.pages ?? 0;
  const canPrev = page > 1;
  const canNext = page < pages;

  return {
    token,
    userId,
    page,
    setPage,
    searchInput,
    setSearchInput,
    debouncedSearch,
    data,
    error,
    loading,
    editId,
    editName,
    setEditName,
    editEmail,
    setEditEmail,
    editPassword,
    setEditPassword,
    saving,
    feedback,
    dismissFeedback,
    load,
    startEdit,
    cancelEdit,
    saveEdit,
    onDelete,
    pages,
    canPrev,
    canNext,
  };
}

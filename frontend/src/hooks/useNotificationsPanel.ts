import { useCallback, useEffect, useRef, useState } from 'react';

import { useAuth } from '@/hooks/useAuth';
import {
  fetchNotifications,
  fetchUnreadNotificationCount,
  markAllNotificationsRead,
  type NotificationRead,
} from '@/services/notificationApi';

export function useNotificationsPanel() {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationRead[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  const refreshUnread = useCallback(async () => {
    if (!token) {
      setUnread(0);
      return;
    }
    try {
      const n = await fetchUnreadNotificationCount(token);
      setUnread(n);
    } catch {
      setUnread(0);
    }
  }, [token]);

  const loadList = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const list = await fetchNotifications(token, 25);
      setItems(list);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void refreshUnread();
    const t = window.setInterval(() => void refreshUnread(), 45000);
    return () => window.clearInterval(t);
  }, [refreshUnread]);

  useEffect(() => {
    if (!open) return;
    void loadList();
    void refreshUnread();
  }, [open, loadList, refreshUnread]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  const onMarkAllRead = async () => {
    if (!token) return;
    try {
      await markAllNotificationsRead(token);
      setItems((prev) => prev.map((x) => ({ ...x, read_at: x.read_at ?? new Date().toISOString() })));
      await refreshUnread();
    } catch {
      /* ignore */
    }
  };

  return {
    token,
    wrapRef,
    open,
    setOpen,
    items,
    unread,
    loading,
    onMarkAllRead,
  };
}

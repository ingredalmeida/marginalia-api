import { useEffect, useState } from 'react';

import { useAuth } from '@/hooks/useAuth';
import { patchUser } from '@/services/userApi';

export function useProfileEdit() {
  const { token, userId, profile, refreshProfile } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (profile) {
      setName(profile.name);
      setEmail(profile.email);
    }
  }, [profile]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || userId == null) {
      return;
    }
    setError(null);
    setSaved(false);
    setLoading(true);
    try {
      const body: { name?: string; email?: string; password?: string } = {};
      if (name.trim() !== profile?.name) {
        body.name = name.trim();
      }
      if (email.trim().toLowerCase() !== profile?.email.toLowerCase()) {
        body.email = email.trim().toLowerCase();
      }
      if (password.length > 0) {
        body.password = password;
      }
      if (Object.keys(body).length === 0) {
        setSaved(true);
        return;
      }
      await patchUser(token, userId, body);
      setPassword('');
      await refreshProfile();
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível salvar.');
    } finally {
      setLoading(false);
    }
  };

  return {
    name,
    setName,
    email,
    setEmail,
    password,
    setPassword,
    error,
    saved,
    loading,
    onSubmit,
  };
}

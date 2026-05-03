import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '@/hooks/useAuth';
import { loginRequest, registerRequest } from '@/services/authApi';

export type AuthFormMode = 'login' | 'signup';

export function useAuthForm() {
  const navigate = useNavigate();
  const { loginWithToken } = useAuth();
  const [mode, setMode] = useState<AuthFormMode>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const setModeClearError = (m: AuthFormMode) => {
    setMode(m);
    setError(null);
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === 'signup') {
        await registerRequest(name, email, password);
      }
      const { access_token } = await loginRequest(email, password);
      loginWithToken(access_token);
      navigate('/home', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível concluir.');
    } finally {
      setLoading(false);
    }
  };

  return {
    mode,
    setMode: setModeClearError,
    name,
    setName,
    email,
    setEmail,
    password,
    setPassword,
    error,
    loading,
    onSubmit,
  };
}

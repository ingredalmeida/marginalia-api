import { apiUrl } from '@/lib/api';
import { parseApiError } from '@/services/parseApiError';

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type UserRead = {
  id: number;
  name: string;
  email: string;
  is_admin: boolean;
  created_at: string;
};

export async function loginRequest(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(apiUrl('/api/v1/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<TokenResponse>;
}

export async function registerRequest(name: string, email: string, password: string): Promise<UserRead> {
  const res = await fetch(apiUrl('/api/v1/auth/register'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: name.trim(),
      email: email.trim().toLowerCase(),
      password,
    }),
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<UserRead>;
}

import { createContext } from 'react';

import type { UserRead } from '@/services/authApi';

export type AuthContextValue = {
  token: string | null;
  userId: number | null;
  profile: UserRead | null;
  profileLoading: boolean;
  refreshProfile: () => Promise<void>;
  loginWithToken: (accessToken: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

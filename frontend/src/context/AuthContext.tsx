import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { AuthContext } from '@/context/auth-context';
import { clearStoredToken, getStoredToken, setStoredToken } from '@/lib/authStorage';
import { authHeader } from '@/lib/authFetch';
import { apiUrl } from '@/lib/api';
import { decodeUserIdFromAccessToken } from '@/lib/jwtDecode';
import type { UserRead } from '@/services/authApi';

const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [profile, setProfile] = useState<UserRead | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  const userId = useMemo(() => (token ? decodeUserIdFromAccessToken(token) : null), [token]);

  useEffect(() => {
    if (token && userId == null) {
      clearStoredToken();
      setToken(null);
    }
  }, [token, userId]);

  const loginWithToken = useCallback((accessToken: string) => {
    setStoredToken(accessToken);
    setToken(accessToken);
  }, []);

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setProfile(null);
  }, []);

  const refreshProfile = useCallback(async () => {
    if (!token || userId == null) {
      setProfile(null);
      setProfileLoading(false);
      return;
    }
    setProfileLoading(true);
    try {
      const res = await fetch(apiUrl(`/api/v1/users/${userId}`), { headers: authHeader(token) });
      if (res.status === 401) {
        clearStoredToken();
        setToken(null);
        setProfile(null);
        return;
      }
      if (!res.ok) {
        setProfile(null);
        return;
      }
      setProfile((await res.json()) as UserRead);
    } catch {
      setProfile(null);
    } finally {
      setProfileLoading(false);
    }
  }, [token, userId]);

  useEffect(() => {
    void refreshProfile();
  }, [refreshProfile]);

  const value = useMemo(
    () => ({
      token,
      userId,
      profile,
      profileLoading,
      refreshProfile,
      loginWithToken,
      logout,
      isAuthenticated: Boolean(token),
    }),
    [token, userId, profile, profileLoading, refreshProfile, loginWithToken, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export { AuthProvider };

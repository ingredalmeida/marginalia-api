import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '@/hooks/useAuth';

const RequireAuth = () => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to='/' replace />;
  }
  return <Outlet />;
};

export default RequireAuth;

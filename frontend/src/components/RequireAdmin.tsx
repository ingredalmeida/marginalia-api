import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '@/hooks/useAuth';

const RequireAdmin = () => {
  const { profile, profileLoading, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to='/' replace />;
  }
  if (profileLoading) {
    return (
      <div className='p-6 lg:p-10'>
        <p className='text-sm text-muted-foreground'>Carregando…</p>
      </div>
    );
  }
  if (!profile?.is_admin) {
    return <Navigate to='/home' replace />;
  }
  return <Outlet />;
};

export default RequireAdmin;

import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import NotificationsBell from '@/components/NotificationsBell';
import { useAuth } from '@/hooks/useAuth';

/** Sininho + sair: presente em todas as páginas autenticadas (via AppLayout). */
const AppUserToolbar = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/', { replace: true });
  };

  return (
    <header className='flex shrink-0 justify-end items-center gap-2 px-6 lg:px-10 pt-6 pb-2'>
      <NotificationsBell />
      <button
        type='button'
        onClick={handleLogout}
        className='w-12 h-12 rounded-full bg-card border border-border flex items-center justify-center hover:bg-secondary'
        title='Sair'
      >
        <LogOut className='w-5 h-5 text-ink' />
      </button>
    </header>
  );
};

export default AppUserToolbar;

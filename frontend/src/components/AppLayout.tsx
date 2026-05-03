import { Outlet } from 'react-router-dom';

import AppSidebar from '@/components/AppSidebar';
import AppUserToolbar from '@/components/AppUserToolbar';

const AppLayout = () => {
  return (
    <div className='min-h-screen bg-background flex'>
      <AppSidebar />
      <div className='flex-1 min-w-0 flex flex-col min-h-0'>
        <AppUserToolbar />
        <div className='flex-1 min-h-0'>
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AppLayout;

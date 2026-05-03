import { Navigate, Route, Routes } from 'react-router-dom';

import AppLayout from '@/components/AppLayout';
import RequireAdmin from '@/components/RequireAdmin';
import RequireAuth from '@/components/RequireAuth';
import AdminAuthors from '@/pages/AdminAuthors';
import AdminBooks from '@/pages/AdminBooks';
import AdminDashboard from '@/pages/AdminDashboard';
import AdminUsers from '@/pages/AdminUsers';
import Auth from '@/pages/Auth';
import BookDetail from '@/pages/BookDetail';
import Explore from '@/pages/Explore';
import Home from '@/pages/Home';
import MyLoans from '@/pages/MyLoans';
import ProfileEdit from '@/pages/ProfileEdit';

const App = () => {
  return (
    <Routes>
      <Route path='/' element={<Auth />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path='/home' element={<Home />} />
          <Route path='/explorar' element={<Explore />} />
          <Route path='/livro/:id' element={<BookDetail />} />
          <Route path='/perfil' element={<ProfileEdit />} />
          <Route path='/emprestimos' element={<MyLoans />} />
          <Route element={<RequireAdmin />}>
            <Route path='/admin/usuarios' element={<AdminUsers />} />
            <Route path='/admin/autores' element={<AdminAuthors />} />
            <Route path='/admin/livros' element={<AdminBooks />} />
            <Route path='/admin/dashboard' element={<AdminDashboard />} />
          </Route>
        </Route>
      </Route>
      <Route path='*' element={<Navigate to='/' replace />} />
    </Routes>
  );
};

export default App;

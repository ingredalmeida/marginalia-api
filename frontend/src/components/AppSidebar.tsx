import { NavLink } from 'react-router-dom';
import {
  BookMarked,
  BookOpen,
  Compass,
  ContactRound,
  Grid3x3,
  LayoutDashboard,
  LibraryBig,
  PanelLeftClose,
  PanelLeftOpen,
  Users,
} from 'lucide-react';

import { useAuth } from '@/hooks/useAuth';
import { useSidebarExpanded } from '@/hooks/useSidebarExpanded';
import { classNames } from '@/services/string';

const AppSidebar = () => {
  const { profile } = useAuth();
  const isAdmin = Boolean(profile?.is_admin);
  const { expanded, toggle } = useSidebarExpanded();

  const initial =
    profile?.name?.trim()?.charAt(0)?.toLocaleUpperCase('pt-BR') ??
    profile?.email?.trim()?.charAt(0)?.toLocaleUpperCase('pt-BR') ??
    '?';

  const navBtn = (isActive: boolean) =>
    classNames(
      'flex items-center gap-3 rounded-xl py-2.5 transition w-full text-left',
      expanded ? 'px-3' : 'px-0 justify-center',
      isActive ? 'bg-coral text-cream shadow-soft' : 'text-muted-foreground hover:bg-secondary',
    );

  return (
    <aside
      className={classNames(
        'bg-card border-r border-border flex flex-col shrink-0 sticky top-0 h-screen py-6 transition-[width] duration-300 ease-out',
        expanded ? 'w-64 px-3' : 'w-20 px-0 items-center',
      )}
    >
      <div
        className={classNames(
          'mb-6 shrink-0 flex items-center gap-3',
          expanded ? 'w-full' : 'justify-center w-full',
        )}
      >
        <NavLink
          to='/home'
          className='w-11 h-11 rounded-xl bg-ink flex items-center justify-center shrink-0 text-cream no-underline hover:opacity-90 transition'
          title='Início'
        >
          <BookOpen className='w-5 h-5 text-cream' />
        </NavLink>
        {expanded && (
          <span className='font-serif text-xl text-ink truncate min-w-0'>Marginália</span>
        )}
      </div>

      <nav className={classNames('flex flex-col gap-1 flex-1 min-h-0', expanded ? 'w-full' : 'items-center')}>
        <NavLink to='/home' end className={({ isActive }) => navBtn(isActive)} title='Início'>
          <Grid3x3 className='w-5 h-5 shrink-0' />
          {expanded && <span className='text-sm font-medium'>Início</span>}
        </NavLink>
        <NavLink to='/explorar' className={({ isActive }) => navBtn(isActive)} title='Explorar acervo'>
          <Compass className='w-5 h-5 shrink-0' />
          {expanded && <span className='text-sm font-medium'>Explorar</span>}
        </NavLink>
        <NavLink
          to='/emprestimos'
          className={({ isActive }) => navBtn(isActive)}
          title='Seus empréstimos'
        >
          <LibraryBig className='w-5 h-5 shrink-0' />
          {expanded && <span className='text-sm font-medium'>Seus empréstimos</span>}
        </NavLink>

        <NavLink
          to='/perfil'
          className={({ isActive }) =>
            classNames(navBtn(isActive), expanded ? 'mt-4 border-t border-border pt-4' : 'mt-4')
          }
          title='Editar perfil'
        >
          <span
            className={classNames(
              'rounded-full bg-gradient-hero text-cream font-serif flex items-center justify-center shrink-0',
              expanded ? 'w-10 h-10 text-lg' : 'w-11 h-11 text-base',
            )}
          >
            {initial}
          </span>
          {expanded && <span className='text-sm font-medium'>Editar perfil</span>}
        </NavLink>

        {isAdmin && (
          <>
            <div
              className={classNames(
                'shrink-0 border-t border-border mt-3',
                expanded ? 'w-full pt-3' : 'w-8 pt-3 mx-auto',
              )}
              aria-hidden
            />
            <NavLink
              to='/admin/usuarios'
              className={({ isActive }) => navBtn(isActive)}
              title='Gerenciar usuários'
            >
              <Users className='w-5 h-5 shrink-0' />
              {expanded && <span className='text-sm font-medium'>Gerenciar usuários</span>}
            </NavLink>
            <NavLink
              to='/admin/autores'
              className={({ isActive }) => navBtn(isActive)}
              title='Gerenciar autores'
            >
              <ContactRound className='w-5 h-5 shrink-0' />
              {expanded && <span className='text-sm font-medium'>Gerenciar autores</span>}
            </NavLink>
            <NavLink
              to='/admin/livros'
              className={({ isActive }) => navBtn(isActive)}
              title='Gerenciar livros'
            >
              <BookMarked className='w-5 h-5 shrink-0' />
              {expanded && <span className='text-sm font-medium'>Gerenciar livros</span>}
            </NavLink>
            <NavLink
              to='/admin/dashboard'
              className={({ isActive }) => navBtn(isActive)}
              title='Dashboard'
            >
              <LayoutDashboard className='w-5 h-5 shrink-0' />
              {expanded && <span className='text-sm font-medium'>Dashboard</span>}
            </NavLink>
          </>
        )}
      </nav>

      <div className={classNames('mt-auto pt-4 shrink-0', expanded ? 'w-full' : 'flex justify-center w-full')}>
        <button
          type='button'
          onClick={toggle}
          className={classNames(
            'rounded-xl border border-border flex items-center justify-center text-ink hover:bg-secondary transition',
            expanded ? 'w-full h-11 gap-2 px-3' : 'w-11 h-11',
          )}
          title={expanded ? 'Recolher menu' : 'Abrir menu'}
          aria-expanded={expanded}
        >
          {expanded ? <PanelLeftClose className='w-5 h-5 shrink-0' /> : <PanelLeftOpen className='w-5 h-5 shrink-0' />}
          {expanded && <span className='text-sm font-medium'>Recolher</span>}
        </button>
      </div>
    </aside>
  );
};

export default AppSidebar;

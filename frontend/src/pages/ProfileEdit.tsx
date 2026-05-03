import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

import Button from '@/components/Button';
import { Input } from '@/components/Input';
import { Label } from '@/components/Label';
import { useProfileEdit } from '@/hooks/useProfileEdit';

const ProfileEdit = () => {
  const { name, setName, email, setEmail, password, setPassword, error, saved, loading, onSubmit } = useProfileEdit();

  return (
    <div className='flex flex-col min-h-screen'>
      <div className='p-6 lg:p-10 shrink-0 self-start'>
        <Link
          to='/home'
          className='inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-ink'
        >
          <ArrowLeft className='w-4 h-4' />
          Voltar
        </Link>
      </div>
      <div className='flex-1 flex flex-col items-center justify-center px-6 pb-16 lg:pb-20'>
        <div className='w-full max-w-md'>
          <h1 className='font-serif text-4xl text-ink mb-2 text-center'>Editar perfil</h1>
          <p className='text-muted-foreground mb-8 text-center'>Atualize nome, e-mail ou senha.</p>

          <form className='space-y-5' onSubmit={onSubmit}>
            {error && (
              <p className='text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-xl px-4 py-3'>
                {error}
              </p>
            )}
            {saved && !error && (
              <p className='text-sm text-teal bg-teal/10 border border-teal/20 rounded-xl px-4 py-3 text-center'>
                Alterações salvas.
              </p>
            )}

            <div className='space-y-2'>
              <Label htmlFor='profile-name'>Nome</Label>
              <Input
                id='profile-name'
                value={name}
                onChange={(ev) => setName(ev.target.value)}
                className='h-12 rounded-xl'
                required
                minLength={1}
              />
            </div>
            <div className='space-y-2'>
              <Label htmlFor='profile-email'>E-mail</Label>
              <Input
                id='profile-email'
                type='email'
                value={email}
                onChange={(ev) => setEmail(ev.target.value)}
                className='h-12 rounded-xl'
                required
              />
            </div>
            <div className='space-y-2'>
              <Label htmlFor='profile-password'>Nova senha (opcional)</Label>
              <Input
                id='profile-password'
                type='password'
                value={password}
                onChange={(ev) => setPassword(ev.target.value)}
                placeholder='Deixe em branco para manter'
                className='h-12 rounded-xl'
                minLength={password ? 8 : undefined}
                maxLength={128}
              />
            </div>

            <Button type='submit' loading={loading} disabled={loading} size='lg' className='w-full h-12 rounded-xl'>
              Salvar
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ProfileEdit;

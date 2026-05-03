import { Link, Navigate } from 'react-router-dom';
import { ArrowRight, BookOpen, Lock, Mail, User } from 'lucide-react';

import Button from '@/components/Button';
import { AUTH_SPINE_DECOR } from '@/data/authSpines';
import { useAuthForm } from '@/hooks/useAuthForm';
import { useAuth } from '@/hooks/useAuth';
import { Input } from '@/components/Input';
import { Label } from '@/components/Label';

const Auth = () => {
  const { isAuthenticated } = useAuth();
  const { mode, setMode, name, setName, email, setEmail, password, setPassword, error, loading, onSubmit } = useAuthForm();

  if (isAuthenticated) {
    return <Navigate to='/home' replace />;
  }

  return (
    <div className='min-h-screen bg-background grid lg:grid-cols-2'>
      <aside className='relative hidden lg:flex flex-col justify-between overflow-hidden bg-gradient-warm p-12'>
        <header className='flex items-center justify-between text-xs tracking-[0.3em] text-muted-foreground'>
          <span>MRG</span>
          <span>VOL · I</span>
          <span>2026</span>
        </header>

        <div className='relative'>
          <h1 className='font-serif text-6xl xl:text-7xl text-center text-ink leading-[0.95] text-balance'>
            Sua biblioteca
            <br />
            <em className='text-coral not-italic'>pessoal</em>
          </h1>

          <div className='mt-12 flex items-end justify-center gap-2 px-4 min-h-[20rem]'>
            {AUTH_SPINE_DECOR.map((s, i) => (
              <div
                key={i}
                className={`${s.color} ${s.w} ${s.h} ${s.rotate} rounded-sm shadow-soft flex items-end justify-center pb-4 origin-bottom transition-transform hover:-translate-y-2`}
              >
                <span
                  className='text-[10px] tracking-[0.25em] text-cream font-semibold uppercase'
                  style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
                >
                  {s.label}
                </span>
              </div>
            ))}
          </div>
          <div className='h-2 bg-ink/80 rounded-sm mx-4 -mt-1' />
        </div>

        <footer className='flex w-full justify-end text-xs tracking-[0.3em] text-muted-foreground'>
          <span>BIBLIOTECA · DIGITAL · PÚBLICA</span>
        </footer>
      </aside>

      <main className='flex items-center justify-center p-6 sm:p-12 bg-card'>
        <div className='w-full max-w-md animate-fade-up'>
          <Link to='/' className='inline-flex items-center gap-2 mb-12'>
            <div className='w-9 h-9 rounded-lg bg-ink flex items-center justify-center'>
              <BookOpen className='w-5 h-5 text-cream' />
            </div>
            <span className='font-serif text-xl text-ink'>Marginália</span>
          </Link>

          <h2 className='font-serif text-4xl text-ink mb-2'>
            {mode === 'login' ? 'Bem-vind@ de volta.' : 'Comece a ler.'}
          </h2>
          <p className='text-muted-foreground mb-8'>
            {mode === 'login'
              ? 'Entre na sua biblioteca e continue de onde parou.'
              : 'Crie sua conta e monte uma estante feita só para você.'}
          </p>

          <div className='inline-flex bg-secondary rounded-full p-1 mb-8'>
            {(['login', 'signup'] as const).map((m) => (
              <button
                key={m}
                type='button'
                onClick={() => setMode(m)}
                className={`px-5 py-2 text-sm rounded-full transition-all ${
                  mode === m ? 'bg-ink text-cream shadow-soft' : 'text-muted-foreground'
                }`}
              >
                {m === 'login' ? 'Entrar' : 'Cadastrar'}
              </button>
            ))}
          </div>

          <form className='space-y-5' onSubmit={onSubmit}>
            {error && (
              <p className='text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-xl px-4 py-3'>
                {error}
              </p>
            )}

            {mode === 'signup' && (
              <div className='space-y-2'>
                <Label htmlFor='name'>Nome</Label>
                <div className='relative'>
                  <User className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground' />
                  <Input
                    id='name'
                    name='name'
                    autoComplete='name'
                    placeholder='Como devemos te chamar?'
                    className='pl-10 h-12 rounded-xl bg-background'
                    value={name}
                    onChange={(ev) => setName(ev.target.value)}
                    required
                    minLength={1}
                  />
                </div>
              </div>
            )}

            <div className='space-y-2'>
              <Label htmlFor='email'>E-mail</Label>
              <div className='relative'>
                <Mail className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground' />
                <Input
                  id='email'
                  name='email'
                  type='email'
                  autoComplete={mode === 'login' ? 'email' : 'email'}
                  placeholder='voce@exemplo.com'
                  className='pl-10 h-12 rounded-xl bg-background'
                  value={email}
                  onChange={(ev) => setEmail(ev.target.value)}
                  required
                />
              </div>
            </div>

            <div className='space-y-2'>
              <Label htmlFor='password'>Senha</Label>
              <div className='relative'>
                <Lock className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground' />
                <Input
                  id='password'
                  name='password'
                  type='password'
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                  placeholder='Mínimo 8 caracteres'
                  className='pl-10 h-12 rounded-xl bg-background'
                  value={password}
                  onChange={(ev) => setPassword(ev.target.value)}
                  required
                  minLength={8}
                  maxLength={128}
                />
              </div>
              {mode === 'login' && (
                <button type='button' className='text-xs text-muted-foreground hover:text-coral transition'>
                  Esqueci a senha
                </button>
              )}
            </div>

            <Button
              type='submit'
              loading={loading}
              disabled={loading}
              size='lg'
              colorSchema='primary'
              className='w-full h-12 rounded-xl text-base group'
            >
              {mode === 'login' ? 'Entrar na biblioteca' : 'Criar conta'}
              <ArrowRight className='w-4 h-4 ml-2 group-hover:translate-x-1 transition shrink-0' />
            </Button>
          </form>
        </div>
      </main>
    </div>
  );
};

export default Auth;

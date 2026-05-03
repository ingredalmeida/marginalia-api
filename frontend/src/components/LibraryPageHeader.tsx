import { FormEvent, useEffect, useState } from 'react';
import { Search } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';

import Button from '@/components/Button';
import { Input } from '@/components/Input';

const LibraryPageHeader = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const qFromUrl = searchParams.get('q') ?? '';
  const [draft, setDraft] = useState(qFromUrl);

  useEffect(() => {
    setDraft(qFromUrl);
  }, [qFromUrl]);

  const applySearch = (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed) {
      setSearchParams({}, { replace: true });
      return;
    }
    setSearchParams({ q: trimmed }, { replace: true });
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    applySearch(draft);
  };

  return (
    <header className='mb-10'>
      <form onSubmit={onSubmit} className='relative min-w-0'>
        <Search className='absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground pointer-events-none' />
        <Input
          name='q'
          value={draft}
          onChange={(ev) => setDraft(ev.target.value)}
          placeholder='Título ou nome do autor…'
          className='h-14 w-full pl-14 pr-28 rounded-full bg-card border-border text-base'
          aria-label='Buscar no acervo'
        />
        <Button
          type='submit'
          colorSchema='styled'
          className='absolute right-2 top-1/2 -translate-y-1/2 h-10 px-6 rounded-full bg-gradient-hero text-cream hover:opacity-90 border-0 shadow-none'
        >
          Buscar
        </Button>
      </form>
    </header>
  );
};

export default LibraryPageHeader;

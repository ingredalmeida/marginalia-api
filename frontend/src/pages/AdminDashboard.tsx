import type { ReactNode } from 'react';

import Button from '@/components/Button';
import { Input } from '@/components/Input';
import { Label } from '@/components/Label';
import { useAdminDashboard } from '@/hooks/useAdminDashboard';
import { downloadReportFile } from '@/services/dashboardApi';

function formatBRDate(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  if (!y || !m || !d) return iso;
  return new Date(y, m - 1, d).toLocaleDateString('pt-BR');
}

function currencyBRL(raw: string): string {
  const n = Number.parseFloat(raw.replace(',', '.'));
  if (!Number.isFinite(n)) return raw;
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

const AdminDashboard = () => {
  const { token, dateFrom, dateTo, setDateFrom, setDateTo, data, loading, error, reload } =
    useAdminDashboard();

  const periodQuery = `date_from=${encodeURIComponent(dateFrom)}&date_to=${encodeURIComponent(dateTo)}`;

  const download = (path: string) => {
    if (!token) return;
    void downloadReportFile(token, path).catch(() => {
    });
  };

  const Kpi = ({ label, value }: { label: string; value: ReactNode }) => (
    <div className='bg-card border border-border rounded-2xl p-5'>
      <p className='text-xs tracking-wide text-muted-foreground uppercase mb-2'>{label}</p>
      <p className='font-serif text-3xl text-ink tabular-nums'>{value}</p>
    </div>
  );

  return (
    <main className='p-6 lg:p-10 max-w-[1400px] mx-auto'>
      <header className='mb-8'>
        <p className='text-xs tracking-[0.3em] text-muted-foreground mb-2'>ADMINISTRAÇÃO</p>
        <h1 className='font-serif text-4xl lg:text-5xl text-ink mb-2'>Dashboard</h1>
      </header>

      <section className='mb-10 flex flex-col sm:flex-row flex-wrap items-end gap-4'>
        <div className='space-y-2'>
          <Label htmlFor='dash-from'>De</Label>
          <Input
            id='dash-from'
            type='date'
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className='h-11 rounded-xl w-full sm:w-auto min-w-[11rem]'
          />
        </div>
        <div className='space-y-2'>
          <Label htmlFor='dash-to'>Até</Label>
          <Input
            id='dash-to'
            type='date'
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className='h-11 rounded-xl w-full sm:w-auto min-w-[11rem]'
          />
        </div>
        <Button type='button' className='rounded-xl h-11' onClick={() => void reload()} loading={loading}>
          Atualizar painel
        </Button>
      </section>

      {error && (
        <p className='text-sm text-coral mb-6 bg-coral/5 border border-coral/20 rounded-xl px-4 py-3'>{error}</p>
      )}

      {data && !loading && (
        <>
          <div className='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10'>
            <Kpi label='Títulos no acervo' value={data.book_titles_total} />
            <Kpi label='Usuários cadastrados' value={data.users_total} />
            <Kpi label='Empréstimos ativos agora' value={data.active_loans} />
            <Kpi label='Em atraso (entre os ativos)' value={data.overdue_loans} />
            <Kpi label='Novos empréstimos no período' value={data.loans_started_in_period} />
            <Kpi label='Total de multas no período' value={currencyBRL(data.total_fines_brl)} />
            <Kpi label='Títulos disponíveis agora' value={data.available_titles} />
            <Kpi label='Títulos em circulação agora' value={data.on_loan_titles} />
            <Kpi
              label='Reservas (fila / hold)'
              value={
                <span className='text-2xl'>
                  {data.reservations_pending} / {data.reservations_hold}
                </span>
              }
            />
          </div>

          <section className='mb-12'>
            <h2 className='font-serif text-2xl text-ink mb-4'>Livros mais emprestados no período</h2>
            {data.top_books.length === 0 ? (
              <p className='text-muted-foreground'>Nenhum empréstimo com retirada neste intervalo.</p>
            ) : (
              <ul className='space-y-3'>
                {(() => {
                  const maxCount = Math.max(...data.top_books.map((b) => b.loan_count), 1);
                  return data.top_books.map((b, i) => (
                    <li
                      key={b.book_id}
                      className='bg-card border border-border rounded-xl px-4 py-3'
                    >
                      <div className='flex flex-wrap items-baseline justify-between gap-2'>
                        <span className='text-muted-foreground text-sm w-6 shrink-0'>{i + 1}.</span>
                        <span className='font-serif text-lg text-ink flex-1 min-w-0'>{b.title}</span>
                        <span className='text-sm text-coral shrink-0'>{b.author_name}</span>
                        <span className='text-sm text-muted-foreground tabular-nums shrink-0'>
                          {b.loan_count} retiradas
                        </span>
                      </div>
                      <div className='mt-3 h-2 rounded-full bg-secondary overflow-hidden'>
                        <div
                          className='h-full rounded-full bg-gradient-hero opacity-90'
                          style={{ width: `${Math.round((b.loan_count / maxCount) * 100)}%` }}
                          role='presentation'
                        />
                      </div>
                    </li>
                  ));
                })()}
              </ul>
            )}
          </section>
        </>
      )}

      {loading && !data && <p className='text-muted-foreground'>Carregando indicadores…</p>}

      <section className='border-t border-border pt-10'>
        <h2 className='font-serif text-2xl text-ink mb-2'>Exportar relatórios (case técnico)</h2>
        <p className='text-sm text-muted-foreground mb-6 max-w-2xl'>
          Os três primeiros usam o mesmo período <strong className='text-ink font-medium'>De / Até</strong> do painel.
          O inventário é um snapshot completo do acervo (sem filtro de data).
        </p>

        <div className='grid gap-6 lg:grid-cols-2'>
          <div className='bg-secondary/40 border border-border rounded-2xl p-5'>
            <h3 className='font-medium text-ink mb-3'>Empréstimos no período</h3>
            <p className='text-xs text-muted-foreground mb-4'>Linhas por empréstimo com retirada entre as datas.</p>
            <div className='flex flex-wrap gap-2'>
              <Button
                type='button'
                colorSchema='secondary'
                className='rounded-xl'
                disabled={!token}
                onClick={() => download(`/api/v1/reports/loans?${periodQuery}&format=csv`)}
              >
                CSV
              </Button>
              <Button
                type='button'
                colorSchema='secondary'
                className='rounded-xl'
                disabled={!token}
                onClick={() => download(`/api/v1/reports/loans?${periodQuery}&format=pdf`)}
              >
                PDF
              </Button>
            </div>
          </div>

          <div className='bg-secondary/40 border border-border rounded-2xl p-5'>
            <h3 className='font-medium text-ink mb-3'>Multas no período</h3>
            <p className='text-xs text-muted-foreground mb-4'>Devoluções com multa no intervalo (por data de devolução).</p>
            <div className='flex flex-wrap gap-2'>
              <Button
                type='button'
                colorSchema='secondary'
                className='rounded-xl'
                disabled={!token}
                onClick={() => download(`/api/v1/reports/fines?${periodQuery}&format=csv`)}
              >
                CSV
              </Button>
              <Button
                type='button'
                colorSchema='secondary'
                className='rounded-xl'
                disabled={!token}
                onClick={() => download(`/api/v1/reports/fines?${periodQuery}&format=pdf`)}
              >
                PDF
              </Button>
            </div>
          </div>

          <div className='bg-secondary/40 border border-border rounded-2xl p-5'>
            <h3 className='font-medium text-ink mb-3'>Títulos mais emprestados</h3>
            <p className='text-xs text-muted-foreground mb-4'>Ranking por número de retiradas no período (até 10).</p>
            <div className='flex flex-wrap gap-2'>
              <Button
                type='button'
                colorSchema='secondary'
                className='rounded-xl'
                disabled={!token}
                onClick={() =>
                  download(`/api/v1/reports/top-books?${periodQuery}&limit=10&format=csv`)
                }
              >
                CSV
              </Button>
              <Button
                type='button'
                colorSchema='secondary'
                className='rounded-xl'
                disabled={!token}
                onClick={() =>
                  download(`/api/v1/reports/top-books?${periodQuery}&limit=10&format=pdf`)
                }
              >
                PDF
              </Button>
            </div>
          </div>

          <div className='bg-secondary/40 border border-border rounded-2xl p-5'>
            <h3 className='font-medium text-ink mb-3'>Inventário completo</h3>
            <p className='text-xs text-muted-foreground mb-4'>Todos os títulos e disponibilidade atual (sem período).</p>
            <div className='flex flex-wrap gap-2'>
              <Button
                type='button'
                colorSchema='secondary'
                className='rounded-xl'
                disabled={!token}
                onClick={() => download('/api/v1/reports/inventory?format=csv')}
              >
                CSV
              </Button>
              <Button
                type='button'
                colorSchema='secondary'
                className='rounded-xl'
                disabled={!token}
                onClick={() => download('/api/v1/reports/inventory?format=pdf')}
              >
                PDF
              </Button>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
};

export default AdminDashboard;

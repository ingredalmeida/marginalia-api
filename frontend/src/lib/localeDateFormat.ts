/** Data/hora curta para lista de notificações (pt-BR). */
export function formatNotificationWhen(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** Data curta para linhas de empréstimo (pt-BR). */
export function formatDateShortPtBr(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

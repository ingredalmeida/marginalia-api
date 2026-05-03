export async function parseApiError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === 'string') {
      return body.detail;
    }
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      const first = body.detail[0] as { msg?: string };
      return first.msg ?? 'Dados inválidos.';
    }
  } catch {
    return res.statusText || 'Erro na requisição.';
  }
  return res.statusText || 'Erro na requisição.';
}

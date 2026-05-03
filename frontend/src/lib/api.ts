export function apiUrl(pathInput: string): string {
  const base = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? '';
  const path = pathInput.startsWith('/') ? pathInput : `/${pathInput}`;
  if (!base) {
    return path;
  }
  return `${base}${path}`;
}

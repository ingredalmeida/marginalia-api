export function decodeUserIdFromAccessToken(accessToken: string): number | null {
  try {
    const part = accessToken.split('.')[1];
    if (!part) {
      return null;
    }
    const base64 = part.replace(/-/g, '+').replace(/_/g, '/');
    const pad = base64.length % 4;
    const padded = pad ? base64 + '='.repeat(4 - pad) : base64;
    const payload = JSON.parse(atob(padded)) as { sub?: string };
    const id = Number.parseInt(String(payload.sub ?? ''), 10);
    return Number.isFinite(id) ? id : null;
  } catch {
    return null;
  }
}

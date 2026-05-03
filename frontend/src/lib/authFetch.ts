export function authHeader(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

export function jsonAuthHeader(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

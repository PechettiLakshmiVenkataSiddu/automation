type Organization = { id: string; name: string; role: string };
function baseUrl(): string {
  const value = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!value) throw new Error('NEXT_PUBLIC_API_BASE_URL is not configured.');
  return value.replace(/\/$/, '');
}
export async function api<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${baseUrl()}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
  });
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}
export async function refreshAccessToken(): Promise<string> {
  const response = await fetch(`${baseUrl()}/v1/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) throw new Error('Session refresh failed');
  return ((await response.json()) as { access_token: string }).access_token;
}
export function getOrganizations(token: string): Promise<Organization[]> {
  return api('/v1/me/organizations', token);
}
export function createConversation(
  token: string,
  organization_id: string,
  title: string,
): Promise<{ id: string }> {
  return api('/v1/conversations', token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, title }),
  });
}
export function sendChatMessage(
  token: string,
  conversationId: string,
  content: string,
): Promise<{ content: string }> {
  return api(`/v1/conversations/${conversationId}/messages`, token, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

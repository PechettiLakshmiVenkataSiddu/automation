type Organization = { id: string; name: string; role: string };
type DashboardSummary = {
  runs_by_status: Record<string, number>;
  pending_approvals: number;
  recent_runs: Array<{ id: string; workflow_name: string; status: string; created_at: string }>;
};

function baseUrl(): string {
  const value = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!value) throw new Error('NEXT_PUBLIC_API_BASE_URL is not configured.');
  return value.replace(/\/$/, '');
}
async function request<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${baseUrl()}${path}`, {
    ...options,
    credentials: 'include',
    headers: { ...options.headers, Authorization: `Bearer ${token}` },
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
  return request('/v1/me/organizations', token);
}
export function getDashboardSummary(
  token: string,
  organizationId: string,
): Promise<DashboardSummary> {
  return request(
    `/v1/dashboard/summary?organization_id=${encodeURIComponent(organizationId)}`,
    token,
  );
}

import { api, getOrganizations, refreshAccessToken } from './chat-api';

export type Memory = { id: string; memory_type: string; text: string; updated_at: string };

export async function loadMemoryWorkspace() {
  const token = await refreshAccessToken();
  const organizations = await getOrganizations(token);
  if (!organizations[0]) throw new Error('No active workspace is available.');
  const organizationId = organizations[0].id;
  const [consent, memories] = await Promise.all([
    api(`/v1/memories/consent?organization_id=${organizationId}`, token),
    api(`/v1/memories?organization_id=${organizationId}`, token),
  ]);
  return {
    token,
    organizationId,
    consent: consent as { enabled: boolean },
    memories: memories as Memory[],
  };
}

export async function setMemoryConsent(token: string, organizationId: string, enabled: boolean) {
  return api('/v1/memories/consent', token, {
    method: 'PUT',
    body: JSON.stringify({ organization_id: organizationId, enabled }),
  });
}

export async function saveMemory(
  token: string,
  organizationId: string,
  memoryType: string,
  text: string,
) {
  return api('/v1/memories', token, {
    method: 'POST',
    body: JSON.stringify({ organization_id: organizationId, memory_type: memoryType, text }),
  });
}

export async function removeMemory(token: string, organizationId: string, memoryId: string) {
  return api(`/v1/memories/${memoryId}?organization_id=${organizationId}`, token, {
    method: 'DELETE',
  });
}

export async function forgetMemories(token: string, organizationId: string) {
  return api(`/v1/memories?organization_id=${organizationId}`, token, { method: 'DELETE' });
}

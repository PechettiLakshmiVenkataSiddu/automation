import { api } from '@/lib/chat-api';

export interface SystemPolicy {
  retention_days_notifications: number;
  retention_days_audit_logs: number;
  allow_unsecure_sandboxes: boolean;
  break_glass_active: boolean;
  break_glass_reason: string | null;
  break_glass_activated_at: string | null;
}

export interface OrgMember {
  user_id: string;
  email: string;
  role: 'admin' | 'member' | 'viewer';
  status: string;
  created_at: string;
}

export interface ApiKeyItem {
  id: string;
  organization_id: string;
  created_by_user_id: string;
  name: string;
  key_prefix: string;
  last_used_at: string | null;
  expires_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface ConnectionItem {
  id: string;
  organization_id: string;
  provider: string;
  scopes: string[];
  status: string;
  created_at: string;
}

export interface AuditEventItem {
  id: string;
  actor_user_id: string | null;
  delegated_actor: string | null;
  event_type: string;
  target_type: string;
  target_id: string | null;
  outcome: 'allowed' | 'denied' | 'succeeded' | 'failed' | 'pending';
  policy_version: string | null;
  correlation_id: string;
  metadata: Record<string, any>;
  occurred_at: string;
}

export function getPolicy(token: string, organization_id: string): Promise<SystemPolicy> {
  return api(`/v1/admin/policy?organization_id=${organization_id}`, token);
}

export function updatePolicy(
  token: string,
  organization_id: string,
  retention_days_notifications: number,
  retention_days_audit_logs: number,
  allow_unsecure_sandboxes: boolean,
): Promise<{ status: string }> {
  return api('/v1/admin/policy', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      retention_days_notifications,
      retention_days_audit_logs,
      allow_unsecure_sandboxes,
    }),
  });
}

export function toggleBreakGlass(
  token: string,
  organization_id: string,
  active: boolean,
  reason: string | null,
): Promise<{ status: string }> {
  return api('/v1/admin/break-glass', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      active,
      reason,
    }),
  });
}

export function getMembers(token: string, organization_id: string): Promise<OrgMember[]> {
  return api(`/v1/admin/members?organization_id=${organization_id}`, token);
}

export function inviteMember(
  token: string,
  organization_id: string,
  email: string,
  role: 'admin' | 'member' | 'viewer',
): Promise<{ user_id: string }> {
  return api('/v1/admin/members', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      email,
      role,
    }),
  });
}

export function updateMemberRole(
  token: string,
  organization_id: string,
  user_id: string,
  role: 'admin' | 'member' | 'viewer',
): Promise<{ status: string }> {
  return api('/v1/admin/members', token, {
    method: 'PUT',
    body: JSON.stringify({
      organization_id,
      user_id,
      role,
    }),
  });
}

export function removeMember(token: string, organization_id: string, user_id: string): Promise<{ status: string }> {
  return api(`/v1/admin/members/${user_id}?organization_id=${organization_id}`, token, {
    method: 'DELETE',
  });
}

export function getApiKeys(token: string, organization_id: string): Promise<ApiKeyItem[]> {
  return api(`/v1/admin/apikeys?organization_id=${organization_id}`, token);
}

export function createApiKey(
  token: string,
  organization_id: string,
  name: string,
  expires_at: string | null,
): Promise<{ id: string; key: string }> {
  return api('/v1/admin/apikeys', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      name,
      expires_at,
    }),
  });
}

export function revokeApiKey(token: string, organization_id: string, key_id: string): Promise<{ status: string }> {
  return api(`/v1/admin/apikeys/${key_id}?organization_id=${organization_id}`, token, {
    method: 'DELETE',
  });
}

export function getConnections(token: string, organization_id: string): Promise<ConnectionItem[]> {
  return api(`/v1/admin/connections?organization_id=${organization_id}`, token);
}

export function revokeConnection(token: string, organization_id: string, provider: string): Promise<{ status: string }> {
  return api(`/v1/admin/connections/${provider}?organization_id=${organization_id}`, token, {
    method: 'DELETE',
  });
}

export function searchAuditEvents(
  token: string,
  organization_id: string,
  event_type?: string,
  target_type?: string,
  actor_user_id?: string,
): Promise<AuditEventItem[]> {
  let url = `/v1/admin/audit?organization_id=${organization_id}`;
  if (event_type) url += `&event_type=${encodeURIComponent(event_type)}`;
  if (target_type) url += `&target_type=${encodeURIComponent(target_type)}`;
  if (actor_user_id) url += `&actor_user_id=${encodeURIComponent(actor_user_id)}`;
  return api(url, token);
}

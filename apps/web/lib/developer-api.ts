import { api } from '@/lib/chat-api';

export interface DeveloperSandbox {
  id: string;
  organization_id: string;
  name: string;
  sandbox_path: string;
  status: 'active' | 'archived';
  created_at: string;
  updated_at: string;
}

export interface DeveloperCommand {
  id: string;
  sandbox_id: string;
  command_line: string;
  status: 'queued' | 'running' | 'awaiting_approval' | 'succeeded' | 'failed' | 'cancelled';
  exit_code: number | null;
  stdout_redacted: string | null;
  stderr_redacted: string | null;
  timeout_seconds: number;
  created_at: string;
  updated_at: string;
}

export function createSandbox(
  token: string,
  organization_id: string,
  name: string,
  sandbox_path: string,
): Promise<{ sandbox_id: string }> {
  return api('/v1/developer/sandboxes', token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, name, sandbox_path }),
  });
}

export function submitCommand(
  token: string,
  organization_id: string,
  sandbox_id: string,
  command_line: string,
  timeout_seconds = 30,
): Promise<{ command_id: string; status: string }> {
  return api('/v1/developer/commands', token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, sandbox_id, command_line, timeout_seconds }),
  });
}

export function getCommand(
  token: string,
  command_id: string,
  organization_id: string,
): Promise<DeveloperCommand> {
  return api(`/v1/developer/commands/${command_id}?organization_id=${organization_id}`, token);
}

export function decideCommandApproval(
  token: string,
  organization_id: string,
  approval_id: string,
  approved: boolean,
  reason?: string,
): Promise<{ status: string }> {
  return api(`/v1/developer/commands/${approval_id}/approve`, token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, approval_id, approved, reason }),
  });
}
export interface CommandApproval {
  id: string;
  organization_id: string;
  command_id: string;
  requested_by_user_id: string;
  decided_by_user_id: string | null;
  policy_version: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  decision_reason: string | null;
  expires_at: string;
  decided_at: string | null;
  created_at: string;
}

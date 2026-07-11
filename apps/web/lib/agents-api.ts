import { api } from '@/lib/chat-api';

export interface AgentPlanStep {
  id: string;
  step_index: number;
  assigned_agent: string;
  description: string;
  requires_approval: boolean;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'rejected';
  input_payload: Record<string, any>;
  output_payload: Record<string, any>;
}

export interface AgentRun {
  id: string;
  organization_id: string;
  user_id: string;
  goal: string;
  status: 'queued' | 'running' | 'awaiting_approval' | 'completed' | 'failed' | 'cancelled';
  budget_limit_usd: number;
  budget_spent_usd: number;
  time_limit_seconds: number;
  expires_at: string;
  created_at: string;
  updated_at: string;
  plan: AgentPlanStep[];
}

export interface AgentAuditLog {
  id: string;
  agent_run_id: string;
  step_id: string | null;
  action_type: 'policy_check' | 'tool_call' | 'memory_access' | 'state_transition' | 'budget_spent' | 'error';
  message: string;
  payload: Record<string, any>;
  created_at: string;
}

export function createAgentRun(
  token: string,
  organization_id: string,
  goal: string,
  budget_limit_usd = 1.0000,
  time_limit_seconds = 600,
): Promise<{ run_id: string }> {
  return api('/v1/agents/runs', token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, goal, budget_limit_usd, time_limit_seconds }),
  });
}

export function getAgentRun(
  token: string,
  run_id: string,
  organization_id: string,
): Promise<AgentRun> {
  return api(`/v1/agents/runs/${run_id}?organization_id=${organization_id}`, token);
}

export function decideAgentApproval(
  token: string,
  run_id: string,
  organization_id: string,
  approved: boolean,
  reason?: string,
): Promise<{ status: string }> {
  return api(`/v1/agents/runs/${run_id}/approve`, token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, approved, reason }),
  });
}

export function getAgentRunLogs(
  token: string,
  run_id: string,
  organization_id: string,
): Promise<AgentAuditLog[]> {
  return api(`/v1/agents/runs/${run_id}/logs?organization_id=${organization_id}`, token);
}

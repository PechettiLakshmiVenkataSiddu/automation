import { api, getOrganizations, refreshAccessToken } from './chat-api';

export type WorkflowNode = {
  id: string;
  type: 'trigger' | 'action' | 'condition' | 'approval' | 'loop';
  label: string;
  config?: Record<string, unknown>;
};
export type WorkflowEdge = { source: string; target: string };
export type WorkflowDefinition = { nodes: WorkflowNode[]; edges: WorkflowEdge[] };
export type WorkflowSchedule = {
  id: string;
  cron_expression: string;
  timezone: string;
  enabled: boolean;
};
export type WorkflowRun = {
  id: string;
  status: string;
  error_code: string | null;
  steps: Array<{ step_key: string; status: string; error_code: string | null }>;
};
export type WorkflowApproval = {
  id: string;
  workflow_run_id: string;
  status: string;
  action_summary: Record<string, unknown>;
  expires_at: string;
};

export async function loadWorkflowWorkspace() {
  const token = await refreshAccessToken();
  const organizations = await getOrganizations(token);
  if (!organizations[0]) throw new Error('No active workspace is available.');
  const organizationId = organizations[0].id;
  const workflows = (await api(`/v1/workflows?organization_id=${organizationId}`, token)) as Array<{
    id: string;
    name: string;
    status: string;
  }>;
  return { token, organizationId, workflows };
}

export function createWorkflow(
  token: string,
  organizationId: string,
  name: string,
  definition: WorkflowDefinition,
) {
  return api('/v1/workflows', token, {
    method: 'POST',
    body: JSON.stringify({ organization_id: organizationId, name, definition }),
  }) as Promise<{ id: string }>;
}

export function saveWorkflowDraft(
  token: string,
  organizationId: string,
  workflowId: string,
  definition: WorkflowDefinition,
) {
  return api(`/v1/workflows/${workflowId}/draft`, token, {
    method: 'PUT',
    body: JSON.stringify({ organization_id: organizationId, definition }),
  });
}

export function getTemplates(token: string) {
  return api('/v1/workflows/templates', token) as Promise<
    Array<{ id: string; name: string; definition: WorkflowDefinition }>
  >;
}
export function getSchedules(token: string, organizationId: string, workflowId: string) {
  return api(
    `/v1/workflows/${workflowId}/schedules?organization_id=${organizationId}`,
    token,
  ) as Promise<WorkflowSchedule[]>;
}
export function addSchedule(
  token: string,
  organizationId: string,
  workflowId: string,
  cronExpression: string,
  timezone: string,
) {
  return api(`/v1/workflows/${workflowId}/schedules`, token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id: organizationId,
      cron_expression: cronExpression,
      timezone,
    }),
  });
}
export function getRuns(token: string, organizationId: string, workflowId: string) {
  return api(
    `/v1/workflows/${workflowId}/runs?organization_id=${organizationId}`,
    token,
  ) as Promise<WorkflowRun[]>;
}
export function getApprovals(token: string, organizationId: string, workflowId: string) {
  return api(
    `/v1/workflows/${workflowId}/approvals?organization_id=${organizationId}`,
    token,
  ) as Promise<WorkflowApproval[]>;
}
export function decideApproval(
  token: string,
  organizationId: string,
  approvalId: string,
  approved: boolean,
) {
  return api(`/v1/automation/approvals/${approvalId}/decision`, token, {
    method: 'POST',
    body: JSON.stringify({ organization_id: organizationId, approved }),
  });
}

import { api } from '@/lib/chat-api';

export interface AnalyticsSummary {
  total_cost: number;
  total_events: number;
}

export interface CategoryBreakdown {
  category: 'model_call' | 'tool_execution' | 'workflow_step' | 'api_sync';
  total_cost: number;
  total_units: number;
  event_count: number;
}

export interface UserBreakdown {
  email: string;
  total_cost: number;
  event_count: number;
}

export interface AnalyticsBreakdown {
  categories: CategoryBreakdown[];
  users: UserBreakdown[];
}

export interface WorkflowMetricItem {
  id: string;
  workflow_id: string;
  run_count: number;
  success_count: number;
  failure_count: number;
  avg_duration_seconds: number;
}

export function getSummary(token: string, organization_id: string): Promise<AnalyticsSummary> {
  return api(`/v1/analytics/summary?organization_id=${organization_id}`, token);
}

export function getBreakdown(token: string, organization_id: string): Promise<AnalyticsBreakdown> {
  return api(`/v1/analytics/breakdown?organization_id=${organization_id}`, token);
}

export function getWorkflowMetrics(token: string, organization_id: string): Promise<WorkflowMetricItem[]> {
  return api(`/v1/analytics/workflows?organization_id=${organization_id}`, token);
}

export function logUsageEvent(
  token: string,
  organization_id: string,
  event_name: string,
  category: 'model_call' | 'tool_execution' | 'workflow_step' | 'api_sync',
  cost: number,
  units: number,
  metadata: Record<string, any> = {},
): Promise<{ status: string; event_id: string }> {
  return api('/v1/analytics/log', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      event_name,
      category,
      cost,
      units,
      metadata,
    }),
  });
}

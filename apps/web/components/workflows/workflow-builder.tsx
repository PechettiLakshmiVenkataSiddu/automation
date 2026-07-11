'use client';

import { FormEvent, useEffect, useState } from 'react';

import {
  addSchedule,
  createWorkflow,
  decideApproval,
  getApprovals,
  getRuns,
  getSchedules,
  getTemplates,
  loadWorkflowWorkspace,
  saveWorkflowDraft,
  type WorkflowApproval,
  type WorkflowDefinition,
  type WorkflowNode,
  type WorkflowRun,
  type WorkflowSchedule,
} from '@/lib/workflow-api';

const blank: WorkflowDefinition = {
  nodes: [{ id: 'trigger', type: 'trigger', label: 'Manual trigger' }],
  edges: [],
};

export function WorkflowBuilder() {
  const [token, setToken] = useState('');
  const [organizationId, setOrganizationId] = useState('');
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [name, setName] = useState('Untitled workflow');
  const [definition, setDefinition] = useState<WorkflowDefinition>(blank);
  const [templates, setTemplates] = useState<
    Array<{ id: string; name: string; definition: WorkflowDefinition }>
  >([]);
  const [schedules, setSchedules] = useState<WorkflowSchedule[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [approvals, setApprovals] = useState<WorkflowApproval[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflowWorkspace()
      .then(async ({ token: accessToken, organizationId: org }) => {
        setToken(accessToken);
        setOrganizationId(org);
        setTemplates(await getTemplates(accessToken));
      })
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : 'Workflow builder could not load.'),
      );
  }, []);

  async function refreshDetails(id: string) {
    const [nextSchedules, nextRuns, nextApprovals] = await Promise.all([
      getSchedules(token, organizationId, id),
      getRuns(token, organizationId, id),
      getApprovals(token, organizationId, id),
    ]);
    setSchedules(nextSchedules);
    setRuns(nextRuns);
    setApprovals(nextApprovals.filter((approval) => approval.status === 'pending'));
  }

  function addNode(type: WorkflowNode['type']) {
    const id = `${type}-${crypto.randomUUID()}`;
    setDefinition((current) => ({
      ...current,
      nodes: [
        ...current.nodes,
        {
          id,
          type,
          label: `${type} node`,
          ...(type === 'loop' ? { config: { max_iterations: 3 } } : {}),
        },
      ],
      edges: [...current.edges, { source: current.nodes.at(-1)?.id ?? 'trigger', target: id }],
    }));
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    try {
      const id = workflowId ?? (await createWorkflow(token, organizationId, name, definition)).id;
      if (workflowId) await saveWorkflowDraft(token, organizationId, id, definition);
      setWorkflowId(id);
      await refreshDetails(id);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Workflow could not be saved.');
    }
  }

  async function createSchedule() {
    if (!workflowId) return setError('Save the draft before adding a schedule.');
    try {
      await addSchedule(token, organizationId, workflowId, '0 9 * * 1-5', 'Asia/Kolkata');
      await refreshDetails(workflowId);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Schedule could not be created.');
    }
  }

  async function decide(approvalId: string, approved: boolean) {
    try {
      await decideApproval(token, organizationId, approvalId, approved);
      if (workflowId) await refreshDetails(workflowId);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Approval could not be decided.');
    }
  }

  return (
    <main className="mx-auto max-w-6xl p-6 sm:p-10">
      <p className="text-sm font-semibold tracking-[0.2em] text-[var(--accent)]">AETHER</p>
      <h1 className="mt-2 text-3xl font-semibold">Workflow builder</h1>
      <form onSubmit={save} className="mt-6">
        <label htmlFor="workflow-name">Workflow name</label>
        <input
          id="workflow-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="ml-3 rounded border border-[var(--border)] bg-[var(--panel)] p-2"
        />
        <section className="mt-6 grid gap-4 md:grid-cols-[14rem_1fr]">
          <aside className="rounded-xl bg-[var(--panel)] p-4">
            <h2 className="font-semibold">Nodes</h2>
            {(['action', 'condition', 'approval', 'loop'] as const).map((type) => (
              <button
                type="button"
                key={type}
                onClick={() => addNode(type)}
                className="mt-2 block text-[var(--accent)]"
              >
                Add {type}
              </button>
            ))}
            <h2 className="mt-6 font-semibold">Templates</h2>
            {templates.map((template) => (
              <button
                type="button"
                key={template.id}
                onClick={() => {
                  setName(template.name);
                  setDefinition(template.definition);
                }}
                className="mt-2 block text-[var(--accent)]"
              >
                Use {template.name}
              </button>
            ))}
          </aside>
          <section
            aria-label="Workflow graph"
            className="rounded-xl border border-[var(--border)] p-4"
          >
            <h2 className="font-semibold">Graph</h2>
            <ol className="mt-3 space-y-2">
              {definition.nodes.map((node) => (
                <li key={node.id} className="rounded bg-[var(--panel)] p-3">
                  <strong>{node.label}</strong>
                  <span className="ml-2 text-sm text-[var(--muted)]">{node.type}</span>
                </li>
              ))}
            </ol>
            <p className="mt-4 text-sm text-[var(--muted)]">
              {definition.edges.length} validated connections
            </p>
          </section>
        </section>
        <button className="mt-6 rounded-lg bg-[var(--accent)] px-4 py-2 font-semibold text-slate-950">
          Save draft
        </button>
      </form>
      {workflowId && (
        <section className="mt-10 grid gap-6 lg:grid-cols-3">
          <article className="rounded-xl bg-[var(--panel)] p-4">
            <h2 className="font-semibold">Schedules</h2>
            <button onClick={createSchedule} className="mt-2 text-[var(--accent)]">
              Add weekday 09:00 schedule
            </button>
            <ul>
              {schedules.map((schedule) => (
                <li key={schedule.id} className="mt-2 text-sm">
                  {schedule.cron_expression} · {schedule.timezone}
                </li>
              ))}
            </ul>
          </article>
          <article className="rounded-xl bg-[var(--panel)] p-4">
            <h2 className="font-semibold">Run diagnostics</h2>
            <ul>
              {runs.map((run) => (
                <li key={run.id} className="mt-2 text-sm">
                  {run.status}:{' '}
                  {run.steps.map((step) => `${step.step_key} (${step.status})`).join(', ') ||
                    'no steps'}
                </li>
              ))}
            </ul>
          </article>
          <article className="rounded-xl bg-[var(--panel)] p-4">
            <h2 className="font-semibold">Pending approvals</h2>
            <ul>
              {approvals.map((approval) => (
                <li key={approval.id} className="mt-2 text-sm">
                  <span>{approval.workflow_run_id}</span>
                  <button
                    onClick={() => decide(approval.id, true)}
                    className="ml-2 text-[var(--accent)]"
                  >
                    Approve
                  </button>
                  <button onClick={() => decide(approval.id, false)} className="ml-2 text-red-300">
                    Reject
                  </button>
                </li>
              ))}
            </ul>
          </article>
        </section>
      )}
      {error && (
        <p role="alert" className="mt-3 text-red-300">
          {error}
        </p>
      )}
    </main>
  );
}

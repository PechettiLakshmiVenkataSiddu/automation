'use client';

import { useQuery } from '@tanstack/react-query';
import { getDashboardSummary, getOrganizations, refreshAccessToken } from '@/lib/dashboard-api';

const labels: Record<string, string> = {
  queued: 'Queued',
  running: 'Running',
  awaiting_approval: 'Awaiting approval',
  succeeded: 'Succeeded',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

export function Dashboard() {
  const tokenQuery = useQuery({
    queryKey: ['access-token'],
    queryFn: refreshAccessToken,
    staleTime: 10 * 60 * 1000,
  });

  const organizations = useQuery({
    queryKey: ['organizations'],
    queryFn: () => getOrganizations(tokenQuery.data ?? ''),
    enabled: Boolean(tokenQuery.data),
  });

  const organizationId = organizations.data?.[0]?.id;

  const summary = useQuery({
    queryKey: ['dashboard', organizationId],
    queryFn: () => getDashboardSummary(tokenQuery.data ?? '', organizationId ?? ''),
    enabled: Boolean(tokenQuery.data && organizationId),
  });

  // Helper to trigger tools via the new backend /v1/developer/commands endpoint
  const triggerTool = async (taskName: string, payload: any) => {
    if (!organizationId) return;

    try {
      const response = await fetch('/v1/developer/commands', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokenQuery.data}`,
        },
        body: JSON.stringify({
          organization_id: organizationId,
          sandbox_id: "default-sandbox", // Ensure this matches your DB
          command_line: "manual_trigger",
          timeout_seconds: 30,
          task_type: taskName, // This triggers the TOOL_REGISTRY in your backend[cite: 1]
          input_payload: payload,
        }),
      });

      if (!response.ok) throw new Error('Failed to trigger task');
      alert(`Task ${taskName} queued successfully!`);
    } catch (error) {
      console.error(error);
      alert('Error triggering task.');
    }
  };

  if (tokenQuery.isLoading || organizations.isLoading || summary.isLoading)
    return <main className="p-8 text-[var(--muted)]">Loading your workspace…</main>;

  if (tokenQuery.isError || organizations.isError || summary.isError)
    return (
      <main className="p-8 text-red-300">
        Your dashboard could not be loaded. Sign in again or try later.
      </main>
    );

  if (!organizations.data?.length)
    return <main className="p-8 text-[var(--muted)]">You do not yet belong to an active workspace.</main>;

  const data = summary.data;
  if (!data) return null;

  return (
    <main className="mx-auto max-w-6xl p-6 sm:p-10">
      <p className="text-sm font-semibold tracking-[0.2em] text-[var(--accent)]">
        {organizations.data[0].name}
      </p>
      
      {/* Tool Trigger Section */}
      <h1 className="mt-2 text-4xl font-semibold">Operations overview</h1>
      <section className="mt-6 flex gap-4">
        <button
          onClick={() => triggerTool('local_file_backup', { path: 'C:\\test.txt' })}
          className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-80"
        >
          Run File Backup
        </button>
        <button
          onClick={() => triggerTool('github_create_issue', { title: 'New Bug Report' })}
          className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-semibold transition hover:bg-[var(--panel)]"
        >
          Create GitHub Issue
        </button>
      </section>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(data.runs_by_status).map(([status, total]) => (
          <article
            key={status}
            className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-5"
          >
            <p className="text-sm text-[var(--muted)]">{labels[status] ?? status}</p>
            <p className="mt-2 text-3xl font-semibold">{total}</p>
          </article>
        ))}
        <article className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-5">
          <p className="text-sm text-[var(--muted)]">Pending approvals</p>
          <p className="mt-2 text-3xl font-semibold">{data.pending_approvals}</p>
        </article>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-semibold">Recent workflow runs</h2>
        <div className="mt-4 overflow-hidden rounded-xl border border-[var(--border)]">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--panel)] text-[var(--muted)]">
              <tr>
                <th className="p-4">Workflow</th>
                <th className="p-4">Status</th>
                <th className="p-4">Started</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_runs.map((run) => (
                <tr key={run.id} className="border-t border-[var(--border)]">
                  <td className="p-4">{run.workflow_name}</td>
                  <td className="p-4">{labels[run.status] ?? run.status}</td>
                  <td className="p-4 text-[var(--muted)]">
                    {new Date(run.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
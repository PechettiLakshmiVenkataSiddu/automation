'use client';

import { useState, useEffect, useRef } from 'react';
import {
  refreshAccessToken,
  getOrganizations,
} from '@/lib/chat-api';
import {
  createAgentRun,
  getAgentRun,
  decideAgentApproval,
  getAgentRunLogs,
  AgentRun,
  AgentAuditLog,
} from '@/lib/agents-api';

export function AgentMonitor() {
  const [goal, setGoal] = useState('');
  const [budgetLimit, setBudgetLimit] = useState('1.00');
  const [timeLimit, setTimeLimit] = useState('600');
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runData, setRunData] = useState<AgentRun | null>(null);
  const [logs, setLogs] = useState<AgentAuditLog[]>([]);
  const [busy, setBusy] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Poll active run
  useEffect(() => {
    if (!activeRunId) return;

    let timer: NodeJS.Timeout;

    async function poll() {
      try {
        const token = await refreshAccessToken();
        const orgs = await getOrganizations(token);
        if (!orgs[0]) return;

        const run = await getAgentRun(token, activeRunId!, orgs[0].id);
        setRunData(run);

        const runLogs = await getAgentRunLogs(token, activeRunId!, orgs[0].id);
        setLogs(runLogs);

        if (['completed', 'failed', 'cancelled'].includes(run.status)) {
          // Stop polling
          return;
        }

        timer = setTimeout(poll, 1500);
      } catch (err) {
        console.error('Polling failed:', err);
        timer = setTimeout(poll, 3000);
      }
    }

    poll();

    return () => clearTimeout(timer);
  }, [activeRunId]);

  // Scroll logs console to bottom
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  async function start(e: React.FormEvent) {
    e.preventDefault();
    if (!goal.trim() || busy) return;
    setBusy(true);
    setError(null);
    setRunData(null);
    setLogs([]);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace available.');

      const result = await createAgentRun(
        token,
        orgs[0].id,
        goal.trim(),
        parseFloat(budgetLimit),
        parseInt(timeLimit),
      );
      setActiveRunId(result.run_id);
    } catch (err: any) {
      setError(err.message || 'Failed to start agent run.');
    } finally {
      setBusy(false);
    }
  }

  async function handleApproval(approved: boolean) {
    if (!activeRunId || deciding) return;
    setDeciding(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      await decideAgentApproval(token, activeRunId, orgs[0].id, approved, reason);
      setReason('');
    } catch (err: any) {
      setError(err.message || 'Failed to submit decision.');
    } finally {
      setDeciding(false);
    }
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: '#f3f4f6', margin: '0 0 0.5rem 0', letterSpacing: '-0.025em' }}>
          Agent Orchestrator
        </h1>
        <p style={{ color: '#9ca3af', fontSize: '1.1rem', margin: 0 }}>
          Plan and execute goals with secure, bounded, policy-controlled autonomous agents.
        </p>
      </div>

      {error && (
        <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#f87171', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          {error}
        </div>
      )}

      {/* Goal Form */}
      <form onSubmit={start} style={{ backgroundColor: '#1f2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151', display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Goal / Objective</label>
          <input
            type="text"
            placeholder="e.g. Research Aether, draft email summary"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            disabled={busy || (runData !== null && !['completed', 'failed', 'cancelled'].includes(runData.status))}
            style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Budget Limit (USD)</label>
            <input
              type="number"
              step="0.05"
              value={budgetLimit}
              onChange={(e) => setBudgetLimit(e.target.value)}
              disabled={busy}
              style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Time Limit (Seconds)</label>
            <input
              type="number"
              value={timeLimit}
              onChange={(e) => setTimeLimit(e.target.value)}
              disabled={busy}
              style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={busy || !goal.trim() || (runData !== null && !['completed', 'failed', 'cancelled'].includes(runData.status))}
          style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', backgroundColor: busy ? '#4b5563' : '#3b82f6', color: '#fff', fontSize: '1rem', fontWeight: 700, border: 'none', cursor: 'pointer', transition: 'background-color 0.2s' }}
        >
          {busy ? 'Starting Plan...' : 'Initialize Agent Run'}
        </button>
      </form>

      {/* Monitor Display */}
      {runData && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Status and Budget Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', backgroundColor: '#111827', padding: '1rem', borderRadius: '8px', border: '1px solid #374151', textAlign: 'center' }}>
            <div>
              <span style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', textTransform: 'uppercase', fontWeight: 600 }}>Run Status</span>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, color: runData.status === 'completed' ? '#10b981' : runData.status === 'failed' ? '#ef4444' : '#3b82f6', textTransform: 'capitalize' }}>
                {runData.status.replace('_', ' ')}
              </span>
            </div>
            <div>
              <span style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', textTransform: 'uppercase', fontWeight: 600 }}>Budget Spent</span>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f3f4f6' }}>
                ${runData.budget_spent_usd.toFixed(4)} / ${runData.budget_limit_usd.toFixed(4)}
              </span>
            </div>
            <div>
              <span style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', textTransform: 'uppercase', fontWeight: 600 }}>Time Boundary</span>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f3f4f6' }}>
                {runData.time_limit_seconds}s
              </span>
            </div>
          </div>

          {/* Plan Steps Checklist */}
          <div style={{ backgroundColor: '#1f2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Orchestrator Execution Plan</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {runData.plan.map((step) => (
                <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', backgroundColor: '#111827', borderRadius: '8px', border: '1px solid #374151' }}>
                  {/* Status Indicator */}
                  <div style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    backgroundColor: step.status === 'completed' ? '#10b981' : step.status === 'running' ? '#3b82f6' : step.status === 'failed' ? '#ef4444' : '#4b5563',
                    color: '#fff'
                  }}>
                    {step.status === 'completed' ? '✓' : step.status === 'running' ? '●' : step.status === 'failed' ? '✗' : step.step_index + 1}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, color: '#f3f4f6', textTransform: 'uppercase', fontSize: '0.8rem', padding: '0.2rem 0.5rem', backgroundColor: '#1f2937', borderRadius: '4px' }}>
                        {step.assigned_agent}
                      </span>
                      {step.requires_approval && (
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', padding: '0.1rem 0.4rem', borderRadius: '4px', border: '1px solid #f59e0b' }}>
                          APPROVAL REQUIRED
                        </span>
                      )}
                    </div>
                    <p style={{ margin: '0.25rem 0 0 0', color: '#d1d5db', fontSize: '0.95rem' }}>{step.description}</p>
                  </div>
                  <span style={{ textTransform: 'capitalize', fontSize: '0.85rem', fontWeight: 600, color: step.status === 'completed' ? '#10b981' : step.status === 'running' ? '#3b82f6' : '#9ca3af' }}>
                    {step.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Approval Block */}
          {runData.status === 'awaiting_approval' && (
            <div style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)', padding: '1.5rem', borderRadius: '12px', border: '1px solid #f59e0b', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <h4 style={{ margin: 0, color: '#f59e0b', fontSize: '1.1rem', fontWeight: 700 }}>Approval Decision Gate</h4>
                <p style={{ margin: 0, color: '#d1d5db', fontSize: '0.9rem' }}>
                  The orchestrator has paused on a sensitive action. Provide your approval feedback.
                </p>
              </div>
              <input
                type="text"
                placeholder="Reason / Comments (optional)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                disabled={deciding}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #f59e0b', backgroundColor: '#111827', color: '#f3f4f6', outline: 'none' }}
              />
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                  onClick={() => handleApproval(true)}
                  disabled={deciding}
                  style={{ flex: 1, padding: '0.5rem 1rem', borderRadius: '6px', backgroundColor: '#10b981', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer' }}
                >
                  Approve Step
                </button>
                <button
                  onClick={() => handleApproval(false)}
                  disabled={deciding}
                  style={{ flex: 1, padding: '0.5rem 1rem', borderRadius: '6px', backgroundColor: '#ef4444', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer' }}
                >
                  Reject Step
                </button>
              </div>
            </div>
          )}

          {/* Scrolling Audit Log Console */}
          <div style={{ backgroundColor: '#111827', padding: '1rem', borderRadius: '8px', border: '1px solid #374151' }}>
            <h3 style={{ margin: '0 0 0.75rem 0', color: '#9ca3af', fontSize: '0.9rem', fontWeight: 700, textTransform: 'uppercase' }}>Real-time Audit Logs</h3>
            <div style={{ height: '200px', overflowY: 'auto', backgroundColor: '#030712', borderRadius: '6px', padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontFamily: 'monospace', fontSize: '0.8rem' }}>
              {logs.map((log) => (
                <div key={log.id} style={{ display: 'flex', gap: '0.5rem' }}>
                  <span style={{ color: '#4b5563' }}>[{new Date(log.created_at).toLocaleTimeString()}]</span>
                  <span style={{
                    fontWeight: 700,
                    color: log.action_type === 'error' ? '#ef4444' : log.action_type === 'policy_check' ? '#f59e0b' : log.action_type === 'tool_call' ? '#60a5fa' : '#10b981'
                  }}>
                    {log.action_type.toUpperCase()}:
                  </span>
                  <span style={{ color: '#f3f4f6' }}>{log.message}</span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

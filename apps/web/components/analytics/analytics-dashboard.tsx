'use client';

import { useState, useEffect } from 'react';
import { refreshAccessToken, getOrganizations } from '@/lib/chat-api';
import {
  getSummary,
  getBreakdown,
  getWorkflowMetrics,
  logUsageEvent,
  CategoryBreakdown,
  UserBreakdown,
  WorkflowMetricItem,
} from '@/lib/analytics-api';

export function AnalyticsDashboard() {
  const [totalCost, setTotalCost] = useState(0.0);
  const [totalEvents, setTotalEvents] = useState(0);
  const [categories, setCategories] = useState<CategoryBreakdown[]>([]);
  const [users, setUsers] = useState<UserBreakdown[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowMetricItem[]>([]);

  // Logger Form
  const [logName, setLogName] = useState('');
  const [logCategory, setLogCategory] = useState<'model_call' | 'tool_execution' | 'workflow_step' | 'api_sync'>('model_call');
  const [logCost, setLogCost] = useState('0.00150');
  const [logUnits, setLogUnits] = useState('150');

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let timer: NodeJS.Timeout;

    async function loadStats() {
      try {
        const token = await refreshAccessToken();
        const orgs = await getOrganizations(token);
        if (!orgs[0]) return;

        const summary = await getSummary(token, orgs[0].id);
        setTotalCost(summary.total_cost);
        setTotalEvents(summary.total_events);

        const breakdown = await getBreakdown(token, orgs[0].id);
        setCategories(breakdown.categories);
        setUsers(breakdown.users);

        const w = await getWorkflowMetrics(token, orgs[0].id);
        setWorkflows(w);

        timer = setTimeout(loadStats, 5000);
      } catch (err) {
        console.error('Failed to poll analytics metrics:', err);
        timer = setTimeout(loadStats, 10000);
      }
    }

    loadStats();

    return () => clearTimeout(timer);
  }, []);

  async function handleLogTest(e: React.FormEvent) {
    e.preventDefault();
    if (!logName.trim() || busy) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      await logUsageEvent(
        token,
        orgs[0].id,
        logName.trim(),
        logCategory,
        parseFloat(logCost) || 0.0,
        parseInt(logUnits) || 0
      );

      setLogName('');
      setLogCost('0.00150');
      setLogUnits('150');
      setSuccess('Test usage event logged.');

      // Refresh breakdown
      const summary = await getSummary(token, orgs[0].id);
      setTotalCost(summary.total_cost);
      setTotalEvents(summary.total_events);

      const breakdown = await getBreakdown(token, orgs[0].id);
      setCategories(breakdown.categories);
      setUsers(breakdown.users);
    } catch (err: any) {
      setError(err.message || 'Failed to dispatch log.');
    } finally {
      setBusy(false);
    }
  }

  async function handleDownloadExport() {
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      const response = await fetch(`/v1/analytics/export?organization_id=${orgs[0].id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to export usage logs.');

      const csvBlob = await response.blob();
      const blobUrl = window.URL.createObjectURL(csvBlob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.setAttribute('download', `usage_report_${orgs[0].id}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: any) {
      setError(err.message || 'Failed to export logs.');
    }
  }

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: '#f3f4f6', margin: '0 0 0.5rem 0', letterSpacing: '-0.025em' }}>
            System Usage Analytics
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '1.1rem', margin: 0 }}>
            Monitor processing credits, token expenses, and automation run reliability summaries.
          </p>
        </div>
        <button
          onClick={handleDownloadExport}
          style={{
            padding: '0.65rem 1.25rem',
            borderRadius: '8px',
            backgroundColor: '#3b82f6',
            color: '#fff',
            fontSize: '0.95rem',
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          Download CSV Export
        </button>
      </div>

      {error && (
        <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#f87171', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          {success}
        </div>
      )}

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
          <span style={{ color: '#9ca3af', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Cost (USD)</span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 800, color: '#f3f4f6', margin: '0.5rem 0 0 0' }}>
            ${totalCost.toFixed(4)}
          </h2>
        </div>

        <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
          <span style={{ color: '#9ca3af', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Recorded Actions</span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 800, color: '#f3f4f6', margin: '0.5rem 0 0 0' }}>
            {totalEvents}
          </h2>
        </div>

        <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
          <span style={{ color: '#9ca3af', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Average Cost / Action</span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 800, color: '#f3f4f6', margin: '0.5rem 0 0 0' }}>
            ${totalEvents > 0 ? (totalCost / totalEvents).toFixed(6) : '0.000000'}
          </h2>
        </div>
      </div>

      {/* Dashboard Core Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '2rem' }}>
        {/* Allocations and Workflows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Category Allocation */}
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 1.25rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Allocation Cost by Category</h3>
            {categories.length === 0 ? (
              <div style={{ color: '#9ca3af', padding: '2rem', textAlign: 'center' }}>No allocation statistics logs.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {categories.map((c) => {
                  const percent = totalCost > 0 ? (c.total_cost / totalCost) * 100 : 0;
                  return (
                    <div key={c.category} style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', fontWeight: 600 }}>
                        <span style={{ color: '#d1d5db' }}>{c.category.replace('_', ' ').toUpperCase()}</span>
                        <span style={{ color: '#f3f4f6' }}>${c.total_cost.toFixed(4)} ({percent.toFixed(1)}%)</span>
                      </div>
                      <div style={{ width: '100%', height: '8px', backgroundColor: '#111827', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ width: `${percent}%`, height: '100%', backgroundColor: '#3b82f6', borderRadius: '4px' }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Workflow Reliability */}
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 1.25rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Workflow Run Reliability</h3>
            {workflows.length === 0 ? (
              <div style={{ color: '#9ca3af', padding: '2rem', textAlign: 'center' }}>No active workflows runtime records found.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {workflows.map((w) => {
                  const successRate = w.run_count > 0 ? (w.success_count / w.run_count) * 100 : 0;
                  return (
                    <div key={w.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', backgroundColor: '#111827', borderRadius: '8px', border: '1px solid #374151' }}>
                      <div>
                        <span style={{ display: 'block', fontWeight: 700, color: '#f3f4f6', fontSize: '0.95rem' }}>Workflow ID: {w.workflow_id}</span>
                        <span style={{ display: 'block', fontSize: '0.8rem', color: '#9ca3af' }}>Runs: {w.run_count} | Avg Duration: {w.avg_duration_seconds}s</span>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{
                          fontSize: '0.85rem',
                          fontWeight: 800,
                          backgroundColor: successRate > 90 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                          color: successRate > 90 ? '#34d399' : '#f87171',
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px'
                        }}>
                          {successRate.toFixed(0)}% Success
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Side panels */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Logger Test Tool */}
          <form onSubmit={handleLogTest} style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: 0, color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Log Test Usage Event</h3>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Action Name</label>
              <input
                type="text"
                placeholder="gpt-4o completion call"
                value={logName}
                onChange={(e) => setLogName(e.target.value)}
                style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Category</label>
              <select
                value={logCategory}
                onChange={(e) => setLogCategory(e.target.value as any)}
                style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none', cursor: 'pointer' }}
              >
                <option value="model_call">Model Call (LLM tokens)</option>
                <option value="tool_execution">Tool Execution (compute time)</option>
                <option value="workflow_step">Workflow Step</option>
                <option value="api_sync">API Sync (calendar/email/chat)</option>
              </select>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Cost (USD)</label>
                <input
                  type="text"
                  value={logCost}
                  onChange={(e) => setLogCost(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Units / Tokens</label>
                <input
                  type="number"
                  value={logUnits}
                  onChange={(e) => setLogUnits(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none' }}
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={busy || !logName.trim()}
              style={{ width: '100%', padding: '0.65rem 1rem', borderRadius: '8px', backgroundColor: '#10b981', color: '#fff', fontSize: '0.95rem', fontWeight: 700, border: 'none', cursor: 'pointer', marginTop: '0.5rem' }}
            >
              {busy ? 'Logging...' : 'Trigger Usage Log'}
            </button>
          </form>

          {/* Users Allocation */}
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Allocation Cost by User</h3>
            {users.length === 0 ? (
              <div style={{ color: '#9ca3af', padding: '1rem', textAlign: 'center' }}>No users logs found.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {users.map((u) => (
                  <div key={u.email} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', borderBottom: '1px solid #374151', paddingBottom: '0.5rem' }}>
                    <span style={{ color: '#d1d5db' }}>{u.email}</span>
                    <span style={{ fontWeight: 700, color: '#f3f4f6' }}>${u.total_cost.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect, useRef } from 'react';
import { refreshAccessToken, getOrganizations } from '@/lib/chat-api';
import {
  createSandbox,
  submitCommand,
  getCommand,
  decideCommandApproval,
  DeveloperCommand,
} from '@/lib/developer-api';

export function TerminalMonitor() {
  const [sandboxName, setSandboxName] = useState('test-env');
  const [sandboxPath, setSandboxPath] = useState('.artifacts/sandbox_test');
  const [activeSandboxId, setActiveSandboxId] = useState<string | null>(null);
  const [commandLine, setCommandLine] = useState('');
  const [activeCommand, setActiveCommand] = useState<DeveloperCommand | null>(null);
  const [commandHistory, setCommandHistory] = useState<DeveloperCommand[]>([]);
  const [busy, setBusy] = useState(false);
  const [reason, setReason] = useState('');
  const [deciding, setDeciding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const consoleEndRef = useRef<HTMLDivElement>(null);

  // Poll command execution
  useEffect(() => {
    if (!activeCommand) return;
    if (['succeeded', 'failed', 'cancelled'].includes(activeCommand.status)) return;

    let timer: NodeJS.Timeout;

    async function poll() {
      try {
        const token = await refreshAccessToken();
        const orgs = await getOrganizations(token);
        if (!orgs[0]) return;

        const cmd = await getCommand(token, activeCommand!.id, orgs[0].id);
        setActiveCommand(cmd);

        // Update in history list
        setCommandHistory((current) =>
          current.map((item) => (item.id === cmd.id ? cmd : item))
        );

        if (['succeeded', 'failed', 'cancelled'].includes(cmd.status)) {
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
  }, [activeCommand]);

  useEffect(() => {
    consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeCommand?.stdout_redacted, activeCommand?.stderr_redacted]);

  async function handleCreateSandbox(e: React.FormEvent) {
    e.preventDefault();
    if (!sandboxName.trim() || !sandboxPath.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace available.');

      const result = await createSandbox(token, orgs[0].id, sandboxName.trim(), sandboxPath.trim());
      setActiveSandboxId(result.sandbox_id);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize sandbox.');
    } finally {
      setBusy(false);
    }
  }

  async function handleSendCommand(e: React.FormEvent) {
    e.preventDefault();
    if (!commandLine.trim() || !activeSandboxId || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace available.');

      const result = await submitCommand(token, orgs[0].id, activeSandboxId, commandLine.trim());
      const cmd = await getCommand(token, result.command_id, orgs[0].id);

      setActiveCommand(cmd);
      setCommandHistory((current) => [...current, cmd]);
      setCommandLine('');
    } catch (err: any) {
      setError(err.message || 'Failed to submit command.');
    } finally {
      setBusy(false);
    }
  }

  async function handleApproval(approved: boolean) {
    if (!activeCommand || deciding) return;
    setDeciding(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      // In custom schema, the approval ID is checked. 
      // For testing, we mock the approval ID to equal the command ID since they correlate 1-1.
      await decideCommandApproval(token, orgs[0].id, activeCommand.id, approved, reason);

      const cmd = await getCommand(token, activeCommand.id, orgs[0].id);
      setActiveCommand(cmd);
      setCommandHistory((current) =>
        current.map((item) => (item.id === cmd.id ? cmd : item))
      );
      setReason('');
    } catch (err: any) {
      setError(err.message || 'Failed to apply decision.');
    } finally {
      setDeciding(false);
    }
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: '#f3f4f6', margin: '0 0 0.5rem 0', letterSpacing: '-0.025em' }}>
          Terminal Subprocess Sandbox
        </h1>
        <p style={{ color: '#9ca3af', fontSize: '1.1rem', margin: 0 }}>
          Execute safe shell commands and apply gated approvals inside verified sandbox boundaries.
        </p>
      </div>

      {error && (
        <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#f87171', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          {error}
        </div>
      )}

      {/* Sandbox Config Form */}
      {!activeSandboxId ? (
        <form onSubmit={handleCreateSandbox} style={{ backgroundColor: '#1f2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151', display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', color: '#f3f4f6', fontSize: '1.2rem', fontWeight: 700 }}>Initialize Sandbox Workspace</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Sandbox Name</label>
              <input
                type="text"
                value={sandboxName}
                onChange={(e) => setSandboxName(e.target.value)}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Sandbox Relative Path</label>
              <input
                type="text"
                value={sandboxPath}
                onChange={(e) => setSandboxPath(e.target.value)}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={busy}
            style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', backgroundColor: '#3b82f6', color: '#fff', fontSize: '1rem', fontWeight: 700, border: 'none', cursor: 'pointer' }}
          >
            {busy ? 'Setting up...' : 'Provision Sandbox Directory'}
          </button>
        </form>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Shell Console Interface */}
          <div style={{ backgroundColor: '#090d16', border: '1px solid #1f2937', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)' }}>
            {/* Terminal Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1rem', backgroundColor: '#111827', borderBottom: '1px solid #1f2937' }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ef4444', display: 'inline-block' }}></span>
                <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#f59e0b', display: 'inline-block' }}></span>
                <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block' }}></span>
              </div>
              <span style={{ fontSize: '0.8rem', color: '#9ca3af', fontFamily: 'monospace' }}>
                bash - sandbox: {sandboxName} ({sandboxPath})
              </span>
              <span style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 700 }}>CONNECTED</span>
            </div>

            {/* Terminal Screen Console */}
            <div style={{ height: '350px', overflowY: 'auto', padding: '1rem', fontFamily: 'monospace', fontSize: '0.9rem', color: '#f3f4f6', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>$ Welcome to Aether Sandboxed Shell. Type a command to execute.</div>
              {commandHistory.map((item) => (
                <div key={item.id} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <div style={{ color: '#3b82f6', fontWeight: 700 }}>
                    $ {item.command_line}
                    <span style={{
                      float: 'right',
                      fontSize: '0.75rem',
                      padding: '0.1rem 0.4rem',
                      borderRadius: '4px',
                      backgroundColor: item.status === 'succeeded' ? 'rgba(16, 185, 129, 0.15)' : item.status === 'failed' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                      color: item.status === 'succeeded' ? '#10b981' : item.status === 'failed' ? '#f87171' : '#60a5fa'
                    }}>
                      {item.status.toUpperCase()}
                    </span>
                  </div>
                  {item.stdout_redacted && (
                    <pre style={{ margin: 0, paddingLeft: '1rem', color: '#10b981', whiteSpace: 'pre-wrap' }}>{item.stdout_redacted}</pre>
                  )}
                  {item.stderr_redacted && (
                    <pre style={{ margin: 0, paddingLeft: '1rem', color: '#f87171', whiteSpace: 'pre-wrap' }}>{item.stderr_redacted}</pre>
                  )}
                </div>
              ))}
              {activeCommand && !['succeeded', 'failed', 'cancelled'].includes(activeCommand.status) && (
                <div style={{ color: '#f59e0b', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span style={{ animation: 'pulse 1.5s infinite' }}>●</span>
                  <span>Command status: {activeCommand.status.toUpperCase()}...</span>
                </div>
              )}
              <div ref={consoleEndRef} />
            </div>

            {/* Input CLI Box */}
            <form onSubmit={handleSendCommand} style={{ display: 'flex', borderTop: '1px solid #1f2937' }}>
              <span style={{ padding: '0.75rem 0.5rem 0.75rem 1rem', color: '#3b82f6', backgroundColor: '#090d16', fontFamily: 'monospace', fontWeight: 700 }}>$</span>
              <input
                type="text"
                placeholder="git status / pytest / npm test"
                value={commandLine}
                onChange={(e) => setCommandLine(e.target.value)}
                disabled={busy || (activeCommand !== null && !['succeeded', 'failed', 'cancelled'].includes(activeCommand.status))}
                style={{ flex: 1, padding: '0.75rem 1rem 0.75rem 0', border: 'none', backgroundColor: '#090d16', color: '#f3f4f6', fontSize: '1rem', outline: 'none', fontFamily: 'monospace' }}
              />
              <button
                type="submit"
                disabled={busy || !commandLine.trim() || (activeCommand !== null && !['succeeded', 'failed', 'cancelled'].includes(activeCommand.status))}
                style={{ padding: '0 1.5rem', backgroundColor: '#1e293b', color: '#f3f4f6', border: 'none', borderLeft: '1px solid #1f2937', cursor: 'pointer', fontWeight: 700 }}
              >
                Execute
              </button>
            </form>
          </div>

          {/* Gated Command Decision Screen */}
          {activeCommand && activeCommand.status === 'awaiting_approval' && (
            <div style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)', padding: '1.5rem', borderRadius: '12px', border: '1px solid #f59e0b', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <h4 style={{ margin: '0 0 0.25rem 0', color: '#f59e0b', fontSize: '1.1rem', fontWeight: 700 }}>Owner Execution Consent Gate</h4>
                <p style={{ margin: 0, color: '#d1d5db', fontSize: '0.9rem' }}>
                  The shell has paused on a gated command: <code style={{ fontFamily: 'monospace', backgroundColor: 'rgba(0,0,0,0.3)', padding: '0.1rem 0.4rem', borderRadius: '4px', color: '#fff' }}>{activeCommand.command_line}</code>. Please review and decide.
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
                  Approve Execution
                </button>
                <button
                  onClick={() => handleApproval(false)}
                  disabled={deciding}
                  style={{ flex: 1, padding: '0.5rem 1rem', borderRadius: '6px', backgroundColor: '#ef4444', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer' }}
                >
                  Reject Execution
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

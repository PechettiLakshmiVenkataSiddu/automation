'use client';

import { useState, useEffect } from 'react';
import { refreshAccessToken, getOrganizations } from '@/lib/chat-api';
import {
  createConnection,
  revokeConnection,
  getMessages,
  proposeEmail,
  getProposals,
  decideProposal,
  EmailMessage,
  EmailProposal,
} from '@/lib/email-api';

export function EmailWorkspace() {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<EmailMessage[]>([]);
  const [proposals, setProposals] = useState<EmailProposal[]>([]);
  const [recipient, setRecipient] = useState('');
  const [subject, setSubject] = useState('');
  const [bodyText, setBodyText] = useState('');
  const [attachmentName, setAttachmentName] = useState('');
  const [busy, setBusy] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Poll inbox messages and proposals
  useEffect(() => {
    let timer: NodeJS.Timeout;

    async function loadData() {
      try {
        const token = await refreshAccessToken();
        const orgs = await getOrganizations(token);
        if (!orgs[0]) return;

        try {
          const fetchedMessages = await getMessages(token, orgs[0].id);
          setMessages(fetchedMessages);
          setConnected(true);
        } catch {
          setConnected(false);
        }

        const fetchedProps = await getProposals(token, orgs[0].id);
        setProposals(fetchedProps);

        timer = setTimeout(loadData, 3000);
      } catch (err) {
        console.error('Failed to poll email data:', err);
        timer = setTimeout(loadData, 5000);
      }
    }

    loadData();

    return () => clearTimeout(timer);
  }, []);

  async function handleConnect(e: React.MouseEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      // Register connection with mock credentials for simulation
      await createConnection(
        token,
        orgs[0].id,
        "mock-access-token",
        "mock-refresh-token",
        ["https://www.googleapis.com/auth/gmail.send"],
        3600
      );
      setConnected(true);
    } catch (err: any) {
      setError(err.message || 'Failed to connect email.');
    } finally {
      setBusy(false);
    }
  }

  async function handleDisconnect(e: React.MouseEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      await revokeConnection(token, orgs[0].id);
      setConnected(false);
      setMessages([]);
    } catch (err: any) {
      setError(err.message || 'Failed to disconnect.');
    } finally {
      setBusy(false);
    }
  }

  async function handleProposeSend(e: React.FormEvent) {
    e.preventDefault();
    if (!recipient.trim() || !bodyText.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      const attachments = attachmentName.trim()
        ? [{ filename: attachmentName.trim(), size_bytes: 1024 }]
        : [];

      await proposeEmail(
        token,
        orgs[0].id,
        recipient.trim(),
        subject.trim() || null,
        bodyText.trim(),
        attachments
      );

      // Reset Form
      setRecipient('');
      setSubject('');
      setBodyText('');
      setAttachmentName('');

      // Refresh list immediately
      const fetchedProps = await getProposals(token, orgs[0].id);
      setProposals(fetchedProps);
    } catch (err: any) {
      setError(err.message || 'Failed to compose draft.');
    } finally {
      setBusy(false);
    }
  }

  async function handleProposalApproval(proposalId: string, approved: boolean) {
    if (deciding) return;
    setDeciding(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      await decideProposal(token, orgs[0].id, proposalId, approved, reason);

      const fetchedProps = await getProposals(token, orgs[0].id);
      setProposals(fetchedProps);
      setReason('');
    } catch (err: any) {
      setError(err.message || 'Failed to resolve decision gate.');
    } finally {
      setDeciding(false);
    }
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: '#f3f4f6', margin: '0 0 0.5rem 0', letterSpacing: '-0.025em' }}>
            Email Integration
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '1.1rem', margin: 0 }}>
            Sync Gmail messages, draft agent compostings, and review approvals before delivery.
          </p>
        </div>
        <div>
          {connected ? (
            <button
              onClick={handleDisconnect}
              disabled={busy}
              style={{ padding: '0.6rem 1.2rem', borderRadius: '8px', border: '1px solid #ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#f87171', fontWeight: 700, cursor: 'pointer' }}
            >
              Disconnect Gmail API
            </button>
          ) : (
            <button
              onClick={handleConnect}
              disabled={busy}
              style={{ padding: '0.6rem 1.2rem', borderRadius: '8px', border: 'none', backgroundColor: '#3b82f6', color: '#fff', fontWeight: 700, cursor: 'pointer' }}
            >
              Connect Gmail API
            </button>
          )}
        </div>
      </div>

      {error && (
        <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#f87171', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          {error}
        </div>
      )}

      {/* Grid Dashboard */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '2rem' }}>
        {/* Inbox Cache & Proposals */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Messages */}
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Inbox / Messages</h3>
            {!connected ? (
              <div style={{ color: '#9ca3af', textAlign: 'center', padding: '2rem' }}>
                Gmail API is disconnected. Connect to synchronize inbox.
              </div>
            ) : messages.length === 0 ? (
              <div style={{ color: '#9ca3af', textAlign: 'center', padding: '2rem' }}>
                Inbox is empty.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {messages.map((msg) => (
                  <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', padding: '1rem', backgroundColor: '#111827', borderRadius: '8px', border: '1px solid #374151', gap: '0.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, color: '#f3f4f6' }}>{msg.subject || '(No Subject)'}</span>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor: msg.status === 'received' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                        color: msg.status === 'received' ? '#60a5fa' : '#10b981',
                        padding: '0.1rem 0.4rem',
                        borderRadius: '4px'
                      }}>
                        {msg.status.toUpperCase()}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>From: {msg.from_address}</span>
                    <p style={{ margin: '0.25rem 0', color: '#d1d5db', fontSize: '0.9rem' }}>{msg.body_snippet}</p>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', fontFamily: 'monospace' }}>
                      {new Date(msg.received_at).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Outgoing Proposals Queue */}
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Pending Outbox Approvals</h3>
            {proposals.length === 0 ? (
              <div style={{ color: '#9ca3af', textAlign: 'center', padding: '2rem' }}>
                No active outgoing email proposals.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {proposals.map((prop) => (
                  <div key={prop.id} style={{
                    display: 'flex',
                    flexDirection: 'column',
                    padding: '1rem',
                    backgroundColor: '#111827',
                    borderRadius: '8px',
                    border: prop.status === 'pending' ? '1px solid #f59e0b' : '1px solid #374151',
                    gap: '0.5rem'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, color: '#f3f4f6' }}>{prop.subject || '(No Subject)'}</span>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor: prop.status === 'approved' ? 'rgba(16, 185, 129, 0.1)' : prop.status === 'rejected' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                        color: prop.status === 'approved' ? '#10b981' : prop.status === 'rejected' ? '#f87171' : '#f59e0b',
                        padding: '0.1rem 0.4rem',
                        borderRadius: '4px'
                      }}>
                        {prop.status.toUpperCase()}
                      </span>
                    </div>

                    <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>To: {prop.recipient_address}</span>
                    <pre style={{ margin: 0, padding: '0.5rem', backgroundColor: '#1f2937', borderRadius: '4px', color: '#d1d5db', fontSize: '0.85rem', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                      {prop.body_text}
                    </pre>

                    {prop.attachments.length > 0 && (
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {prop.attachments.map((att, idx) => (
                          <span key={idx} style={{ fontSize: '0.75rem', color: '#60a5fa', border: '1px solid #60a5fa', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                            📎 {att.filename}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Pending Decision Fields */}
                    {prop.status === 'pending' && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                        <input
                          type="text"
                          placeholder="Reason for approval/rejection (optional)"
                          value={reason}
                          onChange={(e) => setReason(e.target.value)}
                          disabled={deciding}
                          style={{ width: '100%', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #4b5563', backgroundColor: '#1f2937', color: '#f3f4f6', fontSize: '0.85rem', outline: 'none' }}
                        />
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button
                            onClick={() => handleProposalApproval(prop.id, true)}
                            disabled={deciding}
                            style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', backgroundColor: '#10b981', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem' }}
                          >
                            Approve Send
                          </button>
                          <button
                            onClick={() => handleProposalApproval(prop.id, false)}
                            disabled={deciding}
                            style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', backgroundColor: '#ef4444', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem' }}
                          >
                            Reject Send
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Scheduler / Composer Form Panel */}
        <div>
          <form onSubmit={handleProposeSend} style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Compose Draft</h3>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Recipient Email</label>
              <input
                type="email"
                placeholder="client@gmail.com"
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
                disabled={busy}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Subject</label>
              <input
                type="text"
                placeholder="Project Deliverable"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                disabled={busy}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Message Body</label>
              <textarea
                placeholder="Compose message..."
                value={bodyText}
                onChange={(e) => setBodyText(e.target.value)}
                disabled={busy}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none', resize: 'vertical', height: '140px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Attachment Filename (optional)</label>
              <input
                type="text"
                placeholder="invoice.pdf"
                value={attachmentName}
                onChange={(e) => setAttachmentName(e.target.value)}
                disabled={busy}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <button
              type="submit"
              disabled={busy || !recipient.trim() || !bodyText.trim()}
              style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', backgroundColor: '#3b82f6', color: '#fff', fontSize: '1rem', fontWeight: 700, border: 'none', cursor: 'pointer' }}
            >
              {busy ? 'Queueing draft...' : 'Queue Outbox Proposal'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

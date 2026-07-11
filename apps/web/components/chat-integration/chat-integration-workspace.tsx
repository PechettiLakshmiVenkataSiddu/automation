'use client';

import { useState, useEffect } from 'react';
import { refreshAccessToken, getOrganizations } from '@/lib/chat-api';
import {
  createConnection,
  revokeConnection,
  getMessages,
  proposeMessage,
  getProposals,
  decideProposal,
  ChatMessage,
  ChatProposal,
} from '@/lib/chat-integration-api';

export function ChatIntegrationWorkspace() {
  const [connected, setConnected] = useState(false);
  const [activeChannel, setActiveChannel] = useState('C-GENERAL');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [proposals, setProposals] = useState<ChatProposal[]>([]);
  const [messageText, setMessageText] = useState('');
  const [busy, setBusy] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  const channelsList = [
    { id: 'C-GENERAL', name: '# general' },
    { id: 'C-ENGINEERING', name: '# engineering' },
    { id: 'C-ANNOUNCEMENTS', name: '# announcements' },
  ];

  // Poll chat messages and outbox proposals
  useEffect(() => {
    let timer: NodeJS.Timeout;

    async function loadData() {
      try {
        const token = await refreshAccessToken();
        const orgs = await getOrganizations(token);
        if (!orgs[0]) return;

        try {
          const fetchedMessages = await getMessages(token, orgs[0].id, 'slack', activeChannel);
          setMessages(fetchedMessages);
          setConnected(true);
        } catch {
          setConnected(false);
        }

        const fetchedProps = await getProposals(token, orgs[0].id);
        setProposals(fetchedProps);

        timer = setTimeout(loadData, 3000);
      } catch (err) {
        console.error('Failed to poll chat data:', err);
        timer = setTimeout(loadData, 5000);
      }
    }

    loadData();

    return () => clearTimeout(timer);
  }, [activeChannel]);

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
        'slack',
        "mock-access-token",
        "mock-refresh-token",
        ["chat:write", "chat:write.public"],
        3600
      );
      setConnected(true);
    } catch (err: any) {
      setError(err.message || 'Failed to connect chat integration.');
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

      await revokeConnection(token, orgs[0].id, 'slack');
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
    if (!messageText.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      await proposeMessage(
        token,
        orgs[0].id,
        activeChannel,
        messageText.trim()
      );

      // Reset Form
      setMessageText('');

      // Refresh list immediately
      const fetchedProps = await getProposals(token, orgs[0].id);
      setProposals(fetchedProps);
    } catch (err: any) {
      setError(err.message || 'Failed to queue outgoing message.');
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
            Slack / Teams Chat
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '1.1rem', margin: 0 }}>
            Sync messages feed, draft agent conversations, and verify outbox deliveries.
          </p>
        </div>
        <div>
          {connected ? (
            <button
              onClick={handleDisconnect}
              disabled={busy}
              style={{ padding: '0.6rem 1.2rem', borderRadius: '8px', border: '1px solid #ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#f87171', fontWeight: 700, cursor: 'pointer' }}
            >
              Disconnect Slack API
            </button>
          ) : (
            <button
              onClick={handleConnect}
              disabled={busy}
              style={{ padding: '0.6rem 1.2rem', borderRadius: '8px', border: 'none', backgroundColor: '#3b82f6', color: '#fff', fontWeight: 700, cursor: 'pointer' }}
            >
              Connect Slack API
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
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 3fr', gap: '2rem' }}>
        {/* Sidebar channel selector */}
        <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', paddingLeft: '0.5rem', marginBottom: '0.5rem' }}>Channels</span>
          {channelsList.map((ch) => (
            <button
              key={ch.id}
              onClick={() => setActiveChannel(ch.id)}
              style={{
                textAlign: 'left',
                padding: '0.6rem 0.8rem',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: activeChannel === ch.id ? '#3b82f6' : 'transparent',
                color: activeChannel === ch.id ? '#fff' : '#d1d5db',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {ch.name}
            </button>
          ))}
        </div>

        {/* Content feed panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Chat Messages */}
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: 0, color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Messages history</h3>
            {!connected ? (
              <div style={{ color: '#9ca3af', textAlign: 'center', padding: '4rem 2rem' }}>
                Slack/Teams connection is disconnected. Connect to sync.
              </div>
            ) : messages.length === 0 ? (
              <div style={{ color: '#9ca3af', textAlign: 'center', padding: '4rem 2rem' }}>
                No messages stream found.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '350px', overflowY: 'auto', paddingRight: '0.5rem' }}>
                {messages.map((msg) => (
                  <div key={msg.id} style={{ display: 'flex', gap: '1rem', padding: '0.75rem', backgroundColor: '#111827', borderRadius: '8px', border: '1px solid #374151' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                        <span style={{ fontWeight: 700, color: '#f3f4f6', fontSize: '0.9rem' }}>{msg.sender_id}</span>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280', fontFamily: 'monospace' }}>
                          {new Date(msg.received_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <p style={{ margin: 0, color: '#d1d5db', fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>{msg.message_text}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Compose Composer */}
            {connected && (
              <form onSubmit={handleProposeSend} style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <input
                  type="text"
                  placeholder="Propose message to channel..."
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  disabled={busy}
                  style={{ flex: 1, padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
                />
                <button
                  type="submit"
                  disabled={busy || !messageText.trim()}
                  style={{ padding: '0.75rem 1.5rem', borderRadius: '8px', backgroundColor: '#3b82f6', color: '#fff', fontSize: '1rem', fontWeight: 700, border: 'none', cursor: 'pointer' }}
                >
                  {busy ? 'Proposing...' : 'Propose Send'}
                </button>
              </form>
            )}
          </div>

          {/* Pending Proposals Queue */}
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Pending Outbox Approvals</h3>
            {proposals.length === 0 ? (
              <div style={{ color: '#9ca3af', textAlign: 'center', padding: '2rem' }}>
                No active outgoing message proposals.
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
                      <span style={{ fontWeight: 700, color: '#f3f4f6', fontSize: '0.9rem' }}>Channel: {prop.channel_id}</span>
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

                    <pre style={{ margin: 0, padding: '0.5rem', backgroundColor: '#1f2937', borderRadius: '4px', color: '#d1d5db', fontSize: '0.85rem', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                      {prop.message_text}
                    </pre>

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
                            Approve Post
                          </button>
                          <button
                            onClick={() => handleProposalApproval(prop.id, false)}
                            disabled={deciding}
                            style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', backgroundColor: '#ef4444', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem' }}
                          >
                            Reject Post
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
      </div>
    </div>
  );
}

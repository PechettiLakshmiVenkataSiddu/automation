'use client';

import { useState, useEffect } from 'react';
import { refreshAccessToken, getOrganizations } from '@/lib/chat-api';
import {
  createConnection,
  revokeConnection,
  getEvents,
  proposeEvent,
  getProposals,
  decideProposal,
  CalendarEvent,
  CalendarProposal,
} from '@/lib/calendar-api';

export function CalendarWorkspace() {
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [proposals, setProposals] = useState<CalendarProposal[]>([]);
  const [summary, setSummary] = useState('');
  const [description, setDescription] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [attendeeEmail, setAttendeeEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Poll events and proposals
  useEffect(() => {
    let timer: NodeJS.Timeout;

    async function loadData() {
      try {
        const token = await refreshAccessToken();
        const orgs = await getOrganizations(token);
        if (!orgs[0]) return;

        // Calculate a 7-day range for events listing
        const start = new Date();
        start.setHours(0, 0, 0, 0);
        const end = new Date();
        end.setDate(end.getDate() + 7);

        try {
          const fetchedEvents = await getEvents(token, orgs[0].id, start.toISOString(), end.toISOString());
          setEvents(fetchedEvents);
          setConnected(true);
        } catch {
          setConnected(false);
        }

        const fetchedProps = await getProposals(token, orgs[0].id);
        setProposals(fetchedProps);

        timer = setTimeout(loadData, 3000);
      } catch (err) {
        console.error('Failed to poll calendar data:', err);
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
        ["https://www.googleapis.com/auth/calendar.events"],
        ["*"],
        3600
      );
      setConnected(true);
    } catch (err: any) {
      setError(err.message || 'Failed to connect calendar.');
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
      setEvents([]);
    } catch (err: any) {
      setError(err.message || 'Failed to disconnect.');
    } finally {
      setBusy(false);
    }
  }

  async function handleSchedule(e: React.FormEvent) {
    e.preventDefault();
    if (!summary.trim() || !startTime || !endTime || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      const attendees = attendeeEmail.trim() ? [{ email: attendeeEmail.trim() }] : [];
      const result = await proposeEvent(
        token,
        orgs[0].id,
        summary.trim(),
        description.trim() || null,
        new Date(startTime).toISOString(),
        new Date(endTime).toISOString(),
        attendees
      );

      // Reset Form
      setSummary('');
      setDescription('');
      setStartTime('');
      setEndTime('');
      setAttendeeEmail('');

      // Refresh list immediately
      const fetchedProps = await getProposals(token, orgs[0].id);
      setProposals(fetchedProps);
    } catch (err: any) {
      setError(err.message || 'Failed to schedule event.');
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
            Calendar Integration
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '1.1rem', margin: 0 }}>
            Sync schedules, manage availability conflicts, and approve event proposals.
          </p>
        </div>
        <div>
          {connected ? (
            <button
              onClick={handleDisconnect}
              disabled={busy}
              style={{ padding: '0.6rem 1.2rem', borderRadius: '8px', border: '1px solid #ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#f87171', fontWeight: 700, cursor: 'pointer' }}
            >
              Disconnect Google Calendar
            </button>
          ) : (
            <button
              onClick={handleConnect}
              disabled={busy}
              style={{ padding: '0.6rem 1.2rem', borderRadius: '8px', border: 'none', backgroundColor: '#3b82f6', color: '#fff', fontWeight: 700, cursor: 'pointer' }}
            >
              Connect Google Calendar
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
        {/* Availability Calendar & Proposals */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Availability Event Blocks */}
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Upcoming Events (7 Days)</h3>
            {!connected ? (
              <div style={{ color: '#9ca3af', textAlign: 'center', padding: '2rem' }}>
                Google Calendar is disconnected. Connect to sync events.
              </div>
            ) : events.length === 0 ? (
              <div style={{ color: '#9ca3af', textAlign: 'center', padding: '2rem' }}>
                No events scheduled.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {events.map((ev) => (
                  <div key={ev.id} style={{ display: 'flex', flexDirection: 'column', padding: '1rem', backgroundColor: '#111827', borderRadius: '8px', border: '1px solid #374151' }}>
                    <div style={{ display: 'flex', justifySelf: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, color: '#f3f4f6' }}>{ev.summary}</span>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                        {ev.status.toUpperCase()}
                      </span>
                    </div>
                    {ev.description && <p style={{ margin: '0.25rem 0', color: '#9ca3af', fontSize: '0.9rem' }}>{ev.description}</p>}
                    <span style={{ fontSize: '0.8rem', color: '#6b7280', fontFamily: 'monospace' }}>
                      {new Date(ev.start_time).toLocaleString()} - {new Date(ev.end_time).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Incoming Proposals Queue */}
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Proposed Schedules</h3>
            {proposals.length === 0 ? (
              <div style={{ color: '#9ca3af', textAlign: 'center', padding: '2rem' }}>
                No active scheduling proposals.
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
                      <span style={{ fontWeight: 700, color: '#f3f4f6' }}>{prop.summary}</span>
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

                    {prop.conflict_detected && (
                      <span style={{ alignSelf: 'flex-start', fontSize: '0.75rem', fontWeight: 700, color: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', padding: '0.1rem 0.4rem', borderRadius: '4px', border: '1px solid #ef4444' }}>
                        DOUBLE BOOKING CONFLICT DETECTED
                      </span>
                    )}

                    <span style={{ fontSize: '0.8rem', color: '#6b7280', fontFamily: 'monospace' }}>
                      {new Date(prop.start_time).toLocaleString()} - {new Date(prop.end_time).toLocaleString()}
                    </span>

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
                            Approve Proposal
                          </button>
                          <button
                            onClick={() => handleProposalApproval(prop.id, false)}
                            disabled={deciding}
                            style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', backgroundColor: '#ef4444', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem' }}
                          >
                            Reject Proposal
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

        {/* Scheduler Form Panel */}
        <div>
          <form onSubmit={handleSchedule} style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Propose Event</h3>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Summary / Title</label>
              <input
                type="text"
                placeholder="Product Demo Sync"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                disabled={busy}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Description</label>
              <textarea
                placeholder="Review milestone plan"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={busy}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none', resize: 'vertical', height: '80px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Attendee Email</label>
              <input
                type="email"
                placeholder="client@gmail.com"
                value={attendeeEmail}
                onChange={(e) => setAttendeeEmail(e.target.value)}
                disabled={busy}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Start Time</label>
              <input
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                disabled={busy}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>End Time</label>
              <input
                type="datetime-local"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                disabled={busy}
                style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <button
              type="submit"
              disabled={busy || !summary.trim() || !startTime || !endTime}
              style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', backgroundColor: '#3b82f6', color: '#fff', fontSize: '1rem', fontWeight: 700, border: 'none', cursor: 'pointer' }}
            >
              {busy ? 'Submitting proposal...' : 'Propose Event Schedule'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

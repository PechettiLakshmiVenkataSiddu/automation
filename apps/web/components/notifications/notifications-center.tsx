'use client';

import { useState, useEffect } from 'react';
import { refreshAccessToken, getOrganizations } from '@/lib/chat-api';
import {
  getNotifications,
  markRead,
  getPreferences,
  updatePreferences,
  dispatchNotification,
  NotificationItem,
} from '@/lib/notifications-api';

export function NotificationsCenter() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [channels, setChannels] = useState<Array<'in_app' | 'email' | 'push'>>(['in_app']);
  const [quietHoursStart, setQuietHoursStart] = useState('');
  const [quietHoursEnd, setQuietHoursEnd] = useState('');
  const [unsubscribed, setUnsubscribed] = useState(false);

  const [testTitle, setTestTitle] = useState('');
  const [testMessage, setTestMessage] = useState('');
  const [testLevel, setTestLevel] = useState<'info' | 'warning' | 'error'>('info');

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Poll notifications
  useEffect(() => {
    let timer: NodeJS.Timeout;

    async function loadData() {
      try {
        const token = await refreshAccessToken();
        const orgs = await getOrganizations(token);
        if (!orgs[0]) return;

        const fetchedNotifs = await getNotifications(token, orgs[0].id);
        setNotifications(fetchedNotifs);

        timer = setTimeout(loadData, 3000);
      } catch (err) {
        console.error('Failed to poll notifications:', err);
        timer = setTimeout(loadData, 5000);
      }
    }

    loadData();

    return () => clearTimeout(timer);
  }, []);

  // Fetch initial preferences
  useEffect(() => {
    async function loadPrefs() {
      try {
        const token = await refreshAccessToken();
        const orgs = await getOrganizations(token);
        if (!orgs[0]) return;

        const prefs = await getPreferences(token, orgs[0].id);
        setChannels(prefs.channels);
        setQuietHoursStart(prefs.quiet_hours_start || '');
        setQuietHoursEnd(prefs.quiet_hours_end || '');
        setUnsubscribed(prefs.unsubscribed);
      } catch (err) {
        console.error('Failed to load notification preferences:', err);
      }
    }
    loadPrefs();
  }, []);

  async function handleUpdatePrefs(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      await updatePreferences(
        token,
        orgs[0].id,
        channels,
        quietHoursStart || null,
        quietHoursEnd || null,
        unsubscribed
      );
    } catch (err: any) {
      setError(err.message || 'Failed to update preferences.');
    } finally {
      setBusy(false);
    }
  }

  async function handleMarkRead(notificationId: string) {
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      await markRead(token, orgs[0].id, notificationId);

      const fetchedNotifs = await getNotifications(token, orgs[0].id);
      setNotifications(fetchedNotifs);
    } catch (err: any) {
      setError(err.message || 'Failed to mark read.');
    }
  }

  async function handleDispatchTest(e: React.FormEvent) {
    e.preventDefault();
    if (!testTitle.trim() || !testMessage.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const orgs = await getOrganizations(token);
      if (!orgs[0]) throw new Error('No active workspace.');

      const result = await dispatchNotification(
        token,
        orgs[0].id,
        testTitle.trim(),
        testMessage.trim(),
        testLevel
      );

      if (!result.notification_id) {
        setError('Notification suppressed (either unsubscribed, quiet hours external blocks, or deduplication throttled).');
      }

      setTestTitle('');
      setTestMessage('');
      setTestLevel('info');

      const fetchedNotifs = await getNotifications(token, orgs[0].id);
      setNotifications(fetchedNotifs);
    } catch (err: any) {
      setError(err.message || 'Failed to dispatch test notification.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: '#f3f4f6', margin: '0 0 0.5rem 0', letterSpacing: '-0.025em' }}>
            Notification Center
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '1.1rem', margin: 0 }}>
            Configure schedules, delivery channels, and view real-time platform system updates.
          </p>
        </div>
      </div>

      {error && (
        <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#f87171', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          {error}
        </div>
      )}

      {/* Grid Dashboard */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '2rem' }}>
        {/* Inbox / Live notifications Feed */}
        <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
          <h3 style={{ margin: '0 0 1.25rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Alert Logs Feed</h3>
          {notifications.length === 0 ? (
            <div style={{ color: '#9ca3af', textAlign: 'center', padding: '4rem 2rem' }}>
              No notifications logs found.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '550px', overflowY: 'auto', paddingRight: '0.5rem' }}>
              {notifications.map((notif) => {
                const isError = notif.level === 'error';
                const isWarning = notif.level === 'warning';
                const cardBorder = isError ? '1px solid #ef4444' : isWarning ? '1px solid #f59e0b' : '1px solid #3b82f6';
                const levelBg = isError ? 'rgba(239, 68, 68, 0.1)' : isWarning ? 'rgba(245, 158, 11, 0.1)' : 'rgba(59, 130, 246, 0.1)';
                const levelColor = isError ? '#f87171' : isWarning ? '#fbbf24' : '#60a5fa';

                return (
                  <div key={notif.id} style={{
                    display: 'flex',
                    flexDirection: 'column',
                    padding: '1rem',
                    backgroundColor: '#111827',
                    borderRadius: '8px',
                    border: cardBorder,
                    opacity: notif.status === 'read' ? 0.6 : 1,
                    gap: '0.5rem',
                    transition: 'all 0.2s'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 800, color: '#f3f4f6', fontSize: '1rem' }}>{notif.title}</span>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <span style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          backgroundColor: levelBg,
                          color: levelColor,
                          padding: '0.1rem 0.4rem',
                          borderRadius: '4px'
                        }}>
                          {notif.level.toUpperCase()}
                        </span>
                        {notif.status === 'unread' && (
                          <button
                            onClick={() => handleMarkRead(notif.id)}
                            style={{
                              border: 'none',
                              backgroundColor: '#3b82f6',
                              color: '#fff',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              padding: '0.15rem 0.4rem',
                              borderRadius: '4px',
                              cursor: 'pointer'
                            }}
                          >
                            Mark Read
                          </button>
                        )}
                      </div>
                    </div>
                    <p style={{ margin: 0, color: '#d1d5db', fontSize: '0.95rem' }}>{notif.message}</p>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#6b7280' }}>
                      <span>Sent via: {notif.sent_channels.join(', ') || 'none'}</span>
                      <span style={{ fontFamily: 'monospace' }}>{new Date(notif.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Configurations Side Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Preferences */}
          <form onSubmit={handleUpdatePrefs} style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: 0, color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Preferences Settings</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <input
                type="checkbox"
                id="unsubscribed"
                checked={unsubscribed}
                onChange={(e) => setUnsubscribed(e.target.checked)}
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
              <label htmlFor="unsubscribed" style={{ color: '#d1d5db', fontWeight: 600, fontSize: '0.95rem', cursor: 'pointer' }}>
                Unsubscribe from all notifications
              </label>
            </div>

            {!unsubscribed && (
              <>
                <div>
                  <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Delivery Channels</label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {['in_app', 'email', 'push'].map((ch) => {
                      const isChecked = channels.includes(ch as any);
                      return (
                        <div key={ch} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <input
                            type="checkbox"
                            id={`ch-${ch}`}
                            checked={isChecked}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setChannels([...channels, ch as any]);
                              } else {
                                setChannels(channels.filter((val) => val !== ch));
                              }
                            }}
                            style={{ cursor: 'pointer' }}
                          />
                          <label htmlFor={`ch-${ch}`} style={{ color: '#d1d5db', fontSize: '0.9rem', cursor: 'pointer' }}>
                            {ch === 'in_app' ? 'In-App Notifications Log' : ch === 'email' ? 'Email Deliveries' : 'Mobile Push Alerts'}
                          </label>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Quiet Hours Start</label>
                    <input
                      type="time"
                      value={quietHoursStart}
                      onChange={(e) => setQuietHoursStart(e.target.value)}
                      style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.9rem', outline: 'none' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Quiet Hours End</label>
                    <input
                      type="time"
                      value={quietHoursEnd}
                      onChange={(e) => setQuietHoursEnd(e.target.value)}
                      style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.9rem', outline: 'none' }}
                    />
                  </div>
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={busy}
              style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', backgroundColor: '#3b82f6', color: '#fff', fontSize: '1rem', fontWeight: 700, border: 'none', cursor: 'pointer', marginTop: '0.5rem' }}
            >
              {busy ? 'Saving...' : 'Save Preferences'}
            </button>
          </form>

          {/* Test Dispatch Panel */}
          <form onSubmit={handleDispatchTest} style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: 0, color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Dispatch Test Alert</h3>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Title</label>
              <input
                type="text"
                placeholder="Milestone Alert"
                value={testTitle}
                onChange={(e) => setTestTitle(e.target.value)}
                style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Message</label>
              <textarea
                placeholder="Workflow runner completed milestone 1."
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none', height: '60px', resize: 'vertical' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Level</label>
              <select
                value={testLevel}
                onChange={(e) => setTestLevel(e.target.value as any)}
                style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none', cursor: 'pointer' }}
              >
                <option value="info">Info (Blue)</option>
                <option value="warning">Warning (Yellow)</option>
                <option value="error">Error (Red)</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={busy || !testTitle.trim() || !testMessage.trim()}
              style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', backgroundColor: '#10b981', color: '#fff', fontSize: '0.95rem', fontWeight: 700, border: 'none', cursor: 'pointer' }}
            >
              {busy ? 'Triggering...' : 'Fire Dispatch Alert'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

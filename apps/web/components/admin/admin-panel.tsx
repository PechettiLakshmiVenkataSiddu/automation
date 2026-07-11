'use client';

import { useState, useEffect } from 'react';
import { refreshAccessToken, getOrganizations } from '@/lib/chat-api';
import {
  getPolicy,
  updatePolicy,
  toggleBreakGlass,
  getMembers,
  inviteMember,
  updateMemberRole,
  removeMember,
  getApiKeys,
  createApiKey,
  revokeApiKey,
  getConnections,
  revokeConnection,
  searchAuditEvents,
  OrgMember,
  ApiKeyItem,
  ConnectionItem,
  AuditEventItem,
} from '@/lib/admin-api';

type TabType = 'policy' | 'members' | 'apikeys' | 'connections' | 'audit';

export function AdminPanel() {
  const [activeTab, setActiveTab] = useState<TabType>('policy');
  const [orgId, setOrgId] = useState<string | null>(null);

  // Policy state
  const [retentionNotifications, setRetentionNotifications] = useState(30);
  const [retentionAuditLogs, setRetentionAuditLogs] = useState(365);
  const [allowUnsecureSandboxes, setAllowUnsecureSandboxes] = useState(false);
  const [breakGlassActive, setBreakGlassActive] = useState(false);
  const [breakGlassReason, setBreakGlassReason] = useState('');

  // Members state
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'admin' | 'member' | 'viewer'>('member');

  // API Keys state
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyExpires, setNewKeyExpires] = useState('');
  const [generatedKeySecret, setGeneratedKeySecret] = useState<string | null>(null);

  // Connections state
  const [connections, setConnections] = useState<ConnectionItem[]>([]);

  // Audit state
  const [auditEvents, setAuditEvents] = useState<AuditEventItem[]>([]);
  const [filterEventType, setFilterEventType] = useState('');

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Resolve orgId
  useEffect(() => {
    async function initOrg() {
      try {
        const token = await refreshAccessToken();
        const orgs = await getOrganizations(token);
        if (orgs[0]) {
          setOrgId(orgs[0].id);
        }
      } catch (err) {
        console.error('Failed to init workspace:', err);
      }
    }
    initOrg();
  }, []);

  // Reload active tab data
  useEffect(() => {
    if (!orgId) return;
    loadTabData();
  }, [orgId, activeTab]);

  async function loadTabData() {
    if (!orgId) return;
    setError(null);
    try {
      const token = await refreshAccessToken();
      if (activeTab === 'policy') {
        const policy = await getPolicy(token, orgId);
        setRetentionNotifications(policy.retention_days_notifications);
        setRetentionAuditLogs(policy.retention_days_audit_logs);
        setAllowUnsecureSandboxes(policy.allow_unsecure_sandboxes);
        setBreakGlassActive(policy.break_glass_active);
        setBreakGlassReason(policy.break_glass_reason || '');
      } else if (activeTab === 'members') {
        const m = await getMembers(token, orgId);
        setMembers(m);
      } else if (activeTab === 'apikeys') {
        const k = await getApiKeys(token, orgId);
        setApiKeys(k);
      } else if (activeTab === 'connections') {
        const c = await getConnections(token, orgId);
        setConnections(c);
      } else if (activeTab === 'audit') {
        const a = await searchAuditEvents(token, orgId, filterEventType || undefined);
        setAuditEvents(a);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch tab data. Ensure you have administrator access.');
    }
  }

  async function handleSavePolicy(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId || busy) return;
    setBusy(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const token = await refreshAccessToken();
      await updatePolicy(
        token,
        orgId,
        retentionNotifications,
        retentionAuditLogs,
        allowUnsecureSandboxes
      );
      setSuccessMsg('System policies updated successfully.');
    } catch (err: any) {
      setError(err.message || 'Failed to save policies.');
    } finally {
      setBusy(false);
    }
  }

  async function handleToggleBreakGlass(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId || busy) return;
    if (!breakGlassActive && !breakGlassReason.trim()) {
      setError('Please provide a justification reason to activate break-glass mode.');
      return;
    }
    setBusy(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const token = await refreshAccessToken();
      const nextActive = !breakGlassActive;
      await toggleBreakGlass(
        token,
        orgId,
        nextActive,
        nextActive ? breakGlassReason.trim() : null
      );
      setBreakGlassActive(nextActive);
      setBreakGlassReason('');
      setSuccessMsg(`Emergency Override ${nextActive ? 'ACTIVATED' : 'deactivated'}.`);
    } catch (err: any) {
      setError(err.message || 'Failed to toggle break-glass.');
    } finally {
      setBusy(false);
    }
  }

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId || !inviteEmail.trim() || busy) return;
    setBusy(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const token = await refreshAccessToken();
      await inviteMember(token, orgId, inviteEmail.trim(), inviteRole);
      setInviteEmail('');
      setInviteRole('member');
      setSuccessMsg('Member invited successfully.');
      const m = await getMembers(token, orgId);
      setMembers(m);
    } catch (err: any) {
      setError(err.message || 'Failed to invite member.');
    } finally {
      setBusy(false);
    }
  }

  async function handleRoleUpdate(userId: string, role: 'admin' | 'member' | 'viewer') {
    if (!orgId) return;
    setError(null);
    setSuccessMsg(null);
    try {
      const token = await refreshAccessToken();
      await updateMemberRole(token, orgId, userId, role);
      setSuccessMsg('Member role updated.');
      const m = await getMembers(token, orgId);
      setMembers(m);
    } catch (err: any) {
      setError(err.message || 'Failed to update role.');
    }
  }

  async function handleRemoveMember(userId: string) {
    if (!orgId) return;
    setError(null);
    setSuccessMsg(null);
    try {
      const token = await refreshAccessToken();
      await removeMember(token, orgId, userId);
      setSuccessMsg('Membership revoked.');
      const m = await getMembers(token, orgId);
      setMembers(m);
    } catch (err: any) {
      setError(err.message || 'Failed to revoke membership.');
    }
  }

  async function handleCreateKey(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId || !newKeyName.trim() || busy) return;
    setBusy(true);
    setError(null);
    setSuccessMsg(null);
    setGeneratedKeySecret(null);
    try {
      const token = await refreshAccessToken();
      const expiresVal = newKeyExpires ? new Date(newKeyExpires).toISOString() : null;
      const res = await createApiKey(token, orgId, newKeyName.trim(), expiresVal);
      setGeneratedKeySecret(res.key);
      setNewKeyName('');
      setNewKeyExpires('');
      setSuccessMsg('API Key generated successfully.');
      const k = await getApiKeys(token, orgId);
      setApiKeys(k);
    } catch (err: any) {
      setError(err.message || 'Failed to generate API Key.');
    } finally {
      setBusy(false);
    }
  }

  async function handleRevokeKey(keyId: string) {
    if (!orgId) return;
    setError(null);
    setSuccessMsg(null);
    try {
      const token = await refreshAccessToken();
      await revokeApiKey(token, orgId, keyId);
      setSuccessMsg('API Key revoked.');
      const k = await getApiKeys(token, orgId);
      setApiKeys(k);
    } catch (err: any) {
      setError(err.message || 'Failed to revoke API Key.');
    }
  }

  async function handleRevokeConnection(provider: string) {
    if (!orgId) return;
    setError(null);
    setSuccessMsg(null);
    try {
      const token = await refreshAccessToken();
      await revokeConnection(token, orgId, provider);
      setSuccessMsg(`Revoked connections for ${provider}.`);
      const c = await getConnections(token, orgId);
      setConnections(c);
    } catch (err: any) {
      setError(err.message || 'Failed to revoke connection.');
    }
  }

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', fontFamily: 'Inter, sans-serif' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: '#f3f4f6', margin: '0 0 0.5rem 0', letterSpacing: '-0.025em' }}>
          Admin Panel Control Room
        </h1>
        <p style={{ color: '#9ca3af', fontSize: '1.1rem', margin: 0 }}>
          Manage user permissions, security policies, active connection tokens, and track system audits.
        </p>
      </div>

      {/* Tabs Menu */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid #374151', paddingBottom: '0.75rem', marginBottom: '1.75rem' }}>
        {[
          { id: 'policy', label: 'Security & Policy' },
          { id: 'members', label: 'Members' },
          { id: 'apikeys', label: 'API Keys' },
          { id: 'connections', label: 'Connections' },
          { id: 'audit', label: 'Audit Trail' },
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id as any);
                setError(null);
                setSuccessMsg(null);
                setGeneratedKeySecret(null);
              }}
              style={{
                padding: '0.6rem 1.2rem',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: isActive ? '#3b82f6' : 'transparent',
                color: isActive ? '#fff' : '#9ca3af',
                fontSize: '0.95rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {error && (
        <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#f87171', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          {error}
        </div>
      )}

      {successMsg && (
        <div style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          {successMsg}
        </div>
      )}

      {/* Tab Panels */}
      <div style={{ minHeight: '400px' }}>
        {/* Policy Tab */}
        {activeTab === 'policy' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
            {/* System Policies */}
            <form onSubmit={handleSavePolicy} style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.75rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <h3 style={{ margin: 0, color: '#f3f4f6', fontSize: '1.3rem', fontWeight: 700 }}>Data Retention & Safe sandboxes</h3>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                  Notifications Log Retention (Days)
                </label>
                <input
                  type="number"
                  value={retentionNotifications}
                  onChange={(e) => setRetentionNotifications(parseInt(e.target.value) || 30)}
                  style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                  Audit Events Retention (Days)
                </label>
                <input
                  type="number"
                  value={retentionAuditLogs}
                  onChange={(e) => setRetentionAuditLogs(parseInt(e.target.value) || 365)}
                  style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none' }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.5rem' }}>
                <input
                  type="checkbox"
                  id="unsecure_sandboxes"
                  checked={allowUnsecureSandboxes}
                  onChange={(e) => setAllowUnsecureSandboxes(e.target.checked)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <label htmlFor="unsecure_sandboxes" style={{ color: '#d1d5db', fontWeight: 600, fontSize: '0.95rem', cursor: 'pointer' }}>
                  Allow unsecure developer sandbox execution
                </label>
              </div>

              <button
                type="submit"
                disabled={busy}
                style={{ padding: '0.75rem 1rem', borderRadius: '8px', backgroundColor: '#3b82f6', color: '#fff', fontSize: '1rem', fontWeight: 700, border: 'none', cursor: 'pointer', marginTop: '0.5rem' }}
              >
                {busy ? 'Saving...' : 'Save Policies'}
              </button>
            </form>

            {/* Break Glass Controls */}
            <form onSubmit={handleToggleBreakGlass} style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.75rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, color: '#f3f4f6', fontSize: '1.3rem', fontWeight: 700 }}>Break-Glass Emergency</h3>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  backgroundColor: breakGlassActive ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                  color: breakGlassActive ? '#ef4444' : '#10b981',
                  padding: '0.15rem 0.5rem',
                  borderRadius: '4px'
                }}>
                  {breakGlassActive ? 'ACTIVE OVERRIDE' : 'STANDBY'}
                </span>
              </div>

              <p style={{ margin: 0, color: '#9ca3af', fontSize: '0.9rem', lineHeight: 1.5 }}>
                Activating break-glass mode temporarily bypasses policy rules and automated approval gates for emergency debugging. All overrides are logged with high-severity flags.
              </p>

              {!breakGlassActive && (
                <div>
                  <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                    Justification Reason
                  </label>
                  <textarea
                    placeholder="Provide details on the emergency incident prompting policy override..."
                    value={breakGlassReason}
                    onChange={(e) => setBreakGlassReason(e.target.value)}
                    style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none', height: '80px', resize: 'vertical' }}
                  />
                </div>
              )}

              <button
                type="submit"
                disabled={busy}
                style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: breakGlassActive ? '#10b981' : '#ef4444',
                  color: '#fff',
                  fontSize: '1rem',
                  fontWeight: 700,
                  border: 'none',
                  cursor: 'pointer',
                  marginTop: '0.5rem'
                }}
              >
                {busy ? 'Processing...' : breakGlassActive ? 'Deactivate Break-Glass Mode' : 'ACTIVATE BREAK-GLASS MODE'}
              </button>
            </form>
          </div>
        )}

        {/* Members Tab */}
        {activeTab === 'members' && (
          <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '2rem' }}>
            {/* Members table */}
            <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
              <h3 style={{ margin: '0 0 1.25rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Organization Members</h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem', color: '#d1d5db' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #374151', textAlign: 'left' }}>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Email Address</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Role</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Status</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {members.map((member) => (
                      <tr key={member.user_id} style={{ borderBottom: '1px solid #374151' }}>
                        <td style={{ padding: '0.75rem 0.5rem', fontWeight: 500, color: '#f3f4f6' }}>{member.email}</td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>
                          <select
                            value={member.role}
                            onChange={(e) => handleRoleUpdate(member.user_id, e.target.value as any)}
                            style={{ padding: '0.2rem 0.4rem', border: '1px solid #4b5563', borderRadius: '4px', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.85rem' }}
                          >
                            <option value="admin">Admin</option>
                            <option value="member">Member</option>
                            <option value="viewer">Viewer</option>
                          </select>
                        </td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>
                          <span style={{ fontSize: '0.8rem', padding: '0.1rem 0.4rem', borderRadius: '4px', backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#34d399', fontWeight: 700 }}>
                            {member.status.toUpperCase()}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>
                          <button
                            onClick={() => handleRemoveMember(member.user_id)}
                            style={{ border: 'none', backgroundColor: '#ef4444', color: '#fff', fontSize: '0.8rem', fontWeight: 700, padding: '0.25rem 0.5rem', borderRadius: '4px', cursor: 'pointer' }}
                          >
                            Revoke
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Invite Form */}
            <form onSubmit={handleInvite} style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <h3 style={{ margin: 0, color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Invite New Member</h3>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Email</label>
                <input
                  type="email"
                  placeholder="collaborator@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Initial Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as any)}
                  style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none', cursor: 'pointer' }}
                >
                  <option value="member">Member (Read / Write)</option>
                  <option value="admin">Administrator (Control Panel Access)</option>
                  <option value="viewer">Viewer (Read Only)</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={busy || !inviteEmail.trim()}
                style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', backgroundColor: '#10b981', color: '#fff', fontSize: '0.95rem', fontWeight: 700, border: 'none', cursor: 'pointer', marginTop: '0.5rem' }}
              >
                {busy ? 'Inviting...' : 'Send Invitation'}
              </button>
            </form>
          </div>
        )}

        {/* API Keys Tab */}
        {activeTab === 'apikeys' && (
          <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '2rem' }}>
            {/* Keys Table */}
            <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
              <h3 style={{ margin: '0 0 1.25rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Workspace API Keys</h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem', color: '#d1d5db' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #374151', textAlign: 'left' }}>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Name</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Prefix</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Expires At</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiKeys.map((key) => {
                      const isRevoked = key.revoked_at !== null;
                      return (
                        <tr key={key.id} style={{ borderBottom: '1px solid #374151', opacity: isRevoked ? 0.5 : 1 }}>
                          <td style={{ padding: '0.75rem 0.5rem', fontWeight: 500, color: '#f3f4f6' }}>{key.name}</td>
                          <td style={{ padding: '0.75rem 0.5rem', fontFamily: 'monospace' }}>{key.key_prefix}</td>
                          <td style={{ padding: '0.75rem 0.5rem' }}>
                            {key.expires_at ? new Date(key.expires_at).toLocaleDateString() : 'Never'}
                          </td>
                          <td style={{ padding: '0.75rem 0.5rem' }}>
                            {!isRevoked ? (
                              <button
                                onClick={() => handleRevokeKey(key.id)}
                                style={{ border: 'none', backgroundColor: '#ef4444', color: '#fff', fontSize: '0.8rem', fontWeight: 700, padding: '0.25rem 0.5rem', borderRadius: '4px', cursor: 'pointer' }}
                              >
                                Revoke
                              </button>
                            ) : (
                              <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Revoked</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Create Form */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <form onSubmit={handleCreateKey} style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <h3 style={{ margin: 0, color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>Generate API Key</h3>
                <div>
                  <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Key Name</label>
                  <input
                    type="text"
                    placeholder="Production Server Access"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', color: '#9ca3af', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Expiration Date (Optional)</label>
                  <input
                    type="date"
                    value={newKeyExpires}
                    onChange={(e) => setNewKeyExpires(e.target.value)}
                    style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.95rem', outline: 'none' }}
                  />
                </div>
                <button
                  type="submit"
                  disabled={busy || !newKeyName.trim()}
                  style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', backgroundColor: '#10b981', color: '#fff', fontSize: '0.95rem', fontWeight: 700, border: 'none', cursor: 'pointer', marginTop: '0.5rem' }}
                >
                  {busy ? 'Generating...' : 'Generate key'}
                </button>
              </form>

              {/* Reveal Box */}
              {generatedKeySecret && (
                <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', border: '1px solid #3b82f6', padding: '1.25rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <span style={{ color: '#60a5fa', fontWeight: 700, fontSize: '0.9rem' }}>Important: Copy this key now!</span>
                  <p style={{ margin: 0, color: '#d1d5db', fontSize: '0.85rem', lineHeight: 1.4 }}>
                    It will not be displayed again for security reasons.
                  </p>
                  <div style={{
                    padding: '0.75rem',
                    backgroundColor: '#111827',
                    border: '1px dashed #3b82f6',
                    borderRadius: '8px',
                    fontFamily: 'monospace',
                    color: '#f3f4f6',
                    fontSize: '0.9rem',
                    wordBreak: 'break-all',
                    userSelect: 'all',
                    textAlign: 'center'
                  }}>
                    {generatedKeySecret}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Connections Tab */}
        {activeTab === 'connections' && (
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 1.25rem 0', color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>External Integrations Tokens</h3>
            {connections.length === 0 ? (
              <div style={{ color: '#9ca3af', textAlign: 'center', padding: '4rem 2rem' }}>
                No active external OAuth integrations connections found.
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem', color: '#d1d5db' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #374151', textAlign: 'left' }}>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Provider</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Authorized Scopes</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Linked At</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {connections.map((conn) => (
                      <tr key={conn.id} style={{ borderBottom: '1px solid #374151' }}>
                        <td style={{ padding: '0.75rem 0.5rem', fontWeight: 700, color: '#f3f4f6' }}>{conn.provider.toUpperCase()}</td>
                        <td style={{ padding: '0.75rem 0.5rem', fontFamily: 'monospace', fontSize: '0.85rem' }}>{conn.scopes.join(', ')}</td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>{new Date(conn.created_at).toLocaleDateString()}</td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>
                          <button
                            onClick={() => handleRevokeConnection(conn.provider)}
                            style={{ border: 'none', backgroundColor: '#ef4444', color: '#fff', fontSize: '0.8rem', fontWeight: 700, padding: '0.25rem 0.5rem', borderRadius: '4px', cursor: 'pointer' }}
                          >
                            Disconnect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Audit Tab */}
        {activeTab === 'audit' && (
          <div style={{ backgroundColor: '#1f2937', border: '1px solid #374151', padding: '1.5rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: '#f3f4f6', fontSize: '1.25rem', fontWeight: 700 }}>System Audit Event Trail</h3>

              {/* Simple filter */}
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <input
                  type="text"
                  placeholder="Filter by Event Type..."
                  value={filterEventType}
                  onChange={(e) => setFilterEventType(e.target.value)}
                  style={{ padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #4b5563', backgroundColor: '#111827', color: '#f3f4f6', fontSize: '0.9rem', outline: 'none' }}
                />
                <button
                  onClick={loadTabData}
                  style={{ border: 'none', backgroundColor: '#3b82f6', color: '#fff', fontSize: '0.9rem', fontWeight: 700, padding: '0.4rem 0.8rem', borderRadius: '6px', cursor: 'pointer' }}
                >
                  Search
                </button>
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem', color: '#d1d5db' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #374151', textAlign: 'left' }}>
                    <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Timestamp</th>
                    <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Event Type</th>
                    <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Target Type</th>
                    <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Outcome</th>
                    <th style={{ padding: '0.75rem 0.5rem', color: '#9ca3af', fontWeight: 600 }}>Metadata</th>
                  </tr>
                </thead>
                <tbody>
                  {auditEvents.map((evt) => {
                    const isSuccess = evt.outcome === 'succeeded';
                    const badgeBg = isSuccess ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';
                    const badgeColor = isSuccess ? '#34d399' : '#f87171';

                    return (
                      <tr key={evt.id} style={{ borderBottom: '1px solid #374151' }}>
                        <td style={{ padding: '0.75rem 0.5rem', fontFamily: 'monospace', color: '#9ca3af' }}>
                          {new Date(evt.occurred_at).toLocaleString()}
                        </td>
                        <td style={{ padding: '0.75rem 0.5rem', fontWeight: 700, color: '#f3f4f6' }}>{evt.event_type}</td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>{evt.target_type}</td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '4px', backgroundColor: badgeBg, color: badgeColor }}>
                            {evt.outcome.toUpperCase()}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 0.5rem', fontFamily: 'monospace', fontSize: '0.8rem', color: '#9ca3af', maxWidth: '350px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {JSON.stringify(evt.metadata)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

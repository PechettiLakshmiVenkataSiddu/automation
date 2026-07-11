import { api } from '@/lib/chat-api';

export interface ChatMessage {
  id: string;
  provider: 'slack' | 'teams';
  channel_id: string;
  thread_ts: string | null;
  message_text: string;
  sender_id: string;
  status: 'received' | 'sent';
  received_at: string;
}

export interface ChatProposal {
  id: string;
  channel_id: string;
  message_text: string;
  status: 'pending' | 'approved' | 'rejected';
  decision_reason: string | null;
  created_at: string;
}

export function createConnection(
  token: string,
  organization_id: string,
  provider: 'slack' | 'teams',
  access_token: string,
  refresh_token: string,
  scopes: string[] = [],
  expires_in_seconds = 3600,
): Promise<{ connection_id: string }> {
  return api('/v1/chat-integration/connections', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      provider,
      access_token,
      refresh_token,
      scopes,
      expires_in_seconds,
    }),
  });
}

export function revokeConnection(
  token: string,
  organization_id: string,
  provider: 'slack' | 'teams',
): Promise<{ status: string }> {
  return api(
    `/v1/chat-integration/connections?organization_id=${organization_id}&provider=${provider}`,
    token,
    {
      method: 'DELETE',
    }
  );
}

export function getMessages(
  token: string,
  organization_id: string,
  provider: 'slack' | 'teams',
  channel_id: string,
): Promise<ChatMessage[]> {
  return api(
    `/v1/chat-integration/messages?organization_id=${organization_id}&provider=${provider}&channel_id=${channel_id}`,
    token
  );
}

export function proposeMessage(
  token: string,
  organization_id: string,
  channel_id: string,
  message_text: string,
): Promise<{ proposal_id: string }> {
  return api('/v1/chat-integration/proposals', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      channel_id,
      message_text,
    }),
  });
}

export function getProposals(
  token: string,
  organization_id: string,
): Promise<ChatProposal[]> {
  return api(`/v1/chat-integration/proposals?organization_id=${organization_id}`, token);
}

export function decideProposal(
  token: string,
  organization_id: string,
  proposal_id: string,
  approved: boolean,
  reason?: string,
): Promise<{ status: string }> {
  return api(`/v1/chat-integration/proposals/${proposal_id}/approve`, token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, approved, reason }),
  });
}

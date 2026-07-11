import { api } from '@/lib/chat-api';

export interface EmailMessage {
  id: string;
  google_message_id: string;
  thread_id: string;
  from_address: string;
  to_addresses: string[];
  subject: string | null;
  body_snippet: string | null;
  body_text: string | null;
  status: 'received' | 'draft' | 'sent';
  received_at: string;
}

export interface EmailProposal {
  id: string;
  recipient_address: string;
  subject: string | null;
  body_text: string;
  attachments: Array<{ filename: string; size_bytes?: number }>;
  status: 'pending' | 'approved' | 'rejected';
  decision_reason: string | null;
  created_at: string;
}

export function createConnection(
  token: string,
  organization_id: string,
  access_token: string,
  refresh_token: string,
  scopes: string[] = [],
  expires_in_seconds = 3600,
): Promise<{ connection_id: string }> {
  return api('/v1/email/connections', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
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
): Promise<{ status: string }> {
  return api(`/v1/email/connections?organization_id=${organization_id}`, token, {
    method: 'DELETE',
  });
}

export function getMessages(token: string, organization_id: string): Promise<EmailMessage[]> {
  return api(`/v1/email/messages?organization_id=${organization_id}`, token);
}

export function proposeEmail(
  token: string,
  organization_id: string,
  recipient_address: string,
  subject: string | null,
  body_text: string,
  attachments: Array<{ filename: string; size_bytes?: number }> = [],
): Promise<{ proposal_id: string }> {
  return api('/v1/email/proposals', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      recipient_address,
      subject,
      body_text,
      attachments,
    }),
  });
}

export function getProposals(token: string, organization_id: string): Promise<EmailProposal[]> {
  return api(`/v1/email/proposals?organization_id=${organization_id}`, token);
}

export function decideProposal(
  token: string,
  organization_id: string,
  proposal_id: string,
  approved: boolean,
  reason?: string,
): Promise<{ status: string }> {
  return api(`/v1/email/proposals/${proposal_id}/approve`, token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, approved, reason }),
  });
}
